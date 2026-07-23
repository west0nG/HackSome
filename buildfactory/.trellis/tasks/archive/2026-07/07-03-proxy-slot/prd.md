# Proxy 插槽：常驻五角色的 per-account 静态出口 IP

> 父任务：`07-03-capability-provisioning`。从 `07-03-social-rail` 拆出提前做
> （2026-07-03 用户拍板）：proxy 插槽是 X/Reddit CUA 发帖线和 Gumroad/KDP
> 上架线的账号安全前置，其余 social-rail 交付物（IG 续期 job、授权 helper、
> 社交清单）留在原任务按序做。

## 背景

broker 旧路径（`orchestration/broker.py` AC4）已有静态出口接口：
`PROXY_<id>` / `CUA_PROXY` env → 容器注入 `HTTP_PROXY`/`HTTPS_PROXY`/
`NO_PROXY`，未设置默认宿主出口。常驻五角色（compose x-agent）目前没有
这个插槽。账号注入通道已就位：`accounts/<id>/secrets.env` 作为 env_file
注入五角色（53f9929）。

## 需求

1. **单键接口**：`accounts/<id>/secrets.env` 里写一行
   `CUA_PROXY=http://user:pass@host:port` 即启用；键名与 broker 旧路径
   对齐。proxy URL 含凭证，本就该走 secrets.env（凭证单一来源约束自动
   满足）。
2. **展开点在启动 hook，作用域只限 computer-server 子树**：
   `vm/docker/agent_startup.sh` 在 computer-server 的子 shell 里把
   `CUA_PROXY` 展开为大小写两套 `HTTP_PROXY`/`HTTPS_PROXY`/`http_proxy`/
   `https_proxy` + `NO_PROXY`/`no_proxy`（curl 不认大写 `HTTP_PROXY`，
   必须两套都给）。agent_loop → claude 子树**不注入**这组变量。
3. **LLM 流量不走 proxy = 结构性保证（用户硬性条件，2026-07-03）**：
   最初方案是全进程树注入 + NO_PROXY 排除 Anthropic 域，e2e 实测推翻：
   claude CLI 忽略一切按主机名的 NO_PROXY 条目（精确主机/带点后缀/带
   端口全泄，只认 `*` 全局旁路；2026-07-03 squid 对照实验，矩阵见
   design.md）。因此改为作用域隔离：claude 子树根本看不到 proxy 变量。
   账号 API 调用（use-accounts 线的 curl）用显式 `curl -x "$CUA_PROXY"`
   ——原始单键是容器级 env，处处可读。
4. **文档进 accounts/README.md**：键名合约、默认排除项、浏览器继承边界
   （env 继承 = 与 broker 路径同级的 best-effort；Chromium `--proxy-server`
   硬化留给 use-accounts 线）、冒烟命令。

## 约束

- 未设置 `CUA_PROXY` 时逐项零影响：容器 env 里不出现任何 proxy 变量，
  五角色启动与现状完全一致。
- 不动 `docker-compose.yml`（standing-objective 线正在改它，且本设计
  不需要 compose 参与）；不动 broker.py。
- per-account 语义（不是 per-company）：多公司共用一个 ACCOUNT 时共享
  同一出口 IP——"IP 跟着账号走"正是本意，与 broker 语义一致。
- 真实住宅/ISP IP（Decodo/IPRoyal）采购不在本任务内；本地用 squid 容器
  验证"流量确实经过 proxy"。

## 验收标准

> 注意：六个 proxy 变量只存在于 computer-server 进程子树（含 CUA 拉起
> 的浏览器），`docker compose exec` 新开的进程和 agent_loop/claude 子树
> 都看不到。进程树断言用 `/proc/<pid>/environ` 查，流量断言用 exec +
> 手动 source snippet（exec 能看到 env_file 注入的 `CUA_PROXY` 本身）。

- [ ] `secrets.env` 写入 `CUA_PROXY` 指向本地 squid 后：
  ①computer_server 进程 environ 里六个 proxy 变量齐全；
  ②容器内 `bash -c '. <snippet>; curl ifconfig.me'` 的请求出现在 squid
  access log（证明流量走了 proxy）。
- [ ] **LLM 流量不走 proxy（用户硬性条件）**：
  ①agent_loop 进程 environ 里没有 `HTTP_PROXY`/`HTTPS_PROXY`/`NO_PROXY`
  等六变量（结构性隔离的直接证据）；
  ②agent 至少完成一次真实唤醒（claude 调用）期间，squid log 里零新增
  Anthropic/claude.ai 域名记录。
- [ ] 不设 `CUA_PROXY`：容器 env、computer_server 与 agent_loop 进程
  environ 均无任何 proxy 变量，`make up` 后五角色行为与现状一致。
- [ ] 展开逻辑有单测覆盖（未设置 / 设置 / 显式 NO_PROXY 覆盖默认，三条路径）。
- [ ] `accounts/README.md` 增补 proxy 一节：新公司照文档即可启用，无需读代码。
