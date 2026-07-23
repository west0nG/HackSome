# Implement — agent 发件轨（Resend）

## M1 域名 provisioning（inline，一次性）

- [ ] Resend `POST /domains` 建 foundagent.net（us-east-1），取回待写 DNS 记录
- [ ] Cloudflare API 写入记录（仅 `send` 子域 + `resend._domainkey`；根域 MX/SPF 不动）
- [ ] `POST /domains/{id}/verify`，轮询至 verified
- [ ] 事实存档 `research/resend-domain-setup.md`（域 ID、记录清单、verified 时间戳）
- 验证：Resend dashboard/API 域状态 = verified；`dig MX foundagent.net` 仍指 CF Email Routing

## M2 email_send 模块 + 单测（dispatch trellis-implement）

- [ ] `orchestration/email_send.py`：CLI 契约、三道门、send_ledger.jsonl（reserve→HTTP→回填）、Idempotency-Key、fail-closed
- [ ] `orchestration/tests/test_email_send.py`：三道门、账本序、并发 flock、失败占额、拒绝文案含恢复时间（HTTP 全 mock）
- 验证：`python3 -m pytest orchestration/tests/test_email_send.py -q` 全绿；`python3 -m pytest orchestration/tests -q` 无回归

## M3 send-email skill + 接线（dispatch trellis-implement，可与 M2 同批）

- [ ] `agents/assets/skills/send-email/SKILL.md`（design §7 三道检验要点；零 HTML 注释）
- [ ] 5 个角色 yaml `skills:` 各追加 `assets/skills/send-email`
- [ ] `agent/tests/` 中 loadout 相关断言若有硬编码 skill 清单则同步
- 验证：`python3 -m pytest agent/tests -q` 全绿

## M4 真 e2e（主 session 亲手跑，不 mock）

- [ ] 容器内以认领地址 A 发往本域认领地址 B（真实 Resend 外发）
- [ ] 收件轨回流：B 的 inbox 出现该邮件 IME（允许分钟级延迟，耐心 ~10min）
- [ ] 拒绝路径①：未认领 from → exit 1 + claim-mailbox 指引
- [ ] 拒绝路径②：`EMAIL_SEND_DAILY_COMPANY=1` 发第二封 → exit 1 + 恢复时间文案
- 验证：AC2/AC4 逐条对照 prd.md

## M5 收尾

- [ ] dispatch trellis-check（对照 prd/design 全量检查）
- [ ] trellis-update-spec：发件契约进 `.trellis/spec/backend/`（若 peripheral-layer-contracts 有邮件节则并入）
- [ ] commit（Phase 3.4；多 session 共享工作树——只 add 本任务文件）
- [ ] `/trellis:finish-work`

## 回滚点

- M1 后可独立回滚：删 Resend 域 + 删 CF 子域记录，收件轨不受影响
- M2-M3 纯增量文件，`git revert` 即回滚
