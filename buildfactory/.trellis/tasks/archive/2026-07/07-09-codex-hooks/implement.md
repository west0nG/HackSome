# Implement plan: codex-hooks

前置：design.md 已定稿并经用户审阅。步骤按序执行；每步末尾的验证命令必须绿再进下一步。pytest 用 `.venv-cua/bin/python -m pytest`（或 `/opt/homebrew/bin/pytest`），仓库根 /Users/weston/dev/BuildFactory。

## 步骤

1. **helpers 上移（design §2a）**
   - `_snippet_hooks/_merge_hooks/_remove_hooks` 从 `agent/runtimes/claude_code.py` 移到 `agent/loadout.py`（公开名 `snippet_hooks/merge_hooks/remove_hooks`），claude adapter 改 import；docstring 注明"操作任何含顶层 hooks 键的 JSON 文件（claude settings.json / codex hooks.json）"。
   - 验证：`pytest agent/tests -x -q`（golden test `test_claude_runtime_golden.py` 必须零改动通过）。
   - 回滚点 A。

2. **codex materialize_home 第 4 步（design §2b）**
   - 替换 TODO：reconcile 流程与 claude 对称（读 snippet → diff 上次 manifest → remove → merge 进 `CODEX_HOME/hooks.json` → `write_manifest(names, snippet_hooks)`）。无 hooks 声明：不创建文件；上次有本次无：remove 后若文件 hooks 空且无其他键可留空壳（与 claude 的 settings.json 行为一致，不删文件）。全程 try/except 降级 WARN。
   - 单测（`agent/tests/test_codex_runtime.py`）：①声明 hooks → hooks.json 生成且条目在；②两次 materialize 幂等；③撤声明 → 条目被撤、agent 自加条目保留；④snippet 损坏 → WARN + 其余 carrier 照常；⑤manifest hooks 槽记录正确。

3. **build_argv 恒加 trust flag（design §2b/§4）**
   - `--dangerously-bypass-hook-trust` 追加在 `--dangerously-bypass-approvals-and-sandbox` 旁（同受 `bypass_permissions` 门控？——不：flag 语义独立，恒加，含 bypass_permissions=False 分支也加，因 hooks 静默跳过与权限模式无关）。parse_output 加注释：flag 引入的 2 条非致命 error item 已被现立场覆盖。
   - 单测更新 argv 断言（现有 argv 测试会 fail-first，逐个修）。

4. **snippet 加 timeout（design §2c）**
   - `company_state_kit/hooks/settings.snippet.json` 条目加 `"timeout": 30`。
   - 验证：`pytest company_state_kit/tests agent/tests -x -q`（claude merge 的值相等性 dedup 对 snippet 变更的 reconcile 行为由步骤 2 测试覆盖）。

5. **marker keying：COMPANY_WAKE_ID（design §2d）**
   - `company_state_kit/company.py` `session_marker_path`：优先级 `COMPANY_RECORD_MARKER` ＞ `COMPANY_WAKE_ID` ＞ 现状（参数 session_id / `COMPANY_SESSION_ID`）＞ default。docstring 更新优先级表。
   - `orchestration/agent_loop.py` `wake()`：nonce=uuid4，`subprocess.run(..., env={**os.environ, "COMPANY_WAKE_ID": nonce})`，三条路径（runtime/fallback/timeout 前）一致。
   - 单测：company_state_kit 优先级矩阵（4 层）；agent_loop 子进程 env 注入（mock subprocess 断言 env）；broker 路径无 COMPANY_WAKE_ID → 现状行为（回归钉）。
   - 回滚点 B（与 1-4 独立可 revert）。

6. **全量回归**
   - `pytest agent/tests orchestration/tests company_state_kit/tests observatory/tests -q` 全绿。

7. **AC1 真跑（含 design §6 两条容器验证）**
   - 起容器栈（或单容器 docker exec），一个 `provider: codex` 角色 + record hook：wake 一次不 record → 观察 block 一次 + 补 record 放行；`docker exec` 确认 `/etc/codex/` 不存在。留存日志证据到任务目录。

## 验证总命令

```bash
.venv-cua/bin/python -m pytest agent/tests orchestration/tests company_state_kit/tests observatory/tests -q
```

## 回滚

- A：仅 revert helpers 上移（纯移动，无行为变化）。
- B：revert 步骤 5 两文件 → 退回"每次白拦一轮"现状，无数据迁移。
- 全回滚：revert 本任务全部提交；镜像/compose 无改动，无需重建。
