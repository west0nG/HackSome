"""Behavioral text contracts for the CEO strategic-reasoning skill layer."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILLS = ROOT / "agents" / "assets" / "skills"


def _text(name: str) -> str:
    return (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")


def test_meta_skill_routes_to_atoms_without_absorbing_workflows():
    text = _text("think-strategically")
    for name in (
        "trace-causal-chain",
        "challenge-thesis",
        "reason-as-buyer",
        "integrate-new-information",
    ):
        assert f"`{name}`" in text
    assert "read that\n" in text
    assert "complete `SKILL.md`" in text
    assert "do not assume a generic\n`Skill(...)` tool exists" in text
    assert "selecting zero is never valid" in text
    assert "smallest non-zero set" in text
    assert "naming it in prose does not" in " ".join(text.split())
    assert "Do not run them in a fixed sequence" in text
    assert "Do not score the business" in text
    assert "emit a PASS/FAIL verdict" in text
    assert "use `find-opportunity`" in text
    assert "use `manage-objectives`" in text
    assert "use `manage-departments`" in text
    assert "under `/company`" in text


def test_atoms_keep_distinct_reasoning_jobs():
    causal = _text("trace-causal-chain")
    challenge = _text("challenge-thesis")
    buyer = _text("reason-as-buyer")
    integrate = _text("integrate-new-information")

    assert "Reason both forward" in causal and "backward from the sale" in causal
    assert "Do not force every" in causal and "through one funnel" in causal
    assert "strongest fair form" in challenge and "alternative explanations" in challenge
    assert "Do not oppose the thesis for style" in challenge
    assert "Role-play can reveal friction" in buyer and "never market evidence" in buyer
    normalized_buyer = " ".join(buyer.lower().split())
    assert "do not demand proof of a final user outcome" in normalized_buyer
    assert "Identify the exact delta" in integrate
    normalized_integrate = " ".join(integrate.split())
    assert "Do not equate “new” with “start over" in normalized_integrate


def test_v7_objective_workflow_keeps_its_boundary():
    find = _text("find-opportunity")
    objective = _text("manage-objectives")

    assert "working hypothesis" in find
    assert "Do not turn the prior into a lock" in find
    assert "independent review" in objective
    assert "propose_company_objective" in objective
    assert "propose_department_objective" in objective
    assert not (SKILLS / "when-idle" / "SKILL.md").exists()
    assert not (SKILLS / "set-objective" / "SKILL.md").exists()


def test_ceo_charter_reflects_without_reverifying_done():
    charter = (ROOT / "agents" / "assets" / "ceo-charter.md").read_text(
        encoding="utf-8")
    assert "coordinating executive" in charter
    assert "you cannot\ncreate Goals" in charter
    assert "Departments own proactive operating decisions" in charter
    assert "Waiting is never the company's sole state" in charter
    assert "`inspect` is available for read-only verification" in charter
