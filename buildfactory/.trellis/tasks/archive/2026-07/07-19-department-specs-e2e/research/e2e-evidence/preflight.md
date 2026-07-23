# E2E 启动前预检

- Company：`department-specs-e2e-20260719`
- Git commit：`56edb21074f791c0023bc54d2671b7669b90c440`
- 必需改造提交：`027df46` 已包含在当前分支历史中。
- Docker Server：`29.5.3`
- `foundagent/cua-agent:latest` image ID：`sha256:eb91cf6ae9ec466cfd13d4868361b2c63d490b260e223810ee023be41164d65b`
- 启动前专用 state：不存在。
- 启动前带精确 company label 的容器：0。
- 启动前专用 Compose network：不存在。
- 主仓库 account 前置文件：仅确认 `secrets.env`、`codex-auth.json` 存在；未读取内容。
- 工作树临时 account symlink：启动前不存在。
- Department YAML：`builder.yaml`、`growth.yaml`、`researcher.yaml`、`strategist.yaml`。
- `agents/departments/catalog.yaml`：不存在。
- 预检时另有其他 Company 容器运行；本测试不停止、不重启、不修改它们。

注：本地镜像没有 registry RepoDigest，因此证据记录 Docker image ID；E2E 会从当前 commit 重新构建
`foundagent/control-plane:latest`，并在报告中记录构建后的 image ID。
