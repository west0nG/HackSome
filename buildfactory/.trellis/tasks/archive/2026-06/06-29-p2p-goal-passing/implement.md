# 执行计划 — 聪明中枢 Hub（child②）

> 设计见 `design.md`（章节号下引），需求见 `prd.md`。测试用 pytest（项目环境提供；裸 `python3` 未装）。
> 增量式：每步先纯函数/单测后副作用，自包含可独立回滚。旧 `goal_pump`/`run_goal` 全程保留可回退。

## Step 0 — 基线
- [ ] `python -m pytest orchestration/ agent/ -q` → 记下当前全绿基线（child① 后应绿）。
- **回滚锚点**：`git rev-parse HEAD` 记下。

## Step 1 — ledger 扩展（纯，design §4）
- [ ] `orchestration/goal_ledger.py`：新增 `VERIFYING` 状态；`add_goal` 落 `caller`/`target`/`deadline` 字段；新增 `start_verify`（REPORTED→VERIFYING）；`pass_verify` 改签 VERIFYING→DONE；`fail_verify` 改签 VERIFYING→RUNNING/KILLED；新增 `time_out(goal_id, max_attempts)`（RUNNING/VERIFYING→retry/KILLED）。保留 `_require` 守卫 + flock。
- [ ] 迁移 `test_goal_ledger.py` / `test_ledger_notify.py` 到新转移（等价语义，AC7）。
- **验证**：`pytest orchestration/tests/test_goal_ledger.py orchestration/tests/test_ledger_notify.py -q` 绿。
- **回滚**：`git checkout orchestration/goal_ledger.py orchestration/tests/test_goal_ledger.py orchestration/tests/test_ledger_notify.py`。

## Step 2 — Hub handler（纯逻辑，design §3+§4）
- [ ] 新建 `orchestration/hub.py`：`parse_body`（`DISPATCH`/`REPORT`/`VERDICT` 前缀 → 结构；解析失败 fail-loud，不静默丢）；`hub_handler(events, ledger, inbox)` 纯映射「事件 → ledger 转移 + 第二跳 IME」；复用 `goal_runtime.parse_verdict`。
- [ ] 新建 `test_hub_handler.py`：mock ledger/inbox，断言每类事件的转移 + 转投 IME（含解析失败分支）。
- **验证**：`pytest orchestration/tests/test_hub_handler.py -q` 绿。
- **回滚**：删 `orchestration/hub.py` + `test_hub_handler.py`（新文件，零影响面）。

## Step 3 — 循环骨架 + 投递回改 + inbox ack（design §1、§3、§7）
- [ ] `orchestration/agent_loop.py`：抽出共享循环骨架 `poll → handler → sleep`；LLM handler = 现有 `build_wake_prompt`+`wake`+`save_session`，不改语义。
- [ ] `orchestration/hub.py`：`hub_loop` = 循环骨架 + `hub_handler`（handler 为确定性 Python，不 spawn）。
- [ ] `orchestration/messaging.py`：`send`/`report` 第一跳改投 `HUB_KEY`，真实 `to`/`reply_to`/`goal_id` 写进 IME `body`（保持 5-field）。
- [ ] `orchestration/inbox.py`：给 Hub 消费侧加**非推进读 + 显式 `ack`**（`poll_one` 现即读即进 → 改为处理后 ack 推进 cursor）。
- [ ] 迁移 `test_messaging.py`（断言改投 hub 后 IME 形态/路由）；`test_inbox.py` 加 ack 往返用例；`test_agent_loop.py` 调整为共享骨架的等价用例。
- **验证**：`pytest orchestration/tests/test_messaging.py orchestration/tests/test_inbox.py orchestration/tests/test_agent_loop.py -q` 绿。
- **回滚**：逐文件 `git checkout`（messaging 回直投、inbox 去 ack、agent_loop 回原循环）。

## Step 4 — watchdog + reconciliation（design §6、§7）
- [ ] `orchestration/hub.py`：`sweep`（每 tick `list_goals` 扫非终态，`now>deadline` → `time_out`）；`reconcile`（启动/每 tick 对非终态 goal 从 `status` 推下一步、用确定性 id `goal_id:status:attempts` 幂等重发）。挂进 `hub_loop` 的每个 tick（含空转 heartbeat）。
- [ ] 新建 `test_hub_sweep.py`（超时→重投/kill）、`test_hub_reconcile.py`（重发 id 被 `.seen`/`_require` 双重幂等吸收、不重复执行）。
- **验证**：`pytest orchestration/tests/test_hub_sweep.py orchestration/tests/test_hub_reconcile.py -q` 绿。
- **回滚**：sweep/reconcile 是 `hub.py` 内独立函数，从 `hub_loop` 摘除即可。

## Step 5 — compose 接 Hub + 全回归（review gate）
- [ ] `docker-compose.yml`：加第 6 常驻 service `hub`（同镜像 `foundagent/cua-agent:latest`，entrypoint 跑 `hub_loop`，**无 spawn / 无 docker.sock**，挂 inbox + ledger 卷）。
- [ ] `goal_pump`/`run_goal`/`goal_runtime` 相关测试标停用路径（保留不删）。
- **验证**：`python -m pytest orchestration/ agent/ -q` 全绿（含迁移 + 新增）；项目 lint / type-check。
- **Review gate**：跑 `code-reviewer` agent 审本任务 diff（聚焦 doer≠judge 物理隔离、ledger 幂等、dual-write 兜底）。
- **回滚**：注释 compose `hub` service，重新激活旧 `goal_pump` 路径。

## Step 6 — gated e2e（PAID，手动，不入 CI）
- [ ] `make up`（6 常驻含 hub）→ 给 CEO 注入 directive → CEO `send researcher` → researcher 干活写 `/company` → 经 hub 验收 → done 通知回 CEO。
- [ ] FAIL 重投续 context（断言第二次带 feedback）；`max_attempts=3` 耗尽 `kill`。
- [ ] **故障注入**：转 VERIFYING 后、投验收请求前 `kill hub` → 重启后 reconcile 正确补投验收（AC5）。
- **回滚**：e2e 只读不改产线代码；失败则回到 Step 5 修复。

## 完成后（Phase 3）
- [ ] spec 回填：父任务 AC-P3 / `goal_pump 退役`表述；child① spec `resident-agent-contracts.md`「no central pump」节注明业务经 Hub（design §8）。
- [ ] 处理继承待办 m3（首轮 wake 失败仍存 sid，fail-loud）、n1（wake prompt 文案）。
- [ ] 按 AC1–AC7 逐条核对后提交。
