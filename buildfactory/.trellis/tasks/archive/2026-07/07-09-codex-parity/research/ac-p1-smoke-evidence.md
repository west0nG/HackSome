# AC-P1 集成冒烟证据 — codex-parity 父任务（2026-07-10）

环境：`COMPANY=e2ehooks ACCOUNT=foundagent`，hub + builder(codex) + verifier(claude-code) 三容器；overlay（state/e2ehooks/config/loadout.yaml）给 builder 临时加 decide-direction skill。三个 goal 全部走完 dispatch→执行→report→verifier 独立验收→done 闭环。

## AC-P1 三项检查点

**① session 结束时 record 强制生效** ✅
- 未 record 的 wake（goal 2，指示禁用 company.py）被 Stop hook 挡恰好一次并收到补记指引，`record --nothing` 后放行（详证见 archive/2026-07/07-09-codex-hooks/research/ac1-e2e-evidence.md）。
- 主动 record 的 wake（goal 1、goal 3）零阻断静默放行。
- marker 全部按 per-wake `COMPANY_WAKE_ID` nonce 键控（非 thread id、非 default）。

**② wake.<role>.jsonl 含 token usage** ✅
三条 builder(codex) wake 行均含非空 usage（原生 shape：input/cached_input/output/reasoning_output），例：
```
{"key":"builder", ..., "usage":{"input_tokens":209175,"cached_input_tokens":186624,"output_tokens":4686,"reasoning_output_tokens":2493},"ok":true}
```

**③ observation 尸检定位 codex transcript + 数出工具轨迹** ✅
`observatory/runner.py --company e2ehooks once-goal ge6f76ad0…`（观测者 claude-sonnet-5，host 侧）报告落 `state/e2ehooks/observatory/goal/ge6f76ad0….md`：
- 在 codex 布局 `sessions/builder/codex/sessions/2026/07/09/rollout-*.jsonl`（83 行）逐条数出 exec_command 读 skill/`spawn_agent`/`wait_agent`/company.py write+read 回验/messaging report 全轨迹；
- 交叉核验了子代理 rollout、hub.jsonl 的 REPORT 行、verifier 的 claude 布局 transcript；
- 独立判定 PASS，与 verifier 判定一致（双方 provider 不同底座，独立性成立）。

## AC-P2（claude 路径零回归）✅
全量 615 tests passed（agent 219 + orchestration 339 + company_state_kit 32 + observatory 25，含 claude golden test）。verifier 以 claude-code 全程正常验收三个 goal。

## AC-P3（auth 前置核验）✅
`accounts/foundagent/codex-auth.json` 种子直接可用：三次 codex wake 全部成功、token 就地刷新（无需人工重登）。

## 并入执行的子任务真跑 AC

**observatory AC3**：即上文 ③。

**skills AC4**（codex wake 实际触发被修改 skill 且未卡死）✅：
- overlay 把 decide-direction 加入 builder（manifest reconcile 实时正确：skills 列表 +1，hooks 原样保留——顺带二次实证 reconcile 幂等/精确性）。
- builder 真实走完 decide-direction 方法：读 SKILL.md 双路径（`~/.agents/skills/…` 解析成功）→ **意外发现：codex 0.142.5 原生带 multi_agent_v1 工具组（spawn_agent/wait_agent/close_agent）**，builder 用它 spawn 了真实独立 reviewer（观测者证实子代理 transcript 真实存在），主路径直接可用，降级模式未触发；
- 产物 `/company/direction/next-public-artifact.md`：ADJUST 决定 + 4 条理由 + 独立 reviewer verdict 分层记录；verifier PASS。

## 冒烟白捡的观察（非阻塞，留给后续）

1. **codex 原生 multi-agent**：skills 中性化时假设 codex 无 spawn 工具；实际 0.142.5 有 `multi_agent_v1`。decide-direction 的降级路径仍有价值（其他 runtime / 工具被禁用时），但"codex=无 subagent"的假设已过时，相关 skill 文案后续可以放宽。
2. **子代理降级走过场**（观测者发现）：子代理自称用 degraded mode 却未逐条走 direction-critic 四项测试。skill 对子代理侧的执行纪律约束偏弱。
3. **ledger runs[] 明细不回填**（观测者发现）：`runs[0].ok/finished_at/summary` 全程 null，只有顶层 status 推进。通用机制缺口，值得开任务修。

## 成本

codex 订阅（3 wakes ≈ 4.2 分钟）+ claude 订阅（verifier 2 wakes + 观测者 1 次 Sonnet 尸检）。全程零 API 付费。

清理：e2ehooks 栈已拆（state 目录按惯例保留，gitignore 内）；builder.yaml 保持 `provider: codex` 进入 secondtest 全 codex 长跑（用户 07-10 指示）。
