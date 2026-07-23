# Observatory 执行清单

## 顺序

1. [ ] `observatory/runner.py`：数据结构与纯函数先行（终态扫描、processed 集、prompt 组装、argv 构造、报告写盘+元数据头、RED-ALERT 检测），再包 daemon/once CLI。stdlib-only。
2. [ ] 三份宪章 `observatory/charters/{goal_postmortem,company_review,final_synthesis}.md`（中文；按 design「宪章要点」的三道检验写，禁止泛泛而谈）。
3. [ ] `Makefile`：`observatory` / `observe` / `observe-final` 三个 target（透传 COMPANY，默认 foundagent 与现有 target 一致）。
4. [ ] `observatory/tests/test_runner.py`：按 design「测试策略」全覆盖，fake CLAUDE_BIN fixture。
5. [ ] 全量测试绿（`python -m pytest -q`）。

## 验证命令

- 单测：`/Users/weston/dev/BuildFactory/.venv-cua/bin/python -m pytest observatory/ -q`（+ 全量）
- 真跑（AC1/AC2，真 Sonnet 5）：构造终态 goal 后 `python observatory/runner.py --company hardsmoke once-goal <id>`、`once-company`；人工审报告。

## 评审门

- 宪章三份写完后先给用户过目（观测维度是本次实验的灵魂），代码可先行。

## 回滚点

- 纯新增目录 + Makefile 三行，`git rm -r observatory/` + 还原 Makefile 即完全回滚，无运行时耦合。
