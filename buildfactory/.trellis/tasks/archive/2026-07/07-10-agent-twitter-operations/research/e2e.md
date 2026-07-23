# 真实账号 E2E 记录

## 结论

`operate-twitter` 已在 Growth 的真实 fresh-per-wake runtime 中自动触发，能先读
`/company`，再通过现有 Playwright 登录态识别实时 X 账号。首次验收覆盖一项真实
删除；用户随后改为手工清理历史，因此自动批量删除在继续前终止。2026-07-11 用户再次
明确授权自主完成真实账号测试后，第三个 fresh context 补齐了发布、回复、置顶/取消、
资料修改/恢复、删除、canonical 核实与 `/company` 写回，独立 verifier 从实时 X 复核
PASS，最终没有测试残留。

这轮真实运行也给出了明确的后续 CLI 依据：长历史盘点会产生大量页面快照和 token，
批量维护不适合长期依赖逐条浏览器交互。

## 环境与装载

- 测试实例：`thirdtest`，浏览器账号包：`foundagent`。
- Growth runtime：Claude Code，fresh-per-wake。
- 物化位置：`/sessions/growth/skills/operate-twitter/`。
- 已确认 `SKILL.md` 与四个 playbook 均存在；Playwright 使用既有 Chromium
  storage state，没有使用 X API、`xurl` 或 XMCP。

## 第一回合：状态恢复与精确删除

- Goal：`gc22193b19b3c457186bd0c9cc346c652`。
- fresh session：`97a993f1-366a-4f4f-844b-b43665237403`。
- Runtime 明确调用了 `Skill({skill: "operate-twitter"})`；随后调用
  `company-state`，先读 `/company/MAP.md` 和相关 topic，再打开实时 X。
- `/company` 当时没有专用 X 状态叶子。实时账号识别为：
  - display name：`Solvo`
  - handle：`@Solvotheagent`
  - profile：`https://x.com/Solvotheagent`
  - 初始显示：116 posts、8 following、0 followers、空 bio。
- 回合在实时页面中识别出明确测试帖：
  `https://x.com/Solvotheagent/status/2074071054834974853`。
- 通过 X 网页的 Delete 菜单与确认对话框删除；随后重新打开 canonical URL，
  页面显示 `Hmm...this page doesn't exist.`，profile 计数变为 115。
- 运行还识别出完整 Posts+Replies 规模为 116，原创 posts 为 42。该枚举明显消耗了
  过多页面上下文，因此实现随后补入了“最小决策快照、非显式要求不全量枚举、长操作
  先写可恢复状态、批量核实”的规则。

## 第二回合：新上下文恢复与用户取消

- Goal：`g1c42a8698bef42f1bed3bfc479a64802`。
- fresh session：`b86dce0b-639d-4d75-8ecf-a78c1517d4d6`。
- 新上下文没有继承第一回合会话记忆，仍从 `/company` 与实时 X 重新识别出
  `@Solvotheagent`，并读到删除后的 115 posts；这验证了 live-X-first 的跨回合恢复。
- 用户随后决定手工删除全部旧内容。该回合只完成公司状态读取、账号识别和 profile
  盘点，尚未开始第二次删除；收到取消后，Claude/Playwright 子进程被终止。
- 两个测试 Goal 均标记为 `killed`，原因明确记录为 operator cancellation，以免 watchdog
  在未来重试并继续删除。

## 第三回合：完整可回滚 E2E 与独立验收

- Goal：`g6f03cc141ae7472eadc213ac5cef6d3b`，终态 `done`、0 次重试。
- Growth fresh session：`84db7881-6633-4cb9-9be2-09676130ba73`。
- Verifier fresh session：`0236c250-2b31-4237-ac2d-b04381fa9bb2`。
- 部署前发现 runtime Skill 与提交版本 hash 不一致；只在 Growth 空闲后重启该 resident，
  物化后的 `SKILL.md` SHA-256 与 source 完全一致，未打断 Builder 的在途 Goal。
- 实时 baseline：`@Solvotheagent` / `Solvo`，115 posts、无置顶、Bio/Location/Website
  为空，既有公开内容保持不动。
- 唯一测试标记：`FA-X-E2E-20260711-A595578`。临时创建并实时核实：
  - root：`https://x.com/Solvotheagent/status/2075625058765291673`
  - self-reply：`https://x.com/Solvotheagent/status/2075625267499053322`
- root 从公开 profile 完成置顶→核实→取消置顶→核实；Bio 从空值改为标记值并在公开
  profile 核实，再恢复为空并核实。
- 依赖安全顺序删除 reply、再删 root；两个 canonical URL 都返回
  `Hmm...this page doesn't exist.`。最终 profile 精确回到 115 posts、无置顶、空 Bio，
  Name/handle/Location/Website 与既有内容均未变化。
- Growth 写入自然生长的 `growth/x-account.md` 并执行 `company.py record`。独立 verifier
  重新打开 profile、Replies、两个 URL 和实时 marker search，确认零残留后 PASS。
- 运行成本：Growth 835.89 秒、`$11.0051`；verifier 193.82 秒、`$1.0948`。重复网页
  快照和大页面上下文是主要成本，证明后续批量/重复动作值得进入自有 CLI 设计，而不是
  继续依赖逐步浏览器快照。

## 保留、删除与未覆盖项

- 已删除：显式旧测试帖 `2074071054834974853`，以及第三回合创建的 root/reply 两项
  临时内容。
- 自动化停止时保留：其余 115 个 profile 计数所代表的历史；用户选择手工处理。
- 已覆盖：原创发帖、自回复、pin/unpin、Bio 修改/恢复、精确删除、跨 fresh context
  实时恢复、最终 `/company` 写回与独立 verifier 复核。
- 未覆盖：quote、follow/unfollow、like/unlike、头像/banner/handle 修改与 DM；这些不为
  扩大测试面而额外制造外部影响，现有 playbook/静态契约仍保留对应公共能力。DM 继续
  明确不在首期范围。
- 未记录任何 cookie、token、storage-state 内容或其他 secret。
