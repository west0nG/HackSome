# Team Pool 与 operator 控制 — 实施计划

## 1. Handoff 与 registry

- [ ] 定义 Build-side handoff schema 和 hash 校验。
- [ ] 实现幂等 Team ID、registry row 和 reference 初始化。
- [ ] 增加冲突、损坏输入和重放测试。

## 2. Global Team Pool

- [ ] 实现默认两个 active Team 的 FIFO scheduler。
- [ ] 将单 Team compose/runtime 生命周期接入 registry。
- [ ] 保证 queued 不启动任何 Agent/Manager 容器。

## 3. Operator 控制

- [ ] 实现 list/inspect/pause/resume CLI。
- [ ] pause 等待所有运行实例 stop/reconcile 后释放 slot。
- [ ] resume 保留 Team identity、state、Goal、session 和 telemetry。
- [ ] slot 释放后启动最早 queued Team。

## 4. 验证

- [ ] 三 Team / 两 slot 的完整生命周期测试。
- [ ] pause 创建窗口、late stop、重启 reconcile 和幂等竞态测试。
- [ ] 验证无自动完成、idle、轮转、排名或删除路径。
- [ ] 完整 `buildfactory/` 测试、compose config 与 `git diff --check`。
