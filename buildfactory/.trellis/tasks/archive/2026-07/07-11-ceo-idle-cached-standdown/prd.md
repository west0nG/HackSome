# CEO 空闲吸附态：每次 heartbeat 重新执行 when-idle

> 状态：已实现并上线 thirdtest（2026-07-11）
> 现场来源：`.trellis/tasks/07-10-thirdtest-opus-longrun/research/observations.md`（OBS-3）

## 目标与用户价值

当公司没有 Goal 在执行时，CEO 的每次 proactive heartbeat 都要重新调用并从头执行
`when-idle`；历史上的“先等一等”判断只能作为本次决策的输入，不能成为跳过后续
idle pass 的永久许可证。

修复要同时减少公司空转和昂贵假工作：thirdtest 中 CEO 连续数小时没有派单，却在每次
wake 继续读取完整续跑上下文、复述同一结论并产生模型费用。

## 已确认的背景

### 现场时间线

- thirdtest 的 CEO 从 2026-07-10 08:05 UTC 起始终复用同一个 Claude session
  `dd70a6f8-e6d6-4dc2-8107-fc0f0a35b441`；这是 `agents/ceo.yaml:30` 明确配置的
  `session: resume`，不是意外串会话。
- `when-idle` 在整个 transcript 中只通过 Skill 工具加载过一次：
  `state/thirdtest/sessions/ceo/projects/-home-kasm-user/dd70a6f8-e6d6-4dc2-8107-fc0f0a35b441.jsonl:9`。
- CEO 前半段仍会主动派单；13:00 UTC 之后的派单 heartbeat 出现在 16:02、17:07、
  18:38，最后一次是 Pinterest 评估 Goal。因此，“第一次 wake 后立即永久躺平”不是
  准确描述。
- 稳定吸附从 19:41:10 UTC 开始（同一 transcript `:997`），一直持续到至少次日
  02:22:22 UTC（`:1267`）：**6 小时 41 分、连续 27 个 heartbeat，没有一次派单**。
- 这 27 次空手 heartbeat 合计消耗约 **$47.24**；尾部输出逐渐收敛成 79–120 token
  的近似模板：“nothing in flight / germination wait unchanged / standing down”。
- 整个已取证区间共有 42 个 heartbeat，只有 5 个 heartbeat 产生派单。问题不是 CEO
  从未理解规则，而是长会话中后形成的等待结论压过了早期加载的规则。

### 等待结论进入了持久状态

CEO 把“SEO 发芽期 + 外部门槛”的等待姿态写入
`state/thirdtest/company/direction/OVERVIEW.md`：

- `:16-17`：两个时钟未触发，所以不派单；此时派单会是 padding；
- `:87-93`：把等待锚定到约 2026-07-17，并把频繁 heartbeat 定性为合理发芽；
- `:94-99`：进一步写成“多数 idle heartbeat：便宜查账本后 stand down”。

最后一条与 `when-idle` 的不可空手契约直接冲突。CEO 在 02:22 heartbeat 又按这条持久
结论退出，说明只要本次 prompt 没有重新激活技能，旧经营判断就可能被当成本次的答案。

### 当前 prompt 与测试的缺口

`orchestration/agent_loop.py:151-155` 每次只发送同一段软提示：

> your charter's idle duties apply — find the next thing worth doing

它没有点名 `when-idle`，没有要求本次重新调用 Skill，也没有声明上一次 idle verdict
不能直接复用。对应单测 `orchestration/tests/test_agent_loop.py:742-749` 只断言提示里有
`idle duties` 且没有 worker 的 stop 文案，没有钉住重新调用技能与两条账本分支。

完整 CEO charter **确实会在每次 wake 重传**：`agent_loop` 每轮把同一份 charter 传给
`wake()`（`orchestration/agent_loop.py:488-492`），Claude resume argv 仍会带
`--append-system-prompt`（`agent/runtimes/claude_code.py:121-134`）。charter 本身也已在
`agents/assets/ceo-charter.md:80-84` 写明“每个空 heartbeat 都 follow when-idle”。因此
缺口不是 charter 消失，而是本轮直接 user prompt 仍然允许模型不调用 Skill、拿旧结论
回答泛化的“briefly check”。

07-10 的 `.trellis/tasks/archive/2026-07/07-10-when-idle-rewrite/` 已把技能正文改成
“空账本必须派单”，并用两个连续空账本 heartbeat 验收通过。thirdtest 证明技能内容本身
已经足够明确，缺口是后续 heartbeat 没有重新进入它。

## 根因判定

每次 wake 虽然都有完整 charter，但 `when-idle` 技能正文只通过 Skill 工具加载过一次；
直接 heartbeat user prompt 又只给出泛化的“idle duties”提醒，没有要求重新调用 Skill。
随着 CEO 反复形成并持久化等待结论，它可以用旧 verdict 回答“briefly check”，在表面上
响应本轮 prompt，同时绕过技能的空账本契约，最终形成稳定吸附态。

## 已拍板方案与边界

用户于 2026-07-11 拍板：**只改 prompt，不增加机械兜底。**

同日用户批准 `design.md §2` 的最终 heartbeat 文案：核心强调
`You always have something to do on a heartbeat`；空账本时，等待一件事不等于等待所有事，
仍要找出并派发其他值得推进的 Goal。

用户随后明确取消隔离行为验证，并授权实现完成后直接升级当前运行的 `thirdtest-ceo`
容器。这里按“取消模型三轮真跑，保留快速确定性单测与部署健康检查”执行。

用户最终审阅并批准包含上述 prompt、验证取舍与在线升级步骤的完整
`prd.md`、`design.md`、`implement.md`，同意进入实现。

本任务通过更明确的每次 wake 指令解决重新激活问题，并接受剩余风险：运行时不会检查
CEO 是否真的派单，也不会在空手结束后自动重试或告警。发布前只确认 prompt 的确定性
生成与部署状态；模型是否服从由 thirdtest 后续自然 heartbeat 观察，而不是 orchestration
状态机或隔离真跑来保证。

## 需求

### R1 — 每次 proactive heartbeat 显式调用技能

空事件 + `idle: proactive` 的 wake prompt 必须先明确建立 **“You always have something
to do on a heartbeat”**，再要求 CEO **现在调用** `when-idle` 并为本次 wake 从头执行；
不能只说“参考 charter”或“找点值得做的事”。

### R2 — 等待一件事不等于等待所有事

prompt 必须把用户要求的经营含义放在空账本分支中：即使某一件事正在等待，仍然总有
其他值得推进的工作。该措辞不否定等待本身，也不要求推翻等待；它要求 CEO 在持有等待
的同时继续推进别的事情。

### R3 — 在触发 prompt 中重申两条合法结局

prompt 应简洁复述技能的账本分支，避免重新加载前就走偏：

- 有非终态 Goal：一行 stand down；
- 空账本：结束前派出一个新的 Goal；空手回复非法。

具体找什么工作、如何走反驳序、如何避免 padding 仍由 `when-idle` 技能正文负责，prompt
不复制整份决策清单。

### R4 — 兼容边界保持不变

- 所有 worker 的 `idle: stop` heartbeat 文案保持字节一致；
- event wake 不受影响；
- objective 注入和 fresh-session orientation 的组合顺序不变；
- Claude 与 Codex 共用同一个 prompt 契约。

### R5 — 严格保持 prompt-only

产品行为改动只发生在 `orchestration/agent_loop.py` 的 proactive heartbeat prompt。
允许同步更新单测、代码注释和 `.trellis/spec` 契约，但不修改：

- `orchestration.messaging`、Hub、ledger、telemetry 或 hooks；
- session fresh/resume 策略；
- `agents/assets/skills/when-idle/SKILL.md`；
- `agents/assets/ceo-charter.md`。

### R6 — 定向升级当前运行的 CEO

`orchestration/` 已从宿主机只读 bind mount 到 `thirdtest-ceo`，无需 rebuild 或 recreate；
实现完成后，在确认没有 `claude -p` wake 正在执行时，只重启 CEO 服务以重新加载 Python
模块。`state/thirdtest/sessions` 同样是宿主机 bind mount，因此重启后必须继续原 session，
不得清空或轮换 CEO 上下文。其他 resident 与基础设施容器不重启。

## 验收标准

- [x] AC1（R1–R3）：单测钉住 proactive heartbeat 的完整文本，明确包含
      `You always have something to do on a heartbeat`、本次调用 `when-idle`、从头执行、
      等待一件事不等于等待所有事、忙账本一行停、空账本必须新派 Goal。
- [x] AC2（R4）：现有 worker stop golden、event wake、objective + fresh 组合测试继续通过，
      且 worker stop 文案字节不变。
- [x] AC3（R5）：最终产品 diff 不包含 messaging、Hub、ledger、telemetry、hooks、session
      策略、`when-idle` 技能正文或 CEO charter 的改动。
- [x] AC4：按用户授权不执行 CEO 模型行为沙箱或三轮空账本真跑；只运行
      `orchestration/tests/test_agent_loop.py` 与 `git diff --check` 的确定性检查。
- [x] AC5（R6）：升级前确认 `thirdtest-ceo` 没有活动中的 `claude -p` 子进程；随后仅重启
      CEO 容器。重启后容器为 running、`agent_loop` 存活、session id 保持
      `dd70a6f8-e6d6-4dc2-8107-fc0f0a35b441`，其他容器启动时间不变。
- [x] AC6：容器内直接调用 `build_wake_prompt([], idle="proactive")` 得到用户批准的精确
      文案；不主动触发一次付费模型 wake 作为验证。

## 不在本任务范围

- 除经用户授权定向重启 `thirdtest-ceo` 外，不重启或修改 thirdtest 的其他容器与经营状态。
- 不解决 KDP、KYC、Stripe payout、SEO 等经营门槛。
- 不取消 CEO 的 `session: resume`。
- 不用固定工作清单替代 CEO 判断，也不鼓励凑数 Goal。
- 不扩展 worker 的 heartbeat 主动权。
- 不增加空手检测、自动纠正、连续空闲告警或任何运行时强制机制。
