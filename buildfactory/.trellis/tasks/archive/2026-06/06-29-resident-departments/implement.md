# Unified Agent Loop + 全员常驻 + P2P — 执行计划（implement.md）

> 配套 `prd.md` + `design.md`（2026-06-29 第二轮重定向后）。原则：**小步、每步测试绿、ephemeral 路径保留可回退**。
> 中间态红线：child① **不接** 独立验收分权 / watchdog；`goal_pump` / `run_goal` **停用不删**。

## 阶段 0 · 基线确认（回滚锚点）

- [ ] `python -m pytest orchestration/ agent/ -q` → 现有 117 单测全绿（记下基线）。
- [ ] 记当前 `git rev` 为回滚锚点（child① 全程不删 ephemeral 路径，可随时 `RESIDENT` 回退）。

## 阶段 1 · 通用 `agent_loop`（重构 `ceo_loop.py`）

- [ ] `build_claude_argv` 新增 `mcp_config: str | None` → 拼 `--mcp-config`（所有实例都传 cua-local）。
- [ ] 抽 `agent_loop(*, key, charter_path, session_file, heartbeat, mcp_config)`：循环体 = `poll(key) → wake(resume, charter, mcp) → save_session(key)`。
- [ ] 新建启动入口 `orchestration/agent_loop.py`（或扩 `ceo_loop`）：读 env `AGENT_KEY` / `AGENT_CHARTER` / `AGENT_SESSION_FILE` / `AGENT_MCP` / `CEO_HEARTBEAT_SECS` → 调 `agent_loop(...)`。
- [ ] `ceo_loop.main()` 改成薄包装 = `agent_loop(key="ceo", ...)`（兼容归档引用）。
- **验证**：`pytest orchestration/tests/test_ceo_loop.py -q`（调整为 `agent_loop(key="ceo")` 等价用例）；新单测覆盖 `build_claude_argv` 的 mcp 分支 + `agent_loop` 参数化。
- **回滚点**：纯重构，行为等价；测试不绿即回退本阶段。

## 阶段 2 · inbox 双向 P2P + IME `reply_to`

- [ ] IME 约定加 `reply_to`（caller key）+ `goal_id`；`build_wake_prompt` 渲染不变（`text`/`body`），结构字段供 messaging 用。
- [ ] 确认 `FileInbox` 任意 key 双向（已支持，补测即可）。
- **验证**：新单测——任意 key `append`/`poll` 往返、IME `reply_to` 透传；`pytest orchestration/tests/test_inbox.py -q` 绿。

## 阶段 3 · messaging 原语（`goal_cli` 扩 `send` / `report`）

- [ ] `send(to, intent, reply_to=self, goal_id=new)` → `inbox.append(to, IME{...})`。
- [ ] `report(to, summary)` → `inbox.append(to, IME{...})`。
- [ ] 保持 bash 可调（`python -m orchestration.messaging send|report ...`）；charter 会教 agent 用。
- **验证**：新单测——`send`/`report` 构造正确 IME、投对 key；`pytest orchestration/tests/test_goal_cli.py -q`（或新 `test_messaging.py`）绿。

## 阶段 4 · 占位 charter（机制先行）

- [ ] `agents/builder.yaml`、`agents/growth.yaml` 建最小占位（沿用 `company-operator` loadout 指向）。
- [ ] 4 部门 + CEO 的 charter md：CEO/researcher/verifier 已有；builder/growth 写**最小占位**（注明真实内容归 `06-28-role-library`）。
- **验证**：`AgentSpec.load` 5 个 yaml 不报错；`resolve_role_spec("builder"/"growth")` 不 `FileNotFoundError`。

## 阶段 5 · compose 5 service + 统一 entrypoint

- [ ] 统一 entrypoint 脚本：`1) chown -R kasm-user ~/.claude → 2) 起 computer-server :8000 → 3) materialize 本 role charter/skill → 4) exec python3 -m orchestration.agent_loop`。
- [ ] `docker-compose.yml`：改 `ceo` service 走统一 entrypoint（加 `:8000` + `/company` + cua MCP + 持久卷）；新增 `researcher`/`builder`/`growth`/`verifier` 4 service（同模板，只换 `AGENT_KEY`/`AGENT_CHARTER`）。**5 容器都无 docker.sock**。
- [ ] 持久卷 + chown-on-init（解 ceo-loop 记的 root-owned 坑）。
- [ ] broker 容器：暂保留待命或不起（不删；ephemeral/未来用）。
- **验证**：`make up` → `docker ps` 见 5 常驻容器；`make logs-ceo` 见 `agent_loop` 启动；各容器 `:8000` ready。

## 阶段 6 · 最简零人闭环 e2e（PAID·gated）

- [ ] `make up`（5 常驻）→ 注入 directive 给 CEO（沿用现有 directive 注入）。
- [ ] CEO 醒来 `send researcher "<任务>"` → researcher 自驱醒来干活写 `/company` → `report ceo "done: ..."` → CEO 醒来收到。
- [ ] **AC4 专项**：连派两个相关 goal 给 researcher，断言第二个引用第一个上下文（同 session resume）。
- **验证**：观察日志全链路零人；`/company` 有产物；CEO inbox 收到 report。
- **覆盖 AC**：AC1（统一 loop）/ AC2（常驻）/ AC3（P2P 无中心 pump）/ AC4（context）/ AC5（同构）/ AC6（最简闭环）/ AC7（持久化，配合阶段 5 chown + `rm` 重建 resume 验证）。

## 全局回滚

- 任一阶段测试不绿 → 回退该阶段（ephemeral 路径 `broker.spawn`/`run_task`/`goal_pump`/`run_goal` 全程保留，可切回）。
- compose 层回滚：恢复旧 `docker-compose.yml`（仅 broker + ceo + ephemeral worker）。

## 最后一遍全量检查（交付前）

- [ ] `python -m pytest orchestration/ agent/ -q` 全绿（含新增、调整后的等价用例）。
- [ ] 中间态红线复核：未接 verifier 分权 / watchdog；`goal_pump`/`run_goal` 仅停用未删。
- [ ] 待回填项登记到父任务（compose 头注、orchestration-layer design §1、role-library 决策2、ceo-loop「CEO 专属 loop」描述）。
