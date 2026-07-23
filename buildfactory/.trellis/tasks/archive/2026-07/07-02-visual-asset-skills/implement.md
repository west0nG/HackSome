# 实施清单（一个一个做；每 Phase 一 commit = 回滚点）

> 顺序依据：design-asset 无外部 API 依赖先跑通渲染管线；gen-image 次之；visual-iterate 编排前两者最后。
> 所有 vendor 从 raw.githubusercontent.com/git 逐字节拉取（禁从调研报告转述重建）；每个文件进 ATTRIBUTION.md 登记（what/upstream/license/日期/拍板标注）。

## Phase A：design-asset

- [x] A1 拉 vendor（先在任务内记 raw URL 清单再拉）：anthropics `frontend-design/SKILL.md`+LICENSE.txt；jiji262 `design-styles.md`+`design-principles.md`+LICENSE；`theme-factory/themes/*.md`（10 个）+LICENSE.txt；guizang 风格系统+平台规格文件+LICENSE（粒度见 design §5 Q2）；superdesign `theme-tool.ts` → 提取 `token-checklist.md`（注明提取自何文件何行）
- [x] A2 `scripts/render_asset.mjs`：改造本机 frontend-slides `export-pdf.sh`（逐画布尺寸、networkidle+fonts.ready、scale 2）；本机跑通一张样图
- [x] A3 host SKILL.md：格式路由（quote card/轮播/og/小红书）、平台尺寸表（**AC6：先对官方/实测复核**）、主题自治选择（剥上游"问用户"门）、组合指引、voice 读 `/company`；+ ATTRIBUTION.md
- [x] A4 `growth.yaml` 追加 + `test_resident_loadout` 断言 + `pytest agent/tests/ -q` 绿
- [x] A5 盲评：无上下文 sub-agent 只凭 skill 产一张 quote card → 修 host 直到可用
- [x] **commit（回滚点 A）** `7da42fd`

## Phase B：gen-image

- [x] B1 拉 smixs `image/` 整树+LICENSE（依赖闭包完整）；JunSeo99 `skill/` 闭包+LICENSE
- [x] B2 `scripts/generate_image.py`：API 主路径实测出图；Codex 副路径 e2e（flag on，含反回退子句/文件兜底/429 退避）；副→主回落实测；`sips`/`convert` 尺寸后处理
- [x] B3 host SKILL.md：模型路由表、廉价侦察→昂贵定稿、②禁文字重生图/禁空洞形容词 prompt、组合指引；俄语段译文附录；+ ATTRIBUTION.md
- [x] B4 yaml + 断言 + pytest 绿
- [x] **commit（回滚点 B）**

## Phase C：visual-iterate

- [x] C1 拉 guizang `validate-social-deck.mjs` + 溢出修复分级表 + `render.mjs` + LICENSE
- [x] C2 host SKILL.md：loop 状态机（渲染→脚本前置检查→VLM 评审→最小修补→重渲）、rubric（OneRedOak triage 分级 + "问题不开处方" + gstack 阈值改写 + 360px 缩略图/4.5:1 对比度两硬门）、终止数字（3-4 轮/PASS 停/回退告警/同题 2-3 次失败升级）、每轮重注入保留清单、评审落法（design §5 Q1 探明后定）；+ ATTRIBUTION.md
- [x] C3 **e2e 全链（AC5/R6）**：quote card 初版→前置检查→评审→修补→PASS；记录轮数与产物
- [x] C4 yaml + 断言 + pytest 绿；三 skill 联合盲评
- [x] **commit（回滚点 C）**

## 收尾

- [x] D1 父任务 design §4 表三行状态更新（v1 → done）；AC 逐条核；journal 记录
- [x] D2 无新 .py 契约（零逻辑改动）；skill 惯例已沉淀在各 ATTRIBUTION + 任务工件，暂不动 .trellis/spec — spec 沉淀：若渲染管线/物化 scripts 形成新契约 → trellis-update-spec

**验证命令**：`pytest agent/tests/ -q`；`node agents/assets/skills/design-asset/scripts/render_asset.mjs <sample.html> <out.png>`；`python3 agents/assets/skills/gen-image/scripts/generate_image.py --prompt "..." --out /tmp/t.png`
**回滚**：vendor 全 verbatim + host 独立文件 → 删对应 skill 目录 + revert yaml/断言即回滚，无扩散面。
