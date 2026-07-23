"""Route registry and offline run projections."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Mapping, Protocol

from hacksome.hub import (
    LEGACY_RUN_SCHEMA_VERSION,
    RUN_SCHEMA_VERSION,
    RunHub,
)
from hacksome.prompting import PromptResourceError, useful_prompt_catalog
from hacksome.state import StateError, read_jsonl


class RouteContractError(StateError):
    """A persisted run cannot be dispatched to a supported route contract."""


class RunContract(Protocol):
    """One route's offline inspect and semantic validation contract."""

    @property
    def route_id(self) -> str: ...

    @property
    def contract_version(self) -> str: ...

    @property
    def supported_schema_versions(self) -> frozenset[int]: ...

    def inspect(self, hub: RunHub, state: Mapping[str, Any]) -> dict[str, Any]: ...

    def validate(
        self,
        hub: RunHub,
        state: Mapping[str, Any],
    ) -> list[str]: ...


@dataclass(frozen=True, slots=True)
class UsefulRunContract:
    """The existing Useful projection, kept byte/field compatible."""

    route_id: str = "useful"
    contract_version: str = "1"
    supported_schema_versions: frozenset[int] = frozenset(
        {LEGACY_RUN_SCHEMA_VERSION, RUN_SCHEMA_VERSION}
    )

    def inspect(self, hub: RunHub, state: Mapping[str, Any]) -> dict[str, Any]:
        core = hub.core_inspect()
        cards = state.get("idea_card_ids", [])
        return {
            "run_id": core["run_id"],
            "status": core["status"],
            "current_stage": core["current_stage"],
            "task_counts": core["task_counts"],
            "decision_count": core["decision_count"],
            "idea_card_count": len(cards) if isinstance(cards, list) else 0,
            "run_dir": core["run_dir"],
        }

    def validate(
        self,
        hub: RunHub,
        state: Mapping[str, Any],
    ) -> list[str]:
        errors: list[str] = []
        if state.get("schema_version") == RUN_SCHEMA_VERSION:
            route = state.get("route")
            manifest = state.get("resource_manifest")
            if isinstance(route, dict) and isinstance(manifest, dict):
                try:
                    useful_prompt_catalog.load_frozen(
                        hub.run_dir,
                        route_id="useful",
                        contract_version=str(route.get("contract_version", "")),
                        prompt_policy_version=str(
                            route.get("prompt_policy_version", "")
                        ),
                        stage_policy_version=str(
                            route.get("stage_policy_version", "")
                        ),
                        manifest_sha256=str(manifest.get("sha256", "")),
                    )
                except PromptResourceError as exc:
                    errors.append(str(exc))
        try:
            decisions = read_jsonl(hub.decisions_path)
        except (OSError, StateError) as exc:
            errors.append(str(exc))
            decisions = []
        for index, row in enumerate(decisions, start=1):
            if not isinstance(row.get("decision_id"), str):
                errors.append(f"decision {index} has no decision_id")
            if row.get("decision") not in {"pass", "reject"}:
                errors.append(f"decision {index} has invalid decision")

        passed_ideas = {
            row.get("candidate_ref")
            for row in decisions
            if row.get("gate") == "idea-red-team" and row.get("decision") == "pass"
        }
        passed_problems = {
            row.get("candidate_ref")
            for row in decisions
            if row.get("gate") == "problem-gateway" and row.get("decision") == "pass"
        }
        artifacts = state.get("artifacts")
        if not isinstance(artifacts, dict):
            return errors
        cards = state.get("idea_card_ids", [])
        if not isinstance(cards, list):
            errors.append("idea_card_ids must be a list")
            cards = []
        for card_id in cards:
            record = artifacts.get(card_id)
            if not isinstance(record, dict) or record.get("artifact_type") != "idea_card":
                errors.append(f"Idea Card is not registered: {card_id}")
                continue
            source_refs = record.get("source_refs", [])
            if not isinstance(source_refs, list) or not any(
                source in passed_ideas for source in source_refs
            ):
                errors.append(f"Idea Card has no passed Idea source: {card_id}")
            if not isinstance(source_refs, list) or not any(
                source in passed_problems for source in source_refs
            ):
                errors.append(f"Idea Card has no passed Problem source: {card_id}")
        return errors


@dataclass(frozen=True, slots=True)
class CreativeRunContract:
    """Offline projection and currently implemented Creative invariants."""

    route_id: str = "creative"
    contract_version: str = "1"
    supported_schema_versions: frozenset[int] = frozenset({RUN_SCHEMA_VERSION})

    def inspect(self, hub: RunHub, state: Mapping[str, Any]) -> dict[str, Any]:
        core = hub.core_inspect()
        artifacts = state.get("artifacts")
        if not isinstance(artifacts, dict):
            artifacts = {}
        concepts: dict[str, dict[str, Any]] = {
            str(artifact_id): record
            for artifact_id, record in artifacts.items()
            if isinstance(record, dict)
            and record.get("artifact_type") == "creative_concept"
        }
        base_generated = sum(
            1
            for record in concepts.values()
            if _metadata_value(record, "origin") == "base"
            and _metadata_value(record, "revision") == 1
        )
        memory_challengers = sum(
            1
            for record in concepts.values()
            if _metadata_value(record, "origin") == "memory_challenger"
            and _metadata_value(record, "revision") == 1
        )
        dispositions = _creative_dispositions(hub, artifacts)
        hook_passed = {
            row.get("concept_revision_ref")
            for row in dispositions
            if row.get("stage") == "C4" and row.get("outcome") == "pass"
        }
        shortlisted = {
            row.get("concept_revision_ref")
            for row in dispositions
            if row.get("outcome") == "shortlisted"
        }
        finals = {
            str(artifact_id)
            for artifact_id, record in artifacts.items()
            if isinstance(record, dict)
            and record.get("artifact_type") == "creative_final_idea"
        }
        inputs = state.get("inputs")
        memory_input: dict[str, Any] = {}
        if isinstance(inputs, dict):
            candidate_memory_input = inputs.get("idea_memory")
            if isinstance(candidate_memory_input, dict):
                memory_input = candidate_memory_input
        summary_records = [
            record
            for record in artifacts.values()
            if isinstance(record, dict)
            and record.get("artifact_type") == "creative_memory_stage_summary"
        ]
        summary_metadata = (
            summary_records[0].get("metadata", {})
            if len(summary_records) == 1
            else {}
        )
        wait = state.get("wait")
        review = wait if isinstance(wait, dict) else {}
        report_ref = _first_artifact_of_type(
            artifacts, "creative_idea_report_json"
        )
        partial_report_ref = _first_artifact_of_type(
            artifacts, "creative_partial_report_json"
        )
        return {
            "route_id": "creative",
            "run_id": core["run_id"],
            "status": core["status"],
            "current_stage": core["current_stage"],
            "task_counts": core["task_counts"],
            "concept_counts": {
                "base_generated": base_generated,
                "memory_challengers": memory_challengers,
                "generated_total": base_generated + memory_challengers,
                "hook_passed": len(hook_passed),
                "shortlisted": len(shortlisted),
                "final": len(finals),
            },
            "memory": {
                "mode": memory_input.get("mode"),
                "snapshot_sha256": memory_input.get("sha256"),
                "eligible_entry_count": memory_input.get(
                    "eligible_entry_count", 0
                ),
                "selected_cue_count": len(
                    summary_metadata.get("selected_cue_ids", [])
                )
                if isinstance(summary_metadata, dict)
                and isinstance(summary_metadata.get("selected_cue_ids", []), list)
                else 0,
                "status": summary_metadata.get("status", "not_started")
                if isinstance(summary_metadata, dict)
                else "not_started",
            },
            "review": {
                "round_id": review.get("round_id"),
                "status": review.get("status", "not_started"),
                "reviewer_count": 0,
                "covered_concept_count": 0,
                "shortlist_count": len(shortlisted),
                "resumable": review.get("status") == "closed",
            },
            "finalization": {
                "status": "not_started",
                "manifest_ref": None,
                "planned_artifact_count": 0,
                "published_artifact_count": 0,
                "resumable": False,
            },
            "zero_reason_code": state.get("zero_reason_code"),
            "report_ref": report_ref,
            "partial_report_ref": partial_report_ref,
            "needs_reconcile": core["needs_reconcile"],
            "run_dir": core["run_dir"],
        }

    def validate(
        self,
        hub: RunHub,
        state: Mapping[str, Any],
    ) -> list[str]:
        from hacksome.config import (
            PersistedConfigError,
            decode_persisted_dataclass,
        )
        from hacksome.creative.contracts import CreativeWorkflowSettings
        from hacksome.creative.memory import (
            MemoryCapsuleRef,
            MemoryRemixSlot,
            MemoryStageSummary,
            MemoryTaskSlot,
            MemoryValidationError,
        )
        from hacksome.creative.prompting import (
            creative_prompt_catalog,
        )

        errors: list[str] = []
        route = state.get("route")
        manifest = state.get("resource_manifest")
        if isinstance(route, dict) and isinstance(manifest, dict):
            try:
                creative_prompt_catalog.load_frozen(
                    hub.run_dir,
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
            except PromptResourceError as exc:
                errors.append(str(exc))

        settings: Any = None
        hashes = state.get("config_hashes")
        raw_settings = state.get("settings")
        if isinstance(hashes, dict) and isinstance(raw_settings, dict):
            expected = hashes.get("workflow_settings_sha256")
            if isinstance(expected, str):
                try:
                    settings = decode_persisted_dataclass(
                        CreativeWorkflowSettings,
                        raw_settings,
                        expected_sha256=expected,
                    )
                except PersistedConfigError as exc:
                    errors.append(str(exc))

        try:
            events = read_jsonl(hub.events_path)
        except (OSError, StateError) as exc:
            errors.append(str(exc))
            events = []
        optional_failure_events: dict[str, list[dict[str, Any]]] = {}
        for row in events:
            if row.get("kind") != "optional_memory_stage_failed":
                continue
            data = row.get("data")
            task_ref = data.get("task_ref") if isinstance(data, dict) else None
            if not isinstance(task_ref, str) or not task_ref:
                errors.append(
                    "optional_memory_stage_failed event has no task_ref"
                )
                continue
            optional_failure_events.setdefault(task_ref, []).append(row)
        tasks = state.get("tasks")
        if not isinstance(tasks, dict):
            tasks = {}
        for task_id, raw in tasks.items():
            if not isinstance(raw, dict):
                continue
            stage = raw.get("stage")
            if not isinstance(stage, str) or stage not in creative_prompt_catalog:
                errors.append(f"Creative task {task_id} has unsupported stage")
                continue
            spec = creative_prompt_catalog[stage]
            if raw.get("web_search") is not spec.web_search:
                errors.append(f"Creative task {task_id} web policy mismatch")
            if bool(raw.get("web_search")) != (
                stage == "creative-novelty-scan"
            ):
                errors.append(
                    f"Creative task {task_id} violates novelty-only web policy"
                )
            failure_policy = raw.get("failure_policy", "fatal")
            if failure_policy == "optional_branch" and stage not in {
                "creative-memory-recall",
                "creative-memory-remix",
            }:
                errors.append(
                    f"Creative task {task_id} illegally uses optional_branch"
                )
            if raw.get("status") in {"failed", "invalidated"}:
                if failure_policy == "optional_branch":
                    if len(optional_failure_events.get(str(task_id), [])) != 1:
                        errors.append(
                            f"optional Creative task {task_id} must have exactly "
                            "one diagnostic event"
                        )
                elif state.get("status") != "failed":
                    errors.append(
                        f"fatal Creative task {task_id} failed in a non-failed run"
                    )
            elif task_id in optional_failure_events:
                errors.append(
                    f"optional diagnostic references non-failed task {task_id}"
                )
            if stage in {
                "creative-territory-explore",
                "creative-concept-synthesize",
                "creative-cheap-hook-review",
            }:
                parent_refs = raw.get("parent_refs", [])
                if isinstance(parent_refs, list) and any(
                    ref == "input:idea_memory"
                    or "memory-inspiration" in str(ref)
                    for ref in parent_refs
                ):
                    errors.append(
                        f"Creative task {task_id} received Idea Memory too early"
                    )
                prompt_path = raw.get("prompt_path")
                if isinstance(prompt_path, str):
                    try:
                        prompt = hub.run_dir.joinpath(
                            *Path(prompt_path).parts
                        ).read_text(encoding="utf-8")
                    except (OSError, UnicodeError):
                        prompt = ""
                    if "<BEGIN_IDEA_MEMORY_" in prompt or "<BEGIN_MEMORY_CUE_" in prompt:
                        errors.append(
                            f"Creative task {task_id} Prompt contains early memory context"
                        )

        for task_ref, matching_events in optional_failure_events.items():
            raw_task = tasks.get(task_ref)
            if not isinstance(raw_task, dict):
                errors.append(
                    f"optional diagnostic references unknown task {task_ref}"
                )
                continue
            if len(matching_events) != 1:
                errors.append(
                    f"optional Creative task {task_ref} must have exactly "
                    "one diagnostic event"
                )
            stage = raw_task.get("stage")
            data = matching_events[0].get("data") if matching_events else None
            if not isinstance(data, dict) or data.get("stage") != stage:
                errors.append(
                    f"optional diagnostic stage mismatch for task {task_ref}"
                )
            if raw_task.get("failure_policy") != "optional_branch":
                errors.append(
                    f"optional diagnostic references fatal task {task_ref}"
                )
            if raw_task.get("status") not in {"failed", "invalidated"}:
                errors.append(
                    f"optional diagnostic references non-failed task {task_ref}"
                )

        artifacts = state.get("artifacts")
        if not isinstance(artifacts, dict):
            return errors
        concepts = {
            str(artifact_id): record
            for artifact_id, record in artifacts.items()
            if isinstance(record, dict)
            and record.get("artifact_type") == "creative_concept"
        }
        atom_records = {
            str(artifact_id): record
            for artifact_id, record in artifacts.items()
            if isinstance(record, dict)
            and record.get("artifact_type") == "creative_atom"
        }
        base_count = 0
        memory_count = 0
        revisions: dict[str, set[int]] = {}
        revision_reasons: dict[str, list[str]] = {}
        for artifact_id, record in concepts.items():
            metadata = record.get("metadata")
            if not isinstance(metadata, dict):
                errors.append(f"Creative Concept {artifact_id} has no metadata")
                continue
            concept_id = metadata.get("concept_id")
            revision = metadata.get("revision")
            origin = metadata.get("origin")
            primary = metadata.get("primary_territory_ref")
            parents = metadata.get("parent_atom_refs")
            if not isinstance(concept_id, str) or not concept_id:
                errors.append(f"Creative Concept {artifact_id} has no concept_id")
            if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
                errors.append(f"Creative Concept {artifact_id} has invalid revision")
            elif isinstance(concept_id, str):
                revisions.setdefault(concept_id, set()).add(revision)
                reason = metadata.get("revision_reason")
                if isinstance(reason, str):
                    revision_reasons.setdefault(concept_id, []).append(reason)
            if origin not in {"base", "memory_challenger"}:
                errors.append(f"Creative Concept {artifact_id} has invalid origin")
            elif revision == 1 and origin == "base":
                base_count += 1
            elif revision == 1 and origin == "memory_challenger":
                memory_count += 1
                raw_memory_refs = metadata.get("memory_source_refs")
                raw_cue_refs = metadata.get("memory_cue_refs")
                if (
                    not isinstance(raw_memory_refs, list)
                    or not raw_memory_refs
                ):
                    errors.append(
                        f"Memory challenger {artifact_id} has no memory refs"
                    )
                else:
                    for reference in raw_memory_refs:
                        try:
                            MemoryCapsuleRef.from_mapping(reference)
                        except MemoryValidationError as exc:
                            errors.append(
                                f"Memory challenger {artifact_id} has invalid "
                                f"memory ref: {exc}"
                            )
                if (
                    not isinstance(raw_cue_refs, list)
                    or not raw_cue_refs
                    or any(
                        not isinstance(reference, str) or not reference
                        for reference in raw_cue_refs
                    )
                    or len(raw_cue_refs) != len(set(raw_cue_refs))
                ):
                    errors.append(
                        f"Memory challenger {artifact_id} has invalid cue refs"
                    )
                source_task = record.get("task_id")
                source_task_record = (
                    tasks.get(source_task)
                    if isinstance(source_task, str)
                    else None
                )
                if (
                    not isinstance(source_task, str)
                    or not isinstance(source_task_record, dict)
                    or source_task_record.get("stage")
                    != "creative-memory-remix"
                    or source_task_record.get("status") != "succeeded"
                ):
                    errors.append(
                        f"Memory challenger {artifact_id} has no successful "
                        "Memory Remix task"
                    )
            if not isinstance(parents, list) or not parents:
                errors.append(f"Creative Concept {artifact_id} has no Parent Atoms")
            else:
                territories = {
                    _metadata_value(atom_records.get(str(parent), {}), "territory_ref")
                    for parent in parents
                }
                if primary not in territories:
                    errors.append(
                        f"Creative Concept {artifact_id} primary territory mismatch"
                    )
        if settings is not None:
            if base_count > (
                int(settings.concept_synthesizers)
                * int(settings.max_concepts_per_synthesizer)
            ):
                errors.append("base Creative Concept count exceeds persisted limit")
            if memory_count > int(settings.max_memory_challengers):
                errors.append("memory challenger count exceeds persisted limit")
        for concept_id, values in revisions.items():
            if values != set(range(1, max(values) + 1)):
                errors.append(f"Creative Concept {concept_id} revision gap")
            reasons = revision_reasons.get(concept_id, [])
            for reason, limit in (
                ("cheap_hook_repair", 1),
                ("evidence_informed", 1),
                ("human_feedback", 1),
            ):
                if reasons.count(reason) > limit:
                    errors.append(
                        f"Creative Concept {concept_id} exceeds {reason} budget"
                    )

        decisions = []
        try:
            decisions = read_jsonl(hub.decisions_path)
        except (OSError, StateError) as exc:
            errors.append(str(exc))
        decision_ids = {
            row.get("decision_id")
            for row in decisions
            if row.get("route_id") == "creative"
        }
        dispositions = _creative_dispositions(hub, artifacts, errors=errors)
        terminal_counts: dict[str, int] = {}
        hook_passed: set[str] = set()
        c4_routing: dict[str, list[dict[str, Any]]] = {}
        for disposition in dispositions:
            concept_ref = disposition.get("concept_revision_ref")
            if concept_ref not in concepts:
                errors.append(
                    f"Creative disposition references unknown Concept: {concept_ref}"
                )
                continue
            concept_record = concepts[str(concept_ref)]
            if disposition.get("concept_sha256") != concept_record.get("sha256"):
                errors.append(
                    f"Creative disposition Concept hash mismatch: {concept_ref}"
                )
            if disposition.get("decision_ref") not in decision_ids:
                errors.append(
                    f"Creative disposition has unknown decision: "
                    f"{disposition.get('decision_ref')}"
                )
            terminal = disposition.get("terminal")
            if terminal is True:
                terminal_counts[str(concept_ref)] = (
                    terminal_counts.get(str(concept_ref), 0) + 1
                )
            outcome = disposition.get("outcome")
            if outcome == "pass":
                hook_passed.add(str(concept_ref))
            if (
                disposition.get("stage") == "C4"
                and outcome
                in {"pass", "eliminated", "superseded_by_hook_repair"}
            ):
                c4_routing.setdefault(str(concept_ref), []).append(
                    disposition
                )
            target = disposition.get("target_ref")
            if target is not None and target not in concepts:
                errors.append(
                    f"Creative disposition target does not exist: {target}"
                )
            if outcome in {"superseded_by_hook_repair"} and target is None:
                errors.append(
                    f"Creative disposition {outcome} requires target_ref"
                )
            if outcome in {"eliminated"} and target is not None:
                errors.append(
                    f"Creative disposition {outcome} must not have target_ref"
                )
        if any(count > 1 for count in terminal_counts.values()):
            errors.append("Creative Concept revision has multiple terminal dispositions")

        novelty_records = {
            str(artifact_id): record
            for artifact_id, record in artifacts.items()
            if isinstance(record, dict)
            and record.get("artifact_type") == "creative_novelty_scan"
        }
        novelty_by_concept: dict[str, list[str]] = {}
        for artifact_id, record in novelty_records.items():
            source_refs = record.get("source_refs", [])
            concept_sources = [
                ref for ref in source_refs if isinstance(ref, str) and ref in concepts
            ] if isinstance(source_refs, list) else []
            if len(concept_sources) != 1 or concept_sources[0] not in hook_passed:
                errors.append(
                    f"Novelty Scan {artifact_id} has no C4-pass Concept source"
                )
            elif len(concept_sources) == 1:
                novelty_by_concept.setdefault(concept_sources[0], []).append(
                    artifact_id
                )

        if state.get("current_stage") == "creative-c5-complete-internal":
            for concept_ref in sorted(concepts):
                routing = c4_routing.get(concept_ref, [])
                if len(routing) != 1:
                    errors.append(
                        f"Creative Concept {concept_ref} must have exactly one "
                        "final C4 routing outcome at C5 completion"
                    )
                    continue
                outcome = routing[0].get("outcome")
                scan_count = len(novelty_by_concept.get(concept_ref, []))
                if outcome == "pass" and scan_count != 1:
                    errors.append(
                        f"C4-pass Concept {concept_ref} must have exactly one "
                        "Novelty Scan"
                    )
                elif outcome != "pass" and scan_count:
                    errors.append(
                        f"non-pass Concept {concept_ref} must not have a "
                        "Novelty Scan"
                    )

        summaries = [
            artifact_id
            for artifact_id, record in artifacts.items()
            if isinstance(record, dict)
            and record.get("artifact_type") == "creative_memory_stage_summary"
        ]
        reached_memory = any(
            isinstance(raw, dict)
            and raw.get("stage") in {
                "creative-memory-recall",
                "creative-memory-remix",
                "creative-novelty-scan",
            }
            for raw in tasks.values()
        ) or state.get("current_stage") in {
            "creative-c5-complete-internal",
            "creative-novelty-scan",
        }
        if reached_memory and len(summaries) != 1:
            errors.append("Creative C5 must publish exactly one MemoryStageSummary")
        elif len(summaries) == 1:
            summary_id = str(summaries[0])
            try:
                summary = MemoryStageSummary.from_mapping(
                    json.loads(hub.read_artifact(summary_id))
                )
            except (
                OSError,
                UnicodeError,
                json.JSONDecodeError,
                StateError,
                MemoryValidationError,
            ) as exc:
                errors.append(f"invalid MemoryStageSummary {summary_id}: {exc}")
            else:
                summary_record = artifacts.get(summary_id)
                summary_metadata = (
                    summary_record.get("metadata")
                    if isinstance(summary_record, dict)
                    else None
                )
                if (
                    not isinstance(summary_metadata, dict)
                    or summary_metadata.get("status") != summary.status
                    or summary_metadata.get("selected_cue_ids")
                    != list(summary.selected_cue_ids)
                ):
                    errors.append(
                        "MemoryStageSummary metadata does not match its payload"
                    )
                referenced_diagnostics: set[str] = set()
                memory_slots: list[
                    tuple[MemoryTaskSlot | MemoryRemixSlot, str]
                ] = [
                    (summary.recall, "creative-memory-recall"),
                    *(
                        (slot, "creative-memory-remix")
                        for slot in summary.remix_slots
                    ),
                ]
                for slot, expected_stage in memory_slots:
                    if slot.task_ref is not None:
                        task_record = tasks.get(slot.task_ref)
                        if not isinstance(task_record, dict):
                            errors.append(
                                "MemoryStageSummary references unknown task "
                                f"{slot.task_ref}"
                            )
                        elif task_record.get("stage") != expected_stage:
                            errors.append(
                                "MemoryStageSummary task stage mismatch for "
                                f"{slot.task_ref}"
                            )
                        elif slot.status == "succeeded" and task_record.get(
                            "status"
                        ) != "succeeded":
                            errors.append(
                                "MemoryStageSummary marks non-successful task "
                                f"{slot.task_ref} as succeeded"
                            )
                        elif slot.status in {"failed", "invalidated"} and (
                            task_record.get("status")
                            not in {"failed", "invalidated"}
                        ):
                            errors.append(
                                "MemoryStageSummary failure status does not "
                                f"match task {slot.task_ref}"
                            )
                    if slot.diagnostic_ref is not None:
                        referenced_diagnostics.add(slot.diagnostic_ref)
                event_ids = {
                    str(row.get("event_id"))
                    for rows in optional_failure_events.values()
                    for row in rows
                    if isinstance(row.get("event_id"), str)
                }
                if referenced_diagnostics != event_ids:
                    errors.append(
                        "MemoryStageSummary diagnostic refs do not exactly "
                        "match optional failure events"
                    )
                for slot in summary.remix_slots:
                    if slot.challenger_ref is None:
                        continue
                    challenger = concepts.get(slot.challenger_ref)
                    if (
                        not isinstance(challenger, dict)
                        or _metadata_value(challenger, "origin")
                        != "memory_challenger"
                        or challenger.get("task_id") != slot.task_ref
                    ):
                        errors.append(
                            "MemoryStageSummary challenger/task link is invalid: "
                            f"{slot.challenger_ref}"
                        )
        return errors


_CONTRACTS: dict[str, RunContract] = {
    "useful": UsefulRunContract(),
    "creative": CreativeRunContract(),
}


def register_run_contract(contract: RunContract, *, replace: bool = False) -> None:
    """Register a route contract; Creative uses this after its package loads."""

    route_id = contract.route_id
    if not isinstance(route_id, str) or not route_id:
        raise ValueError("route contract requires a non-empty route_id")
    if route_id in _CONTRACTS and not replace:
        raise RouteContractError(f"route contract is already registered: {route_id}")
    _CONTRACTS[route_id] = contract


def get_run_contract(
    state: Mapping[str, Any],
) -> RunContract:
    """Resolve and version-check the contract encoded in a run snapshot."""

    schema_version = state.get("schema_version")
    if schema_version not in {LEGACY_RUN_SCHEMA_VERSION, RUN_SCHEMA_VERSION}:
        raise RouteContractError(
            f"unsupported run schema version: {schema_version!r}"
        )
    route = state.get("route")
    if not isinstance(route, dict):
        raise RouteContractError("run has no route metadata")
    route_id = route.get("id")
    if not isinstance(route_id, str) or not route_id:
        raise RouteContractError("run route has no non-empty id")
    contract = _CONTRACTS.get(route_id)
    if contract is None:
        raise RouteContractError(f"unknown run route: {route_id!r}")
    if schema_version not in contract.supported_schema_versions:
        raise RouteContractError(
            f"route {route_id!r} does not support run schema {schema_version}"
        )
    contract_version = route.get("contract_version")
    if contract_version != contract.contract_version:
        raise RouteContractError(
            f"unsupported {route_id!r} contract version: {contract_version!r}"
        )
    if schema_version == LEGACY_RUN_SCHEMA_VERSION and route_id != "useful":
        raise RouteContractError("schema v1 can only be projected as route 'useful'")
    if schema_version == RUN_SCHEMA_VERSION:
        for key in (
            "prompt_policy_version",
            "stage_policy_version",
            "report_policy_version",
        ):
            value = route.get(key)
            if not isinstance(value, str) or not value:
                raise RouteContractError(
                    f"route {route_id!r} has no valid {key}"
                )
    return contract


def inspect_run(run_dir: str | Path) -> dict[str, Any]:
    hub = RunHub(run_dir)
    state = hub.load_state()
    contract = get_run_contract(state)
    return contract.inspect(hub, state)


def validate_run(run_dir: str | Path) -> list[str]:
    try:
        hub = RunHub(run_dir)
        state = hub.load_state()
        contract = get_run_contract(state)
    except (OSError, StateError) as exc:
        return [str(exc)]
    errors = hub.core_validate()
    errors.extend(contract.validate(hub, state))
    return errors


def _metadata_value(record: Mapping[str, Any], key: str) -> Any:
    metadata = record.get("metadata")
    return metadata.get(key) if isinstance(metadata, dict) else None


def _first_artifact_of_type(
    artifacts: Mapping[str, Any],
    artifact_type: str,
) -> str | None:
    values = sorted(
        str(artifact_id)
        for artifact_id, record in artifacts.items()
        if isinstance(record, dict) and record.get("artifact_type") == artifact_type
    )
    return values[0] if values else None


def _creative_dispositions(
    hub: RunHub,
    artifacts: Mapping[str, Any],
    *,
    errors: list[str] | None = None,
) -> list[dict[str, Any]]:
    dispositions: list[dict[str, Any]] = []
    for artifact_id, record in sorted(artifacts.items()):
        if not isinstance(record, dict) or record.get(
            "artifact_type"
        ) != "creative_concept_disposition":
            continue
        try:
            value = json.loads(hub.read_artifact(str(artifact_id)))
        except (OSError, UnicodeError, json.JSONDecodeError, StateError) as exc:
            if errors is not None:
                errors.append(f"invalid Creative disposition {artifact_id}: {exc}")
            continue
        if not isinstance(value, dict):
            if errors is not None:
                errors.append(
                    f"Creative disposition {artifact_id} must be an object"
                )
            continue
        dispositions.append(value)
    return dispositions
