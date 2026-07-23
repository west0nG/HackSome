# Implement — Continuity in memory layer, not sessions (issue 207)

## 执行清单（按序）

### 阶段 A：auto-memory 关闭（R1）

- [x] A1 `docker-compose.yml`：`x-agent-env` 锚点加
      `CLAUDE_CODE_DISABLE_AUTO_MEMORY: "1"`（带一行注释指 issue #207）。
- [x] A2 `agent/runtimes/claude_code.py`：`home_env()` 返回值加
      `CLAUDE_CODE_DISABLE_AUTO_MEMORY: "1"`；codex adapter 未动（无此概念）。
- [x] A3 单测：test_runtimes home_env 断言更新；test_runner 未钉键集合（无需改）；
      test_provisioner mirror test 自动通过（渲染自加载的 compose 文档）。
      新增 test_compose_kills_auto_memory_on_the_agent_anchor 钉住锚点 + 五
      service + "ceo 是唯一 resume 角色"。

### 阶段 B：session 策略（R2/R5）

- [x] B1 `agent/spec.py`：AgentSpec 加 `session: str = "fresh"` 字段 + 已知
      字段表。（偏差：非法值的 WARN+回落放在消费方 `_role_config` 而非 load —
      spec 保持纯声明，与 provider 的既有分工一致。）
- [x] B2 `agents/ceo.yaml`：加 `session: resume` + 注释。
- [x] B3 `orchestration/agent_loop.py`：`_role_config()` 5 元组；fresh 分支
      不 load/save、每 wake 传 None；resume 分支字节不变；boot 日志加
      `session=<mode>`，start 行 fresh 显示 `session=fresh-per-wake`。
- [x] B4 `build_wake_prompt(..., fresh=False)`：ORIENT_PREFIX 定向指令行
      （不提 session 机制）；fresh=False 字节一致。
- [x] B5 单测：spec 解析（缺省/resume/非法值降级）、fresh 模式（None 传入、
      session 文件不读不写、陈旧文件不泄漏）、resume 模式原样、prompt 前缀
      存在/缺省字节一致、main() session_mode 透传 + boot 日志。

### 阶段 C：charter 强调（R3）

- [x] C1 五个 charter 各加落盘小节：doer 三角色"wake 之间不自动延续"版；
      verifier 适配为"每次评审独立、只产出 verdict"（它是只读角色，不能叫它
      写 /company）；CEO"会话会被压缩、承重结论落盘才算数"版。
- [x] C2 charter 无内容 lint；全量测试过。

### 阶段 D：全量验证

- [x] D1 全量单测：`.venv-cua/bin/python -m pytest orchestration/tests
      agent/tests -q` → 468 passed。`docker compose config` 通过。
- [ ] D2 真跑 e2e（AC1–AC3）：`make up`（或最小 compose 子集）起 ceo+builder
      （+一个 codex 角色若有现成配置）：
      - 触发两次 wake（一次 event 一次 heartbeat 即可）；
      - 断言 builder 两次 session id 不同、ceo 相同（boot/wake 日志 + telemetry）；
      - 断言 `/sessions/<role>/projects/*/memory/` 不存在或空；
      - 断言 builder 的 session 文件 mtime 未变。
- [ ] D3 AC4（心跳成本解耦）留到下次长跑验证——在任务 notes 里记为
      deferred-observation，不阻塞收尾。

## 验证命令

```bash
python3 -m pytest orchestration/tests agent/tests -q
make up COMPANY=<testco>   # e2e；结束后 make down
grep -r "session=" <logs>  # boot 行断言 fresh/resume
ls state/<testco>/sessions/*/projects/*/memory/ 2>/dev/null  # 应无输出
```

## 风险文件 / 回滚点

- `orchestration/agent_loop.py` 是常驻循环核心 —— resume 分支必须字节不变，
  改动全部走 fresh 新分支；单 commit，revert 即回滚。
- `docker-compose.yml` 锚点被 provisioner 镜像 —— 改完必跑 test_provisioner。
- charter 是纯文案，独立 commit，可单独回退。

## 收尾前检查

- [ ] prd AC1–AC3/AC5/AC6 勾完（AC4 记 deferred-observation）。
- [ ] issue #207 关闭评论：链接本任务 + 决策摘要（fresh-except-ceo、
      auto-memory 关死、落盘强调）。
- [ ] spec 更新（3.3）：连续性契约写进 .trellis/spec/backend（agent_loop 的
      session 语义 + auto-memory 开关位置）。
