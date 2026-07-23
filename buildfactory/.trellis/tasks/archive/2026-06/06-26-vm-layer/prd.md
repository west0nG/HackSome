# VM Layer（虚拟机层 / 隔离容器层）

> 父任务：`.trellis/tasks/06-26-foundagent-v6`（Foundagent v6）。本子任务 = 四层骨架第 ① 层，自底向上第一个搭。
> 状态：规划中（design spike 进行中）。目标是先做**最小可运行的隔离容器**，再测试驱动扩展。

## Goal（目标）

为单个 Agent session 提供一个**最小可运行的隔离运行环境**（栈 B 自托管，容器优先），具备 **Computer Use + 浏览器**，以及**可扩展的账号/secrets 注入接口**和**静态出口 IP 接口**。先做到能跑、能测、可扩展、可观测，不追求一步到位。

**已确认环境约束（用户）：**
- 宿主机 = 开发者本机 **Mac**（当前环境）；**不考虑生产环境**，验证阶段全程在这台 Mac。
- **容器（Docker）即可**，只要保证 **agent 隔离**；强隔离 VM 短期无特别优势，能在容器做好就用容器。
- 目标是「在 Mac 上**最好配、最好用**」。

## 上游约束（来自父任务）

- 部署形态 = **栈 B 自托管**：编排Claude Agent；web 层 Browser Use/Steel；静态 IP 用 Decodo/IPRoyal 独享 ISP + AdsPower；secrets 用自托管 Infisical。
- **VM 方法论**：先最小可运行 → 跑起来观察 agent 卡点 → 按需加账号。**初版不配全账号**；账号注入做成**可扩展接口**；「账号可扩展性」是核心设计目标。
- **默认凭证 = Claude subscription plan**（经 Claude Code OAuth，容器挂载 `~/.claude/.credentials.json`）；**API key 仅用于 Phase 0 冒烟（computer-use-demo 需要）及备选/有界负载**。默认运行时 = Claude Code（claude CLI，订阅），可切 Agent SDK（API key）。

## Requirements（需求）

- **VM1 生命周期**：可一键启动/停止一个隔离容器，每 agent session 一个，互不干扰。
- **VM2 Computer Use**：容器内提供截图/点击/输入/按键能力（桌面级），供 agent 操作任意页面/应用。
- **VM3 浏览器自动化**：容器内有可被 agent 驱动的浏览器（Playwright / CDP / Browser Use）。
- **VM4 可扩展账号/secrets 注入接口**：声明式配置、按需加账号、初始最少（一个 Claude 凭证 + 一个邮箱）；新增账号只需改声明、不改核心代码；预留 Infisical 接口。
- **VM5 静态出口 IP 接口**：可插拔出口代理（Decodo/IPRoyal）；初版可默认走本机出口，但接口必须存在、可切换并验证出口 IP 变化。
- **VM6 可承载 agent**：容器内能启动一个 agent 进程（Claude Code / Agent SDK）并让其使用 VM2/VM3 —— VM 层只需证明"能起一个 agent 并操作浏览器"，完整 Agent 层留给子任务 ②。
- **VM7 可观测性（硬要求）**：**Claude / agent 的所有输出 log 必须完全可观测、可记录**（完整捕获、可回放、持久化），便于排查 agent 卡在哪。
- **VM8 Graceful shutdown（硬要求）**：容器/agent 能优雅退出 —— 收到停止信号时妥善结束 agent 进程、刷写日志与状态、不留僵尸/损坏状态。

## Acceptance Criteria（验收）

- [x] **AC1** 一条命令起一个隔离容器，内含可用的 Computer Use + 浏览器。✅ `foundagent/cua-agent` 镜像 + `broker.spawn` 一条命令起容器，computer-server:8000 就绪后 CU+Firefox 可用；spike/smoke/AC6 demo 多次实测起停。
- [x] **AC2** 账号/secrets 可扩展注入 ✅：`accounts/<id>/secrets.env` → `--env-file` 注入容器 env；实测加账号只需 append 一行、不改代码。真实账号按需填（Infisical 后续可生成同格式）。
- [x] **AC3** 在容器内跑起一个 agent，用浏览器完成一件简单任务（如打开网页 → 登录某账号 → 截图），证明「Computer Use + 浏览器 + 账号注入」三者打通。✅ **satisfied via agent-layer AC6**（`f6176b2`）：容器内 agent 在 the-internet 测试站登录成功 + 截图 + `DEMO_ACCOUNT_EMAIL` 注入填页面，三者实测打通。详见 `archive/2026-06/06-26-agent-layer/research/ac6-e2e.md`。
- [x] **AC4** 静态出口 IP 接口 ✅：`proxy=`/env → 容器 `HTTP(S)_PROXY`；实测 curl 走 proxy（死代理→curl 失败，证明接口生效）。真实 ISP IP 按需接；⚠️ 浏览器 proxy 需额外配（Chromium 忽略 env proxy）。
- [x] **AC5** Claude/agent 的全部输出 log 被完整捕获并持久化（可事后回放排查）。✅ JSONL transcript 挂载宿主，实测 215KB/19 行可回放。
- [x] **AC6** 向容器发停止信号后，agent 优雅退出、日志与状态完整刷写，无残留损坏。✅ append-only JSONL 硬 kill 不丢 + `claude --resume` 恢复（实测）。

## Out of Scope（本子任务不做）

- CEO 智能编排 / 决策调度（→ 编排层；broker 多容器 infra 属本层、已具备）。
- **持续运营 / agent 长跑**：本期 task-per-container（每任务一容器、完即弃），不做常驻长跑（用户决定，后续再做）。
- **工作产物持久化**：只留接口（broker `workspace` 卷 hook），不做死——产物归记忆层/Wiki。
- 公司记忆层 Wiki/assets（→ 记忆层）。
- 自主判断力 skill/hook（→ 骨架就绪后）。
- 生产环境 / 跨主机扩展（用户明确：短期只在本机 Mac）。
- 全量账号预配、防关联指纹精调、验证码自动解（按需在后续迭代加，先留接口）。

## Open Questions

- ~~VMQ1 宿主机环境~~ → 已定：**这台 Mac，全程验证都在 Mac，不考虑生产**。
- ~~VMQ4 隔离粒度~~ → 已定：**用容器（Docker），只要保证 agent 隔离**；VM 非必需。
- **VMQ2 容器方案选型**（design spike 进行中）：Bytebot / 自组 Anthropic computer-use Docker / trycua 容器模式 / 其他 —— 目标 Mac 上最好配最好用 + agent 隔离 + computer use + 浏览器。
- **VMQ3 桌面 payload**：用现成桌面（含浏览器 + agent loop）还是自组 Xvfb + 浏览器？（随 VMQ2 一起定）
- **VMQ5 可观测性方案**：完整捕获 Claude 输出 log 的具体做法（stream-json / Agent SDK hooks / 容器日志 / Langfuse 等）—— design spike 定。
- **VMQ6 Graceful shutdown 模式**：SIGTERM 处理 / PID1(tini) / agent 优雅退出与状态刷写 —— design spike 定。

## 下一步

1. **Design spike（进行中）**：调研 + 对比技术与服务商选型，覆盖 ① 容器沙箱方案（Mac 上最好配最好用 + agent 隔离 + computer use + 浏览器）② 可观测性（完整捕获 Claude 全部输出 log）③ graceful shutdown + 生命周期。
2. 选定方案 → 写 `design.md` + `implement.md`。
3. 搭最小可运行版 → 跑 AC1–AC6 → 测试驱动迭代。
