from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path
from typing import Any
from unittest.mock import patch

from hacksome.config import CodexConfig
from hacksome.hub import RUN_SCHEMA_VERSION, RunHub
from hacksome.prompting import useful_prompt_catalog
from hacksome.state import (
    StateConflictError,
    StateError,
    atomic_write_json,
    atomic_write_text,
    read_jsonl,
    sha256_text,
)


class RunHubTests(unittest.TestCase):
    def create_hub(self, root: Path, *, route: str = "useful") -> RunHub:
        hub = RunHub.create(
            "Build something memorable",
            root,
            settings={"max_audiences": 2},
            codex_config=CodexConfig(),
            run_id="run-001",
            route=route,
        )
        frozen = useful_prompt_catalog.freeze(
            hub.run_dir,
            route_id="useful",
            contract_version="1",
            prompt_policy_version="1",
            stage_policy_version="1",
        )
        hub.set_resource_manifest(frozen.manifest_reference())
        return hub

    def test_legacy_projection_is_strictly_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory) / "legacy"
            (run_dir / "input").mkdir(parents=True)
            (run_dir / "tasks").mkdir()
            (run_dir / "artifacts").mkdir()
            challenge = "Legacy challenge"
            atomic_write_text(run_dir / "input" / "challenge.md", challenge)
            atomic_write_text(run_dir / "events.jsonl", "")
            atomic_write_text(run_dir / "decisions.jsonl", "")
            atomic_write_json(
                run_dir / "run.json",
                {
                    "schema_version": 1,
                    "run_id": "legacy",
                    "status": "completed",
                    "current_stage": None,
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "updated_at": "2026-01-01T00:00:00+00:00",
                    "input": {
                        "path": "input/challenge.md",
                        "sha256": sha256_text(challenge),
                    },
                    "settings": {},
                    "codex_config": asdict(CodexConfig()),
                    "tasks": {},
                    "artifacts": {},
                    "idea_card_ids": [],
                },
            )

            hub = RunHub(run_dir)
            projected = hub.load_state()
            self.assertEqual(projected["route"]["id"], "useful")
            self.assertEqual(projected["inputs"]["challenge"], projected["input"])
            self.assertFalse((run_dir / "run.lock").exists())
            self.assertEqual(hub.inspect()["idea_card_count"], 0)
            self.assertEqual(hub.validate(), [])
            self.assertFalse((run_dir / "run.lock").exists())
            with self.assertRaisesRegex(StateError, "strictly read-only"):
                hub.set_run_status("running", stage="legacy")
            self.assertFalse((run_dir / "run.lock").exists())

    def test_new_run_is_v2_and_codex_tuple_fields_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            hub = self.create_hub(Path(directory))
            state = hub.load_raw_state()
            self.assertEqual(state["schema_version"], RUN_SCHEMA_VERSION)
            self.assertEqual(state["route"]["id"], "useful")
            self.assertTrue(hub.lock_path.is_file())
            self.assertEqual(state["pending_records"], [])
            self.assertEqual(hub.load_codex_config(), CodexConfig())
            self.assertIsInstance(state["codex_config"]["disabled_features"], list)
            self.assertEqual(
                [row["event_id"] for row in read_jsonl(hub.events_path)],
                ["run:created"],
            )

    def test_status_transition_has_unique_sequence_and_immutable_first_error(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            hub = self.create_hub(Path(directory))
            hub.set_run_status("running", stage="same")
            hub.set_run_status("running", stage="same")
            hub.set_run_status("failed", stage="same", error=ValueError("first"))
            hub.set_run_status("failed", stage="report", error=RuntimeError("second"))
            state = hub.load_raw_state()
            self.assertEqual(state["transition_seq"], 4)
            self.assertEqual(state["terminal_error"]["kind"], "ValueError")
            self.assertEqual(state["terminal_error"]["message"], "first")
            self.assertEqual(len(state["secondary_errors"]), 1)
            ids = [
                row["event_id"]
                for row in read_jsonl(hub.events_path)
                if row["event_id"].startswith("run:transition:")
            ]
            self.assertEqual(
                ids,
                [
                    "run:transition:00000001",
                    "run:transition:00000002",
                    "run:transition:00000003",
                    "run:transition:00000004",
                ],
            )
            self.assertEqual(hub.validate(), [])

    def test_pending_transition_reconciles_with_original_record(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            hub = self.create_hub(Path(directory))
            with patch("hacksome.hub.append_jsonl", side_effect=OSError("crash")):
                with self.assertRaisesRegex(OSError, "crash"):
                    hub.set_run_status("running", stage="challenge-parse")
            raw = hub.load_raw_state()
            self.assertEqual(raw["status"], "running")
            self.assertEqual(len(raw["pending_records"]), 1)
            pending_record = raw["pending_records"][0]["record"]
            self.assertTrue(hub.core_inspect()["needs_reconcile"])

            self.assertEqual(hub.reconcile_pending(), 1)
            event = read_jsonl(hub.events_path)[-1]
            self.assertEqual(event, pending_record)
            self.assertEqual(hub.reconcile_pending(), 0)
            self.assertEqual(hub.validate(), [])

    def test_decision_outbox_is_idempotent_and_preserves_useful_shape(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            hub = self.create_hub(Path(directory))
            kwargs = {
                "decision_id": "decision-1",
                "gate": "problem-gateway",
                "candidate_ref": "problem-1",
                "decision": "pass",
                "review_ref": "review-1",
                "task_id": "task-1",
            }
            hub.record_decision(**kwargs)
            first = read_jsonl(hub.decisions_path)[0]
            hub.record_decision(**kwargs)
            self.assertEqual(read_jsonl(hub.decisions_path), [first])
            self.assertEqual(
                set(first),
                {
                    "decision_id",
                    "gate",
                    "candidate_ref",
                    "decision",
                    "review_ref",
                    "task_id",
                    "created_at",
                },
            )
            with self.assertRaises(StateConflictError):
                hub.append_decision(
                    {
                        **kwargs,
                        "decision": "reject",
                    }
                )

    def test_artifact_publish_idempotency_adoption_and_conflicts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            hub = self.create_hub(Path(directory))
            arguments: dict[str, Any] = {
                "artifact_id": "artifact-1",
                "artifact_type": "note",
                "relative_path": "artifacts/notes/one.md",
                "content": "same bytes",
                "task_id": None,
            }
            self.assertEqual(hub.publish_artifact(**arguments), "artifact-1")
            first_state = hub.load_raw_state()["artifacts"]["artifact-1"]
            self.assertEqual(hub.publish_artifact(**arguments), "artifact-1")
            self.assertEqual(
                hub.load_raw_state()["artifacts"]["artifact-1"],
                first_state,
            )
            with self.assertRaises(StateConflictError):
                hub.publish_artifact(**{**arguments, "content": "different"})
            with self.assertRaises(StateConflictError):
                hub.publish_artifact(
                    **{
                        **arguments,
                        "artifact_id": "artifact-2",
                    }
                )

            adopt_path = hub.run_dir / "artifacts" / "notes" / "adopt.md"
            atomic_write_text(adopt_path, "adopt me")
            hub.publish_artifact(
                artifact_id="artifact-adopted",
                artifact_type="note",
                relative_path="artifacts/notes/adopt.md",
                content="adopt me",
                task_id=None,
            )
            self.assertEqual(hub.read_artifact("artifact-adopted"), "adopt me")
            self.assertEqual(hub.validate(), [])

    def test_registered_missing_file_and_unregistered_orphan_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            hub = self.create_hub(Path(directory))
            arguments: dict[str, Any] = {
                "artifact_id": "artifact-1",
                "artifact_type": "note",
                "relative_path": "artifacts/one.md",
                "content": "content",
                "task_id": None,
            }
            hub.publish_artifact(**arguments)
            (hub.run_dir / "artifacts" / "one.md").unlink()
            with self.assertRaisesRegex(StateError, "registered.*missing"):
                hub.publish_artifact(**arguments)
            self.assertTrue(
                any("artifact artifact-1 is missing" in error for error in hub.validate())
            )

            orphan = hub.run_dir / "artifacts" / "orphan.md"
            atomic_write_text(orphan, "orphan")
            self.assertTrue(
                any("unregistered artifact file" in error for error in hub.validate())
            )

    def test_invalid_failure_policy_is_rejected_before_task_files_exist(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            hub = self.create_hub(Path(directory))
            with self.assertRaisesRegex(ValueError, "failure policy"):
                hub.begin_task(
                    task_id="task-1",
                    stage="stage",
                    prompt="prompt",
                    prompt_metadata={},
                    output_schema=Path(__file__),
                    web_search=False,
                    parent_refs=[],
                    failure_policy="best_effort",
                )
            self.assertFalse(hub.task_paths("task-1").root.exists())

    def test_run_json_is_strict_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            hub = self.create_hub(Path(directory))
            json.loads(hub.state_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
