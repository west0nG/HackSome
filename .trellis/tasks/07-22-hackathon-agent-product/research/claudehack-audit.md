# Research: ClaudeHack 前作审计

- Query: 审计 `west0nG/ClaudeHack` 的真实架构、执行循环、可复用资产、脆弱/未完成部分，以及 HackSome 新命题带来的变化。
- Scope: mixed（公开 GitHub 仓库 + 当前 HackSome 规划材料）
- Date: 2026-07-22

## Findings

### 结论摘要

ClaudeHack 不是一个抽象的“多 Agent 框架”，而是一个可运行的、以 Python 为确定性控制面、以 Claude Code CLI 子进程为执行面的原型。它已打通 `brief → Useful 型需求研究 → 人工筛选 → 产品文档 → 凭证 → 构建/审查 → HTML Pitch → GitHub 发布`。它最值得继承的是控制面和可观测性；最不应原样继承的是固定 prompt 流水线、弱证据链、只看代码不看渲染结果的“审美审查”，以及把并行数量当成组合多样性的做法。

实际的单项目控制流仍然近似单向：`concept → logic → technical → config → plan → dev → review → pitch → publish`；所谓 streaming 是不同 Card 独立并行前进，而不是单个项目可在 Idea / Build / Pitch 间自由回退（[`control/streaming.py:121`](https://github.com/west0nG/ClaudeHack/blob/main/control/streaming.py#L121)）。代码里只有两个明确回路：Concept 阶段可一次性淘汰 Idea（[`control/stages/stage2.py:101`](https://github.com/west0nG/ClaudeHack/blob/main/control/stages/stage2.py#L101)），Build 失败后最多重跑一次 Dev + Review（[`control/stages/stage3.py:245`](https://github.com/west0nG/ClaudeHack/blob/main/control/stages/stage3.py#L245)）。没有“构建证据推翻 Idea → 回到研究/改命题”“Pitch 暴露叙事缺口 → 回补产品”的控制转移。

并行产出多个项目本身应保留，这是 Agent 的组合搜索优势；问题是 ClaudeHack 的组合管理很弱：所有候选走同一套角色、模板和技术偏好，资源主要按固定 session 预算平均分配，没有根据新证据动态加注/止损，也没有显式约束候选之间的机制、视觉语言和惊喜类型必须真正不同。当前做法更像“同构流水线的 N 次并行”，还不是 portfolio search。

### 实际架构与执行方式

- 输入被解析为 `HackathonBrief`，保存主题、硬约束、评审标准、技术要求、时限等；这是一个清晰可复用的边界对象（[`control/models.py:87`](https://github.com/west0nG/ClaudeHack/blob/main/control/models.py#L87)）。
- Python 控制面负责 asyncio 并发、事件、阶段转换、文件收集和失败处理；Claude Code 以隔离的 `claude -p --output-format stream-json` 子进程运行（[`control/session_manager.py:23`](https://github.com/west0nG/ClaudeHack/blob/main/control/session_manager.py#L23)，[`control/session_manager.py:308`](https://github.com/west0nG/ClaudeHack/blob/main/control/session_manager.py#L308)）。阶段间以 Markdown/目录作为协议，不依赖共享对话记忆。
- Stage 1 先扩展具体人群/痛点，再让 Search 与 Synthesis 分离，并做流式去重及最终审查（[`control/stages/stage1.py:252`](https://github.com/west0nG/ClaudeHack/blob/main/control/stages/stage1.py#L252)，[`prompts/stage1/research.md:167`](https://github.com/west0nG/ClaudeHack/blob/main/prompts/stage1/research.md#L167)）。
- ReviewGate 后，每张卡独立运行 Stage 2→Config→Stage 3→Stage 5→Stage 4，全球 semaphore 限制 Claude session 并发（[`control/streaming.py:38`](https://github.com/west0nG/ClaudeHack/blob/main/control/streaming.py#L38)）。
- Stage 3 将产品构建拆为 Plan / Dev / Review 三个 session；审查 session 与开发共用工作目录并可直接修复（[`control/stages/stage3.py:108`](https://github.com/west0nG/ClaudeHack/blob/main/control/stages/stage3.py#L108)）。
- Stage 5 只产出 `pitch-script.md` 与自包含 `pitch-deck.html`；Storyteller 能读取源码，但没有浏览器/截图验证（[`control/stages/stage5.py:73`](https://github.com/west0nG/ClaudeHack/blob/main/control/stages/stage5.py#L73)，[`control/stages/stage5.py:169`](https://github.com/west0nG/ClaudeHack/blob/main/control/stages/stage5.py#L169)）。

### 建议复用

1. **确定性控制面 + Agent 数据面**：阶段、并发、预算、重试、停止和外部动作由代码拥有，不让 LLM 自己“记住流程”。
2. **文件化 artifact contract**：Brief、Idea Card、Concept、Plan、Review、Pitch 都可检查、恢复、重放；适合升级为带 schema/version/provenance 的 artifact ledger。
3. **Search / Synthesis 上下文隔离**：研究者收集原始证据，合成者在较干净上下文中判断，方向正确；新版本应保留完整来源，而非只保留描述。
4. **候选级 streaming 与故障隔离**：快项目不等待慢项目；某一候选失败不拖垮整体。这适合继续发展成带动态资源分配的 portfolio controller。
5. **事件总线、session JSONL/摘要、resume、超时与预算**：提交历史显示这些能力来自真实运行故障，而非纸面设计；例如长 prompt 改 stdin（[commit `a330fa3`](https://github.com/west0nG/ClaudeHack/commit/a330fa38cf538b588bbad6280295b2dabc294227)）、诊断日志（[commit `d34520c`](https://github.com/west0nG/ClaudeHack/commit/d34520c3dab005044dba245092b6348adb810f24)）和 streaming/credential barrier（[commit `401337a`](https://github.com/west0nG/ClaudeHack/commit/401337a5267952db361195cc7858ebfc545f158f)）。
6. **失败 sentinel 与明确 gate**：`ELIMINATED.md` / `BUILD_FAILED.md` 的机器可读思想值得保留，但应改为结构化决策事件，记录证据、责任 reviewer 和允许的下一跳。

### 脆弱、缺失或会制造 AI slop 的部分

1. **Idea engine 只有 Useful 逻辑，没有 Creative 逻辑。** Stage 1 明确要求“具体人群 + 真实可搜索痛点”，并用频率、workaround、软件可解来筛选（[`prompts/stage1/main.md:40`](https://github.com/west0nG/ClaudeHack/blob/main/prompts/stage1/main.md#L40)，[`prompts/stage2/concept.md:18`](https://github.com/west0nG/ClaudeHack/blob/main/prompts/stage2/concept.md#L18)）。一个纯粹好玩、荒诞、表演性强的 Creative Idea 会被当前质量门直接杀掉。HackSome 需要两套不同的探索先验与判据，共享的只是赛题约束、可构建性和最终证据账本。

2. **证据链在 Stage 1 后断裂。** Search prompt 甚至要求 findings 不必保留完整 URL、日期或 engagement（[`prompts/stage1/research.md:68`](https://github.com/west0nG/ClaudeHack/blob/main/prompts/stage1/research.md#L68)）；最终输出只复制 Idea Card，后续 Concept 却要求判断来源是否“可验证”（[`prompts/stage2/concept.md:20`](https://github.com/west0nG/ClaudeHack/blob/main/prompts/stage2/concept.md#L20)）。这使“真实洞察”和“模型写得像真实洞察”难以区分。应让每个 claim 引用稳定 `evidence_id`，Repo、Demo、Deck 的声明都必须回指研究或运行证据。

3. **评审主要验证可编译，不验证体验是否成立。** Web app 的成功条件基本是 `npm run build`，多数其他类型也只是启动/打包（[`prompts/stage3/review.md:248`](https://github.com/west0nG/ClaudeHack/blob/main/prompts/stage3/review.md#L248)）。Designer 只读 UI 源码、检查颜色/间距/字体并加 hover/transition（[`prompts/stage3/review.md:130`](https://github.com/west0nG/ClaudeHack/blob/main/prompts/stage3/review.md#L130)）；它没有截图、真实浏览器路径、参考物或外部观察者反馈。因此它优化的是“看起来像完成了 UI checklist”，正是常见 AI slop 来源。

4. **Pitch 不是由可观测 Demo 证据合成。** Storyteller 从源码推断“点 X 会看到 Y”（[`prompts/stage5/storyteller.md:36`](https://github.com/west0nG/ClaudeHack/blob/main/prompts/stage5/storyteller.md#L36)），Deck 明确允许 screenshot placeholders，且设计被固定成 dark theme + emoji + 6–8 页模板（[`prompts/stage5/deck-builder.md:36`](https://github.com/west0nG/ClaudeHack/blob/main/prompts/stage5/deck-builder.md#L36)）；最终验证只是 `wc -l`（[`prompts/stage5/deck-builder.md:100`](https://github.com/west0nG/ClaudeHack/blob/main/prompts/stage5/deck-builder.md#L100)）。这既容易产生同质化，也无法保证 Deck、运行状态和现场 Demo 一致。

5. **固定 scaffold 强化同质化。** Dev prompt 为多类项目规定了 React/Vite/Tailwind、Express、Commander 等固定脚手架，并要求“follow plan exactly / don't improvise”（[`prompts/stage3/dev.md:46`](https://github.com/west0nG/ClaudeHack/blob/main/prompts/stage3/dev.md#L46)，[`prompts/stage3/dev.md:268`](https://github.com/west0nG/ClaudeHack/blob/main/prompts/stage3/dev.md#L268)）。这对跑通率有利，但会把不同 Idea 压成相似载体。新版本应让交付约束固定、表达策略可变，并通过渲染后的比较来淘汰套路。

6. **发布阶段会破坏事实一致性。** Stage 3 要求生成真实运行 README，但 Stage 4 随后无条件覆盖它，并对所有 product type 写入通用 `npm install && npm run dev`（[`control/stages/stage4.py:103`](https://github.com/west0nG/ClaudeHack/blob/main/control/stages/stage4.py#L103)，[`control/stages/stage4.py:221`](https://github.com/west0nG/ClaudeHack/blob/main/control/stages/stage4.py#L221)）。CLI、扩展、Slack App 的最终 Repo 因而可能得到错误说明。Repo/Deck/Demo 应从同一 verified manifest 投影，而不是各自重新生成事实。

7. **生成者与批评者没有真正分离。** 所有 AI session 只能选择同一 Claude 家族的 sonnet/opus（[`control/main.py:102`](https://github.com/west0nG/ClaudeHack/blob/main/control/main.py#L102)）；大量 gate 是同一模型在相似 prompt 下自评。HackSome 引入 Codex + Claude Code 的价值不只是“多一个 executor”，而是让 proposal、implementation、observation、critique 具有不同上下文/模型/权限，并检查 critic 是否真的改变了下一步动作。

8. **本地无沙箱的 blast radius 很大。** Claude CLI 固定加 `--dangerously-skip-permissions`（[`control/session_manager.py:308`](https://github.com/west0nG/ClaudeHack/blob/main/control/session_manager.py#L308)），Dev/Review 可用 Bash 且拿到凭证；默认还会创建 public GitHub repo，除非显式 `--skip-publish` 或 `--private`（[`control/main.py:89`](https://github.com/west0nG/ClaudeHack/blob/main/control/main.py#L89)，[`control/stages/stage4.py:286`](https://github.com/west0nG/ClaudeHack/blob/main/control/stages/stage4.py#L286)）。即使 v1 不做 VM/Docker，也需要 capability policy：工作区根目录、命令类别、凭证作用域、网络/发布动作，以及不可逆动作前的硬 gate。

9. **完成度声明高于验证证据。** README 把 Stage 0–5 标成 Done，但把端到端 testing/error handling 列为后续 Polish（[`README.md:499`](https://github.com/west0nG/ClaudeHack/blob/main/README.md#L499)）。仓库树未见 `tests/`、CI workflow、lockfile/`pyproject.toml`，且 README 指向不存在的 `LICENSE`（[`README.md:528`](https://github.com/west0nG/ClaudeHack/blob/main/README.md#L528)）。因此应把它视为高价值原型与故障经验库，而不是可直接扩展的可靠内核。

### HackSome 相比 ClaudeHack 应改变的产品命题

- 从“把每个阶段都跑完”改为“在约束预算内管理一个多候选 portfolio，并最大化最终提交组合的 judge value”。保留并行，但增加真正的差异性约束、候选间比较、证据驱动加注/止损和探索/利用预算。
- 从 stage pipeline 改为显式状态机/事件图：`hypothesis → prototype → observe → critique → continue / pivot / fork / kill / pitch-gap-fix`；每次转移必须有证据和预算理由。
- `Useful` 与 `Creative` 在发现和评价处明确分叉：Useful 依赖用户行为/替代方案证据；Creative 依赖新奇机制、现场可演性、可复述性、反预期与视觉/交互 surprise。不要拿 pain-frequency rubric 评价 Creative。
- 把 anti-slop 从文案规则变成观察系统：实际运行、截图/录屏、关键路径任务、并排候选比较、风格参考与反参考、盲审、重复套路检测；critic 的输出必须成为下一轮 task 或 kill/pivot 决策。
- 建立 `claim/evidence manifest` 作为 Repo、Demo、README、Pitch Script、Deck 的共同事实源，禁止各阶段凭 PRD 再创作能力描述。
- Codex/Claude Code 先作为可替换 worker/reviewer adapters，而不是把编排耦合到某一个 CLI；控制层拥有统一的 session contract、工具权限、产物 schema 和成本记录。

## Files Found

- [`README.md`](https://github.com/west0nG/ClaudeHack/blob/main/README.md) — 对外宣称的 pipeline、CLI 与完成状态。
- [`CLAUDE.md`](https://github.com/west0nG/ClaudeHack/blob/main/CLAUDE.md) — 最接近当前实现的内部架构说明。
- [`Hackathon Agent Design.md`](https://github.com/west0nG/ClaudeHack/blob/main/Hackathon%20Agent%20Design.md) — 设计演进、预算、各阶段格式与待办。
- [`control/main.py`](https://github.com/west0nG/ClaudeHack/blob/main/control/main.py) — CLI、resume、ReviewGate 与主控制流。
- [`control/streaming.py`](https://github.com/west0nG/ClaudeHack/blob/main/control/streaming.py) — 候选级端到端并行编排。
- [`control/session_manager.py`](https://github.com/west0nG/ClaudeHack/blob/main/control/session_manager.py) — Claude CLI 子进程、流式事件、重试、预算、权限与凭证注入。
- [`control/stages/`](https://github.com/west0nG/ClaudeHack/tree/main/control/stages) — Stage 0–5 的实际 gate、失败和发布逻辑。
- [`prompts/`](https://github.com/west0nG/ClaudeHack/tree/main/prompts) — Idea、PRD、Build Review、Pitch 的真实评价函数。
- [Repository tree](https://github.com/west0nG/ClaudeHack/tree/main) — 未发现测试、CI、锁文件或实际 LICENSE。

## Code Patterns

- `HackathonBrief` 是结构化入口契约；Markdown 目录是阶段间 artifact contract。
- `SessionManager` 是统一 worker adapter 的雏形；目前硬编码 `claude`，可抽象为 Codex/Claude Code backend。
- `asyncio.gather` + semaphore 实现候选并行；`streaming.py` 直接 import 各 stage 的 `_private` 函数，说明阶段边界尚未形成稳定公共接口（[`control/streaming.py:25`](https://github.com/west0nG/ClaudeHack/blob/main/control/streaming.py#L25)）。
- 质量状态主要由文件存在、CLI exit code 和 sentinel 文件推导；缺少统一 typed decision/evidence schema。

## External References

- Repository: [west0nG/ClaudeHack](https://github.com/west0nG/ClaudeHack), default branch `main`, public。
- 开发集中在 2026-03-02 至 2026-03-17；初始提交是 [autonomous Stage 1 vertical slice](https://github.com/west0nG/ClaudeHack/commit/a43ebf44106e097c3f57863e9016fc9a0a83ddd1)，当前最新提交把重复 helper 抽成共享模块（[commit `96f6708`](https://github.com/west0nG/ClaudeHack/commit/96f6708f5e22f2de2be12adfe4f318035f06893e)）。
- Python 依赖只有未锁定的 `websockets>=12.0` 与 `aiofiles>=23.0`（[`requirements.txt`](https://github.com/west0nG/ClaudeHack/blob/main/requirements.txt)）；Claude Code CLI 版本也未固定，复现性有限。

## Related Specs

- `.trellis/tasks/07-22-hackathon-agent-product/prd.md` — 当前 HackSome 的 Goal、R1–R6、anti-slop 与 Repo/Deck 一致性要求。
- `.trellis/spec/guides/cross-layer-thinking-guide.md` — Repo / Demo / Deck / evidence ledger 是跨层事实边界，应由单一 contract owner 管理。
- `.trellis/spec/guides/code-reuse-thinking-guide.md` — ClaudeHack 最近一次提交已暴露阶段间 helper 重复和契约漂移；新 orchestrator 应先抽象 worker/artifact/decision 接口。

## Caveats / Not Found

- 审计基于 2026-07-22 时公开 `main` 分支；未运行一次完整 ClaudeHack 流程，因此对实际生成物美学与成功率的判断来自代码、prompt、仓库结构及提交记录，而不是基准测试。
- 仓库中没有随附的完整历史 `workspace/` 运行产物或公开 benchmark，无法量化 Idea 淘汰率、Build 成功率、成本、Deck 质量和获奖相关性。
- “未发现 tests/CI/LICENSE”是对当前公开树的检查结果，不排除作者在未公开环境中有额外验证材料。
