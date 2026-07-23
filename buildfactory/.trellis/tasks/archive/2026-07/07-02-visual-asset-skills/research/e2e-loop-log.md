# e2e 验证记录（AC4 / AC5 / 盲评）

日期：2026-07-03，本机（darwin, node v23.9.0, codex-cli 0.142.5, Playwright chromium @ $CLAUDE_JOB_DIR/tmp/pwenv）。产物在 job tmp 目录（会随 job 清理；本文是留档记录）。

## 盲评（Phase A / AC2 可用性）

无上下文 sub-agent 只拿到 skill 目录 + goal（小红书封面「AI 员工上岗第一天」）+ 最小 /company 事实。产出合格 Swiss/IKB 封面卡（S01 配方、工牌 2×2 网格 signature、渲染一次通过）。其 13 条摩擦报告驱动了 host 修订，最重要的是**依赖闭包第二课**：guizang 文档处处假设的种子模板/webgl 背景/image-overlay.md 未被 vendor（已补齐 + 断言锁定）。

## gen-image wrapper（Phase B / AC4）

- Codex 副路径：`GEN_IMAGE_VIA_CODEX=1` 真出图（800×800 精确尺寸，sips 后处理生效），一次通过。
- 回落链路：codex 不可用 → 自动转 API → 无 key 时带清晰诊断 exit 1。已验证。
- **API 主路径：本机无 OPENAI_API_KEY，未能真出图 —— AC4 遗留 blocker**。首个有 key 的环境跑：
  `python3 agents/assets/skills/gen-image/scripts/generate_image.py --prompt "smoke test" --out /tmp/t.png`

## visual-iterate 全链一轮（Phase C / AC5）

对象 = 盲评产出的真卡片（非人造样例）：

| 步骤 | 结果 |
|---|---|
| 脚本门（validate-social-deck.mjs，staged 进 $PLAYWRIGHT_DIR 运行） | 0 FAIL / 1 WARN：R5 密度 67%（四带 60/69/98/41）。⚠️ 盲评 agent 自评曾声称"密度≥75%通过"——被确定性检查戳穿，实证「脚本门先于自评」 |
| fresh-context 评审（doer≠judge，只给 PNG+goal+rubric 原文） | 1 [High] 标签对比度 4.16:1；2 [Medium] 底带空旷（与 R5 交叉印证）/ 极细字重脆弱；2 [Nit] |
| 最小修复（2 处 surgical edit） | `--grey-3 #737373→#5c5c5a`；卡片 `min-height 236→290px` |
| 重渲 + 重验 | 校验器 1 clean / 0 fails / 0 warns |
| delta 复核（同评审员） | **PASS**：对比度 5.87:1；底带填至 90.8% 画布高、上部节奏像素级不变；零新增 Blocker/High（2 新 Nit 记档） |

## 过程中修掉的 host 缺陷

- 评审员首行 PASS 却报 [High] → rubric 输出契约补「有 Blocker/High 必须 FAIL」。
- 校验器裸 import playwright，物化后无 node_modules → host 写明 stage 进 `$PLAYWRIGHT_DIR` 的调用法（本轮实测可用）。
- `.canvas`/`.poster` 选择器分裂、`out/`→`output/` 命名、字号带仲裁等 13 条盲评摩擦全部回填 host（详见 design-asset SKILL.md 与 git log）。

## 已知遗留

- AC4 API 主路径真出图（等 OPENAI_API_KEY / provisioning 归属拍板）。
- 评审员 [Nit]：底部 hairline 与网格 0px 相贴（上方 49px）不对称；2x 导出尺寸约定（2160×2880 vs 1080×1440 spec）宜在发布侧确认平台接受 2x。
