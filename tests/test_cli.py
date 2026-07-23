from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from hacksome import cli


class _FakeWorkflow:
    create_calls: list[tuple[str, Path, object, object, str | None]] = []

    def __init__(self, run_dir: Path) -> None:
        self.run_dir = run_dir

    @classmethod
    def create(
        cls,
        challenge: str,
        runs_dir: Path,
        *,
        settings: object,
        codex_config: object,
        run_id: str | None,
    ) -> "_FakeWorkflow":
        cls.create_calls.append(
            (challenge, Path(runs_dir), settings, codex_config, run_id)
        )
        return cls(Path(runs_dir) / (run_id or "generated"))

    async def execute(self) -> Path:
        return self.run_dir / "artifacts" / "idea-cards" / "index.md"


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        _FakeWorkflow.create_calls.clear()

    def invoke(self, argv: list[str]) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = cli.main(argv)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_run_uses_v1_defaults_and_overrides(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(cli, "UsefulIdeaWorkflow", _FakeWorkflow):
                code, stdout, stderr = self.invoke(
                    [
                        "run",
                        "--prompt",
                        "Help a real user",
                        "--runs-dir",
                        directory,
                        "--run-id",
                        "cli-test",
                        "--max-audiences",
                        "4",
                        "--researchers-per-audience",
                        "2",
                        "--idea-generators-per-problem",
                        "6",
                    ]
                )
        self.assertEqual(code, 0)
        self.assertEqual(stderr, "")
        self.assertIn("Idea Cards:", stdout)
        prompt, _, settings, _, run_id = _FakeWorkflow.create_calls[0]
        self.assertEqual(prompt, "Help a real user")
        self.assertEqual(run_id, "cli-test")
        self.assertEqual(settings.max_audiences, 4)
        self.assertEqual(settings.researchers_per_audience, 2)
        self.assertEqual(settings.idea_generators_per_problem, 6)
        codex_config = _FakeWorkflow.create_calls[0][3]
        self.assertEqual(codex_config.model, "gpt-5.6-terra")
        self.assertEqual(codex_config.reasoning_effort, "high")

    def test_default_fanout_is_five_audiences_one_researcher_three_generators(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(cli, "UsefulIdeaWorkflow", _FakeWorkflow):
                code, _, _ = self.invoke(
                    ["run", "--prompt", "Prompt", "--runs-dir", directory]
                )
        self.assertEqual(code, 0)
        settings = _FakeWorkflow.create_calls[0][2]
        self.assertEqual(settings.max_audiences, 5)
        self.assertEqual(settings.researchers_per_audience, 1)
        self.assertEqual(settings.idea_generators_per_problem, 3)

    def test_model_and_reasoning_effort_can_be_overridden(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(cli, "UsefulIdeaWorkflow", _FakeWorkflow):
                code, _, _ = self.invoke(
                    [
                        "run",
                        "--prompt",
                        "Prompt",
                        "--runs-dir",
                        directory,
                        "--model",
                        "gpt-5.6-sol",
                        "--reasoning-effort",
                        "xhigh",
                    ]
                )
        self.assertEqual(code, 0)
        codex_config = _FakeWorkflow.create_calls[0][3]
        self.assertEqual(codex_config.model, "gpt-5.6-sol")
        self.assertEqual(codex_config.reasoning_effort, "xhigh")

    def test_challenge_file_is_read_as_utf8(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "challenge.md"
            path.write_text("真实赛题\n", encoding="utf-8")
            with patch.object(cli, "UsefulIdeaWorkflow", _FakeWorkflow):
                code, _, stderr = self.invoke(
                    ["run", str(path), "--runs-dir", directory]
                )
        self.assertEqual(code, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(_FakeWorkflow.create_calls[0][0], "真实赛题\n")

    def test_v1_rejects_more_than_five_audiences(self) -> None:
        with self.assertRaises(SystemExit) as raised:
            self.invoke(["run", "--prompt", "Prompt", "--max-audiences", "6"])
        self.assertEqual(raised.exception.code, 2)

    def test_resume_command_does_not_exist(self) -> None:
        with self.assertRaises(SystemExit) as raised:
            self.invoke(["resume", "runs/example"])
        self.assertEqual(raised.exception.code, 2)

    def test_status_and_validate_are_offline(self) -> None:
        status_payload = {
            "run_id": "run-1",
            "status": "completed",
            "current_stage": None,
            "task_counts": {"succeeded": 4},
            "decision_count": 2,
            "idea_card_count": 1,
        }
        with patch.object(cli, "inspect_run", return_value=status_payload):
            code, stdout, _ = self.invoke(["status", "runs/run-1"])
        self.assertEqual(code, 0)
        self.assertIn("Idea Cards: 1", stdout)

        with patch.object(cli, "validate_run", return_value=[]):
            code, stdout, _ = self.invoke(["validate", "runs/run-1"])
        self.assertEqual(code, 0)
        self.assertIn("Run is valid", stdout)


if __name__ == "__main__":
    unittest.main()
