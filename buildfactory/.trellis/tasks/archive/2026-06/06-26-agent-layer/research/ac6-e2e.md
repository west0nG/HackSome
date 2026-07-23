# Agent Layer — AC6 端到端取证（实测）

> implement.md 阶段 5。证明 agent-layer「五件套」经 broker 单一路径端到端打通：
> computer-use + 浏览器 + 账号注入 + skill/hook/charter 装载 + provider/凭证 seam。
> 运行：`broker.spawn(op_id="demo", task=…, spec=AgentSpec.load("agents/operator.yaml"), task_timeout=600)`
> 凭证：订阅（`CLAUDE_CODE_OAUTH_TOKEN` ← `vm/.env.local`），零 API key。测试站：`the-internet.herokuapp.com/login`（公开测试登录页，option B）。

## AgentResult（结构化执行接口 AG5/AC5）

```
ok       = True
cost_usd = 0.9789846   (订阅，单次端到端)
error    = None
num_turns= 63          (result event, stream-json 解析正确)
session  = 14487892-5eea-49ee-a098-d820b0a44ee8
```

final text 含：skill motto 逐字 + 注入邮箱 + token 掩码 + 两张截图确认 + 登录成功 + `[charter-ack]`。

## 五件套证据

| # | 维度 | 证据 |
|---|---|---|
| 1 | **computer-use** | transcript 实际调用 cua-local MCP：`screenshot×23 / left_click×24 / double_click×8 / type_text×12 / press_key×11 / get_screen_size×2`（非脑补） |
| 2 | **浏览器 + 登录** | `vm/data/op-demo/claude/ac6-login-success.png`（55,827 B）= Firefox 在 `/secure`，绿幅「You logged into a secure area!」+「Secure Area」标题。`tomsmith` / `SuperSecretPassword!` 登录成功 |
| 3 | **账号注入** | broker `--env-file accounts/demo/secrets.env` → 容器 env。agent 经 Bash 读 `DEMO_ACCOUNT_EMAIL=founder@foundagent.net` 并 `type_text` 进登录页 Username 框 → `ac6-injected-email.png`（83,395 B）可见该邮箱。注入值真正流到浏览器动作 |
| 4a | **skill 装载** | `loadout.materialize` → `skills/hello-foundagent/SKILL.md`；transcript 有 `"name":"Skill"` `"skill":"hello-foundagent"`（×1）；motto 逐字回传「Foundagent operator online. Motto: zero humans, full autonomy.」 |
| 4b | **hook 装载** | `settings.json` 合并 PreToolUse；`hook.log` 59 行 `[hook] PreToolUse fired <ts>` → 每次工具调用前触发 |
| 4c | **charter / system-prompt 装载** | charter 经 `--append-system-prompt` 注入；final text 末行输出 `[charter-ack]`（charter 规则生效） |
| 5 | **provider / 凭证 seam** | `ClaudeCodeProvider` + `SubscriptionCreds`（订阅互斥注入，`ANTHROPIC_API_KEY` 清空）跑通；`ok=True` 即订阅路径成功，零 API key |

## VM 层不退化（AC5）

- transcript JSONL 持久化：`vm/data/op-demo/claude/projects/-home-kasm-user/14487892-….jsonl`（9.5 MB），append-only、挂宿主卷，容器删除后仍在。

## 安全红线自查（token 明文零泄漏）

- `DEMO_SERVICE_TOKEN`（敏感，len=14）**仅以掩码** `sk…23 len=14` 出现在 final text。
- 全量扫描 `grep -rF "<token>" vm/data/op-demo/`：**0 匹配，0 文件**（含 transcript JSONL、hook.log、settings、截图目录）。
- transcript 内单独复查：`grep -cF "<token>" *.jsonl = 0`。
- agent 计算掩码用 `${T:0:2}/${T: -2}/${#T}`（shell 参数展开），命令串只含变量名 `$DEMO_SERVICE_TOKEN`、不含明文；输出仅掩码。
- `DEMO_ACCOUNT_EMAIL`（低敏，允许）正常出现在 transcript。

## 容器起停

- `op-demo`：broker.spawn 起（computer-server :8000 ~16s 就绪），spawn 不 teardown。
- 取证完成后手动 `docker rm -f op-demo`；宿主卷 `vm/data/op-demo/`（gitignored）保留全部证据。
- 未改 `agent/` 包、未改 `orchestration/broker.py` 契约、未 commit。

## 结论

AC6 通过。五件套 + AG5 结构化结果 + AG7 broker 单一路径全部端到端验证；computer-use 一次跑通登录（无重试翻车）；账号注入凭证明文零泄漏。
