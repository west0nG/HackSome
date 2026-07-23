# Memory Layer — Design / 技术设计

## 0. 选型结论

harness = **`company.py` CLI + `company-memory` Skill + session-end Stop Hook**（已拍板）。

理由：贴现有 `task.py` / skill / hook 风格；CLI 可在 host 上对临时目录直接单测（AC1–AC4、AC6 不依赖容器）；**导航维护与强制逻辑写进代码、而非靠 agent 自觉**，正好满足 R4（导航自动维护）/ R5（record_thought 必须执行）两条硬需求。

## 1. 边界与职责

- 记忆层只提供「读 / 写 / 组织 公司静态状态」的机制；**不涉及** Goal、任务指派、agent 间通信（属编排层）。
- 对外接口 = `company.py` 命令契约 + skill 约定 + hook 行为。上层（编排层 / agent yaml）通过「挂载 `company/` + 注入 skill/hook」声明式接入，不改本层代码。

## 2. 存储布局与不变式

```
companies/<company-id>/      # 单个 company 的根（容器内挂到 /company）；顶层 companies/ 容纳多个 company
├── MAP.md                   # 根导航/索引：列出顶层主题 + 一行说明 + 指针
├── <topic>/
│   ├── OVERVIEW.md          # 本层导航：列出子项（子主题 + 叶子）+ 一行说明
│   ├── <doc>.md             # 叶子：markdown 知识文档（公司状态）
│   ├── <asset.mp4|png|csv…> # 叶子：任意格式资产（视频/图片/表格/PDF…）
│   └── <subtopic>/          # 支持嵌套，每层都有自己的 OVERVIEW.md
│       └── OVERVIEW.md
```

**不变式（由 `company.py` 维护，不是 agent 手工）：**
- INV1 根永远有 `MAP.md`。
- INV2 每个非根目录永远有 `OVERVIEW.md`。
- INV3 `MAP`/`OVERVIEW` 列出的条目 == 该层实际子项（导航与磁盘一致）。
- INV4 叶子可为**任意格式**（md 知识文档 / 视频 / 图片 / 表格 / PDF 等）；md 写入为 **in-place 覆盖更新**、不 append 流水账，资产按文件整体覆盖。

## 3. `company.py` 命令契约

| 命令 | 作用 | 自动副作用 |
|---|---|---|
| `read [PATH] [--raw]` | 渐进式披露读：空→`MAP.md`；目录→该层 `OVERVIEW.md`；md 文件→正文；**资产默认→描述符（路径/类型/大小/说明），不吐裸字节**。`--raw` = 按需取内容：文本类资产给文本、二进制给绝对路径（供浏览器/图像查看等打开）。空 `company/` 返回 cold-start 提示 | — |
| `tree [PATH] [--depth N]` | 只返回导航骨架（名字 + 一行说明），不返回正文，供 agent 决定下钻点（控 token，撑 AC2） | — |
| `write PATH --content\|--file F [--summary S]` | 创建/覆盖叶子（in-place）：`--content` 写 md 文本；**`--file` 拷入任意格式资产** | 建父目录、补齐各层 `OVERVIEW.md`、登记进父 `OVERVIEW`、顶层主题登记进 `MAP`；`--summary` 写导航一行说明；type 自动判定（目录=topic / .md=doc / 其他=asset） |
| `record [--summary S] [--nothing]` | **session 收尾必调**：把本程知识 / 资产 / 状态变更蒸馏后做 in-place 写入（复用 write 引擎）+ 落「本 session 已记录」运行时标记（在 company 根之外，供 hook 校验）。**`--nothing` / 无变更 = 记空、合法**；不写流水账 | 同 write 的导航维护 |

- **并发**：对 `MAP`/`OVERVIEW` 的更新加文件锁（`flock`），避免并行容器写坏导航。强一致 / 冲突合并推迟。
- **路径安全**：所有 PATH 限制在 `company/` 内（防穿越）。

### 3.1 导航自动维护机制（INV3 怎么保证 / 回答「自动改 OVERVIEW/MAP 怎么实现」）

- 每个 `OVERVIEW.md` / `MAP.md` = **YAML front-matter（CLI 拥有的 `entries` 机器源）** + 其下**自动渲染的 markdown 列表（给 agent 读的视图）**。例：
  ```yaml
  ---
  entries:
    pricing.md:   { type: doc,   summary: "定价与套餐" }
    demo.mp4:     { type: asset, summary: "30s 产品演示" }
    competitors:  { type: topic, summary: "竞品分析" }
  ---
  ```
- 每次 `write` / `record`：① 落文件（或拷资产）→ ② 更新所在目录 nav 的 front-matter entry（type 自动判定）→ ③ 用 front-matter 重渲染该文件的 markdown 视图 → ④ 与磁盘实际子项 **reconcile**（多/少的条目自动增删）。即使文件被带外改动，下次操作也会纠偏 → **INV3 by construction**。
- agent 只读渲染出的视图，**不碰 front-matter**（写进 skill 禁忌）。
- 选 YAML front-matter 当机器源、而非解析自由 markdown：前者解析稳、不易被 agent 的散文写法弄坏。

## 4. Skill：`company-state`

materialize 进 agent 的 `~/.claude/skills/`。约定：
- **开局**：先 `company.py read` 拿 `MAP`，用 `tree`/`read` 按需下钻；**别 `ls -R`** 整棵树。
- **期间**：公司状态有变就 `company.py write <主题路径> --summary ...`；**主题怎么分你自己定**（按信息领域，不按部门）；文档写「当前态」，不要写流水。
- **收尾**：**必须** `company.py record`（本程无新增就记空）。
- **禁忌**：导航文件（`MAP`/`OVERVIEW`）由 `company.py` 维护，**别手改**。

## 5. Hook：session-end 兜底（撑 AC5）

agent hooks（`settings.snippet.json`）注入一个 **Stop hook**：
- Stop 时检查运行时标记（本 session 是否**调过** `record`）。
- **调过即放行**（哪怕记的是空）；**完全没调** → 返回 `decision: "block"` + `reason`「你必须先 `company.py record` 再结束」，逼模型补走（Claude Code Stop hook 的 block 语义）。
- 兜底只读标记、**不替 agent 蒸馏**（蒸馏是认知，必须 agent 做）。
- 降级：若某非交互场景下 block 不适用，则降级为「注入 reason + 记一条告警」。

## 6. 挂载与接入（复用 VM / Agent / 编排层）

- **host**：数据在仓库根的 `companies/<company-id>/`（**gitignore**，不进代码仓库；可后续做成各自 git 仓库）；工具代码放 `company_state_kit/`（含 `company.py` + 测试）。
- **容器**：broker / agent 层把**选定的** `companies/<id>/`（rw 共享）挂到 `/company`、`company_state_kit/`（ro）挂到 `/opt/company_state_kit`，并设 `COMPANY_ROOT=/company`；`company.py` 据此定位 company 根。哪个 company 由启动方（编排层）选定。与 per-account 的 `accounts/<id>/workspace` 区分开。
- 新增一个「启用记忆」的 agent yaml（`skills: [company-state]`、`hooks:` 指向 stop hook），证明声明式接入、零代码改动。
- `company.py` 安装方式 MVP 用挂载（免重建镜像）；烤进镜像作为后续硬化。

## 7. AC 映射 + 测试手段

| AC | 满足方式 | 测试 |
|---|---|---|
| AC1 冷启动+生长 | write 自动建 MAP+主题+OVERVIEW+叶子 | host 对空临时目录跑 write，pytest 断言结构 |
| AC2 渐进式披露读 | read/tree 只返回路径所需 | pytest 断言不含无关分支正文 |
| AC3 导航自动维护 | write 维护父 OVERVIEW/MAP | pytest 断言新指针存在且与磁盘一致 |
| AC4 in-place 更新 | write/record 覆盖同一 doc | pytest 断言被更新而非新增 |
| AC5 record 收尾 | Stop hook 校验标记（调过即过、没调才拦） | 脚本测试模拟 Stop 三情形（没调 / 记空 / 有内容） |
| AC6 共享可见 | company/ 公司级共享 | 两顺序进程（模拟两 session）写/读，pytest 断言可见 |
| AC7 多格式资产 | write --file 拷入 + nav 标 type=asset；read 返回描述符 | pytest：写 .png/.csv，断言 nav 有 type / 说明、read 不吐裸字节 |
| AC8 多公司隔离 | company.py 按指定 root 操作 | pytest：两个 root 互不影响 |
| 端到端 | 容器内真跑启用记忆的 agent | 集成测试 / 人工，验证 AC1+AC6 |

## 8. Tradeoffs / 风险

- **CLI vs MCP**：选 CLI 换 host 可测性 + 与 `task.py` 一致；代价是 agent 走 Bash 而非结构化 Tool Use。
- **导航维护在代码侧**：可靠（撑 R4），代价是 `company.py` 「拥有」导航格式，agent 不能手改导航（已写进 skill 禁忌）。
- **并发**：MVP 仅 `flock` 防导航损坏；多 agent 真并发协作的强一致推迟到编排层。
- **兜底 block**：headless 非交互场景可能不适用，已留降级路径。
