# Agent email identity: mailboxes under foundagent.net (issue #208)

## Goal

给 agent 提供自己域名下的邮箱身份，解掉 firsttest 里 3/4 外部阻塞的第一道墙（邮箱注册/magic-link）。
Agent 能认领邮箱地址、收到发往该地址的邮件，且邮件确定性地送达 agent 的收件箱（现有 IME/inbox 机制）。
邮件系统必须是解耦的独立模块：接上 agent 就能用，拔掉不影响其他层（用户 2026-07-08 核心要求，针对 v5 多阶段耦合的反面教训）。

## 背景（已确认事实）

- firsttest 复盘（issue #208）：Medium magic-link、Pinterest/Quora/Reddit 注册、收款流程，第一道门全是邮箱。
- v6 现状：`peripheral/adapters/email.py` 只有纯转换 `to_ime()`（占位，当时拆成两个占位任务留待凭证），无任何真实收发链路；无 SMTP/IMAP/provider 凭证。
- v6 已有的下游机制（不需要新建）：`peripheral/runner.py:ingest(source, native)` → adapter `to_ime()` → 按 `ime['to']` append 到对应 agent 的 `FileInbox`；runner 常驻 HTTP listener `POST /ingest/<source>`。
- 域名 foundagent.net 已在 Cloudflare（domain rail）；Email Routing 能力可开未开。
- v5 全套参考已调研（`research/v5-email-stack.md`）：identity claim 模型可搬；Gmail 中转层（catch-all→Gmail→IMAP）是复杂度根源，用户判断 v5 机制过于复杂、很大程度是被「只能用 Resend/转发」倒逼的形态。

## Requirements

- R1 邮箱认领：agent 可随时认领 `<name>@foundagent.net` 地址（名字由 agent 自己定）；注册表记录地址 → 接收者（一个或多个 agent）映射；名字全局唯一、终身不改、不可释放；每 agent 拥有上限 3 个。
- R2 收件链路：发往已认领地址的真实外部邮件，被确定性中转（非 LLM）送达对应 agent 的 inbox（IME 形态，复用 `peripheral/adapters/email.py` seam）；任务中途可用 receive 通道的 peek 模式找信（只看不取）。
- R3 共享邮箱：一个地址可路由给多个 agent（fan-out）；owner 管理接收者列表。
- R4 skill 引导（拆两个）：`claim-mailbox`（认领流程 + 命名三原则：自定名、一次终身、有代表性/persona 名，含反例——禁止按临时服务命名如 `medium-signup@`）；`check-email`（peek 循环等信用法 + 不可信提醒）。两者均过 no-generic 三道检验。
- R5 模块边界：邮件后端（Cloudflare Worker/R2/poller）收在独立模块后面，可整体替换；测试走 mock 后端；拔掉模块不影响其余栈。
- R6 bootstrap 引导：公司起步时引导每个 agent 完成首次认领（CEO 侧 nudge），但认领窗口终身开放。

## Acceptance Criteria

- [x] AC1 真信 e2e（三条件缺一不可，用户 07-08 提出）：agent 在**真实外部服务**（首选 Medium magic-link）的注册流程中，**任务进行中途**用 peek 循环收到验证邮件并完成流程；且该邮件**不是队列里的第一条**（到达前有干扰邮件/其他排队消息，agent 须认出正确那封，其余消息事后仍被正常派发）；R2 中邮件移出待处理前缀。
- [x] AC2 共享 fan-out：一个地址挂两个接收者 → 两个 agent 的 inbox 各收到一条 IME。
- [x] AC3 认领规则：非法名/保留名/超 3 个上限被拒；重复 claim 幂等；不存在改名/释放命令。
- [x] AC4 未认领地址来信：不投递任何 inbox，归档到 unmatched 区待查。
- [x] AC5 即插即拔：单元/集成测试全程不触网（mock 后端）；停掉邮件模块服务后，其余 compose 栈与全部既有测试不受影响。
- [x] AC6 skill 落地：`claim-mailbox` 含命名三原则 + 反例 + 「邮箱解不了手机/CAPTCHA」边界声明；`check-email` 含 peek 循环命令示例 + 反默认条目 + 外部邮件不可信提醒。

## Out of scope（issue #208 已明确）

- 手机验证、CAPTCHA——邮件系统解不了，设计里写明边界，防止重复撞墙。
- 发件（D1）：v1 只做收件；发件后置为独立任务，届时可搬 v5 的 Resend+配额设计。

## 已拍板决策（均 2026-07-08）

- D1：v1 只收不发；发件后置独立任务，届时搬 v5 Resend+配额设计。
- D2：地址扁平 `name@foundagent.net`、全局唯一。理由：persona 观感只有扁平成立；company 不是正确的命名空间锚点——一个 company 可以做多个产品（等于多个"公司"），子域按公司切反而错位。测试公司走可插拔后端 mock，不碰真实注册表。（勘误：最初还引用过「CF 免费版子域路由收费」，调研证伪——子域路由 2023-10 起全套餐免费，见 research/inbound-channel-options.md §5；该理由作废，D2 靠前两条理由成立。）
- D3：认领终身开放（bootstrap 只是第一次认领的引导时机，不是唯一窗口——create-role 新建的角色也要有入口）；不可改名、不可释放；每 agent 拥有上限 3 个；共享邮箱 = owner 认领后往接收者列表加人，只占 owner 配额。烂名字靠命名三原则文案 + 终身制稀缺感来压，不靠关窗口。
- D4（调研定案）：物理通道 = Cloudflare Email Routing catch-all → 哑巴 Email Worker（raw MIME 流式写 R2）→ 宿主机 poller（轮询 R2 → stdlib 解析 → 查注册表 → 逐接收者投递 IME → 归档）。全链路 $0、无需公网端点、R2 强一致且天然是 poller 宕机时的持久缓冲。AgentMail 排除（custom domain $20/mo、MX 全托管给种子期公司），留作将来"发送+双向对话"阶段的候选。详见 research/inbound-channel-options.md。
- D5：**不做 wake 注入**（邮箱不是每次任务都相关，不进常驻提示词）。agent 的"记忆" = 注册表 + skill 自查流程（先 `mailbox mine` 再 list 再 claim）+ 超限拒绝时列出已有地址。
- D6：**单通道，否决 mail store**：邮件就是 inbox 里的一条 IME（全文在 body），不另开存储。任务中途找信 = receive 通道加 **peek 模式**（只看不取、游标不动，返回全部未读快照），agent 从中自行认出目标邮件；排队中的其他消息不受影响。已接受代价：用过的邮件 IME 下次 wake 会再派发一次（廉价噪音）。
- D7：skill 拆两个——认领（`claim-mailbox`）与使用（`check-email`）是不同触发场景的能力，分开触发更准。
