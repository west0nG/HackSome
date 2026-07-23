# 单 Team Hackathon runtime — 实施计划

## 回滚点

- `buildfactory/` 初始内容来自 BuildFactory `1a0c5fa` 的本地 archive。
- 只修改 `buildfactory/`；根目录 Idea workflow 的并行改动不是本任务所有。

## 1. 角色与状态基线

- [x] 新增 Lead AgentSpec 与 charter，Worker/Verifier 改为零 Skill。
- [x] 将 Agent-facing Company state 改为 `/project` Team state。
- [x] 实现只写入两份 reference 的单 Team 初始化入口。
- [x] 更新 compose/runtime mounts、actor identity 和 session paths。

## 2. Hub 与方法

- [x] Lead 直接获得 `create_goal/list_my_goals/cancel_goal`。
- [x] 删除 Objective、Department、Notes、mail 和 messaging active 方法。
- [x] 保留 method envelope、actor binding、request-id 幂等与审计。
- [x] 保留 Worker `submit_result` 和 Verifier `submit_verdict`。

## 3. Prompt

- [x] 按父设计实现固定 Lead Prompt和动态 trigger。
- [x] 在 Lead Prompt 内嵌三种 Goal CLI 的完整调用与语义。
- [x] 重写无 deadline Worker Prompt，并嵌入 `submit_result`。
- [x] 将 Verifier Prompt 收敛为只读 Goal review，并嵌入 `submit_verdict`。
- [x] 测试 private acceptance 只进入 Verifier。

## 4. 顺序闭环

- [x] Worker 并发固定为 1，Verifier 并发固定为 1。
- [x] 删除 Goal deadline、到期扫描与 `failed_time`。
- [x] PASS 后运行下一 FIFO Goal；FAIL 恢复原 Worker/session。
- [x] batch 清空后向 Lead 写稳定去重 trigger。
- [x] quiet heartbeat 不产生完成或 idle 状态。

## 5. 清理产品面

- [x] 从 active compose 删除 Department Provisioner、Peripheral 和 mail mounts。
- [x] 删除角色 loadout 中的全部 Skill，不新增替代 Skill。
- [x] 移除 Company-only Prompt、配置和 active tests，保留仍适用的底层 runtime 测试。
- [x] 更新 `buildfactory/README.md` 与 `buildfactory/.trellis/spec/` 为真实单 Team 契约。

## 6. 验证

- [x] Prompt builder 和角色权限单元测试。
- [x] 两 Goal FIFO 的脚本化 Lead → Worker → Verifier → Worker → Verifier → Lead 测试。
- [x] FAIL 后同 Worker/session 返工测试。
- [x] Verifier canonical project 只读负向测试。
- [x] 零 Skill materialization 测试。
- [x] restart/reconcile、method idempotency 和日志回归测试。
- [x] `python -m compileall`、完整 `pytest`、compose config 和 `git diff --check`。
