# 实施计划：Department 单一声明 E2E

## 1. 启动前门禁

- [x] 确认当前分支包含 `027df46`，工作区产品代码无未提交改动。
- [x] 确认 Company ID、state 目录、container label 和 network 均未被占用。
- [x] 记录 Docker Server、CUA/control-plane image ID，并从当前工作树重新构建 control-plane。
- [x] 只检查主仓库 account 所需文件存在，不读取内容。
- [x] 记录四个 Department YAML 与 catalog 不存在的静态证据。

## 2. 建立隔离 fixture

- [x] 创建 `research/e2e-evidence/` 与 preflight。
- [x] 创建临时 `accounts/foundagent` symlink，目标精确等于主仓库 account 目录。
- [x] 初始化全新 Company state。
- [x] 使用真实 Store 类确定性激活 Company Objective fixture，保存 review/proposal 的非敏感输出。

## 3. 启动真实服务

- [x] 构建当前工作树的 `foundagent/control-plane:latest`。
- [x] 只启动 Hub、Verifier Manager、Department Provisioner。
- [x] 等待 Hub healthy，检查三项服务无启动异常。

## 4. 验证 CEO 公开选项

- [x] 用单次 CEO 容器调用 `list_department_options`，保存原始 JSON。
- [x] 独立断言四个固定 ID、严格三字段、公开值与 YAML 一致、内部字段完全缺失。
- [x] 保存断言结果与调用容器/Hub 审计证据。

## 5. 创建 Builder 并完成真实审核

- [x] 用单次 CEO 容器提交 Builder durable initial Objective，保存 creation response。
- [x] 观察真实 Verifier 容器出现、运行和销毁，保存 review final、关键日志与 run archive 路径。
- [x] 第一次真实 verdict 为 FAIL 并保存 reason；补齐 Company State 后仅修订重试一次，第二次 PASS。

## 6. 验证真实 Builder

- [x] 等待 Builder registry `active` 与真实容器 running。
- [x] 采集白名单 labels、三项关键环境变量和 agents mount。
- [x] 在容器内验证四个 YAML 存在、catalog 不存在。
- [x] 在容器内用 AgentSpec 读取并保存安全的 runtime 配置摘要。
- [x] 保存 `resident_loadout` 和 `agent_loop boot` 关键日志。

## 7. 清理与报告

- [x] 精确停止/删除本 Company 的全部固定和动态容器，并清理 network。
- [x] 删除临时 account symlink，确认其他 Company 容器仍在且未被操作。
- [x] 保留 ignored E2E state，记录路径和大小；不得加入 Git。
- [x] 写 `cleanup.md` 与中文 `report.md`，逐条映射 PRD 验收标准。
- [x] 对 evidence 运行 credential/secret 模式扫描，人工复核没有完整环境或 auth 内容。

## 8. 收尾质量门

- [x] `git diff --check`。
- [x] 没有产品代码变更，不重复跑完整单测；报告区分此前 440 项基线与本次真实 E2E。
- [x] 未发现与单一 Department YAML 改造相关的产品缺陷；认证问题属于工作树 E2E 装配/本地 seed 状态，已在报告披露。
- [x] 仅提交本 E2E 任务与脱敏 evidence，不纳入 `.trellis/tasks/07-19-native-company-folder/`。
