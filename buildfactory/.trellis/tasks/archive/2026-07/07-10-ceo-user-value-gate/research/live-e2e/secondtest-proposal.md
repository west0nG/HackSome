# 候选公司 Objective：小团队 MCP 风险扫描 CLI

公司拟继续把 MCP Risk Inventory 作为独立经营方向：服务 5–30 人的软件团队和安全意识较强的开发者，在新增或修改 Claude Code、Cursor、Cline、Copilot、Gemini CLI 等工具的 MCP 配置时，用本地 CLI 或 GitHub Action 扫描本地命令、未固定版本的包执行、secret-like env、宽文件权限、远程 URL、schema drift 和未知 registry。

用户当前可以逐项人工查看配置、依赖客户端或平台自带控制、使用通用安全扫描，或者不处理。候选价值是把这些检查集中成一份可读报告和 CI policy gate；触发预计发生在团队新增或修改 MCP 配置时。

最小交付已经存在：公开 npm CLI、GitHub Action、示例 policy、公开 demo、反馈 issue。第一批用户入口拟继续使用 GitHub 安全/开发工具目录、MCP 社区和产品 issue。完整运行事实与信号只引用下面的证据文件，评审者应亲自打开，不要把本提案中的概括当成证据：

`/Users/weston/dev/BuildFactory/.trellis/tasks/07-10-ceo-user-value-gate/research/live-e2e/secondtest-evidence.md`

已知假设是：公开安全风险会转化成小团队持续扫描、配置提交、PR gate 接入或付费团队治理；已知未知项是用户触发频率、人工检查成本、切换理由和大组织是否需要远重于 CLI 的能力。若真实团队愿意提供配置、在多次变更中保留扫描、接入 PR gate 或付费，则继续；若没有这些行为，则调整或终止。
