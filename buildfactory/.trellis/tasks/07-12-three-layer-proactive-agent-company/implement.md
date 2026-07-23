# 实施计划：三层主动 Agent Company

依赖顺序：先冻结协议与安全边界，再改可靠唤醒和状态机，然后接入动态 Department、一次性 Worker、Verifier 与防空转，最后只在全新 Company 上做真实运行。整个实现不读取或迁移旧 Company 的状态，也不提供 Department 退役功能。

Company Objective、Department Objective 与每次 Worker 结果提交产生的 review 共用同一个全局 3 并发 FIFO 审核池；每轮结果审核都使用新的 Verifier instance。

## Step -1 — 冻结 V6，建立 V7 基线

- [x] 将当前 `main` 的全部 16 个 tracked modifications 与 `.trellis/tasks/07-13-fourthtest-codex-sol-first-revenue/` 纳入一个完整 V6 snapshot commit；不能只移动 branch pointer。
- [x] 明确排除 V7 规划目录 `.trellis/tasks/07-12-three-layer-proactive-agent-company/`，让它在 V6 snapshot 之后仅随 `main` 进入 V7 开发。
- [x] 在 V6 snapshot commit 上创建分支 `v6`，但保持当前开发分支为 `main`；确认 `git rev-parse v6` 与此时的 `git rev-parse main` 相同。
- [x] 后续所有 V7 实现提交只进入 `main`；`v6` 不再前移。
- [x] 未经用户审核规划和明确开始实现前，不执行本步骤的 commit / branch / checkout。

**回滚点**：创建 V7 提交前，`v6` 与 `main` 指向同一 V6 snapshot；若分支整理有误，只修正引用，不改写或丢弃工作树内容。

## Step 0 — 冻结第一版契约与测试基线

- [x] 把 PRD 的核心不变量转成测试用例名称与 fixture：固定内核、零 Department 冷启动、四模板单实例、全局 5 Worker、独立最多 3 个临时 Verifier、严格 FIFO、一次一条消息、成功后 ack、固定 deadline、无 supersede、无 Department 退役。
- [x] 为新架构定义独立测试 Company ID 和临时状态根；所有测试都断言没有读取旧 Company 的 state、Inbox、Ledger、Notes、Objective 或 session。
- [x] 记录当前全量测试结果，只把本任务引入的回归作为阻断；不修改旧 test 的运行数据来“适配”新状态机。
- [x] 验证：现有单元测试基线可复现，任务新增 fixture 不指向任何旧 Company 目录。

**回滚点**：本步只有测试与契约，没有运行时行为变化。

## Step 1 — 确定性方法适配层与状态隔离

- [x] 新增确定性 method adapter，提供版本化请求信封、幂等 `request_id`、响应错误码和 method dispatch；Agent 只看到逻辑工具，不看到传输实现。
- [x] 不挂载 `/shared/control/hub.sock`，也不向 Agent 发放随机 capability token。orchestrator 启动 tool adapter 时绑定固定 actor，方法参数不接受调用方自报 `from`。
- [x] 定义 CEO、Department、Worker、Verifier 的方法白名单和对象归属校验；mutation 必须由 Hub 或相应确定性控制器执行。
- [x] 初始化 `company/`、`agents/`、`notes/`、`departments/`、`ledger/`、`inbox/`、`workers/`、`reviews/`、`control/`、`sessions/`、`telemetry/` 各存储域；只有 `company/` 能成为 LLM runtime 的原始 state mount。
- [x] CEO、Department、Worker 以 rw 挂载完整 `/company`；Verifier instance 以 ro 挂载完整 `/company`。
- [x] 单测：业务 payload 无 `from` 字段、越权 method 被拒、跨 Department Goal 操作被拒、重复 `request_id` 不重复 mutation；LLM runtime 无法看到 `control / telemetry / reviews / workers / inbox / ledger / departments / notes / agents / sessions`。

**回滚点**：method adapter 先以 dormant service 接入；尚未切换现有 Agent 工具时可整体移除。

## Step 2 — 可靠 Inbox 与单消息唤醒

- [x] 以 `FileInbox.peek_one()` / `ack_one()` 替换 `agent_loop.poll()` 的批量提前消费路径；一个 event wake 只处理 FIFO 队首的一条消息。
- [x] 让 `wake()` 返回明确的成功 / 失败结果；只有成功 wake 才 ack 并上报 `wake_completed`。
- [x] 失败时保留同一 `message_id`，系统以固定短退避重试；第一版没有 retry cap、dead-letter 或跳过队首。
- [x] 同一常驻 Agent 加单 wake 互斥；不同 Agent 可并行。
- [x] heartbeat 改为 quiet timer：Inbox 非空、wake 运行、失败重试都抑制计时；CEO / Department 默认从不可由 Agent 修改的模板配置读取 900 秒；Worker 与 Verifier instance 不进入 resident loop。
- [x] 单测：多消息严格逐条处理、失败不 ack、成功后立即处理下一条、同一 Agent 不重入、不同 Agent 可并行、事件积压时不触发 heartbeat。

## Step 3 — Prompt 分层、Notes 与基础 Skill

- [x] 重构 `orchestration/agent_loop.py` 的 Prompt builder：稳定 charter / Skills 由 loadout 提供，动态 wake 严格按 Wake Context → Company Entry → Current Objective → 自己的 Notes → Capabilities → 单一 Trigger → Completion Contract 组合。
- [x] 新增 Notes 读写 helper；harness 读取所属 Agent 的 Notes 并注入 Prompt，Agent 通过确定性工具更新，但 LLM runtime 不获得 Notes 文件夹挂载；Notes 不自动发布到 Company State。
- [x] 新增或改写基础 Skills：受控方法使用、Company State、Notes、Department 管理、Goal 管理、Department 消息；明确“Skill 负责教，确定性方法负责限制”。
- [x] CEO Skill 明确 `inspect` 默认不开启，只在事实冲突、异常、重大取舍或查证需要时调用。
- [x] 单测 / golden：各常驻角色 Prompt 顺序固定，一个 event Prompt 不含第二条消息；CEO 默认 Prompt 没有 Ledger 总览或 Department 协作历史；Worker / Verifier instance 不获得 Notes。

## Step 4 — Department 模板目录、Objective 与创建控制器

- [x] 新增只读模板目录，第一版仅含 `strategist`、`researcher`、`builder`、`growth`；内部模板声明 charter、spec、基础 Skills、MCP 与系统维护的 `heartbeat_secs: 900`。
- [x] 新增 Department Controller：`list_department_options()` 只返回稳定 ID、公开名称和简短描述；`create_department(option_id, initial_objective)` 校验 CEO 身份、白名单、单实例、最多四个、Company Objective 已生效，并在内部装载完整模板。
- [x] 单测明确 CEO 无法读取、提交或修改 charter、spec、Skills、MCP、heartbeat、compose 等内部模板字段。
- [x] 以 `orchestration/objective_store.py` 实现提案 / revision / Verifier 原语；Company Objective 与每个 Department Objective 的初始值和更新都必须 PASS 后才生效。
- [x] Department 创建本身不进入 Verifier；initial Objective FAIL 时不产生空壳 Department，PASS 后才发 provision command。
- [x] 以 `orchestration/department_provisioner.py` 实现固定模板的同路径 DooD、幂等启动和通知；只接受能从模板目录复验的 command，不接受任意 bundle。
- [x] 新 Agent loadout 中移除 `create-role` / `review-role` 以及旧 role CLI 的产品入口；新 Department API 不实现或暴露 `retire`、`delete`、`merge`、`recreate`、`draining`。
- [x] 单测：零 Department 冷启动、四模板枚举、重复 / 越界创建拒绝、Objective FAIL 不启动、PASS 后只启动一次、provision 重放幂等、方向调整只能通过新的 Objective revision。
- [x] 负向验收：控制方法表、CLI、CEO Skill 与模板中均不存在 Department 退役相关入口。

**回滚点**：模板控制器先保持 dormant；未把 CEO Skill 接入前不会触发动态创建。

## Step 5 — Goal Ledger 与 Scheduler 状态机

- [x] 以 `orchestration/scheduler.py` 实现 `owner_department`、单调 `enqueue_seq`、cancel actor / reason，并把终态固定为 `done / failed_time / cancelled`；不实现 Goal 替代关系字段。
- [x] 实现主路径 `open -> claimed -> running -> reported -> verifying -> done`；Verifier FAIL 回到同一 Goal 的 `running`。
- [x] 删除 `HUB_MAX_ATTEMPTS` 终止语义和通用 `killed`；attempt 只做审计。
- [x] Worker 成功启动时一次性写 `deadline_at = started_at + 10800`；dispatch、report、Verifier FAIL、reconcile 都不得重置。
- [x] Scheduler 以全局 5 个 Worker lifecycle 为硬上限并按 `enqueue_seq` 严格 FIFO；starting、running、awaiting_verdict、resuming、stopping 都占名额。
- [x] 队首 Worker 启动故障保持队首并幂等重试，不生成新 Worker，也不越过后续 Goal。
- [x] cancel 只允许所属 Department 或 CEO；Worker / Verifier instance 无权取消。所有竞态由 Hub 单写锁决定。
- [x] 系统不提供 `supersede_goal`；需要换方向时显式 cancel 旧 Goal，再按普通流程独立创建新 Goal。
- [x] 单测：每条合法 / 非法迁移、不可重置 deadline、无 attempt 上限、FIFO、5 名额、stop ack 前不补位、cancel / result / deadline 竞态，以及 supersede 方法和字段确实不存在。

## Step 6 — Worker Manager 与同会话返工

- [x] 以独立 `orchestration/worker_manager.py` 实现 `create_worker`、`run_worker`、`stop_worker`、`inspect_workers` 四个幂等原语；不保留旧 Broker 实现。
- [x] 通用 Worker spec 只接受一个 Goal；不运行 resident loop、无 Inbox、无 heartbeat、无派生 Goal 和治理方法。
- [x] 在 `agent/runner.py` 接入 `resume_token` 并透传到 `RunRequest.resume_token`；持久化 runtime 返回的 `session_token`。
- [x] Verifier FAIL 时使用同一 `worker_id`、同一容器、同一 workspace 与已有 session token；绝不为返工创建第二个 Worker。
- [x] Worker 可直接读写完整 `/company`；完成一轮工作后调用 `submit_result(summary, company_refs)`，引用的持久结果必须是 `/company/...` 路径。
- [x] Verifier FAIL 后原 Worker 在相同 Company State 路径继续修改；`failed_time / cancelled` 不触发自动回滚，由所属 Department 决定是否清理部分写入。
- [x] runtime home、临时 workspace 与 credential material 由系统管理，不作为 Agent 可浏览的 state mount，也不得自动复制到 `/company`。
- [x] Worker terminal 后发 stop；Worker Manager 确认容器退出后才释放并发名额。
- [x] 重启恢复按 company / goal / worker Docker labels 与 registry 对账；不能仅凭内存判断名额。
- [x] 单测：首次运行、带 session token resume、token 产生前崩溃、幂等 start / stop、company refs 路径校验、Worker 对 `/company` 的 rw 权限、Verifier 对 `/company` 的 ro 权限、Manager 重启对账、最多 5 个同存 Worker。

## Step 7 — Verifier Manager 与一次性审核实例

- [x] 新增 `orchestration/verifier_manager.py`，实现确定性的 Verifier Manager 与 review registry / FIFO；不再启动常驻 Verifier Agent。
- [x] 为每个 review 创建独立临时容器和 runtime home；单个 instance 一次只处理一个 Objective 或 Goal result review，结束后删除。
- [x] 审核池硬限制为最多 3 个 instance，独立于最多 5 个 Worker；容器销毁确认前不释放审核名额。
- [x] Company Objective、Department Objective 与每次 Worker 结果提交共用同一个按 `review_seq` 排序的全局 FIFO；不建设两套审核队列或分别计算并发。
- [x] 新增受控 `submit_verdict(review_id, PASS|FAIL, reason)`；Verifier tool adapter 只绑定当前 review，verdict 接受后上下文立即失效，最终自然语言文本不再驱动状态变化。
- [x] Objective PASS 原子激活对应 revision；FAIL 返回给 CEO。
- [x] Goal result PASS 进入 `done`；FAIL 销毁本轮 Verifier instance，把反馈送回同一 Worker session，同时只给所属 Department 发状态通知；Worker 下一次提交时产生另一条 review。
- [x] Verifier instance、Worker、Department 均不能验收自己产生的结果；doer 与 judge 的身份在代码层分离并 fail-closed。
- [x] Verifier Manager 重启时按 review registry 与 Docker labels 对账；不得重复接受 verdict、超过 3 个实例或泄漏已结束容器。
- [x] Goal 在审核排队或运行期间 deadline / cancel 时，使 review 调用上下文失效并移除排队项或销毁实例；晚 verdict 只能成为 terminal no-op。
- [x] 单测：错误 actor context、过期 / 重复 review、实例调用经营方法、PASS / FAIL 状态流、最大 3 并发、第 4 个排队、销毁后释放名额、instance 崩溃后以全新实例重试、deadline 到期后的晚 verdict terminal no-op。

## Step 8 — Hub 消息、Department 协作与 CEO `inspect`

- [x] 将五字段 IME 的内部 `body` 版本化为结构化对象；Hub 校验 type、目标、身份、大小上限与 message ID 去重。
- [x] 实现 `send_department_message(to, subject, body)`；它只投目标 Department，不创建 Goal、不改 Objective、不抄送 CEO。
- [x] Department 消息协议不实现 `kind`、`reply_to_message_id`、`related_goal_id`；请求、回复和 Goal 背景都作为普通 `subject / body` 内容。
- [x] 按消息矩阵路由 Objective、Department provision、Goal 状态、external event 与 escalation；普通 Worker 控制事件不进入 LLM Inbox。
- [x] 实现 CEO 唯一只读 `inspect()`：默认总览，可按 Department 或 Goal drill-down；不返回原始 Ledger 或 Department 协作消息。
- [x] 单测：Hub 使用 tool adapter 绑定的 sender、业务参数无法自报 `from`、非法 type / target / size 被拒、消息中出现未允许的工作流字段被拒、FIFO 不变、CEO 默认不接收普通 Goal / Worker / 内部协作消息、inspect 零副作用且不泄露协作正文。

## Step 9 — 防空转与主动心跳

- [x] Hub 在所有状态变化、Goal 终态、`wake_completed` 与 watchdog tick 后执行空转检查。
- [x] 只要存在 `open / claimed / running / reported / verifying` Goal 就不新增 `company_idle`；Ledger 为空或全终态时，同时为 CEO 与所有 active Department 各保持恰好一条在途 idle 消息。
- [x] 某 Agent 成功处理后立即复查：仍无 Goal 就只给该 Agent 续发，不等待 900 秒或其他 Agent；出现 Goal 就停止续发。
- [x] 已经排队的 `company_idle` 不静默删除；其处理结束后若已有 Goal，只是不再续发。
- [x] 单个 Agent 失败只堵自己的 FIFO，不阻止其他 Agent 继续；Hub 重启从 idle registry + Inbox 重建 outstanding。
- [x] 单测：零 Department 时只唤醒 CEO、多 Department 同时收到、每 Agent 单条在途、立即续发、Goal 抑制、旧 idle 保留、失败隔离、Hub 重启不重复灌入。

## Step 10 — Compose 冷启动与权限收口

- [x] 调整 `docker-compose.yml`：固定启动 CEO、Hub / Scheduler、Verifier Manager、Department Provisioner、Worker Manager 与 peripheral；不再静态启动四个 Department 或常驻 Verifier Agent。
- [x] 新 company 初始化时 Department registry、Goal Ledger 和 review registry 为空，由 Hub 投递第一次 `company_idle`；不存在 Verifier 启动 heartbeat。
- [x] Department service 从固定模板动态生成；Worker 为带 company / goal / worker labels 的一次性同级容器；Verifier instance 为带 company / review labels 的一次性同级容器。
- [x] LLM runtime 的 company state 只挂载 `/company`；Objective、Notes 和单条 message 由 harness 注入，workspace / session / account material 由 runtime 管理但不作为公司状态暴露；所有其他编排目录均不挂载给 LLM。
- [x] `make up / down` 与清理命令按精确 `COMPANY` 和 Docker label 工作，不能触碰旧 test 或其他 stack。
- [x] 新增 run-log recorder：每个 CEO / Department wake、Worker turn、Verifier review 都保存完整 runtime event stream、模型输出、工具调用 / 结果、stdout、stderr、harness / container log 与结构化 metadata，不截断为 tail。
- [x] Hub、Scheduler、Worker Manager、Verifier Manager、Provisioner 与 peripheral 的完整 stdout / stderr 和结构化事件按 company 归档到 `telemetry/services/`。
- [x] `telemetry` 与 run logs 不挂载给任何 LLM runtime，只供 operator / 测试读取；不主动记录 credential 环境值。
- [x] 验证：`docker compose config`、全新 state 初始化、静态服务集合、只暴露 `/company` 的 state mounts、Department 动态启动、Worker / Verifier 生命周期与完整日志落盘。

**回滚点**：所有真实 compose 试验都用新的 Company ID；停止并删除该新 stack 即可，不需要恢复旧 test。

## Step 11 — Skills、charter 与确定性 loadout 校验

- [x] CEO charter 明确只做 Company / Department Objective、组织与跨部门取舍，不直接经营普通 Goal；接入“组建与调整 Department”Skill 与按需 inspect 指引。
- [x] Department 公共 charter 明确围绕自身 Objective 主动提 Goal、监督 Worker、吸收 PASS 结果；四模板只添加必要差异化内容。
- [x] Worker charter 明确一个 Goal、必须持续尝试、没有 blocked / waiting_external / cannot_execute、只有总时间失败。
- [x] Verifier 模板明确 Objective 与 Goal result 两类独立审核，禁止经营和执行；不配置 resident Inbox、Notes、heartbeat 或可续接 session。
- [x] 更新 `agent/tests/test_loadout.py`、`test_mcp_assets.py`、`test_strategic_skills.py` 等确定性检查：角色只获得授权的 Skills / methods / mounts，heartbeat 配置不能由 Agent 修改。
- [x] 暂不凭空补大量专属 Skills；但按“宁多勿少”给 Worker 接入已有且在 V7 runtime 中真正可运行的研究、产品判断、文案、视觉、部署、GA4 与 Twitter 能力；四个 Department 补齐判断型 Skills，Strategy Department 复用 `find-opportunity`。

## Step 12 — 全新 Company 真 E2E

- [x] 使用明确的新 `COMPANY=<new-three-layer-test-id>`；启动前断言旧 Company 路径、容器和 Git 文件均不会被修改。
- [x] 冷启动：固定内核启动、零 Department、零 Worker、零 Verifier instance；CEO 收到 `company_idle`，Objective review 到达后才临时创建 Verifier。
- [ ] 组织：CEO 只读取公开选项 ID / 名称 / 描述，创建至少 Strategy / Build Department；initial Objective FAIL 不启动，重提 PASS 后启动；重复选项拒绝。
- [x] 主动性：Department 各自从 Objective 创建 Goal；空 Ledger 时 CEO / Department 独立持续提出推进方向，而不是等待唯一外部事项。
- [x] 并发：一次创建至少 7 个 Goal，观测最多 5 个 Worker，剩余严格 FIFO；Worker stop ack 后才补位。
- [ ] 验收：构造一次 Verifier FAIL，证明同一 worker / container / session / deadline 返工后 PASS；另在专用 E2E 部署中由 operator 把系统级 timeout 临时缩短，构造 `failed_time` 和显式 `cancelled`，同时单测默认配置仍为 10800 秒且已运行 Goal 不受配置变化影响。
- [ ] Company State：Research Worker 直接把结论写入 `/company`，Builder Worker 直接写入交付物；Verifier 以只读方式从同一路径验收，FAIL 后原 Worker 原地修改，cancel / timeout 不发生隐式回滚。
- [x] 文件可见性：在 CEO、Department、Worker、Verifier runtime 中分别核验，company state 只可直接浏览 `/company`；列出的内部目录均无挂载。
- [x] 消息：两个 Department 经 Hub 发送只有 subject / body 的普通消息，CEO 不被抄送；CEO 只有主动 `inspect` 时看到受限摘要。
- [ ] 审核并发：同时制造至少 5 个 review，观测最多 3 个 Verifier instance、第 4 个及以后排队；每个 verdict 后对应容器被删除，下一轮审核使用全新实例。
- [x] 可靠性：在 Agent wake、Hub、Worker Manager 各制造一次可恢复中断，验证未 ack 重试、idle 去重、Worker 对账和 deadline 不延长。
- [x] 无退役验收：CEO 可更新 Department Objective，但所有控制方法、Skill 与运行时均没有退役、删除、合并、重建或 draining 动作。
- [x] 日志验收：任取 CEO wake、Department wake、Worker turn、Verifier review 和 Hub / Manager 进程，均能还原完整未截断输出、工具事件、stdout / stderr 与关联 ID；Agent 本身无法读取这些日志。
- [x] 证据保存到本任务 `research/e2e-evidence/`：状态迁移、消息 ID、容器 labels、Verifier verdict、并发时间线和旧 Company 未变证明。

## Step 13 — 质量门、文档与交付

- [x] 从 `main` 删除 V6 专属的旧 Hub/Ledger/Objective/消息 CLI、静态五角色配置、常驻 Verifier、旧组织/Goal Skills、兼容入口与对应测试；冻结 `v6` 分支保留历史。
- [x] `agent_loop` 只保留 V7 Hub context + RemoteInbox + 单消息成功后 ack 路径；删除本地 Objective/Notes、批量 poll 和旧 Prompt 分支。
- [x] 删除 Compose 与动态 Department 启动参数中已失效的 V7 选择开关；Hub context、RemoteInbox 与可靠 ack 现在是唯一运行路径。
- [x] 删除未在 V7 运行的 loadout overlay、session `record`/Stop hook 和旧 Observatory；同步移除其活跃规范。

- [x] 定向测试：

  ```bash
  .venv-cua/bin/python -m pytest orchestration/tests/test_inbox_ack.py orchestration/tests/test_agent_loop_v7.py -q
  .venv-cua/bin/python -m pytest orchestration/tests/test_runtime_store.py orchestration/tests/test_scheduler.py orchestration/tests/test_company_hub_v7.py -q
  .venv-cua/bin/python -m pytest orchestration/tests/test_objective_store.py orchestration/tests/test_departments.py orchestration/tests/test_verifier_manager.py orchestration/tests/test_worker_manager.py agent/tests/test_runner.py -q
  ```

- [x] 全量测试：

  ```bash
  .venv-cua/bin/python -m pytest agent/tests/ orchestration/tests/ company_state_kit/tests/ peripheral/tests/
  ```

- [x] 配置：

  ```bash
  docker compose config
  ```

- [x] 使用 `trellis-check` 对照 PRD、设计、测试与真实 E2E 证据；任何关键行为不能只靠 mock 通过。
- [x] 将经实现验证的运行契约更新进 `.trellis/spec/`；未通过实验验证的专属 Skill 想法不写成系统事实。
- [x] 最终交付列出已完成 AC、未决实验观察与新 Company ID；不宣布或执行旧 Company 迁移。

## 验收映射

| PRD 能力 | 主要实施步骤 | 必须有的证据 |
|---|---|---|
| 三层组织与动态 Department | 4、10、11 | 零 Department 冷启动，模板创建后常驻 |
| 无 Department 退役功能 | 4、11、12 | API / CLI / Skill 负向扫描与运行验收 |
| Objective 与 Goal result 经 Verifier | 4、7 | 每 review 一个新实例、最多 3 并发、结构化 PASS / FAIL |
| Department 主动创建 Goal | 3、5、9、12 | heartbeat / company_idle 后真实 Goal |
| 一个 Goal 一个 Worker、全局最多 5 | 5、6、12 | Worker registry + 容器时间线 |
| 严格 FIFO 与固定总时间 | 5、12 | enqueue_seq、不可变 deadline、补位顺序 |
| 一次一条消息且成功后 ack | 2、8 | 失败重放与多消息顺序测试 |
| CEO 默认不知内部流转、按需 inspect | 3、8、12 | Inbox 证据与只读摘要 |
| Company 不空转 | 9、12 | 每 Agent 单条在途与立即续发记录 |
| Worker 直接写 Company State | 1、6、10、12 | `/company` rw / ro 权限与真实审核路径 |
| Agent 只见 `/company` | 1、3、10、12 | 容器 mount 检查与负向访问测试 |
| 全量运行日志 | 10、12、13 | 完整 event / output / tool / stdout / stderr 档案 |
| 全新 test、不迁移旧状态 | 0、10、12 | 新 Company 路径与旧 Company 未变证明 |
| V6 / V7 分支边界 | -1 | `v6` 与 V7 开始前的 `main` 指向同一 V6 snapshot |

## 实施纪律

- 不在本计划获用户审核前运行 `task.py start` 或修改产品代码。
- 分阶段提交，每一阶段只纳入本任务文件；保留工作区中其他任务和用户已有改动。
- 不为“以后可能需要”预留 Department 退役状态或隐藏入口；若未来要做，重新经过需求与状态机设计。
- 不保留 supersede 方法、字段或隐式替代语义；未来若重新需要，单独设计。
- 不用迁移脚本掩盖架构差异；真实验证只开一个全新的 Agent Company。
