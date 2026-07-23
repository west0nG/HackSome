# PRD: 公司级 Loadout Overlay——每公司一份能力开关配置

## 背景

当前主工作流是对 skill / prompt / 外设等能力做组合测试（全开、部分开、裸 agent 对比）。但目前唯一的开关是 `agents/<role>.yaml` 的 `skills:` 列表，外设 adapter（`peripheral/manifest.py::ADAPTERS`）和 MCP（`DEFAULT_MCP_CONFIG`）是代码常量。测一个组合就要改基线文件、测完改回来，且无法按公司区分配置。

目标：每公司一份 **overlay 配置文件**（只写与基线的差异），起 Company 时声明哪些能力开/关；没有该文件时行为与今天完全一致。role YAML 保持"全量能力基线"角色不变。

## 需求

1. Overlay 文件为 YAML，按公司落在 `state/<company>/config/loadout.yaml`；文件缺失或为空 = 行为零变化。
2. v1 可开关的能力面：
   - **每角色 skills**：关掉基线中的某个 skill；或把全局技能池（`agents/assets/skills/`）中基线外的 skill 挂给该角色。
   - **每角色 charter**（system prompt）：`on` / `off` / 替换为另一个 charter 文件（测 prompt 变体）。
   - **每角色 hooks**：`on` / `off`。
   - **每角色 MCP**：`on` / `off` / 替换为另一份 mcp 配置。
   - **外设层 adapters**：白名单（缺省 = 全开）。
3. `defaults:` 块作用于所有角色（如一行关掉全公司 hooks），角色级配置覆盖 defaults。
4. 生效时机统一：各进程**启动时**读取 overlay；修改 overlay → 重启对应容器生效。v1 不做热加载。
5. 开关可往复：claude home 持久化（state-dir 任务）后，skill 从 on 改 off 再重启，上次物化的 skill 目录 / hooks 条目必须被清除（reconcile），不能残留导致"以为关了其实还在"。
6. 容错分两层：
   - 运行时（容器内）：坏 YAML / 未知条目 → 大声 log WARN + 该条目按基线处理，agent 照常启动（沿用"loadout 永不 brick agent"）。
   - 离线校验：`make loadout-check COMPANY=<x>` 在宿主机 fail-fast，typo、指向不存在的路径、未知角色/skill/adapter 逐条报错、非零退出。跑实验前先过一遍。
7. role YAML 基线语义、SOP 声明式扩展哲学、既有测试全部不变。

## 约束

- **依赖 `07-03-state-dir-consolidation`**：本任务的挂载接线（M4 起）踩其落地后的最终 compose 布局实施；纯代码部分可先行。
- overlay 用**目录挂载**（`state/<company>/config/` 只读挂入容器），不用单文件 bind mount——编辑器 rename 写入会更换 inode，容器将永远读到旧内容，这种静默偏差正是本功能要消灭的。⚠️ 因此实际路径比口头拍板的 `state/<company>/loadout.yaml` 多一层 `config/`，需用户确认。
- reconcile 只允许动 loadout 自己物化过的东西（以清单记账）：不得误删 agent 自装的 skill 或自加的 settings 键。
- 不做（v1 边界）：skill 热加载、per-hook 粒度开关、多 compose 栈管理工具。

## 验收标准

- [ ] **回归零变化**：无 loadout.yaml 时，五角色的物化结果（skills 目录、settings.json）、claude argv（charter/mcp flag）、外设 sources 与现状逐项一致。
- [ ] **组合生效**：一份含「growth 关掉部分 skills + verifier `charter: off` + `defaults: hooks: off` + adapters 白名单只留 webhook」的 overlay，起栈后逐项可验证（容器内 skills 目录、settings.json、agent_loop 日志中的 argv、peripheral 启动日志 sources）。
- [ ] **reconcile**：skill on→off→重启后，claude home 中该 skill 目录被移除；hooks off 后 snippet 来源的条目被移除，agent 自加的 settings 键原样保留；不在记账清单里的手装 skill 永不被动。
- [ ] **超基线挂载**：通过 overlay 给角色挂基线外 skill（如给 verifier 挂 send-goal）成功物化。
- [ ] **MCP**：`mcp: off` 时该角色 claude argv 无 `--mcp-config`；替换路径时 flag 指向新路径。
- [ ] **容错**：坏 overlay（未知 skill / 未知角色 / 坏 YAML）下容器照常启动且日志有 WARN；`make loadout-check` 对同一文件非零退出并逐条指出问题。
- [ ] **公司隔离**：两个公司（如 foundagent 与 e2e-dood）各自的 overlay 互不影响。
- [ ] 宿主机 `pytest` 全绿；overlay 解析 / 合成 / reconcile / 容错均有单测。
