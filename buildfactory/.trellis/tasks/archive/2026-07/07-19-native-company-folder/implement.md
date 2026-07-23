# 实施计划：原生 Company 文件夹

## 实施前提

- 用户审阅并批准 `prd.md`、`design.md` 和本计划。
- 批准后运行 `task.py start`，再按 inline 工作流加载 `trellis-before-dev`；规划阶段不修改产品代码。
- 实施期间不修改或清理 `state/*/company/`。

## 1. 建立原生 Agent 契约

- [x] 重写 `agents/assets/skills/company-state/SKILL.md`：定义浅层发现、限定搜索、按需读取、写前查重、描述性命名、主题组织、当前状态维护和谨慎重组/删除。
- [x] 重写 `agents/assets/skills/company-state-readonly/SKILL.md`：Verifier 直接打开精确引用并渐进查证，保持只读。
- [x] 修改 `orchestration/agent_loop.py` 的 COMPANY ENTRY，取消 `MAP.md` 入口并提示原生渐进探索。
- [x] 修改 `agents/assets/skills/operate-twitter/SKILL.md`，删除 `company.py read/write` 和导航文件专属规则，复用原生 Company 访问契约。

验证点：Agent-facing 当前文档不再要求旧 CLI 或导航不变量，同时 Company 与控制面边界仍明确。

## 2. 删除旧管理层与运行时接线

- [x] 删除整个 `company_state_kit/`。
- [x] 删除 `docker-compose.yml` 中两个 `company_state_kit` 挂载和仅服务旧 CLI 的 `COMPANY_ROOT`。
- [x] 删除 `orchestration/department_provisioner.py` 中动态 Department 的两个 toolkit 挂载和旧环境变量。
- [x] 删除 `orchestration/worker_manager.py` 中 Worker toolkit 挂载和旧环境变量/turn extra env。
- [x] 删除 `orchestration/verifier_runtime.py` 中旧环境变量/turn extra env。

验证点：所有 runtime 仍挂载正确的 `/company`，但不再暴露旧 toolkit 或无消费者环境变量。

## 3. 更新自动化测试

- [x] 更新 `orchestration/tests/test_agent_loop_v7.py` 的 Company 入口断言。
- [x] 更新 `agent/tests/test_operate_twitter_skill.py`，固定原生发现/持久化并拒绝旧协议。
- [x] 新增 `agent/tests/test_company_state_skill.py`，固定共享 Skill 的渐进读取、维护和只读边界。
- [x] 更新 `orchestration/tests/test_v7_mount_boundaries.py`，断言动态 runtime 没有 toolkit 挂载且 RW/RO 边界不变。
- [x] 更新 `orchestration/tests/test_compose_accounts.py`，断言固定 CEO runtime 没有 toolkit 挂载且 `/company` 仍为原生入口。
- [x] 检查其他受影响的 runtime、materialization 和 skill tests，按新契约调整，不把旧 CLI 测试改造成迁移测试。

验证点：测试覆盖新的系统边界，而不是通过另一层 Python helper 模拟原生文件系统。

## 4. 更新当前文档与规范

- [x] 重写 `.trellis/spec/backend/company-state-contracts.md`。
- [x] 更新 `.trellis/spec/backend/index.md` 的 Company State 描述。
- [x] 更新 `.trellis/spec/backend/three-layer-agent-company-contracts.md` 的旧 read/tree/write 段落。
- [x] 更新 `README.md` 的架构速览、深入阅读说明和测试命令。
- [x] 搜索其他当前文档中的旧入口；历史 Trellis 任务保留为历史证据，不回写成新事实。

## 5. 删除残留与完整验证

- [x] 对有效产品代码、Skill、Prompt、README、当前规范和测试执行残留搜索：

  ```bash
  rg -n "company_state_kit|/opt/company_state_kit|company\.py|COMPANY_ROOT|MAP\.md|OVERVIEW\.md|\.company\.lock" \
    agent agents orchestration docker-compose.yml README.md .trellis/spec
  ```

  任何命中必须逐项确认：旧协议依赖必须清理；专门防止旧协议回归的负向测试或明确说明其已取消的当前规范可以保留。历史 task artifact 不作为当前产品残留。

- [x] 运行聚焦测试：

  ```bash
  .venv-cua/bin/python -m pytest \
    agent/tests/test_company_state_skill.py \
    agent/tests/test_operate_twitter_skill.py \
    orchestration/tests/test_agent_loop_v7.py \
    orchestration/tests/test_v7_mount_boundaries.py \
    orchestration/tests/test_compose_accounts.py -q
  ```

- [x] 运行完整相关测试：

  ```bash
  .venv-cua/bin/python -m pytest agent/tests orchestration/tests peripheral/tests -q
  ```

- [x] 校验 Compose：

  ```bash
  COMPANY=foundagent ACCOUNT=foundagent docker compose config >/dev/null
  ```

- [x] 检查 Git diff，确认没有 `state/` 运行数据、迁移工具、遥测功能或无关改动。

## 6. 规范同步、提交与回退点

- [x] 按 Trellis Phase 3.3 确认当前规范已经与实现一致。
- [x] 提交前再次运行质量门并记录验证结果。
- [x] 创建一个聚焦提交，包含原生契约、旧层删除、测试和规范同步。
- [x] 质量门全部通过，无需执行回退；若后续真实实验失败，仍只回退代码提交，不操作 `state/`。

## 验证记录

- 聚焦契约测试：33 passed。
- 全量 Agent / Orchestration / Peripheral 测试：402 passed。
- `.venv-cua/bin/python -m compileall -q agent orchestration peripheral`：通过。
- `COMPANY=foundagent ACCOUNT=foundagent docker compose config -q`：通过。
- 旧协议残留搜索：只剩明确防回归的负向断言。
- `state/` diff：空；未新增迁移或遥测实现。

## 完成定义

- PRD 的 AC1–AC11 全部有代码、文档或测试证据。
- `/company` 的 RW/RO 与控制面隔离边界保持不变。
- Agent-facing 当前契约只教授原生文件访问，不存在旧 CLI 双轨路径。
- 旧 `company_state_kit` 及其运行时接线、测试和当前规范残留全部删除。
- 全量相关测试和 Compose 配置校验通过，工作树不包含运行数据变更。
