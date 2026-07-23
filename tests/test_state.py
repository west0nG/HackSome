from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from hacksome.state import (
    StateConflictError,
    append_jsonl,
    atomic_write_json,
    read_json_object,
    read_jsonl,
)


class StateTests(unittest.TestCase):
    def test_atomic_json_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            atomic_write_json(path, {"text": "中文", "count": 2})
            self.assertEqual(read_json_object(path), {"text": "中文", "count": 2})

    def test_jsonl_is_idempotent_by_stable_id(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            record = {"event_id": "event-1", "kind": "started"}
            self.assertTrue(append_jsonl(path, record, id_field="event_id"))
            self.assertFalse(append_jsonl(path, record, id_field="event_id"))
            self.assertEqual(read_jsonl(path), [record])

            with self.assertRaises(StateConflictError):
                append_jsonl(
                    path,
                    {"event_id": "event-1", "kind": "different"},
                    id_field="event_id",
                )


if __name__ == "__main__":
    unittest.main()
