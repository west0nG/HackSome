# Standing objective: per-agent objective.md injected every wake

## 背景 / 问题

- CEO 没有长期方向的锚点：heartbeat 醒来时 charter 只说"看看有没有事要做"，`find-opportunity` / `decide-direction` 每次都从零生成候选方向，无法长期专注在一件事上。
- 部门（researcher/builder/growth）只会被动 `receive-goal`，没有属于自己的长期目标，不构成 proactive agent。

## 需求

1. **每个常驻 agent 一个 objective 文件**（约定名 `objective.md`），存放于该 agent 的私有持久位置——不在 `/company`（共享记忆必须纯生长、无预设路径），不进 goal ledger（objective 不是工作单元，无 open→done 生命周期）。
2. **每次 wake 都注入**：不论 heartbeat 还是有 inbox 事件，只要文件存在且非空，全文注入当次 wake prompt 的开头。文件不存在或为空 = 完全不注入，行为与现状一致。
3. **agent 自写自维护**：harness 只保证目录存在与注入机制，不预设文件内容、不强制任何格式（写不写成 OKR 形式是 agent 自己的决定）。
4. **设定/修订走专用命令，reviewer 门结构强制**：
   - agent 用 `objective` 命令修改自己的 objective：命令自动把提案送独立 reviewer（全新 session，与提案者上下文隔离），**通过才落盘**，不通过则返回评审意见且不写入；
   - 评审判断力属于 reviewer：rubric 是 reviewer 专属的 `review-objective` skill，CEO 的 loadout 不含它、也不存在修改它的命令——被审者无法稀释标准（doer≠judge 结构化，与 Hub 的立场一致）；
   - reviewer 不可用时 fail closed（不写入、报错）；
   - charter/skill 只教判断力：冷启动必设（没有 objective 时设定是第一优先事项）、修订要有证据、内容一屏以内（它每回都进 prompt）。
5. **部门同原语**：部门拿到同样的文件与注入机制，charter 里告知其存在；初始为空即可。

## 约束

- `/company` 不得因此出现任何预设路径或文件。
- 不新增编排层名词：ledger、hub、inbox 协议一律不动。
- 命名用 **objective**，不叫 Goal（与 ledger 的 Goal 冲突）、不叫 OKR（不定死内容格式）。
- 注入不得违反现有约束：wake prompt 不能以 `-` 开头（`claude -p` 会当作 CLI 选项）。
- 注入内容有防御性长度上限（超限截断并告警），防止 agent 把文件写大后每回吃掉大量上下文。
- 与 company loadout overlay（07-03）互不影响。

## 验收标准（AC）

- [ ] 每个 agent 容器内可读写自己的 objective 文件；宿主侧持久化在 `state/<company>/` 下，容器重建后仍在。
- [ ] 文件存在且非空时：heartbeat wake 与 event wake 的 prompt 开头都包含其全文（单元测试覆盖两种 wake）。
- [ ] 文件不存在或为空时：wake prompt 与改动前完全一致（回归安全，单元测试覆盖）。
- [ ] 超过长度上限时截断注入并在 loop 日志打 WARN（单元测试覆盖）。
- [ ] 每次 wake 重新读文件——agent 在某次 wake 中修改了 objective，下一次 wake 注入的是新内容（单元测试覆盖）。
- [ ] loop 日志可观测本次 wake 是否注入及注入长度。
- [ ] `objective show` 打印当前内容；`objective propose` 在 reviewer 返回 GO 时落盘（旧版本存档）、返回 RESHAPE/DROP 时不写入并把意见回给调用者、reviewer 调用失败时不写入且报错（单元测试 mock reviewer 覆盖三种路径）。
- [ ] 评审 rubric 存在于 reviewer 的 `review-objective` skill（ro 挂载），CEO loadout 不含它；提案内容无法改变评审标准。
- [ ] ceo-charter 与 `set-objective` skill 落地起草侧纪律（命令为唯一正路）；三个部门 charter 告知 objective 文件与命令的存在。
- [~] 真跑 e2e（2026-07-03 部分完成，剩余移交真实环境——用户裁决，测试耗时过长）：
  - ✅ 已验证：boot 接线（`objective=/agents/ceo/objective.md`、set-objective 物化进 CEO skills）、无 objective 时每 wake `objective: none` 日志且行为无回归、冷启动判断链真实生效（CEO 未凭空编 objective，而是先派研究 Goal 拿信号——"don't pull a direction out of thin air" 约束住了行为）。
  - ⏳ 移交真实环境：propose→reviewer GO→落盘→下轮注入的完整闭环、reviewer 打回膨胀提案（机制路径已有 28 个单测用 mock 覆盖；rubric 的实战判断质量本来也只能真实环境出结果）。
- [ ] `orchestration/tests` 全部通过。

## 非目标（后续另立任务）

- 周期性 check-in 投递（定时 IME 提醒 CEO 复盘 objective 进度）。
- 部门的 proactive 行为（部门依据自己的 objective 主动向 CEO 提案）——本任务只铺原语。
- objective 内容格式的任何 schema 校验。
