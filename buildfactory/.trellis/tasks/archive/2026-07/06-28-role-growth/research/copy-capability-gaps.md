# Research/Brainstorm: 写出好的合适的 growth 文案，AI 缺什么（07-02 收敛）

- **Query**: 用户叫停"直接 vendor 方法类 skill"后的根本性追问：AI 需要什么 / 先配什么 / 去哪找。本文是 brainstorm 收敛记录，是本批 prd/design 修订的依据。
- **方法**: 从"Claude 已经会什么"倒推缺口，而不是从"开源有什么可搬"正推。

## 缺口拆解（按优先级）

Claude 自带：hook 公式、AIDA/PAS、平台大致规范、通用营销常识 → 方法论文件边际价值低。真缺的：

| # | 缺口 | 人话 | 解法 | 状态 |
|---|---|---|---|---|
| 1 | **公司是谁 / voice 冷启动** | "我们用什么腔调说话"没人定 | **用户拍板（07-02）：growth 的职责**。growth 自己定 voice、自己研究写进 `/company` 的哪个位置（呼应记忆层"主题由 agent 自划"）。落点：charter 职责一句 + VOC skill host 一段，不硬编码路径 | 本批做 |
| 2 | **客户原话（VOC）** | 好文案 = 把客户骂问题的原话捡回来说给他听；原话在 Reddit/G2/HN/评论区，不在模型参数里，得现采 | vendor coreyhaines `customer-research`（细看确认质量高、near drop-in，纠正了"开源没有 VOC skill"的错误判断）+ listening.md curl 配方作程序化采集管子；交付物改为写进 `/company` 的客户语言库 | 本批核心 |
| 3 | **时效性平台机制** | 算法偏好/硬限制会过期，静态 vendor 的表同样会过期 | 需要的是"用前刷新"意识而非一次性 vendor；v1 只留薄硬数据，刷新机制押后 | 押后 |
| 4 | **好坏判断标准** | 没有反馈闭环就没有"好"，只有"合适 + 不 AI 味 + 不违反平台机制" | 随闭环 measure-iterate 押后；不写泛泛自评 rubric（会掉进"没写"陷阱） | 押后 |
| - | AI 味 | | de-ai-ify | ✅ done |

## 排序原则：合适 > 好

冷启动语境下 1、2 是地基；没有公司上下文和客户语言，方法技巧产出的是"漂亮的通用废话"。

## 方法类 catalog（blacktwist 5 writer / repurposer / short-form-video 等）→ 降级

- 定位：不是 v1 的核心缺口；按需再加（observation-gated，呼应"防御没观测失败押后"）。
- 07-02 上午已拷进分支的 4 个目录（draft-social / repurpose-content / short-form-video / social-listening）：**除 listening 两份 reference 改编入 VOC skill 外，其余待用户批准后删除**。再引入零成本：来源/版本/取舍已记录于 `social-vendor-compare.md`。

## `customer-research` 细看结论（vendor 依据）

- 结构：SKILL.md（11.9KB）+ `references/source-guides.md`（16.2KB）。MIT，同仓库第三次 vendor。
- 两种模式：榨现有材料（客服记录/访谈/差评的抽取框架：JTBD/痛点/**language used**）+ 出门采（digital watering hole）。
- ③级具体信号密度高：Reddit 搜索算子（`site:reddit.com "[竞品]" "vs" OR "switched"`）、按行业的 subreddit 清单、高信号帖型清单、G2 "先读 3 星评论（最诚实）/1 星看失败模式/5 星偷爱语当 proof point"、pullpush.io 挖旧帖、汇总模板按"频率 × 强度"排序且带原话引用（= swipe file 形状）。
- persona 生成部分对我们价值一般，但 vendor intact 不裁（de-ai-ify 教训）。

## 验证方式（场景倒推）

不从能力清单正推，用一个具体场景走通：`公司定了方向 X → goal：发第一条 launch 帖`。growth 应当：发现没 voice → 采客户原话入 `/company` → 自定 voice 入 `/company` → 从语言库取材写文案 → de-ai-ify → 交付。盲评 sub-agent 按此场景实测。
