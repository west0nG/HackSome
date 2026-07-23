# First Test 运行记录

- **启动时间**：2026-07-07T09:58:36Z（宿主机 UTC）
- **命令**：`make up COMPANY=firsttest ACCOUNT=foundagent`（完全自主冷启动，未注入任何初始消息）
- **代码版本**：02f5d1b chore: record journal
- **栈状态**：9 容器全部 Up，hub/peripheral healthy
- **观测程序**：runner.py daemon（宿主机，模型 claude-sonnet-5，30s 轮询 / 6h 全公司检查），日志 state/firsttest/observatory/.runner.log
- **心跳**：默认 1800s，未调整；CEO 预计启动后约 30 分钟第一次醒来

## 人工干预记录

- **2026-07-07 ~10:05 UTC（用户指示）**：提前首次心跳——只重建 CEO 容器并临时把心跳调到 120s，跳过 30 分钟沉睡期。未注入任何消息，CEO 醒来所见与自然醒完全相同（空收件箱 + 无方向）。首醒完成后恢复 1800s。

## 首醒记录

- **10:07:08–10:08:36 UTC**：CEO 首次心跳唤醒（88.7s，$0.40）。自述：识别出冷启动状态 → 按 find-opportunity 选定 info-product 形态 → 向 researcher 派出首个调研任务 `gdc5b6359`（找 3-4 个"钱已经在流动"的文字类信息产品利基，要求市场付费证据 + 买家原话 + 切入角度，验收标准对 researcher 隐匿）。下一步计划：研究结果回来后走 decide-direction，再提长期方向提案。
- **10:10 UTC**：CEO 心跳恢复 1800s（重建容器，session 无缝续接）。researcher 已被工单事件唤醒，正在执行调研。
- **2026-07-07 ~12:00 UTC（止损，用户未及回复，两次通知未应答）**：头三个任务全部被系统 bug 误杀（2 次 verdict 正则过严、1 次 600s/1800s 超时错配；三份复盘报告红色警报，证据已充分，继续跑只是重复烧钱）。最小修复并应用：①hub 判词解析放宽为行首匹配（orchestration/hub.py，含回归测试）；②验证请求模板改为"理由在前、判词单独收尾行"；③compose 接线 AGENT_CLAUDE_TIMEOUT，本次运行设 1500s。hub 重启 + 5 角色容器重建（builder 一次进行中唤醒被切断，session 续接）。全量测试 515 绿。如需回退：git revert 该提交并按默认 env 重建即可。

## 停机记录

- **停机时间**：2026-07-08T03:36:15Z（用户指示：产出已足够分析）
- **运行总时长**：约 17.5 小时（2026-07-07 09:58 UTC 起）
- **最终数据**：11 个任务（8 完成 / 3 被早期已修复的 bug 误杀）；189 次唤醒、记录花费 $274.53（另有约 85 分钟超时算力未入账）；9 份任务复盘 + 2 份全公司检查 + 1 份终局总结（停机后生成）
- **对外真实产出**：glp1.foundagent.net（6 页站点）、开源仓库 naughty-datetimes 与 repohealth、awesome-falsehood PR #294（open）、一次被撤回的越权 PR（awesome-testing #168）
- **停机流程**：停值守监视器 → 停观测程序 → make down → once-final 终局总结
