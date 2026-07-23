# Growth Role — 内容生产 + 运营（原子可组合 skill）

> 父任务：`../06-28-role-library`。交付 Growth 的**执行力**层：做优质内容 + 运营内容/账号。
> ⚠️ 边界：唤醒/常驻/inbox/Hub 机制已 done（PR #193/#195）；本任务只碰 **charter 内容 + skill loadout**——声明式，**零 .py 逻辑改动**，仅物化测试断言更新。
> ⚠️ **本 session 修订**：由"4 块扁平 skill（账号/运营/写内容/出图）"改为"**两大事（做内容 / 运营）+ 原子化可组合 skill**"；并纠正 verifier / company-state 两处立场（见 design §2）。

## 现状（已存在，不重做）

- growth = 常驻 `claude -p` session（`agents/growth.yaml`），charter = `assets/growth-charter.md`（**placeholder**），挂 2 个 skill：`company-state` + `receive-goal`。
- 物化机制 `agent/loadout.py::materialize`（`shutil.copytree` 递归）→ 支持带 `references/` 的多文件 skill。
- 外设层已建：**inbound**（IME/inbox/adapter ingress，147 测试，`peripheral/`）。**outbound（真发帖/发信）= MCP tools 或待建对偶**，`use-accounts` 依赖它（design §1、§10）。
- 账号 provisioning **不属本任务**——假设全部已存在（外设层/MCP 提供）。

## Goal

给 Growth 一套务实的"**做出优质内容 + 运营内容/账号**"能力，以**原子化、可组合的 skill**（乐高，非巨石）落地，growth 按判断现场组合。**复用开源（`coreyhaines31/marketingskills`）为主、gap 处自写**。第一版立**可迭代骨架**，不追一次到位。

**核心纪律**：**赋能（多给能力）> 限制（少给边界）**——`限制越小、能力越强`。每条 skill 内容能指认来源：**①系统特定 / ②要压制的 LLM 残余默认 / ③非平凡信号（带反例/阈值）**；**防御"没观测到的失败"一律押后**（呼应 memory `skill-design-no-generic-for-llm` / `foundagent-permissions-stance`）。

## 范围（口径 + 边界，本 session 收敛）

- **口径**：保留父任务**宽 growth**，但**第一版核心 = 两大事：(A) 做优质内容、(B) 运营内容与账号**。cold-email / SEO / CRO / 落地页 / 变现 = **同一循环的渠道变体**，later 铺（Out of Scope）。
- **落地页/部署/产物边界 = Builder**：取决于 CEO 怎么定义产物；growth 产内容+asset，跨职能需求以 sub-goal 建议交 CEO（matrix，不 P2P）。growth **不碰**部署。
- **账号**：假设全部已存在，重点 = 教它**怎么用不同账号**；provisioning 押后。
- **verifier / 记忆（修正，见 design §2）**：growth **不**主动给 verifier 任何 proof；`/company` **只记公司状态（名词）**、非证明接口；verifier 独立去现实核查。→ 发布类 skill **不含**"写 proof 给 verifier"这步。

## Requirements

- **R1 charter 升级**（placeholder → 真）：身份（内容+运营执行者）+ 两大事取向 + **原子 skill 自主组合**（赋能、不规定死流程）+ company-state 只记状态 + 不给 verifier 喂 proof + 跨职能（落地页）交 CEO。赋能式，不堆防御短句。
- **R2 内容侧原子 skill（A）**：v1 = `de-AI-ify`（✅ done）+ `mine-customer-voice`（07-02 二次修订：**vendor** coreyhaines `customer-research` + listening curl 配方；交付 = 写进 `/company` 的客户语言库；**voice 冷启动 = growth 职责、落点自研**；依据见 `research/copy-capability-gaps.md`、详设 design §5.6）+ 视觉三原子 `design-asset`/`gen-image`/`visual-iterate`（07-02 调研回填并**单拆子任务 `../07-02-visual-asset-skills`**：混合 vendor + 自写编排/调用层；生图 API 主路径、Codex 副路径；需求/AC/详设/调研均在子任务，父层只留边界 design §5.5）。方法类 catalog（post/thread/carousel/caption/短视频写法、`copywriting/copy-editing`）**降级为按需 backlog**：缺口分析表明其填的不是真缺口。单一职责、可组合。
- **R3 运营侧原子 skill（B）**：`use-accounts` 写 against **平台/账号 MCP（优先）**、CUA 仅低效回退；per-platform 发布机制。**依赖装哪些账号 MCP（未定、需再看，可能属兄弟 provisioning 任务）** → v1 是否随 MCP 就绪再落待定。cadence/engage/read-signal 押后（observation-gated）。
- **R4 vendor 标注**：复用的开源 skill 拷进本 repo + 标来源 + 许可证（`coreyhaines31/marketingskills` MIT、`blacktwist/social-media-skills` MIT、视觉三原子来源见 research 附录 A）。**用户拍板例外（2026-07-02，内部使用前提）**：guizang（AGPL-3.0）、superdesign（无 license）解禁可 vendor，ATTRIBUTION 注明原许可证状态 + 拍板；未来对外分发本 repo 需回头处理。
- **R5 声明式**：零 .py 逻辑改动；`growth.yaml` skills 追加新条目；`agent/tests/test_resident_loadout.py` 断言更新。
- **R6 原子 + 可组合**：每个 skill = 单一能力、能被 growth 现场拼；**不做巨石 skill**；backlog 明确哪些 v1 / 哪些押后。

## Acceptance Criteria

- [ ] **AC1**：`growth.yaml` skills = `[company-state, receive-goal, + v1 新 skill]`；`test_resident_loadout` 断言含新 skill 且带 `references/` 的多文件 skill 物化存在；`pytest` 绿。
- [ ] **AC2（纪律）**：每条 skill 内容能指认 ①/②/③；**无泛泛 LLM 常识、无"防没观测失败"的防御条目、无"给 verifier 喂 proof"步骤**。
- [ ] **AC3（修正立场）**：charter/skill 中 `/company` 只写状态、verifier 独立核查、落地页边界=Builder，三者可核。
- [ ] **AC4**：vendor 来源/许可证清晰；每个自写 skill 指得出"为什么开源不够"（gap）。
- [ ] **AC5（de-AI-ify 质量）**：`de-AI-ify` 由**具体 tell（反例/信号）**构成，非"更像人类"空泛；全部 skill 风格渐进披露、祈使、可组合。
- [ ] **AC6（backlog）**：哪些 v1 做、哪些押后清楚；"一个一个做"的顺序明确（见 implement.md）。

## Out of Scope（押后 / 不做）

- **押后**（later 铺 / observation-gated）：cold-email / SEO / CRO / 落地页文案 / 变现 等**渠道变体 skill**；闭环 `measure-iterate`（v1 可开环：产出→发布→记状态就收）；运营侧 `cadence/engage/read-signal`；charter 防御短句。
- **不做**：落地页**部署**（Builder）；账号 provisioning（外设/peripheral）；prompt "最优化"（第一版立可迭代骨架）。

## 依据

- 本 session 讨论收敛（两大事 + 原子可组合 + verifier/记忆修正 + 赋能>限制）。
- 父任务 `research/skill-reuse-survey.md`（vendor 策略、`coreyhaines31/marketingskills` near drop-in）+ 父 `prd.md`（通用 charter 结构）。
- `.trellis/spec/backend/peripheral-layer-contracts.md`（外设层 inbound 现状 / outbound 依赖）。
- 子任务 `../07-02-visual-asset-skills/research/visual-asset-skills-research.md`（视觉三原子调研，随任务单拆迁移）。
- memory：`skill-design-no-generic-for-llm`（①/②/③ + 赋能vs防御）、`foundagent-permissions-stance`（少限制多能力）、`foundagent-research-driven-no-samples`（先 research 再写）、`foundagent-layer-decoupling`（/company=状态、跨职能走 CEO）。
</content>
</invoke>
