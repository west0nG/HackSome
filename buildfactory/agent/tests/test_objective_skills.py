"""V7 Objective ownership and independent-review prompt contracts."""

from pathlib import Path

import yaml

from orchestration.verifier_runtime import verifier_prompt


ROOT = Path(__file__).resolve().parents[2]
SKILLS = ROOT / "agents" / "assets" / "skills"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_ceo_has_v7_objective_management_without_v6_review_products():
    config = yaml.safe_load(_text(ROOT / "agents" / "ceo.yaml"))
    names = [Path(value).name for value in config["skills"]]
    assert names.count("manage-objectives") == 1
    assert not {
        "set-objective",
        "review-objective",
        "send-goal",
        "create-role",
        "review-role",
    } & set(names)


def test_manage_objectives_teaches_company_and_department_boundaries():
    text = _text(SKILLS / "manage-objectives" / "SKILL.md")
    required = [
        "concrete buyer or user",
        "what they do today",
        "costly behavior",
        "unresolved gap",
        "first real users",
        "smallest real delivery",
        "facts, assumptions, and unknowns",
        "durable ownership outcome",
        "not a Goal list",
        "independent review",
    ]
    for phrase in required:
        assert phrase in text
    assert "propose_company_objective" in text
    assert "propose_department_objective" in text


def test_ephemeral_verifier_has_one_structured_verdict_capability():
    config = yaml.safe_load(_text(ROOT / "agents" / "ephemeral" / "verifier.yaml"))
    names = [Path(value).name for value in config["skills"]]
    assert names == ["company-state-readonly"]
    assert "heartbeat" not in config
    assert "session" not in config

    charter = _text(ROOT / "agents" / "assets" / "verifier-v7-charter.md")
    assert "one-review judge" in charter
    assert "exactly once" in charter
    assert "destroyed after verdict" in charter
    assert "orchestration.control_client submit_verdict" in charter
    assert "authenticated external accounts" in charter
    assert "exactly `PASS` or `FAIL`" in charter
    assert not (SKILLS / "submit-verdict").exists()
    assert not (SKILLS / "company-methods").exists()


def test_verifier_prompt_applies_distinct_objective_and_goal_rubrics():
    company = verifier_prompt(
        {
            "review_id": "review-1",
            "kind": "company_objective",
            "subject_id": "ceo",
            "payload": {"text": "candidate", "current": None},
        }
    )
    department = verifier_prompt(
        {
            "review_id": "review-2",
            "kind": "department_objective",
            "subject_id": "researcher",
            "payload": {"text": "candidate", "current": "old"},
        }
    )
    goal = verifier_prompt(
        {
            "review_id": "review-3",
            "kind": "goal_result",
            "subject_id": "goal-1",
            "payload": {
                "goal_id": "goal-1",
                "owner_department": "builder",
                "intent": "deliver result",
                "acceptance": "must be evidenced",
                "deadline_at": "2026-07-19T12:00:00Z",
            },
        }
    )

    assert "every item is load-bearing" in company
    assert "costly behavior" in company
    assert "Never lower the bar" in company
    assert "Do not force the Company Objective's external market-demand rubric" in department
    assert "not a one-off Goal" in department
    assert "only declared completion" in goal
    assert "authenticated external accounts" in goal
    assert "A /company artifact is optional" in goal
    assert "never execute, repair, publish" in goal
    assert "same Worker" in goal


def test_find_opportunity_respects_three_layer_ownership():
    files = [SKILLS / "find-opportunity" / "SKILL.md"]
    files.extend((SKILLS / "find-opportunity" / "references").rglob("*.md"))
    joined = "\n".join(_text(path) for path in files)
    assert "manage-objectives" in joined
    assert "CEO must perform this bounded strategic research" in joined
    assert "Once a Strategy Department exists" in joined
    assert "leaves the Company Objective decision to the CEO" in joined
    assert "Department—not the CEO—will" in joined
    assert "set-objective" not in joined
    assert "orchestration.messaging" not in joined


def test_active_ceo_charter_separates_objectives_from_goals():
    text = _text(ROOT / "agents" / "assets" / "ceo-charter.md")
    assert "Company strategy" in text
    assert "you cannot" in text and "create Goals" in text
    assert "Departments own proactive operating decisions" in text
    assert "inspect` is available for read-only verification" in text
    assert "Waiting is never the company's sole state" in text
