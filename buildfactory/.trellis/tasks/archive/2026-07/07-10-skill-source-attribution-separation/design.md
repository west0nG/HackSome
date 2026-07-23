# Design — Skill 来源说明与执行上下文分离

> 依据：`research/audit-summary.md`（跨组汇总）+ 5 份逐项审计（`research/audit-*.md`）。
> 审计已完成 AC1 要求的全量清单；本文只做方案决策，逐项迁移映射见审计文件的 item ID。

## 0. 审计给出的地形（决定设计的三个事实）

1. **82/82 vendored 文件对上游逐字节验证全部成立**，且 vendor 后零改动。vendored 树内的一切来源文字（含 gen-image patterns 的 35 条 `Source concept` 注释、guizang 的文内说明）都是**上游自带内容**，按 R5/AC4 不可就地编辑。
2. **可自由编辑的 C1 全部在 host 层**：7 份 host `SKILL.md`、find-opportunity/decide-direction 的 6 份 reference、以及 `superdesign/token-checklist.md`（提取件、本就不是 byte-exact）。共约 30 项、14 个文件。
3. **10 个 skill 完全干净**；PRD 点名的 when-idle 注释已在 07-10 重写中消失（内容存于 git 历史 + archive），无需处理，只在迁移台账记录处置。

## 1. 决策一：旁路文件形态 — 每 skill 单一 `ATTRIBUTION.md`，不引入 `MAINTENANCE.md`

- 现有 5 份 ATTRIBUTION.md 已经同时承载"归属表 + host 改编说明 + 上游同步策略"，运转良好。
- PRD R2 的 MAINTENANCE.md 是"默认归位方式"，同时明确"已存在旁路文件时优先合并、不得出现多个真相源"。拆两个文件只会制造第二真相源。
- 结论：**每个 skill 一份 ATTRIBUTION.md，内部分节**（来源与许可证表 / host 改编与同步策略 / 研究出处与决策指针）。新建 3 份（find-opportunity、decide-direction、create-role），沿用并增补现有 5 份。
- 旁路语义：ATTRIBUTION.md 不被任何执行正文指向（现存 5 处 "see ATTRIBUTION.md" 指针随迁移一并删除，闭包收口）；靠 copytree 整树物化随 skill 落地（`agent/loadout.py:61`，现状已满足，测试锁住）。

## 2. 决策二：vendored 内的上游来源内容 — 原样保留 + 显式登记豁免（不做"无来源执行层"）

PRD R5 给了两条路：影子执行层（canonical 原件旁路化 + 生成去来源副本供执行读取）或有方案的保留。选**原样保留 + 登记豁免**：

- 上游文内来源说明是**第三方作品的组成部分**，不是我们的出处污染；PRD 的核心问题是"我们写的来源注记进入执行上下文"，这一半已由 host 层迁移解决。
- 影子层代价不成比例：de-ai-ify `zh/` 全树内链互引（integrity 测试逐链检查）、gen-image 24 文件、design-asset 29 文件都要生成副本并重写路由；"Sync = re-fetch" 维护模型变成 "re-fetch + 重新生成 + 重新验链"；树体积翻倍。
- 换来的只是删掉每文件几行的上游自我引用，不改变任何行为。
- 处置：这些文件整棵子树进防回归扫描器的 **vendored 豁免登记**（见 §4），ATTRIBUTION.md 继续作为来源真相源。若后续长跑观察到上游噪声实际造成行为问题，再按 R5 预案对单个文件升级影子层——本轮不做。

## 3. 决策三：host 层迁移方案（逐项映射 = 审计 item ID）

按 skill 分组迁移，每组一个 commit，commit message 引用 item ID，使 AC8 的"每项正文删除对应旁路迁移记录"可直接 diff 审阅：

| Skill | 动作 | 依据 |
|---|---|---|
| find-opportunity | 删 5 条 HTML 注释（FO-1、IP-1、KDP-1、ETSY-1、GUM-1）；新建 ATTRIBUTION.md 收纳 PG/gstack/Amy Hoy 等约 24 个来源 + 6 个 research 路径（已解析为 archive 绝对路径）+ 已删任务 07-01 指针修正；IP-2 边界句保留（判定为 C3 定位说明） | audit-inhouse |
| decide-direction | 删 2 条 HTML 注释（DD-1、DC-1，后者还会进 reviewer 子代理上下文）；新建 ATTRIBUTION.md（gstack 系谱 + ceo-skill-reuse.md archive 路径） | audit-inhouse |
| create-role | 删 CR-1 注释；CR-2 混合句按 R4 重写——保留 capability-first 行为规则、迁走 "07-06" 决策指针；新建 ATTRIBUTION.md（CAMEL/AG2、Apache-2.0 标注） | audit-inhouse |
| mine-customer-voice | 删 MCV-1 括注、MCV-6 整段 `## Sources`（ATTRIBUTION.md 已是严格超集）；MCV-2/3/4/5 中性化改写——保留路径映射规则，去掉 "vendored/upstream" 出处措辞 | audit-voice-visual |
| visual-iterate | 删 VI-1 "vendored" 一词、VI-2 括注、VI-3 整段 Rubric sources（AGPL 例外表述在 ATTRIBUTION.md 原样保留） | audit-voice-visual |
| de-ai-ify | 删 H1 整段 `## Sources`（内容 100% 重复于 ATTRIBUTION.md）；H2 路由句去 "vendored" 改纯行为表述；不碰 `zh/references/sources.md`（上游自有文件、3 处内链指向，删了会挂 integrity 测试） | audit-de-ai-ify |
| gen-image | SKILL.md 3 处（L8/26/34）去 "vendored smixs skill / Host adaptations" 措辞，保留全部路由行为 | audit-gen-image |
| design-asset | SKILL.md 5 项 C1 部分改写（保留路由，去来源措辞；A 系列中 3 项 C3 不动）；token-checklist.md 重做——去掉标题出处、provenance blockquote、"Host adaptation notes" 标题（B1-B6），license blockquote 与提取细节**先吸收进 ATTRIBUTION.md 再删**（X6 缺口）；escape hatch（upstream-SKILL.md 条件路由）为 C3 保留 | audit-design-asset |

行为语义不变（R4/AC8）的机械保证：每个 commit 内，执行正文的删除行 ↔ ATTRIBUTION.md 的新增行一一对应；混合句只改写不整删；C3 清单（各审计文件已逐项列出）为"不许动"红线。

## 4. 决策四：防回归检查（R6/AC6）— `agent/tests/test_skill_provenance.py`

新增一个测试模块，含扫描器函数 + 显式登记表 + 自测 fixture：

- **扫描范围**：`agents/assets/skills/<skill>/**/*.md` 减去旁路文件（`ATTRIBUTION.md`、`LICENSE*`、`COMMERCIAL_LICENSING.md`）减去登记的 vendored 豁免子树。
- **规则 1 — 零 HTML 注释**：host 文件不得含 `<!--`（对齐 07-10 已拍板的 skill 资产零注释原则）。vendored 豁免子树除外（上游自带教学注释、Source concept 等）。
- **规则 2 — 出处关键词**：`adapted from` / `distilled from` / `inspired by` / `source concept` / `provenance` / `vendored` / `upstream` / `ATTRIBUTION.md` / `MAINTENANCE.md`（大小写不敏感、词组精确），命中即失败，除非 (文件, 词组) 在功能白名单登记。刻意不禁 `source`/`来源` 泛词（R6 明确要求）。
- **规则 3 — 执行→旁路指针**：host 执行文件不得提及 ATTRIBUTION.md（已并入规则 2 关键词）。
- **登记表**：模块内常量，两张——`VENDORED_EXEMPT_SUBTREES`（11 棵：de-ai-ify references/en-* + zh/、gen-image smixs-image/ + codex/、design-asset 5 个 vendor 目录、mine-customer-voice references/、visual-iterate references/guizang/，每条附上游 + byte-exact 声明理由）和 `FUNCTIONAL_ALLOWLIST`（(文件, 词组, 理由)，如 design-asset escape hatch 行提及 `upstream-SKILL.md` 文件名）。host 层中性化改写会把白名单需求压到个位数。
- **物化断言**：登记为 vendored 的子树，其 skill 根必须存在 ATTRIBUTION.md 与对应 LICENSE 文件（repo 侧）；物化路径本身已由 `test_loadout.py`（整树 copytree）+ `test_resident_loadout.py:100/127/149`（ATTRIBUTION 落地）锁住，新增 3 份 ATTRIBUTION.md 补进 resident 断言。
- **AC6 fixture 自测**：tmp_path 造一个合成 skill 树、注入一条来源 HTML 注释和一条 "adapted from" 可见句 → 断言扫描器逐条报出；再造干净树 → 断言零报告。保证"新增来源注释时测试会失败"不是靠碰运气。

## 5. 决策五：ATTRIBUTION.md 记录修正（法律/追溯，随迁移同轮落地）

1. **superdesign 许可证更新**：上游现为 AGPLv3 双许可，design-asset ATTRIBUTION.md 的 "No license file (NOASSERTION)" 已过时——更新为 AGPLv3 dual，**保留 2026-07-02 用户批准史**（内部使用立场与 guizang AGPL 先例一致，无需重新审批，但在审阅时向用户明示）。
2. **补 commit pin**：visual-iterate（guizang）与 de-ai-ify（三个上游）只记了 "main @ 日期"，把本次验证得到的 SHA 写入，byte-exact 声明变为可复验。
3. **修失效指针**：gen-image ATTRIBUTION 的 "research doc §4.5 / task prd AC4"、find-opportunity 注释里的已删任务 07-01-ceo-monetization——统一替换为审计已解析出的 `archive/` 绝对路径。

## 6. 范围外事项（明确不做，留决策给用户）

- **codex 上游 "Open an issue on this skill's repo"（cli-reference.md:149）+ SECURITY.md 上游联系方式**：在执行闭包内、byte-exact 不可编辑，属行为隐患（同 first-test 越权外部 PR 一类）。修复手段（host 层反指令或 fleet 级护栏）会**改变行为**，超出本任务"语义不变"边界——建议另开小任务。
- **when-idle 历史注释找回**：内容在 git 历史 + archive 完好，不建 MAINTENANCE.md，台账记录处置即可。
- 运行时代码（loadout/provisioner）零改动；不重命名 guizang "escape hatch" 等功能性路由词汇。

## 7. 兼容与回滚

- 纯内容迁移 + 一个新测试模块；`agent/loadout.py` 等运行时代码不动。
- de-ai-ify integrity 测试（全树链接闭包）是迁移的安全网：删 H1 段连带删除其对 ATTRIBUTION.md 的行内提及，链接不悬空。
- 回滚：每 skill 一个 commit，任意一组可独立 `git revert`；扫描器 commit 放最后，revert 内容组时先 revert 扫描器组或临时加登记即可。
