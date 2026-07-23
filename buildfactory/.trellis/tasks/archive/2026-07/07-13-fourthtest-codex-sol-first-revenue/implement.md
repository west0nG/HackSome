# Fourth Test 启动与验证清单

## 1. 并行基线取证

- [ ] 记录 `thirdtest` 当前容器名、容器 ID、启动时间和健康状态。
- [ ] 记录现有 `thirdtest` Observatory PID 与命令行。
- [ ] 确认 Host `8901` 未占用，`thirdtest` 继续占用 `8900`。
- [ ] 记录 Docker 当前内存占用，作为 Fourth Test 启动后的对照。

## 2. 创建隔离 worktree

- [ ] 从当前提交创建分支 `codex/fourthtest-run` 和 `/Users/weston/dev/BuildFactory-fourthtest`。
- [ ] 将 worktree 的 `accounts/foundagent`、`vm/.env.local` 安全指向主仓库现有文件，不复制 secrets。
- [ ] 将 worktree 的 `state/fourthtest` 指向主仓库 `/Users/weston/dev/BuildFactory/state/fourthtest/`。
- [ ] 确认 `state/fourthtest` 是全新状态；若已存在任何非本轮预检文件则停止并审计，不静默复用。

## 3. 固定 Agent 配置

- [ ] 在 worktree 的五个 `agents/*.yaml` 中设置 `provider: codex`、`model: gpt-5.6-sol`、`effort: xhigh`。
- [ ] 保持 `credentials: subscription`、charter、skills、hooks、MCP、permission、heartbeat 行为不变。
- [ ] 增加只用于 Fourth Test 的 Compose override：给 provisioner 设置 `COMPOSE_PROJECT_NAME=fourthtest`，给 Fourth Test mail-poller 固定独立 bucket、peer registry mount 与 `:8901` Peripheral。
- [ ] 运行 AgentSpec/Codex runtime 单测及 Compose config 渲染；确认所有容器名以 `fourthtest-` 开头、Host 端口为 `8901`，无 `thirdtest` volume 或 container target。

## 4. 无泄密认证预检

- [ ] 只以键名 + PASS/FAIL 检查 `accounts/foundagent` 中 Codex auth、Google key、cookies 与 secrets 文件存在。
- [ ] 在一次性临时 Codex HOME 中验证 `gpt-5.6-sol` 可用且 `xhigh` 被 CLI 接受；不使用正式 session 目录。
- [ ] 用只读 live Stripe API 探针验证认证成功、账户可收款；不输出 secret、余额或客户数据。
- [ ] 检查五个角色 MCP 配置都包含 Stripe，并验证 Codex materialization 不报错。
- [ ] 只以 PASS/FAIL 验证现有 Cloudflare 凭证具备创建/绑定新 R2 bucket 与部署 Email Worker 的权限；缺权时停止，不尝试扩大 token 权限或输出凭证内容。

## 5. 建立两套独立邮件路由

- [ ] 为 Fourth Test 创建独立 R2 bucket `foundagent-mail-fourthtest`，确认现有 R2 凭证可对其读写；不修改 `foundagent-mail` 中的现有对象。
- [ ] 若现有 R2 凭证仅限 `foundagent-mail`，停止上线并补齐最小的双 bucket 读写凭证；不得假定旧 token 自动覆盖新 bucket。
- [ ] 给 Email Worker 增加第二个 R2 binding，并以 `ReadableStream.tee()` + 两个定长流把同一封 raw MIME 写入两个 bucket；保留相同关联 key 与 envelope metadata。
- [ ] 扩展 poller 的可选 peer-registry 冲突检查和 `conflict/` 隔离语义；保持单公司、无 peer 配置时的历史行为不变。
- [ ] 构建固定版本的专用 mail-poller 镜像，记录 tag 与 digest；不得覆盖 `foundagent/mail-poller:latest`。
- [ ] 自动化验证双写、单边复制失败告警、两套独立 backend、成功、重试、unmatched、peer 不可读与跨公司同名 conflict。
- [ ] 先创建/验证新 bucket，再准备双写 Worker；此时仍保持线上旧 Worker 只写 `foundagent-mail`。
- [ ] 为两个 poller 分别挂载 own/peer registry：各自只写自己的 R2 bucket 和 Agent Inbox。
- [ ] 以临时 Compose override 和 `--no-deps` 只重建 `thirdtest-mail-poller`，固定上述版本镜像并只读挂载 Fourth Test registry；记录前后容器 ID，确认五个 Agent、Hub、Peripheral、Broker、Provisioner 与 Observatory 均未重启。
- [ ] 部署双写 Worker；只有两个 R2 `put()` 均成功才记录 fan-out 成功，单边失败必须在 Worker log/Activity Log 中带关联 key 告警，不能宣称具备 Cloudflare 未承诺的自动重试语义。
- [ ] 向随机未认领地址发送实机 smoke mail，验证两个 bucket 各自归档同关联 key 的 unmatched 副本，且没有 Agent 被唤醒。

## 6. 分阶段启动与 Initial Message

- [ ] 执行 Fourth Test 的 shared-dir 初始化，但不启动 Agent。
- [ ] 用 `docker compose -p fourthtest ... --no-build` 先启动 `hub / peripheral / broker / provisioner / mail-poller`；mail-poller 只消费 Fourth Test 独立 bucket。
- [ ] 等待 Hub 和 Peripheral 健康；再次确认 `thirdtest` 除计划中的 mail-poller 外，其余容器均未被重建。
- [ ] 向 `http://127.0.0.1:8901/ingest/webhook` POST 唯一 ID `fourthtest-initial-first-stripe-revenue-v1` 和 PRD 中的原文。
- [ ] 验证 CEO Inbox 只有该消息，消息 ID/正文一致，cursor 不存在或为 0。
- [ ] 启动 `ceo / researcher / builder / growth / verifier`；确认 Fourth Test mail-poller 与 `thirdtest-mail-poller` 同时健康且 bucket 不同。

## 7. 运行验收

- [ ] 五个 boot log 均出现 `provider=codex model=gpt-5.6-sol effort=xhigh`。
- [ ] CEO 的首个 wake 为 `event`，包含唯一 Initial Message；没有更早 heartbeat 或其他消息。
- [ ] CEO 首个 Codex turn 正常完成并留下 thread/transcript 与 usage telemetry。
- [ ] Hub、Peripheral 和五个 Agent 保持运行；没有 crash loop、认证错误或模型 ID 错误。
- [ ] 重新核对 `thirdtest` 五个 Agent、Hub、Peripheral、Broker、Provisioner 的容器 ID、状态、端口和 Observatory PID 均未变化；`thirdtest-mail-poller` 只有计划中的一次容器 ID 变更。

## 8. Observatory

- [x] 从 Fourth Test worktree 启动 `observatory/runner.py --company fourthtest daemon`，显式固定 `codex / gpt-5.6-luna / high` 与版本化 CUA image。
- [x] 写入独立日志和 PID 文件，确认 daemon 存活（launchd label `com.foundagent.observatory.fourthtest`）。
- [x] 确认至少生成一份 `state/fourthtest/observatory/` 报告，报告头记录 `provider: codex`、`model: gpt-5.6-luna`、`effort: high`。
- [x] 确认 Third Test Observatory PID、命令行和 Sonnet 配置均未变化。

## 9. 长跑与首款证据

- [ ] 持续观察机制健康；只修复编排/runtime/基础设施故障，不替 Agent 做选品与经营决策。
- [ ] 定期检查容器重启、Codex 限流、Docker 内存和 Observatory RED-ALERT。
- [ ] 真实 Stripe 首款发生后，记录成功时间、金额、币种、offer、渠道及 Stripe 可核验对象 ID；不把测试支付、operator 自付或非 Stripe 转账计入。
- [ ] 第一时间向用户报告达标；公司继续运行，直到用户明确要求停止。

## 回滚命令边界

- 常规回滚只允许对 Compose project `fourthtest` 执行 stop/down/recreate。
- 双路由切换回滚允许以 `--no-deps` 单独恢复 `thirdtest-mail-poller` 的原镜像与 mount；禁止触碰同 project 的其他服务。
- 只允许终止 Fourth Test Observatory PID。
- 回滚保留 `/Users/weston/dev/BuildFactory/state/fourthtest/`、worktree 和实验日志。
- 禁止运行无 `-p fourthtest` 的 `docker compose down/up`，禁止修改或删除 `state/thirdtest/`。

## 启动前最终门

- [x] `prd.md` 已完成收敛检查，无未决产品问题。
- [x] 用户已审阅 `prd.md`、`design.md` 和本清单，并于 2026-07-13 明确同意启动。
- [ ] 获得同意后才运行 `task.py start`，再加载 `trellis-before-dev` 进入执行。
