# Creative Route 真实 Smoke Test 报告

## 1. 结论

`Hack the Rest — 重新创造休息` 已使用真实 Codex Agent 跑到 C6 唯一人工关卡。
最终有效 run 为 `creative-hack-the-rest-20260724-04`：

- 状态：`waiting / creative-human-review`
- Agent tasks：65 succeeded，0 failed
- 初始 Concept：12
- C4 Hook-pass：12
- C6 shortlist：5
- shortlist 覆盖：4 个 primary Territory
- Review batch：`creative-review-batch-r001`
- 离线验证：`Run is valid.`

本轮按约定没有伪造 reviewer、关闭 C6 或继续到 C7。因此现在得到的是五个
待人工评审的 Concept revision，而不是最终 Idea Card。Idea Card 只会在真实
人审 resolution 闭合后确定性生成。

真实 run 目录与 raw log 不提交到 Git；本报告只记录可复核的统计、首因与内容
摘要。

## 2. 运行配置

- Route：`creative`
- Model：`gpt-5.6-terra`
- Reasoning：`medium`
- Idea Memory：`off`
- 最大并发：4
- 基础设施重试：1
- 单任务超时：600 秒
- 运行超时：7200 秒
- Creative Brief：约 30 秒内产生真实、可解释、可复述、让人想到分享对象的
  惊奇/好笑/神秘/诗意体验；排除仪表盘、普通冥想/番茄钟、AI 鸡汤、长文案和
  不可解释 AI 魔法。

## 3. 三次 fail-closed 与对应修复

| Run | 停止点 | 发现 | 修复 |
| --- | --- | --- | --- |
| `-01` | C2 | Validator 要求 Atom 正文包含模型从未收到的 Controller Territory ID | `a9a8ecb`：正文恢复自然语言职责；Controller 用 ID、metadata、source refs 和显式 C3 Atom→Territory index 维护谱系 |
| `-02` | C2 | 一个 Explorer 把八个必需 H2 压进单个 `Mechanism` section | `9af471a`：C2 Prompt 加入逐字、逐段模板并禁止 inline/bold 压缩 |
| `-03` | C4R | 局部修复改写了 Validator 要求保持不变、但 Prompt 未明示的 source section | `c15e0ce`：C4R/C6A Prompt 明示三个不可变 section，并指明时序、风险与 Demo 澄清应写入哪些可变 section |
| `-04` | C6 | 65 个任务全部成功，生成非空 review batch | 目标达成；保留 open C6，不伪造人工反馈 |

这些失败均留下 immutable terminal error 与 partial report；它们不会进入 Idea
Memory，因为只有 completed、validated 的 Creative run 才可被未来 run 发现。

## 4. C6 Shortlist

| Concept | Primary Territory | 一句话 Hook | 初步判断 |
| --- | --- | --- | --- |
| `s01-01-r002` 房间的接力靠背 | 非常规互动机制 | 你靠住的三十秒里，房间会替你搭起一面不承重、但人人看得见的靠背。 | 规则清楚、低技术、现场共同完成；传播性更偏温暖而非爆笑 |
| `s01-02-r002` 空位的无声请假条 | 反转与揭示 | 你坐进空白三十秒，世界仍在动，但没有一件事可以穿过这张椅子来找你。 | “请求可见但不能穿过边界”很完整；稍有企业健康/艺术宣言气质 |
| `s01-03-r003` 闭眼后的影子借阅处 | 神秘叙事 | 你闭眼五秒，影子会替你把一声哈欠借出去；睁眼后，你得找回它去过哪里。 | 本批最神秘、最像可转述的小故事；低技术侦破机制也最完整 |
| `s02-03-r002` 放下以后，半句话开始唱 | 非常规互动机制 | 你放下手里的东西并停住半句话，大家才有资格替它唱完——但谁也不能替你回答。 | “只改形式、不代答、拿起即坍缩”是独特规则；需要主持人控制边界 |
| `s03-03-r002` 空位的反向合唱 | 社交传播与共同表演 | 你后退一步把位置留空，房间便只能为这段空白唱，不能替你补位。 | 集体参与和一句话复述较强；与无声请假条、半句话合唱存在近似 |

两个独立 Portfolio Curator 对前四项均给出 `include/include`。第五项得到
`include/hold`，由 Controller 的 Territory round-robin 与剩余容量选入。

## 5. 内容质量判断

### 已成立

- 所有入选项都能在约 30 秒内形成可见或可听的因果闭环。
- 最小 Demo 大多只需要卡片、纸张、椅子、桌面物件和现场参与者，不依赖虚假
  AI 能力或未授权数据。
- Hook 基本都能被一句话复述，且明确避开了“做一个休息 App”的惯性答案。
- Novelty Scan 没有把“搜不到”写成绝对原创；C6A 会披露近邻、文化边界和
  刻意未采用的证据。

### 仍不足

- 12 个初始 Concept 明显收敛到“空位、影子、哈欠、合唱、缺席”语义簇。
  六个 C2 Territory 确实不同，但四个 C3 Agent 看到完整 Atom index 后仍选择了
  相似的高显著性 Atom。
- 五项 shortlist 覆盖四个 Territory，但语义层面仍有三项围绕“留下空白、
  他人守住/回应”的近似结构。Controller 的 Territory round-robin 只能保证
  metadata 多样性，不能自动保证体验多样性。
- 整体更接近诗性参与艺术，惊奇和神秘已出现，但“好笑、会立刻录视频转发”
  的强度仍弱。
- 多数体验依赖主持人、三到六位参与者和预置卡片；技术上的 hackathon
  wow-factor 较低。

## 6. Harness 与成本观察

有效 run 的墙钟时间约 17 分 31 秒，共发布 132 个 artifact。65 个任务合计：

- input tokens：2,312,107
- cached input tokens：1,492,224
- output tokens：85,134
- reasoning output tokens：9,956

C5W 的 12 个 Novelty Scan 消耗 1,673,286 input tokens，占总 input 的约
72.4%；其中最慢任务约 404.7 秒。说明“每个 Hook-pass Concept 都独立联网查重”
是当前最主要的时延和 token 成本。

网络噪声审计：

- 49/65 个任务的 raw stderr 含 `ERROR` 或 `WARN`
- 共 166 条，主要是 WebSocket TLS、analytics 与瞬时重连
- 0 个 Prompt 或 structured output 含这些错误字符串

因此这些报错会保存在每个任务的 raw log 中用于诊断，但不会进入后续 Agent
上下文；本轮 65 个任务仍全部成功。裸 `codex exec` 的终端输出很吵，不代表
harness 的创意上下文被污染。

## 7. 下一轮建议

先不要根据一道题直接重写工作流。下一轮 benchmark 建议明确比较：

1. 当前“每个 C3 Agent 自由读取全部 Atom”的基线；
2. Controller 给 C3 分配不同 primary Territory 或不同 Territory pair 的
   coverage 约束。

评价重点不是模型自评，而是人工判断：

- shortlist 的体验机制是否真正不同；
- 30 秒内是否想笑、惊讶或追问；
- 能否一句话复述；
- 是否立刻想到一个想转发的人；
- 是否值得为它拍一段现场视频。

成本侧可以另做一个严格对照：在不牺牲近邻证据的前提下，先对 Hook-pass
Concept 做 deterministic/semantic cluster，再决定 C5W 是扫描所有候选还是只
扫描机制代表项。该改变会影响证据完整性，必须通过 benchmark 决定，不能仅因
本轮 token 高就直接修改合同。
