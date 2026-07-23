# 实施计划：将 submit_result 简化为纯完成声明

## M1：收口完成声明 API 与 Goal 状态

- [x] 修改 `GoalScheduler.create_goal`：新 Goal 不再创建 `latest_summary`、`company_refs`。
- [x] 修改 `GoalScheduler.submit_result`：删除 `summary`、`company_refs` 参数与校验，只保留所有权、状态、session token、operation ID 和状态迁移。
- [x] 删除不再使用的 Company ref 路径校验辅助代码与 import。
- [x] 对读取到的旧 Goal 字段保持容忍；新完成声明保存时移除旧 `latest_summary`、`company_refs`。
- [x] 修改 Hub `_submit_result`：要求空 payload，调用新 Scheduler 签名。
- [x] 修改 `goal_result` review payload：只保留 goal ID、owner、intent、acceptance、deadline。
- [x] 从 Goal projection 和 owner Department 的 Goal 事件中删除 summary/refs。
- [x] 保持 deadline sweep、幂等回放、worker ownership、review enqueue 和竞态顺序不变。

验证：

```bash
.venv-cua/bin/python -m pytest -q \
  orchestration/tests/test_scheduler.py \
  orchestration/tests/test_company_hub_v7.py
```

## M2：修改 Worker 与 Verifier 的运行语义

- [x] 修改 Worker 初始 Prompt：`/company` 维护改为按业务需要可选；完成后只调用空 payload `submit_result`。
- [x] 修改返工 Prompt：修正真实工作后重新声明完成，不要求摘要或路径。
- [x] 修改 Worker charter 与 `submit-work` Skill，展示无 `--json` 的完成声明命令。
- [x] 修改 Verifier charter：强调独立取证、可检查账户内外部状态、禁止执行或修复。
- [x] 修改 Goal Verifier Prompt：删除 Worker summary/refs 章节与持久化结果 rubric。
- [x] 新 rubric 明确 `/company` 非必需、Verifier 自己决定查证方式、证据不足则 FAIL closed。
- [x] 保持 Verifier AgentSpec 最小 Skill 集不变；增加防回归断言，确保未引入 Worker 执行型 Skills。

验证：

```bash
.venv-cua/bin/python -m pytest -q \
  orchestration/tests/test_worker_manager.py \
  orchestration/tests/test_v7_runtime_services.py \
  agent/tests/test_objective_skills.py \
  agent/tests/test_company_state_skill.py \
  agent/tests/test_skill_catalog.py
```

## M3：给 Verifier 注入完整账户包

- [x] `DockerVerifierBackend.create` 将 `include_account_secrets` 改为 `True`。
- [x] 与 Worker 对齐：存在 `secrets.env` 时加入 Docker `--env-file`。
- [x] 与 Worker 对齐：账户目录存在时只读挂载到 `/account`。
- [x] 不新增共享 session、可写 account mount 或 secret 日志。
- [x] 更新 runtime materialization 与 mount boundary 测试：Verifier 有账户包、`/company` 仍只读、内部编排目录仍不可见。
- [x] 保留 Verifier 现有浏览器/桌面 MCP 和最小 Skill 集。

验证：

```bash
.venv-cua/bin/python -m pytest -q \
  orchestration/tests/test_runtime_materialization.py \
  orchestration/tests/test_v7_mount_boundaries.py \
  orchestration/tests/test_v7_runtime_services.py \
  agent/tests/test_mcp_assets.py \
  agent/tests/test_skill_catalog.py
```

## M4：统一规范与删除旧契约

- [x] 更新 V7 三层公司契约：完成声明、独立验收、可选 Company State、Verifier 完整账户包。
- [x] 更新 Company State 契约：删除 Worker result 引用签名、路径错误矩阵和强制持久化案例。
- [x] 更新账户包契约：Worker 与 Verifier 的完整账户包注入，Verifier 的行为只读边界。
- [x] 全仓搜索并清除把 `summary/company_refs` 作为 submit contract 的活跃代码、测试和规范。
- [x] 不修改 archive 下的历史任务材料；它们记录当时事实。

搜索门：

```bash
rg -n "latest_summary|company_refs|Worker summary|submit_result" \
  orchestration agent agents .trellis/spec/backend
```

## M5：状态机与负向回归

- [x] 空 payload 正常提交并只创建一条 review。
- [x] 任意额外 result 字段被拒绝且 Goal 不变。
- [x] 相同 request ID 重放不重复 review。
- [x] 非 owner Worker、终态 Goal、deadline 后提交继续被拒绝/终态优先。
- [x] Worker turn 没调用完成声明时仍自动续跑。
- [x] PASS/FAIL、同 Worker返工、新 Verifier、cancel、timeout、stop ack 后补位全部不回归。
- [x] Verifier Prompt 测试同时覆盖：无 Worker 自述、独立外部查证、`/company` 非强制、不得执行修复。
- [x] Verifier 账户注入测试不得读取或输出真实 secret 值，只验证参数、挂载和 materialization 结果。

## M6：完整质量门与审阅

```bash
.venv-cua/bin/python -m compileall -q agent orchestration peripheral
.venv-cua/bin/python -m pytest agent/tests/ orchestration/tests/ peripheral/tests/
docker compose config -q
```

- [x] 检查 `git diff --check`。
- [x] 对照 PRD 的 AC1–AC11 逐项记录验证结果。
- [x] 复核 diff 未包含账户 secret、真实凭据内容或 telemetry 泄漏。
- [x] 复核 Worker 与 Verifier 文案不再互相矛盾。
- [x] 用户批准规划后才运行 `task.py start` 并进入实现。

## 风险与回滚点

- **API 破坏性变化**：空 payload 与旧 payload 不兼容；必须一次性更新代码、Prompt、Skill、测试和规范，不保留长期双协议。
- **旧状态文件**：允许读取旧字段，但新逻辑不再投影或消费；避免专门迁移正在运行的 Company。
- **Verifier 外部写权限**：完整账户包可能具备写权限；charter 与测试必须锁定“只检查、不执行”，运行日志必须完整。
- **验收发现性**：没有 Worker refs 后，Goal intent 与 acceptance 必须足够精确；证据无法独立找到时 FAIL closed，而不是向 Worker索要 summary。
- **回滚一致性**：任何回滚必须按 M1–M4 的整套契约回滚，禁止只恢复 Hub 字段或只移除 Verifier secrets。
