# BuildFactory 驱动的自主 Hackathon Build Teams

## 目标

在 HackSome 已有的 Prompt → Idea Card 工作流之后，加入一个基于
BuildFactory 当前实现改造的长期自主 Build 系统。人只在 Idea Card 与 Build
之间进行一次显式授权；Team 启动后完全 human-out-of-the-loop，持续观察、构建、
验证和改进自己的项目。

系统不以产出唯一项目为目标。每张获准进入 Build 的 Idea Card 都可以形成一个
独立 Team；所有成功项目全部保留，不排名、不合并，也不自动筛掉其他项目。

## 已确认事实

- BuildFactory 当前受版本控制的本地快照已经放入仓库的 `buildfactory/` 子目录。
- `buildfactory/` 是 HackSome 仓库的一部分，不包含嵌套 `.git`，也未复制运行状态、
  账号凭证、虚拟环境或缓存。
- Build 运行时直接基于这份 BuildFactory 代码裁剪和改造，不重新实现另一套 Agent
  runtime、Hub、Worker 或 Verifier 系统。
- Prompt → Idea Card 的现有实现和正在进行的 Idea E2E benchmark 属于并行工作，
  本任务不得覆盖其未提交改动。

## 产品要求

### R1 — 一次性人工 Review Gate

- Idea 阶段可以产生任意数量的有效 Idea Card。
- Build 前必须暂停在人工 Review Gate，等待 operator 显式提交选择。
- 没有超时默认值；超时、空响应、非法响应或重启都不能自动批准任何 Card。
- operator 可以显式选择任意子集，包括全部或零张。
- 未选择的 Card 仍然是有效 Idea，只是不启动 Build；不得记录为质量 reject。
- Review Gate 对每个 Team 只发生一次。Team 启动后不再存在任何人工审批、
  reapproval 或 human-in-the-loop 分支。

### R2 — 每张 selected Card 创建独立 Team

- 每张被选择的 Idea Card 创建一个隔离的长期 Hackathon Build Team。
- Team 之间不共享项目状态、Repo、Agent session 或实现上下文。
- 每个 Team 初始化时的 Agent 可见 reference 只有：

  ```text
  reference/
    challenge.md
    initial-idea-card.md
  ```

- `challenge.md` 和 `initial-idea-card.md` 都只是初始参考，不是不可变 Objective、
  合规约束或持续成功判据。
- Idea Card 只负责初始化 Agent。Agent 可以修改、放弃或完全不继续原 Idea，并自主
  决定最终做什么。

### R3 — 无确定性语义工作流

- Hub 不得通过固定 category、阶段 Schema 或状态机决定 Agent 应该做什么。
- 系统不得冻结 Audience、Problem、价值时刻、产品机制、PRD、架构或交付顺序。
- 系统不得要求 Agent 按 PRD → Build → Pitch 等预设阶段运行。
- Agent 自己决定是否创建 Objective、PRD、Roadmap、决策文档或其他项目结构。
- 确定性代码只负责机械边界，例如生命周期、能力授权、并发、持久化、恢复和
  Worker/Verifier 仲裁；产品判断和下一步工作由常驻 Agent 决定。

### R4 — 长期运行语义

- Team 没有完成态、自动终态或业务上的 idle 态。
- 系统不设置 Hackathon Deadline，也不按时间自动结束 Team。
- Repo、Demo 或 Deck 发布后，Team 仍可继续观察、抠细节和改进。
- quiet timer 或周期 wake 只能是运行调度机制，不能被解释为 Team 已完成或无事可做。
- 只有 operator 可以显式停止一个 Team。

### R5 — 职责分离

- 每个 Team 只有一个常驻 Hackathon Lead；不保留 BuildFactory 的 Department 层。
- Lead 负责长期判断、观察项目、维护自然项目状态、创建和取消 Goal。
- Lead 每次 wake 的稳定行为直接写入 charter / dynamic prompt：检查项目的真实现状，
  形成判断，推动实质进展，并执行当前角色可以做的事情。
- 不创建或强制调用 `continue-project`、`think-strategically` 等常驻元 Skill。凡是几乎
  每次 wake 都必须遵守的行为属于 Prompt 契约，不属于按需 Skill。
- `send-goal` / Goal 创建同样不是 Skill。Lead prompt 必须直接说明如何把当前判断转成
  一个或多个具体、可独立验证的 Goal，并直接暴露所需 Hub 方法或调用格式，避免 Lead
  每次先发现和读取一个派活 Skill。
- Skill 只承载在特定情境下需要展开的专门方法；Lead 根据当前真实问题自行选择是否使用。
- Lead 可以使用 Playwright、CUA 及其他真实项目检查能力，亲自打开本地或线上产品、
  走 User Flow、观察 UI 和确认当前行为，而不是只读取文件或等待 Verifier 摘要。
- Lead 与 Worker 可以共享大部分项目、研究、浏览器、设计和质量 Skill；两者的核心差异
  是生命周期、上下文范围、Goal 权限和提交契约，而不是人为制造完全不同的能力目录。
- Lead 不直接执行普通构建工作。
- 一次性 Worker 负责代码、设计、研究、测试、部署、Pitch 等实际工作。
- 独立的一次性 Verifier 检查真实结果；FAIL 后恢复原 Worker 继续返工。
- Team 启动后的所有 Lead、Worker 和 Verifier 都是 Agent，不引入人类审批。

### R6 — 两层 Pool

- Global Team Pool 只限制同时 active 的 Team 数量，默认 `max_active_teams = 2`。
- 超出全局槽位的 selected Team 保持排队，不算拒绝或失败。
- active Team 不会自动完成、idle、轮转或释放槽位。
- 只有 operator 显式暂停 active Team 后，系统才释放槽位并启动排队中的下一个 Team。
- operator 暂停使用可恢复的 `paused` 控制状态：停止相关运行实例后保留 Repo、
  Team state、Goal ledger、session token 和排队工作；以后可以恢复同一个 Team。
- `paused` 不是 Agent 的 idle、完成或失败状态。永久删除必须是独立且明确的破坏性操作。
- 每个 active Team 默认最多拥有 5 个 Worker lifecycle 和 3 个并发 Verifier；
  容量可以通过运行配置修改。
- 每个 Team 使用自己的 Goal FIFO 和固定 Worker/Verifier Pool；Team 之间不争抢同一个
  Worker FIFO。默认两个 Team 同时 active 时，全局理论上限是 10 个 Worker lifecycle
  和 6 个并发 Verifier。
- 系统不得根据 Idea 或项目质量自动调整 Team 顺序、资源或存活状态。

## 验收标准

- [ ] Review Gate 只有显式 operator 提交才能形成选择结果，任何隐式或超时路径都不会启动 Team。
- [ ] 一次选择多张 Card 后，每张 Card 都形成隔离 Team，所有可用全局槽位并行启动。
- [ ] 默认最多两个 Team active；其他 selected Team 排队，直到 operator 暂停一个 active Team。
- [ ] 暂停并恢复 Team 后，Repo、Team state、Goal ledger 和可用 session 连续性仍然存在。
- [ ] 每个 active Team 默认独立限制为 5 个 Worker lifecycle 和 3 个并发 Verifier，
      修改一个 Team 的队列不会改变其他 Team 的 Goal FIFO。
- [ ] Team 状态只预置 `reference/challenge.md` 与
      `reference/initial-idea-card.md` 两份 Agent 可见输入。
- [ ] Team 可以在不遵循 Idea Card、没有预设 PRD/Build/Pitch 阶段的情况下继续运行。
- [ ] Lead、Worker 和 Verifier 的职责在运行时能力与写入权限上结构性分离。
- [ ] Worker 结果由独立 Verifier 检查；FAIL 恢复原 Worker，而不是交给人审批。
- [ ] 已经发布 Repo、Demo 或 Deck 的 Team 不会被系统自动标记完成或停止。
- [ ] 多个成功 Team 的项目全部保留，系统不生成 winner、Top-K、合并结果或自动淘汰。
- [ ] BuildFactory 原仓库和 HackSome 现有 Idea workflow 的并行未提交改动均未被覆盖。

## 不在范围内

- 自动选择或排名 Idea Card。
- Build 后的人工审批或方向复核。
- Team 自动轮转、自动让出全局槽位或基于质量的资源调度。
- 固定产品阶段、强制交付顺序和 Idea 一致性检查。
- 迁移 BuildFactory 现有 Company 运行状态、邮箱或外部账号数据。
