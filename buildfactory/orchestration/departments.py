"""Fixed Department spec directory and no-retirement V7 controller."""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from pathlib import Path

import yaml

from orchestration.objective_store import ObjectiveStore
from orchestration.runtime_store import atomic_write_json, file_lock, read_json


class DepartmentError(ValueError):
    pass


@dataclass(frozen=True)
class DepartmentTemplate:
    id: str
    public_name: str
    public_description: str
    agent_spec: str
    charter: str
    heartbeat_secs: int

    def public_option(self) -> dict[str, str]:
        return {
            "id": self.id,
            "name": self.public_name,
            "description": self.public_description,
        }


class DepartmentCatalog:
    ALLOWED_IDS = ("strategist", "researcher", "builder", "growth")

    def __init__(self, templates: dict[str, DepartmentTemplate]):
        if tuple(templates) != self.ALLOWED_IDS:
            raise DepartmentError(
                f"catalog must contain exactly {self.ALLOWED_IDS}, got {tuple(templates)}"
            )
        self._templates = dict(templates)

    @classmethod
    def load(cls, directory: str | Path) -> "DepartmentCatalog":
        directory = Path(directory)
        if not directory.is_dir():
            raise DepartmentError(f"Department specs directory does not exist: {directory}")
        directory = directory.resolve()

        expected_files = {f"{template_id}.yaml" for template_id in cls.ALLOWED_IDS}
        actual_files = {
            path.name
            for pattern in ("*.yaml", "*.yml")
            for path in directory.glob(pattern)
        }
        if actual_files != expected_files:
            raise DepartmentError(
                "Department specs directory must contain exactly "
                f"{sorted(expected_files)}, got {sorted(actual_files)}"
            )

        agents_root = directory.parent
        templates: dict[str, DepartmentTemplate] = {}
        for template_id in cls.ALLOWED_IDS:
            path = directory / f"{template_id}.yaml"
            try:
                row = yaml.safe_load(path.read_text(encoding="utf-8"))
            except (OSError, yaml.YAMLError) as exc:
                raise DepartmentError(f"cannot load Department spec {path}: {exc}") from exc
            if row is None:
                row = {}
            if not isinstance(row, dict):
                raise DepartmentError(f"Department spec {template_id} must be a mapping")

            name = cls._required_text(row, "name", template_id)
            if name != template_id or path.stem != template_id:
                raise DepartmentError(
                    f"Department spec {template_id} name must match its file and fixed id"
                )
            public_name = cls._required_text(row, "public_name", template_id)
            public_description = cls._required_text(
                row, "public_description", template_id
            )
            heartbeat = row.get("heartbeat_secs")
            if type(heartbeat) is not int or heartbeat <= 0:
                raise DepartmentError(
                    f"Department spec {template_id} heartbeat_secs must be a positive integer"
                )

            system_prompt = cls._required_text(row, "system_prompt", template_id)
            if Path(system_prompt).is_absolute():
                raise DepartmentError(
                    f"Department spec {template_id} system_prompt must be relative"
                )
            charter_path = (path.parent / system_prompt).resolve()
            try:
                charter = charter_path.relative_to(agents_root).as_posix()
            except ValueError as exc:
                raise DepartmentError(
                    f"Department spec {template_id} system_prompt must stay inside agents/"
                ) from exc

            try:
                agent_spec = path.resolve().relative_to(agents_root).as_posix()
            except ValueError as exc:
                raise DepartmentError(
                    f"Department spec {template_id} file must stay inside agents/"
                ) from exc

            templates[template_id] = DepartmentTemplate(
                id=template_id,
                public_name=public_name,
                public_description=public_description,
                agent_spec=agent_spec,
                charter=charter,
                heartbeat_secs=heartbeat,
            )
        return cls(templates)

    @staticmethod
    def _required_text(row: dict, field: str, template_id: str) -> str:
        value = row.get(field)
        if not isinstance(value, str) or not value.strip():
            raise DepartmentError(
                f"Department spec {template_id} {field} must be a non-empty string"
            )
        return value

    def options(self) -> list[dict[str, str]]:
        return [self._templates[key].public_option() for key in self.ALLOWED_IDS]

    def internal(self, template_id: str) -> DepartmentTemplate:
        try:
            return self._templates[template_id]
        except KeyError as exc:
            raise DepartmentError(f"unknown Department option: {template_id}") from exc


class DepartmentController:
    def __init__(
        self,
        root: str | Path,
        *,
        catalog: DepartmentCatalog,
        objectives: ObjectiveStore,
    ):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.catalog = catalog
        self.objectives = objectives
        self._lock_path = self.root / ".departments.lock"

    @staticmethod
    def _request_id(request_id: str) -> str:
        return "department-" + hashlib.sha256(request_id.encode("utf-8")).hexdigest()[:16]

    def _request_path(self, request_id: str) -> Path:
        return self.root / "requests" / f"{request_id}.json"

    def _department_path(self, department_id: str) -> Path:
        return self.root / f"{department_id}.json"

    def list_options(self) -> list[dict[str, str]]:
        return self.catalog.options()

    def list_departments(self) -> list[dict]:
        rows = []
        for template_id in self.catalog.ALLOWED_IDS:
            row = read_json(self._department_path(template_id))
            if isinstance(row, dict):
                rows.append(row)
        return rows

    def get(self, department_id: str) -> dict:
        row = read_json(self._department_path(department_id))
        if not isinstance(row, dict):
            raise DepartmentError(f"Department is not active: {department_id}")
        return row

    def request_creation(
        self,
        *,
        option_id: str,
        initial_objective: str,
        requested_by: str,
        request_id: str,
    ) -> dict:
        if requested_by != "ceo":
            raise DepartmentError("only CEO can create a Department")
        template = self.catalog.internal(option_id)
        if self.objectives.current("ceo") is None:
            raise DepartmentError("Company Objective must be active before creating Departments")
        creation_id = self._request_id(request_id)
        path = self._request_path(creation_id)
        with file_lock(self._lock_path):
            existing = read_json(path)
            if isinstance(existing, dict):
                return existing
            if self._department_path(option_id).is_file():
                raise DepartmentError(f"Department already exists: {option_id}")
            for candidate in (self.root / "requests").glob("department-*.json"):
                row = read_json(candidate)
                if (
                    isinstance(row, dict)
                    and row.get("option_id") == option_id
                    and row.get("status") != "objective_rejected"
                ):
                    raise DepartmentError(f"Department creation already in progress: {option_id}")
            proposal = self.objectives.propose(
                actor_id=option_id,
                objective_kind="department",
                text=initial_objective,
                requested_by="ceo",
                request_id=f"{request_id}:initial-objective",
            )
            now = time.time()
            row = {
                "id": creation_id,
                "option_id": option_id,
                "objective_proposal_id": proposal["id"],
                "objective_review_id": proposal["review_id"],
                "status": "objective_reviewing",
                "created_at": now,
                "updated_at": now,
            }
            atomic_write_json(path, row)
            return row

    def reconcile_creation(self, creation_id: str) -> dict:
        path = self._request_path(creation_id)
        with file_lock(self._lock_path):
            row = read_json(path)
            if not isinstance(row, dict):
                raise DepartmentError(f"no such Department creation request: {creation_id}")
            if row["status"] != "objective_reviewing":
                return row
            proposal = self.objectives.apply_review(row["objective_review_id"])
            if proposal["status"] == "rejected":
                row["status"] = "objective_rejected"
                row["reason"] = proposal.get("reason")
                row["updated_at"] = time.time()
                atomic_write_json(path, row)
                return row
            template = self.catalog.internal(row["option_id"])
            command = {
                "command_id": f"provision:{creation_id}",
                "action": "provision_department",
                "creation_id": creation_id,
                "template_id": template.id,
            }
            atomic_write_json(self.root / "commands" / f"{creation_id}.json", command)
            row["status"] = "provisioning"
            row["updated_at"] = time.time()
            atomic_write_json(path, row)
            return row

    def mark_active(self, creation_id: str, *, service_name: str) -> dict:
        path = self._request_path(creation_id)
        with file_lock(self._lock_path):
            request = read_json(path)
            if not isinstance(request, dict):
                raise DepartmentError("Department request does not exist")
            if (
                request.get("status") == "active"
                and self._department_path(request["option_id"]).is_file()
            ):
                return self.get(request["option_id"])
            if request.get("status") not in ("provisioning", "provision_failed"):
                raise DepartmentError("Department request is not provisioning")
            department_id = request["option_id"]
            if self._department_path(department_id).is_file():
                return self.get(department_id)
            template = self.catalog.internal(department_id)
            now = time.time()
            department = {
                "id": department_id,
                "template_id": template.id,
                "name": template.public_name,
                "status": "active",
                "service_name": service_name,
                "heartbeat_secs": template.heartbeat_secs,
                "created_at": now,
                "updated_at": now,
            }
            atomic_write_json(self._department_path(department_id), department)
            request["status"] = "active"
            request["service_name"] = service_name
            request.pop("reason", None)
            request["updated_at"] = now
            atomic_write_json(path, request)
            return department

    def mark_provision_failed(self, creation_id: str, *, reason: str) -> dict:
        path = self._request_path(creation_id)
        with file_lock(self._lock_path):
            row = read_json(path)
            if not isinstance(row, dict):
                raise DepartmentError(f"no such Department creation request: {creation_id}")
            if row.get("status") == "active":
                return row
            if row.get("status") not in ("provisioning", "provision_failed"):
                raise DepartmentError("Department request is not provisioning")
            # This is an observable retry state, not a terminal lifecycle or
            # permission to submit a second creation request. The provisioner
            # keeps the same command and converges on the same container.
            row["status"] = "provision_failed"
            row["reason"] = reason
            row["provision_attempts"] = int(row.get("provision_attempts", 0)) + 1
            row["updated_at"] = time.time()
            atomic_write_json(path, row)
            return row
