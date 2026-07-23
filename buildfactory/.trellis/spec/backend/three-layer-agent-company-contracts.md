# V7 三层主动 Agent Company 契约

> 本文描述 `main` 上的 V7 当前实现。旧的常驻五角色、`send-goal / receive-goal`、
> 任意 Role bundle 与常驻 Verifier 产品语义只保留在冻结的 `v6` 分支中；
> `main` 不再保留其实现、配置、Skill 或活跃规范。
>
> 真实运行证据：`COMPANY=v7-three-layer-e2e-20260714`，2026-07-14；证据归档在
> `.trellis/tasks/07-12-three-layer-proactive-agent-company/research/e2e-evidence/`。

## 1. 固定内核与三层职责

V7 固定启动以下组件：

- CEO：唯一固定经营 Agent，维护 Company Objective、Department Objective、组织与跨部门取舍；
- Company Hub：确定性方法边界、Inbox 路由、Goal/Review 状态与调度的唯一写入入口；
- Department Provisioner：只从固定模板启动常驻 Department；
- Worker Manager：创建、执行、续接和销毁一个 Goal 对应的一次性 Worker；
- Verifier Manager：运行全局 FIFO、最多 3 个并发的一次性审核实例；
- Peripheral：把 webhook 等外部事件归一化后交给 Hub。

`foundagent.net` 另有一个跨 Company、独立 Compose project 的确定性
`mail-router`。它不是任何 Company 栈的角色，只负责把 R2 原始邮件按全局地址
注册表写入对应 Company 的私有 mail journal。

CEO 不执行普通 Goal。Department 围绕自己的 Objective 主动创建 Goal。Worker 只执行一个
Goal。Verifier instance 只审核一个 review。Manager、Hub 与 Peripheral 不做经营判断。

冷启动必须是：零 Department、零 Worker、零 Verifier instance；Hub 只向 CEO 投递一条
`company_idle`。真实 E2E 已从这一状态启动，并由 CEO 自主形成 Company Objective，随后创建
Builder 与 Growth Department。

## 2. 状态域与 LLM 可见性

`CompanyLayout` 在 `state/<company>/` 下建立：

```text
company/  agents/  notes/  departments/  ledger/  inbox/
workers/  reviews/ control/ sessions/     telemetry/ mailboxes/
```

原始 company state 的唯一 LLM 挂载是 `company/ -> /company`：

- CEO、Department、Worker：`/company` 读写；
- Verifier instance：`/company` 只读；
- `agents / notes / departments / ledger / inbox / workers / reviews / control /
  sessions / telemetry / mailboxes` 不挂载为 Agent 可浏览的公司状态；
- Objective、自己的 Notes、单条 Trigger 与受控能力由 harness 注入 Prompt；
- runtime home、workspace、代码、Skill 与只读 account material 是运行基础设施，不属于原始
  company state，也不得自动复制进 `/company`。

`state/_mail/` 是域名级控制面，不属于任一 `CompanyLayout`。它只挂载到各 Company
Hub（claim/list/send 验证）和平台 mail-router；CEO、Department、Worker、Verifier
均不能获得该路径。每个 Company Hub 同时独占自己 root 下的 `mailboxes/`。

Worker 在真实工作自然改变长期共享状态时维护 `/company`，但对外发布、账户配置等工作可以只
存在于实际外部系统中。`submit_result` 的业务 payload 必须是空对象，只声明 Worker 认为工作
已经完成，不携带摘要、证据清单、路径或 URL，也不要求为了提交而制造 Company State 文件。
Verifier 根据 Goal 与私有 acceptance 独立寻找并检查真实结果。FAIL 后原 Worker 原地修改；
cancel 或 timeout 不自动回滚已经发生的 Company State 或外部系统写入。

## 3. 确定性方法边界

`MethodAdapter` 接受版本化信封：

```json
{"version": 1, "request_id": "...", "method": "...", "payload": {}}
```

约束：

- actor 由 harness/runtime 环境绑定，业务 payload 不接受 `from`；
- method 按 CEO、Department、Worker、Verifier、Manager、Peripheral 白名单授权；
- mutation 同时检查 actor、对象归属、当前状态和幂等 `request_id`；
- 相同 `request_id + method + payload` 返回原响应，不重复 mutation；
- 相同 `request_id` 携带不同调用内容返回 `idempotency_conflict`；
- 这是合作型公司内的防误用与审计边界，不是抵御恶意容器的认证系统；第一版没有
  capability token 或 Agent 可见 Unix socket。

默认缓存与完整审计有一个明确例外：`peek_company_email` 返回验证码和 magic
link 等敏感数据，不写 `control/requests` response cache；telemetry 只记录 actor、
Goal、邮件数量与时间范围，不记录正文、链接或验证码。它是实时只读查询，同一
request id 不承诺结果快照。其他 mutation（包括发件）仍按 request id 幂等缓存。

## 4. Objective 与动态 Department

Company Objective、Department Objective 的首次设定和每次 revision 都进入同一个 Verifier
审核池，只有 PASS 后才生效。

第一版 Department 目录固定为 `strategist / researcher / builder / growth`，每类最多一个。
每个 `agents/departments/<id>.yaml` 是该 Department 的唯一声明来源，同时包含公开的
`public_name / public_description`、系统维护的 `heartbeat_secs` 与内部 AgentSpec 运行配置；
控制面按固定 ID 从该目录加载，不存在另一份聚合 catalog 配置。
`list_department_options()` 对 CEO 只返回：

```text
id + public_name + public_description
```

它不返回 charter、AgentSpec、Skill、MCP、heartbeat 或 compose。CEO 调用
`create_department(option_id, initial_objective)`；选项、唯一性、最多四个与 Company
Objective 是否生效由代码校验，只有 initial Objective PASS 后才写 provision command。
Department 创建本身不产生另一条 Department review。

V7 没有 `retire / delete / merge / recreate / draining` 方法或状态，也不保留旧
`create-role / review-role` 产品入口。方向变化只能由 CEO 提交新的 Department Objective。
模板不接受 per-company loadout overlay；CEO 只能选择公开 option，不能改写
charter、Skills、MCP 或 heartbeat。

## 5. Goal、FIFO 与固定总时间

Department 是 Goal owner。Goal 主路径是：

```text
open -> claimed -> running -> reported -> verifying -> done
                                      FAIL -> running（同一 Worker）
```

仅有三个终态：`done / failed_time / cancelled`。

- Goal 创建时分配单调 `enqueue_seq`；全公司严格 FIFO，无优先级、配额、抢占或插队；
- 全局最多 5 个 Worker lifecycle；`starting / running / awaiting_verdict /
  resuming / stopping` 都占名额；
- 排队不计时。Worker 成功启动时只写一次
  `deadline_at = started_at + goal_timeout_secs`，默认 `10800` 秒；
- 执行、审核与全部返工共用这一绝对 deadline，任何 report、FAIL、配置变化或重启都不能延长；
- Worker 启动失败保持同一 `worker_id` 在 FIFO 队首重试，不允许后续 Goal 越过；
- 成功重试后清理瞬时 `latest_feedback`，但保留 `start_attempts` 与 operation ID 审计；
- attempt 没有终止上限；未 PASS 的唯一执行失败是 `failed_time`；
- owner Department 可取消自己的非终态 Goal，CEO 可取消任意受影响 Goal；Worker 与
  Verifier 无取消权限；
- `cancelled` 是控制面撤回，不是执行失败。运行中 Worker 实际销毁并收到
  `worker_stopped` 确认前，槽位不释放；
- 没有 `blocked / waiting_external / cannot_execute / killed / supersede`，也没有 Goal
  替代关系字段。

## 6. 一次性 Worker 与同会话返工

Worker 使用统一 `agents/ephemeral/worker.yaml`，无 resident loop、Inbox、Notes、heartbeat、
Objective 或治理方法。初始 Prompt 只包含 Goal intent、owner、deadline 与完成契约；补充
acceptance 不向 Worker公开，只进入 Verifier Prompt。

执行层按“宁多勿少”复用已有能力库。通用 Worker 除 Company State 和
`submit-work` 外，还获得反证、因果链、买家视角、新信息整合、客户语言研究、
去 AI 味、视觉资产、图像生成、视觉迭代、站点发布、GA4 和 Twitter 操作 Skills。
这些是能实际在当前 Worker runtime 内运行的能力。Worker 另有 `check-email` 与
`send-email`，但只能调用 Company Hub 的受控方法；它看不到原始 Inbox、全局
registry 或 Company mailboxes。Worker peek 的时间下界固定为当前 Goal 的
`created_at`，返工和会话续接不重置这个窗口。

常驻 Department 不获得部署、发布等执行 Skill，但四个模板都获得与其决策
相关的反证、因果链、买家视角和新信息整合能力；真正执行仍通过 Goal
交给 Worker。Strategy Department 额外复用 `find-opportunity`，负责把证据缺口
拆成 Goal、沉淀候选方向，但 Company Objective 的最终取舍仍属于 CEO。

Worker Manager 持久化：

```text
worker_id / goal_id / container_name / state / session_token /
turns / continuity_unavailable / last_result
```

Verifier FAIL 时，Hub 发 `resume_worker`，必须保留同一 `worker_id`、容器、workspace、home、
session token 与 deadline。下一轮 runtime 使用 `RunRequest.resume_token`。如果首次运行在 token
产生前崩溃，只能记录 `continuity_unavailable` 并在同一 Worker lifecycle 重试，不能换 Worker。

创建与对账并发使用进程内 creation lease：周期 reconcile 不得把本进程正在创建的容器误判为
`missing`；进程重启后 lease 为空，因此遗留的 `creating` 仍能被对账。stop 在创建窗口到达时，
迟到的容器必须再次清理，且创建完成路径不得把 `stopped` 覆盖回 `ready`。

## 7. 一次性 Verifier 与全局 3 并发池

Company Objective、Department Objective、每次 Goal result 共用一个按 `review_seq` 排序的
FIFO。最多同时存在 3 个 `running/stopping` Verifier instance；第 4 个 review 保持 queued。

每条 review 使用新的 `instance_id = verifier-<review_seq>-<attempt>`、新的 runtime home、fresh
session 和只读 `/company`。Verifier 获得与 Worker 相同的完整 account package：
`accounts/<id>/secrets.env` 作为环境变量注入，账户目录以 `/account:ro` 挂载；因此它可以独立
检查需要认证的外部结果。它仍只有最小审核 Skill 集，无 Inbox、Notes、heartbeat 或 Worker
执行 Skills，只能对当前 review 调用一次 `submit_verdict(PASS|FAIL, reason)`。账户凭据在角色
契约上仅用于查看和核验，Verifier 不得发布、编辑、删除或修复任何外部结果。最终自然语言不能
直接改状态。

有效 verdict 后 instance 进入 `stopping`；只有容器销毁并收到
`verifier_instance_stopped` 才释放审核名额。instance 崩溃且未提交 verdict 时，原 review 回到
FIFO，但下一次使用全新的 instance。Goal result FAIL 产生返工；返工后的再次提交产生另一条
review，绝不续接上一审核会话。

cancel/deadline 在 Verifier 创建窗口到达时，stop 必须等创建窗口收敛并清理迟到容器后再确认
释放名额；已失效 review 不得进入模型运行。晚 verdict 只能是 terminal no-op。

## 8. Inbox、唤醒、Prompt 与 Notes

常驻 CEO/Department 使用 `peek_one -> wake -> wake_completed/ack`：

- 一个 event wake 只处理 FIFO 队首一条消息；
- 成功后才 ack，并立刻处理下一条未读；
- 失败保留相同 `message_id`，固定短退避后无限重试，不跳过、不 dead-letter；
- 同一常驻 Agent 单 wake，不同 Agent 与 Worker 可以并行；
- heartbeat 是 quiet timer：Inbox 非空、wake 运行或失败重试时不计时；
- CEO 与内置 Department 默认 `heartbeat_secs=900`，值来自系统配置/模板，Agent 不能修改；
- Worker 与 Verifier 不进入 resident loop。

动态 wake Prompt 顺序固定为：

```text
WAKE CONTEXT
COMPANY ENTRY
CURRENT OBJECTIVE
OBJECTIVE REVIEWS IN FLIGHT
OWN NOTES
CAPABILITIES
ONE TRIGGER
COMPLETION CONTRACT
```

charter 与 loadout Skills 是稳定层。Notes 只属于该常驻 Agent，原始 Notes 目录不挂载；长期共享
需要长期共享的事实应写入 Company State；只存在于外部系统中的实际结果不必为了完成声明而复制。

Company State 是 `/company` 原生文件夹。Agent 通过共享 Skill 做浅层发现、限定搜索、
按需读取和直接维护；没有必需索引、session marker 或 Stop hook。没有持久业务变化时
不制造空记录。

原生目录访问的配置、权限和 Agent-facing 契约已有自动化覆盖；长期自主运行效果尚待
新的真实 Company 实验验证，不能沿用旧存储入口的 E2E 证据替它背书。

### Company 邮件

域名级注册表位于 `state/_mail/registry.jsonl`，只包含永久
`localpart -> company` claim。CEO 通过 `claim_company_mailbox` 认领，payload
不能提供 Company id；每个 Company 固定最多 5 个地址，同名跨 Company 全局冲突，
不存在 release、rename、transfer 或 Agent receiver。CEO、Department、Worker 可通过
`list_company_mailboxes` 查看本 Company 地址，其他 Company 映射不可见。

入站邮件由平台 mail-router 写入 `state/<company>/mailboxes/messages.jsonl`。
Hub 默认只向 CEO 发送稳定去重的通知，不向 Department 广播。Department 可调用
`peek_company_email` 查看 Company 最近 100 封；当前 Goal 的合法 Worker 可查看
Goal 创建以来最近 100 封。两者都是全地址、只读、非消费查询，互不干扰，也不推进
CEO 通知 cursor。Verifier 和 CEO 均不能调用 peek。

Department 与当前 Goal 的合法 Worker 都能调用 `send_company_email`；Department
Skill 引导普通外部执行优先创建 Goal 交给 Worker，但不禁止 Department 直接收验证码
或发件。发件地址必须属于当前 Company，使用 request id 作为 reservation 与 Resend
idempotency key；配额为 Company 30/24h、单地址 15/24h，失败 reservation 不退款。
CEO 不发送，Verifier 无任何邮件方法。

## 9. 防空转、内部消息与 CEO inspect

只要存在 `open / claimed / running / reported / verifying` Goal，Hub 不新增
`company_idle`。Ledger 为空或仅终态时，CEO 与每个 active Department 各自最多保留一条在途
idle 消息；某 Agent 成功处理后若仍无 Goal，立即只为它续发，不等待 900 秒，也不等待其他
Agent。失败只堵自己的 FIFO。

Department 协作走 Hub，逻辑字段只有：

```text
message_id / time / from / to / subject / body
```

没有 `kind / reply_to_message_id / related_goal_id`。协作消息不创建 Goal、不改 Objective、
不自动抄送 CEO；CEO 也不能查询协作正文。

CEO 默认不接收普通 Goal、Worker 或 Goal Verifier 流转。唯一查证入口是只读 `inspect()`：
默认公司摘要，可按 Department 或 Goal 下钻；不返回原始 Ledger 或内部消息，也无副作用。
CEO Skill 明确要求只在冲突、异常、重大取舍或事实核实时使用，不能持续轮询或接管 Department。

## 10. 日志、恢复与测试门禁

每个 CEO/Department wake、Worker turn、Verifier review 建立独立 run 目录，保存完整 runtime
JSONL、模型输出、stderr、harness log、container log 与 metadata。Hub、Worker Manager、Verifier
Manager、Provisioner、Peripheral 和常驻 Agent stdout/stderr 存入 `telemetry/services/`。
Telemetry 不挂载给任何 LLM runtime，系统不主动记录 credential 环境值。

恢复依赖持久化状态、命令/receipt、幂等 request ID 与 Docker labels，不以进程内内存作为唯一
真相。Hub 重启重建 idle 与 dispatch；未 ack wake 重放同一消息；Worker/Verifier command 在无
receipt 时重放；已完成 mutation 由 request ID 去重。

最低质量门：

```bash
.venv-cua/bin/python -m compileall -q agent orchestration peripheral
.venv-cua/bin/python -m pytest agent/tests/ orchestration/tests/ peripheral/tests/
docker compose config -q
docker compose -f docker-compose.mail.yml -p foundagent-mail config -q
```

关键负向测试必须持续覆盖：无 Department 退役入口、无 supersede/blocked/waiting 状态、角色
method 越权、业务 payload 不能自报 `from`、`submit_result` 拒绝任何结果字段、Verifier 不能写
`/company`、Worker 看不到验收补充信息、第五个 Worker 后 FIFO 排队、第三个 Verifier 后排队、
stop ack 前不补位、deadline 不可重置、跨 Company 邮件不可见、Verifier 无邮件能力、敏感 peek
不落 response cache/telemetry，以及 Worker/Verifier 创建窗口的 cancel/reconcile 竞态。

## 11. 已验证边界与第一版明确不做

真实 V7 E2E 已证明：全新冷启动、Company Objective PASS、两个 Department Objective 并发审核、
PASS 后才启动 Department、Department 主动创建业务 Goal、5 Worker 占满后后续 Goal 排队、
Worker 执行真实工作、Goal result 使用临时 Verifier、FAIL 后同 Worker/session/deadline 返工、
第二轮使用新 Verifier、显式 cancel 与容器停止、Hub/Agent 中断后的未读重放，以及 operator-only
完整日志。

第一版不做：旧 Company 迁移、Department 退役、Goal supersede、语义去重、成本预算、恶意
Agent 身份防御、失败 Company State 自动回滚、Department 专属 Worker 模板。未被真实实验验证的
专属 Skill 想法不能写成系统事实；已有且能在 V7 运行时真正执行的通用能力
则应优先复用，不做过度裁剪。

## 12. 场景：固定模板中的能力复用

### 1. 范围与触发条件

修改 `agents/ceo.yaml`、`agents/departments/*.yaml`、`agents/ephemeral/*.yaml`、
Skill 资产、MCP 配置或运行时挂载时，必须同时检查能力是否真的能在对应容器内执行。
删除 V6 产品代码时，不得因为旧入口消失而连带删除仍可运行的通用业务能力。

### 2. 签名

```text
AgentSpec.load(path) -> AgentSpec
runtime.materialize_home(spec, home_root, skills_root=...) -> LoadoutInfo
DepartmentCatalog.load(departments_dir) -> 固定模板目录
```

活跃 Skill 只由固定 AgentSpec 声明；V7 不读取 `AGENT_LOADOUT`，也没有 per-company
overlay。CEO 通过 Department option 创建实例，不能提交 Skill、MCP 或模板正文。

### 3. 契约

- Worker 获得能在当前容器运行的通用研究、判断、文案、视觉、部署、分析与分发能力；
- Department 获得决策与管理能力，不直接获得发布类执行 Skill；Strategy Department
  可复用 `find-opportunity`，但不能修改 Company Objective；
- Verifier loadout 只有 `company-state-readonly`；完整 account package 仅供独立核验。
  `submit_verdict` 的唯一命令和约束直接写在 Verifier charter 中，不再依赖通用
  `company-methods` 或独立 `submit-verdict` Skill；
- 一个 Skill 只有在所需脚本、MCP、环境变量、挂载或受控方法均存在时才能加入活跃
  loadout；保留源码不等于向 Agent 宣称该能力可用；
- V7 resident loop 无条件使用 Hub context、RemoteInbox 与成功后 ack，不再通过
  `AGENT_CONTEXT_FROM_HUB / AGENT_REMOTE_INBOX / AGENT_RELIABLE_INBOX /
  AGENT_PROMPT_MODE` 兼容开关选择旧路径；
- CEO loadout 包含 `claim-mailbox`，不包含 peek 或发送；全部 Department 与 Worker
  loadout 包含 `check-email / send-email`；Verifier 不包含任何邮件 Skill。三者只调用
  确定性 Hub 方法，不能挂载 mailbox registry、Company mailboxes 或原始 Inbox。

### 4. 校验与错误矩阵

| 条件 | 结果 |
|---|---|
| AgentSpec 声明不存在的 Skill 路径 | materialization 失败，不静默降级成“看似可用” |
| Department YAML 缺失、额外、ID 不匹配或公开元数据非法 | 固定模板目录加载失败 |
| Verifier 重新声明 `company-methods` 或 `submit-verdict` | loadout 精确集合测试失败；提交命令只属于 charter |
| 邮件 Skill 尝试读取 Inbox、registry 或 mailboxes | 合同测试失败；必须只调用受控 Hub 方法 |
| V6 静态角色、旧组织 Skill 或 overlay 入口重新出现 | V7 负向测试失败 |

### 5. 正常、基础与错误案例

- Good：通用 Worker 同时拥有研究、视觉、部署、GA4 与 Twitter Skills，并能从其
  materialized home 读取脚本和引用资产。
- Base：Strategy Department 用 `find-opportunity` 拆出证据 Goal，把候选方向写入
  `/company`，最终取舍仍由 CEO 完成。
- Good：Department 直接处理当前 wake 的验证码是允许路径；普通外部执行仍优先拆成
  Goal 交给 Worker。
- Bad：为了启用邮件 Skill，向 Worker 挂载 `mailboxes/`、Inbox 或其他内部状态。

### 6. 必需测试

- `agent/tests/test_resident_loadout.py`：各模板的精确 Skill 集合与嵌套资产落盘；
- `agent/tests/test_skill_catalog.py`：Skill 入口、角色预算、邮件角色矩阵与旧命令禁用；
- `agent/tests/test_mcp_assets.py`：CEO、Department、Worker 的完整工具场与 Verifier 收口；
- `orchestration/tests/test_runtime_materialization.py`：临时 Worker/Verifier 的真实 materialization；
- `orchestration/tests/test_v7_negative_contracts.py`：V6 文件、overlay 与旧入口不复活。

### 7. 错误与正确示例

Wrong：

```yaml
skills:
  - ../assets/skills/claim-mailbox  # Department 不能消耗 Company 永久地址名额
```

Correct：

```yaml
skills:
  - ../assets/skills/check-email  # Department 通过 Hub 全量只读 peek
  - ../assets/skills/send-email   # Department 可直接发；Skill 引导优先 Worker
```

## 13. 场景：单一 Department YAML 与公开选项投影

### 1. 范围与触发条件

修改固定 Department 的公开名称、职责描述、heartbeat、AgentSpec 运行配置，或修改 Hub / Provisioner
加载 Department 模板的方式时，必须保持“单一 YAML 声明、控制面严格校验、CEO 只见公开投影”三项
不变量。

### 2. 签名

```text
DepartmentCatalog.load(agents/departments/) -> DepartmentCatalog
DepartmentCatalog.options() -> [{id, name, description}]
create_department({option_id, initial_objective}) -> creation request
```

### 3. 契约

- `agents/departments/` 必须且只能包含 `strategist.yaml`、`researcher.yaml`、`builder.yaml`、
  `growth.yaml` 四个 YAML；返回顺序由固定 ID 列表决定，不由文件系统顺序决定；
- 每个文件的 `name` 必须同时匹配文件 stem 与固定 ID；
- 每个文件必须声明非空 `public_name`、非空 `public_description` 和正整数
  `heartbeat_secs`；内置值显式为 `900`；
- `agent_spec` 由 YAML 文件路径推导，charter 由同一文件的 `system_prompt` 相对路径推导；
  `system_prompt` 必须留在 `agents/` 内；
- Skills 与 MCP 只认同一 Department YAML 的 AgentSpec 字段，不得再建立聚合 catalog 副本；
- CEO 看到的 `name` 表示 Department 叫什么，`description` 表示它有什么用；`id` 只是传给
  `create_department` 的稳定选择句柄；
- CEO 不得通过 list/create 接口读取或覆盖 model、Skills、MCP、charter、heartbeat 或权限。

### 4. 校验与错误矩阵

| 条件 | 结果 |
|---|---|
| Department 目录缺少固定 YAML，或出现额外 `.yaml/.yml` | `DepartmentError`，拒绝启动部分目录 |
| YAML 根节点不是 mapping | `DepartmentError` |
| `name` 与文件名/固定 ID 不一致 | `DepartmentError` |
| `public_name` 或 `public_description` 缺失、非字符串或空白 | `DepartmentError` |
| `heartbeat_secs` 是布尔值、字符串、零或负数 | `DepartmentError` |
| `system_prompt` 是绝对路径或逃出 `agents/` | `DepartmentError` |
| CEO 调用 `list_department_options()` | 只返回 `id / name / description` |
| 非 CEO 调用 list/create | 方法授权拒绝 |

### 5. 正常、基础与错误案例

- Good：Builder YAML 同时声明 `public_name: Build Department`、中文职责描述、
  `heartbeat_secs: 900` 以及完整 AgentSpec；Hub 只投影三个公开字段。
- Base：CEO 读取公开选项后，以 `builder` 作为 `option_id` 创建 Department，不能附带任何内部配置。
- Bad：另建 `catalog.yaml` 复制 Skills、MCP 或 charter，导致控制面与 Agent runtime 各认一份配置。

### 6. 必需测试

- `orchestration/tests/test_departments.py`：固定文件集合、字段类型、ID 一致性、路径边界、
  公开投影和运行路径推导；
- `orchestration/tests/test_company_hub_v7.py`：CEO 只得到三个公开字段，创建仍等待 Objective PASS；
- `orchestration/tests/test_v7_mount_boundaries.py`：Provisioner 注入正确 AgentSpec、charter 和 900 秒
  heartbeat；
- `agent/tests/test_spec.py`、`test_resident_loadout.py`、`test_mcp_assets.py`：新增 Department 元数据
  不改变 AgentSpec、Skills 与 MCP 的实际运行配置。

### 7. 错误与正确示例

Wrong：

```yaml
# agents/departments/catalog.yaml
builder:
  skills: [company-state, manage-goals]  # 与 builder.yaml 形成第二事实来源
```

Correct：

```yaml
# agents/departments/builder.yaml
name: builder
public_name: Build Department
public_description: 把已选择的方向转化为可运行、可交付、可验证的产品与技术资产。
heartbeat_secs: 900
system_prompt: ../assets/departments/builder-charter.md
skills:
  - ../assets/skills/company-state
```
