"""Deterministic rendering for the final Useful Idea report.

This module intentionally contains no model calls and no product judgement. The
workflow supplies text already present in validated artifacts; the renderer
only orders, escapes, and links it.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping

from hacksome.state import atomic_write_bytes


@dataclass(frozen=True, slots=True)
class ReportIdea:
    artifact_id: str
    idea_ref: str
    target_user: str
    problem: str
    felt_value: str
    user_flow: str
    core_mechanism: str
    minimum_features: str
    alternatives_and_adoption: str
    sponsor_technology: str
    beta_scope: str
    highest_risk_dependencies: str
    evidence_refs: tuple[str, ...] = ()
    review_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class EliminationSummary:
    candidate_ref: str
    stage: str
    rule: str
    reason: str
    decision_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ReportInput:
    run_id: str
    challenge_title: str
    challenge_ref: str
    started_at: str
    completed_at: str | None
    stage_statuses: Mapping[str, str]
    ideas: tuple[ReportIdea, ...] = ()
    eliminations: tuple[EliminationSummary, ...] = ()
    warnings: tuple[str, ...] = ()


def _clean(value: str | None) -> str:
    text = (value or "").strip()
    return text if text else "_Not recorded._"


def _link(ref: str) -> str:
    normalized = ref.replace("\\", "/")
    label = Path(normalized).name
    return f"[{label}]({normalized})"


def _linked_refs(refs: Iterable[str]) -> str:
    ordered = sorted(dict.fromkeys(refs))
    return ", ".join(_link(ref) for ref in ordered) if ordered else "_None._"


def render_report(data: ReportInput) -> str:
    """Render a stable Markdown report without ranking or synthesizing claims."""

    lines: list[str] = [
        "# Useful Idea Report",
        "",
        f"- Run: `{data.run_id}`",
        f"- Challenge: {_clean(data.challenge_title)}",
        f"- Challenge source: {_link(data.challenge_ref)}",
        f"- Started: `{data.started_at}`",
        f"- Completed: `{data.completed_at or datetime.now(timezone.utc).isoformat()}`",
        "",
        "## Run Status",
        "",
    ]

    for stage, status in sorted(data.stage_statuses.items()):
        lines.append(f"- `{stage}`: `{status}`")

    lines.extend(["", "## Passed Ideas", ""])
    if not data.ideas:
        lines.extend(
            [
                "No Idea passed every required gate in this run.",
                "",
            ]
        )
    else:
        # Stable creation/path order is deliberate. It is not a quality ranking.
        for idea in sorted(data.ideas, key=lambda item: (item.idea_ref, item.artifact_id)):
            lines.extend(
                [
                    f"### {idea.artifact_id}",
                    "",
                    f"Source: {_link(idea.idea_ref)}",
                    "",
                    "#### Target User",
                    "",
                    _clean(idea.target_user),
                    "",
                    "#### Problem",
                    "",
                    _clean(idea.problem),
                    "",
                    "#### Felt Value",
                    "",
                    _clean(idea.felt_value),
                    "",
                    "#### User Flow",
                    "",
                    _clean(idea.user_flow),
                    "",
                    "#### Core Mechanism",
                    "",
                    _clean(idea.core_mechanism),
                    "",
                    "#### Minimum Features",
                    "",
                    _clean(idea.minimum_features),
                    "",
                    "#### Alternatives and Adoption",
                    "",
                    _clean(idea.alternatives_and_adoption),
                    "",
                    "#### Sponsor Technology",
                    "",
                    _clean(idea.sponsor_technology),
                    "",
                    "#### Deliverable Beta Scope",
                    "",
                    _clean(idea.beta_scope),
                    "",
                    "#### Highest-Risk Dependencies",
                    "",
                    _clean(idea.highest_risk_dependencies),
                    "",
                    f"Evidence: {_linked_refs(idea.evidence_refs)}",
                    "",
                    f"Reviews: {_linked_refs(idea.review_refs)}",
                    "",
                ]
            )

    lines.extend(["## Elimination Appendix", ""])
    if not data.eliminations:
        lines.extend(["No candidate was eliminated.", ""])
    else:
        for item in sorted(
            data.eliminations,
            key=lambda candidate: (candidate.stage, candidate.candidate_ref),
        ):
            lines.extend(
                [
                    f"### `{item.candidate_ref}`",
                    "",
                    f"- Stage: `{item.stage}`",
                    f"- Rule: `{item.rule}`",
                    f"- Reason: {_clean(item.reason)}",
                    f"- Decisions: {_linked_refs(item.decision_refs)}",
                    "",
                ]
            )

    if data.warnings:
        lines.extend(["## Run Warnings", ""])
        lines.extend(f"- {_clean(warning)}" for warning in data.warnings)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_report(path: Path, data: ReportInput) -> None:
    """Atomically write the rendered report."""

    atomic_write_bytes(path, render_report(data).encode("utf-8"))
