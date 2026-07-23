# 全量精简 Skill Description

> 状态：已实施。下文背景中的“当前”指任务启动时基线；最终数值与验证证据见 `research/verification.md`。

## 目标

把 Foundagent 会注入 Agent skill catalog 的 `description` 收敛为低成本、可判定的路由索引：Agent 只凭 description 就能判断何时加载哪个 skill，同时不再在每次唤醒里携带流程、实现、治理背景和例子等应当按需展开的内容。

## 背景与已确认事实

- 项目约定 skill 靠 frontmatter `description` 自动发现，命中后才读取 `SKILL.md` 正文；`docs/overview.md` 已将其定义为“一句 description”的渐进披露入口。
- Codex 把全部可用 skill 的名称、description 和路径放进每轮上下文，并设有 2% skills context budget。仓库中的真实 Codex fixture 已记录 description 超预算后被自动截短的警告；这证明预算约束真实存在，但不等于每个 Foundagent 角色当前都已经触发警告。
- `agents/assets/skills/` 当前共有 24 份 `SKILL.md`：20 份角色 YAML 直接声明的顶层 skill，另有 4 份嵌套 skill；当前 Codex 会把后四份也递归发现为独立入口。
- 当前 24 份 description 合计 7,366 字符 / 1,163 个英文分词；只算 20 份顶层文件也有 5,760 字符 / 935 词。
- 按当前角色 loadout 整树物化后的可发现基线：Builder 7 项 / 1,570 字符 / 271 词，CEO 10 项 / 2,747 字符 / 467 词，Growth 17 项 / 5,080 字符 / 788 词，Researcher 7 项 / 1,570 字符 / 271 词，Verifier 4 项 / 1,243 字符 / 197 词。
- Growth 的 17 项包含 4 个嵌套条目：`qu-ai-wei`、`frontend-design`、`image`、`codex-imagegen`。真实 Growth Codex rollout 证明这些 reference 子树中的 `SKILL.md` 会被当作独立 skill 注入 catalog，而不只是 host skill 的按需参考文件。
- 这 4 项的嵌套位置来自既有“host 适配层 + vendored 方法层”设计，而不是有意建立第二层 role capability：`de-ai-ify` 用 `qu-ai-wei` 作为中文控制层，`design-asset` 用 `frontend-design` 作为审美方法层，`gen-image` 同时组合 `image` 的提示词控制层与 `codex-imagegen` 的调用/调试资料。角色 YAML 只声明三个顶层 host，host 正文再按场景读取子树。
- 当时整树保留 `SKILL.md` 是为了维持上游依赖闭包。`de-ai-ify` 的第一版曾只拷叶子 reference，盲评发现语体矩阵、冲突仲裁等控制层缺失并产生死链，随后才改为 intact vendor；视觉 skill 沿用了同一模式。运行时递归扫描恰好把这些内部入口重新注册为独立 skill，因此当前 catalog 暴露是存储形状泄漏出的副作用，并非角色 loadout 的显式设计。
- 上述 4 份嵌套 `SKILL.md` 都属于 vendored 依赖闭包，现有归档审计把它们锁为 byte-exact；直接改它们的 frontmatter 会破坏 vendor 完整性合同。
- `agent/tests/test_operate_twitter_skill.py` 当前把 `twitter/profile/publish/reply/delete` 和 Direct Messages 排除边界固定在 description 中。其他 Objective 等 prompt 合同主要固定正文语义，而不是 description 的长度。
- `aiworkforce/SOP-adding-roles-and-skills.md` 要求 description 与 wake prompt 的措辞对齐；精简不能只追求字符数而牺牲实际触发。
- Codex `skill-creator` 明确规定 frontmatter 是触发前唯一可见的判断面，必须同时写清“做什么”和“何时用”；因此本任务删除的是流程与背景，不会把 description 压成只有能力名的模糊标签。
- 逐份核对 20 个 host 正文后的目标文案已验证压缩可行：全部顶层 description 可从 5,760 字符 / 935 词降到 2,863 字符 / 443 词，最长单项 176 字符；按角色计算为 Builder 916、CEO 1,405、Growth 1,852、Researcher 916、Verifier 546 字符。精确文案与逐项字符数见 `design.md §4`。
- 两个 runtime adapter 都从同一个 `AgentSpec.skill_paths()` 读取 `agents/assets/skills/`，再调用同一个 `sync_skills` 整树物化；差别仅是 Claude Code 落到 `<CLAUDE_CONFIG_DIR>/skills/`，Codex 落到 `~/.agents/skills/`。本任务无需维护两套 description 或转换层。
- Claude Code 与 Codex 都以 `SKILL.md` 的 `name`/`description` frontmatter 作为发现入口。Codex 的 2% 截短是额外压力；200 字符上限低于两边现有可接受范围，对 Claude Code 只是减少常驻上下文，不会失去格式兼容。

## 需求

### R1：覆盖全部实际注入项

- 审计并处理所有会进入五个角色 skill catalog 的 Foundagent description，不能只改最长几项。
- 统计必须按运行时实际递归发现结果计算，而不是只按角色 YAML 的顶层目录数计算。
- 不修改 Codex 自带 system skills、外部插件或 Agent 自己安装的第三方 skill。
- Catalog 只允许暴露角色 YAML 显式声明的顶层 host skills；嵌套 vendored 方法层继续随 host 物化并由其按需读取，但不得再以独立 skill 自动注册。

### R2：Description 只承担路由职责

- 每个 description 只保留：能力/结果、正向触发条件，以及确有碰撞风险时的一个关键排除边界。
- 执行步骤、工具细节、持久化流程、治理来历、完整例子枚举和设计理由移回 `SKILL.md` 正文、charter、spec 或任务工件。
- description 使用 Agent 实际收到的事件/Goal/wake 用语，避免仅用内部实现名或抽象类别词。

### R3：精简后仍可判定

- 意图相邻的 skill 必须保持清晰边界，例如 `design-asset` 与 `gen-image`、`find-opportunity` 与 `set-objective`、`claim-mailbox` 与 `check-email`、`send-goal` 与 `receive-goal`。
- 角色专属权限或安全边界只有在影响“是否应加载该 skill”时才留在 description；加载后的执行约束留在正文。
- 现有真实触发合同不得因删词失效；需要同步调整过度拟合旧长文案的静态测试。
- 所有顶层 skill 做静态覆盖；动态验证采用用户已批准的高风险代表矩阵，在 Claude Code 与 Codex 各跑一遍，不做低信号的 20×2 全量模型调用。

### R4：建立可持续预算门

- 增加可重复运行的静态校验，解析所有受管 `SKILL.md` frontmatter，并对单项长度、角色 catalog 总量、必需字段和可解析性给出明确失败信息。
- 常规 description 目标为 120–180 字符；单项硬上限 200 字符；任一角色的 Foundagent description 总量硬上限 2,000 字符。预算按 Unicode 字符计数，不绑定某个 provider 的 tokenizer。
- 同步更新 skill 编写 SOP，使以后新增或修改 skill 时先满足同一 description 合同。

### R5：保持依赖与运行时兼容

- 不以直接改写 byte-exact vendored 文件来换取长度下降。
- 4 份 vendored 入口文件改成 runtime 不会自动发现的文件名/形状，文件内容保持 byte-exact；同步更新 host 路由、内部可解析引用、attribution 路径记录和物化测试。
- 不再保留直接点名调用 `qu-ai-wei`、`frontend-design`、`image`、`codex-imagegen` 的独立入口；对应意图分别由 `de-ai-ify`、`design-asset`、`gen-image` 路由。
- Claude Code 与 Codex 使用同一份 skill 资产；设计必须在两种 runtime 的发现模型下成立。
- 不使用 Claude Code 专属的 skill listing override，也不使用 Codex 专属配置来隐藏嵌套项；通过两边共用的文件形状解决，避免切换 provider 后 catalog 漂移。
- 不丢失 host skill 对 vendored 方法正文的按需读取路径、许可证或 attribution 记录。

## 验收标准

- [x] AC1：五个角色所有实际可发现的 Foundagent skill 均纳入审计；清单和角色总量可由自动化校验复现，最终为 Builder 7、CEO 10、Growth 13、Researcher 7、Verifier 4，且没有嵌套 vendored 条目。
- [x] AC2：所有受管 description 不超过 200 Unicode 字符，常规项以 120–180 字符为目标；低于 120 字符但已完整表达能力与触发的短项不填充，且所有项均无流程、实现或设计背景残留。
- [x] AC3：每个角色的 Foundagent description 总量不超过 2,000 Unicode 字符；Growth 从 5,080 字符 / 788 词降至 1,852 字符。
- [x] AC4：相邻 skill 的正向触发和排除边界通过静态合同，并在 Claude Code/Codex 各自的八场景高风险路由矩阵中验证。
- [x] AC5：vendored byte-exact 文件校验、skill 引用完整性、loadout、Objective、Twitter 及全量测试继续通过。
- [x] AC6：SOP 与现行 backend/overview 文档描述同一套 catalog 和 description 规则。
- [x] AC7：分别用 `provider: claude-code` 与 `provider: codex` 做隔离发现检查，证明两边看到相同的角色顶层 skill 集合和新 description，且都不暴露 4 个嵌套 vendored 名称；未修改或重启现有 firsttest/secondtest/thirdtest。

## 不在范围内

- 不精简 `SKILL.md` 正文、references、charter、Objective 或 company state 的内容体量。
- 不调整角色业务能力集合，也不因为本任务删除某项顶层 role skill。
- 不修改 Codex 的 2% 预算算法或第三方 plugin/system skill。
- 不把“description 更短”当成充分条件；触发准确性优先于机械压缩率。
