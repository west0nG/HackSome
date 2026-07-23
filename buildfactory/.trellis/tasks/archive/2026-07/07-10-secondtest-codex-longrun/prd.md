# secondtest: full-codex company longrun

## 背景与授权

用户 2026-07-10 直接指示（睡前口头授权，明早验收）：codex-parity 收官后立即起一家全 codex 的新公司 `secondtest` 做测试；observation 沿用 Sonnet 5；中途发现**非常严峻的机制卡死问题**由值守 agent 自主修复；公司拥有全部 secret 与账号权限（`ACCOUNT=foundagent` 全量账号包）。

## 需求

- R1：五个常驻角色（ceo/researcher/builder/growth/verifier）全部 `provider: codex`；其余配置零改动（charter/skills/mcp/hooks 声明不分叉）。
- R2：`make up COMPANY=secondtest ACCOUNT=foundagent` 全栈拉起（含 hub/peripheral/provisioner/mail-poller）；不发人工 kickoff——CEO 首个 proactive idle wake 即 07-06 开闸后留待生产观察的那次真实唤醒。
- R3：observatory daemon（host 侧，observer model `claude-sonnet-5` 默认值）随跑：goal 尸检 + 周期公司 review。
- R4：通宵值守：监视 hub 心跳/容器崩溃循环/telemetry 错误/goal 卡死/observatory 存活。**机制级卡死**（编排/runtime/基建 bug）自主修复并留提交与记录；**经营层行为**（goal 选择、方向、对外动作）不干预——那是实验本体，交给 observatory 记录。
- R5：干预与异常全部留痕（本任务目录 + journal），明早给用户完整验收报告。

## 约束

- 修复遵循既有立场：never-brick、doer≠judge、中性契约扩展规则；生产中热修优先最小 diff。
- 不因为"省钱"叫停公司：成本记录交给 telemetry/observatory，用户已知情。

## 验收标准

- [x] AC1：公司持续运行至用户晨间验收（中途允许有已修复的中断，不允许无人处置的瘫痪）。（北京时间 00:46 起栈，01:16 首次真实 wake，10:50 最后一次 wake，11:03 生成终局报告；无 goal 留在非终态）
- [x] AC2：期间产生的 goal 有完整闭环样本（dispatch→执行→report→verify→终态）且 telemetry 全程有 usage 数据。（11 个唯一 goal 全部 `done`；其中 2 个首轮 FAIL 后重做；118 次 wake 均有 telemetry）
- [x] AC3：observatory 产出至少一份 goal 尸检或公司 review 报告。（11 份 goal 尸检、2 份公司 review、1 份终局综合报告）
- [x] AC4：所有机制级干预（如有）有：现象 → 根因 → 修复 diff/动作 → 验证 的四段记录。（本轮没有需要 host 值守者热修的 hard-brick 机制事故；两次 TLS heartbeat 失败自动恢复。Goal 内部的 verifier 重做均在 Hub 轨迹中留痕，不属于 host 机制干预）

## 晨间验收与公司审计

- 全周期经营、产品、决策、用户痛点与市场信号审计：`research/secondtest-company-analysis.md`
- 并行值守重大取证更正：`research/overnight-log.md`（CEO 七次方向评审均真实 spawn 独立 reviewer；Observatory 的“同 session 自评”结论不成立）
- 原始经营真相源：`state/secondtest/inbox/hub.jsonl`（37 条，11 个 goal）
- 终局观测报告：`state/secondtest/observatory/final/20260710T030339Z.md`
- 独立复验：公开 npm `mcp-risk-inventory@0.1.2` clean-prefix 安装成功；源码 `npm run check` 与 `npm test` 6/6 通过；公开 repo/npm/外联线程均已重新读取。
- 仓库全量 pytest：620 项中 609 通过、11 失败。失败集中在既有 resident loadout/skill 物化和 `researcher` provider 旧断言，与本任务新增研究报告无关；本轮未越权修改这些基线问题。
- 规格判断：本轮只新增研究/验收文档，没有修改命令、API、数据结构或跨层契约，因此不更新 code-spec；经营判断与产品缺陷全部保留在本任务研究报告中。
