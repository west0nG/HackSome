# Implement: state/<company>/ 按公司隔离 + 会话持久化

## 执行清单（有序）

1. [x] `docker-compose.yml`：
   - 顶部注释区说明「一套栈 = 一个公司，`COMPANY` 选定」；`PUMP_COMPANY` 全部替换为 `COMPANY`
   - agent anchor 挂载源：`./state/${COMPANY:-foundagent}/company:/company`、`./state/${COMPANY:-foundagent}/ledger:/shared/ledger`、`./state/${COMPANY:-foundagent}/inbox:/shared/inbox`
   - hub（原 124-125 行）、peripheral（原 169 行）ledger/inbox 挂载源同步改
   - 每个 agent 服务新增 `./state/${COMPANY:-foundagent}/sessions/<role>:/home/kasm-user/.claude`
   - `AGENT_SESSION_FILE` 改为 `/home/kasm-user/.claude/session_id`（位于各自挂载内）
2. [x] `Makefile`：
   - `COMPANY ?= foundagent`；`shared` target 改为 `mkdir -p state/$(COMPANY)/{company,ledger,inbox,sessions/{ceo,researcher,builder,growth,verifier}}` + `chmod -R 777 state/$(COMPANY)`（company/ 除外可只 777 运行时目录，保持与现行为一致的最小面）
   - `up` 把 `COMPANY` 透传给 compose；更新注释（原第 18 行）
3. [x] 代码默认路径常量（宿主机直跑兜底，容器内走 env；均尊重 `COMPANY` env，默认 `foundagent`）：
   - `orchestration/goal_ledger.py:60` `DEFAULT_LEDGER` → `<repo>/state/<COMPANY>/ledger`（同步改 docstring 12-16 行）
   - `orchestration/inbox.py:44` `DEFAULT_INBOX` → `<repo>/state/<COMPANY>/inbox`（同步改 docstring 96 行）
   - `orchestration/broker.py:37` 公司根解析 → `<repo>/state`，`spawn()` 的 company 挂载路径 → `state/<company_id>/company`
4. [x] `.gitignore`：删除 `orchestration/ledger/`、`orchestration/inbox/`、`companies/` 三条，新增 `state/` 一条（注释：per-company 可变状态，非代码）
5. [x] 数据迁移（停栈状态下执行）：
   - `docker compose down`
   - foundagent（现役公司，继承现有运行时数据）：`mkdir -p state/foundagent && mv companies/foundagent state/foundagent/company && mv orchestration/ledger state/foundagent/ledger && mv orchestration/inbox state/foundagent/inbox`
   - 其余公司（acme、e2e-dood、e2e-goaltest）：`mv companies/<name> state/<name>/company`（运行时目录按需由 `make shared` 创建）
   - 删除空壳 `companies/`
6. [x] grep 验证：`orchestration/ledger|orchestration/inbox|\./companies|PUMP_COMPANY` 在代码/compose/Makefile/文档中无残留引用（`.trellis`、`vm/data` 遗留物除外）

## 验证命令

```bash
# 单测全绿
python3 -m pytest orchestration/ company_state_kit/ agent/ -q

# 栈起得来 + goal 流转
make up && make logs-hub   # 观察 reconcile/sweep 正常

# 会话持久化端到端
# 1) 起栈，等 ceo 完成一次 wake（logs 出现 session id）
# 2) make down && make up（容器重建）
# 3) 确认 ceo 下一次 wake 走 --resume 且 state/foundagent/sessions/ceo/ 内有 transcript + session_id

# 公司隔离
COMPANY=e2e-dood docker compose -p e2e-dood up -d
# 确认 state/e2e-dood/ 与 state/foundagent/ 各自独立读写，互无交叉
```

## 回滚点

- 全部改动为路径字符串 + 一次 `mv`；回滚 = git revert 代码改动 + 把 `state/<company>/` 下目录 `mv` 回原位。
