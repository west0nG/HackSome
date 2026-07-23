# 合并 Department Catalog 与 AgentSpec

## 目标

删除 `agents/departments/catalog.yaml` 这份重复配置，让每个
`agents/departments/<id>.yaml` 成为该 Department 的唯一声明来源，同时保持现有
Department 公开选项、创建权限、运行配置和生命周期行为不变。

## 背景与已确认事实

- 当前四个固定 Department 是 `strategist / researcher / builder / growth`，catalog
  条目与四个 AgentSpec 文件严格 1:1。
- catalog 中的 `agent_spec` 可由 Department ID 与文件名推导；`charter` 与 AgentSpec
  的 `system_prompt` 重复。
- catalog 中的 `skills`、`mcp_config` 与 AgentSpec 重复，且 Department 运行时实际读取
  AgentSpec；catalog 中这两个字段没有运行时消费者。
- `public_name`、`public_description` 与 `heartbeat_secs` 是 catalog 中仍被控制面使用的
  有效字段，应迁移到对应 Department YAML。
- CEO 通过 `list_department_options()` 只能得到 `id / name / description`；只有 CEO
  可以调用 `list_department_options` 与 `create_department`。公开边界由 Hub 的方法授权和
  投影实现，不依赖公开元数据是否单独存放在 catalog 文件中。
- 当前 Agent 容器只读挂载整个 `agents/` 代码资产目录。本任务保持该合作型信任边界，
  不把内部 YAML 对 Agent 做物理文件系统隔离。

## 需求

### R1：单一 Department 声明

- 删除 `agents/departments/catalog.yaml`。
- 四个 Department YAML 分别声明并拥有自己的 `public_name`、`public_description` 和
  `heartbeat_secs`。
- `name` 必须与文件名及固定 Department ID 一致。
- `system_prompt`、`skills`、`mcp_config` 继续只在 AgentSpec 中声明，不再保留第二份列表或路径。

### R2：固定目录与加载规则

- `DepartmentCatalog` 作为“固定 Department 集合”的代码抽象可以保留，但必须从
  `agents/departments/` 中的四个 Department YAML 加载，不再读取聚合 catalog 文件。
- 固定 ID、返回顺序和每类最多一个实例的约束保持不变。
- `agent_spec` 运行路径由 Department ID/文件名确定性推导。
- charter 运行路径由同一 YAML 的 `system_prompt` 推导。
- `heartbeat_secs` 必须是正整数；公开名称和公开描述必须是非空字符串。
- 缺失、额外或 ID 不匹配的 Department YAML 必须在加载阶段明确失败，不能静默形成部分目录。

### R3：公开接口和权限不变

- `list_department_options()` 的结果必须仍然严格只有 `id / name / description`。
- 不得向 CEO 暴露 provider、model、effort、credentials、system prompt、Skills、MCP、
  heartbeat、权限或文件路径。
- `list_department_options` 与 `create_department` 仍仅授权 CEO。
- `create_department` 的业务输入仍只有 `option_id` 与 `initial_objective`；CEO 不能覆盖内部
  Agent 配置。

### R4：运行行为不变

- 四个 Department 的 provider、model、effort、credentials、charter、Skills、MCP、权限、
  session、idle 和 strategic 配置保持现状。
- 四个 Department 的默认显式 heartbeat 保持 `900` 秒，并继续由系统注入，Agent 无权修改。
- 已创建公司的持久状态格式、Department 创建审核流程、容器命名、唯一实例限制和恢复语义不变，
  不需要状态迁移。

### R5：引用、测试与规范收口

- Hub、Department Provisioner、测试和规范不得继续引用 `catalog.yaml`。
- 删除 `DepartmentTemplate` 中没有运行时消费者的重复 `skills`、`mcp_config` 字段。
- 测试必须覆盖单一声明加载、严格公开投影、固定目录完整性、字段校验，以及启动参数仍使用正确的
  AgentSpec、charter 与 heartbeat。
- 更新 V7 后端契约，使签名和错误矩阵描述真实实现，不再要求 catalog 与 AgentSpec 双份配置同步。

## 验收标准

- [x] `agents/departments/catalog.yaml` 不再存在，仓库内没有有效代码、测试或活跃规范引用该路径。
- [x] 四个 Department YAML 都包含非空 `public_name`、非空 `public_description` 和
  `heartbeat_secs: 900`，其余运行配置与改造前等价。
- [x] Department 目录加载后仍按 `strategist / researcher / builder / growth` 返回四个选项。
- [x] 每个公开选项严格只含 `id / name / description`，且现有公开名称和中文描述不变。
- [x] 非 CEO 仍不能列出或创建 Department；CEO 仍不能通过创建 payload 指定内部配置。
- [x] 缺文件、多文件、`name` 与文件名不一致、空公开字段或非正整数 heartbeat 均有失败测试。
- [x] Provisioner 仍向容器提供正确的 `AGENT_SPEC`、由 `system_prompt` 推导的 charter，以及
  `AGENT_HEARTBEAT_SECS=900`。
- [x] 相关定向测试、完整 Python 测试门和 `docker compose config -q` 全部通过。
- [x] V7 后端契约已更新为单一 Department YAML 声明，并继续记录公开三字段投影边界。

## 范围外

- 不收紧 Agent 容器对只读 `agents/` 代码资产的文件系统可见性。
- 不新增、删除或重命名 Department，不改变固定顺序、唯一实例或创建审核流程。
- 不增加 per-company loadout overlay、动态模板注册、Department 退役或重建能力。
- 不修改 CEO、Worker 或 Verifier 的配置模型，除非是保持共享加载契约所必需的机械调整。
- 未经用户另行要求，不创建或更新 Pull Request（包括 PR #45）。
