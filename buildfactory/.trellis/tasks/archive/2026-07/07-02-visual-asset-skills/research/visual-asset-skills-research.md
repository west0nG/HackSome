# visual-asset 三原子 skill 调研报告（DESIGN / IMAGE-GEN / ITERATION-LOOP）

- 任务：`.trellis/tasks/07-02-visual-asset-skills`（2026-07-02 从 `06-28-role-growth` 单拆，随迁本报告），对应父 design §5.5
- 日期：2026-07-02
- 方法：7 条并行 lane（Anthropic 官方 / 英文社区 GitHub / skill 市场 / 中文互联网 / 图像提示词 / Codex 生图 / 本机 Codex 实测 + 本机 skill 盘点）→ 深读候选 → 对抗性复核（关键 claim 逐条证伪尝试）→ 许可证一手核验（逐个 fetch LICENSE 文件原文，不信 README 徽章）
- 标注约定：**【已核实】**= fetch 了一手来源（raw 文件 / GitHub API / 官方文档页）；**【未核实】**= 仅搜索摘要或二手转述；**【本机实测】**= 在本机跑通验证

---

## 0. 结论先行

1. **三个原子 skill 都不必从零自写，但 vendor 覆盖度差异很大**：
   - **DESIGN**：可 vendor 内容最厚。核心组合 = Anthropic `frontend-design`（Apache-2.0，56 行，整体 vendor）+ `jiji262/claude-design-skill` 的 `design-styles.md`/`design-principles.md`（MIT，含 10 套设计语言 + 反 AI-slop 清单 + 具体阈值）+ Anthropic `theme-factory` 的 10 套色板 spec（Apache-2.0）。自写 gap：静态画布词汇适配、社媒平台尺寸规格、HTML→PNG 渲染管线。
   - **IMAGE-GEN**：提示词层可整树 vendor `smixs/visual-skills` 的 `image/`（MIT，已是 SKILL.md+references/ 形状，覆盖 Nano Banana + GPT Image 2）；**调用层无现成可整搬**，需自写薄 wrapper（Codex CLI 路线 + API fallback），可参照 `JunSeo99/claude-skill-codex-imagegen`（MIT）与 `KingGyuSuh/codex-image-in-cc`（Apache-2.0）。
   - **ITERATION-LOOP**：**唯一没有现成独立 skill 可整体 vendor 的一个**——全生态扫描没找到"截图→VLM 批评→修→循环"的独立成品。以自写为主，素材来源充足：Anthropic 官方 best-practices（视觉反馈环是官方明文推荐模式）、OneRedOak design-review 的 triage 矩阵（MIT）、gstack design-review 的阈值 rubric + 风险终止公式（MIT）、guizang 的确定性脚本校验器（AGPL——**用户拍板解禁，可直接 vendor**，见 §0.5 例外）。
2. **Codex 封装生图：技术上完全成立（本机 e2e 一次跑通），但"当生产主路径"经对抗复核被降级为 partial**。原因：官方文档明确推荐自动化用 API key；ToS 灰色 + 有封号先例；配额与常驻 agent 的编码用量共享且图像回合烧 3-5 倍配额；而且**省钱动机已基本消失**——gpt-image-1-mini API 仅 $0.005/张、gpt-image-2 low $0.006/张【已核实】。**建议：API key 为主路径，Codex wrapper 为可选副路径（feature flag 后面，best-effort）**。
3. **与 design.md §5.5 的张力**：§4 表把 `visual-asset` 标为"**自写·复合**"，本调研结论是**内容侧大半可 vendor**（与 de-ai-ify 的教训同构），真正自写的只剩编排层、调用 wrapper、平台规格三块——建议改标"混合 vendor + 自写编排"。§5.5 的 (a)(b)(c) 三分法与用户三原子拆分完全对得上：(b) 设计/排版 ↔ DESIGN，(a) 生成 ↔ IMAGE-GEN，(c) 修复/迭代 ↔ ITERATION-LOOP，方向无冲突。
4. **"Datap" 未能识别**。唯一同名实体 datap.ai 是面向合规中型企业的 AI 数据治理产品，不是 skill 市场、无设计 skill【已核实】。实际调查过的市场见 §1.3，需用户澄清所指。
5. **许可证雷区已逐目录核验**（总表见附录 A）。绝对不可 vendor：Anthropic `pptx/docx/pdf/xlsx`（专有 source-available，明文禁提取/复制/衍生）、`black-forest-labs/skills` / `UI2Code_N` / `ky-design-to-html-skill` / `html2png/skills`（NOASSERTION 或根本没有 LICENSE 文件——html2png README 自称 MIT 但仓库无 LICENSE 文件，GitHub license API 返回 null【已核实】）。**⚠️ 用户拍板例外（2026-07-02，内部使用前提）**：`guizang-social-card-skill`（AGPL-3.0）与 `superdesign`（无有效 license）**解禁可 vendor**——AGPL 在内部使用、不对外分发/不对第三方提供网络服务时不触发 copyleft 义务，若未来本 repo 开源或对外分发需回头处理；两者 vendor 时 ATTRIBUTION 均注明原许可证状态 + "用户拍板"。superdesign 深读已补（2026-07-02）：判定 borrow-rewrite 为主 + token 表可 verbatim 提取；其"变体分叉/品牌抽取"两项传闻能力**证伪**（前者仅剩已废弃 prompt 一句、后者整仓不存在），对 ITERATION-LOOP 零贡献。判定详见 §1.2 / §1.4 / §5。

---

## 1. 设计类 skill 盘点

### 1.1 Anthropic 官方（github.com/anthropics/skills，157k★）

⚠️ 该仓库**无根级 LICENSE，按目录分裂授权**：设计类均 Apache-2.0（逐目录 fetch LICENSE.txt 验证），但 `docx/pdf/pptx/xlsx` 四件套为 Anthropic 专有许可，明文禁止提取/复制/衍生/分发——**连文字都不能拷**【已核实】。

| skill | URL | 许可证 | 对三原子的映射 | 判定 |
|---|---|---|---|---|
| **frontend-design** | github.com/anthropics/skills/tree/main/skills/frontend-design | Apache-2.0【已核实】 | **DESIGN 最佳蓝本**：56 行纯 Markdown，逐行都是"压制 LLM 默认审美"——点名三种 AI 套路外观（奶油底 #F4F1EA+衬线+terracotta / 近黑底+荧光绿或朱红 / 报纸细线密栏）、两遍流程（先出 4-6 色 token 系统+ASCII wireframe+signature 元素，再对照 brief 自我批判）、禁无意义 01/02/03 编号、"Chanel 出门前摘掉一件饰品"克制启发、CSS specificity 互相抵消 gotcha | **vendor 整体** |
| **theme-factory** | .../skills/theme-factory | Apache-2.0【已核实】 | DESIGN 的一致性子件：10 个主题文件（ocean-depths / tech-innovation / golden-hour…），每个含 4 色 hex 色板+字体配对+适用场景，机器可读 schema 已逐字节验证 | **vendor themes/\*.md**（原 SKILL.md 的"问用户选主题"人工确认流程剥掉，改自治选择；字体配对偏薄——全是 DejaVu Sans，可换） |
| **canvas-design** | .../skills/canvas-design | Apache-2.0【已核实】 | ⚠️ **深读后降级**：sweep 阶段看好，两轮深读一致认定体裁错配——它面向"虚构艺术流派宣言→抽象艺术海报"，刻意把文字压到 10%，与 quote card / 小红书图（文字承载 60-90%）**方向相反**；且通篇 "museum-caliber/meticulously crafted" 式修饰属我们纪律禁止的泛泛填充；未给任何 HTML/CSS 渲染机制 | **skip 本体，只借 2 条**：①"不溢出/不重叠/留边距"硬检查清单 → 给 ITERATION-LOOP；②"修订时禁止加新元素、只精修已有"反默认规则（LLM 修图默认=堆料）→ 给 ITERATION-LOOP。**可选独立 vendor canvas-fonts/**（35 个 .ttf、约 18 字族、逐字体 SIL OFL 授权，须连 \*-OFL.txt 一起拷） |
| brand-guidelines | .../skills/brand-guidelines | Apache-2.0【已核实】 | 内容是 Anthropic 自家品牌 spec，不能照搬；但它是"如何把品牌 spec 写成 skill"的官方结构模板（色板+层级+字体角色+fallback+accent 循环） | 借结构，给未来自家 brand skill |
| web-artifacts-builder | .../skills/web-artifacts-builder | Apache-2.0【已核实】 | 深读后**不 vendor**：React18+Vite+Tailwind+shadcn+Parcel 全家桶对静态单文件 HTML→PNG 是不成比例的机器；且它**不含任何截图/PNG 能力**（视觉 QA 明文写成"可选、延后"） | 借 2 条：两阶段"组件式书写→打包单文件"形状；"避免过度居中/紫渐变/统一圆角/Inter 字体"一句反 slop 启发 |
| algorithmic-art | .../skills/algorithmic-art | Apache-2.0【已核实】 | 次要：p5.js 生成艺术，seeded-randomness 可复现模式对插画/背景纹理的零成本程序化路线有借鉴 | 押后 |
| slack-gif-creator | .../skills/slack-gif-creator | Apache-2.0【已核实】 | 对 ITERATION-LOOP 的启示：把平台硬约束写成**可执行 validator 脚本**（validate_gif()）而非文字，是官方推崇的反馈环形态 | 借模式 |
| **pptx**（及 docx/pdf/xlsx） | .../skills/pptx | **Anthropic 专有——禁 vendor**【已核实 LICENSE 全文】 | 讽刺的是它有官方最完整的视觉迭代闭环："Assume there are problems. Your job is to find them"——soffice+pdftoppm 渲成图→派 fresh-eyes 子代理视觉 QA→修→重渲 | **一个字都不能拷**；同一模式必须自写实现（模式本身不受版权保护） |
| skill-creator | .../skills/skill-creator | Apache-2.0（LICENSE 首行已验证） | 写三个 skill 时的格式参照；本机也有插件版 | 参照 |

**官方文档两篇**（非代码，引用不 vendor）：
- Skill authoring best practices（platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices）【已核实】：①"Implement feedback loops"（validator→fix→repeat）与 ②"Use visual analysis"（凡可渲成图就转图让 Claude 看）两节 = **ITERATION-LOOP 的官方背书**；③体量硬约束：SKILL.md 正文 <500 行、引用文件只嵌一层、>100 行参考文件加 TOC；④"Claude 已经很聪明"一问与我们三道检验同源。
- Engineering blog "Equipping agents for the real world with Agent Skills"【已核实】：确认**官方没有视觉产出专属秘籍**，也**没有 IMAGE-GEN（提示词/调图像模型）类官方 skill**——这两块必须靠社区源和自写。

### 1.2 英文社区（GitHub）

| 仓库 | 许可证 | 成熟度 | 映射与判定 |
|---|---|---|---|
| **jiji262/claude-design-skill** | MIT【已核实 raw LICENSE】 | 129★（未经 API 交叉验证） | **DESIGN 第二支柱，vendor 两个文件**：`design-styles.md`（10 套设计语言×5 流派，每套带具体字体栈/hex/网格规则/Avoid 清单/适用与不适用）+ `design-principles.md`（反 slop 清单点名具体套路：紫蓝渐变、emoji 弹点、圆角卡+左色条、SVG 假产品图、Inter/Roboto 默认；硬阈值：slides 正文 ≥24px、印刷 ≥12pt、触控 ≥44px、间距 4/8/12/16/24/32/48/64）。两文件自包含可单独 vendor。**不 vendor** 其 React/Babel 原型类 assets 与 workflow（面向交互 artifact，非静态图）。verification.md 只借 loop 形状（依赖我们没有的 gstack /browse） |
| **JunSeo99/claude-skill-codex-imagegen** | MIT【已核实 raw LICENSE】 | 8★，2026-05 更新 | **用户 Codex 想法的现成实现**，IMAGE-GEN 调用层直接 vendor 依赖闭包：skill/SKILL.md + references/cli-reference.md（精确 flags/输出路径/尺寸后处理/成本表）+ prompting-guide.md（五槽提示词公式+文字渲染规则+反模式表）+ SECURITY.md + LICENSE。细节见 §4 |
| **smixs/visual-skills** | MIT【已核实 raw LICENSE】 | 68★，活跃（2026-07-01 push） | **IMAGE-GEN 提示词层最佳 vendor 目标**：已是 SKILL.md+references/ 形状，强制阅读顺序路由（models→模型文件→golden-rules→任务模块），patterns/ui-social.md 五个参数化模板（IG Story 9:16 / Feed 1:1 等）与我们资产类型近 1:1。⚠️两个 caveat：golden-rules.md 与 text-rendering.md 混有**俄语段落**需翻译；**零调用层**（只产"可复制的 prompt 文本块"，不调 API）。vendor 时须整树带走（SKILL.md 路由表依赖全部兄弟文件，只拷 4-5 个会断链） |
| **OneRedOak/claude-code-workflows** (design-review) | MIT【已核实 raw LICENSE】 | 3,848★（API 验证），但 2025-09 后未更新 | ITERATION-LOOP 借鉴源：8 阶段评审流程 + 4 级 triage（[Blocker]/[High-Priority]/[Medium-Priority]/[Nitpick]）+ "Problems Over Prescriptions" judge 规则（描述问题与影响、不开处方——压制 LLM 默认直接给修法）+ 4.5:1 对比度阈值。**不 vendor 文件**：面向 PR/活网页/Playwright MCP，且 slash-command 引用仓库里不存在的 ../context/ 文件（悬空依赖）；只借上述四件重写 |
| jezweb/claude-skills (design-loop) | MIT【已核实】 | 896★，非常活跃 | ITERATION-LOOP 借鉴：接力棒协议（.design/next-prompt.md 读任务→产出→Playwright 验证→写下一棒）+ 跨页一致性铁律（共享元素逐字复制、不重生成）。状态落盘的 loop 形态可借 |
| Leonxlnx/taste-skill | MIT【已核实 raw LICENSE】 | 自称 54.6k★【未核实】 | 深读后 **borrow-ideas**：多数内容面向交互式营销网站（动效/hover/滚动）不适用静态图。可借：soft-skill 的禁默认清单（Inter/Roboto/Arial 等字体、粗描边图标、灰 1px 边、shadow-md）+ Double-Bezel 嵌套卡片公式 + 10 项出稿前检查单；imagegen-frontend-web 的数值"旋钮"系统（variance/density 1-10 定极）；image-to-code 的 25 项深度看图清单（改写为 ITERATION-LOOP 的 VLM 自检单）。注意大小写：`Leonxlnx`（大写 L） |
| coreyhaines31/marketingskills (skills/image) | MIT（raw LICENSE 已 fetch，字节级复验后再拷） | 约 35.7k★【未核实】 | IMAGE-GEN 借鉴（蒸馏重写不整拷）：**模型选型决策树**（要文字→Ideogram；批量一致→Flux 多参考图；矢量/品牌→Recraft；便宜快→Flux Schnell/Gemini Flash）+ 8 行常见错误表 + **关键判断"永不 AI 生成产品 UI 截图（幻觉），用真截图 2x"**（文中独立出现三次） |
| alonw0/web-asset-generator | MIT【已核实】 | 433★ | og-image/favicon 生成 + 输出校验；og 1200×630 / Twitter 1200×675 规格来源。内部渲染管线未深读 |
| KAOPU-XiaoPu/web-design | MIT【已核实】 | 567★ | "spec first, code second"：先产可编辑 DESIGN.md 再写 HTML——DESIGN skill 的中间产物模式候选 |
| lackeyjb/playwright-skill | MIT【已核实】 | 2,851★ | 渲染→截图原语的无 MCP 替代（agent 现写 Playwright 脚本） |
| superdesign | NOASSERTION（无有效 license）——**用户拍板解禁（2026-07-02）**【license 状态已核实 API】 | 6,611★，已停维（转向 hosted web app；另存在 `superdesign-skill` 姊妹仓，未读，后续候选） | **深读已补（2026-07-02，全树 108 文件 + 6 核心文件原文）**，判定 = **borrow-rewrite 为主**。prompt 全部内联在 `extension.ts`/`customAgentService.ts`（~380 行，两份基本相同），真硬货 15-20 条：反蓝色/Bootstrap 默认压制（点名"NEVER use bootstrap style blue"）、**孤立资产图底反差规则**（浅色组件配深底、反之亦然——直接适用 quote card/海报）、24 个 Google Fonts 收敛清单（按 mono/sans/serif 分桶）、CDN Tailwind+Flowbite 叠加需 `!important` 的 specificity gotcha、**两套完整 oklch token 预设**（neo-brutalism / vercel-linear 暗色，含 8 级阴影栈具体数值）、layout→theme→motion→HTML 定序纪律（人工确认门须改自检门）、ASCII wireframe 先行范例、动效微语法 DSL（`400ms ease-out [Y+20→0]` 式记法）、`{name}_{n}.html` 迭代谱系命名。**可 verbatim 提取：`theme-tool.ts` 的 shadcn 系 design-token 全表**（--background…--shadow-2xl 8 级 elevation）。⚠️ **两项先前 flagged 能力证伪**：变体分叉只剩已废弃根目录 system-prompt.txt 一句"3 平行子代理出变体"（现版 prompt 已删、全仓无任何选优/比较实现，grep 证实）；品牌抽取整仓不存在（themeParser 只是给 LLM 自造色板做 UI 展示）。**对 ITERATION-LOOP 零贡献**（无截图/自评/循环，纯人工看图迭代）。依赖闭包注意：generateTheme 自有工具、CDN 网络依赖（渲染时需外网否则静默裸奔）、oklch 需 Chromium 系渲染器、Flowbite 对静态图无用应弃。ATTRIBUTION 注明"无 license、用户拍板" |
| html2png/skills | **README 自称 MIT 但无 LICENSE 文件 = 视同无授权，skip**【已核实：LICENSE 各路径 404 + API license:null】 | 9★ | 且四个 skill 全是其付费 API（50 req/h）的营销壳。其论点"AI 用 HTML/CSS 排字优于直接生成栅格图"与我们路线一致（佐证非增量）；OG 尺寸表/deviceScaleFactor≥2/delay 1-2s 等可用自身常识重写 |
| omrajguru/brand-social-design | MIT【已核实】 | 2★ | 品牌记忆 + html2canvas 浏览器端导出的架构可借，体量太小不 vendor |
| wuyoscar/GPT-Image2-Skill | MIT（API 确认） | 3,452★ | gpt-image-2 分类 prompt 画廊，内容未读——备选 exemplar 库 |
| OneRedOak 同类 KingGyuSuh/codex-image-in-cc、yazelin/codex-imagegen-skill | Apache-2.0 / MIT【已核实 raw LICENSE】 | 16★ / 0★ | Codex 调用层另两个参照，见 §4 |

### 1.3 skill 市场 / registry（含 "Datap" 排查）

| 市场 | 状态 | 与本任务相关发现 |
|---|---|---|
| **skills.sh**（vercel-labs） | 【已核实】唯一有质量信号（安装量）的 registry | 设计类头部：anthropics/frontend-design 614.7K 装、vercel-labs/web-design-guidelines 431K、Leonxlnx taste 系列合计 490K+ |
| smithery.ai | 详情页对非浏览器 403【已核实现象】 | 有 nano-banana / image-gen（Gemini）类 skill，license 未验证 → needs_browser |
| ClawHub (clawhub.ai) + VoltAgent 索引 | 索引页已核实，详情页 JS 渲染 | 172 个图像/视频 skill；vtl-image-analysis（构图批评框架）是全市场唯一贴近 ITERATION-LOOP 的条目【未核实内容】；NOASSERTION 高发 |
| skillsmp.com | 【已核实】可用 | 本质是 2M+ SKILL.md 的 GitHub 爬虫，只有覆盖没有 curation |
| aitmpl.com | JS 重站，服务器渲染无 skill 列表【已核实现象】 | 无设计类确认发现 |
| **Datap** | **无法识别**【已核实排查】 | datap.ai = 面向 APRA/HIPAA 合规中型企业的数据治理产品，非 skill 市场、无设计 skill；两轮定向搜索无 "Datap" skill 平台。读音相近候选（aitmpl "AI-template"? ClawHub? smithery?）均不像。**需用户澄清** |

**市场层关键空白**：没有任何市场 skill 实现了独立的"截图→VLM 批评→修订"循环——ITERATION-LOOP 注定以自写为主。

### 1.4 中文互联网

| 来源 | 许可证 | 判定 |
|---|---|---|
| **op7418/guizang-social-card-skill**（归藏社交卡片，4.4k★） | AGPL-3.0——**用户拍板解禁（2026-07-02，内部使用）**【已核实 raw LICENSE + API】 | 中文生态最强 DESIGN+ITERATION 范本，**可整树 vendor**（原"只借结构与事实"判定作废；ATTRIBUTION 注明 AGPL + 用户拍板，未来对外分发本 repo 需回头处理）。核心价值：①"选定一套风格系统、绝不混用"（Editorial 16 布局 / Swiss 12 布局、主题白名单禁自定义 hex 保审美底线）；②数字阈值：3:4 画布内容填充 ≥75%、纯空白带 ≤15%、溢出修复分级（1-40px 微调 / 40-90 局部压缩 / 90-160 文本压缩 / 160+ 换布局）、标题间距 28/16px、**360px 缩略图可读性测试**（廉价 VLM 批评代理）；③**确定性后渲染校验器**（node validate-social-deck.mjs，9 条编号规则）——"脚本校验而非 LLM 自评"正是我们 ITERATION-LOOP 想要的结构；④平台事实：小红书轮播 5-9 页 3:4、微信封面 21:9+1:1 成对同文件渲染、Live Photo 小红书 5s/微信 3s、.pvt 只能 AirDrop |
| 火山引擎文章 mp-cover-generator | 文章 n/a；配套 jimeng-mcp-server **无 LICENSE = NOASSERTION**【已核实】 | 唯一完整中文"生图(即梦)+HTML 文字层+Playwright 截图"三层组合实例。**其逆向即梦 free-api 路线自带免责声明"仅限学习、禁止商用、随时失效"——是评估订阅白嫖类方案风险的直接对照组**。可借：多层 text-shadow 描边字色值组合、左文 60-70%/右图 30-40% 构图、capture.js CLI 参数形状（--scale 2 --wait 2000） |
| laolaoshiren/claude-code-skills-zh | MIT【已核实 raw LICENSE】512★ | ⚠️ **深读修正 sweep 结论**：这不是可 vendor 的中文设计 skill 池——是链接索引（awesome-list），自带的 18 个原创 skill 全是开发工具类，与视觉无关。其价值是指路：manwithshit/xhs-images（37★ 小红书信息图，11 风格 6 布局）、alchaincyf/huashu-design（3K★ HTML 原生设计）、nexu-io/open-design（自称 35.3K★，19 设计 skills+71 品牌设计系统）——**均未深读、license 未验证**，是后续候选 |
| ky-design-to-html-skill | **无 LICENSE 文件——比 NOASSERTION 更硬的禁拷**【已核实：LICENSE 各路径 404 + API license:null】145★ | 只可独立重推导思想：区域分序截图对比法（画布→header→nav→main→组件→footer）、transform:scale 画布适配失败模式+三层修复、"廉价感检查单"（字重单一/阴影过黑/圆角无层级/色相单一无中性结构）→ ITERATION-LOOP 自检词表 |
| 平台规格（多来源交叉，非官方文档）【未核实】 | n/a（事实数据） | 小红书：3:4 竖版曝光面积最大（比横版约大 40%），推荐 1242×1660 或生产平衡点 1080×1440，单笔记单比例、≤18 张、≤10MB、文字留 6-8% 安全边距；公众号：头条封面 2.35:1（900×383）+ 分享 1:1（383×383）成对、核心内容居中 600px 安全区、≤5MB。⚠️ guizang 用 21:9(2100×900) 与官方 2.35:1 有小口径差，写 skill 时须自定标准并说明裁切容差。**落地前建议对官方文档复核** |
| 即梦/国产图像 API | 各仓库不一 | 两条路线对照：官方（火山方舟/百炼，稳定可商用）vs 逆向（sessionid 白嫖，禁商用随时失效）。国产官方价：Seedream 4.0 ≈0.20 元/张（社区整理的方舟费用文档，半验证）、通义万相 ≈0.20 元/张【未核实】——**便宜到直接削弱一切白嫖方案的经济动机** |
| vivy-yi/xiaohongshu-skills (271★) | 无 LICENSE = NOASSERTION【已核实】 | 教学型运营文档、无阈值型硬货，参考价值低，列出防止重复调查 |
| 需浏览器补查 | — | linux.do/t/topic/1421061（三平台卡片 skill 自荐帖，403）、知乎两篇（CodeBuddy 小红书封面 skill / xiaohongshu-card-master，403）、火山方舟官方计费页（JS） |

### 1.5 本机已有资产（零获取成本）

| 资产 | 许可证 | 价值 |
|---|---|---|
| gstack `/design-review`（~/.claude/skills/design-review/SKILL.md） | MIT © 2026 Garry Tan【已核实本机 LICENSE 文件】 | **ITERATION-LOOP 最富的量化素材**：10 类 ~80 项审计清单带硬阈值（字体 ≤3、行高 1.5x、行长 45-75 字符、WCAG 4.5:1/3:1、非灰色 ≤12、暗色文字 ~#E0E0E0 非纯白）；**AI-slop 黑名单 10 条**（紫渐变、三列圆圈图标 feature grid="最易识别的 AI 布局"、全居中、统一泡泡圆角、装饰 blob/波浪分隔、emoji 当设计元素、卡片左色条、system-ui 当主字体="放弃排版的信号"）；A-F 评分公式（High 掉一级/Medium 掉半级 + 10 类权重）；**风险自调节公式**（每 revert +15%、组件文件 +5%、>20% 停、硬上限 30 fixes、同一问题 3 次失败升级）。⚠️ 文件 ~85% 是 gstack 平台管线（telemetry/AskUserQuestion/$B/$D 二进制依赖），**不能整拷，只手工提取 ~250 行领域内容并注明出处** |
| gstack design 二进制源码（generate/check/iterate/brief.ts） | MIT 同上 | **实证本机现有生图管线走付费 API**：OpenAI Responses API `tools:[{type:'image_generation', model:'gpt-image-2'}]` + OPENAI_API_KEY + 240s 超时——正是 Codex 想法要绕开的成本点。check.ts 的 3 检 VLM rubric（文字可读性/布局完整性/"像真产品 UI 不像 AI 艺术拼贴"）+ 强制单行 PASS/FAIL 输出协议 → ITERATION-LOOP 直接可借 |
| gstack `/design-shotgun` | MIT 同上 | 反收敛指令带可检验反例："若两个变体互换标题文字而无人察觉，则太相似"；文本概念先行（省 API 钱）再并行生图；每变体自带重试协议（429→等 5s×3） |
| gstack `/design-html` | MIT 同上 | 3 视口截图验证循环、"外科手术式 Edit 不整文件重生成"、**10 轮迭代上限**、DESIGN.md token 持久化（品牌一致性机制） |
| gstack `/codex` skill | MIT 同上 | 无头 Codex 编排的实战脚手架：auth 探测顺序、gtimeout 包裹（330-600s）、stdin 重定向 /dev/null（0.120.0-0.120.2 已知 stdin 死锁）、--json JSONL 流解析、turn.completed 缺失=挂起检测。**注意它完全没用过图像生成**（诚实负样本） |
| frontend-design 官方插件（本机已装） | Apache-2.0【已核实本机 LICENSE】 | 与 1.1 同一文件，agent 环境里已可读 |
| frontend-slides 插件 | MIT © 2025 Zara Zhang【已核实本机 LICENSE】 | **固定画布不变式直接迁移**：每 slide 100vh+overflow:hidden、全部尺寸走 clamp()、图片 max-height:min(50vh,400px)、按 slide 类型的内容密度上限表（"溢出就拆页、绝不滚动"）；STYLE_PRESETS.md 12 套风格；**export-pdf.sh = 现成的逐 .slide 元素 Playwright 截图管线**，改造即得 HTML→PNG 渲染器 |
| dataviz（Claude Code 内置） | 二进制内嵌、无本地文件、license 不明 | 不可提取；若 anthropics/skills 有公开版再 vendor（本轮未发现） |

---

## 2. 生图 skill 素材（IMAGE-GEN）

### 2.1 模型通用 prompt 公式（五家官方指南收敛，可安全写成 skill 的通用核心）

来源：OpenAI Cookbook【已核实】、Google Cloud Nano Banana 指南【已核实】、ai.google.dev【已核实】、docs.bfl.ml FLUX.2【已核实】、Recraft 官方【已核实】、fal.ai Seedream【已核实】：

1. **有序槽位 + 前置加权**：subject → action → composition → setting → lighting → camera/lens → style → palette；**所有模型都对前段 token 加权更高**（JunSeo99 归纳为"前 50 词规则"），风格/主题/情绪放最前。
2. **五槽完整性**（JunSeo99 prompting-guide）：Scene → Subject → Details → **Use case（用途决定尺寸与打磨模式）** → **Constraints（保留/禁止清单）**。"第五槽是多数平庸 prompt 静默失败之处"——漏了就出水印/多余文字。
3. **文字入图**：字面文本用双引号或全大写 + "EXACT TEXT verbatim" 标记；难词逐字母拼写；文本短（通用 3-5 词，Seedream 称 1-10 词【未核实】）；quality=medium/high 给小字密字；**text-first hack**：先用文本回合定稿确切文案，再"渲染 exactly this text"（smixs 与 Google 双源同技）。
4. **系列一致性 = 参考图而非 seed**：所有主流 API 都不主打 seed；Gemini 给参考图**命名**后按名引用（最多 14 张）；gpt-image 用角色锚定图 + 每轮重述保留清单；FLUX pro 档 9MP 总预算（1MP 输出可带 8 张参考）。
5. **编辑 = "只改 X、其余全保持" + 每轮迭代重述保留清单**（OpenAI 官方失败模式表的头号修法）——这条直接贯通到 ITERATION-LOOP：**每次修订必须重注入不变量清单，而不是只描述修法**。
6. 具体化替换泛形容词（smixs Rule 5："shiny"→"brushed steel with matte finish"、"dark green"→"#0d3d2d"）；世界知识锚点省 token（"Bethel, NY, August 1969" 一句唤起 Woodstock 美学）。
7. 反模式表：空洞形容词堆（"stunning, masterpiece, 8K"）、逗号关键词汤、200+ 词失焦（40-80 词最优）、一轮改十处、纯否定句表述弱。

### 2.2 各模型特定分歧（skill 必须分栏写，不能混）

| 维度 | gpt-image-2 | Gemini (Nano Banana) | FLUX.2 | Seedream | Recraft |
|---|---|---|---|---|---|
| 否定 prompt | 可用约束句 | 不鼓励，正向表述（"empty street"非"no cars"） | **禁止**，一律改正向 | 容忍（"not cartoon-like"） | — |
| 尺寸控制 | 边 ≤3840px、双边 16 倍数、比例 ≤3:1、总像素 65.5 万-829 万、**可靠上限 2560×1440**【已核实】 | aspect_ratio + image_size（'1K'/'2K'/'4K' **大写 K 必须**，小写拒绝）【已核实】 | 自由 WxH、16 倍数、≤4MP | — | — |
| 品牌 hex 色 | — | — | **一等公民**：`the apple is #0047AB`（hex 须绑具体对象）+ 渐变语法 | — | — |
| 结构化 JSON prompt | — | — | 官方 schema（scene/subjects/style/color_palette/lighting/camera），与自然语言等效解释 | — | — |
| 矢量/SVG 输出 | 无 | 无 | 无 | 无 | **唯一**（$0.08/张【未核实】），logo/图标专用 |
| input_fidelity | **gpt-image-2 已移除**（默认高保真）；仅 1/1.5 有 | previous_interaction_id 多轮编辑保风格 | -i 参考图 | 多图融合 | — |
| 文字渲染 | 社区称 >99% 含 CJK【未核实】；小号非拉丁文字仍易碎（≥图高 5% 缓解）；**无透明背景**（chroma-key 后处理） | 3-pro-image 主打文字密集件；具名字体（'Brush Script'） | 引号+位置+字体气质 | 中文文字向强【未核实】 | 多级文字层级（标题>副题>注脚尺寸关系） |
| 质量/成本档 | low 起步、retries 比生成贵时才 high | flash-lite(1K 最便宜)/flash(主力 4K)/pro(文字重活) | prompt_upsampling 参数 | — | — |

**廉价侦察→昂贵定稿模式**（smixs golden-rules，直接进 skill）：变体探索用最低档（Flash 0.5K / quality:low），选中后才用 2K/4K 或 high 重生成——这是 ITERATION-LOOP 的成本控制核心。

### 2.3 可 vendor 的 prompt 类 skill 汇总

| 来源 | 判定 |
|---|---|
| smixs/visual-skills `image/` 整树 | **vendor**（MIT）：models.md + nano-banana.md + gpt-image.md + golden-rules.md + prompt-framework.md + text-rendering.md + editing/characters/multi-panel 等 + patterns/ui-social.md + poster-illustration.md（其余 5 个 pattern 可留可裁，留则依赖闭包完整）。俄语段落翻译后随附说明 |
| JunSeo99 prompting-guide.md + cli-reference.md | **vendor**（MIT，随 Codex wrapper 闭包一起） |
| coreyhaines31 image skill | **蒸馏重写**：决策树/错误表/"永不生成 UI 截图"三件，注明 adapted from（MIT）。模型名时效性强，标注"随时间失效需复查" |
| OpenAI Cookbook / Google / BFL / Recraft 官方文档 | **只引用不 vendor**（无 OSS 授权的文档页），失败模式表等改写成自己的文字+标 URL |
| black-forest-labs/skills（官方 FLUX skills 仓库） | **禁 vendor**：GitHub API license:null、树内无 LICENSE【已核实】（页面摘要称 MIT 是错的）。同内容走 docs.bfl.ml 引用 |

---

## 3. 迭代循环 skill 素材（ITERATION-LOOP）

### 3.1 官方背书的 loop 架构（收敛形状）

所有来源收敛为同一条链：**渲染（HTML→PNG）→ 截图（networkidle + 字体加载后、full_page）→ 评审（VLM 按显式 rubric，产出严重度分级发现）→ 修补（最小修改、一次一事）→ 重渲**；终止 = 评审通过 或 达轮次上限。

关键一手证据：
- Claude Code 官方 best-practices【已核实】："Give Claude something that produces a pass or fail, and the loop closes on its own"；视觉行明文写"截图结果、与原稿对比、列差异并修复"；**doer≠judge**：派 fresh-context 验证子代理"干活的不给自己打分"（与本 repo 编排层教义一致）；**Stop hook 连续 8 次 block 后强制收turn**——找到的唯一官方数字终止常数。
- Anthropic pptx skill 的 fresh-eyes 模式（渲成图→无上下文子代理视觉 QA→修→重渲，"Assume there are problems"）——**许可证禁拷文字，模式自写**。
- 学术佐证：UI2Code^N（arXiv:2511.08195，ICML 2026）证实反馈迭代优于单发；其"成对相对排序优于 VLM 绝对打分"是训练期主张——⚠️ **对抗复核发现其公开评测代码恰恰用的是绝对 0-100 打分**，此论点只能标"paper-only、代码未证实"。仓库无 LICENSE，禁拷。
- WebVR 基准【未核实，仅摘要】：rubric 引导的 VLM 评审与专家一致率 76.7-86.7%（最大增益 +22.7 绝对点）——**给 VLM 评审必须发显式书面 rubric，不能问"好不好看"**。

### 3.2 评审 rubric 素材（拼装清单）

自写 rubric 时按来源取件：
1. **triage 分级**（OneRedOak，MIT，可近逐字借）：[Blocker]/[High-Priority]/[Medium-Priority]/[Nitpick]（"Nit:" 前缀）。
2. **judge 行为规则**（OneRedOak）："Problems Over Prescriptions"——说"间距与相邻元素不一致造成视觉杂乱"，不说"把 margin 改成 16px"；每个 Blocker/High 必附截图证据。
3. **静态图适用的检查维度**：对齐/间距一致性、排版层级、色板一致、**文字-背景对比 ≥4.5:1**（WCAG，引标准本身而非转引 gstack）、无溢出/无重叠/留边距（canvas-design 借来）、**360px 缩略图可读测试**（guizang 事实借用——社媒 feed 压缩下小图先行）。
4. **AI-slop 黑名单**（gstack MIT，裁掉页面布局专属项后借用）：紫渐变、三列圆圈图标网格、全居中、统一泡泡圆角、emoji 当设计元素、卡片左色条、泛型 hero 文案。
5. **修订行为约束**：修订=精修已有、禁堆新元素（canvas-design）；外科手术式 Edit、不整文件重生成（gstack design-html）；每轮重注入保留清单（OpenAI 官方）。
6. **廉价前置检查优先于 VLM**：能写成脚本的规则（溢出检测、尺寸校验、像素 diff）先跑脚本，VLM 只管审美判断——guizang validate-social-deck.mjs 与官方 slack-gif-creator validators 的共同结构（guizang 校验器已解禁，可直接 vendor）。

### 3.3 终止条件汇总（自写 skill 的数字来源）

| 机制 | 数值 | 来源 |
|---|---|---|
| 官方 Stop hook 强制上限 | 连续 8 次 block | Claude Code docs【已核实】 |
| gstack 修复循环 | 风险公式：revert +15%/组件文件 +5%/超 10 fixes 后每个 +1%/碰无关文件 +20%；**>20% 停**；硬上限 30 fixes；同一问题 3 次失败→升级 | 本机 MIT【已核实】 |
| gstack design-html | 最多 10 轮迭代 | 同上 |
| Self-Refine 惯例 | ~4 轮 + judge 说"无需再改"停 | arXiv:2303.17651【未核实本轮】 |
| 建议自写默认 | 静态社媒图：**3-4 轮上限 + 评审 PASS 即停 + 分数回退（比基线差）即告警回滚**，Codex 生图路线因 ~1-2 分钟/张延迟更需低轮次 | 综合 |

### 3.4 HTML→PNG 渲染工具对比

| 工具 | 能力 | 确定性 | 依赖 | 判定 |
|---|---|---|---|---|
| **Playwright/Chromium 截图** | 全量现代 CSS（grid/自定义字体/webfont） | 字体渲染随 OS/headless 有漂移，**pin mcr.microsoft.com/playwright Docker 镜像**（字体内嵌）可稳【已核实 Playwright 文档】 | ~300-500MB 浏览器 | **默认渲染器**：截图与检查同一工具链闭环；须等 networkidle + fonts.ready（anthropics webapp-testing 的"CRITICAL"规则，Apache-2.0 已核实，此规则改写一行进 skill）；deviceScaleFactor≥2 出 retina |
| satori + @resvg/resvg-js | 纯 JS/wasm、无浏览器、字节级确定 | 最高 | 轻 | **fallback**：仅 flexbox（Yoga 引擎）、**无 grid/calc()/CSS 变量/z-index**、字体须显式 buffer 加载——够 og-image/简单 quote card，撑不起复杂轮播【未核实本轮，广泛已知 @vercel/og 基础】 |
| 本机 frontend-slides export-pdf.sh | 逐 .slide 元素 Playwright 截图 1920×1080 | 同 Playwright | 已装 | **现成起点**（MIT），改造为逐画布尺寸截图 |
| html2png.dev API | 全 CSS | — | 第三方付费 50 req/h | 拒绝（商业耦合 + 无有效 license） |
| wkhtmltoimage | 老 Qt WebKit | — | — | 不推荐（上游已归档，本轮未核） |
| guizang render.mjs | Playwright 封装 | — | — | **可直接 vendor**（用户拍板解禁 AGPL，见 §0.5） |

---

## 4. Codex 封装生图（research direction 2）

### 4.1 本机实测结果【本机实测，全链路一手】

- **安装修复**：`npm install -g @openai/codex` ~9s 成功，此前缺 `@openai/codex-darwin-arm64` 的 ENOENT 消失。
- **版本**：codex-cli **0.142.5**（2026-07-01 发布的最新 stable）。
- **登录态**：ChatGPT 订阅 OAuth——`codex login status` 显示 "Logged in using ChatGPT"；`~/.codex/auth.json` auth_mode="chatgpt"、OPENAI_API_KEY=null；config.toml model="gpt-5.5"。
- **内置生图**：`codex features list` 含 **`image_generation  stable  true`**（另有 imagegenext 开发中）——**一等公民稳定 feature，不是 hack**。
- **e2e**：一次成功。命令：
  ```
  codex exec --skip-git-repo-check -C <outdir> --sandbox workspace-write \
    "Generate an image of a simple flat red circle on white background and save it as codex-test.png in the current directory. Use your image generation tool, do not draw it with code."
  ```
  退出码 0、~27,188 tokens、远低于 300s；产出 PNG 1254×1254 RGB 781KB，视觉验证与 prompt 相符。机制：工具先写 `~/.codex/generated_images/<session-uuid>/ig_<hash>.png`，agent 自己 `cp` 到 cwd 并自检。
- 三个必要细节：①`--sandbox workspace-write` 必须（否则 agent 无法把文件拷进 -C 目录）；②**反回退子句**（"use your image generation tool, do not draw it with code"）必须——否则 codex 可能用 matplotlib/SVG 画一个交差；③可用 `--enable image_generation` 强制、`-i <file>` 附参考图（迭代循环直接可用：附上一版+批评意见）。

### 4.2 Web 一手来源核实【已核实，均 fetch 官方原页】

- developers.openai.com/codex/cli/features：内置生图**用 gpt-image-2**（不是 gpt-image-1）；自然语言或显式 `$imagegen` 触发；用量"计入通用 Codex 限额，**平均比普通回合快 3-5 倍消耗**"；官方逃生门："更大批量请设 OPENAI_API_KEY 走 API 计价"。
- developers.openai.com/codex/noninteractive：`codex exec` 无头契约齐全（`--json` JSONL 事件流、`-o/--output-last-message`、`--output-schema` 结构化输出、`--ephemeral`、`--skip-git-repo-check`）；**官方自己描述了 CI 里播种 `~/.codex/auth.json` 的订阅认证模式**（"当密码对待"）。⚠️ 超时行为未文档化——wrapper 必须自带 subprocess timeout。
- developers.openai.com/codex/pricing：Plus $20/月 ≈ 每 5 小时窗 15-80 条本地消息（可能叠加周上限）；Pro 5x 档 75-400、20x 档 300-1600；图像回合从**同一池子**烧 3-5 倍。
- 对抗复核第一问（"Codex CLI 有无内置生图、能否无头白嫖"）：**confirmed**。

### 4.3 可靠性与工程化注意

- 活着的 bug（openai/codex issue tracker，GitHub API【已核实】）：#26727/#26567 TooManyRequests 循环无恢复路径、#26595 无法生图、#29824 重试间输出跑题。→ wrapper 需：重试退避、产物存在性检查、自带超时。
- gpt-image-2 **不保证精确像素**（要 256² 给 1254²，e2e 亦 1254²）→ 必须后处理：macOS `sips -z <H> <W>`（注意高在前）、Linux `convert -resize WxH!`。
- **无透明背景**（gpt-image-1.5 有、2 没有）；无 seed、不可复现；复杂 prompt ~1-2 分钟（Bash timeout ≥300s）；CJK 小字更易碎（对小红书中文卡片重要——**文字重的资产仍应走 HTML/CSS DESIGN 路线，生图只管插画/底图**）。
- 输出路径/flag 语义**非公共契约**（JunSeo99 明示版本钉 0.130.0 时代基线）——升级可能悄悄破坏，故 wrapper 要带 find 兜底。

### 4.4 ToS 与耐久性（对抗复核结论 = **partial**，必须如实反映）

技术可行 ≠ 生产可依赖。降级理由（复核 agent 逐条核证）：
1. **官方引导背离**：同一套官方文档写明 "We recommend API key authentication for programmatic Codex CLI workflows"、"API keys are the right default for automation"；ChatGPT 认证的无头模式"仅当确需以你的 Codex 账号身份运行"【已核实 developers.openai.com/codex/auth 等】。
2. **ToS 灰区**：OpenAI Terms 禁止"程序化提取输出 except as permitted through the API"（该条款文本来自搜索引述，官方页 403 未逐字核验【未核实】）；openai/codex#8338 里 OpenAI 工程师确认 fork 无碍但**明确拒绝**对订阅认证自动化的合规性表态【已核实】。
3. **行业先例**：Anthropic 2026-02 禁第三方工具用订阅 OAuth、Google Gemini CLI 同月跟进、opencode ≥1.14.50 移除 ChatGPT Plus/Pro OAuth 入口【未核实细节，多源一致】——这扇门有被关的传统。
4. **封号真实存在**：community.openai.com/t/1381906 等多帖，18 个月 Pro 老用户无预警封禁（疑机房 IP 误伤），ChatGPT+Codex+API 全失、申诉无门【已核实帖子】。对零人公司=视觉管线全线停摆的单点。
5. **配额数学不支持生产**：图像回合 3-5x 消耗 × Plus 每 5h 仅 15-80 条 × 与常驻 agent 自身编码用量共享——增长 agent 做一套轮播就可能撞墙。
6. **省钱动机已过时**：任务前提"gpt-image-1/DALL-E 很贵"已陈旧——DALL-E 2/3 已于 2026-05-12 退役【未核实】，当前 gpt-image-1-mini low $0.005/张、gpt-image-2 low $0.006/张【已核实】，quote card 底图级别的用量下 API 成本可忽略。
7. 中文生态对照组：即梦逆向 free-api 自带"禁商用、随时失效"免责声明——同类"消费订阅当生产 API"模式的普遍结局。

**定位结论**：主路径 = OPENAI_API_KEY 直连 Images API（gpt-image-1-mini 或 gpt-image-2 low 起步）；副路径 = Codex wrapper（feature flag、best-effort、失败自动落回 API）。单订阅自用、非池化非转售的前提下风险属低位，但不许它当唯一依赖。

### 4.5 wrapper 伪代码（综合本机实测 + JunSeo99 兜底模式）

```python
def generate_image(prompt: str, out_path: Path, timeout=300, retries=2) -> Path:
    out_dir = out_path.parent; out_dir.mkdir(parents=True, exist_ok=True)
    full_prompt = (f"{prompt}\n\nUse your image generation tool "
                   f"(do NOT draw with code/matplotlib/SVG). "
                   f"Save the result as {out_path.name} in the current directory.")
    for attempt in range(retries):
        before = snapshot(Path.home()/'.codex/generated_images')   # 现有 session 目录集合
        r = subprocess.run(
            ["codex", "exec", "--skip-git-repo-check", "-C", str(out_dir),
             "--sandbox", "workspace-write", "--enable", "image_generation",
             full_prompt],
            capture_output=True, text=True, timeout=timeout)       # codex 无文档化超时，自己兜
        if out_path.exists() and is_png(out_path):                  # 主判：magic bytes
            return out_path
        new = new_files_since(before, glob='*/ig_*.png')            # 兜底：codex 生成了但没 cp
        if new:
            shutil.copy(max(new, key=mtime), out_path); return out_path
        if "TooManyRequests" in r.stdout + r.stderr:
            sleep(backoff(attempt)); continue                       # 活 bug #26727 的退避
    return fallback_openai_api(prompt, out_path)                    # 主生产路径兜底（API key）
# 迭代循环：追加 ["-i", str(prev_png)]，prompt 里带 VLM 批评 + 逐轮重述保留清单
# 尺寸不精确：成功后按目标尺寸 sips/convert 后处理
```

### 4.6 替代方案成本表

| 路线 | 单价（1024² 或注明） | 验证等级 | 来源 |
|---|---|---|---|
| Codex 订阅内生图 | $0 边际，但烧共享配额 3-5x/回合，Plus 每 5h 仅 15-80 条 | 【已核实】 | developers.openai.com/codex/pricing + features |
| flux-schnell (Replicate) | $0.003 | 【未核实】 | replicate.com/pricing 搜索引述 |
| **gpt-image-1-mini** low/med/high | **$0.005** / $0.011 / $0.036 | 【已核实】 | developers.openai.com/api/docs/guides/image-generation |
| **gpt-image-2** low/med/high | **$0.006** / $0.053 / $0.211（竖横版略低 $0.005/$0.041/$0.165） | 【已核实】 | 同上 |
| gpt-image-1.5 low/med/high | $0.009 / $0.034 / $0.133 | 【已核实】 | 同上 |
| Seedream 4.0（火山方舟） | ≈0.20 元/张（≈$0.028） | 半验证（社区整理的方舟费用文档） | ArcReel ark-docs；官方计费页 JS 未直取 |
| 通义万相 | ≈0.20 元/张，新户 90 天免费额度 | 【未核实】 | 阿里云帮助中心搜索引述 |
| flux-dev (Replicate/fal) | $0.025-0.030 | 【未核实】 | 搜索引述 |
| gemini-2.5-flash-image (nano banana) | ≈$0.039（1290 output tokens×$30/1M） | 【未核实】 | ai.google.dev 搜索引述 |
| Seedream V4.5 (fal) / Recraft V3 | $0.04；Recraft 矢量 $0.08（唯一 SVG 输出） | 【未核实】 | fal.ai 搜索引述 |
| Batch API | OpenAI 各档约半价 | 【已核实】 | developers.openai.com/api/docs/pricing |

---

## 5. 三个原子 skill 落地建议

统一遵循 repo 惯例（de-ai-ify 范式，全部【已核实本 repo 现状】）：`agents/assets/skills/<name>/` = 唯一原创的薄 host SKILL.md + `references/` 上游 verbatim（同步=重拷不改）+ `ATTRIBUTION.md`（表格：what/upstream/license/fetched 日期）+ vendor LICENSE 全文；wiring 只改 `agents/growth.yaml` 的 skills 列表；**必须同步更新 `agent/tests/test_resident_loadout.py` 的集合断言 + 深层文件物化断言**（6f3add3 提交就是漏更断言的翻车记录）；体量守官方约束（SKILL.md <500 行、引用一层深）。组合链落位：`draft-social → de-ai-ify → visual-asset 三原子 → use-accounts`。

⚠️ 所有 vendor 动作**必须从 raw.githubusercontent.com/git 重新逐字节拉取**，不得从本报告的转述重建（多个 lane 的 WebFetch 经过摘要模型，非字节精确）。

### 5.1 DESIGN skill（暂名 `design-asset`）

| 类别 | 内容 |
|---|---|
| **vendor**（verbatim 进 references/） | ① anthropics `frontend-design/SKILL.md` + LICENSE.txt（Apache-2.0，56 行整拷）；② jiji262 `design-styles.md` + `design-principles.md` + LICENSE（MIT，两文件自包含）；③ anthropics `theme-factory/themes/*.md` 全部 10 个 + LICENSE.txt（Apache-2.0）；④ guizang 风格系统与平台规格文件（Editorial/Swiss 布局白名单、主题 hex 白名单、溢出修复分级、小红书/微信平台事实——用户拍板解禁 AGPL，ATTRIBUTION 注明）；⑤ superdesign `theme-tool.ts` 的 design-token 全表提取为 checklist（shadcn 系 CSS 变量 + 8 级阴影，用户拍板解禁，ATTRIBUTION 注明）；⑥ 可选：`canvas-fonts/` 35 个 ttf + 逐字体 OFL.txt（自托管字体、免 Google Fonts 依赖——仅当渲染管线确需时拿，二进制体量大） |
| **借鉴**（改写不拷） | web-artifacts-builder 的反 slop 一句与两阶段形状；Leonxlnx 禁默认清单/Double-Bezel/出稿检查单；frontend-slides 固定画布不变式（clamp/overflow:hidden/密度上限表）；superdesign 深读后落点（细目见 §1.2）：反蓝色默认压制、孤立资产图底反差规则、24 字体清单、!important gotcha、两套 oklch 预设当风格样例、layout→theme→motion 定序（确认门改自检门）、动效微语法、`{name}_{n}.html` 命名；"N 变体并行→择优"只借意图——选优/比较逻辑 superdesign 自己也没做，须自建（可结合 gstack design-shotgun 的反收敛检验）；KAOPU“先 DESIGN.md 后像素”次序 |
| **自写 gap**（对应①②③纪律） | ①系统特定：web 词汇→静态画布词汇映射（hero→主视觉焦点；responsive/keyboard-focus/reduced-motion 显式声明 N/A 丢弃）、平台尺寸规格表（og 1200×630、小红书 3:4 1080×1440、公众号 2.35:1+1:1 成对、留边 6-8%——落地前对官方复核）、品牌/voice 读 `/company`（上游"问用户"流程全部改自治，与 de-ai-ify 同法）；①渲染管线：Playwright 截图脚本（networkidle+fonts.ready、deviceScaleFactor 2、pin Docker 镜像注记），改造 frontend-slides export-pdf.sh；③主题→内容类型的自治选择规则（取代 theme-factory 问答流程） |

### 5.2 IMAGE-GEN skill（暂名 `gen-image`）

| 类别 | 内容 |
|---|---|
| **vendor** | ① smixs `image/` 整树 + LICENSE（MIT）——**依赖闭包完整拿**，patterns 至少留 ui-social.md + poster-illustration.md（其余 5 个拿了不引用亦可）；俄语段落翻译并在 ATTRIBUTION 注明改动例外（或译文放 host 层、上游保持 verbatim）；② JunSeo99 `skill/` 闭包（SKILL.md + cli-reference.md + prompting-guide.md + SECURITY.md + LICENSE，MIT；assets/ 营销图与 dist/ 跳过）——作为 Codex 路线的 references |
| **借鉴** | coreyhaines31 决策树/错误表/"永不生成产品 UI 截图"（蒸馏改写）；OpenAI Cookbook 失败模式→修法表（7 行，改写+标 URL）；BFL hex 绑定/JSON prompt/无否定规则（引用 docs.bfl.ml）；Google text-first 工作流与具名参考图技巧；KingGyuSuh codex-image-in-cc 的 ARCHITECTURE.md 边界案例文档化范式（stdin 陷阱/尺寸不保证/引号传参） |
| **自写 gap** | ①调用层 wrapper（§4.5 伪代码落成脚本）：Codex 路线（feature flag）+ **API 主路径**（gpt-image-1-mini/gpt-image-2 low 起步）+ 自动 fallback + 尺寸后处理 + TooManyRequests 退避；①配额预算规则（"Plus 档每 5h 窗别循环重生成 >N 次，批量走 API"——3-5x 消耗阈值写死进 skill 是③级非平凡信号）；②压制默认：文字重资产禁走生图（交 DESIGN 的 HTML 路线）、禁空洞形容词 prompt；③模型路由表（何时 Codex/API/哪档 quality，含"廉价侦察→昂贵定稿"） |

### 5.3 ITERATION-LOOP skill（暂名 `visual-iterate`）

| 类别 | 内容 |
|---|---|
| **vendor** | **guizang 迭代闭环三件**（用户拍板解禁 AGPL）：`validate-social-deck.mjs`（9 条编号规则确定性校验器）+ 溢出修复分级表（1-40/40-90/90-160/160+px 四档）+ `render.mjs`（Playwright 渲染管线）。此外全生态无其他现成独立品 |
| **借鉴** | OneRedOak triage 矩阵 + "Problems Over Prescriptions"（MIT，近逐字）；gstack 风险公式/AI-slop 黑名单/评分公式（MIT，手工提取 ~250 行领域内容，剥 85% 平台管线，注明 adapted from Garry Tan）；gstack check.ts 单行 PASS/FAIL 输出协议；canvas-design 两条规则（不溢出清单 + 修订禁堆料）；guizang 数字阈值随校验器直接 vendor（见上行，无需再独立重推导）；pptx fresh-eyes 模式（自写实现）；webapp-testing networkidle 规则（一行改写）；Anthropic best-practices 的 pass/fail 闭环与 doer≠judge。（superdesign 深读证实对本 skill 零贡献——无任何截图/自评循环实现，勿再从它找） |
| **自写 gap**（这是三者中自写最多的，正当性=③非平凡阈值密集） | ①loop 状态机：渲染→脚本前置检查（溢出/尺寸/对比度可算项）→VLM 评审（显式 rubric+严重度分级+证据截图+禁开处方）→最小修补（重注入保留清单）→重渲；②doer≠judge：评审走 fresh-context 子代理（贴合本 repo Hub 编排教义）；③终止数字：默认 3-4 轮上限、PASS 即停、分数比基线回退即告警回滚、同一问题 2-3 次未修复升级/放弃；③降级路径：Codex 生图慢（1-2min）→ 迭代时优先改 HTML 层而非重生成底图；③360px 缩略图测试与 4.5:1 对比度作为两个必过硬门 |

### 5.4 与 design.md §5.5 的对齐与张力（需用户裁决）

- **对齐**：(a)(b)(c) ↔ IMAGE-GEN/DESIGN/ITERATION-LOOP 一一对应；"HTML/组件化比裸生图可控"论点被 html2png doctrine 与 guizang 实践双向印证；"平台尺寸/brand 读 /company"不变。
- **张力 1**：§4 表 `visual-asset` 标"**自写·复合**"——调研证实内容侧大半可 vendor，建议改口径为"混合 vendor + 自写编排与调用层"（避免重蹈 de-ai-ify 最初想自写的弯路）。
- **张力 2**：§5.5 写的是**一个** `visual-asset` skill，用户新方向是**三个原子** skill。建议落三个独立目录（原子+可组合原则、各自 <500 行更好守），growth.yaml 挂三条；若想保持 §4 表形状，也可把 `visual-asset` 行拆成三行。
- **张力 3**：§5.5 假设"生图工具已装"（provisioning 外置）。本调研把 provisioning 的具体形态调查清楚了（Codex login / OPENAI_API_KEY / Playwright+浏览器 / 可选字体包），但**装的动作归属仍未定**（见 §6）。

---

## 6. Open Questions 与风险

1. **"Datap" 到底指什么**——排查无果（datap.ai 为无关企业产品），需用户给出确切名称/URL。实际已覆盖的市场：skills.sh、smithery、ClawHub、skillsmp、aitmpl。
2. **视觉工具 provisioning 归属**：Codex CLI 安装+登录、OPENAI_API_KEY 供给、Playwright 浏览器与 Docker 镜像 pin、可选 canvas-fonts——属本任务还是 infra 兄弟任务？特别是 **`codex login` 是交互式 OAuth**（开浏览器），无头常驻 agent 的冷启动要么人工做一次、要么走官方 auth.json 播种模式——零人公司的凭证策略问题（与 memory 中"凭证策略"条目相关）。
3. **订阅配额竞争**：Codex 生图与常驻 agent 自身可能的 Codex 编码用量共享同一池（Plus 每 5h 15-80 条）——若 Codex 路线保留，需预算隔离规则。
4. **ToS 条款未逐字核验**：openai.com/policies/row-terms-of-use 与 help.openai.com 配额页均 403/JS，需浏览器补读后才可在 skill 文档里下确定性表述。
5. **中文平台规格全部来自第三方交叉**（小红书/公众号尺寸、18 张上限、安全边距）——写死进 skill 前对官方文档/实测复核一遍。
6. **smixs 俄语段落的处理方式**：译文放 host 层保持上游 verbatim，还是在 references 内翻译并在 ATTRIBUTION 声明例外？（默认建议前者，守"上游不动"惯例。）
7. **未深读的高潜候选**（后续可补）：skills.sh 上 431K 装的 vercel-labs/web-design-guidelines；中文 lane 指出的 manwithshit/xhs-images（小红书信息图，37★）、alchaincyf/huashu-design（3K★）、nexu-io/open-design（自称 35.3K★）——license 与内容均未验证。
8. **needs_browser 清单**（本轮无浏览器约定下遗留）：smithery 两个 Gemini 生图 skill 详情页、clawhub 详情页、fal.ai/ai.google.dev/火山方舟/MiniMax 官方价格页、linux.do 与知乎两帖、OpenAI ToS 页。
9. **时效风险**：图像模型与价格季度级变动（gpt-image 1→1.5→2 一年内三迭代、DALL-E 已退役）；Codex `$imagegen`/输出路径非公共契约。skill 内所有模型名与单价都应标注"截至 2026-07，用前复查"。
10. **dataviz 内置 skill 不可提取**（在 Claude Code 二进制内、无 license）——若图表类社媒资产成为需求，另寻公开授权源。

---

## 附录 A：许可证核验总表（全部一手 fetch LICENSE 原文或 GitHub API，日期 2026-07-02）

| 来源 | 许可证 | 可否 vendor |
|---|---|---|
| anthropics/skills: frontend-design / theme-factory / canvas-design / web-artifacts-builder / webapp-testing / brand-guidelines / algorithmic-art / slack-gif-creator / skill-creator | Apache-2.0（逐目录 LICENSE.txt；仓库无根 LICENSE） | ✅（须带各目录 LICENSE.txt；canvas-fonts 字体另按 SIL OFL 逐字体带 OFL.txt） |
| anthropics/skills: pptx / docx / pdf / xlsx | Anthropic 专有 source-available | ❌ 禁提取/复制/衍生/分发 |
| jiji262/claude-design-skill | MIT | ✅ |
| JunSeo99/claude-skill-codex-imagegen | MIT | ✅ |
| smixs/visual-skills | MIT | ✅ |
| KingGyuSuh/codex-image-in-cc | Apache-2.0 | ✅ |
| yazelin/codex-imagegen-skill | MIT（默认分支 master） | ✅（备选） |
| lidge-jun/ima2-gen | MIT | ✅（但为整 App，建议外部依赖而非拷源） |
| OneRedOak/claude-code-workflows | MIT | ✅（本次判定只借鉴） |
| Leonxlnx/taste-skill、coreyhaines31/marketingskills、alonw0、KAOPU、lackeyjb、jezweb、omrajguru、wuyoscar、laolaoshiren | MIT | ✅（各自判定为借鉴或后续候选） |
| gstack（本机 ~/.claude/skills/gstack/LICENSE） | MIT © 2026 Garry Tan | ✅（只提取领域内容，剥平台管线） |
| frontend-slides（本机） | MIT © 2025 Zara Zhang | ✅ |
| op7418/guizang-social-card-skill | **AGPL-3.0** | ✅ **用户拍板解禁**（2026-07-02，内部使用前提；未来对外分发/开源本 repo 需回头处理） |
| superdesign | NOASSERTION（无有效 license，版权默认保留） | ✅ **用户拍板解禁**（2026-07-02；深读已补：borrow-rewrite 为主 + theme-tool token 表可提取，ATTRIBUTION 注明版权状态） |
| black-forest-labs/skills / UI2Code_N / ky-design-to-html-skill / html2png/skills / vivy-yi/xiaohongshu-skills / wwwzhouhui/jimeng-mcp-server | NOASSERTION 或无 LICENSE 文件 | ❌ |
| OpenAI / Google / BFL / Recraft / fal 官方文档页 | 厂商文档（无 OSS 授权） | ❌ 拷贝；✅ 改写引用+标 URL |
