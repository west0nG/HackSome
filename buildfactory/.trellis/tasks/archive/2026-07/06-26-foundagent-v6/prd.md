# Foundagent v6

> 父任务（Parent Task）。本任务持有整体愿景、模块划分与跨子任务的验收标准；具体实现拆到 4 个子任务里逐个推进。
> 状态：规划中（Phase 1 Brainstorm）。本文档随 brainstorm 持续更新。

## Goal（目标）

让一个 Agent 拥有自己的虚拟机，在其中**不间断地像 Founder 一样自主运营一门真实的 business，并最终通过运营该 business 赚钱**。

**核心定位：零人公司（Zero-Person Company）。** Foundagent 不是「帮人类干活的工具（human-in-the-loop / 副驾驶）」，而是一个能**自己建立并运营公司**的实体。CEO Agent 完全自主：**人类唯一的职责是在启动时把所有账号（及必要的身份 / 资金基建）准备好，此后一切——选题、决策、build、获客、变现、止损——全部由 Agent 自主完成，人类零介入。**

v6 四层模块全部都要，但**一个一个搭**。（provenance：`main` 已重置为干净起点；旧版代号 Solvo，canonical ref = `origin/v5`，仅作历史记录、不作 v6 设计依据。）

## Background（背景）

- 北极星（按优先级）：① **真正跑通「自主运营 business → 赚钱」闭环**；② **架构清晰 / 易维护扩展**；③ **基础设施更可靠**（VM / 静态IP防封 / 账号注入更坚固）。
  - 注：用户未把「7×24 长期不间断运行」列为首要痛点 —— 长跑稳定性是加分项而非北极星。
- 后台调研：基础设施选型调研（云端 sandbox / Computer Use / 防封 / 本地 VM / 编排 / 账号注入）**进行中**。

## 基础设施研究结论（详见 `research/infra-research.md`）

关键结论：
1. **无万能产品，分层组装**：桌面 Computer Use + 强 stealth 浏览器 + 独享静态 ISP IP + Secrets Vault + Claude 编排内核，5 层正交选型。
2. **每身份固定静态 IP = 养号命脉**：托管浏览器云的「轮换住宅代理」对绑定身份**有害**；正解用独享 ISP IP（Decodo ~$2.5/IP、IPRoyal ~$1.8/IP），每身份一个。
3. **⚠️ 凭证现实**：订阅 token 程序化套利 2026-06 已被官方关闭（程序化用量先扣 Agent SDK credits 再按 API 计费；setup-token 一年期、不自动刷新）。**生产主力 = API key；订阅 token 仅用于有界可控负载。** 双凭证仍可（Claude Code 底层可切 API/订阅）。
4. **登录态跨会话持久化是命脉**（持久 profile / 快照固化 / Anon 服务端注入），不可每次重登（触发风控）。
5. **新选项 Claude Managed Agents（2026-04 公测）**：官方整合「编排 + 持久 pause/resume 会话 + per-session 自托管沙箱 + 出网自控」；唯一硬伤 = 仅 API key、$0.08/session-hour。

两套候选栈：
- **栈 A 云端优先**（最省运维、最快起步）：Claude Managed Agents + E2B Desktop/Scrapybara + Kernel/Browser Use + Decodo ISP + AgentMail/Infisical/Stripe Issuing/Anon。≈$58/mo 运行时 + token。
- **栈 B 自托管**（规模化最省、每身份固定 IP、无锁定）：Claude Agent SDK + QEMU/KVM 或 cua/Lume + Bytebot + Browser Use/Steel 自托管 + Decodo/IPRoyal ISP + AdsPower + 自托管 Infisical + Anon。VM≈电费 + IP $1.8-2.5 + token；代价 = 自建运维。

## 四层模块（Module Map → 子任务）

1. **虚拟机层（VM）** — 每个 Agent session 一台独立 VM：支持 Computer Use + 浏览器/Playwright；注入大量账号（专属账号、邮箱、外部服务）；静态 IP + 防封；本地/云端皆可部署。
2. **Agent 层** — 底座 Claude Code；多 Provider（Claude Code / Codex / OpenCode）；同时支持 API 与 subscription/OAuth token；外挂 Skill / Hook / Prompt 让 Agent 自主处理任务。
3. **编排层（Orchestration）** — 主 Agent（CEO Agent）分配任务、传递数据、回收子 Agent 结果。具体实现待定（见 Q1e）。
4. **公司记忆层（Memory）** — 文件系统实现，具备**渐进式披露**特性；含 Wiki 文件夹 + assets 大文件夹；每层文件夹渐进式披露以防 Agent 信息过载。

**子任务（自底向上顺序，已创建）：**
1. `.trellis/tasks/06-26-vm-layer` — VM 层（**当前进行中**，先做最小可运行版）
2. `.trellis/tasks/06-26-agent-layer` — Agent 层
3. `.trellis/tasks/06-26-memory-layer` — 记忆层
4. `.trellis/tasks/06-26-orchestration-layer` — 编排层

> 每个子任务独立可规划/实现/验收；父任务负责整体集成与跨层验收。依赖与排序写在各子任务的 prd/implement，不靠树结构隐含。

## 已确认事实 / 决策（Confirmed）

- 四层模块全部要做；采用「父任务 + 4 子任务」结构，逐个搭建。
- 底层 Agent 框架以 Claude Code 为主，需支持多 Provider 与 API/订阅双 token。
- 记忆层用文件系统 + 渐进式披露，结构含 Wiki 与 assets。
- **完全自主 / 零人公司**：CEO Agent 完全自主运营；人类介入边界 = 仅在启动时提供账号（及待定的身份/资金基建），此后零介入。这是用户长期坚持的核心信念。
- **部署形态 = 栈 B 自托管**（已确认）：Claude Agent SDK 为编排内核；QEMU/KVM 或 cua/Lume 为 VM；Bytebot 为桌面 payload；Browser Use/Steel 自托管为 web 层；Decodo/IPRoyal 独享 ISP + AdsPower 为防封；自托管 Infisical + Anon + Stripe Issuing 为账号/资金注入。生产用 API key，订阅 token 走有界负载。
- **编排方向**（细节待编排子任务 design）：非 Claude broker 起多个隔离容器、每 agent 一容器自跑 `claude -p`；「CEO → 部门 → 执行者」的具体协议（**设 Goal + 派任务**、结果回收、验收）在编排子任务定，通信形式是**设目标派任务、非 P2P**。
- **本期优先级 = 先搭骨架 / 基础设施**（用户明确）：四层骨架先立起来，再做上层 skill/hook 逻辑（含自主判断力）。
- **四层为全新设计**：编排层等按 v6 自身目标重做，不受任何历史版本约束。
- 自主判断力（北极星①关键）定位：骨架就绪后，通过 **skill + hook** 实现，核心难点是「让 agent 真正遵循 skill 做出有效行动」。本期不深入。
- **VM 方法论（用户经验）**：先搭**最小可运行 VM** 跑起来 → 运行中观察 agent 在哪卡住 → 按需注册账号。**初版不配全账号**；账号注入做成**可扩展接口**（按需加账号），「账号可扩展性」是 VM 层核心设计目标。

## Requirements（需求，初稿，待细化）

- R1 VM：可为单个 Agent session 提供隔离 VM，具备 Computer Use、浏览器自动化、静态 IP/防封、账号注入；支持本地与云端两种部署。**初版先做最小可运行 VM；账号注入采用可扩展接口、测试驱动按需添加，不预配全账号。**
- R2 Agent：可在 VM 内运行以 Claude Code 为底座的 Agent，支持多 Provider 切换与 API/订阅 token；可加载项目自定义 Skill/Hook/Prompt。
- R3 编排：CEO Agent 能拆解任务、分发给子 Agent、回收并整合结果。
- R4 记忆：提供渐进式披露的公司记忆文件系统（Wiki + assets），供各 Agent 读写共享。
- R5 集成：四层能组合出「单 Agent 在单 VM 内、读写记忆、由 CEO 调度」的可运行最小闭环。
- R6 自主判断（后续，非本期骨架）：商业判断（选题 / demand 验证 / kill）通过 **skill + hook** 实现；骨架就绪后再细化 skill 写法与「agent 遵循 skill」机制。

## Acceptance Criteria（验收标准，待 brainstorm 收敛）

- [ ] TBD — 每层补充可测试的验收标准（brainstorm 中逐条补齐）。

## Out of Scope（暂不在范围内）

- TBD（取决于 Q1c：真实资金/支付落地、法律实体注册等是否纳入本期）。

## Open Questions（阻塞规划的开放问题）

- ~~Q1：v6 重构北极星~~ → 已确认（见 Background）。
- ~~Q1b：business 决策由谁定~~ → 已确认：**CEO Agent 完全自主 / 零人公司，人类只在启动时提供账号**。
- **Q1c（最高优先，进行中）**：「人类只提供账号」的边界 —— 「账号」涵盖到哪一层？（仅登录账号+邮箱 / +资金通道 / +真实法律实体与 KYC 身份 / agent 自助一切）→ 决定 VM 层身份注入设计与 business 可行域。
- ~~Q1d：自主判断力机制~~ → 已定位：**靠 skill + hook，骨架就绪后再做**（本期不深入）。
- Q1e：编排实现 → 方向：非 Claude broker + 隔离容器（每 agent 一容器跑 `claude -p`）；「CEO→部门→执行者」协议细节（**设 Goal + 派任务，非 P2P**）移交**编排层子任务**的 design 阶段。
- Q2：第一个 business 方向？（完全自主下，可能是给一个起始 charter/约束集而非指定 business）
- ~~Q3：部署形态~~ → 已确认：**栈 B 自托管优先**（Claude Agent SDK + QEMU/cua + Bytebot + Browser Use/Steel + Decodo/IPRoyal ISP + AdsPower + Infisical + Anon + Stripe）。
- ~~Q1c：账号边界~~ → 已确认：**账号 + 资金通道**（虚拟卡/Stripe Issuing/Wise，实体+KYC 人类一次性备好）。
- ~~Q4：子任务顺序~~ → 已确认：**自底向上 VM → Agent → 记忆 → 编排**（采纳推荐）。
- Q5：风险容忍度（封号、KYC/合规、成本随 Agent 数扩展、token 管理）。
