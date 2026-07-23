# Team bootstrap、全局 Pool 与 operator 控制

## 目标

在已通过验收的单 Team runtime 上增加 Build-side handoff bootstrap、Team registry、
默认两个 active Team、selected Team 排队，以及 operator pause/resume。所有实现仍限制
在 `buildfactory/`，不接入 Idea Review Gate UI。

## 前置条件

- `07-23-single-team-runtime` 已完成并通过完整质量门。

## 需求

- 提供 Build-side bootstrap CLI，输入 challenge、Idea Card、稳定 ID 和 SHA-256。
- 每份 handoff 幂等创建一个隔离 Team state；内容 hash 冲突必须失败。
- 默认 `max_active_teams = 2`；可通过运行配置修改。
- selected Team 超出槽位后保持 FIFO queued，不算失败或拒绝。
- active Team 不自动完成、idle、轮转或释放槽位。
- operator 可以显式 pause active Team；相关运行实例停止后才释放槽位。
- paused Team 保留 `/project`、Goal ledger、session、queue 和 telemetry，可显式 resume。
- pause 释放槽位后自动启动最早 queued Team。
- 系统不根据 Idea 或项目质量改变 Team 顺序。
- 不读取或修改 `src/hacksome/` 内部状态；只消费 handoff contract。

## 验收标准

- [ ] 同一 handoff 重放只创建一个 Team；相同 ID 不同 hash 返回冲突。
- [ ] 一次 bootstrap 至少三个 Team 时默认只启动两个，第三个保持 queued。
- [ ] pause 一个 active Team 后，只有在其运行实例停止确认后第三个 Team 才启动。
- [ ] resume paused Team 时保持项目、Goal、session 和日志连续性；无槽位时进入 queued。
- [ ] operator 控制不会创建完成、idle、quality score、winner 或自动轮转语义。
- [ ] CLI 和 registry 测试不依赖 Idea workflow Python 模块。

## 不在范围内

- Human Review Gate UI、Idea Card 展示或 selection 持久化。
- 自动 Team 排名、合并、删除或归档。
- 多 Worker Team。
