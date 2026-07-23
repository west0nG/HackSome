# Research: social 写作 skill vendor 源对比（blacktwist vs coreyhaines）

- **Query**: implement.md 批1 第2项动手前细看 `coreyhaines31/marketingskills` 的 `social`，并回答用户问题"有没有更好的开源可用"
- **Scope**: external（GitHub API 取真实文件内容 + repo 搜索）
- **Date**: 2026-07-02
- **结论先行**: 用户已拍板**混合方案**——blacktwist 创作类原子 skill 为骨架 + coreyhaines `social` 独有硬货（短视频/platform-limits/listening）补齐。

## coreyhaines `social` (2.1.0) 细看结果

巨石：SKILL.md ~400 行 + 7 refs（共 ~38KB）。按 ①/②/③ 拆：

- **值钱（③）**：`platform-limits.md`（各平台 hashtag/字数硬限制，含 "TikTok max 5 hashtags since Aug 2025" 这类时效数据）；SKILL.md 内的**带时间轴短视频结构**（Problem-Solution / List / Tutorial，0-3s/3-10s/…）；`short-form-video.md`（hook 库按目的分类 + 脚本模板 + Story Arc/POV 结构 + 字幕规格 "MAX 2 lines / 3-5 words per line"）；`listening.md`（12KB：每日 triage loop + 评分 rubric + **Reddit/HN/Bluesky curl 配方** + per-platform notes）+ 伴生 `listening-sources-template.md`；"LinkedIn 正文别放链接放首评" 类平台潜规则；repurposing 的 content-atom 表。
- **要剔**：互动例程/analytics 解释/卡壳建议（LLM 常识）；大量**面向人类操作者**（"每周 2-3 小时 batch"、CapCut/Descript 工具推荐）。
- `reverse-engineering.md`（5.5KB, 6 步爆款逆向）：偏调研闭环，observation-gated → **押后**。

## 生态扫描（GitHub repo + code search）

| 候选 | ★/License | 判定 |
|---|---|---|
| **blacktwist/social-media-skills** | 295★ MIT | **入选骨架**。14 个原子 skill（创作 6：post/thread/carousel/caption/hook-writer + content-repurposer；策略 3 + 分析 4 + context 1）。抽查 post-writer/hook-writer：内容具体（LinkedIn 1200-1500 chars 最优、链接放首评、9 hook 模式各带 when-it-works）。**形态 = 我们要的原子可组合**，平台多 Threads/Bluesky/Pinterest/YouTube。每 skill 单文件 SKILL.md（evals 不需 vendor）；互相以 `-sms` 名交叉引用（42 处指 `social-media-context-sms` 共享上下文 → 统一改指 `/company`）。 |
| stevenflanagan1/social-ai-team | 147★ **无 license** | 排除（不能 vendor）。 |
| bradautomates/head-of-content | 132★ MIT | 调研类（x/ig/tiktok/youtube-research），依赖 API key；属押后的 read-signal，记档。 |
| socialclaw | 53★ MIT | 发帖 CLI = outbound，批2 `use-accounts` 再看，记档。 |
| xhs-images | 40★ MIT | 小红书 infographic 生成，批2 visual-asset/中文平台再看，记档。 |
| 其余（caption 生成器/hyperfx 等） | — | 太窄或绑自家 MCP 服务。 |

**gap 记档**：两家皆西方平台，中文平台（小红书/微信）无覆盖 → 绑批2 账号/MCP 方向再议。

## 落地决策（写进 design §5.6）

4 个新 skill，全部套 de-ai-ify 模式（host SKILL.md = 唯一原创适配层；上游文件 verbatim 进 `references/`）：

1. `draft-social` — refs: blacktwist post/thread/carousel/caption/hook-writer 5 份 + coreyhaines `platform-limits.md`
2. `repurpose-content` — refs: blacktwist content-repurposer
3. `short-form-video` — refs: coreyhaines `short-form-video.md`；3 个带时间轴结构（上游 SKILL.md 独有）由 host 收编并在 ATTRIBUTION 注明
4. `social-listening` — refs: coreyhaines `listening.md` + `listening-sources-template.md`

统一适配（host 层说明，不改上游文件）：`-sms` 交叉引用 → 同 skill 内兄弟 catalog 或"未装，忽略"；`.agents/social-media-context-sms.md` → 读 `/company`（company-state skill）。

## Caveats

- blacktwist 只抽查了 2/6 创作 skill 全文，其余看了章节结构（均为 平台规格+结构模板 形态）；vendor 时如发现某份泛泛可再裁。
- star 数为 2026-07-02 快照。
- coreyhaines `post-templates.md` 与 blacktwist hook/post 模式重叠 → 不 vendor（减冗余）。
