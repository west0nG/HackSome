# 让 CEO 持续建立、质疑并更新商业逻辑

## 目标

让 CEO 像真正的公司决策者一样，把主要精力放在想清楚产品和商业决策上：基于 `/company` 中的事实建立一条能走到销售的因果链，主动攻击其中的假设，并在每次收到新结果、反馈或约束时判断“这改变了什么”。

V1 不试图定义一套万能商业流程，也不把“好思考”压成评分表。它先给 CEO 一个确定会被触发的战略思考入口，以及一组可以自由组合、反复调用的原子化认知 skill；做出来后再根据真实运行暴露的问题收紧。

## 核心问题

当前 CEO 可以发现真实需求、通过 Objective 审核、派发工作并持续构建，但它没有被稳定地要求完成下面这件事：

> 从公司已知事实出发，解释为什么这个具体产品、业务形态和公司能执行的获客方式，会让一个具体买家发现它、理解它、相信它、选择它并付款；当链条中的事实改变时，重新判断原结论是否仍成立。

因此，一个局部上都说得通的方向——需求存在、竞品有人买、产品做得出来——仍可能在整体上根本卖不出去。Agent 会继续优化和派发，而没有意识到最初让方向成立的关键条件已经失效。

这不是单独补一道“需求验证”或“解法有效性验证”就能解决的问题。需求、产品形态、交付能力、分发、买家信任和付款互相耦合；缺的是 CEO 持续构造、批判和更新整个商业逻辑的能力。

## thirdtest 暴露的具体断裂

NCLEX Objective 当时建立了一个表面完整的判断：

- 有真实考生痛点和相邻付费行为；
- 有人购买并喜欢相同形态的 medication workbook；
- 产品是一份便宜、精简、按药物类别组织的资料；
- Amazon KDP organic search 是公司可以立即使用的入口；
- 上线后的真实销售是最终信号。

对应材料见：

- `state/thirdtest/company/products/nclex-exam-prep.md:65-128`
- `state/thirdtest/sessions/verifier/review-nclex-objective.md:5-18`

随后，新信息改变了这条链最关键的部分：

- Builder 确认 KDP 需要电话 2FA、纳税身份和匹配的银行账户，零人公司无法独立完成，见 `state/thirdtest/company/products/pharmacology-guide/KDP-PUBLISHING-PATH.md:9-17,36-67`。
- 公司改成自建 Stripe 商店后，Amazon 内部搜索、榜单、评论和销量飞轮全部消失；流量必须由公司自己创造，见 `state/thirdtest/company/growth/kdp-launch/08-storefront-playbook.md:8-32`。
- 首批一方数据是零销售、零搜索流量，且商店没有已工作的流量驱动，见 `state/thirdtest/company/market/nclex-metrics-snapshots.md:15-42`。

这不是普通执行细节。原 Objective 中“买家在 Amazon 主动搜索”“低摩擦购买”“竞品销量证明入口可用”原本共同支撑产品形态；渠道一换，产品、发现、信任和付款的关系也一起变了。合理反应应当是重新检查整个商业判断，而不只是把 KDP 页面替换成自建站后继续原计划。

thirdtest 证明的是：现有系统能验证一个时点上的叙事，却没有让 CEO 在后续信息改变负载假设时持续重建叙事。

## 为什么现有结构容易产生这个问题

### CEO 的职责更偏向“行动”而不是“想清楚”

`agents/assets/ceo-charter.md:3-18` 把 CEO 描述为 THINK + DISPATCH，但具体运行要求仍是“做完本次 wake 所需的事、保持短促”；`agents/assets/ceo-charter.md:61-64,79-86` 又把结果处理收敛成“决定下一步”。这些规则没有明确要求 CEO 先检查结果对既有商业逻辑造成了什么影响。

### 空闲机制把唯一合法结果写成派发

`agents/assets/skills/when-idle/SKILL.md:10-16,29-32,79-92` 要求 ledger 为空时必须以 Goal 结束。这个机制成功阻止了 CEO 休息摆烂，但也把“持续思考公司方向”压缩成了“找一个下一步派出去”。问题不在 heartbeat 的主动性，而在它只承认派发、不承认战略思考本身是 CEO 的工作。

### Objective 是时点审核，不是持续思考循环

`set-objective` 已经会检查具体用户、替代方案、购买理由、入口和最小交付；Verifier 也会独立审核。但 PASS 只说明当前证据允许开始最小真实交付，不会保证后续新信息自动进入原推理链。现在没有一个比 `find-opportunity`、`set-objective` 更上层的认知入口，负责决定何时重用它们、何时推翻前提、何时只是保持原决策。

### 模型具备能力，但调用条件不足

底层模型通常能做因果推理、反例分析和买家视角推演；问题是它默认会优先完成眼前任务，并用流畅叙事补齐缺口。仅增加 thinking token 不能保证它在每个关键时刻主动切换到这些思考方式。Harness 需要负责确定性触发和提供认知工具，但不替模型写死答案。

## V1 对“商业成立”的理解

V1 的商业终点是**卖出去**。它不额外设置“是否真正帮助用户”的道德或产品效果门槛。

但“真的能帮助”经常是让买家相信、降低风险、形成评价、口碑、复购或转介绍的最好办法。因此产品效果应当在它影响信任和销售因果链时被认真推理，而不是被完全忽略；同时也不能把最终用户结果设成所有业务开始前都必须证明的独立硬门。

同理，business form 不是与需求正交的预选项。Agent 对 info product、SEO pages 等形态的能力优势可以作为先验，但证据可能要求改产品、改渠道、改交付方式，甚至改整个业务形态。V1 要让 CEO 能看到这种耦合，而不是为每个 business form 建一套固定流程。

## 需求

### R1：把战略制定和反思写成 CEO 的首要职责

- CEO 的核心产出是方向、判断及其因果逻辑；派发是判断之后的动作，不是默认终点。
- CEO 应投入与决策重要性相称的思考，不再被“每次 wake 必须短”推向快速行动。
- 收到已验证的 DONE 时，CEO 不重新验收 worker 的交付，但必须判断该结果对当前事实、假设、产品和策略意味着什么。
- 重要事实、推理、假设、决策及其理由继续写入 `/company`；不创建 CEO 私人便签或第二套记忆。

### R2：所有 CEO 事件唤醒先进入战略思考

- CEO 因 Goal 结果、外部反馈、约束或其他 inbox 事件被唤醒时，在采取行动前必须先调用 `think-strategically`。
- 该要求由 wake prompt 确定性注入，而不依赖 CEO 自己记得。
- 只有明确开启战略模式的角色获得该提示；所有 worker 与 verifier 的事件 prompt 保持原样。
- V1 不使用 Stop hook 检查“是否真的想过”。Hook 只能可靠检查标记，无法判断思考质量，过早加入会把反思变成打勾动作。

### R3：保留 heartbeat 的防摆烂作用，但放宽空 ledger 的合法行动

- heartbeat 仍必须调用 `when-idle`，先读取 Goal ledger，而不是凭感觉判断是否空闲。
- 有工作在执行且没有 CEO 判断需要处理时，继续一行 stand down，避免无意义并发和空转。
- ledger 为空时，CEO 不得立即休息；`when-idle` 必须转入 `think-strategically`。
- 战略思考之后可以派发 Goal，也可以形成、修订或记录一个真实的战略判断，或进入 Objective 工作流；不再规定“唯一合法输出只能是 Goal”。
- V1 不为“真实战略进展”制定统一格式或硬阈值。先允许较大的思考空间，再根据运行中出现的空话、重复反思或不行动问题收紧。

### R4：增加一个薄的元认知 skill

新增 `think-strategically`，职责仅限于：

1. 判断当前到底需要想清楚什么；
2. 基于上下文选择一个或多个原子化认知 skill，必要时重复或换一种方式继续；
3. 将所得判断整合为 CEO 的决定、下一步行动和需要写回 `/company` 的结论。

它不提供业务评分、不输出 PASS/FAIL、不规定固定 skill 顺序和调用次数，也不复制 `find-opportunity` 或 `set-objective` 的工作流。后两者仍位于它下方：只有思考后确认需要寻找新方向或正式改 Objective 时才进入。

### R5：增加四个高自由度原子认知 skill

1. `trace-causal-chain`
   - 从已知事实和公司可执行动作推导到商业结果；
   - 找出链中依赖的假设、缺失连接和可能断点；
   - 不强制所有业务使用同一漏斗模板。
2. `challenge-thesis`
   - 暂时把当前结论当作可能错误；
   - 寻找反例、其他解释、隐藏假设和“为什么我们会输”；
   - 允许推翻 Objective，而不是只能优化既定方案。
3. `reason-as-buyer`
   - 从一个具体买家的真实处境推演发现、理解、信任、替代选择、相信和付款；
   - 区分基于事实的推理与角色扮演；角色扮演本身不算市场证据。
4. `integrate-new-information`
   - 明确新结果、反馈、约束或小改动相对既有认知的 delta；
   - 追踪它影响了哪些下游判断；
   - 可以得出保持、局部修改或重做策略，不能因变化很小就跳过思考，也不能因有变化就机械地全面推翻。

四个 skill 各自只做一种认知动作，不内置统一输出模板、分数、裁决或实验流程。

### R6：让新信息进入既有逻辑，而不是另起一套分析

- CEO 在处理任何新信息时先问“它改变了现有认知中的什么”。
- 原有 `/company` 事实和推理全部保留；新信息作为 delta 合并，而不是每次从空白重新规划。
- 小改动也要判断影响范围。若负载逻辑没有改变，重新检查可以合理地得到同一产品决策；“重新思考”不等于“必须改变”。
- 若新信息改变了目标用户、价值、产品、业务形态、交付、分发或主要替代方案，则 CEO 可以通过现有 `set-objective` 正式修改或放弃 Objective。

### R7：保留并澄清现有 opportunity / objective 工作流

- `find-opportunity` 仍负责在没有 grounded candidate 时产生基于真实信号的候选。
- 它对 business form 的选择改为能力约束下的可修订先验；需求和形态应共同演化，不能“随便先选一个然后锁死”。
- `set-objective` 的独立 Verifier、事实/假设区分和 `PASS → BUILD` 保持不变。
- PASS 表示当前证据允许开始最小真实交付，不表示商业逻辑永久成立，也不豁免后续反思。
- 不新增 `VALIDATE` verdict、产品效果 gate 或第二个机会评分器。

### R8：保持 `/company` 为唯一公司状态

- 所有公司事实、上下文、推理、决策和反馈仍位于 `/company` 的自然主题结构中。
- 不新增 belief database、CEO notebook、reflection log 或其他平行存储。
- `think-strategically` 和原子 skill 读取相关 `/company` 内容，并只把会改变未来决策的耐久结论写回现有主题文档。
- 不把每次内心推演机械追加成日志；遵守 company state 的原地维护和渐进读取原则。

### R9：V1 保持宽松并可观察

- 结构上保证 CEO 会进入思考入口、能发现并调用认知 skill、空闲时不会直接睡眠。
- 不在 V1 预先定义“每次至少几条因果”“必须列几个反例”“思考多少 token”或统一报告格式。
- 实施后用不泄露预期答案的 thirdtest 原始情境做一次 forward test，保留完整输入、skill 调用和输出供观察。
- forward test 的作用是发现下一轮要收紧什么，不在本任务中立即演化成固定评分门，除非暴露的是接线错误（例如根本未调用 skill）。

## 行为示例（不是固定模板）

### 重大新信息

收到“KDP 因身份和银行条件无法使用”时，CEO 不应只派发“做一个 Stripe 商店”。它应先看到：原先的发现渠道、信任机制、价格摩擦和竞品证据都依赖 Amazon；如果改为自建站，原产品形态是否仍值得做必须重新判断。结论可以是换渠道、换产品形态、补新的获客逻辑，或放弃方向。

### 小改动

收到“落地页标题改了一行”时，CEO 仍判断这个 delta 改变了什么。若它只影响表达而没有改变用户、offer、渠道或信任假设，则产品决策保持不变，不需要机械重做 Objective。

### 空 ledger

heartbeat 发现没有 Goal 在执行时，CEO 先重新审视当前公司的最重要不确定性和薄弱链条。它可能派发最有价值的 Goal，也可能先写清一个会改变后续工作的战略结论或进入 Objective 流程；不能只说“等待数据”然后休息。

## 验收标准

- [x] AC1：CEO charter 明确战略制定、因果推理、自我批判和持续反思是首要职责；DONE 仍不被重新验收，但其战略含义必须被处理。
- [x] AC2：新增 `think-strategically` 与四个原子 skill，名称、description 和正文职责清晰；它们不包含统一评分、PASS/FAIL、固定调用顺序或强制输出模板。
- [x] AC3：CEO loadout 包含上述五个 skill；researcher、builder、growth、verifier 的 loadout 不变。
- [x] AC4：AgentSpec 提供默认关闭的声明式战略模式；只有 `agents/ceo.yaml` 开启。缺失或非法配置按 never-brick 原则降级为关闭。
- [x] AC5：开启战略模式的事件 wake 在 inbox 内容之前明确要求调用 `think-strategically`；默认模式、所有 worker 事件 wake 与 worker `idle=stop` heartbeat 保持 byte-identical。
- [x] AC6：CEO proactive heartbeat 仍明确调用 `when-idle`。ledger 忙时仍一行结束；ledger 空时明确转入 `think-strategically`，且不再要求唯一结局为派发 Goal。
- [x] AC7：`find-opportunity` 将 business form 表述为可修订先验；`set-objective` 澄清 PASS 只基于当前证据、后续新信息仍可触发反思；独立审核与 `PASS → BUILD` 不变。
- [x] AC8：没有新增 blocking hook、第二套公司记忆、机会评分器、`VALIDATE` verdict、统一商业流程或 worker/verifier 认知改造。
- [x] AC9：相关 role config、wake prompt、skill catalog、loadout 与回归测试通过；现行 backend spec 与新行为一致。
- [x] AC10：完成一次不泄露期待答案的 forward test，并保存原始观测；V1 不以人工编造的综合分数宣称“战略思考质量已解决”。

## 不在范围内

- 不重做 thirdtest 的 NCLEX 产品或替它作出新的商业结论。
- 不在本任务中证明需求一定真实、产品一定有效或市场一定存在。
- 不为软件、服务、内容、SEO、信息产品分别建设完整 business flow。
- 不改 worker、verifier、Goal 验收或 Hub 协议。
- 不要求每个 Objective 同时提出多个产品方案。
- 不新增固定实验设计流程、机会红队角色、商业 viability 分数或硬阈值。
- 不用 Hook、marker 或 transcript parser 猜测 CEO 是否“真的思考过”。
- 不改 `/company` 的存储模型、导航协议或写入工具。

## 已接受的 V1 风险

- Prompt 只能确定性要求调用，不能数学上保证思考质量；先通过真实运行观察模型如何使用这些工具。
- 高自由度 skill 可能产生空话、重复反思或过度推翻；本任务故意不提前用模板压死，后续只针对已观察到的失败收紧。
- 每个事件 wake 增加思考会提高 token 和延迟；CEO 是战略角色，这个成本在 V1 中被接受，worker 不承担该成本。
- 空 ledger 可以以战略判断而非 Goal 结束，可能重新出现“看似思考、实则不前进”；heartbeat 仍禁止立即休息，实际退化形态留给运行观测。
