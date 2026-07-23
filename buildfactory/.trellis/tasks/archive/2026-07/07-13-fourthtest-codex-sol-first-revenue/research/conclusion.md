# Fourth Test 实验收官记录

收官时间：2026-07-19（Asia/Shanghai）

## 收官结论

用户确认 Fourth Test 已收集足够多的信息，可以结束实验并归档。本任务的完成语义是“实验闭环并保留充分证据”，不是“首款商业指标达成”。

Fourth Test 成功建立并运行了隔离的全 Codex GPT-5.6-Sol 公司环境，验证了真实冷启动、独立状态、Initial Message、长时间自主经营、Goal 闭环和 Codex Observatory。实验没有收到符合原 PRD 定义的真实外部客户 Stripe 首款，因此首款验收项明确记为未达成，不做成功回填。

## 证据规模

- CEO Inbox 第一条消息保留唯一 ID `fourthtest-initial-first-stripe-revenue-v1`，正文与 PRD 一致。
- Ledger 保留 39 个 Goal：32 `done`、7 `killed`，归档审计时无非终态 Goal。
- 五个角色共保留 347 条 wake telemetry。
- Codex `gpt-5.6-luna / high` Observatory 保留 39 份 Goal 尸检和 4 份 Company review；报告头与 daemon 日志均记录 provider、model、effort。
- 独立 worktree、`state/fourthtest/`、Compose project、Host 入口、双邮件 bucket/poller 设计和 Fourth Test Observatory 均留下可复核状态与日志。
- 公司真实探索了多条产品、买家、渠道、Objective 审核和 Stripe 收款路径，并暴露了 Objective gate、渠道可达性、Verifier 解析、运行流水闭合和账务安全处置等有效实验信息。

## 原验收标准判读

- 隔离运行、模型配置、Initial Message、账号包/Stripe 能力、Observatory 与大量 Goal 运行证据均已形成。
- 第一笔合格 Stripe 付款：**未达成**。最终 Company State 与 provider 核验记录多次确认相关 Checkout Session 均为 unpaid，并且为 0 PaymentIntent、0 Charge；不能把测试、自访问或未付款 Session 解释为收入。
- 用户于 2026-07-19 明确以“已收集足够多的信息”为实验终止条件并授权归档，因此任务按实验完成归档，而不是按商业成功归档。

## 保留事项

- 归档任务不会删除 `/Users/weston/dev/BuildFactory-fourthtest` worktree、`state/fourthtest/`、Stripe/Vercel/Cloudflare 等外部证据或其他实验资产。
- 审计时没有运行中的 Fourth Test 容器；保留的 worktree 与状态目录继续作为实验取证材料。
- 任何后续对“Codex 公司能否取得真实首款”的新实验都应创建新任务，不应修改本记录来把未达成结果改写为成功。

