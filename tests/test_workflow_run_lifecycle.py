from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from hacksome.state import RunState, RunStatus, StateStore, atomic_write_bytes
from hacksome.workflow import UsefulIdeaWorkflow, WorkflowError


class WorkflowRunLifecycleTests(unittest.IsolatedAsyncioTestCase):
    async def test_cancelled_run_cannot_be_resumed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary) / "cancelled-run"
            run_dir.mkdir()
            challenge = b"one benchmark only\n"
            atomic_write_bytes(run_dir / "challenge.md", challenge)
            store = StateStore(run_dir)
            store.initialize(
                "cancelled-run",
                data={
                    "challenge_ref": "challenge.md",
                    "challenge_sha256": hashlib.sha256(challenge).hexdigest(),
                    "workflow_topology_version": 2,
                },
            )

            def cancel(state: RunState) -> None:
                state.status = RunStatus.CANCELLED
                state.next_actions = []

            store.mutate(cancel)
            workflow = UsefulIdeaWorkflow(run_dir)

            with self.assertRaisesRegex(
                WorkflowError, "cancelled run cannot be resumed"
            ):
                await workflow.execute()


if __name__ == "__main__":
    unittest.main()
