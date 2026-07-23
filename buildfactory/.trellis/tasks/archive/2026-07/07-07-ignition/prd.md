# First Test 点火与观测期运行

## 背景 / 目标

前两个子任务就绪后，正式起 firsttest 公司，验证首个 CEO wake，进入无人干预观测期。本任务的交付物是一份点火 runbook + 一次成功点火 + 运行记录；按"一次性动作不留 repo 脚本"的立场，runbook 落在本任务目录。

## 需求

1. **点火 runbook**（本任务目录 `runbook.md`）：
   - 前置检查：hardening 与 observatory 已合入；foundagent 栈确认 down（避免争抢 @Solvotheagent 等同一批真实外部账号）；`accounts/foundagent/` 关键件在位（secrets.env、google-sa.json、cookies/storage-state.json）；镜像可构建。
   - 点火命令：`make up COMPANY=firsttest ACCOUNT=foundagent`（单栈运行不需要 `-p`；runbook 注明将来并发多公司时须显式 `docker compose -p`）。
   - 首个 CEO wake 验证清单与停机程序（`make down` + 触发 C 类终局综合）。
2. **完全自主冷启动**：不注入任何种子消息，CEO 凭空收件箱 + 心跳自行进入 find-opportunity。
3. **首 wake 验证**：CEO 心跳唤醒成功、无认证错误、开始定方向；telemetry 出现首条 wake 记录。
4. **观测期运行**：observatory runner 启动并常驻；用户手动值守，不设时限。
5. **运行记录**：点火时间、期间任何人工干预（包括临时 down/up）、停机时间，留档本任务目录，供终局综合引用。

## 约束

- 外部动作全部真实执行（用户已拍板），点火后不做任何注入/引导——人工干预仅限止损（`make down`），且必须记录在运行记录里。
- 点火前 `make loadout-check COMPANY=firsttest` 离线校验一次装备物化。

## 验收标准

- [x] AC1：firsttest 全部服务 up，hub/peripheral healthy。（2026-07-07 09:58 UTC 启动，9 容器全 Up，双 healthy）
- [x] AC2：CEO 首次心跳 wake 成功并开始定方向（真 LLM，logs + transcript 可证）。（10:07 首醒 88.7s / $0.40：识别冷启动 → find-opportunity 选 info-product 形态 → 向 researcher 派出首个调研任务 gdc5b6359，带隐匿验收标准；researcher 已事件唤醒开工）
- [x] AC3：observatory runner 常驻运行，产出第一份报告（B 类即可）。（daemon pid 常驻，启动即产出基线全公司检查报告 20260707T095806Z.md）
- [x] AC4：runbook 与运行记录在任务目录留档。（runbook.md + run-log.md，干预记录含"提前首次心跳"一条）
