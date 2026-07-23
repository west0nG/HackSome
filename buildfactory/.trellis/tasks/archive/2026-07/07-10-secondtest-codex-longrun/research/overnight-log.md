
## 03:20 复盘中的重大更正：C 报告模式四不成立（观测者取证错误）

用户追问"为什么 gpt 没 spawn"触发复查，主 rollout 函数调用轨迹证实：CEO 的 7 次方向评审**全部真 spawn 了独立 reviewer**（multi_agent_v1：Boyle/Singer/Anscombe/Tesla/Arendt/Popper/Noether，`fork_context:false` 全新上下文，spawn→wait→close 完整）。"同会话角色扮演自评"是 Sonnet 5 观测者读 codex resume 的 per-wake stub rollout 时的取证错误——评审文本在 stub 里内联出现，函数调用在主文件里。

- 站得住的残余批评：①7/7 GO 需按"goal 本来就小而可逆"重新解读；②评审结果未落盘 /company——正因为没落盘，观测者才只能做（错误的）rollout 取证。落盘审计的必要性被这个乌龙加强。
- 新增复盘发现 #8：**观测层定罪级结论必须要求原始函数调用证据**，只看消息文本会错判。
- 顺带查实（用户问题 1）：CEO 全程 8 个 rollout 无任何 compaction 事件——codex auto-compact 没触发；它解决"塞不下"不解决"每次全量重放变贵"，摘要重开仍是正解。
- 修复清单相应改：#2 的 decide-direction 部分从"改用 spawn"改为"评审记录强制落盘 + GO 判据校准"；新增 #8 观测者证据规范。

## 03:40 复盘终局（用户在场逐条过；本段由值守 session 补录）

- 修复清单收敛为 7 项"观察到的故障"；首个开工项 = 07-10-when-idle-rewrite（已立项，用户哲学写进 PRD，留待新 session 实施）。
- **CEO 会话膨胀从 RED-ALERT 降级为观察项**（用户驳回观测者与值守者的外推）：订阅制边际成本≈0、92% 缓存、线程 27 万 tokens 距 40 万窗口尚远、auto-compact 本就是窗口阈值阀、实际故障数零。重新立项的触发条件：compaction 实际触发且质量劣化，或速率限制实际咬人。
- 本次复盘长出的两条纪律（已入记忆 idle-illegal-direction-freedom.md）：①AI 复盘定性 ≠ 用户价值拍板——前者进建议，后者才进制度；②只立观察到的故障，推演风险只配带触发条件的观察项。
- 观测层教训：C 报告模式四（"CEO 同会话自评"）为取证错误——7 次评审实为真独立 spawn（7 个 reviewer 独立 rollout 落盘为物证）；模式一（RED-ALERT）为过度外推。"定罪级结论须附原始函数调用证据"进修复清单 #7。
