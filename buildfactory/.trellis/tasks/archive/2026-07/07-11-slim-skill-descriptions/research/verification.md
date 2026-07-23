# 实施与验收证据

验证时间：2026-07-11（Asia/Shanghai）

## Catalog 结果

| 范围 | 项数 | Description 字符数 | 英文分词 |
|---|---:|---:|---:|
| 全部顶层 host | 20 | 2,863 | 443 |
| Builder | 7 | 916 | — |
| CEO | 10 | 1,405 | — |
| Growth | 13 | 1,852 | — |
| Researcher | 7 | 916 | — |
| Verifier | 4 | 546 | — |

相比实施前，顶层总量从 5,760 降到 2,863 字符（减少 50.3%）；Growth 的实际发现量从 17 项 / 5,080 字符降到 13 项 / 1,852 字符（字符减少 63.5%）。最长单项 176 字符，所有角色均低于 2,000 字符。

递归扫描 `agents/assets/skills` 只剩 20 个精确名 `SKILL.md`，且全部位于顶层 host。四个旧嵌套路径已清零；live tree 与 live 测试/文档中没有旧路径。归档任务保留历史路径记录，按设计不回写。

实施时搜索了现行 ATTRIBUTION 路径；当前工作树没有承载这四个文件路径的 live ATTRIBUTION 文件，因此没有可改的归因路径。许可证与 vendored 子树仍随 host 完整保留。

## Vendored 完整性

| 新路径 | SHA-256 |
|---|---|
| `de-ai-ify/zh/upstream-SKILL.md` | `28ccdd2792a456168e7872f6d9d1186982680128240b38516bf83c84ea272beb` |
| `design-asset/references/anthropic-frontend-design/upstream-SKILL.md` | `1608ea77fbb6fc30d13a97d12cfa8ebf31358d40f0dd97beed24829d6b3f45dd` |
| `gen-image/references/smixs-image/upstream-SKILL.md` | `cbcb39232bfd43e14f05bc0ead38b8fd01a5304aca6f295befc8021345cc0dea` |
| `gen-image/references/codex/upstream-SKILL.md` | `30747274af88ee0c0a335f9de96039d33379289cf56d60e620a57c5425c5c894` |

四项均与实施前固定值一致。host 路由与物化测试改用新路径；host 明确说明上游正文中的 `SKILL.md` 称呼映射到对应 `upstream-SKILL.md`。

## 确定性验证

```text
定向合同（skill catalog/loadout/reference/Twitter/objective/spec/Codex）：83 passed
agent/tests 全量：233 passed
orchestration/tests 全量：396 passed
git diff --check：通过
```

动态双 runtime 证据见 [dynamic-validation.md](./dynamic-validation.md)：固定镜像版本下，Claude Code 与 Codex 的 Growth/CEO catalog 完全一致，八个高风险场景均 8/8 通过。

## PRD 验收映射

| AC | 证据 | 结果 |
|---|---|---|
| AC1 | role YAML 驱动的静态测试固定 7/10/13/7/4；每棵声明树只允许一个顶层 `SKILL.md` | PASS |
| AC2 | 20 条目标文案逐字落盘；PyYAML 解析后规范化单行；单项均 ≤200 | PASS |
| AC3 | 五角色总量为 916/1,405/1,852/916/546 | PASS |
| AC4 | 五组碰撞语义锚点通过；Claude/Codex 八场景均 8/8 | PASS |
| AC5 | 四份 vendor 哈希、引用完整性、loadout、Objective、Twitter 与全量测试通过 | PASS |
| AC6 | SOP、overview、backend execution spec 已同步同一预算与顶层入口合同 | PASS |
| AC7 | 一次性容器内真实 runtime adapter 物化；Claude 2.1.202 / Codex 0.142.5 catalog 一致，隐藏四名均未暴露；未触碰 live company state | PASS |
