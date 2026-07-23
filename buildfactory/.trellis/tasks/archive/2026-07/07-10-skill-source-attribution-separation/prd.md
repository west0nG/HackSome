# Skill 来源说明与执行上下文分离

> 状态：规划中，留待下一个 session 继续。本任务独立于 `ceo-user-value-gate`，本次不启动实现。
>
> **07-10 归档注记**：用户决定先归档、暂不做。规划已完成：全量审计（research/audit-*.md，82/82 vendored byte-exact 成立）+ design.md + implement.md。注意 design.md/implement.md 仍是"每 skill 一份 ATTRIBUTION.md"的旧方案，**尚未**同步下面的中央台账修订；未来捡起时以本 PRD 修订为准，先改 design 再实施。
>
> **07-10 修订（用户拍板）**：归位方式从"每 skill 一份旁路文件"改为**仓库级中央台账** `agents/assets/skills/ATTRIBUTION.md`（单一大文件、按 skill 分节）。台账不在任何 skill 目录内，物化按目录逐个复制（`agent/spec.py skill_paths()` 逐项声明），因此**永不进入 agent 容器**。各 vendored 子树内的 `LICENSE*` / `COMMERCIAL_LICENSING.md` 例外：许可证文本必须随副本走，原地保留、继续随 skill 物化。现有 5 份 per-skill ATTRIBUTION.md 并入台账后删除。R2/R6/AC3 已按此修订。

## Goal

把公司运行时 Skill 中与执行无关的来源、归属、改编历史和研究出处，从 Agent 会读取的指令正文中完整剥离；这些信息不能丢失，应迁移到不会在普通执行流程中加载的旁路文档。最终让 Agent 只看到完成任务所需的规则，同时保留法律合规、审计和后续维护所需的来源链。

## Confirmed Facts

- 当前 Skill 物化通过 `shutil.copytree` 原样复制整个目录，仓库层没有剥离 Markdown 注释的逻辑；Agent 读取文件时能看到 `<!-- ... -->`。
- `agents/assets/skills/` 当前共有 23 份 `SKILL.md`，已有 5 份 `ATTRIBUTION.md`。
- 初步关键词扫描发现至少 22 份 Markdown 含可能的来源/归属内容；仅顶层或嵌套 `SKILL.md` 中就有 4 份带 HTML 注释：
  - `create-role/SKILL.md`
  - `decide-direction/SKILL.md`
  - `find-opportunity/SKILL.md`
  - `when-idle/SKILL.md`
- 来源说明不只存在于入口 `SKILL.md`。被入口强制读取的 `references/*.md` 也会进入 Agent 上下文，例如 `decide-direction/references/direction-critic.md`。
- `de-ai-ify`、`design-asset`、`gen-image`、`mine-customer-voice`、`visual-iterate` 已有部分独立归属文件，但执行正文中仍存在归属提示、上游说明或改编历史。
- 部分第三方材料被声明为 vendored、byte-exact 或受特定许可证/内部使用授权约束，不能为了清理上下文而直接丢失或随意改写其法律信息。

## Scope

### 纳入

- `agents/assets/skills/**/SKILL.md`。
- 普通 Skill 执行路径会要求 Agent 读取的 `agents/assets/skills/**/references/**/*.md`。
- 以下非执行信息：
  - 方法论、文章、框架、作者或项目来源；
  - “distilled from / adapted from / inspired by / source concept”等出处说明；
  - per-clause provenance、研究任务路径、历史提交或改造缘由；
  - 版权、许可证、内部使用批准和第三方归属；
  - 仅供维护者理解的 upstream 同步方式或 host adaptation 历史。

### 不纳入

- `.agents/skills/` 中的 Trellis 开发工作流 Skill、用户全局 Skill 或已安装插件 Skill；本任务只处理公司运行时资产 `agents/assets/skills/`。
- 用户任务本身需要的来源行为，例如记录图片 URL、保留 CC 作者名、研究时引用客户原话来源。这些是产品行为规则，不是 Skill 自身的出处说明。
- YAML frontmatter 中用于发现 Skill 的 `name`、`description`。
- 修改任何 Skill 的产品判断、工作流程或输出要求。
- 通过运行时统一删除所有 HTML 注释；本任务处理内容归位，不假设所有注释都无意义。

## Requirements

### R1：建立完整清单并逐项分类

- 扫描全部纳入范围文件，不只依赖单一正则。
- 对每一段候选内容记录：原文件、行号、类别、是否会在普通执行中被读取、目标去向、是否涉及许可证或 byte-exact 约束。
- 区分三类内容：
  1. 可直接迁移的来源/研究说明；
  2. 必须保留但应旁路化的法律/维护说明；
  3. 必须继续留在执行正文中的功能性来源规则。

### R2：来源内容只能迁移，不能静默删除

- 外部来源、作者、许可证、授权例外和 per-clause provenance 必须在迁移前后可追溯。
- 归位方式（07-10 修订）：仓库级中央台账 `agents/assets/skills/ATTRIBUTION.md`，按 skill 分节，统一承载作者、外部来源、许可证记录、授权批准史、研究出处、host adaptation 与上游同步策略。
- 例外：各 vendored 子树内的 `LICENSE*` / `COMMERCIAL_LICENSING.md` 原地保留（许可证文本必须随副本物化，法律要求）。
- 现有 5 份 per-skill ATTRIBUTION.md 并入台账后删除；不得产生多个互相冲突的来源真相源。
- 普通执行正文不得提及或要求阅读台账；台账不物化进容器，维护、法律核查或同步上游时在仓库侧按需读取。

### R3：清理所有 Agent 可见的来源说明

- 从入口 `SKILL.md` 和正常执行必读的 reference 中移除：
  - HTML provenance 注释；
  - 可见的“本方法来自……”段落；
  - 仅用于说明借鉴对象、研究历史或出处的链接；
  - 与执行无关的 vendored/上游归属提示。
- `decide-direction/SKILL.md` 和 `direction-critic.md` 文件末尾的 gstack 来源注释必须成为明确回归样例。
- `find-opportunity`、`create-role` 以及 pattern 文件中的 `Source concept` 注释必须纳入同一轮审计，不能只修复最先发现的两个文件。

### R4：保持行为语义不变

- 迁移前后，Agent 必须获得相同的可执行规则、约束、步骤和判断标准。
- 如果一句话同时包含行为规则和来源说明，应重写为纯行为规则，并把出处部分迁移，而不是整句删除。
- 必须保留功能性来源要求，例如：
  - 下载素材时记录原始 URL；
  - 根据许可证要求保留作者归属；
  - 客户研究保存原话及原始页面；
  - 上游格式确实构成运行时输入约束时，保留该约束本身。

### R5：不得破坏第三方许可证和 vendored 完整性

- 不删除或弱化 `LICENSE*`、`COMMERCIAL_LICENSING.md`、现有授权记录以及用户批准的使用限制。
- 对声明为 byte-exact / untouched 的 vendored 文件，不得直接编辑后仍宣称其为原样副本。
- 设计阶段必须明确这类文件的处理方式，例如：保留 canonical vendored 原件，同时让普通运行路径读取独立的无来源执行层；不得在没有方案时机械批量替换。

### R6：增加防回归检查

- 增加自动检查，阻止新的来源/归属说明重新进入 Agent 正常执行正文。
- 检查应覆盖 HTML 注释和可见段落，同时允许显式登记的功能性来源规则，避免简单禁止所有 `source`、`来源` 或 HTML 注释。
- 检查必须验证（07-10 修订）：中央台账**不**随任何 Skill 物化进容器；各 vendored 子树的 LICENSE 文件仍随 skill 物化；每个登记豁免的 vendored 子树在台账中有对应小节（防台账与资产漂移）。
- 所有现有 Skill 路径、引用闭包、loadout 测试和相关完整性测试继续通过。

## Acceptance Criteria

- [ ] AC1：形成覆盖 23 份 `SKILL.md` 及其正常执行必读 references 的逐项审计清单。
- [ ] AC2：`decide-direction`、`direction-critic`、`find-opportunity` 和 `create-role` 中已知的来源注释不再出现在 Agent 执行正文中。
- [ ] AC3：所有纳入范围的外部方法论、出处、归属、许可证和历史说明均能在中央台账 `agents/assets/skills/ATTRIBUTION.md` 中找到，没有静默丢失；vendored 子树内的 LICENSE 文件原地完好。
- [ ] AC4：任何声明为 vendored/byte-exact 的原件仍满足其完整性约束，或已明确改名并停止宣称 byte-exact。
- [ ] AC5：功能性来源行为仍然存在，Agent 仍会记录用户素材来源、遵守许可证并保留研究证据。
- [ ] AC6：对全部运行时 Skill 执行自动扫描时，不再发现未登记的来源/归属说明；新增一个来源注释 fixture 时测试会失败。
- [ ] AC7：Skill 物化、引用文件存在性、现有角色 loadout 和相关测试全部通过。
- [ ] AC8：不改变任何 Skill 的业务行为；差异审阅能把每项正文删除对应到旁路迁移记录。

## Next-session Entry Point

1. 重新运行全量语义盘点并生成迁移清单。
2. 检查现有 5 份 `ATTRIBUTION.md` 及 vendored/许可证约束。
3. 为复杂任务补齐 `design.md` 和 `implement.md`，重点决定 byte-exact vendored 文件的无来源运行层。
4. 把最终方案交给用户审阅；未获批准前不要执行迁移或运行 `task.py start`。
