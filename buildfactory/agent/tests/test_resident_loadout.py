"""V7 fixed-template loadout materialization contracts."""

from pathlib import Path

import pytest

from agent import resident_loadout


ROOT = Path(__file__).resolve().parents[2]
AGENTS = ROOT / "agents"


@pytest.fixture(autouse=True)
def _isolated_runtime_home(tmp_path, monkeypatch):
    home = tmp_path / "user-home"
    home.mkdir()
    auth = tmp_path / "codex-auth.json"
    auth.write_text("{}\n", encoding="utf-8")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("CODEX_AUTH_SEED", str(auth))
    monkeypatch.setenv("DATAFORSEO_USERNAME", "test-user")
    monkeypatch.setenv("DATAFORSEO_PASSWORD", "test-password")
    monkeypatch.delenv("AGENT_SPEC", raising=False)


def _materialize(tmp_path, monkeypatch, key: str, relative_spec: str):
    monkeypatch.setenv("AGENT_SPEC", str(AGENTS / relative_spec))
    return resident_loadout.materialize_for(
        key,
        agents_dir=str(AGENTS),
        claude_home=str(tmp_path / f"{key}-home"),
    )


def test_ceo_gets_organization_objective_and_strategy_skills(tmp_path):
    info = resident_loadout.materialize_for(
        "ceo", agents_dir=str(AGENTS), claude_home=str(tmp_path / "ceo-home")
    )
    assert set(info.skills) == {
        "company-state",
        "claim-mailbox",
        "manage-notes",
        "manage-departments",
        "manage-objectives",
        "find-opportunity",
        "think-strategically",
        "trace-causal-chain",
        "challenge-thesis",
        "reason-as-buyer",
        "integrate-new-information",
    }


@pytest.mark.parametrize(
    ("key", "expected"),
    [
        (
            "strategist",
            {
                "company-state",
                "check-email",
                "send-email",
                "manage-notes",
                "manage-goals",
                "department-messaging",
                "find-opportunity",
                "challenge-thesis",
                "reason-as-buyer",
                "integrate-new-information",
                "trace-causal-chain",
            },
        ),
        (
            "researcher",
            {
                "company-state",
                "check-email",
                "send-email",
                "manage-notes",
                "manage-goals",
                "department-messaging",
                "challenge-thesis",
                "integrate-new-information",
                "trace-causal-chain",
                "reason-as-buyer",
            },
        ),
        (
            "builder",
            {
                "company-state",
                "check-email",
                "send-email",
                "manage-notes",
                "manage-goals",
                "department-messaging",
                "challenge-thesis",
                "integrate-new-information",
                "trace-causal-chain",
            },
        ),
        (
            "growth",
            {
                "company-state",
                "check-email",
                "send-email",
                "manage-notes",
                "manage-goals",
                "department-messaging",
                "challenge-thesis",
                "integrate-new-information",
                "trace-causal-chain",
                "reason-as-buyer",
            },
        ),
    ],
)
def test_department_templates_get_goal_methods_and_broad_judgment_skills(
    tmp_path, monkeypatch, key, expected
):
    info = _materialize(tmp_path, monkeypatch, key, f"departments/{key}.yaml")
    assert set(info.skills) == expected


def test_worker_reuses_broad_execution_skill_library(tmp_path, monkeypatch):
    info = _materialize(tmp_path, monkeypatch, "worker", "ephemeral/worker.yaml")
    assert set(info.skills) == {
        "company-state",
        "check-email",
        "send-email",
        "submit-work",
        "challenge-thesis",
        "trace-causal-chain",
        "reason-as-buyer",
        "integrate-new-information",
        "mine-customer-voice",
        "de-ai-ify",
        "design-asset",
        "gen-image",
        "visual-iterate",
        "deploy-site",
        "provision-ga4",
        "operate-twitter",
    }
    skills_root = tmp_path / "user-home" / ".agents" / "skills"
    assert (skills_root / "de-ai-ify" / "references" / "en-humanizer.md").is_file()
    assert (skills_root / "design-asset" / "scripts" / "render_asset.mjs").is_file()
    assert (skills_root / "gen-image" / "scripts" / "generate_image.py").is_file()


def test_ephemeral_verifier_keeps_only_read_skill_and_charter_verdict(
    tmp_path, monkeypatch
):
    info = _materialize(tmp_path, monkeypatch, "verifier", "ephemeral/verifier.yaml")
    assert info.skills == ["company-state-readonly"]


def test_old_static_role_templates_are_absent():
    assert not {
        "researcher.yaml",
        "builder.yaml",
        "growth.yaml",
        "verifier.yaml",
    }.intersection(path.name for path in AGENTS.glob("*.yaml"))


def test_unknown_key_is_charter_only(tmp_path):
    assert resident_loadout.materialize_for(
        "nope", agents_dir=str(AGENTS), claude_home=str(tmp_path / "home")
    ) is None


def test_main_never_bricks_on_bad_template(tmp_path, monkeypatch, capsys):
    bad_dir = tmp_path / "agents"
    bad_dir.mkdir()
    (bad_dir / "ghost.yaml").write_text(
        "name: ghost\nskills:\n  - assets/skills/does-not-exist\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("AGENT_KEY", "ghost")
    monkeypatch.setenv("AGENTS_DIR", str(bad_dir))
    monkeypatch.setenv("CLAUDE_HOME", str(tmp_path / "claude"))
    assert resident_loadout.main() == 0
    assert "ERROR materializing" in capsys.readouterr().out


def test_main_without_agent_key_is_noop(monkeypatch):
    monkeypatch.delenv("AGENT_KEY", raising=False)
    assert resident_loadout.main() == 0


def test_deprecated_loadout_overlay_cannot_mutate_fixed_template(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("AGENT_LOADOUT", str(tmp_path / "arbitrary.yaml"))
    info = _materialize(tmp_path, monkeypatch, "builder", "departments/builder.yaml")
    assert "manage-goals" in info.skills
    assert "trace-causal-chain" in info.skills
