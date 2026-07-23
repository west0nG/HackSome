# 真实 resident verifier E2E 记录

日期：2026-07-10

## 运行边界

- 两例都通过生产 `AgentSpec → Codex runtime → review-objective → objective verdict` 链路执行，模型为 `gpt-5.5`，不是 mock 或预写 verdict。
- `/agents`、`/company`、inbox 和 `CODEX_HOME` 均位于单次运行的临时目录；只把请求、Codex JSONL、结果和 review 保存到本目录。
- 每份承重证据含 proposal 中没有的 sentinel。结果必须同时满足 runtime 成功、确实发出 verdict、verdict 符合预期、review 含 sentinel，才能算通过。
- 夹具启动阶段有两次人工中止的调试运行，均未形成 verdict 或结果文件，不计入以下 E2E。

## Case 1：secondtest 通用 MCP 风险扫描产品

- 会话：`019f4acb-201e-7870-ae33-7b7d11727ffd`
- 输入：`secondtest-proposal.md`、`secondtest-short.md`、`secondtest-evidence.md`
- 原始输出：`secondtest-run/codex.jsonl`
- 裁决：`FAIL: RESHAPE`
- 四项检查：全部通过。首版 runner 尚未把 checks 字段写进 `result.json`，但完成时打印的四项均为 `true`；`result.json`、`review.md` 和 JSONL 可分别复核 runtime、verdict 与 sentinel `SECONDTEST-7F3C9A`。
- 状态：没有生成 objective、active metadata 或 `/company/product/current-mcp-risk-direction.md`；拒绝 revision 被关闭。

verifier 不只读取摘要，还打开了机会备忘录、产品状态、demo proof、多个 launch/monitoring 记录，并刷新 GitHub/npm 公开面。它确认 npm 包、CLI、GitHub Action 和 release 都真实可用，但 repo、反馈 issue、外部 PR/issue 仍无互动；没有真实团队配置、重复扫描、PR gate、付费或委托行为。

裁决明确区分“产品能跑”和“用户会用”：小团队可能在低频配置变化时人工查看或依赖现有平台/通用扫描；真正有持续控制压力的组织需要集中 inventory、policy、approval 和 audit，薄 CLI 又不足。最小改变结论的动作是让一支真实团队用脱敏配置完成一次工作流试用，并出现保留到下一次变更、PR gate、反馈、委托或付费等有成本行为。

注意：本次模型自行用 raw-byte SHA-256 比较 staged Markdown 与 manifest，因末尾规范化换行产生了“哈希不一致”的假警报，但 verdict 命令按正式 stripped-text 语义完成了权威校验并成功记录。E2E 后已把该语义加入生产 review request、review-objective Skill 和回归测试，避免未来误杀。

## Case 2：一次性人工 MCP 配置审计服务

- 会话：`019f4ad0-9ec2-7ed3-a7af-eeb68d39eb68`
- 输入：`service-proposal.md`、`service-short.md`、`service-evidence.md`
- 原始输出：`service-run/codex.jsonl`
- 裁决：`FAIL: RESHAPE`
- 四项检查：全部通过，且已持久化在 `service-run/result.json`；sentinel 为 `SERVICE-2C8D41`。
- 状态：没有生成 objective、active metadata 或 `/company/services/current-mcp-audit-service.md`；拒绝 revision 被关闭。

verifier 明确认定这是一项可以直接人工交付的服务，不需要先构建软件，现有 CLI 只能作为辅助工具。它没有用下载量或 DAU 机械评审，而是检查真实配置样本、试审、预约、委托、预售/付款、复核后采用和首批合格用户可达性。由于这些行为全部缺失，且用户可以自己花 30–60 分钟检查、同事 review、使用平台控制或不做，最终给出 `FAIL: RESHAPE`。

## 结论

真实模型行为符合本任务的两条关键合同：可运行、可发布、风险真实和公司自有分发不能替代用户采用；同时，服务等非软件形态按其真实委托与交易行为评审，不被强迫先造软件。两例拒绝都 fail closed，没有污染当前 objective 或 `/company`。
