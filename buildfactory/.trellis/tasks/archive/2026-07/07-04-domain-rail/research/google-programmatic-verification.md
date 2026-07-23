# Research: GSC/GA4 程序化验证 + Cloudflare token 权限实测

- **Query**: ① SA 能否全程序化完成 foundagent.net 的 GSC Domain property DNS TXT 验证；② GA4 Analytics Admin API 能否用 SA 从零建 property/data stream；③ 账号包 CF token 对 zone foundagent.net 的 DNS 读写实测
- **Scope**: mixed（外部一手文档 + 本机 API 实测）
- **Date**: 2026-07-04
- **核实方式**: 全部结论来自 2026-07-04 当天抓取的 developers.google.com 官方参考页原文 + Cloudflare API 真实调用，非训练记忆

---

## 问题 1：GSC Domain property 全程序化验证（核心）

### 结论：可行，全程序化，零人工 UI

Service account 就是一个「authenticated user」，Site Verification API 的所有调用都在认证账号的上下文中执行（官方 Getting Started 原文："All API calls need to be authorized by an authenticated user, and all API calls are executed in the context of the authenticated user's account"）。SA 用自己的凭证走 `getToken → CF 放 TXT → insert` 后，SA 自己成为 `foundagent.net`（INET_DOMAIN）的 verified owner；随后用同一 SA 调 Search Console API `sites.add`（`sc-domain:foundagent.net`）即可读写该 Domain property。**全链路无需任何人工 UI 操作。**

旁证：Terraform provider `hectorj/googlesiteverification` 正是用 SA JSON key 走这条链（`googlesiteverification_dns_token` data source → DNS 记录 → `googlesiteverification_dns` resource），是社区长期在生产使用的同一 API 组合。

### API 组合与调用顺序（已从官方参考页逐条核实）

| 步骤 | 调用 | 关键参数 |
|---|---|---|
| 0 | GCP 启用 API | `siteverification.googleapis.com` + `searchconsole.googleapis.com` |
| 1 | `POST https://www.googleapis.com/siteVerification/v1/token` | body: `{"site":{"type":"INET_DOMAIN","identifier":"foundagent.net"},"verificationMethod":"DNS_TXT"}` → 返回 `{method, token}` |
| 2 | Cloudflare API 放 TXT | zone `fde57901aa4b6a85c63e9395ab23d615`，name=`foundagent.net`（apex，不是子域），type=TXT，content=上一步 token 原样（官方措辞 "using the token for the record data"，token 形如 `google-site-verification=xxxx`） |
| 3 | 等待可解析后 `POST https://www.googleapis.com/siteVerification/v1/webResource?verificationMethod=DNS_TXT` | body: `{"site":{"type":"INET_DOMAIN","identifier":"foundagent.net"}}` → 成功即 SA 成为 verified owner，返回的 webResource id 形如 `dns://foundagent.net/` |
| 4 | `PUT https://www.googleapis.com/webmasters/v3/sites/sc-domain%3Afoundagent.net` | 空 body。官方 sites.add 参考页明示 siteUrl 两种形态：`http://www.example.com/`（URL-prefix）或 **`sc-domain:example.com`（Domain property）**；URL 中要转义为 `sc-domain%3A` |
| 5 | 验证读取：`GET https://www.googleapis.com/webmasters/v3/sites` 或 Search Analytics query，`siteUrl=sc-domain:foundagent.net` | |

### Scope（官方参考页原文）

- Site Verification（步骤 1、3）：`https://www.googleapis.com/auth/siteverification`
  - 另有 `siteverification.verify_only`（只能验证、不能读已验证列表）——**别用这个**，用全量 scope。
- Search Console（步骤 4、5）：`https://www.googleapis.com/auth/webmasters`（读写）；只读可用 `webmasters.readonly`。

### 需启用的 GCP API（在 SA 所属项目里）

- `siteverification.googleapis.com`（Site Verification API）
- `searchconsole.googleapis.com`（Search Console API，旧名 Webmasters）
- （问题 2 需要的：`analyticsadmin.googleapis.com`、`analyticsdata.googleapis.com`）

### 已知坑

1. **TXT 传播等待**：`insert` 在 Google 查不到 TXT 时返回 400（"verification token could not be found" 类错误）。Cloudflare 是权威 NS、生效秒级，但仍需重试循环（Terraform provider 专门为此给 create 设了 timeout）。建议：先本地 `dig TXT foundagent.net +short` 确认可见，再带退避重试 insert（如 10s×6 次）。
2. **token 原样放入**：DNS_TXT 的 token 是完整 TXT 值（含 `google-site-verification=` 前缀），不要二次拼接；记录名是 apex 域本身，不是 `_google.foundagent.net` 之类。
3. **TXT 记录要永久保留**：Google 会周期性复查验证，删掉 TXT 会导致 ownership 失效。不要复用 `_domain-rail-test` 那种临时记录思路。
4. **SA 做 owner 的限制**：
   - ownership 变更会给所有 owner 发邮件通知；SA 邮箱收不到，无害但日志里会体现。
   - 属性 owner 是 SA 而非人类账号——用户在自己的 Search Console UI 里**看不到**该属性，除非把人类邮箱也加进 owners（可用 API `webResource.update` 往 owners 列表加人，或在 GSC UI 里由 SA 侧委派；官方 Getting Started 明示 "the authenticated user can delegate ownership to other users after their ownership has been verified"）。
   - IDN 需 punycode（RFC 1034 §3.5），foundagent.net 不涉及。
5. **Domain property 覆盖全部子域**：官方原文 "The owner of a domain is considered to be the owner of all sites and subdomains under that domain"。验证一次 `foundagent.net`，fleet 所有 `*.foundagent.net` 站点的 GSC 数据都在同一属性下——正合本任务需求，也是官方推荐（"verify with domains whenever feasible"）。
6. `sc-domain:` 前缀**只用于 Search Console API**（sites.add/list/query 的 siteUrl）；Site Verification API 侧用的是 `INET_DOMAIN` + 裸域名，两套标识不要混。

### 可直接照做的命令级草稿（python，google-auth）

```python
#!/usr/bin/env python3
"""Verify foundagent.net as GSC domain property using service account. Idempotent."""
import os, time, json, subprocess, urllib.parse
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request

DOMAIN = "foundagent.net"
ZONE = "fde57901aa4b6a85c63e9395ab23d615"
SA_KEY = "/account/google-sa.json"          # 账号包契约路径
CF_TOKEN = os.environ["CLOUDFLARE_API_TOKEN"]  # source secrets.env

SCOPES = [
    "https://www.googleapis.com/auth/siteverification",
    "https://www.googleapis.com/auth/webmasters",
]
creds = service_account.Credentials.from_service_account_file(SA_KEY, scopes=SCOPES)
creds.refresh(Request())
g = {"Authorization": f"Bearer {creds.token}"}
cf = {"Authorization": f"Bearer {CF_TOKEN}", "Content-Type": "application/json"}

# 1. getToken
r = requests.post("https://www.googleapis.com/siteVerification/v1/token", headers=g, json={
    "site": {"type": "INET_DOMAIN", "identifier": DOMAIN},
    "verificationMethod": "DNS_TXT",
})
r.raise_for_status()
token = r.json()["token"]  # e.g. "google-site-verification=xxxx"

# 2. put TXT at apex via Cloudflare (skip if identical record exists)
existing = requests.get(
    f"https://api.cloudflare.com/client/v4/zones/{ZONE}/dns_records",
    headers=cf, params={"type": "TXT", "name": DOMAIN}).json()["result"]
if not any(rec["content"].strip('"') == token for rec in existing):
    requests.post(f"https://api.cloudflare.com/client/v4/zones/{ZONE}/dns_records",
                  headers=cf, json={"type": "TXT", "name": DOMAIN, "content": token, "ttl": 300}
                  ).raise_for_status()

# 3. insert with backoff (DNS propagation)
for attempt in range(8):
    r = requests.post(
        "https://www.googleapis.com/siteVerification/v1/webResource",
        headers=g, params={"verificationMethod": "DNS_TXT"},
        json={"site": {"type": "INET_DOMAIN", "identifier": DOMAIN}})
    if r.ok:
        print("verified owner:", r.json()["id"]); break
    print(f"attempt {attempt}: {r.status_code} {r.text[:200]}"); time.sleep(15)
else:
    raise SystemExit("verification did not succeed; TXT may not have propagated")

# 4. add domain property to Search Console
site = urllib.parse.quote(f"sc-domain:{DOMAIN}", safe="")
requests.put(f"https://www.googleapis.com/webmasters/v3/sites/{site}", headers=g).raise_for_status()

# 5. smoke: list sites
print(requests.get("https://www.googleapis.com/webmasters/v3/sites", headers=g).json())
```

curl 等价（token 获取用 `gcloud auth application-default print-access-token` 或自签 JWT，略）；核心三条：

```bash
# getToken
curl -s -X POST "https://www.googleapis.com/siteVerification/v1/token" \
  -H "Authorization: Bearer $GTOKEN" -H "Content-Type: application/json" \
  -d '{"site":{"type":"INET_DOMAIN","identifier":"foundagent.net"},"verificationMethod":"DNS_TXT"}'
# insert（放好 TXT 后）
curl -s -X POST "https://www.googleapis.com/siteVerification/v1/webResource?verificationMethod=DNS_TXT" \
  -H "Authorization: Bearer $GTOKEN" -H "Content-Type: application/json" \
  -d '{"site":{"type":"INET_DOMAIN","identifier":"foundagent.net"}}'
# Search Console 挂载 domain property
curl -s -X PUT "https://www.googleapis.com/webmasters/v3/sites/sc-domain%3Afoundagent.net" \
  -H "Authorization: Bearer $GTOKEN"
```

### 引用（2026-07-04 抓取）

- https://developers.google.com/site-verification/v1/getting_started —— scope、INET_DOMAIN/DNS_TXT 概念、domain 覆盖子域、delegation、"executed in the context of the authenticated user's account"
- https://developers.google.com/site-verification/v1/webResource/getToken —— `POST …/v1/token`、site.type/identifier/verificationMethod 参数表（页面更新于 2024-06-11，API 无变更）
- https://developers.google.com/site-verification/v1/webResource/insert —— `POST …/v1/webResource?verificationMethod=`、两个 scope
- https://developers.google.com/webmaster-tools/v1/sites/add —— `PUT https://www.googleapis.com/webmasters/v3/sites/{siteUrl}`、`sc-domain:example.com` 写法、`auth/webmasters` scope（更新于 2024-07-23）
- https://github.com/hectorj/terraform-provider-googlesiteverification（docs/resources/dns.md）—— SA 凭证 + DNS TXT 全自动验证的生产级旁证；其 create timeout 印证传播等待坑

---

## 问题 2：GA4 程序化建属性

### 结论：半人工 —— account 一次性人工，之后 property/data stream 全程序化

- **建 GA4 account 无法全程序化**：Admin API 的 `accounts.provisionAccountTicket`（`POST https://analyticsadmin.googleapis.com/v1beta/accounts:provisionAccountTicket`，scope `analytics.edit`）只返回一个 `accountTicketId`；官方参考页原文明确其 `redirectUri` 是 "Redirect URI where **the user will be sent after accepting Terms of Service**. Must be configured in Cloud Console as a Redirect URI"，且响应字段说明 accountTicketId 是 "The param to be passed in the **ToS link**"。即：ticket 必须由人类在浏览器里接受 ToS 才能兑现成 account——ToS 接受是硬性人工环节，SA 无法代签。实操上直接在 analytics.google.com UI 手工建 account 比走 provisionAccountTicket 更省事（后者还要预配置 redirect URI）。
- **account 存在之后全程序化可行**：
  - `properties.create`：`POST https://analyticsadmin.googleapis.com/v1beta/properties`，body 为 Property 实例（`parent: "accounts/{ACCOUNT_ID}"`, `displayName`, `timeZone` 等），scope `analytics.edit`。前提：SA 邮箱已被加为该 GA4 account 的 **Editor**（人工在 Admin → Account access management 加一次，或由已有管理员经 accessBindings API 加）。
  - `properties.dataStreams.create`：`POST https://analyticsadmin.googleapis.com/v1beta/properties/{PID}/dataStreams`，body 为 DataStream（web 流填 `webStreamData.defaultUri`），同 scope；返回含 `measurementId`（`G-XXXX`），拿去埋站点代码。
  - 读数据走 Analytics Data API（`analyticsdata.googleapis.com`，scope `analytics.readonly`），SA 有 account/property 访问权即可。

### 每个新站点的零人工流程（account 就绪后）

```python
# creds: 同一 google-sa.json, scope https://www.googleapis.com/auth/analytics.edit
import requests
BASE = "https://analyticsadmin.googleapis.com/v1beta"
prop = requests.post(f"{BASE}/properties", headers=g, json={
    "parent": "accounts/ACCOUNT_ID",          # 人工建好的 account
    "displayName": "barcodely.foundagent.net",
    "timeZone": "America/Los_Angeles",
    "currencyCode": "USD",
}).json()                                      # -> {"name": "properties/123456789", ...}
stream = requests.post(f"{BASE}/{prop['name']}/dataStreams", headers=g, json={
    "type": "WEB_DATA_STREAM",
    "displayName": "web",
    "webStreamData": {"defaultUri": "https://barcodely.foundagent.net"},
}).json()
print(stream["webStreamData"]["measurementId"])  # G-XXXX，嵌入站点 gtag
```

### 引用（2026-07-04 抓取）

- https://developers.google.com/analytics/devguides/config/admin/v1/rest/v1beta/accounts/provisionAccountTicket —— redirectUri/ToS 原文（页面更新于 2025-04-02）
- https://developers.google.com/analytics/devguides/config/admin/v1/rest/v1beta/properties/create —— endpoint/scope（更新于 2025-01-14）
- https://developers.google.com/analytics/devguides/config/admin/v1/rest/v1beta/properties.dataStreams/create —— endpoint/parent 格式/scope（更新于 2024-10-09）

---

## 问题 3：Cloudflare token 权限实测

### 结论：权限足够 —— 读、写、删全部实测通过，问题 1/2 的 TXT 自动化路径畅通

2026-07-04 用 `accounts/foundagent/secrets.env` 的 `CLOUDFLARE_API_TOKEN`（仅 source 使用，值未落盘）对 zone `fde57901aa4b6a85c63e9395ab23d615` 实测：

| 操作 | 调用 | 结果 |
|---|---|---|
| token 校验 | `GET /user/tokens/verify` | `success: true`，status `active`（token id `379f45d7…`，非机密元数据） |
| 列 DNS 记录 | `GET /zones/{zone}/dns_records` | `success: true`；可见 apex A→76.76.21.21、www、及十余条 `*.foundagent.net` CNAME→`cname.vercel-dns.com` |
| 建 TXT | `POST /zones/{zone}/dns_records`，name=`_domain-rail-test.foundagent.net`，content=`domain-rail-research-probe`，ttl=60 | `success: true`，record id `2b535dd3…`，created `2026-07-04T02:24:49Z` |
| 删 TXT | `DELETE /zones/{zone}/dns_records/2b535dd3…` | `success: true`，测试记录已清理，zone 无残留 |

无任何权限报错，token 具备该 zone 的 DNS Edit 能力。PRD 约束「CF token 权限不足时报用户升级」不触发。

---

## 对 design 的建议

### 全自动路径（推荐主线）

前置到位后，GSC 侧一个幂等脚本跑完，无人工：

1. `provision_gsc.py`（问题 1 草稿即骨架）：getToken → CF 放 apex TXT（已存在同值则跳过）→ insert 带退避重试 → `sites.add sc-domain:foundagent.net` → `sites.list` 冒烟。凭证按账号包契约：`google-sa.json` 走 `/account:ro`，CF token 走 secrets.env。
2. Domain property 覆盖所有子域 ⇒ 子域自助（每 agent 随便开 CNAME→Vercel）与 GSC 完全解耦：开新子域**不需要**任何 Google 侧动作，researcher 的 gsc MCP e2e（AC1/AC2）在验证完成后即可补跑。
3. TXT 验证记录永久保留（写进 accounts/README.md 的子域约定里：apex 的 `google-site-verification=` TXT 不许删）。
4. 可选增强：verify 成功后用 `webResource.update` 把用户人类邮箱加进 owners，让用户能在 GSC UI 看到属性。

### 人工步骤清单（一次性，全部前置）

1. **GCP 侧（PRD 前置 5，尚未完成——`accounts/foundagent/` 目前只有 secrets.env，无 google-sa.json）**：建/复用 GCP 项目 → 启用 4 个 API（`siteverification`、`searchconsole`、`analyticsadmin`、`analyticsdata`）→ 建 SA → 下载 JSON key → 放 `accounts/foundagent/google-sa.json`。SA 不需要任何 GCP IAM 角色（这些 API 的权限模型在 Google 产品侧，不在 GCP IAM）。
2. **GA4 侧**：在 analytics.google.com 人工建一个 GA4 account（接受 ToS）→ Admin → Account access management 把 SA 邮箱加为 **Editor** → 把 account id 记入账号包（如 secrets.env 的 `GA4_ACCOUNT_ID`）。此后每个新站点建 property/stream 零人工。
3. GSC 侧**无人工步骤**（这是相对 accounts/README.md 现有「人工 UI 验证 + 加 SA 邮箱」路径的关键升级；旧路径可降级保留为 fallback）。

### GA4 时序建议

PRD 需求 4 的「等首个站点上线再接」可以细化为：人工前置（上面第 2 条）现在就做掉；property/data stream 创建脚本随 design 一起交付但等首个站点上线才执行（measurementId 需要嵌进站点代码，无站点时建 property 无意义）。
