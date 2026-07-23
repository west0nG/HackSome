# 邮箱改为按 Company 认领

## Goal

将 `foundagent.net` 域名下的邮箱认领、使用与隔离边界从 Department/Agent 调整为 Company。小型 Company 内不再用邮箱隔离 Department；不同 Company 之间必须保持地址、邮件内容与发送能力的严格隔离。

## Background

- 当前 Company 多为小型或“一人公司”，Department 间邮箱隔离会阻碍信息流转，实际收益很低。
- 邮箱的核心用途是在共享 `foundagent.net` 域名与基础设施下隔离不同 Company，并让 Company 使用稳定地址注册外部身份。
- 当前注册表虽然位于 `state/<company>/mailboxes`，但 claim owner、每 Agent 配额、receiver fan-out 和发件 gate 都绑定 `AGENT_KEY`（`orchestration/mailbox.py:15-25,171-205,230-280`、`orchestration/email_send.py:256-293`）。
- 旧邮件设计已经记录：per-company 注册表只适用于单一生产 Company；多个生产 Company 共用域名时必须升级为全局地址注册表（`.trellis/tasks/archive/2026-07/07-08-agent-email/design.md` §2.4）。
- 旧版 `check-email` 曾通过 `orchestration.receive_tool --peek` 让 Agent 浏览自己的未读 Inbox；V7 在 commit `2fecc2b` 中删除该 Skill 与 CLI，并明确禁止 LLM runtime 直接浏览 Inbox。新机制只复用“任务中查看验证码”的体验，不恢复旧内部状态访问。
- 当前基础设施以一个 Compose stack 对应一个 Company，Company State、Hub、网络和控制面状态均由 `COMPANY` 隔离（`README.md:7`、`docker-compose.yml:5-148`）。

## Requirements

### R1：Company 级永久认领

- 邮箱认领主体必须是 Company，不得是 Department、Role、Worker 或单个 Agent。
- 每个 Company 固定最多认领 5 个 `foundagent.net` 地址；配额不随 Department/Agent 数量增长，也不按 Company 单独配置。
- 只有 CEO 可以代表 Company 认领新地址。
- 地址在所有 Company 之间全局唯一；并发认领同一地址时只能有一个 Company 成功。
- 同一 Company 重复认领同一地址幂等。
- 地址永久绑定原 Company，不可改名、释放、转移或重新分配。
- 邮箱本地部分由 CEO 自主选择，并沿用现有格式校验、保留名、禁止 `+` 与全局先到先得规则。

### R2：角色权限

- CEO 可以认领、列出 Company 地址，并接收普通入站邮件通知；CEO 不直接发件。
- Department 不具备认领能力，但可以列出 Company 地址、全量只读 peek Company 邮件并从任一 Company 地址发件；Skill 应建议常规外部执行优先创建 Goal 委派给 Worker，而不是用权限硬性禁止 Department。
- Worker 可以列出 Company 地址、全量只读 peek 当前 Goal 的 Company 邮件，并从任一已认领的 Company 地址发件。
- Verifier 不具备任何邮箱能力，不得读取邮件或验证码。
- 所有能力必须通过确定性 Company Hub 方法暴露；Agent runtime 不得挂载或直接浏览全局注册表、Company 邮件存储或内部 Inbox。

### R3：跨 Company 入站隔离与 CEO 通知

- 域名级路由必须先用全局地址注册表确定目标 Company，再把邮件写入该 Company 独立的控制面存储。
- 任一 Company 不得读取、接收或管理另一 Company 的邮件。
- 已认领地址的普通来信只唤醒所属 Company 的 CEO，不向 Department 广播。
- CEO 可通过现有 Hub/Goal 机制把后续工作委派给相关 Department 和 Worker。
- 未认领地址不得进入任何 Company；注册表不可读或目标 Company 存储失败时必须 fail closed 并保留邮件待重试。

### R4：Department/Worker 全量只读 peek

- 外部注册与验证码处理通常由一次性 Worker 执行，但系统不得禁止 Department 在必要时直接完成同类流程。
- Department 每次 peek 返回当前 Company 最近 100 封邮件，不按地址过滤，也不消费邮件。
- Worker 不需要预先知道 Company 拥有多少地址；每次 peek 返回当前 Company 在该 Goal 启动以来收到的全部邮件。
- 返回集合最多为最近 100 封，并在截取后按接收时间正序输出。
- Worker 根据当前任务预期的发件方、主题、目标邮箱或正文自行识别目标邮件；同一 Company 的并行 Worker 看到相同 Company 邮件集合。
- peek 不消费邮件、不推进 CEO cursor，也不阻止 CEO 的正常通知。
- Worker 重启、恢复或验收失败返工时仍绑定原 Goal，必须继续看到原 Goal 时间窗口内先前收到的邮件。
- 邮件正文和链接属于敏感、不可信外部内容；peek 的方法缓存与 telemetry 不得额外持久化验证码、magic link 或完整正文。

### R5：Company 级发件

- 合法 Department 与当前 Goal 的合法 Worker 都可以从 Company 地址发件；CEO 与 Verifier 不具备发件能力。
- 发件地址必须已在全局注册表中永久归属当前 Company；不能使用未认领地址或其他 Company 地址。
- 保留现有 Company 30 次/滚动 24 小时、单地址 15 次/滚动 24 小时、发送前 reserve、失败不退款和 Provider 幂等语义。
- 发件重试必须使用 Hub request id 保证网络与方法层不会重复发送。

### R6：Skills 与产品表面

- `claim-mailbox` 改为 CEO 专属的 Company 地址认领 Skill，不再出现 Agent owner、receiver、mine、add-receiver 或每 Agent 配额。
- `check-email` 改为 Department 与 Worker 可用的 Skill，通过 Hub 全量只读 peek Company 邮件，不恢复 `receive_tool --peek`；文案应建议常规外部操作优先委派 Worker，而不是禁止 Department。
- `send-email` 改为 Department 与 Worker 可用的 Company 发件 Skill，不再使用 `AGENT_KEY` receiver gate；文案建议 Department 把常规外部执行委派给 Worker，但不阻止直接发件。
- CEO loadout 只加入 `claim-mailbox`；Department 与 Worker loadout 都加入 `check-email` 和 `send-email`；Verifier loadout 不加入邮件 Skills。

### R7：兼容范围

- 不迁移、转换或兼容此前 Company 的 per-Agent/per-Department 邮箱注册表。
- 新机制从新的全局注册表开始；历史归档任务保留原样作为过去设计证据。

## Acceptance Criteria

- [x] **AC1 / R1**：两个 Company 并发认领同一 localpart 时只有一个成功；同 Company 重试幂等；第 6 个地址被拒；系统不存在 rename/release/transfer 路径。
- [x] **AC2 / R2**：CEO 可认领/列出/接收通知，合法 Department 与 Worker 都可 list/peek/send，Verifier 无邮件能力；各角色边界由 Hub 方法测试证明。
- [x] **AC3 / R3**：向 Company A 与 B 的地址分别注入邮件时，只写入各自 Company store，并只唤醒各自 CEO；A 无法看到 B 的地址内容或邮件。
- [x] **AC4 / R3**：未认领地址进入 unmatched；全局注册表损坏或 Company store 写入失败时邮件保持 pending，恢复后可重试且不重复。
- [x] **AC5 / R4**：Department peek 返回 Company 最近 100 封邮件；Worker peek 返回 Goal 创建以来最多最近 100 封邮件；两者均非消费、按时间正序，Worker 重启/返工仍可看到原窗口邮件，CEO 通知不受影响。
- [x] **AC6 / R4**：peek 的 control request cache 与 telemetry 不包含正文、链接、验证码或 magic link；所有 LLM runtime 均无原始邮件/注册表/Inbox 挂载。
- [x] **AC7 / R5**：Department 与 Worker 可从本 Company 已认领地址发送；未认领地址、其他 Company 地址、CEO 与 Verifier 均被拒；现有两级配额与幂等规则通过并发测试。
- [x] **AC8 / R6**：角色 loadout 与三个邮件 Skills 符合新权限；自动化检查禁止旧 owner/receiver/`receive_tool --peek` 文案和命令回归。
- [x] **AC9 / R7**：新代码不读取旧 per-Agent 注册表，不包含迁移或兼容分支。
- [x] **AC10**：相关单元、集成、完整项目测试及 Company Compose、全局 mail-router Compose 校验全部通过，后端契约文档同步到当前实现。

## Out of Scope

- 旧 Company 邮箱数据迁移或自动重新认领。
- 地址改名、释放、转移、回收或 Company 注销后的再分配。
- Department/Agent 私有邮箱、receiver 列表和邮件 fan-out。
- Verifier 邮箱访问。
- 更换 `foundagent.net`、Cloudflare Email Routing、R2 或 Resend provider。
- Worker 查看当前 Goal 创建之前的历史邮件。
- 跨宿主机运行多个 Company；当前全局唯一注册表基于同一宿主机共享文件与 `flock`。
