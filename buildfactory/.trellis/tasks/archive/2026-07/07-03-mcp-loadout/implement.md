# Implement — MCP loadout：per-role mcp.json

> 前置：design.md 已审。每个 Step 独立 commit（回滚点）；Step 7 依赖人工凭证，可后置。

## Step 1 配置资产：五份 per-role json + 角色 yaml 指向

- [x] 新建 `agents/mcp/{ceo,researcher,builder,growth,verifier}.json`（内容按 design D4：全员 cua-local；researcher + dataforseo/gsc；ceo/growth + ga4；凭证一律 `${VAR}`）
- [x] 五份 `agents/<role>.yaml` 的 `mcp_config` 改为 `mcp/<role>.json`（相对路径）
- 验证：`python3 -c "import json,glob; [json.load(open(f)) for f in glob.glob('agents/mcp/*.json')]"`

## Step 2 agent_loop：per-role 解析 + strict flag + compose

- [x] `build_claude_argv` 恒加 `--strict-mcp-config`（design D5）
- [x] `_role_model_effort` → `_role_config`：同一次 yaml 解析返回 (model, effort, mcp)；mcp 相对路径按 spec.resolve；失败 WARN + fallback
- [x] `main()` 优先级：`AGENT_MCP` env（显式设置）＞ yaml ＞ `DEFAULT_MCP_CONFIG`（design D2）
- [x] `docker-compose.yml` 的 `x-agent-env` 删除 `AGENT_MCP` 行
- 验证：`python3 -m pytest orchestration/tests/ agent/tests/ -q`（现有测试全绿，含 overlay 回归 = AC3）

## Step 3 单测补齐（design §5）

- [x] argv strict 断言（含 mcp off 时 strict 仍在）
- [x] `_role_config` 优先级 + 相对路径 resolve
- [x] 配置资产测试：五 json 结构断言 + 五 yaml 指向存在文件 + 凭证必须 `${...}` 形态（= AC1）
- 验证：`python3 -m pytest orchestration/tests/ agent/tests/ -q`

## Step 4 镜像：pin 三个 server

- [x] `Dockerfile.agent`：`npm i -g dataforseo-mcp-server@2.9.11`；`pip install analytics-mcp==0.6.0 mcp-gsc==0.1.0`（ARG pin，模式同 gh/vercel）；追加 `@playwright/mcp@0.0.77` + chromium 烘焙（Step 8 赢者落地）
- [x] rebuild：`docker build -f vm/docker/Dockerfile.agent -t foundagent/cua-agent:latest vm/`
- 验证：`docker run --rm --entrypoint sh foundagent/cua-agent:latest -c "which dataforseo-mcp-server google-analytics-mcp mcp-gsc"`

## Step 5 accounts/README.md（AC4）

- [x] 新键 `DATAFORSEO_USERNAME/PASSWORD` + 领取步骤
- [x] Google SA 扩写：GA4 property 授权 + **GSC 属性加 SA 邮箱** + google-sa.json 落位
- [x] 容器内验证命令

## Step 6 无凭证冒烟（优雅缺省）

- [x] `make up` 后确认：researcher 会话可用、cua-local 正常、dataforseo/gsc 显示连接失败但不影响其它（约束「优雅缺省」）
- 验证：`docker compose logs researcher | grep -i mcp`；容器内 `claude mcp list`

## Step 7 真凭证 e2e（AC2）｜外部依赖，可后置

- 人工前置：DataForSEO 账号（$50 押金）→ secrets.env；GCP SA → google-sa.json；GSC 属性加 SA 邮箱
- [x] researcher 容器内 `claude -p` 经 MCP 取回真实 DataForSEO 响应 ×1（2026-07-04：DFS_OK，"coffee" 搜索量 6.12M，余额 $48.43）
- [ ] ⏭ GSC 响应 ×1 —— 移交 domain-rail 任务（需已验证 GSC 属性；foundagent.net 已备，验证+SA 授权在新任务做）

## Step 8 Playwright vs CLI 对比实验（AC5）｜时间盒 ≤半天

- [x] 同组 researcher 任务分别走 Playwright MCP / `@playwright/cli`，记 token + 成功率
- [x] 结论 + 数字 → 父任务 `research/playwright-vs-cli.md`；赢者进 researcher.json 或 CLI 队列

## 收尾

- [x] spec 更新：`resident-agent-contracts.md`（per-role mcp 解析链 + strict）、`loadout-overlay-contracts.md`（baseline 变 per-role 的表述）、`agent-execution-contracts.md`（若涉及）
- [ ] commit + 归档

## Review gates

- Step 3 后：全量单测绿（自检门）
- Step 6 后：向用户报冒烟结果
- Step 7 前：等用户备好凭证（外部门）
