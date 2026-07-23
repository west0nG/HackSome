# Third Test 实验收官记录

收官时间：2026-07-19（Asia/Shanghai）

## 收官结论

用户确认 Third Test 已收集足够多的信息，可以结束实验并归档。本任务的完成语义是：

- 全 Claude Opus 公司长跑已经真实启动并持续产生经营、执行、验收与观测数据；
- 关键机制问题、行为模式和人工干预已经形成可复核记录；
- 实验样本量足以支撑后续 V7 三层 Agent Company 设计与实现；
- 归档不表示所有业务 Goal 均成功，也不表示旧 V6 fleet 需要继续运行。

## 证据规模

- Ledger 保留 88 个 Goal：76 `done`、11 `killed`、1 `running`；它们包含多组完整的 dispatch → execute → report → verify → terminal 样本。
- 五个角色共保留 1,203 条 wake telemetry，包含实际模型使用量数据。
- Observatory 保留 87 份 Goal 尸检与 17 份 Company review。
- `research/observations.md` 记录了 Stripe live 账户误判、Objective 哈希失效、CEO idle 吸附、真实 X 能力部署、heartbeat 修复等现象、根因、处置和验证证据。
- 主要启动提交为 `d29650ef`；运行期间形成的机制修复和观察结果后来进入 V6 snapshot `9df4b99`，并成为 07-12 V7 架构需求的真实运行依据。

## 原验收标准判读

- AC1：用户于 2026-07-19 明确结束实验并同意归档；实验运行期已经完成。审计时发现旧 Third Test 容器因 V7 `main` 已移除 V6 模块而出现 Hub / Provisioner 重启循环，这是实验结束后的残留运行环境，不把它解释为仍需维持的活跃长跑。
- AC2：满足。存在大量完整 Goal 闭环与原生 usage telemetry。
- AC3：满足。Observatory 报告数量远超最低要求。
- AC4：满足信息收集目标。机制干预与异常集中记录在 `research/observations.md`，并有相关提交、日志和复验结果可追溯。

## 保留事项

- 归档任务不会停止或删除 Docker 容器、`state/thirdtest/`、Observatory 数据或任何外部资产。
- 审计时旧 Third Test Hub / Provisioner 正在重启循环，原因是旧容器仍指向已经切换为 V7 的主工作区代码；如需释放资源或清理残留，应另行执行明确的运行环境停机/清理操作。
- Ledger 中最后一个 `running` Goal 作为实验终止时的现场状态保留，不回填为虚假的成功终态。

