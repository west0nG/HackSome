# 设计：全量精简 Skill Description

> 状态：已按本设计实施；最终静态与动态证据见 `research/verification.md`。

## 1. 总体边界

本任务保持一份 runtime-neutral skill 资产，不引入 Claude Code/Codex 两套 frontmatter：

```text
agents/<role>.yaml
  → AgentSpec.skill_paths()
  → sync_skills(同一批顶层 host 目录)
  → Claude Code: <CLAUDE_CONFIG_DIR>/skills/<name>/
  → Codex: ~/.agents/skills/<name>/
  → catalog 只读取顶层 host 的 name + description
```

两个 adapter 不改。差异只存在于落盘目录与各 CLI 的 catalog 渲染方式；description 内容、长度规则、role loadout 和 host 正文均共用。

## 2. 收紧 catalog 暴露面

### 2.1 四个 vendored 入口改名

运行时按精确文件名 `SKILL.md` 发现入口。四份上游完整 skill 继续留在消费它们的 host 子树，但入口改用仓库已有的 `upstream-SKILL.md` 先例：

| Host | 实施前路径 | 新路径 | 实施前 SHA-256（改名后必须相同） |
|---|---|---|---|
| `de-ai-ify` | `zh/SKILL.md` | `zh/upstream-SKILL.md` | `28ccdd2792a456168e7872f6d9d1186982680128240b38516bf83c84ea272beb` |
| `design-asset` | `references/anthropic-frontend-design/SKILL.md` | `references/anthropic-frontend-design/upstream-SKILL.md` | `1608ea77fbb6fc30d13a97d12cfa8ebf31358d40f0dd97beed24829d6b3f45dd` |
| `gen-image` | `references/smixs-image/SKILL.md` | `references/smixs-image/upstream-SKILL.md` | `cbcb39232bfd43e14f05bc0ead38b8fd01a5304aca6f295befc8021345cc0dea` |
| `gen-image` | `references/codex/SKILL.md` | `references/codex/upstream-SKILL.md` | `30747274af88ee0c0a335f9de96039d33379289cf56d60e620a57c5425c5c894` |

选择 `upstream-SKILL.md` 而不是 provider 配置有三个原因：

1. `design-asset/references/guizang/upstream-SKILL.md` 已证明该名字不会被当作独立 skill；
2. 文件内容可以保持 byte-exact，只变路径；
3. Claude Code 与 Codex 同时生效，不依赖一侧专属的 listing override。

同步更新三个 host 的读取路径、reference map、完整性测试与物化断言；实施扫描确认现行树没有承载这些旧路径的 ATTRIBUTION 文件可改。Vendored 正文中出现的裸文本 `SKILL.md` 都是对上游入口的语义称呼，不是指向自身的 Markdown 文件链接；不改这些字节。Host 增加一条适配说明：子树内的 `SKILL.md` 称呼指当前的 `upstream-SKILL.md`。

### 2.2 最终 catalog 集合

自动化校验从五份 role YAML 计算集合，最终数量固定为：

| Role | 顶层 skill 数 |
|---|---:|
| Builder | 7 |
| CEO | 10 |
| Growth | 13 |
| Researcher | 7 |
| Verifier | 4 |

任何 role 声明目录内部再次出现精确名 `SKILL.md` 都视为 catalog 泄漏并失败；`upstream-SKILL.md`、普通 references 和 scripts 不受影响。

## 3. Description 合同

### 3.1 内容顺序

每个 description 最多承载三件事，按顺序写：

1. **能力/结果**：这个 skill 解决什么问题；
2. **正向触发**：Agent 在什么事件、Goal 或任务语境下使用；
3. **一个必要边界**：仅在容易与相邻 skill 混淆时保留。

执行步骤、命令、工具实现、持久化流程、治理来历、完整例子列表和设计理由不进入 description。权限信息只有在决定“是否加载”时保留，例如 reviewer-only 与 Direct Messages 排除边界。

### 3.2 格式与预算

统一使用可被 PyYAML、Claude Code 和 Codex 解析的 frontmatter；长行优先写成 folded scalar：

```yaml
---
name: example-skill
description: >-
  Do something useful. Use when the relevant event happens; not for the
  neighboring case.
---
```

- Frontmatter 只含 `name`、`description`；`name` 与目录名相同。
- 解析后的 description 必须是单行、首尾无空白、内部空白已归一化。
- 常规目标：120–180 Unicode 字符。
- 单项硬上限：200 Unicode 字符。
- 任一角色的 Foundagent description 总量硬上限：2,000 Unicode 字符。
- 预算按解析后字符串的 Python `len()` 计算，不绑定 provider tokenizer。
- 低于 120 字符不是失败；像简单 Goal 协议一样，短而完整优于为凑长度加字。

## 4. 目标文案

以下英文是实际要写入 frontmatter 的目标文本；表格其余说明为中文审阅材料。

| Skill | 字符数 | 目标 description |
|---|---:|---|
| `check-email` | 123 | `Receive email sent to a foundagent.net address. Use when a task expects an inbound reply, verification code, or magic link.` |
| `claim-mailbox` | 136 | `Find, share, or claim a foundagent.net address. Use when a task needs an inbound identity for signups, magic links, or external contact.` |
| `company-state` | 130 | `Read and update shared company state in /company. Use at session start, whenever durable state changes, and before finishing work.` |
| `create-role` | 166 | `Create and propose a resident department with its charter, skills, and loadout. Use when recurring work lacks a suitable owner; add tools to an existing role instead.` |
| `de-ai-ify` | 121 | `Remove AI-writing tells. Use on finalized public-facing English or Chinese copy before it is sent or baked into an asset.` |
| `deploy-site` | 132 | `Apply foundagent.net naming, deployment, domain, and DNS rules. Use when publishing a public site or changing its Foundagent domain.` |
| `design-asset` | 167 | `Build text-led static visual assets in HTML/CSS and render them to PNG. Use for social cards, covers, carousels, and typography-heavy graphics; not standalone imagery.` |
| `find-opportunity` | 153 | `Research and generate evidence-backed company directions. Use only when the CEO needs a new objective candidate and has none; not for ordinary idle work.` |
| `gen-image` | 167 | `Generate or edit standalone imagery with provisioned image models. Use for illustrations, photos, backdrops, and visual series; route text-led layouts to design-asset.` |
| `mine-customer-voice` | 164 | `Mine customer language from reviews, forums, and comments into /company. Use before writing for a new segment or when its language and brand-voice evidence is thin.` |
| `operate-twitter` | 176 | `Operate the company’s public Twitter/X account. Use the authenticated browser for audits, profile edits, posts, replies, follows, likes, pins, or deletion; not Direct Messages.` |
| `provision-ga4` | 115 | `Create a GA4 property and web stream for a deployed Foundagent site. Use when the live site needs a measurement ID.` |
| `receive-goal` | 128 | `Handle an incoming Goal: understand it, complete the real work, and report the result. Use whenever a Goal arrives in the inbox.` |
| `review-objective` | 135 | `Review an OBJECTIVE-REVIEW request and record the verifier’s verdict. Use only in the verifier role; never when proposing an objective.` |
| `review-role` | 129 | `Review a ROLE-REVIEW request for a proposed resident department and record the verifier’s verdict. Use only in the verifier role.` |
| `send-email` | 152 | `Send outbound email from an owned or shared foundagent.net address. Use for external replies, follow-ups, or notifications; not agent-to-agent messages.` |
| `send-goal` | 124 | `Delegate work to another department by writing and sending a concrete Goal. Use when another role should produce the result.` |
| `set-objective` | 168 | `Set or revise the CEO’s standing objective through independent review. Use when none exists, it is achieved, or evidence invalidates it; not for choosing the next Goal.` |
| `visual-iterate` | 141 | `Validate and iteratively refine rendered visual assets before delivery or publication. Use after design-asset or gen-image produces an image.` |
| `when-idle` | 136 | `Handle a heartbeat with no new messages: check the Goal ledger, stand down if work is active, or dispatch a Goal if the ledger is empty.` |

汇总：20 项共 2,863 字符 / 443 个英文分词；按角色为 Builder 916、CEO 1,405、Growth 1,852、Researcher 916、Verifier 546 字符。

## 5. 静态校验设计

新增 `agent/tests/test_skill_catalog.py`，以 role YAML 和源目录为唯一事实源：

1. 读取 `agents/*.yaml`，解析每个角色声明的 skill 路径；
2. 对顶层 `SKILL.md` 用 PyYAML 解析 frontmatter；
3. 校验字段、目录名、字符串规范、单项 200 字符和角色 2,000 字符预算；
4. 递归检查声明目录下不存在第二个精确名 `SKILL.md`；
5. 校验四份 `upstream-SKILL.md` 的 SHA-256，保证只改名不改内容；
6. 对高碰撞组保留少量语义锚点，而不是锁死整句：
   - `claim-mailbox` / `check-email` / `send-email`；
   - `design-asset` / `gen-image` / `visual-iterate`；
   - `find-opportunity` / `set-objective` / `when-idle`；
   - `send-goal` / `receive-goal`；
   - `review-role` / `review-objective` 的精确事件名与 verifier 边界。

同步调整 `test_operate_twitter_skill.py`：继续固定 Twitter、profile、post/reply、deletion 和 Direct Messages 边界，但不要求旧长描述的逐字词形。

## 6. 双 Runtime 动态验证

动态验证是实现后的隔离证据，不放进每次 CI；静态测试才是长期硬门。

### 6.1 发现检查

- 用临时 HOME/会话目录分别物化 `provider: claude-code` 与 `provider: codex`。
- Claude Code 从 stream-json `init.skills`/Skill 列表取实际发现集合。
- Codex 从首轮 developer `skills_instructions`/JSONL 取实际发现集合。
- 两边都必须只看到角色顶层 host；Growth 不得出现 `qu-ai-wei`、`frontend-design`、`image`、`codex-imagegen`。
- 使用镜像固定版本 Claude Code 2.1.202 与 Codex 0.142.5；本机其他版本只作辅助，不替代固定版本证据。

### 6.2 高风险触发矩阵

同一组安全、无外部写入的路由请求分别交给两个 runtime。允许加载必要的辅助 skill，但必须命中预期 host，且不得命中指定的相邻错误入口。

| 场景 | 必须命中 | 不应作为该意图入口 |
|---|---|---|
| 为新 signup 选择可收信身份，尚未等待邮件 | `claim-mailbox` | `check-email`, `send-email` |
| 已触发 signup，正在等验证码/魔法链接 | `check-email` | `claim-mailbox`, `send-email` |
| 制作文字主导的小红书卡片 | `design-asset` | `gen-image` 作为主构建路径 |
| 制作无排版文字的独立 hero 插画 | `gen-image` | `design-asset` 作为主构建路径 |
| CEO 需要调研候选方向，明确尚不裁决/提案 | `find-opportunity` | `set-objective` 作为当前动作 |
| CEO 已有候选与证据，要替换 standing objective | `set-objective` | `find-opportunity` |
| 对即将发布的中文文案去 AI 味 | `de-ai-ify` | 隐藏的 `qu-ai-wei` 名称 |
| 审计公开 X profile，不涉及私信 | `operate-twitter` | `send-email`，任何 Direct Messages 路径 |

验证请求明确“只做路由/计划，不执行外部写入”，输出与发现证据记录到任务 research 工件。模型路由具有非确定性：动态矩阵用于发现明显退化，不替代静态合同；单次额外辅助 skill 不算失败，稳定命中错误 sibling 才回改 description。

## 7. 文档与兼容性

同步更新：

- `aiworkforce/SOP-adding-roles-and-skills.md`：description 三段职责、200/2,000 预算、顶层入口规则；
- `docs/overview.md`：catalog 只暴露 role YAML 顶层 host，vendored 方法层按需读取；
- `.trellis/spec/backend/agent-execution-contracts.md`：两个 runtime 共用资产与嵌套入口禁止规则；
- 受路径影响的 host、ATTRIBUTION 和现行测试。

不回写归档 Trellis 任务或 firsttest/secondtest/thirdtest 状态。

## 8. 回滚与风险

- **路径漏改**：host 找不到上游入口。由引用完整性、物化测试和真实路由检查捕获；回滚四个文件名及引用即可。
- **Vendor 漂移**：改名时内容被改。由固定 SHA-256 立即失败。
- **过度压缩**：相邻 skill 误触发。由语义锚点与双 runtime 矩阵捕获；只放宽具体 description，不放宽全局预算。
- **Runtime 漂移**：未来 CLI 改发现规则。静态“无嵌套 `SKILL.md`”仍是最保守的开放标准形状；升级 runtime 时重跑发现检查。
- **回滚范围**：还原 20 份 frontmatter、四个路径及 host/ATTRIBUTION/测试/文档改动；无数据迁移、无运行时状态变更。
