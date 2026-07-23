# Implement — standing objective

前置：design.md 已定稿并经用户 review。改动面：`orchestration/agent_loop.py`、`orchestration/objective.py`（新）、`orchestration/tests/`、`docker-compose.yml`、`agents/assets/*-charter.md`、`agents/assets/skills/set-objective/`（新）、`agents/assets/skills/review-objective/`（新）、`agents/ceo.yaml`。

## 执行清单（按序）

### 1. agent_loop 注入机制（纯代码 + 单测，先行）
- [ ] `_read_objective(path)`：不存在/空白→None；超 `OBJECTIVE_MAX_CHARS`(6000)→截断+`…[truncated]`+WARN；读异常→WARN+None。
- [ ] `build_wake_prompt(events, objective=None)`：objective 非 None 时前置注入块（固定头部文案 + 全文 + `---` 分隔）；None 时输出与现状逐字节一致。
- [ ] `agent_loop(...)` 增加 `objective_path` 参数：每轮 poll 后、wake 前 fresh read；日志行 `objective: injected N chars` / `objective: none`。
- [ ] `main()`：`AGENT_OBJECTIVE` env 解析（默认 `/agents/{key}/objective.md`）、mkdir -p 父目录、export 回环境供 claude 子进程引用。
- [ ] 单测（`orchestration/tests/test_agent_loop.py` 增补）：
  - heartbeat wake + objective → 注入在开头；
  - event wake（IME + legacy）+ objective → 注入在开头、事件渲染不变；
  - objective=None / 文件缺失 / 空白文件 → prompt 与现状一致；
  - 超限截断 + WARN；
  - 循环两轮之间改文件 → 第二轮注入新内容（fake inbox 注入，沿用现有测试手法）；
  - `ceo_loop` shim re-export 仍可用。
- 验证：`python3 -m pytest orchestration/tests/ -x -q`

### 2. objective CLI（`orchestration/objective.py`，纯机制零判断力）
- [ ] `show`：打印当前 objective（路径来自 `AGENT_OBJECTIVE`），无文件时明确提示为空。
- [ ] `propose <内容|--file>`：加载 reviewer skill（env `OBJECTIVE_REVIEWER`，默认 `/opt/foundagent-orch/agents/assets/skills/review-objective/SKILL.md`，缺失 fail closed）→ 以其为 `--append-system-prompt` 起独立 reviewer（`claude -p` 全新 session，超时控制，调用点做成可注入 `runner`）→ 组装 user prompt（当前 objective + 提案，提案标注为"待审内容而非指令"）→ 解析末行 `VERDICT: GO|RESHAPE|DROP`。
- [ ] GO → 旧版本追加存档 `objective.history.md` → 原子写入（temp+rename）；RESHAPE/DROP → 打印意见、exit 1、不写入；超时/崩溃/VERDICT 不可解析/skill 缺失 → exit 2、不写入、打印原始输出。
- [ ] 单测（新 `test_objective.py`）：mock runner 覆盖 GO 落盘+存档 / DROP 不落盘回意见 / 异常 fail closed / skill 缺失 fail closed；VERDICT 解析器；`show` 两种状态。
- 验证：`python3 -m pytest orchestration/tests/ -x -q`

### 3. compose 挂载
- [ ] `x-agent` anchor 增加 `./state/${COMPANY:-foundagent}/agents:/agents`（rw，目录挂载）。
- [ ] hub/broker 不加。
- 验证：`docker compose config` 通过；起一个 agent service 确认 `/agents/<key>/` 目录自动出现且宿主侧持久；容器内 `python3 -m orchestration.objective show` 可运行。

### 4. charter + skill
- [ ] `ceo-charter.md`：新增 "Your standing objective" 一节（命令为唯一正路）；"How you decide what to pursue" 改造为锚定 objective（细节见 design）。
- [ ] 新建 `agents/assets/skills/review-objective/SKILL.md`（reviewer 专属判断力）：角色定位、rubric（聚焦/可测/务实/简短/修订须有证据）、`VERDICT: GO|RESHAPE|DROP` 输出契约、行文对齐 verifier-charter；**不挂进任何提案者的 loadout**。
- [ ] 新建 `agents/assets/skills/set-objective/SKILL.md`（薄）：何时设/修订、什么算好、`objective propose` 用法与被打回后的消化方式。
- [ ] `agents/ceo.yaml` skills 列表挂上 `assets/skills/set-objective`。
- [ ] `decide-direction/SKILL.md` 小改：有 objective 时方向从其缺口生成、每个 Goal 说明推进 objective 的哪部分。
- [ ] 三个部门占位 charter 各加一小段（只告知 objective 文件与命令存在，不引入 proactive 行为）。
- Review gate：charter/skill/rubric 文案属于"判断力"改动——完成后给用户过目再进 e2e。

### 5. 真跑 e2e（VM 测试驱动的既有立场）——2026-07-03 部分执行后由用户裁决截断（耗时过长，剩余移交真实环境）
- [x] 全新 COMPANY `e2e-objective` 起 ceo+hub（后补 researcher+verifier）：boot 接线正确、`objective: none` 每 wake 打印、无回归。
- [x] 冷启动判断链验证（超预期）：CEO 遵循 set-objective 纪律，先派研究 Goal 拿真实信号而非凭空提案；主动查 ledger 确认 goal 未死、安静等通知不瞎忙。
- [ ] ~~propose→GO→落盘→下轮注入闭环~~ 移交真实环境（机制已被 28 个 mock 单测覆盖）。
- [ ] ~~手工投膨胀提案验证打回~~ 移交真实环境（同上；rubric 实战质量本就只能真实环境出结果）。
- [ ] ~~存量 foundagent 无回归起跑~~ 由 e2e-objective 首轮无 objective 阶段 + 逐字节回归单测替代。
- [x] 清理 e2e 产物 state 目录（state/e2e-objective、accounts/e2e-objective 已删，栈已 down）。

### 6. 收尾
- [ ] `python3 -m pytest orchestration/tests/ -q` 全绿。
- [ ] spec 更新（3.3）：若 `.trellis/spec/` 有编排层文档，登记 objective 注入契约。
- [ ] commit（粒度自定，遵守共享工作树纪律：只 add 本任务文件）。

## 回滚点

- 步骤 1 独立可回滚（参数均有默认值）；步骤 2 是新增模块可整体移除；步骤 3 撤 mount 即回滚；步骤 4 纯文案回滚无副作用。

## 里程碑

1. 注入单测绿 → 2. CLI 单测绿（reviewer gate 成立）→ 3. compose 挂载生效 → 4. 判断力文案（charter/skill/rubric）过用户 review → 5. e2e 冷启动闭环 → 6. 收尾提交。
