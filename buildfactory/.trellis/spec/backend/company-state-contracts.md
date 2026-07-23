# V7 Company State 契约

> 当前自动化已经验证挂载权限、Agent-facing 指引和旧存储层删除；原生目录在
> 长期自主运行中的发现质量、重复率和可维护性仍待下一次真实 Company 实验验证。

## 场景：Agent 原生访问 Company State

### 1. 范围与触发条件

当代码、Prompt、Skill、Agent runtime 挂载或结果验收涉及 `/company` 时，必须遵守
本契约。`/company` 保存公司当前知道、决定、拥有、构建和测量到的持久状态；它不是
运行日志，也不是编排状态的原始存储入口。

设计决定是让文件系统目录和 leaf 成为唯一结构事实，删除独立 Company 存储 CLI、
必需索引、保留导航文件名与第二份目录镜像。渐进式披露和维护质量由共享 Skill
约束，而不是由另一层 Python 文件 API 模拟。

### 2. 签名与入口

运行时挂载：

```text
CEO / Department / Worker:
  state/<company>/company:/company

Verifier:
  state/<company>/company:/company:ro
```

冷启动由 operator 创建空目录：

```bash
make shared COMPANY=<company>
```

Agent 直接使用 runtime 已有的原生文件工具，没有 Company 专属读写命令或环境变量。
Worker 完成真实工作后只发送空业务 payload：

```json
{}
```

这个调用只推进 Goal 进入独立验收，不携带 Company State 引用、摘要或证据索引。
`/company` 只在真实工作自然改变长期共享状态时维护；外部工作不要求复制进公司文件夹。

### 3. 契约

#### 3.1 可见性与权限

- `/company` 是所有 Agent 唯一可以直接浏览的公司数据树。
- CEO、Department、Worker 完整读写；Verifier 同一路径只读。
- `control / telemetry / reviews / workers / inbox / ledger / departments /
  notes / agents / sessions` 不得挂载进任何 LLM runtime。
- Objective、自己的 Notes、单条消息和逻辑方法列表由 Hub 注入 Prompt；它们不是
  `/company` 文件。
- 固定 CEO 和动态 Department、Worker、Verifier 不挂载额外 Company 存储工具。
- 同一份 `company-state` Skill 源通过统一 loadout 同时物化给 Claude Code 与 Codex。

#### 3.2 渐进读取

读取成本必须随任务相关性增长，而不是随整个 Company 大小增长：

1. Goal 或 acceptance 已指出精确 `/company/...` 路径时先读取该路径。
2. 否则只列根目录直接子项或最多一到两层浅层路径。
3. 根据描述性目录名和文件名进入最相关的局部区域。
4. 名称不足时，在该区域执行限定路径、模式或结果集的搜索。
5. 只打开支撑当前判断所需的少量 leaf。

禁止无目的地递归列出整个树、输出所有正文的无界搜索，或为了“了解公司”批量
读取全部文件。README、索引类文件或其他说明文档只是普通 Company 内容，不能自动
假设其比磁盘现状更权威。

#### 3.3 原生维护

- 写入前查看目标目录并搜索同一主题；已有权威文档时优先原地更新。
- 共享目标可能被其他 Agent 修改时，覆盖前重新读取。
- 按业务主题组织，不按 Agent、Worker 或 Department 建信息墙。
- 使用打开前就能表达内容含义的具体、稳定名称，避免无语义通用文件名。
- 维护当前状态，不追加 wake、session、尝试、读取或完成活动流水。
- 只有时间本身属于持久主题或证据时，才在文件名中加入日期。
- 资产放在其业务主题的自然位置，二进制内容由相应原生 viewer 按需打开。
- 可以创建、移动、重命名和删除内容；删除或替换前确认不会丢失事实、来源、
  交付物或仍被验收引用的证据。
- 没有真实持久业务变化时不写任何文件或空标记。

空 `/company` 是合法状态，不需要初始化文件。原生文件系统不提供应用级事务、
语义合并或 Company 专属写锁；本版本不额外实现这些机制。

### 4. 校验与错误矩阵

| 条件 | 必须发生的结果 |
|---|---|
| 全新 Company 目录为空 | Agent 正常冷启动；第一次有持久变化时才创建自然路径 |
| Goal 或 acceptance 给出精确 leaf | 直接检查该 leaf，不先扫描整个 Company |
| 精确 leaf 缺失或不可访问 | Agent 不得假装存在；Verifier 将缺失证据计入 verdict |
| Agent 需要更多背景 | 先浅层列举，再在相关子树做限定搜索和少量读取 |
| Agent 准备写入已有主题 | 先查目录与同主题内容，优先更新权威 leaf |
| Verifier 尝试写入 | 只读挂载拒绝；Skill 同时明确禁止任何创建、移动、重命名或删除 |
| 路径指向内部编排目录 | runtime 不应存在该挂载；Agent 只能使用对应确定性方法 |
| Worker 提交摘要、路径、URL 或其他结果字段 | Hub 拒绝业务 payload；只接受空完成声明 |
| 二进制资产需要检查 | 使用 image、PDF、browser、video 等合适 viewer，不把原始字节批量输出到上下文 |
| 两个 Agent 可能更新同一 leaf | 覆盖前重新读取；本版本仍是文件系统写入语义，不承诺自动合并 |
| 目录中存在 README 或索引类文件 | 视为普通内容；只有与磁盘事实一致且当前任务相关时才使用 |

### 5. 正常、基础与错误案例

- **Good**：Goal 指向 `/company/product/pricing.md`；Agent 先读该文件，必要时只在
  `/company/product/` 搜索相关材料，更新现有定价文档后发送空完成声明。
- **Base**：空 Company 第一次形成定位结论；Agent 创建语义明确的主题目录与
  `positioning.md`，不创建空索引或 session marker。
- **Good**：Verifier 根据 Goal 和 acceptance 独立判断真实结果所在位置，检查只读
  `/company`、公开网页或已认证外部账户，再提交 verdict。
- **Good**：Worker 完成一次只存在于外部账户中的发布操作，不额外创建 `/company` 文件。
- **Bad**：运行无界递归命令并读取全部正文，只为了获取一般背景。
- **Bad**：每次 wake 新建一个日期结果文件，导致同一业务事实产生多个并行版本。
- **Bad**：为了启用 Company 浏览，把 Ledger、Inbox、Notes 或 telemetry 原始目录挂载
  给 Agent。

### 6. 必需测试

- `orchestration/tests/test_v7_mount_boundaries.py`
  - Worker、Department 的 `/company` 为读写；Verifier 为只读；
  - 所有动态 runtime 不挂载内部状态或额外 Company 存储工具；
  - 旧 Company 存储环境变量不重新出现。
- `orchestration/tests/test_compose_accounts.py`
  - 固定 CEO 保留 `/company` 和 account 注入；
  - 不挂载内部状态或额外 Company 存储工具。
- `orchestration/tests/test_agent_loop_v7.py`
  - resident wake 的 COMPANY ENTRY 明确原生目录、浅层列举和限定搜索；
  - 不依赖预生成导航入口。
- `agent/tests/test_operate_twitter_skill.py`
  - specialized Skill 复用原生渐进式发现与直接持久化；
  - 不重新教授已删除的存储入口。
- `agent/tests/test_company_state_skill.py`
  - 固定原生浅层发现、限定搜索、写前查重、描述性命名和谨慎删除；
  - 固定只读 Skill 的精确证据优先与禁止 mutation；
  - 防止已删除的存储协议重新进入两个 Company State Skill。
- `agent/tests/test_skill_catalog.py`
  - `company-state` 与只读版本对 Claude Code / Codex 保持同一合法 Skill 入口和预算。

完整质量门：

```bash
.venv-cua/bin/python -m compileall -q agent orchestration peripheral
.venv-cua/bin/python -m pytest agent/tests/ orchestration/tests/ peripheral/tests/
docker compose config -q
```

### 7. 错误与正确示例

错误：把整个 Company 一次性输出到上下文，并无条件创建另一份结果。

```bash
find /company -type f -exec sh -c 'printf "--- %s ---\\n" "$1"; cat "$1"' _ {} \;
# 然后写 /company/research/result-2026-07-19.md，未检查已有主题
```

正确：先看浅层结构，在相关子树中缩小范围，读取并更新已有权威 leaf。

```bash
find /company -mindepth 1 -maxdepth 2 -print
rg -l "pricing|target customer" /company/product
sed -n '1,220p' /company/product/pricing.md
# 用 runtime 的原生编辑工具更新 /company/product/pricing.md
```
