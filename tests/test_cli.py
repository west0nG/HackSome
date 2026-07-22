from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from hacksome import cli
from hacksome.models import CodexDoctorResult
from hacksome.workflow import WorkflowSettings


class _FakeWorkflow:
    create_calls: list[tuple[str, Path, object, object, str | None]] = []
    init_calls: list[tuple[Path, object | None]] = []

    def __init__(self, run_dir: Path, *, codex_config: object | None = None) -> None:
        self.run_dir = Path(run_dir).resolve()
        self.codex_config = codex_config
        self.init_calls.append((self.run_dir, codex_config))

    @classmethod
    def create(
        cls,
        prompt: str,
        runs_dir: Path,
        *,
        settings: object,
        codex_config: object,
        run_id: str | None,
    ) -> "_FakeWorkflow":
        cls.create_calls.append(
            (prompt, Path(runs_dir), settings, codex_config, run_id)
        )
        return cls(Path(runs_dir) / (run_id or "generated-run"))

    async def execute(self) -> Path:
        return self.run_dir / "idea-report.md"


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        _FakeWorkflow.create_calls.clear()
        _FakeWorkflow.init_calls.clear()

    def invoke(self, argv: list[str]) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = cli.main(argv)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_run_literal_prompt_passes_parallel_and_timeout_settings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(cli, "UsefulIdeaWorkflow", _FakeWorkflow):
                code, stdout, stderr = self.invoke(
                    [
                        "run",
                        "--prompt",
                        "Help neighborhood repair shops",
                        "--runs-dir",
                        directory,
                        "--run-id",
                        "run-cli-test",
                        "--max-concurrency",
                        "7",
                        "--model",
                        "codex-test-model",
                        "--task-timeout",
                        "45",
                        "--run-timeout",
                        "300",
                        "--researchers-per-audience",
                        "2",
                        "--problem-writers-per-audience",
                        "4",
                        "--idea-generators-per-problem",
                        "6",
                    ]
                )

        self.assertEqual(code, 0)
        self.assertEqual(stderr, "")
        self.assertIn("run-cli-test", stdout)
        self.assertIn("idea-report.md", stdout)
        prompt, runs_dir, settings, config, run_id = _FakeWorkflow.create_calls[0]
        self.assertEqual(prompt, "Help neighborhood repair shops")
        self.assertEqual(runs_dir, Path(directory))
        self.assertEqual(run_id, "run-cli-test")
        self.assertEqual(settings.researchers_per_audience, 2)
        self.assertEqual(settings.problem_writers_per_audience, 4)
        self.assertEqual(settings.idea_generators_per_problem, 6)
        self.assertEqual(settings.task_timeout_seconds, 45)
        self.assertEqual(settings.run_timeout_seconds, 300)
        self.assertEqual(config.max_concurrency, 7)
        self.assertEqual(config.model, "codex-test-model")
        self.assertEqual(config.default_timeout_seconds, 45)

    def test_run_reads_utf8_file_without_sending_a_model_request_in_test(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            challenge = Path(directory) / "challenge.md"
            challenge.write_text("为社区里的老人设计有用的工具\n", encoding="utf-8")
            with patch.object(cli, "UsefulIdeaWorkflow", _FakeWorkflow):
                code, _, stderr = self.invoke(
                    ["run", str(challenge), "--runs-dir", directory]
                )

        self.assertEqual(code, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(
            _FakeWorkflow.create_calls[0][0],
            "为社区里的老人设计有用的工具\n",
        )

    def test_run_requires_exactly_one_input(self) -> None:
        with self.assertRaises(SystemExit) as missing:
            self.invoke(["run"])
        self.assertEqual(missing.exception.code, 2)

        with self.assertRaises(SystemExit) as duplicate:
            self.invoke(["run", "challenge.md", "--prompt", "literal"])
        self.assertEqual(duplicate.exception.code, 2)

    def test_resume_without_overrides_lets_workflow_load_saved_settings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory) / "run-existing"
            with (
                patch.object(cli, "UsefulIdeaWorkflow", _FakeWorkflow),
                patch.object(
                    cli,
                    "_stored_settings",
                    side_effect=AssertionError("must not read settings separately"),
                ),
            ):
                code, stdout, stderr = self.invoke(["resume", str(run_dir)])

        self.assertEqual(code, 0)
        self.assertEqual(stderr, "")
        self.assertIn("Resuming:", stdout)
        self.assertEqual(_FakeWorkflow.init_calls[-1], (run_dir.resolve(), None))

    def test_resume_runtime_override_keeps_saved_workflow_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory) / "run-existing"
            saved = WorkflowSettings(task_timeout_seconds=91)
            saved_codex = cli.CodexConfig(
                executable="saved-codex",
                model="saved-model",
                infrastructure_retries=3,
            )
            with (
                patch.object(cli, "UsefulIdeaWorkflow", _FakeWorkflow),
                patch.object(cli, "_stored_settings", return_value=saved),
                patch.object(
                    cli, "_stored_codex_config", return_value=saved_codex
                ),
            ):
                code, _, stderr = self.invoke(
                    [
                        "resume",
                        str(run_dir),
                        "--max-concurrency",
                        "8",
                        "--model",
                        "resume-model",
                    ]
                )

        self.assertEqual(code, 0)
        self.assertEqual(stderr, "")
        config = _FakeWorkflow.init_calls[-1][1]
        self.assertIsNotNone(config)
        self.assertEqual(config.max_concurrency, 8)
        self.assertEqual(config.model, "resume-model")
        self.assertEqual(config.default_timeout_seconds, 91)
        self.assertEqual(config.executable, "saved-codex")
        self.assertEqual(config.infrastructure_retries, 3)

    def test_status_json_is_machine_readable(self) -> None:
        payload = {
            "run_id": "run-1",
            "status": "running",
            "current_stage": "S3",
            "task_counts": {"completed": 2, "running": 1},
            "completed_artifacts": [],
            "next_actions": ["resume"],
            "warnings": [],
            "final_idea_count": 0,
            "elimination_count": 0,
        }
        with patch.object(cli, "inspect_run", return_value=payload):
            code, stdout, stderr = self.invoke(["status", "some-run", "--json"])

        self.assertEqual(code, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(json.loads(stdout), payload)

    def test_status_human_output_includes_progress_and_warnings(self) -> None:
        payload = {
            "run_id": "run-2",
            "status": "failed",
            "current_stage": "S5",
            "task_counts": {"failed": 1, "completed": 4},
            "completed_artifacts": [],
            "next_actions": ["resume"],
            "warnings": ["one branch failed"],
            "final_idea_count": 1,
            "elimination_count": 2,
        }
        with patch.object(cli, "inspect_run", return_value=payload):
            code, stdout, stderr = self.invoke(["status", "some-run"])

        self.assertEqual(code, 0)
        self.assertEqual(stderr, "")
        self.assertIn("Current stage: S5", stdout)
        self.assertIn("completed=4, failed=1", stdout)
        self.assertIn("one branch failed", stdout)
        self.assertIn("resume", stdout)

    def test_validate_returns_nonzero_and_writes_errors_to_stderr(self) -> None:
        with patch.object(
            cli,
            "validate_run",
            return_value=["task-1: missing evidence.md"],
        ):
            code, stdout, stderr = self.invoke(["validate", "some-run"])

        self.assertEqual(code, 1)
        self.assertEqual(stdout, "")
        self.assertIn("Validation failed", stderr)
        self.assertIn("missing evidence.md", stderr)

    def test_validate_success(self) -> None:
        with patch.object(cli, "validate_run", return_value=[]):
            code, stdout, stderr = self.invoke(["validate", "some-run"])

        self.assertEqual(code, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(stdout, "Run is valid.\n")

    def test_doctor_only_calls_diagnostic_probe(self) -> None:
        instances: list[object] = []

        class FakeRunner:
            def __init__(self, config: object) -> None:
                self.config = config
                instances.append(self)

            async def doctor(self) -> CodexDoctorResult:
                return CodexDoctorResult(
                    executable="fake-codex",
                    available=True,
                    version="codex 1.test",
                    authenticated=True,
                    capabilities={"json_events": True},
                )

            async def run(self, _task: object) -> object:
                raise AssertionError("doctor must not start a model task")

        with patch.object(cli, "CodexRunner", FakeRunner):
            code, stdout, stderr = self.invoke(
                ["doctor", "--codex", "fake-codex", "--json"]
            )

        self.assertEqual(code, 0)
        self.assertEqual(stderr, "")
        payload = json.loads(stdout)
        self.assertTrue(payload["healthy"])
        self.assertEqual(instances[0].config.executable, "fake-codex")

    def test_doctor_unhealthy_returns_nonzero(self) -> None:
        class FakeRunner:
            def __init__(self, _config: object) -> None:
                pass

            async def doctor(self) -> CodexDoctorResult:
                return CodexDoctorResult(
                    executable="missing-codex",
                    available=False,
                    error="not found",
                )

        with patch.object(cli, "CodexRunner", FakeRunner):
            code, stdout, stderr = self.invoke(["doctor"])

        self.assertEqual(code, 1)
        self.assertEqual(stderr, "")
        self.assertIn("Codex: unhealthy", stdout)
        self.assertIn("not found", stdout)


if __name__ == "__main__":
    unittest.main()
