from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from hacksome.prompting import (
    PromptRenderError,
    PromptRenderer,
    RenderedPrompt,
    schema_path,
)


COMMON_VARIABLES = {
    "run_id": "run-001",
    "task_id": "task-001",
    "language": "Chinese",
    "context_manifest": {},
    "output_target": "staging/output.md",
    "mode": "initial",
    "attempt": 1,
    "session_marker": "pending",
}


EXPECTED_HEADINGS = {
    "S2": (
        "Research Scope",
        "Evidence Candidates",
        "Query Log",
        "Counterevidence and Uncertainty",
        "Coverage Gaps",
    ),
    "S3": ("Verification Scope", "Evidence Checks", "Conflicts and Uncertainty"),
    "S4": (
        "Audience and Scenario",
        "Problem",
        "Observed Consequences",
        "Current Workarounds",
        "Frequency or Severity Signals",
        "Evidence",
        "Counterevidence and Uncertainty",
        "Search Gaps",
    ),
    "S5": ("Gateway Scope", "Threshold Checks", "Decision", "Evidence Gap"),
    "S6": (
        "User and Problem",
        "Trigger",
        "End-to-End User Flow",
        "Core Mechanism",
        "Minimum Necessary Features",
        "Improvement over Current Workaround",
        "Evidence",
        "Assumptions and Failure Modes",
        "Pending Checks",
    ),
    "S7": (
        "Research Scope",
        "Direct Competitors",
        "Indirect Alternatives and Workarounds",
        "Open Source Projects",
        "Adoption and Abandonment Evidence",
        "Overlap and Differences",
        "Sources and Query Log",
        "Counterevidence and Coverage Gaps",
    ),
    "S8": (
        "Target User",
        "Problem",
        "Felt Value",
        "User Flow",
        "Core Mechanism",
        "Minimum Features",
        "Alternatives and Adoption",
        "Sponsor Technology",
        "Evidence References",
        "Risks",
        "Revision Notes",
    ),
    "S9": (
        "Review Scope",
        "Felt Value",
        "Real User Flow",
        "Value Delivery",
        "Adoption Reason",
        "Problem Fidelity",
        "Decision",
    ),
    "S10": (
        "Review Scope",
        "Critical Path",
        "Deliverable Beta Scope",
        "Highest-Risk Dependencies",
        "Time and Integration",
        "Repeatable Demo",
        "Scope Integrity",
        "Decision",
    ),
}


class PromptRendererTests(unittest.TestCase):
    def setUp(self) -> None:
        self.renderer = PromptRenderer()

    def test_all_stage_templates_render_with_one_variable_contract(self) -> None:
        expected_variables = frozenset(COMMON_VARIABLES)
        for stage_number in range(11):
            stage = f"S{stage_number}"
            with self.subTest(stage=stage):
                self.assertEqual(
                    self.renderer.required_variables(stage), expected_variables
                )
                rendered = self.renderer.render(stage, COMMON_VARIABLES)
                self.assertIsInstance(rendered, RenderedPrompt)
                self.assertIn(f"# {stage} ", rendered.text)
                self.assertIn("Output language: Chinese", rendered.text)
                self.assertIn(
                    "Assigned output target: staging/output.md", rendered.text
                )
                self.assertEqual(
                    rendered.prompt_version,
                    {"S1": "2", "S4": "2", "S5": "3", "S9": "4"}.get(stage, "1"),
                )
                self.assertEqual(rendered.template_id, rendered.prompt_template_id)
                self.assertEqual(rendered.template_version, rendered.prompt_version)
                self.assertRegex(rendered.template_hash, r"^[0-9a-f]{64}$")
                self.assertRegex(rendered.prompt_hash, r"^[0-9a-f]{64}$")
                self.assertRegex(rendered.context_hash, r"^[0-9a-f]{64}$")

    def test_missing_variable_is_rejected(self) -> None:
        variables = dict(COMMON_VARIABLES)
        del variables["language"]
        with self.assertRaisesRegex(PromptRenderError, "missing variables: language"):
            self.renderer.render("S2", variables)

    def test_extra_variable_is_rejected(self) -> None:
        variables = {**COMMON_VARIABLES, "unexpected": "leak"}
        with self.assertRaisesRegex(
            PromptRenderError, "unexpected variables: unexpected"
        ):
            self.renderer.render("S2", variables)

    def test_template_missing_contract_placeholder_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            prompt_root = root / "prompts"
            prompt_root.mkdir()
            (prompt_root / "common.md").write_text("common\n", encoding="utf-8")
            placeholders = [
                "common_contract",
                "run_id",
                "task_id",
                "language",
                "context_manifest",
                "output_target",
                "attempt",
                "session_marker",
            ]
            (prompt_root / "s0-parse-challenge.md").write_text(
                "\n".join("{" + name + "}" for name in placeholders),
                encoding="utf-8",
            )
            renderer = PromptRenderer(root)
            with self.assertRaisesRegex(
                PromptRenderError, "unexpected variables: mode"
            ):
                renderer.render("S0", COMMON_VARIABLES)

    def test_template_extra_contract_placeholder_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            prompt_root = root / "prompts"
            prompt_root.mkdir()
            (prompt_root / "common.md").write_text("common\n", encoding="utf-8")
            placeholders = ["common_contract", *COMMON_VARIABLES, "rogue"]
            (prompt_root / "s0-parse-challenge.md").write_text(
                "\n".join("{" + name + "}" for name in placeholders),
                encoding="utf-8",
            )
            renderer = PromptRenderer(root)
            with self.assertRaisesRegex(PromptRenderError, "missing variables: rogue"):
                renderer.render("S0", COMMON_VARIABLES)

    def test_hashes_are_stable_across_mapping_order(self) -> None:
        first_manifest = {
            "artifacts": [{"artifact_type": "research", "path": "research/a/r.md"}],
            "audience_id": "audience-001",
        }
        second_manifest = {
            "audience_id": "audience-001",
            "artifacts": [{"path": "research/a/r.md", "artifact_type": "research"}],
        }
        first = self.renderer.render(
            "S4", {**COMMON_VARIABLES, "context_manifest": first_manifest}
        )
        second = self.renderer.render(
            "S4", {**COMMON_VARIABLES, "context_manifest": second_manifest}
        )
        self.assertEqual(first.context_hash, second.context_hash)
        self.assertEqual(first.prompt_hash, second.prompt_hash)
        self.assertEqual(first.template_hash, second.template_hash)

    def test_context_change_changes_input_and_prompt_hashes(self) -> None:
        first = self.renderer.render(
            "S2", {**COMMON_VARIABLES, "context_manifest": {"audience_id": "a-1"}}
        )
        second = self.renderer.render(
            "S2", {**COMMON_VARIABLES, "context_manifest": {"audience_id": "a-2"}}
        )
        self.assertNotEqual(first.context_hash, second.context_hash)
        self.assertNotEqual(first.prompt_hash, second.prompt_hash)
        self.assertEqual(first.template_hash, second.template_hash)

    def test_stage_aliases_are_supported_but_unknown_stage_is_not(self) -> None:
        self.assertEqual(
            self.renderer.render("parse_challenge", COMMON_VARIABLES).template_id,
            "hacksome.s0.parse-challenge",
        )
        with self.assertRaisesRegex(KeyError, "unknown prompt stage"):
            self.renderer.render("S11", COMMON_VARIABLES)

    def test_web_search_boundary_is_explicit_for_every_stage(self) -> None:
        allowed = {"S2", "S3", "S7"}
        for stage_number in range(11):
            stage = f"S{stage_number}"
            rendered = self.renderer.render(stage, COMMON_VARIABLES).text
            with self.subTest(stage=stage):
                if stage in allowed:
                    self.assertIn("Web search: allowed", rendered)
                else:
                    self.assertIn("Web search: forbidden", rendered)

    def test_required_markdown_headings_are_literal_english(self) -> None:
        for stage, headings in EXPECTED_HEADINGS.items():
            rendered = self.renderer.render(stage, COMMON_VARIABLES).text
            with self.subTest(stage=stage):
                for heading in headings:
                    self.assertIn(f"## {heading}\n", rendered)
                self.assertIn("Use the exact English Markdown headings", rendered)

    def test_common_contract_rejects_relative_selection_and_forced_diversity(
        self,
    ) -> None:
        rendered = self.renderer.render("S6", COMMON_VARIABLES).text
        self.assertIn("select a Top-K", rendered)
        self.assertIn("force different directions", rendered)
        self.assertIn("A truthful empty result is valid", rendered)

    def test_living_document_templates_preserve_original_creator(self) -> None:
        s4 = self.renderer.render("S4", COMMON_VARIABLES).text
        s8 = self.renderer.render("S8", COMMON_VARIABLES).text
        self.assertIn("routing.original_created_by_session", s4)
        self.assertIn("routing.original_created_by_session", s8)
        self.assertIn("revision-<N-1 zero-padded to 4>.md", s4)
        self.assertIn("revision-<N-1 zero-padded to 4>.md", s8)
        self.assertIn("never include the current canonical Problem path", s4)
        self.assertIn("never include the current canonical Idea path", s8)

    def test_routing_fields_are_required_in_stage_front_matter(self) -> None:
        s3 = self.renderer.render("S3", COMMON_VARIABLES).text
        s5 = self.renderer.render("S5", COMMON_VARIABLES).text
        s8 = self.renderer.render("S8", COMMON_VARIABLES).text
        self.assertIn("needs_second_verifier", s3)
        self.assertIn("recheck_evidence_ids", s3)
        self.assertIn("two-Verifier budget is exhausted", s3)
        self.assertIn("failed_thresholds", s5)
        self.assertIn("evidence_gaps", s5)
        self.assertIn("needs_competitor_research", s8)
        self.assertIn("competitor_research_gaps", s8)

    def test_s5_requires_problem_relevance_without_becoming_compliance_gate(
        self,
    ) -> None:
        s5 = self.renderer.render("S5", COMMON_VARIABLES).text
        self.assertIn("directly belongs to the challenge theme", s5)
        self.assertIn("Merely appearing in the challenge text", s5)
        self.assertIn("Do not read", s5)
        self.assertIn("`ComplianceView`", s5)

    def test_s9_draft_screen_has_a_narrow_pre_competition_contract(self) -> None:
        s9 = self.renderer.render(
            "S9",
            {**COMMON_VARIABLES, "mode": "draft_screen"},
        ).text

        self.assertIn("test only these four independent claims", s9)
        self.assertIn("adoption, switching, or alternatives", s9)
        self.assertIn("explicitly deferred until the full post-S8 review", s9)
        self.assertIn("without consuming the later product-repair budget", s9)
        self.assertIn("reviewed_idea_revision", s9)
        self.assertIn("reviewed_idea_sha256", s9)
        self.assertIn("Competition research does not exist yet and is forbidden", s9)
        self.assertIn("routing.draft_screen_policy_version", s9)
        self.assertIn("Version `3` is the current primary-outcome closure policy", s9)
        self.assertIn("Version `2` retains the strict causal-control rules", s9)
        self.assertIn("legacy policy-1 or policy-2 artifact", s9)
        self.assertIn(
            "Do not compare Ideas or reject one because another is similar", s9
        )
        self.assertIn("only `invalid` is an early elimination decision", s9)
        self.assertIn("Do not judge engineering difficulty", s9)

    def test_s9_draft_screen_does_not_treat_idea_claims_as_evidence(self) -> None:
        s9 = self.renderer.render(
            "S9",
            {**COMMON_VARIABLES, "mode": "draft_screen"},
        ).text

        self.assertIn("a claim to attack, never evidence", s9)
        self.assertIn("Do not quote or paraphrase the proposed mechanism as proof", s9)
        self.assertIn("Problem evidence can establish the user's Problem", s9)
        self.assertIn("Write the causal chain explicitly", s9)

    def test_s9_draft_screen_rejects_artifact_for_value_substitution(self) -> None:
        s9 = self.renderer.render(
            "S9",
            {**COMMON_VARIABLES, "mode": "draft_screen"},
        ).text

        self.assertIn("Distinguish the artifact the product produces", s9)
        self.assertIn("only after an uncontrolled third party responds or acts", s9)
        self.assertIn("the artifact itself already delivers material", s9)
        self.assertIn("not automatic proof that productizing that workaround", s9)
        self.assertIn("do not silently replace understanding", s9)

    def test_s9_draft_screen_requires_control_without_becoming_compliance(self) -> None:
        s9 = self.renderer.render(
            "S9",
            {**COMMON_VARIABLES, "mode": "draft_screen"},
        ).text

        self.assertIn("Naming an API, integration, internal manifest", s9)
        self.assertIn("does not establish access, permission, or authority", s9)
        self.assertIn("not merely engineering difficulty to defer to S10", s9)
        self.assertIn("authorized enterprise data, customer-owned data", s9)
        self.assertIn("Do not import a hackathon public-data rule", s9)

    def test_s9_draft_screen_limits_repairable_to_a_local_fix(self) -> None:
        s9 = self.renderer.render(
            "S9",
            {**COMMON_VARIABLES, "mode": "draft_screen"},
        ).text

        self.assertIn("same core trigger, core output, core mechanism", s9)
        self.assertIn("replacing any of those core elements", s9)
        self.assertIn("inventing control over a core dependency", s9)
        self.assertIn("set `invalid`", s9)

    def test_s9_policy_three_requires_primary_outcome_closure(self) -> None:
        s9 = self.renderer.render(
            "S9",
            {**COMMON_VARIABLES, "mode": "draft_screen"},
        ).text

        self.assertIn("passed Problem's `## Problem` section itself", s9)
        self.assertIn("Observed consequences may make the same Problem-native", s9)
        self.assertIn("`## Current Workarounds` can never redefine", s9)
        self.assertIn("Trigger -> primary output/action -> felt-value moment", s9)
        self.assertIn("optional field, secondary audience", s9)
        self.assertIn("reviewer-invented use", s9)
        self.assertIn("Reformatting facts the user already supplied", s9)
        self.assertIn("handing those facts to another actor", s9)
        self.assertIn("Apply the no-handoff counterfactual", s9)
        self.assertIn("does the immediate output materially improve", s9)
        self.assertIn("A partial solution may pass only", s9)
        self.assertIn("materially advances that same primary outcome", s9)
        self.assertGreaterEqual(s9.count("`Primary outcome:`"), 1)
        self.assertGreaterEqual(s9.count("`Immediate effect:`"), 1)
        self.assertGreaterEqual(s9.count("`Closure comparison:`"), 1)

    def test_s4_and_s5_bind_gateway_context_to_body_citations(self) -> None:
        s4 = self.renderer.render("S4", COMMON_VARIABLES).text
        s5 = self.renderer.render("S5", COMMON_VARIABLES).text

        self.assertIn("one single Markdown bullet", s4)
        self.assertIn("local Evidence id", s4)
        self.assertIn("verifier-002.md", s4)
        self.assertIn("never a copied `context/`, staging, excerpt", s4)
        self.assertIn("front-matter `source_refs` is not a citation", s4)
        self.assertIn("Counterevidence and Uncertainty", s4)
        self.assertIn("exact canonical Research and Verification subset", s5)
        self.assertIn("No uncited same-Audience file is available", s5)
        self.assertIn("Judge only from the cited subset", s5)

    def test_s1_requires_independent_domain_relevance_for_audiences(self) -> None:
        s1 = self.renderer.render("S1", COMMON_VARIABLES).text
        self.assertIn("including `explicit_audiences`, as clues", s1)
        self.assertIn("rather than a list that must appear in the output", s1)
        self.assertIn("theme or `problem_domains` independently ties", s1)
        self.assertIn("directly experiences or participates in inside the domain", s1)
        self.assertIn("participant, judge, organizer, submission actor", s1)
        self.assertIn("evidence author, or public-data source", s1)
        self.assertIn("name that domain role instead of the meta role", s1)
        self.assertIn("saying only that the prompt or `explicit_audiences`", s1)

    def test_s1_rejects_compliance_context_leakage(self) -> None:
        leaked = {
            "artifacts": [
                {
                    "artifact_type": "compliance_view",
                    "path": "context/compliance.json",
                }
            ]
        }
        with self.assertRaisesRegex(
            PromptRenderError, "crosses its stage boundary: compliance_view"
        ):
            self.renderer.render("S1", {**COMMON_VARIABLES, "context_manifest": leaked})

    def test_each_stage_accepts_its_declared_artifact_types(self) -> None:
        allowed = {
            "S0": ("raw_challenge",),
            "S1": ("discovery_view",),
            "S2": ("discovery_view", "audience"),
            "S3": ("audience", "research"),
            "S4": ("discovery_view", "audience", "research", "verification"),
            "S5": ("discovery_view", "problem", "research", "verification"),
            "S6": (
                "discovery_view",
                "problem",
                "problem_gateway",
                "research",
                "verification",
            ),
            "S7": (
                "idea",
                "problem",
                "problem_gateway",
                "research",
                "verification",
            ),
            "S8": (
                "idea",
                "problem",
                "problem_gateway",
                "research",
                "verification",
                "competition",
                "compliance_view",
            ),
            "S9": (
                "idea",
                "problem",
                "problem_gateway",
                "research",
                "verification",
                "competition",
            ),
            "S10": ("idea", "idea_red_team"),
        }
        for stage, artifact_types in allowed.items():
            manifest = {
                "artifacts": [
                    {"artifact_type": artifact_type} for artifact_type in artifact_types
                ]
            }
            with self.subTest(stage=stage):
                self.renderer.render(
                    stage, {**COMMON_VARIABLES, "context_manifest": manifest}
                )

    def test_blind_reviews_reject_prior_review_paths(self) -> None:
        s3_leak = {
            "artifacts": [
                {
                    "artifact_type": "verification",
                    "path": "verification/a/r/verifier-001.md",
                }
            ]
        }
        with self.assertRaisesRegex(PromptRenderError, "verification"):
            self.renderer.render(
                "S3", {**COMMON_VARIABLES, "context_manifest": s3_leak}
            )

        s9_leak = {"artifacts": [{"path": "idea-reviews/i/red-team-001.md"}]}
        with self.assertRaisesRegex(PromptRenderError, "idea_red_team"):
            self.renderer.render(
                "S9", {**COMMON_VARIABLES, "context_manifest": s9_leak}
            )

    def test_s8_allows_only_the_review_matching_its_repair_mode(self) -> None:
        red_team = {"artifacts": [{"artifact_type": "idea_red_team"}]}
        feasibility = {"artifacts": [{"artifact_type": "feasibility"}]}

        self.renderer.render(
            "S8",
            {
                **COMMON_VARIABLES,
                "mode": "product_repair",
                "context_manifest": red_team,
            },
        )
        with self.assertRaisesRegex(PromptRenderError, "feasibility"):
            self.renderer.render(
                "S8",
                {
                    **COMMON_VARIABLES,
                    "mode": "product_repair",
                    "context_manifest": feasibility,
                },
            )

        self.renderer.render(
            "S8",
            {
                **COMMON_VARIABLES,
                "mode": "scope_reduction",
                "context_manifest": feasibility,
            },
        )
        with self.assertRaisesRegex(PromptRenderError, "idea_red_team"):
            self.renderer.render(
                "S8",
                {
                    **COMMON_VARIABLES,
                    "mode": "scope_reduction",
                    "context_manifest": red_team,
                },
            )


class PromptSchemaTests(unittest.TestCase):
    def test_packaged_schemas_avoid_codex_unsupported_keywords(self) -> None:
        unsupported = {"uniqueItems"}

        def visit(node: object, path: str = "$") -> None:
            if isinstance(node, dict):
                for key, value in node.items():
                    self.assertNotIn(key, unsupported, f"{path}.{key}")
                    visit(value, f"{path}.{key}")
            elif isinstance(node, list):
                for index, value in enumerate(node):
                    visit(value, f"{path}[{index}]")

        for name in ("s0", "s1", "completion"):
            with self.subTest(schema=name):
                visit(json.loads(schema_path(name).read_text(encoding="utf-8")))

    def test_schema_paths_and_aliases_resolve_to_packaged_json(self) -> None:
        self.assertEqual(
            schema_path("s0"), PromptRenderer.schema_path("challenge-brief")
        )
        self.assertEqual(schema_path("s1"), PromptRenderer.schema_path("audience-list"))
        self.assertEqual(
            schema_path("completion"),
            PromptRenderer.schema_path("completion-envelope"),
        )
        for name in ("s0", "s1", "completion"):
            path = schema_path(name)
            self.assertTrue(path.is_file())
            json.loads(path.read_text(encoding="utf-8"))
        with self.assertRaisesRegex(KeyError, "unknown schema"):
            schema_path("s9")

    def test_every_object_schema_rejects_additional_properties(self) -> None:
        def visit(node: object) -> None:
            if isinstance(node, dict):
                if node.get("type") == "object":
                    self.assertIs(node.get("additionalProperties"), False)
                    self.assertEqual(
                        set(node.get("required", [])),
                        set(node.get("properties", {})),
                    )
                for value in node.values():
                    visit(value)
            elif isinstance(node, list):
                for value in node:
                    visit(value)

        for name in ("s0", "s1", "completion"):
            with self.subTest(schema=name):
                schema = json.loads(schema_path(name).read_text(encoding="utf-8"))
                visit(schema)

    def test_s0_keeps_discovery_and_compliance_fields_separate(self) -> None:
        schema = json.loads(schema_path("s0").read_text(encoding="utf-8"))
        discovery = schema["properties"]["discovery_view"]["properties"]
        compliance = schema["properties"]["compliance_view"]["properties"]
        self.assertNotIn("required_technologies", discovery)
        self.assertNotIn("sponsor_requirements", discovery)
        self.assertIn("required_technologies", compliance)
        self.assertIn("sponsor_requirements", compliance)

    def test_s1_schema_allows_an_empty_unranked_audience_list(self) -> None:
        schema = json.loads(schema_path("s1").read_text(encoding="utf-8"))
        audiences = schema["properties"]["audiences"]
        self.assertNotIn("minItems", audiences)
        audience_fields = audiences["items"]["properties"]
        self.assertEqual(
            set(audience_fields),
            {"audience_id", "name", "kind", "direct_relevance", "search_aliases"},
        )
        self.assertNotIn("rank", audience_fields)
        self.assertNotIn("scenario", audience_fields)
        self.assertNotIn("pain", audience_fields)

    def test_completion_envelope_is_lightweight(self) -> None:
        schema = json.loads(schema_path("completion").read_text(encoding="utf-8"))
        self.assertEqual(
            set(schema["properties"]),
            {"schema_version", "run_id", "task_id", "status", "output_paths"},
        )
        self.assertEqual(schema["properties"]["status"]["enum"], ["completed", "empty"])
        self.assertNotIn("content", schema["properties"])
        self.assertNotIn("summary", schema["properties"])


if __name__ == "__main__":
    unittest.main()
