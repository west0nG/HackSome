# 单 Team Hackathon runtime — 实施计划

## 回滚点

- `buildfactory/` 初始内容来自 BuildFactory `1a0c5fa` 的本地 archive。
- 只修改 `buildfactory/`；根目录 Idea workflow 的并行改动不是本任务所有。

## 1. 角色与状态基线

- [ ] 新增 Lead AgentSpec 与 charter，Worker/Verifier 改为零 Skill。
- [ ] 将 Agent-facing Company state 改为 `/project` Team state。
- [ ] 实现只写入两份 reference 的单 Team 初始化入口。
- [ ] 更新 compose/runtime mounts、actor identity 和 session paths。

## 2. Hub 与方法

- [ ] Lead 直接获得 `create_goal/list_my_goals/cancel_goal`。
- [ ] 删除 Objective、Department、Notes、mail 和 messaging active 方法。
- [ ] 保留 method envelope、actor binding、request-id 幂等与审计。
- [ ] 保留 Worker `submit_result` 和 Verifier `submit_verdict`。

## 3. Prompt

- [ ] 按父设计实现固定 Lead Prompt和动态 trigger。
- [ ] 在 Lead Prompt 内嵌三种 Goal CLI 的完整调用与语义。
- [ ] 重写无 deadline Worker Prompt，并嵌入 `submit_result`。
- [ ] 将 Verifier Prompt 收敛为只读 Goal review，并嵌入 `submit_verdict`。
- [ ] 测试 private acceptance 只进入 Verifier。

## 4. 顺序闭环

- [ ] Worker 并发固定为 1，Verifier 并发固定为 1。
- [ ] 删除 Goal deadline、到期扫描与 `failed_time`。
- [ ] PASS 后运行下一 FIFO Goal；FAIL 恢复原 Worker/session。
- [ ] batch 清空后向 Lead 写稳定去重 trigger。
- [ ] quiet heartbeat 不产生完成或 idle 状态。

## 5. 清理产品面

- [ ] 从 active compose 删除 Department Provisioner、Peripheral 和 mail mounts。
- [ ] 删除角色 loadout 中的全部 Skill，不新增替代 Skill。
- [ ] 移除 Company-only Prompt、配置和 active tests，保留仍适用的底层 runtime 测试。
- [ ] 更新 `buildfactory/README.md` 与 `buildfactory/.trellis/spec/` 为真实单 Team 契约。

## 6. 验证

- [ ] Prompt builder 和角色权限单元测试。
- [ ] 两 Goal FIFO 的脚本化 Lead → Worker → Verifier → Worker → Verifier → Lead 测试。
- [ ] FAIL 后同 Worker/session 返工测试。
- [ ] Verifier canonical project 只读负向测试。
- [ ] 零 Skill materialization 测试。
- [ ] restart/reconcile、method idempotency 和日志回归测试。
- [ ] `python -m compileall`、完整 `pytest`、compose config 和 `git diff --check`。
