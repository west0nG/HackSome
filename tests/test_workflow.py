from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path
from typing import Any

from hacksome.artifacts import (
    STAGE_ARTIFACT_SPECS,
    ArtifactDocument,
    parse_markdown_file,
    serialize_markdown,
)
from hacksome.models import CodexLogs, CodexResult, CodexRunStatus, CodexTask
from hacksome.state import RunStatus, StateStore, TaskStatus
from hacksome.workflow import (
    UsefulIdeaWorkflow,
    WorkflowError,
    WorkflowSettings,
    validate_run,
)


_STAGE_RE = re.compile(r"^# (S(?:10|[0-9])) —", re.MULTILINE)
_RUN_ID_RE = re.compile(r"^- Run ID: ([^\n]+)$", re.MULTILINE)
_OUTPUT_TARGET_RE = re.compile(
    r"^- Assigned output target: ([^\n]+)$",
    re.MULTILINE,
)


class ScriptedRunner:
    """Offline CodexRunner replacement that still honors the artifact boundary."""

    def __init__(
        self,
        *,
        zero_audiences: bool = False,
        invalid_once_stage: str | None = None,
    ) -> None:
        self.zero_audiences = zero_audiences
        self.invalid_once_stage = invalid_once_stage
        self.calls: list[CodexTask] = []
        self.stages: list[str] = []

    async def run(self, task: CodexTask) -> CodexResult:
        self.calls.append(task)
        stage = self._match(_STAGE_RE, task.prompt, "stage")
        run_id = self._match(_RUN_ID_RE, task.prompt, "run id")
        self.stages.append(stage)
        call_number = len(self.calls)
        session_id = task.session_id or f"session-{call_number:03d}"

        if stage == "S0":
            structured_output = self._s0_output(run_id, task.task_id)
        elif stage == "S1":
            structured_output = self._s1_output(run_id, task.task_id)
        else:
            output_path = self._write_artifact(
                task=task,
                stage=stage,
                run_id=run_id,
                intentionally_invalid=(
                    stage == self.invalid_once_stage
                    and self.stages.count(stage) == 1
                ),
            )
            structured_output = {
                "schema_version": 1,
                "run_id": run_id,
                "task_id": task.task_id,
                "status": "completed",
                "output_paths": [output_path],
            }

        log_dir = task.log_dir or task.cwd / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        stdout = log_dir / "stdout.jsonl"
        stderr = log_dir / "stderr.log"
        last_message = log_dir / "last-message.json"
        stdout.write_text(
            json.dumps({"event": {"thread_id": session_id}}) + "\n",
            encoding="utf-8",
        )
        stderr.write_text("", encoding="utf-8")
        last_message.write_text(
            json.dumps(structured_output, ensure_ascii=False),
            encoding="utf-8",
        )
        timestamp = f"2026-07-23T00:00:{call_number:02d}+00:00"
        return CodexResult(
            task_id=task.task_id,
            status=CodexRunStatus.SUCCEEDED,
            session_id=session_id,
            structured_output=structured_output,
            usage={"input_tokens": 1, "output_tokens": 1},
            logs=CodexLogs(
                stdout=stdout,
                stderr=stderr,
                last_message=last_message,
            ),
            error=None,
            returncode=0,
            attempts=1,
            started_at=timestamp,
            finished_at=timestamp,
            duration_seconds=0.0,
        )

    @staticmethod
    def _match(pattern: re.Pattern[str], value: str, label: str) -> str:
        match = pattern.search(value)
        if match is None:
            raise AssertionError(f"scripted runner could not find {label} in prompt")
        return match.group(1).strip()

    @staticmethod
    def _s0_output(run_id: str, task_id: str) -> dict[str, Any]:
        sourced_fact = {"text": "24 hours", "source_excerpt": "24 hours"}
        challenge_brief = {
            "source_ref": "challenge.md",
            "title": "Community repair challenge",
            "summary": "Build a useful product for local communities.",
            "theme": "community tools",
            "problem_domains": ["local services"],
            "explicit_audiences": [],
            "judging_criteria": [],
            "hard_constraints": [],
            "allowed_technologies": [],
            "required_technologies": [],
            "sponsor_requirements": [],
            "time_limit": sourced_fact,
            "submission_format": [],
            "required_deliverables": [],
            "other_rules": [],
            "unknowns": [],
            "conflicts": [],
        }
        discovery_view = {
            "theme": "community tools",
            "problem_domains": ["local services"],
            "explicit_audiences": [],
            "nontechnical_boundaries": ["Must help a real user"],
            "unknowns": [],
        }
        compliance_view = {
            "required_technologies": [],
            "allowed_technologies": [],
            "sponsor_requirements": [],
            "time_limit": sourced_fact,
            "submission_format": [],
            "required_deliverables": [],
            "hard_rules": [],
            "unknowns": [],
            "conflicts": [],
        }
        return {
            "schema_version": 1,
            "run_id": run_id,
            "task_id": task_id,
            "input_language": "en",
            "challenge_brief": challenge_brief,
            "discovery_view": discovery_view,
            "compliance_view": compliance_view,
        }

    def _s1_output(self, run_id: str, task_id: str) -> dict[str, Any]:
        audiences = []
        if not self.zero_audiences:
            audiences.append(
                {
                    "audience_id": "audience-repair-workers",
                    "name": "Repair workers",
                    "kind": "profession",
                    "direct_relevance": "They participate in local services.",
                    "search_aliases": ["repair technician"],
                }
            )
        return {
            "schema_version": 1,
            "run_id": run_id,
            "task_id": task_id,
            "input_language": "en",
            "source_ref": "discovery-view.json",
            "audiences": audiences,
            "unknowns": [],
        }

    def _write_artifact(
        self,
        *,
        task: CodexTask,
        stage: str,
        run_id: str,
        intentionally_invalid: bool,
    ) -> str:
        manifest = json.loads(
            (task.cwd / "context-manifest.json").read_text(encoding="utf-8")
        )
        routing = manifest["routing"]
        output_target = self._match(_OUTPUT_TARGET_RE, task.prompt, "output target")
        if stage in {"S4", "S6"} and "path_pattern" in routing:
            output_path = str(routing["path_pattern"]).replace("NNN", "001")
        else:
            output_path = output_target

        metadata = self._metadata_for(
            stage=stage,
            run_id=run_id,
            routing=routing,
        )
        document = ArtifactDocument(
            metadata=metadata,
            body=self._body_for(
                stage,
                metadata["status"],
                omit_last_heading=intentionally_invalid,
            ),
        )
        destination = task.cwd / output_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(serialize_markdown(document), encoding="utf-8")
        return output_path

    @staticmethod
    def _metadata_for(
        *,
        stage: str,
        run_id: str,
        routing: dict[str, Any],
    ) -> dict[str, Any]:
        spec = STAGE_ARTIFACT_SPECS[stage]
        status = {
            "S2": "complete",
            "S3": "complete",
            "S4": "draft",
            "S5": "pass",
            "S6": "draft",
            "S7": "complete",
            "S8": "ready_for_review",
            "S9": "pass",
            "S10": "feasible",
        }[stage]
        metadata: dict[str, Any] = {
            "schema_version": 1,
            "artifact_id": routing.get(
                "artifact_id",
                "artifact-problem-001" if stage == "S4" else "artifact-idea-001",
            ),
            "artifact_type": spec.artifact_type,
            "run_id": run_id,
            "stage": stage,
            "status": status,
            "revision": routing.get("revision", 1),
            "created_by_session": routing.get(
                "original_created_by_session",
                "pending",
            ),
            "updated_by_session": "pending",
            "source_refs": list(routing["source_refs"]),
            "supersedes": routing.get("supersedes"),
        }
        local_defaults: dict[str, Any] = {
            "problem_id": "problem-001",
            "idea_id": "idea-001",
            "needs_second_verifier": False,
            "recheck_evidence_ids": [],
            "failed_thresholds": [],
            "evidence_gaps": [],
            "needs_competitor_research": False,
            "competitor_research_gaps": [],
        }
        for key in spec.required_metadata:
            if key in routing:
                metadata[key] = routing[key]
            elif key in local_defaults:
                metadata[key] = local_defaults[key]
            else:
                raise AssertionError(f"no scripted metadata value for {stage}.{key}")
        return metadata

    @staticmethod
    def _body_for(
        stage: str,
        status: str,
        *,
        omit_last_heading: bool = False,
    ) -> str:
        sections: list[str] = []
        headings = STAGE_ARTIFACT_SPECS[stage].required_headings
        if omit_last_heading:
            headings = headings[:-1]
        for heading in headings:
            if heading == "Decision":
                content = status
            elif heading == "Target User":
                content = "Repair workers"
            elif heading == "Problem":
                content = "Repeated intake transcription causes avoidable delays."
            elif heading == "Felt Value":
                content = "A worker immediately receives a usable structured job record."
            elif heading == "User Flow":
                content = (
                    "A worker submits a real voice note; the product extracts and "
                    "checks job details; the worker confirms a usable work order."
                )
            elif heading == "Deliverable Beta Scope":
                content = "One repeatable voice-note-to-work-order path with real input."
            elif heading == "Highest-Risk Dependencies":
                content = "Speech recognition quality for noisy recordings."
            else:
                content = f"Fixture evidence for {heading}."
            sections.extend((f"## {heading}", "", content, ""))
        return "\n".join(sections).rstrip() + "\n"


class UsefulIdeaWorkflowTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.runs_dir = Path(self.temporary.name)
        self.settings = WorkflowSettings(
            researchers_per_audience=1,
            problem_writers_per_audience=1,
            idea_generators_per_problem=1,
            task_timeout_seconds=30,
            run_timeout_seconds=60,
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def create_workflow(
        self,
        runner: ScriptedRunner,
        *,
        run_id: str,
    ) -> UsefulIdeaWorkflow:
        return UsefulIdeaWorkflow.create(
            "Build a useful tool for local communities in 24 hours.",
            self.runs_dir,
            settings=self.settings,
            runner=runner,  # type: ignore[arg-type]
            run_id=run_id,
        )

    async def test_complete_s0_s11_happy_path_uses_real_artifact_store(self) -> None:
        runner = ScriptedRunner()
        workflow = self.create_workflow(runner, run_id="run-workflow-happy")

        report_path = await workflow.execute()

        state = StateStore(workflow.run_dir).load()
        report = report_path.read_text(encoding="utf-8")
        self.assertEqual(state.status, RunStatus.COMPLETED)
        self.assertEqual(state.current_stage, "S11")
        self.assertEqual(
            state.data["stage_statuses"],
            {f"S{number}": "completed" for number in range(12)},
        )
        self.assertTrue(
            all(task.status is TaskStatus.COMPLETED for task in state.tasks.values())
        )
        self.assertEqual(runner.stages, [f"S{number}" for number in range(11)])
        self.assertEqual(
            {stage for stage, task in zip(runner.stages, runner.calls) if task.web_search},
            {"S2", "S3", "S7"},
        )
        self.assertIn("Repair workers", report)
        self.assertIn("voice-note-to-work-order", report)
        self.assertNotIn("No Idea passed", report)
        self.assertEqual(len(state.data["final_ideas"]), 1)
        self.assertEqual(validate_run(workflow.run_dir), [])

    async def test_valid_zero_audience_result_still_produces_zero_idea_report(self) -> None:
        runner = ScriptedRunner(zero_audiences=True)
        workflow = self.create_workflow(runner, run_id="run-workflow-empty")

        report_path = await workflow.execute()

        state = StateStore(workflow.run_dir).load()
        report = report_path.read_text(encoding="utf-8")
        self.assertEqual(runner.stages, ["S0", "S1"])
        self.assertEqual(state.status, RunStatus.COMPLETED)
        self.assertEqual(
            state.data["stage_statuses"],
            {f"S{number}": "completed" for number in range(12)},
        )
        self.assertEqual(state.data["final_ideas"], [])
        self.assertIn("No Idea passed", report)
        self.assertEqual(validate_run(workflow.run_dir), [])

    async def test_reexecuting_completed_run_is_idempotent(self) -> None:
        runner = ScriptedRunner()
        first = self.create_workflow(runner, run_id="run-workflow-resume")
        await first.execute()
        initial_call_count = len(runner.calls)
        initial_state = StateStore(first.run_dir).load().to_dict()
        initial_report = (first.run_dir / "idea-report.md").read_bytes()
        idea_path = next(first.run_dir.glob("ideas/**/*.md"))
        initial_idea = parse_markdown_file(idea_path)
        revision_paths = sorted((first.run_dir / "revisions").rglob("*.md"))
        initial_revisions = {
            path.relative_to(first.run_dir).as_posix(): path.read_bytes()
            for path in revision_paths
        }

        resumed = UsefulIdeaWorkflow(first.run_dir, runner=runner)  # type: ignore[arg-type]
        await resumed.execute()

        final_idea = parse_markdown_file(idea_path)
        final_revisions = {
            path.relative_to(first.run_dir).as_posix(): path.read_bytes()
            for path in sorted((first.run_dir / "revisions").rglob("*.md"))
        }
        self.assertEqual(len(runner.calls), initial_call_count)
        self.assertEqual(StateStore(first.run_dir).load().to_dict(), initial_state)
        self.assertEqual((first.run_dir / "idea-report.md").read_bytes(), initial_report)
        self.assertEqual(final_idea.revision, initial_idea.revision)
        self.assertEqual(final_idea.metadata, initial_idea.metadata)
        self.assertEqual(final_revisions, initial_revisions)
        self.assertEqual(validate_run(first.run_dir), [])

    async def test_invalid_staged_artifact_gets_one_same_session_correction(self) -> None:
        runner = ScriptedRunner(invalid_once_stage="S2")
        workflow = self.create_workflow(runner, run_id="run-workflow-correction")

        report_path = await workflow.execute()

        s2_calls = [
            task
            for stage, task in zip(runner.stages, runner.calls)
            if stage == "S2"
        ]
        self.assertEqual(len(s2_calls), 2)
        self.assertFalse(s2_calls[0].resume)
        self.assertTrue(s2_calls[1].resume)
        self.assertEqual(s2_calls[1].session_id, "session-003")
        self.assertTrue(report_path.is_file())
        self.assertEqual(validate_run(workflow.run_dir), [])

    async def test_completed_run_rejects_valid_looking_body_tampering(self) -> None:
        runner = ScriptedRunner()
        workflow = self.create_workflow(runner, run_id="run-workflow-tamper")
        await workflow.execute()
        research_path = next(workflow.run_dir.glob("research/**/*.md"))
        research_path.write_text(
            research_path.read_text(encoding="utf-8") + "\nUndeclared edit.\n",
            encoding="utf-8",
        )

        errors = validate_run(workflow.run_dir)

        self.assertTrue(any("content changed" in error for error in errors))
        resumed = UsefulIdeaWorkflow(workflow.run_dir, runner=runner)  # type: ignore[arg-type]
        with self.assertRaisesRegex(WorkflowError, "failed validation"):
            await resumed.execute()

    async def test_completed_run_rejects_raw_challenge_tampering(self) -> None:
        runner = ScriptedRunner()
        workflow = self.create_workflow(
            runner, run_id="run-workflow-challenge-tamper"
        )
        await workflow.execute()
        (workflow.run_dir / "challenge.md").write_text(
            "A different challenge.\n",
            encoding="utf-8",
        )

        errors = validate_run(workflow.run_dir)

        self.assertTrue(any("raw challenge content changed" in error for error in errors))
        resumed = UsefulIdeaWorkflow(
            workflow.run_dir, runner=runner  # type: ignore[arg-type]
        )
        with self.assertRaisesRegex(WorkflowError, "raw challenge content changed"):
            await resumed.execute()

    async def test_completed_run_rejects_report_tampering(self) -> None:
        runner = ScriptedRunner()
        workflow = self.create_workflow(
            runner, run_id="run-workflow-report-tamper"
        )
        await workflow.execute()
        report_path = workflow.run_dir / "idea-report.md"
        report_path.write_text(
            report_path.read_text(encoding="utf-8") + "\nUndeclared edit.\n",
            encoding="utf-8",
        )

        errors = validate_run(workflow.run_dir)

        self.assertTrue(any("final report content changed" in error for error in errors))
        resumed = UsefulIdeaWorkflow(
            workflow.run_dir, runner=runner  # type: ignore[arg-type]
        )
        with self.assertRaisesRegex(WorkflowError, "failed validation"):
            await resumed.execute()


if __name__ == "__main__":
    unittest.main()
