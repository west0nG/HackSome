from __future__ import annotations

import asyncio
import hashlib
import json
import re
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

from hacksome.artifacts import (
    STAGE_ARTIFACT_SPECS,
    ArtifactDocument,
    parse_markdown_file,
    serialize_markdown,
)
from hacksome.config import CodexConfig
from hacksome.models import CodexLogs, CodexResult, CodexRunStatus, CodexTask
from hacksome.state import RunStatus, StateStore, TaskRecord, TaskStatus
from hacksome.workflow import (
    TaskExecutionError,
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


class SimulatedInterruption(BaseException):
    """Models process loss without entering the workflow's retry handling."""


class ScriptedRunner:
    """Offline CodexRunner replacement that still honors the artifact boundary."""

    def __init__(
        self,
        *,
        zero_audiences: bool = False,
        invalid_once_stage: str | None = None,
        verification_recheck_ids: tuple[str, ...] = (),
        problem_evidence_citations: tuple[str, ...] | None = None,
        problem_counterevidence_citations: tuple[str, ...] = (),
        cite_latest_research_on_revision: bool = False,
        blind_verification_covers_recheck: bool = True,
        s5_statuses: dict[str, str] | None = None,
        s9_statuses: dict[str, str] | None = None,
    ) -> None:
        self.zero_audiences = zero_audiences
        self.invalid_once_stage = invalid_once_stage
        self.verification_recheck_ids = verification_recheck_ids
        self.problem_evidence_citations = problem_evidence_citations
        self.problem_counterevidence_citations = problem_counterevidence_citations
        self.cite_latest_research_on_revision = cite_latest_research_on_revision
        self.blind_verification_covers_recheck = blind_verification_covers_recheck
        self.s5_statuses = dict(s5_statuses or {})
        self.s9_statuses = dict(s9_statuses or {})
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
                    stage == self.invalid_once_stage and self.stages.count(stage) == 1
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
        if stage == "S4" and "assigned_paths" in routing:
            output_path = str(routing["assigned_paths"][0])
        elif stage in {"S4", "S6"} and "path_pattern" in routing:
            output_path = str(routing["path_pattern"]).replace("NNN", "001")
        else:
            output_path = output_target

        metadata = self._metadata_for(
            stage=stage,
            run_id=run_id,
            routing=routing,
        )
        if stage == "S5":
            gateway_mode = str(routing["gateway_mode"])
            metadata["status"] = self.s5_statuses.get(
                gateway_mode, str(metadata["status"])
            )
            if metadata["status"] == "reject_candidate":
                metadata["failed_thresholds"] = ["T1"]
                metadata["evidence_gaps"] = []
            elif metadata["status"] == "needs_evidence":
                metadata["failed_thresholds"] = []
                metadata["evidence_gaps"] = ["Find one more first-hand source."]
        if stage == "S9":
            review_mode = str(routing["review_mode"])
            metadata["status"] = self.s9_statuses.get(
                review_mode, str(metadata["status"])
            )
            for key in ("reviewed_idea_revision", "reviewed_idea_sha256"):
                if key in routing:
                    metadata[key] = routing[key]
        if stage == "S3" and self.verification_recheck_ids:
            if routing["verification_round"] == 1:
                metadata["needs_second_verifier"] = True
                metadata["recheck_evidence_ids"] = list(self.verification_recheck_ids)
            else:
                metadata["needs_second_verifier"] = False
                metadata["recheck_evidence_ids"] = []
        document = ArtifactDocument(
            metadata=metadata,
            body=self._body_for(
                stage,
                metadata["status"],
                routing=routing,
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

    def _body_for(
        self,
        stage: str,
        status: str,
        *,
        routing: dict[str, Any] | None = None,
        omit_last_heading: bool = False,
    ) -> str:
        sections: list[str] = []
        headings = STAGE_ARTIFACT_SPECS[stage].required_headings
        if omit_last_heading:
            headings = headings[:-1]
        for heading in headings:
            if heading == "Decision":
                content = status
            elif heading == "Evidence Candidates":
                content = (
                    "### evidence-001\n\n"
                    "Fixture first-hand evidence with a repeated workaround."
                )
            elif heading == "Evidence Checks":
                covered_ids = {"evidence-001", *self.verification_recheck_ids}
                if (
                    routing is not None
                    and routing.get("verification_round") == 2
                    and not self.blind_verification_covers_recheck
                ):
                    covered_ids = {"different-evidence-id"}
                content = "\n\n".join(
                    f"### {evidence_id}\n\nVerdict: supported"
                    for evidence_id in sorted(covered_ids)
                )
            elif heading == "Evidence" and stage == "S4":
                citations = self.problem_evidence_citations
                if citations is None:
                    citations = self._default_problem_citations(routing)
                content = "\n".join(citations) if citations else "None"
            elif heading == "Counterevidence and Uncertainty" and stage == "S4":
                content = (
                    "\n".join(self.problem_counterevidence_citations)
                    if self.problem_counterevidence_citations
                    else "No cited counterevidence."
                )
            elif heading == "Target User":
                content = "Repair workers"
            elif heading == "Problem":
                content = "Repeated intake transcription causes avoidable delays."
            elif heading == "Felt Value":
                content = (
                    "A worker immediately receives a usable structured job record."
                )
            elif heading == "User Flow":
                content = (
                    "A worker submits a real voice note; the product extracts and "
                    "checks job details; the worker confirms a usable work order."
                )
            elif heading == "Deliverable Beta Scope":
                content = (
                    "One repeatable voice-note-to-work-order path with real input."
                )
            elif heading == "Highest-Risk Dependencies":
                content = "Speech recognition quality for noisy recordings."
            else:
                content = f"Fixture evidence for {heading}."
            sections.extend((f"## {heading}", "", content, ""))
        return "\n".join(sections).rstrip() + "\n"

    def _default_problem_citations(
        self,
        routing: dict[str, Any] | None,
    ) -> tuple[str, ...]:
        source_refs = (
            list(routing.get("source_refs", [])) if routing is not None else []
        )
        research_refs = [
            str(ref) for ref in source_refs if str(ref).startswith("research/")
        ]
        if not research_refs:
            research_refs = ["research/audience-repair-workers/researcher-001.md"]
        research_ref = (
            research_refs[-1]
            if self.cite_latest_research_on_revision
            and routing is not None
            and routing.get("revision", 1) > 1
            else research_refs[0]
        )
        research_path = Path(research_ref)
        verification_prefix = (
            f"verification/{research_path.parent.name}/{research_path.stem}/"
        )
        verification_refs = [
            str(ref) for ref in source_refs if str(ref).startswith(verification_prefix)
        ]
        if not verification_refs:
            verification_refs = [f"{verification_prefix}verifier-001.md"]
            if self.verification_recheck_ids:
                verification_refs.append(f"{verification_prefix}verifier-002.md")
        joined = " | ".join(verification_refs)
        return (f"- Fixture claim: {research_ref}#evidence-001 | {joined}",)


class BlockingDraftScreenRunner(ScriptedRunner):
    """Fake runner that exposes how many draft screens reached execution."""

    def __init__(self, *, first_wave_size: int) -> None:
        super().__init__()
        self.first_wave_size = first_wave_size
        self.draft_screen_starts: list[str] = []
        self.first_wave_started = asyncio.Event()
        self.next_candidate_started = asyncio.Event()
        self._draft_screen_releases = asyncio.Semaphore(0)

    async def run(self, task: CodexTask) -> CodexResult:
        if "- Mode: draft_screen" in task.prompt:
            self.draft_screen_starts.append(task.task_id)
            started = len(self.draft_screen_starts)
            if started == self.first_wave_size:
                self.first_wave_started.set()
            elif started == self.first_wave_size + 1:
                self.next_candidate_started.set()
            await self._draft_screen_releases.acquire()
        return await super().run(task)

    def release_draft_screens(self, count: int = 1) -> None:
        for _ in range(count):
            self._draft_screen_releases.release()


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

    async def stage_one_problem(
        self,
        runner: ScriptedRunner,
        *,
        run_id: str,
    ) -> tuple[
        UsefulIdeaWorkflow,
        dict[str, Any],
        dict[str, Any],
        str,
        list[str],
        list[str],
    ]:
        workflow = self.create_workflow(runner, run_id=run_id)
        brief = dict(await workflow._stage_s0())
        audiences = await workflow._stage_s1(brief)
        audience = dict(audiences[0])
        research, verifications = await workflow._stage_s2_s3(brief, audiences)
        problems = await workflow._stage_s4(
            brief,
            audiences,
            research,
            verifications,
        )
        audience_id = str(audience["audience_id"])
        return (
            workflow,
            brief,
            audience,
            problems[0],
            list(research[audience_id]),
            list(verifications[audience_id]),
        )

    async def stage_one_idea(
        self,
        runner: ScriptedRunner,
        *,
        run_id: str,
    ) -> tuple[UsefulIdeaWorkflow, dict[str, Any], Any, str]:
        (
            workflow,
            brief,
            audience,
            problem_ref,
            research_refs,
            verification_refs,
        ) = await self.stage_one_problem(runner, run_id=run_id)
        passed = await workflow._process_problem(
            brief=brief,
            audience=audience,
            problem_ref=problem_ref,
            research_refs=research_refs,
            verification_refs=verification_refs,
        )
        self.assertIsNotNone(passed)
        assert passed is not None
        ideas = await workflow._stage_s6(brief, [passed])
        self.assertEqual(len(ideas), 1)
        return workflow, brief, passed, ideas[0]

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
        self.assertEqual(
            runner.stages,
            ["S0", "S1", "S2", "S3", "S4", "S5", "S6", "S9", "S7", "S8", "S9", "S10"],
        )
        self.assertEqual(
            {
                stage
                for stage, task in zip(runner.stages, runner.calls)
                if task.web_search
            },
            {"S2", "S3", "S7"},
        )
        s5_task = next(
            task for stage, task in zip(runner.stages, runner.calls) if stage == "S5"
        )
        s5_manifest = json.loads(
            (s5_task.cwd / "context-manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            s5_manifest["inputs"][0]["artifact_type"],
            "discovery_view",
        )
        self.assertIn(
            "discovery-view.json",
            s5_manifest["routing"]["source_refs"],
        )
        self.assertEqual(
            s5_manifest["routing"]["source_refs"],
            [
                "problems/audience-repair-workers/writer-001/problem-001.md",
                "discovery-view.json",
                "research/audience-repair-workers/researcher-001.md",
                ("verification/audience-repair-workers/researcher-001/verifier-001.md"),
            ],
        )
        self.assertIn("Repair workers", report)
        self.assertIn("voice-note-to-work-order", report)
        self.assertNotIn("No Idea passed", report)
        self.assertEqual(len(state.data["final_ideas"]), 1)
        self.assertEqual(validate_run(workflow.run_dir), [])

    async def test_draft_screen_invalid_stops_before_competition(self) -> None:
        runner = ScriptedRunner(s9_statuses={"draft_screen": "invalid"})
        workflow = self.create_workflow(
            runner,
            run_id="run-workflow-draft-screen-invalid",
        )

        report_path = await workflow.execute()

        state_store = StateStore(workflow.run_dir)
        state = state_store.load()
        self.assertEqual(state.data["workflow_topology_version"], 2)
        self.assertEqual(state.data["draft_screen_policy_version"], 3)
        self.assertEqual(state.data["final_ideas"], [])
        self.assertFalse(
            any(task.stage in {"S7", "S8", "S10"} for task in state.tasks.values())
        )
        screens = [
            task
            for task in state.tasks.values()
            if task.stage == "S9" and task.data.get("mode") == "draft_screen"
        ]
        self.assertEqual(len(screens), 1)
        self.assertTrue(screens[0].outputs[0].endswith("/draft-screen-003.md"))
        eliminations = [
            decision
            for decision in state_store.decisions()
            if decision.get("type") == "elimination"
        ]
        self.assertEqual(len(eliminations), 1)
        self.assertEqual(eliminations[0]["rule"], "draft-product-invalid")
        self.assertEqual(eliminations[0]["decision_refs"], screens[0].outputs)
        self.assertIn("draft-screen-003.md", report_path.read_text(encoding="utf-8"))
        self.assertEqual(validate_run(workflow.run_dir), [])

    async def test_draft_screen_preparation_uses_codex_concurrency_bound(
        self,
    ) -> None:
        max_concurrency = 2
        candidate_count = 5
        settings = WorkflowSettings(
            researchers_per_audience=1,
            problem_writers_per_audience=1,
            idea_generators_per_problem=candidate_count,
            task_timeout_seconds=30,
            run_timeout_seconds=60,
        )
        runner = BlockingDraftScreenRunner(first_wave_size=max_concurrency)
        workflow = UsefulIdeaWorkflow.create(
            "Build a useful tool for local communities in 24 hours.",
            self.runs_dir,
            settings=settings,
            codex_config=CodexConfig(max_concurrency=max_concurrency),
            runner=runner,  # type: ignore[arg-type]
            run_id="run-workflow-bounded-draft-screens",
        )
        brief = await workflow._stage_s0()
        audiences = await workflow._stage_s1(brief)
        research, verifications = await workflow._stage_s2_s3(brief, audiences)
        problems = await workflow._stage_s4(
            brief,
            audiences,
            research,
            verifications,
        )
        passed = await workflow._stage_s5(
            brief,
            audiences,
            problems,
            research,
            verifications,
        )
        ideas = await workflow._stage_s6(brief, passed)
        self.assertEqual(len(ideas), candidate_count)

        preparation_starts: list[str] = []
        original_binding = workflow._draft_screen_idea_binding

        def record_draft_preparation(*, idea_ref: str, task_id: str) -> tuple[int, str]:
            preparation_starts.append(idea_ref)
            return original_binding(idea_ref=idea_ref, task_id=task_id)

        binding_patch = patch.object(
            workflow,
            "_draft_screen_idea_binding",
            side_effect=record_draft_preparation,
        )
        binding_patch.start()
        self.addCleanup(binding_patch.stop)
        stage_task = asyncio.create_task(workflow._stage_s7_s10(brief, ideas, passed))
        await asyncio.wait_for(runner.first_wave_started.wait(), timeout=2)
        await asyncio.sleep(0)

        first_wave = StateStore(workflow.run_dir).load()
        prepared = [
            task
            for task in first_wave.tasks.values()
            if task.stage == "S9" and task.data.get("mode") == "draft_screen"
        ]
        self.assertEqual(len(preparation_starts), max_concurrency)
        self.assertEqual(len(runner.draft_screen_starts), max_concurrency)
        self.assertEqual(len(prepared), max_concurrency)
        self.assertTrue(all(task.status is TaskStatus.RUNNING for task in prepared))

        runner.release_draft_screens()
        await asyncio.wait_for(runner.next_candidate_started.wait(), timeout=2)
        await asyncio.sleep(0)
        after_one_slot = StateStore(workflow.run_dir).load()
        prepared_after_one_slot = [
            task
            for task in after_one_slot.tasks.values()
            if task.stage == "S9" and task.data.get("mode") == "draft_screen"
        ]
        self.assertEqual(len(preparation_starts), max_concurrency + 1)
        self.assertEqual(len(prepared_after_one_slot), max_concurrency + 1)
        self.assertLess(len(prepared_after_one_slot), candidate_count)
        self.assertEqual(
            sum(task.status is TaskStatus.RUNNING for task in prepared_after_one_slot),
            max_concurrency,
        )

        runner.release_draft_screens(candidate_count)
        finals = await asyncio.wait_for(stage_task, timeout=10)
        self.assertEqual(len(finals), candidate_count)

    async def test_repairable_draft_keeps_full_product_repair_and_provenance(
        self,
    ) -> None:
        runner = ScriptedRunner(
            s9_statuses={
                "draft_screen": "repairable",
                "initial": "repairable",
                "product_recheck": "pass",
            }
        )
        workflow = self.create_workflow(
            runner,
            run_id="run-workflow-draft-and-product-repair",
        )

        report_path = await workflow.execute()

        state_store = StateStore(workflow.run_dir)
        state = state_store.load()
        self.assertEqual(len(state.data["final_ideas"]), 1)
        final = state.data["final_ideas"][0]
        self.assertIsInstance(final, dict)
        idea_ref = str(final["idea_ref"])
        draft_screen_ref = str(final["draft_screen_ref"])
        self.assertTrue(draft_screen_ref.endswith("/draft-screen-003.md"))

        s8_modes = [
            str(task.data.get("mode"))
            for task in state.tasks.values()
            if task.stage == "S8"
        ]
        self.assertEqual(
            sorted(s8_modes),
            ["competition_revision", "product_repair"],
        )
        s9_tasks = [task for task in state.tasks.values() if task.stage == "S9"]
        self.assertEqual(
            {str(task.data.get("mode")) for task in s9_tasks},
            {"draft_screen", "initial", "product_recheck"},
        )
        self.assertEqual(len({task.task_id for task in s9_tasks}), 3)
        self.assertEqual(len({task.session_id for task in s9_tasks}), 3)
        self.assertEqual(len({task.outputs[0] for task in s9_tasks}), 3)
        self.assertTrue(
            any(task.outputs[0].endswith("/red-team-001.md") for task in s9_tasks)
        )
        self.assertTrue(
            any(task.outputs[0].endswith("/red-team-002.md") for task in s9_tasks)
        )

        for task in s9_tasks:
            manifest = task.data["context_manifest"]
            self.assertIsInstance(manifest, dict)
            if task.data.get("mode") == "draft_screen":
                self.assertFalse(
                    any(
                        artifact["artifact_type"] == "competition"
                        for artifact in manifest["artifacts"]
                    )
                )
                continue
            self.assertNotIn(
                draft_screen_ref,
                manifest["routing"]["source_refs"],
            )
            self.assertFalse(
                any(
                    artifact["artifact_type"] == "idea_red_team"
                    for artifact in manifest["artifacts"]
                )
            )

        draft_screen = parse_markdown_file(workflow.run_dir / draft_screen_ref)
        reviewed_revision = draft_screen.metadata["reviewed_idea_revision"]
        reviewed_sha256 = draft_screen.metadata["reviewed_idea_sha256"]
        self.assertEqual(reviewed_revision, 1)
        snapshot_ref = workflow.artifacts.snapshot_relative_path(
            idea_ref,
            reviewed_revision,
        )
        snapshot = workflow.run_dir / snapshot_ref
        self.assertTrue(snapshot.is_file())
        self.assertEqual(
            hashlib.sha256(snapshot.read_bytes()).hexdigest(),
            reviewed_sha256,
        )
        self.assertEqual(parse_markdown_file(snapshot).metadata["stage"], "S6")

        decisions = [
            decision
            for decision in state_store.decisions()
            if decision.get("candidate_ref") == idea_ref
        ]
        self.assertEqual(
            [decision["action"] for decision in decisions],
            ["product-repair", "accept-idea"],
        )
        report = report_path.read_text(encoding="utf-8")
        self.assertIn("draft-screen-003.md", report)
        self.assertIn("red-team-002.md", report)
        self.assertIn("review-001.md", report)
        self.assertEqual(validate_run(workflow.run_dir), [])

    async def test_passing_draft_can_still_fail_the_full_red_team(self) -> None:
        runner = ScriptedRunner(
            s9_statuses={"draft_screen": "pass", "initial": "invalid"}
        )
        workflow = self.create_workflow(
            runner,
            run_id="run-workflow-full-red-team-invalid",
        )

        await workflow.execute()

        state_store = StateStore(workflow.run_dir)
        state = state_store.load()
        self.assertEqual(state.data["final_ideas"], [])
        self.assertFalse(any(task.stage == "S10" for task in state.tasks.values()))
        s9_by_mode = {
            str(task.data.get("mode")): task
            for task in state.tasks.values()
            if task.stage == "S9"
        }
        self.assertEqual(set(s9_by_mode), {"draft_screen", "initial"})
        elimination = next(
            decision
            for decision in state_store.decisions()
            if decision.get("type") == "elimination"
        )
        self.assertEqual(elimination["rule"], "product-invalid")
        self.assertEqual(
            elimination["decision_refs"],
            s9_by_mode["initial"].outputs,
        )
        self.assertNotEqual(
            elimination["decision_refs"],
            s9_by_mode["draft_screen"].outputs,
        )

    async def test_draft_screen_execution_failure_is_resumable_not_elimination(
        self,
    ) -> None:
        runner = ScriptedRunner()
        workflow = self.create_workflow(
            runner,
            run_id="run-workflow-draft-screen-execution-failure",
        )

        with patch.object(
            workflow,
            "_run_draft_screen",
            side_effect=TaskExecutionError("temporary draft-screen failure"),
        ):
            with self.assertRaisesRegex(WorkflowError, "resume can retry"):
                await workflow.execute()

        failed_state = StateStore(workflow.run_dir).load()
        self.assertIs(failed_state.status, RunStatus.FAILED)
        self.assertEqual(failed_state.data["eliminations"], [])
        resumed = UsefulIdeaWorkflow(
            workflow.run_dir,
            runner=runner,  # type: ignore[arg-type]
        )

        report_path = await resumed.execute()

        completed_state = StateStore(workflow.run_dir).load()
        self.assertIs(completed_state.status, RunStatus.COMPLETED)
        self.assertEqual(completed_state.data["eliminations"], [])
        self.assertTrue(report_path.is_file())

    async def test_draft_screen_resume_reuses_review_and_snapshot_binding(self) -> None:
        runner = ScriptedRunner()
        workflow, brief, passed, idea_ref = await self.stage_one_idea(
            runner,
            run_id="run-workflow-draft-screen-resume",
        )
        first_screen = await workflow._run_draft_screen(
            idea_ref=idea_ref,
            passed=passed,
        )
        calls_after_screen = len(runner.calls)

        resumed = UsefulIdeaWorkflow(
            workflow.run_dir,
            runner=runner,  # type: ignore[arg-type]
        )
        first_finals = await resumed._stage_s7_s10(brief, [idea_ref], [passed])
        self.assertEqual(len(first_finals), 1)
        screen_calls = [
            call
            for stage, call in zip(runner.stages, runner.calls)
            if stage == "S9"
            and json.loads(
                (call.cwd / "context-manifest.json").read_text(encoding="utf-8")
            )["routing"]["review_mode"]
            == "draft_screen"
        ]
        self.assertEqual(len(screen_calls), 1)
        self.assertGreater(len(runner.calls), calls_after_screen)
        calls_after_first_finish = len(runner.calls)

        resumed_again = UsefulIdeaWorkflow(
            workflow.run_dir,
            runner=runner,  # type: ignore[arg-type]
        )
        second_finals = await resumed_again._stage_s7_s10(
            brief,
            [idea_ref],
            [passed],
        )

        self.assertEqual(len(runner.calls), calls_after_first_finish)
        self.assertEqual(first_finals, second_finals)
        self.assertEqual(
            first_finals[0].draft_screen_ref,
            first_screen.output_paths[0],
        )
        self.assertEqual(validate_run(workflow.run_dir), [])

    async def test_validate_rejects_tampered_draft_screen_context_copy(self) -> None:
        runner = ScriptedRunner()
        workflow = self.create_workflow(
            runner,
            run_id="run-workflow-draft-context-tamper",
        )
        await workflow.execute()
        state = StateStore(workflow.run_dir).load()
        screen_task = next(
            task
            for task in state.tasks.values()
            if task.stage == "S9" and task.data.get("mode") == "draft_screen"
        )
        manifest = screen_task.data["context_manifest"]
        self.assertIsInstance(manifest, dict)
        idea_entry = next(
            artifact
            for artifact in manifest["artifacts"]
            if artifact["canonical_ref"].startswith("ideas/")
        )
        copied_idea = (
            workflow.run_dir
            / ".staging"
            / screen_task.task_id
            / idea_entry["relative_path"]
        )
        copied_idea.write_text(
            copied_idea.read_text(encoding="utf-8") + "\nTampered.\n",
            encoding="utf-8",
        )
        tampered_sha256 = hashlib.sha256(copied_idea.read_bytes()).hexdigest()

        def forge_context_binding(current: Any) -> None:
            task = current.tasks[screen_task.task_id]
            saved = task.data["context_manifest"]
            saved["routing"]["reviewed_idea_sha256"] = tampered_sha256
            saved_entry = next(
                artifact
                for artifact in saved["artifacts"]
                if artifact["canonical_ref"].startswith("ideas/")
            )
            saved_entry["sha256"] = tampered_sha256

        StateStore(workflow.run_dir).mutate(forge_context_binding)

        errors = validate_run(workflow.run_dir)

        self.assertTrue(
            any(
                "draft screen context and review bind different hashes" in error
                for error in errors
            )
        )
        resumed = UsefulIdeaWorkflow(
            workflow.run_dir,
            runner=runner,  # type: ignore[arg-type]
        )
        with self.assertRaisesRegex(WorkflowError, "failed validation"):
            await resumed.execute()

    async def test_draft_screen_can_rerun_from_s6_snapshot_after_s8(self) -> None:
        runner = ScriptedRunner()
        workflow, brief, passed, idea_ref = await self.stage_one_idea(
            runner,
            run_id="run-workflow-draft-rerun-from-snapshot",
        )
        finals = await workflow._stage_s7_s10(brief, [idea_ref], [passed])
        self.assertEqual(len(finals), 1)
        draft_screen_ref = finals[0].draft_screen_ref
        self.assertIsNotNone(draft_screen_ref)
        assert draft_screen_ref is not None
        state = StateStore(workflow.run_dir).load()
        screen_task = next(
            task
            for task in state.tasks.values()
            if task.stage == "S9" and task.data.get("mode") == "draft_screen"
        )
        manifest = screen_task.data["context_manifest"]
        self.assertIsInstance(manifest, dict)
        idea_entry = next(
            artifact
            for artifact in manifest["artifacts"]
            if artifact["canonical_ref"] == idea_ref
        )
        copied_idea = (
            workflow.run_dir
            / ".staging"
            / screen_task.task_id
            / idea_entry["relative_path"]
        )
        (workflow.run_dir / draft_screen_ref).unlink()
        copied_idea.unlink()
        calls_before_rerun = len(runner.calls)

        rerun = await workflow._run_draft_screen(
            idea_ref=idea_ref,
            passed=passed,
        )

        self.assertEqual(rerun.output_paths, (draft_screen_ref,))
        self.assertEqual(len(runner.calls), calls_before_rerun + 1)
        rerun_state = StateStore(workflow.run_dir).load()
        rerun_task = rerun_state.tasks[screen_task.task_id]
        rerun_manifest = rerun_task.data["context_manifest"]
        rerun_idea_entry = next(
            artifact
            for artifact in rerun_manifest["artifacts"]
            if artifact["canonical_ref"] == idea_ref
        )
        rerun_copy = (
            workflow.run_dir
            / ".staging"
            / rerun_task.task_id
            / rerun_idea_entry["relative_path"]
        )
        copied_document = parse_markdown_file(rerun_copy)
        self.assertEqual(copied_document.metadata["stage"], "S6")
        self.assertEqual(copied_document.revision, 1)
        self.assertEqual(
            hashlib.sha256(rerun_copy.read_bytes()).hexdigest(),
            rerun_manifest["routing"]["reviewed_idea_sha256"],
        )
        self.assertEqual(validate_run(workflow.run_dir), [])

    async def test_resume_fails_closed_when_s6_snapshot_is_damaged_after_s8(
        self,
    ) -> None:
        for damage in ("delete", "tamper"):
            with self.subTest(damage=damage):
                runner = ScriptedRunner()
                workflow = self.create_workflow(
                    runner,
                    run_id=f"run-workflow-s6-snapshot-{damage}",
                )
                with patch.object(
                    workflow,
                    "_run_red_team",
                    side_effect=SimulatedInterruption("interrupted after S8 revision"),
                ):
                    with self.assertRaisesRegex(
                        SimulatedInterruption,
                        "interrupted after S8 revision",
                    ):
                        await workflow.execute()

                interrupted = StateStore(workflow.run_dir).load()
                s6_task = next(
                    task for task in interrupted.tasks.values() if task.stage == "S6"
                )
                idea_ref = s6_task.outputs[0]
                idea = parse_markdown_file(workflow.run_dir / idea_ref)
                self.assertEqual(idea.metadata["stage"], "S8")
                self.assertEqual(idea.revision, 2)
                snapshot_ref = workflow.artifacts.snapshot_relative_path(
                    idea_ref,
                    1,
                )
                snapshot = workflow.run_dir / snapshot_ref
                self.assertTrue(snapshot.is_file())
                if damage == "delete":
                    snapshot.unlink()
                else:
                    snapshot.write_bytes(
                        snapshot.read_bytes() + b"\n<!-- changed snapshot -->\n"
                    )
                calls_before_resume = len(runner.calls)

                resumed = UsefulIdeaWorkflow(
                    workflow.run_dir,
                    runner=runner,  # type: ignore[arg-type]
                )
                with self.assertRaisesRegex(
                    WorkflowError,
                    "cannot resolve the immutable revision snapshot",
                ):
                    await resumed.execute()

                self.assertEqual(len(runner.calls), calls_before_resume)
                failed = StateStore(workflow.run_dir).load()
                self.assertIs(failed.status, RunStatus.FAILED)
                self.assertEqual(failed.data["final_ideas"], [])

    async def test_similar_passing_ideas_both_continue_without_selection(self) -> None:
        self.settings = WorkflowSettings(
            researchers_per_audience=1,
            problem_writers_per_audience=1,
            idea_generators_per_problem=2,
            task_timeout_seconds=30,
            run_timeout_seconds=60,
        )
        runner = ScriptedRunner()
        workflow = self.create_workflow(
            runner,
            run_id="run-workflow-similar-drafts",
        )

        await workflow.execute()

        state = StateStore(workflow.run_dir).load()
        self.assertEqual(len(state.data["final_ideas"]), 2)
        self.assertEqual(
            len(
                [
                    task
                    for task in state.tasks.values()
                    if task.stage == "S9" and task.data.get("mode") == "draft_screen"
                ]
            ),
            2,
        )
        self.assertEqual(
            len([task for task in state.tasks.values() if task.stage == "S7"]),
            2,
        )
        self.assertEqual(state.data["eliminations"], [])

    async def test_topology_version_is_inferred_once_and_preserves_legacy_runs(
        self,
    ) -> None:
        empty_runner = ScriptedRunner()
        fresh = self.create_workflow(
            empty_runner,
            run_id="run-workflow-topology-infer-v2",
        )
        self.assertEqual(
            StateStore(fresh.run_dir).load().data["draft_screen_policy_version"],
            3,
        )

        def remove_version(state: Any) -> None:
            state.data.pop("workflow_topology_version", None)
            state.data.pop("draft_screen_policy_version", None)

        StateStore(fresh.run_dir).mutate(remove_version)
        inferred_v2 = UsefulIdeaWorkflow(
            fresh.run_dir,
            runner=empty_runner,  # type: ignore[arg-type]
        )
        self.assertEqual(inferred_v2.workflow_topology_version, 2)
        self.assertEqual(inferred_v2.draft_screen_policy_version, 3)
        self.assertEqual(
            StateStore(fresh.run_dir).load().data["draft_screen_policy_version"],
            3,
        )
        revision_after_inference = StateStore(fresh.run_dir).load().state_revision
        inferred_v2_again = UsefulIdeaWorkflow(
            fresh.run_dir,
            runner=empty_runner,  # type: ignore[arg-type]
        )
        self.assertEqual(inferred_v2_again.workflow_topology_version, 2)
        self.assertEqual(inferred_v2_again.draft_screen_policy_version, 3)
        self.assertEqual(
            StateStore(fresh.run_dir).load().state_revision,
            revision_after_inference,
        )

        legacy_runner = ScriptedRunner()
        legacy, brief, passed, idea_ref = await self.stage_one_idea(
            legacy_runner,
            run_id="run-workflow-topology-infer-v1",
        )
        await legacy._run_competition(
            idea_ref=idea_ref,
            passed=passed,
            researcher_number=1,
        )

        def remove_legacy_versions(state: Any) -> None:
            state.data.pop("workflow_topology_version", None)
            state.data.pop("draft_screen_policy_version", None)

        StateStore(legacy.run_dir).mutate(remove_legacy_versions)

        resumed_legacy = UsefulIdeaWorkflow(
            legacy.run_dir,
            runner=legacy_runner,  # type: ignore[arg-type]
        )
        self.assertEqual(resumed_legacy.workflow_topology_version, 1)
        self.assertIsNone(resumed_legacy.draft_screen_policy_version)
        legacy_finals = await resumed_legacy._stage_s7_s10(
            brief,
            [idea_ref],
            [passed],
        )
        self.assertEqual(len(legacy_finals), 1)
        self.assertIsNone(legacy_finals[0].draft_screen_ref)
        legacy_state = StateStore(legacy.run_dir).load()
        self.assertEqual(legacy_state.data["workflow_topology_version"], 1)
        self.assertNotIn("draft_screen_policy_version", legacy_state.data)
        self.assertFalse(
            any(
                task.stage == "S9" and task.data.get("mode") == "draft_screen"
                for task in legacy_state.tasks.values()
            )
        )

    async def test_draft_screen_policy_migration_is_independent_and_append_only(
        self,
    ) -> None:
        runner = ScriptedRunner()
        workflow, brief, passed, idea_ref = await self.stage_one_idea(
            runner,
            run_id="run-workflow-draft-policy-migration",
        )

        def select_policy_one(state: Any) -> None:
            state.data["draft_screen_policy_version"] = 1

        StateStore(workflow.run_dir).mutate(select_policy_one)
        policy_one = UsefulIdeaWorkflow(
            workflow.run_dir,
            runner=runner,  # type: ignore[arg-type]
        )
        policy_one_finals = await policy_one._stage_s7_s10(
            brief,
            [idea_ref],
            [passed],
        )
        self.assertEqual(len(policy_one_finals), 1)
        old_screen_ref = policy_one_finals[0].draft_screen_ref
        self.assertIsNotNone(old_screen_ref)
        assert old_screen_ref is not None
        self.assertTrue(old_screen_ref.endswith("/draft-screen-001.md"))
        old_state = StateStore(workflow.run_dir).load()
        old_screen_task = next(
            task
            for task in old_state.tasks.values()
            if task.outputs == [old_screen_ref]
        )
        old_session = old_screen_task.session_id
        self.assertIs(old_screen_task.status, TaskStatus.COMPLETED)
        self.assertTrue((workflow.run_dir / old_screen_ref).is_file())

        stale_task_id = "s9-stale-draft-screen-policy-one"

        def emulate_legacy_state(state: Any) -> None:
            completed = state.tasks[old_screen_task.task_id]
            manifest = completed.data["context_manifest"]
            manifest["routing"].pop("draft_screen_policy_version", None)
            completed.data["prompt_version"] = "2"
            stale = TaskRecord(
                task_id=stale_task_id,
                stage="S9",
                status=TaskStatus.RUNNING,
                next_action="wait-for-codex",
                data={
                    "mode": "draft_screen",
                    "output_target": old_screen_ref,
                    "context_manifest": {
                        "routing": {
                            "idea_ref": idea_ref,
                            "red_team_id": "draft-screen-001",
                            "review_mode": "draft_screen",
                        }
                    },
                },
            )
            state.upsert_task(stale)
            state.data.pop("draft_screen_policy_version", None)

        StateStore(workflow.run_dir).mutate(emulate_legacy_state)
        inferred = UsefulIdeaWorkflow(
            workflow.run_dir,
            runner=runner,  # type: ignore[arg-type]
        )
        self.assertEqual(inferred.draft_screen_policy_version, 1)
        inferred_state = StateStore(workflow.run_dir).load()
        self.assertEqual(inferred_state.data["draft_screen_policy_version"], 1)
        self.assertIs(
            inferred_state.tasks[stale_task_id].status,
            TaskStatus.RUNNING,
        )
        revision_after_inference = inferred_state.state_revision
        UsefulIdeaWorkflow(
            workflow.run_dir,
            runner=runner,  # type: ignore[arg-type]
        )
        self.assertEqual(
            StateStore(workflow.run_dir).load().state_revision,
            revision_after_inference,
        )

        def select_policy_two(state: Any) -> None:
            state.data["draft_screen_policy_version"] = 2

        StateStore(workflow.run_dir).mutate(select_policy_two)
        migrated = UsefulIdeaWorkflow(
            workflow.run_dir,
            runner=runner,  # type: ignore[arg-type]
        )
        migrated_state = StateStore(workflow.run_dir).load()
        self.assertEqual(migrated.draft_screen_policy_version, 2)
        self.assertIs(
            migrated_state.tasks[old_screen_task.task_id].status,
            TaskStatus.COMPLETED,
        )
        cancelled = migrated_state.tasks[stale_task_id]
        self.assertIs(cancelled.status, TaskStatus.CANCELLED)
        self.assertIsNone(cancelled.next_action)
        self.assertIn("superseded-policy", cancelled.last_error or "")
        self.assertEqual(cancelled.data["cancellation_reason"], cancelled.last_error)
        self.assertTrue((workflow.run_dir / old_screen_ref).is_file())
        revision_after_cancellation = migrated_state.state_revision
        UsefulIdeaWorkflow(
            workflow.run_dir,
            runner=runner,  # type: ignore[arg-type]
        )
        self.assertEqual(
            StateStore(workflow.run_dir).load().state_revision,
            revision_after_cancellation,
        )

        wrong_policy_errors = validate_run(workflow.run_dir)
        self.assertFalse(
            any(
                old_screen_task.task_id in error
                and "invalid draft screen binding" in error
                for error in wrong_policy_errors
            )
        )
        self.assertTrue(
            any(
                "does not use the run's selected policy" in error
                for error in wrong_policy_errors
            )
        )
        with self.assertRaisesRegex(WorkflowError, "selected policy"):
            migrated._stage_s11(brief, policy_one_finals)

        policy_two_finals = await migrated._stage_s7_s10(
            brief,
            [idea_ref],
            [passed],
        )
        self.assertEqual(len(policy_two_finals), 1)
        new_screen_ref = policy_two_finals[0].draft_screen_ref
        self.assertIsNotNone(new_screen_ref)
        assert new_screen_ref is not None
        self.assertTrue(new_screen_ref.endswith("/draft-screen-002.md"))
        self.assertNotEqual(new_screen_ref, old_screen_ref)
        final_state = StateStore(workflow.run_dir).load()
        new_screen_task = next(
            task
            for task in final_state.tasks.values()
            if task.outputs == [new_screen_ref]
        )
        self.assertNotEqual(new_screen_task.task_id, old_screen_task.task_id)
        self.assertNotEqual(new_screen_task.session_id, old_session)
        self.assertEqual(
            final_state.tasks[old_screen_task.task_id].data["prompt_version"],
            "2",
        )
        self.assertEqual(new_screen_task.data["prompt_version"], "4")
        new_manifest = new_screen_task.data["context_manifest"]
        self.assertEqual(
            new_manifest["routing"]["draft_screen_policy_version"],
            2,
        )
        self.assertNotIn(old_screen_ref, new_manifest["routing"]["source_refs"])
        self.assertFalse(
            any(
                artifact["artifact_type"] == "idea_red_team"
                for artifact in new_manifest["artifacts"]
            )
        )
        self.assertTrue((workflow.run_dir / old_screen_ref).is_file())
        self.assertTrue((workflow.run_dir / new_screen_ref).is_file())
        self.assertEqual(
            final_state.data["final_ideas"][0]["draft_screen_ref"],
            new_screen_ref,
        )

        report = migrated._stage_s11(brief, policy_two_finals).read_text(
            encoding="utf-8"
        )
        self.assertIn("draft-screen-002.md", report)
        self.assertNotIn("draft-screen-001.md", report)
        self.assertEqual(validate_run(workflow.run_dir), [])

    async def test_policy_two_to_three_migration_preserves_history_and_isolates_work(
        self,
    ) -> None:
        runner = ScriptedRunner()
        workflow, _, passed, idea_ref = await self.stage_one_idea(
            runner,
            run_id="run-workflow-draft-policy-three-migration",
        )

        def select_policy_two(state: Any) -> None:
            state.data["draft_screen_policy_version"] = 2

        StateStore(workflow.run_dir).mutate(select_policy_two)
        policy_two = UsefulIdeaWorkflow(
            workflow.run_dir,
            runner=runner,  # type: ignore[arg-type]
        )
        old_screen = await policy_two._run_draft_screen(
            idea_ref=idea_ref,
            passed=passed,
        )
        old_screen_ref = old_screen.output_paths[0]
        self.assertTrue(old_screen_ref.endswith("/draft-screen-002.md"))
        old_state = StateStore(workflow.run_dir).load()
        old_task = old_state.tasks[old_screen.task_id]
        old_session = old_task.session_id
        old_manifest = old_task.data["context_manifest"]
        self.assertEqual(
            old_manifest["routing"]["draft_screen_policy_version"],
            2,
        )

        stale_task_id = "s9-stale-draft-screen-policy-two"
        unrelated_task_id = "s9-running-full-red-team"

        def emulate_interrupted_policy_two(state: Any) -> None:
            state.upsert_task(
                TaskRecord(
                    task_id=stale_task_id,
                    stage="S9",
                    status=TaskStatus.RUNNING,
                    next_action="wait-for-codex",
                    data={
                        "mode": "draft_screen",
                        "output_target": old_screen_ref,
                        "context_manifest": {
                            "routing": {
                                "idea_ref": idea_ref,
                                "red_team_id": "draft-screen-002",
                                "review_mode": "draft_screen",
                                "draft_screen_policy_version": 2,
                            }
                        },
                    },
                )
            )
            state.upsert_task(
                TaskRecord(
                    task_id=unrelated_task_id,
                    stage="S9",
                    status=TaskStatus.RUNNING,
                    next_action="wait-for-codex",
                    data={
                        "mode": "initial",
                        "context_manifest": {
                            "routing": {"review_mode": "initial"}
                        },
                    },
                )
            )
            state.data.pop("draft_screen_policy_version", None)

        StateStore(workflow.run_dir).mutate(emulate_interrupted_policy_two)
        inferred = UsefulIdeaWorkflow(
            workflow.run_dir,
            runner=runner,  # type: ignore[arg-type]
        )
        self.assertEqual(inferred.draft_screen_policy_version, 2)
        inferred_state = StateStore(workflow.run_dir).load()
        self.assertEqual(inferred_state.data["draft_screen_policy_version"], 2)
        self.assertIs(inferred_state.tasks[stale_task_id].status, TaskStatus.RUNNING)

        def select_policy_three(state: Any) -> None:
            state.data["draft_screen_policy_version"] = 3

        StateStore(workflow.run_dir).mutate(select_policy_three)
        migrated = UsefulIdeaWorkflow(
            workflow.run_dir,
            runner=runner,  # type: ignore[arg-type]
        )
        migrated_state = StateStore(workflow.run_dir).load()
        self.assertEqual(migrated.draft_screen_policy_version, 3)
        self.assertIs(
            migrated_state.tasks[old_task.task_id].status,
            TaskStatus.COMPLETED,
        )
        self.assertEqual(migrated_state.tasks[old_task.task_id].session_id, old_session)
        cancelled = migrated_state.tasks[stale_task_id]
        self.assertIs(cancelled.status, TaskStatus.CANCELLED)
        self.assertIsNone(cancelled.next_action)
        self.assertIn("superseded-policy", cancelled.last_error or "")
        self.assertIs(
            migrated_state.tasks[unrelated_task_id].status,
            TaskStatus.RUNNING,
        )
        self.assertTrue((workflow.run_dir / old_screen_ref).is_file())
        self.assertEqual(validate_run(workflow.run_dir), [])

        new_screen = await migrated._run_draft_screen(
            idea_ref=idea_ref,
            passed=passed,
        )
        new_screen_ref = new_screen.output_paths[0]
        self.assertTrue(new_screen_ref.endswith("/draft-screen-003.md"))
        self.assertNotEqual(new_screen_ref, old_screen_ref)
        final_state = StateStore(workflow.run_dir).load()
        new_task = final_state.tasks[new_screen.task_id]
        self.assertNotEqual(new_task.task_id, old_task.task_id)
        self.assertNotEqual(new_task.session_id, old_session)
        self.assertNotEqual(
            migrated._task_dir(new_task.task_id),
            migrated._task_dir(old_task.task_id),
        )
        new_manifest = new_task.data["context_manifest"]
        self.assertEqual(
            new_manifest["routing"]["draft_screen_policy_version"],
            3,
        )
        self.assertEqual(new_task.data["prompt_version"], "4")
        self.assertNotIn(old_screen_ref, new_manifest["routing"]["source_refs"])
        self.assertFalse(
            any(
                artifact["artifact_type"] == "idea_red_team"
                for artifact in new_manifest["artifacts"]
            )
        )
        self.assertTrue((workflow.run_dir / old_screen_ref).is_file())
        self.assertTrue((workflow.run_dir / new_screen_ref).is_file())
        self.assertEqual(validate_run(workflow.run_dir), [])

    def test_invalid_draft_screen_policy_versions_are_rejected(self) -> None:
        for index, invalid in enumerate((None, True, 3.0, "3", 4), start=1):
            runner = ScriptedRunner()
            workflow = self.create_workflow(
                runner,
                run_id=f"run-workflow-invalid-draft-policy-{index}",
            )

            def set_invalid(state: Any) -> None:
                state.data["draft_screen_policy_version"] = invalid

            StateStore(workflow.run_dir).mutate(set_invalid)
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(
                    WorkflowError,
                    (
                        "draft_screen_policy_version must be one of the integers "
                        "1, 2, or 3"
                    ),
                ):
                    UsefulIdeaWorkflow(
                        workflow.run_dir,
                        runner=runner,  # type: ignore[arg-type]
                    )

    def test_invalid_topology_versions_are_rejected(self) -> None:
        for index, invalid in enumerate((True, 2.0, 3), start=1):
            runner = ScriptedRunner()
            workflow = self.create_workflow(
                runner,
                run_id=f"run-workflow-invalid-topology-{index}",
            )

            def set_invalid(state: Any) -> None:
                state.data["workflow_topology_version"] = invalid

            StateStore(workflow.run_dir).mutate(set_invalid)
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(
                    WorkflowError,
                    "workflow_topology_version",
                ):
                    UsefulIdeaWorkflow(
                        workflow.run_dir,
                        runner=runner,  # type: ignore[arg-type]
                    )

    async def test_completed_s5_replays_historical_gateway_evidence(self) -> None:
        legacy_research = "research/audience-repair-workers/researcher-001.md"
        legacy_verification = (
            "verification/audience-repair-workers/researcher-001/verifier-001.md"
        )
        runner = ScriptedRunner(
            problem_evidence_citations=(
                f"- Research: {legacy_research}#evidence-001",
                f"- Verification: {legacy_verification}",
            )
        )
        (
            workflow,
            brief,
            audience,
            problem_ref,
            research_refs,
            verification_refs,
        ) = await self.stage_one_problem(
            runner,
            run_id="run-workflow-completed-s5-replay",
        )
        audience_id = str(audience["audience_id"])
        with self.assertRaisesRegex(WorkflowError, "must pair each Research"):
            workflow._derive_problem_evidence_refs(
                problem_ref=problem_ref,
                audience_id=audience_id,
                research_refs=research_refs,
                verification_refs=verification_refs,
            )

        historical_evidence = tuple([*research_refs, *verification_refs])
        gateway = await workflow._run_gateway(
            discovery=brief["discovery_view"],
            problem_ref=problem_ref,
            evidence_refs=historical_evidence,
            gateway_number=1,
            gateway_mode="initial",
            evidence_loop_count=0,
        )
        gateway_ref = gateway.output_paths[0]
        workflow._record_transition(
            candidate_ref=problem_ref,
            stage="S5",
            action="pass-problem",
            reason="Historical S5 decision fixture.",
            decision_refs=(gateway_ref,),
        )
        workflow._set_stage("S5", "completed")
        calls_before_resume = len(runner.calls)

        resumed = UsefulIdeaWorkflow(
            workflow.run_dir,
            runner=runner,  # type: ignore[arg-type]
        )
        replayed = await resumed._stage_s5(
            brief,
            [audience],
            [problem_ref],
            {audience_id: research_refs},
            {audience_id: verification_refs},
        )

        self.assertEqual(len(runner.calls), calls_before_resume)
        self.assertEqual(len(replayed), 1)
        self.assertEqual(replayed[0].gateway_ref, gateway_ref)
        self.assertEqual(replayed[0].evidence_refs, historical_evidence)

        await resumed._stage_s6(brief, replayed)
        s6_task = next(
            task for stage, task in zip(runner.stages, runner.calls) if stage == "S6"
        )
        s6_manifest = json.loads(
            (s6_task.cwd / "context-manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            s6_manifest["routing"]["source_refs"],
            [
                "discovery-view.json",
                problem_ref,
                gateway_ref,
                *historical_evidence,
            ],
        )

    async def test_completed_s5_checkpoint_requires_a_terminal_outcome(self) -> None:
        runner = ScriptedRunner()
        (
            workflow,
            brief,
            audience,
            problem_ref,
            research_refs,
            verification_refs,
        ) = await self.stage_one_problem(
            runner,
            run_id="run-workflow-incomplete-s5-checkpoint",
        )
        audience_id = str(audience["audience_id"])
        workflow._set_stage("S5", "completed")
        resumed = UsefulIdeaWorkflow(
            workflow.run_dir,
            runner=runner,  # type: ignore[arg-type]
        )

        with self.assertRaisesRegex(WorkflowError, "no unique terminal outcome"):
            await resumed._stage_s5(
                brief,
                [audience],
                [problem_ref],
                {audience_id: research_refs},
                {audience_id: verification_refs},
            )

    async def test_s5_branch_failure_cannot_complete_without_terminal_outcome(
        self,
    ) -> None:
        runner = ScriptedRunner()
        (
            workflow,
            brief,
            audience,
            problem_ref,
            research_refs,
            verification_refs,
        ) = await self.stage_one_problem(
            runner,
            run_id="run-workflow-s5-branch-failure",
        )
        audience_id = str(audience["audience_id"])

        with patch.object(
            workflow,
            "_process_problem",
            side_effect=TaskExecutionError("temporary Gateway failure"),
        ):
            with self.assertRaisesRegex(WorkflowError, "without a terminal outcome"):
                await workflow._stage_s5(
                    brief,
                    [audience],
                    [problem_ref],
                    {audience_id: research_refs},
                    {audience_id: verification_refs},
                )

        state = StateStore(workflow.run_dir).load()
        self.assertNotEqual(state.data["stage_statuses"].get("S5"), "completed")

    async def test_completed_s5_replay_does_not_promote_a_blind_pass(self) -> None:
        runner = ScriptedRunner(
            s5_statuses={
                "initial": "reject_candidate",
                "blind_rejection_confirmation": "pass",
            }
        )
        (
            workflow,
            brief,
            audience,
            problem_ref,
            research_refs,
            verification_refs,
        ) = await self.stage_one_problem(
            runner,
            run_id="run-workflow-s5-blind-pass-replay",
        )
        audience_id = str(audience["audience_id"])
        first_result = await workflow._stage_s5(
            brief,
            [audience],
            [problem_ref],
            {audience_id: research_refs},
            {audience_id: verification_refs},
        )
        self.assertEqual(first_result, [])
        state = StateStore(workflow.run_dir).load()
        elimination = next(
            item
            for item in state.data["eliminations"]
            if item["candidate_ref"] == problem_ref
        )
        self.assertEqual(elimination["rule"], "unresolved-gateway-disagreement")
        calls_before_resume = len(runner.calls)

        resumed = UsefulIdeaWorkflow(
            workflow.run_dir,
            runner=runner,  # type: ignore[arg-type]
        )
        replayed = await resumed._stage_s5(
            brief,
            [audience],
            [problem_ref],
            {audience_id: research_refs},
            {audience_id: verification_refs},
        )

        self.assertEqual(replayed, [])
        self.assertEqual(len(runner.calls), calls_before_resume)

    async def test_completed_s5_rejects_a_fabricated_elimination(self) -> None:
        runner = ScriptedRunner()
        (
            workflow,
            brief,
            audience,
            problem_ref,
            research_refs,
            verification_refs,
        ) = await self.stage_one_problem(
            runner,
            run_id="run-workflow-fabricated-s5-elimination",
        )
        audience_id = str(audience["audience_id"])

        def fabricate(state: Any) -> None:
            state.data["eliminations"].append(
                {
                    "stage": "S5",
                    "candidate_ref": problem_ref,
                }
            )
            state.data["stage_statuses"]["S5"] = "completed"

        StateStore(workflow.run_dir).mutate(fabricate)
        resumed = UsefulIdeaWorkflow(
            workflow.run_dir,
            runner=runner,  # type: ignore[arg-type]
        )

        with self.assertRaisesRegex(WorkflowError, "invalid elimination record"):
            await resumed._stage_s5(
                brief,
                [audience],
                [problem_ref],
                {audience_id: research_refs},
                {audience_id: verification_refs},
            )

    async def test_s5_routes_counterevidence_only_citations(self) -> None:
        counter_citation = (
            "- Counterexample: research/audience-repair-workers/"
            "researcher-001.md#evidence-001 | verification/"
            "audience-repair-workers/researcher-001/verifier-001.md"
        )
        runner = ScriptedRunner(
            problem_evidence_citations=(),
            problem_counterevidence_citations=(counter_citation,),
        )
        (
            workflow,
            _,
            audience,
            problem_ref,
            research_refs,
            verification_refs,
        ) = await self.stage_one_problem(
            runner,
            run_id="run-workflow-counterevidence-routing",
        )

        selected = workflow._derive_problem_evidence_refs(
            problem_ref=problem_ref,
            audience_id=str(audience["audience_id"]),
            research_refs=research_refs,
            verification_refs=verification_refs,
        )

        self.assertEqual(
            selected,
            (
                "research/audience-repair-workers/researcher-001.md",
                ("verification/audience-repair-workers/researcher-001/verifier-001.md"),
            ),
        )

    async def test_s5_pairs_multi_research_and_repeated_mentions_by_provenance(
        self,
    ) -> None:
        self.settings = WorkflowSettings(
            researchers_per_audience=2,
            problem_writers_per_audience=1,
            idea_generators_per_problem=1,
            task_timeout_seconds=30,
            run_timeout_seconds=60,
        )
        multi_runner = ScriptedRunner(
            problem_evidence_citations=(
                "- Workarounds use research/audience-repair-workers/"
                "researcher-001.md evidence-001 and research/"
                "audience-repair-workers/researcher-002.md evidence-001, "
                "respectively verified by verification/"
                "audience-repair-workers/researcher-001/verifier-001.md "
                "and verification/audience-repair-workers/researcher-002/"
                "verifier-001.md.",
            )
        )
        (
            multi_workflow,
            _,
            multi_audience,
            multi_problem,
            multi_research,
            multi_verifications,
        ) = await self.stage_one_problem(
            multi_runner,
            run_id="run-workflow-multi-research-citation",
        )
        multi_selected = multi_workflow._derive_problem_evidence_refs(
            problem_ref=multi_problem,
            audience_id=str(multi_audience["audience_id"]),
            research_refs=multi_research,
            verification_refs=multi_verifications,
        )
        self.assertEqual(
            multi_selected,
            tuple([*multi_research, *multi_verifications]),
        )

        repeated_runner = ScriptedRunner(
            problem_evidence_citations=(
                "- research/audience-repair-workers/researcher-001.md evidence-001 "
                "is uncertain; that uncertainty is documented again at "
                "research/audience-repair-workers/researcher-001.md evidence-001 "
                "and verification/audience-repair-workers/researcher-001/"
                "verifier-001.md.",
            )
        )
        (
            repeated_workflow,
            _,
            repeated_audience,
            repeated_problem,
            repeated_research,
            repeated_verifications,
        ) = await self.stage_one_problem(
            repeated_runner,
            run_id="run-workflow-repeated-research-citation",
        )
        repeated_lines = repeated_workflow._problem_body_evidence_citations(
            repeated_workflow._document(repeated_problem)
        )
        self.assertEqual(len(repeated_lines), 1)
        self.assertEqual(len(repeated_lines[0].mentions), 1)
        repeated_selected = repeated_workflow._derive_problem_evidence_refs(
            problem_ref=repeated_problem,
            audience_id=str(repeated_audience["audience_id"]),
            research_refs=repeated_research,
            verification_refs=repeated_verifications,
        )
        self.assertEqual(
            repeated_selected,
            (
                "research/audience-repair-workers/researcher-001.md",
                ("verification/audience-repair-workers/researcher-001/verifier-001.md"),
            ),
        )

    async def test_s5_rejects_unknown_and_unpaired_body_citations(self) -> None:
        unknown_runner = ScriptedRunner(
            problem_evidence_citations=(
                "- Claim: research/audience-other/researcher-001.md#"
                "evidence-001 | verification/audience-repair-workers/"
                "researcher-001/verifier-001.md",
            )
        )
        (
            unknown_workflow,
            _,
            unknown_audience,
            unknown_problem,
            unknown_research,
            unknown_verifications,
        ) = await self.stage_one_problem(
            unknown_runner,
            run_id="run-workflow-unknown-evidence-ref",
        )
        with self.assertRaisesRegex(WorkflowError, "outside its current Audience"):
            unknown_workflow._derive_problem_evidence_refs(
                problem_ref=unknown_problem,
                audience_id=str(unknown_audience["audience_id"]),
                research_refs=unknown_research,
                verification_refs=unknown_verifications,
            )

        missing_pair_runner = ScriptedRunner(
            problem_evidence_citations=(
                "- Claim: research/audience-repair-workers/"
                "researcher-001.md#evidence-001",
            )
        )
        (
            missing_pair_workflow,
            _,
            missing_pair_audience,
            missing_pair_problem,
            missing_pair_research,
            missing_pair_verifications,
        ) = await self.stage_one_problem(
            missing_pair_runner,
            run_id="run-workflow-missing-verification-ref",
        )
        with self.assertRaisesRegex(WorkflowError, "must pair each Research"):
            missing_pair_workflow._derive_problem_evidence_refs(
                problem_ref=missing_pair_problem,
                audience_id=str(missing_pair_audience["audience_id"]),
                research_refs=missing_pair_research,
                verification_refs=missing_pair_verifications,
            )

        self.settings = WorkflowSettings(
            researchers_per_audience=2,
            problem_writers_per_audience=1,
            idea_generators_per_problem=1,
            task_timeout_seconds=30,
            run_timeout_seconds=60,
        )
        unpaired_runner = ScriptedRunner(
            problem_evidence_citations=(
                "- Claim: research/audience-repair-workers/"
                "researcher-001.md#evidence-001 | verification/"
                "audience-repair-workers/researcher-002/verifier-001.md",
            )
        )
        (
            unpaired_workflow,
            _,
            unpaired_audience,
            unpaired_problem,
            unpaired_research,
            unpaired_verifications,
        ) = await self.stage_one_problem(
            unpaired_runner,
            run_id="run-workflow-unpaired-evidence-ref",
        )
        with self.assertRaisesRegex(WorkflowError, "unpaired Verification"):
            unpaired_workflow._derive_problem_evidence_refs(
                problem_ref=unpaired_problem,
                audience_id=str(unpaired_audience["audience_id"]),
                research_refs=unpaired_research,
                verification_refs=unpaired_verifications,
            )

    async def test_s5_requires_blind_verifier_coverage_for_cited_recheck(self) -> None:
        runner = ScriptedRunner(
            verification_recheck_ids=("evidence-001",),
        )
        (
            workflow,
            _,
            audience,
            problem_ref,
            research_refs,
            verification_refs,
        ) = await self.stage_one_problem(
            runner,
            run_id="run-workflow-cited-blind-coverage",
        )
        selected = workflow._derive_problem_evidence_refs(
            problem_ref=problem_ref,
            audience_id=str(audience["audience_id"]),
            research_refs=research_refs,
            verification_refs=verification_refs,
        )
        self.assertEqual(selected, tuple([*research_refs, *verification_refs]))

        second_only_runner = ScriptedRunner(
            verification_recheck_ids=("evidence-001",),
            problem_evidence_citations=(
                "- Claim: research/audience-repair-workers/"
                "researcher-001.md#evidence-001 | verification/"
                "audience-repair-workers/researcher-001/verifier-002.md",
            ),
        )
        (
            second_only_workflow,
            _,
            second_only_audience,
            second_only_problem,
            second_only_research,
            second_only_verifications,
        ) = await self.stage_one_problem(
            second_only_runner,
            run_id="run-workflow-second-verifier-only",
        )
        with self.assertRaisesRegex(WorkflowError, "must explicitly cite"):
            second_only_workflow._derive_problem_evidence_refs(
                problem_ref=second_only_problem,
                audience_id=str(second_only_audience["audience_id"]),
                research_refs=second_only_research,
                verification_refs=second_only_verifications,
            )

        missing_runner = ScriptedRunner(
            verification_recheck_ids=("evidence-001",),
            blind_verification_covers_recheck=False,
        )
        (
            missing_workflow,
            _,
            missing_audience,
            missing_problem,
            missing_research,
            missing_verifications,
        ) = await self.stage_one_problem(
            missing_runner,
            run_id="run-workflow-missing-blind-coverage",
        )
        with self.assertRaisesRegex(WorkflowError, "verifier-002 does not cover"):
            missing_workflow._derive_problem_evidence_refs(
                problem_ref=missing_problem,
                audience_id=str(missing_audience["audience_id"]),
                research_refs=missing_research,
                verification_refs=missing_verifications,
            )

    async def test_primary_and_blind_gateways_receive_the_same_cited_subset(
        self,
    ) -> None:
        runner = ScriptedRunner()
        (
            workflow,
            brief,
            audience,
            problem_ref,
            research_refs,
            verification_refs,
        ) = await self.stage_one_problem(
            runner,
            run_id="run-workflow-blind-same-evidence",
        )
        selected = workflow._derive_problem_evidence_refs(
            problem_ref=problem_ref,
            audience_id=str(audience["audience_id"]),
            research_refs=research_refs,
            verification_refs=verification_refs,
        )
        discovery = brief["discovery_view"]
        self.assertIsInstance(discovery, dict)

        await workflow._run_gateway(
            discovery=discovery,
            problem_ref=problem_ref,
            evidence_refs=selected,
            gateway_number=1,
            gateway_mode="initial",
            evidence_loop_count=0,
        )
        await workflow._run_gateway(
            discovery=discovery,
            problem_ref=problem_ref,
            evidence_refs=selected,
            gateway_number=2,
            gateway_mode="blind_rejection_confirmation",
            evidence_loop_count=0,
        )

        s5_manifests = [
            json.loads((task.cwd / "context-manifest.json").read_text(encoding="utf-8"))
            for stage, task in zip(runner.stages, runner.calls)
            if stage == "S5"
        ]
        self.assertEqual(len(s5_manifests), 2)
        expected_refs = [problem_ref, "discovery-view.json", *selected]
        self.assertEqual(
            s5_manifests[0]["routing"]["source_refs"],
            expected_refs,
        )
        self.assertEqual(
            s5_manifests[1]["routing"]["source_refs"],
            expected_refs,
        )
        self.assertEqual(
            [artifact["canonical_ref"] for artifact in s5_manifests[0]["artifacts"]],
            [artifact["canonical_ref"] for artifact in s5_manifests[1]["artifacts"]],
        )

    async def test_revised_problem_recomputes_narrow_refs_for_pass_and_downstream(
        self,
    ) -> None:
        runner = ScriptedRunner(cite_latest_research_on_revision=True)
        (
            workflow,
            brief,
            audience,
            problem_ref,
            research_refs,
            verification_refs,
        ) = await self.stage_one_problem(
            runner,
            run_id="run-workflow-revision-narrow-evidence",
        )
        audience_id = str(audience["audience_id"])
        initial_refs = workflow._derive_problem_evidence_refs(
            problem_ref=problem_ref,
            audience_id=audience_id,
            research_refs=research_refs,
            verification_refs=verification_refs,
        )

        (
            _,
            revised_research,
            revised_verifications,
        ) = await workflow._targeted_problem_retry(
            brief=brief,
            audience=audience,
            problem_ref=problem_ref,
            research_refs=research_refs,
            verification_refs=verification_refs,
            gaps=("Find one additional first-hand recurrence report.",),
        )
        revised_refs = workflow._derive_problem_evidence_refs(
            problem_ref=problem_ref,
            audience_id=audience_id,
            research_refs=revised_research,
            verification_refs=revised_verifications,
        )
        self.assertNotEqual(revised_refs, initial_refs)
        self.assertEqual(len(revised_refs), 2)
        self.assertIn("researcher-retry-", revised_refs[0])
        self.assertIn("researcher-retry-", revised_refs[1])

        passed = await workflow._process_problem(
            brief=brief,
            audience=audience,
            problem_ref=problem_ref,
            research_refs=revised_research,
            verification_refs=revised_verifications,
        )
        self.assertIsNotNone(passed)
        assert passed is not None
        self.assertEqual(passed.evidence_refs, revised_refs)
        await workflow._run_idea_generator(
            discovery=brief["discovery_view"],
            passed=passed,
            generator_id="generator-001",
        )

        s5_task = next(
            task for stage, task in zip(runner.stages, runner.calls) if stage == "S5"
        )
        s6_task = next(
            task for stage, task in zip(runner.stages, runner.calls) if stage == "S6"
        )
        s5_manifest = json.loads(
            (s5_task.cwd / "context-manifest.json").read_text(encoding="utf-8")
        )
        s6_manifest = json.loads(
            (s6_task.cwd / "context-manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            s5_manifest["routing"]["source_refs"],
            [problem_ref, "discovery-view.json", *revised_refs],
        )
        self.assertEqual(
            s6_manifest["routing"]["source_refs"],
            [
                "discovery-view.json",
                problem_ref,
                passed.gateway_ref,
                *revised_refs,
            ],
        )
        self.assertTrue(set(initial_refs).isdisjoint(revised_refs))
        self.assertTrue(
            set(initial_refs).isdisjoint(s6_manifest["routing"]["source_refs"])
        )

        calls_before_resume = len(runner.calls)
        resumed = UsefulIdeaWorkflow(workflow.run_dir, runner=runner)  # type: ignore[arg-type]
        resumed_passed = await resumed._process_problem(
            brief=brief,
            audience=audience,
            problem_ref=problem_ref,
            research_refs=revised_research,
            verification_refs=revised_verifications,
        )
        self.assertEqual(len(runner.calls), calls_before_resume)
        self.assertEqual(resumed_passed, passed)

    async def test_full_resume_rehydrates_targeted_problem_evidence(self) -> None:
        runner = ScriptedRunner(
            cite_latest_research_on_revision=True,
            s5_statuses={
                "initial": "needs_evidence",
                "post_evidence": "pass",
            },
        )
        workflow = self.create_workflow(
            runner,
            run_id="run-workflow-targeted-full-resume",
        )
        record_transition = workflow._record_transition

        def interrupt_after_retry(**kwargs: Any) -> None:
            if kwargs.get("action") == "targeted-evidence-retry":
                raise SimulatedInterruption("interrupted after targeted retry")
            record_transition(**kwargs)

        with patch.object(
            workflow,
            "_record_transition",
            side_effect=interrupt_after_retry,
        ):
            with self.assertRaisesRegex(
                SimulatedInterruption,
                "interrupted after targeted retry",
            ):
                await workflow.execute()

        interrupted = StateStore(workflow.run_dir).load()
        self.assertNotEqual(
            interrupted.data["stage_statuses"].get("S5"),
            "completed",
        )
        problem_ref = next(
            task.outputs[0]
            for task in interrupted.tasks.values()
            if task.stage == "S4" and task.data.get("mode") == "evidence_revision"
        )
        self.assertEqual(
            parse_markdown_file(workflow.run_dir / problem_ref).revision,
            2,
        )

        resumed = UsefulIdeaWorkflow(
            workflow.run_dir,
            runner=runner,  # type: ignore[arg-type]
        )
        report_path = await resumed.execute()

        self.assertEqual(runner.stages.count("S2"), 2)
        self.assertEqual(runner.stages.count("S3"), 2)
        self.assertEqual(runner.stages.count("S4"), 2)
        s5_calls = [
            task for stage, task in zip(runner.stages, runner.calls) if stage == "S5"
        ]
        s5_manifests = [
            json.loads((task.cwd / "context-manifest.json").read_text(encoding="utf-8"))
            for task in s5_calls
        ]
        self.assertEqual(
            [manifest["routing"]["gateway_mode"] for manifest in s5_manifests],
            ["initial", "post_evidence"],
        )
        post_routing = s5_manifests[-1]["routing"]
        self.assertEqual(post_routing["problem_revision"], 2)
        retry_refs = [
            ref for ref in post_routing["source_refs"] if "researcher-retry-" in ref
        ]
        self.assertEqual(len(retry_refs), 2)
        self.assertTrue(retry_refs[0].startswith("research/"))
        self.assertTrue(retry_refs[1].startswith("verification/"))

        completed = StateStore(workflow.run_dir).load()
        problem_actions = [
            decision["action"]
            for decision in StateStore(workflow.run_dir).decisions()
            if decision.get("candidate_ref") == problem_ref
            and decision.get("stage") == "S5"
            and decision.get("type") == "transition"
        ]
        self.assertEqual(
            problem_actions,
            ["targeted-evidence-retry", "pass-problem"],
        )
        self.assertIs(completed.status, RunStatus.COMPLETED)
        self.assertEqual(len(completed.data["final_ideas"]), 1)
        self.assertTrue(report_path.is_file())
        self.assertEqual(validate_run(workflow.run_dir), [])

    async def test_valid_zero_audience_result_still_produces_zero_idea_report(
        self,
    ) -> None:
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
        self.assertEqual(
            (first.run_dir / "idea-report.md").read_bytes(), initial_report
        )
        self.assertEqual(final_idea.revision, initial_idea.revision)
        self.assertEqual(final_idea.metadata, initial_idea.metadata)
        self.assertEqual(final_revisions, initial_revisions)
        self.assertEqual(validate_run(first.run_dir), [])

    async def test_invalid_staged_artifact_gets_one_same_session_correction(
        self,
    ) -> None:
        runner = ScriptedRunner(invalid_once_stage="S2")
        workflow = self.create_workflow(runner, run_id="run-workflow-correction")

        report_path = await workflow.execute()

        s2_calls = [
            task for stage, task in zip(runner.stages, runner.calls) if stage == "S2"
        ]
        self.assertEqual(len(s2_calls), 2)
        self.assertFalse(s2_calls[0].resume)
        self.assertTrue(s2_calls[1].resume)
        self.assertEqual(s2_calls[1].session_id, "session-003")
        s2_task = next(
            task
            for task in StateStore(workflow.run_dir).load().tasks.values()
            if task.stage == "S2"
        )
        self.assertEqual(s2_task.attempts, 2)
        self.assertNotIn("format_validation_failures", s2_task.data)
        self.assertNotIn("format_validation_error", s2_task.data)
        self.assertTrue(report_path.is_file())
        self.assertEqual(validate_run(workflow.run_dir), [])

    async def test_json_correction_budget_and_error_survive_restart(self) -> None:
        runner = ScriptedRunner()
        workflow = self.create_workflow(
            runner,
            run_id="run-workflow-json-correction-resume",
        )
        valid_s0_output = runner._s0_output

        def invalid_s0_output(run_id: str, task_id: str) -> dict[str, Any]:
            output = valid_s0_output(run_id, task_id)
            output["run_id"] = "wrong-run"
            return output

        run_codex = workflow._run_codex
        invocation_count = 0

        async def interrupt_first_correction(**kwargs: Any) -> CodexResult:
            nonlocal invocation_count
            invocation_count += 1
            if invocation_count == 2:
                raise SimulatedInterruption("interrupted during JSON correction")
            return await run_codex(**kwargs)

        with patch.object(
            runner,
            "_s0_output",
            side_effect=invalid_s0_output,
        ):
            with patch.object(
                workflow,
                "_run_codex",
                side_effect=interrupt_first_correction,
            ):
                with self.assertRaisesRegex(
                    SimulatedInterruption,
                    "interrupted during JSON correction",
                ):
                    await workflow._stage_s0()

            interrupted = StateStore(workflow.run_dir).load()
            task = next(iter(interrupted.tasks.values()))
            prior_error = str(task.data["format_validation_error"])
            self.assertEqual(task.data["format_validation_failures"], 1)
            self.assertEqual(task.attempts, 1)

            resumed = UsefulIdeaWorkflow(
                workflow.run_dir,
                runner=runner,  # type: ignore[arg-type]
            )
            with self.assertRaisesRegex(TaskExecutionError, "invalid output"):
                await resumed._stage_s0()

            self.assertEqual(len(runner.calls), 2)
            self.assertIn(prior_error, runner.calls[-1].prompt)
            exhausted = StateStore(workflow.run_dir).load().tasks[task.task_id]
            self.assertEqual(exhausted.data["format_validation_failures"], 2)
            self.assertEqual(exhausted.attempts, 2)

            resumed_again = UsefulIdeaWorkflow(
                workflow.run_dir,
                runner=runner,  # type: ignore[arg-type]
            )
            with self.assertRaisesRegex(
                TaskExecutionError,
                "format correction budget exhausted",
            ):
                await resumed_again._stage_s0()
            self.assertEqual(len(runner.calls), 2)

    async def test_artifact_correction_budget_and_error_survive_restart(
        self,
    ) -> None:
        runner = ScriptedRunner()
        workflow = self.create_workflow(
            runner,
            run_id="run-workflow-artifact-correction-resume",
        )
        brief = await workflow._stage_s0()
        audiences = await workflow._stage_s1(brief)
        audience = audiences[0]
        research_ref = "research/audience-repair-workers/researcher-001.md"
        write_artifact = runner._write_artifact

        def always_write_invalid_artifact(**kwargs: Any) -> str:
            kwargs["intentionally_invalid"] = kwargs["stage"] == "S2"
            return write_artifact(**kwargs)

        run_codex = workflow._run_codex
        invocation_count = 0

        async def interrupt_first_correction(**kwargs: Any) -> CodexResult:
            nonlocal invocation_count
            invocation_count += 1
            if invocation_count == 2:
                raise SimulatedInterruption("interrupted during artifact correction")
            return await run_codex(**kwargs)

        with patch.object(
            runner,
            "_write_artifact",
            side_effect=always_write_invalid_artifact,
        ):
            with patch.object(
                workflow,
                "_run_codex",
                side_effect=interrupt_first_correction,
            ):
                with self.assertRaisesRegex(
                    SimulatedInterruption,
                    "interrupted during artifact correction",
                ):
                    await workflow._run_research(
                        discovery=brief["discovery_view"],
                        audience=audience,
                        researcher_id="researcher-001",
                        target=research_ref,
                    )

            interrupted = StateStore(workflow.run_dir).load()
            task = next(
                task for task in interrupted.tasks.values() if task.stage == "S2"
            )
            prior_error = str(task.data["format_validation_error"])
            self.assertEqual(task.data["format_validation_failures"], 1)
            self.assertEqual(task.attempts, 1)

            resumed = UsefulIdeaWorkflow(
                workflow.run_dir,
                runner=runner,  # type: ignore[arg-type]
            )
            with self.assertRaisesRegex(
                TaskExecutionError,
                "artifact validation failed",
            ):
                await resumed._run_research(
                    discovery=brief["discovery_view"],
                    audience=audience,
                    researcher_id="researcher-001",
                    target=research_ref,
                )

            self.assertEqual(runner.stages.count("S2"), 2)
            self.assertIn(prior_error, runner.calls[-1].prompt)
            exhausted = StateStore(workflow.run_dir).load().tasks[task.task_id]
            self.assertEqual(exhausted.data["format_validation_failures"], 2)
            self.assertEqual(exhausted.attempts, 2)

            resumed_again = UsefulIdeaWorkflow(
                workflow.run_dir,
                runner=runner,  # type: ignore[arg-type]
            )
            with self.assertRaisesRegex(
                TaskExecutionError,
                "format correction budget exhausted",
            ):
                await resumed_again._run_research(
                    discovery=brief["discovery_view"],
                    audience=audience,
                    researcher_id="researcher-001",
                    target=research_ref,
                )
            self.assertEqual(runner.stages.count("S2"), 2)

    async def test_s3_derived_recheck_ids_publish_both_verifiers(self) -> None:
        runner = ScriptedRunner(verification_recheck_ids=("evidence-001",))
        workflow = self.create_workflow(
            runner,
            run_id="run-workflow-s3-derived-recheck",
        )

        await workflow.execute()

        s3_calls = [
            task for stage, task in zip(runner.stages, runner.calls) if stage == "S3"
        ]
        self.assertEqual(len(s3_calls), 2)
        first_manifest = json.loads(
            (s3_calls[0].cwd / "context-manifest.json").read_text(encoding="utf-8")
        )
        second_manifest = json.loads(
            (s3_calls[1].cwd / "context-manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            first_manifest["routing"]["assigned_recheck_evidence_ids"],
            [],
        )
        self.assertEqual(
            second_manifest["routing"]["assigned_recheck_evidence_ids"],
            ["evidence-001"],
        )

        verification_paths = sorted(workflow.run_dir.glob("verification/**/*.md"))
        self.assertEqual(len(verification_paths), 2)
        first = parse_markdown_file(verification_paths[0])
        second = parse_markdown_file(verification_paths[1])
        self.assertIs(first.metadata["needs_second_verifier"], True)
        self.assertEqual(first.metadata["recheck_evidence_ids"], ["evidence-001"])
        self.assertIs(second.metadata["needs_second_verifier"], False)
        self.assertEqual(second.metadata["recheck_evidence_ids"], [])

        state = StateStore(workflow.run_dir).load()
        s3_tasks = [task for task in state.tasks.values() if task.stage == "S3"]
        self.assertEqual(len(s3_tasks), 2)
        self.assertTrue(all(task.status is TaskStatus.COMPLETED for task in s3_tasks))
        self.assertTrue(
            all("publication_prepared" not in task.data for task in s3_tasks)
        )
        self.assertTrue(
            all(
                path.relative_to(workflow.run_dir).as_posix()
                in state.completed_artifacts
                for path in verification_paths
            )
        )
        self.assertEqual(validate_run(workflow.run_dir), [])

    async def test_s3_recovers_after_promotion_before_completed_state(self) -> None:
        runner = ScriptedRunner(verification_recheck_ids=("evidence-001",))
        workflow = self.create_workflow(
            runner,
            run_id="run-workflow-s3-promotion-recovery",
        )
        brief = await workflow._stage_s0()
        audiences = await workflow._stage_s1(brief)
        audience = audiences[0]
        research_ref = "research/audience-repair-workers/researcher-001.md"
        research = await workflow._run_research(
            discovery=brief["discovery_view"],
            audience=audience,
            researcher_id="researcher-001",
            target=research_ref,
        )
        self.assertEqual(research.output_paths, (research_ref,))

        with patch.object(
            workflow,
            "_mark_completed",
            side_effect=RuntimeError("interrupted after canonical promotion"),
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "interrupted after canonical promotion",
            ):
                await workflow._run_verification(
                    audience=audience,
                    research_ref=research_ref,
                    verifier_number=1,
                )

        interrupted_state = StateStore(workflow.run_dir).load()
        interrupted = [
            task for task in interrupted_state.tasks.values() if task.stage == "S3"
        ]
        self.assertEqual(len(interrupted), 1)
        self.assertIs(interrupted[0].data.get("publication_prepared"), True)
        self.assertEqual(interrupted[0].attempts, 1)
        self.assertEqual(interrupted[0].data.get("pending_attempts"), 0)
        self.assertEqual(len(interrupted[0].outputs), 1)
        canonical = workflow.run_dir / interrupted[0].outputs[0]
        self.assertTrue(canonical.is_file())
        calls_before_resume = len(runner.calls)

        resumed = UsefulIdeaWorkflow(workflow.run_dir, runner=runner)  # type: ignore[arg-type]
        recovered = await resumed._run_verification(
            audience=audience,
            research_ref=research_ref,
            verifier_number=1,
        )

        self.assertEqual(len(runner.calls), calls_before_resume)
        self.assertEqual(recovered.output_paths, tuple(interrupted[0].outputs))
        recovered_state = StateStore(workflow.run_dir).load()
        recovered_task = recovered_state.tasks[interrupted[0].task_id]
        self.assertIs(recovered_task.status, TaskStatus.COMPLETED)
        self.assertEqual(recovered_task.attempts, 1)
        self.assertNotIn("publication_prepared", recovered_task.data)
        self.assertNotIn("pending_attempts", recovered_task.data)
        self.assertIn(recovered_task.outputs[0], recovered_state.completed_artifacts)
        recovered_document = parse_markdown_file(canonical)
        self.assertIs(recovered_document.metadata["needs_second_verifier"], True)
        self.assertEqual(
            recovered_document.metadata["recheck_evidence_ids"],
            ["evidence-001"],
        )

    async def test_s3_replays_prepared_staging_when_canonical_is_missing(self) -> None:
        runner = ScriptedRunner(verification_recheck_ids=("evidence-001",))
        workflow = self.create_workflow(
            runner,
            run_id="run-workflow-s3-staged-replay",
        )
        brief = await workflow._stage_s0()
        audiences = await workflow._stage_s1(brief)
        audience = audiences[0]
        research_ref = "research/audience-repair-workers/researcher-001.md"
        await workflow._run_research(
            discovery=brief["discovery_view"],
            audience=audience,
            researcher_id="researcher-001",
            target=research_ref,
        )

        with patch.object(
            workflow.artifacts,
            "promote_many",
            side_effect=SimulatedInterruption("interrupted before canonical promotion"),
        ):
            with self.assertRaisesRegex(
                SimulatedInterruption,
                "interrupted before canonical promotion",
            ):
                await workflow._run_verification(
                    audience=audience,
                    research_ref=research_ref,
                    verifier_number=1,
                )

        interrupted_state = StateStore(workflow.run_dir).load()
        interrupted = [
            task for task in interrupted_state.tasks.values() if task.stage == "S3"
        ]
        self.assertEqual(len(interrupted), 1)
        interrupted_task = interrupted[0]
        self.assertIs(interrupted_task.data.get("publication_prepared"), True)
        self.assertEqual(interrupted_task.attempts, 1)
        self.assertEqual(interrupted_task.data.get("pending_attempts"), 0)
        self.assertEqual(len(interrupted_task.outputs), 1)
        output_ref = interrupted_task.outputs[0]
        staged = workflow.run_dir / ".staging" / interrupted_task.task_id / output_ref
        canonical = workflow.run_dir / output_ref
        self.assertTrue(staged.is_file())
        self.assertFalse(canonical.exists())
        calls_before_resume = len(runner.calls)

        resumed = UsefulIdeaWorkflow(workflow.run_dir, runner=runner)  # type: ignore[arg-type]
        recovered = await resumed._run_verification(
            audience=audience,
            research_ref=research_ref,
            verifier_number=1,
        )

        self.assertEqual(len(runner.calls), calls_before_resume)
        self.assertEqual(recovered.output_paths, (output_ref,))
        self.assertTrue(canonical.is_file())
        recovered_state = StateStore(workflow.run_dir).load()
        recovered_task = recovered_state.tasks[interrupted_task.task_id]
        self.assertIs(recovered_task.status, TaskStatus.COMPLETED)
        self.assertEqual(recovered_task.attempts, 1)
        self.assertNotIn("publication_prepared", recovered_task.data)
        self.assertNotIn("pending_attempts", recovered_task.data)
        self.assertIn(output_ref, recovered_state.completed_artifacts)
        recovered_document = parse_markdown_file(canonical)
        self.assertIs(recovered_document.metadata["needs_second_verifier"], True)
        self.assertEqual(
            recovered_document.metadata["recheck_evidence_ids"],
            ["evidence-001"],
        )

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
        workflow = self.create_workflow(runner, run_id="run-workflow-challenge-tamper")
        await workflow.execute()
        (workflow.run_dir / "challenge.md").write_text(
            "A different challenge.\n",
            encoding="utf-8",
        )

        errors = validate_run(workflow.run_dir)

        self.assertTrue(
            any("raw challenge content changed" in error for error in errors)
        )
        resumed = UsefulIdeaWorkflow(
            workflow.run_dir,
            runner=runner,  # type: ignore[arg-type]
        )
        with self.assertRaisesRegex(WorkflowError, "raw challenge content changed"):
            await resumed.execute()

    async def test_completed_run_rejects_report_tampering(self) -> None:
        runner = ScriptedRunner()
        workflow = self.create_workflow(runner, run_id="run-workflow-report-tamper")
        await workflow.execute()
        report_path = workflow.run_dir / "idea-report.md"
        report_path.write_text(
            report_path.read_text(encoding="utf-8") + "\nUndeclared edit.\n",
            encoding="utf-8",
        )

        errors = validate_run(workflow.run_dir)

        self.assertTrue(
            any("final report content changed" in error for error in errors)
        )
        resumed = UsefulIdeaWorkflow(
            workflow.run_dir,
            runner=runner,  # type: ignore[arg-type]
        )
        with self.assertRaisesRegex(WorkflowError, "failed validation"):
            await resumed.execute()


if __name__ == "__main__":
    unittest.main()
