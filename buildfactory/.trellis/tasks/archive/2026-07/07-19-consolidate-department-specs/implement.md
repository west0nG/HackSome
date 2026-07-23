# 实施计划：合并 Department Catalog 与 AgentSpec

## 1. 实施前检查

- [x] 搜索 `catalog.yaml`、`DepartmentCatalog.load`、`catalog_path`、`public_description`、
  `heartbeat_secs`、`agent_spec`、`charter` 的全部引用，记录需要同步修改的调用方。
- [x] 确认工作区中其他未提交任务文件不属于本任务，不修改或提交
  `.trellis/tasks/07-19-native-company-folder/`。
- [x] 运行现有 Department 定向测试，建立改造前基线。

## 2. 合并配置声明

- [x] 在 `strategist.yaml`、`researcher.yaml`、`builder.yaml`、`growth.yaml` 中加入现有
  `public_name`、`public_description` 与显式 `heartbeat_secs: 900`。
- [x] 保持四个文件的 provider、model、effort、credentials、system_prompt、Skills、MCP、权限、
  session、idle 与 strategic 值不变。
- [x] 删除 `agents/departments/catalog.yaml`。

## 3. 重构固定目录加载器

- [x] 修改 `DepartmentCatalog.load`，接收 Department specs 目录并按 `ALLOWED_IDS` 加载四个 YAML。
- [x] 增加目录文件集合、mapping、name/文件名/ID、公开字段、heartbeat 和 system_prompt 路径校验。
- [x] 从文件名推导 `agent_spec`，从 `system_prompt` 安全归一化推导 charter。
- [x] 从 `DepartmentTemplate` 删除未使用的 `skills`、`mcp_config`。
- [x] 保持 `options()`、`internal()`、固定顺序和异常类型的外部行为。

## 4. 迁移调用方

- [x] 修改 `CompanyHub` 默认配置及内部参数，使其传入 `agents/departments/`。
- [x] 修改 `DepartmentProvisioner` 主入口，使其从同一目录加载。
- [x] 修改所有测试常量和构造调用，不再传入 `catalog.yaml`。
- [x] 全仓搜索并清除活跃代码和测试中的旧路径引用。

## 5. 测试

- [x] 保留并强化“CEO 公开选项严格只有 `id/name/description`”测试。
- [x] 增加四个 YAML 的公开元数据与 heartbeat 加载测试。
- [x] 增加缺文件、额外 YAML、name 不匹配、空公开字段、非法 heartbeat、system_prompt 越界测试。
- [x] 验证 Provisioner Docker 参数仍包含正确的 `AGENT_SPEC`、`AGENT_CHARTER` 和
  `AGENT_HEARTBEAT_SECS=900`。
- [x] 验证 Department AgentSpec 的 Skills、MCP 和 charter materialization 现有测试继续通过。

## 6. 规范更新

- [x] 更新 `.trellis/spec/backend/three-layer-agent-company-contracts.md`：
  - 将 `DepartmentCatalog.load(catalog.yaml)` 改为目录加载签名；
  - 记录每个 Department YAML 同时拥有公开元数据和运行配置；
  - 保留 CEO 公开三字段投影与不能覆盖内部配置的契约；
  - 删除“catalog 与 AgentSpec Skill 列表一致”的双份配置错误矩阵，改为单一声明完整性检查。
- [x] 再次全仓搜索旧 `catalog.yaml` 引用，区分需保留的历史任务文档与必须更新的活跃规范。

## 7. 验证命令

先运行定向检查：

```bash
.venv-cua/bin/python -m pytest \
  orchestration/tests/test_departments.py \
  orchestration/tests/test_company_hub_v7.py \
  orchestration/tests/test_v7_runtime_services.py \
  orchestration/tests/test_v7_mount_boundaries.py \
  agent/tests/test_spec.py \
  agent/tests/test_resident_loadout.py \
  agent/tests/test_mcp_assets.py
```

再运行完整质量门：

```bash
.venv-cua/bin/python -m compileall -q agent orchestration peripheral company_state_kit
.venv-cua/bin/python -m pytest agent/tests/ orchestration/tests/ company_state_kit/tests/ peripheral/tests/
docker compose config -q
```

最后运行：

```bash
rg -n 'catalog\.yaml|catalog_path' agents orchestration agent .trellis/spec
git diff --check
git status --short
```

## 8. 风险与回滚点

- [x] 在删除 catalog 前先确保四个 YAML 已拥有所有有效元数据；否则 Hub 会失去公开选项来源。
- [x] 在迁移 Hub 与 Provisioner 后立即跑定向测试；两者必须指向同一目录。
- [x] 如果路径归一化导致 charter 启动参数错误，回滚加载器与 catalog 删除，不修改持久 company state。
- [x] 提交前只纳入本任务文件和本任务规划文档，不带入其他活跃 Trellis 任务。
