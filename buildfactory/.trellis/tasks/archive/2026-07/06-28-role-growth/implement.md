# Growth Role — 执行计划

> 依据 `design.md`（含 research 回填 + 用户方向修订）。纪律：**赋能 > 限制**；**一个一个做、不批量**；每条 skill 内容能指认 ①/②/③，防御没观测失败不写。
> **分批**：批1 = 内容侧 unblocked（零 provisioning 依赖）；批2 = 依赖 provisioning（视觉工具 / 账号 MCP）的，等方向定了再落。

## 批 1（本轮，unblocked）

**1. `de-ai-ify`（vendor 双语）— ✅ DONE（commits `d28649a` + `0210e11`）**
- 落形：`agents/assets/skills/de-ai-ify/`：host `SKILL.md`（唯一原创=语言路由层）+ `references/en-*`（blader/humanizer + coreyhaines，MIT）+ `zh/`（qu-ai-wei **整份 intact** vendor，MIT）+ `ATTRIBUTION.md` + `vendor/LICENSE.*`。
- 关键修正（含独立盲评发现的 bug）：**vendor 要带整个依赖闭包**——第一版只拷叶子 reference，中文侧控制层(语体矩阵/冲突仲裁/过度消毒反制)和 2 个兄弟文件缺失、死链；改成把 qu-ai-wei 整个 skill 原样 vendor 进 `zh/` 才自洽。破折号从"绝对禁"改成"能无损替换才删、留有真修辞功能的"。
- 挂 `growth.yaml` + `test_growth_gets_de_ai_ify_with_vendored_references`（断言 `zh/` 嵌套子树物化）；`agent/tests/` 38 绿。

**2. `mine-customer-voice`（07-02 二次修订，取代"4 原子混合 vendor"）— ✅ DONE（用户已审批 design §5.6）**

> 上午的 4 原子方案被用户叫停 → 回 brainstorm 从缺口倒推（`research/copy-capability-gaps.md`）：真缺口 = voice 冷启动 + 客户原话，方法类降级。**先给用户看 prd/design、拿到"可以做"再实施**（07-02 教训）。
> 交付记录：4 目录已清场；skill 落盘 + 挂载 + 40 测试绿；盲评两轮——首轮抓 5 缺陷（sparktoro 死链 / 源清单 cp 路径错 / 落点矛盾 / 浏览器依赖未映射 / jq 依赖），前 4 个以 host "Reading the catalogs" 映射块修复，#5 判定 vendored 文件自带说明、不加防御；复核确认场景链（缺 voice→采话→定 voice→取材→de-ai-ify）可走通。

- **清场**：上午已拷的 `draft-social` / `repurpose-content` / `short-form-video` / `social-listening` 4 目录，除 listening 两份 reference 改编入本 skill 外**删除**（未 commit；再引入按 `social-vendor-compare.md` 零成本）。
- **落形**（de-ai-ify 模式）：`agents/assets/skills/mine-customer-voice/`：host `SKILL.md`（唯一原创：何时采 / 交付=写 `/company` 客户语言库·落点 growth 自定 / voice 冷启动=growth 职责 / 适配注记）+ `references/{customer-research.md, source-guides.md, listening.md, listening-sources-template.md}`（全 coreyhaines MIT verbatim）+ `ATTRIBUTION.md` + `vendor/LICENSE.coreyhaines-marketingskills`。
- **统一适配**：`.agents/product-marketing.md` 读取 → 读 `/company`；`.agents/listening-sources.md` 源清单 → `/company` 文档；无喂 proof 步骤。
- **风格纪律（用户此前反馈，务必遵守）**：`description` 一句话；正文只讲应用场景、不写举例叙述；不强调 headless/无用户（正面写"从 `/company` 读"）；host 里别用 em dash。
- **验证**：`.venv-cua/bin/python -m pytest agent/tests/`；挂 `growth.yaml` + `test_resident_loadout` 断言（skill 集合 + references 物化）。
- **收尾**：盲评 sub-agent 走场景链（缺 voice → 采话 → 定 voice → 取材写稿 → de-ai-ify）；中文水位 gap 记批2。

**3.（可选）`copywriting`+`copy-editing`**：vendor，只留具体表（CTA 词表/headline 公式/Seven Sweeps），剔原则散文。视批1 手感决定是否本轮带上。

**4. charter 重写**（design §7）：`assets/growth-charter.md` placeholder → 真（身份/两大事/原子自主组合/company-state 只记状态/不喂 proof/跨职能交 CEO）。赋能式。

**5. 挂载 + 测试**（design §9）：`growth.yaml` skills 追加批1 新条目（保留 `company-state`+`receive-goal`）；`test_resident_loadout` 断言含新 skill + `references/` 物化。

## 批 2（待 provisioning 方向定，本轮不做）

- **`use-accounts`**：写 against 平台/账号 MCP（优先）/ CUA 回退。**卡点 = 装/写哪些账号 MCP（design §10 Q1，用户"再看"）**。可能先出一个"MCP 优先 + CUA 兜底"的通用骨架，具体平台等 MCP 就绪补。
- **`visual-asset`**（复合，design §5.5）：生图工具 + HTML/组件化设计 + 修复迭代。**卡点 = 装哪些视觉工具**。
- backlog（押后）：content-strategy 选搬、hook/thread/repurpose/voice；cadence/engage/read-signal（闭环）；cold-email/SEO/CRO/landing/变现 渠道变体。

## 验证命令

```bash
# 用 .venv-cua/bin/python：系统 python3 没装 yaml/pytest
.venv-cua/bin/python -m pytest agent/tests/test_resident_loadout.py -q
.venv-cua/bin/python -m pytest agent/tests/ -q
.venv-cua/bin/python -c "from agent.spec import AgentSpec; print(AgentSpec.load('agents/growth.yaml').skill_paths())"
```

## 自检门（每个 skill 写完即查）

- **来源**：每条内容指得出 ①/②/③？指不出 = 泛泛常识或防御没观测 → 删。
- **de-AI-ify**：是**具体 tell + 反例**、不是"更像人类"？保留了 What-NOT-to-flag（不过度去味）？
- **vendor**：拷进来标了 LICENSE/来源？`.agents/product-marketing.md` 已重接 `/company`？只留具体表、剔了原则散文？
- **分权/记忆**：全程无"给 verifier 喂 proof"步骤？写 `/company` 只写状态？
- **边界**：落地页/部署没自己碰（交 Builder）？
- **节奏**：一个一个做，没批量占位？

## review gate

- 批1 每个 skill 写完 → 派 `trellis-check` 跑 AC1–AC6。
- 批2 动手前 → provisioning 方向（账号 MCP / 视觉工具）用户确认。

## 回滚点

- 删新 skill 目录 + 还原 `growth.yaml` / `growth-charter.md` / `test_resident_loadout.py`。零 .py 逻辑改动、零数据迁移。
</content>
