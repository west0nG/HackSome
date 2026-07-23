# 长跑最小加固包

## 背景 / 目标

第一次无人值守长跑前，堵住两类问题：①已知 bug 会污染实验（researcher 未认证白跑）；②崩溃/违规/花费不留痕，长跑观测缺数据。**只加"记录"和"自愈"，不加任何行为闸门**——冷却、熔断、鉴权均在范围外（用户拍板）。

## 需求

1. **researcher 凭证修复**：`agents/researcher.yaml` 的 `credentials: api-key` 改回 `subscription`，复用现有 `CLAUDE_CODE_OAUTH_TOKEN`（`vm/.env.local` 里没有 `ANTHROPIC_API_KEY`，api-key 模式必然未认证）。
2. **compose 自愈**：全部服务加 `restart: unless-stopped`；hub 与 peripheral 加 healthcheck，进程 hang/死时 `docker ps` 可见 unhealthy。注意 provisioner 渲染动态角色 service 用的 `x-agent` 锚点也要同步继承 restart 策略。
3. **wake/成本计量落盘**：每次 wake 结束后追加一行 JSONL（落点 `state/<company>/telemetry/`，具体文件名设计时定），至少含：agent key、开始/结束时间、触发类型（事件/心跳）、session id、`cost_usd`、时长。claude 适配器已解析出 `total_cost_usd`（`agent/runtimes/claude_code.py`），目前在 `wake()` 中被丢弃；codex 角色 cost 允许为 null。**只记录，不设任何阈值/熔断/告警。**
4. **hub 审计事件落盘**：`hub_drain` 生成的 `("audit", …)` 动作（伪造 verdict 被拦、越权汇报、畸形消息）目前被直接丢弃（`orchestration/hub.py` drain 处），改为追加写 append-only JSONL（落点 `state/<company>/` 下，hub 独占写），含时间、原消息 id、发送者、拒绝原因。

## 约束

- 除 researcher 凭证语义修复外，**默认行为零变化**：不改任何状态机语义、不加任何拦截/停止逻辑。
- **never-brick**：计量/审计写失败不得影响 wake 与 hub 主流程（降级不崩，沿用 loadout 的立场）。
- 新增落盘均在 `state/<company>/` 下，多公司天然隔离；telemetry 目录需纳入 `Makefile` shared 建目录步骤与 compose 挂载，不破坏现有目录布局。
- 现有测试全部保持通过。

## 验收标准

- [x] AC1：researcher 容器内真 LLM 冒烟 wake 一次，认证成功、正常回复。（2026-07-07 hardsmoke 栈：受控 IME 事件唤醒，session `6e9062a4`，一行回复且未做多余动作）
- [x] AC2：`kill` hub 容器主进程 → 容器自动重启，reconcile 正常接管（实测）。（`docker exec kill -INT 1` → RestartCount=1 → 重新 `[hub] start` → healthcheck 恢复 healthy）
- [x] AC3：一次真实 wake 后 telemetry JSONL 出现对应行，claude 角色 `cost_usd` 非空。（`wake.researcher.jsonl`：trigger=event、cost_usd=0.3284、ok=true）
- [x] AC4：伪造 verdict（非 verifier 发 `VERDICT:`）被 hub 拦截后，审计 JSONL 出现对应记录（测试覆盖）。（`test_hub_audit.py` 3 测钉死；另冒烟中 researcher 一条畸形 REPORT 真实落进 `audit.jsonl`）
- [x] AC5：全量既有测试绿。（489 passed = 479 既有 + 10 新增；`docker compose config` 实测 restart×9 + healthcheck×2 + telemetry volume×5）
