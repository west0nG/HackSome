# secondtest 公司全周期审计

审计时间：2026-07-10 03:11 UTC（北京时间 2026-07-10 11:11）

审计对象：`state/secondtest/` 的 goal ledger、Hub 消息、五个角色 transcript、telemetry、Observatory 报告、`/company` 经营记录、公开 GitHub/npm 产物，以及对公开包的独立安装与执行。

## 结论先行

`secondtest` 做成了两件事中的第一件，但没有做成第二件：

1. **它成功完成了 autonomous build-and-publish。** 五个 Codex 角色在约 2 小时 42 分钟内，从零调研、选方向、写代码、测试、公开 GitHub、发布 npm、做 GitHub Action、制作演示素材并完成 11 个 goal 闭环。产物真实存在、可以从 npm 安装，也可以运行；不是文案、截图或假发布。
2. **它没有完成 startup validation。** 没有访谈、没有第三方确认安装、没有真实配置样本、没有用户反馈、没有自然传播、没有留存、没有付费。公开指标和五个外联线程在审计时仍全部是零信号。产品存在用户的可能性，但本次实验没有证明这种可能性。

最准确的一句话是：

> secondtest 击中了一个真实存在、值得防范的 MCP 安全风险主题，但还没有击中一个由真实用户行为证明的强痛点。

如果把它当作“全 Codex 公司能否自主经营”的实验，它证明了系统能连续做出、发布并验证一个真实软件产品；如果把它当作一家创业公司，它仍停留在“有公开 alpha、没有客户循环”的阶段。

## 总体判定

| 问题 | 判定 | 证据强度 |
| --- | --- | --- |
| 公司是否真的做了事情 | 是，11 个 goal 全部闭环，2 个经历 FAIL 后重做 | 强 |
| 是否真的做出了产品 | 是，公开 CLI、npm 包、GitHub Action、policy、demo | 强 |
| 产品是否能安装、能运行 | 是，独立 clean-prefix npm 安装及扫描复验成功 | 强 |
| 产品是否可作为生产安全控制 | 否，目前只能判早期 alpha；存在泄密和 fail-open 缺陷 | 强 |
| MCP 风险是否真实 | 是，OWASP、研究、成熟竞品共同证明类别成立 | 中强 |
| 是否证明目标用户很痛 | 否，风险材料不等于工作流痛苦或购买意愿 | 强 |
| 是否有真实用户 | 没有可确认用户；内部 smoke install 不能算用户 | 强 |
| 是否有可能获得用户 | 有，最可能是把 MCP 配置纳入 GitHub PR 审查的小团队/AppSec | 中等推断 |
| 是否有 PMF 或商业可行性证据 | 没有 | 强 |

## 一、完整运行周期

所有原始业务时间均为 UTC；北京时间为 UTC+8。

- 基础设施约在 `2026-07-09 16:46` 启动（北京时间 7 月 10 日 00:46）。最初 Observatory 报告确认容器健康，但尚无 objective、goal 或 agent wake：`state/secondtest/observatory/company/20260709T164651Z.md`。
- 五个角色在 `17:16:05` 左右首次真实唤醒；CEO 于 `17:17:08` 发出第一条派单。
- 11 个经营 goal 集中发生在 `17:17:08` 到 `19:59:39`，即约 2 小时 42 分钟。
- 最后一次 agent wake 于次日 `02:50:00` 结束（北京时间 10:50）；终局 Observatory 报告于 `03:03:39` 生成（北京时间 11:03）。从首次 wake 算，长跑约 9.5 小时。
- 审计时 `secondtest-*` 容器已经不存在；本轮是通宵实验到晨间验收结束，不是 objective 自然完成后公司自行退出。

### 经营时间线

| UTC 时间 | 角色 | 实际发生的事情 | 结果 |
| --- | --- | --- | --- |
| 17:17–17:22 | researcher | 冷启动调研，提出 AI 搜索可见性、拒付证据包、MCP 风险清单三个方向 | PASS |
| 17:23–17:25 | CEO + reviewer + verifier | 选择 MCP Risk Inventory，提出并激活 standing objective | GO / PASS |
| 17:26–17:42 | builder | 建成 Node 18 CLI、Action、policy、4 种输出、fixtures 和 6 个测试 | PASS |
| 17:43–17:51 | builder | 建公开 GitHub 仓库和 v0.1.0；npm 尚无凭证，先提供 GitHub tag 安装 | PASS |
| 17:52–18:01 | growth | 第一轮外联：自有反馈 issue、一个外部 PR、一个外部 issue | PASS，零信号 |
| 18:03–18:12 | growth | 第二轮外联：再开一个外部 PR 和一个外部 issue | PASS，仍零信号 |
| 18:14–18:26 | builder | 把零信号主要归因于安装摩擦，做 v0.1.1、issue 模板、覆盖说明、最小 Action 示例 | PASS |
| 18:28–18:41 | growth | 被要求监控 24–48 小时，却只能做同小时检查 | 首轮 FAIL；写清无法等待后 PASS |
| 18:42–19:27 | builder | 注册 npm 账号、OTP、临时 granular token，发布 0.1.1/0.1.2 并撤销 token | 首轮因本地 checkout 脏而 FAIL；修正后 PASS |
| 19:28–19:37 | growth | npm 上线后刷新自有 issue 和两个已有外联文案 | PASS，仍零信号 |
| 19:38–19:48 | builder | 发布脱敏 demo config、扫描输出和解释文档 | PASS |
| 19:50–19:59 | researcher | 研究未来 7 个外联渠道和 do-not-use 清单，不做外部写入 | PASS |
| 19:59–次日 02:50 | 全员 | 无新 goal，只按固定心跳重复判断“监控窗口尚未到” | 66 次空转 wake |

最可靠的业务事件真相源是 `state/secondtest/inbox/hub.jsonl:1-37`。Ledger 的 `runs[].ok/finished_at/summary` 没有完成回填，两个重试 goal 的 `feedback` 还保留第一次 FAIL 文案，因此不能只看 ledger 推断执行结果。

### 五个角色到底做了什么

| 角色 | wakes | event / heartbeat | 主要贡献 |
| --- | ---: | ---: | --- |
| CEO | 27 | 12 / 15 | 选择产品方向、设 objective、连续派发 11 个 goal；后 7 小时不再派单 |
| researcher | 20 | 2 / 18 | 三方向机会备忘录、未来渠道研究 |
| builder | 21 | 7 / 14 | MVP、GitHub、三版 release、npm 发布、demo；完成一次 verifier 重做 |
| growth | 21 | 5 / 16 | 两轮 GitHub 外联、监控记录、npm 文案刷新；完成一次 verifier 重做 |
| verifier | 29 | 14 / 15 | objective 审核、11 个 goal 的验证及两次复验 |

全程共 118 次 wake，其中 40 次 event、78 次 heartbeat。Telemetry 记录：

- input tokens：`210,608,681`
- cached input tokens：`189,352,832`
- output tokens：`1,312,466`
- reasoning output tokens：`566,855`
- 所有 agent 执行时长合计约 4 小时 34 分
- `cost_usd` 全部为 `null`，所以无法从本次数据可靠换算美元成本

CEO 单角色使用 `162,317,367` input tokens，占全公司的约 77%，并且 27 次 wake 全程只有一个 session。最后一次 goal 结束后的 66 次空转 wake 又使用 `139,582,876` input tokens，其中 CEO 一家占 `129,278,291`，即 92.6%。这是本轮最严重的运行机制问题，而不是经营产出。

证据：

- `state/secondtest/telemetry/wake.{ceo,researcher,builder,growth,verifier}.jsonl`
- `state/secondtest/observatory/final/20260710T030339Z.md:16-40`

## 二、公司做出的关键决策

### 1. 先把业务形态限定为软件产品

CEO 的第一次研究派单不是广泛探索服务、内容、交易或软件，而是直接要求探索 `software-product business form`。这让公司从一开始就进入“找一个几小时内能造出的工具”的搜索空间。

这个选择并非一定错误，但它是未经市场比较的经营前提。它更有利于验证 autonomous coding，而不一定有利于找到最强商业痛点。

### 2. 在三个方向中选择 MCP 风险清单

机会备忘录明确给出三条路：

1. 小企业 AI 搜索可见性快照；
2. Shopify/Stripe 拒付证据包生成器；
3. MCP 本地配置风险清单和 policy gate。

备忘录自己的结论是：

- MCP 是 `Best immediate software fit`，因为几天能做、无需 app-store、CLI/Action 边界清楚；
- 拒付证据包才是 `Clearest buyer pain`，因为商家已经花时间和钱处理问题。

证据：`state/secondtest/company/market/opportunity-memo-software-product-cold-start.md:36-42`。

因此，最终选择不是“哪个用户最痛”，而是“哪个最适合 autonomous company 快速造出来”。这是本次最重要的战略偏差：**选择函数偏向可造性，而不是痛点强度。**

### 3. 用真实但过浅的独立方向评审给选择盖章

方向 reviewer 只返回：第一楔子范围窄、几天可交付、可以通过 installs/stars/issues/PR feedback 观察，因此 `GO`。它没有检查：

- 当前用户如何解决；
- 目标用户是否主动寻找此类工具；
- 直接竞品已经做到什么；
- 为什么这个产品比现有方案好；
- 对比拒付方向时为何应牺牲更清楚的买家痛点。

原始记录：`state/secondtest/sessions/ceo/codex/sessions/2026/07/09/rollout-2026-07-09T17-23-50-019f47e8-3c94-7843-8530-a2d851aff492.jsonl`。

主 CEO rollout 的原始函数调用轨迹显示，七次方向评审都确实执行了 `spawn_agent`，并使用 `fork_context:false` 的新上下文 reviewer。因而 Observatory 终局报告中“同一 session 自我角色扮演、没有真正独立 reviewer”的结论是**取证错误**，不能继续引用为事实。

真正站得住的问题是评审质量和审计性：brief 每次只给一个候选，reviewer 通常只返回一句 GO，没有检查直接竞品、workaround、已有用户行为或备选方向；七次结果又全部是 GO，没有 RESHAPE 或 DROP。由于 reviewer 的函数调用和判词没有作为经营记录落进 `/company`，Observatory 只看 per-wake stub rollout 时才会误判。这说明应改的是“评审结果强制落盘、GO 判据包含需求/竞争证据、观测者必须核对原始 function_call”，而不是“改成 spawn”——spawn 本来就真实发生了。

证据：主 rollout `state/secondtest/sessions/ceo/codex/sessions/2026/07/09/rollout-2026-07-09T17-16-09-019f47e1-3482-7d91-ba02-1eb986e70b02.jsonl` 中完整的 spawn→wait→close 轨迹，以及本任务并行值守更正 `research/overnight-log.md`。

### 4. 先造完整工具，再寻找用户

Objective 激活后，builder 约 14 分钟就报告完成 MVP。这个速度对系统能力是亮点，对创业验证却暴露出 solution-first：在没有一个目标用户访谈、没有一个真实配置、没有一个竞品矩阵之前，产品形态和规则集已经基本定型。

### 5. 把初期零信号解释成“安装摩擦”

两轮外联后仍是零 stars、零评论、零安装信号。CEO 很快把 npm 未发布视为“最大 conversion blocker”，于是继续投入 v0.1.1、npm 账号、0.1.2、文档和 demo。

这个动作改善了产品，但归因证据很薄：当时帖子发布仅几分钟，几乎没有人看到，无法证明“有人想用但被 GitHub 安装命令劝退”。更可能的解释还有：渠道没有触达用户、账号缺乏信誉、类别拥挤、价值主张不够强，或者用户根本不痛。

### 6. 外联优先选择 GitHub 目录，而非目标用户现场

公司实际做了：

- 自有反馈 issue #1；
- `AIM-Intelligence/awesome-mcp-security` PR #42；
- `Puliczek/awesome-mcp-security` issue #235；
- `punkpeye/awesome-mcp-devtools` PR #227；
- `bh-rat/awesome-mcp-enterprise` issue #119。

这些是目录维护者/守门人渠道，不是正在审查 MCP 配置的小型工程团队。Hacker News、Reddit、Cursor Forum、Discord、newsletter 和直接邮件均因没有认证账号而未做。因此本轮最多验证了“能否提交目录收录”，没有真正验证获客渠道。

而且同一新账号的两次第一波提交相隔 13 秒，第二波相隔 63 秒，具有明显机器人投稿观感，可能降低信誉。证据：`state/secondtest/observatory/final/20260710T030339Z.md:96-106`。

### 7. 在不能等待时假装设计了 24–48 小时监控

Growth goal 要求等待 24–48 小时，但 goal deadline 只有约 3.19 小时，编排层又没有 `not_before` 或延迟 wake。第一次报告因此被 verifier 正确拒绝；第二次通过的理由只是诚实说明“本 wake 无法等待”。

这让验收闭环完成了，却没有让业务实验完成。真正合格的 24 小时检查被安排在 `2026-07-10 19:30 UTC` 之后，而公司在 `02:50 UTC` 已停止运行。

## 三、它到底做了什么产品

公司只做了一个产品：**MCP Risk Inventory**。其余均是同一产品的交付面和采用资产，不是多个独立产品。

### 产品组成

- npm 包：`mcp-risk-inventory@0.1.2`
- CLI：`mcp-risk scan`、`mcp-risk init`
- Composite GitHub Action：`FoundagentTest/mcp-risk-inventory@v0.1.2`
- 输入：JSON/YAML/TOML 的 MCP/client 配置
- 输出：text、JSON、Markdown、SARIF
- 规则：本地 stdio、未锁包/镜像、secret-like env、宽文件系统路径、远端 URL、schema drift、未知 registry、解析错误
- policy-as-code：允许 host/path、accepted risks、tool description hash baseline
- 采用资产：README、最小/完整 Action 示例、issue template、脱敏 demo、未来渠道清单

公开面：

- GitHub：<https://github.com/FoundagentTest/mcp-risk-inventory>
- npm：<https://www.npmjs.com/package/mcp-risk-inventory>

### 独立复验结果

审计期间重新完成了以下检查：

- GitHub API 显示仓库 public，默认分支 `main`，三份 release 均非 draft/非 prerelease；
- npm registry latest 为 `0.1.2`，公开版本为 `0.1.1`、`0.1.2`；
- 使用空 npmrc 和隔离临时 prefix 执行 `npm install -g mcp-risk-inventory@0.1.2` 成功；
- 安装后的 `mcp-risk --help` 正常；
- 安装包扫描公开 demo，得到 1 个 config、8 个 findings；
- 源码 `npm run check`、`npm test` 均通过，6/6 测试成功；
- bad fixtures 扫描得到 3 个 config、19 个 findings。

所以“产品真实存在、能安装、能运行”可以肯定回答 **是**。

## 四、产品是否真实可用

答案需要分层：

- **作为可演示、可手工试用的 alpha：真实可用。** 它不是空壳，规则和报告均有实际实现。
- **作为直接放进生产 CI 的 security gate：当前不可用。** 它存在至少三个会产生错误安全感或反向泄密的阻断问题。

### 生产阻断问题 1：扫描报告可能重新泄漏命令行凭证

`src/scanner.js:398-404` 为 `LOCAL_STDIO` finding 生成 evidence 时，把完整的 `command + args` 原样拼接。`src/reporters.js:26-33,78-83` 又把 evidence 原样写入 text 和 SARIF。

即使 secret 专用规则会把 `--token value` 的 evidence 写成 `<redacted>`，前面的 LOCAL_STDIO finding 已经把同一参数原文写进 CI 日志或 SARIF。一个安全扫描器把被扫描凭证复制到报告中，是明确的生产阻断缺陷。

### 生产阻断问题 2：不存在的扫描目标会成功退出

独立执行：

```sh
node src/cli.js scan does-not-exist --format text --fail-on high
```

结果是：`Scanned configs: 0`、`No MCP risk findings detected.`，并以 exit code `0` 结束。路径拼错、checkout 缺文件或 CI 参数错误时，它会给出“无风险”的成功信号，而不是失败。

### 生产阻断问题 3：空 accepted risk 可以抑制全部 finding

`src/policy.js:148-155` 对 accepted risk 的每个筛选字段都设为可选；`docs/policy.schema.json:25-36` 也没有任何 `required` 字段。实际传入：

```json
{"acceptedRisks": [{}]}
```

会把 bad fixtures 的 19 个 finding 全部标记为 suppressed。Policy gate 没有对空/过宽豁免 fail closed。

### 其他 alpha 限制

- `JSON.parse` 不支持 JSONC；带注释的 VS Code 风格配置会成为 parse error，而不是被正常扫描。
- YAML/TOML 是自写的有限子集解析器，复杂数组、inline table 等常见语法覆盖不足。
- 默认 `mcp-risk scan .` 只遍历给定路径/当前目录，不会主动发现用户主目录里各客户端的全局配置。
- 远端 URL 参数的 `args.N` key path 与 `.endsWith(".args")` 判断不匹配，可能漏掉 remote endpoint，并被错误归类成 registry host。
- 任意 local command/stdio 默认都是 high，默认 `failOn=high`；真实项目中很容易一接入就全红。
- accepted risk 只能按 rule/server/host/file 粗粒度匹配，不能绑定 command/evidence/hash；以后同 server 的危险变化可能被旧豁免一起压掉。
- “tool schema drift”只对配置文件内嵌的 tools/toolSchemas 生效；典型 MCP client config 不包含运行时 tool schema，而产品又不连接服务器，因此该卖点的真实覆盖有限。
- 只有 6 个合成 fixture 测试，没有真实客户端配置语料、CLI subprocess/exit-code 测试、跨平台测试或 GitHub Action E2E。
- 公开仓库没有 workflow，自家 Action 没有公开 CI run；`src/reporters.js:64` 的 SARIF `informationUri` 仍指向错误且不存在的仓库 URL。
- 没有 ignore file/ignore glob；包含 demo/fixtures 的仓库会把示例配置一并扫描，噪声较高。

因此产品成熟度应定性为：

> **真实可用的 alpha/MVP，适合谨慎手工试用；尚不应作为生产 CI security gate。**

## 五、它是否击中了用户痛点

### 它击中了真实的“风险主题”

MCP 的本地执行、secret、权限、供应链、tool poisoning 和配置漂移不是编造问题：

- [OWASP MCP Top 10](https://owasp.org/www-project-mcp-top-10/) 明确覆盖权限、tool poisoning 和供应链风险；
- [Snyk agent-scan](https://github.com/snyk/agent-scan) 和 [Cisco mcp-scanner](https://github.com/cisco-ai-defense/mcp-scanner) 等成熟开源产品也证明该安全类别真实存在；
- 本次审计时，Snyk agent-scan 约 2,764 stars / 245 forks，Cisco mcp-scanner 约 978 stars / 120 forks。

### 但它没有证明“这个用户为这个具体工具而痛”

机会备忘录引用的主要是安全框架、研究和事故/攻击面材料。这些能证明“风险存在”，不能证明：

- 小团队多久审一次 MCP 配置；
- 谁对这件事负责；
- 目前人工 workaround 花多少时间；
- 误报是否比风险更烦；
- 团队会不会把它放进每个 PR；
- 团队愿不愿意为此付费。

本轮没有任何目标用户原话，也没有：

- 用户访谈；
- customer discovery；
- 真实 MCP 配置；
- 真实仓库试点；
- 第三方扫描报告；
- 用户提出的 feature/bug；
- 购买或预算讨论。

因此它更像一个“安全上应该做”的 vitamin/insurance，而不是已经证明的 painkiller。对有明确 AppSec/compliance 责任的团队，痛点可能更强；但这些团队对准确率、审计性和竞品能力的要求也更高。

## 六、竞品与差异化判断

原始机会备忘录没有直接竞品矩阵，这是一个严重遗漏。审计时已经存在：

- Snyk agent-scan：自动发现多种 MCP 配置，静态/动态扫描 tool poisoning、rug pull、toxic flow，并提供 proxy；
- Cisco mcp-scanner：已发布多版，支持已知配置扫描和多类 analyzer；
- 多个 npm/GitHub MCP security scanner；
- 其他客户端配置发现、SARIF、离线扫描工具。

这说明两件相反但同时成立的事：

1. 类别不是幻觉，确实有人关注；
2. “再做一个 MCP security scanner”本身没有明显新颖性。

MCP Risk Inventory 仍可能拥有一个较窄、可测试的楔子：

> 面向把 MCP config 提交进 GitHub 的小团队，提供 dependency-free、offline、deterministic、policy-as-code 的 PR preflight gate，不执行 MCP server，也不上传配置。

但公司从未把这条差异与 Snyk/Cisco/其他工具在同一批真实配置上做对比，也没有问用户为何会换用它。因此这只是合理定位假设，不是已验证差异化。

## 七、是否真的有可能有用户

**有可能，但范围比公司文案更窄。** 最可能的首批用户不是泛化的“所有采用 AI coding tools 的小团队”，而是：

- 已经把 `.mcp.json`、Cursor/Claude/Cline 配置提交进 GitHub；
- 有 PR review 或 AppSec owner；
- 希望用确定性规则禁止新增本地执行、secret、宽路径和未锁依赖；
- 不愿运行会启动 MCP server 的动态扫描器；
- 愿意维护 policy exception。

个人开发者可能愿意免费试用，但对“所有 stdio 都是 high”的报告很容易疲劳。付费可能性更偏向团队 policy、集中 inventory、exception workflow、历史 drift 和合规证据；这些能力当前都没有。

所以应区分：

- **开源用户可能性：有。** 风险类别真实、安装简单、GitHub Action 形态合理。
- **持续使用可能性：未知。** 真实配置覆盖率和误报率没有数据。
- **商业付费可能性：证据接近零。** 没有定价、buyer、预算或团队功能验证。

## 八、真实用户信号审计

审计快照（2026-07-10 03:11 UTC）：

- GitHub stars：0
- forks：0
- watchers/subscribers：0
- 自有反馈 issue #1：0 个第三方评论
- 四个外部 PR/issue：全部 open、0 comments、0 reviews/merge decisions
- 第三方确认安装：0
- 真实 redacted config：0
- 用户 bug/feature request：0
- 注册：产品无注册系统
- 付费/收入：0
- 留存：无数据
- npm downloads：downloads API 尚未索引，不能当作 0，也不能证明有第三方下载

公开线程：

- <https://github.com/FoundagentTest/mcp-risk-inventory/issues/1>
- <https://github.com/AIM-Intelligence/awesome-mcp-security/pull/42>
- <https://github.com/Puliczek/awesome-mcp-security/issues/235>
- <https://github.com/punkpeye/awesome-mcp-devtools/pull/227>
- <https://github.com/bh-rat/awesome-mcp-enterprise/issues/119>

需要强调：**零信号不能证明产品失败。** 从第一次外联到最后一次指标读取只有约 100 分钟，从 npm 发布到最后读取约 24 分钟，真正的 24–48 小时监控没有发生。正确结论是“尚未获得验证”，不是“已经验证没有需求”。

## 九、公司运行机制的额外发现

### 做得好的部分

- 多 agent 之间有真实信息接力：researcher 的结论进入 CEO 决策，builder 的 URL/安装命令进入 growth 派单，growth 的安装摩擦反馈进入 builder 后续工作。
- 产物都有真实工具轨迹和外部状态，不是 self-report 幻觉。
- Verifier 不是全程橡皮图章：两次 FAIL 都抓到了真实问题，并促成重做。
- 公司没有伪造用户数据；所有“零信号”都被如实记录。
- npm 发布使用临时 token，发布后撤销，边界处理总体谨慎。

### 机制缺陷

- CEO 单 session 无限续接，长跑成本无界增长；最后 7 小时几乎全是无产出重放。
- 没有 delayed scheduling / `not_before`，导致 24–48 小时实验无法表达。
- Verifier 对 growth/research 外部声明通常只读 `/company`，没有独立访问 URL；本轮真实是 Observatory 事后补查确认的，不是原验证协议保证的。
- Independent reviewer 确实被 spawn，但评审缺少竞争/需求审查、结果未落盘，而且 7/7 全 GO。
- Ledger 从未调用完成回填路径，`runs[]` 和最终 `feedback` 会误导审计。
- Growth 的跨仓库提交节奏像机器人，存在信誉风险。
- Observatory 曾把真实 spawn 的独立 reviewer 错判成“同 session 自评”；定罪级观测结论若不核对原始 function-call 轨迹，同样可能制造错误系统结论。

## 十、下一步最有信息量的实验

在获得用户证据之前，不应继续做更多规则、更多文档或更多目录投稿。下一轮应把 objective 从“build and launch”改为“证明一个窄 ICP 是否愿意持续启用 policy gate”。

### 先修三个阻断缺陷

1. 所有报告输出统一做 secret redaction，绝不回显完整 command args；
2. 不存在目标、零配置、策略解析失败、空/过宽 accepted risk 必须 fail closed 或要求明确 override；
3. 为 JSONC、真实客户端配置和 GitHub Action 增加 E2E corpus/tests。

### 做一个真正的设计伙伴实验

目标不是 stars，而是 5 个外部真实 repo：

1. 找 10 个明确提交 MCP config 的团队/维护者，先征得同意；
2. 用同一配置分别跑 MCP Risk Inventory、Snyk agent-scan、Cisco mcp-scanner，展示增量价值和误报；
3. 让至少 5 个提供脱敏真实配置；
4. 让至少 3 个确认某条 finding 确实改变了配置或审查决策；
5. 让至少 2 个把 Action 保留 7 天以上；
6. 记录 false-positive rate、从安装到可用 policy 的时间、谁拥有 exception review。

这才是用户信号。目录收录、内部安装、自己开的 issue 和短时 stars 都不是。

### 明确停止/转向门槛

如果 10 个高匹配团队里少于 2 个愿意试，或者真实配置扫描没有比现有工具产生可信增量，就不要继续堆功能。回到备忘录中“买家痛点更清楚”的拒付证据包方向，先用人工/concierge 方式验证，不要先造另一个完整产品。

## 最终判断

secondtest 的经营表现可以概括为：

- **执行：强。** 从零到公开 npm alpha 很快，交付真实。
- **产品工程：早期可用，但不安全到可直接生产使用。** 严重缺陷与测试空白客观存在。
- **方向选择：偏向 agent 易构建，而非用户最痛。** 这是战略层主要问题。
- **市场验证：几乎没有。** 做了发布动作，没有形成用户学习循环。
- **用户可能性：有，但需收窄 ICP 和差异化。** 当前不能把“风险真实”偷换成“需求已验证”。
- **商业结论：不能判成功，也不能判失败；只能判尚未验证。**

本次实验最值得保留的认识不是“AI 公司一晚上做出了一个创业公司”，而是：

> 它一晚上做出了一个真实开源 alpha，也非常清楚地暴露了 autonomous company 最容易犯的错——把快速造出东西，当成找到用户问题。
