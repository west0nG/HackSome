# ClaudeHack Workflow / Prompt / Memory 实现核对

> 核对对象：本机 `/Users/weston/dev/ClaudeHack`，`main` 分支 commit `96f6708`。本地工作区干净，与 `origin/main` 完全一致，因此同时用 GitHub 链接提供可点击出处。目的不是评价或纠正 ClaudeHack，而是识别其中已经实际跑通、应当被 HackSome 继承的编排结构。

## 结论

ClaudeHack 的有效骨架可以概括为：

> **Python 确定性控制器 + 多个隔离 CLI session + 文件化阶段交接 + 每个 session 的事件日志 + 基于 workspace 产物的恢复。**

它并没有依赖一个所有 Agent 共用的长对话或“全局大脑”。Agent 的对话输出、工作目录文件、阶段输出和运行日志被明确分开。这与 HackSome 当前建议的 Artifact Memory 方向一致。

## 1. Stage 与 Agent 不是一一对应

ClaudeHack 的一个 Stage 可以包含多个不同 session：

- Stage 0 使用 Prompt Interpreter，把原始黑客松 Prompt 转成 `HackathonBrief` JSON。
- Stage 1 先运行 Crowd Direction Agent，再按 direction 并行运行 Research session；Research session 内部继续启动 Search sub-agents，最后用 clean-context Synthesis sub-agent 读取 findings 文件并生成 Idea Cards；随后还有 streaming dedup 和 Final Review。
- Stage 2 对每张 Idea Card 依次启动 Concept、Logic、Technical 三个独立 session，同时让不同 Card 的流水线并行。

因此 HackSome 的“Workflow Stage”应代表一个清楚的业务转换，而不必机械规定“一个 Stage 只能有一个 Agent”。一个 Stage 内可以为了搜索、复核或汇合启动多个 session，但 Stage 仍只有一个正式输入契约和输出契约。

依据：

- [Stage 0 interpreter](https://github.com/west0nG/ClaudeHack/blob/main/control/stages/stage0.py)
- [Stage 1 orchestration](https://github.com/west0nG/ClaudeHack/blob/main/control/stages/stage1.py)
- [Stage 1 research prompt](https://github.com/west0nG/ClaudeHack/blob/main/prompts/stage1/research.md)
- [Stage 2 three-session pipeline](https://github.com/west0nG/ClaudeHack/blob/main/control/stages/stage2.py)

## 2. Prompt 是文件模板，阶段内容显式注入

ClaudeHack 的 Prompt 独立保存在 `prompts/stageN/*.md`。Python 控制器读取模板，将本阶段需要的 `theme`、`HackathonBrief`、Idea Card、Concept 或 Logic 内容显式渲染进 Prompt。

例如 Stage 2：

1. Concept Prompt 读取原 Idea Card。
2. Logic Prompt 读取原 Idea Card 和 `concept.md`。
3. Technical Prompt 读取 `concept.md` 和 `logic.md`。

后续 session 没有继承前一个 Agent 的完整聊天记录，而是只接收经过阶段收敛的文件内容。这是可检查、可复跑的上下文交接。

依据：

- [Prompt loader and renderer](https://github.com/west0nG/ClaudeHack/blob/main/control/template.py)
- [Stage 2 explicit handoff](https://github.com/west0nG/ClaudeHack/blob/main/control/stages/stage2.py)
- [Concept prompt contract](https://github.com/west0nG/ClaudeHack/blob/main/prompts/stage2/concept.md)

## 3. Shared memory 的实际载体是 workspace 文件

ClaudeHack 为每个 session 指定独立 `working_dir`。Research sub-agents 把结果写成 `findings*.md`，clean-context Synthesis sub-agent 只读取这些文件，不读取搜索过程；Stage 2 再由控制器读取 `concept.md`、`logic.md` 等文件并传给下一 session。

这形成了三种不同的数据：

- **正式阶段产物**：Idea Cards、Concept、Logic、Technical 等下游会使用的内容。
- **运行日志**：每个 session 的原始 stream-json JSONL 和人类可读 summary，用于诊断。
- **控制状态**：session id、status、timeout、output files、event bus 信息。

运行日志不会自动成为下游 Agent 的业务事实，这一点应直接继承。

依据：

- [Session manager](https://github.com/west0nG/ClaudeHack/blob/main/control/session_manager.py)
- [Per-session JSONL logger](https://github.com/west0nG/ClaudeHack/blob/main/control/session_logger.py)
- [Research → findings → clean synthesis](https://github.com/west0nG/ClaudeHack/blob/main/prompts/stage1/research.md)

## 4. Resume 依赖产物 checkpoint，不依赖长会话

ClaudeHack 会把 workspace 连同 `run-metadata.json` 归档。恢复时，它复制归档 workspace，检查 Stage 1 是否存在 Idea Cards、Stage 2 是否存在 `concept.md`、Stage 3 是否存在可运行 demo 等完成标记，再从下一 Stage 继续。

这里的 `SessionConfig.session_id` 是控制器的逻辑任务标识；Claude CLI 命令没有传 `--resume`。也就是说，它恢复的是**业务产物和阶段状态**，不是 Provider 的隐藏聊天上下文。

这证明 HackSome 应继续把 artifact checkpoint 当作主要恢复机制。Codex session resume 可以补充“同一任务因进程中断后的续跑”，但不能成为跨阶段 memory。

依据：

- [Workspace restore and continuation](https://github.com/west0nG/ClaudeHack/blob/main/control/main.py)
- [Claude CLI command construction](https://github.com/west0nG/ClaudeHack/blob/main/control/session_manager.py)

## 5. 应直接继承的部分

1. Python / `asyncio` 控制器负责并发、超时、重试和阶段推进。
2. 每个 session 有明确 Prompt、工作目录、工具范围、预算和超时。
3. Prompt 通过 stdin 传入，不塞进 shell 命令参数。
4. 不同业务角色使用不同 session；阶段之间通过文件内容交接。
5. Search 与 Synthesis 分开，Synthesis 只读取整理后的 findings。
6. 多个候选并行推进，全局 semaphore 控制同时运行数量。
7. 原始事件 JSONL 与人类可读 summary 都保留。
8. workspace 是可归档、可恢复的业务 checkpoint。

## 6. 因本次已确认的新目标而扩展的部分

以下差异来自 HackSome 本轮已经确认的新产品要求，并不代表 ClaudeHack 当时的做法无效：

- Audience 阶段只产出职业、人群或类型，不在此时预设具体场景、痛点、产品类型或强制方向差异。
- Research 先产出带 URL、日期、原文和 claim 的 evidence，而不是直接产出正式 Idea Card。
- Evidence 由独立 session 重新打开来源复核后，才进入正式 Problem Card。
- 首轮 Idea 形成前不读取竞品；竞品研究在 Idea 草案之后进行。
- 不采用固定数量、排名或 soft cap；只用绝对门槛淘汰不合格项。
- Codex 的 `--output-schema` 用于把文件交接进一步变成可校验 artifact，Markdown 报告则由这些 artifact 生成。

## 7. 对 HackSome memory 设计的直接启示

最接近 ClaudeHack 已验证结构的 v0.1 方案不是共享完整对话，而是：

1. 控制器冻结本次 run 的 `ChallengeBrief`。
2. 每个 Agent 只收到当前任务需要的上游 artifact。
3. Agent 输出先经过 Schema 校验，再由控制器写入正式 artifact ledger。
4. session JSONL 只用于观察、诊断和同一任务恢复。
5. 新 Stage 默认新 session；不会把 Research session 继续 resume 成 Verifier 或 Judge。
