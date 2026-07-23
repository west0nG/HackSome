"""Internal C0-C5 Creative workflow.

The public CLI intentionally does not expose this route until C6/C7 exist.  The
controller nevertheless persists a complete, inspectable C0-C5 prefix so the
generation, Hook gate, optional Idea Memory branch, and novelty policy can be
tested independently.
"""

from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol, Sequence, cast

from hacksome.codex import CodexRunner
from hacksome.config import (
    CodexConfig,
    serialize_persisted_dataclass,
)
from hacksome.creative.contracts import (
    C0_CHALLENGE_PARSE,
    C1_BRIEF_NORMALIZE,
    C2_TERRITORY_EXPLORE,
    C3_CONCEPT_SYNTHESIZE,
    C4_CHEAP_HOOK_REPAIR,
    C4_CHEAP_HOOK_REVIEW,
    C5M_MEMORY_RECALL,
    C5M_MEMORY_REMIX,
    C5W_NOVELTY_SCAN,
    CreativeWorkflowSettings,
    DEFAULT_CREATIVE_BRIEF,
    DEFAULT_TERRITORY_LENSES,
    atom_id,
    base_concept_id,
    concept_revision_ref,
    memory_concept_id,
    territory_id,
)
from hacksome.creative.artifacts import CreativeValidationContext
from hacksome.creative.memory import (
    IdeaMemorySnapshot,
    MemoryCapsuleRef,
    MemoryCue,
    load_memory_snapshot,
    validate_memory_inspiration_packet,
)
from hacksome.creative.prompting import (
    creative_prompt_catalog,
    validate_creative_output,
)
from hacksome.hub import RunHub
from hacksome.models import CodexTask
from hacksome.prompting import PromptCatalog
from hacksome.state import (
    atomic_write_text,
    sha256_text,
)
from hacksome.task_executor import (
    OPTIONAL_BRANCH_FAILURE_POLICY,
    AgentTaskExecutionError,
    AgentTaskExecutor,
    FailurePolicy,
)


INTERNAL_C5_COMPLETE_STAGE = "creative-c5-complete-internal"
DEFAULT_RUN_TIMEOUT_SECONDS = 6 * 60 * 60

SYNTHESIS_LENSES = (
    "Combine atoms through a legible interaction loop",
    "Combine atoms around a sharp reversal and reveal",
    "Combine atoms around a social retelling or shared performance",
    "Combine atoms through a strange but coherent wildcard structure",
)

class CreativeWorkflowError(RuntimeError):
    """The Creative C0-C5 prefix cannot safely continue."""


class Runner(Protocol):
    async def run(self, task: CodexTask) -> Any: ...


class SnapshotBuilder(Protocol):
    def __call__(
        self,
        runs_dir: str | Path,
        settings: CreativeWorkflowSettings,
    ) -> IdeaMemorySnapshot: ...


class SnapshotPersister(Protocol):
    def __call__(
        self,
        snapshot: IdeaMemorySnapshot,
        run_dir: str | Path,
    ) -> dict[str, Any]: ...


SemanticValidator = Callable[[str, dict[str, Any]], None]


@dataclass(frozen=True, slots=True)
class CreativeConcept:
    concept_id: str
    revision: int
    artifact_ref: str
    primary_territory_ref: str
    parent_atom_refs: tuple[str, ...]
    origin: str
    task_id: str
    memory_cue_refs: tuple[str, ...] = ()
    memory_source_refs: tuple[MemoryCapsuleRef, ...] = ()


@dataclass(frozen=True, slots=True)
class HookGateOutcome:
    passed: tuple[CreativeConcept, ...]
    disposition_refs: tuple[str, ...]
    reviewed_revisions: tuple[CreativeConcept, ...]


@dataclass(frozen=True, slots=True)
class MemoryBranchOutcome:
    challengers: tuple[CreativeConcept, ...]
    summary_ref: str
    selected_cue_ids: tuple[str, ...]
    optional_failure_task_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CreativeC0C5Outcome:
    """Validated internal hand-off to the future C6 implementation."""

    run_dir: Path
    challenge_brief_ref: str
    constraint_view_ref: str
    creative_brief_ref: str
    territory_refs: tuple[str, ...]
    atom_refs: tuple[str, ...]
    base_concept_refs: tuple[str, ...]
    memory_challenger_refs: tuple[str, ...]
    hook_passed_refs: tuple[str, ...]
    novelty_scan_refs: tuple[str, ...]
    memory_summary_ref: str


class CreativeIdeaWorkflow:
    """Persist and execute the internal Creative route through C5."""

    def __init__(
        self,
        hub: RunHub,
        runner: Runner,
        *,
        settings: CreativeWorkflowSettings,
        prompt_catalog: PromptCatalog,
        memory_snapshot: IdeaMemorySnapshot,
        semantic_validator: SemanticValidator,
        task_timeout_seconds: float,
        run_timeout_seconds: float,
    ) -> None:
        self.hub = hub
        self.runner = runner
        self.settings = settings
        self.prompt_catalog = prompt_catalog
        self.memory_snapshot = memory_snapshot
        self.task_timeout_seconds = _positive_timeout(
            task_timeout_seconds, "task_timeout_seconds"
        )
        self.run_timeout_seconds = _positive_timeout(
            run_timeout_seconds, "run_timeout_seconds"
        )
        self.task_executor = AgentTaskExecutor(
            hub,
            runner,
            prompt_catalog,
            task_timeout_seconds=self.task_timeout_seconds,
            semantic_validator=semantic_validator,
            optional_branch_stages=(C5M_MEMORY_RECALL, C5M_MEMORY_REMIX),
        )

    @property
    def run_dir(self) -> Path:
        return self.hub.run_dir

    @classmethod
    def create(
        cls,
        challenge: str,
        runs_dir: str | Path,
        *,
        settings: CreativeWorkflowSettings | None = None,
        codex_config: CodexConfig | None = None,
        run_id: str | None = None,
        runner: Runner | None = None,
        creative_brief: str | None = None,
        creative_brief_file: str | Path | None = None,
        memory_snapshot: IdeaMemorySnapshot | None = None,
        snapshot_builder: SnapshotBuilder | None = None,
        snapshot_persister: SnapshotPersister | None = None,
        prompt_catalog: PromptCatalog | None = None,
        semantic_validator: SemanticValidator | None = None,
        run_timeout_seconds: float = DEFAULT_RUN_TIMEOUT_SECONDS,
    ) -> CreativeIdeaWorkflow:
        # Imports are intentionally lazy: memory discovery imports the route
        # validator, while the route validator imports this package's contracts.
        from hacksome.creative.memory import (
            build_memory_snapshot,
            persist_memory_snapshot,
        )
        selected_settings = settings or CreativeWorkflowSettings()
        selected_config = codex_config or CodexConfig()
        selected_builder = snapshot_builder or cast(
            SnapshotBuilder, build_memory_snapshot
        )
        selected_persister = snapshot_persister or cast(
            SnapshotPersister, persist_memory_snapshot
        )
        selected_catalog = prompt_catalog or creative_prompt_catalog
        if semantic_validator is None:
            def default_validator(stage: str, output: dict[str, Any]) -> None:
                validate_creative_output(
                    stage,
                    output,
                    settings=selected_settings,
                )

            selected_validator: SemanticValidator = default_validator
        else:
            selected_validator = semantic_validator

        if creative_brief is not None and creative_brief_file is not None:
            raise ValueError("creative_brief and creative_brief_file are mutually exclusive")
        if creative_brief_file is not None:
            brief_text = Path(creative_brief_file).read_text(encoding="utf-8")
            brief_source = "file"
        elif creative_brief is not None:
            brief_text = creative_brief
            brief_source = "literal"
        else:
            brief_text = DEFAULT_CREATIVE_BRIEF
            brief_source = "default"
        if not brief_text.strip():
            raise ValueError("Creative Brief input must not be empty")

        # This call must precede RunHub.create: the newly allocated run must
        # never discover itself or observe a later source mutation.
        selected_snapshot = (
            memory_snapshot
            if memory_snapshot is not None
            else selected_builder(runs_dir, selected_settings)
        )
        settings_payload = serialize_persisted_dataclass(selected_settings)
        hub = RunHub.create(
            challenge,
            runs_dir,
            settings=settings_payload,
            codex_config=selected_config,
            run_id=run_id,
            route="creative",
        )
        brief_path = hub.run_dir / "input" / "creative-brief-input.md"
        atomic_write_text(brief_path, brief_text)
        hub.register_input(
            "creative_brief",
            {
                "path": "input/creative-brief-input.md",
                "sha256": sha256_text(brief_text),
                "source": brief_source,
            },
        )
        snapshot_record = selected_persister(selected_snapshot, hub.run_dir)
        hub.register_input("idea_memory", snapshot_record)

        route = hub.load_state()["route"]
        frozen = selected_catalog.freeze(
            hub.run_dir,
            route_id="creative",
            contract_version=route["contract_version"],
            prompt_policy_version=route["prompt_policy_version"],
            stage_policy_version=route["stage_policy_version"],
        )
        hub.set_resource_manifest(frozen.manifest_reference())
        return cls(
            hub,
            runner or CodexRunner(selected_config),
            settings=selected_settings,
            prompt_catalog=frozen.catalog,
            memory_snapshot=selected_snapshot,
            semantic_validator=selected_validator,
            task_timeout_seconds=selected_config.default_timeout_seconds,
            run_timeout_seconds=run_timeout_seconds,
        )

    async def execute_c0_c5(self) -> CreativeC0C5Outcome:
        """Run through novelty evidence and stop at the internal C6 boundary."""

        stage = C0_CHALLENGE_PARSE
        self.hub.set_run_status("running", stage=stage)
        try:
            self._verify_execution_inputs()
            async with asyncio.timeout(self.run_timeout_seconds):
                challenge_ref, constraint_ref = await self._run_c0()
                stage = C1_BRIEF_NORMALIZE
                self.hub.set_run_status("running", stage=stage)
                brief_ref = await self._run_c1(challenge_ref, constraint_ref)

                stage = C2_TERRITORY_EXPLORE
                self.hub.set_run_status("running", stage=stage)
                territory_refs, atom_refs = await self._run_c2(
                    challenge_ref, constraint_ref, brief_ref
                )

                stage = C3_CONCEPT_SYNTHESIZE
                self.hub.set_run_status("running", stage=stage)
                base_concepts = await self._run_c3(
                    challenge_ref,
                    constraint_ref,
                    brief_ref,
                    atom_refs,
                )

                stage = C4_CHEAP_HOOK_REVIEW
                self.hub.set_run_status("running", stage=stage)
                base_gate = await self._run_c4(
                    base_concepts,
                    constraint_ref=constraint_ref,
                    brief_ref=brief_ref,
                )

                stage = C5M_MEMORY_RECALL
                self.hub.set_run_status("running", stage=stage)
                memory = await self._run_c5m(
                    challenge_ref=challenge_ref,
                    constraint_ref=constraint_ref,
                    brief_ref=brief_ref,
                    atom_refs=atom_refs,
                    base_concepts=base_gate.reviewed_revisions,
                    base_gate=base_gate,
                )
                stage = C4_CHEAP_HOOK_REVIEW
                self.hub.set_run_status("running", stage=stage)
                challenger_gate = await self._run_c4(
                    memory.challengers,
                    constraint_ref=constraint_ref,
                    brief_ref=brief_ref,
                )

                stage = C5W_NOVELTY_SCAN
                self.hub.set_run_status("running", stage=stage)
                hook_passed = tuple(
                    sorted(
                        (*base_gate.passed, *challenger_gate.passed),
                        key=lambda concept: concept.artifact_ref,
                    )
                )
                novelty_refs = await self._run_c5w(
                    hook_passed,
                    challenge_ref=challenge_ref,
                    brief_ref=brief_ref,
                )
        except TimeoutError as exc:
            self.hub.set_run_status("failed", stage=stage, error=exc)
            raise CreativeWorkflowError("Creative workflow exceeded run timeout") from exc
        except Exception as exc:
            task_id = exc.task_id if isinstance(exc, AgentTaskExecutionError) else None
            self.hub.set_run_status(
                "failed",
                stage=stage,
                error=exc,
                task_id=task_id,
            )
            if isinstance(exc, CreativeWorkflowError):
                raise
            raise CreativeWorkflowError(str(exc)) from exc

        self.hub.set_run_status(
            "running",
            stage=INTERNAL_C5_COMPLETE_STAGE,
            reason="validated internal C0-C5 hand-off; C6 is not public yet",
        )
        return CreativeC0C5Outcome(
            run_dir=self.run_dir,
            challenge_brief_ref=challenge_ref,
            constraint_view_ref=constraint_ref,
            creative_brief_ref=brief_ref,
            territory_refs=territory_refs,
            atom_refs=atom_refs,
            base_concept_refs=tuple(
                concept.artifact_ref for concept in base_concepts
            ),
            memory_challenger_refs=tuple(
                concept.artifact_ref for concept in memory.challengers
            ),
            hook_passed_refs=tuple(
                concept.artifact_ref for concept in hook_passed
            ),
            novelty_scan_refs=novelty_refs,
            memory_summary_ref=memory.summary_ref,
        )

    def _verify_execution_inputs(self) -> None:
        """Fail closed if run-local resources changed after run creation."""

        errors = self.hub.core_validate()
        if errors:
            raise CreativeWorkflowError(
                "Creative execution preflight failed: " + "; ".join(errors)
            )

        state = self.hub.load_state()
        route = state.get("route")
        manifest = state.get("resource_manifest")
        if not isinstance(route, dict) or not isinstance(manifest, dict):
            raise CreativeWorkflowError(
                "Creative execution preflight requires route resources"
            )
        try:
            verified_catalog = creative_prompt_catalog.load_frozen(
                self.run_dir,
                route_id="creative",
                contract_version=str(route.get("contract_version", "")),
                prompt_policy_version=str(
                    route.get("prompt_policy_version", "")
                ),
                stage_policy_version=str(
                    route.get("stage_policy_version", "")
                ),
                manifest_sha256=str(manifest.get("sha256", "")),
            )
        except Exception as exc:
            raise CreativeWorkflowError(
                f"Creative frozen resources failed verification: {exc}"
            ) from exc

        inputs = state.get("inputs")
        memory_record = (
            inputs.get("idea_memory") if isinstance(inputs, dict) else None
        )
        if not isinstance(memory_record, dict):
            raise CreativeWorkflowError(
                "Creative execution preflight requires Idea Memory input"
            )
        relative_path = memory_record.get("path")
        expected_sha256 = memory_record.get("sha256")
        if not isinstance(relative_path, str) or not isinstance(
            expected_sha256, str
        ):
            raise CreativeWorkflowError(
                "Creative Idea Memory input has no path/hash"
            )
        try:
            verified_snapshot = load_memory_snapshot(
                self.run_dir.joinpath(*Path(relative_path).parts),
                expected_sha256=expected_sha256,
            )
        except Exception as exc:
            raise CreativeWorkflowError(
                f"Creative Idea Memory Snapshot failed verification: {exc}"
            ) from exc
        if verified_snapshot.to_dict() != self.memory_snapshot.to_dict():
            raise CreativeWorkflowError(
                "Creative Idea Memory Snapshot differs from the frozen run input"
            )

        self.prompt_catalog = verified_catalog
        self.task_executor.catalog = verified_catalog
        self.memory_snapshot = verified_snapshot

    async def _run_c0(self) -> tuple[str, str]:
        task_id = "creative-c0-challenge-parse"
        output = await self._execute(
            stage=C0_CHALLENGE_PARSE,
            task_id=task_id,
            blocks=(("ORIGINAL_CHALLENGE", self.hub.challenge()),),
            parent_refs=(),
        )
        challenge_markdown = _required_text(output, "challenge_brief_markdown")
        constraint_markdown = _required_text(output, "constraint_view_markdown")
        challenge_ref = self.hub.publish_artifact(
            artifact_id="creative-challenge-brief-r001",
            artifact_type="creative_challenge_brief",
            relative_path=(
                "artifacts/creative/challenge/"
                "creative-challenge-brief-r001.md"
            ),
            content=challenge_markdown,
            task_id=task_id,
        )
        constraint_ref = self.hub.publish_artifact(
            artifact_id="creative-constraint-view-r001",
            artifact_type="creative_constraint_view",
            relative_path=(
                "artifacts/creative/challenge/"
                "creative-constraint-view-r001.md"
            ),
            content=constraint_markdown,
            task_id=task_id,
            source_refs=(challenge_ref,),
        )
        return challenge_ref, constraint_ref

    async def _run_c1(self, challenge_ref: str, constraint_ref: str) -> str:
        task_id = "creative-c1-brief-normalize"
        brief_input = _input_text(self.hub, "creative_brief")
        output = await self._execute(
            stage=C1_BRIEF_NORMALIZE,
            task_id=task_id,
            blocks=(
                ("ORIGINAL_CHALLENGE", self.hub.challenge()),
                ("CHALLENGE_BRIEF", self.hub.read_artifact(challenge_ref)),
                ("CONSTRAINT_VIEW", self.hub.read_artifact(constraint_ref)),
                ("CREATIVE_BRIEF_INPUT", brief_input),
            ),
            parent_refs=(challenge_ref, constraint_ref, "input:creative_brief"),
        )
        markdown = _required_text(output, "markdown")
        return self.hub.publish_artifact(
            artifact_id="creative-brief-r001",
            artifact_type="creative_brief",
            relative_path="artifacts/creative/brief/creative-brief-r001.md",
            content=markdown,
            task_id=task_id,
            source_refs=(challenge_ref, constraint_ref),
        )

    async def _run_c2(
        self,
        challenge_ref: str,
        constraint_ref: str,
        brief_ref: str,
    ) -> tuple[tuple[str, ...], tuple[str, ...]]:
        async def explore(slot: int, lens: str) -> tuple[int, dict[str, Any], str]:
            task_id = f"creative-c2-territory-{slot:02d}"
            output = await self._execute(
                stage=C2_TERRITORY_EXPLORE,
                task_id=task_id,
                blocks=(
                    ("CHALLENGE_BRIEF", self.hub.read_artifact(challenge_ref)),
                    ("CONSTRAINT_VIEW", self.hub.read_artifact(constraint_ref)),
                    ("CREATIVE_BRIEF", self.hub.read_artifact(brief_ref)),
                    ("TERRITORY_LENS", lens),
                    (
                        "LIMITS",
                        "At most "
                        f"{int(self.settings.max_atoms_per_territory)} atoms.",
                    ),
                ),
                parent_refs=(challenge_ref, constraint_ref, brief_ref),
            )
            return slot, output, task_id

        completed = await asyncio.gather(
            *(
                explore(slot, lens)
                for slot, lens in enumerate(
                    DEFAULT_TERRITORY_LENSES[
                        : int(self.settings.territory_explorers)
                    ],
                    start=1,
                )
            )
        )
        territory_refs: list[str] = []
        atom_refs: list[str] = []
        for slot, output, task_id in sorted(completed):
            territory_ref_id = territory_id(slot)
            output = self._validate_completed_output(
                task_id=task_id,
                stage=C2_TERRITORY_EXPLORE,
                output=output,
                context={"expected_territory_ref": territory_ref_id},
            )
            territory_markdown = _required_text(output, "territory_markdown")
            territory_ref = self.hub.publish_artifact(
                artifact_id=territory_ref_id,
                artifact_type="creative_territory",
                relative_path=(
                    f"artifacts/creative/territories/{territory_ref_id}.md"
                ),
                content=territory_markdown,
                task_id=task_id,
                source_refs=(challenge_ref, constraint_ref, brief_ref),
                metadata={
                    "lens": DEFAULT_TERRITORY_LENSES[slot - 1],
                    "slot": slot,
                },
            )
            territory_refs.append(territory_ref)
            atoms = _object_list(output, "atoms")
            if len(atoms) > int(self.settings.max_atoms_per_territory):
                raise CreativeWorkflowError(
                    f"{task_id} exceeded max_atoms_per_territory"
                )
            for atom_slot, raw in enumerate(atoms, start=1):
                atom_ref_id = atom_id(slot, atom_slot)
                atom_refs.append(
                    self.hub.publish_artifact(
                        artifact_id=atom_ref_id,
                        artifact_type="creative_atom",
                        relative_path=(
                            f"artifacts/creative/atoms/{atom_ref_id}.md"
                        ),
                        content=_required_text(raw, "markdown"),
                        task_id=task_id,
                        source_refs=(territory_ref,),
                        metadata={
                            "territory_ref": territory_ref,
                            "territory_slot": slot,
                            "atom_slot": atom_slot,
                        },
                    )
                )
        return tuple(territory_refs), tuple(atom_refs)

    async def _run_c3(
        self,
        challenge_ref: str,
        constraint_ref: str,
        brief_ref: str,
        atom_refs: Sequence[str],
    ) -> tuple[CreativeConcept, ...]:
        if not atom_refs:
            return ()
        atom_index = _artifact_index(self.hub, atom_refs)

        async def synthesize(slot: int, lens: str) -> tuple[int, dict[str, Any], str]:
            task_id = f"creative-c3-synthesis-{slot:02d}"
            output = await self._execute(
                stage=C3_CONCEPT_SYNTHESIZE,
                task_id=task_id,
                blocks=(
                    ("CHALLENGE_BRIEF", self.hub.read_artifact(challenge_ref)),
                    ("CONSTRAINT_VIEW", self.hub.read_artifact(constraint_ref)),
                    ("CREATIVE_BRIEF", self.hub.read_artifact(brief_ref)),
                    ("CURRENT_ATOM_INDEX", atom_index),
                    ("SYNTHESIS_LENS", lens),
                    (
                        "LIMITS",
                        "At most "
                        f"{int(self.settings.max_concepts_per_synthesizer)} concepts.",
                    ),
                ),
                parent_refs=(
                    challenge_ref,
                    constraint_ref,
                    brief_ref,
                    *atom_refs,
                ),
            )
            return slot, output, task_id

        completed = await asyncio.gather(
            *(
                synthesize(slot, lens)
                for slot, lens in enumerate(
                    SYNTHESIS_LENSES[
                        : int(self.settings.concept_synthesizers)
                    ],
                    start=1,
                )
            )
        )
        concepts: list[CreativeConcept] = []
        seen_markdown: set[str] = set()
        seen_hooks: set[str] = set()
        atom_set = set(atom_refs)
        for synth_slot, output, task_id in sorted(completed):
            output = self._validate_completed_output(
                task_id=task_id,
                stage=C3_CONCEPT_SYNTHESIZE,
                output=output,
                context={"allowed_atom_refs": atom_set},
            )
            candidates = _object_list(output, "concepts")
            if len(candidates) > int(self.settings.max_concepts_per_synthesizer):
                raise CreativeWorkflowError(
                    f"{task_id} exceeded max_concepts_per_synthesizer"
                )
            for candidate_slot, raw in enumerate(candidates, start=1):
                markdown = _required_text(raw, "markdown")
                normalized_markdown = _normalized_text(markdown)
                normalized_hook = _normalized_section(markdown, "One-sentence Hook")
                if normalized_markdown in seen_markdown or (
                    normalized_hook and normalized_hook in seen_hooks
                ):
                    continue
                seen_markdown.add(normalized_markdown)
                if normalized_hook:
                    seen_hooks.add(normalized_hook)
                primary = _required_text(raw, "primary_territory_ref")
                parent_atoms = tuple(_string_list(raw, "parent_atom_refs"))
                if not parent_atoms or any(ref not in atom_set for ref in parent_atoms):
                    raise CreativeWorkflowError(
                        f"{task_id} concept has invalid parent_atom_refs"
                    )
                parent_territories = {
                    _artifact_metadata(self.hub, ref).get("territory_ref")
                    for ref in parent_atoms
                }
                if primary not in parent_territories:
                    raise CreativeWorkflowError(
                        f"{task_id} primary territory is not from a Parent Atom"
                    )
                concept_id = base_concept_id(synth_slot, candidate_slot)
                artifact_ref = concept_revision_ref(concept_id, 1)
                self.hub.publish_artifact(
                    artifact_id=artifact_ref,
                    artifact_type="creative_concept",
                    relative_path=(
                        f"artifacts/creative/concepts/{artifact_ref}.md"
                    ),
                    content=markdown,
                    task_id=task_id,
                    source_refs=parent_atoms,
                    metadata={
                        "concept_id": concept_id,
                        "origin": "base",
                        "revision": 1,
                        "revision_reason": "initial_synthesis",
                        "primary_territory_ref": primary,
                        "parent_atom_refs": list(parent_atoms),
                        "synthesis_slot": synth_slot,
                        "candidate_slot": candidate_slot,
                    },
                )
                concepts.append(
                    CreativeConcept(
                        concept_id=concept_id,
                        revision=1,
                        artifact_ref=artifact_ref,
                        primary_territory_ref=primary,
                        parent_atom_refs=parent_atoms,
                        origin="base",
                        task_id=task_id,
                    )
                )
        return tuple(sorted(concepts, key=lambda item: item.artifact_ref))

    async def _run_c4(
        self,
        concepts: Sequence[CreativeConcept],
        *,
        constraint_ref: str,
        brief_ref: str,
    ) -> HookGateOutcome:
        async def gate(concept: CreativeConcept) -> HookGateOutcome:
            return await self._gate_one_concept(
                concept,
                constraint_ref=constraint_ref,
                brief_ref=brief_ref,
            )

        outcomes = await asyncio.gather(*(gate(concept) for concept in concepts))
        passed = tuple(
            sorted(
                (
                    concept
                    for outcome in outcomes
                    for concept in outcome.passed
                ),
                key=lambda concept: concept.artifact_ref,
            )
        )
        disposition_refs = tuple(
            ref for outcome in outcomes for ref in outcome.disposition_refs
        )
        reviewed_revisions = tuple(
            sorted(
                (
                    concept
                    for outcome in outcomes
                    for concept in outcome.reviewed_revisions
                ),
                key=lambda concept: concept.artifact_ref,
            )
        )
        return HookGateOutcome(
            passed=passed,
            disposition_refs=disposition_refs,
            reviewed_revisions=reviewed_revisions,
        )

    async def _gate_one_concept(
        self,
        concept: CreativeConcept,
        *,
        constraint_ref: str,
        brief_ref: str,
    ) -> HookGateOutcome:
        first_reviews = await self._review_concept(
            concept,
            constraint_ref=constraint_ref,
            brief_ref=brief_ref,
            cycle=1,
        )
        decisions = tuple(_review_decision(output) for _, output, _ in first_reviews)
        reason_codes = _review_reason_codes(output for _, output, _ in first_reviews)
        evidence_refs = tuple(ref for ref, _, _ in first_reviews)
        task_ids = tuple(task_id for _, _, task_id in first_reviews)

        if decisions == ("pass", "pass"):
            decision_ref = self._record_hook_decision(
                concept,
                outcome="pass",
                reason_codes=reason_codes,
                evidence_refs=evidence_refs,
                task_ids=task_ids,
                cycle=1,
            )
            disposition_ref = self._publish_disposition(
                concept,
                outcome="pass",
                terminal=False,
                reason_codes=reason_codes,
                decision_ref=decision_ref,
                evidence_refs=evidence_refs,
                task_ids=task_ids,
                suffix="pass",
            )
            return HookGateOutcome((concept,), (disposition_ref,), (concept,))

        if decisions == ("invalid", "invalid"):
            codes = ("c4_double_invalid", *reason_codes)
            decision_ref = self._record_hook_decision(
                concept,
                outcome="eliminated",
                reason_codes=codes,
                evidence_refs=evidence_refs,
                task_ids=task_ids,
                cycle=1,
            )
            disposition_ref = self._publish_disposition(
                concept,
                outcome="eliminated",
                terminal=True,
                reason_codes=codes,
                decision_ref=decision_ref,
                evidence_refs=evidence_refs,
                task_ids=task_ids,
                suffix="eliminated",
            )
            return HookGateOutcome((), (disposition_ref,), (concept,))

        repair_decision = self._record_hook_decision(
            concept,
            outcome="repair",
            reason_codes=reason_codes,
            evidence_refs=evidence_refs,
            task_ids=task_ids,
            cycle=1,
        )
        repair_disposition = self._publish_disposition(
            concept,
            outcome="repair",
            terminal=False,
            reason_codes=reason_codes,
            decision_ref=repair_decision,
            evidence_refs=evidence_refs,
            task_ids=task_ids,
            suffix="repair",
        )
        repaired = await self._repair_concept(
            concept,
            constraint_ref=constraint_ref,
            brief_ref=brief_ref,
            reviews=first_reviews,
        )
        superseded = self._publish_disposition(
            concept,
            outcome="superseded_by_hook_repair",
            terminal=True,
            target_ref=repaired.artifact_ref,
            reason_codes=("c4_hook_repair_published",),
            decision_ref=repair_decision,
            evidence_refs=evidence_refs,
            task_ids=task_ids,
            suffix="superseded",
        )
        second_reviews = await self._review_concept(
            repaired,
            constraint_ref=constraint_ref,
            brief_ref=brief_ref,
            cycle=2,
        )
        second_decisions = tuple(
            _review_decision(output) for _, output, _ in second_reviews
        )
        second_reasons = _review_reason_codes(
            output for _, output, _ in second_reviews
        )
        second_evidence = tuple(ref for ref, _, _ in second_reviews)
        second_tasks = tuple(task_id for _, _, task_id in second_reviews)
        if second_decisions == ("pass", "pass"):
            outcome = "pass"
            terminal = False
            codes = second_reasons
        else:
            outcome = "eliminated"
            terminal = True
            codes = ("c4_unresolved_after_repair", *second_reasons)
        second_decision = self._record_hook_decision(
            repaired,
            outcome=outcome,
            reason_codes=codes,
            evidence_refs=second_evidence,
            task_ids=second_tasks,
            cycle=2,
        )
        second_disposition = self._publish_disposition(
            repaired,
            outcome=outcome,
            terminal=terminal,
            reason_codes=codes,
            decision_ref=second_decision,
            evidence_refs=second_evidence,
            task_ids=second_tasks,
            suffix=outcome,
        )
        passed = (repaired,) if outcome == "pass" else ()
        return HookGateOutcome(
            passed,
            (repair_disposition, superseded, second_disposition),
            (concept, repaired),
        )

    async def _review_concept(
        self,
        concept: CreativeConcept,
        *,
        constraint_ref: str,
        brief_ref: str,
        cycle: int,
    ) -> tuple[tuple[str, dict[str, Any], str], ...]:
        async def review(reviewer: int) -> tuple[str, dict[str, Any], str]:
            task_id = (
                f"creative-c4-review-{concept.concept_id}-"
                f"r{concept.revision:03d}-c{cycle}-v{reviewer}"
            )
            output = await self._execute(
                stage=C4_CHEAP_HOOK_REVIEW,
                task_id=task_id,
                blocks=(
                    ("CONSTRAINT_VIEW", self.hub.read_artifact(constraint_ref)),
                    ("CREATIVE_BRIEF", self.hub.read_artifact(brief_ref)),
                    ("CONCEPT_REVISION", self.hub.read_artifact(concept.artifact_ref)),
                ),
                parent_refs=(constraint_ref, brief_ref, concept.artifact_ref),
            )
            artifact_ref = (
                f"creative-hook-review-{concept.concept_id}-"
                f"r{concept.revision:03d}-c{cycle}-v{reviewer}"
            )
            self.hub.publish_artifact(
                artifact_id=artifact_ref,
                artifact_type="creative_cheap_hook_review",
                relative_path=(
                    "artifacts/creative/cheap-hook-reviews/"
                    f"{artifact_ref}.json"
                ),
                content=_json_text(output),
                task_id=task_id,
                source_refs=(concept.artifact_ref,),
                metadata={
                    "concept_revision_ref": concept.artifact_ref,
                    "cycle": cycle,
                    "reviewer_slot": reviewer,
                },
            )
            return artifact_ref, output, task_id

        return tuple(await asyncio.gather(review(1), review(2)))

    async def _repair_concept(
        self,
        concept: CreativeConcept,
        *,
        constraint_ref: str,
        brief_ref: str,
        reviews: Sequence[tuple[str, Mapping[str, Any], str]],
    ) -> CreativeConcept:
        if concept.revision != 1:
            raise CreativeWorkflowError("C4 repair budget is already consumed")
        task_id = f"creative-c4-repair-{concept.concept_id}-r001"
        output = await self._execute(
            stage=C4_CHEAP_HOOK_REPAIR,
            task_id=task_id,
            blocks=(
                ("CONSTRAINT_VIEW", self.hub.read_artifact(constraint_ref)),
                ("CREATIVE_BRIEF", self.hub.read_artifact(brief_ref)),
                ("CONCEPT_REVISION", self.hub.read_artifact(concept.artifact_ref)),
                ("HOOK_REVIEW_A", _json_text(reviews[0][1])),
                ("HOOK_REVIEW_B", _json_text(reviews[1][1])),
            ),
            parent_refs=(
                constraint_ref,
                brief_ref,
                concept.artifact_ref,
                reviews[0][0],
                reviews[1][0],
            ),
        )
        output = self._validate_completed_output(
            task_id=task_id,
            stage=C4_CHEAP_HOOK_REPAIR,
            output=output,
            context={
                "source_markdown": self.hub.read_artifact(concept.artifact_ref),
            },
        )
        markdown = _required_text(output, "markdown")
        returned_primary = output.get(
            "primary_territory_ref", concept.primary_territory_ref
        )
        if returned_primary != concept.primary_territory_ref:
            raise CreativeWorkflowError("C4 repair changed primary_territory_ref")
        artifact_ref = concept_revision_ref(concept.concept_id, 2)
        self.hub.publish_artifact(
            artifact_id=artifact_ref,
            artifact_type="creative_concept",
            relative_path=f"artifacts/creative/concepts/{artifact_ref}.md",
            content=markdown,
            task_id=task_id,
            source_refs=(concept.artifact_ref, reviews[0][0], reviews[1][0]),
            metadata={
                "concept_id": concept.concept_id,
                "origin": concept.origin,
                "revision": 2,
                "revision_reason": "cheap_hook_repair",
                "supersedes_ref": concept.artifact_ref,
                "primary_territory_ref": concept.primary_territory_ref,
                "parent_atom_refs": list(concept.parent_atom_refs),
                "memory_cue_refs": list(concept.memory_cue_refs),
                "memory_source_refs": [
                    reference.to_dict()
                    for reference in concept.memory_source_refs
                ],
            },
        )
        return CreativeConcept(
            concept_id=concept.concept_id,
            revision=2,
            artifact_ref=artifact_ref,
            primary_territory_ref=concept.primary_territory_ref,
            parent_atom_refs=concept.parent_atom_refs,
            origin=concept.origin,
            task_id=task_id,
            memory_cue_refs=concept.memory_cue_refs,
            memory_source_refs=concept.memory_source_refs,
        )

    def _record_hook_decision(
        self,
        concept: CreativeConcept,
        *,
        outcome: str,
        reason_codes: Sequence[str],
        evidence_refs: Sequence[str],
        task_ids: Sequence[str],
        cycle: int,
    ) -> str:
        decision_id = (
            f"creative-decision-c4-{concept.concept_id}-"
            f"r{concept.revision:03d}-c{cycle}"
        )
        self.hub.append_decision(
            {
                "decision_id": decision_id,
                "route_id": "creative",
                "stage": "creative-cheap-hook",
                "decision_type": "candidate_gate",
                "outcome": outcome,
                "reason_codes": list(dict.fromkeys(reason_codes)),
                "subject_refs": [concept.artifact_ref],
                "evidence_refs": list(evidence_refs),
                "task_ids": list(task_ids),
            }
        )
        return decision_id

    def _publish_disposition(
        self,
        concept: CreativeConcept,
        *,
        outcome: str,
        terminal: bool,
        reason_codes: Sequence[str],
        decision_ref: str,
        evidence_refs: Sequence[str],
        task_ids: Sequence[str],
        suffix: str,
        target_ref: str | None = None,
    ) -> str:
        artifact_record = _artifact_record(self.hub, concept.artifact_ref)
        disposition_id = (
            f"creative-disposition-{concept.concept_id}-"
            f"r{concept.revision:03d}-{suffix}"
        )
        payload = {
            "disposition_id": disposition_id,
            "concept_revision_ref": concept.artifact_ref,
            "concept_sha256": artifact_record["sha256"],
            "stage": "C4",
            "outcome": outcome,
            "terminal": terminal,
            "target_ref": target_ref,
            "reason_codes": list(dict.fromkeys(reason_codes)),
            "decision_ref": decision_ref,
            "evidence_refs": list(evidence_refs),
            "task_refs": list(task_ids),
        }
        return self.hub.publish_artifact(
            artifact_id=disposition_id,
            artifact_type="creative_concept_disposition",
            relative_path=(
                "artifacts/creative/dispositions/"
                f"{disposition_id}.json"
            ),
            content=_json_text(payload),
            task_id=None,
            source_refs=(
                concept.artifact_ref,
                *evidence_refs,
                *((target_ref,) if target_ref is not None else ()),
            ),
            metadata={
                "concept_revision_ref": concept.artifact_ref,
                "outcome": outcome,
                "terminal": terminal,
                "target_ref": target_ref,
            },
        )

    async def _run_c5m(
        self,
        *,
        challenge_ref: str,
        constraint_ref: str,
        brief_ref: str,
        atom_refs: Sequence[str],
        base_concepts: Sequence[CreativeConcept],
        base_gate: HookGateOutcome,
    ) -> MemoryBranchOutcome:
        remix_slots = int(self.settings.max_memory_challengers)
        empty_slots = [
            {
                "slot": slot,
                "status": "not_started",
                "task_ref": None,
                "challenger_ref": None,
                "diagnostic_ref": None,
            }
            for slot in range(1, remix_slots + 1)
        ]
        mode = _snapshot_mode(self.memory_snapshot)
        if mode == "off":
            return self._publish_memory_summary(
                status="disabled",
                recall={
                    "status": "not_started",
                    "task_ref": None,
                    "diagnostic_ref": None,
                },
                selected_cue_ids=(),
                remix_slots=empty_slots,
                challengers=(),
                optional_failure_task_ids=(),
            )
        if not atom_refs or not _snapshot_has_entries(self.memory_snapshot):
            return self._publish_memory_summary(
                status="empty",
                recall={
                    "status": "not_started",
                    "task_ref": None,
                    "diagnostic_ref": None,
                },
                selected_cue_ids=(),
                remix_slots=empty_slots,
                challengers=(),
                optional_failure_task_ids=(),
            )

        recall_task = "creative-c5m-memory-recall-01"
        try:
            recall_output = await self._execute(
                stage=C5M_MEMORY_RECALL,
                task_id=recall_task,
                blocks=(
                    ("CHALLENGE_BRIEF", self.hub.read_artifact(challenge_ref)),
                    ("CREATIVE_BRIEF", self.hub.read_artifact(brief_ref)),
                    ("CURRENT_ATOM_INDEX", _artifact_index(self.hub, atom_refs)),
                    (
                        "BASE_CONCEPT_DISPOSITION_INDEX",
                        _concept_disposition_index(
                            self.hub, base_concepts, base_gate.disposition_refs
                        ),
                    ),
                    ("IDEA_MEMORY_SNAPSHOT", _snapshot_prompt_text(self.memory_snapshot)),
                ),
                parent_refs=(
                    challenge_ref,
                    constraint_ref,
                    brief_ref,
                    *atom_refs,
                    *(concept.artifact_ref for concept in base_concepts),
                    *base_gate.disposition_refs,
                    "input:idea_memory",
                ),
                failure_policy=OPTIONAL_BRANCH_FAILURE_POLICY,
            )
            recall_output = self._validate_completed_output(
                task_id=recall_task,
                stage=C5M_MEMORY_RECALL,
                output=recall_output,
                context={
                    "memory_snapshot": self.memory_snapshot,
                    "allowed_atom_refs": set(atom_refs),
                    "allowed_concept_refs": {
                        concept.artifact_ref for concept in base_concepts
                    },
                },
                failure_policy=OPTIONAL_BRANCH_FAILURE_POLICY,
            )
            cues: tuple[MemoryCue, ...] = validate_memory_inspiration_packet(
                recall_output,
                snapshot=self.memory_snapshot,
                current_atom_refs=atom_refs,
                related_concept_refs=tuple(
                    concept.artifact_ref for concept in base_concepts
                ),
                max_cues=int(self.settings.max_memory_selected_cues),
            )
            cue_ids = tuple(cue.cue_id for cue in cues)
        except AgentTaskExecutionError as exc:
            diagnostic = self._record_optional_failure(exc, sibling_statuses=())
            return self._publish_memory_summary(
                status="optional_failed",
                recall={
                    "status": _optional_failure_status(exc),
                    "task_ref": recall_task,
                    "diagnostic_ref": diagnostic,
                },
                selected_cue_ids=(),
                remix_slots=empty_slots,
                challengers=(),
                optional_failure_task_ids=(recall_task,),
            )
        except CreativeWorkflowError as exc:
            invalidated = self._invalidate_optional_task(
                recall_task,
                C5M_MEMORY_RECALL,
                exc,
            )
            diagnostic = self._record_optional_failure(
                invalidated, sibling_statuses=()
            )
            return self._publish_memory_summary(
                status="optional_failed",
                recall={
                    "status": "invalidated",
                    "task_ref": recall_task,
                    "diagnostic_ref": diagnostic,
                },
                selected_cue_ids=(),
                remix_slots=empty_slots,
                challengers=(),
                optional_failure_task_ids=(recall_task,),
            )

        packet_ref = self.hub.publish_artifact(
            artifact_id="creative-memory-inspiration-packet-r001",
            artifact_type="creative_memory_inspiration_packet",
            relative_path=(
                "artifacts/creative/memory/"
                "creative-memory-inspiration-packet-r001.json"
            ),
            content=_json_text(recall_output),
            task_id=recall_task,
            source_refs=("input:idea_memory", *atom_refs),
            metadata={"selected_cue_ids": list(cue_ids)},
        )
        if not cues:
            return self._publish_memory_summary(
                status="completed",
                recall={
                    "status": "succeeded",
                    "task_ref": recall_task,
                    "diagnostic_ref": None,
                },
                selected_cue_ids=(),
                remix_slots=empty_slots,
                challengers=(),
                optional_failure_task_ids=(),
            )

        slots_to_start = min(
            int(self.settings.memory_remixers),
            int(self.settings.max_memory_challengers),
        )

        async def remix(slot: int) -> CreativeConcept | None:
            task_id = f"creative-c5m-memory-remix-{slot:02d}"
            cue = cues[(slot - 1) % len(cues)]
            atom_ref = atom_refs[(slot - 1) % len(atom_refs)]
            output = await self._execute(
                stage=C5M_MEMORY_REMIX,
                task_id=task_id,
                blocks=(
                    ("CHALLENGE_BRIEF", self.hub.read_artifact(challenge_ref)),
                    ("CREATIVE_BRIEF", self.hub.read_artifact(brief_ref)),
                    ("CURRENT_ATOM", self.hub.read_artifact(atom_ref)),
                    ("MEMORY_CUE", _json_text(cue.to_dict())),
                ),
                parent_refs=(
                    challenge_ref,
                    brief_ref,
                    atom_ref,
                    packet_ref,
                ),
                failure_policy=OPTIONAL_BRANCH_FAILURE_POLICY,
            )
            try:
                cue_source_keys = {
                    reference.stable_key
                    for reference in cue.source_memory_refs
                }
                source_capsules = tuple(
                    capsule
                    for capsule in self.memory_snapshot.entries
                    if capsule.memory_ref.stable_key in cue_source_keys
                )
                output = self._validate_completed_output(
                    task_id=task_id,
                    stage=C5M_MEMORY_REMIX,
                    output=output,
                    context={
                        "memory_snapshot": self.memory_snapshot,
                        "allowed_atom_refs": {atom_ref},
                        "allowed_cue_refs": {cue.cue_id},
                        "atom_territories": {
                            atom_ref: str(
                                _artifact_metadata(self.hub, atom_ref)[
                                    "territory_ref"
                                ]
                            )
                        },
                        "memory_cues": (cue,),
                        "source_hooks": tuple(
                            capsule.entry.one_sentence_hook
                            for capsule in source_capsules
                        ),
                        "source_mechanism_reveals": tuple(
                            (
                                capsule.entry.core_mechanism,
                                capsule.entry.reveal_pattern,
                            )
                            for capsule in source_capsules
                        ),
                    },
                    failure_policy=OPTIONAL_BRANCH_FAILURE_POLICY,
                )
                raw_concept = output.get("concept")
                if raw_concept is None:
                    return None
                if not isinstance(raw_concept, dict):
                    raise CreativeWorkflowError(
                        f"{task_id} concept must be an object"
                    )
                concept_id = memory_concept_id(slot)
                artifact_ref = concept_revision_ref(concept_id, 1)
                current_atoms = tuple(_string_list(raw_concept, "current_atom_refs"))
                raw_memory_refs = raw_concept.get("memory_source_refs")
                if not isinstance(raw_memory_refs, list):
                    raise CreativeWorkflowError(
                        f"{task_id} memory_source_refs must be an array"
                    )
                memory_refs = tuple(
                    MemoryCapsuleRef.from_mapping(reference)
                    for reference in raw_memory_refs
                )
                returned_cues = tuple(_string_list(raw_concept, "cue_refs"))
                primary = _required_text(raw_concept, "primary_territory_ref")
                if not current_atoms or any(
                    ref not in atom_refs for ref in current_atoms
                ):
                    raise CreativeWorkflowError(
                        f"{task_id} must use at least one current Atom"
                    )
                if not memory_refs or not returned_cues:
                    raise CreativeWorkflowError(
                        f"{task_id} must use a memory source and cue"
                    )
                if any(ref not in cue_ids for ref in returned_cues):
                    raise CreativeWorkflowError(
                        f"{task_id} referenced an unknown cue"
                    )
                parent_territories = {
                    _artifact_metadata(self.hub, ref).get("territory_ref")
                    for ref in current_atoms
                }
                if primary not in parent_territories:
                    raise CreativeWorkflowError(
                        f"{task_id} primary territory is not from its current Atoms"
                    )
            except CreativeWorkflowError as exc:
                raise self._invalidate_optional_task(
                    task_id,
                    C5M_MEMORY_REMIX,
                    exc,
                ) from exc
            self.hub.publish_artifact(
                artifact_id=artifact_ref,
                artifact_type="creative_concept",
                relative_path=f"artifacts/creative/concepts/{artifact_ref}.md",
                content=_required_text(raw_concept, "markdown"),
                task_id=task_id,
                source_refs=(packet_ref, *current_atoms),
                metadata={
                    "concept_id": concept_id,
                    "origin": "memory_challenger",
                    "revision": 1,
                    "revision_reason": "memory_remix",
                    "primary_territory_ref": primary,
                    "parent_atom_refs": list(current_atoms),
                    "current_atom_refs": list(current_atoms),
                    "memory_source_refs": [
                        reference.to_dict() for reference in memory_refs
                    ],
                    "memory_cue_refs": list(returned_cues),
                    "remix_slot": slot,
                },
            )
            return CreativeConcept(
                concept_id=concept_id,
                revision=1,
                artifact_ref=artifact_ref,
                primary_territory_ref=primary,
                parent_atom_refs=current_atoms,
                origin="memory_challenger",
                task_id=task_id,
                memory_cue_refs=returned_cues,
                memory_source_refs=memory_refs,
            )

        settled = await asyncio.gather(
            *(remix(slot) for slot in range(1, slots_to_start + 1)),
            return_exceptions=True,
        )
        challengers: list[CreativeConcept] = []
        failed_tasks: list[str] = []
        slot_rows = list(empty_slots)
        for index, result in enumerate(settled, start=1):
            task_id = f"creative-c5m-memory-remix-{index:02d}"
            if isinstance(result, BaseException):
                if not isinstance(result, AgentTaskExecutionError):
                    raise result
                failed_tasks.append(task_id)
                sibling_statuses = tuple(
                    "succeeded"
                    if isinstance(other, CreativeConcept)
                    else "failed"
                    if isinstance(other, BaseException)
                    else "empty"
                    for other in settled
                )
                diagnostic = self._record_optional_failure(
                    result, sibling_statuses=sibling_statuses
                )
                slot_rows[index - 1] = {
                    "slot": index,
                    "status": _optional_failure_status(result),
                    "task_ref": task_id,
                    "challenger_ref": None,
                    "diagnostic_ref": diagnostic,
                }
            else:
                if result is not None:
                    challengers.append(result)
                slot_rows[index - 1] = {
                    "slot": index,
                    "status": "succeeded",
                    "task_ref": task_id,
                    "challenger_ref": (
                        result.artifact_ref if result is not None else None
                    ),
                    "diagnostic_ref": None,
                }
        return self._publish_memory_summary(
            status="optional_failed" if failed_tasks else "completed",
            recall={
                "status": "succeeded",
                "task_ref": recall_task,
                "diagnostic_ref": None,
            },
            selected_cue_ids=cue_ids,
            remix_slots=slot_rows,
            challengers=tuple(challengers),
            optional_failure_task_ids=tuple(failed_tasks),
        )

    def _invalidate_optional_task(
        self,
        task_id: str,
        stage: str,
        error: BaseException,
    ) -> AgentTaskExecutionError:
        self.hub.invalidate_task(task_id, error)
        return AgentTaskExecutionError(
            f"{task_id} returned invalid content: {error}",
            task_id=task_id,
            stage=stage,
            failure_policy=OPTIONAL_BRANCH_FAILURE_POLICY,
        )

    def _record_optional_failure(
        self,
        error: AgentTaskExecutionError,
        *,
        sibling_statuses: Sequence[str],
    ) -> str:
        event_id = f"optional-memory-stage-failed:{error.task_id}"
        self.hub.append_ledger_record(
            "events",
            {
                "event_id": event_id,
                "kind": "optional_memory_stage_failed",
                "data": {
                    "task_ref": error.task_id,
                    "stage": error.stage,
                    "failure_kind": type(error.__cause__).__name__
                    if error.__cause__ is not None
                    else type(error).__name__,
                    "sibling_outcomes": list(sibling_statuses),
                },
            },
        )
        return event_id

    def _publish_memory_summary(
        self,
        *,
        status: str,
        recall: Mapping[str, Any],
        selected_cue_ids: Sequence[str],
        remix_slots: Sequence[Mapping[str, Any]],
        challengers: Sequence[CreativeConcept],
        optional_failure_task_ids: Sequence[str],
    ) -> MemoryBranchOutcome:
        payload = {
            "status": status,
            "recall": dict(recall),
            "selected_cue_ids": list(selected_cue_ids),
            "remix_slots": [dict(slot) for slot in remix_slots],
        }
        artifact_ref = self.hub.publish_artifact(
            artifact_id="creative-memory-stage-summary-r001",
            artifact_type="creative_memory_stage_summary",
            relative_path=(
                "artifacts/creative/memory/"
                "creative-memory-stage-summary-r001.json"
            ),
            content=_json_text(payload),
            task_id=None,
            source_refs=tuple(
                concept.artifact_ref for concept in challengers
            ),
            metadata={
                "status": status,
                "selected_cue_ids": list(selected_cue_ids),
                "successful_challenger_refs": [
                    concept.artifact_ref for concept in challengers
                ],
                "failed_task_refs": list(optional_failure_task_ids),
            },
        )
        return MemoryBranchOutcome(
            challengers=tuple(challengers),
            summary_ref=artifact_ref,
            selected_cue_ids=tuple(selected_cue_ids),
            optional_failure_task_ids=tuple(optional_failure_task_ids),
        )

    async def _run_c5w(
        self,
        concepts: Sequence[CreativeConcept],
        *,
        challenge_ref: str,
        brief_ref: str,
    ) -> tuple[str, ...]:
        async def scan(concept: CreativeConcept) -> tuple[str, str]:
            task_id = f"creative-c5w-novelty-{concept.concept_id}-r{concept.revision:03d}"
            output = await self._execute(
                stage=C5W_NOVELTY_SCAN,
                task_id=task_id,
                blocks=(
                    ("CHALLENGE_BRIEF", self.hub.read_artifact(challenge_ref)),
                    ("CREATIVE_BRIEF", self.hub.read_artifact(brief_ref)),
                    ("CONCEPT_REVISION", self.hub.read_artifact(concept.artifact_ref)),
                ),
                parent_refs=(challenge_ref, brief_ref, concept.artifact_ref),
            )
            artifact_ref = f"creative-novelty-{concept.concept_id}-r{concept.revision:03d}"
            self.hub.publish_artifact(
                artifact_id=artifact_ref,
                artifact_type="creative_novelty_scan",
                relative_path=(
                    "artifacts/creative/novelty-scans/"
                    f"{artifact_ref}.md"
                ),
                content=_required_text(output, "markdown"),
                task_id=task_id,
                source_refs=(concept.artifact_ref,),
                metadata={
                    "concept_revision_ref": concept.artifact_ref,
                    "sources": output.get("sources", []),
                },
            )
            return concept.artifact_ref, artifact_ref

        completed = await asyncio.gather(*(scan(concept) for concept in concepts))
        return tuple(ref for _, ref in sorted(completed))

    async def _execute(
        self,
        *,
        stage: str,
        task_id: str,
        blocks: Sequence[tuple[str, str]],
        parent_refs: Sequence[str],
        failure_policy: FailurePolicy = "fatal",
    ) -> dict[str, Any]:
        try:
            return await self.task_executor.execute(
                stage=stage,
                task_id=task_id,
                blocks=blocks,
                parent_refs=parent_refs,
                failure_policy=failure_policy,
            )
        except AgentTaskExecutionError:
            raise
        except Exception as exc:
            raise CreativeWorkflowError(f"{task_id}: {exc}") from exc

    def _validate_completed_output(
        self,
        *,
        task_id: str,
        stage: str,
        output: Mapping[str, Any],
        context: CreativeValidationContext,
        failure_policy: FailurePolicy = "fatal",
    ) -> dict[str, Any]:
        try:
            return validate_creative_output(
                stage,
                output,
                settings=self.settings,
                context=context,
            )
        except Exception as exc:
            self.hub.invalidate_task(task_id, exc)
            raise AgentTaskExecutionError(
                f"{task_id} returned invalid content: {exc}",
                task_id=task_id,
                stage=stage,
                failure_policy=failure_policy,
            ) from exc


def _required_text(value: Mapping[str, Any], key: str) -> str:
    result = value.get(key)
    if not isinstance(result, str) or not result.strip():
        raise CreativeWorkflowError(f"output requires non-empty {key}")
    return result


def _positive_timeout(value: object, name: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or value <= 0
    ):
        raise ValueError(f"{name} must be positive")
    return float(value)


def _object_list(value: Mapping[str, Any], key: str) -> list[dict[str, Any]]:
    result = value.get(key)
    if not isinstance(result, list) or any(not isinstance(item, dict) for item in result):
        raise CreativeWorkflowError(f"output {key} must be an array of objects")
    return result


def _string_list(value: Mapping[str, Any], key: str) -> list[str]:
    result = value.get(key)
    if not isinstance(result, list) or any(
        not isinstance(item, str) or not item for item in result
    ):
        raise CreativeWorkflowError(f"output {key} must be an array of strings")
    return result


def _json_text(value: Mapping[str, Any]) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        indent=2,
        sort_keys=True,
    ) + "\n"


def _artifact_record(hub: RunHub, artifact_ref: str) -> dict[str, Any]:
    artifacts = hub.load_state().get("artifacts")
    if not isinstance(artifacts, dict):
        raise CreativeWorkflowError("run artifacts must be an object")
    record = artifacts.get(artifact_ref)
    if not isinstance(record, dict):
        raise CreativeWorkflowError(f"artifact is not registered: {artifact_ref}")
    return record


def _artifact_metadata(hub: RunHub, artifact_ref: str) -> dict[str, Any]:
    metadata = _artifact_record(hub, artifact_ref).get("metadata")
    if not isinstance(metadata, dict):
        raise CreativeWorkflowError(f"artifact has no metadata: {artifact_ref}")
    return metadata


def _artifact_index(hub: RunHub, artifact_refs: Sequence[str]) -> str:
    return "\n\n".join(
        f"## {ref}\n\n{hub.read_artifact(ref)}" for ref in artifact_refs
    )


def _concept_disposition_index(
    hub: RunHub,
    concepts: Sequence[CreativeConcept],
    disposition_refs: Sequence[str],
) -> str:
    payload = {
        "concepts": [
            {
                "concept_revision_ref": concept.artifact_ref,
                "primary_territory_ref": concept.primary_territory_ref,
                "parent_atom_refs": list(concept.parent_atom_refs),
                "hook": _normalized_section(
                    hub.read_artifact(concept.artifact_ref), "One-sentence Hook"
                ),
            }
            for concept in concepts
        ],
        "dispositions": [
            json.loads(hub.read_artifact(ref)) for ref in disposition_refs
        ],
    }
    return _json_text(payload)


def _input_text(hub: RunHub, name: str) -> str:
    inputs = hub.load_state().get("inputs")
    if not isinstance(inputs, dict) or not isinstance(inputs.get(name), dict):
        raise CreativeWorkflowError(f"run input is not registered: {name}")
    record = inputs[name]
    relative = record.get("path")
    if not isinstance(relative, str):
        raise CreativeWorkflowError(f"run input has no path: {name}")
    # The Hub core validator verifies the same path/hash pair offline.
    path = hub.run_dir.joinpath(*Path(relative).parts)
    content = path.read_text(encoding="utf-8")
    if sha256_text(content) != record.get("sha256"):
        raise CreativeWorkflowError(f"run input hash mismatch: {name}")
    return content


def _review_decision(output: Mapping[str, Any]) -> str:
    decision = output.get("overall_decision")
    if decision not in {"pass", "repairable", "invalid"}:
        raise CreativeWorkflowError("Hook review has invalid overall_decision")
    return str(decision)


def _review_reason_codes(
    outputs: Sequence[Mapping[str, Any]] | Any,
) -> tuple[str, ...]:
    codes: list[str] = []
    for output in outputs:
        raw_codes = output.get("reason_codes", [])
        if isinstance(raw_codes, list):
            codes.extend(code for code in raw_codes if isinstance(code, str) and code)
        dimensions = output.get("dimensions", [])
        if isinstance(dimensions, list):
            for dimension in dimensions:
                if isinstance(dimension, dict):
                    code = dimension.get("reason_code")
                    if isinstance(code, str) and code:
                        codes.append(code)
    return tuple(dict.fromkeys(codes))


def _normalized_text(value: str) -> str:
    return " ".join(value.casefold().split())


def _normalized_section(markdown: str, heading: str) -> str:
    pattern = re.compile(
        rf"(?ms)^##[ \t]+{re.escape(heading)}[ \t]*\n+(.*?)(?=^##[ \t]+|\Z)"
    )
    match = pattern.search(markdown)
    return _normalized_text(match.group(1)) if match is not None else ""


def _snapshot_mode(snapshot: Any) -> str:
    mode = getattr(snapshot, "mode", None)
    if isinstance(mode, str):
        return mode
    if isinstance(snapshot, Mapping) and isinstance(snapshot.get("mode"), str):
        return str(snapshot["mode"])
    raise CreativeWorkflowError("Idea Memory Snapshot has no mode")


def _snapshot_has_entries(snapshot: Any) -> bool:
    value = getattr(snapshot, "has_eligible_entries", None)
    if isinstance(value, bool):
        return value
    if callable(value):
        return bool(value())
    if isinstance(snapshot, Mapping):
        entries = snapshot.get("entries")
        return isinstance(entries, list) and bool(entries)
    return False


def _snapshot_prompt_text(snapshot: Any) -> str:
    for name in ("capsule_prompt_text", "prompt_text", "to_prompt_text"):
        value = getattr(snapshot, name, None)
        if callable(value):
            rendered = value()
            if isinstance(rendered, str):
                return rendered
        elif isinstance(value, str):
            return value
    to_dict = getattr(snapshot, "to_dict", None)
    if callable(to_dict):
        value = to_dict()
    elif isinstance(snapshot, Mapping):
        value = dict(snapshot)
    else:
        raise CreativeWorkflowError("Idea Memory Snapshot has no prompt projection")
    if not isinstance(value, dict):
        raise CreativeWorkflowError("Idea Memory Snapshot projection must be an object")
    return _json_text(value)


def _optional_failure_status(error: AgentTaskExecutionError) -> str:
    message = str(error)
    return "invalidated" if "invalid content" in message else "failed"
