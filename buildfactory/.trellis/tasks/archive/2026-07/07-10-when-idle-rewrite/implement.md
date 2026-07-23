# implement: when-idle rewrite

## 顺序清单

1. [x] 重写 `agents/assets/skills/when-idle/SKILL.md`（按 design.md §1 六段结构 + frontmatter description + 尾注改写）。
2. [x] 对齐 `agents/assets/ceo-charter.md:93-99`（按 design.md §2；charter:69-72 不动）。
3. [x] 自查 AC1/AC2：grep 确认压制措辞清零——`Never flip`、`boredom is not a signal`、`done recently`、`no new signal`、`takes new signal`、`never the place to change direction` 在 agents/ 下无残留。
4. [x] 跑全量测试确认零回归（AC4）：`cd /Users/weston/dev/BuildFactory && python3 -m pytest agent/tests orchestration/tests company_state_kit/tests -q`（重点：test_resident_loadout / test_spec / test_agent_loop 应全绿且无需改动）。
5. [x] 文本改动先给用户审（plan-revision-needs-user-review 纪律），再进 AC3：审阅材料必须包含新 SKILL.md 正文的**完整中文版 dump**（07-10 用户要求；归档前必须完成此审阅）。
6. [x] AC3 沙箱真跑（按 design.md §3）：
   - `cp -R state/secondtest state/idletest` + 清 inbox/sessions；
   - `COMPANY=idletest CEO_HEARTBEAT_SECS=120 docker compose up -d hub ceo`；
   - 心跳1 观察派单 → 测试侧扮演部门/verifier 把 goal 推到 DONE → 心跳2 观察再次派单；
   - 按 design.md §3 四条判据逐条记录（CEO 原话 + ledger 列表存档到任务 research/）；
   - 清理 `state/idletest/` 与容器。
7. [x] （未触发）若 AC3 失败：迭代 SKILL.md 文本（记录失败样本）重跑步骤 6；连续失败 2 轮升级给用户（可能需要结构强制，另立任务）。

## 验证命令

```bash
# 压制措辞清零检查（步骤 3）
grep -rn "Never flip\|boredom is not a signal\|done recently\|no new signal\|takes new signal\|never the place to change direction" agents/ && echo FOUND || echo CLEAN
# 全量测试（步骤 4）
python3 -m pytest agent/tests orchestration/tests company_state_kit/tests peripheral/tests observatory/tests -q
```

## 风险点与回退

- 全部改动为文本，`git revert` 即回退，无状态迁移。
- `state/idletest/` 为一次性沙箱，验收后必删；AC3 脚本放 scratchpad 不进 repo。
- 多 session 共享工作树：commit 前查分支、只 add 本任务文件（SKILL.md、ceo-charter.md、.trellis/tasks/07-10-when-idle-rewrite/）。
