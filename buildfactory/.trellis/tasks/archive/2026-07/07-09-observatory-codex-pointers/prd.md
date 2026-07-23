# Observatory dual-runtime transcript pointers

## Goal

observation（observatory）在公司角色跑在 codex 上时依然能完成尸检的核心动作——找到角色 transcript、数出工具轨迹、独立复核。observation 自身继续跑在 host 的 claude + Sonnet 上，不随公司 provider 变化。

## 需求

- R1：`observatory/runner.py` `_pointers_dataplane` 的角色 transcript 指针同时覆盖两种布局，并注明按角色 `provider`（agents/<role>.yaml）二选一：
  - claude-code：`{root}/sessions/<role>/projects/**/*.jsonl`
  - codex：`{root}/sessions/<role>/codex/sessions/**/*.jsonl`（JSONL rollout，事件形态与 claude transcript 不同——指针处一句话说明即可，格式细节由零上下文观测者自行阅读推导，与"允许读仓库代码"的既有立场一致）
- R2：两份宪章（goal_postmortem.md / company_review.md）中"恢复各自的 claude session"等 runtime 专属措辞改为中性（如"恢复/新建各自的 agent session"）；宪章里涉及 transcript 的调查指引不预设 claude 事件格式。
- R3：零上下文纪律不变——指针只指路不代读，不引入任何观测报告目录的泄露。

## 约束

- 只动 `observatory/`（runner 的指针函数 + 两份宪章）；不改公司运行时代码。
- A/B prompt 的既有结构与 dedup 状态语义不变。

## 验收标准

- [x] AC1：A/B prompt 中 transcript 指针含两种布局及 provider 判别指引；现有 observatory 单测（如有断言指针文本）同步更新并通过。
- [x] AC2：宪章全文 grep 无 "claude session" 类 runtime 专属措辞（观测者自身用 claude CLI 跑这一事实不在此列）。
- [x] AC3（真跑，并入父任务 AC-P1 执行——证据见 07-09-codex-parity/research/）：对一个 codex 角色的终态 goal 真跑一次尸检，报告能给出 codex transcript 内的证据指针（文件路径 + 位置）。
