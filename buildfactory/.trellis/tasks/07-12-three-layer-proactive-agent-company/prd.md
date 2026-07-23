# 重构三层主动 Agent 公司架构

## 文档状态

- 阶段：需求与技术设计已收敛，待用户审核
- 当前只做规划，不进入实现
- 本文记录已经确认的第一版产品原则、边界与验收标准

## 目标

把当前以 CEO 为中心、部门被动接单、工作大体串行的二层结构，重构成一个能够长期主动推进工作的三层 Agent Company：

1. CEO 负责公司方向、组织结构和跨部门取舍；
2. Department 围绕自身 Objective 主动发现并创建 Goal；
3. 一次性 Worker 并发执行 Goal，完成后退出；
4. 独立、一次性的 Verifier 实例继续承担 Objective 与 Goal 结果的质量门禁，并允许最多 3 个审核并行；
5. 某个实验可以存在必须经过自然时间才能读取的观测窗口，但公司本身不存在“等待”这一经营状态；观测窗口内仍必须继续推进其他有意义的工作。

## 背景与当前问题

当前系统已经具备常驻 Agent、Standing Objective、Goal Hub、Inbox、Verifier、Company State、角色创建和容器调度等基础能力，但整体行为仍存在以下偏差：

- CEO 实际承担了过多发现、拆解和派发工作，部门缺少真正的决策权；
- Researcher、Builder、Growth 等角色更像被动执行者，而不是围绕 Objective 主动经营的部门；
- CEO 的 idle 策略会在发现任意进行中 Goal 后停止思考，使全公司行为近似串行；
- 当前 Goal 的长期决策者与具体执行者没有清晰分层；
- 原始 Ledger 暴露过多编排内部状态，不应成为 Agent 自由读取的共享文件；
- 静态五角色结构无法适应不同 business mode 所需的不同组织形式。

本任务完成后的第一次运行不是对旧公司 test 的升级或迁移，而是创建一个全新的 Agent Company test。旧 test 保持原样，仅作为行为证据和前后对照使用。

### 真实运行证据（thirdtest，2026-07-12）

以下事实来自 thirdtest longrun 的 telemetry、session transcript、Goal ledger、容器日志与 Company State，用来约束第一版设计，而不是预设实现方案：

- 全角色 fresh-per-wake 后，CEO 能稳定重新调用战略入口，但每个 heartbeat 都需要重新读取 Company State 并重建判断。Stripe 纠正事件之后的 4 次 CEO heartbeat 全部得出同一个“工作在途、等待 07-19/07-25 数据”的结论，共耗时约 510 秒、成本约 3.63 美元；说明“每次都深入思考”与“没有新决策时低成本停下”必须被明确区分。
- 当前 Builder、Growth、Researcher、Verifier 即使没有新消息或职责内工作，也都会每 15 分钟启动 fresh session、检查状态再 stand down。Stripe 纠正后的约 100 分钟内，五个角色共完成 23 次 wake，成本约 15.71 美元；绝大多数没有产生新 Goal、判断或交付。Verifier 与执行 Worker 不应运行主动 heartbeat 的需求由此获得直接证据。
- CEO 在收到 operator correction 后，已经把 crypto reshape 降级为“仅保留在途能力探针”，但没有取消或更新原 Goal。该 Goal 首次执行超时后，Hub 仍按旧 intent 重试，并在约 3 小时后把“这是 crypto reshape 的第一块产品”原样交给 Builder；Builder 随后真实部署了 `polywhale.foundagent.net`。这证明 Company State 中重新解释一个 Goal，不能改变 Scheduler 中已经确认的控制状态和投递载荷；战略变化必须通过确定性的取消语义作用于 Goal。
- Builder 在执行 crypto 支付探针时生成了自托管钱包，并把包含私钥材料的 `WALLET-SECRET.md` 以 `0644` 权限写入共享 `/company`。私钥未进入已检查的 Worker 源码，但该行为说明 Worker 只有 Company State 这一持久化出口时，会把运行秘密误当作公司知识保存；三层架构必须把可共享事实、Worker 会话状态与 secret material 的存储权限分开。
- Fresh CEO 会根据本轮选择读取的 `/company` 路径形成判断；相邻 wake 曾分别得出“真实 sale 可以挽救 NCLEX”和“即使 sale 也无价值”的冲突结论。信息存在于 `/company` 并不足以保证被当前决策完整取回，因此长期共享记忆还需要可发现、可更新且不会留下相互竞争的现行判断。
- CEO 后续把 Notesale、SEO、Quora 与 Pinterest 的未来读取日期解释成全公司的 `HOLD`，在 Goal ledger 为空时连续得出“所有可做的事情已经完成，不应再 Dispatch”的结论。这个结论把“某条实验线现在不应改动”错误推广成“公司没有其他值得推进的工作”，忽略了并行开辟新产品线、测试其他渠道、继续理解买家和改进不污染当前实验的产品部分。时间门槛只能约束对应实验，不能成为公司停止经营的理由。

## 核心术语

- **Company Objective**：公司长期维持的总方向，由 CEO 负责维护。
- **Department Objective**：某个部门持续负责的结果边界，由 CEO 设定或调整，并交给部门自主经营。
- **Goal**：为推进 Department Objective 而创建的、前置条件已经满足、现在即可由一个 Worker 执行和验收的小型具体目标。
- **Department**：常驻的决策 Agent。它主动规划、创建 Goal、吸收结果并决定下一步，不承担长时间的具体执行。
- **Worker**：围绕单个 Goal 临时启动的执行 Agent。Goal 进入终态后销毁。
- **Verifier instance**：围绕单次审核临时启动的独立 Agent。它不属于 Company 的常驻组织，不维护 Objective、Notes 或长期 session，提交一次有效 verdict 后即销毁；系统最多同时运行 3 个。
- **Verifier Manager**：确定性的审核编排组件，负责审核队列、最多 3 个并发实例、review capability、verdict 接收与实例回收。
- **Hub / Scheduler**：确定性的编排层，拥有 Goal 状态、队列、并发和运行生命周期的真实状态。

## 已确认的产品原则

### 1. 三层职责

#### CEO

- 长期维护 Company Objective；
- 决定公司当前需要哪些 Department；
- 为每个 Department 设定和调整 Department Objective；
- 处理跨部门冲突、资源取舍和最终战略决策；
- 默认不包揽各部门内部的 Goal 拆解与具体执行。

#### Department

- 是常驻、主动的管理 Agent；
- 每次被唤醒后，根据 Department Objective、Company State、自己的 Goal 状态与新消息判断下一步；
- 主动创建 Goal，并把具体工作交给 Worker；
- 跟进 Worker 与 Verifier 的反馈，整合结果，继续立项或调整方案；
- 可以产生战略建议，但最终跨部门取舍仍由 CEO 决定。

#### Worker

- 一次只接收一个 Goal；
- 只获得完成该 Goal 所需的上下文和能力；
- 不维护 Objective，不参与组织治理，不再创建下级 Worker，也不自我验证；
- Goal 进入终态后结束运行并被销毁；仅提交一次结果不会提前销毁 Worker；
- 第一版只提供一个全公司共用的通用 Worker 模板，不为 Strategist、Researcher、Builder、Growth 分别预设专属 Worker 类型；
- Department 通过 Goal 描述需要的结果并提供必要上下文，Hub / Scheduler 使用统一模板启动 Worker；
- 通用 Worker 获得共同的基础 instruction、执行能力、完整 Company State 读写能力和结果提交方法，但不获得任何治理权限；
- Worker 与 CEO、Department 一样，可以直接读取和写入完整 `/company`；Researcher Worker 的结论、Builder Worker 的交付物以及其他需要长期保留的成果，都由 Worker 在提交结果前写进 Company State；
- Verifier instance 可以读取完整 `/company`，但保持只读，避免审核者修改自己正在判断的证据；
- Department 专属 Worker Skill、专属工具组合或专属执行模板，等真实运行暴露稳定缺口后再增加；
- 一个 Goal 在逻辑上只分配给一个 Worker；Worker 的生命周期覆盖该 Goal 的执行、提交、Verifier 审核与可能发生的返工；
- Worker 首次提交结果后不立即销毁。Verifier 判定 FAIL 时，反馈必须回到同一个 Worker 会话继续修改，不能默认换一个失去上下文的新 Worker；
- Worker 只有在 Goal 达到 PASS、总时间耗尽，或收到独立的显式取消控制后才销毁；
- Worker 自身无权取消 Goal，也不能把“取消”当作无法完成时的退出方式；只有拥有控制权限的 Department 或 CEO 能通过 Scheduler 发出取消动作；
- 同一个 Worker 可以围绕同一个 Goal 产生多次执行 attempt，但不能转去处理第二个 Goal；
- 从 Worker 启动到 Goal 终态期间，该 Worker 持续占用一个全局 Worker 名额，因此同时处于该生命周期中的 Worker 不得超过 5 个。

### 2. 动态 Department

- CEO 可以根据当前 business mode 按需创建 Department，并通过独立的 Department Objective 流程调整已创建 Department 的方向；
- 第一版只允许从有限的 Department 模板白名单中选择，避免凭空生成任意运行配置；
- 第一版模板白名单固定为以下四种：
  - **Strategist**：持续研究产品、用户、机会、商业模式与战略选项，向 CEO 提供判断和方案，但不替 CEO 做最终跨部门取舍；
  - **Researcher**：围绕已明确的问题获取一手或二手证据、验证关键假设并形成可复用结论；
  - **Builder**：把已选择的方向转化为可运行、可交付、可验证的产品与技术资产；
  - **Growth**：负责分发、内容、获客、渠道实验、转化与增长反馈；
- 新架构不要求把现有 Researcher、Builder、Growth 的运行实例或 session “迁移”为 Department。它们现有的 charter、Skill 配置与工具组合只作为内部模板的可复用素材；新 test 中的 Department 始终由 CEO 从公开选项目录首次创建并绑定 Objective；
- Strategist 作为新增 Department Manager 模板加入目录；Sales、Operations 等其他模板等真实运行暴露职责缺口后再增加；
- 第一版同一种模板最多只能创建一个 Department；四种模板因此也构成动态 Department 数量的确定性上限；
- 第一版没有 Department 退役、删除、合并或重新创建功能；创建后的 Department 持续存在，需要改变职责时只能由 CEO 提交新的 Department Objective 并经过 Verifier；
- 公司首次启动时，Agent / 经营内核只有 CEO；确定性基础服务包括 Hub / Scheduler、Verifier Manager、Provisioner、Worker Manager 与 peripheral，但不预先运行任何 Verifier instance、动态 Department 或 Worker；
- CEO 必须先理解 Company Objective 与当前 business mode，再自主决定需要哪些 Department，而不是由系统替它选择固定组织；
- CEO 发起创建时必须同时提交 `Department 选项 ID + 初始 Department Objective`；选项由确定性方法校验白名单、唯一实例和数量上限，不交给 Verifier 判断；
- Verifier 只审核其中的初始 Department Objective 是否清晰、可经营和符合 Company Objective；只有 Objective 通过后，Provisioner 才创建并启动 Department；
- 第一版不允许先启动一个没有 Objective 的空壳 Department，也不引入“运行中但等待补 Objective”的中间状态；
- 选项确定性校验失败或初始 Objective 审核失败时都不创建 Department；Objective 反馈返回 CEO 修改后重新提交；
- Department 创建本身不经过 Verifier，只由确定性权限、模板和唯一实例规则约束。Department Objective 的首次设定与后续修改仍必须独立经过 Verifier；
- Strategist 即使在行为上接近“影子 CEO”也可以接受，最终取舍权仍属于 CEO；
- Hub / Scheduler、Verifier Manager 与 CEO 属于固定内核，不是可动态增删的 Department；Verifier instance 是按审核请求即用即删的临时执行单元。

### 3. Objective 与 Goal

- Objective 表达持续负责的方向和结果边界，不应退化成一次性任务列表；
- Goal 表达可以真正执行、交付并验证的具体结果；
- Goal 必须足够小、边界明确，并且在创建时已经具备执行所需的前置条件；它不能承担长期路线、未来观察窗口或“等某件事发生后再做”的占位职责；
- Goal 一旦被 Scheduler 接受，就是必须持续尝试直到达成的执行承诺；Worker 不能用 `cannot_execute`、`blocked` 或主观“做不了”提前退出；
- Verifier FAIL 只表示同一个 Worker 需要依据反馈继续返工，不能因为失败次数达到某个数字而终止 Goal；
- Goal 唯一的执行失败来源是超过确定性的总时间限制。前置条件判断错误、实现困难或多次验收失败都会继续消耗这段时间，直到 PASS 或时间耗尽；
- Goal 在 FIFO 队列中的等待时间不计入总时间限制；只有真正获得并发名额且 Worker 成功启动时，Scheduler 才写入一次固定的绝对 `deadline_at`；
- `deadline_at` 一经写入便不可因执行汇报、Verifier 审核、Verifier FAIL、返工 attempt、进程重启或 Scheduler 重扫而重置或顺延；Worker 执行、结果提交、Verifier 审核和所有返工共同消耗这一段总时间；
- 截止时刻到达时，只要 Goal 尚未获得 Verifier PASS，就形成时间失败，Scheduler 终止对应 Worker 并释放并发名额；因此 Verifier 耗时也属于该 Goal 的履约成本；
- 第一版由系统级通用 Worker 策略统一提供 `goal_timeout_secs`，默认固定为 `10800` 秒（3 小时），并由 Scheduler 强制执行；它不是 Goal 内容的一部分，CEO、Department、Worker 都不能修改，也不能为单个 Goal 覆盖；
- 只有 operator / 系统配置能够在部署级别调整 `goal_timeout_secs`；调整只作用于之后启动并写入 `deadline_at` 的 Goal，不追溯修改已经运行的 Goal；
- “Goal 必须达成”只在其业务意图仍然有效时成立。业务意图撤回属于控制面变化，不属于 Worker 执行失败；
- 第一版保留显式 `cancel`：创建该 Goal 的 Department 可以取消自己的非终态 Goal；CEO 在 Company Objective、Department Objective 或战略取舍改变时，可以取消任意受影响的非终态 Goal；Worker 与 Verifier instance 无权取消 Goal；
- `cancel` 通过 Scheduler 确定性地把 Goal 置为终态 `cancelled`，记录操作者、原因与时间；若 Worker 已启动，Scheduler 必须终止该 Worker 并在其真正退出后释放并发名额；
- 第一版不提供 `supersede` 或 Goal 间替代关系。业务方向改变时，控制者只需要显式取消旧 Goal；如果还需要另一项工作，再按普通流程创建一个彼此独立的新 Goal；
- 取消不计作执行失败，也不能改写已经发生的外部副作用；全部取消动作与终止结果必须可审计；
- Department 不得创建内容为“等待某日期”“等待外部回复”“等数据成熟后再读取”的 Goal；这些未来条件属于实验状态、Company State、Notes 或外部事件订阅，不进入 Goal Ledger；
- 外部条件真正到达后，它以事件消息唤醒相关 Department；Department 再基于当时事实创建一个新的、立即可执行的 Goal；
- “现在建立监控”“现在发送请求”“读取此刻已经存在的数据”可以是 Goal，因为它们现在即可完成；“保持 Worker 存活直到未来有结果”不是 Goal；
- 第一版不新增 `blocked` 或 `waiting_external` Goal 状态；
- 正常控制路径为 `CEO -> Department Objective -> Department Goal -> Worker 执行`；
- Department 可以查看自己已有 Goal 来自行判断是否重复立项；第一版不做语义级自动去重；
- Company Objective、Department 创建、Department Objective 与 Goal 状态变化，都必须通过确定性方法发生，不能靠 Agent 直接改编排文件；
- Goal 状态机第一版使用 `open -> claimed -> running -> reported -> verifying -> done` 主路径；Verifier FAIL 从 `verifying` 回到同一个 Worker 的 `running`，任一非终态可因显式控制进入 `cancelled`，Worker 启动后的固定截止时间耗尽则进入 `failed_time`；
- `done`、`failed_time`、`cancelled` 是终态；第一版不保留含义模糊的通用 `killed` 终态。

### 4. 并发与防空转

- Worker 采用全公司共享的并发上限，第一版固定为最多同时运行 5 个；
- Hub / Scheduler 必须允许多个互不依赖的 Goal 并行排队和执行；
- 一个 Goal 只有在真正获得 Worker 名额并启动对应 Worker 后才占用并发；排队中的 Goal 不占用名额；
- 当 5 个名额已满时，后续可执行 Goal 按 Hub 接收并确认入队的时间做全局 FIFO 排队；
- 第一版不设置 Goal priority、Department 配额、抢占或插队；任一 Worker 达到终态并释放名额后，Scheduler 启动队首 Goal；
- 防空转采用单一判定：只要 Ledger 中存在任一非终态 Goal，就认为执行管线已有明确工作，不触发防空转事件；
- `open`、`claimed`、`running`、`reported`、`verifying` 都属于非终态；Ledger 为空或全部 Goal 都是 `done / failed_time / cancelled` 时，才触发防空转；
- 非终态 Goal 的异常卡死由 deadline / watchdog 负责重试；达到 Goal 的总时间限制后才转为时间失败，不使用 Verifier 失败次数作为终止条件；
- 不要求所有 Department 或 5 个 Worker 永远满负荷；
- “等待”不是公司级经营状态。自然时间只能形成某个实验或外部依赖的局部观测窗口，不能形成一个等待中的 Goal；该窗口可以要求暂时不改动对应变量，但不能授权 CEO 或 Department 全面 `HOLD`；
- 当一条工作线需要经过自然时间才能读取结果时，CEO 或 Department 必须保留这条测量线，同时继续推进与其不冲突的其他产品线、渠道增长、买家研究、产品改进、商业模式验证或可交付工作；
- “继续推进”不等于为了填满并发槽而制造 Goal。新工作必须产生用户价值、可复用资产、真实市场反馈或能改变产品判断的证据；但“未来某日再读数据”本身不能被算作当前工作；
- 空 ledger 不是纪律性停止的证据，而是工作管线需要被重新开辟的信号。常驻决策 Agent 必须重新审视尚未覆盖的产品、买家、渠道和因果链，形成新的有效工作，不能只读取旧结论后复述 `HOLD`；
- 只有局部实验需要稳定：不得为了显得主动而反复修改同一个正在测量的价格、页面或渠道，从而污染结果。保持局部实验不变与并行推进公司其他工作必须同时成立；
- 只要公司未被明确停止，就不能同时处于“没有在执行的工作、没有可执行 Goal、没有待启动 Goal、也没有 Agent 正在开辟下一项工作”的状态；
- 防空转必须由确定性状态检查触发 Agent 行动，不能只依赖 Prompt 中一句“保持主动”。
- 防空转条件成立时，Hub / Scheduler 同时向 CEO 与当时所有活跃 Department 各投递一条 `company_idle` 系统事件；若当前没有活跃 Department，则接收者只有 CEO；
- `company_idle` 在公司层面同时投递，但仍遵守每个接收者自身的单 wake、FIFO 与成功后确认规则，不会中断该 Agent 正在处理的消息；
- CEO 收到该事件后只在自己的层级检查 Company Objective、组织结构与 Department Objective；Department 在各自层级主动寻找并创建可执行 Goal。该事件不授权 CEO 直接管理 Worker，也不授权 Department 越权修改 Objective；
- Worker 与 Verifier instance 不接收 `company_idle`，因为它们没有主动经营和立项权限；
- 对每个接收者，系统同时最多保留一条尚未成功处理的 `company_idle`；同一 Agent 的旧空转事件仍在排队、运行或重试时，不得继续堆叠新空转事件；
- 某个 Agent 成功处理自己的 `company_idle` 后，Hub / Scheduler 立即重新检查 Ledger：若仍无非终态 Goal，立即向该 Agent 投递下一条 `company_idle`，不等待其 `heartbeat_secs`；若已经出现非终态 Goal，则不再产生新的空转事件；
- 不设置“等所有接收者都完成本轮”这一全局屏障。某个 Agent 的空转事件失败时，沿用普通消息规则重试同一条消息，只阻塞它自己的空转循环；其他 CEO / Department 各自成功后仍可独立复查与继续；
- 已经入队的 `company_idle` 仍遵守 FIFO 和成功后确认，不能因为另一 Agent 已经创建 Goal 就被静默删除；但该 wake 会读取最新 Objective 和状态，系统不会再为其续发下一条空转事件；

### 5. Verifier

- 保留现有独立审核原则，并继续坚持“执行者不能同时做最终审核者”，但不再保留一个常驻 Verifier 角色；
- 每个审核请求由 Verifier Manager 启动一个全新的临时 Verifier instance；实例只获得当前 `review_id`、审核对象、标准、必要的只读资料和一次性 verdict capability；
- 单个 Verifier instance 一次只审核一个对象，提交一次有效 PASS / FAIL 后立即销毁，不接收普通 Inbox、不运行 heartbeat、不保存 Notes，也不在不同审核之间续接 session；
- Verifier 使用独立并发池，第一版最多同时运行 3 个；该上限与最多 5 个 Worker 的执行池相互独立，Verifier 不占 Worker 名额；
- Company Objective、Department Objective 与每次 Worker 结果提交产生的 review 共用同一个全局 FIFO 审核池；不存在单独的 Objective 审核池或 Goal 审核池；
- 每次 Worker 提交一轮结果都创建一条新的 review 和一个新的 Verifier instance；若本轮 FAIL，同一 Worker 返工并再次提交时，再创建另一个全新的 Verifier instance，不复用上一轮审核会话；
- Company Objective 与每个 Department Objective 的首次设定和后续修改，都必须经过 Verifier 后才能生效；
- Department 的公开选项选择和创建不属于 Verifier 的审核对象，只执行确定性校验；第一版不存在 Department 退役或重新创建动作；
- 每个 Worker 的 Goal 结果都必须经过 Verifier 验收：PASS 后 Goal 才能完成，FAIL 则把具体反馈返回同一个 Worker 继续返工，并把闭环状态通知负责该 Goal 的 Department；
- Goal 的创建与排队本身不需要 Verifier 预审；Verifier 审核的是最终结果是否满足已经接受的 Goal；
- 审核链路必须 fail closed：Verifier 缺席、身份不符或结论不完整时，不得默认通过；
- Verifier instance 不参与主动经营，也不占用动态 Department 名额。

### 6. 状态、数据与消息

- 对 LLM Agent 而言，公司状态树中唯一可直接浏览的路径是 `/company` 及其全部内容；`control / telemetry / reviews / workers / inbox / ledger / departments / notes / agents / sessions` 等编排目录都不挂载给 LLM runtime；
- Agent 每次启动或 wake 时，都必须获得 Company State 的入口信息，再按当前角色与任务自主决定读取哪些具体公司资料；
- Heartbeat、Objective 变更、Worker 结果、Verifier 结论和外部消息，都可以触发相关常驻 Agent 更新判断；
- 长期共享事实沉淀在 Company State，而不是分散在每个 Agent 的私有长期记忆里；
- 每个常驻 Agent 可以拥有一份轻量 Notes，用于向自己的下一次 wake 传递临时上下文；Notes 由 harness 读取并注入 Prompt，Agent 通过确定性方法更新，不能浏览原始 Notes 文件夹；
- Company State 必须继续提供统一、可发现的公司入口；现行判断需要通过 `MAP.md -> OVERVIEW.md -> leaf` 或等价权威索引指向唯一当前版本，旧结论不得与新结论并列成无法区分的“现行事实”；
- Notes 只属于单个常驻 Agent 的跨 wake 便签，不是其他 Agent 的共享事实源，也不能替代 Company State；
- Objective、Inbox message、Notes 与可用方法说明都由 harness 注入当前 Prompt 或通过确定性工具提供；它们的原始存储目录对 Agent 不可见；
- 原始 Ledger 属于 Hub / Scheduler 的编排内部状态，不作为 Agent 可浏览的文件夹；
- CEO 和 Department 只能通过受控方法查询与自身权限相符的摘要，例如公司运行概况、自己的 Goal、单个 Goal 状态和 Worker 占用情况；
- Worker 看到被分配的 Goal、完整且可写的 `/company`、临时运行 workspace 和结果提交方法；持久成果必须写到 `/company`，结果只引用对应 Company State 路径，不再依赖 Agent 可见的独立 artifact 存储；
- Worker 对 `/company` 的写入在 Verifier 审核前就会发生；Verifier FAIL 时原 Worker 在原处继续修改。第一版不为失败、超时或取消的 Goal 自动回滚 Company State 写入，必要清理由负责的 Department 后续决定；
- account secret、运行凭证和 Worker 私有会话材料由 runtime / 工具层管理，不作为可浏览的公司状态目录，也不能作为 Company State 或 Notes 发布；系统不得自动复制 Worker home 或 credential material 到 `/company`。

#### 唤醒机制

- CEO 与所有活跃 Department 都是常驻决策 Agent，采用“事件即时唤醒 + 独立主动 heartbeat”的混合机制；
- 事件唤醒用于处理 Objective 生效、Department 协作消息、Worker / Verifier 结果、外部消息以及其他明确状态变化；Agent 处于空闲时，相关事件应立即触发下一次 wake；
- 主动 heartbeat 用于在没有新消息时重新观察 Company Objective 或 Department Objective，并主动判断下一步；它不能因为公司已有其他 Goal 在运行就自动退化成停止思考；
- 同一个 CEO 或 Department 同时最多只能运行一个 wake；不允许为同一个常驻 Agent 并发启动两个模型调用；
- Agent 正在一次 wake 中时，新到事件只进入它的 Inbox，不中断当前模型调用，也不另起一个并发 wake；
- 当前 wake 结束后，只要 Inbox 中已有未处理事件，就立即启动下一次 event wake，不再等待 heartbeat 到期；
- 一次 event wake 只交给 Agent 一条最早的未读消息；第一版不把多条未读消息批量拼进同一个 Prompt；
- Inbox 必须先以 peek / lease 方式取得队首消息，不能像当前实现一样在模型开始处理前就推进读取 cursor；
- 该消息对应的 wake 成功结束后才确认已读，然后立即处理下一条未读消息；处理期间到达的其他消息继续保持未读并按顺序排队；
- 只要 Inbox 仍有未读消息，就连续运行 event wake；主动 heartbeat 不能插入未读消息队列之前；
- heartbeat 采用“安静计时器”，而不是固定墙钟时刻：只有 Agent 当前没有运行且 Inbox 已清空时才开始计时；
- 任意新事件到达、event wake 开始或消息仍在重试时，都不会额外生成 heartbeat；所有消息处理完成后，从最后一次 wake 结束时重新开始安静计时；
- 安静时长到期后才生成一次 heartbeat wake；heartbeat 完成后重新计时；
- 如果消息持续不断，heartbeat 可以持续推迟，因为每次 event wake 仍会重新注入当前 Objective，并要求常驻决策 Agent 基于 Objective 处理事件与判断后续行动；
- CEO 配置与每个 Department 模板都声明确定性的 `heartbeat_secs`；第一版所有内置配置默认值均为 `900` 秒；
- CEO 与不同 Department 的 `heartbeat_secs` 可以由各自配置 / 模板分别覆盖，但该字段只能由系统配置维护，Agent 自身没有读取后写回或动态修改周期的权限；
- 动态 Department 创建时继承其模板中的 `heartbeat_secs`，后续模板调整不会被 Agent 当作 Objective 或 Goal 自行修改；
- 如果 wake 超时或运行失败，该消息不得被自动标记为已读；
- wake 超时或运行失败后，同一条消息继续留在队首，使用相同 `message_id` 并在确定性短退避后再次触发 event wake；
- 第一版不设置消息处理重试上限，也不把失败消息自动移入 dead-letter 或跳过；只有某次 wake 成功结束后才确认该消息；
- Hub 必须在入队前校验消息格式和大小，尽量防止确定性的坏消息永久堵住接收方；每次失败与重试都必须记录；
- 一个 Agent 被队首消息堵住时，只影响该 Agent 自己，不能阻止其他常驻 Agent 和 Worker 继续运行；
- 串行边界只限于同一个常驻 Agent；CEO、不同 Department 与不同 Worker 之间仍可并行运行；
- heartbeat 与公司防空转是两种不同机制：heartbeat 属于每个常驻决策 Agent，自主周期运行；防空转属于 Hub / Scheduler 对全公司工作管线的确定性检查；
- Worker 不运行 heartbeat。它只因首次 Goal、同一 Goal 的 Verifier FAIL 反馈、取消或终止控制事件继续运行；
- Verifier instance 不运行常驻 loop 或 heartbeat；Verifier Manager 只在审核请求到达且并发名额可用时创建它；
- 防空转不使用全局轮次屏障，而是为每个 CEO / Department 维护独立的单条在途约束；成功处理后立即复查并决定是否续发，因此一个接收者失败不会把其他接收者拖入等待。

#### CEO 的按需查证

- CEO 默认不接收 Department 内每个 Goal 的进度、Worker 提交或 Verifier 结论推送；Goal 的正常闭环只返回负责它的 Department；
- Department 仍可在需要跨部门取舍、调整 Objective 或处理部门级阻塞时，显式向 CEO 上报，但这不是每个 Goal 的自动通知流；
- CEO 只获得一个统一的只读 `inspect` 方法，不建设多套报表或查询 API；
- `inspect` 不带筛选条件时返回公司总览：活跃 Department 与 Objective、各状态 Goal 数量、异常 / 失败概况以及 5 个 Worker 名额的占用情况；
- `inspect` 指定 Department 时展开该部门的 Objective、Goal 列表与状态；指定 Goal 时进一步展开对应 Worker、attempt、Verifier 结论和成果位置；
- `inspect` 只读取 Hub / Scheduler 提供的受控视图，不允许修改状态，不返回原始 Ledger，也不返回 Department 内部协作消息；
- `inspect` 能力始终可用，但默认不调用，也不是 heartbeat 或普通决策的固定步骤；
- CEO 的基础 Skill 必须教育它：只有出现事实不确定、部门说法冲突、异常状态，或重大取舍需要核实时才调用 `inspect`；
- Skill 同时明确禁止把 `inspect` 当作持续轮询仪表盘，或借查证重新接管 Department 的日常 Goal；
- CEO 只在自己判断需要核实事实时主动调用 `inspect`，系统不因每条内部进展自动唤醒 CEO。

#### Department 协作消息

- Department 之间允许直接协作，但所有消息必须先发送给 Hub，由 Hub 校验身份、目标与格式后转发；Department 不能绕过 Hub 直接写对方 Inbox；
- 协作消息不创建 Goal、不修改 Objective，也不对接收方产生强制执行义务；接收方根据自己的 Objective 判断是否立项、回复、拒绝或升级给 CEO；
- 第一版协作消息只表达以下逻辑字段：`message_id`、`time`、`from`、`to`、`subject`、`body`；
- 第一版不提供 `kind`、`reply_to_message_id`、`related_goal_id` 或其他会把普通消息变成工作流协议的字段；需要表达请求、回复或 Goal 背景时，直接写进 `subject` 与 `body`；
- Hub 根据工具适配层绑定的实际调用身份生成 `from`，不接受调用方自报发送者；同时验证 `to` 是活跃 Department，伪造发送者、未知接收方和格式错误都应拒绝并记录；
- Hub 可以为系统审计保留协作消息事件，但该审计记录属于编排层，不进入 Company State，也不自动对 CEO 开放；
- CEO 第一版既不被抄送 Department 内部协作消息，也没有读取这些消息的默认方法；以后只有真实需要出现时才增加知情能力；
- 需要长期复用的结论仍由负责的 Agent 主动沉淀到 Company State，不能把消息历史当作公司的长期记忆。

### 7. Prompt、Skill 与确定性能力

- 基础 Skill 本质上是角色的操作说明与判断方法，不等于系统能力本身；
- 创建 Department、设定 Objective、发送 Goal、读取状态、提交结果、写 Notes 等能力，需要由系统提供确定性方法；
- 第一版不把 `/shared/control/hub.sock` 或随机 capability token 挂载给 Agent，也不把控制传输细节做成 Agent 需要理解的概念；
- Agent 只调用 loadout 中已经提供的确定性工具。工具适配层由 orchestrator 在启动该 Agent 时绑定 actor，业务参数不接受调用方自报 `from`；这只用于减少误用和保持审计归属，不试图抵御主动破解容器的恶意 Agent；
- CEO、Department、Worker 与临时 Verifier instance 应通过 skill / 固定模板获得不同的基础 instruction、自带工具权限和数据视图；
- CEO 必须拥有一个基础的“组建与调整 Department” Skill。它需要说明：何时应该创建或调整部门、如何根据 Company Objective 判断缺少哪类职责、如何比较公开名称与描述、如何调用确定性方法发起创建，以及创建后如何设定 Department Objective；
- 系统必须提供一个只读的“读取可选 Department”方法。它只向 CEO 返回每个选项的稳定 ID、公开名称和面向经营判断的简短描述，例如 `Strategy Department` 及其职责说明；
- 模板目录是当前可创建选项的权威来源，但 charter、Agent spec、Skills、MCP、heartbeat、compose 片段等内部模板结构完全不向 CEO 暴露；CEO 不能凭 Prompt 临时编造一个目录中不存在的 Department 类型；
- Skill 负责教 CEO 做判断和走流程，选项读取方法负责返回公开事实，Department 创建方法负责在内部装载模板并执行确定性变更；三者不能混成一段只能靠模型自觉遵守的文字；
- CEO 只把选项 ID 与初始 Department Objective 交给确定性创建函数；函数在内部装载完整模板并执行校验。CEO 不需要理解、拼装或修改模板的具体样式；初始 Department Objective 仍需经过 Verifier，Objective PASS 后才能进行确定性 provision；
- 专属 Skill 不在第一版凭空设计完整，应先让系统真实运行，再根据行为记录补充；
- Agent 的启动 Prompt 应由稳定角色约束、当前 Objective、必要 Company State 入口、Notes、触发消息与可用方法说明组合而成，具体组合顺序在技术设计中确定。

### 8. 实验优先与可观测性

- 第一版优先把完整闭环跑起来，不提前为尚未观察到的问题加入复杂治理；
- 暂不为重复立项设计语义去重；
- 暂不限制 token / 金钱成本，也不设计 ROI 预算系统；
- 暂不阻止 Strategist 形成强影响力；
- 必须为 CEO、每个 Department、每个 Worker 和每个 Verifier instance 保存完整运行记录，而不只是一条 wake 摘要；
- 每次运行至少保留完整 runtime event stream、模型输出、工具调用与工具结果、stdout、stderr、harness / container log、开始结束时间、触发来源、关联 Goal / review / message、session token 元数据与 usage；不得只保留截断 tail；
- Hub、Scheduler、Worker Manager、Verifier Manager、Provisioner 与 peripheral 的完整进程日志也必须按 company 保存；
- 日志和原始输出存入 Agent 不可见的 `telemetry` / run-log 存储，只供 operator 与测试读取。系统不主动记录 credential 环境值，但如果 Agent 自己把敏感内容输出到 transcript，该内容会按“完整输出”要求进入受限日志；
- 结构化索引继续记录 Objective 变化、Department 变化、Goal / Worker / review 生命周期、Verifier 结论、Notes 变化与公司空转事件，以便后续用实验结果调整机制和 Skill。

### 9. 旧系统模块复用

新架构会复用已经验证过的底层模块，但“代码 / 配置复用”不等于“迁移旧 Agent 实例、session 或 Goal 运行状态”。优先复用：

- Company State 的机制与目录契约，但为新 test 创建全新的空状态实例；
- IME / Inbox 与 wake 机制；
- Goal Hub 的状态机概念；
- Verifier 与 Objective review 的独立审核原则，但不复用现有 Verifier 的常驻生命周期；
- CEO / Department 继续复用常驻 Agent loop；Worker 与 Verifier instance 继续复用 runtime adapter、loadout / overlay，但走临时容器生命周期；
- 现有 role provisioner 中经过验证的动态 compose 生成与启动原语；不复用其“任意 bundle + Department review + retire + Git 落盘”产品语义；
- Worker 复用 broker 中已有的临时同级容器启动与销毁原语，但由 Scheduler 接管队列、并发、deadline、session token 与终态回收；
- Verifier instance 同样复用临时同级容器原语，但由独立 Verifier Manager 管理最多 3 个并发审核，不与 Worker 共用名额；
- broker 当前把“创建容器”和“一次执行”绑在一个 `spawn()` 中，第一版需要将其收敛为可持续一个 Goal 生命周期的创建、执行 / resume、销毁原语；同一个 Worker 的后续返工通过 runtime adapter 的 `resume_token` 继续原会话，不改用常驻 Department provisioner。

允许为三层语义重写 CEO idle 策略、Department 运行方式、Department Objective、受控状态查询、Hub / Worker 调度与动态组织管理。

### 10. 全新 test 的启动边界

- 新 test 使用新的 company identity 与独立状态目录；
- 不复制旧 test 的 Company State、Company Objective、Department Objective、Goal Ledger、Inbox、Notes、Department registry 或 Agent session；
- 新 test 从固定内核和零动态 Department、零 Worker、零 Verifier instance 的冷启动状态开始：CEO 是唯一固定经营 Agent，Hub / Scheduler、Verifier Manager、Provisioner、Worker Manager 与 peripheral 是确定性基础服务；由新 CEO 自行建立 Company Objective 与组织；
- 旧 test 的文件和运行证据不由本任务改写、清空或原地升级；代码、Skill、模板和已验证的底层机制可以作为实现素材复用；
- 第一版不建设旧状态导入器、Ledger 转换器或跨 test session 接续能力。

### 11. V6 / V7 Git 边界

- V7 开发前先把当前完整 V6 实现形成一个可复现的快照提交，并让新分支 `v6` 永久指向该提交；仅创建一个指向旧 HEAD 的分支不足以保存当前未提交改动；
- `main` 与 `v6` 从同一个 V6 快照提交出发；`v6` 停留在 V6，后续 V7 代码直接在 `main` 上继续演进；
- 不创建额外的 V7 feature branch；用户明确选择在 `main` 上进行本次重构；
- V6 快照明确包含当前工作树中的全部 16 个已跟踪修改，以及 `.trellis/tasks/07-13-fourthtest-codex-sol-first-revenue/`；明确排除 V7 规划目录 `.trellis/tasks/07-12-three-layer-proactive-agent-company/`，后者保留在 `main` 进入后续 V7 开发；
- 当前工作区仍有 16 个已跟踪文件修改和两个未跟踪任务目录；创建 `v6` 时必须严格按上述已确认清单形成快照，不能在脏工作区上只移动 branch pointer，也不能误纳入 V7 规划目录；
- 分支整理属于实现前置动作，当前规划阶段不创建分支、不提交、不切换工作树。

## 第一版明确不做

- 不讨论或实现 token、调用费用、烧钱速度与 ROI 预算；
- 不做 Goal 的语义级自动去重；
- 不预先建设完整的部门专属 Skill 库；
- 不做具体 business 场景推演来代替系统实验；
- 不在本任务中解决 Goal 应该归属哪个 run 的最终模型，除非实现闭环时不可避免；
- 不把 Ledger 变成 Company State 的可读文件；
- 不要求所有 Worker 始终占满并发槽位。
- 不迁移或导入旧公司 test 的任何运行状态。
- 不提供 Department 退役、删除、合并、重新创建或 draining 状态；组织在第一版只能从零开始增设 Department，并通过 Objective 更新改变其方向。
- 不提供 `supersede`、Goal 间替代关系或隐式“新 Goal 覆盖旧 Goal”语义；只保留显式 `cancel` 与普通新建 Goal。
- 不为第一版建设抵御恶意 Agent 的容器级身份认证系统；确定性工具绑定 actor 只保证正常调用不会误报身份。

## 验收标准

- [ ] CEO 能从允许的公开选项中按需创建 Department，并通过经过 Verifier 的 Objective 更新调整其方向；第一版没有 Department 退役能力；
- [ ] 公司冷启动时只有 CEO 一个固定经营 Agent，以及 Hub / Scheduler、Verifier Manager、Provisioner、Worker Manager、peripheral 等无经营决策权的确定性基础服务；没有系统预设的 Verifier instance、动态 Department 或 Worker；
- [ ] 第一次架构实验使用全新的 company identity 和独立空状态目录；旧 test 的 Company State、Objective、Ledger、Inbox、Notes、Department registry 与 session 均未导入，旧 test 保持原样可供对照；
- [ ] CEO 调用只读方法时只获得每个 Department 选项的稳定 ID、公开名称和简短描述；无法看到或拼装 charter、spec、Skills、MCP、heartbeat、compose 等内部模板结构；
- [ ] CEO 的基础 Skill 明确教会它如何识别组织缺口、比较公开选项、创建 Department，并为初始或更新后的 Department Objective 发起审核；
- [ ] CEO 无法创建公开选项目录之外的 Department；选项选择不进入 Verifier，但没有 PASS 的初始 Department Objective 时仍无法激活该 Department；
- [ ] 同一模板最多只能创建一个 Department，创建后持续存在；系统不存在退役、删除、合并、重新创建或 draining 接口；
- [ ] Department 创建请求必须同时包含公开选项 ID 和初始 Objective；选项确定性校验失败或 Objective 未获 PASS 时都不会启动 Department；
- [ ] 新 Department 的第一次 wake 已经能够读取生效后的 Department Objective，不存在无 Objective 运行态；
- [ ] Department 创建不产生 Department review 请求；Company Objective 与 Department Objective 的首次设定和每次修改都无法绕过 Verifier；
- [ ] 至少一个 Department 能在没有 CEO 逐条指令的情况下，根据 Objective 主动创建 Goal；
- [ ] Department 能把 Goal 交给一次性 Worker，接收执行结果与 Verifier 反馈，并继续决定下一步；
- [ ] Goal 创建和入队不需要预审，但每个 Goal 的最终结果都必须由独立 Verifier PASS 后才能进入完成态；
- [ ] 每个审核请求只分配给一个全新的 Verifier instance；它一次只审核一个对象，提交 verdict 后被销毁，不保留 Inbox、Notes、heartbeat 或跨审核 session；
- [ ] Verifier 审核池最多同时运行 3 个实例，与最多 5 个 Worker 的执行池相互独立；第 4 个审核请求不会启动第 4 个实例；
- [ ] Company Objective、Department Objective 与每次 Worker 结果提交产生的 review 共用同一个全局 FIFO 和 3 个并发名额，不存在第二套审核池；
- [ ] Worker 每次提交结果都会创建一个新的 Verifier instance；FAIL 后同一 Worker 返工并再次提交时，下一轮使用另一个全新实例，不复用上一轮审核 session；
- [ ] Department 只能创建前置条件已满足、当前可执行、可由一个 Worker 完成的小型 Goal；未来日期或外部条件不会以 `blocked / waiting_external` Goal 留在 Ledger；
- [ ] 外部条件到达时通过事件唤醒 Department，由 Department 在当时创建新的可执行 Goal，而不是恢复一个长期占位 Goal；
- [ ] Worker 完成单个 Goal 后退出，且无法修改 Objective、创建 Department、继续派生 Worker 或完成自我审核；
- [ ] 四种 Department 创建的 Goal 都由同一个通用 Worker 模板执行，第一版不存在按 Department 硬编码的四套 Worker；
- [ ] Verifier 首次判定 FAIL 后，反馈会回到原 Worker 的同一会话继续返工；该 Worker 不会被静默替换，也不会接手其他 Goal；
- [ ] Verifier 连续多次 FAIL 不会因为 attempt 数量触发 Goal 终止；同一 Worker 在总时间限制内持续返工；
- [ ] Worker 没有 `cannot_execute / blocked / waiting_external` 退出路径；未达成的 Goal 只会因总时间耗尽而成为执行失败；
- [ ] Goal 排队期间不消耗总时间；Worker 成功启动时只写入一次固定 `deadline_at`，后续执行、审核、返工和系统重启均不会重置或延长它；
- [ ] Goal 必须在固定 `deadline_at` 前获得 Verifier PASS；到期仍未 PASS 时形成时间失败、销毁对应 Worker 并释放名额，Verifier 审核时间不会被排除在外；
- [ ] 第一版所有 Goal 都使用系统级通用 Worker 策略中的 `goal_timeout_secs=10800`；Agent 和单个 Goal 无法覆盖该值，部署级配置变更不会追溯延长已经启动的 Goal；
- [ ] Department 能取消自己创建的非终态 Goal，CEO 能在战略或 Objective 改变时取消受影响 Goal；Worker 与 Verifier instance 无法调用取消能力；
- [ ] `cancel` 形成独立的 `cancelled` 终态并记录操作者、原因和时间，不会被统计为 Worker 执行失败；运行中的 Worker 被实际终止后才释放名额；
- [ ] 系统没有 `supersede` 方法或 Goal 替代关系字段；方向变化只会显式取消旧 Goal，并在需要时独立创建新 Goal；取消不会声称自动撤回旧 Goal 已经造成的外部副作用；
- [ ] Worker 只在 Goal 进入 `done / failed_time / cancelled` 后销毁，并在容器实际退出后正确释放全局并发名额；
- [ ] 系统能并行执行多个独立 Goal，同时运行的 Worker 永远不超过 5 个；
- [ ] 第 6 个及后续 Goal 保持排队且不启动 Worker；名额释放后严格按全局 FIFO 顺序启动，不发生抢占或隐式优先级；
- [ ] 某个实验处于自然时间观测窗口时，对应测量变量保持稳定，同时公司至少推进一条不污染该实验的其他有意义工作线；
- [ ] CEO 或 Department 不能因为存在未来读取日期、已有实验尚未成熟或某条线暂时没有新数据，就把全公司置于 `HOLD`；
- [ ] 在公司未被明确停止时，如果没有运行中、可运行或排队 Goal，系统会确定性地唤醒有权开辟工作的 Agent；被唤醒者需要产生新的有效工作或正在形成这种工作的实质判断过程，不能以复述旧 `HOLD` 结束；
- [ ] Goal 主路径为 `open -> claimed -> running -> reported -> verifying -> done`；Verifier FAIL 回到同一 Worker 的 `running`，显式取消进入 `cancelled`，固定截止时间耗尽进入 `failed_time`，不存在通用 `killed` 终态；
- [ ] 任一 `open / claimed / running / reported / verifying` Goal 都会抑制防空转；Ledger 为空或仅剩 `done / failed_time / cancelled` 时触发，卡死 Goal 由 watchdog 收敛；
- [ ] 每次防空转触发都会向 CEO 和当时所有活跃 Department 各投递一条 `company_idle`；零活跃 Department 时只唤醒 CEO，Worker 与 Verifier instance 永远不会收到该事件；
- [ ] 同一轮 `company_idle` 的不同接收者可以并行处理，但不会让同一个 Agent 并发 wake、打断队首消息或绕过 FIFO；CEO 与 Department 只能在各自权限层级采取行动；
- [ ] 每个接收者同时最多存在一条未成功处理的 `company_idle`；成功后 Ledger 仍为空会立即续发，不等待 900 秒 heartbeat，出现非终态 Goal 后停止续发；
- [ ] 某个接收者的 `company_idle` 连续失败只会重试该接收者的同一消息，不会阻塞其他接收者成功后的复查与续发；已经入队的事件不会被静默跳过；
- [ ] 防空转测试能够区分“保持局部实验变量稳定”和“全公司无工作”：前者允许，后者必须触发新的经营活动；
- [ ] CEO、Department、Worker、Verifier instance 只能读取和调用符合各自权限的数据与方法；
- [ ] 对所有 LLM Agent，Company State 中只有 `/company` 及其子路径能被直接浏览；`control / telemetry / reviews / workers / inbox / ledger / departments / notes / agents / sessions` 均不存在 Agent 可访问的原始挂载；
- [ ] CEO、Department 与 Worker 能读写完整 `/company`；Verifier instance 能读取完整 `/company` 但无法写入；
- [ ] Worker 能在提交结果前把结论或交付物直接写入 `/company`，Verifier 从这些真实路径验收；FAIL 后同一 Worker 可以继续修改，不会生成独立 artifact 目录或自动回滚；
- [ ] 原始 Ledger 不能被 Agent 当作普通文件浏览，受控查询仍可提供必要运行摘要；
- [ ] 两个 Department 能通过 Hub 交换只包含 `message_id / time / from / to / subject / body` 的普通消息，且消息不会直接创建 Goal；
- [ ] Department 协作消息不存在 `kind`、`reply_to_message_id`、`related_goal_id` 或其他工作流字段；回复关系和 Goal 背景只作为普通正文表达；
- [ ] Department 无法伪造另一个 Department 的身份，也无法向不存在的 Department 投递协作消息；
- [ ] CEO 不会收到、读取或查询 Department 内部协作消息；Hub 的内部审计仍能供系统测试还原路由事实；
- [ ] Department 内的普通 Goal / Worker / Verifier 事件不会自动投递给 CEO；负责该 Goal 的 Department 能正常收到完整闭环结果；
- [ ] CEO 能通过同一个只读 `inspect` 方法查看公司总览，并按 Department 或 Goal 逐层查证必要事实；
- [ ] `inspect` 无法修改编排状态，也不会泄露原始 Ledger 或 Department 内部协作消息；
- [ ] 普通 heartbeat 与常规决策不会自动调用 `inspect`；CEO Skill 明确给出需要查证和禁止例行轮询的边界；
- [ ] CEO 与每个活跃 Department 都能被相关事件立即唤醒，也能在完全没有事件时由各自 heartbeat 独立唤醒；
- [ ] 已有 Goal 正在执行不会从机制上阻止 CEO 或其他 Department 的主动 heartbeat；
- [ ] 同一个 CEO / Department 不会同时出现两个 wake；wake 期间到达的事件不会丢失或中断当前调用，并会在结束后立即触发后续 event wake；
- [ ] 同一 Agent 有三条未读消息时，会按到达顺序产生三次独立 event wake；第一条未完成前，后两条仍保持未读；
- [ ] 一条消息对应的 wake 成功后才确认该消息，下一条随后立即开始；失败或超时不会把消息静默消费掉；
- [ ] 同一消息的 wake 连续失败时保持相同消息身份并持续重试，后续消息不会越过它；失败记录可审计，其他 Agent 仍能并行工作；
- [ ] 一个 Department 的长 wake 不会阻止 CEO、其他 Department 或 Worker 并行运行；
- [ ] Inbox 非空、事件正在处理或失败消息正在重试时，不会插入 heartbeat；队列清空并持续达到设定时长后才触发一次 heartbeat；
- [ ] CEO 与四种内置 Department 模板的默认 `heartbeat_secs` 都是 `900`；系统配置可以分别覆盖，任何 Agent 都不能通过自身工具修改；
- [ ] Worker 不产生主动 heartbeat；Verifier instance 不运行常驻 loop 或 heartbeat，只由 Verifier Manager 为单次审核临时创建；
- [ ] Company State 承担长期共享记忆，常驻 Agent 的 Notes 能跨一次或多次 wake 传递轻量上下文；
- [ ] Company State 的权威入口能指向唯一当前判断，旧判断不会与新判断并列成不可区分的现行事实；Notes 仅对所属常驻 Agent 生效；
- [ ] runtime / 工具层不会把 account secret、credential material、私有会话材料或 Worker home 自动复制到 `/company`；角色 instruction 明确禁止主动把这些材料作为公司知识持久化，但这一规则不会削弱 Worker 对完整 `/company` 的直接读写能力；
- [ ] 每个 CEO / Department wake、Worker turn 和 Verifier review 都保存未截断的 runtime event stream、模型输出、工具调用与结果、stdout、stderr 及 harness / container logs，并能按 agent / wake / goal / review 检索；
- [ ] Hub、Scheduler、Worker Manager、Verifier Manager、Provisioner 与 peripheral 的完整进程日志也按 company 保存；所有 telemetry / run logs 对 Agent 不可见；
- [ ] 现有可复用模块保持复用，已有 Company State、Inbox、Verifier 等关键能力不发生无理由退化；
- [ ] 一次性 Worker 由 Scheduler 通过 broker 的临时同级容器路径启动；常驻 Department provisioner 不会被误用于 Worker，Verifier FAIL 后能够使用原 `session_token` resume 同一 Worker 会话；
- [ ] 新架构至少完成一次端到端实验：CEO 设定组织与 Objective，Department 主动立项，多个 Worker 受全局并发限制执行，Verifier 审核，结果回流并触发后续决策。
- [ ] V7 实现开始前存在一个冻结当前 V6 快照的 `v6` 分支；`main` 从同一快照继续承载 V7，且 V7 规划文件不会被误算进 V6 产品快照。

## 已核对的现有系统事实

- `docker-compose.yml` 目前固定启动 CEO、Researcher、Builder、Growth、Verifier 五个常驻 Agent；它们复用同一个 `agent_loop`，仅角色 key、charter、session 路径等配置不同；
- 当前每个常驻 Agent 的 loop 内部是串行的：一次 wake 运行期间，新消息只会排队，等本次模型调用结束后再处理；不同常驻 Agent 之间可以并行；
- 当前 Hub 是唯一 Ledger writer，负责 Goal 路由、状态机、Verifier 分流和 watchdog，但不负责启动 Worker；
- 当前 broker 已有启动和销毁临时同级容器的原语，但在 compose 中处于 dormant 状态，尚未接入 Hub 队列、并发额度、租约和恢复；
- 当前 Goal Hub 已能同时维护多个 Goal；公司近似串行主要来自旧的 CEO idle / when-idle 决策，而不是 Ledger 只能容纳一个 Goal；
- 当前 `messaging send` 已能把完成通知返回发送者，因此 Department 创建 Goal 的回流基础可以复用；
- 当前 `parent` 语义混合了承接者 / 回复地址，并不是清晰的 `parent_goal_id`；Goal、Department、Worker 的归属关系需要重新建模；
- 当前 Standing Objective 已按 `/agents/<key>/objective.md` 注入每次 wake，但现有治理流程主要围绕 CEO 的公司 Objective，尚无完整的 CEO 管理 Department Objective 机制；
- 当前 Researcher、Builder、Growth 的 charter 是“收到 Goal 后执行并回报”的被动角色，不具备主动立项、监督 Worker 与整合结果的 Department Manager 职责；
- 当前 role lifecycle 可以经 CEO 提案、Verifier 审核、Provisioner 落地新常驻角色，但允许创建自定义 bundle；第一版的有限模板白名单需要在此基础上收窄语义，而不是直接照搬任意角色生成；
- 当前 Verifier 已具备独立身份门、doer ≠ judge 与 fail-closed 的关键基础，应保留并复用，而不是随新架构重写掉；
- 当前 `docker-compose.yml` 实际把 `/shared/ledger`、`/shared/inbox`、`/shared/roles`、`/shared/telemetry`、`/agents` 与 `/sessions` 等内部目录挂进常驻 Agent 容器；“Agent 在公司状态中只能直接浏览 `/company`”是 V7 要新增的不变量，不是 V6 现状；
- Company State 已提供 `MAP.md -> OVERVIEW.md -> leaf` 的渐进式读取和共享长期状态，但现有 session-end record 规则需要重新判断哪些角色适用；
- 旧的 ephemeral broker 路径和当前 resident department 路径都已有真实运行证据，因此新架构可以分别用于一次性 Worker 与常驻 Department，而不需要重新证明底层模型 CLI 与容器可运行；当前 `agent.runner.run_task()` 尚未把 `resume_token` 暴露给 broker 调用方，需要在实现时补齐这一确定性续接接口。

## 主要仓库依据

- `.trellis/spec/backend/resident-agent-contracts.md`
- `.trellis/spec/backend/agent-execution-contracts.md`
- `.trellis/spec/backend/company-state-contracts.md`
- `.trellis/spec/backend/agent-handbook-contracts.md`
- `.trellis/spec/backend/role-lifecycle-contracts.md`
- `.trellis/tasks/archive/2026-07/07-08-proactive-idle/`
- `.trellis/tasks/archive/2026-07/07-10-when-idle-rewrite/`
- `.trellis/tasks/archive/2026-07/07-03-standing-objective/`
- `.trellis/tasks/archive/2026-07/07-06-create-role/`
- `.trellis/tasks/archive/2026-06/06-29-orchestration-rebuild/`
