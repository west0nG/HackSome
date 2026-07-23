# 技术设计：将 submit_result 简化为纯完成声明

## 1. 设计目标

把 Worker 的完成声明、业务成果的存放位置和 Verifier 的验收取证彻底解耦：

- Worker 只通过空 payload 的 `submit_result` 表示“我认为当前 Goal 已完成”；
- Hub 只把这次调用当作状态机事件，不接收 Worker 自述或证据索引；
- Verifier 根据 Goal intent、私有 acceptance、完整账户包和自身工具独立取证；
- `/company` 继续是可选的共享公司状态，不再是所有 Goal 的强制交付介质。

本任务保持单一 Trellis 任务，不拆父子任务：API、Prompt、Verifier runtime 和规范共同定义同一个原子产品契约，任一部分单独交付都会留下互相矛盾的运行语义。

## 2. 边界与不变量

### 2.1 保持不变

- 只有绑定到当前 Goal 的 Worker 能调用 `submit_result`；
- MethodAdapter 的 actor 绑定、method 白名单、稳定 `request_id` 和幂等回放保持不变；
- Goal 主状态机仍为 `running -> reported -> verifying`，PASS/FAIL 后续路径不变；
- Worker 在等待 verdict 时继续占用 lifecycle，FAIL 后续接同一 Worker/session/deadline；
- Verifier 的 `/company` 仍为只读，Hub 方法仍只有当前 review 的 `submit_verdict`；
- Verifier 仍为一次性实例，不保存跨 review 会话；
- Worker 与 Verifier 的并发、FIFO、deadline、cancel、stop ack 语义不变。

### 2.2 新边界

- `submit_result` 的业务 payload 必须严格为空对象；任何额外字段都由 `_payload_fields` 拒绝；
- Worker 不再向控制面提交 `summary`、`company_refs`、URL、正文或证据说明；
- Goal ledger 和公开 projection 不再拥有 `latest_summary`、`company_refs` 结果字段；
- `goal_result` review payload 只由 Hub 已知事实组成，不包含 Worker 为验收组织的内容；
- Verifier 获得与 Worker 相同的完整账户包，但不获得 Worker 执行型 Skills。

## 3. 调用与数据流

### 3.1 Worker 完成声明

Agent-facing 调用：

```bash
python3 -m orchestration.control_client submit_result \
  --request-id 'result-<goal-id>-<meaningful-revision>'
```

`control_client` 已默认把缺失的 `--json` 解析为 `{}`，无需新增 CLI 特例。

Hub 处理顺序：

1. `_payload_fields(payload)` 确保业务 payload 无字段；
2. 先执行 deadline sweep；
3. 根据 harness 绑定的 `actor.goal_id` 和 `actor.actor_id` 校验 Goal/Worker 所有权；
4. Scheduler 只记录状态、session token 和幂等 operation ID；
5. Hub 创建 `goal_result` review，并推动 Goal 进入 `verifying`；
6. 调度一次性 Verifier。

### 3.2 Review payload

新的 Goal review payload：

```json
{
  "goal_id": "goal-...",
  "owner_department": "builder",
  "intent": "...",
  "acceptance": "... or null",
  "deadline_at": 1234567890.0
}
```

不包含：

```text
summary
company_refs
worker_message
result_url
result_body
```

`acceptance` 继续只对 Verifier 公开，不进入 Worker Prompt 或 Worker command。

### 3.3 Verifier 独立取证

Goal Verifier Prompt 应明确：

1. Worker 只声明“完成”，没有提供摘要或证据索引；
2. Verifier 必须从 intent 和 acceptance 推导验收方法；
3. 可以按需检查只读 `/company`、公开网络和使用账户登录后的外部状态；
4. 缺少 `/company` 记录本身不是 FAIL 理由；
5. 无法独立建立完成事实、证据不可访问、相互矛盾或不满足 acceptance 时 FAIL closed；
6. 只能检查，不能执行、修复、发布或修改外部状态；
7. verdict reason 需要说明实际检查了什么以及为什么 PASS/FAIL。

## 4. Verifier 账户包注入

`DockerVerifierBackend.create` 与 Worker 对齐：

- `materialize_ephemeral_home(... include_account_secrets=True)`；
- 若 `accounts/<id>/secrets.env` 存在，加入 Docker `--env-file`；
- 若账户目录存在，加入只读挂载 `<account_dir>:/account:ro`；
- 不把 secret 值复制到 Prompt、review payload、ledger 或 telemetry；
- 保持独立 ephemeral home，避免 Verifier 修改共享 account 文件或复用 Worker session。

Verifier AgentSpec 的 Skills 列表不变：

```text
company-state-readonly
company-methods
submit-verdict
```

浏览器和桌面 MCP 保持不变。完整账户包可能在外部服务上具有写权限；V7 当前是合作型防误用边界，不是恶意容器安全模型，因此第一版通过 charter、一次性实例和完整日志约束只读行为。

## 5. Ledger 与兼容处理

### 5.1 新 Goal

新建 Goal 不再写入：

```text
latest_summary
company_refs
```

Scheduler 的 `submit_result` 签名删除 `summary`、`company_refs` 参数和路径校验辅助函数。

### 5.2 已存在的 Goal JSON

第一版不提供旧 Company 迁移命令。代码必须能读取包含旧字段的 Goal JSON，但不再消费或投影这些字段。Goal 在新的完成声明路径保存时可移除旧结果字段，避免旧信息继续表现成活跃契约。

相同 `request_id` 的历史 MethodAdapter response 继续按原始请求身份回放；不尝试重写已经落盘的历史 response。不同请求走新空 payload 契约。

## 6. Agent-facing 文案调整

### Worker

- Charter：完成当前 Goal；工作需要时可以维护 `/company`，但完成声明不要求任何文件或摘要；
- 初始/返工 Prompt：完成后直接调用 `submit_result`，不要求组织验收材料；
- `submit-work` Skill：展示无 `--json` 的命令，解释它只是完成声明、不是自我验收；
- 仍明确没有 blocked/waiting 终态，未声明完成的 turn 会继续续跑。

### Verifier

- Charter：独立查证，不相信或等待 Worker 自述；可使用账户 secret 检查外部状态；
- Goal Prompt：移除 Worker summary、refs 和“必须持久在 `/company`”rubric；
- 保留 doer≠judge，禁止修复或执行。

### Company State

- 删除“Worker 提交前必须写 `/company`”和结果引用协议；
- 保留“真实、长期共享的业务变化应自然维护”的一般契约；
- 明确没有 Company State 变更也可以合法声明 Goal 完成。

## 7. 错误与竞态

| 条件 | 结果 |
|---|---|
| Worker 发送 `{}` | 正常声明完成并进入 verifying |
| Worker 发送 `summary`、`company_refs` 或其他字段 | `unknown payload fields`，不改变 Goal |
| 非绑定 Worker 调用 | 拒绝，不创建 review |
| Goal 已超时 | deadline 终态优先，完成声明不能复活 Goal |
| 同一 request ID 重放 | 返回原响应，不重复 review |
| Worker turn 结束但未调用 | 同 Worker 自动续跑 |
| Verifier 找不到足够证据 | FAIL，reason 写清缺失或不可访问的事实 |
| Verifier 可登录但外部系统只提供写权限 token | 只检查，不修改；违规属于角色契约违背并由日志审计 |
| 旧 Goal JSON 含 summary/refs | 可读取；新流程不投影、不传给 review |

## 8. 日志、安全与回滚

- 现有 run archive 和 container log 保留；不得打印环境变量或账户文件内容；
- 不新增 secret 到 method audit payload；空 `submit_result` 反而减少 telemetry 中的业务信息；
- 回滚代码时必须同时回滚 Hub/Scheduler、Prompt/Skill、Verifier account 注入、规范和测试，不能恢复半套双协议；
- 若完整账户包导致真实 Verifier 产生非预期外部修改，运行层回滚点是恢复
  `include_account_secrets=False` 并移除 `--env-file`、`/account:ro`，但这会使私有外部验收能力退化，需记录为显式事故处置而非静默降级。

## 9. 受影响文件

核心实现：

- `orchestration/scheduler.py`
- `orchestration/company_hub.py`
- `orchestration/worker_manager.py`
- `orchestration/verifier_runtime.py`

Agent 契约：

- `agents/assets/worker-v7-charter.md`
- `agents/assets/verifier-v7-charter.md`
- `agents/assets/skills/submit-work/SKILL.md`
- `agents/assets/skills/company-state/SKILL.md`
- `agents/assets/skills/company-state-readonly/SKILL.md`

活跃规范：

- `.trellis/spec/backend/three-layer-agent-company-contracts.md`
- `.trellis/spec/backend/company-state-contracts.md`
- `.trellis/spec/backend/account-package-contracts.md`

测试入口：

- `orchestration/tests/test_scheduler.py`
- `orchestration/tests/test_company_hub_v7.py`
- `orchestration/tests/test_worker_manager.py`
- `orchestration/tests/test_v7_runtime_services.py`
- `orchestration/tests/test_runtime_materialization.py`
- `orchestration/tests/test_v7_mount_boundaries.py`
- `agent/tests/test_objective_skills.py`
- `agent/tests/test_company_state_skill.py`
- 其他通过搜索发现仍断言旧 result payload 的测试
