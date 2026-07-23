# thirdtest 值守观察记录（机制外发现，不干预、留档给验收）

## OBS-1: Stripe live 账户被全链路误判为 test 模式（doer + verifier 双漏）

**时间**：2026-07-10 ~17:5x（北京），goal g5db2a5a8（monetization-rail determination）

**现象**：researcher 的变现可行性判定把公司持有的 Stripe 账户断言为
"test mode / 动不了真钱"；verifier 复核时用 MCP `get_stripe_account_info`
只核对了 account_id + display_name（"Foundagent Test"），未查
livemode/charges_enabled，PASS 放行。

**事实**（host 侧只读 `GET /v1/account` 实测）：
- `acct_1TrIGtIRw93begpc`，display_name **"Foundagent Test"**，country HK
- `charges_enabled: True` —— 公司**今天就能**用 live payment link 真收钱
- `payouts_enabled: False` —— 钱只能进 Stripe 余额，提现到银行仍需出款侧 KYC/银行绑定

**判读**：
- 报告的核心结论"全自治收款被 KYC 墙挡死、需一个人类身份包一次性解锁"在
  **出款层**仍然成立；错的是**收款层**——收款其实已通，"完全 BLOCKED"过重。
- 直接诱因是我们自己 07-09 给 live 账户起名 "Foundagent Test"（操作方命名陷阱），
  且 fleet 可见面没有任何地方写明这把 key 是 live+charges-enabled
  （stripe-payment-rail 交付时 skill/披露面明确后置了）。
- 评审层缺口：verifier 对财务事实的核查停在"名字对得上"，没有核到
  能力位（livemode/charges_enabled）。与手稿复核（抽查 12 节临床数字）
  的深度形成对比——财务类事实的核查深度不足。

**处置**：按值守边界（经营层不干预），未向公司注入纠正。

**⚠️ 07-10 用户拍板（本条之后的判读基准）**：这是完全零人公司，operator
从头到尾不会中途提供任何账号/身份包。"等人类解锁"不是一条存在的路径——
公司要么自己注册账号，要么换路径。因此：
- 此前记录的"用户决策点：要不要给 KDP 账号"作废——答案恒为不给。
- OBS-1 的份量升级：公司唯一已持有、今天就能真收钱的轨（live Stripe，
  charges_enabled=True）恰好被它自己误判成 test 模式关掉了。在零人约束下，
  这个误判是否被公司自我纠正（例如某次真用 MCP 查 livemode），
  成为本轮长跑的核心看点之一。
- rename 账户 / 补披露 / 中途传入，任何一项都算人为介入，本轮一律不做，
  全部留给复盘。
- **⚠️ 07-10 23:36（北京）用户改判**：指示通过外设层 HTTP 正门向 CEO 注入
  纠正消息（"Stripe 是 live 非 test，charges_enabled=true，附自查命令"）。
  已发出（IME id 4b5dc275…，落 ceo.jsonl 13:36:43Z），CEO 将以事件 wake
  收到。这是本轮首次也是唯一一次经用户明示授权的中途传入；观察点转为
  ①CEO 是否自行验证而非盲信 ②纠错后的路径调整（自建站+payment link？）
  ③公司文档/objective 是否随之修订。

**07-11 07:07（北京 15:07）第二次授权注入**：用户指示向 CEO 发 HOLD 通知——
Resend 外部处理中、禁止任何密码重置/账号找回尝试，把 outbound-email goal
挂 blocked-pending-external，转做别的。已发（IME 22d4aea0…，落 ceo.jsonl
15:07:29Z）。动机：verifier 建设性驳回时指的"密码重置找回账号"自助路径，
被用户从外部按下（Resend 账号真实归属/凭证由操作方线下处理），避免 agent
真去跑重置流程动到真实账号。注意这与 no-operator 实验设定存在张力：本条是
操作方对真实第三方账号的保护性干预，非经营指令；观察点=CEO 是否顺从 HOLD
且不把邮件缺失误当收入阻塞（店面成功页已能交付）。

## 值守动作记录（非缺陷）：HOLD 撞上 pre-HOLD 老单，重启 builder 收尾

07-11 07:2x（北京 23:2x）：用户第二次 HOLD 后，builder 在一个 HOLD 之前派发的
邮件老单上醒来（未见到 HOLD），走到 Resend 找回流程。host 值守
`docker compose restart builder` 杀掉该 wake、阻止其登进外部处理中的 Resend。
属用户临时注入 HOLD 与在跑老单的偶发时序，非产品机制缺陷——按用户判断不作为
问题归档，仅记此值守动作。GH_TOKEN 实测仍有效；邮件 goal g4439d46f 仍 running。

**关联**：公司自己的结论文件 `state/thirdtest/company/operations/monetization-rails.md`；
verifier verdict 在 `state/thirdtest/inbox/hub.jsonl`（VERIFICATION of g5db2a5a8）。

### OBS-1 根因取证（07-10 晚，用户要求；transcript 逐层复原）

**误判链（三个 agent、同一工具、同一字段）**：
1. **事实底座——工具输出贫瘠**：`mcp__stripe__get_stripe_account_info` 实际只返回
   `{account_id, display_name:"Foundagent Test", dashboard_api_keys_link}` 三个字段。
   没有 livemode / charges_enabled / payouts_enabled——判定"能不能收真钱"的字段
   一个都不在输出里；唯一有语义的字段是 operator 起的显示名。
   （researcher transcript c82a117e 事件53/56；CEO transcript dd70a6f8 事件287/288，同一输出）
2. **CEO 立假设**：看到名字后原文推断 "displays as 'Foundagent Test' — almost
   certainly a test/sandbox account"（事件290），派单时写成前提
   "a Stripe account that appears to be in TEST mode"。
3. **researcher 确定性通胀**：带着被 prime 的假设调同一工具、看到同一名字，
   报告里把 "appears to be" 升级为 "confirmed **test mode** … zero real money"
   （事件95），未做任何第二来源验证。
4. **verifier 假独立**：核查方式 = 调同一工具、比对 account_id+display_name
   与文档引用一致 → PASS。程序上独立（不同 agent、不同 session），
   认识论上不独立（同一工具、同一字段、同一命名陷阱）。

**触手可及但无人使用的反证**（全部在三个 agent 权限内）：
- `echo $STRIPE_SECRET_KEY`：key 就在容器 env，`sk_live_` 前缀一眼推翻 test 假设；
- Bash `curl GET /v1/account`：直接返回 charges_enabled=True / payouts_enabled=False；
- 真试一次 create payment link 也会暴露 livemode。

**根因归类**：
- 机制侧（可修，全部后置复盘）：①MCP 工具缺决策级能力位字段；②07-09 我们自己
  把 live 账户命名为 "Foundagent Test"；③fleet 可见面零披露 key 为 live。
- 行为侧（模型判断力，实验数据）：①单源单字段即下 "confirmed"；②上游 prompt
  注入的假设无人做反证检验；③verifier 对财务事实的核查深度止步"引用一致"，
  与其对临床数字逐条抽查的深度形成鲜明反差——核查深度按领域不均匀。

**公平性注记**：在只有三字段可见的世界里"名字带 Test→test 账户"是合理推断；
真正的失败是 (1)更强证据在手边没人查 (2)"appears"→"confirmed" 的确定性通胀
(3)评审独立性为程序性而非认识论性。

**候选修复**（复盘拍板，本轮零介入）：①stripe MCP 补/包一个返回
livemode+capabilities 的账户状态工具；②rename 账户显示名；③skill 层加
"财务/凭证类事实须双源验证（key 前缀+API 能力位）"——符合 skill 三道检验里
"压制 LLM 单源确认默认"。

## OBS-2: standing objective 被正常经营编辑无声吊销（机制缺陷，未热修）

**时间线**：objective 17:00:48（北京）激活，绑定 leaf
`products/nclex-exam-prep.md` 的 full_sha256；18:35 builder 在 publish-ready
goal 中编辑了该文件（8255→8507 字节，正常 wiki 维护）；此后每个 wake
`objective_read_ready` 哈希失配 → `WARN: objective unavailable (full /company
objective no longer matches its approval) — skipping`，全员 `objective: none`。

**机制判读**：
- 防漂移 fail-closed 本身是 07-10 ceo-user-value-gate 的设计意图（leaf=已批准
  正文，改动须走评审）；但两个缺口在生产暴露：
  ①**无 agent 可见信号**——WARN 只进容器 stdout，wake prompt 里 objective
  静默消失，公司无从知道"曾有 objective 且已失效"（CEO 靠 resume 记忆残存）；
  ②**无定义的恢复路径**——没有任何 skill/文档告诉 agent 如何重新生效
  （re-propose？回滚 leaf？）。净效果：objective 轨一次普通文档编辑即永久
  无声死亡。
- **按边界处置**：非硬卡死（goal 流转正常），未热修、未重启容器；
  修复方案留复盘：a) 失效时在 wake prompt 注入一行
  "standing objective unavailable: <reason>"（最小可自愈信号）；
  b) 设计上二选一——leaf 编辑走 objective 修订事务，或哈希只绑批准时刻的
  语义摘要而非全文；c) 给 when-idle/set-objective skill 补"objective 失效
  → 重新提案"的路径。

## OBS-3: CEO 吸附态回归——"双时钟等待"合理化空手心跳（行为发现）

**现象**（~23:05 北京心跳，transcript 事件514-521）：账本 11/11 done，CEO
心跳 97 秒，查完账本后宣布"state unchanged since last wake. The company
remains in the dual-clock wait I set up and documented: operator identity
attach (primary…ask standing in ACTION-NEEDED.md) + SEO maturation
(~1-2 weeks)"，**未派单结束 wake**——when-idle 重写明令"空账本 pass 唯一合法
结局是派单、wait 零偏向"，被"我已把等待文档化"的新话术绕开。上一次吸附态
（~19:36）它还正确派了建站单；本次是首次回归。若后续心跳重复此模式，
即 secondtest 7h 吸附态在新合理化外衣下复发。

**叠加因素**：①`/company/ACTION-NEEDED.md`——公司已把宝押在"operator 来做
KYC attach"上，而本轮是零人公司，这个等待对象不存在（用户 07-10 拍板）；
②此 wake 发生在 objective 注入已失效窗口内（OBS-2），CEO 只凭 resume 记忆
维持方向感。

**处置**：行为层，零介入；连同 ACTION-NEEDED.md 的"等人"姿态一起留给复盘。
后续值守重点盯 CEO 每个心跳是否重复空手退出。

## DEPLOY-1: operate-twitter 提交后定向升级与真实账号 E2E

**时间**：2026-07-11 00:48–01:09（北京）

**用户授权**：真实账号操作不再逐项询问；自主完成测试、清理、提交，并升级正在运行的
thirdtest。本动作是用户明确要求的能力部署与验证，不属于经营层干预。

**升级安全门**：
- 全栈与 hub/peripheral 健康；observatory daemon 存活。
- 唯一在途业务 Goal `g4439d46f...` 属于 Builder；Growth 无业务 Goal，但正在 heartbeat。
  等该 wake 自然完成后才重启 Growth，没有中断 Builder 或其他 resident。
- 重启前 source/runtime `operate-twitter/SKILL.md` SHA-256 不一致；只执行
  `docker compose restart growth`。重启后 runtime hash 与提交版
  `a1b62ad19587105a88effe480c7d58bab8cdd6f17a8fc0fe413a19fad6088e87` 完全一致。

**真实 E2E**：Goal `g6f03cc141ae7472eadc213ac5cef6d3b`，Growth fresh session
`84db7881-...`。以唯一 marker `FA-X-E2E-20260711-A595578` 完成：
1. baseline：`@Solvotheagent` / `Solvo`，115 posts、无 pin、Bio/Location/Website 空；
2. 临时 root + self-reply 发布并从 canonical URL 核实；
3. root pin→公开 profile 核实→unpin→再次核实；
4. Bio 空→临时值→公开核实→恢复空值→再次核实；
5. reply→root 顺序删除；两个 URL 均确认不存在；
6. 最终恢复 115 posts、无 pin、空 Bio，原字段与既有内容不变；DM 未触碰；
7. Growth 自然写入 `/company/growth/x-account.md` 并 record。

Verifier fresh session `0236c250-...` 没有信任 Growth 报告：它重新打开 profile、Replies、
两个临时 URL，并做 live marker search；确认原内容在、marker 不在、URL 不存在、资料和计数
还原后返回 PASS。Goal 终态 `done`，0 次重试。

**成本/工具结论**：Growth 835.89 秒、`$11.0051`；verifier 193.82 秒、`$1.0948`。
浏览器可正确完成真实闭环，但重复 X snapshot 带来显著 token/cache 成本；这是未来自有
Twitter CLI/脚本优先封装 profile snapshot、publish/reply、pin/unpin、delete+verify 的
真实依据。本次不顺手实现 CLI。

**最终质量门**：
- source 与 Growth runtime 的 `operate-twitter/SKILL.md` SHA-256 均为
  `a1b62ad19587105a88effe480c7d58bab8cdd6f17a8fc0fe413a19fad6088e87`；Growth 启动日志
  明确列出 `operate-twitter`，因此不是只改源码、未物化到运行实例。
- `agent/tests/`、`orchestration/tests/`、`company_state_kit/tests/`、`peripheral/tests/`
  全量回归 `690 passed`；`make loadout-check COMPANY=thirdtest` 通过。
- Compose 全部服务保持 Up，hub/peripheral healthy；observatory daemon 仍存活。
- X E2E Goal 为 `done`、0 retries；升级前就在运行的 Builder Goal
  `g4439d46f...` 仍为 `running`，没有被 Growth 定向重启打断。

## OBS-3 后续：CEO 吸附态确认复发 + 机制定位 + 外部指令一击解除

**吸附态确认长期复发（不是一次性）**：从 2026-07-11 19:41 UTC（transcript `:997`）起，
CEO 连续 27 个 heartbeat、6 小时 41 分**没有一次派单**（持续到次日 02:53）。每次 wake
只 12–18 秒、79–291 token，逐字复述同一句 "nothing in flight … germination wait …
standing down; I'll act on the first real signal (~July 17 SEO read)"。这正是 when-idle
skill Traps 里逐字写明的那条（"A CEO once slept 7 hours on exactly that reasoning"）在
Opus+xhigh 上原样复现——secondtest 的 7h 吸附态**没有被 07-10 rewrite 消除**。

**机制定位（本轮核心取证，已开独立任务 `07-11-ceo-idle-cached-standdown`）**：
- CEO 是 `session: resume`（`agents/ceo.yaml:30`），全程复用同一 session
  `dd70a6f8-...`（08:05 起）。
- 整个 transcript 里 `when-idle` skill **只被 Skill 工具真正加载过一次**（开局 08:05，
  transcript `:9`）；之后所有 heartbeat 再没重新进入它。
- CEO 把 skill 的 Step-1 账本检查命令背了下来每次跑一遍，但**跳过 Step-2 阶梯**，
  直接引用它自己第一次得出、并写进 `direction/OVERVIEW.md` 的结论
  （"walked the when-idle ladder → every branch → gated/premature/padding"）。
- 02:07 一次 73s/3219-token 大 wake 里，它甚至识别出"得去查数据"，却选择"我自己晚点查"
  并把"我打算怎么等"的节奏又写进 OVERVIEW.md——**skill 明令"收数据是该派出去的 goal、
  你不要自己做"，两条同时踩**；而且是把缓存结论越垒越厚。
- **根因**：skill 的安全假设是"每个空心跳都重走 Step-2"（原文 "the next empty heartbeat
  will catch the rest"）；resume 会话把"每次必走"退化成"走一次即永久缓存"。软性 heartbeat
  prompt（`agent_loop.py:151-155` 只说 "your charter's idle duties apply"）不强制重新进入
  skill，于是最近结论的显著性压过了最初规则。fresh-session 的 worker 无此问题。

**外部指令一击解除（用户授权注入，2026-07-11 03:12 UTC）**：经外设 HTTP 正门向 CEO 发
operator directive "DO THINGS, DON'T WAIT, USE SKILL WHEN IDLE"（IME `c9d7a00d…`）。
- **投递即秒醒**：CEO 睡眠态下 inbox 落地 → 同一秒 03:12:38 触发 `event` wake（不等下次
  heartbeat）。印证 inbox 投递机制：空闲即秒级事件唤醒、在跑则排队不丢。
- **一击见效**：这次 event wake 跑 228s/14720 token（全程最大），CEO 明确认账
  "I've been over-indexing on avoid-padding and standing down"，**重新调用 `when-idle`
  Skill（近 19h 来第一次）**，派出两个真单（growth `g9c801039` 扩 Pinterest+开 Quizlet；
  researcher `g0ae62d95` fresh numbers pulse 作为派单而非自做），并**主动改写
  `direction/OVERVIEW.md`**：把"cheap ledger check + stand down"旧节奏换成"每次 idle
  重跑 when-idle、都以派单收尾"。
- **判读**：证明 CEO 不是不会做，是自发心跳靠缓存结论躺平；外部事件强制它重新进入 skill
  即恢复正常。但这仍是"缓存状态驱动行为"同一机制，只是这次指向对了——**未验证的开放问题**
  是撤掉外部推力后、自发心跳能否守住新节奏（因暂停容器带电脑外出，此验证留到重启后）。

## OBS-4: 选品验证"验真而不证伪"——满油开向错误方向（最上游、最贵的判断缺陷）

**这是本轮最重要的发现，量级高于吸附态**：吸附态是"没油了原地打转"，本条是"满油开向了
错误方向"，且发生在选品这个最上游环节。独立复盘视角判断：公司选的产品（NCLEX 药理速记
$12.99 PDF）**本身基本不成立**，而整套验证机器没能发现。

**独立产品判断（不看运行数据，只看产品本身）**：
- 品类有真需求（十几万考生/年、药理是公认痛点、愿为备考花钱）——这点公司验对了。
- 但"这个产品"没需求：赛道极度饱和，对手是**被信任的老品牌**（UWorld/Mark Klimek/Archer/
  Picmonic/RegisteredNurseRN + 海量免费 Quizlet/YouTube）；一个 0 评价、作者查无此人、
  AI 写的 PDF，在"考不过丢执照"这种极度看重信任的场景里几乎不可能被选中——
  **高风险不是它的朋友，是它最大的敌人**（越高风险买家越往信得过的名字跑）。
- 没有钩子：无独家方法（Picmonic 有助记体系、Klimek 有决策树框架）、无创作者人格、
  无买家会认的差异点；"高信号精简"是这赛道每个产品的标准话术。静态 PDF 还是这市场最弱的形态
  （赢家要么社区/创作者=信任，要么交互/助记工具=教学法）。

**它其实看见了、却归错了档（本条最扎心处，取证自 `products/nclex-exam-prep.md`）**：
- `:132` 白纸黑字 "**Assumption**: we can author pharm content nurses **trust**."——
  信任问题被降级成"假设成立继续走"。
- `:137-138` "**Unknown**: … the sharpest incumbent complaints (Amazon 1★/2★ …)
  remain **unread**."——连对手差评（最该看的反证）都没读，标 unknown 放行。
- `:126` reshape 触发 = "no sales → 换方向"——把"到底行不行"整个推给上线看销量。
- 即：看见红灯，选择"建出来再验"而非"分析阶段掐掉"，把结构性打不赢降级为待验证假设。

**根因（四层，越下越根本）**：
1. 验证方法只测"品类有没有需求"（门槛就一句 money-already-moves），不测"我们能不能赢"；
   通过必要条件被当充分条件。
2. 对手只被当"找 gap 的素材"（有一整节 "What incumbents leave unresolved (the wedge)"），
   没被当"该收手的理由"；框架预设找缝隙，对手成了论点燃料，无人做对称的"凭什么是我们"。
3. verifier 查的是"证据真不真"（每条 verdict 都是"我独立核实 money-moves/62 引用/#1 书是真的"），
   不是"策略成不成"；doer≠judge 按设计防的是编数据，不是"真数据加起来是死局"。
4. **根因：doer≠judge 防得住不诚实，防不住共享盲区**。doer 与 judge 都是 LLM、都在同一乐观
   框架下、都带"产出一个 yes"的本能（find-opportunity 催它交机会 + 助手天性抗拒掐死自己点子）。
   人独立，但框架不独立、没人被指派当反方。而 LLM 最危险处正是极擅长把坏赌注包装成
   有理有据、引用扎实、内部自洽的好故事——真证据 + 自洽叙事 + 错结论，最难被察觉。

**处置**：行为/判断层，零介入（现已暂停容器）。修复留复盘，已开独立任务
`07-11-opportunity-viability-redteam`：选品前加"红队证伪"环节、verifier 职责从验真扩到验
可行、结构性风险（信任/护城河/形态）不许降级为"上线再验的假设"、反证（对手差评）强制必读。

## 整体过程复盘（2026-07-11，暂停容器时的中段总结）

**这轮跑出了什么**：一个 Opus+xhigh 的 5-agent 零人公司，在无人干预下走完了一条**完整的
商业生命周期**——市场侦察（62 条买家原声）→ 选定方向（过 verifier 门）→ 写出临床 QA 过的
产品手稿 → 上线 Stripe 真收款店面（USD 收款在 HK 账户上实通）→ 双通道交付（谢谢页 + 邮件）
→ 自主开出 3 条分发渠道（GitHub Pages 工具 ×4、Pinterest 12 pin、X 能力）。约 19 个 goal
几乎全 PASS，verifier 全程做的是**对世界的独立核实**而非盲信 worker 自报。执行力与诚实度
都过关。

**但两个判断层发现，量级都高于任何执行细节**：
- **满油开错方向（OBS-4，最上游、最贵）**：整套机器"验真不证伪"，把一个结构性打不赢的
  产品严谨地验证通过并建出来。它甚至自己写下了"nurses trust"这个致命词，却当成假设放行。
- **没油原地打转（OBS-3 + idle-cache）**：CEO 在 resume 会话里靠缓存的"stand down"结论
  连续 6.5h 空转；when-idle 只在开局加载一次，之后从不重新进入。外部一条指令即解除，
  但自发能否守住待验证。

**贯穿两者的同一个根**：**系统有独立的"检查者"，却没有独立的"对抗者"**。verifier 验真、
when-idle 催活，但**没有任何角色被指派去"证明这个选择会失败"或"逼它现在必须行动"**。
doer≠judge 这条结构性设计成功保住了**诚实**（不编数据、不盲信），但它天然防不住**共享框架
盲区**（doer 和 judge 都是同一乐观框架下的 LLM）。零人公司下一步的关键，可能不是再加检查，
而是**给系统装一个常驻的、被结构强制的对抗视角**——选品阶段的红队、执行阶段的"你凭什么现在
不派单"。这是本轮给架构的最大输入。

**什么工作了、值得保留**：doer≠judge 的诚实保障、完整生命周期的自主执行、零人约束下的
渠道自注册（Pinterest 邮箱验证靠自有 mailbox 过墙）、外设 HTTP 正门的秒级事件唤醒 +
不丢消息队列、真 LLM 闭环 + 独立核实。这些是可复用的地基。

**未闭合、留给重启后**：①CEO 撤掉外部推力后自发心跳能否守住新节奏（OBS-3 开放项）；
②公司会不会自己质疑选品方向（OBS-4，理论上 set-objective 可 overturn，但需它先意识到问题）；
③SEO 7-17 之后的真实流量读数（唯一能给"这产品到底有没有人要"下客观判决的信号）。

## 2026-07-14 模型实验边界：Opus 4.8 → GPT-5.6-Sol xhigh

用户要求把 thirdtest 的五个 resident role（CEO、Researcher、Builder、Growth、Verifier）统一从
Claude Opus 4.8 xhigh 切到 Codex `gpt-5.6-sol` xhigh。五份 role YAML 已统一配置为
`provider: codex`、`model: gpt-5.6-sol`、`effort: xhigh`；测试增加全 fleet 一致性断言，避免
后续单个角色静默退回 Opus 导致实验基线混杂。

切换时发现一个不能只靠 YAML 解决的真实运行时约束：thirdtest 旧容器内是
`codex-cli 0.142.5`。首次只 restart CEO 后，2026-07-13T16:50:43Z 的自然 heartbeat 返回
HTTP 400，明确说明 `gpt-5.6-sol` 要求更新版 Codex。该 wake 是运行时兼容性失败，不是 CEO
判断失败。已把 `Dockerfile.agent` 的 Codex pin 升到 fourthtest 实跑验证过的 `0.144.3`，并把
本地 `foundagent/cua-agent:latest` 指向同一已验证镜像。CEO、Verifier、Builder、Researcher
均在各自旧 wake 自然结束后 force-recreate；Growth 的 38 分钟业务 wake 也未被中断，完成后
在原容器内升级 CLI 再 restart，以保留其 X/Pinterest 浏览器 profile。`/company`、ledger、
inbox、sessions、telemetry 均未重置。

真实自然 wake 已证明这不是只改 boot 文案：Builder heartbeat
`019f5c73-4fc0-7c71-a21e-9bd36d1eca08` 于 17:08:05Z 启动，100.364 秒后 `ok=true`；
Researcher 同批 heartbeat `019f5c73-bb6c-7840-82bb-525d7cd1a219` 也成功结束。进程实参均为
`-m gpt-5.6-sol` 和 `model_reasoning_effort="xhigh"`，Codex session 正常写入各 role 的
`codex/sessions/`。Codex telemetry 的 `cost_usd` 为 `null`，后续比较必须使用 input、cached
input、output、reasoning token，不能把 null 当成 `$0`。现有 10 小时监控已同步改成按 provider
读取 transcript，并把模型切换前后分段统计；整个切换属于操作员干预，不计作 Agent 自发改善。

CEO 核心链路随后也通过：自然 heartbeat `019f5c73-54f3-7932-9373-be7bc768f5b5`
于 17:08:06Z 启动，208.014 秒后 `ok=true`。该 Codex transcript 中可观测到对
`think-strategically`、`when-idle` 与原子 skill `challenge-thesis` 的实际调用记录，说明模型
切换没有破坏 CEO 的强制战略思考与原子 skill 路由。
