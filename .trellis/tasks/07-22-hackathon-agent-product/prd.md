# HackSome Idea Phase v1 — 产品需求文档

## 目标

实现一个小型、本地运行、第一版仅适配 Codex 的中控系统。它接收一道黑客松赛题，最终产出零个或多个有真实依据的 Useful Idea Card。

这一版本只负责寻找 Idea。Build、GitHub Repo 和 Pitch 属于后续独立系统，不在本阶段实现。

产品是否成功，不能只看它有没有生成文件。更重要的判断是：用户能否看懂完整的推理过程，并愿意从最终 Idea Card 中选择至少一个进入 Build 阶段。

## 背景

ClaudeHack 是一个效果很好的参考项目，不是一个需要被纠正的旧系统。HackSome v1 会保留 ClaudeHack 中有价值的并行探索思路，同时把 Idea 阶段单独拆出来，使其过程更清楚、更容易复盘。

HackSome v1 不复制、也不修改 ClaudeHack 的 Build 工作流。

之前 HackSome 的 S0–S11 实现由本方案取代。已有 Git checkpoint 是回滚边界，当前工作区中的旧实现可以直接覆盖。

## 产品要求

### R1 — 七步 Idea 工作流

系统必须实现以下逻辑流程：

1. 解析赛题；
2. 扩散出自然、宽泛的人群类型；
3. 每个人群独立且并行地进行 Research；
4. Problem Writer 产出 Problem，每个 Problem 再进入独立的 Problem Gateway；
5. 每个通过 Gateway 的 Problem 进入 Idea Generator；
6. 每个 Idea 都进入一个独立的 Idea Rate Team / Red Team；
7. 将通过 Red Team 的 Idea 确定性地校验并发布为 Idea Card。

控制器内部可以使用自己的阶段名称，但本版本不得重新加入以下环节：Research Verifier、竞品研究、Idea Revision、Build Feasibility、Challenge Compliance、Build 或 Pitch。

### R2 — Useful 路线的发现方式

- Audience 扩散从职业、群体、角色或宽泛用户类型开始。
- v1 最多扩散五个人群；这是第一版的硬上限，不再继续增加 Audience 分支。
- 在 Research 之前，不得凭空编造非常具体的工作场景，例如“每周需要为不同学生准备练习题的初中老师”。
- Research 需要从公开信息中寻找真实行为、痛点、现有解决方式和反面证据。
- Research Prompt 应在合适时优先搜索 Reddit 和 GitHub，同时允许使用其他公开来源。
- 每个人群拥有独立的 Research Session。v1 默认每个人群一个 Researcher，但数量可配置。
- 一个 Problem Writer 可以为对应人群产出零个或多个 Problem。
- 每个 Problem Gateway 都必须是一个新的独立 Session。
- Problem Gateway 判断该 Problem 是否真实、有证据、与赛题相关，并且对用户确实重要。
- 每个通过 Gateway 的 Problem 会扇出到多个独立的 Idea Generator Session。
- v1 默认每个 Problem 启动三个 Idea Generator，但数量可配置。
- 每个生成出的 Idea 都必须进入一个新的独立 Red Team Session。
- Red Team 只围绕两个核心问题进行绝对判断：
  1. 用户能否真实感受到产品价值？
  2. 产品里是否存在一条真正完整的端到端 User Flow？
- 如果核心价值依赖产品无法控制的权限，或依赖外部角色后续采取行动，也应视为 User Flow 不成立。

### R3 — 动态候选数量

- 除了第一版最多五个人群外，Problem、Idea 和最终 Idea Card 都不设置固定产出数量。
- 不做 Top-K、相对排名、强制方向差异或语义去重。
- 多个 Idea 即使相似，只要都能独立通过统一质量门槛，就全部保留。
- 任何一个阶段都允许产出零个候选结果。
- 一个最终没有任何 Idea Card 的 Run 也可以是流程上有效的结果。
- 所有并行任务受一个全局可配置并发上限约束。

### R4 — Prompt 是 Agent 之间的上下文传输方式

- Agent 需要读取的上游内容，必须由 Hub 直接作为文本注入它的 Prompt。
- Agent 不应被要求寻找或读取上游 Markdown 文件。
- Hub 负责选择上下文、读取已经持久化的内容，并把原文放进有明确边界的 Prompt 区块。
- Research 中来自社区或网页的文字必须标记为“不可信数据”，不能被当作对 Agent 的指令。
- Agent 使用阶段专属的结构化 JSON 返回结果。
- JSON 中的 Markdown 正文由 Hub 保存为正式文件；Agent 不直接写 canonical 文件。

### R5 — Hub 保存完整过程

对于每个 Run 和每个 Task，Hub 必须保存足够的信息，用于后续复盘和确定性检查：

- 原始赛题输入；
- Task ID、阶段、父级候选关系和任务状态；
- 实际发送给 Codex 的完整 Prompt；
- 使用的输出 Schema；
- Codex Session ID、尝试次数、时间、耗时、用量和错误；
- Codex 原始 stdout/stderr JSONL 和原始 last message；
- 解析后的结构化输出；
- 所有发布后的 Markdown；
- pass/reject 决策和完整候选 lineage。

“把内容保存成文件”和“让 Agent 通过文件读取上下文”是两件不同的事：

- 文件是审计、复盘和持久化介质；
- Prompt 才是 Agent 之间唯一的上下文传输介质。

### R6 — 运行边界

- v1 只支持本地 Codex CLI。
- 第一版不需要 VM 或 Docker。
- 每个阶段 Session 都必须与用户环境中的插件、Skill 和项目指令隔离。
- 只有 Research Session 开启实时 Web Search。
- 其他 Session 显式关闭 Web Search，也不需要写工作区。
- 基础设施重试可以恢复同一个 Task 的准确 Codex Session。
- 不同逻辑角色之间必须使用不同 Session，不能继承彼此的隐藏上下文。

### R7 — 最终 Idea Card

一个 Idea Card 至少需要讲清楚：

- 给谁使用；
- 用户面对的真实 Problem；
- 产品是什么，以及它的核心机制；
- 一条具体、完整的端到端 User Flow；
- 用户在哪个时刻能够真实感受到价值；
- 可以现场跑通的 Demo 边界；
- 重要假设、风险和支持证据；
- 来源 Problem、Generator Session 和 Red Team 决策的 lineage。

只有 Markdown 结构有效，并且对应 Red Team 决策为 `pass`，Hub 才能发布 Idea Card。

这一步由控制器确定性执行，不再创建额外的 Agent Session。

## 验收标准

1. 一个脚本化端到端测试能够经过全部七步，并且最终只发布 Problem Gateway 与 Red Team 都通过的 Idea Card。
2. 人群扩散最多返回五个人群；当存在至少两个人群时，各人群 Research 会在全局并发上限内重叠执行，并且不会共享 Codex Session。
3. 在默认配置下，一个通过的 Problem 会启动三个独立 Idea Generator；所有有效输出都保留，不受相似程度和数量影响。
4. 测试能够证明下游 Prompt 包含被选中上游 Markdown 的完整原文，同时不要求 Agent 读取上下文文件。
5. 测试能够证明只有 Research 开启 Web Search。
6. 每个 Task 目录都包含完整 Prompt、请求与结果元数据、原始模型输出和 Codex 日志；Run 状态及决策记录能够定位每个任务和候选项。
7. 被 Problem Gateway 拒绝的 Problem 不会进入 Idea Generator；被 Red Team 拒绝的 Idea 不会变成 Idea Card。
8. 零人群、零 Problem、零 Idea 和零通过 Idea 都能正常结束，并产生有效的空结果。
9. `status` 和 `validate` 可以在不调用 Codex 的情况下检查已经保存的 Run。
10. 如果保留基准测试，PAWN 和米哈游赛题必须继续作为两份不同的 fixture。
11. 默认单元测试不调用付费模型，并且全部通过。

## 不在 v1 范围内

- Creative / Have Fun 路线。
- 独立的 Research Source Verifier。
- 排名、评委式筛选、强制方向差异或相似度淘汰。
- 自动 Repair 或 Revision 循环。
- 竞品研究、Challenge Compliance 和 Build Feasibility。
- 产品 Build、VM/Docker、GitHub 发布、Pitch 或 Pitch Deck。
- Claude Code 运行时适配。
- 修改或 Clone 本地 ClaudeHack 仓库。

## 当前规划状态

v1 暂时没有阻塞实现的产品问题。并行数量均通过配置控制，因此后续可以根据实际测试结果调整，而不需要改变工作流结构。
