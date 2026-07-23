# Creative Idea 工作流合同

> Creative route 的规范性后端合同。实现、CLI、离线 validator 与测试必须以
> 本文为准；PRD/design 用于解释产品意图，不能替代这里的可执行约束。

## 1. Scope / Trigger

当修改以下任一部分时必须读取本文：

- `src/hacksome/creative/` 下的 C0–C7 工作流；
- Hub route、wait、human ledger、finalization 或 result artifact；
- `run --route creative`、`review`、Creative `resume` 或 `benchmark`；
- Idea Memory 的发现、冻结、Recall/Remix 或完成后回写；
- Creative report、Idea Card、partial report 或 Build handoff。

Creative 从一道 challenge 开始，在 Idea 阶段结束。它不负责实现产品、创建
Repo、部署或 Pitch。C6 是唯一 Human-in-the-loop gate；C0–C5 不得增加人工
暂停。

```text
C0 Challenge & Constraints
→ C1 Creative Brief
→ C2 Creative Territories
→ C3 Concept Synthesis
→ C4 Cheap Hook Screen
→ C5M Idea Memory / C5W Novelty Scan
→ C6A Evidence Revision / C6B Portfolio / C6C Human Feedback
→ C7 Deterministic Report
```

Useful 与 Creative 共享 `CodexRunner`、`RunHub`、Prompt/Schema freeze、
`AgentTaskExecutor`、原子文件和 route registry。两条路线不共享候选语义、
gate reason 或报告结构。

## 2. Signatures

### Python

```python
CreativeIdeaWorkflow.create(
    challenge: str,
    runs_dir: str | Path,
    *,
    settings: CreativeWorkflowSettings | None = None,
    codex_config: CodexConfig | None = None,
    run_id: str | None = None,
    runner: Runner | None = None,
    creative_brief: str | None = None,
    creative_brief_file: str | Path | None = None,
    memory_snapshot: IdeaMemorySnapshot | None = None,
    run_timeout_seconds: float = 6 * 60 * 60,
) -> CreativeIdeaWorkflow

CreativeIdeaWorkflow.open(
    run_dir: str | Path,
    *,
    runner: Runner | None = None,
    run_timeout_seconds: float = 6 * 60 * 60,
) -> CreativeIdeaWorkflow

await workflow.execute() -> CreativeRunOutcome
await workflow.resume() -> CreativeRunOutcome

build_report_projection(
    run_dir_or_hub,
    *,
    producer_kind: Literal["live", "fixture"] = "live",
    snapshot: Mapping[str, Any] | None = None,
) -> CreativeReportProjection

render_success_report(
    projection: CreativeReportProjection,
) -> RenderedReportBundle

FinalizationCoordinator(hub).finalize(outputs_or_renderer)
FinalizationCoordinator(hub).replay()
```

`CreativeRunOutcome.status` 只能是：

- `waiting`：非空 C6 batch，等待人工评审；
- `finalizing`：C7 manifest 已冻结但尚未完成发布；
- `completed`：所有 C7 artifact 与 completion event 已闭合。

### CLI

```text
hacksome run (CHALLENGE | --prompt TEXT) --route creative
  [--creative-brief TEXT | --creative-brief-file PATH]
  [--idea-memory auto|off]
  [Codex runtime options]

hacksome review RUN_DIR
  [--host HOST] [--public-host HOST] [--port PORT] [--no-open]

hacksome resume RUN_DIR

hacksome benchmark --route creative MANIFEST.json
hacksome benchmark --continue BENCH_DIR [--worksheet PATH]
```

Creative-only 参数必须使用 `argparse.SUPPRESS` 或等价机制，在 route dispatch
后注入默认值。Useful 显式传 Creative 参数、Creative 显式传 Useful fanout
参数，都必须在创建 run 前报错。

## 3. Contracts

### 3.1 Run 与状态

Creative 只能使用 v2 Hub state，并持久化：

- `route.id=creative` 和 contract/prompt/stage/report policy version；
- Challenge、Creative Brief、Idea Memory Snapshot 的 path/hash；
- 完整 settings/Codex config 及其 canonical hash；
- frozen Prompt/Schema resource manifest；
- `wait`、`terminal_error`、`secondary_errors`、`transition_seq`、
  `pending_records`、`result_artifact_ids`；
- 可选 immutable `finalization` pointer。

`open()` 只能从这些 hash-bound 数据恢复 settings、Codex config、Prompt
catalog 与 Memory Snapshot，不能采用当前 package 默认值替换旧 run 的冻结值。
冻结 Prompt 的版本只能是当前版本或代码显式 allowlist 的历史版本；加载后
继续报告 manifest 中的真实版本，未知版本、ID、web policy、路径或 hash 漂移
一律 fail closed。

### 3.2 Agent 隔离与循环上限

- 每个逻辑任务使用 fresh Codex Session；基础设施重试只恢复该任务自己的
  exact Session。
- 只有 C5W Novelty Scan 使用 web search。
- C0–C4、第一批 C3/C4 的 Prompt、parent refs 与 context 不得含 Idea Memory
  或历史 disposition。
- C5M 最多一次 Recall、八个 cue、两个 Remix challenger；challenger 不得递归
  Recall，仍须经过普通 C4/C5W。
- 每个 Concept 的 budget 独立：C4 hook repair ≤1、C6A evidence revision
  恰好 1、C6C feedback revision ≤1。
- C6B 使用 categorical include/hold/exclude 与 controller round-robin；
  不允许模型 1–10 打分、Top-K 排名或 curator 改写 primary territory。

### 3.3 C6 人工评审

非空 shortlist 发布 immutable `creative_human_review_batch`，写：

```json
{
  "kind": "creative_human_review",
  "round_id": "...",
  "round_artifact_id": "...",
  "round_sha256": "...",
  "batch_sha256": "...",
  "status": "open | closed",
  "resolution_id": null
}
```

Review 与 resolution 是 append-only JSONL：

- reviewer ID 与 display name 分离；
- 同 request ID + 同 canonical request hash 幂等返回原 timestamp；
- 同 ID 不同内容冲突；
- supersede 只能指向同 reviewer/round 的 latest receipt；
- round 关闭后禁止新 review；
- resolution 对每个 shortlist revision 恰好给一个
  `keep|revise|reject|taste_veto|merge` action；
- revise/merge 只可注入明确批准且 hash 复核的 fragment 或 curator
  instruction；单任务最多 12 fragments / 24 KiB；
- close 只冻结 resolution 和 wait，不提前伪造 C6C terminal disposition。

普通 reviewer 首次提交前看不到 peer 原文，提交后只获得只读 team wall；
Memory provenance、merge、feedback approval、coverage override 与 close
controls 只属于 curator projection。人类自由文本始终是不可信数据。

### 3.4 Idea Memory

新 run 创建前按直接子目录稳定扫描，只接受：

- `completed`、离线验证通过的 Creative run；
- 受支持的 route/report/memory schema；
- `producer_kind=live`；
- artifact path/hash 与 Memory Record 内所有 source binding 一致。

Snapshot 自包含复制 capsule，受 run/entry/byte 上限约束。Snapshot 创建后不得
再次读取 source run。Memory Record 不得包含 reviewer/curator 身份、原始人工
评论、curator instruction 正文、Prompt、日志、Session ID 或绝对路径。

### 3.5 C7 成功报告

成功输出的逻辑发布顺序固定：

```text
creative-idea-report.md
creative-idea-report.json
0..N Idea Cards
Idea Card index
0..N Build handoffs
creative-memory-record.json
completed transition
```

报告必须包含完整 Candidate Fate Ledger、Idea Memory Used、
Memory-derived Branches；零 Idea 还包含 Zero-Idea Explanation。合法
`zero_reason_code` 只有：

```text
no_concepts_generated
all_candidates_failed_hook
shortlist_empty
all_human_rejected
```

非零 Idea 时必须为 `null`。每个 completed Concept revision 必须恰好一个
terminal disposition；指向 successor 或 Final Idea 的 `target_ref` 必须存在
且类型正确。

Final Idea Card 只有一个 H1，并恰好包含十二个非空 H2：

```text
Intended Reaction
One-sentence Hook
First Thirty Seconds
Audience Action
Core Mechanism
Reveal and Aftertaste
Minimum Hackathon Demo
Why Someone May Share It
Novelty and References
Human Signal
Risks and Unresolved Disagreement
Lineage
```

`Human Signal` 必须声明它只是构想阶段代理信号，不得声称真实传播力。
Build handoff 是纯 JSON，不能 import Build runtime。它的
`challenge_markdown` 与 `initial_idea_card_markdown` 对齐 BuildFactory 的
bootstrap 输入，但发布 handoff 不等于授权启动 Team。Build-side adapter 必须
复核 `idea_card_sha256`，并用至少
`source_run_id + idea_card_id + idea_card_sha256` 构造跨 run 身份；任何一侧
都不能 import 对方的私有 Python 类型。

### 3.6 两阶段 finalization

C7 renderer 不调用模型、网络、随机数或当前时间。Coordinator：

1. 在一致 snapshot 上绑定 state、四条 ledger head 与所有 hash-bound source；
2. 预分配 artifact/event/completion ID 与唯一持久化时间；
3. 写 exact staged bytes；
4. 原子写 canonical manifest；
5. 绑定 run pointer；
6. 按 manifest 顺序 publish/adopt；
7. 最后一次原子状态变更才设置 `completed` 与 `result_artifact_ids`。

manifest 后中断保持 `running + creative-finalization`，`resume` 只能
`replay()`；不得重新 render 或调用 Agent。字节、source 或 ledger prefix
篡改必须 fail closed。

### 3.7 Failed partial

fatal run 保持 `failed`，保存第一条 immutable `terminal_error`，并尽力发布：

```text
creative-partial-report.md
creative-partial-report.json
```

partial 只记录失败前已持久化的 task/artifact/decision/ref，不生成有效
Idea Card、handoff、Memory Record、completion event 或 result IDs。manifest
后发现篡改时允许保留 manifest 与已发布的 exact plan prefix 供审计，但它们
不属于 `result_artifact_ids`，inspect 必须标记为不可恢复失败。

## 4. Validation & Error Matrix

| 条件 | 必需行为 |
| --- | --- |
| Challenge 为空或 Brief 参数冲突 | 创建 run 前报错 |
| Useful 传 Creative option，或反向 | 创建 run 前报错 |
| frozen config/resource/snapshot hash 漂移 | fatal + partial；不调用下一 Agent |
| C5M optional task 失败 | 写匹配 diagnostic；保留成功 sibling；继续 base |
| C5W/其他 fatal task 失败 | run failed + partial，不能伪装“无先例/空候选” |
| base 与 challenger 均无 Hook pass | 空 batch + `all_candidates_failed_hook`，直接 C7 |
| C6B shortlist 为空 | 空 batch + `shortlist_empty`，直接 C7 |
| review hash/round 过期 | HTTP 409；不写 ledger |
| coverage 不足且无显式 override reason | resolution 拒绝 |
| open round 执行 resume | 非零、零业务写入 |
| Useful run 执行 resume | 非零、目录字节不变 |
| closed C6 wait | C6C 一次，然后 C7 |
| frozen C7 plan | 只重放 exact manifest |
| C7 manifest 前 render/stage 失败 | failed + partial |
| manifest 后普通中断 | finalizing，可 resume |
| staged/published/source/ledger 篡改 | failed + partial；result IDs 为空 |
| partial render 失败 | 保留首因，追加 secondary error |

## 5. Good / Base / Bad Cases

- Good：base Concept 先独立生成；C5M 从冻结历史生成一个机制变换 challenger；
  二者用相同 C4/C5W 标准，最终报告披露来源和变化。
- Good：两位 reviewer 独立复述，Percy 只批准一个相关 fragment；C6C Prompt
  不含未批准评论，报告仍完整审计所有 receipt ref。
- Base：没有历史、`--idea-memory off` 或所有 Concept 被淘汰；流程仍确定性
  完成并写零 Idea 报告与可供未来使用的失败经验。
- Base：manifest 发布到一半进程退出；下一次 resume 不调用 renderer，最终
  bytes/ID/timestamp 与 manifest 完全一致。
- Bad：C3 Prompt 含旧 Idea Card 或 Memory cue；测试必须失败。
- Bad：把 missing/failed Agent task 当成 `candidates=[]`；必须 failed。
- Bad：用 1–10 总分选 Top-K，再让人工只确认；这违反 C6 categorical +
  human curation 合同。
- Bad：完成状态缺 terminal disposition、report、Memory Record 或 exact
  finalization/result binding；离线 validation 必须失败。

## 6. Tests Required

默认质量门必须离线，不调用 Codex 或网络，并断言：

- C0–C6 Prompt allowlist、fresh sessions、web policy、稳定 fanout ID；
- C4 matrix、三类 revision budget、disposition reason/evidence/target 闭包；
- Memory off/empty/auto、source exclusion、snapshot cap/hash、Recall/Remix
  optional failure 与禁止递归；
- 空 batch 三类原因和人工全拒绝第四类原因；
- review request 幂等、Unicode、supersede、pre/post reveal、role projection、
  coverage、merge 与 approved fragment budget；
- C6C keep/revise/reject/taste-veto/merge、重复 resume 与失败前不写伪终态；
- report exact bytes、十二个 H2、零/非零、隐私、Memory Record 分类与 handoff；
- finalization 在 stage/manifest/publish/event/completion 每个边界的 crash
  replay，以及 tamper fail-closed；
- failed partial 不暴露 result；
- Useful CLI golden 与 route behavior 不变；
- benchmark 两种 comparison、shared snapshot/no leakage、blind mapping、
  0/1/N Idea worksheet 和 live/fixture 指标边界。

执行：

```bash
.venv/bin/ruff check src tests
.venv/bin/mypy src
.venv/bin/python -m compileall -q src tests
CODEX_HOME=/private/tmp/hacksome-test-codex-home \
  .venv/bin/python -m unittest discover -s tests -v
git diff --check
```

## 7. Wrong vs Correct

### 错误：从当前 package 默认值恢复旧 run

```python
workflow = CreativeIdeaWorkflow(
    RunHub(run_dir),
    CodexRunner(CodexConfig()),
    settings=CreativeWorkflowSettings(),
)
```

### 正确：恢复 hash-bound frozen contract

```python
workflow = CreativeIdeaWorkflow.open(run_dir)
outcome = await workflow.resume()
```

### 错误：C7 中断后重新渲染

```python
bundle = render_success_report(build_report_projection(run_dir))
coordinator.finalize(bundle.outputs)
```

### 正确：存在 manifest 时只重放

```python
FinalizationCoordinator(RunHub(run_dir)).replay()
```

### 错误：把全部人工反馈塞给 Agent

```python
context = json.dumps(all_human_reviews)
```

### 正确：只注入 resolution 明确批准且复核 hash 的 fragments

```python
fragments = {
    fragment.feedback_ref: fragment
    for fragment in store.feedback_fragments()
}
approved = [
    fragments[feedback_ref]
    for feedback_ref in resolution.approved_feedback_refs
]
verify_fragment_hashes(approved)
```
