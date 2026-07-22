"""Versioned prompt resources and strict rendering for workflow stages."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from enum import Enum
from hashlib import sha256
import json
from pathlib import Path
import re
from string import Formatter
from typing import Any, Mapping


class PromptRenderError(ValueError):
    """Raised when a prompt cannot be rendered without ambiguity."""


@dataclass(frozen=True, slots=True)
class RenderedPrompt:
    """A rendered prompt plus reproducibility metadata."""

    text: str
    prompt_template_id: str
    prompt_version: str
    template_hash: str
    prompt_hash: str
    context_hash: str

    @property
    def template_id(self) -> str:
        """Compatibility alias for the persisted prompt template id."""

        return self.prompt_template_id

    @property
    def template_version(self) -> str:
        """Compatibility alias for the persisted prompt version."""

        return self.prompt_version


@dataclass(frozen=True, slots=True)
class _PromptSpec:
    template_id: str
    version: str
    filename: str


_PROMPT_SPECS: dict[str, _PromptSpec] = {
    "S0": _PromptSpec("hacksome.s0.parse-challenge", "1", "s0-parse-challenge.md"),
    "S1": _PromptSpec("hacksome.s1.expand-audiences", "1", "s1-expand-audiences.md"),
    "S2": _PromptSpec("hacksome.s2.research-evidence", "1", "s2-research-evidence.md"),
    "S3": _PromptSpec("hacksome.s3.verify-evidence", "1", "s3-verify-evidence.md"),
    "S4": _PromptSpec("hacksome.s4.synthesize-problems", "1", "s4-synthesize-problems.md"),
    "S5": _PromptSpec("hacksome.s5.gate-problem", "1", "s5-gate-problem.md"),
    "S6": _PromptSpec("hacksome.s6.generate-ideas", "1", "s6-generate-ideas.md"),
    "S7": _PromptSpec("hacksome.s7.research-competitors", "1", "s7-research-competitors.md"),
    "S8": _PromptSpec("hacksome.s8.revise-idea", "1", "s8-revise-idea.md"),
    "S9": _PromptSpec("hacksome.s9.red-team-idea", "1", "s9-red-team-idea.md"),
    "S10": _PromptSpec("hacksome.s10.build-feasibility", "1", "s10-build-feasibility.md"),
}

_STAGE_ALIASES = {
    "parse_challenge": "S0",
    "parse_brief": "S0",
    "expand_audiences": "S1",
    "research_evidence": "S2",
    "verify_evidence": "S3",
    "synthesize_problems": "S4",
    "gate_problem": "S5",
    "generate_ideas": "S6",
    "research_competitors": "S7",
    "revise_idea": "S8",
    "red_team_idea": "S9",
    "build_feasibility": "S10",
}

_SCHEMA_FILES = {
    "s0": "s0-challenge-brief.schema.json",
    "challenge_brief": "s0-challenge-brief.schema.json",
    "s1": "s1-audience-list.schema.json",
    "audience_list": "s1-audience-list.schema.json",
    "completion": "completion-envelope.schema.json",
    "completion_envelope": "completion-envelope.schema.json",
}

# These are intentionally narrow leakage checks, not a second context-manifest
# schema. They catch unmistakable cross-stage artifacts while leaving the
# workflow's manifest owner responsible for its complete allowlist.
_FORBIDDEN_CONTEXT_MARKERS: dict[str, frozenset[str]] = {
    "S0": frozenset(
        {
            "challenge_brief",
            "discovery_view",
            "compliance_view",
            "audience",
            "research",
            "verification",
            "problem",
            "problem_gateway",
            "idea",
            "competition",
            "idea_red_team",
            "feasibility",
        }
    ),
    "S1": frozenset(
        {
            "challenge_brief",
            "compliance_view",
            "audience",
            "research",
            "verification",
            "problem",
            "problem_gateway",
            "idea",
            "competition",
            "idea_red_team",
            "feasibility",
        }
    ),
    "S2": frozenset(
        {
            "challenge_brief",
            "compliance_view",
            "verification",
            "problem",
            "problem_gateway",
            "idea",
            "competition",
            "idea_red_team",
            "feasibility",
        }
    ),
    "S3": frozenset(
        {
            "challenge_brief",
            "discovery_view",
            "compliance_view",
            "verification",
            "problem",
            "problem_gateway",
            "idea",
            "competition",
            "idea_red_team",
            "feasibility",
        }
    ),
    "S4": frozenset(
        {
            "challenge_brief",
            "compliance_view",
            "problem_gateway",
            "idea",
            "competition",
            "idea_red_team",
            "feasibility",
        }
    ),
    "S5": frozenset(
        {
            "challenge_brief",
            "discovery_view",
            "compliance_view",
            "problem_gateway",
            "idea",
            "competition",
            "idea_red_team",
            "feasibility",
        }
    ),
    "S6": frozenset(
        {
            "challenge_brief",
            "compliance_view",
            "idea",
            "competition",
            "idea_red_team",
            "feasibility",
        }
    ),
    "S7": frozenset(
        {
            "challenge_brief",
            "discovery_view",
            "compliance_view",
            "audience",
            "competition",
            "idea_red_team",
            "feasibility",
        }
    ),
    "S8": frozenset({"challenge_brief", "discovery_view", "audience"}),
    "S9": frozenset(
        {
            "challenge_brief",
            "discovery_view",
            "compliance_view",
            "audience",
            "idea_red_team",
            "feasibility",
        }
    ),
    "S10": frozenset(
        {
            "challenge_brief",
            "discovery_view",
            "compliance_view",
            "audience",
            "research",
            "verification",
            "problem",
            "problem_gateway",
            "competition",
        }
    ),
}

_TYPE_MARKERS = {
    "audience": "audience",
    "audience_list": "audience",
    "challenge_brief": "challenge_brief",
    "competition": "competition",
    "competitor_research": "competition",
    "compliance": "compliance_view",
    "compliance_view": "compliance_view",
    "discovery_view": "discovery_view",
    "feasibility": "feasibility",
    "idea": "idea",
    "idea_card": "idea",
    "idea_red_team": "idea_red_team",
    "problem": "problem",
    "problem_card": "problem",
    "problem_gateway": "problem_gateway",
    "gateway": "problem_gateway",
    "red_team": "idea_red_team",
    "research": "research",
    "verification": "verification",
}

_PATH_MARKERS: tuple[tuple[str, str], ...] = (
    ("/idea-reviews/", "idea_red_team"),
    ("/feasibility/", "feasibility"),
    ("/competition/", "competition"),
    ("/gateways/", "problem_gateway"),
    ("/verification/", "verification"),
    ("/research/", "research"),
    ("/problems/", "problem"),
    ("/ideas/", "idea"),
)

_COMMON_CALLER_VARIABLES = frozenset(
    {
        "run_id",
        "task_id",
        "language",
        "context_manifest",
        "output_target",
        "mode",
        "attempt",
        "session_marker",
    }
)


def schema_path(name: str) -> Path:
    """Return the packaged path for a supported Codex output schema."""

    normalized = name.strip().lower().replace("-", "_").removesuffix(".json")
    try:
        filename = _SCHEMA_FILES[normalized]
    except KeyError as exc:
        choices = ", ".join(sorted({"s0", "s1", "completion"}))
        raise KeyError(f"unknown schema {name!r}; expected one of: {choices}") from exc
    path = Path(__file__).resolve().parent / "schemas" / filename
    if not path.is_file():
        raise FileNotFoundError(f"packaged schema is missing: {path}")
    return path


class PromptRenderer:
    """Load and strictly render the external prompt for one workflow stage."""

    def __init__(self, resource_root: Path | None = None) -> None:
        self._resource_root = (
            resource_root.resolve()
            if resource_root is not None
            else Path(__file__).resolve().parent
        )
        self._prompt_root = self._resource_root / "prompts"

    @staticmethod
    def schema_path(name: str) -> Path:
        return schema_path(name)

    @staticmethod
    def required_variables(stage: object) -> frozenset[str]:
        _normalize_stage(stage)
        return _COMMON_CALLER_VARIABLES

    def render(
        self, stage: object, variables: Mapping[str, object]
    ) -> RenderedPrompt:
        canonical_stage = _normalize_stage(stage)
        if not isinstance(variables, Mapping):
            raise TypeError("variables must be a mapping")

        spec = _PROMPT_SPECS[canonical_stage]
        common = self._read_prompt("common.md")
        template = self._read_prompt(spec.filename)
        fields = _placeholder_fields(template)
        expected = fields - {"common_contract"}
        supplied = set(variables)

        missing = sorted(expected - supplied)
        extra = sorted(supplied - expected)
        if missing or extra:
            parts: list[str] = []
            if missing:
                parts.append(f"missing variables: {', '.join(missing)}")
            if extra:
                parts.append(f"unexpected variables: {', '.join(extra)}")
            raise PromptRenderError(
                f"cannot render {canonical_stage}: " + "; ".join(parts)
            )
        if expected != _COMMON_CALLER_VARIABLES:
            missing_contract = sorted(_COMMON_CALLER_VARIABLES - expected)
            extra_contract = sorted(expected - _COMMON_CALLER_VARIABLES)
            raise PromptRenderError(
                f"template {spec.filename} violates the common variable contract; "
                f"missing={missing_contract}, extra={extra_contract}"
            )

        context = variables["context_manifest"]
        _validate_context_boundary(canonical_stage, variables["mode"], context)
        rendered_values = {key: _display_value(value) for key, value in variables.items()}
        rendered_values["common_contract"] = common.rstrip()

        try:
            text = template.format_map(rendered_values).rstrip() + "\n"
        except (KeyError, ValueError) as exc:  # Defensive: fields were checked above.
            raise PromptRenderError(
                f"failed to render {canonical_stage} template: {exc}"
            ) from exc

        template_material = (
            f"{spec.template_id}\0{spec.version}\0{common}\0{template}".encode("utf-8")
        )
        return RenderedPrompt(
            text=text,
            prompt_template_id=spec.template_id,
            prompt_version=spec.version,
            template_hash=sha256(template_material).hexdigest(),
            prompt_hash=sha256(text.encode("utf-8")).hexdigest(),
            context_hash=sha256(_canonical_json(context).encode("utf-8")).hexdigest(),
        )

    def _read_prompt(self, filename: str) -> str:
        path = self._prompt_root / filename
        if not path.is_file():
            raise FileNotFoundError(f"packaged prompt is missing: {path}")
        return path.read_text(encoding="utf-8")


def _normalize_stage(stage: object) -> str:
    candidates: list[str] = []
    if isinstance(stage, Enum):
        candidates.extend([str(stage.value), stage.name])
    else:
        candidates.append(str(stage))

    for candidate in candidates:
        normalized = candidate.strip().replace("-", "_").replace(" ", "_")
        upper = normalized.upper()
        if upper in _PROMPT_SPECS:
            return upper
        alias = _STAGE_ALIASES.get(normalized.lower())
        if alias is not None:
            return alias
        match = re.search(r"(?:^|[._])S(10|[0-9])(?:$|[._])", upper)
        if match:
            return f"S{match.group(1)}"

    raise KeyError(f"unknown prompt stage: {stage!r}")


def _placeholder_fields(template: str) -> frozenset[str]:
    fields: set[str] = set()
    try:
        parsed = Formatter().parse(template)
        for _, field_name, format_spec, conversion in parsed:
            if field_name is None:
                continue
            if not field_name or not field_name.isidentifier():
                raise PromptRenderError(
                    f"template placeholder must be a simple identifier: {field_name!r}"
                )
            if format_spec or conversion:
                raise PromptRenderError(
                    f"template placeholder cannot use formatting or conversion: {field_name}"
                )
            fields.add(field_name)
    except ValueError as exc:
        raise PromptRenderError(f"invalid prompt template: {exc}") from exc
    return frozenset(fields)


def _display_value(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, Enum):
        return str(value.value)
    if value is None or isinstance(value, (bool, int, float)):
        return json.dumps(value, allow_nan=False, ensure_ascii=False)
    return json.dumps(
        _json_value(value),
        allow_nan=False,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )


def _canonical_json(value: object) -> str:
    return json.dumps(
        _json_value(value),
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _json_value(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_value(asdict(value))
    if isinstance(value, Enum):
        return _json_value(value.value)
    if isinstance(value, Path):
        return value.as_posix()
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if isinstance(value, (set, frozenset)):
        normalized = [_json_value(item) for item in value]
        return sorted(normalized, key=lambda item: json.dumps(item, sort_keys=True))
    raise TypeError(
        f"prompt variable value of type {type(value).__name__} is not JSON serializable"
    )


def _validate_context_boundary(stage: str, mode: object, manifest: object) -> None:
    markers = _context_markers(manifest)
    forbidden = set(_FORBIDDEN_CONTEXT_MARKERS[stage])

    # S8 is the only authoring stage that may receive a previous review. Which
    # review is allowed is determined by the bounded repair mode.
    if stage == "S8":
        raw_mode = mode.value if isinstance(mode, Enum) else mode
        normalized_mode = str(raw_mode).strip().lower().replace("-", "_")
        if "product_repair" in normalized_mode or "red_team" in normalized_mode:
            forbidden.add("feasibility")
        elif "scope_reduction" in normalized_mode or "feasibility" in normalized_mode:
            forbidden.add("idea_red_team")
        else:
            forbidden.update({"idea_red_team", "feasibility"})

    leaked = sorted(markers & forbidden)
    if leaked:
        raise PromptRenderError(
            f"context for {stage} crosses its stage boundary: {', '.join(leaked)}"
        )


def _context_markers(value: object) -> set[str]:
    markers: set[str] = set()

    def visit(item: object, parent_key: str | None = None) -> None:
        if is_dataclass(item) and not isinstance(item, type):
            visit(asdict(item), parent_key)
            return
        if isinstance(item, Mapping):
            for raw_key, child in item.items():
                key = str(raw_key).strip().lower().replace("-", "_")
                key_marker = _TYPE_MARKERS.get(key)
                if key_marker is not None and key not in {"type", "kind"}:
                    markers.add(key_marker)
                if key in {"artifact_type", "artifact_kind", "context_type"}:
                    marker = _TYPE_MARKERS.get(str(child).strip().lower().replace("-", "_"))
                    if marker is not None:
                        markers.add(marker)
                elif key in {"path", "file", "relative_path", "artifact_path"}:
                    _add_path_marker(markers, child)
                elif key not in {"content", "text", "body", "payload"}:
                    visit(child, key)
            return
        if isinstance(item, (list, tuple, set, frozenset)):
            for child in item:
                visit(child, parent_key)
            return
        if parent_key in {"path", "file", "relative_path", "artifact_path"}:
            _add_path_marker(markers, item)

    visit(value)
    return markers


def _add_path_marker(markers: set[str], path_value: object) -> None:
    if not isinstance(path_value, (str, Path)):
        return
    normalized = "/" + str(path_value).replace("\\", "/").strip("/").lower() + "/"
    for needle, marker in _PATH_MARKERS:
        if needle in normalized:
            markers.add(marker)


__all__ = [
    "PromptRenderError",
    "PromptRenderer",
    "RenderedPrompt",
    "schema_path",
]
