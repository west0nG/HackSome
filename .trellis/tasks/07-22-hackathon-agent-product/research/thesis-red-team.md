# Research: Hackathon Agent 产品命题反方审视

- Query: 对“本地 Agent 能以极少/无人介入，把黑客松题目自主推进到 Idea、Build、Pitch，并产出有 taste 的 Beta Repo 与 Pitch Deck”做第一性原理反证；找出最致命前提、可观察证伪、可修复执行问题与战略前提破裂，并设计最小决定性实验。
- Scope: mixed（当前 PRD、项目工作流与外部一手研究）
- Date: 2026-07-22

## Findings

### 最强版本的命题

这个命题并不荒谬。Codex/Claude Code 已能在有测试、终端输出和截图反馈的环境里长程执行；公开资料、比赛规则与历史作品也能为选题提供先验。如果系统能把规则解析、候选组合、可运行验证、事实账本和 Deck 合成串成闭环，它很可能比一个缺少流程的单人参赛者更快、更完整。当前 PRD 也已经避免了“只写一条超级 prompt”：要求候选淘汰与回退（`prd.md:33-37`）、每轮获取可观察证据（`prd.md:39-43`），以及生成者之外的对抗评审（`prd.md:45-49`）。

### 单一、最具后果的前提失败：系统没有 Idea/taste 的可信传感器

命题把两类完全不同的反馈混成了一个“迭代闭环”：

- Build 层大多有环境真值：代码能否启动、测试是否通过、页面是否渲染、Deck 是否与 Repo 一致。
- Idea/taste 层的目标却是关系性的：某个痛点是否真的重要、某个创意对这批评委是否意外、哪个取舍是否有品味。题目文本、本地运行结果和模型自己的解释都不包含这些答案。

因此真正缺失的不是更多生成能力，而是一个与生成模型错误不相关、且能反映用户/观众/评委反应的反馈通道。若 Codex 和 Claude 同时担任作者、用户、设计评论家与评委，角色提示只改变视角，不创造新信息。优化其内部评分会发生代理目标漂移：作品更完整、更流畅、更符合常见 rubric，却未必更有洞察或记忆点；这正是“AI slop”最可能的生成机制。多个模型也不自动等于独立判断：Apple 2026 的研究中，9 个不同模型家族的 judge panel 因相关错误只提供约 2 个独立投票的信息量。

所以：**“能自主交付两个文件产物”是可行工程命题；“能在无人外部判断下自主知道哪个 Idea/版本更值得做”尚无成立依据。** 非线性 workflow 如果每轮没有新增外部证据，只是更昂贵的自洽循环。

### 并行多项目应保留，但要验证它是不是“有效投资组合”

并行生产是 Agent 相对人类团队的真实结构性优势，不应退回单项目。反方问题是：`N` 个项目是否真是 `N` 个独立赌注。若它们共享题目解读、检索语料、模型审美和同一个 critic，候选数量增加但失败高度相关，best-of-N 的收益会很快趋平；更严重的是，同一个失真的内部评分器还会把 build token 继续投给错误分支。

因此并行架构应被定义成 portfolio allocator，而非任务 fan-out：早期强制候选在目标用户、核心机制、交互范式和叙事母题上正交；分阶段从“多而便宜的证据探针”收缩到少量可演示 build；保留一部分预算给低共识/反常识候选，允许被早期误杀的分支回流。关键指标不是产出项目数，而是 **effective independent bets、best-of-portfolio 外部得分、合格项目/单位成本，以及 allocation regret（事后最优分支与实际重投分支的差距）**。

### 如果该前提为假，应观察到什么

1. 自主循环显著提高自己的 rubric 分数与表面完成度，但盲评人类对最终作品的偏好不高于同预算的一次性强 baseline。
2. Codex 与 Claude critic 高度同意彼此，却在同一批“精致但空洞”样本上共同判断错误；增加 critic 数量没有等比例提高与人类的一致性。
3. critic 对候选 Idea 的排名会被措辞、长度、视觉 polish 或选项顺序明显改变；对同一模型生成的候选存在来源偏好。
4. `Useful` 路线能写出 plausible 的痛点叙事，却拿不出来自目标用户的新增行为证据；`Creative` 路线在不同随机种子下收敛到相似的 AI 产品母题。
5. 只加入两次、每次 5 分钟的真实外部判断（Idea 选择与 Demo 反应）就产生远大于增加模型轮次的质量提升。若如此，瓶颈是缺失信息，不是编排能力。
6. Build 通过率很高，但 Idea/记忆点/评委偏好得分与 Build 通过率弱相关，说明“把软件做完”不是当前主要约束。
7. 并行项目数从 4 增至 8 或 16 后，表面差异继续增加，但盲评 best-of-N、失败类型多样性与有效独立赌注数几乎不再增长；后续算力又集中到内部高分、外部低分的分支，形成高 allocation regret。

### 可修复的执行弱点 vs. 破裂的战略前提

| 类型 | 判断 |
| --- | --- |
| 可修复执行弱点 | 规则/预算解析、模型交接、失败恢复、浏览器与测试反馈、事实账本、Repo–Demo–Deck 一致性、停止条件、两条赛道的不同 rubric。这些都有可观察状态和确定性 verifier。 |
| 破裂的战略前提 | “生成者分离出的另一个 LLM 就是独立 taste”“只要非线性迭代就会改善 Idea”“一个通用 rubric 能覆盖 Useful 与 Creative”“完成 Repo + Deck 即代表完成黑客松”。这些若没有外部结果信号，无法靠 prompt、更多 agent 或更多轮次修复。 |
| 可修复的产品定位 | 把 v1 从“全自主选出唯一好 Idea 的参赛者”改为“证据驱动的 hackathon portfolio operating system”：并行探索多个真正正交的项目，自动完成研究、构建与叙事，把极少的人类/真实受众反馈视为组合重配的高价值传感器；或先只承诺一个具体黑客松、一种赛道和已知评委 rubric。 |

### 最小决定性实验（先于完整 orchestrator）

**实验 1：Evaluator validity test，1–2 天，无需先写 Agent。** 选 6 个未被模型反复见过的黑客松 brief（Useful/Creative 各 3），每题准备 6 个匿名 Idea，其中刻意放入“视觉/语言完整但洞察空”的 decoy 与“表达粗糙但有独特洞察”的候选。让拟采用的 Codex/Claude critic 排序，再由 3–5 位目标型评委盲做 pairwise choice。预注册：pairwise accuracy、top-1 命中、Kendall rank correlation、交换顺序后的稳定性、来源偏差。若 pairwise accuracy 不稳定地高于 65%，或 polish decoy 被系统性选中，就不要先投资完整自治闭环；核心 reward model 尚不存在。

**实验 2：Portfolio loop value test，薄垂直切片。** 对 4–6 个新 brief，以相同总模型成本比较：A）强单项目 baseline（只作为机会成本基准）；B）并行 N 项目、由模型自评分配后续 build 预算；C）B 加候选正交约束、分阶段 evidence gate，并用两次各 5 分钟的真人反馈做组合重配。最终由不知道条件的评委按真实 rubric 评分，并检查 Demo 与 Deck 事实。记录 best-of-portfolio 外部分数、合格成品数/成本、候选失败相关性和 allocation regret。并行优势成立需 B/C 的 best-of-N 与产量收益足以覆盖每个项目变浅的代价；若 B 的 nominal N 很大但 effective bets 很少，而 C 明显改善预算重投，就应保留并行、同时把“独立证据 + 最小高信息 HITL”写入 allocator，而不是继续盲目增加 fan-out。

**实验 3：Kill/pivot test，验证所谓非线性是否真实。** Agent 选 Idea 后才释放一份负面用户证据或关键技术阻塞，同时提供一个诱人但无证据的新方向。看它能否基于证据在“坚持、缩 scope、换 Idea”中作对，并记录决策依据。若 pivot 主要跟随 critic 文风或新颖措辞，workflow 只是流程表演。

### 当前最值得问用户的一个问题

> 如果只能保留一次、最多 10 分钟的人类输入，你最愿意把它放在“选 Idea”“看第一次 Demo”还是“Pitch 彩排”？

这个问题比先讨论 agent 架构更关键：它会暴露用户真正认为哪一层的外部判断不可替代，也决定 v1 是在证明“零 HITL”，还是在优化“每一比特人类判断的杠杆率”。

## Files Found

- `.trellis/tasks/07-22-hackathon-agent-product/prd.md` — 当前产品命题、自治约束、anti-slop 目标及规划验收标准；核心证据见 `:5-7`, `:20-24`, `:33-54`, `:64-89`。
- `.trellis/tasks/07-22-hackathon-agent-product/task.json` — 当前任务仍为 `planning`，尚未进入实现。
- `.trellis/workflow.md` — 要求 plan before code 且研究必须持久化，见 `:5-11`；任务研究目录约定见 `:40-59`。
- `.trellis/spec/guides/index.md` — AI cross-review 的项目内警示：严重结论需对实际事实验证，并预留较高假阳性预算，见 `:54-66`。

## Code Patterns

- 当前仓库没有产品代码；PRD 明确说明只有 Trellis 脚手架（`prd.md:15-16`）。因此没有可引用的 Agent 编排、评估器或反馈回路实现模式。
- 当前可复用的设计模式是“每轮动作必须绑定可观察证据”（`prd.md:41-42`）与“批评必须改变下一轮动作”（`prd.md:47-49`）；本研究的反方判断是：这两条对 Build 有效，但 Idea/taste 所需的“证据来源”尚未定义。

## External References

- [Anthropic, Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)（2024-12）：evaluator-optimizer 的适用前提是评价标准清晰且改进可测；自主 agent 执行中需要从环境持续取得 ground truth，必要时在 checkpoint 请求人类判断。
- [Anthropic, Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)（2026）：区分 transcript 与真实 outcome；强调含糊 rubric 会产生不一致判断，并建议早期用 20–50 个真实任务建立 eval。对本项目的启示是不能把“Agent 说它完成了”或“critic 说更好了”当 outcome。
- [Apple ML Research, Nine Judges, Two Effective Votes](https://machinelearning.apple.com/research/correlated-llm-evaluation-panels)（2026-06）：9 个 frontier judge 在测试中约等于 2 个独立投票，相关错误是瓶颈；这是“多 critic 自动获得独立 taste”的直接反证，但任务域并非黑客松，结论只能方向性外推。
- [NeurIPS 2024, LLM Evaluators Recognize and Favor Their Own](https://proceedings.neurips.cc/paper_files/paper/2024/file/7f1f0218e45f5414c79c0679633e47bc-Paper-Conference.pdf)：在摘要任务中观察到 frontier LLM 对自身输出的偏好且与 self-recognition 相关；支持对生成/评审共享模型分布的警惕，但并未直接测量产品 taste。
- [OpenAI, Introducing Codex](https://openai.com/index/introducing-codex/)（2025，页面有后续更新）：Codex 的可信反馈主要来自 terminal logs 与 test outputs，并明确建议人工 review/validate。它证明 Build verifier 的成熟度，不证明开放式 Idea 选择的评价有效性。

## Related Specs

- `.trellis/spec/guides/index.md:54-66` — AI 评审结论需要真实验证，避免把自洽评论当事实。
- `.trellis/spec/guides/cross-layer-thinking-guide.md` — 后续设计需把 Challenge → Evidence → Decision → Artifact 的边界契约显式化；本轮无代码实现，不适用具体前后端规范。

## Caveats / Not Found

- 尚无产品代码或真实运行 trace，因此本结论是对产品前提的反证，不是对某个实现的性能审计。
- 没有直接的公开研究证明“LLM 不能评审黑客松 Idea”；外部研究只证明自偏好、相关错误和含糊 rubric 的已知风险。上述最小实验正是为了在目标域内证伪或挽救命题。
- 本文件没有评估用户 2026 年 3 月的 ClaudeHack Repo；仅凭项目名无法可靠定位所有者，且该部分应与 ClaudeHack 专项研究合并，而不是在这里猜测。
