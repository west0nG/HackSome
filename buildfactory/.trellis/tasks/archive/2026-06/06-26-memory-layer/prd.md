# Memory Layer（公司记忆层）

## Goal / 目标

为 Foundagent 的每个 agent 提供一套「公司记忆」系统：

1. 一个承载公司**全部静态状态信息**（公司当前是什么样 + 运营信息）的文件存储 `company/`；
2. 一套让 agent 能**读取、写入、并自行组织**这些信息的 harness。

核心原则：**记忆层只管「名词」（公司当前状态），不管「动词」（任务 / 通信 / Goal）**。它与编排层、Goal 注入解耦。我们标准化「形式」（不变式 + 工具），把「内容结构」（主题怎么分）交给 agent 按每个 business 自行决定。

## Background / 背景

- v6 四层骨架第 3 层（VM 层、Agent 层已 done 并归档；编排层 MVP broker 在 in_progress）。
- broker 已预留 `accounts/<id>/workspace` 的挂载机制；本层提供的是**公司级共享**的 `company/`，区别于 per-account 工作区。
- 不照搬 Matrix / Paperclip；它们只作参考。

## Requirements / 需求

**R1 公司记忆存储（多公司）**
- 顶层一个容器目录 `companies/`，**可容纳多个 company**；每个 company 一个独立文件夹 `companies/<company-id>/`，内含该公司的 `MAP` / 主题 / 文档 / 资产。（下文 `company/` 指**单个** company 的根目录）
- 单个 company 文件夹承载该公司的所有信息 + 运营信息 = 该公司**当前静态状态**。
- **公司级共享**（同一 company 跨 agent / session 共享，不是 per-account）；容器启动时把**选定的** `companies/<id>/` 挂到固定路径 `/company`。
- **冷启动**：全新 company 从空开始，**不预铺**任何主题结构。

**R2 信息组织：主题制 + agent 自划**
- 按信息**主题 / 领域**组织，**不按部门**；无部门信息墙，任何 agent 可读任意主题（"跨部门访问"退化为"读另一个主题"）。
- 主题分类**不由系统固定**，由 agent 按每个 business 自行划定、按需生长。

**R3 渐进式披露（读挡）**
- 入口 `MAP.md`（根索引，session 启动读的第一份）；每个目录一份 `OVERVIEW.md`（本层导航）；叶子为具体内容。
- agent 默认只见顶层，按需沿 `MAP → OVERVIEW → 叶子` 下钻；不强制把整棵树读进 context。

**R4 导航自动维护（写挡）**
- agent 新增 / 修改 / 移动内容时，所在层级的 `OVERVIEW` / `MAP` 导航被**自动保持一致**，不依赖 agent「记得」手动更新。
- 写入语义是**更新对应主题文档以反映最新状态（in-place）**，而非往流水账 append。

**R5 `record`（收尾写挡）**
- 一个 session 收尾**必须执行**的动作：把本程值得留下的东西（知识 / 资产 / 状态变更）蒸馏后写回该 company 对应主题。
- **允许空**：本程确实无新增时，`record` 可记空、合法；强制只针对「压根没走这一步」。
- 强制机制：session-end Stop hook（详见 `design.md`）。

**R6 与系统调试日志隔离**
- 容器内的 JSONL transcript 是「优化系统用」的 debug log，**不属于记忆层**，不作为 agent 可读记忆。

**R7 多格式资产（wiki 与 assets 合一）**
- `company/` 不只放 markdown 知识文档，还承载公司**全部资产**：视频、图片、表格（csv/xlsx）、PDF 等任意格式。
- 资产与描述它的知识文档**同处一个主题目录**（assets 旁边就是对应的 wiki）。
- 非文本资产：导航里有一行说明 + 类型标记；`read` **默认**返回**描述符（路径 / 类型 / 大小 / 说明）**而非裸字节；**但资产可读**——agent 按需可取其内容（文本类资产直接给文本，二进制给绝对路径供浏览器 / 图像查看等工具打开）。

## Acceptance Criteria / 验收标准

> 全部 AC 已验证（2026-06-28）：55 host 测试（`company_state_kit/tests` + `agent/tests`）+ 真实双 session 容器 e2e（cold-start 写入 / 渐进式披露 / 跨 session 读取 / CLI↔hook marker 一致）；`trellis-check` 判定 PASS。

- [x] **AC1 冷启动 + 生长**：对一个空 `company/`，agent 在一个 session 内能创建首批主题与内容；结束后 `company/` 含合法的 `MAP.md` + 至少一个主题目录及其 `OVERVIEW.md` 与叶子文档。
- [x] **AC2 渐进式披露读**：新 session 的 agent 仅凭 `MAP.md` 起步，能按需下钻定位到某条既有信息，且无需把整棵树读进 context（读取量随路径深度增长，而非随总量）。
- [x] **AC3 导航自动维护**：agent 新增一个主题 / 叶子后，其父层 `OVERVIEW` / `MAP` 自动包含该新节点的指针；人工核对导航与实际目录一致。
- [x] **AC4 in-place 更新**：对已存在的某条状态信息再次 record，结果是该文档被更新为最新态，而非新增重复 / 流水记录。
- [x] **AC5 record 收尾**：session 收尾会触发 `record`（允许记空）；**完全没走 record 时** Stop hook 兜底拦截、逼其补走（机制见 `design.md`）。
- [x] **AC6 共享可见**：agent A 写入的信息，agent B 在其后的 session 能通过渐进式披露读到（验证 `company/` 是公司级共享、跨 agent 可见）。
- [x] **AC7 多格式资产**：能把非 md 资产（如 .png / .mp4 / .csv）写入某主题，导航登记其说明 + 类型；`read` 默认返回描述符（不吐裸字节），**按需可取内容**（文本类给文本、二进制给绝对路径）；md 文档照常按文本读。
- [x] **AC8 多公司隔离**：`companies/` 下两个不同 company 各自独立；对 company A 的读写不影响 company B；`company.py` 按指定的 company 根目录操作。

## Out of scope / 明确不做（推迟，遇到再修）

- 园丁 / librarian 自动防熵增、定期重整 taxonomy。
- 主题 split / merge / rename 的**专用重整工具**（MVP 先靠基本写入 + 导航维护；复杂重整推迟）。
- Goal 的注入机制（属编排层 / 单独议题）。
- Agent 间任务指派 / 通信（编排层）。
- 多 agent **并发**写 `company/` 的强一致 / 冲突合并（MVP 可简单处理，方案见 `design.md`）。

## Constraints / 约束

- Python 3.13；复用 Agent 层契约（headless `claude`、skill / hook 落地点）与 broker 的容器挂载机制。
- 写给用户读的部分用中文；代码 / 注释 / 契约用英文。
