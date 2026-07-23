# Implement — Skill 来源说明与执行上下文分离

> 前置：design.md 已获用户审阅通过，`task.py start` 已执行。
> 逐项迁移的权威映射 = `research/audit-*.md` 的 item ID；本清单只排顺序和验证点。
> 每步一个 commit，message 引用 item ID（AC8 的 diff 审阅依据）。

## Step 0 — 扫描器先行（红灯态）

- [ ] 新建 `agent/tests/test_skill_provenance.py`：扫描器函数 + `VENDORED_EXEMPT_SUBTREES`（11 棵，含理由）+ `FUNCTIONAL_ALLOWLIST`（初始为空或极少）+ fixture 自测（合成树注入违规 → 报出；干净树 → 零报告）。
- [ ] 对真实资产的断言先标 `xfail(strict=False)` 或单独跳过开关——此时它应该恰好报出审计清单上的全部 host 层 C1 项。
- [ ] 验证：`pytest agent/tests/test_skill_provenance.py -v`，报出项与 `research/audit-summary.md` 的 ~30 项清单一致（多报/漏报都要回到审计核对）。
- 回滚点：本 commit 独立 revert。

## Step 1 — in-house 三件套（新建 ATTRIBUTION.md）

- [ ] find-opportunity：删 FO-1、IP-1、KDP-1、ETSY-1、GUM-1 五条 HTML 注释；新建 `ATTRIBUTION.md`（来源清单 + research 路径用 audit-inhouse 已解析的 archive 路径 + 07-01 已删任务指针修正）；IP-2 不动。
- [ ] decide-direction：删 DD-1、DC-1；新建 `ATTRIBUTION.md`。
- [ ] create-role：删 CR-1；CR-2 按 R4 重写（留 capability-first 规则、迁 07-06 指针）；新建 `ATTRIBUTION.md`（含 Apache-2.0 标注）。
- [ ] 验证：三份 SKILL.md/references diff 中每个删除块 ↔ ATTRIBUTION.md 新增块一一对应；`grep -rn '<!--' agents/assets/skills/{find-opportunity,decide-direction,create-role}` 为空。
- Commit：`refactor(skills): migrate in-house provenance to ATTRIBUTION.md (FO-1,IP-1,KDP-1,ETSY-1,GUM-1,DD-1,DC-1,CR-1,CR-2)`

## Step 2 — mine-customer-voice + visual-iterate

- [ ] MCV-1 删括注；MCV-6 删 `## Sources` 整段；MCV-2/3/4/5 中性化改写（保留映射规则原义，去 vendored/upstream 措辞）。
- [ ] VI-1 删词、VI-2 删括注、VI-3 删整段（先核对 ATTRIBUTION.md:12-27 确为超集，AGPL 例外句原样在位）。
- [ ] 验证：两份 SKILL.md 无 "ATTRIBUTION"/"vendored"/"upstream" 残留；C3 红线（C3-a…C3-f）逐条原样在位。
- Commit：`refactor(skills): strip host provenance from mine-customer-voice/visual-iterate (MCV-1..6, VI-1..3)`

## Step 3 — de-ai-ify + gen-image

- [ ] de-ai-ify：删 H1 `## Sources` 段（先核对 ATTRIBUTION.md 覆盖）；H2 改写；`zh/references/sources.md` 与全部 vendored 文件零接触。
- [ ] gen-image：SKILL.md L8/26/34 三处措辞改写，路由行为逐句保留。
- [ ] 验证：`pytest agent/tests/test_de_ai_ify_integrity.py`（链接闭包不悬空）；两份 SKILL.md 无关键词残留。
- Commit：`refactor(skills): strip host provenance from de-ai-ify/gen-image (H1,H2, gen-image L8/26/34)`

## Step 4 — design-asset（最重一组）

- [ ] ATTRIBUTION.md 先行增补：吸收 token-checklist license blockquote + 提取细节、render_asset.mjs 头注细节（X6 缺口）；superdesign 许可证更新为 AGPLv3 dual（保留 2026-07-02 批准史）。
- [ ] token-checklist.md 重做：去 B1-B6 出处件，checklist 正文（C3）逐条保留。
- [ ] SKILL.md：5 项 C1 部分改写；3 项 C3（inert-citation 块、escape hatch、recheck caveat）不动。
- [ ] 验证：diff 映射审阅；guizang/jiji262/theme-factory/anthropic 子树零字节变化（`git diff --stat` 确认只动了 SKILL.md/token-checklist/ATTRIBUTION.md）。
- Commit：`refactor(skills): design-asset provenance to ATTRIBUTION.md (A1..A8 C1-part, B1..B6, X6, superdesign AGPLv3 record)`

## Step 5 — ATTRIBUTION 记录修正收尾

- [ ] visual-iterate / de-ai-ify ATTRIBUTION.md 补本次验证的上游 commit SHA。
- [ ] gen-image ATTRIBUTION.md 失效指针改为 archive 绝对路径。
- Commit：`docs(skills): pin upstream SHAs + fix stale pointers in ATTRIBUTION records`

## Step 6 — 扫描器转正（绿灯态）

- [ ] 摘掉 Step 0 的 xfail/跳过开关；按残余命中补齐 `FUNCTIONAL_ALLOWLIST`（每条必须带理由，预期个位数：design-asset escape hatch 文件名提及等）。
- [ ] resident loadout 断言补新 3 份 ATTRIBUTION.md 存在性（`agent/tests/test_resident_loadout.py` 现有 100/127/149 三处的同款）。
- [ ] 验证（全量）：
  - `pytest agent/tests/ -x -q`
  - `pytest orchestration/tests/ -x -q`
  - `grep -rn '<!--' agents/assets/skills --include='*.md'` 命中全部落在登记豁免子树内
- Commit：`test(skills): enforce provenance scanner + registry (R6/AC6)`

## Step 7 — 收尾核对（对照 AC）

- [ ] AC1 清单：research/ 五份审计 + summary 在位（已完成于规划期）。
- [ ] AC2：四个点名文件正文无来源注释（Step 1 覆盖）。
- [ ] AC3：抽查 5 项迁移内容能在 ATTRIBUTION.md 找到原文或等价表述。
- [ ] AC4：`git diff` 确认 vendored 子树零改动 → byte-exact 声明完好。
- [ ] AC5：C3 红线清单逐条复核在位。
- [ ] AC6：临时注入一条注释跑扫描器 → 失败 → 撤销（fixture 自测已固化同逻辑）。
- [ ] AC7/AC8：全量测试绿 + commit ↔ item ID 映射完整。
- 之后进入 Phase 3（spec 更新 + journal + 归档）。

## 全局回滚

每步独立 commit，逆序 revert 即可；Step 6 转正后若需 revert 内容步骤，先 revert Step 6 或在登记表临时加豁免。运行时代码零改动，无部署面。
