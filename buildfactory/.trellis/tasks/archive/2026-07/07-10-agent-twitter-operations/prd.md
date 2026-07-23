# Agent Twitter 运营能力

## Goal

为 Growth Agent 提供所有 Foundagent 公司都能复用的 `operate-twitter` Skill。每次承接 Twitter/X 运营 Goal 时，Agent 必须先恢复公司长期上下文、再读取 X 的实时账号状态，随后自行选择最有价值的动作并完成执行、核实与状态回写，而不是把 Twitter 当成一次性的发帖工具。

目标闭环为：

> 读取 `/company` → 实时读取 X → 判断 → 选择 playbook → 执行 → 实时核实 → 更新 `/company`

Skill 不绑定任何账号、产品、受众或固定 `/company` 路径；不同公司的状态结构继续自由生长。

## Background / Confirmed Facts

- Resident Agent 的每次唤醒不能依赖上一回合的临时上下文；跨回合连续性来自 `/company`、standing objective 与当前 Goal。
- `/company` 保存公司当前状态而非流水日志，由 Agent 按业务主题自由组织，并通过 MAP → topic → leaf 渐进读取。
- Growth 容器已有登录 X 的 Playwright 浏览器：`accounts/<id>/cookies/storage-state.json` 作为只读登录种子，`agent/browser_mcp.sh` 保持 cookies、DISPLAY 与 proxy 三项独立降级。
- `07-03-social-rail` 已用真实账号成功发布过测试内容；本任务不重新解决登录与浏览器连通性。
- Growth loadout 目前没有 Twitter 专用 Skill；旧 `06-28-role-growth` 只留下 `use-accounts` 设计意图，没有形成现行能力。
- 公司治理是零人工运营者：Growth 在 Goal 授权范围内真实执行外部动作，verifier 事后独立核查；不增加逐帖人审或新的审批系统。
- 现有 `de-ai-ify`、`mine-customer-voice`、`design-asset`、`gen-image` 与 `visual-iterate` 已分别提供客户语言、文案去味和视觉生产能力，Twitter Skill 应组合使用而非复制这些内容。
- 官方规则研究确认非 API 网页自动化存在账号限制/封禁风险。用户于 2026-07-10 明确拒绝付费 X API、`xurl` 和 XMCP，选择自有网页脚本化操作并承担风险；研究证据保存在 `research/x-platform-automation-facts.md`，不构成本任务的实施阻塞。
- 用户于 2026-07-11 明确授权在当前真实 X 账号上完成本任务的读写验收，包括清理既有测试内容、修改资料、发布临时内容并在验收结束前删除恢复。

## Requirements

### R1 — 每次先恢复决策所需的长期状态

Agent 在做 Twitter 决策前，先使用 `company-state` 的渐进发现方式读取当前公司的 MAP，并按现有导航定位相关 leaf。Skill：

- 不创建或要求 `/company/channels/`、`twitter.md` 等统一 taxonomy；
- 不保存固定状态路径；
- 不硬编码 handle、品牌、产品、受众、voice、关注对象或内容策略；
- 不要求把分散在多个自然 leaf 的信息复制到统一模板。

在任何对外动作前，Agent 必须已经能够回答以下决策就绪问题：

1. 账号代表谁、以什么身份说话？
2. Twitter 对公司当前目标承担什么作用？
3. 最近做过哪些相关动作，出现了什么反馈？
4. 当前有哪些待处理信号、机会或承诺？
5. 为什么本回合选择这个动作，而不是其他动作或暂不行动？

如果 `/company` 还不足以回答，Agent 先调查或建立必要状态；状态落点由 Agent 根据该公司的现有主题结构自行决定。

### R2 — X 是当前账号事实的实时真相

- `/company` 负责账号存在的目的、公司目标、策略、经验与跨回合待办，但允许滞后。
- X 负责当前登录身份、公开资料、置顶内容、实际发布/回复记录和当前可见互动；涉及平台当前状态时，以实时 X 为准。
- 每次 Twitter Goal 都先读 `/company`，再实时打开 X 确认自己的账号身份和账号内容；不得仅凭旧状态推断账号现在有什么。
- 不固定扫描整条时间线或页面集合。Agent 根据 Goal 与状态缺口读取最小必要范围；任何外部写入前必须确认当前账号和动作直接依赖的页面上下文。
- `/company` 与 X 冲突时，以 X 的可见事实做本回合判断，并在结束前更新值得跨回合保留的状态。

### R3 — 按公司价值选择动作

Agent 不能默认每次发帖，也不以发帖数量、曝光、点赞或粉丝数作为自动目标。它按以下原则做高自由度判断，不使用固定分数、cadence 或动作优先级：

1. 服务公司当前目标和本次 Goal 的真实结果；
2. 重视与目标相关的真实信号、已有承诺和高价值关系；
3. 优先能增加用户认知、需求学习、有效触达或账号可信度的动作；
4. 把平台指标当作反馈证据和诊断信号，而非最终目标；
5. 没有高价值动作时可以不操作，不为保持活跃制造内容。

该闭环只在本回合承接 Twitter Goal 时触发；普通 Growth heartbeat 不凭时间经过自动产生外部动作，也不绕过现有 Goal/verification 生命周期。

### R4 — 一个 Skill，多个按需 playbook

首期交付一个顶层 `operate-twitter` Skill：

- `SKILL.md` 只包含每次都必须执行的状态恢复、实时核实、决策、playbook 路由、执行后核实和状态回写闭环；
- `bootstrap-or-reposition` playbook：起号、重新定位、主页一致性与首批内容；
- `publish` playbook：原创帖、Thread、引用发布以及内容/视觉 Skills 的组合；
- `engage` playbook：公开 mentions、回复、引用、点赞、关注、目标讨论与账号发现；
- `maintain` playbook：资料修改、置顶/取消置顶、已有内容审计和删除；
- 一个 Goal 可以组合多个 playbook，未选中的 reference 不需要加载；
- 不保存容易过期的 `mode: setup/ongoing` 字段，每次依据实时账号自行判断；
- 不复制现有客户语言、去 AI 味或视觉 Skill 的方法内容。

### R5 — 覆盖起号、日常运营与删除

首期公共账号能力包括：

- 实时检查并按公司身份修改 display name、bio、头像、banner、链接、位置、handle（Goal 确实需要且平台允许时）与置顶内容；
- 建立第一批能让访问者理解账号是谁、为何值得关注的主页内容；
- 发布原创帖/Thread，回复、引用、点赞、关注和观察相关讨论；
- 审计并删除错误、重复、过时、误导、测试性质或已明显违背当前定位的帖子/回复。

删除是正式能力，不是人类专属例外。删除前必须在实时 X 上确认精确对象、上下文与理由；删除后必须核实对象已消失，并将有长期价值的定位变化、原因或后续事项写回 `/company`。Skill 不把批量清空账号设为默认起号步骤，也不添加逐条人审。

首期不读取、发送或管理 Direct Messages。DM 需要独立的私密关系状态、收件箱语义与验收边界，待真实运营出现需求后再增加 playbook；公开 mentions、回复和引用不受此限制。

### R6 — 首期使用现有浏览器，CLI 后置

- 首期复用 Growth 已登录的 Playwright 浏览器，不新增 X developer App、API token、付费 credits 或第三方社媒工具。
- 用户已知情接受网页脚本化操作风险；Skill 不自行改走付费 API，也不把 API provisioning 变成前置条件。
- 为节省 token，优先使用直接 URL、结构化页面快照/可访问性信息与最小必要导航；只有判断视觉资料或页面状态确实需要时才使用截图。
- Skill 不硬编码易变化的 X DOM selector；工具层与“状态→判断→动作”语义分离。
- 自有 Twitter CLI/脚本封装后置。只有真实运行证明确有重复流程、token 或稳定性问题后，才从观测设计命令面；本任务不预先实现完整 CLI。

### R7 — 真实账号完成闭环验收并恢复测试改动

- 当前真实 X 账号可用于本任务读写验收，包括修改资料、发布、回复和删除。
- 优先清理账号上已有测试内容并完成真实有价值的维护；现有内容无法覆盖关键路径时，才新增临时测试内容。
- 临时帖子、回复或资料修改必须在同一次验收收尾前删除或恢复，并在实时 X 上二次确认；不得把清理留给下一回合。
- 经实时判断确有账号价值的变化可以保留，最终报告必须分别列出保留项和已回滚测试项。
- 该授权只用于本任务当前真实账号验收，不把测试发帖变成未来 Skill 的默认测试方式。

### R8 — 回写当前状态，供下一回合接续

观察或动作完成后，Agent 使用 `company-state` 把值得跨回合保留的新事实、决策、结果、经验和待办更新到该公司自然生长的状态中：

- 写当前状态，不追加浏览/操作流水；
- 不为 verifier 制作专用 proof；verifier 独立读取 Goal 并核查现实；
- 即使没有值得更新的 leaf，仍遵守 `company.py record --nothing` 的 session-end 契约。

## Acceptance Criteria

- [ ] **AC1 — 自由状态发现：** 全新 Agent 能在任何 Twitter 动作前从 `/company` 当前导航发现相关状态，回答五个决策就绪问题；Skill 不依赖固定 topic、文件或字段。
- [ ] **AC2 — 实时事实优先：** 即使 `/company` 保存了过期资料或帖子信息，Agent 也会通过实时 X 发现差异，以当前账号内容为准，避免错号、重复发布或错误删除。
- [ ] **AC3 — 价值判断：** Agent 根据公司目标与平台信号选择发布、互动、维护、观察或不行动；面对无关高曝光与目标用户具体问题时，不仅按 vanity metrics 决策。
- [ ] **AC4 — Playbook 路由：** 同一个 `operate-twitter` 入口可按实时状态选择并组合起号/重定位、发布、互动和维护 playbook；未选择的 reference 无需加载。
- [ ] **AC5 — 起号与维护：** 面对空白、资料不完整或定位混乱的账号，Agent 能从自由生长的公司状态恢复身份并完成相符的资料、视觉、链接、置顶与必要内容清理，Skill 中没有硬编码品牌身份。
- [ ] **AC6 — 精确删除：** 面对指定错误、过时或测试内容，Agent 先在实时 X 确认对象与上下文，再删除并核实结果，不依赖旧状态猜测。
- [ ] **AC7 — 跨回合接续：** 完成动作后，下一次全新唤醒能从更新后的 `/company` 与实时 X 继续，不需要人类复述上一回合。
- [ ] **AC8 — 浏览器兼容：** 方案复用现有 Growth Playwright/storage-state/proxy/DISPLAY 轨，不改变 `agent/browser_mcp.sh` 的三项独立降级，也不需要 X API 凭证或付费 credits。
- [ ] **AC9 — 真实 E2E：** 当前真实账号完成至少一次“长期状态 → 实时 X → 决策 → 真实写入 → 核实 → 状态回写/收尾”的闭环，优先清理已有测试内容。
- [ ] **AC10 — 测试恢复：** 所有临时内容与资料改动在验收结束前删除或恢复，并经实时 X 二次确认；最终报告分别列出保留项与回滚项。
- [ ] **AC11 — 治理兼容：** Twitter 动作由现有 Goal 生命周期触发并由 verifier 独立验收；普通 heartbeat 不凭空操作，本任务不增加人类逐帖审批。
- [ ] **AC12 — 通用复用：** 同一 Skill 放入账号定位、产品状态与 `/company` taxonomy 都不同的 Foundagent 公司时，无需修改 Skill 文件，只需该公司的状态与账号登录态。
- [ ] **AC13 — 范围边界：** 首期不读取、发送或管理 DM，不实现 Twitter CLI，不要求 `xurl`/XMCP/X API；公开 mentions、回复和引用仍可运行。

## Out of Scope

- 重新设计 X/Twitter 登录、Cookie 导出、账号隔离、proxy 或浏览器 wrapper。
- 首期实现自有 Twitter CLI，或接入 `xurl`、XMCP、付费 X API、付费第三方社媒工具。
- 读取、发送或管理 X Direct Messages。
- 覆盖 Instagram、LinkedIn 等其他社交平台。
- 在没有真实失败证据前建立复杂审批、配额、固定内容日历、发帖频率或防误操作规则。
- 以粉丝数、曝光量等无法稳定保证的业务结果作为代码验收条件。
