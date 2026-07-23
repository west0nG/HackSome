# 单 Team Hackathon runtime — 技术设计

## 基线

直接修改 `buildfactory/` 中现有 V7 三层实现。保留 runtime adapter、method envelope、
Goal scheduler、Worker/Verifier Manager、session continuity、logs 和 reconciliation；
删除 Company 产品面。

父任务中的 Prompt、状态和权限设计是本子任务的完整产品来源：

- `../07-23-autonomous-build-teams/prd.md`
- `../07-23-autonomous-build-teams/design.md`

## 单 Team 组件

```text
Team Hub
  ├─ resident Lead loop
  ├─ Goal FIFO (worker_max = 1)
  ├─ Worker Manager
  └─ Verifier Manager (verifier_max = 1)
```

Lead 取代 CEO 与 Department。Hub 直接允许 Lead 创建、查看和取消 Goal，不再存在
Objective 或 Department owner。

## 状态

将 `CompanyLayout` 收敛为 Team layout。Agent-facing root 的语义和挂载改为
`project -> /project`。控制面最少保留：

```text
project/
ledger/
inbox/
workers/
reviews/
control/
sessions/
telemetry/
```

删除 active layout 对 `agents/notes/departments/mailboxes` 的依赖。Team 初始化函数负责
原子写入两份 reference，并拒绝路径逃逸或非 UTF-8 文本。

## Prompt builder

- resident builder 改为 Hackathon Lead 固定 Prompt + one trigger；
- Worker builder 删除 owner Department 与 deadline；
- Verifier builder 只支持 `goal_result`，删除 Objective review branches；
- 三个 builder 都直接嵌入完整 CLI 命令和 request-id 说明；
- 不注入 Objective、Notes、Skill 路由或产品阶段。

## 调度

Scheduler 保留多条 open Goal 与 enqueue sequence，但 `max_workers=1`。删除
`deadline_at`、到期扫描和 `failed_time`。Goal 终态只保留：

```text
done | cancelled
```

Verifier PASS 时：

1. 当前 Goal → `done`；
2. 若仍有 open Goal，立即调度下一 Worker；
3. 若 batch 已清空，向 Lead Inbox 写稳定去重的 `goal_batch_drained` trigger。

Verifier FAIL 时恢复当前 Worker，不投递 Lead trigger。

## 权限

- Lead 与 Worker：`/project:rw`，相近 MCP/CLI 工具，零 Skill；
- Verifier：canonical `/project:ro`，检查工具可用，零 Skill；
- Verifier 仅保留 `submit_verdict` 业务方法；
- Lead 不被代码禁止直接修改项目。

## 删除与保留

删除 active compose/service/config：

- Department Provisioner 和 Department templates；
- Objective Store 与 Objective review；
- mail router 依赖、mail Hub 方法与 email Skills；
- resident Notes；
- Peripheral service；
- Skill declarations。

保留 Skill materialization 模块与测试入口，但新增零 Skill materialization 覆盖。
