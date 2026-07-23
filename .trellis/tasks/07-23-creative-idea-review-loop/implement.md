# Creative 创意工作流实施计划

## 0. 执行规则

- 本任务是直接实施任务，不再拆成父任务；按四个可独立验证的切片完成一个 Draft PR。
- 在 Percy 明确批准本设计前，不执行 `task.py start`，不写产品代码。
- 开始实施后先使用 `trellis-before-dev` 读取当前规范。
- 所有共享层修改先证明 Useful 行为不变，再接入 Creative 使用方。
- 不提交工作区中与本任务无关的 Trellis upgrade、onboarding 或队友改动。
- 每个切片结束都同步并检查 `origin/main`；如果同一文件有上游改动，先停下来比较语义，不盲目覆盖。
- 默认测试全部离线；在线 Codex/联网 benchmark 只在 Percy 提供题目并显式要求后运行。

### 0.1 当前实施快照（2026-07-23）

以下快照记录实际完成度；下方原子清单继续作为验收合同，不用机械勾选掩盖
尚未执行的门禁。

- 已完成并分段提交：route-aware Harness、Creative C0–C5（含 Idea Memory）、
  C6 人工策展、C7 确定性报告与可重放 finalization、离线 benchmark 合同。
- 已接通 CLI：`run --route creative`、`status`、`review`、`resume` 与
  plan-only `benchmark`；Useful 默认行为和输出仍有回归测试。
- 已把“空 C6 batch”接到 C7：没有可评审 Concept 时不进入人工等待，但
  Candidate Fate Ledger、稳定淘汰原因、Zero-Idea Explanation 与 Memory
  Record 仍然生成，供后续 Agent 检索“启发”和“应避免模式”。
- benchmark 当前只完成严格 manifest、共享 Memory Snapshot、盲化 A/B、
  worksheet 与离线 evaluator 合同；没有实现在线 arm execution controller，
  CLI 会明确拒绝伪装成已执行或已恢复。
- 已于 `8c80b6e` 合入 Weston 最新 `origin/main@1aaf61a`：保留 Useful
  Gateway v3、Generator v5、Red Team v4 与 BuildFactory Lead wake gate；
  route-aware `PromptCatalog` 增加显式历史版本 allowlist，旧冻结 Prompt 不会被
  新版本字节或标签替换。
- 最终离线门禁：ruff、mypy、compileall、Node UI syntax、CLI help smoke、
  wheel build/resource inspection 全部通过；主项目 `253` tests passed、
  `8` tests skipped、`0` failed。8 个 skip 仅为当前沙箱明确拒绝 loopback
  socket 的真实 HTTP/lifecycle 测试，普通开发机/CI 仍会执行它们。
- Draft PR 已创建。首次真实 Creative smoke run 在 C2 暴露了隐藏后置条件：
  validator 要求 Atom 正文包含模型从未收到的 Controller Territory ID。当前
  修复把谱系收回结构化 metadata/source refs，并让 C3 读取显式
  Atom→Territory index；自然语言 fixture、tamper 回归与全量门禁均已通过。
- 待完成：修复后的真实 Creative smoke run、浏览器/LAN QA 与在线双臂
  benchmark；不能用 mock、离线 evaluator 或 plan-only CLI 结果替代。
- 工作区存在与本任务无关的 Trellis 升级/onboarding 改动；提交必须使用精确
  文件列表，不能把这些文件一起 stage。

## 1. Preflight 与基线

- [ ] 检查当前分支为 `codex/creative-review-loop`，base 为最新 `origin/main`。
- [ ] 用 `git status --short` 建立“本任务文件 / 现有用户文件”边界。
- [ ] 再次读取：
  - `.trellis/spec/backend/agent-workflow-contracts.md`
  - `.trellis/spec/guides/cross-layer-thinking-guide.md`
  - `.trellis/spec/guides/code-reuse-thinking-guide.md`
- [ ] 运行现有 Useful 基线质量门并保存结果。
- [ ] 更新 `task.json` 为 implementation 状态，只在 Trellis final-review 获得 Percy 批准后执行。

## 2. 切片一：Route-aware Harness，保持 Useful 等价

### 2.1 Run schema 与 route contract

- [ ] 在 `src/hacksome/hub.py` 增加 v1/v2 读取：
  - v1 投影为 `route.id=useful`；
  - v1 projection 严格只读，不创建 lock、不写回、不要求 v2 字段；
  - 新 run 写 v2 与显式 route metadata；
  - v2 正式登记 Challenge/Creative Brief/Idea Memory Snapshot 的 path/hash/source/mode；
  - 新增 `result_artifact_ids` 和 Creative `waiting` 状态；
  - 新增 immutable 首因 `terminal_error` 与 append-only `secondary_errors`；
  - 新增单调 `transition_seq`，避免 repair/resume 重复 status event ID 冲突；
  - 新增受限 `pending_records` outbox，用原 timestamp/content reconcile event/decision/resolution；
  - artifact 实现完整 id/path/hash 幂等矩阵、record-without-file fail closed、publish event reconcile 和 orphan 检测；
  - 保留 Useful `idea_card_ids` 和当前 inspect 字段。
- [ ] 增加唯一的 persisted-config serializer/decoder：
  - JSON list 恢复为 `CodexConfig` 要求的 tuple；
  - Creative settings 由同一入口验证；
  - 未知字段、缺失安全字段或 hash 漂移 fail closed。
- [ ] 新增 `src/hacksome/routes.py`：
  - `RunContract` protocol；
  - `useful` / `creative` route registry；
  - 未知 route 与未支持 schema 的明确错误。
- [ ] 把 core validation 与 route validation 分开：
  - core 检查 input/task/artifact/hash/event；
  - core 检查 transition sequence、pending outbox、缺失 event 和未登记 orphan；
  - Useful contract 检查 Idea Cards 与 pass/reject ledger；
  - Creative contract 在后续切片补全。
- [ ] 扩展 decision append 接口，同时保留 `RunHub.record_decision()` 作为 Useful wrapper。

### 2.2 Prompt 与 task executor

- [ ] 在 `src/hacksome/prompting.py` 公开 `PromptSpec` 与 `PromptCatalog`。
- [ ] 把现有 Useful `_SPECS` 迁移为 `useful_prompt_catalog`，不改变模板 ID/version/schema。
- [ ] v2 run 创建时把整条 route（含条件式 C5M 和尚未执行的 C6C）Prompt/Schema 复制到 `RUN_DIR/resources/`，生成 template ID/version/hash + schema hash + web policy manifest；所有 task 从 frozen copy 加载。
- [ ] resume 前验证 resource manifest、冻结文件和受支持 contract version；package 资源更新不改变 frozen Prompt，冻结副本被篡改或代码不再支持该版本时 fail closed。
- [ ] 新增 `src/hacksome/task_executor.py`，抽取：
  - render；
  - begin_task；
  - CodexTask；
  - result/failure；
  - semantic validation。
- [ ] Task record 增加默认 `fatal` 的 `failure_policy`；只允许 Creative C5M Recall/Remix 使用 route allowlist 的 `optional_branch`，Useful 与其他 stage 保持 fatal。
- [ ] 让 `UsefulIdeaWorkflow` 组合 `AgentTaskExecutor`，删除重复 `_call()` 实现。
- [ ] 对相同 fake runner 输入比较迁移前后：
  - task/request/prompt metadata；
  - stage 顺序；
  - decision；
  - Idea Card；
  - inspect/validate。

### 2.3 CLI 与跨进程 lease

- [ ] 在 `src/hacksome/state.py` 增加受限的 `run.lock` advisory lease。
- [ ] 增加独立 `review-server.lock`；`run.lock` 只围绕单次 shared snapshot 或 exclusive mutation，不能让长期 server 阻塞 `status`。
- [ ] 在 `src/hacksome/cli.py` 增加 `--route`，默认 `useful`。
- [ ] route-specific option 使用 `argparse.SUPPRESS`，dispatch 后才注入 route 默认；显式传入另一 route option 报错。
- [ ] `status/validate` 按 persisted route dispatch。
- [ ] 增加 `reconcile RUN_DIR`：只 flush allowlisted outbox，不调用模型/改变业务状态；支持 terminal failed/completed run。
- [ ] 保留 `render_prompt/schema_path/stages`、`inspect_run/validate_run` 和 `RunHub.create()` 的既有签名/Useful 默认。
- [ ] 此切片暂不开放 Creative `run`，未完成 route 返回清晰的“尚未实现”错误。

### 2.4 切片一测试门

- [ ] `tests/test_hub.py`：v1 read-only/no lock write、v2 write、terminal error 首因、config JSON round-trip、transition outbox 各崩溃点/terminal reconcile、artifact 全幂等/冲突/missing-file/adopt/orphan/event reconcile、unknown route、route projection。
- [ ] `tests/test_prompting.py`：两个 catalog、resource freeze/manifest、等待期间 package resource 更新仍用 frozen bytes、frozen tamper/unsupported version fail closed、exact prompt hash、未知 stage。
- [ ] `tests/test_task_executor.py`：success、infra failure、semantic invalidation、cancel、failure-policy 默认值/allowlist/序列化。
- [ ] `tests/test_routes.py`：inspect/validate dispatch。
- [ ] `tests/test_cli.py`：迁移前 Useful run/status human + JSON golden 字节/字段不变、默认/显式 Useful 等价、跨 route 显式参数拒绝、terminal reconcile。
- [ ] 运行完整 Useful 质量门。
- [ ] 形成 commit 1：`refactor: add route-aware idea workflow harness`。
- [ ] 推送分支并创建 Draft PR，让 Weston 可以尽早审共享契约。

## 3. 切片二：Creative C0-C5 生成、筛选、Idea Memory 与研究

### 3.1 Creative contracts 与资源

- [ ] 新建 `src/hacksome/creative/` package：
  - `contracts.py`
  - `artifacts.py`
  - `memory.py`
  - `prompting.py`
  - `workflow.py`
- [ ] 实现 `CreativeWorkflowSettings` 的默认值、类型检查与硬上界，包括 memory runs/entries/bytes/cues/remixers/challengers。
- [ ] 定义 C0-C5 stage constants、稳定 ID 和 revision metadata。
- [ ] 定义 `ConceptDisposition`、stable reason-code enum、跨 run 复合 ref 和四种合法 `zero_reason_code`。
- [ ] 定义并验证三个互不借用的 revision budget：C4 repair ≤1、C6A evidence revision =1、C6C feedback revision ≤1；每个 revision 记录固定 reason，幂等重试不得新建版本。
- [ ] 为下列任务添加 versioned Prompt：
  - C0 Challenge Parse
  - C1 Brief Normalize
  - C2 Territory Explore
  - C3 Concept Synthesize
  - C4 Cheap Hook Review
  - C4 Repair
  - C5M Memory Recall
  - C5M Memory Remix
  - C5W Novelty Scan
  - C6 Evidence Revise
  - C6 Portfolio Curate
  - C6 Feedback Revise
- [ ] 为每种 envelope 添加 JSON Schema，并加入 package data。
- [ ] 实现所有 Markdown H2、数量上限、URL、revision 和 parent ref 语义验证。

### 3.2 C0-C3

- [ ] 实现 Creative settings builder 与参数验证，但本切片不把 `--route creative` 注册为可执行 CLI。
- [ ] 未提供 Brief 时，把默认简报写入 `input/creative-brief-input.md`。
- [ ] 无论 default/literal/file，均把 Brief input 的 path/hash/source 写入 v2 `inputs`。
- [ ] 在创建 Creative run 目录前构造 Idea Memory Snapshot：
  - `auto` 只扫描显式 runs root 的直接子目录，排序后应用 run/entry/byte 上限；
  - `off`、无历史与有 diagnostics 的空 snapshot 都写入 controller-owned `state/creative-memory/idea-memory-snapshot.json`，不把它伪装成早期 Agent 的 stage input；
  - 只接受 completed、validated、supported、non-fixture Creative memory record；
  - 复制 capsule 与复合 ref/hash，后续不再读取 source run；
  - Useful、failed/waiting/partial、未知版本、hash mismatch、symlink/路径逃逸全部排除并记录原因。
- [ ] C0 分别发布 Challenge Brief 和 Constraint View。
- [ ] C1 规范化 Brief，不暂停。
- [ ] C2 用六个独立 Session 探索固定 lens；每个最多三个 Atom。
- [ ] C2 Atom 的 `Territory` 保持自然语言；内部 Territory/Atom ID 只由
  Controller 分配，并用 source refs + metadata 绑定，不要求模型回显 ID。
- [ ] C3 用四个独立 Session 综合；每个最多三个 Concept。
- [ ] C3 的 Atom index 由 Controller 显式写出每个 Atom→Territory ref；
  route validator 校验 Atom ID、metadata slot/ref、source refs 与实际
  Territory artifact 一致，测试 fixture 不得从 task ID 偷塞隐藏前提。
- [ ] Base Concept envelope 必须提供 `primary_territory_ref`，且属于 Parent Atoms 的 Territory；发布后任何 curator 不得改写。
- [ ] 断言 C2/C3 和初始 C4 的 parent refs、registered context、stage input 与 Prompt 均不含 Idea Memory Snapshot、历史 disposition 或外部先例，并在 task policy 中禁止主动扫描 run 历史。
- [ ] Controller 在 fanout 前分配稳定 ID，并按 ID 聚合。
- [ ] 合法空 Concept 集可以继续。

### 3.3 C4

- [ ] 每个 Concept 启动两个 fresh reviewer。
- [ ] 实现六个稳定维度原因码和完整 review aggregation matrix。
- [ ] `repairable` 最多生成一个新 revision。
- [ ] C4R 与 C6A Prompt 明示并机械验证三个不可变 section：
  `Intended Reaction`、`Real Input, Transformation and Output`、
  `Parent Atoms`；不得只在 validator 中保留隐藏后置条件。
- [ ] C4 repair 保留 source 的 `primary_territory_ref`。
- [ ] repaired revision 再接受两个 fresh reviewer。
- [ ] 双 invalid 以 `c4_double_invalid`、修复后非双 pass 以 `c4_unresolved_after_repair` 淘汰，并保留维度原因码。
- [ ] task 失败/缺失使 run failed，不写 candidate reject。
- [ ] 每次 route decision 写 subject/reason-codes/evidence/task refs；每个 revision 发布 pass/repair/eliminated `ConceptDisposition`，Hook repair 成功发布后以 `superseded_by_hook_repair` + `target_ref` 闭合旧 revision。

### 3.4 C5M Idea Memory

- [ ] 实现 `src/hacksome/creative/memory.py`：
  - memory record/snapshot/capsule/`MemoryStageSummary` Schema 与 semantic validation；
  - direct-child discovery、稳定排序、hard limits、diagnostics；
  - composite cross-run refs 与独立 capsule hash；
  - snapshot 自包含 copy/hash；
  - exact section extraction 与隐私字段拒绝。
- [ ] Snapshot 非空且存在当前 Atom 时启动至多一个 Recall，输出至多八条 `inspire|avoid` cue；否则发布明确 empty/disabled 状态且不调用 Agent。
- [ ] Recall 只读取 C0/C1、Atom index、base Hook/disposition index 和 capsule；历史文本作为不可信数据，不能改变规则。
- [ ] 最多两个 Remix Session 各生成一个 `creative-concept-mNN-r001`：
  - 至少一个 current Atom + 一个 memory cue；
  - `primary_territory_ref` 属于 current Atom sources；
  - 完整跨 run provenance；
  - `Past Inspiration Used / What Was Transformed / Why This Is Not A Copy`；
  - normalized Hook 相同、直接 mechanism+reveal 复制、snapshot 外 ref 均拒绝。
- [ ] Challenger 使用普通 C4 Prompt/Schema、双 reviewer 与一次 repair budget；它不再触发 Recall/Remix。
- [ ] `auto` 下 Recall/Remix task 失败写一一对应的 `optional_memory_stage_failed` event/diagnostic，base 分支继续且不伪装成无历史。
- [ ] Recall 失败时不启动 Remix；两个 Remix 使用 all-settled，一成一败时保留已验证 challenger 并只跳过失败 sibling。
- [ ] 所有 C5M 路径都由 Controller 恰好发布一个 `MemoryStageSummary`，分别记录 Recall 与每个 Remix slot 的 succeeded/failed/invalidated/not-started、task/challenger/diagnostic refs；部分成功的总状态仍是 `optional_failed`。
- [ ] Completed-run validator 仅容忍带 `failure_policy=optional_branch`、C5M allowlist stage 和匹配 diagnostic 的 failed/invalidated task；任何其他 failed task 都是 fatal。

### 3.5 C5W Novelty Scan

- [ ] 只有 base/challenger 的 C4 pass Concept 进入 Novelty Scan。
- [ ] 只有 C5W task 设置 `web_search=True`。
- [ ] 验证 source URL、relation 枚举和必需 section。
- [ ] 网络/任务失败使 run failed，绝不生成“未发现先例”的空结论。
- [ ] Scan 只作为证据，不直接 gate Concept；memory challenger 不豁免外部查重。
- [ ] 本切片只通过 stage-level/fake-runner 内部测试验证 C0-C5；不创建对用户承诺可继续的持久化半成品 run，不产生未定义终态。

### 3.6 切片二测试门

- [ ] 单测六个默认 lens 和所有 settings 上界。
- [ ] 单测 C0/C1 exact context allowlist。
- [ ] 用乱序完成的 fake runner 验证稳定 ID/报告输入顺序。
- [ ] 覆盖 C4 所有 decision 组合、reason codes、disposition closure 和修复上限。
- [ ] 覆盖 memory off/无历史/zero-Idea source/坏来源 diagnostics/source 删除篡改/snapshot 篡改/稳定 cap 顺序。
- [ ] 覆盖 Recall/Remix 上限、无 current Atom、无 relevant cue、copy reject、复合 ref、optional failure 和禁止递归。
- [ ] 覆盖 Recall 失败、Remix 0/1/2 成功、两个 sibling 一成一败，以及错误 stage 冒充 optional 的拒绝。
- [ ] 断言 C0-C4/C5M 没有 web，C5W 才有。
- [ ] 覆盖空 Atom、空 base Concept、base 全部 C4 reject、challenger 全 reject、C5W 失败。
- [ ] 完整 Useful + Creative 离线测试。
- [ ] 形成 commit 2：`feat: add creative generation memory and novelty pipeline`。
- [ ] 更新 Draft PR 的架构说明和测试证据。

## 4. 切片三：C6 修订、自动策展与团队评审

### 4.1 C6A/C6B

- [ ] 接线并语义验证切片二已经冻结版本的 evidence-revise 与 portfolio-curate Prompt/Schema。
- [ ] 每个 C4 pass Concept 生成一个 evidence-informed revision，输入包含 Hook、Novelty、相关 Memory cues（无相关 cue 时显式空集合）和 C0/C1。
- [ ] 验证该 revision 只消费 C6A budget；即使 source 已做过 C4 repair，也不得混淆或重置其 lineage budget。
- [ ] C6A evidence revision 保留 source `primary_territory_ref`。
- [ ] C6A 新 revision 验证并发布后，以 `superseded_by_evidence_revision` + `target_ref` 终结 source revision；任务失败不得伪造成功转移。
- [ ] 两个独立 curator 输出 include/hold/exclude，不输出分数、排序或 primary territory；Controller 只使用 Concept metadata 中已验证的 `primary_territory_ref`。
- [ ] Controller 实现分层批准票 + Territory round-robin。
- [ ] shortlist 最大 8 个；入选项发布非终态 `shortlisted` disposition，所有未入选项发布终态 `not_shortlisted` disposition，区分 curator 证据不足与 portfolio/territory 容量原因。
- [ ] 没有 Hook-pass 或 shortlist 为空时发布 `status=skipped_empty`、`concept_refs=[]`、带合法 `skip_reason` 的空 batch，不写 wait、不启动 server，直接进入 C7。
- [ ] shortlist 非空时发布 immutable review batch，写 `wait` 并以正常 `waiting` 返回。
- [ ] `CreativeIdeaWorkflow.execute()` 返回 typed waiting/completed outcome；waiting CLI 退出 0 并打印下一条 review 命令。
- [ ] 实现 `CreativeRunContract.inspect/validate` 投影：base/memory Concept counts、memory mode/snapshot/status、disposition/zero reason、round/hash、coverage、resumable 与非法 fixture。

### 4.2 Review domain 与 ledger

- [ ] 新建 `src/hacksome/creative/review.py`：
  - snapshot DTO；
  - HumanReview schema/domain validation；
  - HumanResolution validation；
  - hash/round/revision binding；
  - append-only 与 supersedes。
- [ ] 初始化 `human-reviews.jsonl` 与 `human-resolutions.jsonl`。
- [ ] reviewer name 与 reviewer ID 分离。
- [ ] review/resolution 以规范化 client `request_sha256` 重试幂等，复用原 server timestamp；冲突 ID、过期 hash 和未知 ref 拒绝。
- [ ] supersedes 只能指向同 reviewer/round 的 latest record；首份记录标记 pre-reveal，看到 team wall 后的 edit 标记 post-reveal。
- [ ] 生成最多 8 个 canonical adjacent pair；按 reviewer ID 只交换显示顺序，提交验证 pair ID/两端 hash。
- [ ] round 关闭后拒绝所有新 review/supersede，只使用 latest non-superseded receipt。
- [ ] 默认 coverage gate + Percy 显式 override reason。
- [ ] 为 concept/pair/overall feedback 生成稳定 fragment ref/hash；Resolution 验证每个 shortlist ref 恰好一个 action、merge group 互斥、approved fragment 相关且来自 latest receipt。
- [ ] 每个 revise/merge 至少一个 approved fragment 或 hash 绑定的 curator instruction。
- [ ] 保存 resolution hash、latest receipt set hash 与 approved fragment hash；wait close + resolution ledger 通过 outbox reconcile。

### 4.3 HTTP server

- [ ] 新建 `src/hacksome/creative/review_server.py`，只使用标准库。
- [ ] 实现固定 HTML/assets/API 路由。
- [ ] 实现 `/join/<token>` → HttpOnly cookie → 无 token URL，并关闭/脱敏 access log。
- [ ] 默认 loopback/随机端口；非 loopback 强制 `--public-host`，用它生成 URL/Host allowlist 并打印警告。
- [ ] review/curator link 分离但只使用一个 role capability cookie；另设 reviewer-session cookie，避免共享 team token 泄露提交状态。
- [ ] 实现 `/api/reviewer-sessions`，local reviewer ID 与 session/capability 绑定，payload ID 必须匹配。
- [ ] 校验 Host、Origin、Content-Type、body size、method，并设置 CSP/no-store/no-referrer/nosniff。
- [ ] 实现字段上限和每个 C6C task 的 12 fragments / 24 KiB feedback budget，超限不静默截断。
- [ ] 不开放 CORS，不暴露 run 目录。
- [ ] `/api/snapshot` 按 cookie/首次提交状态返回：pre-submit reviewer 无 peer/历史来源，post-submit reviewer 只读 team wall 但 round 关闭前仍不展示 memory provenance，curator 包含完整 raw receipts + memory provenance/copy-risk + coverage + merge/close 数据。
- [ ] Server 生命周期持有 `review-server.lock`；每个 snapshot/mutation 使用短生命周期 shared/exclusive `run.lock`；关闭 round 后自动退出。

### 4.4 HTML/CSS/JS

- [ ] 新建 `src/hacksome/review_ui/index.html`、`styles.css`、`app.js`。
- [ ] 实现三栏 Desktop 和单列 Mobile。
- [ ] 实现 Concept detail、反应 chips、自由评论、一句话复述、分享对象。
- [ ] 实现可跳过的 pairwise compare。
- [ ] 提交前隐藏 peer feedback。
- [ ] 实现 Percy 策展台：
  - coverage matrix；
  - reviewer 原始 receipt；
  - memory 来源、借用/规避内容与 copy-risk；
  - 每个候选 action；
  - approved feedback fragment checkboxes + curator instruction；
  - 互斥 merge groups；
  - coverage override reason；
  - 关闭前确认与关闭后 resume 提示。
- [ ] 用 `textContent` 渲染所有 run/user 文本。
- [ ] `localStorage` 保存 reviewer profile 与未提交草稿；hash 变化时阻止静默提交。
- [ ] 实现“传递回执”成功状态、明确 error/closed/stale/empty 状态。
- [ ] 键盘、focus、44px touch target、reduced motion。
- [ ] 更新 package data 并测试 wheel/resource 可读。

### 4.5 Resolution 与 resume

- [ ] 实现 `review` / `resume` command handler，但先通过模块级测试，不在本切片对用户公开 Creative route 命令。
- [ ] Percy resolution 支持 keep/revise/reject/taste_veto/merge。
- [ ] 关闭轮次只保存 immutable resolution、latest receipt-set hash 与 closed wait，不提前发布 terminal disposition。
- [ ] `resume` 中为每个 shortlist source 发布且只发布一个 `promoted_to_final|revised_into|human_reject|human_taste_veto|merged_into` terminal disposition；keep/revise/merge 必须先发布合法 Final Idea 再写 `target_ref`，reject/taste-veto 也在 resume 闭合。
- [ ] C6C task/验证失败时不得预写成功 disposition；尚未处理的 source 保持非终态并由 failed partial + terminal error 解释。
- [ ] 只把 resolution 明确批准且 hash 复核通过的 feedback fragments/curator instruction 注入 Prompt。
- [ ] `keep` 由控制器提升精确 revision；每个 `revise/merge` 结果最多一个 feedback revision。
- [ ] keep/revise 保留 source `primary_territory_ref`；merge 只能从 source primary refs 中选择一个写入 Final Idea metadata。
- [ ] C6C 只能消费尚未使用的 feedback budget；重复 resume、重放 outbox 或 server 重启不得增加 revision。
- [ ] 重复 resume 不产生额外任务或 revision。
- [ ] Completed-run validation 证明每个 Concept revision 恰好一个 terminal disposition；failed partial 允许未闭合 revision，但必须保留 terminal error，且所有后继 `target_ref` 存在、类型正确。

### 4.6 切片三测试与浏览器门

- [ ] Review store：Unicode、request-hash 幂等/原 timestamp、冲突、supersedes latest-only、pre/post-reveal、stale hash。
- [ ] HTTP：固定路由、reviewer-session 隔离、role-aware snapshot、public-host/Host、auth、Origin、security headers、body/field/context budget、非法 JSON、traversal。
- [ ] Resolution：exactly-once action、coverage、override、fragment 粒度/hash、revise/merge feedback requirement、receipt-set hash、互斥 merge、taste veto、全拒绝、outbox crash/reconcile。
- [ ] Pairwise：0/1/2/N 生成、上限、左右交换、未知/重复/stale pair。
- [ ] Workflow：empty batch、waiting、open round、closed round、resume-once。
- [ ] Resolution timing：close 只冻结 resolution；resume 先发布 Final target 再写 disposition；C6C 失败不留下悬空 target 或伪成功终态。
- [ ] Empty batch：`no_concepts_generated|all_candidates_failed_hook|shortlist_empty` 均不写 wait/server，且不丢 disposition。
- [ ] Role projection：普通 reviewer 在 round 关闭前看不到 memory provenance；curator 能检查来源与 copy-risk。
- [ ] Revision budget：base 与 memory challenger 的 0/1 次 C4 repair × 固定 1 次 C6A × 0/1 次 C6C 组合均保持正确 lineage，任何额外调用 fail closed。
- [ ] 浏览器 QA：
  - Desktop；
  - Mobile；
  - 键盘；
  - 草稿恢复；
  - reviewer 首次提交前无法读取 peer feedback，提交后只读 team wall；
  - curator coverage/merge/approve/override/close 全流程；
  - 成功/错误/关闭/过期；
  - reduced motion。
- [ ] 完整 Useful + Creative 离线测试。
- [ ] 形成 commit 3：`feat: add bounded human curation relay`。
- [ ] 在 Draft PR 添加截图或短录屏与本地启动说明。

## 5. 切片四：C7 报告、Handoff、Benchmark 与文档

### 5.1 Deterministic report

- [ ] 新建 `src/hacksome/creative/report.py`。
- [ ] 从 Hub、decision ledger、human ledgers 读取已验证数据。
- [ ] 按稳定 ID 渲染完整历史和零个或多个 Idea Card，并固定生成 Candidate Fate Ledger、Idea Memory Used、Memory-derived Branches；零 Idea 增加逐项原因/证据的 Zero-Idea Explanation。
- [ ] 实现 Final Creative Idea Card 的 12 个必需 H2、Human Signal 代理声明和 controller-owned Lineage。
- [ ] 生成 Markdown 与 machine-readable JSON。
- [ ] 定义/验证 completed、四种 zero reason 和 failed partial JSON 的完整顶层字段；每个 Concept 输出 origin、memory refs、terminal outcome 与 disposition refs/reasons/evidence。
- [ ] 确定性生成 `creative-memory-record.json`：
  - 每个 Final Idea 生成一个 positive entry；除直接 `promoted_to_final` 的重复 source 外，每个 terminal Concept 生成 concept entry，Hook/evidence/human revise/merge source 保留 transformed 经验；
  - entry 区分 `source_kind=concept_revision|final_idea`，验证 source candidate/hash/concept lineage/primary territory；
  - controller 分类 `positive|portfolio_only|caution|subjective|transformed`，并逐项覆盖 superseded/revised/merged successor outcome；
  - 两个 capacity reason → `portfolio_only`，两个 curator-support reason → `caution`，逐项测试且不临时推断；
  - 只做已验证 section 的定长精确抽取；C4 caution 可复制与 reason code 绑定的有界机器 review evidence；
  - human reject/taste veto 不复制人类理由正文，只保留 subjective outcome/code/ref；
  - 排除身份、原始人类评论、curator instruction 正文、Prompt/log/Session/绝对路径；
  - fixture record 标记 producer，后续 discovery 排除。
- [ ] 在第一个 Final artifact 发布前实现 `state/creative-finalization/` 两段式 plan：
  - 锁定并 hash canonical pre-finalization source manifest；
  - 预分配 artifact/event/completed-transition ID 与时间；
  - 先精确渲染 report/cards/handoffs，再用 staged report hash 渲染 memory record；
  - 把所有 bytes/hash/path/type/size/publish order 写入 staging，全部复核后才原子发布 immutable manifest。
- [ ] `resume` 识别 `status=running/current_stage=creative-finalization`，复核 source ledger heads 和 staged/existing bytes，只按 manifest 幂等 publish/adopt；不得重新 render、调用模型、改变 ID/hash/时间。
- [ ] 固定逻辑发布顺序：report/cards/handoffs → memory record → completed；只有全部 artifact records、文件和 outbox events 闭合后写 completed/result IDs。
- [ ] manifest 前 fatal error handler 尝试 deterministic partial report；manifest 后普通 publish interruption保持 resumable，不伪装成 failed。staged/existing bytes 篡改 fail closed，plan-linked 文件不得被暴露为有效 card/handoff/memory record；partial render 失败不覆盖首因。
- [ ] 不在 render 时调用模型、网络、随机数或当前时间。
- [ ] 对相同 fixture 连续渲染两次并比较精确字节。
- [ ] C7/空 shortlist/failed partial 全部接通后，才在 CLI 正式开放：
  - `run --route creative`
  - `review`
  - `resume`
  - `benchmark`
  - `--idea-memory auto|off`
  - Creative route-specific options
- [ ] CLI 回归验证：`resume` 对 Useful run fail closed、退出非零且 run 目录所有字节不变；Creative C6 resume 与 C7 finalization replay 互斥分派。
- [ ] Creative 第一次对用户可见时，正常业务路径只能得到 `waiting`、`completed` 或带 partial report 的 `failed`，不存在停在 C5 的公开半成品状态；C7 publish/process 中断可额外返回可恢复的 `finalizing` + resume 命令，empty C6 batch 在无中断时直接 completed 且报告解释原因。

### 5.2 Build handoff

- [ ] 每张最终卡生成纯 JSON handoff：
  - `source_run_id`
  - `idea_card_id`
  - `idea_card_sha256`
  - `challenge_markdown`
  - `initial_idea_card_markdown`
- [ ] 不 import `buildfactory`。
- [ ] 记录 Build Review Gate 仍可选零张卡，未选项不是 Creative reject。

### 5.3 Benchmark

- [ ] 添加两种明确 comparison：
  - `workflow_vs_oneshot`：两边 memory off，隔离工作流本身收益；
  - `memory_ablation`：相同 full-route 的 auto/off，隔离历史积累收益。
- [ ] 每个 case 在启动 arm 前冻结一份 benchmark-level memory snapshot；两个 arm 登记同一 hash，case 内新输出不得回流污染后启动 arm。
- [ ] `hacksome benchmark --route creative MANIFEST.json` 支持：
  - `live`：C6 正常 waiting，正式 review/resume 后用 `--continue BENCH_DIR` 汇总；
  - `fixture`：必须提供 review fixture，并标记 producer/hash，不进入真人指标。
- [ ] 输出 comparison kind、memory policy/snapshot hash、source diagnostics、cue/challenger/copy-reject、token、wall time、任务数、候选数、筛选结果和人工 worksheet。
- [ ] 生成 blind A/B packet、独立 arm-map 和 packet hash；`--continue BENCH_DIR --worksheet PATH` 校验/import 幂等 `benchmark-review.json`。
- [ ] Live 至少一份完整 worksheet 才计算人类指标；fixture 明确省略。
- [ ] 提供离线 evaluator 单测；不把真实在线 run 放进默认测试。
- [ ] Percy 提供真实 Challenge 后再运行并记录实际结果。

### 5.4 README 与操作说明

- [ ] README 解释 Useful/Creative 两条路线与默认 Useful 兼容。
- [ ] 给出 Creative run → waiting → review → resume → report 的完整命令。
- [ ] 解释 `--idea-memory auto|off`、先独立生成后读历史、来源资格、快照冻结、最多两个 challenger 和无全局数据库；明确 v1 保证 Prompt/parent/context 隔离，不把 read-only sandbox 宣称为 chroot。
- [ ] 解释 C7 finalization 中断的 `status`/`resume` 行为，以及恢复只重放 frozen bytes。
- [ ] 解释空 C6 batch 只是跳过无对象的人审；零 Idea 报告与 memory record 仍保留逐项淘汰原因。
- [ ] 解释本地/LAN 安全边界和没有公共账户系统。
- [ ] 解释 Harness、Agent Session、revision、hash binding 和 deterministic report。
- [ ] 标明 Idea 阶段结束点与 Build handoff 边界。
- [ ] 新建 `.trellis/spec/backend/creative-agent-workflow-contracts.md` 并更新 backend index。
- [ ] 将现有 Useful spec 收窄为 Useful route；更新“only Useful / CLI 无 resume”等全局陈述，同时保留 Useful 自身无运行级 resume。

### 5.5 切片四测试门

- [ ] 报告包含所有生成/修复/淘汰/评审/合并/最终项，以及每个 disposition 的稳定原因码和 evidence refs。
- [ ] 四类零 Idea 报告合法且互斥；空 C6 batch 的 skip reason 与 `zero_reason_code` 一致。
- [ ] completed run 的 memory record hash/分类/隐私排除/确定性合法；failed/waiting/fixture 不可被 discovery 消费。
- [ ] finalization crash matrix 覆盖 manifest 前、每个 staged/published artifact 前后、outbox、completed transition；重复 resume 字节/ID/时间不变，缺失或篡改 staged bytes fail closed。
- [ ] Handoff hash 与文件字节一致。
- [ ] route validate 覆盖 completed/waiting/failed 的合法与非法状态。
- [ ] CreativeRunContract 覆盖 revision、disposition、memory snapshot/capsule/composite ref、C4/C5M/C5W gate、round/review/resolution、final report/card/memory/handoff 的完整闭包。
- [ ] Benchmark manifest、comparison kind、shared snapshot/no arm leakage、memory ablation、0/1/N Idea portfolio、blind packet/arm mapping、worksheet hash/import、offline evaluator 和缺失数据行为。
- [ ] 形成 commit 4：`feat: complete creative idea route and deterministic report`。

## 6. Final Quality Gate

- [ ] 同步最新 `origin/main`，检查共享文件 overlap。
- [ ] 运行：

```bash
.venv/bin/ruff check src tests
.venv/bin/mypy src
.venv/bin/python -m compileall -q src tests
.venv/bin/python -m unittest discover -s tests -v
git diff --check
```

- [ ] 运行 Useful CLI smoke test。
- [ ] 运行完全 fake 的 Creative e2e：无历史、memory challenger、零 Idea 与非零 Idea 路径。
- [ ] 浏览器最终 QA 并保存证据。
- [ ] 检查没有在线 benchmark、run 产物、token、cookie 或日志被提交。
- [ ] 检查 package wheel 中包含 Creative Prompt/Schema/UI，包括 C5M Recall/Remix 资源。
- [ ] 使用 `trellis-check` 做 spec/实现漂移复核并修复。

## 7. PR 收口

- [ ] `git diff --stat` 与 `git diff --check`。
- [ ] 只 stage 本任务文件；逐项排除已有 Trellis/onboarding 改动。
- [ ] PR 描述用中文，包含：
  - 为什么需要 Creative 独立 route；
  - Harness 实际抽取了什么、没有抽象什么；
  - C0-C7 状态图；
  - Idea Memory 的先独立生成、来源冻结、challenger 上限和隐私边界；
  - 空 C6 batch 与零 Idea 淘汰原因示例；
  - C6 页面截图和操作步骤；
  - Useful 回归证据；
  - Creative 离线测试证据；
  - 尚未运行的在线 benchmark；
  - 对 Weston/Build handoff 的边界。
- [ ] Push 前再次同步/检查 `origin/main`。
- [ ] 将 Draft PR 标记 ready 前完成 final review。
- [ ] 把 PR URL、commit 和测试结论写回 `task.json`/开发日志。

## 8. Review Gate

- [ ] `prd.md`、`design.md`、`implement.md` 无互相冲突。
- [ ] C1 不引入第二个人工暂停。
- [ ] C6 是唯一 Human-in-the-loop gate。
- [ ] Creative `resume` 没有改变 Useful “无运行级 resume”的合同。
- [ ] Human feedback 不作为可信指令。
- [ ] Shortlist 不使用模型 1–10 总分。
- [ ] 所有循环均有上限。
- [ ] C2/C3/初始 C4 不注入历史上下文且明确禁止主动扫描；C5M 最多两个 challenger，all-settled 保留成功 sibling，且不能递归或绕过 C4/C5W。
- [ ] 所有候选 revision、hash、处置原因码、证据、跨 run 来源和原始反馈可追溯。
- [ ] Memory Record 不含身份、未批准人类原文、Prompt/log/Session，且只从 completed validated Creative run 自动发现。
- [ ] C7 不调用模型、可零输出，并生成可供未来 run 消费的确定性 memory record；多文件发布有 frozen manifest 和可重放崩溃边界。
- [ ] Percy 已明确批准进入实施。
