# when-idle rewrite: idle pass is an illegal state

## 背景

- 记忆 `idle-illegal-direction-freedom.md`：用户 07-10 拍板的设计哲学（本 PRD 的最高依据）——idle pass 必须派单、方向变更权归 AI（闸门管质量不管频率）、勿把 AI 复盘定性固化成制度。
- 实证：secondtest 长跑（state/secondtest/ + `.trellis/tasks/archive/…/07-10-secondtest-codex-longrun/research/overnight-log.md` + 终局报告 `state/secondtest/observatory/final/20260710T030339Z.md` 模式二）——CEO 靠 when-idle 现有的两个早退出口"合法"睡了 7 小时：所有 goal done 后第一轮 idle 巡检得出"等明天 19:30Z 的监控窗口"，之后每个心跳撞 Step 2 早退（"idle pass done recently, no new signal"逐字引用 skill 原文），"等待"成为稳定吸附态；Step 3 的 side-quest 条款（写在早退之后）再也不会被走到。
- 当前 skill 的保守标定源自 firsttest 复盘时 **AI 的分析定性**（"三次翻方向=病"、"boredom is not a signal"），不是用户的价值拍板——本次重写按用户拍板纠正。

## 改动面清单（已勘察确认）

- `agents/assets/skills/when-idle/SKILL.md` 全文重写。现文本中的具体病灶：
  - Step 2 早退（SKILL.md:26-32）——secondtest 逐字引用的出口，删。
  - Step 3 "Never flip the company's direction inside an idle pass… boredom is not a signal"（SKILL.md:48-51）——删。
  - "Waiting is side-quest time" 段的 "it is NOT a reason to overturn the wait… Overturning a written wait takes new signal about that same asset"（SKILL.md:54-58）——对换向权的硬性压制，删限制、留"等待期照常派活"的正面指引。
  - Traps 第二条 "overturning your own written wait-commitment on a quiet heartbeat"（SKILL.md:72-73）——同上对齐。
  - 尾部设计注释引用 pattern ⑦ "direction changes are gated out of idle passes"（SKILL.md:79-84）——按新哲学改写。
- `agents/assets/ceo-charter.md:93-99` 有同款压制措辞（"only overturn a written wait on new signal… an idle pass is never the place to change direction"）——一并对齐。
- 测试面（已确认为空集）：无任何测试断言 when-idle 文本内容。只有 loadout 存在性检查（agent/tests/test_resident_loadout.py:29）与 yaml `idle:` 键管线（test_spec.py:117、orchestration/tests/test_agent_loop.py:702-729），纯文本重写不触碰。`orchestration/agent_loop.py` 的 proactive 提示词只说 "charter's idle duties apply"，不用动。

## 需求

- R1（idle=非法态）：**账本无在跑 goal 时，idle pass 的唯一合法终局是派出至少一个 goal**。删除全部空手出口。"在等某个未来窗口"不构成空手理由——wait 本身合法可持有（不需要也不鼓励推翻），但 wait ≠ 闲：持有 wait 的同时照常派活（sidequest/改产品/growth/开渠道，wait 和干事不互斥）。
  - 兜底清单语义（07-10 拍板：判断优先 + 反驳序）：CEO 凭判断直接挑"当下最有价值的一个"派；清单（收数据 → 改进现有资产 → 开/喂渠道 → find-opportunity 探索第二机会）只在自认为"没事可做"时充当反驳工具——按四层走到尽头 find-opportunity 永远可派；"所有候选都不值得做"本身即"方向可能错了"的信号，走 decide-direction。不写成必须逐层下行的强制优先级。
- R2（方向变更权归 AI）：删除全部压制性措辞（见改动面清单）。方向变更在任何 wake（含 idle pass）都合法，条件只有一个：走 `decide-direction` 闸门且理由落盘可审计——闸门管"换得有没有理由"，不管频率、不管触发时机、不管有没有"新信号"。合法 ≠ 鼓励：推翻 wait/换向只是与 hold-the-wait、并行派活并列的选项之一，新文本不设偏向，全凭 CEO 判断。
- R3（保留项，勿动）：账本**有**在跑 goal 时"一行确认后停"仍合法（公司不闲就不是 idle）；"idle pass 自己不做业务、不对外写、产出只能是 dispatched goal"的结构不变（doer≠judge）；worker 侧硬停不变（本任务只动 CEO 的 when-idle 面）。
- R4（一致性）：SKILL.md 尾部设计注释**删除不重写**（skill 资产零注释，见约束）；ceo-charter.md 引用段同步更新；现有测试零回归（测试面已确认无文本断言，预期零改动）。

## 约束

- 纯文本落地（07-10 用户拍板）：本轮只改 SKILL.md + charter 措辞，不加 harness 侧结构强制（agent_loop 不动）。依据：secondtest 里 CEO 是逐字遵循 skill 原文空转的，病根在文本给了出口；若重写后真跑再现合理化空转，另立任务补结构闸门。
- 遵循 skill 三道检验（系统特定/压制 LLM 默认/非平凡取舍）：新文本要写清"什么算可派的事"的判断标准与兜底顺序，不写泛泛的"总能找到事做"。
- 防新病（07-10 用户修订：按质不按量）：必须派单 ≠ 鼓励灌水，但**批量合法**——一次 pass 派几个由判断定，唯一标准是每个 goal 独立站得住（advance the company），非法的是凑数（为显得高产而派）。不设"一次只能一个"的数量帽（那又是频率管制）；firsttest 的 burst 教训保留为陷阱警示（针对兴奋驱动的凑数，不针对数量本身）。
- skill 资产零注释（07-10 用户拍板）：SKILL.md 是 agent 全文可见的，HTML 注释一样进上下文——设计注记/机制说明一律落 task 工件与 git history，不落 skill 文件（呼应 issue#207"prompt 只定向不披露机制"）。出处 attribution 类注释的全面清理属另一任务（07-10-skill-source-attribution-separation），不在本任务扩面。

## 验收标准

- [x] AC1：新 SKILL.md 中，空账本 idle pass 不存在任何"空手结束"的合法路径；等待未来窗口的场景有明确的替代派单指引（"Waiting is not idling"段）。
- [x] AC2：方向变更的全部压制性措辞移除（SKILL.md 与 ceo-charter.md 两处，grep 清零验证）；换向路径 = decide-direction 闸门 + 理由落盘，无频率/时机/新信号限制。
- [x] AC3（真跑，CEO-only 沙箱，07-10 拍板；✅通过，全记录见 research/ac3-run-log.md——两个空账本心跳均真实派单，第二个发生在精确复刻的吸附态场景，CEO 原话"Ledger was empty, so I dispatched a side-quest"）：拷贝 secondtest 终局状态（goal 全 done + 存在未来监控窗口）到沙箱目录，只起 codex CEO（与 secondtest 睡觉的同款 runtime），`AGENT_HEARTBEAT_SECS` 压缩心跳；派出的 goal 由测试侧在心跳间隙标记 done（配合理桩结果）制造下一个空账本心跳。CEO 连续 ≥2 个空账本心跳均以真实派单结束（无一次空手），且派的不是同一 goal 的重复灌水。不起部门 worker——外部零写入，验收对象是 CEO 派单行为而非 goal 执行质量。
- [x] AC4：零新增测试失败（改后复测同为 11 failed / 634 passed）。实测基线（07-10）：main 上已有 11 个既有失败（secondtest 全员切 codex 导致 test_spec/test_resident_loadout 的 provider/claude 路径断言失败，与本任务无关）；本任务改动前后均为 11 failed / 634 passed，即零回归。

## 关联（不在本任务范围）

- decide-direction 评审落盘 /company（修复清单 #2）——与本任务配套但独立立项；本任务的 R2 依赖其闸门存在即可，不依赖其落盘改造完成。
