# 将 Company Wiki 降级为 Agent 原生文件夹

## 目标

把 `/company` 从必须经由 `company.py` 读取和维护的受管 Wiki，改成 Agent 使用原生文件能力直接浏览、搜索、创建、编辑和整理的共享文件夹。渐进式披露和内容维护规则由 Agent Skill 教授，不再由 Python CLI、`MAP.md` 或 `OVERVIEW.md` 强制实现。

## 背景与已确认事实

- `/company` 已经是所有 LLM runtime 唯一可直接浏览的公司数据树。
- CEO、Department 和 Worker 对 `/company` 拥有读写挂载；Verifier 对同一路径只有只读挂载。该权限边界由容器挂载实现，不依赖 `company.py`。
- 当前 `company-state`、`company-state-readonly`、`operate-twitter` 和 resident wake prompt 显式依赖 `company.py`、`MAP.md` 或 `OVERVIEW.md`。
- `company.py` 同时实现旧 Wiki 的 read/tree/write、导航同步、锁、资产描述和程序化 snapshot/delete/restore，但程序化存储接口目前没有生产调用方，只有其专属单元测试引用。
- 现有 `/company` 原生可写挂载本来就允许 Agent 绕过 CLI，因此旧 CLI 的路径、锁和导航不变量不是完整的系统强制边界。
- 用户选择直接删除旧管理层及其测试，以保持代码库整洁；需要回退时使用 Git 历史恢复。
- 用户明确不要求迁移或清理现有 `state/*/company/` 运行数据，也不要求本任务新增实验遥测。

## 需求

### R1：原生 Company 文件夹

- Agent 使用自身可用的原生文件工具直接读取、搜索和维护 `/company`。
- 空 `/company` 是合法冷启动状态；第一次持久化业务内容时按需要创建目录和文件。
- 正常工作路径不得依赖 `company.py` 或任何预生成索引。

### R2：Skill 中的渐进式披露

- Agent 从 `/company` 根目录的浅层列表开始，只进入与当前任务相关的目录。
- Agent 根据描述性目录名和文件名筛选候选内容，再读取少量相关正文。
- Agent 不得无目的地递归列出或读取整个 `/company`，也不得把整个公司状态一次性载入上下文。
- 当文件名不足以定位信息时，Agent 使用限定范围的原生搜索继续缩小范围。

### R3：Skill 中的维护约定

- 写入前先查看目标目录并搜索相关内容，优先更新已有事实，避免重复文档和并行真相。
- 使用清晰、具体、稳定且能表达内容含义的目录名和文件名。
- 内容按业务主题组织，不按 Agent、Worker 或 Department 建立信息墙。
- 保存公司当前知道、决定、拥有、构建和测量到的持久状态，而不是 wake、session、尝试次数、读取记录或活动流水。
- 读写角色可以使用原生能力创建、更新、移动、重命名和删除内容；执行重组或删除前必须确认内容已经过时、重复或被新位置完整承接，不得误删仍承担事实或验收证据的文件。
- 资产与解释其业务含义的相关内容放在自然的主题位置；二进制资产通过适合的原生查看工具按需打开。

### R4：取消强制导航结构

- 新 Company、新目录和新文件不要求生成 `MAP.md`、`OVERVIEW.md`、front matter 摘要或 `.company.lock`。
- `MAP.md`、`OVERVIEW.md`、README 或其他说明文件可以作为普通业务内容存在，但不是保留名称、CLI 所有物或全局不变量。
- 系统不维护磁盘内容与独立导航镜像之间的一致性。

### R5：删除旧管理层

- 删除 `company_state_kit` 中服务于旧 Wiki CLI、导航不变量和专属测试契约的实现。
- 删除固定与动态 runtime 中仅用于暴露 `company.py` 的挂载和环境变量。
- 删除或改写 Agent Skill、specialized Skill、wake prompt、README、后端规范和测试中的旧入口与旧不变量。
- 仓库中不保留未使用的兼容副本或迁移脚本。

### R6：控制面与验收边界保持不变

- Objective、Goal、Inbox、Ledger、Notes、权限、review、Worker 生命周期和其他编排状态继续通过 Company Hub 的确定性方法或 prompt 投影访问。
- 这些内部状态仍不得作为原生文件挂载给 Agent。
- Worker 继续在提交结果前把持久交付物写入 `/company`；`submit_result` 继续提交绝对的 `/company/...` leaf 路径。
- Verifier 继续以只读方式检查这些实际 leaf，不能修改 Company State。

### R7：实验与回退边界

- 本任务不新增正式指标、遥测或新的观察系统。
- 首次效果观察使用现有 telemetry、运行日志和 Company 目录快照。
- 实现不修改、删除或迁移 `state/*/company/` 中的现有运行数据，也不以其内容驱动兼容逻辑；其中的旧导航文件在新契约下只是普通现有文件。
- 代码回退通过 Git 历史完成，不提供运行数据回滚或兼容迁移。

## 验收标准

- [x] AC1（R1、R2）：可写角色的 Agent-facing 指引完整描述原生发现、限定搜索、按需读取和直接维护 `/company`，不要求调用 `company.py`。
- [x] AC2（R3）：Skill 明确包含写前查重、描述性命名、主题式组织、更新当前状态和谨慎重组/删除规则。
- [x] AC3（R1、R4）：空 Company 和没有 `MAP.md` / `OVERVIEW.md` 的任意目录在契约上完全有效。
- [x] AC4（R4、R5）：仓库的有效代码、Skill、Prompt、README、规范和测试不再把 `company.py`、`MAP.md`、`OVERVIEW.md`、`.company.lock` 或 `COMPANY_ROOT` 作为 Company State 协议的一部分。
- [x] AC5（R5）：`company_state_kit` 实现与专属测试被删除；固定和动态 runtime 不再挂载该目录，且没有失效挂载或孤立引用。
- [x] AC6（R6）：CEO、Department、Worker 的 `/company` 读写挂载和 Verifier 的只读挂载仍由自动化测试固定。
- [x] AC7（R6）：Objective、Goal、Inbox、Ledger、Notes、review、权限与生命周期的确定性边界及 `submit_result` 的 `/company/...` leaf 契约不变。
- [x] AC8（R5）：`company-state-readonly` 和 Verifier prompt 引导直接检查被引用的原生路径，同时继续禁止写入。
- [x] AC9（R5）：依赖 Company State 的 specialized Skill（至少 `operate-twitter`）不再绕过新原生契约或教授旧 CLI。
- [x] AC10（R7）：实现 diff 不包含 `state/*/company/` 运行数据、数据迁移工具或新增遥测。
- [x] AC11：更新后的相关单元测试、完整 Agent/Orchestration/Peripheral 测试和 Compose 配置校验通过。

## 非目标

- 不重新设计 Company Hub 控制面或更改角色权限模型。
- 不清理、转换或重新索引已有 Company 运行数据。
- 不引入数据库、向量检索、全文索引服务、新 Wiki 产品或替代索引格式。
- 不证明说明文件永远无用；只取消其系统级强制性。
- 不在本任务中评价原生方案的长期效果或设计正式量化指标。
