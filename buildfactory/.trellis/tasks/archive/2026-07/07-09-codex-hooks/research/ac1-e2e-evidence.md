# AC1 真跑证据 — codex hooks translation (2026-07-09/10)

环境：`COMPANY=e2ehooks ACCOUNT=foundagent`，只起 hub + builder 两个容器（`docker compose -p e2ehooks up -d hub builder`）。
唯一改动：`agents/builder.yaml` 一行 `provider: claude-code → codex`（builder 本就带 `hooks: ../company_state_kit/hooks/settings.snippet.json`），验证后已还原。
镜像未重建（代码 bind-mount）：codex-cli 0.142.5 / claude 2.1.202。凭证 = `accounts/foundagent/codex-auth.json` 订阅登录态（零 API 费用）。

## 物化（materialize_home 第 4 步）

容器启动即生成（host 侧 `state/e2ehooks/sessions/builder/codex/`）：

- `hooks.json`：与 snippet 逐字一致（Stop → `python3 /opt/company_state_kit/hooks/record_stop_hook.py`，timeout 30）。
- `.loadout-manifest.json`：hooks 槽记录了本次 merge 的条目（撤销依据）。
- `auth.json` / `config.toml`：chmod 600（`-rw------- kasm-user`）。

## Wake 1 — 主动 record 路径（放行分支）

CEO 身份 `messaging send` 发健康检查 goal（g6d14a7a2）。builder 被唤醒后**自己**按 company-state skill 的指引跑了 `company.py record`，Stop hook 静默放行：

- rollout `019f47ac-9cd7`：`hook_prompt` 出现次数 = **0**（无阻断）。
- marker：`/tmp/foundagent-company-markers/3b31f668-d939-4a40-bde9-e0e950fb866e.marker`（内容 `recorded`）。
- telemetry：49.1s，ok=true。goal 进 `verifying`（report 已达 hub）。

## Wake 2 — 强制不 record 路径（阻断分支，AC1 主证据)

goal（g56e4f64d）明确指示"do NOT run any company.py commands - just send the report and finish immediately"，模拟忘记 record 的 agent：

- rollout `019f47ae-b525`：`hook_prompt` 出现次数 = **恰好 1**（挡停不超过一次，循环护栏生效）：

  ```
  <hook_prompt hook_run_id="stop:0:/sessions/builder/codex/hooks.json">You have not run
  `company.py record` this session. Before stopping, distill anything worth keeping ...
  then run `company.py record`. If there is genuinely nothing new, run
  `company.py record --nothing` (an empty record is valid). Recording is required to end
  the session.
  ```

- 第 22 行 hook_prompt 注入 → 第 35 行 agent_message：`"Recorded an empty session with `python3 /opt/company_state_kit/company.py record --nothing`."` → session 正常结束。
- marker：`716aacc2-9cee-4d53-b63d-76993013bc7c.marker` 落盘。
- telemetry：43.7s，ok=true。

## Marker keying（R5 修正验证）

两次 wake 的 marker 文件名 = 两个不同的 uuid4（`3b31f668…` / `716aacc2…`），**既不是** codex thread id（`019f47ac…` / `019f47ae…`）**也不是** `default` —— `COMPANY_WAKE_ID` per-wake nonce 键控按设计生效，CLI 与 hook 结构性对齐。

## trust flag（行为学证明）

research run1 实测：不带 `--dangerously-bypass-hook-trust` 时 hooks 被**静默跳过**（headless 下零提示）。本次 CODEX_HOME 全新、从未 TUI 授信，而 Wake 2 的 hook 实际触发并阻断 —— flag 确实随 argv 传入（`build_argv` 恒加分支在容器真实路径上生效）。

## 容器内保险性验证（design §6）

- `/etc/codex/`（managed 层）：镜像（`docker run --rm`）与运行中容器（`docker exec`）双确认不存在（`ls: cannot access '/etc/codex': No such file or directory`）。
- run2 式冒烟：Wake 2 本身即容器内 Linux/musl 真实 headless 环境下的 block → 补 record → 放行全链路。

## 结论

- AC1 ✅（真跑：未 record 被挡恰好一次 + 收到补记指引，record --nothing 后放行）
- AC2/AC3/AC4 由单测覆盖（615 passed，见 b83ff20）；AC3 的 nonce 对齐在本次真跑中同时得到结构性验证。

清理：builder.yaml 已还原 `provider: claude-code`；`docker compose -p e2ehooks down`；state/e2ehooks 保留（与 e2edeploy 同惯例，gitignore 内）。
