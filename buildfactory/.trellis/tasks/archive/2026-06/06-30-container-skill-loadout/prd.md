# Container skill materialization (loadout → ~/.claude/skills)

> 父任务：`../06-26-foundagent-v6`。状态：planning → 工件回填（实现已在分支
> `chore/orchestration-cleanup-skill-loadout` 完成，commit `b8c7f8c`，本工件如实记录）。

## Goal

常驻 agent 容器把每个角色 yaml 声明的 `skills:`/`hooks:` 真正 materialize 进
`~/.claude`，让 subscription claude 能按 `description` 自动发现并触发 civic skill
（send-goal / receive-goal / company-state）。在此之前这些声明是**死配置**——
常驻路径 `agent_startup.sh → agent_loop` 只用 `--append-system-prompt` 注入 charter，
从不 materialize；派活能用纯粹因为 charter 内联了命令、Hub 的 work-order 也内嵌了
report 命令（06-29 agent-handbook Tier-B e2e 就是靠这个跑通的，但 skill 的
description-triggering 需要真正落盘）。

## Confirmed facts（代码库已验证）

- **断点根因**：`agent_loop.py` 全程只读 `AGENT_CHARTER`；compose 只 mount 了
  `./orchestration` 和 `./agents/assets`，**没 mount `./agent`（loadout 包）也没 mount
  `agents/*.yaml`** → 容器内 `from agent.spec import ...` 直接失败。
- **materialize 已存在**：`agent/loadout.py:materialize(spec, claude_home)` 把 skill 拷进
  `<claude_home>/skills/<name>/`、hook merge 进 `settings.json`；`agent/spec.py:AgentSpec.load`
  从 yaml 读 spec。原 spike 在宿主侧调用它（broker 路径），常驻路径没接。
- **依赖面**：`agent` 包唯一外部依赖是 `spec.py` 的 PyYAML；`runner/provider/credentials`
  全 stdlib-only。cua-agent 镜像原本只装了 `cua-computer mcp`，缺 PyYAML。
- **认证不受影响**：claude 用 `CLAUDE_CODE_OAUTH_TOKEN`（env）认证，不是 `~/.claude/.credentials`；
  往 `~/.claude/skills` 写不会 clobber 凭证。容器内 claude_home = `/home/kasm-user/.claude`。
- **per-role loadout**（各 yaml 声明）：ceo=send-goal；researcher/builder/growth=
  company-state+receive-goal；builder/growth 另有 `hooks: ../company_state_kit/hooks/
  settings.snippet.json`（相对 yaml 目录）；verifier=company-state。

## Requirements

- **R1 启动时 materialize**：常驻容器启动、在 `exec agent_loop` 之前，按 `$AGENT_KEY`
  读 `agents/<key>.yaml`，把其 skills+hooks materialize 进 `~/.claude`。
- **R2 best-effort 不 brick**：materialize 失败（缺 skill 目录/缺依赖/坏 yaml）必须
  **大声 log + exit 0**，降级为 charter-only，绝不让 agent 起不来。charter 是地板，
  仍由 agent_loop 每次 wake 单独注入，与本步解耦。
- **R3 单一事实源**：skill/hook 来自 yaml（不在别处再抄一份角色→skill 映射）。
- **R4 容器内可达**：loadout 包、yaml 树、builder/growth 的相对 hook 路径
  （`../company_state_kit/...`）在容器内都能解析；镜像具备解析 yaml 的依赖。
- **R5 不动 charter 注入**：本任务只加 skills/hooks 落盘，不改 charter 经
  `AGENT_CHARTER` 的既有注入路径（避免动 agent_loop 主回路）。

## Acceptance Criteria

- [x] AC1：`agent/resident_loadout.py` 存在；`materialize_for(key, agents_dir, claude_home)`
  按角色 yaml 落盘 skills+hooks；`main()` 从 env 读 `AGENT_KEY/AGENTS_DIR/CLAUDE_HOME`。
- [x] AC2：per-role 映射正确（宿主 + 单测验证）——ceo→[send-goal]；
  researcher→{company-state,receive-goal}；builder/growth 同上且 `hooks_merged=True`
  （company_state_kit 的 `Stop` hook 进 settings.json）；verifier→[company-state]。
- [x] AC3：best-effort——坏 loadout（指向不存在的 skill）时 `main()` 返回 0 且日志含
  `ERROR materializing`；无 `AGENT_KEY` 时 no-op 返回 0。
- [x] AC4：接线就位——`agent_startup.sh` 在 exec 前调 `agent.resident_loadout`；
  compose x-agent 挂 `./agent`+`./agents`+`company_state_kit`（foundagent-orch 路径）；
  `Dockerfile.agent` 装 PyYAML；`docker compose config -q` 通过。
- [x] AC5：测试套件绿（新增 `agent/tests/test_resident_loadout.py` 7 例；全套 154）。
- [ ] AC6（待真机）：`make up` 后 `make logs-ceo` 可见
  `[resident_loadout] ceo: skills=['send-goal'] ... -> /home/kasm-user/.claude`，
  且容器内 `~/.claude/skills/send-goal/SKILL.md` 存在。**需 docker + OAuth token 环境，
  本机未跑；列为交付后真机冒烟项。**

## Out of Scope

- 把 charter 也收进 yaml 单一事实源（retire `AGENT_CHARTER` 手工接线）——更大重构，另议。
- `researcher.yaml` 缺 `system_prompt` 字段的补齐（charter 经 env 仍生效，不阻塞本任务）。
- 死代码清理（pump 簇删除）——独立任务 `06-30-orch-dead-code-cleanup`。

## Open Questions

- 无阻塞项。唯一未闭环的是 AC6 真机冒烟，需用户在 docker 环境跑一次确认。
