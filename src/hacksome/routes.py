"""Route registry and offline run projections."""

from __future__ import annotations

from dataclasses import dataclass
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
class PendingCreativeRunContract:
    """Minimal slice-one projection until the Creative contract is registered."""

    route_id: str = "creative"
    contract_version: str = "1"
    supported_schema_versions: frozenset[int] = frozenset({RUN_SCHEMA_VERSION})

    def inspect(self, hub: RunHub, state: Mapping[str, Any]) -> dict[str, Any]:
        return hub.core_inspect()

    def validate(
        self,
        hub: RunHub,
        state: Mapping[str, Any],
    ) -> list[str]:
        return []


_CONTRACTS: dict[str, RunContract] = {
    "useful": UsefulRunContract(),
    "creative": PendingCreativeRunContract(),
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
