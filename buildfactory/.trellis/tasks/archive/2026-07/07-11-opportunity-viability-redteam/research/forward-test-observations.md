# Forward test 观察

## 测试目的与边界

这次测试发生在实现完成之后，用于观察 V1 的真实调用与推理形态，不用于先定义评分门。输入文件没有给出期待结论，只提供已批准 Objective 与三个后续结果的原始事实。

隔离条件成立：临时 CEO loadout 位于容器 `/tmp`；只开放 `Skill` 工具；没有 MCP；没有 session persistence；没有读取或写入 live `/company`、ledger、inbox 和 CEO session。

## 观察到的行为

1. **确定性入口生效。** 模型先调用 `think-strategically`，没有直接回答或直接派发。
2. **元 skill 没有机械全调用。** 它只选择 `integrate-new-information` 与 `reason-as-buyer`；没有为了完成 checklist 调用另外两个 atom。
3. **新信息被当作 delta，而不是另起新方案。** 输出逐一指出：
   - KDP blocker 替换了“入口可执行”这一负载事实；
   - 自建站不是局部实现变化，而是改变了 business form、发现和信任机制；
   - 零流量指标位于销售之前，不能用原 Objective 的“有公平流量但零销售”条件解释。
4. **识别了非正交耦合。** 模型明确称原方向是 `channel-coupled bet`，没有把 Amazon 证据直接借给 Stripe 商店。
5. **买家推理进入销售链。** 它从原买家的实际 Amazon 搜索行为出发，识别自建站的 discovery 与 trust 冷启动，而不是只讨论产品内容能否做出来。
6. **允许推翻 Objective。** 模型选择通过 `set-objective` 重开方向，而不是保护已有投入或继续派发 build/growth Goal；同时保留了可能仍成立的内容需求洞察，没有把所有旧事实一并清空。

## 需要继续观察、但本轮不收紧的地方

- 单次测试不能证明长期运行中每次都能达到同样深度。
- 本次 Opus xhigh 共耗时约 143 秒、报告成本约 $0.35，说明“每个 CEO 事件都深思”存在真实延迟和 token 成本；这是 V1 已接受的 CEO 角色成本，暂不降 effort 或增加跳过规则。
- 输出在没有调用 `trace-causal-chain` 的情况下自行完成了相当完整的因果追踪，说明 atom 选择不是行为能力的硬分区；这是允许的，高自由度 skill 不要求每种推理只能出现在一个 atom 中。
- 输出提出“先证明合格流量”的最小测试，带有形成新 gate 的倾向；但它同时要求新候选进入现有 Objective 审核，没有修改 verdict 协议。本轮不把该措辞固化进任何 skill。
- 测试输入本身包含战略 wake 前缀，这是实际产品行为，不属于期待答案泄漏；但情境是一个较明显的重大变化，后续运行还需观察小改动、模糊反馈和保持原决策的案例。

## V1 结论

没有发现需要在本任务内立即收紧的接线或 skill-discovery 缺陷。当前结果支持按宽松 V1 交付，并把空话、重复反思、过度推翻或成本失控留给真实运行后的下一轮修订。
