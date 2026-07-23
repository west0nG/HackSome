"""Live E2E for native ``/company`` discovery, mutation, and verification.

This test intentionally lives outside ``orchestration/tests``: it starts real
Docker containers and spends two real model turns (one Worker, one Verifier).
Run it explicitly with ``make e2e-native-company``.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import time
import uuid
from pathlib import Path

import pytest

from orchestration.company_hub import CompanyHub
from orchestration.method_adapter import ActorContext
from orchestration.runtime_store import read_json, require_identifier


REPO = Path(__file__).resolve().parents[2]
CEO = ActorContext("ceo", "ceo")
PROVISIONER = ActorContext("manager", "department-provisioner")
VERIFIER_MANAGER = ActorContext("manager", "verifier-manager")
DEPARTMENT_ID = "researcher"
TARGET_REF = "/company/quality/native-company-folder-e2e.md"
TARGET_RELATIVE = Path("quality/native-company-folder-e2e.md")
TERMINAL_GOAL_STATES = {"done", "failed_time", "cancelled"}


def _run(
    args: list[str],
    *,
    env: dict[str, str] | None = None,
    timeout: float = 120.0,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        args,
        cwd=REPO,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if check and result.returncode != 0:
        raise AssertionError(
            f"command failed ({result.returncode}): {' '.join(args)}\n"
            f"stdout:\n{result.stdout[-8000:]}\n"
            f"stderr:\n{result.stderr[-8000:]}"
        )
    return result


def _compose(
    compose_env: dict[str, str],
    *args: str,
    timeout: float = 120.0,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    return _run(
        ["docker", "compose", *args],
        env=compose_env,
        timeout=timeout,
        check=check,
    )


def _request(method: str, payload: dict, request_id: str) -> dict:
    return {
        "version": 1,
        "request_id": request_id,
        "method": method,
        "payload": payload,
    }


def _call(
    hub: CompanyHub,
    actor: ActorContext,
    method: str,
    payload: dict,
    request_id: str,
) -> dict:
    response = hub.call(actor, _request(method, payload, request_id))
    assert response["ok"], response
    return response["result"]


def _pass_review(hub: CompanyHub, review_id: str) -> None:
    review = hub.reviews.get(review_id)
    actor = ActorContext(
        "verifier",
        review["instance_id"],
        review_id=review_id,
    )
    _call(
        hub,
        actor,
        "submit_verdict",
        {"verdict": "PASS", "reason": "E2E fixture prerequisite"},
        f"fixture-verdict-{review_id}",
    )
    _call(
        hub,
        VERIFIER_MANAGER,
        "verifier_instance_stopped",
        {
            "review_id": review_id,
            "instance_id": review["instance_id"],
        },
        f"fixture-stopped-{review['instance_id']}",
    )


def _seed_active_department(state_root: Path) -> None:
    """Create only the deterministic prerequisite; no model is used here."""

    hub = CompanyHub(state_root, max_workers=1, max_verifiers=1)
    objective = _call(
        hub,
        CEO,
        "propose_company_objective",
        {
            "objective": (
                "Operate an isolated quality-assurance company that validates "
                "native shared-folder behavior with observable evidence."
            )
        },
        "fixture-company-objective",
    )
    _pass_review(hub, objective["review_id"])

    creation = _call(
        hub,
        CEO,
        "create_department",
        {
            "option_id": DEPARTMENT_ID,
            "initial_objective": (
                "Own repeatable evidence for isolated runtime behavior."
            ),
        },
        "fixture-create-researcher",
    )
    _pass_review(hub, creation["objective_review_id"])
    _call(
        hub,
        PROVISIONER,
        "department_started",
        {
            "creation_id": creation["id"],
            "service_name": "fixture-researcher",
        },
        "fixture-researcher-started",
    )

    # Fixture reviews created real manager commands, but this E2E intentionally
    # starts at Goal execution. Remove only those already-completed fixture
    # commands before the live managers begin scanning.
    for command_dir in (
        hub.layout.reviews / "commands",
        hub.layout.departments / "commands",
    ):
        for path in command_dir.glob("*.json"):
            path.unlink()

    assert list(hub.layout.company.iterdir()) == []


def _wait_for_hub(company: str, timeout: float = 90.0) -> None:
    deadline = time.monotonic() + timeout
    container = f"{company}-hub"
    while time.monotonic() < deadline:
        result = _run(
            [
                "docker",
                "inspect",
                "--format",
                "{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}",
                container,
            ],
            check=False,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip() == "healthy":
            return
        time.sleep(1)
    raise AssertionError(f"Hub {container} did not become healthy")


def _create_live_goal(company: str, sentinel: str) -> dict:
    expected = _expected_content(sentinel)
    intent = (
        "Validate the native Company State cold start. The /company folder is "
        "initially empty and has no MAP.md, OVERVIEW.md, or required index. "
        "First use a native filesystem command to list only /company's direct "
        "children (no recursive listing). Do not call company.py or any Company "
        "State storage CLI. Then create exactly one durable leaf at "
        f"{TARGET_REF} with exactly this UTF-8 content (including the final newline):\n\n"
        f"{expected}\n"
        "Do not create a map, overview, index, log, or any other Company State "
        "file. Finally call submit_result as the payload-free completion signal. "
        "Do not attach a summary, path list, or other result payload."
    )
    acceptance = (
        f"Inspect {TARGET_REF}. PASS only if it exists with the exact requested "
        f"content and sentinel {sentinel}, it is the only leaf under /company, "
        "and no MAP.md or OVERVIEW.md was created. The durable file itself, not "
        "an unverified completion claim, is the evidence."
    )
    result = _run(
        [
            "docker",
            "exec",
            "-e",
            f"AGENT_KEY={DEPARTMENT_ID}",
            "-e",
            "AGENT_KIND=department",
            "-e",
            f"DEPARTMENT_ID={DEPARTMENT_ID}",
            "-e",
            "HUB_URL=http://127.0.0.1:8910",
            f"{company}-hub",
            "python3",
            "-m",
            "orchestration.control_client",
            "create_goal",
            "--json",
            json.dumps(
                {"intent": intent, "acceptance": acceptance},
                ensure_ascii=False,
            ),
            "--request-id",
            "e2e-native-company-goal",
        ],
        timeout=30,
    )
    return json.loads(result.stdout)


def _expected_content(sentinel: str) -> str:
    return (
        "# Native Company Folder E2E\n"
        f"sentinel: {sentinel}\n"
        "discovery: shallow-native-list\n"
        "storage: direct-/company-write\n"
    )


def _observe_company_mount(company: str, kind: str, *, expected_rw: bool) -> bool:
    containers = _run(
        [
            "docker",
            "ps",
            "--filter",
            f"label=foundagent.company={company}",
            "--filter",
            f"label=foundagent.kind={kind}",
            "--format",
            "{{.Names}}",
        ],
        check=False,
        timeout=10,
    )
    for name in containers.stdout.splitlines():
        inspected = _run(
            [
                "docker",
                "inspect",
                name,
                "--format",
                '{{range .Mounts}}{{if eq .Destination "/company"}}{{.RW}}{{end}}{{end}}',
            ],
            check=False,
            timeout=10,
        )
        if inspected.returncode == 0 and inspected.stdout.strip() == str(expected_rw).lower():
            return True
    return False


def _wait_for_goal(
    state_root: Path,
    goal_id: str,
    company: str,
    timeout: float,
) -> tuple[dict, dict]:
    deadline = time.monotonic() + timeout
    path = state_root / "ledger" / f"{goal_id}.json"
    previous: tuple[str | None, str | None] | None = None
    live_evidence: dict[str, str | bool | None] = {
        "worker_mount_readwrite": False,
        "verifier_mount_readonly": False,
        "sha256_at_verifying": None,
    }
    while time.monotonic() < deadline:
        goal = read_json(path)
        if isinstance(goal, dict):
            status = (goal.get("status"), goal.get("worker_state"))
            if status != previous:
                print(
                    f"[native-company-e2e] goal={goal_id} "
                    f"status={status[0]} worker={status[1]}",
                    flush=True,
                )
                previous = status
            if not live_evidence["worker_mount_readwrite"]:
                live_evidence["worker_mount_readwrite"] = _observe_company_mount(
                    company, "worker", expected_rw=True
                )
                if live_evidence["worker_mount_readwrite"]:
                    print("[native-company-e2e] observed Worker /company rw=true", flush=True)
            if goal.get("status") == "verifying":
                if not live_evidence["verifier_mount_readonly"]:
                    live_evidence["verifier_mount_readonly"] = _observe_company_mount(
                        company, "verifier", expected_rw=False
                    )
                    if live_evidence["verifier_mount_readonly"]:
                        print(
                            "[native-company-e2e] observed Verifier /company rw=false",
                            flush=True,
                        )
                target = state_root / "company" / TARGET_RELATIVE
                if live_evidence["sha256_at_verifying"] is None and target.is_file():
                    live_evidence["sha256_at_verifying"] = _sha256(target)
            if goal.get("status") in TERMINAL_GOAL_STATES:
                return goal, live_evidence
        for worker_path in (state_root / "workers").glob("worker-*.json"):
            worker = read_json(worker_path)
            if not isinstance(worker, dict):
                continue
            last_result = worker.get("last_result")
            error = last_result.get("error") if isinstance(last_result, dict) else None
            if isinstance(error, str) and any(
                marker in error.lower()
                for marker in ("access token", "refresh token", "log in again", "login required")
            ):
                raise AssertionError(f"Codex credential failed during Worker turn: {error}")
        time.sleep(2)
    raise AssertionError(f"Goal {goal_id} did not finish within {timeout:.0f}s")


def _wait_for_dynamic_shutdown(
    state_root: Path,
    company: str,
    goal_id: str,
    review_id: str,
    timeout: float = 120.0,
) -> None:
    deadline = time.monotonic() + timeout
    final_observation: tuple[object, object, list[str]] | None = None
    while time.monotonic() < deadline:
        goal = read_json(state_root / "ledger" / f"{goal_id}.json")
        review = read_json(state_root / "reviews" / f"{review_id}.json")
        containers = _run(
            [
                "docker",
                "ps",
                "-aq",
                "--filter",
                f"label=foundagent.company={company}",
            ],
            check=False,
            timeout=10,
        )
        container_ids = [line for line in containers.stdout.splitlines() if line.strip()]
        worker_state = goal.get("worker_state") if isinstance(goal, dict) else None
        verifier_state = review.get("instance_state") if isinstance(review, dict) else None
        final_observation = (worker_state, verifier_state, container_ids)
        if worker_state == "stopped" and verifier_state is None and not container_ids:
            return
        time.sleep(1)
    raise AssertionError(f"Dynamic runtimes did not fully stop: {final_observation}")


def _wait_for_run(
    state_root: Path,
    *,
    kind: str,
    key: str,
    value: str,
    timeout: float = 60.0,
) -> Path:
    deadline = time.monotonic() + timeout
    runs = state_root / "telemetry" / "runs"
    while time.monotonic() < deadline:
        for metadata_path in runs.glob("*/metadata.json"):
            metadata = read_json(metadata_path)
            if (
                isinstance(metadata, dict)
                and metadata.get("kind") == kind
                and metadata.get(key) == value
            ):
                return metadata_path.parent
        time.sleep(1)
    raise AssertionError(f"No {kind} run found with {key}={value}")


def _commands(runtime_path: Path) -> list[str]:
    commands: list[str] = []
    for raw_line in runtime_path.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(raw_line)
        except json.JSONDecodeError:
            continue
        if event.get("type") != "item.completed":
            continue
        item = event.get("item")
        if not isinstance(item, dict) or item.get("type") != "command_execution":
            continue
        command = item.get("command")
        if isinstance(command, str):
            commands.append(command)
    return commands


def _touches_company_root(command: str) -> bool:
    # Do not confuse paths such as .../skills/company-state/SKILL.md with the
    # native Company State mount. A real root reference ends at /company or
    # continues with a slash/command delimiter, never a hyphen.
    return bool(re.search(r"/company(?=/|\s|['\";&|)]|$)", command))


def _is_shallow_company_listing(command: str) -> bool:
    if not _touches_company_root(command):
        return False
    if re.search(r"\bls\b[^;&|\n]*\s/company(?:[/'\"\s]|$)", command):
        return True
    if re.search(r"\bfind\s+/company(?:\s|/)", command) and re.search(
        r"-maxdepth\s+[12](?:\s|$)", command
    ):
        return True
    if re.search(r"\btree\b", command) and re.search(r"(?:-L|--level)\s+[12]", command):
        return True
    if re.search(r"\bfd\b|\bfdfind\b", command) and re.search(
        r"(?:-d|--max-depth)\s+[12]", command
    ):
        return True
    return False


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _assert_runtime_behavior(
    worker_run: Path,
    verifier_run: Path,
    company_dir: Path,
    expected: str,
    live_evidence: dict,
) -> dict:
    target = company_dir / TARGET_RELATIVE
    files = sorted(
        path.relative_to(company_dir).as_posix()
        for path in company_dir.rglob("*")
        if path.is_file()
    )
    assert files == [TARGET_RELATIVE.as_posix()]
    assert target.read_text(encoding="utf-8") == expected
    assert not list(company_dir.rglob("MAP.md"))
    assert not list(company_dir.rglob("OVERVIEW.md"))

    worker_runtime = worker_run / "runtime.jsonl"
    verifier_runtime = verifier_run / "runtime.jsonl"
    worker_commands = _commands(worker_runtime)
    verifier_commands = _commands(verifier_runtime)
    all_commands = worker_commands + verifier_commands
    assert not [command for command in all_commands if "/opt/company_state_kit" in command]
    assert not [
        command
        for command in all_commands
        if re.search(r"(?:^|['\";&|]\s*|\bpython3?\s+)company\.py\s", command)
    ]
    company_commands = [command for command in worker_commands if _touches_company_root(command)]
    assert company_commands, "Worker never touched /company"
    assert _is_shallow_company_listing(company_commands[0]), (
        "Worker's first /company command was not a shallow native listing: "
        f"{company_commands[0]}"
    )
    assert any(TARGET_REF in command for command in worker_commands)
    assert any(TARGET_REF in command for command in verifier_commands)
    assert live_evidence["worker_mount_readwrite"] is True
    assert live_evidence["verifier_mount_readonly"] is True
    assert live_evidence["sha256_at_verifying"] == _sha256(target)

    return {
        "company_files": files,
        "sha256": _sha256(target),
        "worker_company_commands": company_commands,
        "verifier_company_commands": [
            command for command in verifier_commands if _touches_company_root(command)
        ],
        "worker_mount_readwrite": True,
        "verifier_mount_readonly": True,
        "company_hash_unchanged_during_verification": True,
    }


def _assert_control_plane_evidence(
    state_root: Path,
    goal: dict,
    review_id: str,
) -> dict:
    review = read_json(state_root / "reviews" / f"{review_id}.json")
    assert isinstance(review, dict)
    assert review["status"] == "passed"
    assert review["verdict"] == "PASS"
    assert review["routed"] is True
    assert "summary" not in review["payload"]
    assert "company_refs" not in review["payload"]
    assert TARGET_REF in review["payload"]["intent"]
    assert TARGET_REF in review["payload"]["acceptance"]

    rows: list[dict] = []
    audit_path = state_root / "telemetry" / "index" / "methods.jsonl"
    for line in audit_path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if isinstance(row, dict):
            rows.append(row)

    def matching_index(method: str, actor_kind: str, *, start: int = 0) -> int:
        for index, row in enumerate(rows[start:], start):
            request = row.get("request")
            actor = row.get("actor")
            if (
                isinstance(request, dict)
                and request.get("method") == method
                and isinstance(actor, dict)
                and actor.get("kind") == actor_kind
                and row.get("response", {}).get("ok") is True
            ):
                if method == "create_goal" and request.get("request_id") != "e2e-native-company-goal":
                    continue
                if method == "submit_result" and actor.get("goal_id") != goal["id"]:
                    continue
                if method == "submit_verdict" and actor.get("review_id") != review_id:
                    continue
                return index
        raise AssertionError(f"Missing audited {actor_kind}.{method}")

    create_index = matching_index("create_goal", "department")
    submit_index = matching_index("submit_result", "worker", start=create_index + 1)
    verdict_index = matching_index("submit_verdict", "verifier", start=submit_index + 1)
    submit_payload = rows[submit_index]["request"]["payload"]
    assert submit_payload == {}
    return {
        "review_status": review["status"],
        "review_verdict": review["verdict"],
        "submit_result_payload": submit_payload,
        "verifier_discovered_company_evidence_from_goal": True,
        "method_sequence": [
            "department.create_goal",
            "worker.submit_result",
            "verifier.submit_verdict",
        ],
    }


def _cleanup(compose_env: dict[str, str], company: str) -> None:
    _compose(
        compose_env,
        "stop",
        "-t",
        "10",
        "worker-manager",
        "verifier-manager",
        "hub",
        timeout=45,
        check=False,
    )
    labelled = _run(
        [
            "docker",
            "ps",
            "-aq",
            "--filter",
            f"label=foundagent.company={company}",
        ],
        check=False,
        timeout=15,
    )
    container_ids = [line for line in labelled.stdout.splitlines() if line.strip()]
    if container_ids:
        _run(["docker", "rm", "-f", *container_ids], check=False, timeout=45)
    _compose(
        compose_env,
        "down",
        "--remove-orphans",
        timeout=60,
        check=False,
    )


@pytest.mark.skipif(
    os.environ.get("RUN_NATIVE_COMPANY_E2E") != "1",
    reason="live Docker/model E2E; run with make e2e-native-company",
)
def test_native_company_folder_worker_to_readonly_verifier() -> None:
    assert _run(["docker", "info"], check=False, timeout=15).returncode == 0
    assert _run(
        ["docker", "image", "inspect", "foundagent/cua-agent:latest"],
        check=False,
        timeout=15,
    ).returncode == 0

    auth_source_account = require_identifier(
        os.environ.get("E2E_AUTH_SOURCE_ACCOUNT", "foundagent"),
        label="auth source account",
    )
    configured_seed = os.environ.get("E2E_CODEX_AUTH_SEED")
    live_host_seed = Path.home() / ".codex" / "auth.json"
    if configured_seed:
        auth_seed = Path(configured_seed).expanduser().resolve()
    elif live_host_seed.is_file():
        # The parked account seed can have a single-use refresh token that an
        # earlier Agent already rotated. Prefer the currently active local
        # Codex login when available, while still copying it only into the
        # throwaway runtime account below.
        auth_seed = live_host_seed
    else:
        auth_seed = REPO / "accounts" / auth_source_account / "codex-auth.json"
    assert auth_seed.is_file() and auth_seed.stat().st_size > 0

    company = f"e2e-native-{uuid.uuid4().hex[:12]}"
    require_identifier(company, label="company")
    state_parent = REPO / "state"
    state_parent.mkdir(parents=True, exist_ok=True)
    state_root = state_parent / company
    state_root.mkdir(mode=0o777)
    runtime_account = require_identifier(f"{company}-runtime", label="runtime account")
    runtime_account_dir = REPO / "accounts" / runtime_account
    runtime_account_dir.mkdir(mode=0o700)
    runtime_auth_seed = runtime_account_dir / "codex-auth.json"
    shutil.copyfile(auth_seed, runtime_auth_seed)
    runtime_auth_seed.chmod(0o600)
    sentinel = f"native-{uuid.uuid4().hex}"
    expected = _expected_content(sentinel)
    compose_env = {
        **os.environ,
        "PWD": str(REPO),
        "COMPANY": company,
        "ACCOUNT": runtime_account,
        "WORKER_TURN_TIMEOUT_SECS": os.environ.get("WORKER_TURN_TIMEOUT_SECS", "900"),
        "VERIFIER_TURN_TIMEOUT_SECS": os.environ.get("VERIFIER_TURN_TIMEOUT_SECS", "900"),
    }
    keep_state = os.environ.get("E2E_KEEP_STATE") == "1"
    started = False
    try:
        print(f"[native-company-e2e] company={company}", flush=True)
        _seed_active_department(state_root)
        # Match `make shared`: dynamic Agent containers run as uid 1000 and
        # need the bind-mounted Company State tree to be writable.
        for path in (state_root, *state_root.rglob("*")):
            path.chmod(0o777 if path.is_dir() else 0o666)
        print("[native-company-e2e] starting hub + Worker/Verifier managers", flush=True)
        control_image_exists = _run(
            ["docker", "image", "inspect", "foundagent/control-plane:latest"],
            check=False,
            timeout=15,
        ).returncode == 0
        build_mode = "--no-build" if control_image_exists else "--build"
        _compose(
            compose_env,
            "up",
            "-d",
            build_mode,
            "hub",
            "worker-manager",
            "verifier-manager",
            timeout=1800,
        )
        started = True
        _wait_for_hub(company)
        goal = _create_live_goal(company, sentinel)
        goal_id = goal["id"]
        print(f"[native-company-e2e] created goal={goal_id}", flush=True)
        final_goal, live_evidence = _wait_for_goal(
            state_root,
            goal_id,
            company,
            timeout=float(os.environ.get("NATIVE_COMPANY_E2E_TIMEOUT_SECS", "1200")),
        )
        assert final_goal["status"] == "done", final_goal
        review_id = final_goal["last_review_id"]

        worker_run = _wait_for_run(
            state_root,
            kind="worker_turn",
            key="goal_id",
            value=goal_id,
        )
        verifier_run = _wait_for_run(
            state_root,
            kind="verifier_review",
            key="review_id",
            value=review_id,
        )
        _wait_for_dynamic_shutdown(state_root, company, goal_id, review_id)
        evidence = _assert_runtime_behavior(
            worker_run,
            verifier_run,
            state_root / "company",
            expected,
            live_evidence,
        )
        control_evidence = _assert_control_plane_evidence(
            state_root,
            final_goal,
            review_id,
        )

        # Prove the native leaf survives an orchestration-process restart and is
        # visible to a fresh read-only process through a new bind mount.
        before_restart = evidence["sha256"]
        _compose(compose_env, "restart", "hub", timeout=90)
        _wait_for_hub(company)
        target_host = state_root / "company" / TARGET_RELATIVE
        assert _sha256(target_host) == before_restart
        fresh_reader = _run(
            [
                "docker",
                "run",
                "--rm",
                "-v",
                f"{state_root / 'company'}:/company:ro",
                "alpine:latest",
                "sha256sum",
                TARGET_REF,
            ],
            timeout=60,
        )
        assert fresh_reader.stdout.split()[0] == before_restart

        report = {
            "company": company,
            "goal_id": goal_id,
            "review_id": review_id,
            "worker_run": worker_run.name,
            "verifier_run": verifier_run.name,
            "persistence_after_hub_restart": True,
            "dynamic_containers_removed": True,
            **evidence,
            **control_evidence,
        }
        report_path = os.environ.get("NATIVE_COMPANY_E2E_REPORT")
        if report_path:
            Path(report_path).write_text(
                json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        print(
            "[native-company-e2e] PASS\n"
            + json.dumps(report, ensure_ascii=False, indent=2),
            flush=True,
        )
    except Exception:
        if started:
            logs = _compose(
                compose_env,
                "logs",
                "--no-color",
                "--tail",
                "200",
                "hub",
                "worker-manager",
                "verifier-manager",
                timeout=30,
                check=False,
            )
            print("[native-company-e2e] service logs:\n" + logs.stdout, flush=True)
        raise
    finally:
        _cleanup(compose_env, company)
        if keep_state:
            print(f"[native-company-e2e] kept state at {state_root}", flush=True)
        else:
            resolved = state_root.resolve()
            assert resolved.parent == state_parent.resolve()
            assert resolved.name.startswith("e2e-native-")
            shutil.rmtree(resolved, ignore_errors=True)
        resolved_account = runtime_account_dir.resolve()
        assert resolved_account.parent == (REPO / "accounts").resolve()
        assert resolved_account.name.startswith("e2e-native-")
        shutil.rmtree(resolved_account, ignore_errors=True)
