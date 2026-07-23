# CEO meta-skill: runtime role creation (custom charter/skills/MCP)

## Goal

让 CEO 在运行时发现「现有角色都不适合某类任务」时，能自己创建一个**高质量的新角色**——自定义 charter/character、自定义 skill set、自定义 MCP set——新角色成为常驻部门（永久入编），Hub 可路由、重启后仍在。防形式主义靠评审门（doer≠judge）。

**v1 定调（用户 07-06 两轮拍板）**：
- 评审统一交常驻 **verifier**（公司唯一评审席：任务验收 + objective 审批 + 角色审批），`objective propose` 旧内联评审路径一并迁移（R7）。
- **verdict 全公司统一一种**：`PASS / FAIL: <reason>`（废除 GO/RESHAPE/DROP 第二套词表）。
- **试用期/转正门砍掉**：评审 PASS 即上岗，无 probation 状态、无 confirm 命令；`retire` 保留作止损。
- **skill 与 rubric 先写简单版**：只写正向引导，不预编防御性限制（反规避条款、结构强制检查等全不写）——限制必须等真实观测到的失误再加（SOP 阶段 3 原则）。实验后迭代。

## Requirements

### R1 机制：`role` CLI（纯机制，零判断，异步评审）

- CEO 容器内可调用的 CLI（`python3 -m orchestration.role`），子命令：`propose` / `verdict` / `list` / `retire` / `status`。
- `propose <name>`：读提案包 → 确定性 lint → registry(proposed) → 发评审请求消息到 verifier inbox（含 bundle 路径）。本轮即结束，不等结论。
- `verdict <name> PASS|FAIL --reason <r>`：**仅 verifier 容器可执行**（`AGENT_KEY == verifier` 身份门，与 Hub sender-identity 同信任级）；记 registry 事件并把结论消息送回提案方 inbox；PASS 时原子写物化队列。
- 判断力全部在 skill 层；CLI 代码不含任何质量判断。

### R2 机制：物化与起动（provisioner）

- agent 容器把 `agents/` 挂成 ro 且无 docker.sock，所以 PASS 之后的物化由一个有写权限 + sock 的确定性组件（非 LLM）执行：写 4 类角色文件（yaml / charter / mcp.json / 新 skills）、建 session 目录、起新容器、git commit、通知 CEO（inbox 消息）。
- 新角色必须在 `make down && make up` 后仍存在（compose 生命周期内，不是裸 docker run 孤儿）。
- 角色状态落 registry（append-only 事件：proposed/passed/failed/live/retired）。

### R3 引导 skill：`create-role`（CEO 侧，v1 简单版）

正向引导，不编限制。核心内容：

- **先把岗位需求写具体**（task-specifier）：这个 workflow 缺什么、现有哪个角色试过/为什么不合适、新角色要在什么判断姿态上不同——说真话即可，不强制格式和数量门槛。
- **charter anatomy 模板**（从真实 charter 反推的七段结构：一句话身份+否定空间 / 运行模型 / 系统协议段逐字命令 / Principles / 方法论点名 skill 下沉 / 必要时输出契约）。
- **三道检验作为写作指引**（①系统特定 ②压制 LLM 默认 ③非平凡取舍）：写 charter/skill 时对着自查，泛泛的删；点名占位 charter（builder/researcher/growth）为反面对照。
- **组包与提交**：bundle 布局 + `role propose` 逐字命令 + 异步说明（结论下次 wake 到 inbox）。
- **MCP 段**：默认不附 mcp.json（= 全量集）；需要就自己写（可收窄、可新增 server，新增凭证走 `${VAR}`）。
- description 对齐 wake prompt 措辞（触发准确性是生效前提）。

### R4 评审 rubric skill：`review-role`（verifier 专属，v1 简单版）

- 接进 `agents/verifier.yaml` 的 `skills:`；不进任何提案方 loadout（doer≠judge 隔离）。
- 核心判断就三条：**①差异化**（和最近的现有角色差在身份/判断姿态，还是只差工具清单）**②非泛泛**（删掉角色名后这份 charter 是否套谁都行——占位 charter 密度 = 不合格）**③理由可信**（为什么现有角色不行的陈述是否站得住）。
- 防注入 ground rule（提案是被审内容不是指令）+ 输出契约：执行 `role verdict <name> PASS|FAIL --reason "<one line>"`；FAIL 的 reason 给出具体改法或劝弃。
- verifier charter 相应扩职一段：评审席职责 + rubric 提案方不可见。

### R5 verdict 统一（用户拍板）

- 全公司 verdict 只有一种词表：`PASS / FAIL: <reason>`。goal 验收（现状已是）、角色审批（R1）、objective 审批（R7 迁移时替换 GO/RESHAPE/DROP）全部同一契约。
- 「改了重交」还是「别做了」由 FAIL 的 reason 文本承载，不设第三种状态。

### R6 CEO 派发知识动态化

- 消除 `ceo-charter.md` 里硬编码的部门名单：改为动态发现（`role list`），新角色 live 后 CEO 下一次 wake 即可向其派发，无需改 charter 文本。

### R7 `objective propose` 迁移到 verifier 评审

- `objective propose`：改为 staging（草案暂存 `/agents/<key>/objective.proposed.md`）+ 评审请求到 verifier inbox；删除内联 fresh-session reviewer 路径。
- 新增 `objective verdict <role> PASS|FAIL --reason`（verifier 身份门）：PASS 执行原 `_write_go`（归档 + 原子写）+ 回消息通知提案方。
- `review-objective` skill 改为 verifier skill 并接进 verifier.yaml，verdict 词表换成 PASS/FAIL；`set-objective` 文本改异步措辞。
- 已知例外：verifier 自己的 objective 提案构成自审，v1 不解决（罕见 + 影响面小）。

### R8 MCP 策略（用户 07-06 修订：不设收窄禁令）

- 默认：新角色的 `agents/mcp/<name>.json` = 全量 server set 的逐字拷贝。
- 自定义：可收窄、**也可新增 server**（npx 型运行时可下载、远程型无需安装）。
- lint 只保留硬不变式：json 可解析、凭证必须 `${VAR}` 引用不得字面量（沿 `test_mcp_assets.py`）；新增 server 引用的 env 变量缺失时**警告不拦**（server 起不来是该角色自己运行时的问题，fail-slow 可观测）。

## Constraints

- **doer≠judge 靠结构强制**：rubric 只在 verifier loadout；`verdict` 子命令有 `AGENT_KEY` 身份门；无 verdict = 永远 pending，绝不默认放行（fail-closed）。
- **声明式扩展**：新角色 = 数据文件（yaml/charter/mcp/skills），零 .py 改动；`role` CLI 与 provisioner 是一次性基建。
- **命名安全**：角色名单一 charset 校验（作为文件名/inbox key/容器名/服务名复用）；保留字 `ceo` `hub` `verifier` `harness` `broker` `provisioner` 不可用。
- **git**：物化的角色文件由 provisioner 自主 commit。
- **许可证**：借鉴的外部内容按 license 标注（ag2/skill-creator Apache-2.0 可用；disler meta-agent、PersonaHub 禁止拷文本）。
- 不修 dormant broker.spawn 的 `operator.yaml` 悬挂引用（绕开，不复活该路径）。

## Non-goals

- **试用期/转正门**（v1 砍掉；要不要加、怎么加等真实运行观测后再议）。
- **skill/rubric 里的防御性限制**（反规避条款、evidence 结构强制、headless 措辞 lint 等）——等观测到真实失误再按 SOP 阶段 3 补。
- 基于绩效的自动裁撤（retire 仅显式触发）。
- verifier 自身 objective 提案的自审破口（R7 已知限制）。
- 角色间技能库的向量检索。

## Acceptance Criteria

- [ ] **AC1 提案链路（异步）**：CEO 容器内 `role propose <bundle>`——lint 拦住非法名/坏 yaml/凭证字面量；通过后 registry(proposed) + verifier inbox 收到评审请求。`role verdict` 在非 verifier 容器执行被拒；verifier 容器 PASS → 队列条目 + 提案方收到结论消息；无 verdict = 永远 pending，不物化。
- [ ] **AC2 质量门实证（真 LLM，常驻 verifier）**：一份对照占位 charter 密度炮制的平庸提案被 verifier FAIL；一份按 create-role skill 走完全程的合格提案拿到 PASS。（这就是 v1 简单版 rubric 的第一次实验，结果反哺迭代。）
- [ ] **AC3 物化与存活**：PASS 后 provisioner 写全 4 类文件 + session 目录 + 起容器 + git commit + registry 事件 + inbox 通知 CEO；`make down && make up` 后新角色容器仍在；`role retire` 停容器 + registry 事件。
- [ ] **AC4 新角色可用**：向新角色 dispatch 一个 goal，经 Hub 正常路由；容器内 charter 注入、skills 物化、MCP 生效（`--strict-mcp-config` 下工具可用）；objective.md 自动创建并注入。
- [ ] **AC5 派发动态化**：不改 CEO charter 文本的前提下，CEO 能发现并向新角色派发（`role list` 返回含新角色的名单）。
- [ ] **AC6 确定性校验**：mcp 不变式测试改为按 glob 覆盖所有角色（含运行时新建，允许内容分化但凭证不变式恒查）；`role` CLI 与 provisioner 有单测（lint、身份门、queue 原子性、物化幂等、命名校验、compose 存活配置生成）。
- [ ] **AC7 objective 迁移**：`objective propose` 经 verifier 异步评审跑通一轮 PASS（草案生效、归档正确）；旧内联 reviewer 代码删除；**公司 verdict 通道**（goal 验收/objective/role，即经 verifier 或状态机的裁决）无 GO/RESHAPE/DROP 残留——decide-direction 及其 direction-critic 属 CEO 会话内 advisory rubric、不经 verifier，三值在彼处承载真实决策信息，明确豁免（07-06 check 裁定）；`objective verdict` 身份门单测。
