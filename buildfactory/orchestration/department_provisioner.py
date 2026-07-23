"""Fixed-template V7 Department provisioner (no retirement surface)."""

from __future__ import annotations

import hashlib
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from agent.runner import AGENT_HOME_MOUNT
from orchestration.container_logs import ResidentLogSnapshotter
from orchestration.control_client import BoundActor, HubClient
from orchestration.departments import DepartmentCatalog, DepartmentTemplate
from orchestration.runtime_store import CompanyLayout, atomic_write_json, read_json
from orchestration.runtime_materialization import (
    account_package_docker_args,
    prepare_container_tree,
)


class DepartmentProvisionError(RuntimeError):
    pass


@dataclass(frozen=True)
class DepartmentDefinition:
    company_id: str
    department_id: str
    container_name: str
    home: Path
    company_dir: Path
    template: DepartmentTemplate


class DepartmentBackend(Protocol):
    def ensure(self, definition: DepartmentDefinition) -> str: ...


class DockerDepartmentBackend:
    def __init__(
        self,
        *,
        repo: str | Path,
        company_id: str,
        account_id: str | None = None,
        image: str | None = None,
        network: str | None = None,
    ):
        self.repo = Path(repo).resolve()
        self.company_id = company_id
        self.account_id = account_id or company_id
        self.image = image or os.environ.get("CUA_AGENT_IMAGE", "foundagent/cua-agent:latest")
        self.network = network or f"{company_id}_default"

    @staticmethod
    def _run(args: list[str]) -> subprocess.CompletedProcess:
        return subprocess.run(args, capture_output=True, text=True)

    def ensure(self, definition: DepartmentDefinition) -> str:
        existing = self._run(
            [
                "docker",
                "inspect",
                "-f",
                '{{index .Config.Labels "foundagent.template"}}',
                definition.container_name,
            ]
        )
        if existing.returncode == 0:
            if existing.stdout.strip() != definition.template.id:
                raise DepartmentProvisionError("existing Department container has wrong template")
            started = self._run(["docker", "start", definition.container_name])
            if started.returncode != 0:
                raise DepartmentProvisionError(
                    f"docker start failed: {started.stderr.strip()}"
                )
            return definition.container_name

        definition.home.mkdir(parents=True, exist_ok=True)
        prepare_container_tree(definition.home)
        args = [
            "docker",
            "run",
            "-d",
            "--restart",
            "unless-stopped",
            "--name",
            definition.container_name,
            "--network",
            self.network,
            "--label",
            f"foundagent.company={definition.company_id}",
            "--label",
            "foundagent.kind=department",
            "--label",
            f"foundagent.department={definition.department_id}",
            "--label",
            f"foundagent.template={definition.template.id}",
            "-v",
            f"{definition.home}:{AGENT_HOME_MOUNT}",
            "-v",
            f"{definition.company_dir}:/company",
            "-v",
            f"{self.repo / 'agent'}:/opt/foundagent-orch/agent:ro",
            "-v",
            f"{self.repo / 'agents'}:/opt/foundagent-orch/agents:ro",
            "-v",
            f"{self.repo / 'orchestration'}:/opt/foundagent-orch/orchestration:ro",
            "-v",
            f"{self.repo / 'vm' / 'docker' / 'agent_startup.sh'}:/dockerstartup/custom_startup.sh:ro",
            "-e",
            "PYTHONPATH=/opt/foundagent-orch",
            "-e",
            f"AGENT_KEY={definition.department_id}",
            "-e",
            "AGENT_KIND=department",
            "-e",
            f"DEPARTMENT_ID={definition.department_id}",
            "-e",
            f"AGENT_SPEC=/opt/foundagent-orch/agents/{definition.template.agent_spec}",
            "-e",
            f"AGENT_CHARTER=/opt/foundagent-orch/agents/{definition.template.charter}",
            "-e",
            f"AGENT_HEARTBEAT_SECS={definition.template.heartbeat_secs}",
            "-e",
            "HUB_URL=http://hub:8910",
            "-e",
            f"CLAUDE_CONFIG_DIR={AGENT_HOME_MOUNT}",
            "-e",
            f"CODEX_HOME={AGENT_HOME_MOUNT}/codex",
            "-e",
            f"AGENT_SESSION_FILE={AGENT_HOME_MOUNT}/session_id",
            "-e",
            "CLAUDE_CODE_DISABLE_AUTO_MEMORY=1",
        ]
        account_dir = self.repo / "accounts" / self.account_id
        args += account_package_docker_args(account_dir)
        args += [self.image, "--wait"]
        result = self._run(args)
        if result.returncode != 0:
            raise DepartmentProvisionError(f"docker run failed: {result.stderr.strip()}")
        return definition.container_name


class DepartmentProvisionerService:
    def __init__(
        self,
        layout: CompanyLayout,
        *,
        company_id: str,
        catalog: DepartmentCatalog,
        backend: DepartmentBackend,
        hub: HubClient,
    ):
        self.layout = layout
        self.company_id = company_id
        self.catalog = catalog
        self.backend = backend
        self.hub = hub
        (layout.departments / "receipts").mkdir(parents=True, exist_ok=True)

    def _receipt(self, command_id: str) -> Path:
        digest = hashlib.sha256(command_id.encode("utf-8")).hexdigest()
        return self.layout.departments / "receipts" / f"{digest}.json"

    def process_once(self) -> int:
        processed = 0
        for path in sorted((self.layout.departments / "commands").glob("*.json")):
            command = read_json(path)
            if not isinstance(command, dict) or not isinstance(command.get("command_id"), str):
                continue
            if self._receipt(command["command_id"]).is_file():
                continue
            try:
                completed = self._process(command)
            except Exception as exc:  # noqa: BLE001 — one command must not block the others
                print(
                    f"[department-provisioner] command {command['command_id']} failed: {exc!r}",
                    flush=True,
                )
                continue
            if completed:
                processed += 1
        return processed

    def _process(self, command: dict) -> bool:
        if set(command) != {"command_id", "action", "creation_id", "template_id"}:
            raise DepartmentProvisionError("invalid Department command schema")
        if command["action"] != "provision_department":
            raise DepartmentProvisionError("Department provisioner supports only creation")
        template = self.catalog.internal(command["template_id"])
        request = read_json(
            self.layout.departments / "requests" / f"{command['creation_id']}.json"
        )
        if not isinstance(request, dict) or request.get("status") not in (
            "provisioning",
            "provision_failed",
        ):
            raise DepartmentProvisionError("creation request is not provisioning")
        if request.get("option_id") != template.id:
            raise DepartmentProvisionError("command template does not match creation request")
        definition = DepartmentDefinition(
            company_id=self.company_id,
            department_id=template.id,
            container_name=f"{self.company_id}-{template.id}",
            home=self.layout.sessions / template.id,
            company_dir=self.layout.company,
            template=template,
        )
        try:
            service_name = self.backend.ensure(definition)
        except Exception as exc:  # noqa: BLE001 — deterministic failure reaches CEO
            # The failure notification is idempotent, while the command stays
            # unreceipted and is retried with the same Department/container.
            self.hub.call(
                "department_provision_failed",
                {"creation_id": command["creation_id"], "reason": str(exc)},
                request_id=f"department-provision-failed:{command['command_id']}",
            )
            return False
        # Keep callback transport failures out of the provision-failure path:
        # the container may already be healthy. A later scan re-runs ensure()
        # idempotently and retries this same request id.
        result = self.hub.call(
            "department_started",
            {"creation_id": command["creation_id"], "service_name": service_name},
            request_id=f"department-started:{command['command_id']}",
        )
        atomic_write_json(
            self._receipt(command["command_id"]),
            {"command_id": command["command_id"], "processed_at": time.time(), "result": result},
        )
        return True


def main() -> None:
    repo = Path(os.environ.get("FOUNDAGENT_HOST_REPO") or Path(__file__).resolve().parents[1])
    company_id = os.environ.get("COMPANY", "v7-test")
    layout = CompanyLayout.initialize(
        os.environ.get("COMPANY_STATE_ROOT") or repo / "state" / company_id
    )
    catalog = DepartmentCatalog.load(repo / "agents" / "departments")
    backend = DockerDepartmentBackend(
        repo=repo,
        company_id=company_id,
        account_id=os.environ.get("ACCOUNT") or company_id,
        network=os.environ.get("COMPANY_NETWORK") or f"{company_id}_default",
    )
    hub = HubClient(
        actor=BoundActor("manager", "department-provisioner"),
        timeout=float(os.environ.get("HUB_CLIENT_TIMEOUT_SECS", "30")),
    )
    service = DepartmentProvisionerService(
        layout,
        company_id=company_id,
        catalog=catalog,
        backend=backend,
        hub=hub,
    )
    poll = float(os.environ.get("DEPARTMENT_PROVISIONER_POLL_SECS", "0.5"))
    print(f"[department-provisioner] ready company={company_id}", flush=True)
    snapshotter = ResidentLogSnapshotter(
        layout.telemetry / "services" / "agents",
        company_id=company_id,
        run_command=backend._run,
    )
    next_log_snapshot = 0.0
    while True:
        try:
            service.process_once()
        except Exception as exc:  # noqa: BLE001 — bad command is visible, service survives
            print(f"[department-provisioner] scan failed: {exc!r}", flush=True)
        now = time.monotonic()
        if now >= next_log_snapshot:
            try:
                snapshotter.snapshot_once()
            except Exception as exc:  # noqa: BLE001 — logs cannot stop provisioning
                print(
                    f"[department-provisioner] resident log snapshot failed: {exc!r}",
                    flush=True,
                )
            next_log_snapshot = now + float(
                os.environ.get("RESIDENT_LOG_SNAPSHOT_SECS", "5")
            )
        time.sleep(max(0.05, poll))


if __name__ == "__main__":
    main()
