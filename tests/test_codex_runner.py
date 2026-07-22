from __future__ import annotations

import asyncio
import json
import os
import stat
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

from hacksome.codex import CodexRunner
from hacksome.config import CodexConfig
from hacksome.models import CodexFailureKind, CodexRunStatus, CodexTask


FAKE_CODEX = r'''#!/usr/bin/env python3
import fcntl
import json
import os
import signal
import sys
import time
from pathlib import Path


args = sys.argv[1:]

if args == ["--version"]:
    print("codex-cli 0.fake")
    raise SystemExit(0)

if args == ["--help"]:
    print("--search --sandbox --cd")
    raise SystemExit(0)

if args == ["exec", "--help"]:
    print("--json --output-schema --output-last-message resume")
    raise SystemExit(0)

if args == ["login", "status"]:
    if os.environ.get("FAKE_CODEX_LOGIN_FAIL"):
        print("Not logged in", file=sys.stderr)
        raise SystemExit(1)
    print("Logged in")
    raise SystemExit(0)

prompt = sys.stdin.read()
cwd = Path.cwd()
calls_path = Path(os.environ["FAKE_CODEX_CALLS"])
with calls_path.open("a", encoding="utf-8") as calls:
    calls.write(json.dumps({"argv": args, "prompt": prompt, "cwd": str(cwd)}) + "\n")

attempt_file = cwd / ".fake-attempt"
try:
    attempt = int(attempt_file.read_text(encoding="utf-8")) + 1
except FileNotFoundError:
    attempt = 1
attempt_file.write_text(str(attempt), encoding="utf-8")

last_message = Path(args[args.index("--output-last-message") + 1])
mode = os.environ.get("FAKE_CODEX_MODE", "success")
is_resume = "resume" in args

if mode == "timeout":
    marker = Path(os.environ["FAKE_CODEX_TERM_MARKER"])
    def on_term(_signum, _frame):
        marker.write_text("term", encoding="utf-8")
    signal.signal(signal.SIGTERM, on_term)
    print(json.dumps({"type": "thread.started", "thread_id": "thread-timeout"}), flush=True)
    while True:
        time.sleep(0.05)

if mode == "concurrency":
    tracker_path = Path(os.environ["FAKE_CODEX_TRACKER"])
    tracker_path.touch(exist_ok=True)
    with tracker_path.open("r+", encoding="utf-8") as tracker:
        fcntl.flock(tracker, fcntl.LOCK_EX)
        raw = tracker.read()
        data = json.loads(raw) if raw else {"current": 0, "maximum": 0}
        data["current"] += 1
        data["maximum"] = max(data["maximum"], data["current"])
        tracker.seek(0)
        tracker.truncate()
        tracker.write(json.dumps(data))
        tracker.flush()
        fcntl.flock(tracker, fcntl.LOCK_UN)
    time.sleep(0.15)
    with tracker_path.open("r+", encoding="utf-8") as tracker:
        fcntl.flock(tracker, fcntl.LOCK_EX)
        data = json.loads(tracker.read())
        data["current"] -= 1
        tracker.seek(0)
        tracker.truncate()
        tracker.write(json.dumps(data))
        tracker.flush()
        fcntl.flock(tracker, fcntl.LOCK_UN)

if mode == "fail_once" and attempt == 1:
    print(json.dumps({"type": "thread.started", "thread_id": "thread-retry"}), flush=True)
    print(json.dumps({"type": "usage.partial", "usage": {"input_tokens": 3}}), flush=True)
    print("temporary transport failure", file=sys.stderr, flush=True)
    raise SystemExit(7)

if mode == "large_event":
    print(json.dumps({"type": "item.completed", "payload": "x" * (128 * 1024)}), flush=True)

thread_id = "thread-retry" if is_resume else f"thread-{cwd.name}"
print(json.dumps({"type": "thread.started", "thread_id": thread_id}), flush=True)
print(json.dumps({
    "type": "turn.completed",
    "usage": {"input_tokens": 5, "output_tokens": 2, "cached_input_tokens": 1},
}), flush=True)
print("fake diagnostic", file=sys.stderr, flush=True)
last_message.write_text(json.dumps({"status": "ok", "prompt": prompt}), encoding="utf-8")
'''


class CodexRunnerTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self._temporary = tempfile.TemporaryDirectory()
        self.root = Path(self._temporary.name)
        self.fake_codex = self.root / "fake-codex"
        self.fake_codex.write_text(textwrap.dedent(FAKE_CODEX), encoding="utf-8")
        self.fake_codex.chmod(
            self.fake_codex.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP
        )
        self.schema = self.root / "schema.json"
        self.schema.write_text(
            json.dumps({"type": "object", "required": ["status"]}),
            encoding="utf-8",
        )
        self.calls = self.root / "calls.jsonl"

    def tearDown(self) -> None:
        self._temporary.cleanup()

    def config(self, **overrides: object) -> CodexConfig:
        values: dict[str, object] = {
            "executable": str(self.fake_codex),
            "infrastructure_retries": 0,
            "termination_grace_seconds": 0.05,
        }
        values.update(overrides)
        return CodexConfig(**values)  # type: ignore[arg-type]

    def task(self, task_id: str = "task-1", **overrides: object) -> CodexTask:
        work_dir = self.root / task_id
        work_dir.mkdir(exist_ok=True)
        values: dict[str, object] = {
            "task_id": task_id,
            "prompt": "literal $(touch SHOULD_NOT_EXIST) `uname` prompt\n",
            "cwd": work_dir,
            "output_schema": self.schema,
        }
        values.update(overrides)
        return CodexTask(**values)  # type: ignore[arg-type]

    def fake_environment(self, **values: str):
        return patch.dict(
            os.environ,
            {"FAKE_CODEX_CALLS": str(self.calls), **values},
            clear=False,
        )

    def read_calls(self) -> list[dict[str, object]]:
        return [
            json.loads(line)
            for line in self.calls.read_text(encoding="utf-8").splitlines()
        ]

    async def test_run_uses_stdin_explicit_args_cwd_search_and_jsonl_logs(self) -> None:
        runner = CodexRunner(self.config())
        task = self.task(web_search=True)

        with self.fake_environment():
            result = await runner.run(task)

        self.assertTrue(result.success)
        self.assertEqual(result.status, CodexRunStatus.SUCCEEDED)
        self.assertEqual(result.session_id, "thread-task-1")
        self.assertEqual(result.structured_output["status"], "ok")
        self.assertEqual(result.usage["input_tokens"], 5)
        self.assertEqual(result.usage["output_tokens"], 2)
        self.assertEqual(result.attempts, 1)

        call = self.read_calls()[0]
        argv = call["argv"]
        self.assertIsInstance(argv, list)
        config_values = [
            argv[index + 1]
            for index, value in enumerate(argv[:-1])
            if value == "--config"
        ]
        self.assertIn('web_search="live"', config_values)
        self.assertNotIn("--search", argv)
        self.assertIn("--ask-for-approval", argv)
        self.assertIn("never", argv)
        self.assertIn("workspace-write", argv)
        self.assertEqual(call["cwd"], str(task.cwd.resolve()))
        self.assertEqual(call["prompt"], task.prompt)
        self.assertNotIn(task.prompt, argv)
        self.assertFalse((task.cwd / "SHOULD_NOT_EXIST").exists())

        stdout_records = [
            json.loads(line)
            for line in result.logs.stdout.read_text(encoding="utf-8").splitlines()
        ]
        stderr_records = [
            json.loads(line)
            for line in result.logs.stderr.read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual(stdout_records[0]["event"]["type"], "thread.started")
        self.assertTrue(any(row["type"] == "runner.stderr" for row in stderr_records))
        self.assertEqual(
            json.loads(result.logs.last_message.read_text(encoding="utf-8"))["status"],
            "ok",
        )

    async def test_run_explicitly_disables_web_search(self) -> None:
        runner = CodexRunner(self.config())

        with self.fake_environment():
            result = await runner.run(self.task(web_search=False))

        self.assertTrue(result.success)
        argv = self.read_calls()[0]["argv"]
        config_values = [
            argv[index + 1]
            for index, value in enumerate(argv[:-1])
            if value == "--config"
        ]
        self.assertIn('web_search="disabled"', config_values)
        self.assertNotIn('web_search="live"', config_values)

    async def test_large_jsonl_event_exceeds_asyncio_default_line_limit(self) -> None:
        runner = CodexRunner(self.config())

        with self.fake_environment(FAKE_CODEX_MODE="large_event"):
            result = await runner.run(self.task())

        self.assertTrue(result.success)
        records = [
            json.loads(line)
            for line in result.logs.stdout.read_text(encoding="utf-8").splitlines()
        ]
        large_event = next(
            record["event"]
            for record in records
            if record["event"]["type"] == "item.completed"
        )
        self.assertGreater(len(large_event["payload"]), 64 * 1024)

    def test_subprocess_stream_limit_has_a_safe_minimum(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least 65536"):
            self.config(subprocess_stream_limit_bytes=1024)

    async def test_infrastructure_retry_resumes_only_explicit_thread_id(self) -> None:
        runner = CodexRunner(self.config(infrastructure_retries=1))
        task = self.task()

        with self.fake_environment(FAKE_CODEX_MODE="fail_once"):
            result = await runner.run(task)

        self.assertTrue(result.success)
        self.assertEqual(result.attempts, 2)
        self.assertEqual(result.session_id, "thread-retry")
        self.assertEqual(result.usage["input_tokens"], 8)
        calls = self.read_calls()
        self.assertEqual(len(calls), 2)
        first_argv = calls[0]["argv"]
        second_argv = calls[1]["argv"]
        self.assertNotIn("resume", first_argv)
        resume_index = second_argv.index("resume")
        self.assertIn("thread-retry", second_argv[resume_index + 1 :])
        self.assertNotIn("--last", second_argv)
        self.assertEqual(calls[1]["prompt"], task.prompt)

    async def test_explicit_resume_uses_requested_session(self) -> None:
        runner = CodexRunner(self.config())
        task = self.task(session_id="known-thread", resume=True)

        with self.fake_environment():
            result = await runner.run(task)

        self.assertTrue(result.success)
        argv = self.read_calls()[0]["argv"]
        self.assertIn("resume", argv)
        self.assertIn("known-thread", argv)
        self.assertNotIn("--last", argv)

    async def test_semaphore_bounds_parallel_processes(self) -> None:
        tracker = self.root / "tracker.json"
        runner = CodexRunner(self.config(max_concurrency=2))
        tasks = [self.task(f"parallel-{index}") for index in range(4)]

        with self.fake_environment(
            FAKE_CODEX_MODE="concurrency",
            FAKE_CODEX_TRACKER=str(tracker),
        ):
            results = await asyncio.gather(*(runner.run(task) for task in tasks))

        self.assertTrue(all(result.success for result in results))
        tracker_data = json.loads(tracker.read_text(encoding="utf-8"))
        self.assertEqual(tracker_data["current"], 0)
        self.assertEqual(tracker_data["maximum"], 2)

    async def test_timeout_sends_term_then_kills_process_group(self) -> None:
        marker = self.root / "term-marker"
        runner = CodexRunner(self.config())
        # Leave enough startup time for the fake process to install its TERM
        # handler before exercising the runner's timeout path.
        task = self.task(timeout_seconds=0.4)

        with self.fake_environment(
            FAKE_CODEX_MODE="timeout",
            FAKE_CODEX_TERM_MARKER=str(marker),
        ):
            result = await runner.run(task)

        self.assertEqual(result.status, CodexRunStatus.TIMED_OUT)
        self.assertFalse(result.success)
        self.assertIsNotNone(result.error)
        self.assertEqual(result.error.kind, CodexFailureKind.TIMED_OUT)
        self.assertEqual(marker.read_text(encoding="utf-8"), "term")
        self.assertLess(result.duration_seconds, 1.5)

    async def test_doctor_reports_capabilities_and_login_failure(self) -> None:
        runner = CodexRunner(self.config())

        with self.fake_environment():
            healthy = await runner.doctor()
        self.assertTrue(healthy.healthy)
        self.assertEqual(healthy.version, "codex-cli 0.fake")
        self.assertTrue(all(healthy.capabilities.values()))

        with self.fake_environment(FAKE_CODEX_LOGIN_FAIL="1"):
            unhealthy = await runner.doctor()
        self.assertFalse(unhealthy.healthy)
        self.assertFalse(unhealthy.authenticated)
        self.assertIn("Not logged in", unhealthy.error or "")

    async def test_doctor_reports_missing_executable_without_raising(self) -> None:
        runner = CodexRunner(self.config(executable=str(self.root / "missing")))

        result = await runner.doctor()

        self.assertFalse(result.healthy)
        self.assertFalse(result.available)
        self.assertIn("not found", result.error or "")


if __name__ == "__main__":
    unittest.main()
