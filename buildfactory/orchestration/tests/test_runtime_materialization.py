from pathlib import Path

from agent.spec import AgentSpec
from orchestration.runtime_materialization import (
    account_package_docker_args,
    materialize_ephemeral_home,
    read_env_file,
    wait_for_computer_server,
)


ROOT = Path(__file__).resolve().parents[2]


def test_env_file_parser_never_evaluates_shell_text(tmp_path):
    env_file = tmp_path / "secrets.env"
    env_file.write_text(
        "# comment\nTOKEN='literal value'\nDANGEROUS=$(touch /tmp/never-run)\n",
        encoding="utf-8",
    )

    values = read_env_file(env_file)

    assert values == {
        "TOKEN": "literal value",
        "DANGEROUS": "$(touch /tmp/never-run)",
    }


def test_ephemeral_codex_home_gets_bound_skills_auth_and_account_env(tmp_path):
    account = tmp_path / "account"
    account.mkdir()
    (account / "codex-auth.json").write_text('{"tokens":"seed"}', encoding="utf-8")
    (account / "secrets.env").write_text(
        "DATAFORSEO_USERNAME=test-user\n"
        "DATAFORSEO_PASSWORD=test-pass\n"
        "STRIPE_SECRET_KEY=test-stripe\n",
        encoding="utf-8",
    )
    spec = AgentSpec.load(str(ROOT / "agents" / "ephemeral" / "worker.yaml"))
    home = tmp_path / "home"

    info = materialize_ephemeral_home(
        spec,
        home,
        account_dir=account,
        include_account_secrets=True,
    )

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
    assert (home / "skills" / "submit-work" / "SKILL.md").is_file()
    assert (home / "skills" / "check-email" / "SKILL.md").is_file()
    assert (home / "skills" / "send-email" / "SKILL.md").is_file()
    assert (home / "codex" / "auth.json").read_text(encoding="utf-8") == '{"tokens":"seed"}'
    config = (home / "codex" / "config.toml").read_text(encoding="utf-8")
    assert "test-user" in config
    assert "test-stripe" in config


def test_verifier_materialization_keeps_minimal_loadout_without_serializing_unused_secret(
    tmp_path,
):
    account = tmp_path / "account"
    account.mkdir()
    (account / "codex-auth.json").write_text('{"tokens":"seed"}', encoding="utf-8")
    (account / "secrets.env").write_text(
        "STRIPE_SECRET_KEY=must-not-appear\n", encoding="utf-8"
    )
    spec = AgentSpec.load(str(ROOT / "agents" / "ephemeral" / "verifier.yaml"))
    home = tmp_path / "home"

    materialize_ephemeral_home(
        spec,
        home,
        account_dir=account,
        include_account_secrets=True,
    )

    config = (home / "codex" / "config.toml").read_text(encoding="utf-8")
    assert "must-not-appear" not in config
    assert "stripe" not in config.lower()
    assert "playwright" in config
    assert {path.name for path in (home / "skills").iterdir()} == {
        "company-state-readonly",
    }


def test_account_package_docker_args_share_env_file_and_read_only_mount(tmp_path):
    account = tmp_path / "account"
    account.mkdir()
    env_file = account / "secrets.env"
    env_file.write_text("TOKEN=value\n", encoding="utf-8")

    assert account_package_docker_args(account) == [
        "--env-file",
        str(env_file),
        "-v",
        f"{account}:/account:ro",
    ]


def test_computer_server_readiness_poll_is_bounded(monkeypatch):
    attempts = []
    clock = iter([0.0, 0.0, 0.01, 0.02])
    monkeypatch.setattr("orchestration.runtime_materialization.time.monotonic", lambda: next(clock))
    monkeypatch.setattr("orchestration.runtime_materialization.time.sleep", lambda _: None)

    def run(args):
        attempts.append(args)
        from subprocess import CompletedProcess

        return CompletedProcess(args, 1, "", "not ready")

    assert wait_for_computer_server(run, "worker-1", timeout_secs=0.02) is False
    assert len(attempts) == 3
    assert all(call[:3] == ["docker", "exec", "worker-1"] for call in attempts)


def test_computer_server_readiness_accepts_listening_port():
    from subprocess import CompletedProcess

    def run(args):
        return CompletedProcess(args, 0, "up\n", "")

    assert wait_for_computer_server(run, "verifier-1", timeout_secs=0) is True
