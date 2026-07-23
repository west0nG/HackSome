from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
from datetime import UTC, datetime
from typing import Any

from hacksome.config import CodexConfig
from hacksome.creative.artifacts import (
    ATOM_HEADINGS,
    CHALLENGE_BRIEF_HEADINGS,
    CONCEPT_HEADINGS,
    CONSTRAINT_VIEW_HEADINGS,
    CREATIVE_BRIEF_HEADINGS,
    HOOK_DIMENSIONS,
    HOOK_REASON_BY_DIMENSION,
    NOVELTY_SCAN_HEADINGS,
)
from hacksome.creative.contracts import (
    C5W_NOVELTY_SCAN,
    CreativeWorkflowSettings,
    DEFAULT_TERRITORY_LENSES,
)
from hacksome.creative.prompting import creative_prompt_catalog
from hacksome.creative.memory import (
    IdeaMemorySnapshot,
    MemoryCapsule,
    MemoryRecord,
)
from hacksome.creative.workflow import (
    CreativeIdeaWorkflow,
    CreativeWorkflowError,
)
from hacksome.models import CodexLogs, CodexResult, CodexRunStatus, CodexTask
from hacksome.routes import inspect_run, validate_run
from hacksome.state import atomic_write_json, sha256_json, sha256_text


def _markdown(title: str, headings: tuple[str, ...], value: str) -> str:
    sections = "\n\n".join(
        f"## {heading}\n\n{value}" for heading in headings
    )
    return f"# {title}\n\n{sections}\n"


def _concept_markdown(slot: int, *, repaired: bool = False) -> str:
    atom_ref = f"creative-atom-t{slot:02d}-01"
    values = {
        "Intended Reaction": f"Surprise {slot}",
        "One-sentence Hook": (
            f"A room answers gesture {slot} with an unexpected shared echo"
            + (" that arrives sooner" if repaired else "")
        ),
        "First Impression": f"A quiet object marked {slot}.",
        "Audience Action": f"The audience performs gesture {slot}.",
        "Setup, Reveal and Aftertaste": (
            f"The object waits, reverses gesture {slot}, then leaves a shared echo."
        ),
        "Real Input, Transformation and Output": (
            f"A real gesture {slot} is transformed locally into a visible echo."
        ),
        "Why It Is Unexpected Yet Legible": (
            "The same action returns with one understandable rule changed."
        ),
        "Minimum Hackathon Demo": "A sensor, a laptop, and one projected response.",
        "Assumptions, Confusion and Risks": "The gesture remains opt-in and visible.",
        "Parent Atoms": atom_ref,
    }
    sections = "\n\n".join(
        f"## {heading}\n\n{values[heading]}" for heading in CONCEPT_HEADINGS
    )
    return f"# Echo {slot}{' Repaired' if repaired else ''}\n\n{sections}\n"


def _hook_review(decision: str) -> dict[str, Any]:
    dimensions: list[dict[str, Any]] = []
    for index, dimension in enumerate(HOOK_DIMENSIONS):
        failed = decision != "pass" and index == 0
        dimensions.append(
            {
                "dimension": dimension,
                "verdict": "fail" if failed else "pass",
                "reason_code": (
                    HOOK_REASON_BY_DIMENSION[dimension] if failed else None
                ),
                "evidence": (
                    "The opening needs a clearer visible cue."
                    if failed
                    else "The Concept states a concrete, legible interaction."
                ),
            }
        )
    return {
        "overall_decision": decision,
        "dimensions": dimensions,
        "markdown": f"# Cheap Hook Review\n\nDecision: {decision}.\n",
    }


def _non_empty_memory_snapshot() -> IdeaMemorySnapshot:
    entry_payload: dict[str, Any] = {
        "memory_entry_id": "memory-source-001",
        "source_kind": "final_idea",
        "source_candidate_ref": "creative-idea-001",
        "source_candidate_sha256": sha256_text("historic final idea"),
        "source_concept_refs": [],
        "primary_territory_ref": "creative-territory-01",
        "one_sentence_hook": "A shadow arrives before its performer.",
        "audience_action": "The audience moves one hand.",
        "core_mechanism": "A delayed sensor trace is played out of order.",
        "reveal_pattern": "The room recognizes its own future gesture.",
        "intended_reaction": "Surprise and curiosity.",
        "terminal_outcome": "promoted_to_final",
        "reason_codes": [],
        "reason_evidence": [],
        "evidence_refs": [],
        "classification": "positive",
    }
    entry = {
        "capsule_sha256": sha256_json(entry_payload),
        **entry_payload,
    }
    record = MemoryRecord.from_mapping(
        {
            "memory_schema_version": 1,
            "source_run_id": "historic-run",
            "source_route": {
                "id": "creative",
                "contract_version": "1",
            },
            "source_report_artifact_id": "creative-idea-report-json",
            "source_report_sha256": sha256_text("historic report"),
            "created_at": "2026-07-22T00:00:00+00:00",
            "producer_kind": "live",
            "zero_reason_code": None,
            "challenge_context": {
                "summary": "Make a temporal interaction.",
                "intended_reactions": "Surprise and curiosity.",
            },
            "entries": [entry],
        }
    )
    record_hash = sha256_json(record.to_dict())
    record_artifact_id = "creative-memory-record"
    capsule = MemoryCapsule.from_source(
        record=record,
        record_artifact_id=record_artifact_id,
        record_sha256=record_hash,
        entry=record.entries[0],
    )
    return IdeaMemorySnapshot.from_mapping(
        {
            "schema_version": 1,
            "mode": "auto",
            "created_from": "runs_dir",
            "source_records": [
                {
                    "source_run_id": record.source_run_id,
                    "source_route_id": "creative",
                    "source_contract_version": "1",
                    "source_memory_record_artifact_id": record_artifact_id,
                    "source_memory_record_sha256": record_hash,
                }
            ],
            "entries": [capsule.to_dict()],
            "diagnostics": [],
            "truncated": False,
            "empty_reason": None,
        }
    )


class CreativeScriptedRunner:
    """Offline runner that deliberately finishes sibling fanout out of order."""

    def __init__(
        self,
        *,
        novelty_failure: bool = False,
        hook_mode: str = "pass",
        memory_ref: dict[str, str] | None = None,
    ) -> None:
        self.novelty_failure = novelty_failure
        self.hook_mode = hook_mode
        self.memory_ref = memory_ref
        self.tasks: list[CodexTask] = []
        self.completion_order: list[str] = []

    async def run(self, task: CodexTask) -> CodexResult:
        self.tasks.append(task)
        if task.task_id.endswith("-01") or "-s01-" in task.task_id:
            await asyncio.sleep(0.02)
        if (
            self.novelty_failure
            and task.task_id
            == "creative-c5w-novelty-creative-concept-s01-01-r001"
        ):
            raise RuntimeError("novelty search unavailable")

        output = self._output(task.task_id)
        self.completion_order.append(task.task_id)
        assert task.log_dir is not None
        task.log_dir.mkdir(parents=True, exist_ok=True)
        stdout = task.log_dir / "stdout.jsonl"
        stderr = task.log_dir / "stderr.jsonl"
        last_message = task.log_dir / "last-message.attempt-001.json"
        stdout.write_text('{"event":{"type":"turn.completed"}}\n', encoding="utf-8")
        stderr.write_text("", encoding="utf-8")
        last_message.write_text(
            json.dumps(output, ensure_ascii=False),
            encoding="utf-8",
        )
        now = datetime.now(UTC).isoformat()
        return CodexResult(
            task_id=task.task_id,
            status=CodexRunStatus.SUCCEEDED,
            session_id=f"session-{task.task_id}",
            structured_output=output,
            usage={"input_tokens": 1, "output_tokens": 1},
            logs=CodexLogs(
                stdout=stdout,
                stderr=stderr,
                last_message=last_message,
            ),
            error=None,
            returncode=0,
            attempts=1,
            started_at=now,
            finished_at=now,
            duration_seconds=0.01,
        )

    def _output(self, task_id: str) -> dict[str, Any]:
        if task_id == "creative-c0-challenge-parse":
            return {
                "challenge_brief_markdown": _markdown(
                    "Challenge Brief",
                    CHALLENGE_BRIEF_HEADINGS,
                    "Source fact: build an honest interactive demo.",
                ),
                "constraint_view_markdown": _markdown(
                    "Constraint View",
                    CONSTRAINT_VIEW_HEADINGS,
                    "Source fact: use only available data and permissions.",
                ),
            }
        if task_id == "creative-c1-brief-normalize":
            return {
                "markdown": _markdown(
                    "Creative Brief",
                    CREATIVE_BRIEF_HEADINGS,
                    "Aim for a legible surprise without hidden labor.",
                )
            }
        if task_id.startswith("creative-c2-territory-"):
            slot = int(task_id.rsplit("-", 1)[1])
            territory_ref = f"creative-territory-{slot:02d}"
            return {
                "territory_markdown": (
                    f"# Territory {slot}\n\nA distinct interaction mechanism.\n"
                ),
                "atoms": [
                    {
                        "markdown": _markdown(
                            f"Atom {slot}",
                            ATOM_HEADINGS,
                            f"Uses {territory_ref} through an opt-in gesture.",
                        )
                    }
                ],
            }
        if task_id.startswith("creative-c3-synthesis-"):
            slot = int(task_id.rsplit("-", 1)[1])
            return {
                "concepts": [
                    {
                        "markdown": _concept_markdown(slot),
                        "primary_territory_ref": (
                            f"creative-territory-{slot:02d}"
                        ),
                        "parent_atom_refs": [
                            f"creative-atom-t{slot:02d}-01"
                        ],
                    }
                ]
            }
        if task_id.startswith("creative-c4-review-"):
            if self.hook_mode == "repair_success" and "-c1-v2" in task_id:
                return _hook_review("repairable")
            if self.hook_mode == "repair_unresolved" and (
                "-c1-v2" in task_id or "-c2-v2" in task_id
            ):
                return _hook_review("repairable")
            return _hook_review("pass")
        if task_id.startswith("creative-c4-repair-"):
            slot = 1 if "-s01-" in task_id else 2
            return {"markdown": _concept_markdown(slot, repaired=True)}
        if task_id == "creative-c5m-memory-recall-01":
            if self.memory_ref is None:
                raise AssertionError("Recall requires a configured memory ref")
            return {
                "cues": [
                    {
                        "cue_id": "memory-cue-01",
                        "source_memory_refs": [self.memory_ref],
                        "role": "inspire",
                        "transferable_pattern": (
                            "Reorder a participant's own physical trace."
                        ),
                        "why_relevant": (
                            "The repaired Concept now makes its temporal rule legible."
                        ),
                        "current_atom_refs": ["creative-atom-t01-01"],
                        "related_concept_refs": [
                            "creative-concept-s01-01-r002"
                        ],
                        "elements_that_must_not_be_copied": [
                            "The original shadow presentation."
                        ],
                    }
                ],
                "no_relevant_memory_reason": None,
            }
        if task_id.startswith("creative-c5w-novelty-"):
            return {
                "markdown": _markdown(
                    "Novelty Scan",
                    NOVELTY_SCAN_HEADINGS,
                    "A bounded search found adjacent work but no direct collision.",
                ),
                "sources": [
                    {
                        "title": "Primary project page",
                        "url": "https://example.com/project",
                        "relation": "adjacent",
                        "evidence": "It shares a sensor but not the reveal.",
                    }
                ],
            }
        raise AssertionError(f"unexpected Creative task: {task_id}")


def _settings() -> CreativeWorkflowSettings:
    return CreativeWorkflowSettings(
        territory_explorers=2,
        max_atoms_per_territory=1,
        concept_synthesizers=2,
        max_concepts_per_synthesizer=1,
        idea_memory_mode="off",
        memory_remixers=0,
        max_memory_challengers=0,
    )


class CreativeWorkflowContractTests(unittest.TestCase):
    def test_default_fanout_and_web_policy_are_bounded(self) -> None:
        settings = CreativeWorkflowSettings()

        self.assertEqual(settings.territory_explorers, 6)
        self.assertEqual(len(DEFAULT_TERRITORY_LENSES), 6)
        self.assertEqual(settings.concept_synthesizers, 4)
        self.assertEqual(settings.hook_reviewers_per_concept, 2)
        self.assertEqual(settings.memory_recallers, 1)
        self.assertEqual(settings.max_memory_challengers, 2)
        self.assertEqual(
            tuple(
                stage
                for stage in creative_prompt_catalog
                if creative_prompt_catalog[stage].web_search
            ),
            (C5W_NOVELTY_SCAN,),
        )


class CreativeWorkflowTests(unittest.IsolatedAsyncioTestCase):
    async def test_tampered_frozen_inputs_fail_before_any_agent_starts(
        self,
    ) -> None:
        tamper_kinds = ("prompt", "schema", "idea-memory-snapshot")
        for tamper_kind in tamper_kinds:
            with (
                self.subTest(tamper_kind=tamper_kind),
                tempfile.TemporaryDirectory() as directory,
            ):
                runner = CreativeScriptedRunner()
                workflow = CreativeIdeaWorkflow.create(
                    "Make a tamper-evident interactive surprise.",
                    directory,
                    settings=_settings(),
                    run_id=f"creative-tamper-{tamper_kind}",
                    runner=runner,
                )
                state = workflow.hub.load_state()
                if tamper_kind == "idea-memory-snapshot":
                    relative_path = state["inputs"]["idea_memory"]["path"]
                else:
                    manifest_path = (
                        workflow.run_dir / state["resource_manifest"]["path"]
                    )
                    manifest = json.loads(
                        manifest_path.read_text(encoding="utf-8")
                    )
                    challenge_stage = next(
                        row
                        for row in manifest["stages"]
                        if row["stage"] == "creative-challenge-parse"
                    )
                    relative_path = (
                        "resources/"
                        + challenge_stage[
                            "template" if tamper_kind == "prompt" else "schema"
                        ]["path"]
                    )
                frozen_path = workflow.run_dir / relative_path
                frozen_path.write_text(
                    frozen_path.read_text(encoding="utf-8") + "\n",
                    encoding="utf-8",
                )

                caught: CreativeWorkflowError | None = None
                try:
                    await workflow.execute_c0_c5()
                except CreativeWorkflowError as exc:
                    caught = exc

                self.assertIsNotNone(
                    caught,
                    f"{tamper_kind} tampering must fail closed",
                )
                self.assertEqual(
                    runner.tasks,
                    [],
                    f"{tamper_kind} was detected only after an Agent started",
                )
                self.assertEqual(
                    workflow.hub.load_state()["status"],
                    "failed",
                )

    async def test_memory_off_e2e_is_stable_isolated_and_valid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runner = CreativeScriptedRunner()
            workflow = CreativeIdeaWorkflow.create(
                "Make an honest thirty-second interactive surprise.",
                directory,
                settings=_settings(),
                codex_config=CodexConfig(max_concurrency=4),
                run_id="creative-e2e",
                runner=runner,
            )

            outcome = await workflow.execute_c0_c5()

            self.assertEqual(
                outcome.territory_refs,
                ("creative-territory-01", "creative-territory-02"),
            )
            self.assertEqual(
                outcome.atom_refs,
                ("creative-atom-t01-01", "creative-atom-t02-01"),
            )
            self.assertEqual(
                outcome.base_concept_refs,
                (
                    "creative-concept-s01-01-r001",
                    "creative-concept-s02-01-r001",
                ),
            )
            self.assertEqual(outcome.memory_challenger_refs, ())
            self.assertEqual(
                outcome.hook_passed_refs,
                outcome.base_concept_refs,
            )
            self.assertEqual(
                outcome.novelty_scan_refs,
                (
                    "creative-novelty-creative-concept-s01-01-r001",
                    "creative-novelty-creative-concept-s02-01-r001",
                ),
            )
            self.assertLess(
                runner.completion_order.index("creative-c2-territory-02"),
                runner.completion_order.index("creative-c2-territory-01"),
            )
            self.assertLess(
                runner.completion_order.index("creative-c3-synthesis-02"),
                runner.completion_order.index("creative-c3-synthesis-01"),
            )

            novelty_tasks = [
                task
                for task in runner.tasks
                if task.task_id.startswith("creative-c5w-novelty-")
            ]
            self.assertEqual(len(novelty_tasks), 2)
            self.assertTrue(all(task.web_search for task in novelty_tasks))
            self.assertTrue(
                all(
                    not task.web_search
                    for task in runner.tasks
                    if task not in novelty_tasks
                )
            )

            early_tasks = [
                task
                for task in runner.tasks
                if task.task_id.startswith(
                    (
                        "creative-c2-",
                        "creative-c3-",
                        "creative-c4-review-",
                    )
                )
            ]
            self.assertTrue(early_tasks)
            for task in early_tasks:
                self.assertNotIn("<BEGIN_IDEA_MEMORY_", task.prompt)
                self.assertNotIn("<BEGIN_MEMORY_CUE_", task.prompt)
                self.assertNotIn("input:idea_memory", task.prompt)

            state = workflow.hub.load_state()
            for task in early_tasks:
                parent_refs = state["tasks"][task.task_id]["parent_refs"]
                self.assertNotIn("input:idea_memory", parent_refs)
                self.assertFalse(
                    any("memory-inspiration" in ref for ref in parent_refs)
                )
            self.assertEqual(state["status"], "running")
            self.assertEqual(
                state["current_stage"],
                "creative-c5-complete-internal",
            )
            self.assertFalse(
                any(
                    task_id.startswith("creative-c5m-")
                    for task_id in state["tasks"]
                )
            )
            memory_summary = json.loads(
                workflow.hub.read_artifact(outcome.memory_summary_ref)
            )
            self.assertEqual(memory_summary["status"], "disabled")
            self.assertEqual(
                memory_summary["recall"]["status"],
                "not_started",
            )
            self.assertEqual(validate_run(workflow.run_dir), [])
            projection = inspect_run(workflow.run_dir)
            self.assertEqual(projection["concept_counts"]["base_generated"], 2)
            self.assertEqual(projection["concept_counts"]["hook_passed"], 2)
            self.assertEqual(projection["memory"]["status"], "disabled")

    async def test_novelty_failure_is_fatal_and_never_publishes_empty_scan(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runner = CreativeScriptedRunner(novelty_failure=True)
            workflow = CreativeIdeaWorkflow.create(
                "Make a shareable interactive surprise.",
                directory,
                settings=_settings(),
                run_id="creative-novelty-failure",
                runner=runner,
            )

            with self.assertRaisesRegex(
                CreativeWorkflowError,
                "novelty search unavailable",
            ):
                await workflow.execute_c0_c5()

            state = workflow.hub.load_state()
            self.assertEqual(state["status"], "failed")
            self.assertEqual(state["current_stage"], C5W_NOVELTY_SCAN)
            self.assertEqual(
                state["terminal_error"]["task_id"],
                "creative-c5w-novelty-creative-concept-s01-01-r001",
            )
            failed_novelty = [
                record
                for record in state["tasks"].values()
                if record["stage"] == C5W_NOVELTY_SCAN
                and record["status"] == "failed"
            ]
            self.assertTrue(failed_novelty)
            self.assertTrue(
                all(record["failure_policy"] == "fatal" for record in failed_novelty)
            )
            self.assertNotIn(
                "creative-novelty-creative-concept-s01-01-r001",
                state["artifacts"],
            )
            published_scans = [
                artifact_id
                for artifact_id, record in state["artifacts"].items()
                if record["artifact_type"] == "creative_novelty_scan"
            ]
            for artifact_id in published_scans:
                self.assertTrue(workflow.hub.read_artifact(artifact_id).strip())

    async def test_c4_repair_is_bounded_and_requires_two_fresh_passes(
        self,
    ) -> None:
        scenarios = (
            (
                "repair-success",
                "repair_success",
                ("creative-concept-s01-01-r002",),
                "creative-novelty-creative-concept-s01-01-r002",
                "pass",
            ),
            (
                "repair-unresolved",
                "repair_unresolved",
                (),
                None,
                "eliminated",
            ),
        )
        for run_id, hook_mode, passed, novelty_ref, final_outcome in scenarios:
            with self.subTest(run_id=run_id), tempfile.TemporaryDirectory() as directory:
                runner = CreativeScriptedRunner(hook_mode=hook_mode)
                settings = CreativeWorkflowSettings(
                    territory_explorers=1,
                    max_atoms_per_territory=1,
                    concept_synthesizers=1,
                    max_concepts_per_synthesizer=1,
                    idea_memory_mode="off",
                    memory_remixers=0,
                    max_memory_challengers=0,
                )
                workflow = CreativeIdeaWorkflow.create(
                    "Make a repairable interactive surprise.",
                    directory,
                    settings=settings,
                    run_id=run_id,
                    runner=runner,
                )

                outcome = await workflow.execute_c0_c5()

                self.assertEqual(outcome.hook_passed_refs, passed)
                self.assertEqual(
                    outcome.novelty_scan_refs,
                    (novelty_ref,) if novelty_ref is not None else (),
                )
                repair_tasks = [
                    task
                    for task in runner.tasks
                    if task.task_id.startswith("creative-c4-repair-")
                ]
                self.assertEqual(len(repair_tasks), 1)
                second_cycle_reviews = [
                    task
                    for task in runner.tasks
                    if task.task_id.startswith("creative-c4-review-")
                    and "-c2-" in task.task_id
                ]
                self.assertEqual(len(second_cycle_reviews), 2)

                state = workflow.hub.load_state()
                concept_revisions = sorted(
                    artifact_id
                    for artifact_id, record in state["artifacts"].items()
                    if record["artifact_type"] == "creative_concept"
                )
                self.assertEqual(
                    concept_revisions,
                    [
                        "creative-concept-s01-01-r001",
                        "creative-concept-s01-01-r002",
                    ],
                )
                disposition_rows = [
                    json.loads(workflow.hub.read_artifact(artifact_id))
                    for artifact_id, record in state["artifacts"].items()
                    if record["artifact_type"]
                    == "creative_concept_disposition"
                ]
                source_terminal = [
                    row
                    for row in disposition_rows
                    if row["concept_revision_ref"]
                    == "creative-concept-s01-01-r001"
                    and row["terminal"]
                ]
                self.assertEqual(len(source_terminal), 1)
                self.assertEqual(
                    source_terminal[0]["outcome"],
                    "superseded_by_hook_repair",
                )
                self.assertEqual(
                    source_terminal[0]["target_ref"],
                    "creative-concept-s01-01-r002",
                )
                repaired_dispositions = [
                    row
                    for row in disposition_rows
                    if row["concept_revision_ref"]
                    == "creative-concept-s01-01-r002"
                ]
                self.assertEqual(
                    repaired_dispositions[0]["outcome"],
                    final_outcome,
                )
                if final_outcome == "eliminated":
                    self.assertIn(
                        "c4_unresolved_after_repair",
                        repaired_dispositions[0]["reason_codes"],
                    )
                self.assertEqual(validate_run(workflow.run_dir), [])

    async def test_memory_recall_indexes_repaired_active_revision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            snapshot = _non_empty_memory_snapshot()
            runner = CreativeScriptedRunner(
                hook_mode="repair_success",
                memory_ref=snapshot.entries[0].memory_ref.to_dict(),
            )
            settings = CreativeWorkflowSettings(
                territory_explorers=1,
                max_atoms_per_territory=1,
                concept_synthesizers=1,
                max_concepts_per_synthesizer=1,
                idea_memory_mode="auto",
                memory_remixers=0,
                max_memory_challengers=0,
            )
            workflow = CreativeIdeaWorkflow.create(
                "Make a temporal interactive surprise.",
                directory,
                settings=settings,
                run_id="creative-repaired-memory-recall",
                runner=runner,
                memory_snapshot=snapshot,
            )

            outcome = await workflow.execute_c0_c5()

            self.assertEqual(
                outcome.hook_passed_refs,
                ("creative-concept-s01-01-r002",),
            )
            recall_task = next(
                task
                for task in runner.tasks
                if task.task_id == "creative-c5m-memory-recall-01"
            )
            self.assertIn(
                '"concept_revision_ref": "creative-concept-s01-01-r001"',
                recall_task.prompt,
            )
            self.assertIn(
                '"outcome": "superseded_by_hook_repair"',
                recall_task.prompt,
            )
            self.assertIn(
                '"concept_revision_ref": "creative-concept-s01-01-r002"',
                recall_task.prompt,
            )
            self.assertIn('"outcome": "pass"', recall_task.prompt)
            self.assertIn("that arrives sooner", recall_task.prompt)

            memory_summary = json.loads(
                workflow.hub.read_artifact(outcome.memory_summary_ref)
            )
            self.assertEqual(memory_summary["status"], "completed")
            self.assertEqual(
                memory_summary["selected_cue_ids"],
                ["memory-cue-01"],
            )
            self.assertEqual(
                memory_summary["recall"]["status"],
                "succeeded",
            )
            self.assertEqual(validate_run(workflow.run_dir), [])

    async def test_c5_contract_rejects_disappearing_results_and_fatal_invalidation(
        self,
    ) -> None:
        scenarios = (
            (
                "missing-c4-route",
                "final C4 routing outcome",
            ),
            (
                "missing-novelty",
                "must have exactly one Novelty Scan",
            ),
            (
                "fatal-invalidated",
                "failed in a non-failed run",
            ),
        )
        for mutation, expected_error in scenarios:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                runner = CreativeScriptedRunner()
                settings = CreativeWorkflowSettings(
                    territory_explorers=1,
                    max_atoms_per_territory=1,
                    concept_synthesizers=1,
                    max_concepts_per_synthesizer=1,
                    idea_memory_mode="off",
                    memory_remixers=0,
                    max_memory_challengers=0,
                )
                workflow = CreativeIdeaWorkflow.create(
                    "Keep every Creative candidate accountable.",
                    directory,
                    settings=settings,
                    run_id=mutation,
                    runner=runner,
                )
                await workflow.execute_c0_c5()
                state = workflow.hub.load_state()

                if mutation == "missing-c4-route":
                    disposition_id = next(
                        artifact_id
                        for artifact_id, record in state["artifacts"].items()
                        if record["artifact_type"]
                        == "creative_concept_disposition"
                        and record["metadata"]["outcome"] == "pass"
                    )
                    del state["artifacts"][disposition_id]
                elif mutation == "missing-novelty":
                    novelty_id = next(
                        artifact_id
                        for artifact_id, record in state["artifacts"].items()
                        if record["artifact_type"] == "creative_novelty_scan"
                    )
                    del state["artifacts"][novelty_id]
                else:
                    state["tasks"]["creative-c0-challenge-parse"][
                        "status"
                    ] = "invalidated"
                atomic_write_json(workflow.hub.state_path, state)

                self.assertTrue(
                    any(
                        expected_error in error
                        for error in validate_run(workflow.run_dir)
                    )
                )


if __name__ == "__main__":
    unittest.main()
