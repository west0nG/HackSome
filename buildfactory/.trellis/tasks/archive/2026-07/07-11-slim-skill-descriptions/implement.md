# 实施计划：全量精简 Skill Description

> 用户已审阅批准，任务已通过 `task.py start` 进入实施；下列勾选项记录本次实际完成状态。

## 1. 入口边界迁移

- [x] 记录四份 vendored `SKILL.md` 的实施前 SHA-256，与 `design.md §2.1` 对齐。
- [x] 将四份文件改名为同目录 `upstream-SKILL.md`，不修改文件字节。
- [x] 更新 `de-ai-ify`、`design-asset`、`gen-image` host 中的读取路径与 reference map。
- [x] 更新现行测试和物化断言，补充“子树内 SKILL.md 称呼指 upstream-SKILL.md”的 host 适配说明；现行树无受影响 ATTRIBUTION 路径可改，见 verification。
- [x] 运行引用扫描，确认没有仍指向四个旧路径的可执行引用。

## 2. 全量改写 20 份 Description

- [x] 按 `design.md §4` 精确改写 20 个顶层 `SKILL.md` frontmatter；正文除路径适配外不扩面。
- [x] 使用合法 YAML folded scalar；修复原 `de-ai-ify` 未加引号冒号导致的严格 YAML 解析问题。
- [x] 逐项核对能力、正向触发、必要边界，没有把执行步骤移入 description。
- [x] 生成实施后 catalog 报告，核对总计 2,863 字符及五个角色预算。

## 3. 长期静态门

- [x] 新增 `agent/tests/test_skill_catalog.py`：字段/名称/空白、200 字符单项预算、2,000 字符角色预算、嵌套 `SKILL.md` 禁止、角色集合计数、四份 vendor 哈希。
- [x] 为高碰撞 skill 组增加最小语义锚点，不锁死整句。
- [x] 更新 `agent/tests/test_operate_twitter_skill.py` 的 frontmatter 断言，使其固定新语义而非旧词形。
- [x] 确认 `test_de_ai_ify_integrity.py`、`test_resident_loadout.py` 与视觉子树物化断言适配新路径。

## 4. 文档同步

- [x] 更新 `aiworkforce/SOP-adding-roles-and-skills.md`。
- [x] 更新 `docs/overview.md`。
- [x] 更新 `.trellis/spec/backend/agent-execution-contracts.md`。
- [x] 不修改任何归档任务、live state 或历史 e2e 证据。

## 5. 确定性验证

按从窄到宽顺序执行：

```bash
./.venv-cua/bin/python -m pytest \
  agent/tests/test_skill_catalog.py \
  agent/tests/test_resident_loadout.py \
  agent/tests/test_de_ai_ify_integrity.py \
  agent/tests/test_operate_twitter_skill.py \
  agent/tests/test_objective_skills.py \
  agent/tests/test_spec.py \
  agent/tests/test_codex_runtime.py -q

./.venv-cua/bin/python -m pytest agent/tests/ -q
./.venv-cua/bin/python -m pytest orchestration/tests/ -q
```

- [x] 所有目标测试通过（83 passed）。
- [x] 全量 agent/orchestration 回归通过（233 + 396 passed）。
- [x] `rg` 确认只有 20 个顶层可发现 `SKILL.md`，四个旧嵌套路径清零。
- [x] 实施后四份 `upstream-SKILL.md` SHA-256 与设计固定值一致。

## 6. 双 Runtime 隔离验证

- [x] 在一次性容器临时目录物化 Growth 与 CEO loadout，不修改现有 firsttest/secondtest/thirdtest。
- [x] 用镜像固定 Claude Code 2.1.202 做 catalog 发现检查。
- [x] 用镜像固定 Codex 0.142.5 做 catalog 发现检查。
- [x] 两边运行 `design.md §6.2` 的八个高风险路由场景；禁止外部写入。
- [x] 把 provider/version、实际 catalog、每个场景命中与偏差写入任务 research 工件。
- [x] 两边均 8/8 命中，未出现稳定误触发 sibling，无需调整 description。

## 7. 收尾门

- [x] 对照 PRD AC1–AC7 逐项记录证据。
- [x] 重读 20 份最终 description，确认无执行流程、实现背景或冗余枚举回流。
- [x] 重读 `prd.md`、`design.md`、`implement.md`，同步实施中经批准的措辞变化。
- [x] 已运行 Trellis 质量检查；未经用户另行授权，未提交、未推送、未改 live company state。任务因工作改动尚未提交而暂不 archive。

## 风险文件与回滚点

- 四份 vendored 入口及三个 host：路径改动最容易造成断链；先做、先测，必要时独立回滚。
- 20 份 `SKILL.md` frontmatter：正文不做顺手清理，降低 review 面。
- `agent/tests/test_skill_catalog.py`：预算与 catalog 规则的长期 source of truth；阈值只来自已批准 PRD。
- 文档/spec：必须与测试常量同步，避免“文档说顶层、运行时又递归暴露”的再次漂移。
