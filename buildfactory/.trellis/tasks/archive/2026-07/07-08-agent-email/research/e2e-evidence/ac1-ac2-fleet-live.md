# AC1/AC2 fleet 真跑记录（2026-07-08）

> M6 第二阶段（承接 plumbing-live.md）。生产公司 foundagent、`make up` 全员 10 容器、真 LLM。

## 时间线

1. `make up`（撞上 firsttest 遗留容器名冲突，`docker rm` 停用容器后成功——"kill 残留"问题的又一实证）。
2. mail-poller 首个周期即把用户之前的两封 `plumbing-test` 测试信归档 `unmatched/`（生产注册表当时无认领）——**AC4 生产实证**：零投递、不打扰任何 agent。
3. CEO 身份下发认领 goal（`6cb0da56…`，带 verifier 专属验收）→ **45 秒后 growth 自主认领 `ivy@foundagent.net`**，label "Growth/Marketing department persona"——命名三原则奏效（persona 名、非服务名），并自发把事实持久化到 `/company/operations/mailboxes.md`。
4. 下发 Medium goal（`71fcbc5b…`）→ 立刻注入两封干扰信（newsletter + 伪装验证信 `noreply@quora.com · Confirm your Quora account`）+ 一条 FYI 噪音消息。
5. growth 同一 wake 内：medium.com 提交 `ivy@` → **peek 从队列中段捞出 `noreply@medium.com · Your login code is 632448`**（收件箱物理顺序：干扰信第 6、7 位，Medium 信第 8 位）→ 完成登录 → 注册 **@ivy_45376（"Ivy Solvo"）** → 证据入 `/company/social/`（medium_account.md + 2 张截图）→ goal 报完 → 最终 ledger `status: done`（过完 doer≠judge 验收）。
6. 后续 wake：growth 把干扰信识别为"signup artifacts/newsletters……no action, no links clicked"——**Quora 陷阱未咬钩**；FYI 噪音正常处理；cursor 线性推进（→11），无消息丢失。
7. AC2：owner（growth 身份）`add-receiver ivy builder` → `resolve('ivy')==['growth','builder']` → 注入 `AC2 fan-out check` → **双收件箱各一条 IME**，id 分别 `<mid>:growth` / `<mid>:builder`，间隔 7ms，R2 归档 processed。

## 验收矩阵

| AC | 结果 | 证据 |
|---|---|---|
| AC1 真实服务+任务中途+非首条 | ✅ | medium_account.md、2 截图、inbox 顺序 6/7 干扰 → 8 Medium、ledger done |
| AC2 fan-out | ✅ | 双 inbox IME、独立去重 id |
| AC3 认领规则 | ✅ | 34 单测 + 真跑认领 UX（终身制文案落 CLI 输出） |
| AC4 未认领归档 | ✅ | 单测 + 生产 `unmatched=2` 实证 |
| AC5 即插即拔 | ✅ | 全离线测试、无反向依赖、fleet 直接跑通 |
| AC6 skill | ✅ | 两 skill + 真跑中被 growth 实际遵循（先 mine/list、peek 循环、不点陷阱链接） |

## 计划外收获

- **Gumroad 也解锁了**：CEO 自主派的卖货 goal 里，growth 用 `ivy@` 完成 Gumroad 注册（收件箱第 12 行确认信）——firsttest 邮箱墙上的第二个平台，零额外开发。
- growth 自发提交 standing objective 并获 verifier `PASS`（07-03 机制在生产自然运转）。
- D6 接受的"重派已处理邮件"代价被实际观察到且无害（growth 一句确认收尾）。

## 遗留

- firsttest 停用容器残留仍会阻塞 `make up`（本次手工 `docker rm` 解决）——"kill 残留"待单独拍板。
- Medium 实际给的是 login code + magic link 双形态，check-email skill 的描述覆盖两者，无需改动。
