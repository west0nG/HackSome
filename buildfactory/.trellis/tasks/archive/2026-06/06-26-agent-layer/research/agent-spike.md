# Agent Layer — 前置 Spike 结论（S1-S3）

> 目的：消除 `design.md` R1-R3 的不确定性，供主代理 review 后决定是否回填 design。
> 环境：镜像 `foundagent/cua-agent:latest`，claude CLI `2.1.195`，容器内 `kasm-user`（HOME=`/home/kasm-user`），订阅 token（`vm/.env.local` 的 `CLAUDE_CODE_OAUTH_TOKEN`），**无** `ANTHROPIC_API_KEY`。
> 起停容器：`spike-agent`（已 teardown，无残留）。

---

## ⚠️ design 需回填清单（交主代理决定，本报告不改 design.md）

1. **【R1 / design §3.5 字段名错】** runner 解析 `result` event 的字段与 design 假设不符：
   - final text 字段是 **`result`**（不是 `text`）。
   - cost 字段是 **`total_cost_usd`**（不是 `cost_usd`）。
   - **ok 信号必须用 `is_error`（bool）判定，不能用 `subtype`**：实测一次 401 错误时 `subtype` 仍为 `"success"` 而 `is_error=true`。即 `ok = (not is_error)`。
   - 建议把 design §3.5 解析逻辑明确为：`ok = not ev["is_error"]`；`text = ev["result"]`；`cost_usd = ev.get("total_cost_usd")`；`error` 取 `api_error_status` / `result`。

2. **【R3 / design §3.3 凭证互斥】** 新增关键约束（design 未提）：**`ANTHROPIC_API_KEY` 优先级高于 `CLAUDE_CODE_OAUTH_TOKEN`**——两者同时存在时 API key 胜出、订阅 token 被静默忽略。因此：
   - 凭证 seam 必须**只注入二者之一**（互斥）。
   - 订阅模式（默认）下必须保证容器环境里**没有** `ANTHROPIC_API_KEY`，否则订阅被悄悄覆盖 → 隐性 bug。
   - 「一键切 api-key」= 注入 `ANTHROPIC_API_KEY` 且**清掉** `CLAUDE_CODE_OAUTH_TOKEN`（虽然 API key 本就会胜出，但清掉更干净、避免混淆）。
   - 建议在 design §3.3 / §6 R3 补一句「SubscriptionCreds 与 ApiKeyCreds 的 env 互斥，runner 注入前应剔除另一方」。

3. **【R3 未尽验证】** 无真实 API key，**未能验证 api-key 端到端成功调用**（仅验证「识别 + 路径成立 + 优先级」）。标注：**待有真实 key 时复核** api-key 模式跑通（AC3 的「能跑通最小调用」那半句）。

> R2（skill 落点）**与 design 假设一致，无需回填**。

---

## S1 — stream-json `result` event 字段（→ runner 解析依据）

**命令**（容器内，订阅 token 注入）：
```
claude -p "say hi" --output-format stream-json --verbose \
  --dangerously-skip-permissions --mcp-config /opt/foundagent/mcp.json
```

**事件序列**（共 4 行 NDJSON，每行一个 event）：
```
system        | subtype=init
assistant     |
rate_limit_event |
result        | subtype=success      ← 末行，runner 取这个
```

**末行 `result` event 真实样例**（已裁剪）：
```json
{
  "type": "result",
  "subtype": "success",
  "is_error": false,
  "result": "Hi! How can I help you today?",
  "total_cost_usd": 0.0417612,
  "num_turns": 1,
  "stop_reason": "end_turn",
  "duration_ms": 6935,
  "api_error_status": null
}
```
`result` event 全部 key：`api_error_status, duration_api_ms, duration_ms, fast_mode_state, is_error, modelUsage, num_turns, permission_denials, result, session_id, stop_reason, subtype, terminal_reason, time_to_request_ms, total_cost_usd, ttft_ms, ttft_stream_ms, type, usage, uuid`。

**附：`system/init` event 关键字段**（对 runner / loadout 都有用）：
- `apiKeySource = "none"`（订阅 OAuth 时为 none，见 S3 对照）
- `model = "claude-sonnet-4-6"`
- `permissionMode = "bypassPermissions"`（`--dangerously-skip-permissions` 生效）
- `mcp_servers = [{"name":"cua-local","status":"pending"}]`（`/opt/foundagent/mcp.json` 已加载，懒连接）
- `skills = [...]`（见 S2，落点验证用这个列表）
- `memory_paths.auto = /home/kasm-user/.claude/projects/-home-kasm-user/memory/`

**结论**：design §3.5 的「取末尾 type=='result' event」思路正确，但**字段名需按上表修正**（见回填清单 #1）。`--append-system-prompt` / `--mcp-config` / `--output-format stream-json --verbose` 这套 flag 全部有效（help 中 `--append-system-prompt[-file]` 已确认存在）。

---

## S2 — skill 发现/调用落点（→ loadout 落点）

**步骤**：容器内写 `~/.claude/skills/hello-foundagent/SKILL.md`（带 `name`/`description` frontmatter + 一句话 body：固定 motto），再跑 `claude -p`。

**SKILL.md**：
```
---
name: hello-foundagent
description: A trivial probe skill. Use when asked to greet the Foundagent company. Replies with a fixed company motto.
---
When invoked, respond with exactly: "Foundagent operator online. Motto: zero humans, full autonomy."
```

**发现证据**（`system/init` 的 `skills` 列表，注入后首位即出现）：
```
['hello-foundagent', 'deep-research', 'design-sync', 'update-config', 'verify',
 'debug', 'code-review', 'simplify', 'batch', 'fewer-permission-prompts',
 'loop', 'schedule', 'claude-api', 'run', 'run-skill-generator']
```
`hello-foundagent discovered: True`。

**调用证据**（assistant event 里有真实 Skill tool_use，非脑补）：
```
text block: Here are the available skills: - hello-foundagent — ...
tool_use:   Skill   input={"skill": "hello-foundagent"}
text block: Foundagent operator online. Motto: zero humans, full autonomy.
```
final `result` = `"Foundagent operator online. Motto: zero humans, full autonomy."`（与 skill body 逐字一致）。

**结论**：**订阅版 claude 能从 `~/.claude/skills/<name>/SKILL.md` 发现并经 `Skill` 工具调用该 skill**。design §3.4 把 loadout 的 skill 落点定为 `<claude_home>/skills/<name>/`（`claude_home = vm/data/<name>/claude` 挂到容器 `/home/kasm-user/.claude`）**完全成立，无需回填**。

---

## S3 — api-key 凭证切换路径（→ AC3）

> 无真实 API key，**未真跑成功调用**；改为验证「env 识别 + 注入路径 + 优先级」。用明显假 key `sk-ant-INVALID-spike-probe-not-a-real-key`，**只读 `system/init` 的 `apiKeySource` 识别信号**，不依赖调用成功。

**权威文档**（`claude --help`，`--simple` 段落，确认 env 名）：
> "Anthropic auth is **strictly ANTHROPIC_API_KEY** or apiKeyHelper via --settings (OAuth and keychain are never read)."

**Test 3A：只设 `ANTHROPIC_API_KEY`（假）、不设 OAuth**
```
init.apiKeySource = "ANTHROPIC_API_KEY"     ← claude 识别并采用该 env
result.is_error   = True
api_error_status  = 401                       ← 仅因 key 是假的；路径本身通
```

**Test 3B：同时设 OAuth（真）+ `ANTHROPIC_API_KEY`（假）**
```
init.apiKeySource = "ANTHROPIC_API_KEY"
result.is_error   = True
result.result     = "Invalid API key · Fix external API key"
```
=> **API key 胜出、订阅 token 被忽略**（否则真 OAuth 会成功）。

**对照 S1**：只设 OAuth 时 `apiKeySource="none"` 且成功。

**结论**：
- 凭证 seam 切到 api-key = 注入 **`ANTHROPIC_API_KEY`**，路径成立（claude 确认识别）。
- **优先级：`ANTHROPIC_API_KEY` > `CLAUDE_CODE_OAUTH_TOKEN`**（两者并存时 API key 覆盖订阅）→ 见回填清单 #2：seam 必须互斥注入，订阅模式下严禁残留 `ANTHROPIC_API_KEY`。
- **待有真实 key 时复核**：api-key 模式端到端成功调用未验证（401 仅证明 key 假，不证明真 key 会通——但路径与识别已确证）。
- 顺带一个 runner 注意点（来自 3A）：401 时 `subtype` 仍为 `"success"`、靠 `is_error=True` 才能识别错误（已并入回填清单 #1）。

---

## 容器记录

- 起：`spike-agent`（`docker run -d --name spike-agent foundagent/cua-agent:latest --wait`，computer-server :8000 ~18s 就绪）。
- 停：`docker rm -f spike-agent` 已执行；`docker ps -a` 确认无 `spike-agent` / `op-*` 残留。
- 未改 `agent/` 包、未改 `orchestration/broker.py`、未 commit。
