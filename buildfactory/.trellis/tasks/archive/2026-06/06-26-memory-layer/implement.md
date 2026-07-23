# Memory Layer — Implement / 执行计划

按顺序执行，每步带验证 + 回滚点；两个 review gate 处停下来给用户过目。

## S1. `company.py` 核心 + 单测  —— [Review Gate A]

- `company.py` 通过 `--root` / `COMPANY_ROOT` 指向「某个 company 的根」，所有操作限定其内（多公司由启动方选 root）。
- 实现 storage 布局工具 + 命令：`read` / `tree` / `write`（`--content` / `--file`，in-place + 导航自动维护 + `flock`） / `record`（应用变更 + 运行时标记，`--nothing` 允许记空） / cold-start 处理 / 路径安全。
- 导航维护抽成内部 `_apply_write`，被 `write` 与 `record` 共用；nav = front-matter 机器源 + 渲染体 + 磁盘 reconcile。
- 写 pytest 覆盖 **AC1 / AC2 / AC3 / AC4 / AC6 / AC7 / AC8**。
- **验证**：`python3 -m pytest company_state_kit/tests -q` 全绿。
- **回滚**：纯新增，删 `company_state_kit/` 即回滚。
- **Gate A**：核心契约 + 测试结果给用户过目，再继续。

## S2. `company-state` skill

- 写 `SKILL.md`：开局 read、期间 write（含 `--file` 存资产）、收尾必 `record`（无新增就记空）、按主题不按部门、写当前态不写流水、导航别手改。
- **验证**：skill 文本 review；可选 materialize 到临时 claude_home 验证落地无误。

## S3. Stop hook + 接线 + 测试（AC5）

- 写 hook 脚本：读运行时标记，**调过即放行（含记空）**、**完全没调** 才 `block` + `reason`；留降级分支。
- 写 `settings.snippet.json` 片段（合并进 agent 的 `.claude/settings.json`）。
- **验证**：脚本级测试模拟 Stop 三种情形（没调 / 记空 / 有内容）。

## S4. 挂载接入 + 启用记忆的 agent yaml + 端到端  —— [Review Gate B]

- broker / agent 层：把**选定的** `companies/<id>/`（rw）挂到 `/company`、`company_state_kit/`（ro）挂到 `/opt/company_state_kit`，设 `COMPANY_ROOT=/company`（参考 `orchestration/broker.py` 现有 `accounts/<id>/workspace` 挂载段）。
- 新增 `agents/<name>.yaml`（`skills: [company-state]`、`hooks:` 指向 stop hook）。
- **端到端**：容器内跑该 agent 一个 session，验证冷启动建 `MAP`/主题（AC1）、另起 session 能读到（AC6）。
- **回滚**：mount / yaml 为加法，移除即回滚。
- **Gate B**：端到端结果给用户过目。

## S5. spec 落档

- 在 `.trellis/spec/backend/` 加 `company-state` 契约文档（`company.py` 命令契约 + 不变式 + 多公司根 + 挂载约定），声明「供编排层复用」，与 `agent-execution-contracts.md` 同级。

## 验证命令

- 单测：`python3 -m pytest company_state_kit/tests -q`
- 端到端：在容器内按 broker 的跑法启动 memory-enabled agent，人工核对 `company/` 产出。

## Review Gates

- **Gate A**（S1 后）：核心命令契约 + 单测。
- **Gate B**（S4 后）：容器内端到端。

## Rollback

- 全部为新增：`companies/`（数据，gitignored）、`company_state_kit/`（工具 + 测试）、`company-state` skill、stop hook、新 agent yaml、broker mount 片段——逐步可回退，不动既有 VM/Agent/编排层代码路径。
