# AC3 真跑记录（2026-07-10, CEO-only 沙箱）

形态：cp state/secondtest → state/idletest（11 done goals、inbox 清空、CEO session_id 删除=全新会话、codex auth 保留）；`COMPANY=idletest ACCOUNT=foundagent CEO_HEARTBEAT_SECS=120 docker compose -p idletest up -d hub ceo`；测试侧经 hub 容器扮部门/verifier（identity gate 走真协议），配套桩产物写入 /company。

## 唤醒序列（telemetry: ac3-wake-telemetry.jsonl）

| # | trigger | 时刻 | 结果 |
|---|---------|------|------|
| 1 | **heartbeat**（空账本 11 done） | 04:14 | ✅ 派单 growth：Marketplace 上架就绪调查（ac3-hb1-goal.json）。goal 文本内明确持有 19:30Z 窗口约束；"Independent direction review returned GO"=先过了 decide-direction |
| 2 | event（Marketplace 阻塞报告） | 04:19 | 派单 builder：启用 2FA（ac3-event-goal-2fa.json）——结果唤醒的正常跟进 |
| 3 | event（2FA done） | 04:22 | 派单 growth：正式上架（ac3-event-goal-marketplace.json） |
| 4 | event（上架 done，公司进入吸附态） | 04:23 | **无派单**（结果唤醒无强制，合法） |
| 5 | **heartbeat**（空账本 14 done，全办完+全新鲜+只等 19:30Z——secondtest 睡 7 小时的精确场景） | 04:26 | ✅ 派单 builder：扫描覆盖加固（ac3-hb2-goal.json，阶梯第 2 层"改进现有资产"）。CEO 原话："Ledger was empty, so I dispatched a side-quest that advances the product without touching fresh outreach threads." |

## 四条判据

1. 每个空账本心跳均以真实派单结束：2/2 ✅（心跳 #1、#5）
2. 无重复灌水：5 个 goal（含 11 个历史）两两不同（就绪调查→2FA→上架→覆盖加固为递进链）✅
3. 派单节制：每次 wake 派 1 个（其判断，非规则强制）✅
4. 无自我豁免话术："no new signal"/"done recently" 类表述零出现；wait 被持有而非用作空手理由 ✅

结论：AC3 通过。附注：wake#2 telemetry ok:false("Reconnecting... 2/5 request timed out")但派单已落账——codex 传输重连抖动，不影响行为判定。
