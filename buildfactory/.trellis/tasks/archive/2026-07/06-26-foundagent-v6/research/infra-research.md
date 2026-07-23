{
  "summary": "Research agent-purpose VM/sandbox, computer-use, anti-block, orchestration, and identity-injection options for Foundagent v6",
  "agentCount": 13,
  "logs": [
    "Researched 6/6 dimensions; synthesizing report"
  ],
  "result": {
    "report": "# Foundagent v6 基础设施研究综合报告\n\n> 目标:为「自主经营业务赚钱的 AI Agent」搭建底座。每个 agent session 需要隔离 VM(支持 Computer Use + 浏览器/Playwright)、可注入账号、静态 IP/防封、本地或云端皆可部署;Agent 层基于 Claude Code(skills/hooks/prompts),支持多 provider 与 API/订阅双凭证,CEO 编排器委派 sub-agent,文件系统级公司记忆层(Wiki + assets)。\n\n---\n\n## 1. 执行摘要 (TL;DR)\n\n1. **没有任何单一厂商覆盖全部需求,正确架构是分层组装。** 一套完整的 founder-agent = 「桌面/OS 沙箱(Computer Use)」+「强 stealth 浏览器层(高风控 web)」+「独享静态 ISP IP(每身份固定出口)」+「Secrets Vault + 账号注入」+「Claude 编排内核」。把它当 5 个正交层分别选型,而非找一个万能产品。\n\n2. **2026 年最重要的新发现是 [Claude Managed Agents](https://platform.claude.com/docs/en/managed-agents/self-hosted-sandboxes)(2026-04 公测)。** 它把「编排 + 服务端持久 pause/resume 会话 + per-session 隔离沙箱 + 你掌控出网」整合进官方产品,可让「每个 founder session = 一个持久会话 + 一个自托管沙箱 VM(在你 VPC,经 E2B/Modal/Daytona/Cloudflare/Vercel/Firecracker)+ 独立静态出口 IP」。唯一硬缺口:**只吃 API key,不支持订阅 OAuth token**;计费 = token + $0.08/session-hour。\n\n3. **「每身份固定静态 IP」极度稀缺,且是选择自托管的决定性理由。** 几乎所有浏览器云给的都是**轮换住宅代理**,对「一账号绑一稳定 IP 养号」反而有害。正解:独享静态住宅(ISP)代理([Decodo](https://decodo.com) $2.5/IP、[IPRoyal](https://iproyal.com) $1.8/IP 起、[Bright Data](https://brightdata.com) $2.5-3.5/IP),配在隔离 VM/防关联 profile 上,Computer Use/CDP agent 自动继承出口 IP——网络层对 Agent 完全透明。\n\n4. **Computer Use 分两层、两层都要。** (a) 完整桌面(跑任意 SaaS/桌面应用):托管首选 [E2B Desktop](https://e2b.dev/pricing) 或 [Scrapybara](https://scrapybara.com/),自托管首选 [Bytebot](https://github.com/bytebot-ai/bytebot)(Apache-2.0,一条 docker compose)或 [trycua/cua](https://github.com/trycua/cua)(MIT,Mac 原生 VM 群)。(b) 强 stealth 浏览器(高风控登录/注册):[Browser Use](https://browser-use.com/pricing)(stealth ~81%、$0.02/h 最便宜)或 [Kernel](https://www.kernel.sh/)(持久 profile 自动回写登录态)。\n\n5. **跨会话登录态持久化是 founder-agent 的命脉,不是每次重登(重登触发风控)。** 最佳能力:Kernel 持久 profiles > [Browserbase](https://www.browserbase.com) Contexts > Steel cookie 注入 > VM/容器快照 + [Anon](https://www.anon.com/) 服务端会话注入。\n\n6. **成本与凭证现实:idle 成本主导**(always-on agent 大部分时间在等 LLM),优先「只按 active CPU 计费」的厂商;**订阅 token 套利时代已结束**——2026-06-15 起订阅经第三方/程序化 agent 用量先扣 Agent SDK credits 再按 API 费率计,且 setup-token 1 年期、无自动刷新、到期即断。**生产用 API key,订阅 token 仅用于有界、可控的推理负载。**\n\n---\n\n## 2. 分维度对比\n\n### 2.1 云端 Agent 专用 VM / Sandbox\n\n| 选项 | 类型 | Computer Use | 静态 IP·防封 | 部署 | 定价(已核实 Jun 2026) | 推荐度 |\n|---|---|---|---|---|---|---|\n| [E2B / E2B Desktop](https://e2b.dev/pricing) | Firecracker 沙箱 + 完整 Linux GUI 桌面 | ★★★★★ 唯一开箱完整桌面 | 无,需自叠代理 | 云 + Enterprise BYOC/self-host | Hobby 免费($100 credits);Pro $150/mo;1vCPU $0.05/h 按秒 | ★★★★★ |\n| [AWS Bedrock AgentCore](https://aws.amazon.com/bedrock/agentcore/pricing/) | 托管浏览器(OS 级动作)+ Code Interpreter | ★★★★ 托管浏览器 OS 级鼠标键盘 + Live View | 自有 AWS 网络,无住宅代理 | 仅 AWS 云 | $0.0895/vCPU-hr + $0.00945/GB-hr,idle/I-O 免费 | ★★★★(AWS 用户) |\n| [Kernel](https://www.kernel.sh/docs/info/pricing) | 托管 headful 浏览器云 + turnkey 防封 | ★★★ 浏览器级 Computer Controls | ★★★★★ 全档 stealth 静态 ISP 出口 + CAPTCHA | 仅云 | Free $0;Hobbyist $30;Startup $200;headless ≈$0.06/h | ★★★★(web 层) |\n| [Browserbase](https://www.browserbase.com/pricing) | 托管浏览器云(Kernel 对手) | ★★★ 浏览器级 + Stagehand | ★★★ Basic Stealth + Contexts 持久登录 | 仅云 | Free;Developer $20;Startup $99;$0.10-0.12/h | ★★★★(web 层) |\n| [Morph Cloud](https://cloud.morph.so/web/pricing) | 快照/fork 优先 VM(Infinibranch) | ★★ 自建 VNC | 无 | 云 + 自托管 SDK | $0.05/MCU;Free 300 MCU/mo | ★★★(需 fork 业务状态时) |\n| [Daytona](https://www.daytona.io/pricing) | 通用 agent 沙箱(多 OS、BYOC) | ★★ VNC 自建 | 无 | 云 + BYOC + on-prem | $200 credit;Linux vCPU $0.0504/h 纯用量 | ★★★★(全能底座) |\n| [Cloudflare Sandboxes](https://blog.cloudflare.com/sandbox-ga/) | 边缘持久沙箱 + 网络层凭证注入 | ★★ 终端,无 GUI | ★★★★ 网络层注入凭证 + 每域名出网策略 | 仅云 | 仅按 active CPU 计费,~2s 恢复 | ★★★★(账号注入控制面) |\n| [Fly.io Machines](https://fly.io/docs/about/pricing/) | 裸 Firecracker microVM + 廉价静态 IP | ✗ 自建 | ★★★★ 最便宜原生静态 IP($2/mo IPv4) | 云 + 自有镜像 | shared-1x ~$2/mo;静态 egress IP ~$3.6/mo | ★★★(自建静态 IP 底座) |\n| [Vercel Sandbox](https://vercel.com/docs/sandbox/pricing) | Firecracker 沙箱,持久 + idle-free | ✗ | 无 | 仅云(iad1) | active CPU $0.128/h,I/O wait 免费 | ★★(Vercel 生态) |\n| [Modal Sandboxes](https://modal.com/docs/guide/sandbox) | Python-first,GPU 强 | ★★ 可建 VNC | 无 | 仅云 | 沙箱 CPU ≈3x base,GPU T4-B200 | ★★★(GPU 工作) |\n| [Northflank](https://northflank.com/blog/best-code-execution-sandbox-for-ai-agents) | 生产 microVM + 平台 + BYOC | ★★ 自建 | 用自有云 IP | 云 + BYOC | H100 ~$2.74/h(未独立核实) | ★★(平台一体) |\n| [Blaxel](https://blaxel.ai/blog/best-cloud-sandboxes-ai-agents-2026) | 零成本待机 + 快恢复 + fork | ✗ | 无 | 云 | XS $0.0828/h,待机 $0 compute(未核实) | ★★(idle 极省) |\n| [Coder](https://coder.com/) | 自托管/BYOC 治理型 CDE | ★ 工作区可建 | 用自有网络 | 自托管/air-gap 最强 | OSS 免费 + 企业版定制 | ★★(治理/air-gap) |\n\n**点评:** 云端最佳「桌面 Computer Use」候选是 **E2B Desktop**(唯一开箱完整 Linux 桌面,Manus 已规模化采用,按秒计费在并发下最省)。若业务数据已在 AWS,**AgentCore** 的托管浏览器 + idle-free 计费很划算。**Cloudflare Sandboxes** 的网络层凭证注入是「安全注入大量账号」的最佳控制面。**Daytona** 是均衡全能底座(纯用量 + BYOC + 多 OS),但其 snapshot 是镜像模板而非 Morph 式实时内存 fork。\n\n---\n\n### 2.2 Computer Use 与浏览器自动化云\n\n| 选项 | 类型 | Computer Use | 静态 IP·防封 | 部署 | 定价 | 推荐度 |\n|---|---|---|---|---|---|---|\n| [Scrapybara](https://scrapybara.com/) | 托管完整桌面(Ubuntu/Win)+浏览器 | ★★★★★ 原生 Act SDK,跨任意桌面应用 | 无,需自叠代理 | 云 + Enterprise 自托管 | Free;Basic $29;Pro $99;compute 小时 + $0.04/step | ★★★★★(托管首选) |\n| [trycua / cua](https://github.com/trycua/cua) | 开源完整桌面(mac/Linux/Win/Android)+云 | ★★★★★ 唯一覆盖 macOS | 自托管完全自控 | 本地(Apple Virt/QEMU)+ 云 | OSS 免费(MIT);云 by request | ★★★★★(自托管首选) |\n| [E2B Desktop](https://e2b.dev/pricing) | 托管完整 Linux 桌面,开源 | ★★★★★ 为 Computer Use 原生 | 无;Enterprise BYOC 自控 | 云 + BYOC/self-host | 1vCPU $0.05/h 按秒 | ★★★★★ |\n| [Bytebot](https://github.com/bytebot-ai/bytebot) | 开源自托管 AI 桌面 agent(容器) | ★★★★★ 含 agent loop + 桌面 + UI | 自托管自控,无开箱 stealth | 纯自托管 docker compose | 免费(Apache-2.0)+ token | ★★★★★(自托管 MVP) |\n| [Anthropic Computer Use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool) | 模型能力 + Docker 参考实现 | ★★★★★ 协议/loop 源头 | 无,全 DIY | 本地/云 Docker | 仅 Claude token;header `computer-use-2025-11-24` | ★★★★★(必备「大脑」) |\n| [Kernel](https://www.kernel.sh/) | 浏览器云,强持久化 | ★★★ 浏览器级 | ★★★★ 持久 profile + stealth + 住宅代理 | 仅云 | Free;Hobbyist $30;headless ≈$0.06/h | ★★★★(多账号持久) |\n| [Browser Use Cloud](https://browser-use.com/pricing) | AI 浏览器 agent + CDP 云,核心开源 | ★★★ stealth 浏览器 | ★★★★ stealth ~81% + 住宅代理 | 云 + 自托管 | Free;Dev $29;会话 $0.02/h 最低 | ★★★★(高风控 web) |\n| [Steel.dev](https://steel.dev/) | 开源浏览器云 API | ★★★ 浏览器级 | ★★★ 代理 + 指纹 + CAPTCHA | 云 + 自托管 | Launch Free($30 credits);Scale $250 | ★★★(自托管 web) |\n| [Hyperbrowser](https://www.hyperbrowser.ai/) | 浏览器云,强反检测 | ★★ | ★★★★ ultra stealth + 旋转住宅 | 仅云 | 会话 $0.10/h;Startup $30 | ★★★(强反爬站点) |\n| [Anchor Browser](https://anchorbrowser.io/) | 安全云浏览器(偏合规) | ★★ | ★★★ 分档,全 stealth 在 $2000 档 | 云 + Enterprise on-prem | Free;Starter $50;使用 $0.09/h | ★★(合规多账号) |\n| [Skyvern](https://www.skyvern.com/) | 开源 Vision-LLM 浏览器工作流 | ★★ web 工作流 | 无突出 | 云 + 自托管(AGPL) | Free 5000 credits;step ~$0.05 | ★★(AGPL 谨慎) |\n\n**点评:** 桌面层「托管 vs 自控」两极:快速起步用 **Scrapybara / E2B Desktop**(跨实例保存登录态、pause/resume);长期降本 + 每账号静态 IP + 无锁定迁到 **cua / Bytebot** 自托管。Web 高风控层用 **Browser Use**($0.02/h + 81% stealth)做注册/登录,多账号长期持有用 **Kernel** 的持久 profiles(会话结束自动回写 cookie——几乎为 founder-agent 量身定制)。许可:MIT(cua/Steel)与 Apache-2.0(Bytebot/E2B)商用友好;**Skyvern 是 AGPL-3.0,闭源商用须评估 copyleft**。\n\n---\n\n### 2.3 防封 / 静态·住宅 IP / 代理 / 验证码\n\n| 选项 | 类型 | 静态 IP·防封 | 部署 | 定价(已核实 Jun 2026) | 推荐度 |\n|---|---|---|---|---|---|\n| [Bright Data](https://brightdata.com) | 代理网络 + 托管解封 | ★★★★★ 195 国独享 ISP IP + Web Unlocker | 云 | 独享 ISP $2.5-3.5/IP;住宅 PAYG $8/GB | ★★★★(行业标杆) |\n| [Oxylabs](https://oxylabs.io) | 企业级代理 | ★★★★ 优质 ASN ISP,带宽不限 | 云 | ISP $1.2-1.6/IP(默认半独享须升独享) | ★★★★ |\n| [Decodo (前 Smartproxy)](https://decodo.com) | 性价比中端代理 | ★★★★★ 100% 独享 ISP,3 种计费 | 云 | ISP 独享 $2.5-3.33/IP;14 天退款 | ★★★★★(规模化默认) |\n| [IPRoyal](https://iproyal.com) | 预算友好代理 | ★★★★ 独享 ISP 不限流量,住宅流量永不过期 | 云 | ISP from $1.8/proxy;住宅 from $1.75/GB | ★★★★★(低频多身份) |\n| [SOAX](https://soax.com) | 统一额度池(住宅/移动/ISP) | ★★★ 移动 IP 信任度最高 | 云 | Starter $90/25GB → $0.32/GB(企业) | ★★★(特殊高风控目标) |\n| [CapSolver](https://www.capsolver.com) | AI 验证码识别 | 挑战层(非 IP) | 云 API + 扩展 | reCAPTCHA v2 $0.8/1k;Turnstile/CF $1.2;DataDome $2.5 | ★★★★★(验证码主力) |\n| [2Captcha](https://2captcha.com) | AI+人工混合验证码 | 挑战层(非 IP) | 云 API | reCAPTCHA v2 $1-2.99/1k(覆盖 Arkose/FunCaptcha) | ★★★★(冷门兜底) |\n| [Multilogin](https://multilogin.com) | 防关联浏览器(指纹最强) | ★★★★★ 一流指纹 + 捆绑住宅代理 | 本地 + 云 | Pro 10 $11/mo;Business $89/mo 起 | ★★★★(指纹要求最高) |\n| [AdsPower](https://www.adspower.com) | 防关联浏览器(预算 + 自动化首选) | ★★★★ 指纹隔离 + 官方 MCP + headless | 本地 + 云 | Pro ~$5.4/mo(年付 10 profiles);BYO 代理 | ★★★★★(MCP 原生最契合) |\n| [GoLogin](https://gologin.com) | 防关联浏览器(真云浏览器) | ★★★★ 云浏览器免自建 VM + 2GB 代理 | 本地 + 云 | Professional $24/mo(100 profiles) | ★★★(免自建 VM) |\n| [Browserbase](https://www.browserbase.com) | AI-agent 云浏览器(防封 + 持久一体) | ★★★ Contexts 持久登录 + 自动验证码 + 代理 | 纯云 | Developer $20;Startup $99;$0.10-0.12/h | ★★★★(全托管最省运维) |\n\n**点评:** **持久身份的正确原语 = 独享静态 ISP 代理(非轮换)**,= 数据中心速度 + 住宅信任 + 固定 IP,最适合养号。规模化首选 **Decodo**(200 IP @ $2.5)或 **IPRoyal**(低频身份、流量永不过期)。代理对 Computer Use 透明,配在 VM/profile 上即自动继承。防关联浏览器解决「同机多账号不被关联」,与 IP 防封正交,agent 友好度:**AdsPower(官方 MCP + Local API + headless,Claude 自然语言驱动)> GoLogin > Multilogin(指纹最强但贵)**。验证码做兜底层:**CapSolver 主 + 2Captcha 备**(API 兼容,零成本切换)。托管解封器(Bright Data Web Unlocker)会**轮换 IP,只能做无状态只读采集,绝不能用在登录态账号上**。\n\n---\n\n### 2.4 本地 / 自托管 VM(支持 Computer Use)\n\n| 选项 | 类型 | Computer Use | 静态 IP·防封 | 部署 | 定价 | 推荐度 |\n|---|---|---|---|---|---|---|\n| [Bytebot](https://github.com/bytebot-ai/bytebot) | turnkey 自托管 computer-use 桌面 agent | ★★★★★ agent loop + 桌面 + 邮件 + UI | 家庭/办公住宅 IP 免费,需自加代理轮换 | docker compose / Helm k8s | 免费(Apache-2.0)+ Claude token | ★★★★★(最快 turnkey) |\n| [trycua/cua + Lume](https://github.com/trycua/cua) | VM 群编排 + agent SDK(Apple Silicon 原生) | ★★★★★ 含 macOS guest,MCP 原生 | 本地住宅 IP;云为数据中心 | 本地 + 云/BYOC | OSS 免费(MIT);云未公开定价 | ★★★★★(Mac VM 群) |\n| [Anthropic quickstart](https://github.com/anthropics/anthropic-quickstarts/tree/main/computer-use-demo) | 参考 Docker 镜像 + 最佳实践 kit | ★★★★★ 协议源头 | 无,自建 | 本地 docker run / macOS | 免费 + Claude token | ★★★★★(参考 payload) |\n| [Kasm Workspaces](https://kasm.com/) | 容器流送/DaaS 平台(自托管) | ★★★ 提供隔离桌面,无 LLM loop | 自有基础设施每节点出口 | 自托管 + SaaS | CE 免费(≤5 并发非商用);Starter ~$5-10/user | ★★★★(成熟多租户平台) |\n| [QEMU/KVM + libvirt](https://www.qemu.org/) | 裸金属 hypervisor(最强隔离) | ★★★★ 全 VM 桌面 | ★★★★★ 每 VM bridged 独立 MAC/IP | 本地/自托管 Linux | 免费(GPL)+ 硬件电费 | ★★★★(成本底线 + 隔离上限) |\n| [Apple container](https://github.com/apple/container) | macOS 原生 Linux 容器(每容器 micro-VM) | ★★★ 跑桌面镜像 | ★★★★ 每容器独立 LAN IP(macOS 26) | 仅本地 Apple Silicon | 免费(Apache-2.0,v1.0 2026-06) | ★★★★(Mac 新稳定底座) |\n| [UTM](https://mac.getutm.app/) | Mac VM app(QEMU + Apple Virt 前端) | ★★★ GUI 桌面 | 默认 Mac IP(住宅) | 仅本地 Mac | 免费;App Store 付费便利版 | ★★(仅原型/调试) |\n| [Daytona(自托管)](https://github.com/daytonaio/daytona) | AI 代码执行沙箱(headless 为主) | ★ headless 偏向,非 GUI | 无 | 自托管 k8s | OSS 免费;云定价未公开 | ★(本维度差,OSS 维护存疑) |\n\n**点评:** 心智模型 = **PAYLOAD(agent loop + 桌面)+ PLATFORM(每 session 起一个)**。Payload 选 **Bytebot**(最 turnkey:含 Thunderbird 邮件 + Firefox + VS Code + 任务 UI)或 Anthropic 参考镜像。Platform 扇出选 **cua/Lume**(Mac 原生 + macOS guest)、**QEMU/KVM**(最省 + 最强隔离 + 每 VM bridged 静态 IP)、或 **Apple container**(v1.0,每容器独立 IP)。**自托管的隐藏优势:家庭/办公 LAN 出口是反 bot 系统信任的真实住宅 ISP IP**。跨会话持久化靠快照模式:配好一台登录态桌面 → 快照 → 每 session fork = 启动即已认证。**macOS guest 仅 Apple Silicon + Virtualization.framework,且 SLA 上限约每物理 Mac 2 个**——除非必须用 Mac-only 应用,默认 Linux 桌面。\n\n---\n\n### 2.5 多 Agent 编排(基于 Claude Code)\n\n| 选项 | 类型 | Computer Use | 静态 IP·防封 | 部署 | 凭证 | 推荐度 |\n|---|---|---|---|---|---|---|\n| [Claude Agent SDK](https://code.claude.com/docs/en/agent-sdk/subagents) | 官方 SDK / 编排原语 | ★★★★ computer-use 工具 + 14 内置工具 | secure-deployment 出站代理模式 | both(TS/Py/Go) | **唯一原生吃 API key + 订阅 OAuth** | ★★★★★(自建内核) |\n| [Claude Managed Agents](https://platform.claude.com/docs/en/managed-agents/self-hosted-sandboxes) | 官方托管编排 + 沙箱 + 持久会话 | ★★★★ 沙箱内标准工具 + computer-use | ★★★★★ 自托管沙箱出网你说了算 | both(Anthropic 云 / 自有 VPC) | 仅 API key(无订阅) | ★★★★★(最省事托管) |\n| [Agent Teams](https://code.claude.com/docs/en/agent-teams) | 官方实验多会话团队 | 继承 Claude Code | 网络无关 | local(终端,需 tmux/iTerm2) | 按 lead 凭证 | ★★★(原型/人在环路) |\n| [Trellis](https://github.com/mindfold-ai/Trellis) | 多平台工作流 harness(本仓已用) | 取决于底层 agent | 网络无关 | both | 多 provider,沿用底层凭证 | ★★★★(现成骨架,AGPL) |\n| [OpenClaw](https://docs.openclaw.ai/concepts/oauth) | 第三方 agent 网关 / OAuth token-sink | 取决于底层 | 建议配独立账号 + 静态 IP | both | 跨 Claude+Codex 管 API key + OAuth | ★★★(凭证维度) |\n| [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/multi_agent/) | 厂商 SDK / handoffs | ★★★ ComputerTool | 网络无关 | both | Codex 订阅或 API key | ★★★(多 provider OpenAI 侧) |\n| [LangGraph](https://www.langchain.com/langgraph) | 通用有状态图运行时 | 可接节点 | 网络无关 | both | 偏 API key | ★★★(跨 provider 长周期有状态) |\n| [Git-worktree 扇出](https://code.claude.com/docs/en/worktrees) | 并行隔离模式(非产品) | N/A | N/A | both | 沿用当前会话 | ★★★★(底座) |\n| [ruflo(前 claude-flow)](https://github.com/ruvnet/ruflo) | Agent meta-harness / swarm | 取决于底层 | 网络无关 | both | 订阅支持存疑 | ★★(参考,重写期风险) |\n\n**点评:** **CEO→部门→执行者** 直接用 Agent SDK 的 `agents` 参数表达(逐 agent 指定 model/effort/tools/权限/memory,5 层嵌套,`resume(session_id+agentId)` 可恢复),超大规模升级到 **Workflow 工具**(后台 JS 脚本,单 run ≤16 并发/≤1000 agent)。Agent SDK 是**唯一原生同时吃 API key 与订阅 OAuth token 的编排内核**。若不想自建持久化 + 沙箱,升级到 **Managed Agents**(把跨会话持久 + per-session 隔离 + 出网自控一次解决)。**「静态 IP + 账号注入」有官方通用落地模式**:agent 关进容器 `--network none`,全部出网经一台静态 IP 宿主上的出站代理(Envoy credential_injector / Squid / LiteLLM),代理注入凭证 + 域名白名单——一招同时给稳定出口 IP + agent 永不接触凭证。\n\n---\n\n### 2.6 Agent 身份 / 账号注入\n\n| 选项 | 类型 | 防封价值 | 部署 | 定价(已核实) | 推荐度 |\n|---|---|---|---|---|---|\n| [AgentMail](https://www.agentmail.to/pricing) | 虚拟邮箱(per-agent 收件箱) | 自定义域名 DKIM/SPF/DMARC 过表单校验 | 云 + BYO 域名/BYOC | Free;Developer $20;Startup $200(150 inbox,~$1.33/inbox) | ★★★★★(邮件身份) |\n| [MailSlurp](https://www.mailslurp.com/product/email-address-api/) | 虚拟邮箱 + SMS API | catch-all 域名背海量别名 | 云 | Start free;付费仅 in-app(未核实) | ★★★★(邮件+SMS 合并) |\n| [5sim](https://5sim.net/) | SMS 验证(临时号) | 风险项:回收 VOIP 易被封 | 云 API | PAYG ~$0.01/号 | ★★(一次性低风险) |\n| [SMS-Activate](https://sms-activate.io/) | SMS 验证(临时号) | 同上,rental 模式略好 | 云 API | PAYG ~$0.05+/号 | ★★(一次性,与 5sim 互备) |\n| [Twilio Verify + 号码](https://www.twilio.com/en-us/verify/pricing) | 自有号码 + 合法验证 | 持久 2FA 好,但识别为 VOIP | 云 | Verify $0.05/次;长号 ~$1.15/mo + A2P 登记 | ★★★(持久业务线) |\n| [Privacy.com](https://agents.privacy.com/) | 虚拟卡(turnkey,授权层硬上限) | 真卡号过商户校验 + 商户锁定 | 云 + API/CLI/MCP | 消费级分层;美国银行账户 | ★★★★(美国 turnkey + MCP today) |\n| [Stripe Issuing for Agents](https://docs.stripe.com/issuing/agents) | 虚拟卡(程序化 + 策略门控) | 单用即焚卡 + 实时授权 webhook | 云 + sandbox | 无 setup,定价 sales-gated | ★★★★★(规模化支付主干) |\n| [Crossmint](https://www.crossmint.com/solutions/agentic-payments) | 全球卡 + 钱包 + 稳定币 | 真 Visa + 钱包级限额 + 白名单 | 云,全球 150+ 国 | sales-gated | ★★★★(国际 + 机器对机器) |\n| [Anon](https://www.anon.com/) | 账号注入(托管认证会话) | 持久真实会话避免反复登录触发风控 | 云 SDK | sales-gated | ★★★★(跨会话/重启保持登录) |\n| [Infisical](https://infisical.com/pricing) | Secrets 管理(开源、可自托管) | per-agent machine identity 隔离 | both(自托管 / 云) | Free 自托管无限 machine identity;Pro $18/identity | ★★★★★(注入主干) |\n| [Doppler](https://www.doppler.com/pricing) | Secrets 管理(SaaS,最快注入) | service token/account 限爆炸半径 | 云优先(自托管仅 Enterprise) | Free 3 user;$8/user;dynamic/self-host 仅 Enterprise | ★★★(小试/非敏感) |\n| [1Password Secrets Automation](https://www.1password.dev/secrets-automation/) | Secrets(基于 1Password vault) | Connect 可自托管缓存 | both | 含 1Password Business 订阅 | ★★★(已用 1Password) |\n\n**点评:** 分三层而非一层:**(1) 身份 SOURCES** 铸造新身份(邮件 AgentMail/MailSlurp;手机 5sim/Twilio;卡 Stripe/Privacy/Crossmint);**(2) Secrets VAULT 注入主干**(自托管 **Infisical** MIT 核心:无限免费 machine identity + agent injector,所有账号留自有基础设施;cloud Pro $18/identity 在规模上不可行,故自托管几乎是必须;**修正:dynamic 短时密钥不免费,ee/ 目录需企业 license**);**(3) SESSION 注入层**([Anon](https://www.anon.com/) 跨会话/VM 重启保持登录,token 服务端注入永不进 LLM context)。**邮件是最易做可信且最便宜的一环——铁律:用自定义域名,绝不用 temp-mail(本身就是封禁信号)**。**手机/SMS 是可信身份最弱一环**:回收 VOIP 临时号只能过一次性低风险门,业务账号长期 2FA 须用自有 Twilio 号或真实 eSIM。**支付的决定性安全属性 = 授权前硬上限**:**Stripe Issuing for Agents** 的单用即焚卡 + 实时 `issuing_authorization.request` webhook 是规模化主干,**Privacy.com**(MCP today)是美国 turnkey 最快路径,**Crossmint** 是唯一全球 + 支持 x402/AP2 机器对机器协议。\n\n---\n\n## 3. Foundagent 推荐技术栈组合\n\n> 关键认知:**「需要每身份固定 IP」是选自托管的决定性理由**;**「最省运维」是选云端的理由**。两套都把 Anthropic Computer Use(Opus 4.8,`computer-use-2025-11-24`)作为「大脑」,把 secure-deployment 出站代理作为账号注入 + 静态 IP 的统一落地模式。\n\n### 栈 A —— 云端优先(最省运维,快速起步)\n\n| 层 | 选型 | 理由 |\n|---|---|---|\n| 编排内核 | **[Claude Managed Agents](https://platform.claude.com/docs/en/managed-agents/self-hosted-sandboxes)**(自托管沙箱模式)+ API key | 服务端持久 pause/resume 会话 + per-session 沙箱 + 出网自控一次解决;每个 founder session = 一个持久会话 |\n| 桌面 Computer Use | **[E2B Desktop](https://e2b.dev/pricing)** 或 **[Scrapybara](https://scrapybara.com/)** | 开箱完整 Linux 桌面,跨实例保存登录态;E2B 按秒计费在并发下最省 |\n| Web 强 stealth 层 | **[Kernel](https://www.kernel.sh/)**(持久 profiles)+ 高风控用 **[Browser Use](https://browser-use.com/pricing)** | 持久 profile 自动回写登录态;Browser Use $0.02/h + 81% stealth |\n| 静态 IP / 防封 | **[Decodo](https://decodo.com)** 独享 ISP IP(每身份一个)+ **[CapSolver](https://www.capsolver.com)** 验证码 | 独享非轮换 ISP = 每账号固定出口;挂沙箱出网代理 |\n| 账号注入 | 邮件 **[AgentMail](https://www.agentmail.to/pricing)** + Secrets **[Infisical](https://infisical.com/pricing)**(云)+ 支付 **[Stripe Issuing for Agents](https://docs.stripe.com/issuing/agents)** + 会话 **[Anon](https://www.anon.com/)** | 每身份自定义域名邮箱 + 单用即焚卡 + 持久登录 |\n| 订阅 token 负载 | Agent SDK / Claude Code(订阅 OAuth)另跑有界推理任务 | Managed Agents 不吃订阅,故订阅额度走旁路 |\n\n**成本量级(每 founder-agent/月,粗算):** Managed Agents 运行时 $0.08/session-hour(常驻 ≈$58/mo,**强烈建议事件驱动、空闲即关 session**)+ token(子 agent 扇出 ≈7x 单会话)+ 独享 ISP IP $2.5 + 邮箱 ~$1.33 + 验证码 ~$0(按量近忽略)+ Stripe 按交易。**结论:运行时与 token 是大头,靠「空闲关 session + 子阶段路由 Sonnet/Haiku + prompt caching」控本。**\n\n### 栈 B —— 本地/自托管(规模化最省钱,每身份固定 IP + 无锁定)\n\n| 层 | 选型 | 理由 |\n|---|---|---|\n| 编排内核 | **[Claude Agent SDK](https://code.claude.com/docs/en/agent-sdk/subagents)**(subagents + Workflow) | 双凭证内核;CEO→部门→执行者 = 非 Claude broker 起兄弟容器,每 agent 一隔离容器自跑 `claude -p` |\n| VM Platform | **[QEMU/KVM](https://www.qemu.org/)**(Linux 机)或 **[cua/Lume](https://github.com/trycua/cua)**(Mac mini,需 macOS guest 时) | 每 VM bridged 独立 IP,快照 fork = 启动即认证;成本 ≈ 电费 |\n| 桌面 Payload | **[Bytebot](https://github.com/bytebot-ai/bytebot)**(Apache-2.0,含邮件 + 浏览器 + UI)以 Claude 为 planner | 一条 docker compose 起完整 founder 桌面,Helm/k8s 扇出 |\n| Web 强 stealth 层 | **[Browser Use](https://browser-use.com/pricing)** 核心库(自托管)或 **[Steel.dev](https://steel.dev/)**(MIT 自托管) | 自托管 = 自建每账号出口 IP,高风控登录稳健 |\n| 静态 IP / 防封 | **[Decodo](https://decodo.com)** / **[IPRoyal](https://iproyal.com)** 独享 ISP IP + **[AdsPower](https://www.adspower.com)** 防关联(官方 MCP)+ **[CapSolver](https://www.capsolver.com)** | 每身份固定出口 + 指纹隔离;AdsPower MCP 让 Claude 自然语言驱动 profile;**家庭/办公住宅 IP 出口是额外防封优势** |\n| 账号注入 | 自托管 **[Infisical](https://infisical.com/pricing)** MIT 核心(无限免费 machine identity)+ 快照固化登录态 + **[Anon](https://www.anon.com/)** | 所有账号留自有基础设施;启动注入 env/挂载 |\n| 凭证 | API key(生产)+ 订阅 OAuth token(Claude Code 底层即同时用) | 双凭证,订阅仅用于额度可控的有界负载 |\n\n**成本量级(每 founder-agent/月,粗算):** VM compute ≈ 电费(owned hardware 单 session 趋近 0)+ 独享 ISP IP $1.8-2.5 + 邮箱 ~$1.33 + 验证码 ~$0 + Claude token(主要支出)。**高并发下显著低于云端,代价是自建编排/沙箱/IP 工程与运维。**\n\n---\n\n## 4. 关键风险与开放问题\n\n1. **封号 / ToS 风险(最高优先级)。** 「像创始人一样经营生意」要的是**稳定身份**(账号、声誉、登录态),与「暴力解封/轮换住宅 + 临时号」根本冲突。回收 VOIP 临时号、temp-mail 域名、托管解封器轮换 IP 都是封号信号。**主链路必须是「每 agent 一个独享 ISP IP + 防关联 profile/持久 Context + 自定义域名邮箱 + 验证码兜底」;解封器仅作旁路只读采集。** 规划「优雅的账号轮换与丢失」,而非完美规避。\n\n2. **KYC / 合规是身份独立性的结构性天花板。** 所有支付选项最终都绑你的法人/银行账户——**无法在规模上铸造真正独立的金融身份**(Stripe/Privacy/Crossmint 给的是每 agent 范围预算,非独立持卡人)。叠加 2025-26 收紧的合成身份检测,这是产品边界,不是工程问题。\n\n3. **成本随 agent 数量扩展。** 子 agent/团队扇出 ≈7x token;Managed Agents 叠加 $0.08/session-hour(N 个常驻 ≈ N×$58/mo 仅运行时);住宅代理 $5-12/GB 常是隐藏大头;Doppler/Infisical cloud 按 identity 计价在 fleet 规模上致命。**控本杠杆:owned hardware 自托管 VM、空闲即关 session、子阶段路由 Sonnet/Haiku、独享 ISP 取代按 GB 住宅代理、自托管 Infisical 取代云。**\n\n4. **订阅 token 管理(已变天)。** `setup-token` 发 1 年期 `CLAUDE_CODE_OAUTH_TOKEN`,**无自动刷新、到期即断**([anthropics/claude-code #12447](https://github.com/anthropics/claude-code))——不适合无人值守长跑;2026-06-15 起订阅经程序化/第三方 agent 用量先扣 Agent SDK credits 再按 API 费率计。**生产用 API key + Managed Agents,订阅仅用于额度可控的有界推理。**\n\n5. **沙箱隔离强度。** Bytebot/Anthropic 参考镜像是容器(共享宿主内核,Anthropic 警告须跑在专用 VM 内),处理不可信 web 动作有 prompt-injection 风险——生产用 QEMU/KVM 全 VM 或 Apple container micro-VM 隔离。\n\n6. **待核实项(预算前确认):** MailSlurp 付费定价(in-app gated)、cua Cloud 按分钟费率(未公开)、Stripe/Crossmint/Anchor on-prem 的 sales-gated 价格、Northflank/Blaxel 厂商自述数据(未独立核实)、Daytona OSS 维护状态。\n\n---\n\n## 5. 建议的下一步(MVP 最小可跑通路径)\n\n**目标:1 周内跑通「单个 founder-agent 在隔离桌面里用 Computer Use,带固定出口 IP,持有 1 个自定义域名邮箱 + 1 张限额卡,完成一次真实业务动作(如注册一个 SaaS 并发一封邮件)」。**\n\n1. **桌面 Payload(Day 1-2):** 本地一条 `docker compose` 起 **[Bytebot](https://github.com/bytebot-ai/bytebot)**,把 Claude(Opus 4.8)设为 LiteLLM planner,验证 Computer Use 能在 Firefox/Thunderbird 里读邮件、点击、填表。\n\n2. **固定出口 IP + 防封(Day 2-3):** 买 1 个 **[Decodo](https://decodo.com)** 或 **[IPRoyal](https://iproyal.com)** 独享 ISP IP,配在 Bytebot 容器出网;接 **[CapSolver](https://www.capsolver.com)** 作验证码工具(MCP/函数)。验证从该固定 IP 出网且能解一次 reCAPTCHA。\n\n3. **身份注入(Day 3-4):** 注册 1 个自定义域名,在 **[AgentMail](https://www.agentmail.to/pricing)** 开 1 个 `founder@yourbrand.com` 收件箱(MCP server 让 Claude 直接读 OTP);自托管 **[Infisical](https://infisical.com/pricing)** MIT 核心存该身份的邮箱密码/API key,启动注入容器;开 1 张 **[Privacy.com](https://agents.privacy.com/)**(美国,MCP today,最快)或 Stripe Issuing 限额卡。\n\n4. **跑通一次业务动作(Day 4-5):** 让 agent 在桌面里完成「注册某 SaaS → 读 AgentMail OTP → 用限额卡付费 → 发一封确认邮件」全流程,验证账号注入 + 固定 IP + 验证码兜底 + 支付硬上限闭环。\n\n5. **持久化 + 编排(Day 5-7):** 对配好登录态的容器/卷做**快照**,验证「fork 后启动即已认证」;用 **[Claude Agent SDK](https://code.claude.com/docs/en/agent-sdk/subagents)** 的 `agents` 参数写一个最小 CEO→1 个 sub-agent 委派,确认 `resume(session+agentId)` 跨会话续跑。\n\n**MVP 之后的演进路线:** 跑通后,把 Bytebot fleet 用 Helm 扇到 owned hardware(QEMU/KVM 或 Mac mini cua/Lume)拿到「每身份固定 IP + 边际成本 ≈ 电费」;或若要最省运维,迁到 **[Claude Managed Agents](https://platform.claude.com/docs/en/managed-agents/self-hosted-sandboxes)** 自托管沙箱模式把持久化/隔离/出网交给官方。无论哪条路,**secure-deployment 出站代理(注入凭证 + 域名白名单 + 固定 IP)都应作为账号注入与防封的默认架构**。",
    "dimensions": [
      {
        "dimension": "云端 Agent 专用 VM / Sandbox",
        "options": [
          {
            "name": "E2B (Sandbox + E2B Desktop)",
            "url": "https://e2b.dev/pricing",
            "category": "Agent code-execution sandbox (Firecracker microVM) with a dedicated screen-based Computer-Use desktop flavor",
            "description": "Open-source-backed cloud sandbox on Firecracker microVMs, ~150ms cold start, per-session isolation. The open-source 'E2B Desktop' SKU (e2b-dev/desktop) gives a full Ubuntu + Xfce GUI streamed over VNC/noVNC with xdotool/scrot, purpose-built for screen-based Computer Use. Maintains official anthropic-computer-use and open-computer-use reference repos. Sandboxes support persistence/pause and custom images.",
            "pricing": "VERIFIED Jun 2026: Hobby free with $100 one-time credits, 20 concurrent, up to 1h sessions, 10 GiB storage. Pro $150/mo (24h sessions, 100 concurrent expandable to 1,100, 20 GiB storage). Per-second compute: vCPU $0.000014/s (1 vCPU) up to $0.000112/s (8 vCPU); RAM $0.0000045/GiB/s (~2 vCPU default ≈ $0.10/h). Enterprise custom (BYOC/self-host).",
            "computerUseSupport": "Best-in-class screen-based: E2B Desktop is a real Linux GUI desktop (sees screen, moves mouse, types) with official Anthropic Computer Use + OpenAI Operator demos. Can run arbitrary desktop apps, not just a browser.",
            "staticIpAntiBlock": "No native static-egress IP / residential proxy / CAPTCHA handling. Must layer a proxy yourself. Confirmed gap.",
            "deployment": "Cloud primary; self-host/BYOC on Enterprise; SDK is open source.",
            "pros": [
              "Only mainstream sandbox with a turnkey full GUI desktop for screen-based Computer Use",
              "Can run arbitrary desktop apps, not browser-only",
              "Fast microVM start (~150ms), generous $100 free credit",
              "Open-source SDK + self-host path limits lock-in"
            ],
            "cons": [
              "No built-in static IP / residential proxy / CAPTCHA — anti-block must be added separately",
              "$150/mo Pro base fee gates 24h sessions and higher concurrency",
              "Desktop sandboxes use more RAM/CPU than headless, raising per-hour cost",
              "No live-memory fork (only persistence/pause)"
            ],
            "relevanceToFoundagent": "Top pick for the screen-based Computer-Use requirement: a real Linux desktop per founder-agent that Claude drives directly, able to use any GUI app a business needs (not just a browser). Inject accounts via env/mounted files; persist a sandbox per business. The one gap is anti-block — pair with Kernel/Browserbase or a Fly static IP for sites that block datacenter ranges.",
            "verified": true
          },
          {
            "name": "AWS Bedrock AgentCore (Browser tool + Code Interpreter)",
            "url": "https://aws.amazon.com/bedrock/agentcore/pricing/",
            "category": "Managed AWS agent runtime: per-session isolated Browser tool (with OS-level actions) + Code Interpreter sandbox",
            "description": "AWS-managed agent primitives GA in 2026. The Browser tool gives a secure managed Chrome with a CDP WebSocket endpoint (Playwright connects as if local) PLUS, since Apr 2026, OS-level interaction beyond CDP: mouse (click/move/drag/scroll), keyboard (type/press/shortcuts), and full-desktop screenshots at OS coordinates — i.e. screen-based computer use inside the managed browser. Built-in Live View (real-time video feed embeddable via the TS SDK), session recording, CloudWatch metrics. Code Interpreter is a per-session isolated microVM for Python/JS. Browser Profiles persist cookies/localStorage to S3.",
            "pricing": "VERIFIED Jun 2026: consumption-based. Runtime/Code Interpreter $0.0895/vCPU-hr + $0.00945/GB-hr, billed per-second on ACTIVE CPU + peak memory; I/O wait and idle accrue no charge (1s minimum). Browser sessions: configurable timeout default 15min, max 8h; multiple concurrent. Browser Profiles billed at S3 Standard rates (from Apr 15 2026).",
            "computerUseSupport": "Strong managed-browser computer use: OS-level mouse/keyboard + full-desktop screenshots beyond CDP, plus Playwright/CDP and embeddable Live View. Not a general desktop for arbitrary non-browser apps.",
            "staticIpAntiBlock": "Custom browser supports custom network settings/IAM, but no documented residential proxy / stealth / CAPTCHA solving. Anti-block is a gap; egress runs in your AWS network.",
            "deployment": "Cloud-only on AWS (ties you to AWS, but that may be where business data/services already live).",
            "pros": [
              "Managed Computer-Use browser with OS-level actions + Live View + Playwright, no infra to run",
              "Idle/I/O-wait is free (consumption pricing) — ideal for a mostly-waiting founder agent",
              "Per-session microVM isolation; Browser Profiles persist auth (cookies) to S3",
              "Sits next to the business's real AWS infra (data, services, IAM)"
            ],
            "cons": [
              "No turnkey general desktop for non-browser apps",
              "No managed residential proxy / stealth / CAPTCHA — weaker anti-block",
              "12-component pricing is complex; AWS lock-in",
              "Cloud-only, no self-host"
            ],
            "relevanceToFoundagent": "Strong managed answer if the business lives on AWS: gives the founder-agent a Computer-Use browser (Playwright + OS-level clicks + Live View for human oversight) with cookie persistence for logged-in sessions, and an isolated Code Interpreter for non-browser work — all on idle-free pricing. Filling the anti-block gap (proxy/stealth) is still on you.",
            "verified": true
          },
          {
            "name": "Kernel (kernel.sh / onkernel)",
            "url": "https://www.kernel.sh/docs/info/pricing",
            "category": "Managed cloud browser infrastructure for web agents (headful Chromium-as-a-service) with turnkey anti-block",
            "description": "YC + $22M Series A browser-infra platform. Sub-150ms cold starts on managed headful browsers, persistent sessions (cookies/auth survive across invocations), Browser replays, live view, and a Computer Controls API. Native Playwright/Puppeteer/CDP. Stealth mode adds a managed default STATIC ISP proxy (static exit IP per session) plus an automatic CAPTCHA solver (reCAPTCHA + Cloudflare challenges); you can swap in your own residential proxy (rotating). Managed Auth handles logins.",
            "pricing": "VERIFIED Jun 2026: Developer free ($5/mo credit, 5 concurrent). Hobbyist $30/mo ($10 credit, 10 concurrent, adds replays/profiles/Managed Auth/file up-down). Startup $200/mo ($50 credit, 50 concurrent + 100 reserved, adds proxy config/extensions/pools/GPU). Per-second: headless $0.0000166667/s, headful $0.0001333336/s, headful+GPU $0.0008000016/s. Stealth mode + Computer Controls API included on ALL tiers; Managed Auth has no per-connection fee. Enterprise custom (HIPAA).",
            "computerUseSupport": "Browser-level computer use via a Computer Controls API on headful browsers, but it is a browser sandbox, not a full OS desktop (no arbitrary non-browser apps).",
            "staticIpAntiBlock": "Strongest TURNKEY anti-block here: stealth (on every tier) routes through a managed static ISP proxy with a static per-session exit IP and an automatic CAPTCHA solver; bring-your-own residential proxy supported (proxy config from Startup tier). Directly targets 'avoid blocks' + 'static IP'.",
            "deployment": "Cloud-only managed service (no self-host).",
            "pros": [
              "Turnkey anti-block: static-ISP-proxy stealth + CAPTCHA solving included on all tiers, no per-proxy fee",
              "Static per-session exit IP out of the box — fits the static-IP requirement without DIY",
              "Persistent auth/cookies + Managed Auth simplify many injected accounts",
              "Native Playwright/Puppeteer/CDP, sub-150ms, pay only for active browser time"
            ],
            "cons": [
              "Browser-only — cannot run a general desktop OS or non-browser tooling",
              "Cloud-only, no self-host",
              "Proxy CONFIG (BYO residential) and pools gated to the $200 Startup tier",
              "Newer company; scale less proven than hyperscalers"
            ],
            "relevanceToFoundagent": "Best fit for the web-interaction + anti-block + injected-accounts slice: signups, dashboards, marketplaces on sites that block datacenter IPs. Stealth's static ISP exit IP plus CAPTCHA solving and Managed Auth covers 'static IP / avoid blocks / many logged-in accounts' with almost no setup. Pair with E2B Desktop/AgentCore for non-browser desktop work.",
            "verified": true
          },
          {
            "name": "Browserbase (Stagehand)",
            "url": "https://www.browserbase.com/pricing",
            "category": "Managed cloud headless/headful browser infrastructure for web agents (Kernel's main rival)",
            "description": "Mature browser-as-a-service for AI agents with CDP access, Stagehand automation framework, session recording/live view, persistent contexts for auth, BYO or bundled proxies, and stealth + CAPTCHA solving on paid tiers. Broad framework support (Playwright/Puppeteer/Stagehand).",
            "pricing": "VERIFIED Jun 2026: Free (1 concurrent browser, 1 browser-hr, 15min/session, 7-day retention). Developer $20/mo (25 concurrent, 100 browser-hrs, 1GB proxy; overage $0.12/browser-hr, $0.0000167/GB-s, $12/GB proxy). Startup $99/mo (100 concurrent, 500 browser-hrs, 5GB proxy; overage $0.10/browser-hr, $0.00001389/GB-s, $10/GB proxy). Scale custom. Basic Stealth + Auto CAPTCHA on paid tiers; Advanced Stealth only on Scale.",
            "computerUseSupport": "Browser-level computer use (Stagehand act/observe + CDP), not a full OS desktop. Good for screenshot-driven and structured web actions.",
            "staticIpAntiBlock": "Basic Stealth Mode + automatic CAPTCHA solving on paid tiers; bundled proxy GB + BYO proxies. Advanced (stronger) Stealth gated to the custom Scale tier — anti-block is real but the strongest mode is enterprise-only.",
            "deployment": "Cloud-only managed service.",
            "pros": [
              "Cheapest entry to managed stealth browsers ($20/mo Developer with 25 concurrent)",
              "Persistent contexts for saved auth; Stagehand simplifies agent web actions",
              "Bundled + BYO proxies; auto CAPTCHA solving on paid tiers",
              "Very mature, widely adopted, strong framework/ecosystem support"
            ],
            "cons": [
              "Browser-only, no general desktop or non-browser apps",
              "Strongest 'Advanced Stealth' locked behind custom Scale pricing",
              "Cloud-only, no self-host",
              "Proxy/stealth quality for the hardest sites may need the enterprise tier"
            ],
            "relevanceToFoundagent": "A cheaper, more mature alternative to Kernel for the web layer: persistent logged-in contexts (injected accounts), bundled proxies + CAPTCHA solving for moderate anti-block, at $20/mo. For sites with aggressive bot defense you may need Scale-tier Advanced Stealth or Kernel's static-ISP stealth. Pair with a desktop sandbox for non-browser tasks.",
            "verified": true
          },
          {
            "name": "Morph Cloud (Infinibranch)",
            "url": "https://cloud.morph.so/web/pricing",
            "category": "Snapshot/fork-first agent VM — live memory+disk+process branching",
            "description": "VMs whose differentiator is Infinibranch: snapshot, branch, and restore full VM state (memory + disk + running processes) in <250ms, with parallel branches sharing the parent's filesystem, packages, env, and process state. An agent can fork a running VM into parallel copies (~250ms) to explore multiple paths without restarting. Browser-based access; VSCode/Cursor/tmux integration; 'Devboxes' are the persistent dev environments.",
            "pricing": "VERIFIED Jun 2026: usage via Morph Compute Units (MCU) at $0.05/MCU. 1 MCU = 1 vCPU-hr + 4GB RAM-hr + 16GB disk-hr, OR 5TB snapshot-hr. Free 300 MCU/mo (8 concurrent / 32 total). Developer $40/mo (1,000 MCU, 32 concurrent). Team $250/mo (7,500 MCU, 128 concurrent). [Correction: tier is 'Team', not 'Scale'.]",
            "computerUseSupport": "Not a packaged Computer-Use GUI; full VM where you can install a desktop/VNC yourself. No turnkey desktop documented.",
            "staticIpAntiBlock": "No static-IP / proxy / anti-block feature documented. Confirmed gap.",
            "deployment": "Cloud (cloud.morph.so). Sandbox SDK has a self-host/cloud option (custom pricing).",
            "pros": [
              "Unique live-memory fork: branch full memory+process+disk state in <250ms — checkpoint a working 'business' state and explore strategies cheaply",
              "Persistent long-running instances; resume exactly where left off",
              "Transparent MCU pricing with a usable 300-MCU free tier"
            ],
            "cons": [
              "No turnkey Computer-Use desktop — must build GUI/VNC yourself",
              "No native static IP / anti-block",
              "Smaller provider; self-host SDK pricing opaque",
              "No managed account-injection layer"
            ],
            "relevanceToFoundagent": "The standout for persistence + checkpoint/fork: snapshot the entire running business VM (processes + logged-in sessions in memory) and branch to A/B test strategies or recover from a bad action. Add a desktop layer for Computer Use and a proxy for anti-block. Best when 'time-travel/forking business state' is a core product feature.",
            "verified": true
          },
          {
            "name": "Daytona",
            "url": "https://www.daytona.io/pricing",
            "category": "General agent runtime / sandbox (isolated kernel, image snapshots, suspend/resume, multi-OS)",
            "description": "Runtime rebuilt for agents in 2025. Sub-90ms sandbox creation, dedicated kernel + filesystem + network stack per sandbox, suspend/resume, and image-based Snapshots (Docker/OCI templates: base OS + runtimes + packages). Shared Volumes for persistence; Docker-in-Docker, k3s, and GPU snapshots. Sandboxes can run indefinitely. Linux (root) and Windows confirmed; web terminal + browser VS Code; VNC is listed as a human-access tool.",
            "pricing": "VERIFIED Jun 2026: pure usage-based, no feature-gating subscription. $200 free credit + 5 GiB free storage. vCPU (Linux) $0.0504/hr (~$0.000014/s), vCPU (Windows) $0.0858/hr, RAM $0.0162/GiB/hr (after 5 GiB free), storage $0.000108/GiB/hr, GPU H100 $3.95/hr, RTX PRO 6000 $3.03/hr. Startup program (up to $50k credits) + Enterprise (SSO/audit/BYOC).",
            "computerUseSupport": "VNC access exists as a human tool, but no documented turnkey Computer-Use product; a screen-based desktop would be self-assembled. Multi-OS (Linux/Windows) with programmatic control.",
            "staticIpAntiBlock": "Per-sandbox network stack, but no documented static-egress IP / proxy / anti-block. Confirmed gap.",
            "deployment": "Cloud + BYOC (your own cloud) + enterprise on-prem.",
            "pros": [
              "Fastest fresh-start (sub-90ms); suspend/resume + indefinite-run sandboxes",
              "No subscription gating — pure pay-go, generous $200 credit; cheap vCPU ($0.0504/hr)",
              "Linux + Windows; BYOC/on-prem for the 'run locally or in your cloud' need",
              "Enterprise compliance (SSO/audit) for handling real business data"
            ],
            "cons": [
              "'Snapshots' are image templates, NOT live memory snapshots (no Morph-style live fork)",
              "No turnkey Computer-Use desktop (build VNC yourself)",
              "No native static IP / anti-block; macOS support not confirmed on current docs",
              "Account-injection plumbing left to you"
            ],
            "relevanceToFoundagent": "Strong all-round per-session isolation + persistence + BYOC foundation, cheap at scale, with Windows for breadth. Use as the primary work VM; add a DIY desktop (E2B-Desktop pattern) for Computer Use and a proxy/Kernel for anti-block. Note its snapshots are templates, so use Morph if you need live business-state forking.",
            "verified": true
          },
          {
            "name": "Cloudflare Sandboxes / Containers",
            "url": "https://blog.cloudflare.com/sandbox-ga/",
            "category": "Edge-distributed persistent agent sandbox with network-layer credential injection",
            "description": "GA April 2026. Each Sandbox is a persistent, isolated Linux 'real computer' (shell, filesystem, background processes) addressed by name — resumes if it exists, starts on demand. Disk-state snapshots stored in R2, auto-snapshot on idle, restore ~2s vs ~30s rebuild. PTY terminal over WebSocket (xterm.js), persistent Python/JS/TS code interpreter (Jupyter-like state). Two-tier: heavy Containers vs millisecond V8-isolate Dynamic Workers.",
            "pricing": "VERIFIED Jun 2026: charges only for ACTIVELY used CPU (no idle compute charge while waiting on the LLM). Concurrency: 15,000 lite / 6,000 basic / 1,000+ larger instances. Built on Workers/Containers billing; exact per-second container rates not published on this page (flag).",
            "computerUseSupport": "Real terminal + full Linux OS, but no GUI desktop / Computer-Use VNC; browser-driving would be Playwright-in-container, not screen-based.",
            "staticIpAntiBlock": "Standout for accounts: a programmable egress proxy injects credentials at the NETWORK layer so agent code never sees the token, with per-domain auth + dynamic network restriction. No residential/static-IP evasion for third-party sites (egress is for control, not evasion).",
            "deployment": "Cloud-only (Cloudflare global edge). No self-host.",
            "pros": [
              "Network-layer credential injection — best answer to 'inject many accounts safely' (agent never holds the secret)",
              "Per-domain egress policy = built-in guardrails on what the agent can reach",
              "Charges only active CPU + auto-idle disk snapshot — cheap for an always-on founder agent",
              "Massive concurrency, global edge, ~2s state restore"
            ],
            "cons": [
              "No GUI desktop for screen-based Computer Use",
              "No residential/static IP to evade site blocks",
              "Cloud-only; tied to the Workers ecosystem",
              "Exact at-scale container per-second pricing not pinned down"
            ],
            "relevanceToFoundagent": "Best control plane for safely injecting many accounts/credentials and constraining egress per domain — exactly the 'agent runs a business with many logins but must not leak secrets' need — plus cheap idle. Weak on screen-based Computer Use and on block-evasion; pair with E2B Desktop/Kernel for actuation.",
            "verified": true
          },
          {
            "name": "Fly.io Machines",
            "url": "https://fly.io/docs/about/pricing/",
            "category": "Low-level Firecracker microVM primitive with cheap native static IPs (build-your-own sandbox)",
            "description": "Raw Firecracker microVMs with full VM control, sub-second start/stop, per-second billing, and a global private WireGuard network with granular public/private routing. The primitive teams use to build their own agent sandbox infra (you control rootfs, networking, IPs). Stopped machines keep only rootfs storage.",
            "pricing": "VERIFIED Jun 2026: shared-cpu-1x/256MB ~$0.0028/h (~$2.02/mo); performance-1x/2GB ~$32.19/mo; extra RAM ~$5/GB/mo; stopped-machine rootfs storage $0.15/GB/mo. Dedicated IPv4 $2/mo; native static egress IP $0.005/h (~$3.60/mo, IPv4+IPv6). Egress $0.02/GB (NA/EU) to $0.12/GB (Africa/India); inbound + same-region free. ~40% compute discount on reserved blocks.",
            "computerUseSupport": "None out of the box — bare microVM. You install a desktop/VNC stack yourself.",
            "staticIpAntiBlock": "Best native static-IP story of the set: cheap dedicated IPv4 ($2/mo) and native static egress IPs (~$3.60/mo) — directly supports 'static IP to avoid blocks'. Datacenter ranges, so sophisticated sites can still block.",
            "deployment": "Cloud (Fly global regions). You fully own the VM image.",
            "pros": [
              "Cheap, first-class static/dedicated IPs — cleanest static-IP-per-agent model",
              "Full VM control (any OS image, any tooling, desktop+VNC if you build it)",
              "Sub-second microVM start, per-second billing, global regions, private networking",
              "Reservation discount makes always-on cheap at scale"
            ],
            "cons": [
              "Most assembly required — no agent SDK, no snapshot/fork, no Computer-Use desktop, no account injection",
              "Static IPs are datacenter, not residential — aggressive sites may still block",
              "Free tier discontinued; egress metered",
              "Operational/isolation-hardening burden on you"
            ],
            "relevanceToFoundagent": "The build-your-own foundation when you want cheap static datacenter IPs per founder-agent and full control. You add the Computer-Use desktop, snapshot logic, and account injection yourself — most effort, maximum control, cleanest static-IP-per-agent. Often paired with a residential-proxy/Kernel layer for the hardest-to-block sites.",
            "verified": true
          },
          {
            "name": "Vercel Sandbox",
            "url": "https://vercel.com/docs/sandbox/pricing",
            "category": "Firecracker microVM sandbox for untrusted/agent code, persistent-by-default, idle-free pricing",
            "description": "Compute primitive for safely running untrusted or AI-generated code on Vercel. Firecracker microVM per sandbox with its own filesystem + network, Amazon Linux 2023, node26/24/22 + python3.13 runtimes, root/sudo, and system-privileged processes (Docker, VPN, FUSE). Persistent sandboxes are the default (auto-save on stop, resume), plus manual Snapshots and Drives (beta) for shared persistent storage. JS/Python SDK + CLI.",
            "pricing": "VERIFIED Jun 2026: Active CPU $0.128/hr (I/O wait NOT billed), provisioned memory $0.0212/GB-hr, creations $0.60/1M, data transfer $0.15/GB, snapshot storage $0.08/GB-mo. Hobby free allotment (5 CPU-hrs, 420 GB-mem-hrs, 10 concurrent, 45min max). Pro: 2,000 concurrent, 24h max, $20/mo credit. Max vCPU 4/8/32 (Hobby/Pro/Ent). Only iad1 region.",
            "computerUseSupport": "No GUI desktop / Computer-Use; real Linux microVM (could run Playwright in-container, not screen-based).",
            "staticIpAntiBlock": "No static-egress IP / proxy / anti-block documented. Gap.",
            "deployment": "Cloud-only on Vercel; single region (iad1).",
            "pros": [
              "Persistent-by-default + snapshots + Drives — easy cross-session state for a long-lived agent",
              "Idle-free pricing (active CPU only, I/O wait free) — cheap for an LLM-waiting agent",
              "System-privileged (Docker/VPN/FUSE) and root access; fast millisecond start",
              "Clean SDK/CLI; drops into a Vercel-hosted product"
            ],
            "cons": [
              "No Computer-Use desktop, no static IP / anti-block",
              "Single region (iad1) limits latency/geo options",
              "Cloud-only, Vercel lock-in; max 32 vCPU",
              "Lower concurrency on free tier; 45min cap on Hobby"
            ],
            "relevanceToFoundagent": "Good idle-cheap, persistent work VM if the product already lives on Vercel: run the founder-agent's non-browser tooling/code with auto-resume across sessions. Add Kernel/Browserbase for web anti-block and E2B Desktop/AgentCore for Computer Use; not a standalone answer to the Computer-Use or static-IP needs.",
            "verified": true
          },
          {
            "name": "Modal Sandboxes",
            "url": "https://modal.com/docs/guide/sandbox",
            "category": "Python-first serverless sandbox, GPU-strong",
            "description": "Secure containers for executing untrusted user/agent code, defined at runtime. Filesystem persistence via Volumes plus Filesystem Snapshots for state across sessions, network tunnels / TCP connectivity, and configurable GPU (T4–B200). Python-first serverless platform; sandbox compute priced ~3x standard Modal compute. ~$300M ARR by 2026.",
            "pricing": "Usage per-second. CPU from ~$0.119/vCPU-hr (standard); sandbox CPU ~3x that. GPU per-second across T4–B200, billed separately for GPU+CPU+RAM. No published flat sandbox plan; exact sandbox rates not fully pinned (flag — not re-verified this round).",
            "computerUseSupport": "No turnkey desktop; an Anthropic-computer-use example runs the demo inside a Modal Sandbox, so a VNC desktop is buildable. Jupyter example exists.",
            "staticIpAntiBlock": "Network tunnels/TCP but no documented static-egress IP or anti-block. Gap.",
            "deployment": "Cloud-only.",
            "pros": [
              "Best GPU story (T4–B200) if the business needs model inference/training/media generation in-sandbox",
              "Filesystem snapshots + volumes for persistence; runtime-defined containers",
              "Mature, well-funded, strong Python ergonomics",
              "Documented path to run Anthropic Computer Use in-sandbox"
            ],
            "cons": [
              "Sandbox compute ~3x base rate — pricier for pure CPU agent work",
              "No native static IP / anti-block, no turnkey desktop",
              "Cloud-only, Python-centric",
              "Exact sandbox per-second pricing opaque"
            ],
            "relevanceToFoundagent": "Most relevant when the business needs GPU compute (generate media, run/fine-tune models). For pure web/Computer-Use founder work it is pricier and less specialized than E2B/Kernel. Best as an optional GPU worker, not the primary session VM.",
            "verified": true
          },
          {
            "name": "Northflank",
            "url": "https://northflank.com/blog/best-code-execution-sandbox-for-ai-agents",
            "category": "Production microVM sandbox + full app platform with BYOC",
            "description": "Production-grade microVM sandboxes with unlimited persistent session lengths, plus a full platform (databases, CI/CD, pipelines, observability) deployable into your own VPC (BYOC). GPU support (H100/A100) with all-inclusive pricing claimed ~62% cheaper than separately-billed competitors.",
            "pricing": "Pay-per-use on CPU/memory/storage; H100 ~$2.74/hr all-inclusive with VPC deployment. Exact sandbox per-second CPU/RAM rates not captured from a primary page (flag — vendor-sourced).",
            "computerUseSupport": "MicroVM can host a desktop/VNC if built; no documented turnkey Computer-Use product.",
            "staticIpAntiBlock": "BYOC lets you use your own cloud's IPs/egress, but no native residential/anti-block layer.",
            "deployment": "Cloud + BYOC into your own cloud account; strong enterprise/VPC story.",
            "pros": [
              "Unlimited persistent sessions + microVM isolation suit an always-on founder agent",
              "BYOC into your VPC = run in cloud you control, with DBs/CI/observability in one place",
              "Cheaper bundled GPU; production-platform features beyond a bare sandbox"
            ],
            "cons": [
              "No turnkey Computer-Use desktop or native anti-block/static-IP evasion",
              "Details mostly from Northflank's own blog — not independently verified (flag)",
              "More platform than minimal sandbox; heavier to adopt"
            ],
            "relevanceToFoundagent": "Good if you want one platform for the agent sandbox PLUS the business's real infra (databases, services) in your own VPC. Computer-Use and anti-block still need layering on.",
            "verified": false
          },
          {
            "name": "Blaxel",
            "url": "https://blaxel.ai/blog/best-cloud-sandboxes-ai-agents-2026",
            "category": "Agent sandbox with indefinite zero-cost standby + fast resume and fork",
            "description": "Sandboxes that stay in standby indefinitely with no compute charge (storage only) and resume in <25ms; supports forking. Memory-tier pricing rather than separate CPU/RAM rates.",
            "pricing": "Per-second by memory tier: XS 2GB $0.0828/hr, S 4GB $0.1656/hr, M 8GB $0.3312/hr, L 16GB $0.6624/hr, XL 32GB $1.3248/hr. No compute charge in standby (storage only). (Vendor-sourced — not independently verified.)",
            "computerUseSupport": "No documented turnkey Computer-Use desktop.",
            "staticIpAntiBlock": "No documented static IP / anti-block.",
            "deployment": "Cloud. No GPU sandboxes; weaker BYOC/compliance per comparisons.",
            "pros": [
              "Cheapest idle model: indefinite standby with $0 compute, <25ms resume — great for a mostly-waiting founder agent",
              "Simple memory-tier pricing, per-second billing, fork support"
            ],
            "cons": [
              "No GPU, weaker BYOC/compliance, no static IP/anti-block, no turnkey desktop",
              "Data sourced mainly from vendor blogs — not independently verified (flag)"
            ],
            "relevanceToFoundagent": "Attractive purely for cost of an always-on-but-mostly-idle agent (free standby, fast resume, fork). Lacks Computer Use and anti-block, so not a standalone answer.",
            "verified": false
          },
          {
            "name": "Coder (self-hosted CDE for agents)",
            "url": "https://coder.com/",
            "category": "Self-hosted/BYOC governed dev environments + agent orchestration",
            "description": "Self-hostable platform for cloud development environments and AI coding agents. Workspaces defined in Terraform, connected via WireGuard, auto-shutdown when idle. 'Coder Tasks' runs/manages AI agents with isolation, audit logging, and policy governance. Deployable in any cloud or fully air-gapped on-prem.",
            "pricing": "Open-source core (free, self-host) + enterprise/premium tiers (custom). You pay your own underlying cloud/compute.",
            "computerUseSupport": "IDE/workspace oriented; no turnkey Computer-Use desktop, though a workspace can host one.",
            "staticIpAntiBlock": "Uses your own infra's networking/IPs (you control egress); no native anti-block layer.",
            "deployment": "Self-hosted / any cloud / air-gapped on-prem — strongest 'run locally or in your own cloud' story.",
            "pros": [
              "Best fit for 'run locally/on-prem, fully controlled'; air-gap capable",
              "Open-source core, Terraform-defined per-session workspaces, strong governance/audit (useful when an agent handles real money/accounts)",
              "You own the network, so static IP is whatever your infra provides"
            ],
            "cons": [
              "Built for human/coding-agent dev workflows, not screen-based Computer Use or web anti-block out of the box",
              "Operational overhead of self-hosting; you assemble desktop, proxy, account injection",
              "Enterprise governance features are paid/custom"
            ],
            "relevanceToFoundagent": "The control-and-governance option: if Foundagent must run on your own infra with audit/policy over each agent's actions, Coder provides the isolation + orchestration shell. Computer Use, anti-block, and account injection are still DIY on top.",
            "verified": false
          }
        ],
        "keyInsights": [
          "No single provider covers every Foundagent need (per-session isolation + screen-based Computer Use + Playwright + injected accounts + static-IP/anti-block + local-or-cloud). The realistic design is a LAYERED stack: a desktop/OS sandbox for Computer Use (E2B Desktop, or DIY on Daytona/Fly/Vercel/Morph), a managed anti-block browser for blockable sites (Kernel or Browserbase, or AWS AgentCore Browser if on AWS), a credential-injection control plane (Cloudflare egress proxy), and cheap static IPs where needed (Fly.io).",
          "Computer Use comes in two flavors and you likely need both. (1) Full-OS screen-based desktop with arbitrary apps: only E2B Desktop ships turnkey (Ubuntu+Xfce+noVNC, official Anthropic/OpenAI repos); everyone else is DIY-VNC. (2) Managed browser with computer-use actions: AWS Bedrock AgentCore Browser now does OS-level mouse/keyboard + full-desktop screenshots beyond CDP, plus embeddable Live View; Kernel and Browserbase offer browser-scoped computer controls. If the business needs non-browser GUI apps, you need E2B Desktop or a DIY desktop.",
          "Anti-block, refined: Kernel's stealth (included on ALL tiers) routes through a managed STATIC ISP proxy giving a static per-session exit IP, plus an automatic CAPTCHA solver (reCAPTCHA + Cloudflare challenges), and you can swap in your own residential proxy — this is the best turnkey 'static IP + avoid blocks' answer. Browserbase bundles Basic Stealth + Auto CAPTCHA on paid tiers but locks Advanced Stealth to custom Scale pricing. For raw datacenter static IPs at the VM layer, Fly.io is cheapest ($2/mo dedicated IPv4, ~$3.60/mo static egress) but datacenter ranges are still blockable.",
          "For injecting many accounts safely, two strong patterns: Cloudflare Sandboxes inject credentials at the NETWORK layer (agent code never sees the token) with per-domain auth policy; AWS AgentCore Browser Profiles persist cookies/localStorage to S3; Kernel/Browserbase Managed Auth + persistent contexts keep web logins alive across sessions. Bare VMs (Fly/Daytona/Morph/Vercel/Modal) leave account injection to you (env vars / mounted files).",
          "Persistence vs snapshot vs fork are different capabilities. Live MEMORY+process fork is unique to Morph Infinibranch (<250ms, branch a running business state to explore strategies or recover). Disk/state snapshots: Cloudflare (auto-idle disk snapshot to R2, ~2s restore), Vercel Sandbox (persistent-by-default + snapshots + Drives), Modal (filesystem snapshots), E2B (persistence/pause). Daytona 'snapshots' are image TEMPLATES, not live state — use Morph if you need to checkpoint a running agent's memory.",
          "Idle cost dominates for an always-on founder agent (mostly waiting on the LLM), so prefer providers that bill only active CPU. Best idle models: AWS AgentCore (idle + I/O-wait free), Cloudflare Sandboxes (active CPU only), Vercel Sandbox ($0.128/active-CPU-hr, I/O wait free), Kernel/Browserbase Standby, Blaxel ($0 compute in standby, <25ms resume). Active-rate references: Daytona Linux vCPU $0.0504/hr, E2B 2vCPU ~$0.10/hr, Morph $0.05/MCU. Modal sandbox CPU is ~3x base — reserve it for GPU work.",
          "Deployment flexibility ('local or cloud'): Coder is strongest for self-host/air-gap/own-cloud (Terraform + WireGuard); Daytona and Northflank offer BYOC into your VPC; E2B Enterprise allows self-host (open-source SDK). Kernel, Browserbase, Cloudflare, Morph-cloud, Modal, Vercel, and AWS AgentCore are effectively cloud-only — and AgentCore additionally locks you to AWS (which can be a plus if the business data already lives there).",
          "Suggested Foundagent stack: PRIMARY work VM = E2B Desktop (screen-based Computer Use, runs any app) or Daytona/Vercel (idle-cheap, persistent, BYOC) with a DIY desktop; WEB anti-block layer = Kernel (turnkey static-ISP stealth + CAPTCHA) or Browserbase (cheaper), or AWS AgentCore Browser if all-in on AWS; ACCOUNT/credential injection = Cloudflare egress-proxy pattern (or AgentCore Browser Profiles for web auth); STATIC datacenter IP per agent = Fly.io; CHECKPOINT/FORK of full business state = Morph Infinibranch; GPU work = Modal; FULL self-host/governance = Coder."
        ]
      },
      {
        "dimension": "Computer Use 与浏览器自动化云 (Computer Use & Browser Automation Cloud)",
        "options": [
          {
            "name": "Scrapybara",
            "url": "https://scrapybara.com/",
            "category": "托管完整虚拟桌面 (Ubuntu/Windows) + 浏览器,原生 Computer Use 云",
            "description": "为 AI agent 提供托管远程虚拟桌面实例,共三种实例类型:Ubuntu(完整 Linux 桌面)、Windows(完整 Windows 桌面)、Browser(轻量 Chromium,<1s 启动)。原生面向 Computer Use:提供 Act SDK(Python+TS),统一封装 Claude Computer Use 与 OpenAI CUA,内置 ComputerTool/BashTool/EditTool,支持多轮对话与结构化输出。支持已认证会话保存复用('Save and reuse browser auth states across instances')、实例 pause/resume,实时流式查屏。是与 Foundagent '每 session 一台隔离 VM + Computer Use + 浏览器' 最贴合的托管产品之一。",
            "pricing": "Free $0(10 compute 小时, 100 agent credits, 5 并发);Basic $29/mo(100 小时, 500 credits, 25 并发);Pro $99/mo(500 小时, 2500 credits, 100 并发);Enterprise 定制(自托管 + 99.9% SLA + 专属支持)。双重计费:compute 小时 + agent credits('每个 step = 1 条带工具调用的 assistant 消息 = 1 credit',超量 $0.04/credit);可 BYO 模型 key 由模型商直接计费、不消耗 credits。",
            "computerUseSupport": "原生支持。专为 Computer Use 设计,提供完整桌面(截图+鼠标+键盘),Claude/OpenAI CUA 模型经 Act SDK 几乎零样板驱动。",
            "staticIpAntiBlock": "弱项:官网/文档未宣传静态 IP、住宅代理或反指纹/反检测。防封需在 VM 内自行叠加代理,或走 Enterprise 自托管自建出网。",
            "deployment": "云为主;Enterprise 提供自托管。",
            "pros": [
              "真正完整桌面(Ubuntu+Windows),Computer Use 可跨任意桌面应用而非仅 web",
              "原生 Act SDK + 内置工具,接 Claude/OpenAI computer-use 几乎零样板",
              "已认证会话跨实例保存复用 + pause/resume,契合 '注入多账号、长期运行'",
              "Enterprise 可自托管,满足本地/云双形态"
            ],
            "cons": [
              "无内建静态 IP/住宅代理/反指纹,防封需自建",
              "credits 计费在高频 step 下成本偏高($0.04/step,除非 BYO key)",
              "完整桌面实例比纯浏览器更重、单价更高"
            ],
            "relevanceToFoundagent": "高。对一个要像创始人一样操作各类 SaaS/桌面工具的 agent,这是上手最快的托管 '隔离桌面 + Computer Use' 方案:跨实例保存登录态便于注入并长期持有多个业务账号,pause/resume 支持长生命周期 agent。最大缺口是无每-session 静态 IP/反封锁,需在 VM 内叠代理或迁 Enterprise 自托管。建议作为托管首选,与自托管 cua/Bytebot 做 '省心 vs 可控' 对比。",
            "verified": true
          },
          {
            "name": "trycua / cua",
            "url": "https://github.com/trycua/cua",
            "category": "开源完整桌面 sandbox 基础设施 (macOS/Linux/Windows/Android) + 可选云",
            "description": "开源 Computer-Use Agent 基础设施(MIT, 19.1k stars)。统一 Python SDK(pip install cua, Python 3.11+)跨多 OS。核心:Lume(基于 Apple Virtualization.Framework 在 Apple Silicon 上近原生起 macOS/Linux VM)、QEMU 后端(支持 BYOI .qcow2/.iso)、cua-agent(自主任务框架)、cua-bench(OSWorld/ScreenSpot/Windows Arena 评测 + RL 环境,可导轨迹训模型)。Cua Cloud / Cua Run 提供弹性 warm-pool 沙箱(BYOC/on-prem)。",
            "pricing": "开源栈免费(GitHub)。云(Cua Run / 专用 fleet)目前 'by request' 邮件联系,官网未公开标准定价。自托管仅承担自有基础设施成本。",
            "computerUseSupport": "原生且最全面。完整桌面横跨 macOS/Linux/Windows/Android,是少数能给 agent 真正 macOS 桌面的方案。",
            "staticIpAntiBlock": "自托管时由你自己的网络/出口决定:可绑定每-session 专属静态 IP 与自建代理(完全可控);产品本身不内建住宅代理/反指纹 stealth。",
            "deployment": "本地(Lume/QEMU)+ 云(Cua Run/BYOC/on-prem),最灵活双形态。",
            "pros": [
              "MIT 开源、自托管,无 vendor lock-in,成本可压到基础设施价",
              "唯一同时覆盖 macOS/Linux/Windows/Android 完整桌面的方案",
              "本地 Apple Silicon 即可起 VM,云形态可弹性扩展,满足 '本地或云均可'",
              "自托管 = 网络/IP/账号注入完全自控,易做每-session 固定静态 IP"
            ],
            "cons": [
              "云端定价不透明(需联系);自托管需自担运维与 IP/代理工程",
              "部分能力(部分云/BYOI 流程)仍偏早期",
              "反检测/防封需完全自建,无开箱 stealth"
            ],
            "relevanceToFoundagent": "高。若 Foundagent 倾向长期可控基础设施(自管每账号静态 IP、注入登录态、降本、避免锁定),cua 是首选开源底座:本地起隔离 VM、按账号绑定专属出口 IP、用快照固化登录态,边际成本最低。与 Scrapybara/E2B(托管)构成 '自建 vs 托管' 两极;短板是 stealth 与运维需自建。",
            "verified": true
          },
          {
            "name": "E2B / E2B Desktop",
            "url": "https://e2b.dev/pricing",
            "category": "托管沙箱云(含完整 Linux 桌面 Desktop flavor),开源",
            "description": "'Enterprise AI Agent Cloud',提供秒级启动的隔离沙箱;其 Desktop flavor 是完整图形化 Linux 桌面(Xfce + noVNC),专为 Computer Use(Anthropic Computer Use / OpenAI Operator)设计——给 agent 屏幕+鼠标+键盘。被 Manus 用于给 agent 提供 '虚拟电脑',在 agent 规模化场景已被验证。同一平台也是通用代码执行沙箱。开源,支持 BYOC/on-prem/self-host。",
            "pricing": "Hobby Free(一次性 $100 credits, ≤1h 会话, ≤20 并发, 10GiB 存储);Pro $150/mo(可定制 CPU/RAM, ≤24h 会话, ≤100 并发, 可加购至 1100, 20GiB);Enterprise 定制(BYOC/on-prem/self-host)。按秒计费:1 vCPU $0.05/h、2 vCPU(默认)$0.101/h、4 vCPU $0.202/h;RAM $0.016/GiB/h;存储免费额度内。",
            "computerUseSupport": "Desktop flavor 原生支持完整桌面 Computer Use(为 Anthropic/OpenAI computer-use 而建);通用 flavor 亦可作代码执行后端。",
            "staticIpAntiBlock": "无内建 stealth/住宅代理;Enterprise BYOC/self-host 下网络与出口 IP 完全自控,可做每-session 静态 IP。",
            "deployment": "云 + Enterprise BYOC/on-prem/self-host,双形态。",
            "pros": [
              "托管完整 Linux 桌面里单价最低(1 vCPU $0.05/h, 按秒计),适合大规模并发",
              "为 Computer Use 原生设计,已被 Manus 等 agent 产品规模化采用",
              "Hobby $100 额度 + 24h 会话 + 100~1100 并发,扩缩容友好",
              "开源 + BYOC/on-prem,可迁到自有云做 IP/合规自控"
            ],
            "cons": [
              "桌面为 Linux(无原生 macOS/Windows 桌面,不及 cua 全面)",
              "无开箱 stealth/反封锁,需自叠代理",
              "快照/pause-resume 等持久化能力以 SDK/平台为准,需按场景确认"
            ],
            "relevanceToFoundagent": "高。对 '每 session 一台隔离桌面 + Computer Use' 的诉求,E2B Desktop 是 Scrapybara 之外最强托管候选,且按秒计费在大规模并发下成本更优;Enterprise BYOC 让你把桌面跑进自有云,从而给每个业务账号绑定固定出口 IP 并满足合规。是 '托管起步、可演进到自控' 的均衡选择。",
            "verified": true
          },
          {
            "name": "Bytebot",
            "url": "https://github.com/bytebot-ai/bytebot",
            "category": "开源自托管 AI 桌面 agent(容器化 Linux 桌面)",
            "description": "开源(Apache-2.0)自托管 AI 桌面 agent:给 AI 一台自己的电脑——容器化 Linux 桌面(Ubuntu 22.04 + XFCE,内置 Firefox/VS Code 等),可用任意应用、处理文档、用密码管理器登录网站/应用、跨程序完成多步工作流。架构:NestJS(协调 AI 与桌面动作)+ Next.js(任务管理 UI)。支持 Anthropic Claude / OpenAI GPT / Google Gemini,并经 LiteLLM 接 100+ provider(Azure/Bedrock/Ollama 本地模型)。每个桌面跑在独立 Docker 容器,docker compose 约 2 分钟起。",
            "pricing": "开源免费(Apache-2.0,GitHub)。完全自托管,仅承担自有基础设施成本 + 所选模型的 API 费用。",
            "computerUseSupport": "原生完整桌面 Computer Use:容器内完整 Linux 桌面,agent 像人一样操作任意 GUI 应用与浏览器。",
            "staticIpAntiBlock": "自托管 = 网络/出口 IP 完全自控,可为每容器绑定专属静态 IP 与自建代理;无开箱 stealth/反指纹。",
            "deployment": "纯自托管(Docker / docker compose),本地或任意云。",
            "pros": [
              "Apache-2.0 宽松许可,商用友好;完全自托管,数据不出自有服务器",
              "每桌面独立 Docker 容器隔离,docker compose 2 分钟起,落地极快",
              "原生支持密码管理器登录 + 跨应用多步工作流,贴合 '注入账号 + 像创始人办事'",
              "模型无锁定(Claude/GPT/Gemini + LiteLLM 100+),边际成本近于零(仅基础设施)"
            ],
            "cons": [
              "仅 Linux 桌面(无 macOS/Windows);需自担运维、扩缩容、IP/代理工程",
              "无开箱 stealth/反封锁,高对抗站点需自建",
              "容器化桌面方案,规模化(warm-pool/弹性)需自己工程化"
            ],
            "relevanceToFoundagent": "高(自托管路线)。是 cua 之外最简单的开源完整桌面方案:每个 '创始人 agent' 一台隔离 Docker 桌面,用密码管理器持久持有多账号、跨 SaaS/桌面应用办事,网络出口与每账号静态 IP 完全自控,边际成本趋零。适合 Foundagent 自托管 MVP 与降本;短板是 macOS/Windows 缺席、stealth 与规模化要自建。",
            "verified": true
          },
          {
            "name": "Anthropic Computer Use (reference)",
            "url": "https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool",
            "category": "模型能力 + DIY 参考实现(非托管基础设施)",
            "description": "Claude 的 computer use 工具:提供截图、鼠标/键盘控制以自主操作桌面/浏览器,在 WebArena 单 agent 基准达 SOTA。当前 beta header 为 computer-use-2025-11-24(支持 Claude Opus 4.8/4.7/4.6、Sonnet 4.6、Opus 4.5);旧版 computer-use-2025-01-24 支持 Sonnet 4.5/Haiku 4.5/Opus 4.1(已弃用)/Sonnet 4(已退役,Bedrock&GCP 除外)/Opus 4(已退役,GCP 除外)。官方 quickstart 提供 Docker 参考实现(anthropics/anthropic-quickstarts:computer-use-demo,含 Linux 桌面+X11+VNC+Streamlit+agent loop)。Anthropic 只提供模型能力与参考代码,不托管环境/IP/沙箱。",
            "pricing": "无独立费用,仅按 Claude API token 计费。参考 Docker 镜像免费开源;环境/算力成本自托管承担。",
            "computerUseSupport": "这是 Computer Use 能力本身的来源(reference),定义工具协议与 agent loop,其余产品多在其上构建。",
            "staticIpAntiBlock": "无。完全 DIY——你提供 VM 即可绑任意静态 IP/代理/反检测,但零开箱能力。",
            "deployment": "本地/云均可(自托管 Docker);Anthropic 不提供托管运行时。",
            "pros": [
              "权威、最新的 Computer Use 协议与 agent loop 参考,理解整套机制的基线",
              "Docker 参考实现可直接本地跑、零基础设施费用",
              "支持 ZDR(零数据保留),合规友好;Claude 在浏览器/桌面任务表现强(Opus 4.8)",
              "可作为自建路线的技术蓝本"
            ],
            "cons": [
              "本身不是基础设施:无托管 VM、无静态 IP、无反封锁、无账号注入,全部自建",
              "参考镜像为最小化 demo,生产化(隔离/扩缩容/IP 管理)需大量工程",
              "beta 状态,header/版本会更新"
            ],
            "relevanceToFoundagent": "基础/必备。这是 Foundagent agent 的 'Computer Use 大脑/协议层' 与默认模型(Opus 4.8 经 computer-use-2025-11-24);但它不提供执行环境,必须配 Scrapybara/E2B/cua/Bytebot 或浏览器云做 '身体'。ZDR 对处理业务数据合规有利。",
            "verified": true
          },
          {
            "name": "Kernel",
            "url": "https://www.kernel.sh/",
            "category": "浏览器云(browser-only),强持久化 + 隔离 VM",
            "description": "面向 web agent 的浏览器基础设施(YC,已融 $22M Series A)。浏览器跑在隔离虚拟机中,300ms 连接、约 7.5s 冷启(官称比 Browserbase 快 3.4x)。核心亮点是持久化:设置 KERNEL_PROFILE_NAME 即按 profile 自动在会话结束时把 cookie/登录/会话数据写回 profile,供后续会话复用。内建 managed stealth + 住宅代理 + 自动 CAPTCHA;live view/replays 可实时观看并接管。CDP/Playwright 兼容。仅浏览器,非完整桌面。",
            "pricing": "Developer Free $0+用量(含 $5 credits, 5 并发);Hobbyist $30/mo+用量($10 credits, 10 并发, 解锁持久 profiles);Startup $200/mo+用量($50 credits, 50 on-demand + 100 reserved 池);Enterprise 定制。按秒计费:Headless $0.0000166667/s(≈$0.06/h)、Headful $0.0001333336/s(≈$0.48/h)、Headful+GPU $0.0008000016/s(≈$2.88/h);'只为用量付费、无 idle 费'。",
            "computerUseSupport": "无完整桌面 Computer Use;作为 web agent 的浏览器后端,CDP 兼容,可被 computer-use 模型驱动浏览器。",
            "staticIpAntiBlock": "managed stealth + 住宅代理 + 自动 CAPTCHA(全档可用);以住宅代理为主,非每-session 固定静态 IP。强项是持久 profile 让账号 '身份' 跨会话稳定。",
            "deployment": "纯云托管。",
            "pros": [
              "持久 profiles 自动回写登录态——直接解决跨会话多账号持久 + 注入",
              "隔离 VM + live view/接管,启动极快(300ms 连接),适合大规模并行 agent",
              "managed stealth + 住宅代理 + 自动 CAPTCHA 全档可用,反封锁开箱",
              "headless ≈$0.06/h 便宜,按秒计费、无 idle 费"
            ],
            "cons": [
              "仅浏览器,无桌面级 Computer Use",
              "住宅代理轮换为主,非每-session 固定静态 IP",
              "纯云托管,无自托管;持久 profiles 需 Hobbyist($30/mo)起"
            ],
            "relevanceToFoundagent": "高(web 场景)。'持久 profiles 自动回写 cookie/登录' 几乎是为 'founder-agent 长期持有多个业务账号、避免反复登录触发风控' 量身定制——这是 web 层最贴合 Foundagent 账号持久诉求的产品。隔离 VM + 快启 + 全档 stealth 适合规模化并行;作为强持久化 web 执行层,与桌面层(Scrapybara/E2B/cua/Bytebot)组合最佳。",
            "verified": true
          },
          {
            "name": "Browser Use Cloud",
            "url": "https://browser-use.com/pricing",
            "category": "AI 浏览器 agent + CDP 浏览器云(browser-only),核心库开源",
            "description": "知名开源浏览器 agent 库(browser-use)的官方云。提供远程 CDP 兼容浏览器:维护自有 Chromium fork 持续反检测(社区基准 stealth 约 81%,普通无头约 2%),匹配真实桌面指纹/header/时序。内建住宅代理、自动 CAPTCHA、Webhook Events(全档)。CDP 兼容,直接复用 Playwright/Puppeteer。V3 agent 自训 LLM。核心库开源可自托管。",
            "pricing": "Free $0(3 并发, 含 Advanced Stealth + Captcha);Dev $29/mo(25 并发);Business $299/mo;Scaleup $999/mo(500 并发);Enterprise 定制(年付省 2 月,各档月度 credits ≈ 月费)。用量:浏览器会话 $0.02/h;代理 $5/GB;V3 token 1.2x provider 价,或 BYO key + 0.2x 编排费。付费档解锁 BYO key/BYO proxy/Scheduled Jobs/Auto Recharge。核心库开源自托管免费。",
            "computerUseSupport": "无完整桌面;其 stealth 浏览器 + 自家 agent 可被 computer-use 模型或 V3 LLM 驱动 web,反检测在浏览器云中领先。",
            "staticIpAntiBlock": "强:自有 Chromium fork 持续反检测(约 81% stealth 基准)+ 住宅代理 + 自动 CAPTCHA;以住宅轮换为主,非每-session 固定静态 IP。",
            "deployment": "云 + 核心库开源自托管,双形态。",
            "pros": [
              "stealth 实测最强档之一(约 81% 基准),驱动高风控真实 web 稳健",
              "核心库开源可自托管,CDP 兼容 Playwright,迁移零成本",
              "$0.02/h 浏览器会话极低;BYO key 仅 0.2x 编排费,大规模控成本"
            ],
            "cons": [
              "仅浏览器,无桌面级 Computer Use",
              "住宅代理轮换为主,非每-session 固定静态 IP",
              "云端定价多层(会话+代理+token/step)需精算"
            ],
            "relevanceToFoundagent": "中高(web 场景)。开源 + 顶级 stealth + 全网最低 $0.02/h,是 Foundagent 在高风控站点做注册/登录/操作的强 web 执行层,BYO key 让大规模成本可控;核心库开源便于自托管自建出口 IP。桌面层仍需 Scrapybara/E2B/cua/Bytebot 补齐。",
            "verified": true
          },
          {
            "name": "Steel.dev",
            "url": "https://steel.dev/",
            "category": "开源浏览器云 API(browser-only)",
            "description": "开源浏览器 API(steel-dev/steel-browser),云端控制浏览器集群,专为 AI agent/自动化设计。一行改动跑 Puppeteer/Playwright/Selenium(CDP 兼容)。支持最长 24h 长会话、<1s 平均启动、cookie/localStorage 保存与注入(续接登录态)、代理 + 浏览器指纹控制、内建自动 CAPTCHA。集成 Claude Computer Use / OpenAI Computer Use / Browser Use / Magnitude / Notte。可 Docker 自托管/本地运行。仅浏览器,无完整桌面。",
            "pricing": "Launch Free($0 + 用量, 含 $30 一次性 credits, 邮件/社区支持);Scale $250/mo(+用量, 含 $100/mo credits, 专属 Slack, Enterprise SSO, HIPAA-ready BAA);Enterprise 定制(1000+ 并发, Stealth Browser, reserve 浏览器池)。",
            "computerUseSupport": "无桌面 Computer Use;作为 web agent 浏览器后端,CDP 兼容,可被 computer-use 模型驱动,并已集成多家 Computer Use/agent 框架。",
            "staticIpAntiBlock": "代理 + 浏览器指纹控制 + 自动 CAPTCHA;高阶 Stealth Browser 在 Enterprise。以代理为主,每-session 静态 IP 需自托管自建。",
            "deployment": "云 + 自托管(开源 Docker),双形态。",
            "pros": [
              "开源(MIT)+ 可自托管,避免锁定,本地/云皆可,契合双形态",
              "会话状态保存注入(cookie/localStorage)+ 24h 长会话,便于多账号续接",
              "Playwright/Puppeteer/Selenium 全兼容 + 集成主流 Computer Use 框架,迁移成本低"
            ],
            "cons": [
              "仅浏览器,无桌面级 Computer Use",
              "强 stealth(Stealth Browser)在 Enterprise 档;反封锁不及专做 stealth 的厂商",
              "云档跨度大(Launch $0 → Scale $250),无中间档"
            ],
            "relevanceToFoundagent": "中高(web 场景)。开源 MIT + 自托管使其在 '可控、低成本、本地化' 优于纯托管浏览器云:自托管时可自建每账号静态 IP,24h 会话 + cookie 注入便于长期持有登录态。适合作 web 执行层,与自托管 cua/Bytebot 桌面层组合。",
            "verified": true
          },
          {
            "name": "Hyperbrowser",
            "url": "https://www.hyperbrowser.ai/",
            "category": "浏览器云(browser-only),强反检测",
            "description": "YC 支持的云浏览器基础设施,托管浏览器会话 + 内建 CAPTCHA 解决、代理轮换、ultra stealth、反 bot 检测,支持上千并发、<500ms 启动。指纹覆盖 UA/WebGL/Canvas/AudioContext,结合住宅代理 IP 轮换 + 行为模拟。提供 HyperAgent(开源 AI 浏览器自动化)。仅浏览器。",
            "pricing": "信用点:1 credit = $0.001(1000 credits = $1)。浏览器会话 100 credits/h($0.10/h);AI agent step 20 credits($0.02);Web scraping 1-10 credits/页;代理 $10/GB。Free 含 1000 credits + 1 并发。Startup $30/mo + 用量(含 30,000 credits, 25 并发, 30 天留存)。Scale $100/mo + 用量。Enterprise(ultra stealth/无限 credits/自定义速率)。",
            "computerUseSupport": "无桌面 Computer Use;面向 web agent,HyperAgent + CDP 驱动浏览器。",
            "staticIpAntiBlock": "强:ultra stealth + 旋转住宅代理 + 指纹伪装 + 自动 CAPTCHA + 反 bot,是反封锁较突出的浏览器云之一(以轮换住宅为主,非固定静态 IP)。",
            "deployment": "纯云托管。",
            "pros": [
              "反检测/stealth 能力强,适合高对抗站点驱动真实 web",
              "启动快(<500ms)、并发高(上千),信用点计费灵活",
              "HyperAgent 开源,集成 Browser Use"
            ],
            "cons": [
              "仅浏览器,无桌面级 Computer Use",
              "无自托管;以轮换住宅 IP 为主而非每-session 固定静态 IP",
              "信用点 + 用量叠加,成本预测需精算"
            ],
            "relevanceToFoundagent": "中。当 Foundagent 需在强反爬/强风控站点稳健操作 web 时,Hyperbrowser 的 ultra stealth 是加分项;但桌面 Computer Use 与每账号固定 IP 绑定需另解,且纯云托管不利于出口 IP 自控。",
            "verified": true
          },
          {
            "name": "Anchor Browser",
            "url": "https://anchorbrowser.io/",
            "category": "面向 Computer Use agent 的安全云浏览器(browser-centric,偏合规)",
            "description": "云托管浏览器,定位 'Computer Use agent 的安全基础设施'——让 AI agent 像人一样浏览、填表、提取数据。提供已认证(登录态)浏览器、自动 captcha bypass、任意 geolocation 路由;高档加 Cloudflare Verified Browser Agents、自定义代理、Anchor Chromium 全 stealth、自定义区域;Enterprise 提供 BYOC & on-prem。强调企业/合规与安全可信操作。",
            "pricing": "Free(5 credits/mo, ≤5 并发);Starter $50/mo(≤25 并发, 解锁已认证浏览器/captcha bypass/任意地理);Team $500/mo(≤50 并发, Cloudflare Verified Agents/自定义代理/30 天留存);Growth $2000/mo(≤200 并发, Anchor Chromium 全 stealth/自定义区域);Enterprise 定制(500+ 并发, BYOC & on-prem)。各付费档超量 $1.00/credit。按量:浏览器创建 $0.01/个、使用 $0.09/小时、代理 $8/GB、AI step $0.01。",
            "computerUseSupport": "明确面向 Computer Use agent,但实质是云浏览器(非完整桌面 OS);可作 computer-use 模型的安全浏览器执行环境。",
            "staticIpAntiBlock": "分档:任意 geolocation(Starter)、自定义代理 + Cloudflare Verified Agents(Team $500)、Anchor Chromium 全 stealth + 自定义区域(Growth $2000)、独特指纹/on-prem(Enterprise)。强 stealth 门槛较高。",
            "deployment": "云为主;Enterprise 提供 BYOC & on-prem。",
            "pros": [
              "原生强调已认证会话 + 安全/合规,适合 '注入多账号' 的可信操作",
              "按量便宜(使用 $0.09/h, 创建 $0.01/个),Starter $50 起即解锁登录态/captcha bypass",
              "Enterprise 支持 BYOC & on-prem + 独特指纹"
            ],
            "cons": [
              "全 stealth 在 Growth($2000/mo),自定义代理在 Team($500/mo),反封锁门槛高",
              "本质是浏览器,非完整桌面 Computer Use",
              "以代理为主,非每-session 固定静态 IP(自控 IP 需 Enterprise on-prem)"
            ],
            "relevanceToFoundagent": "中。'安全 + 已认证会话 + 面向 computer-use' 的定位贴合 Foundagent 多账号可信操作,按量价格亲民;但强防封需 Team/Growth 高档,且仍是浏览器层而非桌面。注:相较早前资料,使用费已是 $0.09/h(非 $0.05),并新增 Team $500/mo 档。",
            "verified": true
          },
          {
            "name": "Skyvern",
            "url": "https://www.skyvern.com/",
            "category": "开源 AI 浏览器自动化 agent(browser workflows)",
            "description": "用 Vision LLM 自动化任意网站的浏览器工作流(靠视觉理解页面交互,不止 XPath)。开源(AGPL-3.0,20k+ stars),提供 TypeScript SDK、REST API、MCP 支持,可 Docker Compose 自托管(数据留本地)。定位浏览器工作流自动化(非完整桌面)。也有托管云。",
            "pricing": "Free:每月 5000 credits(免信用卡);Pro 约 $149/mo(资料口径);step 计费 2025 年降至约 $0.05/step。完整付费档/credit 消耗率官网 pricing 页未全公开(需登录/联系)。",
            "computerUseSupport": "Vision-LLM 驱动的浏览器自动化,概念接近 Computer Use 但限于 web 工作流,非桌面 OS 级。",
            "staticIpAntiBlock": "官网未突出 stealth/住宅代理/静态 IP;自托管时可自配代理/IP。防封非其卖点。",
            "deployment": "云 + 自托管(Docker Compose, AGPL),双形态。",
            "pros": [
              "开源 + 自托管 + 视觉理解,适合复杂多步 web 工作流",
              "MCP/REST/TS SDK,易集成进 agent 编排",
              "Free 档慷慨(5K credits/月)"
            ],
            "cons": [
              "AGPL-3.0 许可(商用需评估 copyleft 影响)",
              "无桌面级 Computer Use;反封锁非强项",
              "付费定价不透明(pricing 页缺明细)"
            ],
            "relevanceToFoundagent": "中低。可作 web 工作流执行/编排候选;但桌面 Computer Use、强 stealth、每账号静态 IP 均需另配,且 AGPL-3.0 copyleft 对闭源商用产品需谨慎评估。优先级低于 cua/Bytebot(桌面)与 Kernel/Browser Use(web)。",
            "verified": true
          }
        ],
        "keyInsights": [
          "分两层选型,且两层都要:完整虚拟【桌面】(Scrapybara、trycua/cua、E2B Desktop、Bytebot、Anthropic Docker)让 agent 像创始人一样跑任意应用(桌面 SaaS、密码管理器、文件操作);【浏览器】云(Kernel、Browserbase、Browser Use、Steel、Hyperbrowser、Anchor、Skyvern)只覆盖 web 但更快/更便宜/stealth 更强。推荐架构:桌面为核心 + 在其内/并行叠加一个强 stealth 浏览器层处理高风控 web 登录。",
          "对一个要长期持有数十个业务账号的 founder-agent,'跨会话登录态持久' 是关键规格,而非每次重登(重登易触发风控)。最贴合的能力排序:Kernel 持久 profiles(会话结束自动回写 cookie/登录)> Steel cookie/localStorage 注入 > Scrapybara/Browser Use 保存的 auth states > E2B/cua/Bytebot 可快照的 VM/容器。Kernel 的持久 profile 几乎是为此诉求量身定制。",
          "'每-session 固定静态 IP' 极稀缺:几乎所有云给的是【轮换住宅代理】,对 '一个账号绑一个稳定 IP' 反而不利。要可靠实现每账号固定出口 IP,唯一可靠路径是自托管(cua、Bytebot、Steel OSS、E2B BYOC、Scrapybara/Anchor 的 on-prem)自建出网。把 '需要固定 IP 绑账号' 当作选自托管的决定性理由。",
          "脑 vs 身分离:Anthropic 只提供 Computer Use 协议 + 模型(Opus 4.8,beta header computer-use-2025-11-24)+ 一个 Docker demo,不托管 VM/IP/沙箱——必须配执行 '身体'。已验证最新 header 与机型;且该能力支持 ZDR,处理业务数据合规友好。",
          "规模化成本(粗算,BYO 模型 key 以避加成):最便宜浏览器 = Browser Use $0.02/h、Kernel headless ≈$0.06/h;中档 = Anchor $0.09/h、Hyperbrowser/Browserbase $0.10-0.12/h、Kernel headful ≈$0.48/h;托管桌面 = E2B 最低($0.05/h@1vCPU,按秒)、Scrapybara compute 小时 + $0.04/step。住宅代理 $5-12/GB 常是真正大头。自托管(cua/Bytebot)只付基础设施,高并发下最省。",
          "自托管许可:MIT(cua、Steel)与 Apache-2.0(Bytebot、E2B 核心)商用友好;Browser Use 核心开源;Skyvern 为 AGPL-3.0(copyleft,闭源商用前须评估)。优先 MIT/Apache 的 cua / Bytebot / E2B / Steel 作自建底座。",
          "Foundagent 推荐栈:(1) 桌面核心——先用 E2B Desktop 或 Scrapybara 快速起步,长期迁到自托管 cua / Bytebot 以拿到每账号静态 IP + 降本 + 无锁定;(2) Web/stealth 层——高风控登录用 Browser Use 或 Hyperbrowser,多账号持久用 Kernel 持久 profiles;(3) 脑——Anthropic Computer Use(Opus 4.8)。账号注入 + 每账号固定 IP 在自托管出网下最可控。"
        ]
      },
      {
        "dimension": "防封 / 静态·住宅 IP / 代理 / 验证码 (Anti-block / Static & Residential IP / Proxy / CAPTCHA)",
        "options": [
          {
            "name": "Bright Data",
            "url": "https://brightdata.com",
            "category": "代理网络 + 托管解封 (Proxy network + managed unblocker / scraping browser)",
            "description": "体量最大的代理与采集基础设施厂商。提供 150M+ 轮换住宅 IP、约 1.3M 静态住宅(ISP)IP(195 国),以及托管型 Web Unlocker 和 Scraping Browser(云端无头浏览器,内置自动过验证码 + 指纹 + 重试)。是'静态 IP + 防封'这一维度的事实标杆。",
            "pricing": "已核实(2026-06)。静态 ISP 共享池:10 IP=$1.8/IP、100=$1.45、500=$1.4、1000=$1.3/IP;独享池:10=$3.5/IP、100=$2.75、500=$2.6、1000=$2.5/IP。按 GB:PAYG $8/GB→承诺量 $5/GB(每 IP 含 100GB 公平用量)。住宅 PAYG $8/GB(促销 $4),承诺量低至 $2.5-5/GB。Scraping Browser $8.40/GB(PAYG)→$6.30/GB。CAPTCHA Solver $1.50/1k→$1.05/1k。所有套餐提供免费试用,首充至多匹配 $500。",
            "computerUseSupport": "原始代理是网络层、对 Computer Use 完全透明 —— 在 VM/浏览器上配置该静态 IP,任何 Computer Use agent 即继承该出口 IP。Scraping Browser 是程序化(Playwright/Puppeteer/CDP)的云端无头浏览器,不是供截图点击的 GUI。",
            "staticIpAntiBlock": "强。195 国的独享、非轮换静态住宅(ISP)IP,非常适合维持一个稳定身份。Web Unlocker/Scraping Browser 自动解验证码 + 轮换 + 指纹,接近 100% 解封,但它会轮换 IP,因此不适合做单一登录身份。",
            "deployment": "云(代理可从本地或云端 VM 路由);托管产品(Unlocker/Scraping Browser)仅云端。",
            "pros": [
              "网络规模与可靠性行业第一,IP 池与地理定位最全(195 国)",
              "产品线完整:从原始代理到全托管解封一站式",
              "提供真正独享、非轮换的静态 ISP IP(每身份一个稳定出口)",
              "支持 AWS/Azure Marketplace 计费,企业合规齐全"
            ],
            "cons": [
              "价格最高;托管产品按 GB 计费($5-8.4/GB),规模上来后昂贵",
              "强制 KYC/合规审核,部分'敏感'目标站点被平台主动封禁不可用",
              "托管 Scraping Browser 会轮换 IP,不能维持单一登录身份",
              "学习曲线与配置复杂度高于轻量厂商"
            ],
            "relevanceToFoundagent": "静态 IP 层的首选:为每个 founder-agent 身份分配一个独享 ISP IP 作为长期稳定出口(养号、保持登录态/声誉)。把该 IP 配在 agent 的隔离 VM/防关联 profile 上,出口即固定。Web Unlocker/Scraping Browser 仅用于只读的市场/竞品调研(无状态采集),绝不要用在'创始人'登录态的真实账号上 —— 它会轮换 IP 导致账号被风控。规模上独享 ISP $2.5-3.5/IP/月,数十个身份月成本可控。",
            "verified": true
          },
          {
            "name": "Oxylabs",
            "url": "https://oxylabs.io",
            "category": "代理网络(企业级)",
            "description": "与 Bright Data 并列的企业级代理厂商,ISP 代理来自顶级 ASN(Lumen、Comcast、BT Group、Orange、Cox),并有 Web Unblocker 托管解封产品。",
            "pricing": "已核实(2026-06)。ISP per-IP:10 IP=$1.6/IP($16)、100=$1.3/IP($130)、500=$1.2/IP($600)、2000+ 定制;含'公平使用'不限带宽(单 IP ≤50GB/月可 100 并发,超出降至 10 并发),22 国。住宅:PAYG $4/GB→承诺量 $2/GB。ISP 免费试用需联系销售(support@oxylabs.io)。",
            "computerUseSupport": "网络层透明,适用任意 Computer Use VM/浏览器。另有 Web Unblocker(程序化解封端点)。",
            "staticIpAntiBlock": "强。ISP 代理来自优质 ASN,会话时长无限、非轮换,适合稳定身份。但默认套餐 ISP IP 为'半独享'(最多与 3 个用户共享),对纯净身份是隐患 —— 应升级到完全独享。",
            "deployment": "云。",
            "pros": [
              "企业级稳定性与支持,ISP 带宽不限(公平使用)",
              "ISP IP 来自优质运营商 ASN(Lumen/Comcast/BT/Orange/Cox),信任度高",
              "per-IP 价格低($1.2-1.6),24/7 客户成功团队",
              "Web Unblocker 提供托管解封"
            ],
            "cons": [
              "ISP 仅约 22 国,偏 US/UK/DE/FR/CA",
              "默认 ISP IP 为半独享(最多 3 人共享 → 身份串味风险)",
              "试用需销售审批,强 KYC",
              "整体价格偏高"
            ],
            "relevanceToFoundagent": "静态 IP 层对 Bright Data 的有力替代,在 US/EU 覆盖足够时尤佳。给每个 founder-agent 一个独享(务必非半独享)ISP IP 作固定出口,优质 ASN 让账号注册/长会话更不易触发风控。覆盖国家少于 Bright Data,若身份需要冷门地理则不适用。",
            "verified": true
          },
          {
            "name": "Decodo (formerly Smartproxy)",
            "url": "https://decodo.com",
            "category": "代理网络(性价比中端)",
            "description": "2025 年 4 月由 Smartproxy 更名而来。提供 100% 独享的静态住宅(ISP)IP,计费方式灵活(按独享 IP / 按 IP / 按 GB 三选一),易用性与文档口碑好。",
            "pricing": "已核实(2026-06)。ISP 独享(per-IP):3 IP=$3.33/IP($9.99)、10=$2.90、20=$2.80、50=$2.70、100=$2.60、200=$2.50/IP($500);另有 Pay/IP 共享低至 $0.27/IP、Pay/GB 共享低至 $1.30/GB 两种模式。住宅:$3.75/GB→$2/GB。约 13 个地区(US/CA/UK/FR/DE/IT/NL/BE/PL/SE/AU/JP/HK)。3 天免费试用 + 14 天退款保证。",
            "computerUseSupport": "网络层透明,适用任意 Computer Use 环境。",
            "staticIpAntiBlock": "强。100% 独享静态 ISP IP,优质 ASN,官方宣称'无验证码/无 IP 封禁'。适合维持持久身份。",
            "deployment": "云。",
            "pros": [
              "价格/易用性平衡最佳,真正 100% 独享 ISP IP",
              "三种计费(按 IP 独享 / 按 IP / 按 GB)灵活适配不同身份用量",
              "14 天退款保证 + 3 天试用,上手门槛低,文档清晰"
            ],
            "cons": [
              "ISP 覆盖约 13 国,池子规模小于 Bright Data/Oxylabs",
              "品牌更名(Smartproxy→Decodo)带来一定迁移/认知成本",
              "冷门地理位置较少"
            ],
            "relevanceToFoundagent": "规模化'每身份一个独享 ISP IP'的最佳性价比默认后端:200 IP 时 $2.50/IP/月,即可同时给 200 个 founder-agent 身份各配一个干净固定出口。100% 独享保证身份不串味,14 天退款降低试错成本。成本敏感时的首选静态 IP 层。",
            "verified": true
          },
          {
            "name": "IPRoyal",
            "url": "https://iproyal.com",
            "category": "代理网络(预算友好)",
            "description": "高性价比代理厂商。静态住宅/ISP 为独享、不限流量;轮换住宅流量'永不过期',非常契合大量低用量并行身份的场景。",
            "pricing": "已核实(2026-06)。ISP/静态住宅:from $1.80/proxy(更短租期价更高,如 24h 档约 $2.40),不限流量,500K+ IP,60+ 地区。住宅:from $1.75/GB,32M+ 池,购买的流量永不过期。支持 SOCKS5。",
            "computerUseSupport": "网络层透明,适用任意 Computer Use 环境。",
            "staticIpAntiBlock": "强(单身份)。独享(非共享)静态住宅 IP,每 IP 不限流量;非过期住宅流量适合用量很低的身份。",
            "deployment": "云。",
            "pros": [
              "独享 ISP IP 便宜($1.80 起)且流量不限",
              "住宅流量永不过期(买一次慢慢用),非常适合大量低频身份",
              "支持 SOCKS5,无长期合约,60+ 地区"
            ],
            "cons": [
              "IP 池/地理覆盖较小,企业级工具少",
              "在最难的反爬目标上质量稳定性弱于 Bright Data/Oxylabs"
            ],
            "relevanceToFoundagent": "为大量并行 founder-agent 身份提供最低成本骨干:每身份一个 $1.80 起的独享固定 IP,不限流量;轮换住宅流量永不过期,完美匹配'几十个身份各自只偶尔上网'的低频场景(无需为闲置流量付费)。预算受限或身份数量多时极具吸引力;遇到最硬的反爬目标再临时切换到 Bright Data。",
            "verified": true
          },
          {
            "name": "SOAX",
            "url": "https://soax.com",
            "category": "代理网络(统一额度池)",
            "description": "住宅/移动/ISP/数据中心代理共用一套额度池,155M+ IP,195+ 地区。移动代理(运营商级 NAT)信任度极高,适合最难的目标。",
            "pricing": "Starter $90/25GB($3.60/GB)→Business $1,600/800GB($2/GB),Enterprise 低至 $0.32/GB。额度跨所有代理类型及 Web Data API 通用。3 天 $1.99 试用。",
            "computerUseSupport": "网络层透明,适用任意 Computer Use 环境。",
            "staticIpAntiBlock": "中-强。统一额度内可用 ISP 代理;住宅+移动池地理多样;移动 IP 信任度最高,适合风控最严的站点。",
            "deployment": "云。",
            "pros": [
              "一套额度跨住宅/移动/ISP/数据中心通用,极其灵活",
              "移动代理质量突出(运营商级 NAT,信任度最高)",
              "195+ 地区,定位粒度细"
            ],
            "cons": [
              "以 GB 计费为主,没有像 IPRoyal/Decodo 那种廉价的'固定单 IP 永久持有'套餐",
              "入门价偏高($90 起)",
              "不太适合做'每身份一个固定 IP 长期不变'的骨干"
            ],
            "relevanceToFoundagent": "当某个 founder-agent 身份运营的目标站点风控极严(需要移动级信任),或需要灵活混用多种代理类型时很有用。作为廉价固定 IP 骨干则不如 IPRoyal/Decodo —— 定位为'特殊身份/特殊目标'的补充代理,而非默认静态 IP 层。",
            "verified": true
          },
          {
            "name": "CapSolver",
            "url": "https://www.capsolver.com",
            "category": "验证码识别(AI 自动)",
            "description": "AI 驱动的验证码识别服务,速度快、覆盖广,支持现代挑战类型(reCAPTCHA、Turnstile、Cloudflare、DataDome、AWS WAF)。API 兼容 2Captcha,迁移成本低。",
            "pricing": "已核实(2026-06,均按每 1000 次):reCAPTCHA v2 $0.80、v2 Enterprise $1.00、v3 $1.00、v3 Enterprise $3.00、Cloudflare Turnstile $1.20、Cloudflare Challenge $1.20、DataDome Slider $2.50、AWS WAF $2.00、ImageToText $0.40、VisionEngine $1.50。最低充值约 $6。注意:其定价页未列 hCaptcha。",
            "computerUseSupport": "API 化、与 Computer Use 正交 —— 当流程中出现验证码时,作为一个工具被调用。提供浏览器扩展(本地运行)+ Selenium/Puppeteer/Playwright 集成。",
            "staticIpAntiBlock": "非 IP/防封产品本身;解决的是'验证码挑战层',降低在挑战关口被拦截的概率。",
            "deployment": "云 API(+ 可本地运行的浏览器扩展)。",
            "pros": [
              "快(reCAPTCHA 3-5s,图像 0.2s)且便宜",
              "现代验证码覆盖最广(含 Turnstile/Cloudflare/DataDome/AWS WAF)",
              "API 兼容 2Captcha,99%+ 在线率"
            ],
            "cons": [
              "纯 AI 对最冷门/全新挑战可能失手;定价页未列 hCaptcha",
              "在部分站点处于 ToS/法律灰色地带",
              "成功率随对方防御更新波动,需谨慎集成以免反被识别"
            ],
            "relevanceToFoundagent": "founder-agent 的默认验证码兜底层:在注册/登录/发帖流程抛出 reCAPTCHA/Turnstile/Cloudflare/DataDome 时由 agent 调用 API 求解,~$0.80-2.50/1k,成本几乎可忽略。作为一个 MCP/函数工具挂到 agent 上,与 Computer Use 流程正交。因 API 兼容 2Captcha,可与之做双路冗余。",
            "verified": true
          },
          {
            "name": "2Captcha",
            "url": "https://2captcha.com",
            "category": "验证码识别(AI+人工 混合)",
            "description": "老牌验证码服务,AI 优先 + 人工兜底。能处理 AI 难解的冷门挑战(Arkose/FunCaptcha、Amazon、ALTCHA)。其 API 是行业事实标准,被众多服务克隆。",
            "pricing": "reCAPTCHA v2 $1-$2.99/1k,v3 $1.45-$2.99,Turnstile $1.45,图像 $0.5-$1,reCAPTCHA Enterprise $1-$2.99。最低充值 $3。",
            "computerUseSupport": "API 化工具,SDK 丰富;可对任意图像任务做人工兜底,适合嵌入 Computer Use/自动化流程。",
            "staticIpAntiBlock": "仅挑战层,非 IP/防封产品。",
            "deployment": "云 API。",
            "pros": [
              "人工兜底可解纯 AI 解不了的冷门验证码(Arkose/FunCaptcha 等)",
              "历史悠久,API 是事实标准,生态广",
              "最低充值低($3)"
            ],
            "cons": [
              "比 AI 优先方案更慢更贵(人工延迟 10-25s)",
              "部分挑战类型支持随行情变动",
              "同样存在 ToS/法律灰色地带"
            ],
            "relevanceToFoundagent": "排在 CapSolver 之后的次级/兜底求解器:当 CapSolver 对某个不寻常挑战(Arkose/FunCaptcha 等)失手时,agent 回退到 2Captcha 的人工兜底。因 CapSolver API 兼容其格式,代码层切换几乎零成本,构成验证码层的高可用冗余。",
            "verified": true
          },
          {
            "name": "Multilogin",
            "url": "https://multilogin.com",
            "category": "防关联浏览器(antidetect browser)",
            "description": "指纹技术最强的防关联浏览器(每日对抗主流检测算法测试),并捆绑住宅代理。每个 profile 隔离,防止多账号被关联。",
            "pricing": "已核实(2026-06)。试用 $2(一次性 3 天,5 profiles,200MB 代理 + 60 移动分钟)。Pro 10 $11/月或 $85/年(10 profiles,1GB 代理);Pro 50 $29/月或 $230/年(3GB);Pro 100 $40/月或 $320/年(5GB,2 团队席位)。Business $89/月起(年付 $685 起,300-10,000 profiles,10GB+ 代理,无限席位)。额外代理 $3.50/GB。",
            "computerUseSupport": "运行真实 Chromium/Firefox GUI profile → 可被 Computer Use 通过截图点击驱动;同时提供 API + 硬化版 Selenium/Puppeteer/Playwright(限速 50-100 RPM)。",
            "staticIpAntiBlock": "强。一流指纹引擎 + 自带住宅 IP + 每 profile 隔离,有效防止身份被关联与封禁,适合长期维护身份。",
            "deployment": "本地 + 云(本地 app + 云端 profile)。",
            "pros": [
              "指纹/防关联能力业内最强(每日对抗检测算法测试)",
              "捆绑住宅代理(小规模无需另购代理)",
              "完整自动化 API + 硬化浏览器,支持移动端模拟,近十年口碑"
            ],
            "cons": [
              "防关联浏览器里偏贵",
              "捆绑代理流量很少(1-5GB),仍需另配静态 ISP IP 才能稳定身份",
              "自动化限速 50-100 RPM;若只需要换 IP 则属于杀鸡用牛刀"
            ],
            "relevanceToFoundagent": "当一个 founder-agent 要同时持有多个登录态账号且绝不能被关联时(如同时运营多个平台店铺/社媒号),做'每身份指纹+隔离层'的最高端选择 —— 它的指纹引擎最难被识破。每个 profile 应搭配一个独享 ISP IP(捆绑流量不足以养号)。指纹要求最高时升级到它,否则用 AdsPower 更划算。",
            "verified": true
          },
          {
            "name": "AdsPower",
            "url": "https://www.adspower.com",
            "category": "防关联浏览器(预算 + 自动化首选)",
            "description": "最便宜、最适合 agent 自动化的防关联浏览器。提供 Local API、headless 模式,以及官方 LocalAPI MCP Server(可让 Claude/Cursor 等 AI 原生驱动)。不含代理,需自带。",
            "pricing": "已核实(2026-06)。免费版 2 profiles(0 团队成员);Professional 可选 10/20/50/100 profiles;Business(热门);Enterprise 5000+ profiles 询价。月/季(-10%)/年(-20%)计费,年付赠 12GB 轮换代理(价值 $84)。常见档位约 Pro $5.40/月(年付,10 profiles)、Business $21.60/月(年付,100 profiles)。不含静态代理(BYO)。",
            "computerUseSupport": "已核实。运行真实 Chromium(SunBrowser)/Firefox(FlowerBrowser)GUI → 可被 Computer Use 截图驱动;Local API(端口 50325,Pro 120 / Business 300 / Enterprise 600 req/min)+ Selenium/Puppeteer/Playwright 经 CDP/WebSocket 连接;支持 headless(--headless=true --api-key=… --api-port=50325);官方 LocalAPI MCP Server(TypeScript/Python,基于 Playwright)让 Claude Desktop/Cursor 用自然语言 创建/启动/关闭/配置(指纹/代理/UA/国家)browser profile。",
            "staticIpAntiBlock": "每 profile 指纹隔离扎实;IP 依赖你自带的代理。headless + MCP 使其在规模化自动化上最友好。",
            "deployment": "本地 + 云(主体为本地 app;可用 API key 多设备;支持 headless)。",
            "pros": [
              "价格最低,profile 多且便宜",
              "agent 自动化体验最佳(Local API + 官方 MCP server + headless + RPA + CDP)",
              "可被 Computer Use 截图或纯 Playwright/CDP 两种方式驱动"
            ],
            "cons": [
              "不含静态代理,必须另配 ISP/住宅 IP",
              "指纹能力略逊于 Multilogin",
              "依赖本地 AdsPower 客户端运行;同一设备上 GUI 与 headless 不能同时运行"
            ],
            "relevanceToFoundagent": "Foundagent 的默认防关联浏览器:每身份一个廉价 profile($0.5-1/月量级),经官方 MCP server / Local API 让 agent 程序化创建并驱动浏览器(无需写脚本),每 profile 配一个独享 ISP IP 即得'指纹隔离 + 固定出口'的完整持久身份。MCP 原生支持 Claude 是与 founder-agent 架构最契合的一点;headless 适合服务器端规模化。需配自建/托管设备跑客户端。",
            "verified": true
          },
          {
            "name": "GoLogin",
            "url": "https://gologin.com",
            "category": "防关联浏览器(具备真正云浏览器)",
            "description": "中端防关联浏览器,亮点是提供真正的'云浏览器'(browser-in-the-cloud),可在服务器端运行 profile 而无需自建 VM。提供 REST API 与 Android 端。",
            "pricing": "Profile 套餐:Professional $24/月(100 profiles)、Business $49/月(300)、Enterprise $99/月(1000)、Custom 从 $149/月起;含 2GB 住宅代理 + REST API(300-1200 RPM)。独立的 Cloud Browser(按小时):Starter $4/月(20h)→ Enterprise $40/月(200h)。免费 3-profile 档。",
            "computerUseSupport": "本地真实 Chromium GUI → 可被 Computer Use 截图驱动;REST API + Selenium/Puppeteer/Playwright;另有云浏览器(远程/无头)用于服务器端自动化。",
            "staticIpAntiBlock": "每 profile 指纹隔离;云浏览器让 profile 无需本地硬件即可运行;内含 2GB 住宅代理但稳定身份仍需自带静态 IP。",
            "deployment": "本地 + 云(本地 app + 真正的云浏览器 + Android app)。",
            "pros": [
              "提供真正的云浏览器(无需自建 VM 即可服务器端跑 profile)",
              "REST API 完善,价格低于 Multilogin",
              "有 Android 支持与免费 3-profile 档"
            ],
            "cons": [
              "指纹能力弱于 Multilogin",
              "内含代理很少;云浏览器按小时计费,常驻 agent 会累积成本",
              "每套餐仅 1 个团队成员;最难站点上有被识别的反馈"
            ],
            "relevanceToFoundagent": "当你希望用'托管云浏览器 profile'承载每个 founder-agent 身份、避免自建 VM 时有用:云浏览器在服务器端跑指纹隔离的 profile,搭配独享 ISP 代理即得无需自管硬件的持久身份。定位介于 AdsPower(廉价/本地)与 Multilogin(高端指纹)之间;无官方 MCP,集成靠 REST API。",
            "verified": true
          },
          {
            "name": "Browserbase",
            "url": "https://www.browserbase.com",
            "category": "AI-agent 云浏览器(托管:防封 + 代理 + 验证码 + 跨会话持久化一体)",
            "description": "专为 AI agent 打造的托管云浏览器(Firecracker 隔离 microVM)。通过 CDP/Playwright/Puppeteer/Selenium 及自研 Stagehand 框架驱动。核心能力是 Contexts —— 跨会话持久化整个 Chromium user-data 目录(cookie/localStorage/IndexedDB/Service Worker/站点权限),实现'登录一次、后续会话自动保持登录态'。默认开启自动验证码,可选住宅/数据中心代理,走'合法 agent 身份'路线(Cloudflare Web Bot Auth 签名 agent、Verified 真实指纹)而非纯对抗式隐身。",
            "pricing": "已核实(2026-06)。Free $0(3 并发,1 浏览器小时,7 天留存);Developer $20/月(25 并发,100 小时后 $0.12/h,1GB 代理,自动验证码);Startup $99/月(100 并发,500 小时后 $0.10/h,5GB 代理,30 天留存,Most Popular);Scale 定制(250+ 并发,高级隐身 + Verified agent,HIPAA BAA/DPA/SSO)。",
            "computerUseSupport": "程序化为主(CDP/Playwright/Puppeteer/Selenium/Stagehand);非供截图点击的本地 GUI,但可作为 Computer Use agent 的'远端浏览器后端'(agent 通过 CDP 远程驱动云端会话)。",
            "staticIpAntiBlock": "中。默认自动验证码(5-30s 解)+ 可选住宅/数据中心代理 + Verified 真实指纹/Cloudflare 签名 agent,过 Cloudflare 等较强;但代理偏轮换,默认不提供'每身份一个固定出口 IP'。其差异化优势是 Contexts 的跨会话登录态持久化,而非固定 IP。",
            "deployment": "纯云(托管)。",
            "pros": [
              "专为 AI agent 设计,原生 CDP/Playwright/Stagehand + 统一模型网关",
              "Contexts 跨会话持久化登录态 —— 正是 founder-agent 养号刚需,无需自建带快照的 VM",
              "默认自动验证码 + 一键住宅代理,开箱即用",
              "走'合法 agent 身份'(Cloudflare Web Bot Auth / Verified)路线,长期更稳健"
            ],
            "cons": [
              "按浏览器小时计费($0.10-0.12/h),常驻/长跑 agent 成本累积快",
              "代理偏轮换,不提供'每身份一个固定 ISP IP'的稳定出口(需自配)",
              "隐身走合规路线,在主动封禁 bot 的目标上不如对抗式 antidetect + 独享 ISP",
              "纯程序化,无本地 GUI"
            ],
            "relevanceToFoundagent": "若不想自建带快照/持久卷的 VM,这是承载 founder-agent 浏览器身份最快的托管路径:用 Contexts 为每个身份持久化登录态(跨会话自动保持登录,等价于'账号注入 + 养号'),默认自动验证码 + 住宅代理直接处理防封,全程 CDP/Stagehand 程序化驱动,天然契合 agent 架构。最佳用法是给会话挂一个独享 ISP 代理,补上它缺失的'固定出口 IP'短板,即可同时拿到持久身份 + 稳定 IP。注意按小时计费,适合事件驱动/短时任务,常驻 agent 需控制在线时长。",
            "verified": true
          }
        ],
        "keyInsights": [
          "持久身份的正确原语 = 独享静态住宅/ISP 代理(非轮换、每身份一个固定 IP),而非轮换住宅代理。ISP 代理 = 数据中心速度 + 住宅信任 + 固定 IP,最适合账号注册/登录与长会话养号。已核实月成本/IP:IPRoyal $1.80 起(不限流量)、Oxylabs $1.20-1.60(半独享,须升独享)、Decodo $2.50-3.33(100% 独享)、Bright Data 独享 $2.50-3.50。规模化推荐 Decodo(200 IP @ $2.50)或 IPRoyal(低频身份,流量永不过期)。",
          "代理是网络层、对 Computer Use 完全透明:在隔离 VM/防关联 profile 上配置静态 IP,Computer Use 或 CDP agent 即自动继承一致出口 IP —— 这是给每个隔离沙箱分配稳定身份最干净的方式,无需改 agent 代码。",
          "跨会话持久化(founder-agent 的命脉)有三条路:(a) 自建 VM/容器 + 持久磁盘快照,自己存 cookie/profile;(b) 防关联浏览器 profile(AdsPower/Multilogin/GoLogin),profile 本地/云端持久;(c) Browserbase Contexts —— 托管持久化整个 user-data 目录(cookie/localStorage/IndexedDB/登录态),'登录一次后续自动保持',最省自建成本。三者都需外挂一个独享 ISP IP 才能让出口也稳定。",
          "防关联浏览器解决'同机多账号不被关联'(指纹一致性 + 隔离),与 IP 防封正交。agent 友好度排序:AdsPower(官方 MCP server + Local API 50325 + headless + CDP,Claude 可自然语言驱动,最契合 founder-agent)> GoLogin(REST API + 真云浏览器,免自建 VM)> Multilogin(指纹最强但偏贵、限速 50-100 RPM)。Multilogin 捆绑少量住宅代理,AdsPower/GoLogin 需自带。",
          "验证码是兜底层,与 IP 防封正交、按 API 调用:CapSolver 作主力(纯 AI,reCAPTCHA v2 $0.80/1k、Turnstile/Cloudflare $1.20、DataDome Slider $2.50、AWS WAF $2.00,快、覆盖广;注意其定价页未列 hCaptcha);2Captcha 作兜底(AI+人工,覆盖 Arkose/FunCaptcha 等冷门类型)。CapSolver API 兼容 2Captcha,可零成本切换做双路冗余。挂成 MCP/函数工具即可嵌入 agent 流程。",
          "托管'解封器'(Bright Data Web Unlocker/Scraping Browser、Oxylabs Web Unblocker)把代理轮换+指纹+验证码+重试打包成单端点,近 100% 成功率 —— 但无头/程序化、仅云端、按 GB 计费($5-8.4/GB)且会轮换 IP,因此只能做无状态只读采集(市场/竞品调研),绝不能用在'创始人'登录态账号上。",
          "Foundagent 的核心取舍:稳定身份(独享 ISP IP + 防关联 profile/持久 Context,长期养号、可注入账号)vs 暴力解封(轮换住宅 + 自动验证码,只读采集)。'像创始人一样经营生意'要的是稳定身份(账号、声誉、登录态),所以主链路必须是'每 agent 一个独享 ISP IP + 持久浏览器身份 + 验证码兜底';解封器仅作旁路数据收集。",
          "两套推荐栈(均含验证码兜底:CapSolver 主 + 2Captcha 备):栈 A 自托管最省钱 = AdsPower(每身份廉价 profile,官方 MCP/Local API/headless 让 agent 程序化驱动)+ Decodo/IPRoyal 独享 ISP IP(固定出口),适合规模化数十身份;栈 B 全托管最省运维 = Browserbase(Contexts 持久登录态 + 自动验证码 + 内置代理,纯 CDP/Stagehand 驱动)+ 外挂一个独享 ISP IP 补固定出口,适合事件驱动/短时任务(按小时计费,常驻需控时长)。指纹要求最高时把 AdsPower 升级为 Multilogin。",
          "成本锚点:每个 founder-agent 身份 ≈ 独享 ISP IP $1.8-3.5/月 + 防关联 profile 位 $0.5-9/月(或 Browserbase 按 $0.10-0.12/浏览器小时)+ 按量验证码(~$0.8-2.5/1k,近乎可忽略)。即可低成本并行运营数十个互不关联的独立身份。"
        ]
      },
      {
        "dimension": "本地 / 自托管 VM（支持 Computer Use）— self-hosted / local computer-use desktops for a founder-agent (Mac or Linux hosts)",
        "options": [
          {
            "name": "Bytebot (self-hosted AI desktop agent)",
            "description": "Open-source (Apache-2.0) self-hosted AI desktop agent: it gives an LLM its own containerized Ubuntu 22.04 + XFCE desktop pre-loaded with Firefox, Thunderbird (email client), and VS Code. A NestJS service runs the plan/act loop (screenshot -> click/type/scroll), a Next.js app provides a task-management UI, and each task runs in its own isolated container. Drives any provider (Anthropic Claude, OpenAI, Gemini) and 100+ more via a bundled LiteLLM proxy (incl. Ollama for local models).",
            "url": "https://github.com/bytebot-ai/bytebot",
            "category": "Turnkey self-hosted computer-use desktop AGENT (agent loop + desktop + task UI in one)",
            "pricing": "Free / open source (Apache-2.0). No license, subscription, or per-seat fee. Real cost = your chosen LLM API tokens (Claude API/Bedrock) + the compute to run the Docker containers. A managed Bytebot Cloud also exists for those who don't want to self-host (usage-based).",
            "computerUseSupport": "Native computer-use agent — this is the whole product. First-class Claude support (set Anthropic as the planner model); the desktop ships browser + email + editor so an agent can actually do business work, not just demo clicks.",
            "staticIpAntiBlock": "No built-in residential-IP/rotation layer (the documented 'proxy' is the LiteLLM MODEL proxy, not network egress). Egress = the Docker host's IP, so self-hosting at home/office gives you a trusted residential IP for free; add an outbound proxy per container for rotation.",
            "deployment": "Self-hosted: Docker Compose locally, or Helm charts on Kubernetes for fan-out; also runs on Railway / AWS / GCP / Azure. Managed cloud optional.",
            "pros": [
              "The single most 'founder-agent shaped' OSS here: ships the agent loop + a real desktop (browser + email + editor) + a task UI, so it works out of the box rather than as plumbing",
              "Apache-2.0, no fees; pay only Claude tokens + infra (a few cents/task + a modest server)",
              "Each task in its own isolated container; Helm/k8s path gives real multi-session fan-out",
              "Documented file upload (PDF/spreadsheet) and credential/'automatic authentication' handling — a built-in hook for account injection",
              "Provider-agnostic via LiteLLM; run Claude as the planner while keeping a local-model fallback"
            ],
            "cons": [
              "Container shares the host kernel (Docker isolation, not a full VM) — run on a dedicated/locked-down host for untrusted web actions",
              "No residential-IP/anti-block or per-session account vault built in — you add proxy + credential templating",
              "Linux desktop only (no macOS/Windows guest); younger project, smaller ops track record than Kasm/QEMU",
              "Quality of the agent loop depends heavily on the planner model + prompt tuning"
            ],
            "relevanceToFoundagent": "Likely the fastest path to a working founder-agent: one Docker Compose boots a desktop where Claude reads/sends email (Thunderbird), browses (Firefox), edits docs, and processes uploaded files. For cross-session persistence, snapshot a container/volume with accounts already logged in and fork per task; its credential/auto-auth handling is the natural place to inject the business's email/Stripe/etc. logins. Self-host at home for a residential egress IP; scale via Helm on owned hardware to keep marginal cost ~= electricity. Use this as the payload, cua/QEMU below as the heavier-isolation fleet substrate.",
            "verified": true
          },
          {
            "name": "trycua/cua + Lume",
            "description": "Open-source infrastructure for computer-use agents: 'cua' is an agent SDK + sandbox/computer abstraction + benchmark suite (cua-bench), and 'Lume' creates/runs macOS/Linux VMs on Apple Silicon via Apple's Virtualization.framework (near-native, no Docker Desktop/Parallels), with 'Lumier' giving a Docker-compatible interface to Lume VMs. One API targets Linux/Windows/macOS/Android across local (QEMU + Apple Virtualization) or cloud, and it exposes an MCP server so Claude Code/Cursor can drive the desktop in the background.",
            "url": "https://github.com/trycua/cua",
            "category": "VM-fleet orchestration + computer-use agent SDK (Apple Silicon native, plus cloud)",
            "pricing": "OSS stack (cua SDK, Lume, Lumier, cua-bench) is MIT and free for local self-host. Managed Cua Cloud is usage-based and billed per minute; the live pricing page only states 'Free tier on GitHub. Dedicated fleets by request' and exact per-minute/credit rates are NOT published (request access / see dashboard). Cloud currently offers Linux (Xfce) sandboxes; Windows/macOS cloud machines are 'coming soon'.",
            "computerUseSupport": "Purpose-built for computer-use agents (screenshot/click/type across full desktops). First-class Claude support via the agent SDK and MCP; can run the Anthropic loop or cua's own agents and record trajectories for benchmarking.",
            "staticIpAntiBlock": "No documented built-in static-IP/proxy layer. Local Lume/QEMU VMs egress from your Mac/host IP (residential if at home = a real anti-block advantage); cloud sandbox IPs are datacenter unless you add a proxy.",
            "deployment": "Both. Local: Lume VMs on Apple Silicon, plus a QEMU path for other OSes. Cloud: managed Cua Cloud / BYOC / on-prem scaling.",
            "pros": [
              "The best OSS VM-fleet substrate for Claude on a Mac: per-session isolated full-desktop VMs + agent SDK + MCP + benchmark harness in one MIT project",
              "Apple Virtualization.framework = near-native macOS/Linux guests on a Mac mini you already own (fixed cost vs per-minute cloud)",
              "Can host macOS guests (needed for Mac-only business apps); clean local->cloud burst path",
              "Lumier's Docker-compatible interface fits existing container workflows"
            ],
            "cons": [
              "macOS guests are Apple-Silicon-only and Apple's SLA effectively caps ~2 macOS VMs per physical Mac — limits per-host macOS session density",
              "Cloud pricing is not published and cloud is Linux-only today (macOS/Windows 'coming soon') — earlier secondhand 'credits/$1' figures are unconfirmed and were dropped",
              "More 'infra/SDK' than turnkey: you build the agent UX, account injection, and IP layer on top",
              "Younger project; operational maturity below Kasm/QEMU"
            ],
            "relevanceToFoundagent": "Strongest fit when you want a programmatic FLEET of isolated computer-use VMs rather than one container: a few Mac minis running Lume give many near-native desktops at ~electricity cost, each on a residential-ish IP, all driven by a Claude-native SDK/MCP. Template a snapshot with the business accounts logged in and clone per session for cross-session persistence; pair with Bytebot or the Anthropic loop as the in-VM agent. Reserve Cua Cloud only for spiky burst capacity once you confirm its (unpublished) per-minute rate.",
            "verified": true
          },
          {
            "name": "Anthropic computer-use quickstart (Docker image + macOS best-practices variant)",
            "description": "Anthropic's official reference: a Docker image (ghcr.io/anthropics/anthropic-quickstarts:computer-use-demo-latest) running a full Linux desktop (X11 + window manager + Firefox) with xdotool screenshot/click/type tooling wired to the Claude computer-use loop, a noVNC viewer, and a Streamlit chat UI (ports 5900/6080/8501/8080). A newer companion 'Computer Use Best Practices' quickstart runs natively on macOS (no container) and demonstrates explicit tool defs, image pruning, prompt caching, server-side compaction, batched tool calls, a sandboxed shell, and trajectory recording.",
            "url": "https://github.com/anthropics/anthropic-quickstarts/tree/main/computer-use-demo",
            "category": "Reference Docker image + best-practices kit (Linux desktop + Claude agent loop)",
            "pricing": "Free / open source (MIT-style quickstart). Only cost is Claude API tokens (Anthropic API, AWS Bedrock, or Google Vertex backends).",
            "computerUseSupport": "Native — this IS the Anthropic computer-use reference; always tracks the latest computer-use model + API contract (Opus 4.x / Sonnet) and ships the screenshot/mouse/keyboard tool implementations.",
            "staticIpAntiBlock": "None built in. Egress = the Docker host's network; add a static/residential IP via host networking or an outbound proxy yourself.",
            "deployment": "Local single `docker run` (or any cloud VM with Docker); the best-practices variant runs directly on macOS.",
            "pros": [
              "Zero-cost, official, canonical reference for the tool schema + agent loop",
              "One command to a working Claude-controlled Linux desktop; backend-agnostic (Anthropic/Bedrock/Vertex)",
              "The macOS best-practices kit shows the cost/reliability patterns (caching, pruning, compaction) you need at production scale",
              "Ideal 'inner image' that cua, Kasm, QEMU, or Apple container can wrap"
            ],
            "cons": [
              "Explicitly a beta reference, not production: single session, restart between uses",
              "Container shares the host kernel — Anthropic warns to run it inside a dedicated VM with minimal privileges (prompt-injection risk)",
              "No multi-tenant orchestration, account injection, or IP rotation — all DIY",
              "Linux-only desktop"
            ],
            "relevanceToFoundagent": "The canonical payload and the source of truth for the tool/loop contract. For Foundagent, fork the image (bake in browser + Playwright + an email client + per-session credential mounts), lift the cost/reliability patterns from the macOS best-practices kit, then let a platform (Bytebot/cua/Kasm/QEMU/Apple container) spin one per session. Treat it as the reference payload, not the platform.",
            "verified": true
          },
          {
            "name": "Kasm Workspaces",
            "description": "A container-streaming / Desktop-as-a-Service platform that delivers full Linux/Windows desktops and isolated browsers/apps to a web browser over noVNC. Self-hostable and multi-tenant, with provisioning, session isolation, autoscaling, RBAC/audit, and an admin/API layer — effectively a private DaaS on your own Docker/k8s.",
            "url": "https://kasm.com/",
            "category": "Container-streaming / Desktop-as-a-Service platform (self-hostable)",
            "pricing": "Community Edition free, limited to 5 concurrent sessions, for individual/non-profit/testing use (commercial use needs a license). Paid Starter tier offers Per-Named-User or Per-Concurrent-Session licensing (third-party listings cite roughly $5-$10/user/mo); Professional/Enterprise are quote-driven. (Kasm's own pricing/G2 pages are gated/JS-rendered; exact tier matrix needs a sales quote.)",
            "computerUseSupport": "No native LLM loop, but provides exactly the streamed, isolated desktop/browser a computer-use agent needs. Point the Anthropic loop (or cua/Bytebot/Playwright) at a Kasm session; Kasm handles isolation, lifecycle, and scaling.",
            "staticIpAntiBlock": "No residential-IP feature itself, but it runs on infra you control, so you choose egress per node; combine with an outbound proxy or per-node IP. Its 'web isolation / cloud browser' design lets you pin egress per deployment.",
            "deployment": "Both. Self-host on-prem / private cloud / your VPC via Docker (single-server) or scaled clusters; or consume their SaaS.",
            "pros": [
              "Production-grade multi-tenant orchestration, isolation, autoscaling, RBAC, and audit out of the box — the platform layer the Anthropic demo lacks",
              "Free CE covers early Foundagent dev (<=5 concurrent agents) at $0",
              "Large prebuilt Workspace/app image registry; self-hosted = full data + IP control",
              "Mature ops compared with rolling your own QEMU fleet"
            ],
            "cons": [
              "Per-user/per-session licensing gets expensive at scale vs raw QEMU/k8s",
              "5-concurrent cap and non-commercial restriction on the free tier",
              "You still bring the computer-use agent logic and account injection",
              "Pricing transparency is poor (quote-driven; public pages gated)"
            ],
            "relevanceToFoundagent": "Best 'buy the platform, not the plumbing' option for self-hosting: it solves multi-session isolation, lifecycle, and scaling so Foundagent only injects accounts and drives the desktop with Claude. Good middle ground between the bare Anthropic image and a DIY QEMU fleet — prototype free on CE (<=5 agents), then weigh its per-seat licensing against owned-hardware QEMU/cua once concurrency grows.",
            "verified": true
          },
          {
            "name": "QEMU/KVM (+ libvirt)",
            "description": "The standard open-source hypervisor stack on Linux hosts (QEMU device model + KVM kernel acceleration, managed via libvirt/virt-manager). Runs full, hardware-isolated Linux/Windows guests; reach the desktop via VNC/SPICE and drive a computer-use agent against it (xdotool/ydotool for input).",
            "url": "https://www.qemu.org/",
            "category": "Bare-metal hypervisor (maximum VM isolation, Linux host)",
            "pricing": "Free / open source (GPL). Cost = your own server + electricity — the cheapest possible per-session compute if you own hardware.",
            "computerUseSupport": "No agent built in, but a true full-VM desktop is the strongest isolation substrate for computer use. Run the Anthropic loop / cua / Bytebot inside or against the guest via VNC/SPICE.",
            "staticIpAntiBlock": "Best low-level IP control of any option: bridged/macvtap gives each VM its own MAC/IP on your LAN; route per-VM egress through specific static or residential ISP uplinks/proxies.",
            "deployment": "Local / self-hosted (Linux host, homelab, or VPS). Underpins most clouds, so configs port upward.",
            "pros": [
              "Maximum isolation (separate kernel per VM) and maximum control",
              "Effectively free at scale on owned Linux hardware — beats per-minute cloud dramatically for always-on agents",
              "Snapshots/clones let you template a 'clean account-injected desktop' and fork per session in seconds",
              "Mature, ubiquitous, fully scriptable (libvirt API)"
            ],
            "cons": [
              "Most DIY: you build orchestration, session lifecycle, account injection, networking, and the agent glue",
              "macOS guests only legal on Apple hardware and not QEMU's strength on Apple Silicon (use Lume/cua instead)",
              "Operational/maintenance burden and a real learning curve (libvirt, networking)",
              "x86 emulation on ARM hosts is slow — match arch and use KVM"
            ],
            "relevanceToFoundagent": "The cost floor and isolation ceiling for self-hosting. For many long-lived founder-agents, a QEMU/KVM fleet on owned Linux hardware with per-VM bridged residential/static IPs is the cheapest, most block-resistant, and most controllable design: template one authenticated desktop snapshot per business and clone per session for instant cross-session persistence. The trade-off is building the orchestration that Kasm/cua/Bytebot give you for free.",
            "verified": true
          },
          {
            "name": "Apple container + Containerization framework",
            "description": "Apple's open-source (Apache-2.0) Swift tooling that runs OCI Linux containers, each inside its own lightweight VM, natively on Apple Silicon. 'apple/containerization' is the framework (optimized kernel, ext4, netlink, Rosetta for linux/amd64); 'apple/container' is the Docker-like CLI. Reached version 1.0 on 2026-06-09.",
            "url": "https://github.com/apple/container",
            "category": "Native macOS Linux-container runtime (per-container micro-VM)",
            "pricing": "Free / open source (Apache-2.0).",
            "computerUseSupport": "No GUI/desktop or agent layer out of the box — targets headless Linux containers. Run a desktop image (e.g. the Anthropic computer-use image with X11+VNC, or Bytebot's) inside it and connect via VNC, like Docker.",
            "staticIpAntiBlock": "Standout feature: on macOS 26 each container gets its OWN dedicated IP address (no port-mapping), giving every agent session a distinct network identity on the LAN — handy for per-session IP separation; no residential/proxy layer itself (full networking needs macOS 26 Tahoe).",
            "deployment": "Local only, Apple Silicon Macs (runs on macOS 15 but full per-container networking requires macOS 26).",
            "pros": [
              "VM-grade isolation per container with container ergonomics — strong safety for untrusted agent actions",
              "Per-container dedicated IP simplifies giving each agent session a distinct network identity",
              "Now 1.0 (released 2026-06-09): no longer pre-release; first-party Apple support, fast boot, Rosetta for amd64 images",
              "Free, OCI-compatible — existing computer-use images run with minimal change"
            ],
            "cons": [
              "Full networking requires macOS 26; functionality is limited on macOS 15",
              "No GUI/desktop/agent layer — you supply the desktop image and the Claude loop",
              "Linux containers only (no macOS/Windows guests; for macOS guests use Lume/cua)",
              "Newer ecosystem than Docker for tooling/GUI specifics"
            ],
            "relevanceToFoundagent": "A clean, now-stable (1.0) local substrate on Mac hardware: run Bytebot or the Anthropic computer-use image as per-container micro-VMs, each with its OWN dedicated LAN IP — better isolation than Docker Desktop and a built-in answer to 'distinct network identity per session.' Pair with home/office residential egress for anti-block. Good production-candidate base for a Mac-hosted Foundagent fleet, with the caveat that you provide the desktop+agent payload and need macOS 26.",
            "verified": true
          },
          {
            "name": "UTM",
            "description": "A free, open-source Mac/iOS app wrapping QEMU (emulation) and Apple's Virtualization.framework (near-native ARM virtualization) behind a GUI. Runs Linux and Windows desktops on Apple Silicon, with utmctl for scripted VM control.",
            "url": "https://mac.getutm.app/",
            "category": "Mac VM application (QEMU + Apple Virtualization front-end)",
            "pricing": "Free from mac.getutm.app (Apache-2.0 / GPL components). The Mac App Store build is a paid convenience copy that funds the project; same software.",
            "computerUseSupport": "No agent layer; provides the GUI desktop. Drive it with the Anthropic loop / Playwright / Bytebot via VNC/SPICE or run the agent inside the guest. utmctl enables start/stop/clone scripting.",
            "staticIpAntiBlock": "Configurable VM networking (shared/bridged); egress defaults to the Mac's IP (residential if at home). No proxy/rotation built in.",
            "deployment": "Local only (a desktop Apple Silicon Mac). Not a server/cloud product.",
            "pros": [
              "Easiest way to stand up a Linux/Windows computer-use desktop on a Mac for prototyping",
              "Free and open source; Apple Virtualization.framework for near-native ARM guests",
              "utmctl scripting + snapshots/clone for templated account-injected images"
            ],
            "cons": [
              "Desktop-app ergonomics, not headless fleet orchestration — weak for many concurrent sessions",
              "For programmatic Apple-Silicon VM fleets, Lume/cua is the better-fit API",
              "x86 guests rely on slow QEMU emulation on Apple Silicon",
              "No multi-tenant, account-injection, or IP-management features"
            ],
            "relevanceToFoundagent": "Good for local development and a few hand-managed agent desktops on a Mac, but for Foundagent's 'many isolated sessions, programmatically' need, prefer cua/Lume (same Apple Virtualization core, real API) or Apple container. Keep UTM as the prototyping/debugging tool, not the production fleet.",
            "verified": true
          },
          {
            "name": "Daytona (self-hosted) — poor fit, flagged",
            "description": "An AI-code-execution sandbox runtime: isolated 'computers' (dedicated kernel/filesystem/network) that spin up in <90ms with SSH/VNC/web-terminal. Pivoted in 2025 from a dev-environment manager to an AI-agent sandbox runtime focused on headless code execution.",
            "url": "https://github.com/daytonaio/daytona",
            "category": "AI-agent code/sandbox runtime (Kubernetes-based) — headless-code focus",
            "pricing": "Open-source repo free to use/fork; managed cloud pricing not published on the repo.",
            "computerUseSupport": "Lists VNC access and 'computer use' among its tools, but the product is optimized for headless Python/TS/JS code execution, not full GUI desktop agents.",
            "staticIpAntiBlock": "References 'regions'/'network limits' but no documented static-IP/residential/proxy feature.",
            "deployment": "Self-host on Kubernetes (Helm/Terraform) or managed cloud.",
            "pros": [
              "Very fast sandbox spin-up (<90ms) and clean SDKs for agent-driven code execution",
              "Self-hostable on k8s for data control; snapshots/persistent state; SSH/VNC access"
            ],
            "cons": [
              "Primary strength is headless code execution, not GUI computer-use desktops",
              "Reportedly (as of 2025-26) core development moved to a private codebase with the OSS repo receiving limited updates — verify current support before adopting (not re-confirmed this round)",
              "No static-IP/anti-block features; cloud pricing opaque; licensing shifted during the 2025 pivot"
            ],
            "relevanceToFoundagent": "Weak fit for THIS dimension: it targets headless AI code execution, not the GUI computer-use desktop the founder-agent needs. Keep it only for the 'run agent-generated code' subtask; for isolated computer-use desktops prefer Bytebot / cua / QEMU / Apple container. Verify its OSS maintenance status before building on it.",
            "verified": false
          }
        ],
        "keyInsights": [
          "Two-layer mental model, refined: a computer-use setup = (1) a PAYLOAD (agent loop + desktop) and (2) a PLATFORM that spins up one per session. Payloads: Bytebot (most turnkey — ships agent loop + browser + Thunderbird email + VS Code + task UI) and Anthropic's reference image (minimal, canonical tool/loop contract). Platforms for fan-out: cua/Lume, Kasm, raw QEMU/KVM, or Apple container. Foundagent should pick one payload and one platform rather than building both.",
          "For a founder-agent that lives in email + browser, Bytebot is the fastest turnkey self-host: Apache-2.0, one Docker Compose boots a Linux desktop where Claude (set as the LiteLLM planner) reads/sends mail in Thunderbird, browses in Firefox, edits docs, and processes uploaded PDFs/spreadsheets; Helm charts scale it on k8s. Cost = Claude tokens (~cents/task) + a modest server. Its documented credential/'automatic authentication' handling is the built-in hook for account injection.",
          "Cost at scale strongly favors owned hardware for always-on agents: Bytebot/cua/QEMU on a Mac mini or Linux box cost ~electricity per session, while cloud computer-use sandboxes bill per minute (and cua Cloud is Linux-only today, with macOS/Windows 'coming soon', exact rates unpublished). Self-host the steady-state fleet; reserve cloud strictly for spiky bursts.",
          "Anti-block is a HIDDEN advantage of self-hosting: a VM/container on your home or office LAN egresses from a real residential ISP IP that anti-bot systems trust far more than datacenter ranges. None of these tools bundle residential-proxy rotation (note: Bytebot's 'proxy' is the LiteLLM MODEL proxy, not network egress), so the design pattern is self-hosted desktop + per-VM/-container residential or static IP (QEMU bridged networking, or Apple container's per-container dedicated IP on macOS 26), optionally plus a static-residential ISP proxy for rotation.",
          "Cross-session persistence + account injection is YOUR layer, but snapshots make it trivial: configure one desktop (log into the business's email/Stripe/bank/SaaS), snapshot it (QEMU/Lume/UTM clone or a container volume), and FORK per session so every agent boots already authenticated. Bytebot adds credential handling on top; the others rely on this snapshot-template pattern.",
          "Maturity update (June 2026): Apple container reached 1.0 on 2026-06-09 (no longer pre-release; per-container dedicated IP confirmed, full networking needs macOS 26). Production-self-host ranking: Kasm (most mature multi-tenant platform, but per-seat licensing and a 5-session/non-commercial free cap) > QEMU/KVM (cheapest + max control, max DIY) > cua/Lume (best Mac+Claude VM-fleet infra) ~ Bytebot (best turnkey agent desktop) > Apple container (solid, now-stable Mac substrate) > UTM (dev/prototype only). Daytona is effectively out for this dimension (headless-code focus; OSS maintenance reportedly reduced).",
          "macOS-guest caveat stands: only Apple Silicon + Virtualization.framework (Lume/cua/UTM) can host macOS guests, and Apple's SLA effectively caps ~2 macOS VMs per physical Mac — budget more Macs if a workflow needs Mac-only apps. Linux desktops (Bytebot, Anthropic image, Kasm, QEMU, Apple container) have no such cap, so default to Linux unless a business app is Mac-only.",
          "Recommended Foundagent starting stack: pilot Bytebot with Claude as the planner for the founder-agent's email+browser work (Docker Compose locally, Helm/k8s to fan out on owned hardware); pre-bake account-injected snapshots and give each instance a residential/static IP for anti-block. If you need heavier isolation or macOS guests, run cua/Lume on Mac minis or QEMU/KVM on a Linux box as the VM fleet, keep Kasm CE (free, <=5 concurrent) as an orchestration prototype, and reserve cua Cloud (per-minute) only for burst capacity. (Also worth a glance: E2B Desktop, an OSS desktop sandbox, as an alternative payload.)"
        ]
      },
      {
        "dimension": "多 Agent 编排（尤其基于 Claude Code）— CEO orchestrator → sub-agents, 多 provider, 同时支持 API key 与 subscription/OAuth token，并关注跨会话持久化 / 账号注入 / 防封 / 规模化成本",
        "options": [
          {
            "name": "Claude Agent SDK (subagents 参数 + Workflow 工具)",
            "url": "https://code.claude.com/docs/en/agent-sdk/subagents",
            "category": "官方 SDK / 编排原语（与 Claude Code 同 runtime）",
            "description": "Anthropic 官方 Agent SDK，用 query() 的 agents 参数以代码定义 sub-agent。已核实 AgentDefinition 字段：description/prompt/tools/disallowedTools/model/skills/memory(user|project|local)/mcpServers/initialPrompt/maxTurns/background/effort(low..max)/permissionMode——可逐 agent 指定模型、推理强度、工具、权限与记忆源。主 agent 经内置 Agent 工具（v2.1.63 由 Task 改名）按 description 自动委派或点名调用；sub-agent 各自独立 context、只回传最终消息、可并发。v2.1.172 起 sub-agent 可再生 sub-agent（最多 5 层，第 5 层不能再生）。可恢复：抓 session_id + Agent 结果里的 agentId，第二次 query 传 resume 续跑；sub-agent transcript 独立存储、主对话压缩不受影响、按 cleanupPeriodDays（默认 30 天）清理。规模化用 Workflow 工具（TS SDK v0.3.149+ / Claude Code v2.1.154+）：Claude 写一段 JS 脚本由 runtime 在对话外后台执行，单次 run 上限 16 并发 agent、共 1000 个 agent；仅在同一活跃会话内可恢复（退出 Claude Code 后下次重跑会从头开始）。内置 /deep-research 即一个 Workflow。所有付费档 + API + Bedrock/Vertex/Foundry 可用；在 claude -p / Agent SDK 下 Workflow 与工具调用按规则直接执行、无交互确认。",
            "pricing": "SDK 免费开源。用量计费两选一：ANTHROPIC_API_KEY（按量）或 CLAUDE_CODE_OAUTH_TOKEN（claude setup-token 生成、有效期 1 年、绑 Pro/Max/Team/Enterprise、仅推理）。重要坑：setup-token 无自动刷新机制，长时无人值守跑到期即断（GitHub anthropics/claude-code #12447），需手动重置。2026-06-15 起订阅的“程序化/第三方 agent”用量先扣每月 Agent SDK credits、再按 API 费率扣 usage credits——订阅额度仍可喂自动化，但已计量、不再是免费套利。",
            "computerUseSupport": "支持：Claude computer-use 工具需要带 Xvfb 虚拟显示 + 轻量桌面（Mutter/Tint2）+ Firefox/LibreOffice 等的沙箱环境；另含 Read/Write/Edit/Bash/Glob/Grep/WebSearch/WebFetch 等 14+ 内置工具，MCP 原生。",
            "staticIpAntiBlock": "编排层本身与网络无关，但官方 secure-deployment 指南给了规范模式（见单独 keyInsight）：把 agent 放进容器/VM 并 --network none，全部出网经宿主上一台静态 IP 的出站代理（Envoy credential_injector / Squid / mitmproxy / LiteLLM），由代理注入账号凭证 + 域名白名单。该模式一举解决静态 IP（用代理的 IP）与账号注入（agent 永不接触凭证）。",
            "deployment": "both（本地脚本 / 云服务器 / 容器；TS + Python + Go 等）",
            "pros": [
              "最贴近 Foundagent CEO 编排器：纯代码层级化定义 sub-agent，逐 agent 指定 model/effort/tools/权限/memory",
              "唯一原生同时吃 API key 与订阅 OAuth token 的编排内核",
              "context 隔离 + 并发 + 可恢复（resume session+agentId）；规模化用 Workflow（≤16 并发/≤1000 agent 单 run）",
              "官方维护、与 Claude Code 同 runtime、文档完善、MCP 原生；secure-deployment 给了静态 IP + 凭证注入的官方落地模式"
            ],
            "cons": [
              "多 provider 仅限 Claude 家族（GPT/Gemini 需另接网关或换框架）",
              "订阅 OAuth token 仅限推理、无自动刷新、到期即断，不适合纯无人值守长跑",
              "Workflow 仅同会话内可恢复，退出即重跑；纯 SDK 无开箱 UI/看板，需自建编排脚本与每 session 沙箱"
            ],
            "relevanceToFoundagent": "最高（自建路线的内核）。CEO→部门→执行者可直接用 agents 参数表达，超大规模用 Workflow；双凭证命中硬需求。给 founder agent 跑业务时：跨会话持久化靠 resume(session+agentId) 自管、账号注入与防封靠 secure-deployment 的出站代理模式、规模化成本靠把子阶段路由到 Sonnet/Haiku + Workflow 的 agent 上限。若不想自己搭持久化与沙箱，则升级到下面的 Claude Managed Agents。",
            "verified": true
          },
          {
            "name": "Claude Managed Agents（官方托管 Agent 平台）",
            "url": "https://platform.claude.com/docs/en/managed-agents/self-hosted-sandboxes",
            "category": "官方托管编排 + 沙箱 + 服务端持久会话（生产基础设施）",
            "description": "Anthropic 2026-04-08 公测发布的一套可组合 API（beta 头 managed-agents-2026-04-01），把 Agent SDK 的 harness 与生产基础设施打包：编排/推理留在 Anthropic 侧，工具与代码执行可选 (1) Anthropic 托管云沙箱（默认）(2) 自托管沙箱（在你自己的 VPC/机器，agent 的文件系统/进程/出网都归你管）(3) MCP tunnels 打通你私网里的 MCP server。推理 harness 与执行沙箱解耦——Claude 可立即推理，沙箱并行启动。会话=服务端 append-only 事件日志，持久保存、支持 pause/resume 与完整重建，原生可观测（Developer Console）。自托管走工作队列模型：你跑 environment worker 轮询/认领 session，可让每个 session 跑在自己的 Docker/microVM 里、做 per-session 网络控制；官方有 AWS Lambda MicroVMs、E2B、Modal、Daytona、Cloudflare、Vercel Sandbox、Blaxel、Namespace、GKE Agent Sandbox 等集成指南。多 agent 协调与自评估处于 research preview（需单独申请）。注意：自托管沙箱暂不支持 Memory（仅云沙箱支持）。",
            "pricing": "按两维计费：token（与标准 Claude API 同费率，输入/输出/缓存读写都算）+ session 运行时 $0.08/session-hour（毫秒计、仅 running 状态计）。无月费/无按 agent license。自托管沙箱的算力由你自付（仍照常计 token）。鉴权：组织 API key（建会话/读队列）+ environment key（worker 连队列）；AWS 上用 IAM SigV4。",
            "computerUseSupport": "支持：在沙箱内提供 bash/read/write/edit/glob/grep 标准工具集，可叠加自定义工具与 computer-use；支持 Managed Agents 全部模型含 Claude Opus 4.8。",
            "staticIpAntiBlock": "全场最强：自托管沙箱跑在你自己的网络里，出站 IP 与网络策略完全由你定（可做 per-session 静态 IP / per-session 出网控制）；配合 E2B/Modal/Daytona/Cloudflare/Vercel/Firecracker 等沙箱商即可给每个 founder session 分配独立静态出口。云沙箱则走 Anthropic 出网控制。",
            "deployment": "both（Anthropic 云 / 你的 VPC 自托管）",
            "pros": [
              "把此前‘正交三层’（编排 + 服务端持久 pause/resume 会话 + per-session 隔离沙箱 + 你掌控的出网）整合进一个官方产品",
              "每个 founder session = 一个持久服务端会话 + 一个独立沙箱 VM/容器（自托管在你 VPC）+ 独立出口 IP，正中 Foundagent 架构",
              "原生多 agent 协调（research preview）、原生可观测、免自建持久化与执行隔离基础设施"
            ],
            "cons": [
              "仅 API key（含 environment key），不支持订阅 OAuth token——不满足‘订阅凭证也要喂’的那条硬需求",
              "公测 + 多 agent 协调仍 research preview；自托管不支持 Memory；$0.08/session-hour 对大量常驻 session 会累加（每常驻 session 约 $58/月仅运行时，未含 token）",
              "控制面锁定 Anthropic（编排/推理不可迁出）"
            ],
            "relevanceToFoundagent": "极高（最省事的托管路线）。这是最接近‘Foundagent 基础设施’的单一现成产品：把跨会话持久化（服务端 pause/resume 会话）、运行隔离（每 session 自己的沙箱 VM）、静态 IP/防封（自托管出网你说了算）一次性解决，并把扇出/多 agent 交给官方。唯一缺口是不吃订阅 token——所以策略上：生产用 Managed Agents + API key，订阅额度走 Agent SDK / Claude Code 另跑。",
            "verified": true
          },
          {
            "name": "Claude Code Agent Teams（CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS）",
            "url": "https://code.claude.com/docs/en/agent-teams",
            "category": "官方实验特性 / 多会话团队编排",
            "description": "实验特性（默认关，settings.json/env 设 CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1）。已核实当前形态（截至 v2.1.186 仍为 experimental）：v2.1.178 起 TeamCreate/TeamDelete 工具已移除，设了 env 后直接 spawn teammate 即自动建队、退出自动清理；主会话当 lead 协调，teammate 是各自独立 context 的完整 Claude Code 实例，经共享 task list（文件锁防竞争、依赖自动解锁）+ mailbox 直接互发消息，可点对点对话/打断/要求 plan 审批。显示默认 in-process（任意终端），split-pane 需 tmux 或 iTerm2(it2)。teammate 可复用 .claude/agents/ 的 subagent 定义（沿用其 tools/model，定义体追加进系统提示）。",
            "pricing": "Claude Code 内置免费；按 lead 凭证计费。已核实成本：teammate 在 plan 模式下约为单会话 7x token，且随 teammate 数线性增长；官方建议 3-5 个、每人 5-6 个任务。Sonnet 当 teammate 更划算。",
            "computerUseSupport": "继承 Claude Code 工具集，可经 MCP/computer-use 接入；本质终端编码工具，computer use 非主打。",
            "staticIpAntiBlock": "网络无关；静态 IP 需 VM/代理层（见 secure-deployment 模式）。",
            "deployment": "local（终端为主；split-pane 需 tmux/iTerm2，VS Code 集成终端/Windows Terminal/Ghostty 不支持分屏）",
            "pros": [
              "天然 CEO/lead + 多 teammate，teammate 间可辩论/互相证伪（竞争性假设调试、并行评审/研究的最佳场景）",
              "共享 task list + 自动依赖解锁 + 自领任务，协调由 runtime 处理；可直接复用 subagent 定义",
              "TaskCreated/TaskCompleted/TeammateIdle hook 可做质量门禁"
            ],
            "cons": [
              "实验性、限制多：in-process teammate 不随 /resume 恢复（task list 本地持久但 teammate 不重建）、单会话仅一个团队、不可嵌套团队、lead 不可转移、权限只能在 spawn 时定",
              "约 7x token、协调开销大；偏交互式终端，不适合无人值守云端 headless"
            ],
            "relevanceToFoundagent": "中高（原型/人在环路阶段）。概念上最像‘CEO 带一群下属并行干活并互通’，适合做探索与并行评审；但 experimental + 终端依赖 + 无 headless 恢复，不适合生产无人自治。可借鉴其 lead/task-list/mailbox 模式，用 Agent SDK 或 Managed Agents 自建 headless 版。",
            "verified": true
          },
          {
            "name": "Trellis (mindfold-ai/Trellis)",
            "url": "https://github.com/mindfold-ai/Trellis",
            "category": "多平台 AI 编码工作流 harness / 编排层（本仓库已采用）",
            "description": "开源多平台编码工作流 CLI，把 spec/task PRD/workspace 记忆持久化进仓库（.trellis/spec、.trellis/tasks、.trellis/workspace journals），让‘每个新会话带真实上下文开局’。已核实：号称并已点名支持 16 个平台中的 Claude Code、Cursor、OpenCode、iFlow、Codex、Kilo、Kiro、Gemini CLI、Antigravity 等；first-class 并行靠 git worktree 给每个 task 建隔离目录，多 agent 会话并发互不污染；trellis channel 做实时多 agent 协作（spawn worker、跨 agent review、进度巡检、forum）。4 阶段循环（Plan/Implement/Verify/Finish）由自动触发的 skill + sub-agent 驱动。",
            "pricing": "AGPL-3.0 开源、免费（npm i -g @mindfoldhq/trellis）。需 Node≥18 + Python≥3.9；模型用量由底层 agent 计费。",
            "computerUseSupport": "自身不提供；取决于底层编码 agent。",
            "staticIpAntiBlock": "网络无关；静态 IP 需 VM/代理层。",
            "deployment": "both（本地 CLI；可在云 VM 跑；git-worktree 扇出，远程可 SSH 拉回）",
            "pros": [
              "天然多 provider：同一套 .trellis 结构驱动 Claude Code/Codex/Cursor/Gemini 等，凭证沿用各底层 agent（API key 与订阅皆可）",
              "git-worktree 扇出 + channel 支持开发期多 agent 并行/协作",
              "spec/记忆持久化让长期自治 agent 不每次从零；本仓库已集成，落地成本最低"
            ],
            "cons": [
              "AGPL-3.0 传染性强，商用需评估合规",
              "它是工作流/规范层非运行时编排引擎；真正 LLM 调度仍靠底层 agent + git worktree，吞吐受本机/worktree 数量限制（单机约 4-5）",
              "面向编码工作流设计，非编码的‘运营业务’任务需自定义 workflow"
            ],
            "relevanceToFoundagent": "中。Trellis 是本仓库开发期的编码工作流（把 spec/task/记忆持久化进 .trellis），不充当 founder-agent 产品的运行时编排内核；其持久化的 .trellis 记忆与多 provider 经验对开发有借鉴。注意 AGPL。",
            "verified": true
          },
          {
            "name": "OpenClaw（第三方 agent 网关 / OAuth 凭证中枢）",
            "url": "https://docs.openclaw.ai/concepts/oauth",
            "category": "第三方多 provider agent 网关 / 凭证 token-sink",
            "description": "第三方（非 Anthropic 官方，文档以‘Anthropic staff told us’措辞描述许可）开源 harness/网关，核心价值在凭证：同时管 API key 与订阅 OAuth token，且跨 provider——Anthropic 走 API key / 复用本地 claude -p / setup-token，OpenAI 走 ChatGPT·Codex 的 OAuth。用 ~/.openclaw/agents/<id>/agent/auth-profiles.json 作 token-sink 集中存储、按 expires 自动续期、避免多工具登录互挤，支持多 agent 多账号隔离（work/personal）与按会话路由（/model Opus@anthropic:work）。",
            "pricing": "开源免费（所读页未列明确 license/价格，需自行确认）；模型用量按订阅或 API 计费。",
            "computerUseSupport": "网关层，computer use 取决于底层 agent。",
            "staticIpAntiBlock": "建议配独立账号 + 静态 IP/代理隔离。注意：所读的 oauth 概念页本身并无封号/ToS 警告（此前草稿高估了），封号风险提示主要来自社区资料（learnopenclaw.ai 等）。",
            "deployment": "both（本地 / 自托管；多 agent 多账号）",
            "pros": [
              "直接命中‘同时用 API key 与订阅/OAuth token’，且跨 Claude + Codex 统一管理",
              "集中 token-sink + 自动续期 + 多账号隔离，适合给每个 session 注入不同账号",
              "多 provider 路由 + 多 agent 隔离"
            ],
            "cons": [
              "第三方项目，政策依赖 provider 善意；订阅政策 2026 年反复（见下）",
              "凭证侧便利不解决运行隔离/沙箱/持久化，需另配",
              "license/定价页面未明确"
            ],
            "relevanceToFoundagent": "中高（仅针对凭证维度）。2026 关键时间线：4-4 Anthropic 一度禁止订阅经 OpenClaw 等第三方框架使用（改额外计费）；随后官方为所有付费订阅新增‘Agent SDK credits’子额度，6-15 起订阅的程序化/第三方 agent 用量先扣 Agent SDK credits、超出按 API 费率扣 usage credits——即订阅喂第三方 agent 现已被官方允许但计量、‘$20 套出几百刀’的套利时代结束。结论：若要把订阅额度也喂进自动化，OpenClaw 的 token-sink + 多账号 + 自动续期仍是现成参考，但它现在是‘合规但计量’而非省钱手段，且不替代沙箱/持久化层。",
            "verified": false,
            "_invalid": "⚠️ 失效：本条系 'OpenClaw' 错词检索产物，与 Agent 层 provider OpenCode（sst/opencode coding agent）无关；所述 OAuth 网关及 docs.openclaw.ai / learnopenclaw.ai 链接疑似幻觉，勿据此做选型。"
          },
          {
            "name": "OpenAI Agents SDK（前身 Swarm）",
            "url": "https://openai.github.io/openai-agents-python/multi_agent/",
            "category": "厂商 SDK / 轻量多 agent 编排（handoffs）",
            "description": "OpenAI 2025-03 发布的生产级 SDK，取代已废弃的 Swarm。原语极少：Agents、Handoffs（控制权单向转交带 context）、Agents-as-tools（manager 保持对话、调专家做有界子任务）、Guardrails。两种编排：LLM-based（模型自行规划/handoff）与 code-based（结构化输出 + 链式/并行/反馈循环显式控制）。内置 tracing（OpenAI 面板或 OpenTelemetry）。提供 ComputerTool 配合 OpenAI computer-use 模型。",
            "pricing": "SDK 开源(MIT)、免费；模型用量计费。Codex 可用 ChatGPT Plus/Pro/Business 订阅登录或 API key。",
            "computerUseSupport": "支持：SDK 提供 ComputerTool + OpenAI computer-use 模型。",
            "staticIpAntiBlock": "网络无关；静态 IP 需 VM/代理层。",
            "deployment": "both（Python/TS 库，本地或云）",
            "pros": [
              "handoff + agents-as-tools 两种范式干净，正好表达 CEO 保持对话 / 或把控制权交给专家",
              "经 LiteLLM / any-llm 适配器可接非 OpenAI 模型（含 Claude），多 provider 混编",
              "内置 tracing/guardrails，生产可观测性好；TS 版可用"
            ],
            "cons": [
              "原生最优体验绑 OpenAI 模型；跨 provider 需适配层、能力对齐有损耗",
              "无原生 git-worktree / VM 隔离扇出，需自建",
              "不原生处理订阅/OAuth token 注入（本轮未重新抓取，依据前轮核实）"
            ],
            "relevanceToFoundagent": "中高。若 Foundagent 走多 provider，这是 OpenAI 侧对位内核，handoff 契合 CEO 委派，可经 LiteLLM 与 Claude 混编；Codex 侧可吃 ChatGPT 订阅或 API key。持久化/沙箱/防封仍需自建。",
            "verified": true
          },
          {
            "name": "LangGraph (LangChain)",
            "url": "https://www.langchain.com/langgraph",
            "category": "通用低层编排框架 / 有状态图运行时",
            "description": "低层 agent runtime + 编排框架，把交互建成有向图（节点/边/条件分支），支持 single/multi-agent/hierarchical(supervisor)。强项是生产级有状态：typed state、checkpointer（内存/SQLite/Postgres）、time-travel 调试、任意节点中断改 state 再 resume（适合审批流）。任意 model provider、无锁定。",
            "pricing": "库 MIT 开源免费；LangGraph Platform（云托管/自托管 runtime + LangSmith 可观测）付费分层。",
            "computerUseSupport": "框架本身不提供；可把 Anthropic computer-use / 浏览器工具作为节点接入。",
            "staticIpAntiBlock": "网络无关；静态 IP 需 VM/代理层。",
            "deployment": "both（自托管/本地库 + LangGraph Platform 云）",
            "pros": [
              "最成熟的生产级有状态编排：checkpoint + 中断/恢复 + 持久化，适合长周期自治业务的跨会话持久化",
              "任意 provider，可混用 Claude/GPT/Gemini，无锁定",
              "supervisor/hierarchical 直接表达 CEO→部门→执行者；可观测性强"
            ],
            "cons": [
              "学习曲线陡（图/状态/checkpointer 概念多），轻量任务过重",
              "凭证以 provider API key 为主，订阅/OAuth token 非其关注点，需自接",
              "非 Claude Code 系，复用现成 coding-agent 能力少，computer use/账号注入需自建（本轮未重抓，依前轮核实）"
            ],
            "relevanceToFoundagent": "中高（跨 provider + 长周期有状态引擎首选）。其 checkpointer 是除 Managed Agents 外最强的跨会话持久化/可审批方案；但偏 API key，且静态 IP 与账号注入要自建（用 secure-deployment 代理模式）。",
            "verified": true
          },
          {
            "name": "Git-worktree 扇出（Claude Code 原生 -w/--worktree）",
            "url": "https://code.claude.com/docs/en/worktrees",
            "category": "并行隔离模式（非产品）",
            "description": "用 git worktree 给每个并行 agent 一个独立工作目录 + 分支，共享同一仓库历史，避免分支冲突/stash 混乱。Claude Code 原生 --worktree/-w 一键创建并进入；Trellis、各类 /team-build 脚本以它做并行扇出底座。典型单机 4-5 个 worktree，更多则放远程机器跑、SSH 拉回。",
            "pricing": "免费（git 内置 + Claude Code）。",
            "computerUseSupport": "N/A（隔离机制）。",
            "staticIpAntiBlock": "N/A；静态 IP 仍由 VM/代理层负责。",
            "deployment": "both（本地多 worktree；远程机器 + SSH 拉回）",
            "pros": [
              "零额外依赖的并行扇出原语，让多个子 agent 物理隔离、互不污染",
              "与任何编排器（SDK / Agent Teams / Trellis / Managed Agents 自托管）正交组合",
              "Claude Code 原生 -w 一键，凭证沿用当前会话（订阅或 API key 皆可）"
            ],
            "cons": [
              "只是隔离模式，不含调度/通信/记忆，需上层编排器配合",
              "单机 worktree 数量受 CPU/内存限制（约 4-5），扩展要上远程机群",
              "面向代码仓库，对非 git 业务工作流不直接适用"
            ],
            "relevanceToFoundagent": "高（作为底座）。单机内并行隔离的最廉价手段，配合 SDK/Trellis 做扇出；但跨 VM/静态 IP/账号隔离要升级到 per-session 沙箱（Managed Agents 自托管或 E2B/Modal 等）。",
            "verified": true
          },
          {
            "name": "ruflo（原 claude-flow, ruvnet）",
            "url": "https://github.com/ruvnet/ruflo",
            "category": "Agent meta-harness / 多 agent swarm 编排",
            "description": "自称‘the leading agent meta-harness for Claude’，在 Claude Code/Codex 之上加多 agent swarm 层：大量专用 agent，按 hierarchical/mesh 拓扑协调，配持久向量记忆（AgentDB/HNSW）、自学习（SONA）、RAG、跨机联邦；hooks 自动路由/spawn/学习，约 210 个 MCP 工具分 5 组。2026 初由 claude-flow 改名 ruflo 并转 Rust/WASM 重写（v3.x）。已知其在跟进 Claude Code 嵌套 sub-agent（depth=5）能力（issue #2335）。",
            "pricing": "MIT 开源免费（npx ruflo init）。模型用量按各 provider 计费。",
            "computerUseSupport": "自身不提供；取决于底层 agent。",
            "staticIpAntiBlock": "网络无关；静态 IP 需 VM/代理层。",
            "deployment": "both（npm/npx 本地；Docker 自托管；有托管 demo）",
            "pros": [
              "现成的层级/网状 swarm + 持久记忆 + 大量 MCP 工具，开箱程度高",
              "多 provider：Claude Code/Codex 为主，另路由 GPT/Gemini/Cohere/Ollama",
              "hooks 自动 spawn/路由/学习，适合大规模 agent 群"
            ],
            "cons": [
              "文档主要提标准 API key 鉴权，原生订阅/OAuth token 支持存疑（未核实）；且 2026-06 起即便经 Claude Code 走订阅也会扣 Agent SDK credits",
              "刚大改名 + Rust/WASM 重写，稳定性/迁移风险高；社区对其‘营销 vs 实效’有争议",
              "抽象层厚、概念多，上手与可控性成本高"
            ],
            "relevanceToFoundagent": "中。想要现成大规模 swarm + 记忆 + MCP 生态时它最丰富；但订阅 token 支持存疑 + 重写期风险，建议参考/借鉴而非直接生产依赖。",
            "verified": true
          }
        ],
        "keyInsights": [
          "Claude Managed Agents（2026-04-08 公测）是本轮最重要的新发现，也是当前最贴合 Foundagent 的单一基础设施：它把此前被认为‘正交’的三层——编排、服务端持久 pause/resume 会话、per-session 隔离沙箱 + 你掌控的出网——整合进官方产品。可让‘每个 founder session = 一个持久服务端会话 + 一个自托管沙箱 VM/容器（在你 VPC，经 E2B/Modal/Daytona/Cloudflare/Vercel/Firecracker）+ 独立静态出口 IP’。唯一硬缺口：只吃 API key（含 environment key），不支持订阅 OAuth token；且多 agent 协调仍 research preview。计费=token + $0.08/session-hour（常驻 session 要算这笔）。",
          "‘静态 IP/防封 + 账号注入’有一条官方、跨方案通用的落地模式（Agent SDK secure-deployment）：把 agent 关进容器/VM 并 --network none，全部出网强制经一台静态 IP 宿主上的出站代理（Envoy credential_injector / Squid / mitmproxy / LiteLLM）。代理负责注入 per-session 账号凭证 + 域名白名单。一招同时给出稳定出口 IP（代理的 IP）和账号注入（agent 永不接触凭证），与选哪个编排器无关——这应作为 Foundagent 防封与凭证层的默认架构。",
          "双凭证现实在 2026 变了，订阅 token 不再是免费套利：claude setup-token 仍发 1 年期 CLAUDE_CODE_OAUTH_TOKEN（绑 Pro/Max/Team/Enterprise、仅推理、无自动刷新→长跑到期即断，#12447）；且 6-15 起订阅的程序化/第三方 agent 用量先扣每月‘Agent SDK credits’、再按 API 费率扣 usage credits（4-4 曾一度全禁）。落地建议：生产规模用 API key + Managed Agents；订阅 token 仅用于额度可控、能接受 1 年期 + credit 上限的有界推理负载。",
          "按工作负载选编排形态：(a) 大量轻量委派用 Agent SDK subagents（context 隔离、5 层嵌套、可 resume）→ 超大规模升 Workflow 工具（后台 runtime 跑 JS 脚本，单 run ≤16 并发/≤1000 agent，仅同一活跃会话内可恢复，退出即重跑）；(b) 需要互相辩论/协作的对等 agent 用 Agent Teams（截至 v2.1.186 仍实验、约 7x token、3-5 人、in-process teammate 不随 resume 恢复）或 Trellis channel（AGPL-3.0、16 平台、git-worktree 扇出、.trellis 记忆持久）。Foundagent 的‘CEO founder 带部门’在协作语义上像 (b)，但要无人值守、跨会话持久、每 session 隔离时落到 Managed Agents 会话最稳。",
          "规模化成本由 token 扇出主导，而非编排 license：子 agent/团队扇出≈单会话 7x token；Managed Agents 还叠加 $0.08/session-hour（N 个常驻 founder session≈N×约$58/月仅运行时，未含 token）；企业级 Claude Code 平均约 $13/开发者/活跃日。控本杠杆：把子阶段路由到 Sonnet/Haiku、teammate 限 3-5、空闲即关 session、用 Workflow 的 agent 上限兜底、对共享 context 用 prompt caching。"
        ]
      },
      {
        "dimension": "Agent 身份 / 账号注入 (Agent Identity & Account Injection) — virtual email, SMS/phone verification, virtual cards/payments, secrets management, and credential-injection layers for provisioning and operating believable, scalable founder-agent identities",
        "options": [
          {
            "name": "AgentMail",
            "url": "https://www.agentmail.to/pricing",
            "category": "Virtual email — programmatic per-agent inbox built for AI agents",
            "description": "API-first email provider that gives each agent its own real, persistent inbox. Programmatic inbox creation, send/receive with full threading, attachments, real-time delivery via webhooks + WebSockets, IMAP/SMTP access, custom domains with DKIM/SPF/DMARC, an MCP server for tool integration, Python/TS SDKs, and multi-tenant 'Pods' for platform builders.",
            "pricing": "Verified on pricing page: Free $0/mo (3 inboxes, 3,000 emails/mo, 100/day, 3GB). Developer $20/mo (10 inboxes, 10k emails/mo, unlimited daily, 10GB, 10 custom domains). Startup $200/mo (150 inboxes, 150k emails/mo, 150GB, 150 custom domains, SOC 2 report). Enterprise custom (unlimited inboxes, white-label, EU-region cloud, bring-your-own-cloud, DEDICATED IPs, OIDC/SAML SSO).",
            "computerUseSupport": "Not a Computer Use target itself; it is the email backend. During a Computer Use signup the agent fills the form in the browser, then reads the verification/OTP email programmatically via API, webhook, or the MCP server (directly callable by Claude-based agents).",
            "staticIpAntiBlock": "No proxy/IP layer for browsing. Anti-block value: real custom-domain addresses with proper DKIM/SPF/DMARC pass signup-form checks that reject temp-mail domains (which are widely blacklisted and are themselves a block signal). Enterprise tier adds DEDICATED IPs for inbound/outbound deliverability — useful so the agent's own outbound business email isn't flagged.",
            "deployment": "Cloud (SaaS). Partial self-direction via IMAP/SMTP and bring-your-own custom domain; Enterprise offers bring-your-own-cloud.",
            "pros": [
              "Purpose-built for autonomous agents — per-agent inbox maps 1:1 onto 'each agent session is its own founder'",
              "Generous free tier; Developer $20/mo and Startup $200/mo (150 inboxes) are cheap per identity",
              "MCP server + Python/TS SDKs make agent integration trivial",
              "Custom domains (DKIM/SPF/DMARC) avoid the temp-mail blacklist problem; Enterprise dedicated IPs aid deliverability"
            ],
            "cons": [
              "Cloud-only custody — all agent email lives with a third party",
              "Newer/smaller vendor than incumbents (longevity risk)",
              "Inbox caps per tier mean cost grows roughly linearly with fleet size beyond 150 inboxes"
            ],
            "relevanceToFoundagent": "Strongest fit for the email-identity slice and the easiest part to make believable. Give each founder-agent a persistent custom-domain inbox (e.g. founder@yourbrand.com) so it can register for services, receive OTP/confirmation emails programmatically during browser signups, and keep a real cross-session communication record for its 'business.' Use custom domains (never temp-mail) and reserve dedicated IPs for agents that send outbound customer email. At ~$1.33/inbox/mo on the Startup tier it scales cheaply for the first ~150 agents.",
            "verified": true
          },
          {
            "name": "MailSlurp",
            "url": "https://www.mailslurp.com/product/email-address-api/",
            "category": "Virtual email + SMS API for automation (catch-all domains)",
            "description": "Provision disposable, expiring, permanent, or custom-domain inboxes in code, including catch-all domains that funnel any address into controlled inbox pools. Receive email via polling or webhooks, AI-powered parsing for structured OTP extraction, plus real phone numbers and SMS flows, deliverability/render testing, and SPF/DKIM/DMARC domain monitoring.",
            "pricing": "Has a 'Start free' tier; full paid pricing lives only on the in-app page (app.mailslurp.com/pricing) which is auth-gated and NOT captured this session — treat exact numbers as unverified before budgeting.",
            "computerUseSupport": "Same pattern as AgentMail — backend for OTP/confirmation retrieval during Computer Use signups; also offers SMS numbers so one vendor can cover both email and phone OTP.",
            "staticIpAntiBlock": "No browsing IP layer. Catch-all + custom domains give believable addresses; combined SMS reduces vendor sprawl. Disposable-domain inboxes carry the usual temp-mail block risk, so prefer custom/catch-all domains for real signups.",
            "deployment": "Cloud (SaaS).",
            "pros": [
              "Single vendor for both email AND SMS/phone — fewer integrations",
              "Catch-all domains scale to effectively unlimited per-agent aliases under one purchased domain",
              "Mature, automation-focused, strong SDK coverage and webhooks",
              "Built-in deliverability/DMARC monitoring helps keep identities credible"
            ],
            "cons": [
              "Exact paid pricing not captured from a primary source (flag: verify before committing)",
              "Positioned for QA/testing rather than long-lived agent operations",
              "Cloud-only; no MCP server (you wrap the REST API yourself)"
            ],
            "relevanceToFoundagent": "Best consolidation play: one API for email + SMS identity, and the catch-all-domain model lets a single purchased domain back thousands of agent aliases for a fraction of per-inbox pricing — attractive once the fleet outgrows AgentMail's per-inbox tiers. Weaker than AgentMail on agent-native ergonomics (no MCP) and unconfirmed pricing.",
            "verified": true
          },
          {
            "name": "5sim",
            "url": "https://5sim.net/",
            "category": "SMS / phone verification — rentable virtual numbers",
            "description": "Online SMS-verification marketplace offering temporary virtual numbers across ~150–180 countries for receiving OTPs from specific services (Amazon, Google, Telegram, WhatsApp, OpenAI, Instagram, etc.). Developer REST API, single-use activations and longer rentals, large live-number pool with daily replenishment.",
            "pricing": "Pay-per-use, no monthly fee; entry pricing roughly $0.01 per number with per-service variation (WhatsApp/Telegram cost more). Prices fluctuate by service/country and stock — treat figures as approximate. Money-back if no SMS arrives in the activation window.",
            "computerUseSupport": "Complements Computer Use: agent reaches the 'enter phone number' step, requests a number via API, polls the API for the inbound code, types it into the browser. No native MCP/agent SDK — wrap the REST API.",
            "staticIpAntiBlock": "No browsing IP layer; actually a block RISK — numbers are shared/recycled and many are VOIP, so major services (Google, WhatsApp, banks) frequently reject or later flag them, and accounts can be banned.",
            "deployment": "Cloud service consumed via API.",
            "pros": [
              "Extremely cheap per OTP — viable at fleet scale for low-stakes gates",
              "Large country/service catalog with a clean API",
              "No subscription; refund on failed delivery"
            ],
            "cons": [
              "Recycled/VOIP numbers are commonly pre-flagged or banned by big platforms",
              "Throwaway-number verification commonly violates target-service ToS → agent accounts terminated",
              "No durable ownership of a number for re-login/2FA later",
              "Legal grey zone for some uses/jurisdictions; exact pricing volatile"
            ],
            "relevanceToFoundagent": "Cheapest way to clear a one-time phone gate, but the WEAK link in a 'believable founder identity': recycled numbers undermine the realism the project wants and can't receive 2FA weeks later when the agent must re-login. Use only for disposable, low-stakes signups — never for a business account the agent must keep.",
            "verified": true
          },
          {
            "name": "SMS-Activate",
            "url": "https://sms-activate.io/",
            "category": "SMS / phone verification — rentable virtual numbers",
            "description": "Large competitor to 5sim for receiving OTP/PVA codes on virtual numbers across 180+ countries. Offers one-time activations (~20 min validity) and rentals from hours to weeks with unlimited inbound SMS, a documented API (api2), a 'Free Price' bidding system, and a VIP loyalty program for discounts.",
            "pricing": "Pay-per-use; entry pricing around $0.05+ depending on service/country (API returns per-number price JSON), rentals higher for the window, VIP up to ~40% cheaper. Full refund if no SMS within ~20 min. Prices fluctuate — approximate.",
            "computerUseSupport": "Same integration model as 5sim — wrap the REST API to request a number and poll for the code mid-signup. No agent-native SDK/MCP.",
            "staticIpAntiBlock": "No browsing IP layer; same recycled/VOIP block risk as 5sim. Rentals give a number you hold longer (better for repeat 2FA during a session) but still not a clean carrier identity.",
            "deployment": "Cloud service consumed via API.",
            "pros": [
              "Rental mode supports unlimited inbound SMS over days/weeks (useful for ongoing 2FA in a longer session)",
              "Very broad service/country coverage and mature API",
              "Loyalty/Free-Price mechanisms lower cost at volume"
            ],
            "cons": [
              "Same ban/flag risk and ToS exposure as all shared-number services",
              "Pricing varies widely and unpredictably by service/country",
              "Russia-origin vendor — sanctions/payment/compliance considerations for some operators"
            ],
            "relevanceToFoundagent": "Interchangeable with 5sim; its rental mode is slightly better when an agent needs to receive 2FA repeatedly across a multi-hour session. Keep both as fallbacks since stock/quality for any given target service fluctuates daily — but still a disposable-gate tool, not a durable identity.",
            "verified": true
          },
          {
            "name": "Twilio Verify (+ Programmable SMS numbers)",
            "url": "https://www.twilio.com/en-us/verify/pricing",
            "category": "Owned phone numbers + legitimate verification",
            "description": "Enterprise multi-channel verification (SMS, voice, email, WhatsApp, push, TOTP, Silent Network Auth) with a managed number pool and built-in compliance/localization. Separately, Twilio Programmable Messaging rents dedicated long-code/toll-free numbers that can receive inbound SMS programmatically via API/webhook.",
            "pricing": "Verified: Verify = $0.05 per successful verification + channel fees (US SMS +$0.0083). Owned numbers: long code ~$1.15/mo, toll-free ~$2.15/mo, plus US A2P 10DLC brand registration ($4.50–$46 one-time) and campaign registration ($15 one-time + recurring monthly).",
            "computerUseSupport": "Verify is for verifying YOUR OWN users, not for receiving OTP from third-party services. The relevant piece for Foundagent is renting a real Twilio number whose inbound SMS the agent reads via API/webhook to capture codes from external signups.",
            "staticIpAntiBlock": "No browsing IP layer. Twilio numbers are recognizably VOIP and rejected by many consumer platforms (Google, WhatsApp, banks); US A2P registration is mandatory and adds friction. More durable than throwaway services but not 'invisible.'",
            "deployment": "Cloud (SaaS) with robust API/webhooks.",
            "pros": [
              "Reputable, reliable, well-documented; durable owned numbers good for persistent 2FA/re-login",
              "Strong webhook/API tooling and SLAs",
              "Compliance/regulatory machinery handled for you"
            ],
            "cons": [
              "Numbers are flagged as VOIP and blocked by many target services",
              "Per-number monthly cost + A2P registration overhead make per-agent scaling expensive vs $0.01 throwaway numbers",
              "Not designed to defeat third-party verification"
            ],
            "relevanceToFoundagent": "Best when a founder-agent needs a STABLE, owned number it controls for the life of its business (recurring 2FA, customer comms, re-login) rather than a one-shot OTP. Pair with throwaway services for disposable gates; reserve Twilio (or a real eSIM) for the agent's persistent 'business line.' VOIP detection still limits which platforms will accept it.",
            "verified": true
          },
          {
            "name": "Privacy.com (for AI Agents)",
            "url": "https://agents.privacy.com/",
            "category": "Virtual cards / payments — agent spend control (turnkey)",
            "description": "Consumer-grade virtual card platform with controls enforced at the authorization layer (over-cap transactions are declined before approval, not refunded after). Per-card spend limits, pause/unpause/close on demand, merchant-locked cards, plus CLI, REST API, and an MCP server (mcp.privacy.com) for Claude/Cursor. Issued via Patriot Bank (US, FDIC). PCI-DSS compliant, SOC 2 Type II, 256-bit encryption.",
            "pricing": "Tiered consumer plans: Personal (free; foreign-tx fee 3% / $0.50 min), plus Plus/Pro/Premium (Pro/Premium waive foreign-tx fees). Funded from a linked US bank account.",
            "computerUseSupport": "Agent generates/retrieves a scoped card via API/MCP/CLI (e.g. `privacy cards create --spend-limit <n>`), then types the card details into a checkout during a Computer Use flow. Auth-level caps mean a misbehaving agent literally cannot overspend.",
            "staticIpAntiBlock": "No browsing IP layer. Provides real (not prepaid-gift) card numbers that pass merchant checks better than many prepaid cards; merchant-locking limits blast radius if details leak.",
            "deployment": "Cloud (SaaS) + API/CLI/MCP.",
            "pros": [
              "Hard, pre-authorization spend caps are ideal guardrails for autonomous spend",
              "MCP + CLI + API make it directly agent-operable TODAY with the least setup",
              "Single-merchant locking and instant close limit fraud/runaway spend",
              "Fast, low-friction card creation"
            ],
            "cons": [
              "US-only: requires a US bank account/identity (KYC) — all cards trace to one shared identity",
              "Consumer product, not a multi-tenant issuing platform; per-agent legal-entity separation is unclear",
              "Card velocity/limits may throttle a large fleet"
            ],
            "relevanceToFoundagent": "Best turnkey 'give the agent a card with a hard ceiling' option for a US-based operator, and the fastest to wire up (MCP today). Excellent safety properties (auth-level caps + instant kill switch) for an autonomous founder, but the single underlying KYC identity means every agent's card ultimately ties back to you — fine for a controlled pilot, limiting for truly independent identities.",
            "verified": true
          },
          {
            "name": "Stripe Issuing for Agents (+ Agent Toolkit)",
            "url": "https://docs.stripe.com/issuing/agents",
            "category": "Virtual cards / payments — programmatic, policy-gated issuance",
            "description": "Full card-issuing platform with a dedicated 'Issuing for agents' product. Programmatically create virtual cards with spending controls (per-card/rolling limits, MCC/allowed-category restrictions, country blocks, specific-merchant blocks), single-use cards that auto-cancel after one cleared authorization (`lifecycle_controls.cancel_after.payment_count=1`), per-agent metadata, and a real-time `issuing_authorization.request` webhook (2s timeout) where your own code approves/declines every transaction. Funded from an Issuing balance, Treasury (US), or stablecoin-backed cards (private preview, 30+ countries).",
            "pricing": "No setup fees; per-program pricing via Stripe sales (interchange-share / per-card / per-transaction). Funded via Issuing balance / Treasury / stablecoin wallet.",
            "computerUseSupport": "Explicitly agent-oriented: create a single-use card scoped to one purchase via API, hand the number/expiry/CVC to the agent for checkout, and enforce arbitrary policy in your own code through the real-time auth webhook. Verified concrete API examples on the /issuing/agents docs page.",
            "staticIpAntiBlock": "No browsing IP layer. Real Visa/Mastercard network cards with per-card and per-transaction policy; single-use auto-cancel cards minimize exposure and look legitimate to merchants.",
            "deployment": "Cloud (SaaS) with deep API + sandbox. Standard Issuing in US, UK, EEA; stablecoin-backed programs in 30+ countries (private preview).",
            "pros": [
              "Industrial-strength single-use/scoped cards with metadata — the cleanest 'one card per agent task' model, now first-class for agents",
              "Real-time authorization webhook = enforce ANY spend policy (budget, merchant, velocity, fraud) in your own code before the charge clears",
              "Programmatic monitoring/reconciliation/dispute APIs for an agent's ongoing operations",
              "Mature platform, strong docs/sandbox; stablecoin funding extends reach beyond US/UK/EEA"
            ],
            "cons": [
              "Requires being an underwritten Stripe Issuing platform/business (heavier KYC/onboarding than consumer cards)",
              "Pricing opaque (sales-gated)",
              "Cards fund from YOUR balance under one corporate identity — scoped budgets per agent, not separate legal identities",
              "Stablecoin-backed cross-border cards still in private preview"
            ],
            "relevanceToFoundagent": "The most powerful payments primitive for the project: programmatic, single-use, policy-gated cards tagged with agent metadata fit 'each session is an isolated founder with a scoped budget,' and the real-time auth webhook lets your orchestrator veto any purchase. Higher onboarding cost than Privacy.com but far more control, auditability, and scale — the right backbone once the fleet is past pilot.",
            "verified": true
          },
          {
            "name": "Crossmint Agentic Payments",
            "url": "https://www.crossmint.com/solutions/agentic-payments",
            "category": "Virtual cards / payments — global agent stack (wallets + cards + stablecoin)",
            "description": "Single-API stack giving agents fiat + stablecoin wallets with programmable spending caps, merchant whitelisting, and human-approval-above-threshold, plus virtual card numbers derived via Visa Intelligent Commerce, stablecoin rails in 150+ countries, x402 (in production) + Google AP2 protocol support, and Merchant-of-Record services that handle returns/chargebacks/compliance.",
            "pricing": "Sales-gated; not published. Funding via fiat onramps and stablecoins.",
            "computerUseSupport": "Agent wallet + derived virtual card numbers are created via API in minutes; the agent then pays at any merchant (card) or machine-to-machine (x402/stablecoin), covering both Computer-Use checkouts and direct API/tool payments without a human in the loop.",
            "staticIpAntiBlock": "No browsing IP layer. Real Visa card numbers + wallet-level limits/whitelisting; global stablecoin rails sidestep card-network geo limits.",
            "deployment": "Cloud (SaaS), global (stablecoins in 150+ countries, fiat globally).",
            "pros": [
              "Broadest geographic reach (global, not US/UK/EEA-limited) — best for international agent identities",
              "Covers both human-merchant card payments AND machine-to-machine payments (x402 in production, AP2) the agent economy is moving toward",
              "Per-agent wallets with spend limits + merchant whitelisting + approval thresholds map cleanly to per-session founders",
              "Merchant-of-Record offloads compliance, returns, and chargebacks"
            ],
            "cons": [
              "Pricing and KYC/onboarding requirements opaque (sales-gated) — verify before committing",
              "Crypto/stablecoin component adds operational and regulatory complexity",
              "Younger ecosystem; agentic-payment protocols (x402/AP2) still stabilizing"
            ],
            "relevanceToFoundagent": "Most forward-looking option and the only one that is truly global + supports emerging agent-to-agent payment protocols. Strongest if Foundagent operates internationally, needs agents to pay for APIs/tools/other agents autonomously (not just consumer checkouts), or wants Merchant-of-Record to absorb compliance. Pick over Stripe when global reach or machine-to-machine payments matter more than Stripe's maturity.",
            "verified": true
          },
          {
            "name": "Anon",
            "url": "https://www.anon.com/",
            "category": "Account injection — managed authenticated sessions for agents on sites without APIs",
            "description": "Developer platform that lets AI agents securely access and operate accounts across the web — including sites with no official API — by managing the login/session lifecycle (OAuth, SSO, 2FA) under a zero-trust architecture. Credentials are stored in a dedicated vault and used server-side so secrets never enter the agent's context window; agentic sessions can spawn child sessions, pause/resume across infra restarts, and be interrupted by orchestrator policy. NOTE: confirm you are using anon.com / the developer auth platform — a separate 'Anon' brand does AI search visibility (GEO/SEO).",
            "pricing": "Sales/developer-gated; not published. Verify before budgeting.",
            "computerUseSupport": "Directly complementary to Computer Use: rather than re-solving login/2FA in the browser on every run, Anon injects an authenticated session so the agent starts already logged in, and re-establishes it across restarts — reducing repeated CAPTCHA/OTP friction during automated flows.",
            "staticIpAntiBlock": "No browsing IP layer of its own. Anti-block value is indirect: persisting real authenticated sessions avoids the repeated fresh-login pattern that triggers anti-bot challenges.",
            "deployment": "Cloud (SaaS) developer platform with SDK/API.",
            "pros": [
              "Solves the 'log the agent back in' problem across sessions and infra restarts — true cross-session persistence",
              "Server-side credential injection keeps tokens out of the LLM context (matches secure agent patterns)",
              "Works on sites without official APIs; handles OAuth/SSO/2FA",
              "Session model (child sessions, pause/resume, policy interrupts) fits a long-running founder-agent"
            ],
            "cons": [
              "Oriented toward delegating an EXISTING human/user identity to an agent, not minting fresh independent identities — partial fit for 'each agent is its own founder'",
              "Pricing/onboarding opaque",
              "Brand-name collision (anon.com vs an unrelated AI-visibility 'Anon') — verify the right product"
            ],
            "relevanceToFoundagent": "Fills the gap the email/phone/card providers don't: keeping a founder-agent logged in to the dozens of services it uses, across sessions and VM restarts, without re-running fragile browser logins each time. Best used as the session/credential-injection layer on top of a secrets vault — strongest when an agent must persistently OPERATE accounts it already created, rather than create brand-new ones.",
            "verified": true
          },
          {
            "name": "Infisical",
            "url": "https://infisical.com/pricing",
            "category": "Secrets management — open-source, self-hostable (the account-injection backbone)",
            "description": "Open-source (MIT core, ~27k GitHub stars) secrets platform that stores, syncs, and injects credentials across environments and workloads via an agent, CLI, Kubernetes/Docker, or native integrations. Markets explicitly to 'developers and agents.' Machine identities and the Infisical Agent injector are available on all tiers; RBAC and secret rotation are Pro+; dynamic short-lived secrets are Enterprise. SOC2/HIPAA/FIPS 140-3.",
            "pricing": "Verified: Free $0/mo (self-host or cloud; up to 5 identities, 3 projects, 3 environments, machine identities + agent injector). Pro $18/mo per identity (unlimited identities, RBAC, secret rotation, 12 environments). Enterprise custom (dynamic secrets, advanced controls). IMPORTANT CORRECTION: even self-hosted, the `ee/` directory (incl. dynamic secrets) is NOT MIT — dynamic/short-lived secrets require an Infisical enterprise license whether cloud or self-host.",
            "computerUseSupport": "Not a Computer Use target; it is the source of truth that injects each agent's email password, SMS-API key, card token, and service logins into its VM at boot. Dynamic secrets (Enterprise) can mint short-lived per-session credentials scoped to one agent.",
            "staticIpAntiBlock": "N/A (no browsing IP layer). Security value: per-agent machine identities and scoped secrets so a compromised/banned agent VM can't leak the whole identity pool.",
            "deployment": "Both — self-host on your own infra (keeps all injected agent identities in-house) or managed cloud.",
            "pros": [
              "Self-hostable + open-source core = full control over the master roster of all agent identities (critical when hoarding many sensitive accounts)",
              "Unlimited machine identities + agent/k8s/Docker injectors are FREE when self-hosted — fits one-VM-per-agent provisioning at scale",
              "Per-agent machine identities give clean isolation between sessions",
              "Active 2025–2026 momentum as the open alternative to Vault's BSL relicensing"
            ],
            "cons": [
              "CORRECTION vs prior draft: dynamic short-lived secrets are NOT free even self-hosted — they need an enterprise license (the ee/ dir is licensed, not MIT)",
              "Cloud Pro is priced per identity ($18/mo) — brutal for large fleets, so self-host is effectively mandatory at scale",
              "Self-hosting adds ops burden (you now run security-critical infra)",
              "Less mature than Vault for the most advanced dynamic-secret engines"
            ],
            "relevanceToFoundagent": "Top pick for the actual 'inject many accounts into each VM' problem. Self-host the MIT core: unlimited free machine identities + the agent injector cover provisioning the whole fleet, keeping every agent's emails/numbers/card tokens/logins under your control instead of a third party. Budget for an enterprise license only if you want true per-session dynamic/short-lived secrets; otherwise static scoped secrets per machine identity already give clean isolation. This is the backbone the email/SMS/card/Anon layers plug into.",
            "verified": true
          },
          {
            "name": "Doppler",
            "url": "https://www.doppler.com/pricing",
            "category": "Secrets management — SaaS, fastest env-var injection",
            "description": "Developer-friendly secrets manager that injects secrets as environment variables at runtime via the CLI (`doppler run`), service tokens, and service accounts, with config inheritance, automatic rotation, and activity logs. Known for 'zero to injected secrets in under 5 minutes.'",
            "pricing": "Verified: Developer free for 3 users, then $8/user/mo (service tokens, 50-token limit, API-based rotation). Team $21/user/mo (14-day trial, service accounts, automatic rotation; add-ons $9/seat each). Enterprise custom — dynamic secrets, proxied rotation, AND self-host (on-prem) are Enterprise-only.",
            "computerUseSupport": "Not a Computer Use target; injects the agent's credentials into the VM/process as env vars at startup. Service accounts suit headless/automated agent runtimes.",
            "staticIpAntiBlock": "N/A (no browsing IP layer). Scoping via service tokens/accounts limits blast radius per agent.",
            "deployment": "Cloud-first; on-prem/self-host exists but is Enterprise-only (correction vs prior draft, which said no self-host).",
            "pros": [
              "Fastest, simplest setup and excellent DX for env-var injection",
              "Clean per-environment/per-service scoping and rotation",
              "Generous free tier for small fleets"
            ],
            "cons": [
              "Self-host and dynamic secrets are both gated to Enterprise — so SaaS custody for everyone else (all sensitive agent identities live in Doppler's infra)",
              "Per-USER pricing scales awkwardly vs machine-heavy agent fleets",
              "No agent-native MCP; env-var model only"
            ],
            "relevanceToFoundagent": "Great if you want least-friction credential injection and accept SaaS custody for a small pilot. For Foundagent's hoard-many-accounts model, cloud-default custody plus Enterprise-gated self-host/dynamic-secrets make self-hosted Infisical the stronger primary, with Doppler a fast-start alternative or for non-sensitive config.",
            "verified": true
          },
          {
            "name": "1Password Secrets Automation",
            "url": "https://www.1password.dev/secrets-automation/",
            "category": "Secrets management — built on 1Password vaults",
            "description": "Extends 1Password into a developer/automation secrets platform. Two modes: Service Accounts (no extra infra, via the 1Password CLI) and self-hosted Connect servers (REST API + caching + SDKs). `op run` resolves secret references and injects them as env vars into a command/runtime. Included with a 1Password subscription.",
            "pricing": "Bundled with 1Password Business/Teams subscription (per-user). No separate Secrets Automation fee surfaced.",
            "computerUseSupport": "Not a Computer Use target; `op run` injects the agent's credentials as env vars at VM/process launch. Connect server gives a programmatic REST endpoint agents can call.",
            "staticIpAntiBlock": "N/A (no browsing IP layer). Connect can be self-hosted for in-infra caching/control.",
            "deployment": "Both — Service Accounts (cloud-backed) or self-hosted Connect server.",
            "pros": [
              "Familiar, trusted vault if the team already uses 1Password — humans and agents share one store",
              "Self-hosted Connect option for in-infra caching and higher throughput",
              "Simple env-var injection via op run; agents can reuse human-saved logins"
            ],
            "cons": [
              "Service Accounts have strict rate limits (Connect needed for scale) — friction when many VMs pull secrets at boot",
              "Per-user subscription model is unnatural for large machine/agent fleets",
              "Primarily a password manager; fewer advanced dynamic-secret engines than Infisical/Vault"
            ],
            "relevanceToFoundagent": "Reasonable if you already standardize on 1Password and want one human-and-agent vault — and uniquely, agents can reuse logins a human saved into shared vaults. For a scaling fleet hammering the store at VM startup, self-hosted Connect is required, and Infisical/Vault are more machine-native — so this is a secondary choice.",
            "verified": true
          }
        ],
        "keyInsights": [
          "Architect this dimension as three layers, not one: (1) identity SOURCES that mint new identities (email: AgentMail/MailSlurp; phone: 5sim/SMS-Activate/Twilio; cards: Stripe Issuing/Privacy.com/Crossmint); (2) a secrets VAULT/INJECTION backbone that stores every agent's passwords, API keys, and card tokens and injects them into each VM at boot (self-hosted Infisical recommended); and (3) a SESSION/credential-injection layer (Anon) that keeps a founder-agent logged in across sessions and VM restarts. Sources create identities; the vault + Anon operate them over time.",
          "CORRECTION to the prior draft on Infisical: dynamic/short-lived secrets are NOT free even when self-hosted — the ee/ directory is licensed (not MIT) and dynamic secrets require an enterprise license whether cloud or self-host. The right read for Foundagent: self-host the MIT core to get UNLIMITED free machine identities + the agent injector (covers the whole fleet, all accounts stay in-house), and pay for an enterprise license only if you specifically need per-session dynamic secrets/rotation. Cloud Pro is $18/mo PER IDENTITY, which is prohibitive at fleet scale, so self-host is effectively mandatory. Doppler gates both self-host and dynamic secrets to Enterprise, reinforcing Infisical as the primary.",
          "Email is the easiest part to make believable and cheap: AgentMail's per-agent inbox is a 1:1 fit (free tier, MCP server, custom domains with DKIM/SPF/DMARC, and Enterprise dedicated IPs for outbound deliverability; ~$1.33/inbox/mo at the 150-inbox Startup tier). MailSlurp's catch-all domains back effectively unlimited aliases under one purchased domain for fleets that outgrow per-inbox pricing. Hard rule: use CUSTOM domains, never temp-mail domains — temp-mail is widely blacklisted and is itself a block signal.",
          "Phone/SMS is the weakest link for a believable identity and the hardest to persist. Recycled VOIP numbers from 5sim (~$0.01) and SMS-Activate (~$0.05) clear one-shot OTP gates cheaply but are routinely rejected or later banned by Google/WhatsApp/banks and can't receive 2FA weeks later for re-login. Twilio gives durable owned numbers (good for persistent 2FA/customer comms) but is recognizably VOIP and adds US A2P 10DLC registration plus ~$1.15+/number/mo. Strategy: throwaway numbers for disposable low-stakes signups; an owned Twilio number or a real eSIM for any account the agent must KEEP.",
          "For agent payments, hard pre-authorization spend caps are the decisive safety property. Stripe Issuing now ships a first-class, documented 'Issuing for agents' product (docs.stripe.com/issuing/agents): per-agent virtual cards with metadata, single-use cards that auto-cancel after one cleared charge, and a real-time issuing_authorization.request webhook (2s) where your orchestrator approves/declines every transaction — the cleanest 'one scoped card per agent task.' Privacy.com is the fastest turnkey path (MCP + CLI today, auth-level caps) but is US-only with one shared KYC identity. Crossmint is the only global option and the only one supporting machine-to-machine protocols (x402 in production, Google AP2) plus stablecoins in 150+ countries.",
          "KYC is the structural ceiling on identity independence: every payment option ultimately ties back to YOUR underwritten legal entity/bank, so you cannot mint truly separate FINANCIAL identities at scale without separate legal entities — Stripe/Privacy/Crossmint give scoped budgets per agent, not separate cardholders of record. Combined with tightening 2025 fraud/synthetic-ID detection and the fact that throwaway-number/temp-mail verification commonly violates target-service ToS, plan for graceful account rotation and loss, not perfect evasion or perfectly independent identities.",
          "Account INJECTION and identity CREATION are different problems that need different tools, and the project needs both. The email/phone/card providers CREATE fresh identities; Anon and the secrets vault INJECT/operate existing credentials — keeping the founder-agent logged in across sessions and restarts with tokens served SERVER-SIDE so secrets never enter the LLM context window. Anon is oriented toward delegating an existing identity (partial fit for 'each agent is its own founder'), so use it to persist operation of accounts the agent already created.",
          "Anti-block / static-IP is NOT this dimension's job — it belongs to the proxy/residential-IP dimension; none of these providers supply a browsing IP. This layer's job is to not BE the block signal: a believable founder-agent = aged custom-domain email (not temp-mail) + a less-recycled or owned/eSIM number (not fresh VOIP) + a real funded card (not prepaid gift) + persisted real sessions (Anon) + a non-datacenter IP from the proxy layer. Footnote: HashiCorp Vault remains the gold standard for dynamic secrets but its 2023 BSL relicensing is exactly why teams moved to MIT-core Infisical in 2025–2026; choose Vault only if you need its mature dynamic-secret engines and accept the license/ops weight."
        ]
      }
    ]
  }
}