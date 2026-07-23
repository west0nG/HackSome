# V6 冻结与测试基线

- 冻结提交：`9df4b99 chore: snapshot v6`
- 冻结分支：`v6`
- 创建后 `main` 与 `v6` 均指向 `9df4b99`，当前工作分支仍为 `main`。
- V6 快照包含已确认的 16 个 tracked modifications 与 `.trellis/tasks/07-13-fourthtest-codex-sol-first-revenue/`，不包含本 V7 规划目录。

## 全量测试基线

命令：

```bash
.venv-cua/bin/python -m pytest agent/tests/ orchestration/tests/ company_state_kit/tests/ peripheral/tests/ -q
```

结果：`712 passed, 1 failed`。

唯一失败：`agent/tests/test_de_ai_ify_integrity.py::test_de_ai_ify_reference_links_resolve_end_to_end`。V6 的 `growth` 已配置为 Codex provider，`resident_loadout` 因此把 Skill 物化到 Codex home，而该旧测试仍固定检查 Claude home 下的 `skills/de-ai-ify/SKILL.md`。这是 V7 代码修改前已经存在的基线失败，后续 loadout 契约收口时一并修正测试口径。
