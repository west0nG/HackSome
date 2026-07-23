"""Central persistence owner for one Idea workflow run."""

from __future__ import annotations

import re
import threading
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

from hacksome.config import CodexConfig
from hacksome.models import CodexResult
from hacksome.state import (
    StateError,
    append_jsonl,
    atomic_write_json,
    atomic_write_text,
    read_json_object,
    read_jsonl,
    sha256_file,
    sha256_text,
)


RUN_SCHEMA_VERSION = 1
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True, slots=True)
class TaskPaths:
    root: Path
    workspace: Path
    raw: Path
    prompt: Path
    request: Path
    result: Path
    output: Path


class RunHub:
    """Persist prompts, Sessions, artifacts, decisions, and run state."""

    def __init__(self, run_dir: str | Path) -> None:
        self.run_dir = Path(run_dir).expanduser().resolve()
        self.state_path = self.run_dir / "run.json"
        self.events_path = self.run_dir / "events.jsonl"
        self.decisions_path = self.run_dir / "decisions.jsonl"
        self._lock = threading.RLock()
        if not self.state_path.is_file():
            raise StateError(f"run does not exist: {self.run_dir}")

    @classmethod
    def create(
        cls,
        challenge: str,
        runs_dir: str | Path,
        *,
        settings: Mapping[str, Any],
        codex_config: CodexConfig,
        run_id: str | None = None,
    ) -> "RunHub":
        if not isinstance(challenge, str) or not challenge.strip():
            raise ValueError("challenge must not be empty")
        normalized_id = run_id or cls._generated_run_id(challenge)
        if not _SAFE_ID.fullmatch(normalized_id):
            raise ValueError(
                "run_id must contain only letters, numbers, '.', '_' or '-'"
            )
        root = Path(runs_dir).expanduser().resolve() / normalized_id
        if root.exists():
            raise StateError(f"run directory already exists: {root}")
        (root / "input").mkdir(parents=True)
        (root / "tasks").mkdir()
        (root / "artifacts").mkdir()
        challenge_path = root / "input" / "challenge.md"
        atomic_write_text(challenge_path, challenge)
        now = utc_now()
        challenge_sha256 = sha256_text(challenge)
        state = {
            "schema_version": RUN_SCHEMA_VERSION,
            "run_id": normalized_id,
            "status": "created",
            "current_stage": None,
            "created_at": now,
            "updated_at": now,
            "input": {
                "path": "input/challenge.md",
                "sha256": challenge_sha256,
            },
            "settings": dict(settings),
            "codex_config": asdict(codex_config),
            "tasks": {},
            "artifacts": {},
            "idea_card_ids": [],
        }
        atomic_write_json(root / "run.json", state)
        atomic_write_text(root / "events.jsonl", "")
        atomic_write_text(root / "decisions.jsonl", "")
        hub = cls(root)
        hub._event(
            "run.created",
            event_id="run:created",
            data={"challenge_sha256": challenge_sha256},
        )
        return hub

    @staticmethod
    def _generated_run_id(challenge: str) -> str:
        stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        return f"idea-{stamp}-{sha256_text(challenge)[:8]}"

    @property
    def run_id(self) -> str:
        value = self.load_state().get("run_id")
        if not isinstance(value, str):
            raise StateError("run.json has no valid run_id")
        return value

    def load_state(self) -> dict[str, Any]:
        state = read_json_object(self.state_path)
        if state.get("schema_version") != RUN_SCHEMA_VERSION:
            raise StateError("unsupported run schema version")
        return state

    def challenge(self) -> str:
        state = self.load_state()
        input_data = _object(state.get("input"), "run input")
        path = self._resolve_relative(_string(input_data.get("path"), "input path"))
        text = path.read_text(encoding="utf-8")
        if sha256_text(text) != input_data.get("sha256"):
            raise StateError("challenge input hash does not match run.json")
        return text

    def set_run_status(self, status: str, *, stage: str | None = None) -> None:
        if status not in {"created", "running", "completed", "failed"}:
            raise ValueError(f"unsupported run status: {status}")

        def update(state: dict[str, Any]) -> None:
            state["status"] = status
            state["current_stage"] = stage

        self._mutate(update)
        self._event(
            "run.status",
            event_id=f"run:status:{status}:{stage or 'none'}",
            data={"status": status, "stage": stage},
        )

    def task_paths(self, task_id: str) -> TaskPaths:
        if not _SAFE_ID.fullmatch(task_id):
            raise ValueError(f"unsafe task id: {task_id!r}")
        root = self.run_dir / "tasks" / task_id
        return TaskPaths(
            root=root,
            workspace=root / "workspace",
            raw=root / "raw",
            prompt=root / "prompt.md",
            request=root / "request.json",
            result=root / "result.json",
            output=root / "output.json",
        )

    def begin_task(
        self,
        *,
        task_id: str,
        stage: str,
        prompt: str,
        prompt_metadata: Mapping[str, Any],
        output_schema: Path,
        web_search: bool,
        parent_refs: Sequence[str],
    ) -> TaskPaths:
        paths = self.task_paths(task_id)
        if paths.root.exists():
            raise StateError(f"task already exists: {task_id}")
        paths.workspace.mkdir(parents=True)
        paths.raw.mkdir()
        atomic_write_text(paths.raw / "stdout.jsonl", "")
        atomic_write_text(paths.raw / "stderr.jsonl", "")
        atomic_write_text(paths.prompt, prompt)
        request = {
            "task_id": task_id,
            "stage": stage,
            "status": "running",
            "created_at": utc_now(),
            "web_search": web_search,
            "parent_refs": list(parent_refs),
            "prompt": {
                **dict(prompt_metadata),
                "path": self._relative(paths.prompt),
                "sha256": sha256_text(prompt),
            },
            "output_schema": {
                "name": output_schema.name,
                "sha256": sha256_file(output_schema),
            },
        }
        atomic_write_json(paths.request, request)
        request_sha256 = sha256_file(paths.request)

        def update(state: dict[str, Any]) -> None:
            tasks = _object(state.get("tasks"), "tasks")
            if task_id in tasks:
                raise StateError(f"task already registered: {task_id}")
            tasks[task_id] = {
                "task_id": task_id,
                "stage": stage,
                "status": "running",
                "request_path": self._relative(paths.request),
                "request_sha256": request_sha256,
                "prompt_path": self._relative(paths.prompt),
                "prompt_sha256": sha256_text(prompt),
                "parent_refs": list(parent_refs),
                "web_search": web_search,
            }
            state["current_stage"] = stage

        self._mutate(update)
        self._event(
            "task.started",
            event_id=f"task:{task_id}:started",
            data={"task_id": task_id, "stage": stage},
        )
        return paths

    def finish_task(self, result: CodexResult) -> None:
        paths = self.task_paths(result.task_id)
        if not paths.request.is_file():
            raise StateError(f"task was not started: {result.task_id}")
        atomic_write_json(paths.output, result.structured_output)
        error: dict[str, Any] | None = None
        if result.error is not None:
            error = {
                "kind": result.error.kind.value,
                "message": result.error.message,
                "retryable": result.error.retryable,
                "returncode": result.error.returncode,
            }
        payload = {
            "task_id": result.task_id,
            "status": result.status.value,
            "session_id": result.session_id,
            "attempts": result.attempts,
            "usage": result.usage,
            "started_at": result.started_at,
            "finished_at": result.finished_at,
            "duration_seconds": result.duration_seconds,
            "returncode": result.returncode,
            "error": error,
            "output_path": self._relative(paths.output),
            "raw_logs": {
                "stdout": self._relative(result.logs.stdout),
                "stderr": self._relative(result.logs.stderr),
                "last_message": self._relative(result.logs.last_message),
            },
        }
        atomic_write_json(paths.result, payload)
        output_sha256 = sha256_file(paths.output)
        result_sha256 = sha256_file(paths.result)

        def update(state: dict[str, Any]) -> None:
            tasks = _object(state.get("tasks"), "tasks")
            task = _object(tasks.get(result.task_id), f"task {result.task_id}")
            task.update(
                {
                    "status": result.status.value,
                    "result_path": self._relative(paths.result),
                    "result_sha256": result_sha256,
                    "output_path": self._relative(paths.output),
                    "output_sha256": output_sha256,
                    "session_id": result.session_id,
                }
            )

        self._mutate(update)
        self._event(
            "task.finished",
            event_id=f"task:{result.task_id}:finished",
            data={
                "task_id": result.task_id,
                "status": result.status.value,
                "session_id": result.session_id,
            },
        )

    def fail_task(self, task_id: str, error: BaseException) -> None:
        """Persist a runner/preflight exception that occurred after begin_task."""

        paths = self.task_paths(task_id)
        payload = {
            "task_id": task_id,
            "status": "failed",
            "session_id": None,
            "attempts": 0,
            "usage": {},
            "started_at": None,
            "finished_at": utc_now(),
            "duration_seconds": None,
            "returncode": None,
            "error": {"kind": type(error).__name__, "message": str(error)},
            "output_path": None,
            "raw_logs": {
                "stdout": self._relative(paths.raw / "stdout.jsonl"),
                "stderr": self._relative(paths.raw / "stderr.jsonl"),
                "last_message": None,
            },
        }
        atomic_write_json(paths.result, payload)
        result_sha256 = sha256_file(paths.result)

        def update(state: dict[str, Any]) -> None:
            tasks = _object(state.get("tasks"), "tasks")
            task = _object(tasks.get(task_id), f"task {task_id}")
            task.update(
                {
                    "status": "failed",
                    "result_path": self._relative(paths.result),
                    "result_sha256": result_sha256,
                    "session_id": None,
                }
            )

        self._mutate(update)
        self._event(
            "task.finished",
            event_id=f"task:{task_id}:finished",
            data={"task_id": task_id, "status": "failed", "session_id": None},
        )

    def invalidate_task(self, task_id: str, error: BaseException) -> None:
        """Mark a Codex-successful task failed when publication validation fails."""

        paths = self.task_paths(task_id)
        payload = read_json_object(paths.result)
        payload["status"] = "failed"
        payload["validation_error"] = {
            "kind": type(error).__name__,
            "message": str(error),
        }
        atomic_write_json(paths.result, payload)
        result_sha256 = sha256_file(paths.result)

        def update(state: dict[str, Any]) -> None:
            tasks = _object(state.get("tasks"), "tasks")
            task = _object(tasks.get(task_id), f"task {task_id}")
            task["status"] = "failed"
            task["result_sha256"] = result_sha256

        self._mutate(update)
        self._event(
            "task.invalidated",
            event_id=f"task:{task_id}:invalidated",
            data={
                "task_id": task_id,
                "kind": type(error).__name__,
                "message": str(error),
            },
        )

    def publish_artifact(
        self,
        *,
        artifact_id: str,
        artifact_type: str,
        relative_path: str,
        content: str,
        task_id: str | None,
        source_refs: Sequence[str] = (),
        metadata: Mapping[str, Any] | None = None,
    ) -> str:
        if not _SAFE_ID.fullmatch(artifact_id):
            raise ValueError(f"unsafe artifact id: {artifact_id!r}")
        destination = self._resolve_relative(relative_path)
        if destination.exists():
            raise StateError(f"artifact path already exists: {relative_path}")
        atomic_write_text(destination, content)
        record = {
            "artifact_id": artifact_id,
            "artifact_type": artifact_type,
            "path": relative_path,
            "sha256": sha256_text(content),
            "task_id": task_id,
            "source_refs": list(source_refs),
            "metadata": dict(metadata or {}),
            "created_at": utc_now(),
        }

        def update(state: dict[str, Any]) -> None:
            artifacts = _object(state.get("artifacts"), "artifacts")
            if artifact_id in artifacts:
                raise StateError(f"artifact already exists: {artifact_id}")
            artifacts[artifact_id] = record

        self._mutate(update)
        self._event(
            "artifact.published",
            event_id=f"artifact:{artifact_id}:published",
            data={"artifact_id": artifact_id, "artifact_type": artifact_type},
        )
        return artifact_id

    def read_artifact(self, artifact_id: str) -> str:
        state = self.load_state()
        artifacts = _object(state.get("artifacts"), "artifacts")
        record = _object(artifacts.get(artifact_id), f"artifact {artifact_id}")
        path = self._resolve_relative(_string(record.get("path"), "artifact path"))
        content = path.read_text(encoding="utf-8")
        if sha256_text(content) != record.get("sha256"):
            raise StateError(f"artifact hash mismatch: {artifact_id}")
        return content

    def record_decision(
        self,
        *,
        decision_id: str,
        gate: str,
        candidate_ref: str,
        decision: str,
        review_ref: str,
        task_id: str,
    ) -> None:
        if decision not in {"pass", "reject"}:
            raise ValueError(f"unsupported decision: {decision}")
        append_jsonl(
            self.decisions_path,
            {
                "decision_id": decision_id,
                "gate": gate,
                "candidate_ref": candidate_ref,
                "decision": decision,
                "review_ref": review_ref,
                "task_id": task_id,
                "created_at": utc_now(),
            },
            id_field="decision_id",
        )

    def set_idea_cards(self, artifact_ids: Sequence[str]) -> None:
        def update(state: dict[str, Any]) -> None:
            state["idea_card_ids"] = list(artifact_ids)

        self._mutate(update)

    def inspect(self) -> dict[str, Any]:
        state = self.load_state()
        tasks = _object(state.get("tasks"), "tasks")
        counts: dict[str, int] = {}
        for raw in tasks.values():
            task = _object(raw, "task")
            status = _string(task.get("status"), "task status")
            counts[status] = counts.get(status, 0) + 1
        decisions = read_jsonl(self.decisions_path)
        return {
            "run_id": state.get("run_id"),
            "status": state.get("status"),
            "current_stage": state.get("current_stage"),
            "task_counts": counts,
            "decision_count": len(decisions),
            "idea_card_count": len(state.get("idea_card_ids", [])),
            "run_dir": str(self.run_dir),
        }

    def validate(self) -> list[str]:
        errors: list[str] = []
        try:
            state = self.load_state()
        except (OSError, StateError) as exc:
            return [str(exc)]
        try:
            challenge = self.challenge()
            if not challenge.strip():
                errors.append("challenge is empty")
        except (OSError, StateError, UnicodeError) as exc:
            errors.append(str(exc))

        tasks = state.get("tasks")
        if not isinstance(tasks, dict):
            errors.append("run.json tasks must be an object")
            tasks = {}
        for task_id, raw in tasks.items():
            if not isinstance(raw, dict):
                errors.append(f"task {task_id} must be an object")
                continue
            for key in ("request_path", "prompt_path"):
                value = raw.get(key)
                if not isinstance(value, str) or not self._resolve_relative(value).is_file():
                    errors.append(f"task {task_id} is missing {key}")
            for path_key, hash_key in (
                ("request_path", "request_sha256"),
                ("prompt_path", "prompt_sha256"),
            ):
                value = raw.get(path_key)
                expected = raw.get(hash_key)
                if isinstance(value, str) and isinstance(expected, str):
                    path = self._resolve_relative(value)
                    if path.is_file() and sha256_file(path) != expected:
                        errors.append(f"task {task_id} {path_key} hash mismatch")
            status = raw.get("status")
            if status == "succeeded":
                for key in ("result_path", "output_path"):
                    value = raw.get(key)
                    if not isinstance(value, str) or not self._resolve_relative(value).is_file():
                        errors.append(f"task {task_id} is missing {key}")
                for path_key, hash_key in (
                    ("result_path", "result_sha256"),
                    ("output_path", "output_sha256"),
                ):
                    value = raw.get(path_key)
                    expected = raw.get(hash_key)
                    if isinstance(value, str) and isinstance(expected, str):
                        path = self._resolve_relative(value)
                        if path.is_file() and sha256_file(path) != expected:
                            errors.append(f"task {task_id} {path_key} hash mismatch")
                if not isinstance(raw.get("session_id"), str) or not raw.get("session_id"):
                    errors.append(f"task {task_id} has no Session ID")
            paths = self.task_paths(str(task_id))
            for log_name in ("stdout.jsonl", "stderr.jsonl"):
                if not (paths.raw / log_name).is_file():
                    errors.append(f"task {task_id} is missing raw/{log_name}")

        artifacts = state.get("artifacts")
        if not isinstance(artifacts, dict):
            errors.append("run.json artifacts must be an object")
            artifacts = {}
        for artifact_id, raw in artifacts.items():
            if not isinstance(raw, dict):
                errors.append(f"artifact {artifact_id} must be an object")
                continue
            artifact_path = raw.get("path")
            if not isinstance(artifact_path, str):
                errors.append(f"artifact {artifact_id} has no path")
                continue
            resolved = self._resolve_relative(artifact_path)
            if not resolved.is_file():
                errors.append(f"artifact {artifact_id} is missing: {artifact_path}")
                continue
            if sha256_file(resolved) != raw.get("sha256"):
                errors.append(f"artifact {artifact_id} hash mismatch")

        decisions = read_jsonl(self.decisions_path)
        passed_ideas = {
            row.get("candidate_ref")
            for row in decisions
            if row.get("gate") == "idea-red-team" and row.get("decision") == "pass"
        }
        passed_problems = {
            row.get("candidate_ref")
            for row in decisions
            if row.get("gate") == "problem-gateway" and row.get("decision") == "pass"
        }
        cards = state.get("idea_card_ids", [])
        if not isinstance(cards, list):
            errors.append("idea_card_ids must be a list")
            cards = []
        for card_id in cards:
            record = artifacts.get(card_id)
            if not isinstance(record, dict) or record.get("artifact_type") != "idea_card":
                errors.append(f"Idea Card is not registered: {card_id}")
                continue
            source_refs = record.get("source_refs", [])
            if not isinstance(source_refs, list) or not any(
                source in passed_ideas for source in source_refs
            ):
                errors.append(f"Idea Card has no passed Idea source: {card_id}")
            if not isinstance(source_refs, list) or not any(
                source in passed_problems for source in source_refs
            ):
                errors.append(f"Idea Card has no passed Problem source: {card_id}")
        return errors

    def _mutate(self, callback: Any) -> None:
        with self._lock:
            state = self.load_state()
            callback(state)
            state["updated_at"] = utc_now()
            atomic_write_json(self.state_path, state)

    def _event(self, kind: str, *, event_id: str, data: Mapping[str, Any]) -> None:
        append_jsonl(
            self.events_path,
            {
                "event_id": event_id,
                "kind": kind,
                "data": dict(data),
                "created_at": utc_now(),
            },
            id_field="event_id",
        )

    def _resolve_relative(self, relative: str) -> Path:
        pure = PurePosixPath(relative)
        if pure.is_absolute() or not pure.parts or ".." in pure.parts:
            raise StateError(f"unsafe run-relative path: {relative!r}")
        resolved = self.run_dir.joinpath(*pure.parts).resolve(strict=False)
        if resolved != self.run_dir and self.run_dir not in resolved.parents:
            raise StateError(f"path escapes run directory: {relative!r}")
        return resolved

    def _relative(self, path: Path) -> str:
        resolved = path.expanduser().resolve(strict=False)
        try:
            return resolved.relative_to(self.run_dir).as_posix()
        except ValueError as exc:
            raise StateError(f"path is outside run directory: {resolved}") from exc


def _object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise StateError(f"{label} must be an object")
    return value


def _string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise StateError(f"{label} must be a non-empty string")
    return value
