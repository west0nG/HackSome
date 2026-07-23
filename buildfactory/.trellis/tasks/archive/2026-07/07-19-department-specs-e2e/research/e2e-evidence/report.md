# Department 单一声明真实 E2E 报告

## 结论

本次针对“删除 `agents/departments/catalog.yaml`、由四个 Department YAML 同时承载公开元数据与
内部 AgentSpec”的窄 E2E **通过**。

真实链路已经走通：

```text
四个 Department YAML
  → Hub 公开投影
  → CEO-bound list/create
  → Verifier Manager + 临时 CUA Verifier + 真实 Codex
  → Department Provisioner
  → 真实 Builder resident 容器
```

CEO 实际只能看到四项 `id/name/description`；使用 `builder` ID 发起创建后，第一次真实审核因
fixture 的 `/company` 缺少 Company Objective 可见依据而 FAIL。补齐生产 Company State 后，按方案
允许的一次重试由新的真实 Verifier PASS，Builder 随后进入 active/running，并从合并后的
`builder.yaml` 正确解析和启动。没有手写 PASS，也没有把第一次 FAIL 隐藏成通过。

## 验收结果

| 验收项 | 结果 | 证据 |
|---|---|---|
| 全新 Company、无旧 state/container/network | PASS | `preflight.md` |
| CEO 只见四个固定选项 | PASS | `list-options.json` |
| 每项严格只有 `id/name/description` | PASS | `list-options-assertion.json` |
| 公开值逐项匹配四个 YAML | PASS | `list-options-assertion.json` |
| 无 model/Skills/MCP/charter/heartbeat 等内部字段 | PASS | `list-options-assertion.json` |
| CEO 使用公开 `builder` ID 创建 | PASS | `create-department.json`、`create-department-retry.json` |
| Builder Objective 经过真实临时 Verifier + Codex | PASS | `review-first-fail.json`、`review-final.json` |
| PASS 后真实 Provisioner 启动 Builder | PASS | `department-final.json` |
| Builder running 且 labels/env/mount 正确 | PASS | `builder-inspect.json` |
| 容器内只有四个 Department YAML、无 catalog | PASS | `builder-runtime.json` |
| AgentSpec 与 resident loop 从单一 YAML 正确启动 | PASS | `builder-runtime.json`、`service-logs.txt` |
| 专用容器、network、symlink 全部清理 | PASS | `cleanup.md` |

## 真实审核过程

### 认证基础设施诊断

最初六次 instance 没有形成业务 verdict：

1. 工作树的 `accounts/foundagent` 是指向主仓库的绝对 symlink；manager 容器只挂了工作树，无法
   解析 symlink 目标，因此前两次 home 没有 `auth.json`，Codex 返回 401。
2. 给 manager 增加 account-target 只读 bridge 后，主仓库 seed 已过期，Codex 报告 refresh token
   已被使用。
3. 未覆盖主仓库 account 文件，而是把当前 Codex 会话的 `auth.json` 临时、只读地 bind 到 manager
   看到的 seed 路径。第 7 个 instance 获得有效 seed 并完成第一次真实模型审核。

这些是同一 review 的系统级 instance 恢复，不是 Objective 文案重试。证据只记录文件存在、大小、
错误类别与 instance 次数，没有读取或保存 credential 内容。

### 第一次真实 verdict：FAIL

Verifier 认可 Objective 是长期、可衡量的 Builder 职责，但 `/company` 为空，无法验证它是否与
Company Objective 对齐，因此 fail closed。随后用真实 `company_state_kit` 写入
`strategy/company-objective.md`，生成 `MAP.md`，再使用新的 CEO request ID 提交唯一一次文案重试。

### 第二次真实 verdict：PASS

新的 Verifier instance 读取 `/company/strategy/company-objective.md` 后确认：Builder Objective 与
Company 方向直接对齐，职责是长期重复能力而不是一次性 Goal，数周内有可观测指标，并保留不承诺
法律合规、认证或诉讼保护的边界。

Verifier 的 `submit_verdict` 已被 Hub 接受并持久化为 PASS；随后 manager 停止一次性容器时，Codex
进程在写出 `turn.completed` 前收到终止信号，因此 run archive 的 runtime `ok` 为 false/rc 137。
这里以受控方法已经写入的 review verdict 为业务事实，不把自然语言或进程退出码当作 PASS。

## Builder 运行时结果

- Registry：`builder / active / heartbeat=900`。
- 容器：`department-specs-e2e-20260719-builder / running`。
- 镜像：`foundagent/cua-agent:latest` 的本地 image ID
  `sha256:eb91cf6ae9ec466cfd13d4868361b2c63d490b260e223810ee023be41164d65b`。
- Control plane 从当前工作树重新构建；初始 Hub 使用 image ID
  `sha256:b3f2416d5493b6a643b0d74823dd1a53c45b370ff2a693e5d199f9cc191222b9`，认证 bridge
  重建后的 managers 使用 image ID
  `sha256:e034aec04b491d463399640063b492bcdefc9d7a3e02fd72803ee285cc9f9c89`；产品代码均由当前工作树只读挂载。
- `AGENT_SPEC`、`AGENT_CHARTER`、`AGENT_HEARTBEAT_SECS` 精确匹配预期。
- `agents/` 以只读方式从当前工作树挂载。
- 容器内 `AgentSpec` 解析为 `builder / codex / gpt-5.6-sol / xhigh`，MCP 为 `builder.json`，
  八个 Skill 与 YAML 一致。
- 日志包含完整 `resident_loadout` 和 `[agent_loop] boot`，使用正确 charter、MCP、model、effort、
  Hub objective/inbox、fresh session 与 proactive idle。

Builder 启动后收到了系统 event，但它是在 provisioner 获得 current-auth 临时 bridge 之前创建的，
其第一次业务 wake 使用旧 account seed 并进入可靠重试。PRD 明确不要求等待 Builder 完成经营 Goal；
因此本报告只确认 resident 容器和单一 YAML 配置启动，不宣称 Builder 的业务模型 wake 成功。

## 明确未验证

- Company Objective 的真实模型审核：它是确定性 fixture，`objective-fixture.json` 明确记录
  `real_model_reviewed=false`。
- Builder 的业务 Goal、Goal result、Worker、长期 heartbeat 与 session 恢复。
- 其他三个 Department 的真实 provision；它们的公开投影和 YAML 值已在同一次 Hub list 中验证。

## 清理与可复核状态

专用容器和 network 均已删除，临时 symlink 与 auth bridge 均已移除。ignored state 保留在
`state/department-specs-e2e-20260719/`，包含真实 review/run archive，供本地复核，但不会提交。
