# Fourth Test 启动基线

记录时间：2026-07-13（Asia/Shanghai）

## Git 与隔离目标

- 主仓库 HEAD：`17149fe214edaf8648d22802392fe723f6c2e5f7`
- Fourth Test 分支：`codex/fourthtest-run`
- Fourth Test worktree：`/Users/weston/dev/BuildFactory-fourthtest`
- 启动前确认：上述分支、worktree 路径与 `state/fourthtest/` 均不存在。
- 主工作区已有用户改动保持不动：Third Test observations 以及 07-12 任务目录。

## Third Test 运行基线

Compose project：`buildfactory`

| 服务 | 容器 ID | 启动基线 |
|---|---|---|
| hub | `4b40caf8ae71` | Up / healthy |
| peripheral | `6811908d8982` | Up / healthy / host `8900` |
| broker | `f4edd25dcda9` | Up |
| provisioner | `fda32a46e851` | Up |
| mail-poller | `fb9e818302bf` | Up；计划内唯一允许重建的服务 |
| ceo | `02d8a2228a73` | Up |
| researcher | `ea05b3006949` | Up |
| builder | `43d22726ec55` | Up |
| growth | `a53cadadaafe` | Up |
| verifier | `05d015c6ed1b` | Up |

Third Test Observatory：PID `19500`，命令为 `observatory/runner.py --company thirdtest daemon`，启动于 2026-07-10 15:35:34。

## 宿主资源基线

- Host `8900` 已由 Third Test 使用；`8901` 空闲。
- Docker VM 可见内存上限约 `7.75 GiB`。
- 启动前主要 Agent 内存：CEO `1.04 GiB`、Researcher `848 MiB`、Builder `251 MiB`、Growth `375 MiB`、Verifier `817 MiB`。
- 启动 Fourth Test 后必须重点检查 OOM、重启与 Codex subscription 限流。
