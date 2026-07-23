# Orchestration Layer — Design（编排层设计）

> 子任务 `06-26-orchestration-layer`。主体 = **Goal 协议 + 容器化编排**；broker 是其中一个（容器化的）搬运组件，不再是主角。
> **原则**：确定性外壳（程序按死规矩跑的部分）先写实；模糊的、靠大模型判断的那半，明确标「先不定、等真实 case」。状态枚举/流转是第一版、跑起来按实验改。调研（`research/goal-definition-survey.md`、`research/container-orchestration.md`）只作参考、不照搬。

## 0. 一句话

上面派「要的结果」(goal)，下面一个执行者盯着它一轮轮干、干完才验、验不过接着改，看门狗防瞎耗。**全程零人、全在容器里。**

## 1. 容器拓扑（DooD）

```
宿主 Mac：只剩 docker 引擎 + 一句「一键启动」(compose)
  [broker 容器]  挂宿主 docker.sock
    │ 起兄弟容器（非嵌套 DinD；都是宿主 docker 的平级子容器）
    ├─ [外设层容器]（常驻）   外部信号归一 → ledger/inbox
    ├─ [CEO 容器]（常驻）      派 goal、收验收结果
    ├─ [worker 容器]（临时）   领 goal、跨 session 干、用完即拆
    └─ ...
  共享 volume：goal ledger（派发+状态）/ 公司 assets（成果）/ CEO scratchpad
```

- **现状 → 本版本**：broker 现在是宿主机 python 进程；本版本把它**搬进容器**、挂 `docker.sock`，起出来的 agent 容器仍是宿主 docker 的**兄弟**（非嵌套）。
- **broker = 非大模型的笨搬运工**：盯 ledger 状态变化 → 起/停容器、把要验的 goal 派给验收 agent。**agent 之间不直接说话**，全靠读写 ledger。
- **复用现有 broker 能力**（OC1–OC4 已验证）：`docker run -d` 起 `foundagent/cua-agent` → 轮询容器内 `:8000` ready → `docker exec claude -p ...`；不映射宿主端口（容器内 `localhost:8000` 自给自足，N 容器无冲突）；订阅凭证零 API key。
- **代价**：挂 socket = 把宿主 docker 控制权交给 broker 容器（提权）；测试期可接受，安全收窄后置（route：socket-proxy → 语义化 broker → Sysbox/Firecracker）。

## 2. 派 goal，不派 task

- 派发单元 = **goal（想要的结果）**，执行者自己想步骤；不派「做某一步」。更自主、契合 CEO 不事必躬亲。
- 大 goal 里可再开小 goal → 一棵递归树，每层都一样。

## 3. goal 和「一次尝试(run)」分开（干净的关键）

- **goal** = 一直活着、不达目的不算完。**run/session** = 对它的一次尝试。一个 goal → 多次尝试。
- **执行 = 同一执行者跨多 session 死磕**：带着上次学到的继续 → 拿出「做完了」证据 → 才验 → 验不过把「哪不对」喂回去**接着干**，**不是杀了重起**（重起把经验全扔，费钱又蠢）。
- 和 broker「一任务一容器」天然契合；只是把「goal 状态」与「一次容器执行」拆两层记。

## 4. 死规矩外壳（状态机，现在就能定）

- **状态枚举（第一版，按实验改）**：
  `open`(等领) → `claimed`(被一个执行者领走、加锁) → `running`(在干) → `reported`(说做完了) → `verifying`(在验) → `done` ／ `killed`(看门狗或上层叫停)。
  **验不过不是新状态** → 直接回 `running`（带上「哪不对」接着干）。
- **单一领取 + 加锁**：一个 goal 同时只能被一个执行者领（原子 checkout），纯程序判定。
- **看门狗刹车**：试 N 次不成 / 原地打转 → 升级上报，由上层改方向或 `killed`。防做不成的 goal 无限烧钱。

## 5. 验收（统一交 agent、零人）

- goal 报完成 → 派一个**验收 agent** → **去公司 assets 里查成果有没有、好不好** → 要确定性就**自己写个检查程序跑**，否则看着判 → **全程无人**。
- **没有 `verify_kind` 字段**：验收方式不预先声明，验收 agent 自己决定怎么验。
- 零人原则覆盖验收：业界对软任务「退回人审」那条路我们走不了；软任务只能交验收 agent（认它的已知弱点、无人审兜底）。

## 6. goal 长什么样（4 字段最小骨架）

```
id        # 唯一
parent    # 谁派的 / 属于哪个大 goal（成树）
intent    # 要的结果，自然语言（大模型那半，内容不规定）
status    # 第 4 节那套状态枚举（死规矩）
```

- **没 `result`**：成果落公司 assets、不在 goal 上。
- **没 `verify_kind`**：验收统一交 agent。
- **先不定（等真实 case）**：intent 内部结构、验收细则、约束（预算/时限）、重试上限数字。

## 7. 成果 vs 记录（边界，别重复）

- **成果（名词：落地页/文档/产品）→ 公司 assets**（记忆层 `company_state_kit`）。
- **goal 记录（动词：派了、到哪步）→ goal ledger**（编排运行时，host 侧共享 volume）。
- 验收 agent 读 assets 判好坏，状态写回 ledger；两边不存重复内容。

## 8. 两条做法规矩

- **派活时就把「啥算做完」说清楚**（期望成果），给验收 agent 一个判的依据，也防跑偏。
- **「做完没」独立判断**，绝不能用「想不出新步骤了」当做完（会假完成/瞎耗）。

## 9. 跟别的部分的关系

- 执行者跨 session 死磕 → 工作记忆维护 → **compact** `06-28-agent-compact`。
- 外部信号（邮件/Stripe…）触发 → **外设层** `06-28-peripheral-layer`。
- 看门狗 / 没人叫就自检 → **heartbeat**（同编排层，待写）。
- CEO 顶层决策（选题/kill）→ skill+hook 阶段。

## 10. 明确不锁死的

- 状态枚举、流转细节：第一版，跑起来按实验改。
- 大模型那半的所有字段：等真实 case。
- **别照抄** Paperclip 50+ 列字段膨胀。

---

# 实现设计（贴现有代码）

> 现有 broker：`spawn(op_id, task) -> AgentResult`（一个容器一次 `claude -p` = 一次 run）、`run_fleet`、`teardown`。goal 协议架在其上。并发用 `fcntl.flock`（与 `company_state_kit` 一致）。

## 11. 增量切分（先跑通再加）

- **增量 1（本次做）**：goal ledger + 状态机，**纯 python、不依赖 docker、单测覆盖**。执行/验收做成**可注入 seam**（测试用假函数）。证明死规矩外壳端到端能跑。
- 增量 2：接真实执行——execute = `broker.spawn(intent)`；验收 = 派一个验收 agent（读公司 assets 判）。
- 增量 3：DooD——broker 进容器、compose 一键起。

## 12. 增量 1 详设：goal ledger + 状态机

**`orchestration/goal_ledger.py`（纯逻辑、确定性、可单测）**

- 存储：每 goal 一个 JSON 文件 `<ledger>/<goal_id>.json`；ledger 根 = env `GOAL_LEDGER`（默认 `<repo>/orchestration/ledger`，**不在 company folder**——编排运行时、非公司记忆）。原子性用 `fcntl.flock`。
- **goal 记录**：`{id, parent, intent, status, attempts, feedback, runs:[...], created_at, updated_at}`。（4 字段骨架 + 运行时簿记 attempts/feedback/runs/时间戳——这些是死规矩外壳要的，不算 LLM 侧字段。）
- **run 记录**（一次尝试，挂 goal.runs，体现 goal/run 解耦）：`{run_id, kind: execute|verify, ok, summary, started_at, finished_at}`。
- **状态枚举**：`open → claimed → running → reported → verifying → done | killed`；验不过 → 回 `running`（verdict 写进 goal.feedback）。
- **API（每个做状态合法性校验，非法转换抛错）**：
  - `add_goal(intent, parent=None) -> goal_id`
  - `claim_open_goal(worker_id) -> goal | None`：**原子**——flock 文件、若 `status==open` 则置 `claimed`+assignee 写回，否则跳过 → 保证单一领取。
  - `start_run(goal_id, kind) -> run_id` / `finish_run(goal_id, run_id, ok, summary)`
  - `to_reported` / `to_verifying` / `pass_verify`(→done) / `fail_verify(goal_id, feedback)`(→running, attempts+1) / `kill(goal_id, reason)`
  - `should_kill(goal_id, max_attempts) -> bool`（看门狗：attempts ≥ max_attempts）

**`orchestration/goal_loop.py`（驱动一个 goal 跑到底）**

- `run_goal(ledger, goal_id, execute_fn, verify_fn, max_attempts=3)`：
  ```
  claim → while True:
    start_run(execute) → execute_fn(intent, feedback) → finish_run → to_reported
    to_verifying → verify_fn(goal):
        过  → pass_verify → done, break
        不过 → fail_verify(feedback)
    if should_kill(max_attempts): kill, break
  ```
- `execute_fn(intent, feedback)->(ok, summary)`、`verify_fn(goal)->(passed, feedback)` 是**注入 seam**：单测用假函数；增量 2 换成 `broker.spawn` / 验收 agent。

**单测**：① add→claim 原子（俩 worker 抢同一 goal 只一个成功）；② 全程状态机 claim→run→report→verify 过→done；③ 失败回路：连不过→回 running、attempts 累加→N 次 watchdog kill；④ 非法转换抛错。

## 13. 增量 2 详设：接真实执行 + 验收 agent

> 把增量1 的注入 seam 换成真实 broker。execute = 容器跑 claude 干 intent；verify = 另起一个验收 agent 读公司 assets 判。**LLM 入、标准化出**：验收 agent 的判断必须落成机器可解析的 verdict。

**`orchestration/goal_runtime.py`（连接 ledger/loop 与 broker）**

- `build_task(intent, feedback) -> str`（纯函数）：intent +（若有）上次 verdict 反馈，拼成执行者任务 prompt。
- `parse_verdict(text) -> (passed: bool, feedback: str)`（纯函数，**标准化出的闸门**）：抓输出里最后一行 `VERDICT: PASS` / `VERDICT: FAIL: <reason>`；抓不到 → 当 FAIL（"无可解析 verdict"）。
- `make_execute_fn(op_id, company_id, spec=None) -> execute_fn`：`execute_fn(intent, feedback)` = `broker.spawn(op_id, build_task(...), spec, company_id=company_id)` → `(res.ok, res.text)`，用完 `teardown`。执行者挂 /company（company-state skill），成果写进公司 assets。
- `make_verify_fn(op_id, company_id, spec=None) -> verify_fn`：`verify_fn(goal)` = spawn 验收 agent（同挂 /company），prompt =「读公司记忆，判断 `<intent>` 是否达成；**最后一行只输出** `VERDICT: PASS` 或 `VERDICT: FAIL: <原因>`」→ `parse_verdict(res.text)`。执行者与验收用**不同 op_id**。

- **验收 agent spec = 必须独立、只读、无 record hook**（`agents/verifier.yaml`：带 company-state 读技能、**无 hooks**）。⚠️ e2e 教训：复用带 `record` Stop hook 的 operator spec，会在 agent 说完 `VERDICT: PASS` 后**强制一步 record 收尾**，把 verdict 顶成非最终输出 → `parse_verdict` 抓不到 → 假失败。**executor 用 company-operator（要 record 写成果），verifier 用 verifier.yaml（绝不 record）。零人。**
- **重试连续性**：本增量 = 上次 verdict 反馈拼进下次 prompt（feedback-in-prompt）。**真正的跨 session 工作记忆 = compact 任务（已拆出、不在此）**，这里先做最小桥接。
- **e2e 入口** `run_goal_e2e(intent, company_id)`：add_goal→claim→`run_goal(execute_fn, verify_fn)`→打印终态。需 docker + image + `CLAUDE_CODE_OAUTH_TOKEN`，**烧 token、gated**（环境就绪才跑）。

**测试**：纯函数 `build_task` / `parse_verdict`（PASS / FAIL / 无 verdict 三情形）单测；adapters 用 **fake spawn** 验证（不起真容器、不烧 token）。真实 e2e 环境就绪时手动跑。

## 14. 增量 3 详设：DooD（broker 进容器）

> 把 broker 从宿主 python 进程搬进一个容器；它挂宿主 `docker.sock`，起的 agent 容器仍是宿主 docker 的**兄弟**（非嵌套）。宿主近空 + 一键起。

**关键 DooD 技巧 = 路径一致**：broker 在容器里跑 `docker run -v <src>:<dst>`，`<src>` 由**宿主 docker daemon** 解释，不是 broker 容器的文件系统。→ 把宿主仓库**挂到容器内同一个绝对路径**（`${PWD}:${PWD}`，workdir 同），于是 broker.py 用 `__file__` 算出的 `_REPO` 在容器内外是同一路径，所有 `-v` 源路径对宿主有效、**零翻译，broker.py 不用改**。

**`orchestration/Dockerfile.broker`**：thin 控制镜像 = python3 + docker CLI **client**（仅客户端、非 daemon）+ 仓库 python 依赖（按 `agent/`、`orchestration/` 实际 import 装，至少 pyyaml）。仓库代码**挂载**（不 COPY，便于迭代）。

**`docker-compose.yml`**（仓库根）service `broker`：
- build: `orchestration/Dockerfile.broker`
- volumes：`/var/run/docker.sock:/var/run/docker.sock` + `${PWD}:${PWD}`（同路径）
- working_dir：`${PWD}`
- env：`CLAUDE_CODE_OAUTH_TOKEN`（从 `vm/.env.local`）、`FOUNDAGENT_HOST_REPO=${PWD}`（防御）
- command：`sleep infinity`（常驻控制容器，靠 exec 驱动）
- （外设层 / CEO service 后续加，本增量只 broker。）

**一键**：`docker compose up -d`；驱动用 `docker compose exec broker python -m orchestration.goal_runtime <company> <intent>` 或 broker demo。

**验证**：
- 便宜（不烧 token）：`compose up -d` → `exec broker docker run --rm hello-world`（证明 socket+CLI+起兄弟容器通）→ `exec broker python -c "import orchestration.broker"`（仓库+依赖可用）→ 宿主 `docker ps` 看 agent 容器与 broker **平级**（非嵌套）。
- 完整（烧 token，可选）：`exec broker` 跑一次最小 cua-agent spawn / goal e2e，证明容器内 broker 能起 cua-agent 兄弟并跑 claude。

**宿主近空**：跑起来宿主只剩 docker 引擎 + `compose up`。socket 挂载=提权，硬化后置。
