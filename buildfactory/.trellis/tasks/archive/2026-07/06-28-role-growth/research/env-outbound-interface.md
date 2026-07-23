# Growth 环境调研 — outbound 账号接口（本地代码核实）

> 来源：`vm/cua_mcp.py`、`vm/docker/agent-mcp.json`、`vm/docker/Dockerfile.agent`、`peripheral/adapters/`、`agents/growth.yaml`。全部本地核实，非推测。
> 结论：**Open Q1 已解 —— growth 操纵账号 = Computer Use（CUA），不是平台 API。**

## 1. outbound = CUA（Computer Use），subscription-only

- growth 的 `mcp_config: /opt/foundagent/mcp.json`，经 `Dockerfile.agent:29 COPY docker/agent-mcp.json /opt/foundagent/mcp.json` → 实际是 **`cua-local` MCP server**（`cua_mcp.py`）。**已确认 growth 拿到 CUA。**
- `cua_mcp.py` 暴露的是**原子 Computer Use 原语**（操作一个 `cua-ubuntu` Linux 桌面容器）：
  - `screenshot()` / `get_screen_size()`
  - `left_click(x,y)` / `double_click(x,y)`
  - `type_text(text)` / `press_key(key)`
- **关键架构约束**：docstring 明确"**deliberately NOT cua-mcp-server**：不套第二个 API-key 的 cua-agent LLM，Claude 自己(跑在用户 subscription)直接调这些原语当大脑"。→ **整套是 subscription-only、无第二个 API-key 模型**。
- `peripheral/adapters/` 只有 `webhook` + `email`，且都是 **inbound**（native→IME）。**没有任何社媒 outbound adapter**。hub.py 里的"outbound IME"是编排消息，与社媒无关。

**含义**：growth 用账号 = **像人一样操作桌面/浏览器**（截图→定位→点击→输入→发布），不是调 API。这正是"外设层让他操纵账号"的落地形态。

## 2. `use-accounts` 定性

- **v1 可行**（接口是真的、已到 growth 手上）。
- 本质 = **Computer-Use GUI 操作 skill**：① 系统特定（CUA 原语 + screenshot→act 循环 + 逐平台 UI 导航）+ ③ 非平凡（坐标点击很脆、要靠截图自检、错误恢复）。**强 ① + ③，正当自写。**
- **现成模型可借**：本地已装 `wechat-desktop` skill（`~/.claude/plugins/cache/ClaudeWechat/.../skills/wechat-desktop/`）——**完全同一范式**（screenshot+click+type 操作桌面 App），带 workflows：`send-file` / `forward` / `quote-reply` / `broadcast` / `scheduled-monitoring`。→ `use-accounts` 的结构/循环/自检模式**直接参考它**，别从零编。

## 3. `visual-asset` 出了个真岔路（Open Q2 收窄、变硬）

- **环境里没有任何生图工具**（grep `image_gen/dall/stable-diffusion/imagen/flux` 全空）。唯一的"手"是 CUA。
- 叠加**subscription-only 约束**：接一个付费生图 API **违背架构取向**（cua_mcp 刻意不引第二个 API-key 模型）。
- 选项：
  - **A. 程序化/模板化 asset**（桌面上 HTML/CSS/SVG → 截图成 PNG，或 PIL）：确定、无 API、适合 quote card / 轮播 / og-image；弱在照片级图像。
  - **B. CUA 驱动网页生图工具**（浏览器里开免费生图站，生成→下载）：守住 subscription-only，但脆、慢。
  - **C. 接生图 API/MCP**：能力强，但**破 subscription-only**。
  - **D. v1 先不做真生图**：visual-asset = 模板卡片，照片级图押后。
- **待用户拍**（倾向 A 或 D，最贴 subscription-only + 确定性）。

## 4. 对 verifier 立场的加强（呼应 design §2.1）

CUA 让 verifier 能**独立截图/登号核查**帖子在不在、对不对 → 进一步证明 growth **无需给 verifier 喂 proof**。§2.1 立场更稳。

## 5. 对 design 的回填（web scouting 回来后一并 consolidate）

- §10 Q1 → `use-accounts` 写 against CUA 原语；参考 `wechat-desktop`。
- §10 Q2 → 收窄成 A/B/C/D 四选。
- §1 外设层描述 → 补"outbound = CUA"。
- §4 backlog：`use-accounts`、`visual-asset` 定形。

## 6. 用户方向修订（本轮，覆盖上文结论）

> findings（CUA 是当前唯一 wire 的 outbound、无生图工具）**属实且保留**；但**设计方向**按用户意见修订，覆盖 §2/§3 的倾向。

1. **outbound 改 MCP 优先，CUA 降为低效回退**。用户：CUA 是"token 消耗最大、最不稳定"的 outbound 方式。方向 = 优先用 **MCP**（平台/账号 MCP、软件 MCP，或**自写轻量 MCP/skill**）；CUA 仅在某平台无 MCP 时兜底。→ **`use-accounts` 写 against 平台 MCP（优先）**，`wechat-desktop`(CUA) 仅作回退样板。
   - **未决**：具体装/写哪些账号 MCP？当前环境只 wire 了 CUA → 这是 **MCP provisioning**（infra，可能属兄弟任务）。用户明确"这块还要再看"。→ 影响 `use-accounts` v1 是否随 MCP 就绪再落。
2. **subscription-only 澄清（纠正上文过度解读）**：该约束指 `cua_mcp` 不套第二个 *orchestrator* LLM，**不禁止装能力工具**。用户会为 agent 装 **GPT image-gen** 等生图工具。→ §3 的"接生图 API 破 subscription-only"**作废**。
3. **visual-asset = 复合能力（非单一机制）**：生图只是其一；还要 **HTML/组件化设计** + 生成后**修复迭代**。装工具、教 agent **用 + 编排**。→ §3 的 A/B/C/D 单选作废，改 design §5.5。
</content>
