# X 平台自动化与 Agent 工具事实（2026-07-10）

> 目的：只记录会影响 `operate-twitter` 设计的当前官方事实。X 的政策、API 与价格会变化；实现前应复核链接，不把价格或端点清单永久硬编码进 Skill。

> **项目裁决（2026-07-10）**：用户明确拒绝付费 X API，选择自有网页脚本化操作，并知情承担这里记录的账号限制/封禁风险。因此本文是风险与备选路径记录，不是要求本任务改走 API 的阻塞性规范。

## 1. 网页自动化不是可持续默认路径

X 在 2026 年 4 月更新的 Automation Rules 中明确禁止 non-API-based automation，并直接举例 scripting the X website；规则说明这类技术可能导致账号永久封禁。

- 官方规则：[X's automation development rules](https://help.x.com/en/rules-and-policies/x-automation)
- 服务条款同时要求自动访问使用 X 当前公开提供的接口，未经书面许可不得抓取或以其他自动方式访问：[X Terms of Service](https://x.com/en/tos)

结论：仓库现有 Playwright storage-state 能证明登录与页面操作技术可行，但不能因此把浏览器脚本当作正式无人值守运营的低风险路径。

## 2. 各类自动动作的当前官方边界

Automation Rules 与 Authenticity Policy 当前包含以下与本任务直接相关的约束：

- 自动原创发布可以存在，但不得重复、误导、垃圾化或操纵趋势。
- 不允许使用关键词搜索后向大量陌生用户发送未经请求的自动回复。
- 自动 mention/reply 要求接收者事先请求或明确表达希望收到联系，且一次互动只发送一次自动回复。
- AI 驱动的自动回复 bot 需要 X 事先书面明确批准。
- 自动点赞不允许。
- 自动关注/取关不得批量、激进或无差别执行。
- 反复发布再删除同一内容、重复或近似重复内容、无关链接回复等属于不真实或垃圾行为。

来源：

- [X Automation Rules](https://help.x.com/en/rules-and-policies/x-automation)
- [Authenticity Policy](https://help.x.com/en/rules-and-policies/authenticity)
- [X Rules](https://help.x.com/en/rules-and-policies/x-rules)

这些是平台要求，不应扩写成大量假想防御规则；Skill 只保留会直接改变动作合法性的当前边界。

## 3. 官方 Agent / CLI 路径已经存在

X 当前提供：

- 官方 `xurl`：带 OAuth 管理的 curl-like CLI，并自带 Agent `SKILL.md`；
- 官方 XMCP：从 X OpenAPI 自动生成 200+ MCP tools，支持 allowlist；
- 官方 X `skill.md`：面向 Agent 的 API 能力摘要；
- OpenAPI、Python/TypeScript XDK 与 Docs MCP。

来源：

- [Agent Resources](https://docs.x.com/tools/ai)
- [MCP Servers](https://docs.x.com/tools/mcp)
- [xurl](https://docs.x.com/tools/xurl)
- [skill.md](https://docs.x.com/tools/skill-md)
- [官方 XMCP 仓库](https://github.com/xdevplatform/xmcp)

当前比较：

| 路径 | 优点 | 当前缺点 |
|---|---|---|
| `xurl` | 官方 CLI；OAuth 与 token 持久化思路成熟；终端 JSON 对 Agent 省 token；可调用 raw API | 仍需开发者账号、App、凭证与预付 credits；需要装入镜像和账号包 |
| XMCP | 官方；接口自动生成；Agent 直接用工具；支持 allowlist | 当前启动 OAuth token 只存内存；默认 200+ tools 会增加上下文；仓库当前 stdio 与预置 token 改进仍在 PR 中 |
| 自写 CLI | 可做最窄输出和公司级配额 | 重复官方已有能力，认证、端点演进和政策维护成本最高，不应作为首选 |
| Playwright 网页操作 | 已有登录态，能覆盖 UI-only 动作 | 官方明确禁止 non-API automation，存在永久封号风险 |

若未来重新考虑 API，可优先评估官方 `xurl`，再视真实 token/完成度证据决定是否需要薄封装。本任务依据用户裁决不采用该路线。

## 4. API 覆盖与成本快照

官方 API 已提供 own posts、mentions、home timeline、搜索、用户读取、发帖/回复/引用、删除帖子、媒体、DM、关注、点赞、列表等能力。官方 XMCP 的 allowlist-ready 工具清单可作为当前覆盖证据。

按 2026-07-10 官方 pricing 页面：

- own-data reads 为 `$0.001/resource`；
-普通 Post read 为 `$0.005/resource`，User read 为 `$0.010/resource`；
-普通无 URL 内容创建为 `$0.015/request`，带 URL 内容创建显示为 `$0.200/request`；
-用户交互创建为 `$0.015/request`，interaction delete 为 `$0.010/request`。

来源：[X API Pricing](https://docs.x.com/x-api/getting-started/pricing)

价格只用于当前方案判断。Skill 不应背诵价格；工具层应读取实际响应/账单并设公司级预算。

## 5. 资料编辑与置顶缺口

当前官方 X API 文档与官方 XMCP 的完整工具清单支持读取 bio、头像、banner、URL、handle 和 pinned post，但未列出修改这些资料或 pin/unpin post 的写端点。X API v1.1 被官方标记为 legacy、limited support；公开新文档未给出这些操作的稳定替代。

因此目前只能确认：

- 读取资料与置顶内容：API 可行；
- 发帖、回复、引用、删除等：API 可行，但受自动化规则约束；
- 修改资料与 pin/unpin post：需要用实际开发者凭证验证 legacy endpoint 是否仍可用；
- 若 legacy 不可用，浏览器回退是技术可行但政策高风险，不能伪装成合规路径。

实现设计必须让这个缺口显式可见，不能让 Agent 在不知情时静默换成网页脚本。
