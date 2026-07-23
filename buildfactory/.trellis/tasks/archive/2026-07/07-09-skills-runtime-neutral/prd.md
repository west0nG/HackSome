# Fleet skills: remove claude-only assumptions

## Goal

fleet skills 在两种 runtime 下都可执行：有 claude 专属机制（subagent、`~/.claude/skills` 路径）的 skill 补上显式降级路径或双路径写法，使 CEO/worker 任一角色切 codex 时 skill 不静默失灵。

## 需求

- R1（decide-direction，主要项）：
  - "大方向复核 spawn 独立 subagent（Agent 工具）"一段，补无 subagent 机制时的显式降级路径——参照 visual-iterate 已有的写法（降级为自查清单模式，明确告知代价）。
  - `~/.claude/skills/decide-direction/references/direction-critic.md` 引用改双路径（`~/.claude/skills/...` 或 `~/.agents/skills/...`，按实际存在者取用）。
- R2（全量排查）：grep 全部 `agents/assets/skills/*/SKILL.md`（含 references），列出并处理残留的 claude 专属指令；已达标者（visual-iterate 已有降级路径、mine-customer-voice 已双路径）不动。
- R3（create-role 链路：provider 跟随公司主 provider，用户 07-09 拍板"跟随"）：
  - R3a（skill 模板）：create-role SKILL.md 模板的 `provider: claude-code` 行改为跟随指引——起草时显式写公司当前主 provider（看现有 agents/*.yaml 的众数），不盲抄示例值。
  - R3b（结构兜底）：新增单一来源 helper `fleet_default_provider(agents_dir)`（现有常驻 role yaml 中 provider 的众数；平手或无角色 → claude-code）。`orchestration/role.py` lint 对缺省 provider 的解析、以及 provisioner 物化 proposal 时的缺省填充都走它；物化落盘的 `agents/<name>.yaml` 永远含显式 provider（审计可见，不留隐式默认）。whitelist 校验语义不变。

## 约束

- 遵循 skill 三道检验（系统特定/压制 LLM 默认/非平凡取舍）：降级路径要写清"什么时候算降级、代价是什么"，不写泛泛的"如果不可用就跳过"。
- 不改任何 skill 的核心方法论内容；skill 侧只动 runtime 依赖表述。
- 代码改动仅限 R3b 的 create-role 链路（orchestration/role.py + provisioner 的 provider 缺省解析），whitelist 与其余 lint 规则不动。

## 验收标准

- [x] AC1：decide-direction 在无 Agent 工具的 runtime 下有明确可执行的降级行为；references 引用在两种 skills 安装路径下都解析得到。
- [x] AC2：全量 grep 复查无残留的无降级 claude 专属硬指令（报告排查清单于 implement 记录）。
- [x] AC3：①proposal 的 role.yaml 缺省 provider 时，物化出的 `agents/<name>.yaml` 含显式 provider = 当时 fleet 众数（单测：全 codex fleet → 新角色 codex；混合平手 → claude-code）；②create-role 模板含跟随指引；③provider whitelist lint 语义不变。
- [x] AC4（真跑，并入父任务 AC-P1 执行——证据见 07-09-codex-parity/research/）：一个 codex 角色的 wake 中实际触发过至少一个被修改的 skill 且未因 runtime 差异卡死。
