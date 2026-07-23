Facts verified against the installed code. All loop registrations and the default model match the research. Here is the report.

---

# Foundagent VM 层架构决策报告：cua-agent 是否为 computer-use 专门优化？双层 vs 单层

> 面向 Foundagent v6（CEO → 部门 → 执行者）的 VM/computer-use 层选型。所有代码引用已对 `/Users/weston/dev/BuildFactory/.venv-cua` 实装版本核验。

---

## 1. 结论先行

**是。cua-agent 是专门为 computer-use 优化的"loop-runner 框架"，而不是让通用 LLM 裸调 `click` 的薄壳。**

关键证据：`ComputerAgent.__init__` 用 `find_agent_config(model)` 按**模型名正则**把请求路由到 **16+ 个内置 agent loop** 之一（`agent/agent.py:293`），每个 loop 显式声明两类能力——`step`（完整 agent 循环：截图→推理→动作）与 `click`（纯像素定位 grounding），见 `agent/types.py:18 AgentCapability=Literal['step','click']`。它把"规划"与"像素定位"在架构上解耦，这正是"为 computer-use 优化"的结构性证据。

---

## 2. cua-agent 的 computer-use 优化：内置 loops 与专门模型

`ComputerAgent` 的核心是可插拔 loop。每个 loop 实现 `predict_step()`（一步 agent 循环）和 `predict_click()`（给图+元素描述 → 返回 `(x,y)`），并用 `get_capabilities()` 声明支持哪类能力。已对实装代码核验的注册表（`agent/loops/*.py` 的 `@register_agent` 正则）：

| Loop / 模型 | 注册正则（实装核验） | 能力 | 专门优化点 |
|---|---|---|---|
| **Anthropic CU**（Claude） | `r".*claude-.*"` (`anthropic.py:1481`) | step+click | 用 Anthropic **原生托管 `computer` 工具**；按模型自动选工具版本+beta header：Claude 4/3.7 → `computer_20250124`（beta `computer-use-2025-01-24`），Claude 3.5 → `computer_20241022`（`anthropic.py:36-67`） |
| **OpenAI CUA** | `r".*(^\|/)computer-use-preview"` (`openai.py:59`) | step+click | OpenAI `computer_use_preview` 工具，带 `display_width/height/environment` |
| **Gemini CU** | `r"^gemini-2\.5-computer-use-preview-10-2025$"` (`gemini.py:187`) | step+click | Google 原生 computer-use 模型 |
| **UI-TARS / UI-TARS-2**（ByteDance） | `r"(?i).*ui-?tars.*"` (`uitars.py:566`)，`uitars2.py:689` | step+click | **统一端到端 GUI agent**：单模型同时规划+定位，可独立当 operator，也能在 composed 里当 grounder。UI-TARS-2 用专门 `<seed:tool_call>` 输出格式解析 |
| **GTA1**（Salesforce AI） | `r".*GTA1.*"` (`gta1.py:75`) | **click only**（`predict_step` 直接 `NotImplementedError`） | 纯 grounding：Qwen 风格 `smart_resize` 分辨率对齐 + 系统提示"输出元素中心点 (x,y)" + temperature=0 + 坐标按 `scale_x/scale_y` 回映射原图 |
| **Holo1.5**（H Company） | `r"(?i).*(Holo1\.5\|Hcompany/Holo1\.5).*"` (`holo.py:118`) | **click only**（`NotImplementedError('only trained on UI localization')`） | Qwen2-VL smart_resize + JSON `{action:click_absolute,x,y}` + clamp |
| **OmniParser**（Microsoft） | `r"omniparser\+.*\|omni\+.*"` priority=2 (`omniparser.py:274`) | step | **Set-of-Marks (SOM)**：把编号元素 ID 叠在截图上，LLM 只做"多选题"选 ID，再由 bbox 中心反推 `(x,y)`——彻底回避 LLM 估像素 |
| **Moondream3** | `r"moondream3\+.*"` priority=2 (`moondream3.py:283`) | grounding 增强 | `detect`（拿 bbox）+ `caption`（标注）+ `point`（出坐标）三段增强 |
| **GLM-4.5V** | `r"(?i).*GLM-4\.5V.*"` (`glm45v.py:672`) | step | 智谱视觉 CU 模型 |
| **Qwen3-VL** | `r"(?i).*qwen.*"` priority=-1 (`qwen.py:236`) | grounding | 阿里视觉定位 |
| **Gelato / UI-Ins / OpenCUA / InternVL** | `.*Gelato.*` / `.*UI-Ins.*` / `.*OpenCUA.*` / `.*InternVL.*` | 多为 click | 各家专门 grounding；OpenCUA/InternVL 直接继承 `ComposedGroundedConfig` |
| **Composed（两阶段）** | **`r".*\+.*"` priority=1** (`composed_grounded.py:123`) | step | **核心两层架构**（见下） |

### 核心两阶段：`composed_grounded` loop（用户问的"两层设计"的真身）

模型名写成 `grounding_model+thinking_model`（如 `huggingface-local/HelloKKMe/GTA1-7B+anthropic/claude-sonnet-4-5`）即自动启用。流程（`composed_grounded.py`）：

1. thinking 模型只输出**动作 + 文字元素描述**（如"红色提交按钮"）——专用工具 schema `GROUNDED_COMPUTER_TOOL_SCHEMA` **故意只暴露 `element_description` 字段，不暴露 x/y**（`:28-92`）。
2. 对每个描述调 `grounding_agent.predict_click()`，**最多重试 3 次**直到拿到坐标（`:274-281` `for _ in range(3)`），存入 `desc2xy`，再把描述替换回真实 `(x,y)`（`:284`）。

> 即"规划脑不碰像素，专门定位模型负责像素 + 自纠错"。

---

## 3. 模型 / 凭证 / 成本

### 3.1 operator 能否用 Claude 订阅（Claude Code OAuth）？—— 不能

- cua-agent 鉴权 **100% 走 litellm**，只接受 API key / env var，构造函数只有 `api_key` / `api_base`（`agent/agent.py`），CLI 只认 `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `CUA_API_KEY`。全代码库 grep `oauth|subscription|claude code` **零命中**。
- Claude Code 的订阅 OAuth token（`sk-ant-oat...`）调 **Anthropic Messages API 会被明确拒绝**（"OAuth authentication is currently not supported"，GitHub `anthropics/claude-code` #37205，2026 仍未开放）。
- litellm 的"Claude Max 订阅"OAuth 透传**只存在于 proxy 层**且官方标注未完成/有 bug（`forward_client_headers_to_llm_api`；litellm issue #19618 / PR #19453：token 未被转发，报 `x-api-key header is required`）。cua 用的是 **SDK 直调**，拿不到这条路。

**结论**：订阅留给 **CEO 大脑层**（它本就跑在 Claude Code 上）。**VM operator 层无论单层双层，只要用 Claude 做 CU 就必须独立配 `ANTHROPIC_API_KEY` 按量计费**——订阅省不下这部分钱。

### 3.2 能否本地跑专门模型（Mac）？—— 能，且是一等公民

启动时注册 4 个本地 custom provider：`huggingface-local`、`human`、`mlx`、`cua`（`agent/agent.py:272-283`）。前缀决定 provider：

- **`mlx/...`**：`MLXVLMAdapter` 在 **Apple Silicon 原生**跑（`mlx_vlm.load/generate`），默认模型常量 `mlx-community/UI-TARS-1.5-7B-4bit`。7B-4bit 约 4-5GB 统一内存，单次 grounding `max_tokens=128`，延迟低，适合高频循环；首次加载约 18-25s。
- **`huggingface-local/...`**：Torch/MPS，如 `huggingface-local/HelloKKMe/GTA1-7B`、`ByteDance-Seed/UI-TARS-1.5-7B`。
- **`cua/...`**：cua 托管推理端点（`CUA_BASE_URL=https://inference.cua.ai/v1` + `CUA_INFERENCE_API_KEY`），可把 grounder 放远端，免本地显存。

**可本地的 grounding-only**：GTA1-7B、Holo1.5-7B、Moondream3、OmniParser（**必须配 planner**）。**可本地的 unified**：UI-TARS-1.5-7B / UI-TARS-2（可单独当完整 operator）。

### 3.3 成本对比

computer-use 循环里**绝大多数 step 是 screenshot→定位→click/type**，每步都要回传整张高 token 截图（image input）。

- **"每次点击都过 Claude"**（默认单模型方案）= 把**最高频、最低价值**的像素定位动作用**最贵**的 Claude image token 计费，Claude 调用频次 = O(每个原子动作)。
- **本地 grounder + 偶尔调 planner**：定位交给本地 MLX UI-TARS-7B-4bit（**无 per-token 费、电费近似 0**），Claude 调用降到 O(每个子任务)——数量级级别省钱。这正是 cua composite 博客明说的 cost optimization 逻辑（"小 grounding 模型扛高频，大 planner 仅在需要时调"，cua.ai/blog/composite-agents）。

⚠️ **注意**：cua-mcp-server 0.1.16 **开箱即最贵方案**——`server.py:159` 默认 `CUA_MODEL_NAME=anthropic/claude-sonnet-4-5-20250929`（已核验），即"Claude 直接做全部 computer-use"单模型。切换只需改这个环境变量，零代码改动。

---

## 4. 双层 vs 单层 推荐（针对 Foundagent CEO → 部门 → 执行者）

### 明确推荐：**双层为主、单层为辅、grounding 可热插拔**

cua 已把两种工具同时摆出来（`mcp_server/server.py`）：

- **单层（A）**：`screenshot_cua()` 直接返回一张图，由 CEO 自己决定下一步点哪（原子工具）。
- **双层（B）**：`run_cua_task(task)` / `run_multi_cua_tasks()`（支持并发）——内部 new 一个 `ComputerAgent` 跑**完整 operator 循环**（while: `predict_step` → 执行动作 → `sleep` 后自动截图回灌 → 直到最终消息，`agent/agent.py:599-718`），只回传聚合文本 + 终态图。Foundagent **不必二选一写死，两个工具都注册**。

### 为什么推荐双层（理由是结构性的，不是"换个更会点鼠标的模型"）

| 维度 | 双层收益 |
|---|---|
| **上下文隔离** | 每步全屏截图、失败重试、多轮 vision token 全关在独立 operator 进程里（默认 `only_n_most_recent_images=3`，已核验 `server.py:165`），CEO 只收到"成败 + 摘要 + 终态图"，不污染长程规划上下文 |
| **分层自治** | 天然契合 CEO→部门→执行器；可独立加 `budget_manager` 卡预算、`trajectory_saver` 回放调试 |
| **成本/失败收敛** | vision-heavy、易失败的循环集中在底层，CEO 不被低层像素操作占用 |
| **并发** | `run_multi_cua_tasks` 并发多 operator |

### Benchmark 证据（关键分裂）

| 基准 | 维度 | 数据 |
|---|---|---|
| **OSWorld**（端到端任务完成率） | **Claude SOTA，反超特化 operator** | Claude Sonnet 4.5 **61.4%**（2025-09 发布即 SOTA）> Opus 4.1 44.4% > UI-TARS-1.5 42.5% / GTA1-7B(+CUA) ~45.2% / OpenAI Operator 36.4% / Claude 3.7 28% |
| **ScreenSpot-Pro**（纯像素 grounding，高分屏专业控件） | **特化模型碾压 Claude** | UI-TARS-1.5 **61.6%** / GTA1-7B **50.1%**（32B 95.2% 标准变体）vs GPT-4o **0.9%** / 通用 MLLM <2% / Claude Computer Use **~17.1%** |

**关键洞察**：在**整体任务完成率**上 Claude 自己就是最强 operator（没有开源特化模型能压过它）——所以默认让 operator 用 `anthropic/claude-sonnet-4-5`（优先 Sonnet 控成本）。但在**纯像素定位**上 Claude 是弱项（专门视觉模型强项）——这正是 cua composed 两阶段存在的真正理由，也是"高分屏/专业软件点不准"时的补救手段。

> 一句话：**双层不是为了找个更强的点击模型（Claude 自己最强），而是为了上下文隔离、分层自治、成本/失败收敛与并发**——恰好是 zero-person company CEO 最需要的；grounding 弱项用 composed 模型按需补，凭证上 operator 层必须独立配 API key。

---

## 5. 对 Phase 2 的具体调整建议

### 走双层（推荐）—— operator agent 落地

1. **MVP 默认档（纯 API，立刻可用，零本地依赖）**：
   - operator = cua MCP 的 `run_cua_task`，`CUA_MODEL_NAME=anthropic/claude-sonnet-4-5-20250929`（当前默认值，已核验 `server.py:159`）。
   - 凭证：给 operator 进程独立配 `ANTHROPIC_API_KEY`（按量）。**不要**指望复用 CEO 的订阅。
   - 保留 `CUA_MAX_IMAGES=3` 控上下文/成本。

2. **遇到高分屏 / 专业软件点不准时（一行切换到 composed 两阶段，代码零改动）**：
   ```
   CUA_MODEL_NAME=huggingface-local/HelloKKMe/GTA1-7B+anthropic/claude-sonnet-4-5-20250929
   ```
   ComputerAgent 自动路由到 `ComposedGroundedConfig`（正则 `.*\+.*`）：Claude 思考出 element_description，GTA1 精确转坐标 + 3 次重试自纠。grounder 可走本地（需 GPU/显存）或 cua 远端推理端点（`cua/...` + `CUA_INFERENCE_API_KEY`）。

3. **成本敏感 / 想压到接近零（本地 Mac）**：
   - unified operator：`mlx-community/UI-TARS-1.5-7B-4bit`（Apple Silicon 原生，单模型端到端，可独立跑完整 agent loop）。
   - 或 composed：`mlx-community/UI-TARS-1.5-7B-4bit+anthropic/claude-sonnet-4-5`（本地 grounder + Claude planner）。
   - 代价：任务完成率低于 Claude 原生 CU，建议作为批量/成本敏感任务的备选档，而非默认。

### CEO 怎么委托

- 把**一个完整电脑任务**作为委派单元：CEO 调 MCP 工具 `run_cua_task(task="在 X 网站完成 Y")`，**不要让 CEO 自己循环 screenshot/click**。
- CEO 只负责下达任务 + 验收（收"成败 + 摘要 + 终态图"），多任务用 `run_multi_cua_tasks` 并发。
- CEO 大脑继续跑用户 Claude Code 订阅（OAuth）；operator 层独立 API key，两套凭证物理隔离。

### 若仍想保留单层（最后一公里 / 调试）

- 同时注册原子 `screenshot_cua`（+ 轻量 click/type MCP），仅在 **1-3 步轻量场景**用（确认弹窗、读一个值、operator 卡住时人工接管式纠偏）——享受最短反馈环。
- 即使单层也能保留专门化好处：通过 cua 的 `predict_click` 入口，让原子 click 走专门 grounding 模型（而非 CEO 裸估像素），即"CEO 出元素描述 → 专门模型出坐标"。

---

### 引用速查（模型 / loop / URL）

- cua composite-agents 官方理据：`cua.ai/blog/composite-agents`（"most language models lack precision in pixel-level coordinate prediction; specialized vision models … outperform general models"）
- 实装代码：`/Users/weston/dev/BuildFactory/.venv-cua/.../agent/agent.py`、`agent/loops/{anthropic,openai,gemini,uitars,uitars2,gta1,holo,omniparser,composed_grounded}.py`、`agent/decorators.py`、`mcp_server/server.py:159,165`
- GTA1：arxiv 2507.05791，github.com/Yan98/GTA1，`HelloKKMe/GTA1-7B`
- UI-TARS：arxiv 2501.12326，`ByteDance-Seed/UI-TARS-1.5-7B`，`mlx-community/UI-TARS-1.5-7B-4bit`
- OmniParser：arxiv 2408.00203，microsoft/OmniParser
- OSWorld：anthropic.com/news/claude-sonnet-4-5（61.4%）、os-world.github.io
- ScreenSpot-Pro：github.com/likaixin2000/ScreenSpot-Pro
- 凭证约束：github.com/anthropics/claude-code issue #37205；litellm docs/tutorials/claude_code_max_subscription、issue #19618 / PR #19453

---

**报告文件路径**（如需保存，本 Markdown 即交付物本身，未写入磁盘）。相关实装代码位于 `/Users/weston/dev/BuildFactory/.venv-cua/lib/python3.13/site-packages/agent/` 与 `/Users/weston/dev/BuildFactory/.venv-cua/lib/python3.13/site-packages/mcp_server/server.py`。