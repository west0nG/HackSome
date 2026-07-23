from __future__ import annotations

import tempfile
import unittest

from hacksome.config import CodexConfig
from hacksome.creative.contracts import CreativeWorkflowSettings
from hacksome.creative.workflow import CreativeIdeaWorkflow
from hacksome.hub import RunHub
from hacksome.prompting import useful_prompt_catalog
from hacksome.routes import get_run_contract, inspect_run, validate_run
from hacksome.state import atomic_write_json, sha256_file


class RouteContractTests(unittest.TestCase):
    def freeze_useful_manifest(self, hub: RunHub) -> None:
        frozen = useful_prompt_catalog.freeze(
            hub.run_dir,
            route_id="useful",
            contract_version="1",
            prompt_policy_version="1",
            stage_policy_version="1",
        )
        hub.set_resource_manifest(frozen.manifest_reference())

    def freeze_placeholder_manifest(self, hub: RunHub) -> None:
        path = hub.run_dir / "resources" / "manifest.json"
        atomic_write_json(path, {})
        hub.set_resource_manifest(
            {"path": "resources/manifest.json", "sha256": sha256_file(path)}
        )

    def test_useful_projection_preserves_existing_inspect_fields(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            hub = RunHub.create(
                "challenge",
                directory,
                settings={},
                codex_config=CodexConfig(),
                run_id="useful-run",
            )
            self.freeze_useful_manifest(hub)
            projection = inspect_run(hub.run_dir)
            self.assertEqual(
                list(projection),
                [
                    "run_id",
                    "status",
                    "current_stage",
                    "task_counts",
                    "decision_count",
                    "idea_card_count",
                    "run_dir",
                ],
            )
            self.assertEqual(validate_run(hub.run_dir), [])

    def test_creative_route_uses_registered_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workflow = CreativeIdeaWorkflow.create(
                "challenge",
                directory,
                run_id="creative-run",
                settings=CreativeWorkflowSettings(idea_memory_mode="off"),
            )
            projection = inspect_run(workflow.run_dir)
            self.assertEqual(projection["route_id"], "creative")
            self.assertEqual(validate_run(workflow.run_dir), [])

    def test_unknown_route_and_contract_version_are_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            hub = RunHub.create(
                "challenge",
                directory,
                settings={},
                codex_config=CodexConfig(),
                run_id="unknown-run",
            )
            self.freeze_placeholder_manifest(hub)
            state = hub.load_raw_state()
            state["route"]["id"] = "unknown"
            atomic_write_json(hub.state_path, state)
            self.assertIn("unknown run route", validate_run(hub.run_dir)[0])

            state["route"]["id"] = "useful"
            state["route"]["contract_version"] = "999"
            atomic_write_json(hub.state_path, state)
            self.assertIn("unsupported 'useful' contract", validate_run(hub.run_dir)[0])

    def test_contract_resolution_accepts_projected_v1_useful(self) -> None:
        state = {
            "schema_version": 1,
            "route": {"id": "useful", "contract_version": "1"},
        }
        self.assertEqual(get_run_contract(state).route_id, "useful")


if __name__ == "__main__":
    unittest.main()
