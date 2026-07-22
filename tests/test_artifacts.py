from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from hacksome.artifacts import (
    STAGE_ARTIFACT_SPECS,
    ArtifactConflictError,
    ArtifactDocument,
    ArtifactFormatError,
    ArtifactStore,
    ArtifactValidationError,
    PromotionRequest,
    UnsafePathError,
    expected_canonical_path,
    extract_sections,
    parse_markdown,
    safe_join,
    safe_relative_path,
    serialize_markdown,
    required_manifest_binding_fields,
    validate_document,
    validate_source_refs,
)


def metadata_for(stage: str, **overrides: object) -> dict[str, object]:
    spec = STAGE_ARTIFACT_SPECS[stage]
    revision = 2 if stage == "S8" else 1
    metadata: dict[str, object] = {
        "schema_version": 1,
        "artifact_id": f"artifact-{stage.lower()}",
        "artifact_type": spec.artifact_type,
        "run_id": "run-001",
        "stage": stage,
        "status": {
            "S5": "pass",
            "S9": "pass",
            "S10": "feasible",
        }.get(stage, sorted(spec.statuses)[0]),
        "revision": revision,
        "created_by_session": "session-creator",
        "updated_by_session": "session-updater",
        "source_refs": ["inputs/context.json"],
        "supersedes": (
            "revisions/ideas/audience-001/writer-001/problem-001/"
            "generator-001/idea-001/revision-0001.md"
            if revision > 1
            else None
        ),
    }
    routing_defaults: dict[str, object] = {
        "audience_id": "audience-001",
        "researcher_id": "researcher-001",
        "research_round": 1,
        "research_ref": "research/audience-001/researcher-001.md",
        "verifier_id": "verifier-001",
        "verification_round": 1,
        "writer_id": "writer-001",
        "problem_id": "problem-001",
        "problem_ref": "problems/audience-001/writer-001/problem-001.md",
        "gateway_id": "gateway-001",
        "gateway_mode": "initial",
        "evidence_loop_count": 0,
        "generator_id": "generator-001",
        "idea_id": "idea-001",
        "revision_reason": "competition_research",
        "idea_ref": (
            "ideas/audience-001/writer-001/problem-001/"
            "generator-001/idea-001.md"
        ),
        "red_team_id": "red-team-001",
        "review_mode": "initial",
        "review_id": "review-001",
    }
    for key in spec.required_metadata:
        if key in routing_defaults:
            metadata[key] = routing_defaults[key]
        elif key in {"needs_second_verifier", "needs_competitor_research"}:
            metadata[key] = False
        elif key in {
            "recheck_evidence_ids",
            "failed_thresholds",
            "evidence_gaps",
            "competitor_research_gaps",
        }:
            metadata[key] = []
        else:
            metadata[key] = f"value-{key}"
    metadata.update(overrides)
    return metadata


def body_for(stage: str, *, omit: str | None = None) -> str:
    lines: list[str] = []
    for heading in STAGE_ARTIFACT_SPECS[stage].required_headings:
        if heading == omit:
            continue
        lines.extend([f"## {heading}", "", f"Content for {heading}.", ""])
    return "\n".join(lines).rstrip() + "\n"


def document_for(stage: str, **metadata_overrides: object) -> ArtifactDocument:
    return ArtifactDocument(
        metadata=metadata_for(stage, **metadata_overrides),
        body=body_for(stage),
    )


def manifest_binding_for(document: ArtifactDocument) -> dict[str, object]:
    spec = STAGE_ARTIFACT_SPECS[str(document.metadata["stage"])]
    fields = list(required_manifest_binding_fields(spec))
    if spec.stage == "S4" and document.revision is not None and document.revision > 1:
        fields.extend(("artifact_id", "problem_id"))
    return {key: document.metadata[key] for key in dict.fromkeys(fields)}


class MarkdownParsingTests(unittest.TestCase):
    def test_round_trip_and_named_sections_ignore_fenced_headings(self) -> None:
        document = document_for("S2")
        document = ArtifactDocument(
            metadata=document.metadata,
            body=document.body
            + "\n```markdown\n## Not A Real Section\n```\n",
        )

        serialized = serialize_markdown(document)
        parsed = parse_markdown(serialized)

        self.assertEqual(parsed.metadata, document.metadata)
        self.assertEqual(parsed.body, document.body)
        self.assertIn("Research Scope", parsed.sections())
        self.assertNotIn("Not A Real Section", parsed.sections())
        self.assertEqual(
            parsed.section("Evidence Candidates"),
            "Content for Evidence Candidates.",
        )

    def test_front_matter_must_be_a_unique_mapping(self) -> None:
        with self.assertRaisesRegex(ArtifactFormatError, "mapping"):
            parse_markdown("---\n- one\n---\nBody\n")
        with self.assertRaisesRegex(ArtifactFormatError, "duplicate key"):
            parse_markdown("---\nstage: S2\nstage: S3\n---\nBody\n")
        with self.assertRaisesRegex(ArtifactFormatError, "closing"):
            parse_markdown("---\nstage: S2\n")

    def test_duplicate_named_heading_is_ambiguous(self) -> None:
        with self.assertRaisesRegex(ArtifactFormatError, "duplicate"):
            extract_sections("## Same\nfirst\n## Same\nsecond\n")


class ArtifactValidationTests(unittest.TestCase):
    def test_registry_validates_every_stage_contract(self) -> None:
        for stage, spec in STAGE_ARTIFACT_SPECS.items():
            with self.subTest(stage=stage):
                document = document_for(stage)
                relative = expected_canonical_path(document)
                validated = validate_document(
                    document,
                    relative_path=relative,
                    expected_run_id="run-001",
                )
                self.assertEqual(validated.stage, stage)

    def test_common_and_stage_failures_are_reported_together(self) -> None:
        document = ArtifactDocument(
            metadata=metadata_for(
                "S2",
                schema_version=True,
                status="draft",
                created_by_session="pending",
            ),
            body=body_for("S2", omit="Coverage Gaps"),
        )

        with self.assertRaises(ArtifactValidationError) as captured:
            validate_document(document, relative_path="problems/not-research.md")

        message = str(captured.exception)
        self.assertIn("schema_version", message)
        self.assertIn("real Codex session", message)
        self.assertIn("status for S2", message)
        self.assertIn("Coverage Gaps", message)
        self.assertIn("under research/", message)

    def test_required_section_cannot_be_empty(self) -> None:
        body = body_for("S3").replace(
            "## Evidence Checks\n\nContent for Evidence Checks.",
            "## Evidence Checks\n",
        )
        with self.assertRaisesRegex(ArtifactValidationError, "Evidence Checks"):
            validate_document(
                ArtifactDocument(metadata=metadata_for("S3"), body=body),
                relative_path=(
                    "verification/audience-001/researcher-001/verifier-001.md"
                ),
            )

    def test_revision_requires_a_safe_supersedes_reference(self) -> None:
        with self.assertRaisesRegex(ArtifactValidationError, "requires supersedes"):
            validate_document(document_for("S8", supersedes=None))
        with self.assertRaisesRegex(ArtifactValidationError, "supersedes"):
            validate_document(document_for("S8", supersedes="../revision.md"))

    def test_stage_requires_provenance_and_exact_manifest_metadata(self) -> None:
        with self.assertRaisesRegex(ArtifactValidationError, "source_ref"):
            validate_document(document_for("S5", source_refs=[]))
        with self.assertRaisesRegex(ArtifactValidationError, "assigned task manifest"):
            validate_document(
                document_for("S5"),
                expected_metadata={"problem_ref": "problems/assigned.md"},
            )

    def test_machine_routing_fields_are_typed_and_consistent(self) -> None:
        with self.assertRaisesRegex(ArtifactValidationError, "boolean"):
            validate_document(document_for("S3", needs_second_verifier="yes"))
        with self.assertRaisesRegex(ArtifactValidationError, "non-empty"):
            validate_document(
                document_for(
                    "S3",
                    needs_second_verifier=True,
                    recheck_evidence_ids=[],
                )
            )
        with self.assertRaisesRegex(ArtifactValidationError, "T1 through T5"):
            validate_document(
                document_for(
                    "S5",
                    status="reject_candidate",
                    failed_thresholds=["T6"],
                )
            )
        with self.assertRaisesRegex(ArtifactValidationError, "competitor_research_gaps"):
            validate_document(
                document_for(
                    "S8",
                    needs_competitor_research=True,
                    competitor_research_gaps=[],
                )
            )


class PathAndReferenceTests(unittest.TestCase):
    def test_safe_relative_paths_reject_ambiguous_or_escaping_input(self) -> None:
        self.assertEqual(safe_relative_path("research/a.md").as_posix(), "research/a.md")
        for unsafe in (
            "",
            "/absolute.md",
            "../escape.md",
            "research/../escape.md",
            "./research.md",
            "research//a.md",
            "C:\\escape.md",
            "~/.secret",
        ):
            with self.subTest(path=unsafe), self.assertRaises(UnsafePathError):
                safe_relative_path(unsafe)

    def test_safe_join_rejects_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "target"
            target.mkdir()
            link = root / "linked"
            link.symlink_to(target, target_is_directory=True)
            with self.assertRaisesRegex(UnsafePathError, "symlink"):
                safe_join(root, "linked/file.md")

    def test_source_refs_must_exist_and_respect_task_allowlist(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "research" / "audience" / "researcher.md"
            source.parent.mkdir(parents=True)
            source.write_text("source", encoding="utf-8")

            refs = validate_source_refs(
                ["research/audience/researcher.md#evidence-001"],
                run_root=root,
                allowed_refs=["research/audience/researcher.md"],
            )
            self.assertEqual(
                refs,
                ("research/audience/researcher.md#evidence-001",),
            )
            with self.assertRaisesRegex(ArtifactValidationError, "allowlist"):
                validate_source_refs(
                    ["research/audience/researcher.md"],
                    run_root=root,
                    allowed_refs=[],
                )
            with self.assertRaises(FileNotFoundError):
                validate_source_refs(["research/missing.md"], run_root=root)


class ArtifactStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.run_root = Path(self.temporary.name) / "run-001"
        self.store = ArtifactStore(self.run_root, run_id="run-001")
        context = self.run_root / "inputs" / "context.json"
        context.parent.mkdir(parents=True)
        context.write_text("{}\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_staged(
        self,
        task_id: str,
        name: str,
        document: ArtifactDocument,
    ) -> Path:
        path = self.store.staged_path(task_id, name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(serialize_markdown(document), encoding="utf-8")
        return path

    def test_stamp_validate_promote_and_idempotent_retry(self) -> None:
        staged = self.write_staged(
            "task-s2",
            "result.md",
            document_for(
                "S2",
                created_by_session="pending",
                updated_by_session="pending",
            ),
        )
        stamped = self.store.stamp_session(staged, "session-real")
        self.assertEqual(stamped.metadata["created_by_session"], "session-real")

        result = self.store.promote(
            staged,
            "research/audience-001/researcher-001.md",
            expected_metadata=manifest_binding_for(stamped),
        )
        self.assertTrue(result.path.is_file())
        self.assertEqual(result.document.revision, 1)
        self.assertFalse(result.already_present)
        retry = self.store.promote(
            staged,
            "research/audience-001/researcher-001.md",
            expected_metadata=manifest_binding_for(stamped),
        )
        self.assertTrue(retry.already_present)

        changed = ArtifactDocument(
            metadata=stamped.metadata,
            body=stamped.body + "\nChanged.\n",
        )
        staged.write_text(serialize_markdown(changed), encoding="utf-8")
        with self.assertRaisesRegex(ArtifactConflictError, "different content"):
            self.store.promote(
                staged,
                "research/audience-001/researcher-001.md",
                expected_metadata=manifest_binding_for(stamped),
            )

    def test_publication_requires_a_complete_manifest_binding(self) -> None:
        document = document_for("S2")
        staged = self.write_staged("task-binding", "research.md", document)
        with self.assertRaisesRegex(
            ArtifactValidationError,
            "missing assigned task manifest fields",
        ):
            self.store.promote(
                staged,
                expected_canonical_path(document),
                expected_metadata={"stage": "S2"},
            )

    def test_batch_is_fully_validated_before_publication(self) -> None:
        first_document = document_for(
            "S2",
            audience_id="audience-batch",
            researcher_id="first",
        )
        first = self.write_staged("task-a", "first.md", first_document)
        invalid = ArtifactDocument(
            metadata=metadata_for(
                "S2",
                artifact_id="artifact-b",
                audience_id="audience-batch",
                researcher_id="second",
            ),
            body=body_for("S2", omit="Query Log"),
        )
        second = self.write_staged("task-b", "second.md", invalid)

        with self.assertRaises(ArtifactValidationError):
            self.store.promote_many(
                [
                    PromotionRequest(
                        first,
                        "research/audience-batch/first.md",
                        manifest_binding_for(first_document),
                    ),
                    PromotionRequest(
                        second,
                        "research/audience-batch/second.md",
                        manifest_binding_for(invalid),
                    ),
                ]
            )
        batch = self.run_root / "research" / "audience-batch"
        self.assertFalse((batch / "first.md").exists())
        self.assertFalse((batch / "second.md").exists())

    def test_fresh_same_directory_batch_is_published_as_one_directory(self) -> None:
        first_document = document_for(
            "S2",
            audience_id="audience-batch",
            researcher_id="first",
        )
        first = self.write_staged("task-a", "first.md", first_document)
        second_document = document_for(
            "S2",
            artifact_id="artifact-second",
            audience_id="audience-batch",
            researcher_id="second",
        )
        second = self.write_staged(
            "task-b",
            "second.md",
            second_document,
        )

        results = self.store.promote_many(
            [
                PromotionRequest(
                    first,
                    "research/audience-batch/first.md",
                    manifest_binding_for(first_document),
                ),
                PromotionRequest(
                    second,
                    "research/audience-batch/second.md",
                    manifest_binding_for(second_document),
                ),
            ]
        )

        self.assertEqual(len(results), 2)
        self.assertTrue(all(result.path.is_file() for result in results))
        self.assertEqual(
            list((self.run_root / "research").glob(".audience-batch.promotion-*")),
            [],
        )

    def test_living_document_replacement_snapshots_previous_revision(self) -> None:
        canonical = (
            "ideas/audience-001/writer-001/problem-001/"
            "generator-001/idea-001.md"
        )
        initial_document = document_for(
            "S6",
            artifact_id="idea-001",
            idea_id="idea-001",
            created_by_session="session-author",
            updated_by_session="session-author",
        )
        initial = self.write_staged("task-s6", "idea.md", initial_document)
        first = self.store.promote(
            initial,
            canonical,
            expected_metadata=manifest_binding_for(initial_document),
        )
        old_content = first.path.read_bytes()

        snapshot_ref = self.store.snapshot_relative_path(canonical, 1)
        revised_document = document_for(
            "S8",
            artifact_id="idea-001",
            idea_id="idea-001",
            created_by_session="session-author",
            updated_by_session="session-reviser",
            revision=2,
            supersedes=snapshot_ref,
        )
        revised = self.write_staged("task-s8", "idea.md", revised_document)
        result = self.store.replace_living_document(
            revised,
            canonical,
            expected_metadata=manifest_binding_for(revised_document),
        )

        self.assertEqual(result.document.stage, "S8")
        self.assertEqual(result.document.revision, 2)
        self.assertEqual(result.snapshot_path, (self.run_root / snapshot_ref).resolve())
        self.assertEqual((self.run_root / snapshot_ref).read_bytes(), old_content)
        self.assertEqual(
            self.store.validate_canonical(canonical).metadata["updated_by_session"],
            "session-reviser",
        )
        retry = self.store.replace_living_document(
            revised,
            canonical,
            expected_metadata=manifest_binding_for(revised_document),
        )
        self.assertTrue(retry.already_present)

        assert result.snapshot_path is not None
        result.snapshot_path.unlink()
        with self.assertRaisesRegex(ArtifactValidationError, "snapshot is missing"):
            self.store.validate_canonical(canonical)

    def test_living_document_must_advance_exactly_one_revision(self) -> None:
        canonical = (
            "ideas/audience-001/writer-001/problem-001/"
            "generator-001/idea-001.md"
        )
        initial_document = document_for(
            "S6",
            artifact_id="idea-001",
            idea_id="idea-001",
            created_by_session="session-author",
            updated_by_session="session-author",
        )
        initial = self.write_staged(
            "task-s6",
            "idea.md",
            initial_document,
        )
        self.store.promote(
            initial,
            canonical,
            expected_metadata=manifest_binding_for(initial_document),
        )
        invalid_document = document_for(
            "S8",
            artifact_id="idea-001",
            idea_id="idea-001",
            created_by_session="session-author",
            revision=3,
            supersedes=self.store.snapshot_relative_path(canonical, 2),
        )
        invalid = self.write_staged(
            "task-s8",
            "idea.md",
            invalid_document,
        )
        with self.assertRaisesRegex(ArtifactConflictError, "advance"):
            self.store.replace_living_document(
                invalid,
                canonical,
                expected_metadata=manifest_binding_for(invalid_document),
            )

    def test_living_document_cannot_change_stable_identity(self) -> None:
        canonical = (
            "ideas/audience-001/writer-001/problem-001/"
            "generator-001/idea-001.md"
        )
        initial_document = document_for(
            "S6",
            artifact_id="idea-artifact-001",
            created_by_session="session-author",
            updated_by_session="session-author",
        )
        initial = self.write_staged("task-s6", "idea.md", initial_document)
        self.store.promote(
            initial,
            canonical,
            expected_metadata=manifest_binding_for(initial_document),
        )

        revised_document = document_for(
            "S8",
            artifact_id="different-artifact",
            created_by_session="session-author",
            supersedes=self.store.snapshot_relative_path(canonical, 1),
        )
        revised = self.write_staged("task-s8", "idea.md", revised_document)
        with self.assertRaisesRegex(ArtifactConflictError, "artifact_id"):
            self.store.replace_living_document(
                revised,
                canonical,
                expected_metadata=manifest_binding_for(revised_document),
            )

    def test_non_initial_revision_cannot_be_published_without_parent(self) -> None:
        document = document_for("S8")
        staged = self.write_staged(
            "task-s8",
            "idea.md",
            document,
        )
        with self.assertRaisesRegex(ArtifactConflictError, "without an existing"):
            self.store.promote(
                staged,
                expected_canonical_path(document),
                expected_metadata=manifest_binding_for(document),
            )

    def test_immutable_artifact_cannot_use_living_replacement(self) -> None:
        canonical = "research/audience-001/researcher-001.md"
        document = document_for("S2")
        staged = self.write_staged("task-one", "research.md", document)
        self.store.promote(
            staged,
            canonical,
            expected_metadata=manifest_binding_for(document),
        )
        changed = ArtifactDocument(
            metadata=document_for("S2").metadata,
            body=body_for("S2") + "Changed.\n",
        )
        replacement = self.write_staged("task-two", "research.md", changed)
        with self.assertRaisesRegex(ArtifactConflictError, "immutable"):
            self.store.replace_living_document(
                replacement,
                canonical,
                expected_metadata=manifest_binding_for(changed),
            )

    def test_staged_symlink_is_rejected(self) -> None:
        real = self.write_staged("task-real", "real.md", document_for("S2"))
        task_dir = self.store.task_staging_dir("task-link")
        link = task_dir / "linked.md"
        link.symlink_to(real)
        with self.assertRaises(UnsafePathError):
            self.store.promote(
                link,
                "research/audience-001/researcher-001.md",
                expected_metadata=manifest_binding_for(document_for("S2")),
            )


if __name__ == "__main__":
    unittest.main()
