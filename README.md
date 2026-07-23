# HackSome

HackSome v1 是一个本地运行、仅适配 Codex 的 Useful Idea Agent。它接收一道黑客松赛题，经过七步流程后产出零个或多个 Idea Card：

```text
赛题解析 → 人群扩散（最多 5 个）→ 每个人群独立并行 Research
       → Problem Writer → 每个 Problem 的独立 Gateway
       → 每个通过 Problem 的 3 个并行 Idea Generator
       → 每个 Idea 的独立 Red Team → Idea Card
```

系统不做 Top-K、相对排名、强制方向差异或语义去重。多个相似 Idea 只要分别通过统一绝对门槛，就都会保留。

## 核心数据边界

Hub 会保存所有中间 Markdown、完整 Prompt、Codex Session ID、原始 JSONL 日志、结构化输出和 pass/reject 决策。但 Agent 不通过文件读取上游上下文：Hub 会把需要的完整文本直接注入下一个 Prompt。

## 安装

需要 Python 3.11+ 和已登录的 Codex CLI：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/hacksome doctor
```

## 运行

```bash
hacksome run challenge.md
hacksome run --prompt "为本地社区做一个真正有用的产品"
```

可调整并发和扇出：

```bash
hacksome run challenge.md \
  --max-concurrency 4 \
  --max-audiences 5 \
  --researchers-per-audience 1 \
  --idea-generators-per-problem 3
```

查看或离线校验一个 Run：

```bash
hacksome status runs/<run-id>
hacksome validate runs/<run-id>
```

v1 不提供 Run 级 `resume`。同一个 Codex Task 的基础设施重试仍会绑定并恢复该 Task 的准确 Session。

## Run 目录

```text
runs/<run-id>/
  run.json
  input/challenge.md
  events.jsonl
  decisions.jsonl
  tasks/<task-id>/
    prompt.md
    request.json
    result.json
    output.json
    raw/
  artifacts/
    challenge/
    audiences/
    research/
    problems/
    problem-reviews/
    ideas/
    idea-reviews/
    idea-cards/
```

## 范围

这一版本只做 Idea 阶段。Creative 路线、Build、GitHub Repo、Pitch 和 Pitch Deck 均不在 v1 范围内。

## 测试

默认测试使用脚本化 Runner 和假的 Codex 可执行程序，不会调用付费模型：

```bash
python3 -m unittest discover -s tests -v
```
