# 实施计划：CEO 持续战略思考循环

## 实施顺序

1. [x] 进入开发阶段前加载 `trellis-before-dev`，重新读取 backend spec 与工作区状态；确认只编辑本任务文件和下列产品代码，不碰现有 thirdtest 业务状态及其他未提交改动。

2. [x] 建立五个 skill 骨架并完成正文：
   - 使用 `skill-creator` 的初始化脚本在 `agents/assets/skills/` 下创建：
     - `think-strategically`
     - `trace-causal-chain`
     - `challenge-thesis`
     - `reason-as-buyer`
     - `integrate-new-information`
   - 元 skill 只负责识别问题、路由 atom、综合判断与落地；不复制 atom 正文。
   - 每个 atom 保持单一职责、高自由度；不加入分数、PASS/FAIL、固定调用顺序、固定数量或统一模板。
   - description 明确真实触发语，使模型能在对应情境中发现 skill。
   - 若初始化器生成 `agents/openai.yaml`，只保留 UI 元数据，不在其中放另一份行为规则。

3. [x] 接入 CEO loadout：
   - 在 `agents/ceo.yaml` 的 skills 中加入五个新目录；不加入任何 worker 或 verifier。
   - 在 `agent/tests/test_resident_loadout.py` 更新 CEO 精确集合，并继续精确锁定各部门集合未变化。
   - 在 `agent/tests/test_skill_catalog.py` 为五个 description 增加关键触发词测试。

4. [x] 增加声明式战略模式：
   - `agent/spec.py`：在 `_FIELDS` 与 `AgentSpec` 增加 `strategic: bool = False`。
   - `agents/ceo.yaml`：设置 `strategic: true`；其他 role yaml 不修改。
   - `agent/tests/test_spec.py`：覆盖默认 false、CEO true、builder false。

5. [x] 接入 resident wake prompt：
   - `orchestration/agent_loop.py`：
     - 增加 `STRATEGIC_EVENT_PREFIX`；
     - 为 `build_wake_prompt` 与 `agent_loop` 增加默认关闭的 `strategic` 参数；
     - 只在非空事件 wake 中把前缀放在 Objective 后、事件正文前；
     - heartbeat 不直接使用此前缀；
     - `_role_config` 解析 bool，非法值 WARN + false，所有 never-brick 默认 tuple 补齐该字段；
     - `main()` 透传并在 boot log 输出该模式。
   - `orchestration/tests/test_agent_loop.py`：
     - strategic event 的顺序与内容；
     - 默认/worker event byte-identical；
     - `strategic=True` 不改变 heartbeat；
     - 与 Objective、fresh orientation、legacy event、leading-dash 规则组合；
     - role config true、缺失、非法和坏 YAML；
     - main/loop 透传。

6. [x] 更新 CEO charter：
   - `agents/assets/ceo-charter.md` 把战略制定、因果推理、自我批判和持续反思写成首要职责；
   - 删除重要决策必须“保持短促”的暗示；
   - 澄清 DONE 不重新验收，但必须整合其对现有商业逻辑的影响；
   - 保持 CEO 不做 worker 工作、Objective 只能走 `set-objective`、结论写回 `/company` 等边界。

7. [x] 更新 heartbeat 认知路径：
   - `agents/assets/skills/when-idle/SKILL.md` 保留 ledger 命令和 busy stand-down；
   - coasting 分支先调用 `think-strategically`；
   - 删除“唯一合法 ending 是 Goal”和必然产出 side quest 的固定 ladder；
   - 允许 Goal、Objective 流程或真实战略结论作为思考后的行动，但仍禁止立即睡眠、空话和 CEO 亲自执行外部工作。
   - 同步修改 `orchestration/agent_loop.py` 的 proactive heartbeat 固定文本及对应单测，使其只承诺调用 `when-idle` 和空 ledger 不休息，不再承诺必定 dispatch。

8. [x] 做现有 opportunity/objective workflow 的小范围兼容修改：
   - `agents/assets/skills/find-opportunity/SKILL.md`：把 business form 改为能力约束下的可修订先验，明确 form 与需求共同演化；保留 grounded research、2–3 candidates 和 handoff。
   - `agents/assets/skills/set-objective/SKILL.md`：澄清 PASS 是当前证据下的 BUILD 授权，后续新信息仍需反思；负载前提变化时允许正式 revision；不新增 verdict 或 gate。
   - 更新 skill catalog 中受 description 文案影响的断言，但不扩大两个 workflow 的职责。

9. [x] 同步现行 spec：
   - `.trellis/spec/backend/resident-agent-contracts.md`：记录 `strategic` 字段、事件 wake 前缀、默认兼容和新的 proactive idle 语义。
   - `.trellis/spec/backend/agent-handbook-contracts.md`：记录“DONE 不重验收，但 CEO 要整合战略含义”。
   - 检查 `.trellis/spec/backend/agent-execution-contracts.md`；只有它对 AgentSpec 字段枚举不再完整时才做最小更新。
   - `.trellis/spec/backend/company-state-contracts.md` 不改行为。

10. [x] 验证五个 skill 与定向回归：

```bash
./.venv-cua/bin/python /Users/weston/.codex/skills/.system/skill-creator/scripts/quick_validate.py agents/assets/skills/think-strategically
./.venv-cua/bin/python /Users/weston/.codex/skills/.system/skill-creator/scripts/quick_validate.py agents/assets/skills/trace-causal-chain
./.venv-cua/bin/python /Users/weston/.codex/skills/.system/skill-creator/scripts/quick_validate.py agents/assets/skills/challenge-thesis
./.venv-cua/bin/python /Users/weston/.codex/skills/.system/skill-creator/scripts/quick_validate.py agents/assets/skills/reason-as-buyer
./.venv-cua/bin/python /Users/weston/.codex/skills/.system/skill-creator/scripts/quick_validate.py agents/assets/skills/integrate-new-information

./.venv-cua/bin/pytest -q \
  agent/tests/test_spec.py \
  agent/tests/test_resident_loadout.py \
  agent/tests/test_skill_catalog.py \
  orchestration/tests/test_agent_loop.py
```

11. [x] 运行范围化全量回归与静态检查：

```bash
./.venv-cua/bin/pytest -q \
  agent/tests company_state_kit/tests observatory/tests \
  orchestration/tests peripheral/tests

git diff --check

rg -n "only legal ending|only output shape|find and dispatch the next worthwhile Goal before you stop" \
  agents orchestration .trellis/spec \
  --glob '!**/archive/**'
```

静态搜索可以命中解释历史问题的任务文档，但现行 charter、skill、代码和 spec 不得继续把 coasting heartbeat 的唯一合法结局定义为 dispatch。

12. [x] 做一次隔离 forward test 并记录原始观测：
   - 从 thirdtest 现有文件复制最小原始片段作为输入，不修改原文件；
   - 使用 fresh context 和新 CEO skill loadout，不提供期待结论，不连接可执行外部写入；
   - 保存到本任务工程证据目录：
     - `research/forward-test-input.md`
     - `research/forward-test-output.md`
     - `research/forward-test-observations.md`
   - 记录实际 meta/atom 调用、delta 整合、因果链变化和退化行为，不汇总成分数，不把单次结果变成新 gate。
   - 若问题是接线失败或 skill 根本不可发现，在本任务内修复并重跑；若只是推理深度不理想，原样记录为下一轮收紧依据。

13. [x] 做收敛检查：逐条核对 PRD AC1–AC10、设计边界、测试结果和 diff，确认没有顺手加入评分器、新存储、worker 改造、blocking hook 或 thirdtest 业务修改；然后进入 `trellis-check`。

## 验证结果

- 五个新 skill 均通过 `quick_validate.py`。系统 Python 缺少 PyYAML，实际使用项目 `.venv-cua` 解释器；这是解释器依赖问题，skill 结构本身无错误。
- 定向回归：98 passed，覆盖 AgentSpec、精确 loadout、skill catalog/预算、认知 skill 文本边界和 resident wake prompt。
- 范围化全量回归：736 passed，覆盖 `agent/tests`、`company_state_kit/tests`、`observatory/tests`、`orchestration/tests`、`peripheral/tests`。
- `git diff --check` 通过；新文件无 trailing whitespace；现行 `agents/`、`orchestration/` 和 `.trellis/spec/` 中不再存在旧的“coasting 必须 dispatch”固定措辞。
- Forward test 工程证据：
  - [输入](./research/forward-test-input.md)
  - [原始输出](./research/forward-test-output.md)
  - [观察](./research/forward-test-observations.md)
- 隔离 Opus xhigh 测试真实调用 `think-strategically` → `integrate-new-information` → `reason-as-buyer`，没有机械全调四个 atom；它识别了渠道、产品形态、发现和信任的耦合，并选择重开 Objective 而非继续构建。
- 已知但未在 V1 收紧：单次测试不能证明长期质量；该次推理耗时约 143 秒、报告成本约 $0.35；小变化、模糊反馈、重复反思和保持原决策的表现仍需在真实运行中观察。
- 未重启 live resident，未修改 thirdtest 的 `/company`、Objective、ledger、inbox 或 session。

## 高风险文件与检查点

- `orchestration/agent_loop.py`：默认参数必须保持旧调用者与 worker prompt byte-identical；不能把 strategic 前缀放到 heartbeat 或所有角色。
- `agent/spec.py` / `_role_config`：tuple 扩展会影响多个解构和索引测试；所有缺失/异常返回路径必须同时补齐，不能破坏 never-brick。
- `agents/assets/skills/think-strategically/SKILL.md`：不能长成包含全部商业知识的总 checklist，也不能递归要求 workflow 再调用自己。
- `when-idle`：放宽输出不等于允许 ledger 为空时立即睡眠；保留主动 heartbeat 的产品目标。
- `ceo-charter.md`：战略反思不能被写成重新验收 DONE，避免破坏 doer≠judge 与 Hub 终态语义。
- `find-opportunity` / `set-objective`：只做兼容修改，不借机重写需求验证、Verifier rubric 或 PASS/FAIL 协议。
- `/company`：本任务没有新 schema；forward test 只能使用隔离副本，不能写 live thirdtest。

## 验证结果记录位置

实施时在本文件勾选步骤，并在“验证结果”节补充：

- 五个 quick validation 结果；
- 定向与全量 pytest 数量；
- 静态搜索剩余命中的解释；
- forward test 三个证据文件的链接；
- 已知但未在 V1 收紧的推理问题。

## 回滚点

- Runtime、AgentSpec、CEO YAML、五个 skill、charter/workflow 文案、测试与 spec 作为一组回滚。
- 没有 `/company`、Objective、ledger、inbox 或 session 数据迁移。
- 若战略前缀导致运行问题，临时回滚 `agents/ceo.yaml` 的 `strategic: true` 即可恢复事件 prompt；heartbeat 仍由独立的 `idle` 设置控制。
- 不通过删除 worker 回归断言来“修复”兼容失败；战略能力必须保持声明式、默认关闭。
