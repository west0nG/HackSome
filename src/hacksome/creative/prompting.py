"""Versioned PromptCatalog for every model-backed Creative stage."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

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
    C6A_EVIDENCE_REVISE,
    C6B_PORTFOLIO_CURATE,
    C6C_FEEDBACK_REVISE,
    CreativeWorkflowSettings,
)
from hacksome.prompting import PromptCatalog, PromptSpec


_PACKAGE_ROOT = Path(__file__).resolve().parent.parent
_PROMPT_DIR = _PACKAGE_ROOT / "prompts" / "creative"
_SCHEMA_DIR = _PACKAGE_ROOT / "schemas" / "creative"


def _spec(stage: str, *, web_search: bool = False) -> PromptSpec:
    short_name = stage.removeprefix("creative-")
    return PromptSpec(
        stage=stage,
        template_id=f"hacksome.creative.{short_name}",
        version="1",
        template_path=_PROMPT_DIR / f"{stage}.md",
        schema_path=_SCHEMA_DIR / f"{stage}.schema.json",
        web_search=web_search,
    )


creative_prompt_catalog = PromptCatalog(
    (
        _spec(C0_CHALLENGE_PARSE),
        _spec(C1_BRIEF_NORMALIZE),
        _spec(C2_TERRITORY_EXPLORE),
        _spec(C3_CONCEPT_SYNTHESIZE),
        _spec(C4_CHEAP_HOOK_REVIEW),
        _spec(C4_CHEAP_HOOK_REPAIR),
        _spec(C5M_MEMORY_RECALL),
        _spec(C5M_MEMORY_REMIX),
        _spec(C5W_NOVELTY_SCAN, web_search=True),
        _spec(C6A_EVIDENCE_REVISE),
        _spec(C6B_PORTFOLIO_CURATE),
        _spec(C6C_FEEDBACK_REVISE),
    )
)

def validate_creative_output(
    stage: str,
    output: Mapping[str, Any],
    *,
    settings: CreativeWorkflowSettings,
    context: Any = None,
) -> dict[str, Any]:
    """Validate through the route artifact owner without a module import cycle."""

    from hacksome.creative.artifacts import (
        validate_creative_output as validate_artifact,
    )

    return validate_artifact(
        stage,
        output,
        settings=settings,
        context=context,
    )


__all__ = ["creative_prompt_catalog", "validate_creative_output"]
