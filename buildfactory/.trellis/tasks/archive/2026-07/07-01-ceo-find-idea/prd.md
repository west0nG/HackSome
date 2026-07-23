# CEO find-opportunity（业态自觉·找机会骨架）

> 父任务：`../07-01-ceo-monetization`（多业态变现愿景）。本任务=父任务的**① CEO 生成层骨架**。
> ⚠️ 边界：**声明式，零 .py 逻辑改动**——只新增 1 个 skill 文件、改 `ceo.yaml` 一行、charter 加一小段、更新物化测试断言。判断/审查归已交付的 `decide-direction`+`direction-critic`，本任务不碰其逻辑，只在下游接上。
> ⚠️ **范围（用户拍板）**：本任务**只锁骨架**——业态自觉 + 找机会的通用纪律 + 每个业态留占位。**「怎么在某个业态里找机会」的具体方法这一轮不写**，留空，单独开研究任务做（那是最该认真研究、不能糊的部分）。

## 现状（已存在，不重做）

- CEO 判断链**残缺前端**：`decide-direction`+`direction-critic` 已存在，但假设「候选方向已存在」；**「候选从哪来」是空的**。
- 且现有判断链**默认候选是软件产品**（最窄切入、几天能发、"部门能 ship" 都隐含产品）。而 agent 变现不限于产品（父任务愿景）。
- 物化机制 `agent/loadout.py::materialize` 用 `shutil.copytree` 整目录拷（已核）。
- 执行层现状（已核）：部门占位、外设层仅入站——没有业态今天能端到端跑；故本任务只做 CEO 侧生成骨架。

## Goal

给 CEO 一个 **`find-opportunity` skill 骨架**，把「生成候选」补上且**业态自觉**：

- **业态自觉（Level-1）**：知道自己**不只能做产品**——还可以做服务/信息产品、内容/自媒体等；每次 wake 挑一个业态探索，**初期随便挑、别纠结**。
- **找机会的通用纪律（本任务真正写实的部分）**：别凭空编 → 先派研究 Goal 给 `researcher` 取真实信号 → 产 2-3 个明显不同的候选 → 逐个交 `decide-direction` 判断（不自判）→ 查 `/company` 避已否 + 标定几天能交付。
- **具体方法留空占位**：每个业态「怎么找机会」的具体打法**这轮不写**，skill 里留一句占位（指向后续研究任务）。骨架靠上面的**通用信号驱动法**就已能跑。

**核心纪律**：赋能 > 限制；只写通过三道检验的条目；用大白话，不造黑话（撤掉"透镜/方式轮"这类词）。

## Requirements

- **R1 skill `find-opportunity`**（触发 heartbeat / 「该追什么但没候选」）：别凭空编（开篇）→ 挑一个业态（不只能做产品·初期随便挑）→ 先派研究 Goal 取信号 → 产 2-3 个不同候选 → 逐个交 decide-direction。
- **R2 业态自觉（Level-1）**：skill 列出 ≥3 个业态（服务/信息、内容/自媒体、产品；电商可提及）；product 不是唯一路径；每业态一句「追它=做什么」。**不写 token-ROI 选择准则**（agent 算不了）。
- **R3 具体方法占位**：每业态「怎么找机会」的具体方法**留空**，skill 用一句话占位（"更具体的方法在补，先用下面的通用信号驱动法"），并在 design/父 PRD 记为后续研究任务。
- **R4 信号接地可跑通**：通用法 = 派 `python3 -m orchestration.messaging send --to researcher --intent "<具体问题>"` 取真信号再生成，headless 不假设交互端。
- **R5 接缝纪律**：只生成不判断（不召 critic）；生成前查 `/company` 避已否（DO_NOT_RESURFACE）；标定「几天能交付的最小真实价值」，非十亿级；候选匹配部门真能造/交付的东西。
- **R6 charter 顶层一句**：idle 无候选时走 find-opportunity（先挑业态再找机会），别空手拍产品方向直接发。
- **R7 借用署名**：PG / gstack(MIT)（骨架里的通用纪律来源）。
- **R8 声明式**：零 .py 逻辑改动；仅 `agent/tests/test_resident_loadout.py` 断言更新。

## Acceptance Criteria

- [ ] **AC1（物化）**：`ceo.yaml` skills 含 `find-opportunity`；`test_resident_loadout` 断言含 `find-opportunity` 且 `SKILL.md` 物化存在；`pytest` 绿。
- [ ] **AC2（业态自觉）**：SKILL.md 列 ≥3 业态、product 不是唯一路径、明确「初期随便挑」；skill 内无 token-ROI 选择准则。
- [ ] **AC3（大白话 + 占位）**：skill 无"透镜/方式轮/lens"黑话；每业态具体方法处是明确占位（不是编的假方法）。
- [ ] **AC4（通用纪律写实 + 信号接地）**：别凭空编 + 先派研究 Goal 取信号（真实 `messaging send` 命令）+ 产 2-3 候选 + 交 decide-direction + 避已否 + 标定小，均写清。
- [ ] **AC5（接缝）**：与 decide-direction 无职责矛盾（只生成不判断）。
- [ ] **AC6（署名+风格）**：借用标来源+许可；风格与现有 skill 一致（祈使/具体/渐进披露），description 对齐 heartbeat wake 措辞。
- [ ] **AC7（e2e，SOP 第 7 阶段·不可跳）**：真跑一次 wake（`make up`）观测 CEO 走 find-opportunity：挑业态→派研究 Goal 取信号→产多候选→交 decide-direction。（骨架跑通即可；具体方法留后。）

## Out of Scope（押后 / 不做）

- **各业态「怎么找机会」的具体方法**——本轮留空，单独研究任务（父 PRD 任务地图）。
- 跨境电商任何内容；各业态执行能力（父任务 ② 层，sibling）；有状态业态轮转；改 decide-direction/critic；新建 agent 定义；度量层；防御性「别生成 X」清单。

## 依据

- 父 `../07-01-ceo-monetization/prd.md`（愿景/roadmap/门控）；判断侧 `../06-28-role-ceo/`（decide-direction/critic 契约、DO_NOT_RESURFACE）。
- `research/idea-generation-methods.md`（本任务已实拉 PG/gstack/1000TF/Sales Safari）**降级为后续「找机会方法」研究任务的种子**，不作本任务 skill 正文依据。
- 本 session 用户多轮形状决策（多业态 / 实验非提前证明 / token-ROI 归 operator / 具体方法留空 / 大白话）。
