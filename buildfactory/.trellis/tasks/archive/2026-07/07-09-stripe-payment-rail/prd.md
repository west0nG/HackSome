# Stripe payment rail: secret key injection + fleet-wide MCP

## Goal

给 fleet 铺 Stripe 收款轨：用户已人工完成 Stripe 开户 + KYC（live 账户可收款），
agent 通过官方 `@stripe/mcp` 获得收款能力（创建产品/价格/payment link/invoice、
查余额流水等）。本轮只铺通用轨道，不绑定具体变现场景。

## Requirements

1. **凭证插槽**：`accounts/<id>/secrets.env` 新增 `STRIPE_SECRET_KEY` 键；
   `accounts/README.md` 键名清单加 Stripe 一节（拿 key 步骤 + 验证命令 +
   风险说明）。真实 key 由用户人工填入 `accounts/foundagent/secrets.env`，
   不进 git。
2. **MCP loadout**：五个 `agents/mcp/<role>.json` 各加 `stripe` server
   （全员全量集，沿用 07-06 立场）。key 缺失时该 server 连接失败但不影响
   其他 server、不阻断 agent 启动（与 dataforseo 同语义）。
3. **镜像 pin**：`@stripe/mcp` 按既有惯例 pin 进 `Dockerfile.agent`
   （ARG 版本 + 全局安装），运行时零冷下载。

## Constraints

- **完整 secret key（sk_live），非 restricted key**——用户 07-09 拍板，延续
  "先给足权限、收窄后置"立场。已知后果：`@stripe/mcp` 本地进程实为
  mcp.stripe.com 的转发器，工具面 = 密钥权限面，无应用层白名单；full key
  意味着 agent 可退款/改订阅/动 dispute。风险已明示并被接受。
- **skill 本轮不写**：场景未定时写必然泛泛（违反三道检验）。等第一个真实
  变现场景再写。charter 层面的定向语（"公司有 live Stripe 账户"）也留到
  skill 那轮一起做，本轮零 charter 改动。
- **webhook 不铺**：收款感知靠 MCP 余额/流水查询覆盖；实时通知后置。
- 密钥经 env 注入，不落 repo；改 `secrets.env` 后需 force-recreate 容器
  生效（README 既有规则，Stripe 一节需重申）。

## Acceptance Criteria

- [x] AC1（结构）：五个 role json 均含 stripe server 配置；`@stripe/mcp`
      已 pin 进 Dockerfile.agent 并成功 build；secrets.env 未配 key 时
      `make up` 五容器正常启动，stripe server 显示未连接而非报错崩溃。
      ✅ 镜像完整 build 通过；无 key/空 key 降级在镜像内实测（进程干净
      exit 1，不阻断启动）；571 项测试全绿。
- [x] AC2（真 e2e）：用户填入真实 sk_live key 并重建容器后，任一 agent
      容器内 `/mcp` 显示 stripe 已连接 → agent 用 MCP 工具创建一个 live
      payment link → Stripe Dashboard 可见该 link → agent 将其 deactivate。
      全程不产生真实扣款。
      ✅ 07-09 通过：一次性 builder 容器（真实 role loadout + strict
      mcp-config）纯 MCP 完成产品→价格→payment link→灭活→归档全流程，
      `plink_1TrJIYIRw93begpcvrV5axyI`（livemode），宿主机 API 独立复核
      link/product 均 `active: false`，零扣款、零 fallback。
- [x] AC3（文档）：`accounts/README.md` 含 Stripe 一节：key 获取步骤、
      `STRIPE_SECRET_KEY` 键名、force-recreate 提醒、full-key 风险一句话、
      验证命令。

## Notes

- 决策记录：memory `stripe-payment-rail`（07-09 拍板：full key / 通用铺轨 /
  skill+webhook 后置）。
- AC2 依赖用户人工填 key，属一次性人工前置（与 dataforseo/GA4 同模式）；
  实施时结构部分先行，e2e 在 key 就位后收尾。
