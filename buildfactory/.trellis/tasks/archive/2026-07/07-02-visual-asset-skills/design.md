# Visual-asset 三原子 — 设计

> 依据：`prd.md` + `research/visual-asset-skills-research.md`（§5 落地建议为骨架，tradeoffs 已在报告打完，此处只记结论）+ 父 design §5.5/§8/§9。
> 纪律照旧：赋能 > 限制；①/②/③ 三道过滤；vendor 依赖闭包完整（de-ai-ify 盲评教训）。

## 1. 目录落形（de-ai-ify 范式：host SKILL.md = 唯一原创层，上游 verbatim 进 references/）

```
agents/assets/skills/
├── design-asset/
│   ├── SKILL.md                  # host：格式路由、平台尺寸表、主题自治选择、组合指引、voice 读 /company
│   ├── ATTRIBUTION.md
│   ├── references/
│   │   ├── frontend-design.md    # anthropics（Apache-2.0）56 行整拷 + LICENSE
│   │   ├── design-styles.md      # jiji262（MIT）10 套设计语言
│   │   ├── design-principles.md  # jiji262（MIT）反 slop 清单 + 硬阈值
│   │   ├── themes/*.md           # theme-factory 10 色板（Apache-2.0）
│   │   ├── guizang/…             # 风格系统 + 平台规格（AGPL·拍板）
│   │   └── token-checklist.md    # superdesign theme-tool.ts 提取（无 license·拍板）
│   └── scripts/render_asset.mjs  # Playwright 截图（改造本机 frontend-slides export-pdf.sh，MIT）
├── gen-image/
│   ├── SKILL.md                  # host：模型路由表、廉价侦察→昂贵定稿、禁文字重生图、组合指引
│   ├── ATTRIBUTION.md
│   ├── references/
│   │   ├── smixs-image/…         # 整树 verbatim（MIT）；⚠️偏离记录(07-03)：原计划"俄语段译文放 host 附录"放弃——俄语遍布全树非个别段落、且消费者是 LLM 可原样读，改为 host 声明 normative（见 gen-image ATTRIBUTION）
│   │   └── codex/…               # JunSeo99 闭包（MIT）：cli-reference + prompting-guide
│   └── scripts/generate_image.py # wrapper：API 主 + codex 副 + 自动回落 + 尺寸后处理
└── visual-iterate/
    ├── SKILL.md                  # host：loop 状态机、评审 rubric、终止数字、doer≠judge 落法
    ├── ATTRIBUTION.md
    └── references/guizang/…      # validate-social-deck.mjs + qa-checklist（AGPL·拍板）；⚠️修正(07-03)：调研称上游有 render.mjs 属误、仓库无此文件，渲染统一走 design-asset 自写 render_asset.mjs；溢出分级以事实形式进 host（带出处）
                                  # rubric 借鉴（OneRedOak/gstack）改写进 SKILL.md，不拷文件
```

## 2. 关键决策（结论，论证见 research）

- **渲染器**：Playwright 截图为默认（networkidle + `document.fonts.ready` + deviceScaleFactor 2；Docker 镜像 pin 作注记）。satori/resvg 仅记为轻量 fallback 选项，v1 不实现。
- **生图调用**：主 = `OPENAI_API_KEY` 直连 Images API（gpt-image-1-mini low $0.005/张起步，按路由表升档）；副 = `codex exec`（`--sandbox workspace-write` + 反回退子句 + `--enable image_generation` + `~/.codex/generated_images` 兜底 + 429 退避），env flag `GEN_IMAGE_VIA_CODEX=1` 开启，失败自动落回主路径。伪代码 = research §4.5，本机 e2e 已验证（0.142.5，gpt-image-2）。
- **评审（doer≠judge）**：优先 fresh-context 子代理按显式 rubric 评审；若 resident 环境子代理机制不可用，降级 = 同 session 但强制「确定性校验器先跑 + 显式书面 rubric + 证据截图」（§4 Q1 实施时探明）。
- **迭代成本纪律**：Codex 生图慢（1-2min/张）→ 迭代时优先改 HTML 层而非重生成底图；每轮修订重注入保留清单（OpenAI 官方头号失败模式修法）。
- **组合指引**：写进三个 SKILL.md 各自的「何时用我 / 何时叫兄弟」段，不写死流程（父任务原子可组合原则）。

## 3. host 体量标定

各 SKILL.md < 500 行（官方硬约束），references 一层深，>100 行 reference 带 TOC。预估：design-asset host 150-250 行；gen-image host 120-200；visual-iterate host 150-250。

## 4. 测试与验证

- `test_resident_loadout`：growth 物化集合含三 skill + 每 skill 至少一个 `references/` 深层文件存在断言 + scripts 文件存在。
- **e2e（AC5）**：goal 场景「为 X 做一张 launch quote card」——design-asset 出 HTML→PNG；gen-image 出底图（API 路径）；visual-iterate 跑至少一轮 检查→评审→修补→PASS。产物留档，人工抽查。
- **盲评**：无上下文 sub-agent 只读 skill 目录实测产图（de-ai-ify 教训：写完必须盲评）。

## 5. Open Questions（实施时收口）

1. fresh-context 评审子代理在 resident（claude -p）环境的可用性 → 探明；降级路径已定（§2）。
2. guizang vendor 粒度：整树 vs 只拿「风格系统 + 校验器 + 渲染器」三块——倾向后者（拍板解禁不等于不做最小化），实施时按依赖闭包定。
3. scripts 运行时依赖（node/playwright/python-openai）在目标 VM 的存在性 = provisioning（out of scope），缺则记 blocker。
