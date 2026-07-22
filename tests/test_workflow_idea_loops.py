from __future__ import annotations

import tempfile
import unittest
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any

from hacksome.artifacts import parse_markdown_file
from hacksome.state import StateStore
from hacksome.workflow import UsefulIdeaWorkflow, WorkflowSettings, validate_run
from tests.test_workflow import ScriptedRunner


class RepairThenScopeRunner(ScriptedRunner):
    """Exercise both bounded Idea repair paths without making network calls."""

    @staticmethod
    def _metadata_for(
        *,
        stage: str,
        run_id: str,
        routing: dict[str, Any],
    ) -> dict[str, Any]:
        metadata = ScriptedRunner._metadata_for(
            stage=stage,
            run_id=run_id,
            routing=routing,
        )
        if stage == "S9":
            metadata["status"] = {
                "initial": "repairable",
                "product_recheck": "pass",
                "scope_recheck": "pass",
            }[routing["review_mode"]]
        elif stage == "S10":
            metadata["status"] = {
                "initial": "scope_reduction",
                "scope_recheck": "feasible",
            }[routing["review_mode"]]
        return metadata


class UsefulIdeaRepairLoopTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.runs_dir = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    async def test_product_repair_then_scope_reduction_use_fresh_reviews(self) -> None:
        runner = RepairThenScopeRunner()
        workflow = UsefulIdeaWorkflow.create(
            "Build a useful tool for local communities in 24 hours.",
            self.runs_dir,
            settings=WorkflowSettings(
                researchers_per_audience=1,
                problem_writers_per_audience=1,
                idea_generators_per_problem=1,
                task_timeout_seconds=30,
                run_timeout_seconds=60,
            ),
            runner=runner,  # type: ignore[arg-type]
            run_id="run-workflow-idea-repairs",
        )

        report_path = await workflow.execute()

        state_store = StateStore(workflow.run_dir)
        state = state_store.load()
        self.assertEqual(len(state.data["final_ideas"]), 1)
        final = state.data["final_ideas"][0]
        self.assertIsInstance(final, dict)
        idea_ref = str(final["idea_ref"])

        stage_modes = Counter(
            (task.stage, str(task.data.get("mode")))
            for task in state.tasks.values()
        )
        self.assertEqual(stage_modes[("S8", "competition_revision")], 1)
        self.assertEqual(stage_modes[("S8", "product_repair")], 1)
        self.assertEqual(stage_modes[("S8", "scope_reduction")], 1)
        self.assertEqual(stage_modes[("S8", "competition_followup")], 0)
        self.assertEqual(stage_modes[("S9", "initial")], 1)
        self.assertEqual(stage_modes[("S9", "product_recheck")], 1)
        self.assertEqual(stage_modes[("S9", "scope_recheck")], 1)
        self.assertEqual(stage_modes[("S10", "initial")], 1)
        self.assertEqual(stage_modes[("S10", "scope_recheck")], 1)

        canonical = parse_markdown_file(workflow.run_dir / idea_ref)
        idea_stem = PurePosixPath(idea_ref).with_suffix("").as_posix()
        snapshot_refs = [
            f"revisions/{idea_stem}/revision-{revision:04d}.md"
            for revision in range(1, 4)
        ]
        snapshots = [
            parse_markdown_file(workflow.run_dir / reference)
            for reference in snapshot_refs
        ]
        self.assertEqual([document.revision for document in snapshots], [1, 2, 3])
        self.assertEqual(canonical.revision, 4)
        self.assertIsNone(snapshots[0].metadata["supersedes"])
        self.assertEqual(snapshots[1].metadata["supersedes"], snapshot_refs[0])
        self.assertEqual(snapshots[2].metadata["supersedes"], snapshot_refs[1])
        self.assertEqual(canonical.metadata["supersedes"], snapshot_refs[2])
        self.assertEqual(
            {document.metadata["created_by_session"] for document in snapshots}
            | {canonical.metadata["created_by_session"]},
            {snapshots[0].metadata["created_by_session"]},
        )

        review_tasks = [
            task for task in state.tasks.values() if task.stage in {"S9", "S10"}
        ]
        self.assertEqual(len(review_tasks), 5)
        self.assertEqual(len({task.task_id for task in review_tasks}), 5)
        self.assertEqual(len({task.session_id for task in review_tasks}), 5)
        self.assertNotIn(None, {task.session_id for task in review_tasks})
        self.assertTrue(all(len(task.outputs) == 1 for task in review_tasks))
        self.assertEqual(
            len({task.outputs[0] for task in review_tasks}),
            len(review_tasks),
        )

        review_by_mode = {
            (task.stage, str(task.data["mode"])): task for task in review_tasks
        }
        self.assertTrue(
            review_by_mode[("S9", "initial")].outputs[0].endswith(
                "/red-team-001.md"
            )
        )
        self.assertTrue(
            review_by_mode[("S9", "product_recheck")].outputs[0].endswith(
                "/red-team-002.md"
            )
        )
        self.assertTrue(
            review_by_mode[("S9", "scope_recheck")].outputs[0].endswith(
                "/red-team-003.md"
            )
        )
        self.assertTrue(
            review_by_mode[("S10", "initial")].outputs[0].endswith(
                "/review-001.md"
            )
        )
        self.assertTrue(
            review_by_mode[("S10", "scope_recheck")].outputs[0].endswith(
                "/review-002.md"
            )
        )

        for task in review_tasks:
            routing = task.data["routing_metadata"]
            self.assertIsInstance(routing, dict)
            metadata = routing[task.outputs[0]]
            source_refs = set(metadata["source_refs"])
            self.assertIn(idea_ref, source_refs)
            if task.stage == "S9":
                self.assertFalse(
                    any(
                        reference.startswith(("idea-reviews/", "feasibility/"))
                        for reference in source_refs
                    )
                )
            else:
                red_team_refs = {
                    reference
                    for reference in source_refs
                    if reference.startswith("idea-reviews/")
                }
                self.assertEqual(len(red_team_refs), 1)
                self.assertFalse(
                    any(reference.startswith("feasibility/") for reference in source_refs)
                )

        idea_decisions = [
            decision
            for decision in state_store.decisions()
            if decision.get("candidate_ref") == idea_ref
        ]
        self.assertEqual(
            [
                (decision["type"], decision["stage"], decision["action"])
                for decision in idea_decisions
            ],
            [
                ("transition", "S9", "product-repair"),
                ("transition", "S10", "scope-reduction"),
                ("transition", "S10", "accept-idea"),
            ],
        )
        self.assertEqual(
            idea_decisions[0]["decision_refs"],
            review_by_mode[("S9", "initial")].outputs,
        )
        self.assertEqual(
            idea_decisions[1]["decision_refs"],
            review_by_mode[("S10", "initial")].outputs,
        )
        self.assertEqual(
            set(idea_decisions[2]["decision_refs"]),
            {
                review_by_mode[("S9", "scope_recheck")].outputs[0],
                review_by_mode[("S10", "scope_recheck")].outputs[0],
            },
        )
        self.assertFalse(
            any(
                decision.get("type") == "elimination"
                and decision.get("candidate_ref") == idea_ref
                for decision in state_store.decisions()
            )
        )

        report = report_path.read_text(encoding="utf-8")
        self.assertIn("Repair workers", report)
        self.assertIn("voice-note-to-work-order", report)
        self.assertNotIn("No Idea passed", report)
        self.assertEqual(validate_run(workflow.run_dir), [])


if __name__ == "__main__":
    unittest.main()
