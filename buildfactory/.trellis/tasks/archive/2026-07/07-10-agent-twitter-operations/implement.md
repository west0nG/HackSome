# Implement — Agent Twitter 运营能力

> 当前处于规划阶段。只有用户审阅 `prd.md`、`design.md` 与本文件并明确同意实施后，才运行 `task.py start`。Codex inline 模式不生成或依赖 `implement.jsonl` / `check.jsonl`。

## A. 实施前门禁

- [ ] 重新运行 `python3 ./.trellis/scripts/task.py current --source`，确认当前任务仍是 `07-10-agent-twitter-operations`。
- [ ] 加载 `trellis-before-dev` 与 Phase 2.1 细节，读取其中要求的相关 spec；不直接从规划阶段跳到编辑代码。
- [ ] 检查 `git status --short` 与 `git diff --name-only`。当前工作树已有其他任务的未提交修改；只触碰本计划列出的文件，不覆盖或纳入无关变化。
- [ ] 复核当前事实：
  - `agents/growth.yaml` 仍没有 `operate-twitter`；
  - `agents/mcp/growth.json` 的 `playwright` 仍指向 `agent/browser_mcp.sh`；
  - `state/foundagent/company/social/x_account.md` 仍记录待清理测试帖 `https://x.com/Solvotheagent/status/2074071054834974853`；
  - 用户的付费 API 拒绝、浏览器风险接受、真实账号读写授权和 DM 后置决策未被后续需求推翻。
- [ ] 若实现前 X、Playwright 或 Skill runtime 的事实已变化，先更新 planning artifacts 并回报用户，不凭旧研究继续。

## B. 建立 Skill 骨架

- [ ] 按 `skill-creator` 原则创建 `agents/assets/skills/operate-twitter/`：项目文件全部通过 `apply_patch` 写入；如需运行系统 `init_skill.py`，只在临时目录生成参考骨架，不把不符合本仓库约定的 `agents/openai.yaml` 或模板文件带入项目。
- [ ] 新建 `SKILL.md`：
  - frontmatter 只含 `name: operate-twitter` 与覆盖 Twitter/X 运营触发场景的 `description`；
  - 使用祈使语气，保持核心入口精简；
  - 明确 Goal 触发边界、`/company` 渐进发现、五个决策就绪问题、实时 X 优先、价值排序、身份门、结果核实与 `company.py record`；
  - 直接链接四个 playbook，并说明何时读取；
  - 明确首期使用现有 Playwright、无付费 API、无 DM、CLI 后置；
  - 不写固定 company topic、账号 handle、品牌、selector、发帖频率或 vanity metric 目标。
- [ ] 新建 `references/bootstrap-or-reposition.md`：主页审计、身份/受众/承诺、资料与视觉一致性、置顶与首批内容、按需组合现有 VOC/视觉 Skills。
- [ ] 新建 `references/publish.md`：真实信号选材、近期内容去重、post/Thread/quote 选择、按需组合 `de-ai-ify`/视觉 Skills、发布后 canonical 验证。
- [ ] 新建 `references/engage.md`：公开 mentions/搜索/目标讨论、reply/quote/like/follow 的现场判断、完整上下文读取、价值优先、DM 边界。
- [ ] 新建 `references/maintain.md`：资料调整、置顶/取消置顶、已有内容审计、精确删除、测试变更恢复。
- [ ] 检查四个 playbook 不重复核心闭环，不复制现有 Skill 的长篇方法，也不互相深层引用。

## C. Loadout 接线与静态契约

- [ ] 修改 `agents/growth.yaml`：
  - 在 Growth baseline skills 中加入 `assets/skills/operate-twitter`；
  - 更新顶部过时的 `Charter + use-accounts follow` 注释；
  - 不修改 provider、hooks、MCP 或 permission mode。
- [ ] 修改 `agent/tests/test_resident_loadout.py`：
  - Growth skill set 增加 `operate-twitter`；
  - 新增物化断言，确认 `SKILL.md` 与四个 references 经真实 `copytree` 路径全部存在；
  - 其他角色的 baseline skill set 保持不变。
- [ ] 新增 `agent/tests/test_operate_twitter_skill.py`：
  - 解析并校验 frontmatter `name` / `description`；
  - 检查 `SKILL.md` 四个直接 Markdown reference 均可解析；
  - 固定核心闭环、自由状态发现、实时 X、Goal 权限、Playwright、DM 与 CLI 边界的少量结构性锚点；
  - 确认没有把 `/company/channels/` 或某个账号 handle 作为运行前提；
  - 不把价值判断实现成测试里的关键词打分，也不复制整份 Skill 形成同源断言。

## D. 确定性验证

- [ ] 运行定向测试：

  ```bash
  .venv-cua/bin/python -m pytest \
    agent/tests/test_resident_loadout.py \
    agent/tests/test_operate_twitter_skill.py \
    agent/tests/test_mcp_assets.py \
    agent/tests/test_browser_mcp.py -q
  ```

- [ ] 运行 loadout 静态检查：

  ```bash
  make loadout-check COMPANY=foundagent
  ```

- [ ] 对新增 Skill 做人工结构检查：
  - 主入口控制在 500 行以内，playbook 一层直达；
  - 无死链、无模板占位、无 README/CHANGELOG；
  - 没有把 `xurl`、XMCP、X API credential 或付费 credits 写成前置；
  - 没有 DM 操作说明；
  - 没有固定 `/company` taxonomy、固定账号或易碎 DOM selector；
  - “不操作”仍是合法决策分支。

## E. 容器只读 smoke

- [ ] 检查默认 foundagent stack 与 goal ledger；如有其他 Goal 正在运行，不重启 Growth 或插入测试 Goal，先等现有工作自然结束。
- [ ] 让 Growth 容器重新物化 loadout（优先只重启/重建必要服务，不无故重置整家公司），在容器内确认：
  - `operate-twitter/SKILL.md` 与四个 references 已落在该 runtime 的 skills 目录；
  - Playwright MCP 正常连接；
  - 打开 `https://x.com` 为 @Solvotheagent 登录态；
  - 能从实时主页读到 handle、资料、置顶和近期内容；
  - 没有执行任何 mutation。
- [ ] 登录态失效则按现有 `accounts/README.md` 契约报告并处理，不改写 browser wrapper，不改走 API。

## F. 真实账号 E2E

### F1. 起始快照

- [ ] 用 company CLI 按 MAP → social → `x_account.md` 的当前自然路径读取状态；此路径只属于 foundagent 测试实例，不写进通用 Skill。
- [ ] 在 `research/e2e.md` 记录：测试时间、当前 handle、资料摘要、置顶、待删测试帖 URL，以及测试前需要恢复的资料值。不得记录 cookies、token 或 secret。

### F2. 第一个新上下文：真实动作闭环

- [ ] 通过现有 Hub/Goal 路径向 Growth 派一个结果型 Goal，要求使用 `operate-twitter` 审计并维护当前账号。Goal 明确允许删除已记录的测试帖；不要把逐步操作写死，让 Skill 自己完成状态→实时→判断闭环。
- [ ] verifier-only acceptance 要求独立确认：
  - 已读取 `/company` 与实时 X；
  - 操作账号为 @Solvotheagent；
  - 已删除测试帖 `2074071054834974853` 或给出实时不可删除的具体原因；
  - 临时测试内容不存在；
  - `/company` 保持当前状态语义而非操作日志。
- [ ] 观察 Growth 实际选择的 playbook、页面读取量和 token/耗时，不中途替它提供隐藏路径；记录真实摩擦，作为是否需要后续 CLI 的依据。
- [ ] 若已有测试帖足以覆盖 mutation→verify，不额外造临时内容。只有关键发布路径仍未被既有 `07-03-social-rail` 证据与本轮测试覆盖时，才发布一条明确临时内容并在同一收尾中删除。
- [ ] 若 Skill 判断某项资料变更对账号真实有价值，可以保留；否则恢复初始值。所有临时变化在本轮结束前从实时 X 二次确认已恢复。

### F3. 第二个新上下文：跨回合接续

- [ ] 再派一个只读 Twitter 状态 Goal，让新的 Growth 上下文重新从 `/company` 与实时 X 恢复账号状态，报告下一项最有价值动作或合理不行动，不重复已删除测试内容，也不执行外部写入。
- [ ] 核对第二个上下文无需人类复述第一轮发生了什么，并正确处理 `/company` 与实时 X 的优先级。

### F4. E2E 收尾

- [ ] 完成 `research/e2e.md`：分别列出保留的真实变化、已恢复临时变化、已删除旧测试垃圾、token/浏览器摩擦与尚未覆盖的动作。
- [ ] 从实时 profile 与所有临时 post/reply URL 做最后一次清理检查。发现残留立即在当前实现回合清理，不留到未来 session。
- [ ] 若真实运行暴露重复/高 token 流程，只记录具体调用序列和成本；不在本任务顺手实现 CLI。

## G. 全量质量检查

- [ ] 加载并执行 `trellis-check`，按 inline 模式由主会话直接检查，不派实施/检查 sub-agent。
- [ ] 运行全量相关测试：

  ```bash
  .venv-cua/bin/python -m pytest \
    agent/tests/ orchestration/tests/ company_state_kit/tests/ peripheral/tests/ -q
  ```

- [ ] 检查完整数据流：Growth yaml → loadout materialization → Skill trigger → company-state 读取 → Playwright 实时读取/动作 → company-state record → verifier 独立验收。
- [ ] 检查复用与一致性：没有复制现有 VOC、去 AI 味、视觉 Skill；没有修改 browser wrapper/MCP；没有把 foundagent 的实际 `social/x_account.md` 路径写进通用资产。
- [ ] 检查 `git diff --check`、`git status --short` 与任务范围；无关脏文件保持原样。

## H. Spec、提交与收尾

- [ ] 使用 `trellis-update-spec` 更新 `.trellis/spec/backend/resident-agent-contracts.md`：记录 Growth 的 `operate-twitter` loadout、自由状态发现、实时 X 优先、四 playbook、浏览器复用与 CLI/DM 边界。只写已验证的当前契约。
- [ ] 复跑定向与全量测试，确保 spec 更新没有引入断言/引用漂移。
- [ ] 按 Trellis Phase 3.4 只暂存本任务文件；不得把 `.trellis/tasks/07-10-email-send-resend/` 或其他用户修改带入提交。
- [ ] 提交信息建议：`feat(growth): add stateful twitter operations skill`。
- [ ] 运行任务归档/收尾流程，最终向用户报告：Skill 结构、测试结果、真实账号保留/删除/恢复项、已知浏览器风险和 CLI 是否出现真实建设依据。

## 回滚点

1. **Skill 未接线前**：删除新增目录和测试即可，运行时零变化。
2. **Loadout 接线后**：从 `agents/growth.yaml` 移除一行并重启 Growth，manifest reconcile 会移除物化 Skill；不改浏览器与 company state。
3. **真实账号 E2E 中**：资料临时值按起始快照恢复；临时帖子/回复立即删除。旧测试垃圾删除不可逆，但这是用户授权且目标明确的真实清理。
4. **平台限制/封号**：网页自动化风险已由用户接受，没有技术回滚可以保证恢复账号；停止后续 mutation，保留事实记录，不隐瞒或自动切换付费 API。
