from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from hacksome.artifacts import (
    ArtifactDocument,
    parse_markdown_file,
    serialize_markdown,
)
from hacksome.models import CodexTask
from hacksome.state import StateStore
from hacksome.workflow import UsefulIdeaWorkflow, WorkflowSettings, validate_run
from tests.test_workflow import ScriptedRunner


@dataclass(frozen=True, slots=True)
class GatewayOutcome:
    status: str
    failed_thresholds: tuple[str, ...] = ()
    evidence_gaps: tuple[str, ...] = ()


class ProblemLoopRunner(ScriptedRunner):
    """Script S5 outcomes while preserving the normal offline artifact path."""

    def __init__(self, outcomes: dict[str, GatewayOutcome]) -> None:
        super().__init__()
        self.outcomes = outcomes
        self.manifests: list[tuple[str, dict[str, Any]]] = []

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
        self.manifests.append((stage, manifest))
        routing = manifest["routing"]

        # An S4 evidence revision targets the existing Living Document through
        # assigned_paths, while the human-facing output target remains its
        # directory. Honor that exact assignment in this offline runner.
        if stage == "S4" and "assigned_paths" in routing:
            output_path = str(routing["assigned_paths"][0])
            document = ArtifactDocument(
                metadata=self._metadata_for(
                    stage=stage,
                    run_id=run_id,
                    routing=routing,
                ),
                body=self._body_for(stage, "draft"),
            )
            destination = task.cwd / output_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(serialize_markdown(document), encoding="utf-8")
            return output_path

        output_path = super()._write_artifact(
            task=task,
            stage=stage,
            run_id=run_id,
            intentionally_invalid=intentionally_invalid,
        )
        if stage != "S5":
            return output_path

        gateway_mode = str(routing["gateway_mode"])
        try:
            outcome = self.outcomes[gateway_mode]
        except KeyError as exc:
            raise AssertionError(
                f"no scripted Gateway outcome for mode {gateway_mode!r}"
            ) from exc

        destination = task.cwd / output_path
        original = parse_markdown_file(destination)
        metadata = dict(original.metadata)
        metadata.update(
            {
                "status": outcome.status,
                "failed_thresholds": list(outcome.failed_thresholds),
                "evidence_gaps": list(outcome.evidence_gaps),
            }
        )
        destination.write_text(
            serialize_markdown(
                ArtifactDocument(
                    metadata=metadata,
                    body=self._body_for(stage, outcome.status),
                )
            ),
            encoding="utf-8",
        )
        return output_path


class ProblemLoopWorkflowTests(unittest.IsolatedAsyncioTestCase):
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
        runner: ProblemLoopRunner,
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

    async def test_needs_evidence_runs_one_targeted_loop_then_passes(self) -> None:
        gap = "Find a second independent first-hand report of recurring delays."
        runner = ProblemLoopRunner(
            {
                "initial": GatewayOutcome(
                    status="needs_evidence",
                    evidence_gaps=(gap,),
                ),
                "post_evidence": GatewayOutcome(status="pass"),
            }
        )
        workflow = self.create_workflow(
            runner,
            run_id="run-problem-evidence-loop",
        )

        report_path = await workflow.execute()

        problem_path = next(workflow.run_dir.glob("problems/**/*.md"))
        problem_ref = problem_path.relative_to(workflow.run_dir).as_posix()
        problem = parse_markdown_file(problem_path)
        problem_snapshot_ref = workflow.artifacts.snapshot_relative_path(
            problem_ref,
            1,
        )
        problem_snapshot = parse_markdown_file(
            workflow.run_dir / problem_snapshot_ref
        )

        stage_manifests = {
            stage: [manifest for actual, manifest in runner.manifests if actual == stage]
            for stage in {"S2", "S3", "S4", "S5"}
        }
        targeted_research = [
            manifest
            for manifest in stage_manifests["S2"]
            if manifest["routing"]["research_round"] == 2
        ]
        revised_problem = [
            manifest
            for manifest in stage_manifests["S4"]
            if manifest["routing"]["revision"] == 2
        ]
        gateway_modes = [
            manifest["routing"]["gateway_mode"]
            for manifest in stage_manifests["S5"]
        ]
        gateway_documents = [
            parse_markdown_file(path)
            for path in sorted(workflow.run_dir.glob("gateways/**/*.md"))
        ]

        self.assertEqual(gateway_modes, ["initial", "post_evidence"])
        self.assertEqual(
            [document.status for document in gateway_documents],
            ["needs_evidence", "pass"],
        )
        self.assertEqual(
            stage_manifests["S5"][1]["routing"]["problem_revision"],
            2,
        )
        self.assertEqual(len(stage_manifests["S2"]), 2)
        self.assertEqual(len(targeted_research), 1)
        self.assertEqual(targeted_research[0]["evidence_gaps"], [gap])
        self.assertEqual(len(stage_manifests["S3"]), 2)
        self.assertEqual(len(revised_problem), 1)
        self.assertEqual(revised_problem[0]["routing"]["evidence_gaps"], [gap])
        self.assertEqual(problem.revision, 2)
        self.assertEqual(problem.metadata["supersedes"], problem_snapshot_ref)
        self.assertEqual(problem_snapshot.revision, 1)
        self.assertEqual(
            list(
                (workflow.run_dir / "revisions" / Path(problem_ref).with_suffix(""))
                .glob("revision-*.md")
            ),
            [workflow.run_dir / problem_snapshot_ref],
        )

        problem_decisions = [
            decision
            for decision in StateStore(workflow.run_dir).decisions()
            if decision.get("candidate_ref") == problem_ref
            and decision.get("stage") == "S5"
        ]
        self.assertEqual(
            [decision.get("action") for decision in problem_decisions],
            ["targeted-evidence-retry", "pass-problem"],
        )
        self.assertTrue(report_path.is_file())
        self.assertIn("Repair workers", report_path.read_text(encoding="utf-8"))
        self.assertEqual(validate_run(workflow.run_dir), [])

    async def test_same_threshold_blind_rejection_eliminates_without_s6(self) -> None:
        runner = ProblemLoopRunner(
            {
                "initial": GatewayOutcome(
                    status="reject_candidate",
                    failed_thresholds=("T3",),
                ),
                "blind_rejection_confirmation": GatewayOutcome(
                    status="reject_candidate",
                    failed_thresholds=("T3",),
                ),
            }
        )
        workflow = self.create_workflow(
            runner,
            run_id="run-problem-double-reject",
        )

        report_path = await workflow.execute()

        problem_path = next(workflow.run_dir.glob("problems/**/*.md"))
        problem_ref = problem_path.relative_to(workflow.run_dir).as_posix()
        problem = parse_markdown_file(problem_path)
        gateway_manifests = [
            manifest
            for stage, manifest in runner.manifests
            if stage == "S5"
        ]
        gateway_modes = [
            manifest["routing"]["gateway_mode"] for manifest in gateway_manifests
        ]
        gateway_ids = [
            manifest["routing"]["gateway_id"] for manifest in gateway_manifests
        ]
        gateway_documents = [
            parse_markdown_file(path)
            for path in sorted(workflow.run_dir.glob("gateways/**/*.md"))
        ]

        self.assertEqual(
            gateway_modes,
            ["initial", "blind_rejection_confirmation"],
        )
        self.assertEqual(gateway_ids, ["gateway-001", "gateway-002"])
        self.assertEqual(
            [document.status for document in gateway_documents],
            ["reject_candidate", "reject_candidate"],
        )
        self.assertEqual(
            [document.metadata["failed_thresholds"] for document in gateway_documents],
            [["T3"], ["T3"]],
        )
        self.assertEqual(runner.stages.count("S5"), 2)
        self.assertNotIn("S6", runner.stages)
        self.assertEqual(problem.revision, 1)
        self.assertFalse(
            (workflow.run_dir / "revisions" / Path(problem_ref).with_suffix(""))
            .exists()
        )

        # The blind Gateway receives the same facts, never gateway-001 itself.
        blind_manifest = gateway_manifests[1]
        blind_refs = [
            artifact["canonical_ref"]
            for artifact in blind_manifest["artifacts"]
        ]
        self.assertFalse(any(ref.startswith("gateways/") for ref in blind_refs))

        state_store = StateStore(workflow.run_dir)
        problem_decisions = [
            decision
            for decision in state_store.decisions()
            if decision.get("candidate_ref") == problem_ref
            and decision.get("stage") == "S5"
        ]
        self.assertEqual(len(problem_decisions), 1)
        self.assertEqual(problem_decisions[0]["type"], "elimination")
        self.assertEqual(problem_decisions[0]["rule"], "double-confirmed:T3")
        self.assertEqual(
            problem_decisions[0]["decision_refs"],
            sorted(
                artifact.relative_to(workflow.run_dir).as_posix()
                for artifact in workflow.run_dir.glob("gateways/**/*.md")
            ),
        )
        state = state_store.load()
        self.assertEqual(len(state.data["eliminations"]), 1)
        self.assertEqual(state.data["final_ideas"], [])
        self.assertIn("No Idea passed", report_path.read_text(encoding="utf-8"))
        self.assertEqual(validate_run(workflow.run_dir), [])


if __name__ == "__main__":
    unittest.main()
