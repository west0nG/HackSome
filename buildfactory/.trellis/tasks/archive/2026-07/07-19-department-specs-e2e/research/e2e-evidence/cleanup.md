# E2E 清理结果

- 使用 `department-specs-e2e-20260719` Compose project 停止并删除 Hub、Verifier Manager 与
  Department Provisioner。
- 使用精确 `foundagent.company=department-specs-e2e-20260719` label 删除 Builder、Verifier 和
  认证诊断期间隔离的临时容器。
- Compose 首次删除 network 时因动态容器仍占用而返回 `Resource is still in use`；精确 label
  容器清理后确认 network 已无 endpoint，再删除专用 network。
- 清理后精确 company label 容器数：`0`。
- 清理后 `department-specs-e2e-20260719_default` network：不存在。
- 临时 `accounts/foundagent` symlink：已删除。
- 临时 account-target / current-auth 只读 Compose bridge：已删除。
- 其他 Company 的容器仍在运行，本测试没有对它们执行停止、重启或删除。
- 独立 state 保留在 ignored 路径
  `state/department-specs-e2e-20260719/`，清理时大小为 `6.6M`；它不进入 Git。
