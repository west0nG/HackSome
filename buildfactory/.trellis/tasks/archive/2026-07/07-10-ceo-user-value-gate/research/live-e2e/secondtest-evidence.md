# secondtest 真实运行材料摘录

本文件只把 `state/secondtest/company/` 中已经存在的事实压成一次隔离评审可读取的证据面；原始记录仍是下列文件：

- `state/secondtest/company/market/opportunity-memo-software-product-cold-start.md`
- `state/secondtest/company/product/mcp-risk-inventory.md`
- `state/secondtest/company/product/mcp-risk-inventory-demo-proof.md`
- `state/secondtest/company/product/mcp-risk-inventory-launch-signal.md`
- `state/secondtest/company/product/mcp-risk-inventory-v0-1-1-monitoring-signal.md`
- `state/secondtest/company/product/mcp-risk-inventory-npm-refresh-launch-signal.md`
- `state/secondtest/company/product/mcp-risk-inventory-second-wave-launch-signal.md`

## 已确认事实

- MCP 风险主题有公开安全材料支持；原机会备忘录列出了 OWASP、Cloud Security Alliance 和官方 MCP issue 等风险信号。
- 产品真实存在且可用：CLI、GitHub Action、公开 GitHub release、npm `0.1.2`、内部 fixture、公开 demo 和干净安装 smoke test 均已完成。
- 公司做过两轮 GitHub 目录/issue/PR 分发，也创建了反馈 issue。
- 最后一次运行记录中的外部结果是：0 star、0 watcher、0 fork、GitHub traffic 0 view/0 clone、所有已知提交 0 comment/0 review、反馈 issue 0 comment；npm download API 尚未给出可用计数。
- 唯一确认安装仍是公司自己的 clean-prefix smoke install。没有外部团队提交真实配置、保留跨配置使用、接入 PR gate、付费、委托审计或采取其他有成本行为。
- 原始定位是“小型工程团队”；其触发主要发生在新增或修改 MCP 配置时。现有替代包括人工查看配置、已有平台/客户端控制、通用依赖与安全扫描，以及更完整的网关/治理产品。
- 对小团队，单次人工查看可能足够且触发不频繁；对有集中治理、审批、审计和合规预算的大组织，一个薄 CLI 又缺少资产盘点、统一策略、审批、例外和审计链。

E2E-SOURCE-SENTINEL: SECONDTEST-7F3C9A
