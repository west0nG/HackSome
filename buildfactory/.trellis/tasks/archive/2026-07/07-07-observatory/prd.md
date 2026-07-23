# Observatory 零上下文观测机制

## 背景 / 目标

First Test 长跑的主产出不是公司业绩，而是观测结论。本任务建一套**宿主机外挂、严格只读**的观测机制：定期/事件性地派一个**零上下文**的全新 LLM 去审视公司运行数据，用独立视角评估业务决策、tool/skill 使用、多 agent 协作真实性、verifier 准确性，产出中文报告。

## 需求

### 三类观测

1. **A · Goal 尸检（事件驱动）**：ledger 里 goal 进入 `done`/`killed` 即触发。范围为该 goal 完整线程：DISPATCH 原文（含隐匿验收标准）→ 承接部门时间窗内的 transcript → REPORT → verifier verdict。重点调查方向（写进 charter 的问题清单，非表格）：goal 定得对不对、够不够宏观；doer 是真做了还是声称做了；用了哪些 tool/skill、哪个工具输出误导了它、对照角色 loadout 找该用未用的；**verifier 独立复核**——观测者拿同一验收标准自查产物（含真实外部 URL/帖子），给出自己的结论并与 verifier verdict 对比。
2. **B · 公司级评审（周期 + 手动）**：默认每 6 小时（可配）+ `make observe` 随时手动触发。读全公司快照（ledger 全量、hub 消息流、company/ 记忆、telemetry）。调查方向：它在运营什么业务（纯从数据重建，重建不出来本身就是 finding）；业务一眼能否跑通、若明显跑不通回溯决策链定位成因；多 agent 是真协作还是伪装单机；显而易见的错误决策（附证据指针）；wake/成本 vs 产出的经济性。
3. **C · 终局综合（长跑结束后手动一次）**：唯一允许读全部 A/B 报告的环节，把独立报告收敛成反复出现的失败模式，并**归因到可修的系统层**（skill / charter / 编排 / 工具误导 / 模型能力 / 数据缺失）。

### 零上下文（结构性保证）

- 每次 A/B 观测 = 一个全新 `claude -p` 调用，无 `--resume`；prompt 只含静态 charter + 原始数据路径 + 本次范围（goal id 或时间窗，由 runner 机械切片）。
- A/B 观测者禁止读 `observatory/` 报告目录（结构隔离 + prompt 禁令）；C 是刻意例外。
- runner 自身用确定性状态记录哪些 goal 已尸检（去重），这不属于上下文污染。

### 观测者权限与报告

- 宿主机运行，对 `state/<company>/` 与仓库代码**只读**——允许它读代码、自己从代码推导系统行为；允许外网只读核验（部署 URL、真实发帖）。严禁写 state、严禁向任何 inbox 发消息。
- 报告为**中文自由文本 markdown**，不强制结构化元组/评分表——charter 给的是要调查的问题，怎么写让观测者自己发挥。发现严重问题（花费异常、公司在做危险的事）时在报告开头显著标注，runner 在控制台高亮提示（无自动干预，用户在手动值守）。
- 落点 `state/<company>/observatory/{goal,company,final}/`；该目录不在 compose 挂载清单内，公司 agent 结构性不可见。

### Runner

- 宿主机脚本 + make targets：轮询 ledger 终态触发 A；定时器触发 B；`make observe` 手动触发 B；C 手动。
- 观测调用用宿主机自己的 claude 订阅（强模型），不占公司额度。

## 约束

- 纯外挂：不进 compose 栈，不修改公司运行时代码（依赖 07-07-longrun-hardening 落盘的 telemetry/audit 数据，但不以其为硬前置——数据缺失时报告里说明即可）。
- charter 遵守"给 LLM 写 skill 不能泛泛"的三道检验：系统特定（引用本系统真实数据面与机制）、压制 LLM 默认（如"倾向把 verifier 判断当权威"、"倾向复述而非核验"）、含非平凡取舍标准。
- 观测报告语言中文；runner 代码/注释英文。
- 观测调用统一用 **Sonnet 5**（`claude-sonnet-5`，用户拍板 2026-07-07），可经 `OBSERVER_MODEL` 覆盖；用宿主机 claude 订阅，不占公司额度。

## 验收标准

- [x] AC1：人工制造一个终态 goal → 自动产出尸检报告，含观测者对 verifier verdict 的独立复核结论。（2026-07-07 真 Sonnet 5 实跑：观测者给出与 verifier PASS 相反的独立 FAIL，识破数据是人工注入，用 audit.jsonl 交叉证明"回执已送达"为假，另挖出 2 个真实系统缺口——_verify_ime 只锚定 /company、finish_run 死代码）
- [x] AC2：`make observe` 产出公司级评审，观测者纯凭数据重建出"这家公司在做什么"。（机制由单测覆盖——spawn/prompt 组装/报告落盘/时间窗推进；真跑质量检验经用户拍板省略：假数据上继续测意义有限，留到 First Test 真实长跑）
- [x] AC3：零上下文可验证：观测进程无 resume、prompt 中无任何前次报告内容（测试断言的是实际 spawn 的 argv 与实发 prompt，含旧报告内容不泄漏）。
- [x] AC4：报告为中文自由文本，严重发现有显著标注。（实跑报告全中文，首行 RED-ALERT 按协议触发，runner 控制台红色高亮）
- [x] AC5：C 类综合能读全部报告并产出按系统层归因的问题清单。（机制由单测覆盖：C 的 prompt 含报告目录、A/B 不含；真跑留到长跑结束后的正式使用）
