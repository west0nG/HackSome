# CEO find-opportunity — 设计（骨架版·大白话·具体方法留空）

> 依据 `prd.md` + 父 `../07-01-ceo-monetization` + 判断侧 `../06-28-role-ceo`。
> 系统事实已核：`ceo.yaml` 现挂 `send-goal`+`decide-direction`；`agent/loadout.py::materialize` 用 `shutil.copytree` 拷整目录；测试 `test_ceo_gets_dispatch_and_direction_skills` 断言 skills 集合 + 物化。执行层：部门占位、外设层仅入站。

## 0. 收敛后的核心

find-opportunity = **CEO 判断链前端「生成候选」的骨架**：业态自觉 + 找机会的通用纪律 + 每业态具体方法留占位。

- **业态自觉（Level-1）**：不只能做产品；挑一个业态，初期随便挑。
- **通用找机会法（本任务写实处）**：别凭空编 → 先派研究 Goal 给 `researcher` 取真实信号 → 产 2-3 候选 → 逐个交 `decide-direction`。这套**跨业态通用**，骨架靠它就能跑。
- **具体方法留空**：每业态「怎么找机会」的具体打法这轮不写（单独研究任务）。
- **大白话**：撤掉"透镜/方式轮/lens"，用「找机会的方法/角度」。

## 1. headless 约束（保留的系统事实）

CEO 跑 `claude -p`，无交互端、不能 spawn worker，但**能发 Goal**（`python3 -m orchestration.messaging send --to researcher --intent "<问题>"`）——通用信号法复用这条现成通道，不引入新机制。`permission_mode: bypass`、无 allowed-tools 限制，CEO 具备 Bash。

## 2. 落点（单文件，最轻）

| # | 落点 | 内容 |
|---|---|---|
| 2.1 | `agents/assets/skills/find-opportunity/SKILL.md`（新增，**仅 1 文件**） | 别凭空编 → 业态自觉(选业态) → 通用信号法(派研究 Goal) → 每业态占位一句 → 产 2-3 候选 → 交 decide-direction → 两护栏 → 署名 |
| 2.2 | `agents/ceo.yaml` skills +1 行 | 挂 `assets/skills/find-opportunity` |
| 2.3 | `agents/assets/ceo-charter.md` 增一句 | idle 无候选→先挑业态再 find-opportunity 再判断 |
| 2.4 | `agent/tests/test_resident_loadout.py` 改断言 | skills 含 `find-opportunity` + SKILL.md 物化 |

**为何单文件、无 references/**：具体方法留空，没有要拆出去的大块内容；通用纪律是给 CEO 自己读的、不长。将来某业态的具体方法写出来了，再由那个研究任务决定是否拆 `references/`。这轮**不建空占位文件**（避免 agent 运行时读到一堆 TODO 文件）。

## 3. skill `find-opportunity` — SKILL.md

**description（对齐 heartbeat wake·渐进披露触发）**：
> How the CEO comes up with candidate directions when it has none — across business forms, not just products. Use on an idle/heartbeat wake, or whenever you must decide what to pursue but have no concrete candidate yet — to pick a business form (a service, a content play, a product, ...), get real signal before imagining anything, produce a few grounded options, and hand them to decide-direction to judge.

**body（祈使/具体/大白话，~50-65 行）**：
1. **别凭空编（开篇）**：你被要「想个方向」时的默认是吐一个听着合理的通用点子——这类无真信号的候选交 decide-direction 只会被独立审毙掉。别自由联想。
2. **你不只能做产品（选业态·Level-1）**：你可以做不同的变现业态——一个**服务/信息产品**、一个**内容/自媒体**、一个**软件产品**（以后还有电商等）。挑一个探索本次 wake，**初期随便挑、别纠结**；每业态一句「追它=做什么」（见 §4）。
3. **先拿到真实信号再想（通用找机会法·写实）**：选好业态后，**别凭想象造机会**——先派一个小研究 Goal 让 `researcher` 去看这个方向里真实的需求/抱怨/缺口：`python3 -m orchestration.messaging send --to researcher --intent "<一个具体、可回答的问题>"`，拿回信号再据此生成。
   - **占位一句**：*每个业态其实有更对路的找机会方法，正在专门研究补上；在补齐前，对任何业态都先用上面这套「先取真实信号」的通用做法。*（不写假方法。）
4. **产 2-3 个明显不同的候选**：别停在第一个；至少一个刻意不一样。每个自包含写清：给谁、做什么、为什么现在、什么信号说明有戏。
5. **逐个交 decide-direction，别自己判**：find-opportunity 只生成——不召 critic、不下 GO/DROP（那是 decide-direction 的活）。
6. **两护栏**：生成前查 `/company` 记忆避开已试/已否方向（别重复提）；标定「部门几天能交付的最小真实价值」，不是宏大愿景；候选要匹配公司真能造/交付的东西。
7. **署名注释**（HTML 注释）：通用纪律借自 PG *How to Get Startup Ideas* + gstack office-hours/ETHOS（MIT, Garry Tan/YC）；接 decide-direction。

## 4. 业态清单（SKILL.md 步 2 内联，简表）

| 业态 | 追它 = 做什么 |
|---|---|
| 服务/信息产品 | 产出并交付文本/内容/分析（报告、newsletter、代写、课程） |
| 内容/自媒体 | 持续产内容 + 发布 + 涨粉 |
| 产品/软件 | 造并上线软件 |
| （跨境电商） | 选品/铺货/投流 —— 以后再说 |

一句纪律：**不只能做产品；初期随便挑一个；候选匹配部门真能造/交付的东西**。（不写 token-ROI——agent 算不了，那是父任务 operator 的排序标尺。）

## 5. charter 增量（2.3）

`## How you decide what to pursue` 段末增一句：
> 若 heartbeat 空闲、手上没有具体候选，先用 `find-opportunity` skill：**先挑一个变现业态**（服务/内容/产品…——你不只能做产品；初期随便挑别纠结），**先派个研究 Goal 拿到真实信号**，再生成几个接地的候选——**不要空手拍一个产品方向直接发**。生成后逐个走上面的判断流。

## 6. 边界 / 测试 / 兼容

- **零 .py 逻辑改动**：新增 1 skill 文件 + `ceo.yaml` +1 行 + charter +1 句 + 改 1 条测试断言。`copytree` 已物化。
- **测试**：`test_ceo_gets_dispatch_and_direction_skills`（改名 `..._and_opportunity_skills`）断言 `set(info.skills) == {"send-goal","decide-direction","find-opportunity"}` + `os.path.exists(skills/"find-opportunity"/"SKILL.md")`。LLM 生成行为靠 e2e 验证。
- **与 decide-direction 无重叠**：find-opportunity 产候选（发散），decide-direction 判候选（收敛+critic）；body 显式「不自判」。
- **回滚**：删 `find-opportunity/` 目录 + 还原 `ceo.yaml`/charter/测试。

## 7. 待确认（review gate）

1. **骨架单文件 SKILL.md**：业态自觉 + 通用信号法 + 每业态占位一句；**不建空 references 文件** —— design 取此。
2. **具体方法留空**、后续专门研究任务写（父 PRD 任务地图）—— 确认。
3. **命名 `find-opportunity`**（替代 find-idea），大白话、无"透镜"—— 确认。
4. **押后**：各业态具体方法/执行能力(sibling)/电商/轮转/度量/防御清单 —— 确认。
