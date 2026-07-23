# Visual-asset 三原子 skill（design-asset/gen-image/visual-iterate）

> 父任务：`../06-28-role-growth`（growth「做优质内容」侧）。07-02 用户定：从父任务单拆。
> ⚠️ 边界：声明式——**零 .py 逻辑改动**，只加 skill 目录 + `growth.yaml` 条目 + 物化测试断言。
> 调研依据：`research/visual-asset-skills-research.md`（9 路调研 + 对抗复核 + 许可证一手核验 + Codex 本机 e2e）。核心结论已经用户确认：①一拆三原子；②生图 API 主路径 / Codex 副路径；③guizang(AGPL)/superdesign(无 license) 拍板解禁（内部使用，ATTRIBUTION 注明）。

## Goal

给 growth 产社媒视觉资产（quote card / 轮播 / og-image / 小红书图文）的完整能力，落成三个原子可组合 skill：

- `design-asset`：HTML/CSS 组件化设计静态资产，Playwright 截图出 PNG——文字/排版类资产的主路线。
- `gen-image`：生图 prompt + 工具调用，只管插画/底图。
- `visual-iterate`：渲染 → 确定性脚本前置检查 → VLM 评审 → 最小修补 的自检循环。

**混合 vendor + 自写编排/调用层**（非"自写·复合"）；第一版立可迭代骨架。

## Requirements

- **R1 design-asset**：vendor（anthropics `frontend-design` / jiji262 两文件 / `theme-factory` 10 色板 / guizang 风格系统+平台规格 / superdesign token 表提取）+ 自写 gap（渲染管线脚本、平台尺寸表、主题自治选择、voice/brand 读 `/company`）。
- **R2 gen-image**：vendor（smixs `image/` 整树、JunSeo99 Codex 调用闭包）+ 自写 wrapper——**主路径 = OPENAI_API_KEY 直连**（gpt-image-1-mini low 起步）、**副路径 = codex exec**（feature flag，失败自动回落 API）+ 模型路由表；**文字重资产禁走生图**（归 design-asset）。
- **R3 visual-iterate**：vendor（guizang `validate-social-deck.mjs` + 溢出修复分级表 + `render.mjs`）+ 自写 loop 编排、评审 rubric（OneRedOak/gstack 借鉴改写）、终止数字（3-4 轮上限 / PASS 即停 / 回退告警）；评审 = fresh-context 子代理（doer≠judge）。
- **R4 vendor 纪律**：依赖闭包完整；上游 verbatim 进 `references/` + `ATTRIBUTION.md`（来源/许可证/拍板例外/拉取日期）；**一律从 raw/git 逐字节重新拉取，禁止从调研报告的转述重建**（报告经摘要模型非字节精确）。
- **R5 声明式**：`growth.yaml` skills 追加 3 条目；`test_resident_loadout` 断言更新（含 `references/` 深层文件物化断言——吃 6f3add3 漏更教训）；零 .py。
- **R6 真跑验证**：三 skill 链真产一张合格图（e2e）；visual-iterate 至少走一轮「评审→修补→PASS」。

## Acceptance Criteria

- [ ] **AC1**：`growth.yaml` 在现有条目上追加 `design-asset`/`gen-image`/`visual-iterate`；`test_resident_loadout` 断言含三 skill 且 `references/` 深层文件物化存在；`pytest` 绿。
- [ ] **AC2（纪律）**：三个 host SKILL.md 每条内容可指认 ①系统特定/②压制默认/③非平凡信号；无泛泛常识、无防御堆砌、无"喂 proof"步骤。
- [ ] **AC3（vendor/许可证）**：ATTRIBUTION 齐全；guizang/superdesign 标注「原许可证 + 用户拍板 2026-07-02 + 内部使用」；Anthropic 专有四件套（pptx 等）零拷贝。
- [ ] **AC4（wrapper 实测）**：API 主路径真出图；Codex 副路径 e2e 通过（或 flag-off 且记录原因）；副→主回落逻辑有实测。
- [ ] **AC5（迭代闭环真跑）**：一个真实资产走 渲染→前置检查→VLM 评审→修补→PASS 至少一轮；确定性校验器先于 VLM 跑。
- [ ] **AC6（尺寸复核）**：小红书/公众号尺寸写入 skill 前对官方/实测复核（调研值来自第三方交叉，见报告 §1.4）。

## Out of Scope

- **provisioning**：OPENAI_API_KEY 供给、Playwright 浏览器安装、`codex login` 无头冷启动——归属待定（可能 infra 兄弟任务）；本任务假设已装，缺则记 blocker 不自装。
- 品牌 brand skill（借 brand-guidelines 结构，另开）；发布/账号（`use-accounts`，父任务）；动图/视频资产。
- prompt 最优化、闭环 measure-iterate（父任务口径：v1 开环）。

## 依据

- `research/visual-asset-skills-research.md`（本任务内，含许可证核验总表·附录 A）。
- 父 `design.md` §5.5（三原子表 + 组合关系）+ §8（vendor 策略）+ 父 `prd.md` R2/R4。
- memory：`sop-adding-roles-and-skills`（⚠️真跑 e2e）、`skill-design-no-generic-for-llm`（①②③）、`license-stance-user-override`（拍板例外）。
