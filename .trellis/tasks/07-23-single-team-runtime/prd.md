# 单 Team Hackathon runtime 与三角色 Prompt

## 目标

把 `buildfactory/` 中一个 Company 的 V7 runtime 裁剪为一个长期 Hackathon Team：
一个 resident Lead、一个并发 Worker、一个并发 Verifier。第一版只证明单 Team 可以
从两份 reference 初始化并持续完成 Goal batch，不实现多 Team registry 或 Review Gate 接线。

## 需求

- 所有实现和测试改动限制在 `buildfactory/`。
- Agent 可见状态挂载为 `/project`，初始化只包含
  `reference/challenge.md` 与 `reference/initial-idea-card.md`。
- Lead、Worker、Verifier 均为 `skills: []`；保留 Skill 框架但不物化任何 Skill。
- 删除 active runtime 中的 CEO、Department、Objective、Notes、Company mail、
  Department messaging、Peripheral 经营语义。
- Lead 是唯一 resident Agent，使用长期 session；它拥有完整项目和工具权限。
- Lead 固定 Prompt 包含角色定位、`/project` 语义、真实状态检查规范和
  `create_goal/list_my_goals/cancel_goal` 的完整 CLI 调用。
- Lead 可以在一次 wake 中创建任意数量 Goal；Goal 按 enqueue sequence FIFO。
- 每个 Team 同时最多一个 Worker；Worker 拥有完整项目与工具权限。
- Worker Prompt 包含当前 Goal、`/project` 语义和 `submit_result` 完整调用。
- Worker 只看 Goal intent；private acceptance 只进入 Verifier Prompt。
- 每次 review 使用 fresh Verifier；canonical `/project` 对 Verifier 只读。
- Verifier Prompt 包含 Goal、acceptance、检查职责和 `submit_verdict` 完整调用。
- Verifier FAIL 恢复同一个 Worker、workspace、home 和 session；PASS 运行 batch
  中的下一条 Goal；队列清空才 wake Lead。
- 删除 Goal deadline、`failed_time` 和 Company idle/完成语义。quiet heartbeat
  只是再次触发 Lead 继续项目。
- 不通过固定产品阶段、目录 taxonomy 或 Objective 决定 Agent 下一步。

## 验收标准

- [ ] 从空 Team state 启动后，三个角色都能看到正确的 `/project` 权限和零 Skill loadout。
- [ ] Lead Prompt 单独即可让 Agent理解角色、项目页和所有 Goal CLI 方法。
- [ ] Lead 一次创建至少两条 Goal 后，系统只运行一个 Worker，并按 FIFO 对每条 Goal
      完成 Worker → Verifier。
- [ ] Worker Prompt 单独即可完成真实工作并正确调用空 payload `submit_result`。
- [ ] Verifier 能运行真实检查，但无法修改 canonical `/project`，且只能提交当前 review verdict。
- [ ] private acceptance 不出现在 Worker Prompt，但完整出现在 Verifier Prompt。
- [ ] FAIL 使用原 Worker/session 返工；PASS 后继续下一 Goal；batch 清空才 wake Lead。
- [ ] 没有 deadline、`failed_time`、Objective review、Department provisioning 或 Skill
      依赖仍进入 active Team 路径。
- [ ] 已有 runtime adapter、幂等 method envelope、日志与恢复测试继续通过。
- [ ] 不修改 `src/hacksome/`、根 `tests/` 或正在并行开发的 Idea workflow 文件。

## 不在范围内

- 多 Team registry、global pool、operator pause/resume。
- Human Review Gate 或 Idea workflow 接线。
- 新增任何 Hackathon Skill。
- 自动完成、自动排名或固定 Build/Pitch 阶段。
