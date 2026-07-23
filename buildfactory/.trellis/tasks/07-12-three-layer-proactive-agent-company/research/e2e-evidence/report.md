# V7 三层主动 Agent Company：真实 E2E 报告

- 日期：2026-07-14
- Company ID：`v7-three-layer-e2e-20260714`
- Account：`foundagent`
- 运行方式：`docker compose up -d --no-build`
- 结论：V7 主路径已经在全新 Company 上真实跑通；旧 Company 未迁移、未读取为新公司上下文、聚合指纹未变化。

## 1. 冷启动与组织形成

冷启动时仅有 CEO、Hub、Scheduler、Department Provisioner、Worker Manager、Verifier Manager 与 peripheral 等固定内核；Department、Worker、Verifier instance 都为零。Hub 给 CEO 投递 `company_idle` 后，CEO 自主完成市场研究并写入 Company State，随后提出 Company Objective。

Company Objective 产生 `review-fc369ab5ea59bcd0`，由临时实例 `verifier-1-1` 审核为 PASS。CEO 只依据公开模板选项创建 Builder 与 Growth；两个 Department Objective 分别产生 `review-a8eece77da778a4a` 与 `review-27468005b8a3cd41`，由 `verifier-2-1`、`verifier-3-1` 并行审核为 PASS，之后才启动对应常驻 Department。两条 review 创建时间仅差约 0.17 秒，且后创建的 Growth review 先完成，证明审核不是串行常驻角色。

真实形成的业务方向为：面向小型 Shopify agency 的 accessibility regression-QA 服务验证。CEO 负责 Company / Department Objective 与组织取舍；Growth 和 Builder 随后独立创建并推进 Goal，未等待 CEO 逐项派工。

## 2. 主动性与 Department 协作

Growth 与 Builder 在各自 Objective 生效后，自主创建了市场、转化、QA runner、pilot intake、证据安全与 synthetic sample 等业务 Goal。最终 Ledger 有 12 条 Goal，其中多个来自 Department 后续 wake，而非 CEO 指令。

两个 Department 通过 Hub 直接交换普通 `subject / body` 消息，例如：

- Growth → Builder：`Define the pre-contact public sample handoff`
- Builder → Growth：`Pilot handoff contract now being built`
- Builder → Growth：`Pre-contact public sample boundary defined`

这些消息只出现在目标 Department Inbox；CEO Inbox 没有副本。CEO 仅在一次明确需要核对公司状态时调用了 `inspect`，默认 wake context 不包含原始 Ledger 或 Department 对话正文。

## 3. 五 Worker 上限、严格 FIFO 与固定 deadline

真实业务 Goal 自然填满了五个 Worker lifecycle：`worker-1`、`worker-3`、`worker-5`、`worker-10`、`worker-11` 同时运行时，enqueue sequence 12 的 `goal-e9f9f888f99a7b84` 保持 `open`，没有越过并发上限。

sequence 2 的 `worker-2` 在 PASS 后于 `1784037465.1401184` 确认停止；`worker-11` 随后才于 `1784037465.3674943` 创建。补位发生在 stop 确认之后。sequence 12 在五个 lifecycle 均占位时继续排队，符合严格 FIFO。

`worker-5` 与 `worker-10` 各发生过一次真实的 computer-server readiness timeout；Scheduler 保留同一个 Goal / Worker 和队首位置重试，没有越过它们创建后续 Worker。每个已经启动的 Goal 保留原始绝对 `deadline_at`，启动重试、Verifier FAIL、Hub / Manager 重启均未延长 deadline。

在五个 Worker 运行期间重启 Worker Manager 后，五个容器 ID 均保持不变：`31f9b5f5ddb8`、`3f74f355f1c9`、`d1ae645ae497`、`25f9cf42165f`、`f47fd3315354`；registry 中的 Worker ID、start attempts 和 deadline 也未变化，没有重复启动或额外占位。

## 4. 独立 Verifier 与同 Worker 返工

`goal-712b8b56ca7ea5f6` 完整展示了结果验收闭环：

1. `worker-2` 首次提交 `/company/market/shopify-accessibility-pilot-conversion-pack.md`。
2. 新实例 `verifier-4-1` 对 `review-6fd5908ffb36b798` 给出 FAIL，并返回具体缺口。
3. 系统保留同一 `worker-2`、同一容器、同一 workspace、同一 session token `019f60df-eb7a-7781-984b-5bd5d8bfb419` 与同一 deadline；Worker 在 Company State 原文件上继续修改。
4. 第二次提交产生新 review `review-a9c1bbd7c4baa1c3` 和新实例 `verifier-6-1`，最终 PASS。
5. Goal 进入 `done`，Worker 容器确认销毁后才释放第五个 Worker 名额。

Worker registry 记录该 Worker `turns: 2`、同一个 session token，且 Goal 的 `start_attempts: 1`、`deadline_at: 1784047510.5706952` 全程未变。另有两个真实业务结果被 `verifier-7-1`、`verifier-8-1` 并行判为 FAIL，并分别回到原 Worker 继续返工。

一次运行中实际观测到的 Verifier 并发峰值为 2；全局最多 3、第 4 个排队、取消/超时 during-create、销毁确认后释放名额等边界由确定性并发测试覆盖。此次真实业务结果没有在同一时刻自然形成 4 条以上 review，因此不把“真实观测到 3+1”标为已完成。

## 5. Cancel、Company State 与挂载边界

Growth 识别出五条 operator 注入的并发 marker Goal 与自身 Objective 无关并主动取消，证明 Department 拥有自己 Goal 的治理能力。其中 `goal-75be65ef192e6fd9` 已创建 `worker-4` 并提交结果，随后被取消；关联 review 变为 `cancelled`，Worker 被停止。系统没有 supersede，也没有 Department 退役入口。

真实 Worker 直接在 `/company` 写入市场与产品交付物；Verifier 从同一路径只读验收。容器 mount 检查确认：

- Worker：`/company` 为 rw。
- Verifier：`/company` 为 ro。
- Ledger、Inbox、Reviews、Workers、Departments、Notes、Control、Telemetry、Sessions 均没有作为业务 state mount 暴露给 LLM runtime。
- runtime home、workspace、account material 由系统单独管理，不属于 Company State。

## 6. 可靠唤醒与恢复

真实运行中分别中断过 Agent wake 与 Hub。未 ack 的消息在恢复后仍按原 message ID 重放；对于“cursor 已推进但 ack receipt 尚未落盘”的窗口，Hub 根据只读 consumed 证据补写 receipt，没有重复业务 mutation。Hub 与 Verifier Manager 重启后，Objective、Department、Goal、review FIFO、Worker deadline 和 idle registry 均保留。

Worker Manager 的五 Worker 在线重启也已在本次运行中完成，对账后未重复执行命令。相关 crash-window、stop-during-create、late container cleanup 与幂等 replay 另有单元/并发回归测试。

受控停机时还发现旧版 `make down` 只移除固定 Compose 服务，无法清理没有 Compose project label 的动态容器。实现已在本次交付内修正为：先停止固定服务，再按精确 `foundagent.company=$(COMPANY)` label 停止并删除动态 Department / Worker / Verifier，最后清理 Compose 资源；新增回归测试验证不会使用宽泛匹配。修正后本测试公司的容器与网络均为零。

## 7. 全量可观测性

运行归档包含：

- 21 个 CEO / Department wake run；
- 6 个已完成归档的 Worker turn（停止测试公司前仍有长时 Worker turn 在运行）；
- 9 个已完成归档的 Verifier review run；受控停机时另有 2 个 review 正在运行，其容器已按 Company label 清理，registry 可在下次启动时对账；
- 1324 条 method audit 记录；
- CEO、Builder、Growth 的完整 stdout / stderr；
- Hub、Department Provisioner、Worker Manager、Verifier Manager 与 peripheral service log。

每个 run 目录分别保存 `metadata.json`、`runtime.jsonl`、`model-output.txt`、`harness.log`、`container.log` 与 `stderr.log`。Telemetry 未挂载给任何 LLM runtime。

## 8. 自动化验证

- 全量测试：`739 passed in 10.74s`
- Python compileall：通过
- `git diff --check`：通过
- `docker compose config -q`：通过
- `make loadout-check COMPANY=v7-three-layer-e2e-20260714 ACCOUNT=foundagent`：通过

测试覆盖包括：方法身份绑定与幂等冲突、权限矩阵、单消息 FIFO/成功后 ack、quiet heartbeat、Objective 原子激活、Department 单实例、Goal 状态机、五 Worker、三 Verifier、固定 deadline、同 session 返工、Manager reconcile、取消/超时竞态、无 supersede、无 Department retirement，以及只挂载 `/company` 的边界。

## 9. 未伪装成真实通过的实验项

以下行为已经实现并由确定性测试覆盖，但本次长跑没有专门制造对应真实模型场景：

- 首次 Company / Department Objective 先 FAIL 再修订 PASS；本次三个初始 Objective 均一次 PASS。
- 临时缩短系统 timeout 后真实等待 Goal 进入 `failed_time`；默认 10800 秒、deadline 不可重置和晚 verdict no-op 已测试。
- 同时形成至少 4 条真实 review 以肉眼观测“3 个运行 + 第 4 个排队”；本次真实峰值为 2。

这些是后续压力/故障注入实验，不是当前主路径实现缺口。

## 10. 旧 Company 隔离

启动前与停止后使用同一算法复核，既有 Company 聚合指纹完全一致：

| Company | 启动前 | 停止后 |
|---|---|---|
| `firsttest` | `6fb58c7d66128845b7c34195711abc8eadfb7ff6` | `6fb58c7d66128845b7c34195711abc8eadfb7ff6` |
| `foundagent` | `392e514ea7f9429d2edc2cf544a749e6fa80448a` | `392e514ea7f9429d2edc2cf544a749e6fa80448a` |
| `fourthtest` | `fd1ea7adcbcc813afa7429f0755e2d75c72dc3cf` | `fd1ea7adcbcc813afa7429f0755e2d75c72dc3cf` |
| `secondtest` | `92252c922e7b64626c5efce434f507468d87d2a1` | `92252c922e7b64626c5efce434f507468d87d2a1` |
| `thirdtest` | `0d2900f7e525a9502320a2f46fe9918d07e112b2` | `0d2900f7e525a9502320a2f46fe9918d07e112b2` |

V7 使用独立目录 `state/v7-three-layer-e2e-20260714/`。没有状态迁移步骤，也没有修改旧 Company 的测试数据来适配新架构。
