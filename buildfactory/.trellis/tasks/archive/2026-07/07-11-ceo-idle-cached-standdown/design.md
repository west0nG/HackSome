# Design — proactive heartbeat 每次重新调用 when-idle

> 最终 prompt 文案已于 2026-07-11 获用户批准。

## 1. 设计结论

只改 `orchestration/agent_loop.py` 中 `idle: proactive` 的空事件 heartbeat 文本。
完整 CEO charter 已经在每次 wake 作为 system-prompt addition 重传；本设计针对的是本轮
`-p` user prompt 仍然过软。新 prompt 不再泛泛地指向 charter，而是在每次 wake 给出一个
短、完整、可执行的入口：

1. 现在调用 `when-idle`；
2. 为本次 wake 从头执行；
3. 等待一件事不等于所有事情都要等，仍有其他值得推进的工作；
4. 有工作在跑则一行停，空账本则新派 Goal 后才能结束。

不增加任何运行时检测、派单 marker、重试、告警或 telemetry 字段。

## 2. 拟定 prompt

产品文本使用英文，与现有 resident prompt 保持一致：

```text
HEARTBEAT wake: nothing new since last time. You always have something to do on
a heartbeat: invoke the `when-idle` skill now and follow it from the top. If work
is already in flight, stand down in one line. If nothing is in flight, waiting
on one thing does not mean waiting on everything: there is always other
worthwhile work you can advance, so find and dispatch the next worthwhile Goal
before you stop.
```

落到 Python 字符串时保持一行输出，不在运行时加入换行；上面的折行仅用于审阅。

### 每句承担的职责

- `You always have something to do on a heartbeat`：把用户要求的第一原则放在本轮最显眼的
  位置；“检查后发现公司正忙并一行停”也属于完成本次职责，不等于强制叠加 Goal。
- `invoke ... now`：目标是触发真实 Skill 调用，而不是依赖长 session 中早先读过的内容。
- `follow it from the top`：把技能执行限定为每个 heartbeat 的新 pass。
- `waiting on one thing does not mean waiting on everything`：不否定或推翻合理等待，只明确
  等待某一条路径时仍要推进其他值得做的工作。
- 两条 ledger branch：让模型在调用技能前就知道唯一合法出口，不把整份反驳序复制进
  prompt。

## 3. 代码边界与数据流

改动位于 `_render_events(events, idle)` 的 `not events and idle == "proactive"` 分支：

```text
ceo-charter.md ───────────────→ 每 wake 的 system-prompt addition

FileInbox.poll 返回 []
        ↓
build_wake_prompt(..., idle="proactive")
        ↓
_render_events 生成新版 heartbeat user prompt
        ↓
Claude / Codex 收到同一段每-wake 指令
        ↓
模型调用 when-idle → 查账本 → stand down 或 dispatch
```

没有新的状态、文件、环境变量或协议字段。Hub、messaging 和 ledger 完全不知道本次改动。

## 4. 兼容性

- `idle: stop`：保持现有 golden 字符串字节一致；这是 worker 安全边界。
- event wake：`events` 非空时不进入 heartbeat 分支，输出不变。
- objective：仍由 `build_wake_prompt` 在 heartbeat 外层 prepend，顺序不变。
- fresh orientation：仍位于 objective 与 heartbeat 之前，顺序不变。
- provider：prompt 在 runtime adapter 之前生成，Claude 与 Codex 自动获得同一行为。
- session：CEO 继续 `resume`；其他角色策略不变。

## 5. 测试设计

### 单元测试

把现有 `test_heartbeat_proactive_text_defers_to_charter` 升级为完整 prompt golden，避免未来
又退化成一句泛化软提醒。测试同时断言：

- 精确文本包含 `You always have something to do on a heartbeat`、`when-idle` 与
  `invoke ... now`；
- `waiting on one thing does not mean waiting on everything`；
- `work in flight` 与 `nothing in flight` 两个分支都存在；
- `STOP_ORDER` 仍不出现在 proactive prompt；
- 现有 worker stop、event wake、objective/fresh 组合测试保持通过。

用户已明确取消模型行为真跑。本任务不创建 scratch 公司、不主动触发 heartbeat，也不以
真实模型是否调用 Skill 作为本次发布前门槛。

## 6. 当前容器升级设计

已确认运行时形态：

- `thirdtest-ceo` 的 `/opt/foundagent-orch/orchestration` 是宿主机
  `/Users/weston/dev/BuildFactory/orchestration` 的只读 bind mount；代码修改无需构建镜像；
- `state/thirdtest/sessions` bind mount 到 `/sessions`，容器重启不会丢失 CEO session；
- 长驻 Python 已导入旧模块，所以仅修改宿主文件不够，必须重启 CEO 进程/容器；
- 其他 resident 也能看到新源码，但它们的 `idle: stop` 分支文本未变，不需要重启。

升级顺序：

1. 确认 `thirdtest-ceo` 中只有长驻 `python3 -m orchestration.agent_loop`，没有活动
   `claude -p` 子进程，避免中断一个正在执行的 wake；
2. 记录当前 CEO session id 和其他容器启动时间；
3. 执行 `COMPANY=thirdtest ACCOUNT=foundagent docker compose -f docker-compose.yml restart ceo`；
4. 确认容器 running、`agent_loop` 重新启动且仍加载原 session id；
5. 在容器内用纯 Python 构造 proactive heartbeat prompt，核对批准文本；不触发付费模型 wake；
6. 确认其他容器没有被重启。

## 7. 已接受的取舍与剩余风险

用户选择 prompt-only，因此接受以下剩余风险：

- 模型理论上仍可忽略 prompt；系统不会知道或自动恢复；
- 单测只能证明指令存在，不能证明每种长上下文下都服从；
- 用户选择跳过行为真跑，因此上线前没有模型服从性的实证样本；效果留给当前 thirdtest
  后续自然 heartbeat 观察。

收益是改动面极小，不引入 messaging/ledger 的新耦合，也不改变 resident loop 的控制流。

## 8. 回滚

无状态迁移。回滚 `agent_loop.py` 的 prompt 字符串、对应单测与 spec 说明，再定向重启
`thirdtest-ceo` 即可；session 与公司状态不回滚。

## 9. 上线结果

2026-07-11 已按本设计直接升级 `thirdtest-ceo`：无镜像构建，原 session id 保持不变，
其他容器未重启；容器内实际生成的 heartbeat prompt 与 §2 一致。按用户决定未做模型行为
真跑，效果由后续自然 heartbeat 观察。
