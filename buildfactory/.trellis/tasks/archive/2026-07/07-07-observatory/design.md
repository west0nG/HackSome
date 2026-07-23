# Observatory 技术设计

## 形态与落点

```
observatory/                     # repo 顶层，纯宿主机外挂，不进 compose
├── runner.py                    # daemon + CLI（stdlib-only，与 orchestration/ 同风格）
├── charters/
│   ├── goal_postmortem.md       # A 类宪章（中文，prompt 主体）
│   ├── company_review.md        # B 类宪章
│   └── final_synthesis.md       # C 类宪章
└── tests/test_runner.py
```

报告与 runner 状态落 `state/<company>/observatory/`（不在 compose 挂载清单内，公司 agent 结构性不可见）：

```
state/<company>/observatory/
├── goal/<goal-id>.md            # A 类报告（goal id 即文件名，天然去重可查）
├── company/<UTC-ts>.md          # B 类报告
├── final/<UTC-ts>.md            # C 类报告
├── .processed                   # 已尸检 goal id，每行一个（runner 确定性状态）
└── .last_company_review         # 上次 B 类运行的 UTC 时间戳
```

## 观测者调用（零上下文 + 只读的结构保证）

每次观测 = 一个全新子进程：

```
claude -p <assembled-prompt> --model $OBSERVER_MODEL \
  --allowedTools "Read,Glob,Grep,WebFetch,WebSearch" \
  --output-format text
```

- **零上下文**：无 `--resume`/`--continue`，每次进程全新；prompt = 静态宪章 + 动态块（company 名、state 根路径、本次范围），不含任何前次报告内容。
- **只读是工具面硬约束**：不给 Write/Edit/Bash，观测者物理上无法写文件、发消息、执行命令；外网核验走 WebFetch/WebSearch（只读）。
- **报告 = 进程 stdout**：由 runner 捕获写盘，观测者从不接触报告目录（无写工具 + prompt 不提报告路径）。runner 在文件头注入元数据（时间、模型、类型、范围）。
- cwd = 仓库根，观测者可自由读代码与 `state/<company>/`。
- C 类例外：prompt 动态块里明确给出 `observatory/{goal,company}/` 路径让它读全部报告。

环境旋钮（均有默认）：`OBSERVER_MODEL=claude-sonnet-5`、`CLAUDE_BIN=claude`（测试注 fake）、`OBSERVE_INTERVAL_SECS=21600`、`OBSERVATORY_POLL_SECS=30`。

## 触发与调度

- **A 尸检**：每 poll 扫 `state/<company>/ledger/g*.json`，`status ∈ {done, killed}` 且不在 `.processed` → 观测；报告成功写盘后记 `.processed`（at-least-once，崩溃最多重测一个 goal，无害）。
- **B 评审**：距 `.last_company_review` 超过间隔 → 观测；时间窗 =（上次时间戳, 现在]，由 runner 机械切片写进动态块（首次 = 不限起点）。
- **C 综合**：仅手动。
- CLI：`runner.py --company <name> daemon`（A+B 常驻）/ `once-company` / `once-goal <id>` / `once-final`。
- make targets：`observatory`（daemon）、`observe`（once-company）、`observe-final`。
- 串行执行，一次一个观测进程（无并发，队列天然由 poll 顺序形成）。

## Prompt 组装

`prompt = charter 全文 + "\n\n---\n\n" + 动态块`。动态块只含机械事实：

- 公共：company 名、`state/<company>/` 路径、仓库根提示（"系统代码就在当前目录，可自行阅读推导"）。
- A：goal JSON 全文内嵌 + 指点（该 goal 的 DISPATCH/REPORT 在 `inbox/hub.jsonl`、验收标准原文在 `inbox/verifier.jsonl`、角色 transcript 在 `sessions/<role>/projects/**/*.jsonl`、角色装备清单在 `agents/<role>.yaml` + `sessions/<role>/.loadout-manifest.json`）——指路不代读，让观测者自己挖。
- B：时间窗起止 + 同上数据面指点 + telemetry 路径。
- C：`observatory/{goal,company}/` 报告目录路径。

**红色警报协议**：宪章约定——若有严重发现（花费异常、公司在做危险/不可逆的蠢事、verifier 系统性误判），报告第一行固定为 `RED-ALERT: <一句话>`。runner 检查捕获 stdout 的首行，命中则控制台高亮打印（不做任何自动干预）。

## 宪章要点（三道检验的落法）

三份宪章是本任务的核心交付物，各自必须：①引用本系统真实机制（goal 状态机语义、doer≠judge、验收标准隐匿、charter 占位现状）；②点名要压制的 LLM 默认——"把 verifier 的 verdict 当权威"（你的职责恰是复核它）、"复述数据而非核验"（发帖/部署要真的去外网看）、"倾向给面面俱到的综述"（只写有证据指针的发现）；③给非平凡取舍——"宁可漏报也不编造证据"、"业务可行性按'一个理性人类运营者会不会做'判断而非技术上能不能跑"。

## 测试策略

不调真 LLM：`CLAUDE_BIN` 指向 fixture 脚本（echo 固定 markdown，含/不含 RED-ALERT 两种）。覆盖：终态检测与 `.processed` 去重、报告写盘路径与元数据头、prompt 组装（含宪章全文与 goal JSON、**不含** observatory 报告路径——A/B 零上下文断言）、argv 断言（无 --resume、allowedTools 白名单、model 默认与覆盖）、B 类时间窗推进、RED-ALERT 检测、claude 进程非零退出不写报告不记 processed。

## 真跑验收（AC1/AC2 用真 Sonnet 5）

用 hardsmoke 遗留 state（有真实 transcript）+ 手工构造一个终态 goal（ledger JSON + hub.jsonl 对应消息），跑 `once-goal` 与 `once-company` 各一次，人工检查报告质量与中文。
