from __future__ import annotations

import tempfile
import threading
import unittest
from pathlib import Path

from hacksome.state import (
    RunState,
    RunStatus,
    StateConflictError,
    StateFormatError,
    StateStore,
    TaskRecord,
    TaskStatus,
    append_jsonl_once,
    atomic_write_json,
    read_json,
    read_jsonl,
    reconcile_task_outputs,
    stable_task_id,
)


class JsonStorageTests(unittest.TestCase):
    def test_atomic_json_round_trip_replaces_complete_value(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "state.json"
            atomic_write_json(path, {"message": "你好", "value": 1})
            self.assertEqual(read_json(path), {"message": "你好", "value": 1})
            atomic_write_json(path, {"value": 2})
            self.assertEqual(read_json(path), {"value": 2})
            self.assertEqual(list(path.parent.glob(f".{path.name}.*.tmp")), [])

    def test_invalid_json_has_path_and_location(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "state.json"
            path.write_text('{"broken":', encoding="utf-8")
            with self.assertRaisesRegex(StateFormatError, "line 1"):
                read_json(path)
            path.write_text('{"same": 1, "same": 2}', encoding="utf-8")
            with self.assertRaisesRegex(StateFormatError, "duplicate JSON object key"):
                read_json(path)

    def test_jsonl_append_is_idempotent_and_conflict_safe(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "events.jsonl"
            record = {"event_id": "event-001", "kind": "task_completed"}
            self.assertTrue(append_jsonl_once(path, record, id_field="event_id"))
            self.assertFalse(append_jsonl_once(path, record, id_field="event_id"))
            self.assertEqual(read_jsonl(path), [record])
            with self.assertRaises(StateConflictError):
                append_jsonl_once(
                    path,
                    {"event_id": "event-001", "kind": "different"},
                    id_field="event_id",
                )
            self.assertEqual(read_jsonl(path), [record])

    def test_jsonl_rejects_partial_or_non_object_lines(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "events.jsonl"
            path.write_text('{"event_id":"one"}\n{"event_id":', encoding="utf-8")
            with self.assertRaisesRegex(StateFormatError, "events.jsonl:2"):
                read_jsonl(path)
            path.write_text("[]\n", encoding="utf-8")
            with self.assertRaisesRegex(StateFormatError, "JSON object"):
                read_jsonl(path)

    def test_jsonl_refuses_a_symlinked_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "actual.jsonl"
            target.write_text('{"event_id":"outside"}\n', encoding="utf-8")
            link = root / "events.jsonl"
            link.symlink_to(target)

            with self.assertRaisesRegex(StateFormatError, "symlink"):
                read_jsonl(link)
            with self.assertRaisesRegex(StateFormatError, "symlink"):
                append_jsonl_once(
                    link,
                    {"event_id": "event-001"},
                    id_field="event_id",
                )


class StateContractTests(unittest.TestCase):
    def test_stable_task_id_is_deterministic_and_stage_scoped(self) -> None:
        first = stable_task_id("S2", "audience-001", {"round": 1})
        second = stable_task_id("S2", "audience-001", {"round": 1})
        self.assertEqual(first, second)
        self.assertNotEqual(first, stable_task_id("S3", "audience-001", {"round": 1}))
        self.assertRegex(first, r"^s2-[0-9a-f]{20}$")

    def test_task_and_run_state_round_trip_preserves_extensible_data(self) -> None:
        task = TaskRecord.create(
            "S2",
            "audience-001",
            status=TaskStatus.COMPLETED,
            attempts=1,
            session_id="session-001",
            outputs=["research/audience-001/researcher-001.md"],
            data={"prompt_hash": "abc"},
        )
        state = RunState(
            run_id="run-001",
            current_stage="S2",
            status=RunStatus.RUNNING,
            tasks={task.task_id: task},
            completed_artifacts=list(task.outputs),
            next_actions=["schedule-verification"],
            data={
                "raw_input": "inputs/challenge.md",
                "settings": {"researchers": 3},
                "branch_budgets": {"problem-001": {"evidence_loops": 1}},
                "final_ideas": [],
                "eliminations": [],
            },
        )

        restored = RunState.from_dict(state.to_dict())

        self.assertEqual(restored.to_dict(), state.to_dict())
        self.assertTrue(restored.is_task_complete(task.task_id))
        self.assertEqual(restored.data["settings"], {"researchers": 3})
        self.assertFalse(restored.tasks[task.task_id].allow_empty_outputs)
        self.assertTrue(TaskRecord(task_id="empty-s4", stage="S4").allow_empty_outputs)

    def test_task_mapping_must_match_embedded_id(self) -> None:
        task = TaskRecord(task_id="task-one", stage="S2")
        with self.assertRaisesRegex(StateFormatError, "does not match"):
            RunState(run_id="run-001", tasks={"task-two": task})

    def test_invalid_status_and_non_json_data_are_rejected(self) -> None:
        with self.assertRaisesRegex(StateFormatError, "task status"):
            TaskRecord(task_id="task", stage="S2", status="unknown")
        with self.assertRaisesRegex(StateFormatError, "valid JSON"):
            RunState(run_id="run-001", data={"bad": {1, 2}})  # type: ignore[dict-item]
        with self.assertRaisesRegex(StateFormatError, "schema_version"):
            RunState(run_id="run-001", schema_version=True)
        with self.assertRaisesRegex(StateFormatError, "task entries"):
            RunState.from_dict({"run_id": "run-001", "tasks": {"bad": []}})
        with self.assertRaisesRegex(StateFormatError, "cannot be overridden"):
            TaskRecord(
                task_id="bad-empty-policy",
                stage="S3",
                allow_empty_outputs=True,
            )


class StateStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.run_dir = Path(self.temporary.name) / "run-001"
        self.store = StateStore(self.run_dir)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_initialize_mutate_and_ledger_helpers(self) -> None:
        initialized = self.store.initialize("run-001", data={"counter": 0})
        self.assertEqual(initialized.run_id, "run-001")

        task = TaskRecord.create("S2", "audience-001")

        def update(state: RunState) -> None:
            state.current_stage = "S2"
            state.status = RunStatus.RUNNING
            state.data["counter"] = 1
            state.upsert_task(task)

        updated = self.store.mutate(update)
        self.assertEqual(updated.data["counter"], 1)
        self.assertEqual(updated.state_revision, 1)
        self.assertIn(task.task_id, self.store.load().tasks)

        event = {"event_id": "event-001", "kind": "task_started"}
        decision = {"decision_id": "decision-001", "outcome": "pass"}
        self.assertTrue(self.store.append_event(event))
        self.assertFalse(self.store.append_event(event))
        self.assertTrue(self.store.append_decision(decision))
        self.assertEqual(self.store.events(), [event])
        self.assertEqual(self.store.decisions(), [decision])

    def test_initialize_rejects_a_different_run(self) -> None:
        self.store.initialize("run-001")
        with self.assertRaises(StateConflictError):
            self.store.initialize("run-other")

    def test_failed_mutation_does_not_change_state(self) -> None:
        self.store.initialize("run-001", data={"value": 1})

        def fail(state: RunState) -> None:
            state.data["value"] = 2
            raise RuntimeError("stop")

        with self.assertRaisesRegex(RuntimeError, "stop"):
            self.store.mutate(fail)
        self.assertEqual(self.store.load().data["value"], 1)

    def test_stale_save_cannot_overwrite_a_newer_mutation(self) -> None:
        self.store.initialize("run-001", data={"value": 0})
        stale = self.store.load()

        def advance(state: RunState) -> None:
            state.data["value"] = 1

        current = self.store.mutate(advance)
        stale.data["value"] = -1
        with self.assertRaisesRegex(StateConflictError, "stale state revision"):
            self.store.save(stale)
        self.assertEqual(self.store.load().data["value"], 1)
        self.assertEqual(self.store.load().state_revision, current.state_revision)

    def test_concurrent_mutations_do_not_lose_updates(self) -> None:
        self.store.initialize("run-001", data={"counter": 0})
        thread_count = 8
        increments = 20

        def worker() -> None:
            for _ in range(increments):
                def increment(state: RunState) -> None:
                    current = state.data["counter"]
                    assert isinstance(current, int)
                    state.data["counter"] = current + 1

                self.store.mutate(increment)

        threads = [threading.Thread(target=worker) for _ in range(thread_count)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(self.store.load().data["counter"], thread_count * increments)


class ReconciliationTests(unittest.TestCase):
    def test_reconciliation_distinguishes_skip_recover_and_rerun(self) -> None:
        tasks = {
            "complete-good": TaskRecord(
                task_id="complete-good",
                stage="S2",
                status=TaskStatus.COMPLETED,
                outputs=["good.md"],
            ),
            "complete-empty": TaskRecord(
                task_id="complete-empty",
                stage="S4",
                status=TaskStatus.COMPLETED,
                outputs=[],
            ),
            "complete-unexpected-empty": TaskRecord(
                task_id="complete-unexpected-empty",
                stage="S3",
                status=TaskStatus.COMPLETED,
                outputs=[],
            ),
            "complete-missing": TaskRecord(
                task_id="complete-missing",
                stage="S3",
                status=TaskStatus.COMPLETED,
                outputs=["missing.md"],
            ),
            "failed-valid": TaskRecord(
                task_id="failed-valid",
                stage="S7",
                status=TaskStatus.FAILED,
                outputs=["recoverable.md"],
            ),
            "waiting-invalid": TaskRecord(
                task_id="waiting-invalid",
                stage="S8",
                status=TaskStatus.WAITING,
                outputs=["bad.md"],
            ),
        }
        state = RunState(run_id="run-001", tasks=tasks)
        # Reconciliation derives this permission from the stage contract even
        # if an in-memory caller tampers with the convenience field.
        tasks["complete-unexpected-empty"].allow_empty_outputs = True

        def validate(path: str) -> bool:
            if path == "missing.md":
                raise FileNotFoundError(path)
            if path == "bad.md":
                raise ValueError("bad front matter")
            return True

        report = reconcile_task_outputs(
            state,
            validate,
            discovered_outputs=["good.md", "recoverable.md", "orphan.md"],
        )

        self.assertEqual(
            report.skippable_task_ids,
            ("complete-empty", "complete-good"),
        )
        self.assertEqual(report.recoverable_task_ids, ("failed-valid",))
        self.assertEqual(report.incomplete_task_ids, ("waiting-invalid",))
        self.assertEqual(
            report.stale_completed_task_ids,
            ("complete-missing", "complete-unexpected-empty"),
        )
        self.assertEqual(
            report.unexpected_empty_task_ids,
            ("complete-unexpected-empty",),
        )
        self.assertEqual(report.missing_outputs["complete-missing"], ("missing.md",))
        self.assertIn("ValueError", report.invalid_outputs["waiting-invalid"]["bad.md"])
        self.assertEqual(report.orphan_outputs, ("orphan.md",))
        self.assertTrue(report.can_skip("complete-good"))
        self.assertFalse(report.clean)


if __name__ == "__main__":
    unittest.main()
