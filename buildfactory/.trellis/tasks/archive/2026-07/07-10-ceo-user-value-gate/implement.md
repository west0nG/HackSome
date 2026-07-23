# 实施计划：CEO 用户价值闸门

> 主体实现、确定性回归与真实 resident verifier 模型行为校准均已完成，见第 8 节。

## 前置与发布依赖

- [x] 删除旧 Skill 前确认 `07-10-skill-source-attribution-separation/research/audit-inhouse.md` 已逐项保存 `decide-direction` / `direction-critic` 的来源、许可和原文定位；全局来源剥离任务仍按用户要求留到下一 session，不在本任务执行。
- [x] 由独立任务 `07-10-when-idle-objective-handoff` 完成三处入口迁移，并与本任务放在同一发布序列；没有改写其运营语义。
- [x] 开发前运行 `trellis-before-dev`，重新读取当时有效的 backend specs 和工作区状态。

## 1. 先锁住机制回归

- [x] 扩展 `orchestration/tests/test_objective.py` 的 fixture，使 CEO 有隔离的 `/agents`、`/company` 和 inbox。
- [x] 锁住 CEO v2 bundle 必填项、path confinement/nav name、动态指针、manifest hash、revision、owned-leaf 防覆盖、FAIL 前缀。
- [x] 锁住 `RESHAPE`/`DROP` 的 staged 生命周期、PASS full/short 同步、path 迁移和旧版本归档。
- [x] 为 company、delete、history、short、active metadata、committed journal 等写点增加故障注入，并覆盖 prepared/committed journal 恢复。
- [x] 保留并继续通过全部非 CEO legacy proposal、身份门、无 verdict 不生效和重复 verdict fail-closed 测试。

## 2. 提供 company-state 的受控存储接口

- [x] 在 `company_state_kit/company.py` 中最小抽取受 root lock 保护的 snapshot/write/delete/restore API；受控 API 与 CLI 复用 `_apply_write` 和同一导航维护逻辑。
- [x] 删除只接受 leaf，拒绝 root、目录、`MAP.md`、`OVERVIEW.md` 和越界路径；objective 只删除 active metadata 明确拥有的旧 leaf。
- [x] 写入、删除、恢复后继续满足 INV1–INV4；不自动生成任何业务 topic。
- [x] 在 `company_state_kit/tests/test_company.py` 增加 path 安全、summary 保留、old leaf 删除、nav reconcile 和恢复测试。

## 3. 实现 CEO proposal bundle 与 revision gate

- [x] 在 `orchestration/objective.py` 增加 v2 manifest、稳定序列化、SHA-256 和 revision id。
- [x] 扩展 `propose` 参数：`--short-file`、`--company-path`、`--company-summary`；CEO 缺失任一项 fail closed，非 CEO 保持旧接口。
- [x] stage full/short 后最后原子写 manifest；restage 先使旧 manifest 失效，再发一条携带 revision 的 verifier IME。
- [x] 扩展 `verdict`：CEO 必须 `--revision`；增加 `--reason-file`，并验证 FAIL 首个非空行为 `RESHAPE:` 或 `DROP:`。
- [x] 旧 review request 或混合、被篡改的 staged 文件不能给新版候选 verdict。

## 4. 实现一致生效、归档与恢复

- [x] 增加 `objective.active.json`，只保存动态 path、summary、revision 和 hashes，不复制完整商业正文。
- [x] `PASS` 前预检并快照旧 short/metadata/history、旧 full leaf 和目标 leaf；目标已存在且不归当前 objective 所有时拒绝覆盖；旧版本被绕过流程篡改时也拒绝切换。
- [x] 写 prepared journal；在 company root lock 内写 full、必要时删除旧 owned leaf，再原子写 short/active/history。
- [x] 将 journal 标记 committed 后消费 staged；`RESHAPE` 保留草稿但用独立标记永久关闭旧 revision，`DROP` 消费 staged；verdict review text 进入 proposer inbox。
- [x] 任一普通异常立即回滚；`show/propose/verdict` 和 agent wake 在读取 objective 前处理遗留 journal。
- [x] `objective.history.md` 归档旧短摘要与可获得的旧完整版本；company leaf 不累积历史。
- [x] 更新 `orchestration/agent_loop.py`：active metadata 存在时校验 short/full/summary；不一致则告警且不注入，legacy 无 metadata 路径保持原样。

## 5. 合并判断 Skill，不造新模板

- [x] 重写 `agents/assets/skills/set-objective/SKILL.md`：精确触发边界、跨 business form、具体用户代入、替代/频率/行为/采用/触达/证伪、bundle 命令和重新评审语义。
- [x] 重写 `agents/assets/skills/review-objective/SKILL.md`：CEO 严格价值分支 + 非 CEO 既有结构分支；承重证据独立核查；禁止相关项跳过、可逆轻审和裸 verdict。
- [x] 更新 `agents/assets/skills/find-opportunity/SKILL.md` 及其 active references，把候选交给 `set-objective`，保持“只生成、不自审”。
- [x] 更新 `agents/assets/ceo-charter.md`：普通 Goal 推进当前 objective，不经过方向重审；改变 objective 才调用 `set-objective`。
- [x] 更新 `agents/assets/verifier-charter.md`：禁止手工改 state，但允许 verifier-only verdict 通过受控机制生效；公开质量标准不再被误写为秘密考题。
- [x] 更新 `agents/ceo.yaml` 和 `agent/tests/test_resident_loadout.py`，移除 `decide-direction`，继续隔离 `review-objective` 和裁决权限。
- [x] 确认来源审计已保存旧文件信息、when-idle 三处入口已迁移后，删除 `agents/assets/skills/decide-direction/` 的被跟踪文件；全局来源剥离任务保持独立。

## 6. 更新现行合同与文档

- [x] 更新 `.trellis/spec/backend/resident-agent-contracts.md`：CEO v2 bundle、动态 company leaf、revision、active metadata、PASS/FAIL reason 和 legacy 兼容。
- [x] 更新 `.trellis/spec/backend/role-lifecycle-contracts.md`：删除 `decide-direction` advisory exemption，保留单一 verifier seat。
- [x] 更新 `.trellis/spec/backend/agent-execution-contracts.md` 中已失效的 degraded-mode 示例。
- [x] 更新 `.trellis/spec/backend/company-state-contracts.md`：受控内部存储/删除与导航不变量。
- [x] 更新 `docs/overview.md` 的现行 CEO 判断链和 objective 存储说明；历史 journey/archive 保持历史事实。

## 7. 静态、单元与集成验证

- [x] 定向 objective/company/agent-loop/Skill/loadout 回归：144 项通过。
- [x] 完整执行 `agent/tests + orchestration/tests + company_state_kit/tests`：620 项通过；10 项为本次改动前已存在的 Codex/Claude loadout 落点与 provider 断言失败，没有新增失败。
- [x] `git diff --check` 通过，Python compileall 通过；仓库没有配置独立 linter/type checker。
- [x] 对 active runtime/docs 做 `rg`：旧名称只剩测试中的负断言；when-idle 的运行时引用已由独立任务清零。
- [x] 四个相关 Skill 通过 `quick_validate.py`；静态合同测试锁住无第三 verdict、无相关项轻审、无固定 company taxonomy 和无统一样本模板。

## 8. 隔离 company 的真实行为 e2e

- [x] 重放 `secondtest` 原始通用 MCP 扫描候选，保存完整 proposal、verifier 实际打开的来源和 `FAIL: RESHAPE` 结果到本任务 `research/live-e2e/`。
- [x] 重放一次性人工 MCP 配置审计服务，verifier 明确认定无需构建软件，并按样本、试审、委托、付款与首批用户可达性给出 `FAIL: RESHAPE`，没有套用软件下载或统一复购标准。
- [x] 用隔离文件系统集成测试跑通 `PASS → 动态 full leaf → 短摘要指针 → 下一 wake 注入`，并覆盖篡改后的 fail-closed。
- [x] 人工检查并真实重放 `secondtest` 校准条款和 prompt 合同：内部 demo、风险清单、竞品存在及自有安装均不能承载 PASS。

## 风险点与回滚

- `orchestration/objective.py` 与 company-state 跨挂载一致性是最高风险；所有持久化步骤必须可注入失败，journal 恢复测试不过不得发布。
- 不能在 `when-idle` 仍指向旧 Skill 时删除目录；发布序列检查是硬门。
- 不批量改 archive 里的历史表述；静态清零只针对 active runtime 和现行 docs/spec。
- 回滚后旧 agent loop 仍可注入 v2 生成的短 `objective.md`；额外 metadata/full leaf 被旧代码忽略，因此无需破坏性迁移。
