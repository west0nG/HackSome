# PRD: Agent model/effort config in role yaml

## 背景

当前所有 claude 调用（一次性 worker、常驻 agent_loop、objective 独立 reviewer）都不带
`--model` / `--effort`，实际跑的是订阅账号默认模型 + CLI 默认 effort，且不可配。
用户拍板：模型/effort 在 `agents/<role>.yaml` 里配，不配则默认
**claude-opus-4-8 + effort xhigh**。

## 需求

1. `AgentSpec` 新增可选字段 `model` / `effort`，默认 `claude-opus-4-8` / `xhigh`；
   `agents/<role>.yaml` 可覆盖，无需改代码（延续 AC1 声明式约定）。
2. 一次性路径：`ClaudeCodeProvider.build_exec` argv 追加 `--model` / `--effort`。
3. 常驻路径：`agent_loop` 从 `agents/<AGENT_KEY>.yaml` 读取 model/effort
   （容器内 AGENTS_DIR 已挂载）；yaml 缺失或读取失败 → WARN + 默认值，
   延续 never-brick 约定，绝不因此停循环。
4. objective reviewer 的独立 `claude -p` turn 同样使用默认 model/effort
   （它无角色 yaml，统一常量即可）。

## 验收标准

- AC1: yaml 不写 model/effort 时，三条路径 argv 均含
  `--model claude-opus-4-8 --effort xhigh`。
- AC2: yaml 写了 `model:` / `effort:` 时，spec 路径 argv 用 yaml 值。
- AC3: 常驻路径 yaml 缺失/损坏时 WARN 并回落默认，loop 不中断。
- AC4: 既有测试全绿；新增覆盖上述三条的单测。

## 非目标

- 不做 effort 取值校验（CLI 自身会报错，错误进 transcript）。
- 不改 codex/opencode stub。
