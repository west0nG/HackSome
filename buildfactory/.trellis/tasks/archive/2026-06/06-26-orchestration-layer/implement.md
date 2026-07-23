# Orchestration Layer — Implement

> 执行计划。当前做 **增量 1**：goal ledger + 状态机（纯 python、可单测、不依赖 docker）。增量 2/3（真实 broker 接入 / DooD）后续。
> 设计见 `design.md` 第 11–12 节。**原则**：死规矩外壳先写实、最小、可测；LLM 侧字段不碰。参照 `company_state_kit/company.py` 的 `flock` 用法、`agent/tests/` 的测试风格。

## 增量 1 检查单

1. [ ] `orchestration/goal_ledger.py`
   - goal/run 记录（见 design §12）；每 goal 一个 JSON 文件 `<ledger>/<id>.json`。
   - ledger 根 = env `GOAL_LEDGER`，默认 `<repo>/orchestration/ledger`（**不在 company folder**）。
   - `fcntl.flock` 做原子 claim（参照 `company_state_kit/company.py` 的 `_nav_lock`）。
2. [ ] 状态机 + 转换 API（每个带合法性校验，非法转换抛 `ValueError`）：
   `add_goal / claim_open_goal / start_run / finish_run / to_reported / to_verifying / pass_verify / fail_verify / kill / should_kill`。
   状态：`open→claimed→running→reported→verifying→done|killed`；验不过→回 `running`。
3. [ ] `orchestration/goal_loop.py`：`run_goal(ledger, goal_id, execute_fn, verify_fn, max_attempts=3)`，execute/verify 为注入 seam。
4. [ ] `orchestration/tests/test_goal_ledger.py` + `test_goal_loop.py`（建 `orchestration/tests/__init__.py` 若需要；测试用 `tmp_path`）：
   - 原子 claim（并发/重复 claim 只一个成功）。
   - 全程状态机 claim→run→report→verify 过→done。
   - 失败回路：verify 连不过→回 running、attempts 累加→N 次后 watchdog `kill`。
   - 非法转换抛错。
5. [ ] 不依赖 docker、不真起容器。
6. [ ] `orchestration/ledger/` 加进 `.gitignore`（运行时产物）。

## 验收（增量 1）

- `.venv-cua/bin/python -m pytest orchestration/tests/ -q` 全绿；状态机 / 原子 claim / 看门狗 三类用例都覆盖。
- goal 记录字段 = `id/parent/intent/status` + 运行时簿记（attempts/feedback/runs/时间戳）；**无 `result`、无 `verify_kind`**。

## 验证命令

```
.venv-cua/bin/python -m pytest orchestration/tests/ -q
```

## 增量 2 检查单（接真实执行 + 验收 agent）

> 设计见 `design.md` §13。**先把可单测的纯逻辑做扎实；真实容器 e2e 烧 token，gated、不在单测里跑。**

1. [ ] `orchestration/goal_runtime.py`：
   - `build_task(intent, feedback) -> str`（纯函数）。
   - `parse_verdict(text) -> (passed, feedback)`（纯函数）：抓最后一行 `VERDICT: PASS` / `VERDICT: FAIL: <reason>`；抓不到→FAIL。
   - `make_execute_fn(op_id, company_id, spec=None)` / `make_verify_fn(op_id, company_id, spec=None)`：包 `broker.spawn`（不同 op_id），返回 `(ok, summary)` / `(passed, feedback)`；用完 `teardown`。
   - `run_goal_e2e(intent, company_id)`：add_goal→claim→`run_goal`→打印终态（gated：需 docker+image+token）。
2. [ ] 验收 agent：复用 company-enabled operator spec + 验收 prompt（强制最后一行 `VERDICT: ...`）；必要时加薄 `agents/verifier.yaml`。零人。
3. [ ] `orchestration/tests/test_goal_runtime.py`：
   - `build_task`（有/无 feedback）、`parse_verdict`（PASS / FAIL: reason / 无 verdict 三情形）单测。
   - `make_execute_fn` / `make_verify_fn` 用 **fake spawn**（monkeypatch `broker.spawn`/`teardown`）验证不起真容器、verdict 正确解析、teardown 被调用。
4. [ ] `broker.py` 尽量不改（只读用）；若必须改，最小化。
5. [ ] `.venv-cua/bin/python -m pytest orchestration/tests/ -q` 全绿；**不烧 token、不起容器**。

## 验收（增量 2）

- 纯函数 + adapter（fake spawn）单测全绿；`parse_verdict` 三情形覆盖。
- 真实 e2e（`run_goal_e2e`）入口存在、可手动跑（环境就绪时）；不在自动测试里跑。

## 增量 3 检查单（DooD：broker 进容器）

> 设计见 `design.md` §14。**关键 = 路径一致技巧（宿主仓库挂到容器内同一绝对路径），broker.py 不改。**

1. [ ] `orchestration/Dockerfile.broker`：python3 + docker CLI **client** + 仓库 python 依赖（按 `agent/`、`orchestration/` 实际 import 装，至少 pyyaml）。代码挂载、不 COPY。
2. [ ] `docker-compose.yml`（仓库根）：service `broker` —— 挂 `/var/run/docker.sock` + `${PWD}:${PWD}`（同路径）、`working_dir: ${PWD}`、env `CLAUDE_CODE_OAUTH_TOKEN`（来自 `vm/.env.local`）+ `FOUNDAGENT_HOST_REPO=${PWD}`、`command: sleep infinity`。
3. [ ] 一键说明：README/Makefile 一行 `docker compose up -d`。
4. [ ] `broker.py` 尽量不改（路径一致技巧让它无需改）；若必须改，最小化。
5. [ ] **便宜验证（不烧 token）**：build 镜像 → `docker compose up -d` → `docker compose exec broker docker run --rm hello-world`（兄弟容器通）→ `docker compose exec broker python -c "import orchestration.broker; print('ok')"`（依赖通）→ 宿主 `docker ps` 确认 broker 与 agent 容器**平级、非嵌套**。
6. [ ] **不跑付费 cua-agent e2e**（主 session 处理）。

## 验收（增量 3）

- broker 容器内能起兄弟容器（hello-world 证明 socket+CLI+DooD 通）；仓库代码+依赖在容器内可 import。
- 宿主近空：一句 `docker compose up -d` 起控制平面。**AC4 达成。**
