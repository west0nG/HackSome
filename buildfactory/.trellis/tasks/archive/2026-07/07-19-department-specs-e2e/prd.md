# 验证 Department 单一声明 E2E

## 目标

在全新的隔离 Company 上运行一套真实 Docker E2E，证明删除
`agents/departments/catalog.yaml` 后：CEO 仍只能按“叫什么、有什么用”查看固定 Department
选项；CEO 能用公开 ID 创建 Builder；真实 Verifier 能审核其初始 Objective；真实 Builder
容器能从合并后的单一 YAML 正确启动。

## 已确认事实

- 改造提交 `027df46` 已在 `codex/catalog` 分支，四个 Department YAML 是唯一声明来源。
- 单元/集成层已有 440 项测试通过，但此前没有启动本分支的真实 Hub、Verifier 与 Department
  容器形成运行证据。
- Docker Server 与 `foundagent/cua-agent:latest` 已存在；主仓库
  `accounts/foundagent/` 中存在 `secrets.env` 与 `codex-auth.json`，测试只确认存在，不读取或记录内容。
- 工作树不自带 ignored account 文件，因此 E2E 期间需要一个临时、明确指向主仓库 account 目录的
  `accounts/foundagent` symlink；停机后必须删除该 symlink。
- 本次验证目标是配置、公开投影和 Provisioner 运行链路，不是重新评估 CEO 的自治经营判断。

## 需求

### R1：隔离与启动前证据

- 使用唯一 Company ID `department-specs-e2e-20260719`，启动前必须确认对应 state 目录和带该
  company label 的容器都不存在。
- 记录 Git commit、Docker Server、CUA 镜像 digest、四个 Department YAML 文件集合，以及
  `catalog.yaml` 不存在。
- 不停止、不重启、不修改其他正在运行的 Company。

### R2：真实 CEO 公开投影

- 启动真实 Hub 后，通过 `docker compose run` 创建使用真实 CEO 镜像、CEO 环境与 CEO actor
  绑定的单次方法客户端。
- `list_department_options` 必须返回且只返回四个固定选项；每项严格只有
  `id / name / description`。
- 公开 `name` 与中文 `description` 必须和四个 Department YAML 一致；结果中不得出现 model、
  Skills、MCP、charter、heartbeat、权限或文件路径。
- `id` 仅作为后续 `create_department` 的选择句柄。

### R3：Objective 前置与真实审核

- Company Objective 不是本次测试对象，使用项目真实 `ObjectiveStore`/`VerifierManager` 持久化
  逻辑确定性建立一个已 PASS 的 E2E fixture，避免额外市场判断干扰目标链路。
- Builder 初始 Objective 必须通过 CEO 的真实 `create_department` 方法提交。
- `verifier-manager` 必须实际创建临时 Verifier 容器并运行真实模型；不得手工写 PASS。
- 若真实 Verifier 判 FAIL，必须保存理由；最多修订一次并重新发起创建，不能把 FAIL 伪装成通过。

### R4：真实 Department Provisioning

- Department Objective PASS 后，真实 Department Provisioner 必须处理命令并启动
  `department-specs-e2e-20260719-builder`。
- Builder 容器必须带正确的 company/kind/department/template labels。
- 容器环境必须包含：
  - `AGENT_SPEC=/opt/foundagent-orch/agents/departments/builder.yaml`
  - `AGENT_CHARTER=/opt/foundagent-orch/agents/assets/departments/builder-charter.md`
  - `AGENT_HEARTBEAT_SECS=900`
- 容器内必须能读取 `builder.yaml`，不能存在 `catalog.yaml`；AgentSpec 必须仍解析出 Builder 的
  provider、model、Skills 与 MCP 配置。
- Builder 日志至少必须证明 resident loadout 完成且 resident loop 使用正确的 charter、MCP、
  model、effort、session 与 idle 配置启动。无需等待 Builder 完成经营 Goal。

### R5：证据与清理

- 所有可提交证据保存到本任务 `research/e2e-evidence/`，不得包含 credential 内容、完整环境变量、
  auth 文件或 secrets。
- 保存：preflight、公开 options JSON、创建/审核/Department 最终状态、脱敏 Docker inspect、关键日志、
  清理结果和最终报告。
- E2E 完成或失败后都必须停止并删除该 Company 的固定及动态容器，并清理 Compose 网络与临时
  account symlink。
- 可以保留 ignored 的独立 E2E state 目录供本地复核，但必须在报告中注明；不得加入 Git。

## 验收标准

- [x] 启动前隔离检查通过，没有复用旧 Company state 或容器。
- [x] CEO-bound 方法客户端实际返回四个选项，每项严格只有 `id/name/description`，值与 YAML 一致。
- [x] 结果中不存在任何内部配置字段，CEO 使用 `builder` ID 发起真实创建请求。
- [x] Builder 初始 Objective 由真实临时 Verifier 容器和真实模型审核为 PASS。
- [x] 真实 Builder 容器进入 running，Department registry 进入 `active`。
- [x] Builder 的 labels、三项关键环境变量、单一 YAML 文件与 resident 启动日志全部符合预期。
- [x] `catalog.yaml` 在宿主机和 Builder 容器挂载中都不存在。
- [x] E2E 证据完整、脱敏，无 credential 内容。
- [x] 测试 Company 的全部容器和网络已清理，其他 Company 未被操作。
- [x] 报告明确区分真实通过、失败重试和未验证项，不用 mock 结果冒充 E2E。

## 范围外

- 不让自治 CEO LLM 自主选方向或决定创建哪个 Department；该行为已由既有 V7 长跑 E2E 覆盖，
  本次用 CEO-bound 方法客户端获得确定性配置证据。
- 不验证 Worker、Goal result、Verifier 并发、Department 协作、heartbeat 周期或长期 session 恢复。
- 不修改产品代码，除非真实 E2E 暴露与本改造直接相关的缺陷；若需要修复，必须回到实现/检查流程。
- 不创建 Pull Request。
