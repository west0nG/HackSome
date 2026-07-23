# CEO 判断力 — 执行计划（v2）

> 依据 `design.md` v2。纪律：**赋能 > 限制**；每条 skill / charter / critic 内容能指认来源（①系统 / ②压制 LLM 默认 / ③gstack 提炼），**防御没观测到的失败一律不写**。

## 顺序清单

1. **新建 `agents/assets/skills/decide-direction/SKILL.md`**（design §4）
   - frontmatter：`name: decide-direction` + `description`（对齐 heartbeat / 决定追什么 wake 措辞）。
   - body：务实取向 → 最窄切入 → 双向门决策（要不要召 critic）→ 如何召 critic → 用 verdict。~50-70 行，风格对齐 `send-goal`。
   - 末尾 gstack 署名注释。
2. **新建 `agents/assets/skills/decide-direction/references/direction-critic.md`**（design §5）
   - critic 任务 prompt：务实产品顾问角色（NOT YC 十亿级）+ 反自嗨姿态 + 务实 4 问（按成熟度 smart-route）+ 务实门槛 + `GO / RESHAPE / DROP` verdict 格式。
   - gstack 署名。
3. **增强 `agents/assets/ceo-charter.md`**（design §3）
   - `## Principles` 后加 `## How you decide what to pursue`（~4-6 行）：务实落地（SCOPE REDUCTION）+ 双向门（可逆就试、70% 够）+ 重大方向召独立审、你仍是 decider。不动其余。
4. **改 `agents/ceo.yaml`**（design §2.4）
   - `skills:` 追加 `- assets/skills/decide-direction`（保留 `send-goal`）。
5. **更新 `agent/tests/test_resident_loadout.py`**
   - `test_ceo_gets_send_goal`：断言 `set(info.skills)` 含 `decide-direction`，assert `SKILL.md` + `references/direction-critic.md` 物化存在。按需重命名。
6. **核对 `agent/loadout.py::materialize`**：确认它**递归复制 skill 子目录**（`references/`）。若只复制顶层 `SKILL.md`，需调整 materialize 或改用扁平 reference —— 实现前先验证。

## 验证命令

```bash
# 物化 + reference 子目录（核心 AC1）
python3 -m pytest agent/tests/test_resident_loadout.py -q
python3 -m pytest agent/tests/ -q
# reference 是否物化（针对清单 #6 的风险）
python3 -c "from agent import resident_loadout as r; import tempfile,os; d=tempfile.mkdtemp(); r.materialize_for('ceo', agents_dir='agents', claude_home=d); print(os.path.exists(os.path.join(d,'skills','decide-direction','references','direction-critic.md')))"
# yaml 可解析
python3 -c "from agent.spec import AgentSpec; print(AgentSpec.load('agents/ceo.yaml').skill_paths())"
```

## 自检门（写完即查）

- **来源**：每条 skill / charter / critic 内容能指认 ①/②/③/gstack 提炼？指不出 = 泛泛或防御没观测 → **删**。
- **务实标定**：critic 门槛是"真实小痛点 + 能验证 + 能落地"？有没有混入 desperate / 10-star / future-fit / maximum-rigor？有 → **砍**。
- **双向门**：小方向是否明确"直接发、不召 critic"？
- **headless**：措辞是否假设有交互端？（critic 是 sub-agent，不是人类；CEO 无用户可问。）
- **触发**：`description` 是否对齐 heartbeat wake 措辞？

## review gate

- design §7 四个待确认项 → 用户确认后再写 body。
- 实现后、commit 前：派 `trellis-check` 跑 AC1–AC5。

## 回滚点

- 删 `decide-direction` 目录 + 还原 `ceo.yaml` / `ceo-charter.md` / `test_resident_loadout.py`。零数据迁移、零 .py 逻辑改动。
</content>
