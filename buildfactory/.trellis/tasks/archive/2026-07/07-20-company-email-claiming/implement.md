# 实施计划：Company 级邮箱认领

## 1. 控制面存储与全局注册表

- [x] 在 `CompanyLayout` 中增加内部 `mailboxes` 域及初始化目录；确认该目录不进入任何 LLM runtime 挂载。
- [x] 重写 `orchestration/mailbox.py`：从 Agent owner/receiver 事件模型改为永久 `address -> company` 全局注册表。
- [x] 固定 Company 配额为 5，保留名称格式、保留名、全局唯一、同 Company 幂等与跨进程 flock。
- [x] 删除 `mine`、`add-receiver`、`remove-receiver`、Agent cap 和 `MAILBOX_CAP` 产品语义。
- [x] 实现 Company 邮件 journal、稳定去重、CEO 通知 cursor 与 Goal 时间窗口查询。
- [x] 重写 `orchestration/tests/test_mailbox.py`，覆盖两 Company 隔离、并发同名 claim、固定 5 个配额、永久无 release/transfer、消息去重和最近 100 封窗口。

## 2. 全局入站 mail-router

- [x] 将 `peripheral/email/poller.py` 从“解析为 Agent receivers 并 fan-out”改为平台级 router：全局注册表解析 Company，再写对应 Company mail store。
- [x] 保留 Cloudflare Worker、R2 backend、MIME 解析、pending/processed/unmatched 与故障重试契约。
- [x] 确保注册表错误或 Company store 写入错误时 R2 对象保持 pending；只有未认领地址进入 unmatched。
- [x] 使用稳定 source id 保证“Company journal append 成功、R2 archive 前崩溃”重试不重复。
- [x] 重写 `peripheral/tests/test_email_poller.py`，覆盖 Company A/B 路由、未认领、损坏注册表、不可写 store、重试去重与归档矩阵。

## 3. Company Hub 邮箱方法

- [x] 给 `CompanyHub` 注入不可由业务 payload 覆盖的 `company_id` 与全局 mail root。
- [x] 增加 CEO 方法 `claim_company_mailbox`、`list_company_mailboxes`。
- [x] 增加 Department/Worker 方法 `list_company_mailboxes`、`peek_company_email`、`send_company_email`。
- [x] Department peek 必须校验 active/self-bound resident actor；Worker 邮箱方法必须校验 actor、goal_id、worker_id 与 Scheduler Goal 绑定；Verifier 调用必须 forbidden。
- [x] 在 Hub `tick()` 中把 Company mail journal 的新记录可靠、稳定去重地投递给 CEO，并在成功后推进通知 cursor。
- [x] 为 Department peek 实现最近 100 封；为 Worker peek 实现 Goal `created_at` 时间下界与最近 100 封；两者均正序输出且非消费。
- [x] 扩展 `MethodAdapter` 的敏感只读方法策略：不持久化完整 peek response，telemetry 不记录正文/链接/验证码。
- [x] 扩展 Hub/adapter 测试，覆盖 CEO 单播、Department/Worker 全量 peek、Worker 返工可见、角色边界、跨 Company 不可见和敏感审计不落正文。

## 4. Company 级发件

- [x] 重构 `orchestration/email_send.py`，把 Agent receiver gate 替换为“from 地址属于 Hub 当前 Company”。
- [x] 仅允许合法 Department 或当前 Goal 的合法 Worker 通过 Hub 方法触发发件；业务 payload 不接受 company 或 actor 字段。
- [x] 使用 Hub request id 作为发送 reservation 与 Resend idempotency key。
- [x] 保留 Company 30/24h、单地址 15/24h、先 reserve、失败不退款、HTTP 锁外执行和发送 ledger。
- [x] 重写 `orchestration/tests/test_email_send.py`，覆盖 Department/Worker 成功、CEO/Verifier 禁止、他 Company 地址禁止、未认领禁止、并发配额与幂等重试。

## 5. Skills 与角色装备

- [x] 重写 `agents/assets/skills/claim-mailbox/SKILL.md` 为 CEO 专属 Company 认领流程。
- [x] 恢复并重写 `agents/assets/skills/check-email/SKILL.md`：Department/Worker 通过 Hub 全量 peek Company 邮件，不使用旧 Inbox CLI，并建议常规操作优先交给 Worker。
- [x] 重写 `agents/assets/skills/send-email/SKILL.md` 为 Department/Worker 的 Company 发件流程，并用引导而非权限要求优先委派 Worker。
- [x] 在 `agents/ceo.yaml` 仅加入 `claim-mailbox`；全部 Department YAML 与 `agents/ephemeral/worker.yaml` 都加入 `check-email`、`send-email`；Verifier YAML 不加入邮件 Skills。
- [x] 更新 skill catalog/loadout 测试，禁止旧 `mine/add-receiver/remove-receiver/receive_tool --peek` 文案回归。

## 6. 部署与配置

- [x] 给 Company Hub 增加 `state/_mail` 控制面挂载；验证 Agent、Department、Worker、Verifier 均无该挂载。
- [x] 新增平台级 mail-router Compose 入口与专用 image/entrypoint，挂载全局 registry 与所有 Company state，读取 R2 凭据。
- [x] 在 Makefile 增加 `mail-up`、`mail-down`、`mail-logs`，保证普通 Company `up/down` 不复制或误删平台 router。
- [x] 将 Hub 所需 Resend 凭据通过控制面 env 注入，不把全局 registry 或 Company mail store 暴露给 Worker。
- [x] 更新 Compose 合同测试与运维 README，说明平台 router 单实例、Company 栈多实例的启动顺序和恢复语义。

## 7. 规范与清理

- [x] 更新 `.trellis/spec/backend/peripheral-layer-contracts.md`：全局 router、Company journal、CEO 通知与 Worker peek。
- [x] 更新 `.trellis/spec/backend/three-layer-agent-company-contracts.md`：角色邮件权限与受控 Hub 方法。
- [x] 删除或改写所有仍描述 Agent/Department owner、receiver fan-out、每 Agent 3 个地址和旧 `receive_tool` 的注释、测试与文档。
- [x] 保留旧归档任务作为历史证据，不改写 archive 内容。

## 8. 验证命令

- [x] 定向测试：

  ```bash
  python3 -m pytest \
    orchestration/tests/test_mailbox.py \
    orchestration/tests/test_email_send.py \
    orchestration/tests/test_company_hub_v7.py \
    orchestration/tests/test_method_adapter.py \
    orchestration/tests/test_compose_accounts.py \
    peripheral/tests/test_email_poller.py \
    peripheral/tests/test_adapters.py -q
  ```

- [x] Agent/loadout 合同测试：

  ```bash
  python3 -m pytest agent/tests/test_skill_catalog.py \
    agent/tests/test_resident_loadout.py \
    agent/tests/test_spec.py -q
  ```

- [x] 全量项目测试（显式限制仓库测试目录，避免收集 `state/` 内插件缓存）：

  ```bash
  python3 -m pytest agent/tests orchestration/tests peripheral/tests -q
  ```

- [x] Compose 校验：

  ```bash
  COMPANY=foundagent ACCOUNT=foundagent docker compose config -q
  docker compose -f docker-compose.mail.yml -p foundagent-mail config -q
  ```

- [x] 离线双 Company 集成测试：同名并发 claim 只有一个成功；向 A/B 地址各注入一封 mock 邮件，只进入各自 store；A Worker 无法 peek 或从 B 地址发件。

## 9. 风险点与回滚点

- 全局注册表是永久身份源：任何测试必须使用临时 root，禁止清空真实 `state/_mail`。
- 修改 `MethodAdapter` 时保持其他方法现有幂等缓存与完整审计语义，只对明确标记的敏感只读方法例外。
- mail-router 写入 Company store 与 R2 archive 的顺序不可反转。
- Hub CEO 通知 cursor 只能在 Inbox append 成功后推进。
- 回滚时先停平台 mail-router，确保 R2 保留 pending 邮件；不得删除全局注册表或 Company mail journal。

## 10. 最终验证结果

- 2026-07-20：仓库实际测试目录全量回归通过，`418 passed`。
- Company Compose 与独立 `foundagent-mail` Compose 配置校验通过。
- `mail-router` 镜像真实构建通过，容器内可导入 router 与 Company mailbox 模块。
- 三个邮件 Skill、Trellis context、Python 编译和 `git diff --check` 全部通过。
