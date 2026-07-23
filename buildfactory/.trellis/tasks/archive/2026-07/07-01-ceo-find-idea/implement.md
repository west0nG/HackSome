# CEO find-opportunity — 执行计划（骨架版）

> 依据 `design.md`。声明式，零 .py 逻辑改动。SOP-adding-roles-and-skills 第 5→8 阶段（落点→单测→**真跑 e2e**→迭代）。

## 前置（已完成）

- [x] 系统事实：`ceo.yaml` skills、`copytree` 拷、测试断言、执行层现状
- [x] 任务树重构：父 `07-01-ceo-monetization` ← 子 `find-opportunity`；父 PRD（含后续「找机会方法」研究任务地图）
- [x] 子 prd.md / design.md（骨架版·大白话·具体方法留空）
- [x] 种子研究 `research/idea-generation-methods.md`（PG/gstack/1000TF/Sales Safari）——降级为后续方法任务的种子，不作本 skill 正文依据

## 执行清单（有序）

### S1 — SKILL.md（骨架·单文件）
- [ ] 建 `agents/assets/skills/find-opportunity/SKILL.md`（frontmatter `name: find-opportunity` + design §3 description；body §3 七步 + §4 业态简表 + 署名注释）。
- [ ] 自检：**无"透镜/方式轮/lens"黑话**；每业态具体方法处是**明确占位**（design §3 步3 那句），不是编的假方法。
- [ ] 自检：业态清单 ≥3、明确「不只能做产品·初期随便挑」、无 token-ROI 选择准则；通用信号法命令与 charter 一致；「只生成不判断」写清。

### S2 — 挂载 + charter
- [ ] `agents/ceo.yaml` skills 增 `- assets/skills/find-opportunity`（注释：业态自觉发散生成候选，喂 decide-direction）。
- [ ] `agents/assets/ceo-charter.md` `## How you decide what to pursue` 段末加 design §5 那句。

### S3 — 测试断言
- [ ] 改 `test_resident_loadout.py::test_ceo_gets_dispatch_and_direction_skills`（→ `..._and_opportunity_skills`）：
  - `assert set(info.skills) == {"send-goal", "decide-direction", "find-opportunity"}`
  - `assert os.path.exists(skills / "find-opportunity" / "SKILL.md")`

### S4 — 单测验证
- [ ] `python3 -m pytest agent/tests/test_resident_loadout.py -q` 绿。
- [ ] `python3 -m pytest agent/tests/ -q` 全绿（无回归）。

### S5 — trellis-check
- [ ] 派 `trellis-check`：核 AC1-AC6、大白话无黑话、占位不是假方法、与 decide-direction 无矛盾。

### S6 — ⚠️ 真跑 e2e（SOP 第 7 阶段·不可跳）
- [ ] `make up` 触发一次 CEO heartbeat wake。
- [ ] 观测日志（`make logs`）：CEO 走 find-opportunity——挑一个业态（不纠结）→ `messaging send --to researcher` 派研究 Goal 取信号 → 产 2-3 候选 → 逐个进 decide-direction。
- [ ] 记录：是否吐通用 sitcom idea（陷阱压住没）、是否只会想产品（业态自觉生效没）、信号路径真跑通没。异常写 research/ 或 debug retrospective。

### S7 — 迭代
- [ ] 据 e2e 观测调措辞（骨架第一版立可迭代）。

## 验证命令速查
```bash
python3 -m pytest agent/tests/test_resident_loadout.py -q     # S4 物化断言
python3 -m pytest agent/tests/ -q                             # S4 全量无回归
grep -n find-opportunity agents/ceo.yaml                      # S2 挂载
grep -niE '透镜|方式轮|lens' agents/assets/skills/find-opportunity/SKILL.md  # S1 应无输出(无黑话)
make up && make logs                                          # S6 e2e wake 观测
```

## Review Gate（进 S1 前确认 design §7 四问）
1. 骨架单文件 SKILL.md（业态自觉 + 通用信号法 + 每业态占位一句，不建空 references）。
2. 具体方法留空，后续专门研究任务写。
3. 命名 `find-opportunity`，大白话。
4. 押后项（各业态方法/执行能力/电商/轮转/度量/防御清单）。

## 回滚点
- S1-S3 任一步坏：删 `agents/assets/skills/find-opportunity/` + `git checkout agents/ceo.yaml agents/assets/ceo-charter.md agent/tests/test_resident_loadout.py`。
- S6 e2e 暴露问题：回 S1 调措辞（不回滚结构）。

## 完成标准（对齐 prd AC）
- AC1-AC6：S4 单测绿 + S5 check 过。
- AC7：S6 e2e 观测到 find-opportunity 骨架真实生效（挑业态→取信号→产候选→交判断）。
