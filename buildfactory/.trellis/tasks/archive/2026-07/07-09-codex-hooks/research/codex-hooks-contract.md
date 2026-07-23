# Research: codex Stop hook 阻断契约（0.142.5 实测）

- **Query**: codex hooks 系统的 Stop 阻断契约、循环护栏、trust 机制、多源合并，及其在 pinned 0.142.5 下的真实行为
- **Scope**: mixed（官方文档 + 本机 live 实验）
- **Date**: 2026-07-09
- **实验环境**: 本机 codex-cli **0.142.5**（与 `vm/docker/Dockerfile.agent` pin 的容器版本**完全一致**），ChatGPT 订阅 auth，隔离 CODEX_HOME + 非 git workdir，全部产物在 scratchpad `exp/`（run1–run5 JSONL + hook 日志 + rollout transcript 均为真实捕获）

## 结论速览

**codex Stop hook 契约与 claude 几乎逐字段同构：`{"decision":"block","reason":...}` + exit 0 阻断、exit 0 无输出放行、stdin 里就有 `stop_hook_active`。现有 `record_stop_hook.py` 的 stdin/stdout 契约零改动即可在 codex 下工作（R4 的"双契约垫片"不需要）。唯一必要的 argv 变化：hooks 存在时加 `--dangerously-bypass-hook-trust`，否则 hook 被静默跳过。**

---

## 五个问题的答案

### Q1. Stop hook 阻断契约 —— 【实测，高置信】

**hooks.json schema**（三层：事件 → matcher 组 → handlers；Stop 事件 matcher 被忽略，可省略）：

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 /abs/path/to/record_stop_hook.py",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

- `timeout` 单位秒，省略默认 **600 秒**（建议显式给小值，如 30）。
- `statusMessage` 可选；`async: true` 会被**跳过**（尚不支持）；只有 `type: "command"` 会跑（`prompt`/`agent` 被解析但跳过）。
- hook 以 session `cwd` 为工作目录运行。

**阻断（= claude 的 block 等价物）**：stdout 打印 `{"decision":"block","reason":"<text>"}` 并 exit 0。文档原文："For this event, `decision: "block"` doesn't reject the turn. Instead, it tells Codex to continue and automatically creates a new continuation prompt that acts as a new user prompt, using your `reason` as that prompt text."（另一等价通道：exit code **2** + stderr 写 reason —— 文档，未实测。）

**放行**：exit 0、无输出（实测通过；与 claude 脚本现行为一致）。

**`continue`/`stopReason`/`systemMessage` 不是阻断词汇**：那是 common output fields —— `continue: false` 语义相反（强制停、且优先级高于其他 hook 的 block）；`systemMessage` 只是 UI/事件流警告。**让模型继续干活的机制就是 `decision:block`，与 claude 同名同形。**

**模型实际看到什么（实测，rollout transcript 逐字捕获）**：reason 被包装成一条 `role: "user"` 消息注入：

```
<hook_prompt hook_run_id="stop:0:/path/to/hooks.json">HOOK-BLOCK: before stopping you MUST ...</hook_prompt>
```

run2 实测全链路：模型收到该消息后真的执行了 hook 要求的 shell 命令（`touch sentinel.marker`）并按指示回复——**回注指令完全有效**。claude 侧 reason 的表达无需改写。

### Q2. 循环护栏 —— 【实测，高置信】

**`stop_hook_active` 存在，字段名与 claude 完全相同**。Stop 事件 stdin 字段（run2/run5 逐字节捕获）：

```json
{"session_id": "...", "turn_id": "...", "transcript_path": ".../rollout-....jsonl",
 "cwd": "...", "hook_event_name": "Stop", "model": "gpt-5.5",
 "permission_mode": "bypassPermissions", "stop_hook_active": false,
 "last_assistant_message": "PING"}
```

- 第一次 Stop：`stop_hook_active: false`；被 block 续跑后的第二次 Stop：`true`。**turn 作用域**（两次 Stop 的 `turn_id` 相同；`exec resume` 开新 turn 后重置为 false —— run5 实测），即每次 wake 都有独立的一轮强制，符合我们的需要。
- 现有 `record_stop_hook.py` 的 `if event.get("stop_hook_active"): allow` 护栏**原样生效**。
- 额外可用状态：hook 继承父进程 env（见 Q4 附带实测），marker 目录自身也可做 attempt 记账——但既然 `stop_hook_active` 在，两者都用不上。

### Q3. hook trust 与 headless —— 【实测，高置信】

- **不带 `--dangerously-bypass-hook-trust`：hooks 被静默跳过**（run1：hook 未执行、JSONL 和 stderr 里连 warning 都没有——headless `--json` 下无任何提示，这是最危险的静默失效模式）。
- **带上该 flag：hooks 正常运行**（run2/3/5）。flag 是 per-invocation 的，`codex exec --help` 确认存在（"Run enabled hooks without requiring persisted hook trust for this invocation"）。
- **结论：argv 必须追加 `--dangerously-bypass-hook-trust`**（与 `--dangerously-bypass-approvals-and-sandbox` 并列；建议仅在本次 materialize 确实翻译了 hooks 时加，语义最小化）。
- trust 无法非交互预置：审阅/信任只有 TUI `/hooks` 一条路（文档），trust 按 hook 定义的 hash 记账；实测跑完后翻遍 CODEX_HOME（含 state_5.sqlite 等全部 SQLite 表）没有可预写的 trust 存储。【实测+文档，中高置信】
- 替代路线 `requirements.toml` managed hooks（"trusted by policy" 免审阅）**走不通**：其位置只有 cloud-managed / macOS MDM / 系统级 `/etc/codex/requirements.toml`，**不在 CODEX_HOME 下**，粒度是整机/全 fleet——会把 hooks 塞给容器里所有角色，与"verifier 必须无 hooks"直接冲突。【文档，高置信】
- 附带：flag 开启后 JSONL 里出现 **2 条** `item.completed` / `item.type=="error"` 的警告项（"`--dangerously-bypass-hook-trust` is enabled..."）——非致命，`turn.completed` 照发；现有 `parse_output` 的"error item 不算失败"立场恰好覆盖，无需改动。【实测】

### Q4. 多源合并与隔离 —— 【实测，高置信】

实测（run3，隔离 CODEX_HOME + 非 git workdir + bypass flag）：

| 来源 | 是否生效 |
|---|---|
| `$CODEX_HOME/hooks.json` | ✅ 生效 |
| `<workdir>/.codex/hooks.json`（workdir **不是** git repo） | ✅ **同样生效**（两个 hook 都跑了；多源合并=全都跑，不覆盖） |
| `/etc/codex`（系统层） | 本机不存在；容器镜像内需确认不存在（见"待容器内验证"） |
| `$CODEX_HOME/config.toml` 内联 `[hooks]` | 未用；文档：与 hooks.json 同层共存会 merge + 启动警告 → **只用 hooks.json 一种表示** |

**隔离结论有一条豁口**：`--dangerously-bypass-hook-trust` 会连 workdir 的 `.codex/hooks.json` 一起放行（文档说 project 层需 project trust，但 bypass flag 实测把它也放开了，git repo 与否无关）。agent workdir 是 agent 可写的 → agent 理论上能给自己加 hooks。按我们的 permissions 立场（先给权限、少限制）可接受，但设计文档应记录这一点；`allow_managed_hooks_only` 能压掉它但会连 CODEX_HOME hooks 一起压掉，不可用。

**附带实测（R5 关键前提）**：hook 子进程**继承 codex 父进程的全部 env**（run3 中 hook 读到了启动前 export 的 `COMPANY_TEST_ENV`，也看得到 `CODEX_HOME`）→ per-wake nonce 经 env 传给 hook 的路线可行。

### Q5. 0.142.5 版本核对 —— 【实测，高置信】

本机二进制就是 **codex-cli 0.142.5**（`codex --version` 确认），与 Dockerfile.agent pin 完全一致。Q1–Q4 的全部核心行为（schema 生效、decision:block 续跑、stop_hook_active、bypass flag、多源合并、env 继承、崩溃降级、resume 路径）都在该版本上 live 验证，**不存在"文档写的是新版"的风险敞口**。仅标注为【文档】的条目（exit-2 通道、TUI trust 流程、requirements.toml 位置、plugin hooks）未逐一实测。

---

## 额外实测发现（design 直接要用）

1. **hook 崩溃 = 静默 fail-open**（run4：exit 1 + 垃圾 stdout → 会话正常结束、turn.completed 照发、无任何 error item）。never-brick 天然满足；**反向警告**：shim 里任何异常路径都不得 `sys.exit(2)`（exit 2 = block 通道），现脚本恒 exit 0，安全。
2. **block-续跑不产生第二对 turn 事件**：同一 `turn.started`/`turn.completed`、同一 `turn_id`，最后一条 `agent_message` 是续跑后的回复 → 现有 `parse_output`（last agent_message wins、单 completed 判定）**零改动兼容**。
3. **`exec resume` 路径 Stop hook 照常触发**（run5：resume 后 block/续跑/`stop_hook_active` 全套行为一致，thread id 不变）——resident 常驻 wake 循环两条分支都覆盖。
4. **`features.hooks` 默认开启**（0.142.5 实测：什么都没配 hooks 就跑了）。
5. codex 的 `session_id`（= thread id）**跨 wake 不变**（resume 同 id）→ 若 marker 按 session_id 键控，第一次 record 后后续每个 wake 都免检——这正是 R5 说的错位在 codex 侧的镜像。**per-wake nonce 是两个 runtime 共同的正解**，且 nonce 走 env 在两侧 hook 中都可读（codex 侧本次实测；claude 侧 hook 为子进程继承 env，已知行为）。

## 建议生成的 hooks.json（materialize_home step 4）

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 /opt/company_state_kit/hooks/record_stop_hook.py",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

配套 argv（`build_argv`）：hooks 翻译成功时追加 `--dangerously-bypass-hook-trust`。

## R4 垫片设计建议：不需要垫片

`record_stop_hook.py` 用到的三样东西在 codex 下逐一成立：

| 契约点 | claude | codex 0.142.5 | 结论 |
|---|---|---|---|
| stdin `stop_hook_active` | ✅ | ✅ 同名同义（实测） | 原样 |
| stdin `session_id` | ✅ | ✅（= thread id，实测） | 原样（仅作 fallback，见下） |
| block 输出 | `{"decision":"block","reason"}` + exit 0 | 完全相同（实测） | 原样 |
| allow 输出 | exit 0 无输出 | 完全相同（实测） | 原样 |

唯一要改的是 **marker keying（R5，runtime 中性改动而非 codex 垫片）**：`session_marker_path` 改为 env-first——agent_loop 每次 wake 前 export 一个 per-wake nonce（如 `COMPANY_WAKE_ID`），`company.py` CLI 与 hook 都优先读该 env，stdin `session_id` 仅作无 env 时的 fallback。理由：① codex 无法预设 thread id 且 resume 时 id 不变；② claude resident 侧本就没人 export `COMPANY_SESSION_ID`（PRD R5 指出的既有错位）；③ env 继承两侧实测/已知均成立。

## 待容器内验证（唯一剩余敞口，均为低风险）

- 镜像内确认 `/etc/codex/`、`/etc/codex/requirements.toml` 不存在（本机不存在；若基础镜像日后带入会引入 managed 层）。
- 容器内（Linux/musl 二进制、真实 headless 环境）复跑一次 run2 式冒烟：同版本同 flag，预期行为一致；纯保险性质。
- ChatGPT Business/Enterprise 账号的 cloud-managed requirements 会随登录下发（文档）——当前订阅若属个人 Plus/Pro 不受影响；换企业账号时留意 `allow_managed_hooks_only` 被云端推下来的可能。

## 实验产物清单（scratchpad，会话级）

`/private/tmp/claude-501/-Users-weston-dev-BuildFactory/76ba1dbb-c91f-4d1f-911e-10e1cfb3a537/scratchpad/exp/`：
- `run1.*`：无 bypass flag → hook 静默跳过
- `run2.*` + `hooks/stop_hook_log.jsonl`：完整 block→续跑→stop_hook_active=true→放行链路
- `run3.*`：repo 级 `.codex/hooks.json`（非 git dir）生效 + env 继承证明
- `run4.*`：hook 崩溃 fail-open
- `run5.*`：`exec resume` 路径全套行为
- `home/sessions/.../rollout-*.jsonl`：`<hook_prompt>` 注入的逐字 wire format

## Sources

- https://developers.openai.com/codex/hooks （.md 直出版本已存 scratchpad `hooks-doc.md`；Stop 章节、Config shape、Review and trust、Common output fields）
- https://developers.openai.com/codex/config-reference （`requirements.toml`、`allow_managed_hooks_only`）
- https://developers.openai.com/codex/enterprise/managed-configuration （requirements.toml 三个位置与优先级）
- 本机 live 实验：codex-cli 0.142.5，2026-07-09，run1–run5（上述清单）
- 前置调研：`.trellis/tasks/archive/2026-07/07-07-codex-runtime/research/codex-cli-capability-map.md` §9
