from pathlib import Path

from agent.resident_loadout import materialize_for
from agent.runtimes import runtime_for
from agent.spec import AgentSpec


ROOT = Path(__file__).resolve().parents[2]


def test_all_team_roles_declare_and_materialize_zero_skills(tmp_path, monkeypatch):
    paths = (
        ROOT / "agents" / "lead.yaml",
        ROOT / "agents" / "ephemeral" / "team-worker.yaml",
        ROOT / "agents" / "ephemeral" / "team-verifier.yaml",
    )
    for path in paths:
        spec = AgentSpec.load(str(path))
        assert spec.skills == []
        assert spec.skill_paths() == []
        info = runtime_for(spec).materialize_home(
            spec, str(tmp_path / f"{spec.name}-home")
        )
        assert info.skills == []

    monkeypatch.setenv("AGENT_SPEC", str(paths[0]))
    info = materialize_for("lead", str(ROOT / "agents"), str(tmp_path / "home"))
    assert info is not None
    assert info.skills == []
    skills_root = tmp_path / "home" / "skills"
    assert not skills_root.exists() or list(skills_root.iterdir()) == []
