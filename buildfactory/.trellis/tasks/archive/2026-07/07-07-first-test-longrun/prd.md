# First Test: 首次端到端公司长跑（观测驱动）

## 背景 / 目标

系统雏形已齐（Hub 编排 + 5 常驻角色 + create-role + 账号轨），历史上从未真正无人干预地长跑过——之前最长的真跑只是特性收尾时的单轮冒烟。本任务发起第一次真实长跑：起代号 **firsttest** 的新公司，复用 foundagent 账号包，完全自主冷启动，让它 try whatever it wants。

**目的是观测，不是产出。** 现有 charter/skill 的粗糙是刻意保留的实验对象；长跑要回答的是"哪些地方需要增强、哪些需要补齐"，答案由独立零上下文观测者从运行数据中提炼。

## 用户已拍板的实验参数

- **初始目标**：完全自主冷启动，不注入任何种子消息。CEO 第一次心跳唤醒时凭 find-opportunity / decide-direction 自己定方向——"从零选方向"的判断链本身是第一观测对象。
- **时长**：不设时限，用户手动盯，觉得不对随时 `make down`。
- **外部动作**：全部真实执行（真发推 @Solvotheagent、真部署 Vercel、真改 Cloudflare、可能调付费 API、create-role 真起容器）。无 dry-run。
- **成本**：只计量落盘，不设阈值、不熔断。

## 任务地图（三个子任务，按序）

1. **07-07-longrun-hardening**：最小加固包。其中 wake/成本计量与 hub 审计落盘是 Observatory 的数据前置。
2. **07-07-observatory**：零上下文观测机制（goal 尸检 + 公司级评审 + 终局综合）。
3. **07-07-ignition**：点火 runbook、起栈、首个 CEO wake 验证，进入观测期。

## 跨子任务验收标准

- [x] AC1：firsttest 栈无人干预运行，任一容器进程崩溃后自动拉起并恢复对账。（17.5 小时无人值守；hub kill -INT 实测自愈；中途 hub 修复重启后 reconcile 无缝接管）
- [x] AC2：每次 wake 的成本与时间线在宿主机可查（纯记录，无任何阈值行为）。（189 次唤醒 $274.53 入账；已知缺口：超时被杀会话约 85 分钟未入账 → 终局总结模式六）
- [x] AC3：goal 进入终态自动产出尸检报告；公司级评审周期性产出；报告为中文自由文本，且每次观测为零上下文。（9 份任务复盘 + 2 份公司级评审，全中文，5 次 RED-ALERT 全部言之有物）
- [x] AC4：hub 拦截的违规消息可事后追溯。（audit.jsonl 生产环境真实落账，含 researcher 畸形 REPORT 一例）
- [x] AC5：终局综合把失败模式归因到可修的系统层。（`state/firsttest/observatory/final/20260708T034456Z.md`：7 个模式，每个 ≥2 独立例证 + 主归因层 + 具体修法；2 个已中途修复，5 个待修）

## 范围外（本轮明确不做）

- wake 冷却 / 成本熔断阈值 / :8900 鉴权（用户拍板：本地环境，暂不管）。
- builder/researcher/growth 占位 charter 与薄 skill 的补齐——这正是长跑要暴露的对象，跑完凭观测报告再修。
- dry-run / 沙盒开关。
- 多公司并发运行的 compose project 隔离（本次 foundagent 栈保持 down，单栈运行）。
