# Deploy-site skill: agent-facing domain rail norms

## Goal

把 foundagent.net 域名轨的"子域自助"规范从运营者文档搬到 agent 可见面：新增一个薄的
`deploy-site` skill，让 fleet 部署对外站点时起产品名、绑 `<product>.foundagent.net`
子域，并看得到 DNS 红线。

## 背景（firsttest 证据）

- builder 把站点放在 `site/` 目录直接 `vercel deploy --yes`，Vercel 拿目录名当项目名，
  产出 `site-west0ngs-projects.vercel.app`；项目名到跑完都没改。
- "子域自助"规范完整写在 `accounts/README.md:116-134`，但容器只挂
  `accounts/foundagent/` 到 `/account`（`orchestration/broker.py:84`），agent 看不到。
- 域名绑定最后是被 GSC 硬约束倒逼自愈的（`glp1.foundagent.net`），没有这个约束的
  站点（如发到 X 的落地页）不会自愈。
- 两条 DNS 禁则（apex 的 `google-site-verification` TXT、别人建的记录）对手握完整
  Cloudflare token 的 agent 不可见——这是安全窟窿，比丑网址严重。

## Requirements

1. 新 skill `agents/assets/skills/deploy-site/SKILL.md`，fleet 共享（不限 builder）。
2. 内容只装三样，保持薄：
   - **事实**：foundagent.net 轨现状——GSC Domain property 已验证覆盖全部子域、
     子域自助、Cloudflare DNS 即登记册（建名前先查占用）、CNAME 到
     `cname.vercel-dns.com` 的标准接法。
   - **规矩**：对外站点必须起产品名（显式命名 Vercel 项目，不用目录名默认值）+ 绑
     `<product>.foundagent.net`；对外引用只用自定义域，vercel.app 只当内部预览；
     内部临时/e2e 站不绑，不浪费动作。
   - **禁则**：不删 apex 上任何 `google-site-verification=` TXT；不动别的 agent
     建的 DNS 记录（除非目标明确要求迁移）。
3. 不写 vercel/wrangler CLI 教程——LLM 自带的常识不进 skill（三道检验）。
4. skill description 要能在"部署/上线对外站点、绑域名"场景触发。
5. `accounts/README.md` 的"子域自助"小节改为指向 skill（单一事实源，避免两处漂移）；
   运营者侧的一次性 Google 前置状态留在 README。

## Acceptance Criteria

- [x] AC1：skill 文件存在，内容过三道检验（①系统特定 ②压制"deploy URL 能用就交差"
      的 LLM 默认 ③何时绑域的取舍标准），且不含 CLI 常识教程。中文/英文按现有
      skill 惯例（英文）。✅ trellis-check 逐句核验通过。
- [x] AC2：`accounts/README.md` 子域自助小节收敛为指针，无重复正文；两条禁则在
      skill 内语义完整保留（README 原文中文、skill 英文，忠实翻译且保持硬规则地位）。
      ✅ 收敛为 2 行指针；运营者小节原样。
- [x] AC3（真 e2e）：起一个测试公司，给 builder 一个"部署一个对外测试页"的 goal，
      观察其：a) Vercel 项目用了产品名而非目录名默认值；b) 绑了
      `<product>.foundagent.net` 子域且 HTTP 200；c) 未触碰禁则记录。跑完清理
      测试子域与 Vercel 项目。
      ✅ 2026-07-09 COMPANY=e2edeploy（hub+builder+verifier）：goal 中性表述（未提域名/
      命名），builder 自主产出 Vercel 项目 `foundagent-about` + `about.foundagent.net`
      CNAME(DNS-only) + HTTP 200；宿主机独立比对 DNS 基线：仅新增 1 条记录，apex A 与
      两条 google-site-verification TXT 原样。verifier PASS，goal=done。花费 $2.48
      （builder $2.02 + verifier $0.46）。已清理：Vercel 项目删除(204)、CNAME 删除、
      compose down。

## 实施中发现并修复（超出原 scope，已在本任务内落地）

- **分发接线缺口**：skill 落盘 ≠ fleet 可见——必须写进角色 yaml `skills:` 列表才会被
  `agent/resident_loadout.py` 物化。deploy-site 已接入 builder/growth/researcher/ceo
  （verifier 不加，doer≠judge 最小集），同步 `agent/tests/test_spec.py` 与
  `test_resident_loadout.py` 断言。
- **历史遗留同类缺口**：`provision-ga4` 自 07-06 交付以来从未接线，经用户拍板同样接入
  四个角色。pytest agent/tests/ 210 passed。

## Notes

- 体量标定：lightweight，PRD-only。
- 来源规范文本：`accounts/README.md` "foundagent.net domain rail" 一节；改写成对
  agent 说话的形式，而不是照抄运营者口吻。
- 关联记忆：provisioning-artifact-form（反复用能力→skill）、
  skill-design-no-generic-for-llm（三道检验）、foundagent-domain-rail。
