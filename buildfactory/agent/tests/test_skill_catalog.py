"""V7 active Agent loadouts expose only their declared top-level Skills."""

from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

from agent.spec import AgentSpec


ROOT = Path(__file__).resolve().parents[2]
AGENTS = ROOT / "agents"
SKILLS = AGENTS / "assets" / "skills"
ROLE_YAMLS = {
    "ceo": AGENTS / "ceo.yaml",
    "strategist": AGENTS / "departments" / "strategist.yaml",
    "researcher": AGENTS / "departments" / "researcher.yaml",
    "builder": AGENTS / "departments" / "builder.yaml",
    "growth": AGENTS / "departments" / "growth.yaml",
    "worker": AGENTS / "ephemeral" / "worker.yaml",
    "verifier": AGENTS / "ephemeral" / "verifier.yaml",
}
EXPECTED_ROLE_COUNTS = {
    "ceo": 11,
    "strategist": 11,
    "researcher": 10,
    "builder": 9,
    "growth": 10,
    "worker": 16,
    "verifier": 1,
}
MAX_DESCRIPTION_CHARS = 200
MAX_ROLE_DESCRIPTION_CHARS = 3000
UPSTREAM_HASHES = {
    "de-ai-ify/zh/upstream-SKILL.md":
        "28ccdd2792a456168e7872f6d9d1186982680128240b38516bf83c84ea272beb",
    "design-asset/references/anthropic-frontend-design/upstream-SKILL.md":
        "1608ea77fbb6fc30d13a97d12cfa8ebf31358d40f0dd97beed24829d6b3f45dd",
    "gen-image/references/smixs-image/upstream-SKILL.md":
        "cbcb39232bfd43e14f05bc0ead38b8fd01a5304aca6f295befc8021345cc0dea",
    "gen-image/references/codex/upstream-SKILL.md":
        "30747274af88ee0c0a335f9de96039d33379289cf56d60e620a57c5425c5c894",
}


def _skill_dirs(role: str) -> list[Path]:
    spec = AgentSpec.load(str(ROLE_YAMLS[role]))
    return [Path(path).resolve() for path in spec.skill_paths()]


def _frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"missing frontmatter: {path}"
    _opening, raw, _body = text.split("---", 2)
    meta = yaml.safe_load(raw)
    assert isinstance(meta, dict), f"frontmatter must be a mapping: {path}"
    return meta


def _catalog_descriptions() -> dict[str, str]:
    names = {path.name for role in ROLE_YAMLS for path in _skill_dirs(role)}
    return {
        name: _frontmatter(SKILLS / name / "SKILL.md")["description"].lower()
        for name in names
    }


def test_v7_role_catalog_is_top_level_resolvable_and_budgeted():
    skills_root = SKILLS.resolve()
    assert set(ROLE_YAMLS) == set(EXPECTED_ROLE_COUNTS)

    for role in ROLE_YAMLS:
        skill_dirs = _skill_dirs(role)
        assert len(skill_dirs) == EXPECTED_ROLE_COUNTS[role]
        assert len(skill_dirs) == len(set(skill_dirs)), f"duplicate skill in {role}"

        role_chars = 0
        for skill_dir in skill_dirs:
            assert skill_dir.parent == skills_root
            host = skill_dir / "SKILL.md"
            assert host.is_file(), f"missing host entrypoint: {host}"
            meta = _frontmatter(host)
            assert set(meta) == {"name", "description"}
            assert meta["name"] == skill_dir.name
            description = meta["description"]
            assert description == " ".join(description.split())
            assert len(description) <= MAX_DESCRIPTION_CHARS
            role_chars += len(description)
        assert role_chars <= MAX_ROLE_DESCRIPTION_CHARS


def test_v7_active_loadouts_remove_old_role_and_goal_products():
    declared = {path.name for role in ROLE_YAMLS for path in _skill_dirs(role)}
    assert {
        "manage-departments",
        "manage-objectives",
        "manage-goals",
        "department-messaging",
        "submit-work",
    } <= declared
    retired = {
        "company-methods",
        "create-role",
        "review-role",
        "review-objective",
        "send-goal",
        "receive-goal",
        "set-objective",
        "submit-verdict",
        "when-idle",
    }
    assert not (declared & retired)
    assert all(not (SKILLS / name / "SKILL.md").exists() for name in retired)


def test_worker_reuses_the_broad_execution_skill_field():
    worker = {path.name for path in _skill_dirs("worker")}
    assert {
        "mine-customer-voice",
        "de-ai-ify",
        "design-asset",
        "gen-image",
        "visual-iterate",
        "deploy-site",
        "provision-ga4",
        "operate-twitter",
        "challenge-thesis",
        "trace-causal-chain",
        "reason-as-buyer",
        "integrate-new-information",
    } <= worker

    resident_decision_layers = {
        path.name
        for role in ("ceo", "strategist", "researcher", "builder", "growth")
        for path in _skill_dirs(role)
    }
    assert not {
        "deploy-site",
        "provision-ga4",
        "operate-twitter",
        "design-asset",
        "gen-image",
    }.intersection(resident_decision_layers)


def test_company_mail_skills_follow_role_boundaries_and_use_only_hub_methods():
    role_skills = {
        role: {path.name for path in _skill_dirs(role)} for role in ROLE_YAMLS
    }
    assert "claim-mailbox" in role_skills["ceo"]
    assert not {"check-email", "send-email"}.intersection(role_skills["ceo"])
    for role in ("strategist", "researcher", "builder", "growth", "worker"):
        assert {"check-email", "send-email"} <= role_skills[role]
        assert "claim-mailbox" not in role_skills[role]
    assert not {"claim-mailbox", "check-email", "send-email"}.intersection(
        role_skills["verifier"]
    )

    texts = {
        name: (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
        for name in ("claim-mailbox", "check-email", "send-email")
    }
    assert all("orchestration.control_client" in text for text in texts.values())
    legacy = (
        "orchestration.receive_tool",
        "orchestration.mailbox mine",
        "add-receiver",
        "remove-receiver",
        "orchestration.email_send --",
    )
    assert all(token not in "\n".join(texts.values()) for token in legacy)
    assert "guidance, not a ban" in texts["check-email"]
    assert "guidance, not a permission restriction" in texts["send-email"]


def test_declared_skill_trees_have_one_discoverable_entrypoint():
    for skill_dir in {path for role in ROLE_YAMLS for path in _skill_dirs(role)}:
        entrypoints = set(skill_dir.rglob("SKILL.md"))
        assert entrypoints == {skill_dir / "SKILL.md"}


def test_vendored_entrypoints_remain_byte_exact():
    for relative, expected in UPSTREAM_HASHES.items():
        path = SKILLS / relative
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected


def test_v7_method_skill_descriptions_keep_distinct_boundaries():
    descriptions = _catalog_descriptions()

    assert "public department options" in descriptions["manage-departments"]
    assert "objective revisions" in descriptions["manage-objectives"]
    assert "department create, inspect, and cancel" in descriptions["manage-goals"]
    assert "private lightweight cross-wake note" in descriptions["manage-notes"]
    assert "another through hub" in descriptions["department-messaging"]
    assert "one-goal worker" in descriptions["submit-work"]
    assert "company foundagent.net addresses" in descriptions["claim-mailbox"]
    assert "verification code" in descriptions["check-email"]
    assert "department and worker" in descriptions["send-email"]

    think = descriptions["think-strategically"]
    causal = descriptions["trace-causal-chain"]
    challenge = descriptions["challenge-thesis"]
    buyer = descriptions["reason-as-buyer"]
    integrate = descriptions["integrate-new-information"]
    assert "strategic reasoning" in think and "every ceo wake" in think
    assert "commercial result" in causal
    assert "counterevidence" in challenge
    assert "concrete buyer" in buyer
    assert "existing company reasoning" in integrate
