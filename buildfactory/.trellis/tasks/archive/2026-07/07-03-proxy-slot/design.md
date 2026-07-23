# Design: proxy 插槽展开机制

轻量任务，设计只有一个非平凡决策点，记录如下。

## 展开逻辑放哪

三个候选，取 ③：

1. **compose x-agent-env 加 `${COMPANY_PROXY:-}`**：否决。compose 无法
   条件性省略 key，未设置时会留下空字符串 env 变量，违反"逐项零影响"；
   且 docker-compose.yml 正被 standing-objective 线修改，避让。
2. **agent_startup.sh 内联 if 块**：可行，但 hook 结尾是 `exec`，bash
   逻辑没法被 pytest 直接测。
3. **独立 snippet，由 agent_startup.sh source**：采用。单测用
   `bash -c '. proxy_env.sh; env'` 喂不同输入断言输出，hook 本身只加一行
   guarded source。

### snippet 落点：`agent/proxy_env.sh`（不是 vm/docker/）

`vm/docker/` 没有整目录挂载——compose 只单文件 bind 了
`agent_startup.sh` 本身，放那里容器看不见。`agent/` 已整目录 ro 挂载到
五角色的 `/opt/foundagent-orch/agent`（resident_loadout.py 同由本 hook
调用，先例一致），单测也天然落在 `agent/tests/`。hook 里 source 加
`[ -f ]` guard：镜像/挂载不齐时缺文件不得 brick 启动。

## proxy_env.sh 行为合约

```sh
# 输入：环境变量 CUA_PROXY（可空）、NO_PROXY（可空，用户显式覆盖）
# 输出：CUA_PROXY 非空时 export 六个变量；为空时什么都不做
if [ -n "${CUA_PROXY:-}" ]; then
  export HTTP_PROXY="$CUA_PROXY" HTTPS_PROXY="$CUA_PROXY"
  export http_proxy="$CUA_PROXY" https_proxy="$CUA_PROXY"
  export NO_PROXY="${NO_PROXY:-localhost,127.0.0.1,.anthropic.com,anthropic.com,.claude.ai,claude.ai}"
  export no_proxy="$NO_PROXY"
fi
```

## 作用域：只注入 computer-server 子树（e2e 实测后的设计修订）

第一版把六变量注入整个 hook 进程树、靠 NO_PROXY 排除 Anthropic 域。
e2e 真实唤醒抓包推翻：squid log 出现 4 条 `CONNECT api.anthropic.com:443`
——claude 的 LLM 流量泄进了 proxy。冻结后台唤醒后用一次性容器做的
NO_PROXY 对照矩阵（2026-07-03，每轮一次真实 `claude -p` 调用）：

| NO_PROXY 写法 | proxy 泄漏 |
|---|---|
| `*` | 0（生效） |
| `api.anthropic.com`（精确主机） | 泄 |
| `anthropic.com` / `.anthropic.com`（后缀） | 泄 |
| `api.anthropic.com:443`（带端口） | 泄 |

结论：**claude CLI 只认 `*`，忽略一切按主机名的 NO_PROXY 条目**（curl
在同容器同写法下正常旁路，是 claude 自身的代理解析行为）。`*` 等于全局
不走 proxy，无法只排除 Anthropic → 排除表路线废弃。

修订：hook 只在 computer-server 的子 shell 里 source snippet——CUA
桌面/浏览器（账号敏感面）走 proxy；agent_loop → claude → Bash 子进程
根本看不到 HTTP(S)_PROXY，LLM 不走 proxy 从"依赖工具的 NO_PROXY 语义"
变成结构性保证。副作用是 claude 会话里的 Bash 命令不再自动继承 proxy
——这是特性不是损失：账号 API 调用应当**显式**走
`curl -x "$CUA_PROXY"`（单键是容器级 env，处处可读），gh/vercel/
wrangler 等开发面流量保持直连，不烧住宅流量。use-accounts 线落地时把
`-x` 模式写进 skill 模板。

- source 位置：computer-server 的子 shell 内（见上节），CUA 拉起的
  浏览器随之继承；agent_loop / claude 子树保持干净。
- 这组 env 只存在于 computer-server 进程子树，`docker compose exec`
  新开进程看不到（验收要用 `/proc/<pid>/environ`）；kasm 桌面里不经
  custom_startup 的进程同理拿不到——可接受，账号流量都从
  computer-server 派生；浏览器级硬化（`--proxy-server`）留给
  use-accounts 线。
- `PROXY_<id>` 是 broker 旧路径的 per-op 拼写，常驻路径一个 stack 一个
  account，不需要；README 里注明这一对应关系。

## 测试

- 单测：`agent/tests/test_proxy_env.py`（pytest，subprocess 跑 bash），
  三条路径：未设置→无输出；设置→六变量+默认 NO_PROXY；设置且显式
  NO_PROXY→覆盖默认。
- e2e：本地 squid 容器 + `CUA_PROXY=http://host.docker.internal:3128`，
  独立 project（`COMPANY=e2eproxy -p e2eproxy`）只起 ceo 一个角色，
  不碰正在跑的公司栈；按 PRD 验收标准逐条验（含真实唤醒期间 squid log
  零 Anthropic 记录）。注意 agent_startup.sh 是单文件 bind，编辑器
  rename-write 换 inode 后运行中容器看到的是旧内容——e2e 必须
  force-recreate。
