# thirdtest: full-claude-opus company longrun

## 背景与授权

用户 2026-07-10 直接指示：secondtest（全 codex）收官后起第三家全新公司 `thirdtest`，这回全员用 Claude 的 Opus 模型 + xhigh effort；observation 沿用 Sonnet 5。公司拥有全部 secret 与账号权限（`ACCOUNT=foundagent` 全量账号包，沿用 secondtest 先例）。

## 需求

- R1：五个常驻角色（ceo/researcher/builder/growth/verifier）全部切回 `provider: claude-code`；model/effort 不在 yaml 里写——claude-code 适配器 fleet 默认即 `claude-opus-4-8` + `xhigh`；其余配置零改动（charter/skills/mcp/hooks 声明不分叉）。
- R2：`make up COMPANY=thirdtest ACCOUNT=foundagent` 全栈拉起（state/thirdtest 全新落盘，无任何旧公司状态）；不发人工 kickoff——CEO 首个 proactive idle wake 自主开工（含 07-10 when-idle 重写后首次长跑生产观察：空账本 pass 必须派单）。
- R3：observatory daemon（host 侧，observer model `claude-sonnet-5` 默认值）随跑：goal 尸检 + 周期公司 review。
- R4：值守边界沿用 secondtest：**机制级卡死**（编排/runtime/基建 bug）自主修复并留提交与记录（现象→根因→修复→验证四段）；**经营层行为**（goal 选择、方向、对外动作）不干预——那是实验本体，交给 observatory 记录。
- R5：干预与异常全部留痕（本任务目录 + journal），给用户完整验收报告。

## 约束

- 修复遵循既有立场：never-brick、doer≠judge、中性契约扩展规则；生产中热修优先最小 diff。
- 不因为"省钱"叫停公司：成本记录交给 telemetry/observatory，用户已知情（Opus+xhigh 成本显著高于 codex 订阅，属实验设计的一部分）。
- 起跑前须真跑验证 Claude 订阅 auth（vm/.env.local 的 CLAUDE_CODE_OAUTH_TOKEN）在容器内可用，避免起跑后才发现 auth 失效。
- 已知坑（secondtest 起跑经验）：`make up` 的 `--build` 可能因 docker mirror 拉不动基础镜像而挂 → 镜像本地都有，直接 `docker compose up -d --no-build`。

## 验收标准

- [ ] AC1：公司持续运行至用户验收（中途允许有已修复的中断，不允许无人处置的瘫痪）。
- [ ] AC2：期间产生的 goal 有完整闭环样本（dispatch→执行→report→verify→终态）且 telemetry 全程有 usage 数据（claude-code 侧原生 token usage）。
- [ ] AC3：observatory 产出至少一份 goal 尸检或公司 review 报告。
- [ ] AC4：所有机制级干预（如有）有：现象 → 根因 → 修复 diff/动作 → 验证 的四段记录。

## 观察点

- when-idle 重写（07-10）后 CEO 空账本心跳的真实派单表现（secondtest 尾声曾出现 7h 吸附态睡眠，重写后 e2e 已验但这是首次长跑生产观察）。
