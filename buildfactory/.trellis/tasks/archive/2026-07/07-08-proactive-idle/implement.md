# 执行清单：公司空闲时主动找事做

按顺序做，每步都有验证命令。整体分四段，段间是天然的回滚点。

## 第一段：底层接线（idle 键）

- [ ] `agent/spec.py`：白名单加 `"idle"`，`RoleSpec` 加字段，默认 `"stop"`。
- [ ] `orchestration/agent_loop.py`：
  - `_role_config()` 返回 idle（非法值 WARN → `"stop"`，照抄 session 键的
    降级写法）；
  - `_render_events()` 空事件分支按 idle 出两种文本，`stop` 分支逐字节不动；
  - `build_wake_prompt()` / `agent_loop()` / `main()` 把 idle 传下去，参数
    带默认值保持旧调用签名可用。
- [ ] 单测先行补齐：
  - `agent/tests/`：spec 解析 idle 键（缺省 / proactive / 非法值）；
  - `orchestration/tests/test_agent_loop.py`：`stop` 逐字节回归钉、
    `proactive` 文本断言、与 objective 前缀 / fresh 前缀的组合顺序、
    不以 `-` 开头。
- [ ] 验证：`python3 -m pytest orchestration/tests agent/tests -x -q` 全绿。

回滚点：这一段独立成立且零行为变化（没人设 proactive），可单独提交。

## 第二段：技能 + 配置

- [ ] 新建 `agents/assets/skills/when-idle/SKILL.md`（英文），按
  design.md 改动二的六个主干写（查账、冷却、开放式找事四类举例、等待=旁线
  任务、产出只能是派单、压制的默认），写完对照三道检验自查：
  1. 每条内容都系统特定（含确切命令/路径）吗？
  2. 每条都在压制一个具体的 LLM 默认吗？
  3. 取舍标准非平凡吗（删掉后 CEO 会做错事吗）？
- [ ] `agents/ceo.yaml`：`idle: proactive` + skills 列表加
  `assets/skills/when-idle`（附一行注释说明用途，风格照抄现有行）。
- [ ] 验证：`python3 -m pytest agent/tests -x -q`（loadout 相关测试仍绿）；
  肉眼过一遍 SKILL.md 的三道检验结论。

## 第三段：章程

- [ ] `agents/assets/ceo-charter.md`："How you decide what to pursue" 按
  design.md 改动三调整（查账顺序、巡检指向技能、等待承诺边界一句）。
- [ ] 自查：章程与技能不重复展开同一套细节（章程定方向，技能给步骤）；
  heartbeat 相关表述与新提示词不再打架。

## 第四段：真跑 e2e + 收尾

- [ ] 起测试公司：`COMPANY=e2eidle docker compose up -d`（凭证复用现有账号
  包，同首跑做法）。
- [ ] AC2 正向：确保账本目录无非终态活儿 → 等一次 CEO 空醒（或把
  `CEO_HEARTBEAT_SECS` 调小加速）→ 取证三样：
  - `state/e2eidle/telemetry/wake.ceo.jsonl` 有 trigger=heartbeat 的记录；
  - hub 日志出现新 DISPATCH；
  - `state/e2eidle/ledger/` 出现新 goal 文件。
- [ ] AC3 反向：账本里有在跑活儿时，CEO 空醒输出一句话停、成本 $0.25 量级
  （看 wake 记录的 cost_usd）。
- [ ] AC4 边界：巡检那次醒来的会话记录里没有对外写操作，产出只有 send。
- [ ] `.trellis/spec/backend/resident-agent-contracts.md`：增补 idle 键契约
  （两种空醒文本、默认值、降级行为）。
- [ ] 全量验证：`python3 -m pytest orchestration/tests agent/tests -q`。
- [ ] **用户评审门**：把 `when-idle` 的 description 和 SKILL.md 正文翻译成
  中文交用户审；有修改落回英文原文并重跑相关验证后，才算收尾。

## 风险与回滚

- 风险最高的文件是 `orchestration/agent_loop.py`（全员共用的唤醒路径）——
  靠"stop 分支逐字节回归钉"兜底；改坏了会被第一段单测当场拦下。
- e2e 若发现 CEO 不按技能办（提示词赢不过旧习惯之类），回到第二/三段改文本
  重跑，不动底层。
- 整体回滚：撤 `ceo.yaml` 两行即回现状。
