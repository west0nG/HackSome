"""Markdown artifact contracts and atomic publication.

Long-form stage output remains ordinary Markdown.  A small YAML front matter
block carries routing fields, while exact H2 sections make deterministic
validation and report extraction possible without duplicating the body into a
JSON sidecar.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
from collections.abc import Collection, Iterable, Mapping
from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from types import MappingProxyType
from typing import Any

import yaml

from hacksome.state import atomic_write_bytes, exclusive_path_lock, fsync_directory


ARTIFACT_SCHEMA_VERSION = 1
COMMON_FRONT_MATTER_FIELDS = (
    "schema_version",
    "artifact_id",
    "artifact_type",
    "run_id",
    "stage",
    "status",
    "revision",
    "created_by_session",
    "updated_by_session",
    "source_refs",
    "supersedes",
)

# These fields are assigned by the orchestrator for every artifact task.  They
# are deliberately narrower than COMMON_FRONT_MATTER_FIELDS: status is an
# agent decision, and immutable stages already constrain revision to one.
COMMON_MANIFEST_BINDING_FIELDS = (
    "schema_version",
    "artifact_type",
    "run_id",
    "stage",
    "created_by_session",
    "updated_by_session",
    "source_refs",
    "supersedes",
)

_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
_SAFE_FRAGMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_HEADING = re.compile(r"^ {0,3}(#{1,6})[ \t]+(.+?)[ \t]*$")
_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")


class ArtifactError(RuntimeError):
    """Base class for artifact parsing, validation and publication errors."""


class ArtifactFormatError(ArtifactError):
    """Markdown or YAML could not be parsed unambiguously."""


class ArtifactValidationError(ArtifactError):
    """An artifact parsed successfully but violated its stage contract."""

    def __init__(self, issues: str | Iterable[str]) -> None:
        normalized: tuple[str, ...]
        if isinstance(issues, str):
            normalized = (issues,)
        else:
            normalized = tuple(str(issue) for issue in issues)
        if not normalized:
            normalized = ("artifact validation failed",)
        self.issues = normalized
        super().__init__("; ".join(normalized))


class UnsafePathError(ArtifactError):
    """A run-relative path could escape or ambiguously address the run root."""


class ArtifactConflictError(ArtifactError):
    """Publication would silently overwrite different durable content."""


class _UniqueKeyLoader(yaml.SafeLoader):
    pass


def _construct_unique_mapping(
    loader: _UniqueKeyLoader,
    node: yaml.MappingNode,
    deep: bool = False,
) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in mapping
        except TypeError as exc:
            raise yaml.constructor.ConstructorError(
                "while constructing front matter",
                node.start_mark,
                "front matter keys must be scalar and hashable",
                key_node.start_mark,
            ) from exc
        if duplicate:
            raise yaml.constructor.ConstructorError(
                "while constructing front matter",
                node.start_mark,
                f"duplicate key {key!r}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


@dataclass(frozen=True, slots=True)
class MarkdownSection:
    title: str
    level: int
    body: str


@dataclass(frozen=True, slots=True)
class ArtifactDocument:
    metadata: Mapping[str, Any]
    body: str

    def __post_init__(self) -> None:
        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping")
        if not isinstance(self.body, str):
            raise TypeError("body must be a string")
        object.__setattr__(self, "metadata", dict(self.metadata))

    @property
    def artifact_id(self) -> str | None:
        value = self.metadata.get("artifact_id")
        return value if isinstance(value, str) else None

    @property
    def stage(self) -> str | None:
        value = self.metadata.get("stage")
        return value if isinstance(value, str) else None

    @property
    def status(self) -> str | None:
        value = self.metadata.get("status")
        return value if isinstance(value, str) else None

    @property
    def revision(self) -> int | None:
        value = self.metadata.get("revision")
        return value if isinstance(value, int) and not isinstance(value, bool) else None

    def sections(self, *, level: int | None = 2) -> Mapping[str, MarkdownSection]:
        return extract_sections(self.body, level=level)

    def section(self, title: str, *, level: int | None = 2) -> str:
        sections = self.sections(level=level)
        try:
            return sections[title].body
        except KeyError as exc:
            raise KeyError(f"Markdown section {title!r} does not exist") from exc


@dataclass(frozen=True, slots=True)
class ArtifactSpec:
    stage: str
    artifact_type: str
    statuses: frozenset[str]
    required_headings: tuple[str, ...]
    canonical_prefix: str
    required_metadata: tuple[str, ...] = ()
    typed_metadata: tuple[tuple[str, str], ...] = ()
    manifest_binding_fields: tuple[str, ...] = ()
    lineage_identity_fields: tuple[str, ...] = ()
    minimum_source_refs: int = 1
    living_document: bool = False
    minimum_revision: int = 1
    maximum_revision: int | None = 1


def _spec(
    stage: str,
    artifact_type: str,
    statuses: Iterable[str],
    headings: Iterable[str],
    prefix: str,
    metadata: Iterable[str],
    *,
    typed_metadata: Iterable[tuple[str, str]] = (),
    manifest_binding_fields: Iterable[str] = (),
    lineage_identity_fields: Iterable[str] = (),
    living: bool = False,
    minimum_revision: int = 1,
    maximum_revision: int | None = 1,
) -> ArtifactSpec:
    return ArtifactSpec(
        stage=stage,
        artifact_type=artifact_type,
        statuses=frozenset(statuses),
        required_headings=tuple(headings),
        canonical_prefix=prefix,
        required_metadata=tuple(metadata),
        typed_metadata=tuple(typed_metadata),
        manifest_binding_fields=tuple(manifest_binding_fields),
        lineage_identity_fields=tuple(lineage_identity_fields),
        living_document=living,
        minimum_revision=minimum_revision,
        maximum_revision=maximum_revision,
    )


_SPECS = {
    "S2": _spec(
        "S2",
        "research",
        ("complete",),
        (
            "Research Scope",
            "Evidence Candidates",
            "Query Log",
            "Counterevidence and Uncertainty",
            "Coverage Gaps",
        ),
        "research",
        ("audience_id", "researcher_id", "research_round"),
        manifest_binding_fields=(
            "artifact_id",
            "audience_id",
            "researcher_id",
            "research_round",
        ),
    ),
    "S3": _spec(
        "S3",
        "verification",
        ("complete",),
        ("Verification Scope", "Evidence Checks", "Conflicts and Uncertainty"),
        "verification",
        (
            "audience_id",
            "research_ref",
            "researcher_id",
            "verifier_id",
            "verification_round",
            "needs_second_verifier",
            "recheck_evidence_ids",
        ),
        typed_metadata=(
            ("needs_second_verifier", "bool"),
            ("recheck_evidence_ids", "string_list"),
        ),
        manifest_binding_fields=(
            "artifact_id",
            "audience_id",
            "research_ref",
            "researcher_id",
            "verifier_id",
            "verification_round",
        ),
    ),
    "S4": _spec(
        "S4",
        "problem",
        ("draft",),
        (
            "Audience and Scenario",
            "Problem",
            "Observed Consequences",
            "Current Workarounds",
            "Frequency or Severity Signals",
            "Evidence",
            "Counterevidence and Uncertainty",
            "Search Gaps",
        ),
        "problems",
        ("audience_id", "writer_id", "problem_id"),
        manifest_binding_fields=("audience_id", "writer_id", "revision"),
        lineage_identity_fields=("audience_id", "writer_id", "problem_id"),
        living=True,
        maximum_revision=None,
    ),
    "S5": _spec(
        "S5",
        "problem_gateway",
        ("pass", "needs_evidence", "reject_candidate"),
        ("Gateway Scope", "Threshold Checks", "Decision", "Evidence Gap"),
        "gateways",
        (
            "problem_ref",
            "gateway_id",
            "gateway_mode",
            "evidence_loop_count",
            "failed_thresholds",
            "evidence_gaps",
        ),
        typed_metadata=(
            ("failed_thresholds", "threshold_list"),
            ("evidence_gaps", "string_list"),
        ),
        manifest_binding_fields=(
            "artifact_id",
            "problem_ref",
            "gateway_id",
            "gateway_mode",
            "evidence_loop_count",
        ),
    ),
    "S6": _spec(
        "S6",
        "idea",
        ("draft",),
        (
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
        "ideas",
        ("idea_id", "problem_ref", "generator_id"),
        manifest_binding_fields=("problem_ref", "generator_id", "revision"),
        lineage_identity_fields=("idea_id", "problem_ref", "generator_id"),
        living=True,
    ),
    "S7": _spec(
        "S7",
        "competition",
        ("complete",),
        (
            "Research Scope",
            "Direct Competitors",
            "Indirect Alternatives and Workarounds",
            "Open Source Projects",
            "Adoption and Abandonment Evidence",
            "Overlap and Differences",
            "Sources and Query Log",
            "Counterevidence and Coverage Gaps",
        ),
        "competition",
        ("idea_ref", "researcher_id", "research_round"),
        manifest_binding_fields=(
            "artifact_id",
            "idea_ref",
            "researcher_id",
            "research_round",
        ),
    ),
    "S8": _spec(
        "S8",
        "idea",
        ("ready_for_review",),
        (
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
        "ideas",
        (
            "idea_id",
            "problem_ref",
            "generator_id",
            "revision_reason",
            "needs_competitor_research",
            "competitor_research_gaps",
        ),
        typed_metadata=(
            ("needs_competitor_research", "bool"),
            ("competitor_research_gaps", "string_list"),
        ),
        manifest_binding_fields=(
            "artifact_id",
            "idea_id",
            "problem_ref",
            "generator_id",
            "revision_reason",
            "revision",
        ),
        lineage_identity_fields=("idea_id", "problem_ref", "generator_id"),
        living=True,
        minimum_revision=2,
        maximum_revision=None,
    ),
    "S9": _spec(
        "S9",
        "idea_red_team",
        ("pass", "repairable", "invalid"),
        (
            "Review Scope",
            "Felt Value",
            "Real User Flow",
            "Value Delivery",
            "Adoption Reason",
            "Problem Fidelity",
            "Decision",
        ),
        "idea-reviews",
        ("idea_ref", "red_team_id", "review_mode"),
        manifest_binding_fields=(
            "artifact_id",
            "idea_ref",
            "red_team_id",
            "review_mode",
        ),
    ),
    "S10": _spec(
        "S10",
        "feasibility",
        ("feasible", "scope_reduction", "infeasible"),
        (
            "Review Scope",
            "Critical Path",
            "Deliverable Beta Scope",
            "Highest-Risk Dependencies",
            "Time and Integration",
            "Repeatable Demo",
            "Scope Integrity",
            "Decision",
        ),
        "feasibility",
        ("idea_ref", "review_id", "review_mode"),
        manifest_binding_fields=(
            "artifact_id",
            "idea_ref",
            "review_id",
            "review_mode",
        ),
    ),
}

STAGE_ARTIFACT_SPECS: Mapping[str, ArtifactSpec] = MappingProxyType(_SPECS)


def artifact_spec(stage: str, artifact_type: str | None = None) -> ArtifactSpec:
    try:
        spec = STAGE_ARTIFACT_SPECS[stage]
    except KeyError as exc:
        raise ArtifactValidationError(f"unsupported artifact stage {stage!r}") from exc
    if artifact_type is not None and artifact_type != spec.artifact_type:
        raise ArtifactValidationError(
            f"stage {stage} requires artifact_type {spec.artifact_type!r}, "
            f"not {artifact_type!r}"
        )
    return spec


def _json_compatible(value: Any, *, context: str) -> Any:
    try:
        encoded = json.dumps(value, ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ArtifactFormatError(f"{context} must contain only JSON-compatible values") from exc
    return json.loads(encoded)


def required_manifest_binding_fields(spec: ArtifactSpec) -> tuple[str, ...]:
    """Return the task-assigned fields required before publication."""

    return tuple(
        dict.fromkeys(
            (*COMMON_MANIFEST_BINDING_FIELDS, *spec.manifest_binding_fields)
        )
    )


def _validate_manifest_binding(
    spec: ArtifactSpec,
    expected_metadata: Mapping[str, Any] | None,
    *,
    revision: int | None = None,
) -> Mapping[str, Any]:
    """Reject publication without a complete controller-owned assignment."""

    if expected_metadata is None:
        raise ArtifactValidationError(
            "publication requires complete expected_metadata from the task manifest"
        )
    if not isinstance(expected_metadata, Mapping):
        raise TypeError("expected_metadata must be a mapping")
    if any(not isinstance(key, str) for key in expected_metadata):
        raise TypeError("expected_metadata keys must be strings")
    normalized = _json_compatible(
        expected_metadata,
        context="expected metadata",
    )
    if not isinstance(normalized, dict):  # Mapping input should always encode as an object.
        raise TypeError("expected_metadata must encode as a JSON object")
    required = list(required_manifest_binding_fields(spec))
    if spec.stage == "S4" and revision is not None and revision > 1:
        required.extend(("artifact_id", "problem_id"))
    if spec.stage == "S9" and normalized.get("review_mode") == "draft_screen":
        required.extend(("reviewed_idea_revision", "reviewed_idea_sha256"))
    missing = [key for key in dict.fromkeys(required) if key not in normalized]
    if missing:
        raise ArtifactValidationError(
            "expected_metadata is missing assigned task manifest fields: "
            + ", ".join(missing)
        )
    return normalized


def parse_markdown(text: str) -> ArtifactDocument:
    """Parse one Markdown document with a required YAML front matter block."""

    if not isinstance(text, str):
        raise TypeError("Markdown content must be a string")
    if text.startswith("\ufeff"):
        text = text[1:]
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise ArtifactFormatError("Markdown must start with a YAML '---' delimiter")

    closing_index: int | None = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            closing_index = index
            break
    if closing_index is None:
        raise ArtifactFormatError("YAML front matter has no closing '---' delimiter")

    yaml_text = "".join(lines[1:closing_index])
    try:
        metadata = yaml.load(yaml_text, Loader=_UniqueKeyLoader)
    except yaml.YAMLError as exc:
        raise ArtifactFormatError(f"invalid YAML front matter: {exc}") from exc
    if not isinstance(metadata, dict):
        raise ArtifactFormatError("YAML front matter must be a mapping")
    if any(not isinstance(key, str) for key in metadata):
        raise ArtifactFormatError("YAML front matter keys must be strings")
    _json_compatible(metadata, context="YAML front matter")
    body = "".join(lines[closing_index + 1 :])
    return ArtifactDocument(metadata=metadata, body=body)


def parse_markdown_file(path: str | Path) -> ArtifactDocument:
    source = Path(path)
    if source.is_symlink():
        raise UnsafePathError(f"artifact cannot be a symlink: {source}")
    try:
        return parse_markdown(source.read_text(encoding="utf-8"))
    except UnicodeDecodeError as exc:
        raise ArtifactFormatError(f"{source} is not valid UTF-8: {exc}") from exc


def serialize_markdown(
    document_or_metadata: ArtifactDocument | Mapping[str, Any],
    body: str | None = None,
) -> str:
    """Serialize an artifact with stable common-field ordering."""

    if isinstance(document_or_metadata, ArtifactDocument):
        if body is not None:
            raise TypeError("body must be omitted when serializing ArtifactDocument")
        metadata = dict(document_or_metadata.metadata)
        body_text = document_or_metadata.body
    else:
        if body is None:
            raise TypeError("body is required when serializing metadata")
        metadata = dict(document_or_metadata)
        body_text = body
    if not isinstance(body_text, str):
        raise TypeError("body must be a string")
    _json_compatible(metadata, context="YAML front matter")

    ordered: dict[str, Any] = {}
    for key in COMMON_FRONT_MATTER_FIELDS:
        if key in metadata:
            ordered[key] = metadata[key]
    for key, value in metadata.items():
        if key not in ordered:
            ordered[key] = value
    yaml_text = yaml.safe_dump(
        ordered,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
    return f"---\n{yaml_text}---\n{body_text}"


def _heading_positions(body: str) -> list[tuple[int, int, str, int]]:
    positions: list[tuple[int, int, str, int]] = []
    offset = 0
    fence_character: str | None = None
    fence_length = 0
    for line in body.splitlines(keepends=True):
        stripped_line = line.rstrip("\r\n")
        fence_match = _FENCE.match(stripped_line)
        if fence_match:
            marker = fence_match.group(1)
            if fence_character is None:
                fence_character = marker[0]
                fence_length = len(marker)
            elif marker[0] == fence_character and len(marker) >= fence_length:
                fence_character = None
                fence_length = 0
            offset += len(line)
            continue
        if fence_character is None:
            match = _HEADING.match(stripped_line)
            if match:
                title = re.sub(r"[ \t]+#+[ \t]*$", "", match.group(2)).strip()
                positions.append((offset, offset + len(line), title, len(match.group(1))))
        offset += len(line)
    return positions


def extract_sections(
    body: str,
    *,
    level: int | None = 2,
) -> Mapping[str, MarkdownSection]:
    """Return named Markdown sections, ignoring headings inside code fences."""

    if level is not None and not 1 <= level <= 6:
        raise ValueError("level must be between 1 and 6, or None")
    headings = _heading_positions(body)
    sections: dict[str, MarkdownSection] = {}
    for index, (_, content_start, title, heading_level) in enumerate(headings):
        if level is not None and heading_level != level:
            continue
        content_end = len(body)
        for next_start, _, _, next_level in headings[index + 1 :]:
            if next_level <= heading_level:
                content_end = next_start
                break
        if title in sections:
            raise ArtifactFormatError(f"duplicate Markdown heading {title!r}")
        sections[title] = MarkdownSection(
            title=title,
            level=heading_level,
            body=body[content_start:content_end].strip(),
        )
    return MappingProxyType(sections)


def safe_relative_path(value: str | os.PathLike[str], *, field_name: str = "path") -> PurePosixPath:
    """Normalize one canonical run-relative POSIX path or reject it."""

    raw = os.fspath(value)
    if not isinstance(raw, str) or not raw or raw != raw.strip():
        raise UnsafePathError(f"{field_name} must be a non-empty canonical string")
    if "\x00" in raw or "\\" in raw:
        raise UnsafePathError(f"{field_name} must use safe POSIX path syntax")
    windows = PureWindowsPath(raw)
    if windows.is_absolute() or windows.drive:
        raise UnsafePathError(f"{field_name} must be relative: {raw!r}")
    path = PurePosixPath(raw)
    if path.is_absolute():
        raise UnsafePathError(f"{field_name} must be relative: {raw!r}")
    raw_parts = raw.split("/")
    if any(part in {"", ".", ".."} for part in raw_parts):
        raise UnsafePathError(f"{field_name} is not canonical: {raw!r}")
    if path.parts[0].startswith("~"):
        raise UnsafePathError(f"{field_name} cannot use home expansion")
    return path


def safe_join(
    root: str | Path,
    relative: str | os.PathLike[str],
    *,
    must_exist: bool = False,
    file_only: bool = False,
) -> Path:
    """Join below *root*, rejecting traversal and every existing symlink."""

    root_path = Path(root).resolve(strict=False)
    relative_path = safe_relative_path(relative)
    candidate = root_path.joinpath(*relative_path.parts)
    cursor = root_path
    for part in relative_path.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise UnsafePathError(f"path traverses symlink: {cursor}")
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(root_path)
    except ValueError as exc:
        raise UnsafePathError(f"path escapes run root: {relative!r}") from exc
    if must_exist and not candidate.exists():
        raise FileNotFoundError(candidate)
    if file_only and candidate.exists() and not candidate.is_file():
        raise ArtifactValidationError(f"expected a file: {candidate}")
    return candidate


def split_source_ref(reference: str) -> tuple[PurePosixPath, str | None]:
    if not isinstance(reference, str) or not reference:
        raise UnsafePathError("source reference must be a non-empty string")
    if reference.count("#") > 1:
        raise UnsafePathError(f"source reference has multiple fragments: {reference!r}")
    path_text, separator, fragment = reference.partition("#")
    path = safe_relative_path(path_text, field_name="source reference")
    if separator and not _SAFE_FRAGMENT.fullmatch(fragment):
        raise UnsafePathError(f"unsafe source-reference fragment: {fragment!r}")
    return path, fragment if separator else None


def _canonical_ref(reference: str) -> str:
    path, fragment = split_source_ref(reference)
    return path.as_posix() + (f"#{fragment}" if fragment else "")


def validate_source_refs(
    source_refs: Any,
    *,
    run_root: str | Path | None = None,
    current_path: str | os.PathLike[str] | None = None,
    allowed_refs: Collection[str] | None = None,
) -> tuple[str, ...]:
    """Validate safe, existing and optionally allow-listed upstream refs."""

    if not isinstance(source_refs, list):
        raise ArtifactValidationError("source_refs must be a YAML list")
    normalized: list[str] = []
    allowed_full: set[str] | None = None
    allowed_paths: set[str] | None = None
    if allowed_refs is not None:
        allowed_full = {_canonical_ref(ref) for ref in allowed_refs}
        allowed_paths = {split_source_ref(ref)[0].as_posix() for ref in allowed_refs}

    current = (
        safe_relative_path(current_path, field_name="current artifact path").as_posix()
        if current_path is not None
        else None
    )
    for reference in source_refs:
        if not isinstance(reference, str):
            raise ArtifactValidationError("every source_ref must be a string")
        canonical = _canonical_ref(reference)
        path, _ = split_source_ref(canonical)
        path_text = path.as_posix()
        if canonical in normalized:
            raise ArtifactValidationError(f"duplicate source_ref: {canonical}")
        if current is not None and path_text == current:
            raise ArtifactValidationError("an artifact cannot include itself in source_refs")
        if allowed_full is not None and allowed_paths is not None:
            if canonical not in allowed_full and path_text not in allowed_paths:
                raise ArtifactValidationError(
                    f"source_ref was not in the task context allowlist: {canonical}"
                )
        if run_root is not None:
            target = safe_join(run_root, path, must_exist=True, file_only=True)
            if not target.is_file():
                raise ArtifactValidationError(f"source_ref is not a file: {canonical}")
        normalized.append(canonical)
    return tuple(normalized)


def _non_empty_string(metadata: Mapping[str, Any], key: str, issues: list[str]) -> None:
    value = metadata.get(key)
    if not isinstance(value, str) or not value.strip():
        issues.append(f"{key} must be a non-empty string")


def _validate_routing_field(key: str, value: Any, issues: list[str]) -> None:
    if key.endswith("_round") or key.endswith("_count"):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            issues.append(f"{key} must be a non-negative integer")
        return
    if not isinstance(value, str) or not value.strip():
        issues.append(f"{key} must be a non-empty string")


def _validate_typed_metadata(
    key: str,
    value: Any,
    kind: str,
    issues: list[str],
) -> None:
    if kind == "bool":
        if not isinstance(value, bool):
            issues.append(f"{key} must be a boolean")
        return
    if kind in {"string_list", "threshold_list"}:
        if not isinstance(value, list):
            issues.append(f"{key} must be a list of strings")
            return
        if any(not isinstance(item, str) or not item.strip() for item in value):
            issues.append(f"{key} must contain only non-empty strings")
            return
        if len(set(value)) != len(value):
            issues.append(f"{key} must not contain duplicates")
        if kind == "threshold_list":
            invalid = sorted(set(value) - {"T1", "T2", "T3", "T4", "T5"})
            if invalid:
                issues.append(
                    f"{key} may contain only T1 through T5, not {', '.join(invalid)}"
                )
        return
    raise RuntimeError(f"unknown ArtifactSpec metadata type {kind!r}")


def _validate_routing_consistency(
    spec: ArtifactSpec,
    metadata: Mapping[str, Any],
    issues: list[str],
) -> None:
    if spec.stage == "S3":
        audience_id = metadata.get("audience_id")
        researcher_id = metadata.get("researcher_id")
        research_ref = metadata.get("research_ref")
        if all(isinstance(value, str) for value in (audience_id, researcher_id)):
            assigned_research_ref = (
                f"research/{audience_id}/{researcher_id}.md"
            )
            if research_ref != assigned_research_ref:
                issues.append(
                    "research_ref must match audience_id and researcher_id; "
                    f"expected {assigned_research_ref!r}"
                )
        needs_second = metadata.get("needs_second_verifier")
        evidence_ids = metadata.get("recheck_evidence_ids")
        if isinstance(needs_second, bool) and isinstance(evidence_ids, list):
            if needs_second and not evidence_ids:
                issues.append(
                    "recheck_evidence_ids must be non-empty when "
                    "needs_second_verifier is true"
                )
            if not needs_second and evidence_ids:
                issues.append(
                    "recheck_evidence_ids must be empty when "
                    "needs_second_verifier is false"
                )
    elif spec.stage == "S5":
        status = metadata.get("status")
        failed = metadata.get("failed_thresholds")
        gaps = metadata.get("evidence_gaps")
        if isinstance(failed, list) and isinstance(gaps, list):
            if status == "pass" and (failed or gaps):
                issues.append("pass requires empty failed_thresholds and evidence_gaps")
            elif status == "needs_evidence":
                if failed:
                    issues.append("needs_evidence requires empty failed_thresholds")
                if not gaps:
                    issues.append("needs_evidence requires at least one evidence gap")
            elif status == "reject_candidate" and not failed:
                issues.append("reject_candidate requires at least one failed threshold")
    elif spec.stage == "S8":
        needs_research = metadata.get("needs_competitor_research")
        gaps = metadata.get("competitor_research_gaps")
        if isinstance(needs_research, bool) and isinstance(gaps, list):
            if needs_research and not gaps:
                issues.append(
                    "competitor_research_gaps must be non-empty when "
                    "needs_competitor_research is true"
                )
            if not needs_research and gaps:
                issues.append(
                    "competitor_research_gaps must be empty when "
                    "needs_competitor_research is false"
                )
    elif spec.stage == "S9":
        review_mode = metadata.get("review_mode")
        reviewed_revision = metadata.get("reviewed_idea_revision")
        reviewed_sha256 = metadata.get("reviewed_idea_sha256")
        if review_mode == "draft_screen":
            if (
                isinstance(reviewed_revision, bool)
                or not isinstance(reviewed_revision, int)
                or reviewed_revision < 1
            ):
                issues.append(
                    "draft_screen reviewed_idea_revision must be a positive integer"
                )
            if not isinstance(reviewed_sha256, str) or not _SHA256.fullmatch(
                reviewed_sha256
            ):
                issues.append(
                    "draft_screen reviewed_idea_sha256 must be a lowercase SHA-256"
                )
        elif (
            "reviewed_idea_revision" in metadata
            or "reviewed_idea_sha256" in metadata
        ):
            issues.append(
                "reviewed Idea revision/hash fields are allowed only for draft_screen"
            )


def _path_component(metadata: Mapping[str, Any], key: str) -> str:
    value = metadata.get(key)
    if not isinstance(value, str) or not _SAFE_ID.fullmatch(value) or ":" in value:
        raise ArtifactValidationError(f"{key} is not a safe path identifier")
    return value


def _reference_lineage(
    metadata: Mapping[str, Any],
    key: str,
    expected_prefix: str,
    expected_part_count: int,
) -> tuple[str, ...]:
    value = metadata.get(key)
    if not isinstance(value, str):
        raise ArtifactValidationError(f"{key} must be a run-relative path")
    path, fragment = split_source_ref(value)
    if fragment is not None or path.suffix.lower() != ".md":
        raise ArtifactValidationError(f"{key} must reference one Markdown artifact")
    if path.parts[0] != expected_prefix:
        raise ArtifactValidationError(f"{key} must be under {expected_prefix}/")
    if len(path.parts) != expected_part_count:
        raise ArtifactValidationError(
            f"{key} does not match the canonical {expected_prefix} path shape"
        )
    lineage = (*path.parts[1:-1], path.stem)
    if any(
        not _SAFE_ID.fullmatch(component) or ":" in component
        for component in lineage
    ):
        raise ArtifactValidationError(f"{key} contains an unsafe path identifier")
    return lineage


def expected_canonical_path(
    document_or_metadata: ArtifactDocument | Mapping[str, Any],
) -> str:
    """Derive the only canonical path allowed by stage routing metadata."""

    metadata = (
        document_or_metadata.metadata
        if isinstance(document_or_metadata, ArtifactDocument)
        else document_or_metadata
    )
    stage = metadata.get("stage")
    parts: tuple[str, ...]
    if stage == "S2":
        parts = (
            "research",
            _path_component(metadata, "audience_id"),
            f"{_path_component(metadata, 'researcher_id')}.md",
        )
    elif stage == "S3":
        parts = (
            "verification",
            _path_component(metadata, "audience_id"),
            _path_component(metadata, "researcher_id"),
            f"{_path_component(metadata, 'verifier_id')}.md",
        )
    elif stage == "S4":
        parts = (
            "problems",
            _path_component(metadata, "audience_id"),
            _path_component(metadata, "writer_id"),
            f"{_path_component(metadata, 'problem_id')}.md",
        )
    elif stage == "S5":
        parts = (
            "gateways",
            *_reference_lineage(metadata, "problem_ref", "problems", 4),
            f"{_path_component(metadata, 'gateway_id')}.md",
        )
    elif stage in {"S6", "S8"}:
        parts = (
            "ideas",
            *_reference_lineage(metadata, "problem_ref", "problems", 4),
            _path_component(metadata, "generator_id"),
            f"{_path_component(metadata, 'idea_id')}.md",
        )
    elif stage == "S7":
        parts = (
            "competition",
            *_reference_lineage(metadata, "idea_ref", "ideas", 6),
            f"{_path_component(metadata, 'researcher_id')}.md",
        )
    elif stage == "S9":
        parts = (
            "idea-reviews",
            *_reference_lineage(metadata, "idea_ref", "ideas", 6),
            f"{_path_component(metadata, 'red_team_id')}.md",
        )
    elif stage == "S10":
        parts = (
            "feasibility",
            *_reference_lineage(metadata, "idea_ref", "ideas", 6),
            f"{_path_component(metadata, 'review_id')}.md",
        )
    else:
        raise ArtifactValidationError(f"unsupported artifact stage {stage!r}")
    return PurePosixPath(*parts).as_posix()


def validate_document(
    document: ArtifactDocument,
    *,
    spec: ArtifactSpec | None = None,
    run_root: str | Path | None = None,
    relative_path: str | os.PathLike[str] | None = None,
    expected_run_id: str | None = None,
    expected_metadata: Mapping[str, Any] | None = None,
    allowed_source_refs: Collection[str] | None = None,
) -> ArtifactDocument:
    """Apply common, stage-specific, path and source-reference validation."""

    metadata = document.metadata
    issues: list[str] = []
    missing = [key for key in COMMON_FRONT_MATTER_FIELDS if key not in metadata]
    if missing:
        issues.append(f"missing front matter fields: {', '.join(missing)}")

    schema_version = metadata.get("schema_version")
    if (
        isinstance(schema_version, bool)
        or not isinstance(schema_version, int)
        or schema_version != ARTIFACT_SCHEMA_VERSION
    ):
        issues.append(f"schema_version must be {ARTIFACT_SCHEMA_VERSION}")
    for key in (
        "artifact_id",
        "artifact_type",
        "run_id",
        "stage",
        "status",
        "created_by_session",
        "updated_by_session",
    ):
        _non_empty_string(metadata, key, issues)
    for key in (
        "artifact_id",
        "run_id",
        "created_by_session",
        "updated_by_session",
    ):
        value = metadata.get(key)
        if isinstance(value, str) and value.strip() and not _SAFE_ID.fullmatch(value):
            issues.append(f"{key} contains unsafe characters")
    for key in ("created_by_session", "updated_by_session"):
        if metadata.get(key) == "pending":
            issues.append(f"{key} must be stamped with the real Codex session id")

    revision = metadata.get("revision")
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
        issues.append("revision must be a positive integer")
        revision = None
    supersedes = metadata.get("supersedes")
    if supersedes is not None:
        if not isinstance(supersedes, str):
            issues.append("supersedes must be null or a run-relative path")
        else:
            try:
                safe_relative_path(supersedes, field_name="supersedes")
            except UnsafePathError as exc:
                issues.append(str(exc))
    if revision == 1 and supersedes is not None:
        issues.append("revision 1 must set supersedes to null")
    if revision is not None and revision > 1 and supersedes is None:
        issues.append("revision greater than 1 requires supersedes")

    stage = metadata.get("stage")
    artifact_type = metadata.get("artifact_type")
    if spec is None and isinstance(stage, str):
        try:
            spec = artifact_spec(
                stage,
                artifact_type if isinstance(artifact_type, str) else None,
            )
        except ArtifactValidationError as exc:
            issues.extend(exc.issues)
    elif spec is not None:
        if stage != spec.stage:
            issues.append(f"stage must be {spec.stage!r}")
        if artifact_type != spec.artifact_type:
            issues.append(f"artifact_type must be {spec.artifact_type!r}")

    if expected_run_id is not None and metadata.get("run_id") != expected_run_id:
        issues.append(f"run_id must be {expected_run_id!r}")
    if expected_metadata is not None:
        if not isinstance(expected_metadata, Mapping):
            raise TypeError("expected_metadata must be a mapping")
        if any(not isinstance(key, str) for key in expected_metadata):
            raise TypeError("expected_metadata keys must be strings")
        normalized_expected = _json_compatible(
            expected_metadata,
            context="expected metadata",
        )
        for key, expected_value in normalized_expected.items():
            if key not in metadata:
                issues.append(f"expected front matter field is missing: {key}")
            elif metadata[key] != expected_value:
                issues.append(
                    f"front matter {key} does not match the assigned task manifest"
                )

    if spec is not None:
        status = metadata.get("status")
        if status not in spec.statuses:
            issues.append(
                f"status for {spec.stage} must be one of "
                f"{', '.join(sorted(spec.statuses))}"
            )
        typed_metadata = dict(spec.typed_metadata)
        for key in spec.required_metadata:
            if key not in metadata:
                issues.append(f"missing stage metadata field: {key}")
            elif key in typed_metadata:
                _validate_typed_metadata(key, metadata[key], typed_metadata[key], issues)
            else:
                _validate_routing_field(key, metadata[key], issues)
        _validate_routing_consistency(spec, metadata, issues)
        if revision is not None:
            if revision < spec.minimum_revision:
                issues.append(
                    f"{spec.stage} revision must be at least {spec.minimum_revision}"
                )
            if spec.maximum_revision is not None and revision > spec.maximum_revision:
                issues.append(
                    f"{spec.stage} revision must not exceed {spec.maximum_revision}"
                )
        try:
            sections = extract_sections(document.body, level=2)
        except ArtifactFormatError as exc:
            issues.append(str(exc))
            sections = {}
        for heading in spec.required_headings:
            section = sections.get(heading)
            if section is None:
                issues.append(f"missing required H2 heading: {heading}")
            elif not section.body.strip():
                issues.append(f"required H2 section is empty: {heading}")

    normalized_path: PurePosixPath | None = None
    if relative_path is not None:
        try:
            normalized_path = safe_relative_path(
                relative_path,
                field_name="canonical artifact path",
            )
        except UnsafePathError as exc:
            issues.append(str(exc))
        if normalized_path is not None:
            if normalized_path.suffix.lower() != ".md":
                issues.append("long artifact path must end in .md")
            if spec is not None and normalized_path.parts[0] != spec.canonical_prefix:
                issues.append(
                    f"{spec.stage} artifact must be under {spec.canonical_prefix}/"
                )
            if spec is not None:
                try:
                    expected_path = expected_canonical_path(document)
                except ArtifactValidationError as exc:
                    issues.extend(exc.issues)
                else:
                    if normalized_path.as_posix() != expected_path:
                        issues.append(
                            "canonical artifact path does not match routing metadata; "
                            f"expected {expected_path!r}"
                        )

    normalized_source_refs: tuple[str, ...] = ()
    try:
        normalized_source_refs = validate_source_refs(
            metadata.get("source_refs"),
            run_root=run_root,
            current_path=normalized_path,
            allowed_refs=allowed_source_refs,
        )
    except (ArtifactError, FileNotFoundError) as exc:
        issues.append(str(exc))
    if spec is not None and len(normalized_source_refs) < spec.minimum_source_refs:
        issues.append(
            f"{spec.stage} requires at least {spec.minimum_source_refs} source_ref"
        )

    if issues:
        raise ArtifactValidationError(issues)
    return document


def validate_artifact(
    path: str | Path,
    *,
    run_root: str | Path | None = None,
    relative_path: str | os.PathLike[str] | None = None,
    spec: ArtifactSpec | None = None,
    expected_run_id: str | None = None,
    expected_metadata: Mapping[str, Any] | None = None,
    allowed_source_refs: Collection[str] | None = None,
) -> ArtifactDocument:
    document = parse_markdown_file(path)
    return validate_document(
        document,
        spec=spec,
        run_root=run_root,
        relative_path=relative_path,
        expected_run_id=expected_run_id,
        expected_metadata=expected_metadata,
        allowed_source_refs=allowed_source_refs,
    )


@dataclass(frozen=True, slots=True)
class PromotionRequest:
    staged_path: str | Path
    canonical_path: str
    expected_metadata: Mapping[str, Any]
    allowed_source_refs: Collection[str] | None = None
    replace_living: bool = False


@dataclass(frozen=True, slots=True)
class PublishedArtifact:
    path: Path
    relative_path: str
    document: ArtifactDocument
    snapshot_path: Path | None = None
    already_present: bool = False


@dataclass(frozen=True, slots=True)
class _PreparedPromotion:
    request: PromotionRequest
    staged_path: Path
    target_path: Path
    relative_path: str
    content: bytes
    document: ArtifactDocument
    spec: ArtifactSpec
    snapshot_path: Path | None
    snapshot_content: bytes | None
    already_present: bool


class ArtifactStore:
    """Validate staged output and publish it below one local run directory."""

    def __init__(
        self,
        run_root: str | Path,
        *,
        run_id: str | None = None,
        staging_directory: str = ".staging",
        revisions_directory: str = "revisions",
    ) -> None:
        self.run_root = Path(run_root).resolve(strict=False)
        self.run_id = run_id
        self.staging_directory = safe_relative_path(
            staging_directory,
            field_name="staging directory",
        ).as_posix()
        self.revisions_directory = safe_relative_path(
            revisions_directory,
            field_name="revisions directory",
        ).as_posix()
        self.locks_directory = ".artifact-locks"
        self.staging_root = safe_join(self.run_root, self.staging_directory)

    def task_staging_dir(self, task_id: str, *, create: bool = True) -> Path:
        if not isinstance(task_id, str) or not _SAFE_ID.fullmatch(task_id):
            raise UnsafePathError("task_id is not safe for a staging directory")
        path = safe_join(self.staging_root, task_id)
        if create:
            path.mkdir(parents=True, exist_ok=True)
        return path

    def staged_path(self, task_id: str, relative_path: str) -> Path:
        task_root = self.task_staging_dir(task_id)
        return safe_join(task_root, relative_path)

    def canonical_path(self, relative_path: str, *, must_exist: bool = False) -> Path:
        normalized = safe_relative_path(relative_path, field_name="canonical path")
        staging_parts = safe_relative_path(self.staging_directory).parts
        revision_parts = safe_relative_path(self.revisions_directory).parts
        lock_parts = safe_relative_path(self.locks_directory).parts
        if (
            normalized.parts[: len(staging_parts)] == staging_parts
            or normalized.parts[: len(revision_parts)] == revision_parts
            or normalized.parts[: len(lock_parts)] == lock_parts
        ):
            raise UnsafePathError("canonical artifacts cannot target reserved directories")
        return safe_join(self.run_root, normalized, must_exist=must_exist)

    def _checked_staged_path(self, path: str | Path) -> Path:
        candidate = Path(path)
        if not candidate.is_absolute():
            relative = safe_relative_path(candidate.as_posix(), field_name="staged path")
        else:
            try:
                lexical_relative = candidate.relative_to(self.staging_root)
            except ValueError as exc:
                raise UnsafePathError(
                    f"staged artifact is outside {self.staging_root}: {candidate}"
                ) from exc
            relative = safe_relative_path(
                PurePosixPath(*lexical_relative.parts).as_posix(),
                field_name="staged path",
            )
        checked = safe_join(
            self.staging_root,
            relative,
            must_exist=True,
            file_only=True,
        )
        if not checked.is_file():
            raise ArtifactValidationError(f"staged artifact is not a file: {checked}")
        return checked

    def stamp_session(self, staged_path: str | Path, session_id: str) -> ArtifactDocument:
        """Replace ``pending`` session placeholders in a staged document."""

        if not isinstance(session_id, str) or not _SAFE_ID.fullmatch(session_id):
            raise ValueError("session_id must be a safe non-empty identifier")
        source = self._checked_staged_path(staged_path)
        document = parse_markdown_file(source)
        metadata = dict(document.metadata)
        changed = False
        for key in ("created_by_session", "updated_by_session"):
            if metadata.get(key) == "pending":
                metadata[key] = session_id
                changed = True
        stamped = ArtifactDocument(metadata=metadata, body=document.body)
        if changed:
            atomic_write_bytes(source, serialize_markdown(stamped).encode("utf-8"))
        return stamped

    def snapshot_relative_path(self, canonical_path: str, revision: int) -> str:
        canonical = safe_relative_path(canonical_path, field_name="canonical path")
        if canonical.suffix.lower() != ".md":
            raise UnsafePathError("Living Document path must end in .md")
        if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
            raise ValueError("revision must be a positive integer")
        without_suffix = canonical.with_suffix("")
        return (
            PurePosixPath(self.revisions_directory)
            / without_suffix
            / f"revision-{revision:04d}.md"
        ).as_posix()

    @staticmethod
    def _lineage_identity_fields(document: ArtifactDocument) -> tuple[str, ...]:
        stage = document.metadata.get("stage")
        artifact_type = document.metadata.get("artifact_type")
        if not isinstance(stage, str):
            raise ArtifactValidationError("Living Document has no valid stage")
        spec = artifact_spec(
            stage,
            artifact_type if isinstance(artifact_type, str) else None,
        )
        return tuple(
            dict.fromkeys(
                (
                    "artifact_id",
                    "artifact_type",
                    "run_id",
                    "created_by_session",
                    *spec.lineage_identity_fields,
                )
            )
        )

    def _validate_lineage(
        self,
        document: ArtifactDocument,
        canonical_path: str,
    ) -> None:
        """Verify every declared predecessor snapshot back to revision one."""

        current = document
        current_revision = current.revision
        if current_revision is None:
            raise ArtifactValidationError("revision must be a positive integer")
        identity_fields = self._lineage_identity_fields(current)
        expected_identity = {
            key: current.metadata.get(key)
            for key in identity_fields
        }

        while current_revision > 1:
            expected_ref = self.snapshot_relative_path(
                canonical_path,
                current_revision - 1,
            )
            if current.metadata.get("supersedes") != expected_ref:
                raise ArtifactValidationError(
                    f"revision {current_revision} must supersede {expected_ref!r}"
                )
            try:
                snapshot_path = safe_join(
                    self.run_root,
                    expected_ref,
                    must_exist=True,
                    file_only=True,
                )
            except FileNotFoundError as exc:
                raise ArtifactValidationError(
                    f"revision snapshot is missing: {expected_ref}"
                ) from exc
            snapshot = parse_markdown_file(snapshot_path)
            snapshot_stage = snapshot.metadata.get("stage")
            snapshot_type = snapshot.metadata.get("artifact_type")
            if not isinstance(snapshot_stage, str):
                raise ArtifactValidationError(
                    f"revision snapshot has no valid stage: {expected_ref}"
                )
            snapshot_spec = artifact_spec(
                snapshot_stage,
                snapshot_type if isinstance(snapshot_type, str) else None,
            )
            validate_document(
                snapshot,
                spec=snapshot_spec,
                run_root=self.run_root,
                expected_run_id=self.run_id,
            )
            if expected_canonical_path(snapshot) != canonical_path:
                raise ArtifactValidationError(
                    f"snapshot {expected_ref} changed its canonical routing path"
                )
            if snapshot.revision != current_revision - 1:
                raise ArtifactValidationError(
                    f"snapshot {expected_ref} must contain revision "
                    f"{current_revision - 1}"
                )
            for key, expected_value in expected_identity.items():
                if snapshot.metadata.get(key) != expected_value:
                    raise ArtifactValidationError(
                        f"snapshot {expected_ref} changed {key}"
                    )
            current = snapshot
            current_revision -= 1

    def _prepare(self, request: PromotionRequest) -> _PreparedPromotion:
        staged = self._checked_staged_path(request.staged_path)
        relative = safe_relative_path(
            request.canonical_path,
            field_name="canonical artifact path",
        ).as_posix()
        target = self.canonical_path(relative)
        content = staged.read_bytes()
        try:
            document = parse_markdown(content.decode("utf-8"))
        except UnicodeDecodeError as exc:
            raise ArtifactFormatError(f"{staged} is not valid UTF-8: {exc}") from exc
        stage = document.metadata.get("stage")
        artifact_type = document.metadata.get("artifact_type")
        if not isinstance(stage, str):
            raise ArtifactValidationError("stage must be a non-empty string")
        spec = artifact_spec(
            stage,
            artifact_type if isinstance(artifact_type, str) else None,
        )
        expected_metadata = _validate_manifest_binding(
            spec,
            request.expected_metadata,
            revision=document.revision,
        )
        validate_document(
            document,
            spec=spec,
            run_root=self.run_root,
            relative_path=relative,
            expected_run_id=self.run_id,
            expected_metadata=expected_metadata,
            allowed_source_refs=request.allowed_source_refs,
        )

        snapshot_path: Path | None = None
        snapshot_content: bytes | None = None
        if target.exists():
            if target.is_symlink() or not target.is_file():
                raise ArtifactConflictError(f"canonical target is not a regular file: {target}")
            existing_content = target.read_bytes()
            if existing_content == content:
                self._validate_lineage(document, relative)
                return _PreparedPromotion(
                    request=request,
                    staged_path=staged,
                    target_path=target,
                    relative_path=relative,
                    content=content,
                    document=document,
                    spec=spec,
                    snapshot_path=None,
                    snapshot_content=None,
                    already_present=True,
                )
            if not request.replace_living:
                raise ArtifactConflictError(
                    f"canonical artifact already exists with different content: {relative}"
                )
            if not spec.living_document:
                raise ArtifactConflictError(
                    f"{stage} artifacts are immutable and cannot be replaced"
                )
            try:
                existing = parse_markdown(existing_content.decode("utf-8"))
            except UnicodeDecodeError as exc:
                raise ArtifactFormatError(
                    f"canonical artifact is not valid UTF-8: {target}"
                ) from exc
            existing_stage = existing.metadata.get("stage")
            existing_type = existing.metadata.get("artifact_type")
            if not isinstance(existing_stage, str):
                raise ArtifactValidationError("existing artifact has no valid stage")
            existing_spec = artifact_spec(
                existing_stage,
                existing_type if isinstance(existing_type, str) else None,
            )
            validate_document(
                existing,
                spec=existing_spec,
                run_root=self.run_root,
                relative_path=relative,
                expected_run_id=self.run_id,
            )
            self._validate_lineage(existing, relative)
            if not existing_spec.living_document:
                raise ArtifactConflictError("existing artifact is not a Living Document")
            identity_fields = tuple(
                dict.fromkeys(
                    (
                        *self._lineage_identity_fields(existing),
                        *self._lineage_identity_fields(document),
                    )
                )
            )
            for key in identity_fields:
                if document.metadata.get(key) != existing.metadata.get(key):
                    raise ArtifactConflictError(
                        f"Living Document revision cannot change {key}"
                    )
            old_revision = existing.revision
            new_revision = document.revision
            if old_revision is None or new_revision != old_revision + 1:
                raise ArtifactConflictError(
                    f"Living Document revision must advance from {old_revision!r} "
                    f"to {(old_revision + 1) if old_revision is not None else 'unknown'}"
                )
            snapshot_relative = self.snapshot_relative_path(relative, old_revision)
            if document.metadata.get("supersedes") != snapshot_relative:
                raise ArtifactConflictError(
                    f"supersedes must be the previous snapshot path {snapshot_relative!r}"
                )
            snapshot_path = safe_join(self.run_root, snapshot_relative)
            if snapshot_path.exists():
                if snapshot_path.is_symlink() or snapshot_path.read_bytes() != existing_content:
                    raise ArtifactConflictError(
                        f"immutable revision snapshot conflicts at {snapshot_relative}"
                    )
            else:
                snapshot_content = existing_content
        elif request.replace_living:
            raise ArtifactConflictError(
                f"cannot replace missing Living Document: {relative}"
            )
        elif document.revision != 1:
            raise ArtifactConflictError(
                f"cannot publish revision {document.revision} without an existing "
                "Living Document"
            )

        return _PreparedPromotion(
            request=request,
            staged_path=staged,
            target_path=target,
            relative_path=relative,
            content=content,
            document=document,
            spec=spec,
            snapshot_path=snapshot_path,
            snapshot_content=snapshot_content,
            already_present=False,
        )

    def _target_for_request(self, request: PromotionRequest) -> tuple[str, Path]:
        relative = safe_relative_path(
            request.canonical_path,
            field_name="canonical artifact path",
        ).as_posix()
        return relative, self.canonical_path(relative)

    def _publication_lock_path(self, relative_path: str) -> Path:
        digest = hashlib.sha256(relative_path.encode("utf-8")).hexdigest()
        return safe_join(
            self.run_root,
            f"{self.locks_directory}/{digest}.lock",
        )

    def _publish(self, prepared: _PreparedPromotion) -> PublishedArtifact:
        if prepared.already_present:
            return PublishedArtifact(
                path=prepared.target_path,
                relative_path=prepared.relative_path,
                document=prepared.document,
                already_present=True,
            )
        if prepared.snapshot_path is not None and prepared.snapshot_content is not None:
            atomic_write_bytes(prepared.snapshot_path, prepared.snapshot_content)
        atomic_write_bytes(prepared.target_path, prepared.content)
        return PublishedArtifact(
            path=prepared.target_path,
            relative_path=prepared.relative_path,
            document=prepared.document,
            snapshot_path=prepared.snapshot_path,
        )

    def promote(
        self,
        staged_path: str | Path,
        canonical_path: str,
        *,
        expected_metadata: Mapping[str, Any],
        allowed_source_refs: Collection[str] | None = None,
    ) -> PublishedArtifact:
        request = PromotionRequest(
            staged_path=staged_path,
            canonical_path=canonical_path,
            expected_metadata=expected_metadata,
            allowed_source_refs=allowed_source_refs,
        )
        relative, _ = self._target_for_request(request)
        with exclusive_path_lock(self._publication_lock_path(relative)):
            return self._publish(self._prepare(request))

    def replace_living_document(
        self,
        staged_path: str | Path,
        canonical_path: str,
        *,
        expected_metadata: Mapping[str, Any],
        allowed_source_refs: Collection[str] | None = None,
    ) -> PublishedArtifact:
        request = PromotionRequest(
            staged_path=staged_path,
            canonical_path=canonical_path,
            expected_metadata=expected_metadata,
            allowed_source_refs=allowed_source_refs,
            replace_living=True,
        )
        relative, _ = self._target_for_request(request)
        with exclusive_path_lock(self._publication_lock_path(relative)):
            return self._publish(self._prepare(request))

    def _publish_atomic_directory_batch(
        self,
        prepared: list[_PreparedPromotion],
    ) -> tuple[PublishedArtifact, ...] | None:
        """Publish a fresh same-directory fan-out with one atomic rename."""

        if not prepared or any(
            item.already_present
            or item.request.replace_living
            or item.snapshot_path is not None
            for item in prepared
        ):
            return None
        parents = {item.target_path.parent for item in prepared}
        if len(parents) != 1:
            return None
        destination = parents.pop()
        if destination.exists():
            return None

        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = Path(
            tempfile.mkdtemp(
                prefix=f".{destination.name}.promotion-",
                dir=destination.parent,
            )
        )
        try:
            for item in prepared:
                atomic_write_bytes(temporary / item.target_path.name, item.content)
            fsync_directory(temporary)
            os.rename(temporary, destination)
            fsync_directory(destination.parent)
        except BaseException:
            if temporary.exists():
                shutil.rmtree(temporary)
            raise
        return tuple(
            PublishedArtifact(
                path=item.target_path,
                relative_path=item.relative_path,
                document=item.document,
            )
            for item in prepared
        )

    def promote_many(
        self,
        requests: Iterable[PromotionRequest],
    ) -> tuple[PublishedArtifact, ...]:
        """Validate a locked batch, then atomically publish each member.

        A fresh S4/S6-style batch whose files share one new directory becomes
        visible through one directory rename.  Other batches retain atomic
        per-file replacement and idempotent retry behavior.
        """

        request_list = list(requests)
        targets: dict[str, Path] = {}
        for request in request_list:
            relative, target = self._target_for_request(request)
            if relative in targets:
                raise ArtifactConflictError(
                    f"batch contains duplicate destination {relative!r}"
                )
            targets[relative] = target

        with ExitStack() as locks:
            for relative, _ in sorted(
                targets.items(),
                key=lambda item: str(item[1]),
            ):
                locks.enter_context(
                    exclusive_path_lock(self._publication_lock_path(relative))
                )
            prepared = [self._prepare(request) for request in request_list]
            atomic_batch = self._publish_atomic_directory_batch(prepared)
            if atomic_batch is not None:
                return atomic_batch
            return tuple(self._publish(item) for item in prepared)

    def validate_canonical(
        self,
        canonical_path: str,
        *,
        allowed_source_refs: Collection[str] | None = None,
        expected_metadata: Mapping[str, Any] | None = None,
    ) -> ArtifactDocument:
        relative = safe_relative_path(
            canonical_path,
            field_name="canonical artifact path",
        ).as_posix()
        target = self.canonical_path(relative, must_exist=True)
        document = validate_artifact(
            target,
            run_root=self.run_root,
            relative_path=relative,
            expected_run_id=self.run_id,
            expected_metadata=expected_metadata,
            allowed_source_refs=allowed_source_refs,
        )
        if expected_metadata is not None:
            stage = document.metadata.get("stage")
            artifact_type = document.metadata.get("artifact_type")
            if not isinstance(stage, str):
                raise ArtifactValidationError("stage must be a non-empty string")
            _validate_manifest_binding(
                artifact_spec(
                    stage,
                    artifact_type if isinstance(artifact_type, str) else None,
                ),
                expected_metadata,
                revision=document.revision,
            )
        self._validate_lineage(document, relative)
        return document


__all__ = [
    "ARTIFACT_SCHEMA_VERSION",
    "COMMON_FRONT_MATTER_FIELDS",
    "COMMON_MANIFEST_BINDING_FIELDS",
    "STAGE_ARTIFACT_SPECS",
    "ArtifactConflictError",
    "ArtifactDocument",
    "ArtifactError",
    "ArtifactFormatError",
    "ArtifactSpec",
    "ArtifactStore",
    "ArtifactValidationError",
    "MarkdownSection",
    "PromotionRequest",
    "PublishedArtifact",
    "UnsafePathError",
    "artifact_spec",
    "extract_sections",
    "expected_canonical_path",
    "parse_markdown",
    "parse_markdown_file",
    "required_manifest_binding_fields",
    "safe_join",
    "safe_relative_path",
    "serialize_markdown",
    "split_source_ref",
    "validate_artifact",
    "validate_document",
    "validate_source_refs",
]
