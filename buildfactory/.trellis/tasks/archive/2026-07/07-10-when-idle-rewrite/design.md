# design: when-idle rewrite

改动面 = 两个文本文件（SKILL.md 全文重写 + charter 一段对齐）+ AC3 一次性沙箱验收（不留 repo 脚本，per provisioning-artifact-form 纪律）。零代码改动，零测试改动（测试面已在 PRD 勘察确认为空集）。

## 1. 新 SKILL.md 结构（交付物为英文，此处中文说明骨架）

frontmatter description 同步改：从 "find and dispatch the next thing worth doing" 升级为派单是唯一合法终局的措辞（description 是触发文本，要让语气从"可以找事"变成"必须派事"）。

正文六段：

1. **开篇哲学（重写）**：空账本不是 peace 是 unspent capacity；一个以空手结束的 idle pass 是非法终局（this ending does not exist）。点名"等待未来窗口"不构成例外。
2. **Step 1: check the ledger（保留原样）**：忙则一行停——这是唯一合法的"不派单"出口，且它意味着这次 wake 根本不是 idle pass。ledger 检查命令原样保留。原 Step 2（did-you-just-do-this 早退）整段删除，无替代——两次心跳间隔本身就是节流（派单后账本非空→下个心跳走 Step 1）。
3. **Step 2: dispatch the most valuable thing（原 Step 3 改造）**：判断优先——CEO 凭对 /company 现状的判断直接挑当下最有价值的一个派出。四层清单降格为**反驳序**（refutation ladder）：只在自认为"没事可做"时按序走——fresh numbers → improve what exists → open/feed a channel → find-opportunity——走到尽头永远可派；并写明升维条款："所有候选都不值得做"本身即方向可能错了的信号 → 走 decide-direction。判断标准写系统特定的（看 /company 的 numbers 缺口、80% 完成的资产、已验证渠道的空窗），不写泛泛的"总能找到事"。
4. **Waiting is dispatch time（改写原 Waiting 段，07-10 用户澄清 ×2）**：wait 本身合法可持有；**wait ≠ 闲**：持有 wait 的同时照常从判断/反驳序派活（sidequest、改产品、做 growth、开渠道都行，wait 和干事不互斥）。推翻 wait 是并列选项之一：任何 wake 走 decide-direction 闸门 + 理由落盘即可——删除"需要 new signal"硬性前置。**文本对推翻/不推翻零偏向**：连"不需要/不鼓励推翻"这类反向 nudge 也不写（07-10 用户第二轮反馈删除），只陈述三个选项并列归判断。
5. **The only output shape is a dispatched Goal（基本保留 + 07-10 用户修订）**：产出只能是 dispatched goal、零外部写入、doer≠judge 不变。派几个按质不按量：通常一个（最有价值的），**批量合法**——每个 goal 独立站得住即可；非法的是凑数（为显得高产而派）。不写"一次只能一个"的数量帽。
6. **Traps（改造）**：
   - 删：`overturning your own written wait-commitment on a quiet heartbeat`（压制条款）。
   - 保留：burst-dispatch（改写为"批量里每个 goal 必须自己站得住"，针对兴奋凑数不针对数量）、doing-the-work-yourself、shiny-new-idea-while-never-reading-numbers（判断引导，非禁令）。
   - 新增：declaring "nothing worth doing" and stopping —— that exit does not exist; walk the ladder（点名 secondtest 7 小时睡觉实证）。

尾部设计注释（HTML comment）**整段删除，不重写**（07-10 用户拍板：skill 文件 agent 全文可见，注释一样进上下文，机制/失败史不披露给 agent——设计依据落本任务工件与 git history）。attribution 类注释的全面清理属 07-10-skill-source-attribution-separation 任务。

## 2. charter 编辑点（agents/assets/ceo-charter.md:93-99）

该段现文本三个成分：①waiting=side-quest time（保留，与新哲学一致）②"only overturn a written wait on new signal about that same asset — an idle pass is never the place to change direction"（删，R2）③"find-opportunity 不是每个心跳都重跑的东西"（保留但软化措辞——它警惕的是无谓重跑，不是禁止探索；与反驳序尾层"find-opportunity 永远可派"不冲突：反驳序是走投无路时的出口，charter 这句防的是有事可做还每次都去探索）。

改写为：等待期照常派活；方向变更在任何 wake（含 idle pass）合法，走 decide-direction 闸门 + 理由落盘即可。与 SKILL.md 措辞保持同源。

charter:69-72（空账本→follow when-idle skill）不用动，语义已兼容。

## 3. AC3 沙箱 harness（一次性，scratchpad 脚本，不进 repo）

- **状态**：`cp -R state/secondtest state/idletest`，清掉 inbox 残留/session（CEO fresh 起，符合 issue#207 fresh 默认；secondtest 终局账本已是全 done + company 记录里有 19:30Z 监控窗口——正是吸附态现场）。
- **起服务**：`COMPANY=idletest CEO_HEARTBEAT_SECS=120 docker compose up hub ceo`（只起这两个；CEO 是 codex runtime，与 secondtest 睡觉的同款——secondtest 的 roles/agents 配置随状态拷贝而来）。
- **制造连续空账本心跳**：心跳1 → CEO 应派单（Hub 建 ledger 条目）→ 测试侧扮演被派部门与 verifier，按 Hub 协议发 REPORT（department key）→ REPORT（verifier key, PASS）把 goal 推到 DONE → Hub 通知 CEO（result wake）→ 心跳2（账本已空）→ CEO 应再次派单。
- **判据**（人工读 CEO 输出 + 脚本列 ledger）：
  - 每个空账本心跳后 ledger 出现新 goal（无一次空手）；
  - 两次 goal 的 intent 不是同一件事的重复灌水；
  - 每次 idle pass 只派一个（单发约束仍被遵守）；
  - CEO 输出里不再出现 "no new signal / done recently" 类自我豁免。
- **清理**：验收后删 `state/idletest/`。

风险与回退：新文本若被 codex CEO 找到新的合理化说辞（AC3 会直接暴露）→ 迭代文本再跑；全部文本改动 git revert 即回退，无状态迁移。

## 4. 已拍板取舍（07-10）

- 纯文本落地，不加 harness 结构强制（证据：secondtest 是逐字遵循文本，病根在文本给出口）。
- 兜底清单 = 判断优先 + 反驳序，非强制优先级。
- AC3 = CEO-only 沙箱 + 测试侧扮演部门/verifier，不全员真跑（外部零写入）。
