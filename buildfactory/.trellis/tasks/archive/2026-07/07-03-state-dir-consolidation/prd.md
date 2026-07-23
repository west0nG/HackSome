# PRD: 宿主机运行时状态按公司隔离集中到 state/<company>/ + agent 会话持久化

## 背景

宿主机上的可变运行时状态目前散在三处：`companies/`（repo 根）、`orchestration/ledger/`、`orchestration/inbox/`（混在编排层代码目录里），且 ledger/inbox 是全局共享的、不区分公司。同时 agent 的 LLM 会话（`~/.claude` transcript + session_id 指针）只存在容器内部文件系统，容器重建（`make up` / `compose down`）即失忆。

目标形态：**`state/<company>/` 一个文件夹 = 一个公司的全部可变状态**，公司之间完全隔离；备份/迁移/删除一个公司 = 操作这一个文件夹；容器重建后 agent 对话可通过 `--resume` 恢复。

## 需求

1. 新建 gitignored 顶层 `state/` 目录，**按公司隔离**，每个公司一个自包含子目录：
   - `state/<company>/company/` — company wiki（原 `companies/<company>/`，挂到容器 `/company`）
   - `state/<company>/ledger/` — 该公司的 goal ledger（挂到 `/shared/ledger`）
   - `state/<company>/inbox/` — 该公司的消息 inbox（挂到 `/shared/inbox`）
   - `state/<company>/sessions/<role>/` — 该公司每个常驻 agent 的 Claude home（sessions 根整体挂到容器 `/sessions`，各服务用 `CLAUDE_CONFIG_DIR=/sessions/<role>` 选定自己的子目录；compose 的 YAML anchor 列表无法按服务追加，故不用 per-role 挂载点）
2. **一套 compose 栈 = 一个公司**：所有挂载源由单一 env（`COMPANY`，默认 `foundagent`，取代现 `PUMP_COMPANY`）推导；不同公司之间不共享任何宿主目录。同时跑多个公司 = 多个 compose project（`COMPANY=acme docker compose -p acme up`），本次不做多栈管理工具。
3. 容器内路径（`/company`、`/shared/ledger`、`/shared/inbox`）保持不变——只改挂载源，业务代码逻辑零改动。
4. session_id 指针文件（`AGENT_SESSION_FILE`）移入被挂载的 Claude home 内，随宿主目录持久化。
5. 宿主机直跑的兜底默认路径（`DEFAULT_LEDGER`/`DEFAULT_INBOX`/broker 的公司根）与新布局一致，并尊重 `COMPANY` env。
6. 迁移现有数据，不丢任何现存 goal/消息/公司文档：现 ledger/inbox 数据归属 foundagent（compose 默认公司）；其余公司（acme、e2e-*）只迁 wiki，运行时目录按需创建。
7. `.gitignore` 中三条散落的排除规则收敛为一条 `state/`。

## 约束

- **隔离的结构边界**：company wiki 根有导航不变式（INV1-3，nav==disk 自动 reconcile），ledger/inbox/sessions 必须是 wiki 根的兄弟目录（`state/<company>/` 下平铺），不能放进 `company/` 里。
- `vm/.env.local`（凭证）与 `vm/data/`（休眠 broker 路径的遗留物）不在本次范围内；broker 是 dormant 路径，仅同步其公司路径解析（`state/<id>/company`），不动其 claude_home 布局。
- `state/sessions/` 挂载与启动时 `resident_loadout` 物化的兼容性已核实：`materialize` 幂等、只覆盖单个 skill 子目录，不清空 `~/.claude`，transcripts 安全。
- 权限沿用现有方案：`make shared` 按 `COMPANY` 预创建并 `chmod 777`。

## 验收标准

- [x] `docker-compose.yml` 中所有可变状态挂载源均位于 `./state/${COMPANY:-foundagent}/` 之下；容器内挂载点不变；不存在跨公司共享的可变挂载。（`docker compose config` 核验）
- [x] `make up` 后五个 agent + hub + peripheral 正常启动，hub 心跳正常，CEO wake 正常。
- [x] 隔离验证：`COMPANY=e2e-dood -p e2e-dood` 起第二套 project（hub），`docker inspect` 确认两 hub 的 `/shared/ledger` 分别映射到 `state/e2e-dood/ledger` 与 `state/foundagent/ledger`；e2e-dood 容器内写入探针只出现在自己目录。实施中发现并修复：`container_name` 原写死 `foundagent-*` 导致第二 project 名字冲突，已参数化为 `${COMPANY:-foundagent}-*`（默认栈名不变）。
- [x] 宿主机 `pytest`（orchestration + company_state_kit + agent + peripheral）191 全绿；`DEFAULT_LEDGER`/`DEFAULT_INBOX`/broker `STATE_ROOT` 指向 `state/` 新路径。
- [x] 既有数据迁移后可读：6 个 goal JSON 全部可解析，inbox JSONL/cursor/seen 完整，4 家公司 wiki 迁至 `state/<id>/company`，容器内 `company.py read` 正常。
- [x] 会话持久化生效：`make down && make up` 容器销毁重建后，CEO 以同一 session id 启动并 `--resume` 成功——重建后的会话中能看到重建前的消息（agent 回复 RESUMED-OK）。
- [x] 旧的 `companies/`、`orchestration/ledger/`、`orchestration/inbox/`、`PUMP_COMPANY` 引用 grep 干净（代码/compose/Makefile/spec 均已更新）。
