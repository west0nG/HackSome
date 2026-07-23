# Implement: Agent 邮箱身份（收件 v1）

> 顺序即依赖。每步含验证命令。全程 mock 后端可测（AC5），真 Cloudflare 只在 M6。

## M1 注册表 + CLI + inbox peek ✅ 2026-07-08

- [x] `orchestration/mailbox.py`：registry.jsonl append-only 事件 + reduce 读；flock（claim 读+校验+append 全程持锁，比 role.py 更紧）；存 `state/<company>/mailboxes/`
- [x] 子命令 `claim/mine/list/add-receiver/remove-receiver`；owner 身份门（exit 2）；无 rename/release；超限报错列出已有地址；`resolve()` 供 M3（⚠️注册表读错误抛异常——poller 须留信重试，勿归 unmatched）
- [x] 校验：正则/保留名单/全局唯一/上限 3（MAILBOX_CAP）/幂等；claim 侧不做大小写归一（大写直接拒），resolve 查询侧 lowercase
- [x] `FileInbox.peek(key)` 只读快照游标不动；CLI `python3 -m orchestration.receive_tool --peek [--agent KEY]`（无 --peek 拒绝，不给 Bash 留误消费入口）
- [x] 测试：test_mailbox.py 34 例（含 subprocess 真并发）+ test_inbox.py/test_receive.py 补 9 例；orchestration 325 passed
- 验证：`python -m pytest orchestration/tests/ -q` ✅

## M2 adapter 升级（`peripheral/adapters/email.py`）✅ 2026-07-08

- [x] native 契约扩为 `{from, subject, text, links, message_id, to}`；`to` 透传；不可信标注行；正文截断；`id=message_id:to`（+旧 preview/link 回退兼容；UNTRUSTED_MARKER/BODY_TEXT_MAX 常量导出）
- [x] 更新 `peripheral/tests/test_adapters.py`（16 passed，含 fan-out 去重/截断边界/id 回退矩阵）
- 验证：`python -m pytest peripheral/tests/ -q`

## M3 poller（`peripheral/email/poller.py`）✅ 2026-07-08

- [x] backend 接缝类 `MailBackend`（`fetch_batch/archive_processed/archive_unmatched`，`MailBlob{key,raw_bytes,metadata}`）+ `R2Backend`（boto3 懒导入进构造函数，list `inbox/` → copy+delete 归档）+ `MockBackend`（本地实证无 boto3 环境测试全绿）
- [x] 主循环：解析（stdlib email，text/plain 优先→decoded payload 回退；链接正则+去尾标点+去重）→ resolve receivers（registry 抛错 → WARN 留信重试，绝不归 unmatched）→ 逐 receiver POST `/ingest/email`（不短路，尽量多投）→ 全 2xx 才归档 processed；env 见模块 docstring（R2_ENDPOINT/R2_ACCESS_KEY_ID/R2_SECRET_ACCESS_KEY 必填、R2_BUCKET=foundagent-mail、INGEST_URL=http://peripheral:8900、MAIL_POLL_INTERVAL=30、注册表沿用 MAILBOX_ROOT|COMPANY）
- [x] `peripheral/tests/test_email_poller.py` 13 例：命中（含大小写 envelope）/fan-out 两 POST 一归档/unmatched 零投递/500 留队重试不重复归档/部分失败整封 defer/registry 错误留队/坏信不断批 + MIME 解析矩阵（multipart 取 plain/无 Message-ID 容忍/链接清洗）
- 验证：`python -m pytest peripheral/tests/ -q` ✅ 29 passed（orchestration 331 passed 回归无损）

## M4 Worker + compose 接线 ✅ 2026-07-08

- [x] `peripheral/email/worker/`（index.ts 哑 Worker 含 FixedLengthStream + wrangler.jsonc 绑定 MAIL_BUCKET + README 运维手册）；`peripheral/email/Dockerfile`（python3.12-slim + boto3，实测构建+镜像内 import 全通）+ 根 `.dockerignore`（allowlist，防 2G context）
- [x] docker-compose 加 `mail-poller` 服务（纯 +38 行追加；env_file vm/.env.local 承载 R2 凭证；registry 只读挂载 /shared/mailboxes；depends_on peripheral）；⚠️修复过一处集成撞点：INGEST_URL 由完整路径改回 base URL（poller 自己拼 /ingest/email）
- [x] 回归：`docker compose config -q` ✅；全仓 `.venv-cua/bin/python -m pytest -q` **616 passed** ✅
- 验证：`docker compose config -q`；`python -m pytest -q`（全仓）

## M5 skill + bootstrap 引导

- [x] `agents/assets/skills/claim-mailbox/SKILL.md`（design §2.6：mine → list → claim 流程 + 命名三原则/反例 + 共用取舍 + 边界声明）✅
- [x] `agents/assets/skills/check-email/SKILL.md`（design §2.6：peek 循环含命令示例 + 三条反默认 + 不可信提醒）✅
- [x] CEO charter 加「入职引导认领邮箱」判断力条款（起步/新部门入职时发 claim goal；名字必须 agent 自己起）✅
- [x] 过 no-generic 三道检验自查（AC6）✅（M5 agent 逐条自查通过，风格模板 send-goal/set-objective）

## 质量核查（trellis-check，2026-07-08）✅

- [x] 全维度通过：spec 合规 / AC2-AC6 机制 / 跨组件接缝 / 代码质量；86 个本任务用例
- [x] check 修复：**agent 容器缺注册表挂载**（compose x-agent anchor 加 `/shared/mailboxes` rw + `MAILBOX_ROOT` env + `make shared` 预建 chmod——否则容器内 claim 落容器临时层，生产失效）；2 处注释笔误
- [x] check 后主会话补齐：①skill 接线（ceo/researcher/builder/growth 四个 yaml + test_resident_loadout/test_spec pins；verifier 刻意不挂——极简评审席）②design §2.7(3) IME 显示收件地址（poller native +`address`、adapter 头行渲染、双侧测试）③M4 遗留 INGEST_URL 撞点修复
- [x] 全仓回归 **617 passed**

## M6 真跑 e2e（AC1/AC2，SOP 硬门）

- [x] 操作员一次性动作 ✅ 2026-07-08：用户给了 Global Key + R2 密钥对（account/zone 映射曾记反，已核对纠正）；Email Routing 本来就 ready，**零 dashboard 点击**
- [x] `wrangler r2 bucket create` + `wrangler deploy`（+`workers_dev: false` 修正，commit 0231e43）+ REST 设 catch-all 并回读验证 ✅
- [x] **plumbing 真跑全绿** ✅：真邮件 → Worker(`outcome:ok`) → R2(8980B+metadata) → 隔离环境 claim+`run_once`(`processed:1`) → growth inbox IME（标注/发往/组合id 全对）→ peek 可见 → R2 归档 processed/；证据 `research/e2e-evidence/plumbing-live.md`
- [x] AC1 三条件场景 ✅ 2026-07-08 fleet 真跑：growth 认领 `ivy@foundagent.net`（45s，persona 名）→ 干扰信 6/7 位、Medium 登录码第 8 位 → 任务中途 peek 捞对 → Medium @ivy_45376 注册成功、ledger done → 干扰信后续 wake 正确忽略（Quora 陷阱未咬钩）
- [x] add-receiver 后注入一封 → growth/builder 双 inbox 各一条 IME（id `:growth`/`:builder`）✅（AC2）
- [x] e2e 证据 `research/e2e-evidence/ac1-ac2-fleet-live.md`（附计划外收获：Gumroad 注册也解锁）✅

## 回滚点

- M1-M3 纯新增文件 + adapter 小改，逐 commit 可回退
- M4 compose 改动独立 commit；回滚 = 删 service 块
- 云端资源（Worker/bucket/catch-all）不进代码回滚范围；catch-all 可一键改回 drop

## 收尾检查（task.py start 前）

- [x] implement.jsonl / check.jsonl 填真实条目（peripheral 契约 spec + 本任务两份 research）
- [x] 用户已审 prd/design/implement 三件套（07-08 多轮迭代拍板）
