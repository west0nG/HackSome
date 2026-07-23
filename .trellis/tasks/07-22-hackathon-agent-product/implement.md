# HackSome Idea Phase v1 — 实施计划

## 回滚点

- 保留 Git checkpoint `3c7066b`，作为旧版 S0–S11 实现的恢复点。
- 不修改 `/Users/weston/dev/ClaudeHack`。

## 1. 替换协议和资源

- [ ] 将后端工作流 Spec 改写为七步 Idea-only 拓扑和 Prompt 注入协议。
- [ ] 用五种小型输出结构替换旧 Schema：Document、Audience List、Candidate List、Review 和必要的最终元数据。
- [ ] 用七个角色 Prompt 替换旧的 S0–S10 Prompt。
- [ ] 为 Problem 和 Idea 添加确定性的 Markdown 章节校验。

## 2. 实现中控 Hub

- [ ] 保存原始输入，并用原子方式维护 `run.json`。
- [ ] 保存每个 Task 的完整 Prompt、Schema、Session、Result、Error、Usage、时间以及原始 Codex 日志。
- [ ] 使用稳定 lineage ID 保存 Artifact、Event 和 pass/reject Decision。
- [ ] 提供读取 Artifact 原文的内部接口，用于 Prompt 注入。
- [ ] 不实现供 Agent 使用的文件 Context Manifest。
- [ ] 支持不调用 Codex 的 Run 状态查看和完整性校验。

## 3. 简化 Runtime 和 Prompt Renderer

- [ ] 保留已经验证过的 Codex stdin、JSONL、Session 和 Schema 协议。
- [ ] 如果真实与 Fake Runner 测试都通过，将阶段默认 Sandbox 改为只读。
- [ ] 只有 Research Task 开启实时 Web Search。
- [ ] 把所有上游 Markdown 放进边界清楚的 Prompt 数据区块。
- [ ] 在调用 Codex 前保存最终 Prompt。

## 4. 重写 Workflow

- [ ] 解析一份赛题，并扩散动态数量的宽泛 Audience。
- [ ] 每个 Audience 的 Research 并行运行。
- [ ] 每个 Audience 运行一个 Problem Writer，发布零个或多个 Problem。
- [ ] 每个 Problem 使用一个全新 Problem Gateway，只让 pass 的 Problem 继续。
- [ ] 每个通过的 Problem 启动可配置数量的 Idea Generator，默认五个。
- [ ] 每个 Idea 使用一个全新 Red Team，只让 pass 的 Idea 继续。
- [ ] 确定性校验并发布 Idea Card 和 Index。
- [ ] 保留所有相似但通过门槛的 Idea，不做排名、去重或强制方向差异。
- [ ] 保证并行完成顺序不会改变 Task ID、候选 ID 或最终排序。

## 5. 替换 CLI、README 和测试

- [ ] 保留小型本地 CLI：`doctor`、`run`、`status` 和 `validate`。
- [ ] 在进入代码实现前，确认 v1 是否需要失败 Run 的 `resume` 命令。
- [ ] 重写 README，明确 Idea-only 边界和 Hub Trace 结构。
- [ ] 直接替换旧 Workflow Loop 测试，不保留过时的 S0–S11 行为。
- [ ] 保留仍然符合新版 Runtime 的 CodexRunner 协议测试。
- [ ] 如果保留 Benchmark Fixture，PAWN 和米哈游必须是两个独立输入。

## 6. 必须运行的检查

- [ ] `python3 -m compileall -q src tests`
- [ ] `python3 -m unittest discover -s tests -v`
- [ ] `git diff --check`
- [ ] 使用 Trellis Check 检查 Spec 一致性、Prompt 传输、持久化完整性、Gateway/Red Team 独立性以及遗漏的边界情况。

## Review Gate

- 规划 Gate：PRD、Design 和本计划准确表达用户确认的七步范围，没有隐藏的旧阶段。
- 数据流 Gate：任何 Agent 都可以在不读取文件的情况下完成任务。
- 持久化 Gate：只依靠 Run 数据，就能复原发给 Agent 的 Prompt 和 Agent 返回的原始结果。
- 产品 Gate：只有具有真实可感知价值和完整 User Flow 的 Idea 才能成为 Idea Card。
