# E2E 设计：Department 单一声明与公开投影

## 1. 测试边界

这是一套针对配置改造的窄而深 E2E：

```text
真实 Department YAML
  → 真实 Hub 加载目录
  → CEO-bound 真实容器调用 list/create
  → 真实持久化 creation request
  → 真实 Verifier Manager + 临时 Verifier + Codex
  → 真实 Department Provisioner
  → 真实 Builder resident 容器启动
```

Company Objective 只是一项业务前置，不属于被测改造。它在 Hub 启动前使用真实 Store 类创建并
确定性 PASS；Builder Objective 则必须走完整真实审核链。这样既覆盖 Department 创建门，又避免
为了测试 YAML 而重新运行一次不可控的市场判断。

## 2. 隔离拓扑

- Company：`department-specs-e2e-20260719`
- Account：`foundagent`
- Compose project/network：由 compose 的 `name: ${COMPANY}` 形成独立
  `department-specs-e2e-20260719_default`。
- 只启动：`hub`、`verifier-manager`、`department-provisioner`。
- CEO：不启动 resident service；使用 `docker compose run --rm --no-deps --entrypoint python3 ceo`
  执行单次 `orchestration.control_client`，继承真实 CEO actor 环境。
- Builder：由 Provisioner 使用 `docker run` 动态创建，和生产路径完全一致。

不启动 Worker Manager、Peripheral 或自治 CEO，减少无关行为和端口冲突。

## 3. 前置 Objective fixture

在 Hub 启动前，用 `CompanyLayout`、`VerifierManager`、`ObjectiveStore` 的真实生产类：

1. 初始化全新 state root；
2. propose 一个明确标注 E2E fixture 的 Company Objective；
3. schedule 得到真实 review/instance ID；
4. 以确定性 PASS reason 提交 verdict；
5. apply review，并把 review 标为 routed、instance 标为 stopped。

该步骤不宣称验证真实 Company Objective 审核，只为满足
`create_department` 的“Company Objective 已 active”不变量。fixture 的全过程与输出写入 evidence。

## 4. CEO 公开选项断言

单次 CEO 容器调用：

```bash
python3 -m orchestration.control_client list_department_options \
  --request-id department-specs-e2e-list-options
```

保存原始 JSON，并用独立 Python 断言：

- ID 顺序是 `strategist / researcher / builder / growth`；
- 每行 key set 恰好是 `id / name / description`；
- name/description 与宿主机四个 YAML 一致；
- JSON 序列化文本不含内部字段名。

这同时验证 Hub 的真实目录加载、公开投影和 CEO 方法授权。

## 5. 创建与真实审核

CEO 容器调用：

```json
{
  "option_id": "builder",
  "initial_objective": "Own the repeatable delivery capability ..."
}
```

使用既有、已在 V7 E2E 中真实 PASS 的 durable Builder Objective 语义，避免把一次性测试任务写成
Department Objective。Verifier Manager 必须：

1. 发现 review command；
2. 创建带本 Company label 的临时 Verifier 容器；
3. 等待 computer-server；
4. 运行 Codex；
5. 通过 `submit_verdict` 返回 PASS/FAIL；
6. 销毁临时容器并释放 slot。

轮询有界：首次最多等待 10 分钟。FAIL 时保存完整脱敏 reason，允许用更清晰但同职责边界的
Objective 重新创建一次；第二次仍 FAIL 则本 E2E 失败。

## 6. Provisioner 与 Builder 断言

Objective PASS 后，Hub 产生 provision command。最多等待 3 分钟直到：

- `state/.../departments/builder.json` 为 `active`；
- Docker 容器 `department-specs-e2e-20260719-builder` 为 running。

采集时只输出白名单字段：

- labels：company、kind、department、template；
- env：精确匹配 `AGENT_SPEC`、`AGENT_CHARTER`、`AGENT_HEARTBEAT_SECS` 的三行；
- mounts：确认当前工作树 `agents/` 只读挂载；
- 容器内文件：四个 Department YAML 存在、catalog 不存在；
- AgentSpec：name/provider/model/effort、Skill basename 集合、MCP basename；
- logs：`resident_loadout` 与 `agent_loop boot` 关键行。

不记录完整 `.Config.Env`，避免把 account secrets 带入证据。

## 7. 证据目录

```text
research/e2e-evidence/
  preflight.md
  objective-fixture.json
  list-options.json
  list-options-assertion.json
  create-department.json
  review-final.json
  department-final.json
  builder-inspect.json
  builder-runtime.json
  service-logs.txt
  cleanup.md
  report.md
```

原始大体积 runtime JSONL 留在 ignored E2E state；报告记录其路径与关键 run ID，不复制 credential
或不必要的大文件进 Git。

## 8. 清理与失败策略

无论 PASS/FAIL：

1. 使用精确 Company label 停止并删除动态容器；
2. `docker compose down --remove-orphans` 清理固定服务与网络；
3. 断言该 company label 的容器数为零，目标 network 不存在；
4. 删除仅本 E2E 创建的 `accounts/foundagent` symlink；
5. 保留 state 目录但不提交，用于复核真实日志。

任何 auth、镜像、Docker 或模型失败都记录为基础设施失败，不得改写状态文件制造 PASS。

## 9. 取舍

- 使用真实 Verifier 和真实 Builder runtime，因为配置加载问题只有跨进程/容器才能获得充分证据。
- CEO 使用真实容器内的受控客户端而非自治 LLM；被测对象是它能看到的数据边界，不是其自然语言
  决策质量。
- Company Objective 使用确定性 fixture；Builder Objective 使用真实审核，保持测试聚焦且成本有界。
- E2E 默认是手动、付费、非 CI 测试；不把 account credentials 复制进仓库。
