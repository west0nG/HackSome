# Agent Layer — Implementation Plan

> 配套 `prd.md` + `design.md`。有序执行；每阶段末尾的「验证」对应 prd 的 AC。每阶段独立 commit。

## 前置 spike（消除 design R1-R3 不确定性，先验证再写代码）

- [ ] **S1** 起一个 `cua-agent` 容器，`docker exec` 跑 `claude -p "say hi" --output-format stream-json --verbose`，记录 `result` event 字段结构（→ runner 解析）。
- [ ] **S2** 在容器 `.claude/skills/` 放一个 trivial skill，确认订阅版 claude 能发现/调用（→ 确认 loadout 落点）。
- [ ] **S3** 容器内用 `ANTHROPIC_API_KEY` 跑一次最小 `claude -p`，确认 API key 路径可用（→ AC3 切换）。
- 验证：三点结论写入 `research/agent-spike.md`；若与 design 假设不符，回填 design.md 再继续。

## 阶段 0 — 脚手架

- [ ] 建 `agent/` 包（空模块 + `__init__.py` + `tests/`）。
- [ ] 建 `agents/` 声明目录 + `agents/assets/`（占位）。

## 阶段 1 — 声明 + Provider/凭证 seam（AG1/AG2/AG3）

- [ ] `agent/spec.py`：`AgentSpec` dataclass + `AgentSpec.load()` (YAML) + `provider_for` / `credential_for` 工厂。
- [ ] `agents/operator.yaml`：示例通用 operator spec。
- [ ] `agent/credentials.py`：`CredentialSource` + `SubscriptionCreds` + `ApiKeyCreds`。
- [ ] `agent/provider.py`：`Provider` 抽象 + `ClaudeCodeProvider` + `CodexProvider`/`OpenCodeProvider`（stub 抛 `NotImplementedError`）。
- 验证（AC1/AC2/AC3 部分）：单测 — spec 加载、provider 选择、凭证 `env()` 正确、stub 抛错；新增第二个 yaml 不改 .py。

## 阶段 2 — 三类装载（AG4/D6）

- [ ] `agent/loadout.py`：`materialize(spec, claude_home)` — system-prompt / skills / hooks 三类物化。
- [ ] 示例资源：`assets/company-charter.md`、`assets/skills/hello-foundagent/SKILL.md`、`assets/hooks/settings.snippet.json`（均 trivial、无判断逻辑）。
- 验证（AC4 静态）：materialize 后 `.claude/skills/<name>/`、`.claude/settings.json`（合并未覆盖）、CLAUDE.md/append-arg 落点正确。

## 阶段 3 — 执行接口 runner（AG5）

- [ ] `agent/runner.py`：`run_task()` — 组装 provider ExecPlan → `docker exec` → 解析 stream-json `result` event → `AgentResult`。
- 验证（AC5）：对一个就绪容器跑一个任务，断言 `AgentResult.ok/text` 字段。

## 阶段 4 — broker 重构为单一路径（AG7/D7）

- [ ] `broker.spawn()` 增 `spec` 参数（默认 `agents/operator.yaml`）；docker run 前 `loadout.materialize`；就绪后 `runner.run_task`；删除 broker.py:91-105 硬编码 `claude -p`。
- 验证（AC7 回归）：跑原 `__main__` demo（firefox / describe desktop），行为不退化。

## 阶段 5 — 端到端打通（AG6）

- [ ] 配一个低风险账号到 `accounts/demo/secrets.env`（自建邮箱 / 测试登录页凭证）。
- [ ] 跑端到端：agent 加载示例 skill/hook → 浏览器打开网站 → 低风险账号登录 → 截图。
- 验证（AC4 动态 + AC6）：截图 + transcript 证明五者打通；hook 触发日志、skill 被调用、人设体现可见。

## 验证命令

- 单测：`.venv-cua/bin/python -m pytest agent/tests/ -q`
- 端到端 / 回归：`set -a && source vm/.env.local && set +a && .venv-cua/bin/python -m orchestration.broker`
- spike：`.venv-cua/bin/python vm/spike_cua.py`（容器起得来）+ 手动 `docker exec` 验证 S1-S3。

## 风险点 / 回滚

- **broker 重构**（动已验证 VM 层代码）：单列一次 commit；回归 demo 必跑；失败即回退该 commit。
- **stream-json 解析**：依赖 S1 结论；解析失败回退 `--output-format json`（单 JSON）兜底。
- **hook 合并**：必须合并 `.claude/settings.json` 既有键，禁止整文件覆盖。
- **回滚点**：阶段 1-3 为纯新增（不影响现状）；阶段 4 为唯一改动现状点，独立可回退。
</content>
