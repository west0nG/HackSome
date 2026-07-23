# Implement: runtime role creation

依赖顺序：机制（1-3）→ 判断力（4）→ objective 迁移热身（5）→ 校验迁移（6）→ 真 LLM 实证（7-8）→ 开闸（9）。步骤 1-6 全程 dormant（CEO 无 create-role 入口），随时可弃。

## Step 1 — 共享状态与 compose 管线

- [x] `docker-compose.yml`：`x-agent` 增挂 `state/<company>/roles` → `/shared/roles`（rw）；新增 `provisioner` service（repo rw 同宿主路径 + docker.sock + state，照抄 broker 挂载法；镜像按 design §3 取最小改动方案）。
- [x] `Makefile`：`shared` 目标 session 目录预建改为 `agents/*.yaml` glob 驱动；`up`/`down` 在 `docker-compose.roles.yml` 存在时自动追加 `-f`。
- [x] 验证：`make up` 静态五角色行为与现状一致（override 不存在路径）；`docker compose config` 无告警。

**回滚点**：本步独立 commit，revert 即回到现状。

## Step 2 — `orchestration/role.py`（CLI）+ 单测

- [x] lint 模块（命名/保留字/yaml 双引用一致性/skills 存在性/mcp 凭证 `${VAR}` 硬不变式 + 新增 server env 缺失仅警告/charter+rationale 非空）——独立函数，供 CLI 与 provisioner 共用。v1 有意不做：headless grep、rationale 结构强制。
- [x] `propose`：bundle 读取 → lint → registry(proposed) → 评审请求 IME 直投 verifier inbox（不走 Hub goal 状态机）。
- [x] `verdict <name> PASS|FAIL --reason`：`AGENT_KEY==verifier` 身份门 → registry(passed/failed) + 结论 IME 回提案方；PASS 原子写 queue。
- [x] `list` / `status` / `retire`（queue retire 条目 + registry）。
- [x] 单测（无 LLM）：lint 全分支（含新增 server 警告不拦）、身份门（AGENT_KEY 缺失/错值=拒）、queue 原子性、propose→verdict 状态流转、重名/保留字拒绝、pending 语义（无 verdict 不产生 queue）。
- [x] 验证：`pytest orchestration/tests/test_role_cli.py -q` 绿。

## Step 3 — `orchestration/provisioner.py` + 单测

- [x] queue 轮询循环；`create`：复验 lint → 原子写 4 类文件（mcp.json 缺省拷全量集）→ mkdir+chmod session → 由 registry live 集生成 `docker-compose.roles.yml`（全展开模板）→ `compose up -d <name>` → git add（仅本次文件）+ commit → registry(live) + inbox 通知 ceo → queue 归档。`retire`：stop + 重生成 override。
- [x] **模板防漂移单测**：生成 service block 与主 compose `x-agent` 的 mounts/env 逐项比对。
- [x] 幂等单测：同一 queue 条目重放不重复写/不重复 commit；崩溃中断后重跑收敛。
- [x] 验证：`pytest orchestration/tests/test_provisioner.py -q` 绿；容器内 dry-run（mock docker/git）通过。

## Step 4 — 判断力：skills + charter 编辑（v1 简单版）

- [x] `agents/assets/skills/review-role/SKILL.md`：三条核心判断（差异化/非泛泛/理由可信）+ 防注入 ground rule + `role verdict` 逐字输出契约；frontmatter 自声明「NOT for the proposing agent」。**不写反规避/Gate 阵。**
- [x] `agents/verifier.yaml`：`skills:` 接入 review-role。
- [x] `agents/assets/verifier-charter.md`：评审席扩职段（rubric 提案方不可见；verdict 词表与 goal 验收同一套 PASS/FAIL；审自己的提案时从严）。
- [x] `agents/assets/skills/create-role/SKILL.md`：正向引导五段（岗位规格化/charter anatomy/三道检验自查/MCP+skills 取舍/组包提交+异步说明）；尾部来源+许可证注释。**不写防御性限制。**
- [x] 三道检验自查：新写 skill 每条子句可指认 ①/②/③。
- [x] `agents/assets/ceo-charter.md`：L48 名单 → `role list` 动态指引；"How you decide" 段点名 create-role。
- [x] ⚠️ 本步**不改** `agents/ceo.yaml` 的 `skills:`（开闸留到 Step 9）；ceo.yaml 隔离注释更新措辞。

## Step 5 — R7：objective propose 迁移（评审席热身 + 词表统一）

- [x] `orchestration/objective.py`：`propose` 改 staging（`/agents/<key>/objective.proposed.md`）+ 评审请求 IME；删除内联 `run_reviewer` 路径；新增 `verdict <role> PASS|FAIL`（身份门；PASS 走原 `_write_go` + 回消息）。
- [x] `review-objective/SKILL.md`：改 verifier skill，criteria 保留实质、判定映射到 PASS/FAIL，输出契约=执行 `objective verdict` 命令；接进 `agents/verifier.yaml`。
- [x] `set-objective/SKILL.md`：异步措辞 + 词表更换。
- [x] 全库 grep：GO/RESHAPE/DROP 无残留（代码/skill/charter/测试）。
- [x] 单测更新：objective 测试改走 propose→verdict 两段式；身份门用例；PASS 归档/原子写行为不变的回归用例。
- [x] 验证：`pytest orchestration/tests/ -q` 全绿。

**回滚点**：本步独立 commit，可单独 revert 回内联评审（与 role 机制解耦）。

## Step 6 — 确定性校验迁移

- [x] `agent/tests/test_mcp_assets.py`：静态 `ROLES` → `glob(agents/*.yaml)`；「全员 md5 相同」放宽为「凭证不变式恒查 + 无自定义时等于全量集」（MCP 允许分化）。
- [x] 验证：`pytest agent/tests/ -q` 全绿。

## Step 7 — AC2/AC7 真 LLM 评审实证（`make up` 环境，常驻 verifier）

- [x] AC7 先行：CEO 容器发一个 objective 提案 → verifier wake 审 → verdict 回流 → PASS 生效归档正确。
- [x] 构造两份角色提案 bundle：①平庸提案（占位 charter 密度 + 空洞理由）②合格提案（走完 create-role 全流程产出）。
- [x] `role propose` 各跑一次：① 应 FAIL，② 应 PASS。结果无论如何都是 v1 rubric 的第一份实验数据——①若 PASS 记录下来，回 Step 4 迭代 rubric（仍保持简单，只加被实验证明需要的条目）。
- [x] 产物（verdict 全文 + inbox 消息流）存 `research/ac2-evidence/`。
- [x] 顺带观察（评审门 F6 备查）：rubric 三条判断不触及 bundle 内 skills/ 与自定义 mcp.json 的实质内容；实证轮留意是否有水货借道 bundle skills 混入，有实例再按 SOP 阶段 3 补条目。

## Step 8 — AC3-AC5 e2e 全链路（真环境，不能跳）

- [x] 用 Step 7 的合格 bundle 走 propose→verifier PASS→provisioner 物化→容器起动。
- [x] 核验：4 文件落盘且 git commit 存在；`make down && make up` 后新角色容器仍在（AC3）；dispatch goal 经 Hub 路由、charter/skills/MCP/objective 全生效（AC4，观测信号照 journey：输出用 charter 语言 + strict-mcp 下工具调用成功）；`role retire` 停容器 + registry 事件（AC3 后半）；`role list` 含新角色（AC5）。
- [x] 判负前先自证测量（grep 的工具名/关键词先核对）。
- [x] e2e 产物与结论存 `research/e2e-evidence/`。

## Step 9 — 开闸

- [x] `agents/ceo.yaml` `skills:` 接入 `assets/skills/create-role`。
- [ ] 重启 ceo 容器（skills 物化是 startup-only）；观察一个真实 wake 周期无异常触发。（推迟：沙盒 e2e 未起 CEO 常驻循环，留到下次生产 make up）

**回滚点**：摘 ceo.yaml 一行 + `docker compose stop provisioner`；已建角色逐个 `role retire`；物化 commit 逐个 revert。

## Step 10 — 收尾

- [x] spec 更新：role 创建机制与不变式、统一评审席、统一 verdict 词表写入 `.trellis/spec/`（trellis-update-spec）。
- [x] 全量 `pytest -q` + 提交（多 session 纪律：只 add 本任务文件）。
- [x] memory 更新：orchestration protocol 条目（评审席=verifier、PASS/FAIL 统一、试用期砍掉、MCP 可新增）。
