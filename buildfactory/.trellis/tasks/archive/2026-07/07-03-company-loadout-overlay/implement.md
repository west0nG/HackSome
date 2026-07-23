# Implement: 公司级 Loadout Overlay

前置依赖：`07-03-state-dir-consolidation` 的挂载重排。M1–M3 为纯代码 + 单测，可先行；M4（compose/Makefile 接线）必须踩其落地后的最终布局。

## M1 — overlay 解析核心

- [ ] 新增 `agent/overlay.py`：`load` / `role_view` / `apply_to_spec` / `effective_charter` / `effective_mcp` / `effective_adapters` + warnings 上传（见 design「模块」节）
- [ ] 新增 `agent/tests/test_overlay.py`：缺省=基线、空文件/无文件、defaults+role 合成与覆盖优先级、skills off、skills on 超基线（全局池解析 + 解析不到 WARN）、charter/mcp 三态、坏 YAML、未知键/角色/取值、version 不符

验证：`pytest agent/tests/test_overlay.py`

## M2 — materialize reconcile

- [ ] `agent/loadout.py`：`.loadout-manifest.json` 记账；启动时删除「上次有、本次无」的 skill 目录；hooks off / snippet 指纹变化时按上次 snippet 逐值移除 settings.json 条目；清单缺失 = 空清单（只加不删）
- [ ] `agent/resident_loadout.py`：接入 `AGENT_LOADOUT` env → load → apply_to_spec → materialize；失败路径保持 log + exit 0
- [ ] 单测：on→off 残留清除、手装 skill（不在清单）不动、hooks off 保留 agent 自加键、指纹变化重合、幂等重跑

验证：`pytest agent/tests/`

## M3 — agent_loop / peripheral / loadout-check

- [ ] `orchestration/agent_loop.py::main`：overlay → charter off/替换、mcp off/替换；更新 line 29 注释；`build_claude_argv` 不动
- [ ] `peripheral/runner.py::_registry`：`effective_adapters` 过滤；空白名单合法；单测（含未知 adapter WARN）
- [ ] 新增 `agent/loadout_check.py` + Makefile `loadout-check` target；单测覆盖每类错误与退出码

验证：`pytest agent/ orchestration/ peripheral/`（全绿，含既有测试零回归）

> review gate：M1–M3 完成后跑一次 trellis-check，确认无 overlay 路径下五角色现有 loadout 测试逐项不变，再进 M4。

## M4 — compose / Makefile 接线（等 state-dir 落地）

- [ ] `make shared`：预创建 `state/$(COMPANY)/config/`
- [ ] `docker-compose.yml`：x-agent + peripheral 加 `config/` 只读挂载与 `AGENT_LOADOUT` env
- [ ] 手工验证 A：无 overlay 起栈，`make logs` 无 WARN，行为同现状
- [ ] 手工验证 B：放入 AC「组合生效」那份 overlay，逐项核对容器内 skills 目录 / settings.json / argv 日志 / peripheral sources

回滚点：M4 独立 commit，revert 即回到纯代码状态（M1–M3 无 overlay 文件时行为零变化，可安全留在 main）。

## M5 — e2e 验收 + spec 沉淀

- [ ] PRD 验收标准逐条走一遍（含双公司隔离：foundagent 与 e2e-dood 各挂不同 overlay 互不影响）
- [ ] `.trellis/spec/backend/` 新增 loadout-overlay 契约文档（schema、reconcile 记账规则、容错口径）
- [ ] `aiworkforce/SOP-adding-roles-and-skills.md` 增补：「测试能力组合用公司 overlay，不改 role YAML 基线」
- [ ] review gate：交用户验收后再 finish
