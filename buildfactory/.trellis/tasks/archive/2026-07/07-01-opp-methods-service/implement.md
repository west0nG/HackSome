# Implement — info-product 找机会方法

执行计划。上下文顺序：prd.md → design.md → research/{r1,r2,r3}。声明式改动，零 .py。

## 有序清单

1. **[写] 父说明** — 新建 `agents/assets/skills/find-opportunity/references/finding-info-product-opportunities.md`
   - 顶部：一句脊柱洞见（design §一）+ 一行边界注（本文覆盖 info-product 子形态；done-for-you 服务 / RaaS 是 follow-up）。
   - 正文：design §二的 7 步。平台无关步（0/1/2/3/6/7）写全；步 4-5 写**共通逻辑** + "平台细节见对应子说明"。逐步写 ① 研究-Goal `--intent` 模板（照 r1/r2/r3，措辞收干净）② 回来看什么 ③ keep/drop 规则。
   - 结尾：**平台菜单 + 路由**——列 Gumroad/亚马逊 KDP/Etsy（各一句适配）+ Substack/Udemy（标"playbook 待补"）；"选定后读 `platform-<x>.md`"。
   - 阈值用"约/数量级/例如"措辞（~40-60 条、≥5 作者、≥3 付费竞品、Tier-1 付费才算 GO 等）。
   - 结尾 provenance 脚注（Amy Hoy/Alex Hillman、Nathan Barry、Ramit Sethi、Justin Welsh、Pieter Levels、Daniel Vassallo、Indie Hackers；作思想来源署名，指向 research/）。风格对齐 `direction-critic.md`：大白话、第二人称、无 lens/透镜黑话。

2. **[写] 3 个平台子说明** — `references/platform-{gumroad,amazon-kdp,etsy}.md`（各依据 `research/{gumroad,amazon-kdp,etsy}.md`）
   - 每个：把步 4（证明付费）+ 步 5（饱和/找缝）**平台化**——该平台需求信号在哪看的研究-Goal 模板 + 可观测读数（销量/评论/BSR/"X sold"/搜索量）+ keep/drop 阈值 + 该平台适合的产品形态 + 平台脾气/工具/价格锚。
   - 同样大白话、第二人称、无黑话、带该平台 provenance；数字"约/数量级"。

3. **[改] SKILL.md 接线** — `agents/assets/skills/find-opportunity/SKILL.md`
   - line 46-48 占位注释：改为"info-product 业态已有具体方法 → 见 references/finding-info-product-opportunities.md；其余业态仍在做"。
   - "Get real signal…"节 / 业态表附近加一句路由：选了 service / info-product 业态就读父说明走具体方法；通用信号法作其它业态回退保留。
   - 不动骨架结构（业态自觉、只生成不判、2-3 候选、查 /company 都保留）。

4. **[核] 静态质量检查**（对应 AC1-AC7, AC9）
   - 父说明 7 步齐全；每取信号步有三件套（AC1/AC2）。
   - 付费主闸 + 三档规则在（AC3）；饱和/诚实闸三条在（AC4）；候选定义门 + 接缝在（AC5）。
   - SKILL.md 路由 + 占位更新 + 平台菜单在（AC6）。
   - 3 个平台子说明存在、步 4-5 平台化、三件套齐、父说明能路由到（AC9）。
   - `grep -ri "lens\|透镜" agents/assets/skills/find-opportunity/` 为空；`git diff --stat` 只含 .md（AC7）。

5. **[核] 交叉一致性** — 与骨架接缝、与 decide-direction 反空想标准不冲突（design §五）。可派 `trellis-check`。

6. **[e2e·推荐] 空公司真跑**（AC8）— 视执行层就绪度：`PUMP_COMPANY` 空公司 cold-start，看 CEO 选 info-product 后是否读到父说明+平台子说明、发出带 marketplace 付费证据问法的研究-Goal。若不跑，wrap-up 明确标注未验证。

## 验证命令

```bash
# 结构
ls agents/assets/skills/find-opportunity/references/finding-info-product-opportunities.md
# 无黑话
grep -rni "lens\|透镜" agents/assets/skills/find-opportunity/ || echo "clean"
# 只改 md
git status --short && git diff --stat
# 命令真实性（模板里的 send 用法与代码一致）
grep -n "def .*send\|--intent\|--accept" orchestration/messaging.py | head
```

## 回滚点

- 纯新增（父 + 3 子 reference 文件）+ 一处 SKILL.md 小改；回滚 = 删 references 下新增文件 + `git checkout agents/assets/skills/find-opportunity/SKILL.md`。无代码/无迁移风险。

## Review gates

- 写完父说明 + 3 子说明 + SKILL.md 后、commit 前跑步骤 4-5；AC1-AC7+AC9 全绿再报完成。AC8 按上述处理。
