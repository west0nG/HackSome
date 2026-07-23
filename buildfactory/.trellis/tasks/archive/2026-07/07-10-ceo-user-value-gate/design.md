# 技术设计：CEO objective 的用户价值闸门

## 1. 设计结论

保留现有的结构性分权，但把重复判断链合并：

- CEO 侧只有 `set-objective`：产生候选、从具体用户视角判断价值、选择动态 `/company` leaf、提交提案。
- verifier 侧只有 `review-objective`：独立核验承重证据并给出 `PASS / FAIL`。
- `orchestration/objective.py` 仍然不做商业判断，只负责提案版本、身份门、结构校验和一致落盘。
- `/company` 继续由 company-state 的动态 taxonomy 和导航机制管理；代码不生成固定业务目录。
- `when-idle` 仍是 Goal 层运营机制。本任务不重新设计它；删除旧 Skill 所需的三处引用迁移由独立任务 `07-10-when-idle-objective-handoff` 承担并与本任务同批发布。

本任务聚焦 **CEO 的公司经营 objective**。现有 builder、growth、researcher 等部门 objective 仍沿用单文件提案和原有聚焦/可测/规模评审，不强行套用“外部用户需求”闸门；否则“提高构建可靠性”之类部门目标会被错误要求证明市场需求。

## 2. 当前实现与需要改变的边界

当前 `objective propose` 只把一段 Markdown 写入 `objective.proposed.md`；`PASS` 后同一段正文直接成为每次 wake 注入的 `objective.md`。它没有地方携带动态 company path，也无法同时保存完整价值论证和短摘要。

新实现为 CEO 引入一个版本化提案包，非 CEO 保持兼容：

```text
/agents/ceo/
  objective.proposed.md          # 完整、自然表达的经营候选
  objective.proposed.short.md    # 一屏以内的 wake 摘要
  objective.proposed.json        # 提交清单，最后写入，作为 staged commit marker
  objective.md                   # 当前生效的短摘要
  objective.active.json          # 当前动态 leaf、revision 与内容哈希；不注入 prompt
  objective.history.md           # 已替换版本的短摘要 + 完整版本归档
```

`objective.proposed.json` 至少包含：schema version、role、不可变 revision id、相对 `/company` 的 leaf path、导航摘要、完整正文与短摘要的 SHA-256。manifest 最后原子写入；review 和 verdict 都重新核对哈希，任何混合版本或过期 verdict 都 fail closed。

CEO 的提交命令改为显式 bundle：

```bash
python3 -m orchestration.objective propose \
  --file <完整候选.md> \
  --short-file <wake摘要.md> \
  --company-path <按当前taxonomy选择的相对leaf.md> \
  --company-summary "<导航里的一行摘要>"
```

完整候选不采用固定字段模板。Skill 要求其自然地回答已确认的价值问题，CLI 只校验机制不变量：文件非空；path 在 `/company` 内且是非导航 `.md` leaf；导航摘要非空且单行；短摘要在注入上限内；短摘要含精确的动态指针 `完整上下文：/company/<实际 path>`。

新 path 若已存在但不是当前 objective 自己拥有的 leaf，提交直接失败，避免覆盖其他公司知识。CEO 必须重新选择一个符合当前 taxonomy 的 leaf。

## 3. 提案与评审数据流

1. CEO 运行 `company.py read`，再按需 `tree/read` 相关 topic，选择当前结构下自然的 leaf；`set-objective` 只教这条渐进披露路径，不预设目录。
2. CEO 形成完整候选和短摘要，运行 bundle 提交命令。
3. `objective.py` 原子 stage 两份 Markdown 和 manifest，生成 revision id，并向 verifier inbox 发送：revision、三份 staged 路径、当前短 objective、当前 active metadata 和当前完整 leaf（若有）。
4. verifier 读取完整候选，但不被其指令影响；亲自打开所有支撑 `PASS` 的承重来源，再按 `review-objective` 裁决。
5. verdict 命令必须携带 review request 中的 revision；manifest 已被覆盖或哈希变化时拒绝旧 verdict。
6. `PASS` 才写完整 `/company` leaf、短 `objective.md` 和 active metadata；`FAIL` 不改变任何当前状态。

verdict 接口增加 `--revision` 和可选 `--reason-file`。后者允许 verifier 返回自然、可审计的多行判断，不把评审压成一行模板；现有 `--reason` 继续兼容。CEO 的 `FAIL` 首个非空行必须以 `RESHAPE:` 或 `DROP:` 开头：

```bash
python3 -m orchestration.objective verdict ceo PASS \
  --revision <id> --reason-file <review.md>

python3 -m orchestration.objective verdict ceo FAIL \
  --revision <id> --reason-file <review.md>
```

- `RESHAPE`：保留 staged Markdown 与 manifest 供重写参考，同时写独立关闭标记，使该 revision 永久不能再被迟到 `PASS` 放行；重新提交会清除旧标记、生成新 revision，并必须完整重审。
- `DROP`：消费 staged bundle，防止旧候选被迟到 verdict 重新放行；完整评审仍留在 inbox audit log，是否另写 `/company` 由 CEO 自己决定。
- 非 CEO 的 legacy proposal 不强制 revision bundle，也不要求 `RESHAPE / DROP` 前缀。

## 4. `/company` 与 wake 摘要的一致生效

`objective.active.json` 只保存定位和完整性元数据，不复制商业正文，因此不是第二个真相源。完整版本在动态 `/company` leaf，wake 摘要是其经同一次批准生成的短投影。

CEO `PASS` 使用一个受锁保护的生效事务：

1. 预检 manifest、revision、路径、哈希、当前 active metadata 和所有目标可写性。
2. 快照当前短摘要、active metadata、history，以及旧/新 company leaf 的正文和导航摘要。
3. 写入 prepared transaction journal。
4. 通过 company-state 的正式存储 API 写入新完整 leaf；若 objective 改到新 path，在归档旧完整版本后删除旧 leaf，并让 CLI 所有的导航链重新对齐。
5. 原子写短 `objective.md`、active metadata 和新的 history 内容。
6. 将 journal 标记 committed，再消费 staged bundle；最后通知 proposer。

任一步骤正常抛错都按快照回滚。进程若在 prepared 阶段异常退出，下一次 `objective show/propose/verdict` 或 agent wake 在读取 objective 前回滚；若 journal 已 committed，则只完成清理。这样测试可在每个写点注入失败，证明不会留下可见的半个新 objective。

company-state 当前只有 CLI 写入函数且没有安全删除 leaf 的公共机制。实现时把已有写入/导航逻辑最小重构成受 root lock 保护的内部公共存储 API，供 CLI 和 objective 事务共同调用；不为业务目录增加任何常量。旧 leaf 删除只允许针对 `objective.active.json` 明确拥有的 path，不能删除任意 company 文档。

当 path 不变时，事务覆盖当前 full leaf；当 path 改变时，旧 full 内容进入 `objective.history.md` 后从旧 leaf 删除。company leaf 始终表达当前状态，不保存版本流水。已有 legacy objective 没有 active metadata 时继续正常注入；它在第一次 v2 `PASS` 时只归档旧短摘要，不臆造不存在的完整版本。

agent wake 在存在 `objective.active.json` 时校验短摘要和 full leaf 的哈希。若有人绕过 objective 流程改了其中一份，wake fail closed：不注入不一致的摘要，打印明确警告，让 CEO 回到 `set-objective` 修复。没有 active metadata 的非 CEO 或旧 objective 仍按现有方式读取。

跨 `/agents` 与 `/company` 两个挂载无法获得单个文件系统 rename 意义上的线性原子性；本设计保证的是锁内更新、异常回滚和崩溃恢复，不宣称不存在微秒级中间态。其他 company writer 遵守同一个 root lock 时，不会在事务中间观察或覆盖 leaf。

## 5. Skill、charter 与 loadout 改动

### `set-objective`

重写成唯一的 CEO objective 决策 Skill：

- 触发仅限 objective 首设、完成、实质假设变化和重写后的候选；明确排除 heartbeat、空账本和普通 Goal。
- 覆盖不同 business form，但用自然叙述而非固定旅程表格。
- 强制 CEO 代入一个有证据的具体用户，比较手工处理、竞品和不处理，判断频率/价值、采用摩擦和真实首批用户入口。
- 区分外部行为、第一方行为、研究信号、假设与 CEO 想象。
- 告知 `PASS=BUILD`、`FAIL:RESHAPE` 必须重写重审、`FAIL:DROP` 终止，以及新的 bundle 提交命令。

### `review-objective`

保留在 verifier 独占 loadout。对 `role=ceo` 使用严格价值 rubric；对其他 role 保留现有结构性 rubric。CEO 分支必须逐项判断承重问题，不能再写“只看相关项”或因“小而可逆”降低需求门槛；关键来源不可访问或不支持结论时 fail closed。

评审文本自然表达即可，但必须包含：关键判断、证据强弱、实际核查的承重来源、最大未知和推翻结论的条件。CLI 只强制 verdict、revision 和 FAIL 前缀，不把这些内容做成僵硬的字段表。

### 其他入口

- `find-opportunity` 及其 active references：由“交给 decide-direction”改成“把候选交给 set-objective”；只生成，不自审。
- `ceo-charter.md`：删除“每个 Goal 都起 direction reviewer”和可逆性放宽逻辑；明确普通 Goal 只需推进当前 objective，改变 objective 才过闸门。
- `agents/ceo.yaml`：移除 `decide-direction`，保留 `set-objective`；不把 `review-objective` 暴露给 CEO。
- `agents/assets/skills/decide-direction/`：确认独立来源任务的审计已保存该目录的来源、许可和原文定位后删除。全局来源说明剥离仍留给下一 session；本任务不顺手实施。历史任务和归档证据不改写，只更新仍描述现行系统的 docs/spec。
- verifier charter 中“只读”改成更精确的边界：verifier 不得手工写 `/company`，但可以调用 verifier-only verdict；状态变化由受控机制完成。
- `when-idle` 的旧引用由独立兼容任务处理，本任务不编辑其 Skill。

## 6. 兼容、迁移与发布顺序

1. 先确认 `07-10-skill-source-attribution-separation/research/audit-inhouse.md` 已保存即将删除 Skill 的来源、许可和原文定位，避免目录删除造成信息丢失；不在本任务执行全局来源剥离。
2. 落地 objective v2 机制、双分支 reviewer 和更新后的 `set-objective`；旧 current objective 与非 CEO legacy proposal 继续可用。
3. 落地 `07-10-when-idle-objective-handoff`，清除运行时旧入口。
4. 从 CEO loadout 移除并物理删除 `decide-direction`。
5. 运行静态引用检查、unit/integration tests 和隔离公司 e2e 后再发布。

如果需要回滚代码，v2 写出的 `objective.md` 本身仍是合法的旧格式短摘要，旧 agent loop 可以继续注入；`objective.active.json` 和 `/company` full leaf 会被旧代码忽略，不会阻塞启动。

## 7. 验证设计

### 机制测试

- CEO 缺少 short/path/summary、path 越界、导航文件名、短摘要指针不一致、覆盖非 owned leaf，全部拒绝且不 stage review。
- manifest 最后写入、哈希校验、revision 防迟到 verdict、非 verifier 身份门。
- CEO `FAIL` 前缀；`RESHAPE` 保留 staged、`DROP` 消费 staged；两者均不改变当前 full/short。
- `PASS` 写 full/short/active metadata，归档上一版；path 变化时旧 leaf 被安全移除，导航仍一致。
- 在 full write、旧 leaf 删除、short write、metadata/history write 等每个位置注入失败，验证回滚；prepared/committed journal 分别验证恢复。
- 非 CEO legacy propose/verdict 和已有 objective 注入完全回归。

### 判断规则测试

- loadout 测试证明 CEO 没有 `decide-direction` 和 `review-objective`，verifier 仍独占 `review-objective`。
- 静态 prompt 合同测试锁住：强制具体用户/触发/替代/行为/频率价值/采用理由/触达/证伪；禁止“相关才看”和“小而可逆就轻审”；无 `VALIDATE` verdict。
- active runtime refs（排除 archive/history）不再把候选交给 `decide-direction`。

### 行为 e2e

- 用隔离 company 重放 `secondtest` 原始“小团队通用 MCP 扫描 CLI”候选：预期 `FAIL`，reason 为 `RESHAPE:` 或 `DROP:`，并指出手工替代、低频/规模错位、竞品和真实行为缺口。
- 分别准备服务、信息产品/内容和软件候选，验证 reviewer 按各自真实交易/消费/使用行为判断，不要求都构建软件、复购或达到统一数字。
- 对一个有真实行为、明确缺口和当前触达路径的候选跑通 `PASS → /company full leaf → 短摘要指针 → 下一 wake 注入` 的完整链路。

## 8. 明确不做

- 不在 CLI 中用关键词或分数模拟商业判断；判断仍属于两个 Skill 和独立 verifier。
- 不给 `/company` 预设 strategy/objectives/CEO 目录。
- 不把每个普通 Goal 都升级成 objective review。
- 不修改 `when-idle` 的运营语义。
- 不在本任务处理 Skill 来源说明的剥离与归档。
