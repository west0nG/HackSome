# Design — Container skill materialization

> 配套 `prd.md`。实现已落地（commit `b8c7f8c`）；本文记录所选形态与权衡。

## 选型：容器内启动时 materialize（vs 宿主预 materialize）

三条候选路：

1. **宿主侧 materialize + bind-mount `~/.claude`**（spike 原设计）：在 `make up` 前于宿主
   把 `vm/data/<key>/claude` 备好再挂进容器。问题：常驻路径是纯 `docker compose up`，
   引入宿主预处理步会再造一层"两代机制"；且 bind-mount 整个 `~/.claude` 有 clobber
   claude 配置目录的风险。
2. **容器内 materialize（选用）**：容器启动钩子按 `$AGENT_KEY` 现场读 yaml、materialize
   进容器本地 `~/.claude`。纯 compose、无宿主步、每容器自洽；`~/.claude` 是容器本地态
   （每次起容器重建，声明驱动，正合适）。
3. **硬编码角色→skill 映射的 shell**：直接违反 R3 单一事实源，否决。

选 2。代价是镜像要能解析 yaml（加 PyYAML）+ 把 `agent/`、`agents/` 挂进容器。

## 形态

- **新增 `agent/resident_loadout.py`**（薄入口，复用既有 `materialize`）：
  - `materialize_for(key, agents_dir, claude_home)`：`AgentSpec.load(agents/<key>.yaml)`
    → `materialize(spec, claude_home)`；无 yaml → 返回 None（charter-only，合法）。
  - `main()`：从 env 读 `AGENT_KEY`/`AGENTS_DIR`/`CLAUDE_HOME`（**调用时读**，非 def-time
    默认值，使容器 env 与测试都能重定向）；包一层 try/except，失败大声 log 并 return 0。
  - PyYAML 在 `materialize_for` 内**惰性 import**，缺依赖也走"被捕获的 loadout 错误"
    （降级 charter-only）而非 import-time 崩钩子。
- **`agent_startup.sh`**：`computer_server &` 之后、`exec agent_loop` 之前插一行
  `python3 -m agent.resident_loadout`。它非 exec、阻塞跑完即返回，再 exec 主回路。
- **`docker-compose.yml`（x-agent 锚点）**新增 mount：
  - `./agent:/opt/foundagent-orch/agent:ro`（loadout 包；PYTHONPATH 已含 foundagent-orch）
  - `./agents:/opt/foundagent-orch/agents:ro`（yaml + assets；materialize 源）
  - `./company_state_kit:/opt/foundagent-orch/company_state_kit:ro`（builder/growth 的
    `../company_state_kit/...` 相对 hook 解析；原 `/opt/company_state_kit` mount 保留，
    company-state skill 硬编码了它）
- **`Dockerfile.agent`**：pip 增 `pyyaml`。

## 数据流（启动一次）

```
容器起 → kasm 桌面就绪 → custom_startup.sh
  → computer_server &                         (后台, cua MCP)
  → python3 -m agent.resident_loadout         (前台一次性)
        读 agents/$AGENT_KEY.yaml
        → 拷 skills/<name>/ 进 ~/.claude/skills
        → merge hooks 进 ~/.claude/settings.json
        (失败 → log ERROR, exit 0)
  → exec agent_loop                            (前台常驻; charter 仍按 wake 注入)
```

## 边界与兼容

- **不动 agent_loop 主回路**：charter 仍走 `AGENT_CHARTER` env（R5）。本步与 wake 解耦：
  skills/hooks 是文件态一次性落盘，charter 是每 wake 的 `--append-system-prompt`。
- **凭证安全**：写 `~/.claude` 不碰 `CLAUDE_CODE_OAUTH_TOKEN`（env 认证）。
- **幂等**：`materialize` 本身幂等（重拷 skill、去重 merge hook）；容器重启重跑无副作用。
- **回滚**：revert commit `b8c7f8c` 即恢复 charter-only；compose mount 是纯增量。

## 已知未闭环

- AC6 真机冒烟（`make up` + 看日志/容器内 skill 落盘）需 docker + OAuth 环境，本机未跑。
