# CEO 用户价值闸门：从真实问题到真实 objective

> 状态：主体实现、确定性回归与真实 resident verifier 校准均已完成。`when-idle` 的三处兼容改名由独立任务负责，本任务没有重新设计其运营逻辑。

## 背景

当前系统把同一次 objective 决策拆成了两个 CEO Skill：`decide-direction` 判断“值不值得做”，`set-objective` 负责“怎么设成 objective”。两者职责重叠，且 `decide-direction` 把方向判断扩散到了 heartbeat 和普通 Goal。

现有判断也容易把“问题客观存在、市场在增长、竞品存在、东西很快能做出来”误当成“具体用户真的会选择它”。`secondtest` 就是回归案例：MCP 安全风险真实，软件也真实可安装，但小团队可能偶尔手工看一下就够了；真正有规模、审计和合规压力的大组织，需要的能力又远重于一个 CLI。产品因此落在“对小用户太重、对大用户太轻”的断层里。

这不是单纯的软件产品问题。公司也可能做服务、信息产品、内容/媒体或其他形态，所以 objective 评审必须判断真实经营价值，而不是默认判断“要不要写一个产品”。

## Goal

让 `set-objective` 成为唯一的 objective 决策入口。CEO 在设置或改变 objective 前，必须从一个有证据支撑的具体用户出发，判断候选方向应当 `DROP / RESHAPE / BUILD`；只有独立 verifier 给出 `PASS`，候选才成为公司的生效 objective。

## Requirements

### R1 / R8 / R9：只保留一条 objective 决策链

- 将 `decide-direction` 的价值判断并入现有 `set-objective`，删除独立的 `decide-direction` Skill、临时 direction reviewer 及所有悬空引用；不新增 `what-should-i-do-now`、`choose-next-goal` 或第二个方向评审。
- `find-opportunity` 只负责产生不同 business form 的候选，然后交给 `set-objective`。CEO 负责准备候选，但不能自我批准；现有常驻 verifier 的 `review-objective` 是唯一独立评审者。
- 本任务的用户价值闸门只适用于 CEO 的公司经营 objective。builder、growth、researcher 等部门内部 objective 继续使用现有的聚焦、可测、规模与修订理由标准，不要求证明外部市场需求。
- `set-objective` 只在 objective 层发生变化时触发：首次设置；原 objective 完成后选择下一 objective；改变目标用户、触发场景、痛点、核心价值、business form、交付方式或主要替代；以及 `RESHAPE` 后形成新候选。
- heartbeat、空账本和普通 Goal 不是触发理由。已通过 objective 下的开发、修复、文档、发布、分发和既定补证 Goal 不重复过闸门。
- `when-idle` 继续负责空账本时选择下一项 Goal，CEO charter 继续处理 Goal 的 `DONE / KILLED` 结果。它们若发现必须改变 objective，才转入 `set-objective`；本任务不修改这些运营路径。

### R2 / R12 / R13：从一个具体用户判断任何 business form 的真实价值

每个候选都要说清最小真实交付是什么：它可以是一单人工服务、一份可购买的信息产品、一项会被真实消费的内容、一个进入工作流的软件，或其他真实经营形态。`BUILD` 指开始这项最小真实交付，不等于写软件。

CEO 必须代入一个由证据支持的具体人物和情境，用适合该 business form 的自然方式讲清：谁在什么时刻想完成什么；现在如何处理或为什么不处理；现状的时间、金钱、风险和组织成本；问题及价值出现得多频繁；为什么他会买、委托、阅读、安装或使用，而不是继续手工处理、选竞品或什么都不做；公司现在从哪里实际接触到第一批这样的人；什么最小结果会改变判断。

这不是固定表格：不强制统一用户旅程、买方/使用者拆分、复购模型、漏斗、渠道、人数或 DAU。一次性服务、一次购买的信息产品、持续内容和工作流软件可以采用完全不同的论证方式。但宽泛的“开发者”“小团队”“内容消费者”，以及“以后做营销/发社交媒体”，都不能替代具体用户和当前可用的触达路径。

事实、假设和待验证项必须分开。CEO 的“如果我是他，我会不会用”是发现采用摩擦的推理工具，不是需求证据。

### R3 / R4：用外部真实行为判断需求，同时认真计算手工替代

- 冷启动不要求已有本公司用户。可核验的外部行为可以证明需求，例如目标用户已经付费购买替代方案、持续投入人工、雇用服务商、反复使用 workaround、主动提供真实样本、安装接入工具或持续寻找解决办法。行为必须匹配具体用户和触发场景，并能追溯来源、时间及其成本。
- 用户真实购买或使用竞品只能证明这一类需求存在；候选还必须说清未被满足的缺口，以及用户为什么会切换、叠加或另行购买。公司拥有第一方行为后，应优先使用它，不能用行业趋势覆盖相反的内部数据。
- 行业报告、新闻热度、市场规模、竞品融资或功能表、内部 fixture/测试/demo/样稿、公司自己的安装、推广 PR/反馈 issue/目录收录、短期虚荣指标和“听起来不错”，都只能支持继续研究，不能单独支持 `PASS`。容易、便宜、可逆或几天能做完，也不能降低需求门槛。
- 必须诚实判断“用户能不能自己查一下”：考虑单次耗时、出错概率、专业要求、协作人数和累计成本。问题低频、手工处理简单、后果有限且没有持续消费或委托理由时，默认不应成为独立经营方向。
- 低频本身不是机械否决。单次损失极高、法规或审计强制、事件规模大、责任与预算明确，或方案能以极低摩擦嵌入持续流程时，仍可能成立；若只对某类组织成立，就应收窄 ICP、改变 business form 或交付方式。

### R5 / R6：协议仍是 `PASS / FAIL`，经营含义是 `BUILD / RESHAPE / DROP`

- `PASS` 等同于 `BUILD`：证据足以激活 objective，并开始最小真实交付。
- `FAIL --reason "RESHAPE: ..."` 表示问题可能真实，但用户、场景、形态、交付、触达、证据或切入点尚不成立。原候选不得生效或执行；CEO 修改后必须把完整新候选重新提交。
- `FAIL --reason "DROP: ..."` 表示痛点弱、现状已足够、没有可达用户，或补证后仍没有行为证据；该候选到此终止。
- 不增加 `VALIDATE` verdict。证据不足时仍是 `FAIL: RESHAPE`，并指出一个最小、真实、可观察且确实会改变决策的补证动作，例如访谈、收集样本、人工 concierge、预售、首单服务、发布最小内容或真实工作流试接入。只有业务语境需要时才规定数字、样本量和观察期。
- 补证不是对原候选的有条件放行。完成后仍须重写并重审；失败后必须继续 `RESHAPE` 或 `DROP`，不能靠加功能、发版本、扩大渠道或换虚荣指标维持原方向。
- objective CLI 继续只接受 `PASS / FAIL`；Goal verification 和 role review 的既有协议不变。

### R10：完整 objective 随 `/company` 自己的结构生长

- proposer 先通过 company-state 的渐进披露读取当前 `MAP.md` 和相关 topic，再按业务主题选择或创建合适的 leaf。系统不得预设 `/company/strategy/`、`ceo/`、`objectives/`、固定文件名或按角色生成的目录。
- staged proposal 同时携带目标 leaf path、导航摘要、完整候选和一屏以内的短摘要。完整候选保留用户与情境、business form、替代、频率与价值、最小交付、触达路径、证据、关键假设及调整/终止条件；短摘要是 wake 注入用的投影，并包含动态指针 `完整上下文：/company/<实际 leaf path>`。
- verifier 同时审查完整候选、动态路径和短摘要，确认语义一致且归类符合公司当前结构。`PASS` 通过同一生效流程写入完整 leaf 和短摘要；任一写入失败都 fail closed，不得留下部分生效或两个互相矛盾的版本。
- `FAIL` 不改变当前 leaf 或当前短摘要，也不强制创建 rejected-directions 目录。CEO 想记录否决结论就按当时的 company-state 结构记录，不想记录则不记录。
- `/company` leaf 只表达当前状态；旧 objective 的流水仍由现有 objective history 负责。`MAP.md` 和 `OVERVIEW.md` 只能由 company-state CLI 维护。

### R11：独立评审严格且 fail closed

- verifier 必须检查承重判断：具体用户与触发、现有替代、真实行为、频率/价值、采用理由、最小交付、现实触达路径和证伪条件。缺失、矛盾、不可追溯或只有模型推测时，返回 `FAIL: RESHAPE`；明显没有需求、缺口或可达用户时，返回 `FAIL: DROP`。
- 小公司不必拥有完美数据或自己的现成用户，但 `PASS` 至少要同时成立：有真实需求行为；现有方案留下具体缺口；用户选择候选的理由可信；公司能实际接触首批用户；最小交付能快速产生可观察结果。
- verifier 必须亲自打开或查询所有支撑 `PASS` 的承重证据，可使用现有浏览器、搜索、Stripe、GA4、GSC 等能力；辅助背景无需穷举。来源打不开、内容不支持结论或第一方数据对不上时，不能 `PASS`。
- 评审结果不能只有一行 verdict；必须说明关键判断、证据等级、实际核查的承重来源、最大未知，以及什么条件会推翻结论。候选写得完整、投入已发生或交付很容易，都不能放宽标准。

### R7：`secondtest` 是必须拦住的回归案例

原始的“小型工程团队 MCP 风险扫描 CLI”不能直接 `PASS`：已有材料证明风险主题和软件可行，却没有证明真实团队会提供配置、安装接入、跨配置变化持续保留、付费或采取其他有成本的行为；小团队可能低频手工查看，已有平台能力和直接产品也能完成基础扫描，而大型组织需要的又是集中资产、策略、审批和审计能力。

合理初始结果是 `FAIL: RESHAPE`：转向真实团队的人工配置审计或 PR gate 试接入，并取得真实控制行为、样本和接入意愿；若合格团队既没有现有控制动作，也不愿提供样本或接入流程，则 `FAIL: DROP`。任何示例数量或观察周期都只是该案例的设计参数，不得机械扩展成所有 business form 的统一门槛。

## Acceptance Criteria

- [x] **AC1–AC5、AC21–AC25、AC28–AC29：价值案例。** 缺少具体用户、触发、替代、频率/价值、行为证据、采用理由、最小交付或当前可用的首批用户路径时不能 `PASS`；外部真实行为可支持冷启动，但行业趋势、竞品存在、CEO 代入和易于交付不能代替它。低频高后果或特殊 business form 不会被统一模板、固定数字或 DAU 机械误杀。
- [x] **AC6：secondtest。** 真实 Codex resident verifier 已重放原始通用扫描 CLI，亲自打开承重来源并刷新公开信号，明确指出低频/手工替代、平台与通用扫描替代、大小组织需求错位和真实采用行为缺口，最终给出 `FAIL: RESHAPE`；完整记录位于 `research/live-e2e/`。
- [x] **AC7、AC15、AC23、AC26：独立评审。** 候选只经过常驻 `review-objective` 一次独立评审；verifier fail closed，亲自核查所有承重证据，并输出可审计的判断、来源、最大未知和推翻条件。
- [x] **AC9–AC12：触发与职责。** 普通 Goal、heartbeat 和空账本不会触发 objective 重设；不新增运营选择 Skill；CEO loadout、charter、`find-opportunity`、references 和测试不再引用独立 `decide-direction`；when-idle 的兼容改名由独立任务承担。
- [x] **AC13：跨经营形态。** 服务、信息产品和内容/媒体候选可在不构建软件的情况下 `PASS`，并使用适合其形态的购买、委托、消费或持续参与证据。
- [x] **AC14、AC16：verdict。** objective CLI 仍严格使用 `PASS / FAIL`；`FAIL` reason 必须以 `RESHAPE:` 或 `DROP:` 开头，且任何 `RESHAPE` 都不会激活 objective 或授权执行原候选，只有重审后的 `PASS` 才能生效；Goal 与 role 协议不变。
- [x] **AC17–AC20、AC27：持久化。** `PASS` 后，完整 objective 位于 proposer 按当前 taxonomy 选择的动态 `/company` leaf，短摘要含正确动态指针，二者来自同一次批准且不会部分生效；`FAIL` 不改现状、不强制落盘，代码和 Skill 中不存在固定公司目录假设。
- [x] **AC30：角色边界。** CEO 的公司经营 objective 使用完整用户价值闸门；非 CEO 的部门内部 objective 保持原协议和结构性评审，不会被要求提供外部用户、市场需求或首批获客路径。
- [x] **AC8：回归质量。** 本次相关 Skill、prompt 和 orchestration 回归全部通过；全量中的 10 项失败均为改动前已有的 Codex/Claude 迁移基线问题。

## Non-goals

- 不在本任务中继续开发或营销 `secondtest`。
- 不修改 `when-idle` 的实现、终局行为或任务文档。
- 不规定统一的用户旅程、买方/使用者数量、复购模型、漏斗、获客渠道、样本量、数值阈值或观察周期。
- 不要求所有经营方向高频，也不以 DAU 作为唯一价值标准。
- 不建立强制的 rejected-directions registry 或否决记录目录。
- 不把 CEO 的外部用户价值 rubric 套到 builder、growth、researcher 等部门内部 objective 上。
