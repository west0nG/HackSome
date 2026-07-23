# First Test 启动与停机操作清单

## 启动前检查

1. 代码：main 已含 07-07-longrun-hardening 与 07-07-observatory 两次合并。
2. `docker ps` 确认 foundagent 栈没在跑（两家公司共用同一批真实外部账号，不能同时跑）。
3. `accounts/foundagent/` 四件在位：`secrets.env`、`google-sa.json`、`cookies/storage-state.json`、`codex-auth.json`。
4. `vm/.env.local` 含 `CLAUDE_CODE_OAUTH_TOKEN`。
5. `make loadout-check COMPANY=firsttest` 通过。

## 启动

```bash
make up COMPANY=firsttest ACCOUNT=foundagent
```

- 完全自主冷启动：不注入任何初始消息。CEO 在第一次心跳（默认 30 分钟）醒来，发现收件箱为空、也没有长期方向，会自己开始找方向。
- 心跳间隔保持默认 1800 秒，不要调小——这是设计节奏。
- 单独跑一家公司不需要 `docker compose -p`；将来两家并行时必须显式加。

## 启动观测程序（公司起来之后）

```bash
mkdir -p state/firsttest/observatory
nohup .venv-cua/bin/python observatory/runner.py --company firsttest daemon \
  > state/firsttest/observatory/.runner.log 2>&1 &
```

- 观测程序跑在宿主机、只读，每当有任务走到终态就出一份复盘报告，每 6 小时出一份全公司检查。
- 报告在 `state/firsttest/observatory/{goal,company}/`，报告第一行出现 `RED-ALERT:` 表示观测者认为有严重问题，值守时优先看。

## 运行期检查手段

- `docker ps`：看 9 个容器状态，hub/peripheral 有健康检查。
- `make logs COMPANY=firsttest`：跟实时日志。
- `state/firsttest/telemetry/wake.<角色>.jsonl`：每次唤醒一行，含花费。
- `state/firsttest/ledger/`：任务账本；`ledger/audit.jsonl`：被拦截的违规消息。
- 随时手动触发一次全公司检查：`make observe COMPANY=firsttest`。

## 停机

```bash
make down COMPANY=firsttest
kill <观测程序 pid>          # 或 pkill -f 'runner.py --company firsttest'
```

停机后跑总结汇总（唯一会读全部报告的一步）：

```bash
.venv-cua/bin/python observatory/runner.py --company firsttest once-final
```

## 干预纪律

- 跑起来之后不注入、不引导；人工干预只限止损（`make down`），且必须记进 run-log.md。
