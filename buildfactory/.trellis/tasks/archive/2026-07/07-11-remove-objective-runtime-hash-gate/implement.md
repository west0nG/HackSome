# 实施计划：移除 Objective 生效后校验

## 实施顺序

1. [x] 进入 Phase 2 前加载 `trellis-before-dev`，读取 backend spec 中 resident agent、company-state 和错误处理相关约束。
2. [x] 修改 `orchestration/objective.py`：
   - 将 `objective_read_ready` 收窄为事务恢复兼容入口；
   - 将 `_load_active` 收窄为 schema/role/path/revision 结构读取；
   - 删除 `_apply_ceo_pass` 对旧短版哈希、旧全文哈希、旧摘要和旧 leaf 存在性的前置阻断；
   - 保留 staged bundle 哈希、revision、身份门、路径所有权、事务和回滚。
3. [x] 修改 `orchestration/agent_loop.py` 的注释和异常措辞，明确每次唤醒只依赖事务恢复与当前短版读取。
4. [x] 更新 `orchestration/tests/test_objective.py`：
   - active short/full/summary/hash 字段漂移不阻断 show；
   - full leaf 缺失不阻断 show；
   - 漂移或缺失状态可被新 PASS 正常替换；
   - staged 篡改和旧 revision 仍被拒绝；
   - 事务恢复/回滚和路径所有权保持。
5. [x] 更新 `orchestration/tests/test_agent_loop.py`，证明当前短版直接注入且 company drift 不再产生 unavailable。
6. [x] 更新 `.trellis/spec/backend/resident-agent-contracts.md`，删除运行时哈希/摘要阻断契约，保留审核期完整性和事务恢复说明。
7. [x] 做静态搜索，确认现行代码、测试和 spec 不再宣称 active 内容失配会阻止注入；归档任务和 thirdtest 观察记录保持原样。

## 验证命令

```bash
./.venv-cua/bin/pytest -q \
  orchestration/tests/test_objective.py \
  orchestration/tests/test_agent_loop.py

./.venv-cua/bin/pytest -q \
  agent/tests/test_objective_skills.py \
  agent/tests/test_resident_loadout.py

./.venv-cua/bin/pytest -q \
  agent/tests company_state_kit/tests observatory/tests \
  orchestration/tests peripheral/tests

make loadout-check COMPANY=thirdtest

rg -n "objective_read_ready|no longer matches its approval|verifies the short/full hashes|active hash mismatch" \
  orchestration agent .trellis/spec \
  --glob '!**/archive/**'
```

`rg` 可以保留 `objective_read_ready` 兼容函数和恢复测试命中，但不得再出现“active 内容失配阻断唤醒”的现行契约。

仓库根目录不带路径运行 `pytest -q` 会继续进入 `state/*/sessions/*/plugins/cache`，其中不同插件含同名测试模块，因而在测试收集阶段报重复模块；这不是产品代码失败。全量回归必须显式限定上面五个项目测试目录。本次结果为 722 passed；Objective/Agent loop 定向测试为 108 passed，loadout/skill 合同测试为 24 passed，`make loadout-check COMPANY=thirdtest` 通过。

## 高风险文件与检查点

- `orchestration/objective.py`：不能误删 staged proposal 哈希检查或事务恢复。
- `orchestration/agent_loop.py`：不能让事务恢复异常击穿常驻循环；恢复失败仍须降级为不注入并打印明确警告。
- `orchestration/tests/test_objective.py`：新测试必须验证允许 active 漂移，而不是通过删除断言形成空测试；同时保留反例证明 staged 漂移仍被拒绝。
- `.trellis/spec/backend/resident-agent-contracts.md`：只更新现行契约，不改写归档设计历史。
- `state/thirdtest/**`：实施和自动化测试期间只读；只有所有验证通过后的受控发布步骤可以重启 CEO service，仍不得直接修改业务状态文件。

## 发布步骤

1. [x] 代码和全量回归全部通过后，确认 `thirdtest-ceo` 没有正在运行的 Claude/Codex child wake。
2. [x] 只执行 `COMPANY=thirdtest ACCOUNT=foundagent docker compose restart ceo`，不重启其他 resident、Hub 或外围服务。
3. [x] 只读检查 CEO 日志与下一次 wake，确认出现 `objective: injected ... chars` 且不再出现 active hash/summary mismatch；确认 session id、ledger、inbox、company 和 Objective 文件未丢失。

## 发布验证记录

- 2026-07-11 03:29:08Z 只重启 `thirdtest-ceo`；容器 ID 保持不变，只有 CEO 的启动时间更新，其余九个服务的容器 ID 和启动时间均未变化。
- 重启前后 CEO session、短版、active metadata 和完整正文的 SHA-256 完全一致；ledger/inbox/company 文件数量分别保持 25/22/71，未发生丢失。
- 现场旧失配仍然存在：批准时全文哈希为 `ca891bbe...`，当前全文哈希为 `5c6126cd...`；新容器内直接读取返回 `ready=True`、1472 字符，证明不是通过改写状态绕过问题。
- 2026-07-11 03:44 自然 heartbeat 日志显示 `objective: injected 1472 chars`，随后原 session `dd70a6f8-e6d6-4dc2-8107-fc0f0a35b441` 正常完成；新进程日志未出现 active hash/summary mismatch。

## 回滚点

- 代码、测试和 spec 作为一组回滚；没有状态迁移。
- 若全量测试暴露依赖旧阻断行为，回到规划核对该依赖究竟属于提案期保护还是生效后保护，不能为了过测恢复全文哈希门。
