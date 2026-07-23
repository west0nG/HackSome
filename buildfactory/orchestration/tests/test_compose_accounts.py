"""V7 Compose boundaries: fixed kernel, dynamic LLM roles, and state isolation."""

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
COMPOSE = yaml.safe_load((ROOT / "docker-compose.yml").read_text())
SERVICES = COMPOSE["services"]
MAIL_COMPOSE = yaml.safe_load((ROOT / "docker-compose.mail.yml").read_text())


def _target(value: str) -> str:
    parts = value.rsplit(":", 2)
    return parts[-2] if parts[-1] in ("ro", "rw") else parts[-1]


def test_static_stack_contains_only_ceo_plus_deterministic_kernel():
    assert set(SERVICES) == {
        "ceo",
        "hub",
        "worker-manager",
        "verifier-manager",
        "department-provisioner",
        "peripheral",
    }
    for removed in ("researcher", "builder", "growth", "verifier", "broker"):
        assert removed not in SERVICES


def test_ceo_keeps_account_injection_but_no_internal_state_mounts():
    ceo = SERVICES["ceo"]
    account_entries = [
        row
        for row in ceo["env_file"]
        if isinstance(row, dict) and str(row.get("path", "")).startswith("accounts/")
    ]
    assert account_entries and account_entries[0]["required"] is False
    assert any(str(value).endswith(":/account:ro") for value in ceo["volumes"])

    forbidden_targets = {
        "/control",
        "/telemetry",
        "/reviews",
        "/workers",
        "/inbox",
        "/ledger",
        "/departments",
        "/notes",
        "/agents",
        "/sessions",
        "/mailboxes",
        "/mail-global",
        "/shared/control",
        "/shared/telemetry",
        "/shared/reviews",
        "/shared/workers",
        "/shared/inbox",
        "/shared/ledger",
    }
    targets = {_target(str(value)) for value in ceo["volumes"]}
    assert "/company" in targets
    assert not (targets & forbidden_targets)
    assert not any("company_state_kit" in str(value) for value in ceo["volumes"])
    assert "COMPANY_ROOT" not in ceo["environment"]
    assert not {
        "AGENT_CONTEXT_FROM_HUB",
        "AGENT_REMOTE_INBOX",
        "AGENT_RELIABLE_INBOX",
        "AGENT_PROMPT_MODE",
    }.intersection(ceo["environment"])
    assert ceo["environment"]["RESEND_API_KEY"] == ""


def test_only_company_hub_mounts_global_mail_control_plane():
    hub = SERVICES["hub"]
    hub_targets = {_target(str(value)) for value in hub["volumes"]}
    assert "/state" in hub_targets
    assert "/mail-global" in hub_targets
    assert hub["environment"]["COMPANY"] == "${COMPANY:-foundagent}"
    assert hub["environment"]["MAIL_GLOBAL_ROOT"] == "/mail-global"
    assert hub["env_file"] == [{"path": "vm/.env.local", "required": False}]

    for name, service in SERVICES.items():
        if name == "hub":
            continue
        targets = {_target(str(value)) for value in service.get("volumes", [])}
        assert "/mail-global" not in targets
        assert "/mailboxes" not in targets


def test_platform_mail_router_is_a_separate_singleton_project():
    assert MAIL_COMPOSE["name"] == "foundagent-mail"
    assert set(MAIL_COMPOSE["services"]) == {"mail-router"}
    router = MAIL_COMPOSE["services"]["mail-router"]
    assert router["container_name"] == "foundagent-mail-router"
    assert router["build"] == {
        "context": ".",
        "dockerfile": "peripheral/email/Dockerfile",
    }
    assert router["environment"]["MAIL_GLOBAL_ROOT"] == "/mail-global"
    assert router["environment"]["COMPANIES_STATE_ROOT"] == "/companies-state"
    targets = {_target(str(value)) for value in router["volumes"]}
    assert targets == {"/companies-state", "/companies-state/_mail", "/mail-global"}
    assert "ports" not in router
    assert not any(str(key).startswith("foundagent.company") for key in router.get("labels", {}))


def test_system_owned_limits_and_heartbeat_are_fixed_in_compose():
    assert SERVICES["hub"]["environment"]["WORKER_MAX"] == "5"
    assert SERVICES["hub"]["environment"]["VERIFIER_MAX"] == "3"
    assert SERVICES["hub"]["environment"]["GOAL_TIMEOUT_SECS"] == "10800"
    assert SERVICES["ceo"]["environment"]["AGENT_HEARTBEAT_SECS"] == "900"
    assert SERVICES["worker-manager"]["environment"]["WORKER_MAX"] == "5"
    assert SERVICES["verifier-manager"]["environment"]["VERIFIER_MAX"] == "3"


def test_only_lifecycle_managers_receive_docker_socket():
    with_socket = {
        name
        for name, service in SERVICES.items()
        if any(str(value).startswith("/var/run/docker.sock:") for value in service.get("volumes", []))
    }
    assert with_socket == {
        "worker-manager",
        "verifier-manager",
        "department-provisioner",
    }


def test_agent_runtime_never_mounts_operator_logs():
    assert not any("telemetry" in str(value) for value in SERVICES["ceo"]["volumes"])
    assert any(
        "telemetry/services" in str(value)
        for value in SERVICES["peripheral"]["volumes"]
    )
    assert SERVICES["ceo"]["labels"] == {
        "foundagent.company": "${COMPANY:-foundagent}",
        "foundagent.kind": "ceo",
        "foundagent.agent": "ceo",
    }


def test_make_down_cleans_dynamic_containers_by_exact_company_label():
    makefile = (ROOT / "Makefile").read_text()
    down = makefile.split("\ndown:\n", 1)[1].split("\nbuild:\n", 1)[0]

    exact_filter = 'label=foundagent.company=$(COMPANY)'
    assert "$(COMPOSE) stop" in down
    assert down.count(exact_filter) == 2
    assert "docker stop --time 10" in down
    assert "docker rm -f" in down
    assert down.index("$(COMPOSE) stop") < down.index("docker stop --time 10")
    assert down.index("docker rm -f") < down.index("$(COMPOSE) down --remove-orphans")


def test_makefile_manages_mail_router_independently_from_company_stack():
    makefile = (ROOT / "Makefile").read_text()
    assert "MAIL_COMPOSE := docker compose -f docker-compose.mail.yml -p foundagent-mail" in makefile
    assert "mail-up:" in makefile
    assert "$(MAIL_COMPOSE) up -d --build" in makefile
    assert "mail-down:" in makefile
    assert "$(MAIL_COMPOSE) down --remove-orphans" in makefile
    assert "mail-logs:" in makefile
    assert "$(MAIL_COMPOSE) logs -f mail-router" in makefile
    ordinary_up = makefile.split("\nup: shared\n", 1)[1].split("\n# Domain-level", 1)[0]
    assert "MAIL_COMPOSE" not in ordinary_up
