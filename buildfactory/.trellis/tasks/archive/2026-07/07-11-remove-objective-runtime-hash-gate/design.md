# 技术设计：Objective 生效后只恢复事务，不校验内容

## 1. 设计结论

把 Objective 的完整性边界收回到“提案正在审核和生效”的阶段：

- staged 完整正文、staged 短版、revision、Verifier 身份门和 PASS 事务保持严格；
- Objective 一旦生效，短版和 `/company` 就是同一信任域中的当前状态，不再逐字节追认批准版本；
- 每次唤醒仍先恢复被打断的 PASS 事务，但恢复成功后直接读取当前短版；
- active metadata 继续定位当前 Objective 拥有的 company leaf，存量哈希保留但只作审计信息。

这不是取消 Objective 审核，而是取消一个不能提供真实权限隔离、却能让 Objective 无声消失的运行时开关。

## 2. 当前数据流与问题

当前读取链路是：

```text
Agent wake / objective show
  → objective_read_ready
  → 恢复事务
  → 解析 active metadata
  → 比较短版哈希
  → 读取并锁定 /company leaf
  → 比较全文哈希和导航摘要
  → 任一失配：返回 None，不注入 Objective
```

当前替换链路还会在新 PASS 前重复比较旧短版、旧全文和旧摘要。thirdtest 证明，这会把正常经营维护当成绕过审批，并把系统困在无法自助替换的状态。

## 3. 新读取链路

保留现有 `objective_read_ready(path)` 调用面以降低兼容风险，但改变其职责：

```text
Agent wake / objective show
  → objective_read_ready
  → 只恢复未完成事务
  → 恢复成功：ready
  → 直接读取当前 objective.md
```

只有事务恢复失败仍返回 unavailable。正常读取不解析 `objective.active.json`，不打开 `/company`，不比较短版、全文、摘要或任何哈希。

`agent_loop._read_objective` 保持原有缺失、空白、读取异常和 6000 字符截断行为；更新注释，使“内容失配会跳过”的旧承诺消失。

## 4. 新 PASS 对已有 active 状态的处理

`_load_active` 只保留后续安全操作真正需要的结构校验：

- schema version；
- role 必须是 CEO；
- 安全的 company 相对路径；
- 非空 revision。

不再要求或验证 active 的 `full_sha256`、`short_sha256`、`company_summary`。新提案 manifest 仍严格要求这些字段并重新核对 staged 内容。

`_apply_ceo_pass` 删除对旧短版哈希、旧全文哈希、旧导航摘要和旧 leaf 必须存在的前置要求：

- 旧短版存在时，按当前内容进入 history；缺失时跳过短版归档；
- 旧 full leaf 存在且是 UTF-8 Markdown 时，按当前内容进入 history；缺失时允许新 PASS 重建；
- path 不变时覆盖当前 leaf；path 改变时只删除 active metadata 所有的旧安全路径；
- 事务快照、失败回滚和崩溃恢复继续覆盖实际写入前的当前状态。

## 5. 保留的严格边界

以下保护不变：

1. `propose` 最后写 manifest，并为本次 staged full/short 生成 revision 和哈希；
2. `verdict` 必须由 Verifier 身份执行；
3. verdict revision 必须等于当前 staged revision；
4. verdict 前重新计算 staged full/short 哈希；
5. FAIL revision 的关闭语义不变；
6. 新 company path 不能覆盖非当前 Objective 所有的 leaf；
7. PASS 的 prepared/committed journal、快照和回滚不变；
8. 非 CEO 单文件 Objective 协议不变。

因此，直接编辑生效短版确实会影响下一次唤醒——这是用户明确接受的同信任域行为；但通过正式提案命令时，审核内容与生效内容仍不会混版。

## 6. 兼容与迁移

- `objective.active.json` 继续写 schema v2 和现有字段，不需要迁移 thirdtest 或其他公司状态。
- `objective_read_ready` 保留函数名和返回形状，现有调用者无需同步迁移。
- 已经因哈希失配的公司，在新代码实际加载后会恢复注入当前短版；无需改 active metadata 或回滚 company leaf。
- 运行中的 resident agent loop 是常驻 Python 进程。bind mount 会让新源码在容器内可见，但不会刷新 `sys.modules` 中已经导入的 `orchestration.objective`；要让现有 thirdtest CEO 采用新读取行为，需要在代码与回归通过后重启 CEO 进程。
- 当前缺陷只影响 CEO v2 company objective 的唤醒注入；Verifier 的 `objective verdict` 由新启动的 CLI 子进程加载代码，其他部门仍使用 legacy Objective。因此若执行发布，只需重启 `thirdtest-ceo`，无需重启整个 fleet。
- `/sessions/ceo`、`/company`、ledger、inbox 和 `/agents` 都是宿主持久挂载，正常的 service restart 不清除这些状态；但必须等待当前 Claude wake 结束，避免杀死正在执行的回合。
- 用户已授权把受控 CEO restart 与重启后只读验证纳入本任务；它是所有代码和回归通过后的最后发布门。

## 7. 测试设计

- 将“active hash 失配阻断读取”改为“短版、full、summary、active 审计字段漂移均不阻断读取”。
- 将“新 PASS 拒绝旧 active 漂移”改为“新 PASS 接受漂移并归档当前可读内容”。
- 增加 full leaf 缺失后仍可读取短版并被新 PASS 恢复的覆盖。
- 保留并运行 staged bundle 篡改、迟到 revision、身份门、路径所有权、PASS 回滚和 prepared/committed 恢复测试。
- Agent loop 测试证明 company full 改变后仍注入短版，短版直接改变后注入新内容，且不输出 `objective unavailable`。

## 8. 回滚

代码回滚即可恢复旧校验；active schema 和存量文件没有迁移。回滚会再次让已经漂移的公司进入 unavailable 状态，因此回滚前必须明确接受这一旧行为，不能靠修改 thirdtest 状态掩盖。
