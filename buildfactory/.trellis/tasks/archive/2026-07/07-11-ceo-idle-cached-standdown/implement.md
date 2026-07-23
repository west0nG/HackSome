# Implement — proactive heartbeat prompt refresh + live CEO upgrade

## 顺序清单

1. [x] 运行
   `python3 ./.trellis/scripts/task.py start .trellis/tasks/07-11-ceo-idle-cached-standdown`，
   进入实现阶段。
2. [x] 加载 `trellis-before-dev`，读取 Phase 2 所需 spec 与本任务工件。
3. [x] 修改 `orchestration/agent_loop.py`：
   - 替换 `idle: proactive` 的空 heartbeat prompt；
   - 同步 `_render_events` / `build_wake_prompt` 附近注释，说明每次显式调用
     `when-idle`，不再写成仅“defer to charter”；
   - 不改变函数签名、分支结构或 loop 控制流。
4. [x] 修改 `orchestration/tests/test_agent_loop.py`：
   - 将 proactive prompt 测试升级为完整 golden；
   - 钉住 `You always have something to do on a heartbeat` 与
     `waiting on one thing does not mean waiting on everything`；
   - 保留 worker `STOP_ORDER` 的 byte-equal golden；
   - 复跑 event wake、objective + fresh 组合测试。
5. [x] 更新 `.trellis/spec/backend/resident-agent-contracts.md` 的 Idle stance：
   - 记录 proactive prompt 每 wake 显式调用 `when-idle`；
   - 记录等待一件事不等于所有事情都停下；
   - 不把 prompt-only 描述成 harness 强制保证。
6. [x] 运行用户保留的确定性检查：
   - `.venv-cua/bin/python -m pytest orchestration/tests/test_agent_loop.py -q`；
   - `git diff --check`。
7. [x] 不运行 CEO 模型行为沙箱、不创建 scratch 公司、不主动触发 heartbeat。
8. [x] 升级前安全门：
   - `thirdtest-ceo` 中无活动 `claude -p` 子进程；若有则等该 wake 自然结束；
   - 记录当前 `/sessions/ceo/session_id`；
   - 记录 thirdtest 其他容器的 StartedAt。
9. [x] 定向升级：
   - `COMPANY=thirdtest ACCOUNT=foundagent docker compose -f docker-compose.yml restart ceo`；
   - 不 restart/recreate 其他服务，不 build 镜像。
10. [x] 部署健康检查：
    - `thirdtest-ceo` 为 running，`python3 -m orchestration.agent_loop` 存活；
    - boot/start 日志显示原 session id；
    - 容器内 `build_wake_prompt([], idle="proactive")` 等于批准文本；
    - 其他容器 StartedAt 与升级前一致。
11. [x] 对最终 `prd.md` 做 lossless convergence pass，记录升级结果并完成任务。

## 验证命令

```bash
.venv-cua/bin/python -m pytest orchestration/tests/test_agent_loop.py -q
git diff --check

docker exec thirdtest-ceo sh -lc \
  "ps -eo pid,ppid,etime,args | grep -E 'orchestration.agent_loop|claude -p' | grep -v grep"

COMPANY=thirdtest ACCOUNT=foundagent \
  docker compose -f docker-compose.yml restart ceo

docker inspect thirdtest-ceo --format \
  'status={{.State.Status}} started={{.State.StartedAt}} restarts={{.RestartCount}}'
```

## 预期产品改动文件

- `orchestration/agent_loop.py`
- `orchestration/tests/test_agent_loop.py`
- `.trellis/spec/backend/resident-agent-contracts.md`

Trellis 规划、升级记录与验收记录另计，不属于产品运行面。

## 实施与上线结果

- 产品改动严格限于上列 3 个预期文件，没有修改 loop 控制流、session 策略、技能正文、
  charter、messaging、ledger、telemetry、Hub 或 hooks。
- 宿主系统 Python 没有安装 pytest；按项目 README 使用
  `.venv-cua/bin/python -m pytest orchestration/tests/test_agent_loop.py -q`，结果为
  **53 passed in 0.61s**。`git diff --check` 通过。
- 升级前完整进程快照确认 `thirdtest-ceo` 只有常驻 `orchestration.agent_loop`，没有活动
  `claude` 子进程；session id 为
  `dd70a6f8-e6d6-4dc2-8107-fc0f0a35b441`。
- 2026-07-11 03:04:17 UTC 定向重启 `thirdtest-ceo`。重启后容器为 running，
  `orchestration.agent_loop` 存活，boot/start 日志显示 `session=resume`、
  `idle=proactive` 与同一 session id。
- 容器内纯 Python 构造出的 proactive heartbeat 与用户批准文本逐字一致；没有触发付费
  模型 wake。只有 CEO 的 StartedAt 改变，thirdtest 其余 9 个容器保持原启动时间。

## 风险点与回退

- 最大风险是 prompt-only 且跳过行为真跑后，模型仍可能在长 resume 上忽略新指令；由
  thirdtest 后续自然 heartbeat 暴露，不主动花费模型调用验证。
- restart 若撞上活动 wake 会硬中断模型，因此无 `claude -p` 子进程是部署硬门。
- `orchestration/` 与 `/sessions` 均为 bind mount，无镜像构建和状态迁移。
- 回滚产品 diff 后再次定向 restart `thirdtest-ceo`；不回滚 session 或公司状态。

## `task.py start` 前检查

- [x] 用户已批准最终 prompt、prompt-only 范围、跳过行为验证和定向升级当前 CEO；
- [x] `prd.md`、`design.md`、`implement.md` 已覆盖新范围；
- [x] 工作树中无与产品改动文件重叠的用户修改；
- [x] 当前仍为 planning，未提前修改产品代码或容器状态。
