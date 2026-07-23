# 双 Runtime 隔离验证

验证时间：2026-07-11（Asia/Shanghai）

## 结论

Claude Code 与 Codex 都只发现角色 YAML 声明的顶层 Foundagent skill；Growth 为 13 项、CEO 为 10 项。`qu-ai-wei`、`frontend-design`、`image`、`codex-imagegen` 四个 vendored 内部名称均未出现。八个高风险路由场景在两边都是 8/8 命中预期 host，没有命中指定的错误 sibling。

## 环境与隔离

- 镜像：`foundagent/cua-agent:latest`，image id `d24a6a9c59bd`。
- 固定 CLI：Claude Code `2.1.202`；Codex `0.142.5`。
- 路由模型：Claude `claude-opus-4-8` / effort `low`；Codex `gpt-5.5` / reasoning effort `low`。这是只测 description 路由的低成本配置。
- 每次运行都在 `docker run --rm` 的一次性容器中，从真实 `AgentSpec.skill_paths()` 经对应 runtime adapter 物化 Growth 或 CEO loadout；home 位于容器 `/tmp`，容器退出即删除。
- 为隔离分类请求，动态验证关闭 hooks/MCP 物化；Claude 只暴露 `Skill` 工具但没有发生 tool use，Codex 使用 `read-only` sandbox + `approval_policy=never` 且没有发生 command/tool item。
- 没有修改、重启或挂载写入 `firsttest`、`secondtest`、`thirdtest`，也没有执行邮件、社媒、浏览器、建站或其他外部动作。

## 实际发现集合

| Role | Claude Code `init.skills` 中的 Foundagent 子集 | Codex 首轮 `skills_instructions` 驱动的返回集合 | 一致性 |
|---|---|---|---|
| Growth | 13 | 13 | 完全一致 |
| CEO | 10 | 10 | 完全一致 |

Growth（两边相同）：

```text
check-email, claim-mailbox, company-state, de-ai-ify, deploy-site,
design-asset, gen-image, mine-customer-voice, operate-twitter,
provision-ga4, receive-goal, send-email, visual-iterate
```

CEO（两边相同）：

```text
check-email, claim-mailbox, create-role, deploy-site, find-opportunity,
provision-ga4, send-email, send-goal, set-objective, when-idle
```

Claude `init.skills` 还会列 CLI 自带技能；上面只取由本次 role loadout 物化的 Foundagent 子集。Codex 的首条 `agent_message` 在没有读取 skill 正文或调用命令的情况下返回了同一集合。

运行标识：

- Claude Growth session：`434bb9f8-fd98-4b77-9438-210175296c36`
- Claude CEO session：`6c199697-d376-4cd5-8b62-cefcc8291a10`
- Codex Growth thread：`019f4f47-5a9f-7d82-9a12-0fa2e71476fa`
- Codex CEO thread：`019f4f47-f519-7662-b752-3144109c7d8f`

## 高风险路由矩阵

| 场景 | 预期 host | Claude Code | Codex | 结果 |
|---|---|---|---|---|
| G1 新 signup 需要可收信身份，尚未等待邮件 | `claim-mailbox` | `claim-mailbox` | `claim-mailbox` | PASS |
| G2 signup 已提交，等待验证码/魔法链接 | `check-email` | `check-email` | `check-email` | PASS |
| G3 文字与排版主导的小红书卡片 | `design-asset` | `design-asset` | `design-asset` | PASS |
| G4 无排版文字的独立 hero 插画 | `gen-image` | `gen-image` | `gen-image` | PASS |
| G5 CEO 尚无候选，只研究证据支持的方向 | `find-opportunity` | `find-opportunity` | `find-opportunity` | PASS |
| G6 CEO 已有候选与证据，要替换 standing objective | `set-objective` | `set-objective` | `set-objective` | PASS |
| G7 即将发布的中文文案去 AI 味 | `de-ai-ify` | `de-ai-ify` | `de-ai-ify` | PASS |
| G8 审计公开 X profile，排除私信与邮件 | `operate-twitter` | `operate-twitter` | `operate-twitter` | PASS |

两边都只返回一个 primary skill；没有辅助 skill 加载，也没有错误 sibling。

## 非致命偏差

Codex 两次运行都因为 `CODEX_HOME` 位于 `/tmp` 而警告不创建 PATH helper，并在捕获包含多行评测 prompt 的 shell snapshot 时报告一次 `Unterminated quoted string`。这两条都发生在模型调用前，不影响 skill catalog 注入；两次运行均产生预期的首条 `agent_message` 并以 `turn.completed` 结束。没有把该警告误判为路由失败。
