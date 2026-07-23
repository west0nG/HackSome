# Unified Agent Loop + 全员常驻 + P2P — 技术设计（design.md）

> 配套重定向后的 `prd.md`（2026-06-29 第二轮）。基线：`orchestration/{ceo_loop,inbox,goal_cli}.py`、`docker-compose.yml`、`agents/*.yaml`。
> 一句话：`ceo_loop` → 通用 `agent_loop`；CEO + 4 部门都是它的实例（全常驻、自驱 poll 各自 inbox、容器内 `claude --resume`）；inbox 升双向 P2P；跑通最简零人闭环。

## 0. 范围与中间态

- 本任务只做**机制**：统一 loop + 全员常驻 + P2P 通信。
- **中间态（prd 已声明）**：最简闭环**暂不含**独立验收分权 + watchdog；现有同步 `goal_pump`/`run_goal` **停用不删**（child② 重建异步版）。

## 1. 关键简化：复用 `ceo_loop` 的 subprocess 路径，不碰 ephemeral spawn

- `ceo_loop.wake_ceo` 已是**容器内直接** `subprocess.run(["claude","-p",...,"--resume",sid])`（`build_claude_argv`），**不走** `broker.spawn` / `agent.runner.run_task`（那是 docker-exec 进容器的 ephemeral 路径）。
- 统一 loop 下部门也容器内自跑 `claude --resume` → **本任务不改 `agent/provider.py`/`runner.py`/`broker.py`**。那条 ephemeral 路径（含 `goal_pump`/`run_goal`）在 child① **退役、保留可回退**。
- session **每容器自管**（一容器一 key 一 session，像现 CEO），无需 host 集中管。

## 2. 通用 `agent_loop`（重构 `ceo_loop.py`）

把 `main()` 的 CEO 专属循环抽成参数化函数：

```
def agent_loop(*, key, charter_path, session_file, heartbeat, mcp_config=None):
    inbox = FileInbox()
    session = load_session(session_file)
    while True:
        events = inbox.poll(key, heartbeat)          # receive 信号（自己的 inbox）
        session = wake(session, build_wake_prompt(events), charter_path, mcp_config)
        save_session(session_file, session)          # 仅变化时
```

- `wake`（即现 `wake_ceo` 泛化）：`build_claude_argv` 已支持 `resume`/`new_session`/`charter`；**新增 `--mcp-config`，所有实例（含 CEO）都传 cua-local**（不限制能力——CEO 也可能需要操作桌面）。
- `build_wake_prompt` 已能渲染 5-field IME（`text`+`body`），对 CEO（收 result）和部门（收 goal）都通用——"该干嘛"由 charter + IME 内容决定，不写进 loop。
- 实例参数：

> **5 个实例完全同构，只有 `key` + `charter` 不同**；computer-server(`:8000`) + cua MCP + `/company` 挂载**全部相同、全 on**（用户定：不限制能力，用不用是一回事、开不开是一回事）。

| 实例 | key | charter |
|---|---|---|
| CEO | `ceo` | ceo-charter |
| Researcher | `researcher` | researcher-charter |
| Builder | `builder` | builder-charter |
| Growth | `growth` | growth-charter |
| Verifier | `verifier` | verifier-charter |

> `ceo_loop.py` 保留一个薄 `main()` = `agent_loop(key="ceo", ...)`，兼容现有归档引用；新部门 entrypoint 走同一 `agent_loop`。

## 3. inbox 双向 P2P（扩展现有 `FileInbox`）

- `FileInbox.append(key,event)` / `poll(key,timeout)` **已支持任意 key**——双向 P2P 不需要新存储，只是 CEO 与各部门各用自己的 key。
- **IME 加 `reply_to`**（payload 约定）：派活 IME 带 `reply_to=caller_key`、`goal_id`，部门据此知道干完回投给谁。
- 渲染：`build_wake_prompt` 渲染 `text`/`body` 不变；`reply_to`/`goal_id` 作为结构字段供 messaging 原语使用（也可渲进 prompt 让 agent 知道上下文）。

## 4. messaging 原语（cli，注入所有 agent 容器）

由现有 `goal_cli` 改 / 扩成统一 messaging（bash 调，非 MCP）：

- `send(to, intent, reply_to=self, goal_id=new)` → `inbox.append(to, IME{text=intent, reply_to, goal_id})`。CEO 派活、部门派下级都用它。
- `report(to, summary)` → `inbox.append(to, IME{text=summary, ...})`。部门干完回投 caller（`to=reply_to`）。

agent 在容器内用 Bash 调（charter 教它）：CEO 醒来 `send researcher "..."`；researcher 干完 `report ceo "done: ..."`。

## 5. compose：5 个常驻 service + 统一 entrypoint

统一 entrypoint 脚本（所有 agent 共用，按 env 参数化）：

```
1) chown -R kasm-user ~/.claude         # 持久卷归位（解 ceo-loop 记的 root-owned 坑）
2) 起 computer-server :8000（镜像默认那套）—— 所有实例（含 CEO），不限制能力
3) materialize 本 role 的 charter/skill 进 ~/.claude
4) exec python3 -m orchestration.agent_loop   # 读 AGENT_KEY/CHARTER/MCP_CONFIG/... env
```

- 5 个 service 同镜像 `foundagent/cua-agent:latest`、同 entrypoint，**只靠 env `AGENT_KEY` + `AGENT_CHARTER` 区分**（其余配置全相同）。
- 挂载：**5 容器统一**——都挂 inbox + 各自 charter + `/company` + company_state_kit + cua MCP + 持久 `~/.claude`，都起 `:8000`，**都无 docker.sock**（spawn 是另一回事，与 computer-server 无关；部门和 CEO 都不 spawn）。CEO 挂 `/company` 便于读公司状态做决策（顺应不限制能力）。
- `restart: unless-stopped`。

## 6. session per-key 持久化

- 每容器一个 `session_file`（容器内路径）+ 持久 `~/.claude` 卷；chown-on-init（§5 step 1）做到跨 `rm` resume（AC7）。
- 与 CEO 现状同形，只是每部门各有一份。

## 7. 中间态：pump / run_goal 停用（不删）

- child① CEO 直投部门、部门直回，**不经** `goal_pump`/`run_goal`。
- `goal_ledger`：child① 可暂只作旁路记录或暂不写（child② 正式旁路化 + 异步状态机）。
- 这些模块**保留在代码库**（回滚 + child② 重建基础），仅在 compose / 启动路径上不再激活。

## 8. 兼容性 / 回滚

- ephemeral 路径（`broker.spawn`/`runner.run_task`/`goal_pump`/`run_goal`）整套保留，可回退。
- broker 容器（docker.sock）：child① 可保留待命（未来 ephemeral）或暂不起；不删。
- 待回填：compose 头注、orchestration-layer design §1、role-library 决策2、ceo-loop「CEO 专属 loop」描述。

## 9. 测试策略

- **新单测**：① `agent_loop` 的 pure builders（`build_claude_argv` 加 mcp_config 分支、`build_wake_prompt` 对部门 IME 的渲染）；② inbox 任意 key 双向 + IME `reply_to` 往返；③ messaging `send`/`report` 构造正确 IME 并投对 key。
- **现有测试**：`ceo_loop` 测试随重构调整为 `agent_loop(key="ceo")` 等价用例；`inbox`/`goal_ledger` 核心不变；`goal_pump`/`run_goal`/`goal_runtime` 测试在 child① **保留但标记停用路径**（child② 重建）。
- **gated e2e（PAID）**：`make up`（5 常驻）→ 注入 directive 给 CEO → CEO `send researcher` → researcher 自驱醒来干活写 `/company` → `report ceo` → CEO 醒来收到。**AC4 专项**：连派两个相关 goal 给 researcher，断言第二个引用第一个上下文（同 session）。

## 10. 实现时验证项（fail-loud）

1. 部门容器内 `claude -p --resume` + cua MCP（`:8000`）+ company_state_kit 三者协同（CEO 只验证过纯 `claude -p`）。
2. computer-server flag 起停正确（on 起 `:8000`、off 不起）。
3. chown-on-init 后 `kasm-user` 可写持久 `~/.claude`。
4. 部门 claude 在一个 turn 内调 `messaging report` 成功 `append` 回 caller inbox（跨 uid 锁 0o666 仍生效）。
5. 部门 loop 串行处理（一次一个 goal）下，长任务不阻塞 inbox 投递（投递是 append，不阻塞）。

> 任一项不成立显式报错，不静默回退 ephemeral。
