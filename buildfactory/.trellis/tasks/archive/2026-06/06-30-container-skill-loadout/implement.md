# Implement — Container skill materialization

> 配套 `prd.md` / `design.md`。实现已完成于 commit `b8c7f8c`；本清单为如实执行记录 + 验证。

## 执行清单（全部已完成）

- [x] 1. 新增 `agent/resident_loadout.py`：`materialize_for` + `main()`（env 调用时读、
  best-effort、PyYAML 惰性 import）。
- [x] 2. `vm/docker/agent_startup.sh`：`exec agent_loop` 前插 `python3 -m agent.resident_loadout`。
- [x] 3. `docker-compose.yml` x-agent 锚点：加 `./agent`、`./agents`、
  `./company_state_kit:/opt/foundagent-orch/company_state_kit` 三个 mount。
- [x] 4. `vm/docker/Dockerfile.agent`：pip 加 `pyyaml`。
- [x] 5. 新增 `agent/tests/test_resident_loadout.py`：per-role 映射 4 例 + best-effort 3 例。

## 验证（已跑）

- [x] 宿主端到端：对 5 个角色各 materialize 进 tmp claude_home，肉眼核对 skills/ + settings.json
  → 全对（ceo=send-goal；researcher/builder/growth=company-state+receive-goal；
  builder/growth 有 Stop hook；verifier=company-state）。
- [x] 单测：`pytest agent/tests/test_resident_loadout.py` → 7 passed。
- [x] 全套：`pytest orchestration/tests agent/tests` → **154 passed**。
- [x] compose 语法：`docker compose config -q` → OK。

## 待真机冒烟（AC6，交付后）

- [ ] `make up`（需 docker + `vm/.env.local` 的 `CLAUDE_CODE_OAUTH_TOKEN`）。
- [ ] `make logs-ceo` 见 `[resident_loadout] ceo: skills=['send-goal'] ...`。
- [ ] `docker compose exec ceo ls ~/.claude/skills` 见 `send-goal/`。

## 回滚点

- 单 commit `b8c7f8c`；`git revert b8c7f8c` 即回 charter-only。compose mount / Dockerfile
  改动均为纯增量，revert 不影响其它服务。

## 风险

- 镜像需重建（`docker compose build` 拉 pyyaml）；`make up` 已带 `--build`。
- AC6 未在本机闭环——若真机日志未见 `[resident_loadout]` 行或容器内无 skill 落盘，
  优先查：①`agent/` 是否挂进 `/opt/foundagent-orch/agent`；②PYTHONPATH 是否含
  `/opt/foundagent-orch`；③镜像是否真带 pyyaml（`docker compose exec ceo python3 -c "import yaml"`）。
