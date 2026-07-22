"""Durable local run state and append-only ledgers.

This module owns the JSON boundary for the orchestrator.  Callers work with
``RunState`` and ``TaskRecord`` instances; raw JSON is decoded and validated in
one place.  State replacement is atomic, while event and decision ledgers are
append-only and idempotent by their stable record identifiers.
"""

from __future__ import annotations

import errno
import hashlib
import json
import os
import re
import stat
import tempfile
import threading
from collections.abc import Callable, Iterable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, TypeAlias

try:  # pragma: no cover - exercised on the supported POSIX runtime.
    import fcntl
except ImportError:  # pragma: no cover - keeps the helpers usable on Windows.
    fcntl = None  # type: ignore[assignment]


JsonScalar: TypeAlias = None | bool | int | float | str
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject: TypeAlias = dict[str, JsonValue]

STATE_SCHEMA_VERSION = 1
EMPTY_OUTPUT_STAGES = frozenset({"S4", "S6"})
_ID_COMPONENT = re.compile(r"[^a-z0-9._-]+")
_MISSING = object()


class StateError(RuntimeError):
    """Base class for durable-state errors."""


class StateFormatError(StateError):
    """A state or ledger file does not satisfy its on-disk contract."""


class StateConflictError(StateError):
    """A stable identifier was reused for different durable content."""


def _json_copy(value: Any, *, context: str) -> JsonValue:
    """Validate that *value* is strict JSON and return a detached copy."""

    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return json.loads(encoded)
    except (TypeError, ValueError) as exc:
        raise StateFormatError(f"{context} is not valid JSON: {exc}") from exc


def _json_object_copy(value: Any, *, context: str) -> JsonObject:
    copied = _json_copy(value, context=context)
    if not isinstance(copied, dict):
        raise StateFormatError(f"{context} must be a JSON object")
    return copied


class _DuplicateJsonKey(ValueError):
    pass


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJsonKey(f"duplicate JSON object key {key!r}")
        result[key] = value
    return result


def _fsync_directory(directory: Path) -> None:
    """Durably record a rename where the platform supports directory fsync."""

    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    try:
        descriptor = os.open(directory, flags)
    except OSError:
        return
    try:
        os.fsync(descriptor)
    except OSError:
        pass
    finally:
        os.close(descriptor)


def fsync_directory(directory: str | Path) -> None:
    """Best-effort durability barrier for a directory entry change."""

    _fsync_directory(Path(directory))


def atomic_write_bytes(path: str | Path, content: bytes, *, mode: int = 0o600) -> Path:
    """Replace *path* atomically with *content* on the same filesystem."""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_symlink():
        raise StateError(f"refusing to replace symlink: {destination}")

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=destination.parent,
    )
    temporary = Path(temporary_name)
    try:
        try:
            os.fchmod(descriptor, mode)
        except (AttributeError, OSError):
            pass
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
        _fsync_directory(destination.parent)
    except BaseException:
        try:
            os.close(descriptor)
        except OSError:
            pass
        temporary.unlink(missing_ok=True)
        raise
    return destination


def atomic_write_json(path: str | Path, value: Any) -> Path:
    """Validate and atomically write JSON using a stable human-readable form."""

    normalized = _json_copy(value, context="JSON value")
    encoded = (
        json.dumps(
            normalized,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
    return atomic_write_bytes(path, encoded)


def read_json(path: str | Path, *, default: Any = _MISSING) -> JsonValue:
    """Read one strict JSON value, with path-aware decode errors."""

    source = Path(path)
    try:
        raw = source.read_text(encoding="utf-8")
    except FileNotFoundError:
        if default is _MISSING:
            raise
        return _json_copy(default, context="default JSON value")
    except UnicodeDecodeError as exc:
        raise StateFormatError(f"{source} is not valid UTF-8: {exc}") from exc

    try:
        value = json.loads(raw, object_pairs_hook=_unique_json_object)
    except _DuplicateJsonKey as exc:
        raise StateFormatError(f"{source} contains {exc}") from exc
    except json.JSONDecodeError as exc:
        raise StateFormatError(
            f"{source} contains invalid JSON at line {exc.lineno}, "
            f"column {exc.colno}: {exc.msg}"
        ) from exc
    return _json_copy(value, context=str(source))


def read_json_object(path: str | Path, *, default: Any = _MISSING) -> JsonObject:
    value = read_json(path, default=default)
    if not isinstance(value, dict):
        raise StateFormatError(f"{Path(path)} must contain a JSON object")
    return value


_THREAD_LOCKS: dict[str, threading.RLock] = {}
_THREAD_LOCKS_GUARD = threading.Lock()


def _thread_lock(path: Path) -> threading.RLock:
    key = str(path.resolve(strict=False))
    with _THREAD_LOCKS_GUARD:
        return _THREAD_LOCKS.setdefault(key, threading.RLock())


@contextmanager
def _locked(path: Path, *, shared: bool = False) -> Iterator[None]:
    """Coordinate state changes across threads and local processes."""

    lock_path = path.with_name(f".{path.name}.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    local_lock = _thread_lock(lock_path)
    with local_lock:
        descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
        try:
            if fcntl is not None:
                operation = fcntl.LOCK_SH if shared else fcntl.LOCK_EX
                fcntl.flock(descriptor, operation)
            yield
        finally:
            if fcntl is not None:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)


@contextmanager
def exclusive_path_lock(path: str | Path) -> Iterator[None]:
    """Expose the local process-safe lock used by durable file owners."""

    with _locked(Path(path)):
        yield


def _read_jsonl_unlocked(path: Path) -> list[JsonObject]:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    if not hasattr(os, "O_NOFOLLOW") and path.is_symlink():
        raise StateFormatError(f"refusing to read JSONL through symlink: {path}")
    try:
        descriptor = os.open(path, flags)
    except FileNotFoundError:
        return []
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            raise StateFormatError(
                f"refusing to read JSONL through symlink: {path}"
            ) from exc
        raise
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise StateFormatError(f"JSONL ledger is not a regular file: {path}")
        try:
            with os.fdopen(descriptor, "r", encoding="utf-8") as handle:
                descriptor = -1
                raw = handle.read()
        except UnicodeDecodeError as exc:
            raise StateFormatError(f"{path} is not valid UTF-8: {exc}") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)

    records: list[JsonObject] = []
    for line_number, line in enumerate(raw.splitlines(), start=1):
        if not line.strip():
            raise StateFormatError(f"{path}:{line_number} is an empty JSONL record")
        try:
            value = json.loads(line, object_pairs_hook=_unique_json_object)
        except _DuplicateJsonKey as exc:
            raise StateFormatError(f"{path}:{line_number} contains {exc}") from exc
        except json.JSONDecodeError as exc:
            raise StateFormatError(
                f"{path}:{line_number} contains invalid JSON at column "
                f"{exc.colno}: {exc.msg}"
            ) from exc
        if not isinstance(value, dict):
            raise StateFormatError(f"{path}:{line_number} must be a JSON object")
        records.append(_json_object_copy(value, context=f"{path}:{line_number}"))
    return records


def read_jsonl(path: str | Path) -> list[JsonObject]:
    """Read and validate a complete append-only JSONL ledger."""

    source = Path(path)
    with _locked(source, shared=True):
        return _read_jsonl_unlocked(source)


def append_jsonl_once(
    path: str | Path,
    record: Mapping[str, Any],
    *,
    id_field: str,
) -> bool:
    """Append *record* exactly once by a required stable identifier.

    ``True`` means a new line was appended.  Repeating byte-equivalent logical
    content returns ``False``.  Reusing the same identifier for different
    content is a conflict instead of a silent overwrite.
    """

    if not id_field or not isinstance(id_field, str):
        raise ValueError("id_field must be a non-empty string")
    normalized = _json_object_copy(dict(record), context="JSONL record")
    record_id = normalized.get(id_field)
    if not isinstance(record_id, str) or not record_id.strip():
        raise StateFormatError(f"JSONL record requires non-empty {id_field!r}")

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    encoded = (
        json.dumps(
            normalized,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")

    with _locked(destination):
        matches = [
            existing
            for existing in _read_jsonl_unlocked(destination)
            if existing.get(id_field) == record_id
        ]
        if len(matches) > 1:
            raise StateFormatError(
                f"ledger already contains duplicate {id_field} {record_id!r}"
            )
        if matches:
            if matches[0] == normalized:
                return False
            raise StateConflictError(
                f"{id_field} {record_id!r} already exists with different content"
            )

        flags = os.O_APPEND | os.O_CREAT | os.O_WRONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        elif destination.is_symlink():
            raise StateFormatError(
                f"refusing to append JSONL through symlink: {destination}"
            )
        try:
            descriptor = os.open(destination, flags, 0o600)
        except OSError as exc:
            if exc.errno == errno.ELOOP:
                raise StateFormatError(
                    f"refusing to append JSONL through symlink: {destination}"
                ) from exc
            raise
        try:
            if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                raise StateFormatError(
                    f"JSONL ledger is not a regular file: {destination}"
                )
            view = memoryview(encoded)
            while view:
                written = os.write(descriptor, view)
                if written <= 0:
                    raise StateError(f"short append while writing {destination}")
                view = view[written:]
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        _fsync_directory(destination.parent)
    return True


class TaskStatus(str, Enum):
    WAITING = "waiting"
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RunStatus(str, Enum):
    WAITING = "waiting"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


def _required_text(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise StateFormatError(f"{field_name} must be a non-empty string")
    return value


def _optional_text(value: Any, *, field_name: str) -> str | None:
    if value is None:
        return None
    return _required_text(value, field_name=field_name)


def _string_list(value: Any, *, field_name: str) -> list[str]:
    if not isinstance(value, (list, tuple)):
        raise StateFormatError(f"{field_name} must be a list of strings")
    result: list[str] = []
    for item in value:
        result.append(_required_text(item, field_name=f"{field_name} item"))
    if len(set(result)) != len(result):
        raise StateFormatError(f"{field_name} must not contain duplicates")
    return result


def stable_record_id(namespace: str, *identity: Any, length: int = 20) -> str:
    """Return a deterministic, filesystem-safe identifier for logical work."""

    namespace = _required_text(namespace, field_name="namespace")
    if length < 8 or length > 64:
        raise ValueError("length must be between 8 and 64")
    slug = _ID_COMPONENT.sub("-", namespace.strip().lower()).strip("-._") or "record"
    canonical = json.dumps(
        _json_copy(list(identity), context="stable identifier input"),
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    digest = hashlib.sha256(namespace.encode("utf-8") + b"\0" + canonical).hexdigest()
    return f"{slug}-{digest[:length]}"


def stable_task_id(stage: str, *identity: Any) -> str:
    """Create the stable task id used to make resume decisions idempotent."""

    stage = _required_text(stage, field_name="stage")
    return stable_record_id(stage, *identity)


@dataclass(slots=True)
class TaskRecord:
    """Durable state for one logical workflow task."""

    task_id: str
    stage: str
    status: TaskStatus | str = TaskStatus.WAITING
    attempts: int = 0
    session_id: str | None = None
    outputs: list[str] = field(default_factory=list)
    last_error: str | None = None
    next_action: str | None = None
    allow_empty_outputs: bool | None = None
    data: JsonObject = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.task_id = _required_text(self.task_id, field_name="task_id")
        self.stage = _required_text(self.stage, field_name="stage")
        try:
            self.status = TaskStatus(self.status)
        except ValueError as exc:
            raise StateFormatError(f"invalid task status: {self.status!r}") from exc
        if isinstance(self.attempts, bool) or not isinstance(self.attempts, int):
            raise StateFormatError("attempts must be an integer")
        if self.attempts < 0:
            raise StateFormatError("attempts must not be negative")
        self.session_id = _optional_text(self.session_id, field_name="session_id")
        self.outputs = _string_list(self.outputs, field_name="outputs")
        self.last_error = _optional_text(self.last_error, field_name="last_error")
        self.next_action = _optional_text(self.next_action, field_name="next_action")
        allowed_by_stage = self.stage in EMPTY_OUTPUT_STAGES
        if self.allow_empty_outputs is None:
            self.allow_empty_outputs = allowed_by_stage
        elif not isinstance(self.allow_empty_outputs, bool):
            raise StateFormatError("allow_empty_outputs must be a boolean")
        elif self.allow_empty_outputs != allowed_by_stage:
            raise StateFormatError(
                "allow_empty_outputs is derived from stage and cannot be overridden"
            )
        self.data = _json_object_copy(self.data, context="task data")

    @classmethod
    def create(cls, stage: str, *identity: Any, **kwargs: Any) -> "TaskRecord":
        return cls(task_id=stable_task_id(stage, *identity), stage=stage, **kwargs)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "TaskRecord":
        allowed = {
            "task_id",
            "stage",
            "status",
            "attempts",
            "session_id",
            "outputs",
            "last_error",
            "next_action",
            "allow_empty_outputs",
            "data",
        }
        unknown = sorted(set(value) - allowed)
        if unknown:
            raise StateFormatError(f"unknown task fields: {', '.join(unknown)}")
        try:
            return cls(
                task_id=value["task_id"],
                stage=value["stage"],
                status=value.get("status", TaskStatus.WAITING.value),
                attempts=value.get("attempts", 0),
                session_id=value.get("session_id"),
                outputs=value.get("outputs", []),
                last_error=value.get("last_error"),
                next_action=value.get("next_action"),
                allow_empty_outputs=value.get("allow_empty_outputs"),
                data=value.get("data", {}),
            )
        except KeyError as exc:
            raise StateFormatError(f"task record is missing {exc.args[0]!r}") from exc

    def to_dict(self) -> JsonObject:
        try:
            status = TaskStatus(self.status).value
        except ValueError as exc:
            raise StateFormatError(f"invalid task status: {self.status!r}") from exc
        return _json_object_copy(
            {
                "task_id": self.task_id,
                "stage": self.stage,
                "status": status,
                "attempts": self.attempts,
                "session_id": self.session_id,
                "outputs": _string_list(self.outputs, field_name="outputs"),
                "last_error": self.last_error,
                "next_action": self.next_action,
                "allow_empty_outputs": self.allow_empty_outputs,
                "data": self.data,
            },
            context=f"task {self.task_id}",
        )


@dataclass(slots=True)
class RunState:
    """Versioned run state with an extensible workflow-owned data object."""

    run_id: str
    current_stage: str | None = None
    status: RunStatus | str = RunStatus.WAITING
    tasks: dict[str, TaskRecord] = field(default_factory=dict)
    completed_artifacts: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)
    data: JsonObject = field(default_factory=dict)
    schema_version: int = STATE_SCHEMA_VERSION
    state_revision: int = 0

    def __post_init__(self) -> None:
        self.run_id = _required_text(self.run_id, field_name="run_id")
        if self.current_stage is not None:
            self.current_stage = _required_text(
                self.current_stage,
                field_name="current_stage",
            )
        try:
            self.status = RunStatus(self.status)
        except ValueError as exc:
            raise StateFormatError(f"invalid run status: {self.status!r}") from exc
        if (
            isinstance(self.schema_version, bool)
            or not isinstance(self.schema_version, int)
            or self.schema_version != STATE_SCHEMA_VERSION
        ):
            raise StateFormatError(
                f"unsupported state schema_version {self.schema_version!r}; "
                f"expected {STATE_SCHEMA_VERSION}"
            )
        if (
            isinstance(self.state_revision, bool)
            or not isinstance(self.state_revision, int)
            or self.state_revision < 0
        ):
            raise StateFormatError("state_revision must be a non-negative integer")
        normalized_tasks: dict[str, TaskRecord] = {}
        for key, task in self.tasks.items():
            key = _required_text(key, field_name="task mapping key")
            if isinstance(task, Mapping):
                task = TaskRecord.from_dict(task)
            if not isinstance(task, TaskRecord):
                raise StateFormatError("tasks must map ids to TaskRecord objects")
            if task.task_id != key:
                raise StateFormatError(
                    f"task mapping key {key!r} does not match task_id {task.task_id!r}"
                )
            normalized_tasks[key] = task
        self.tasks = normalized_tasks
        self.completed_artifacts = _string_list(
            self.completed_artifacts,
            field_name="completed_artifacts",
        )
        self.next_actions = _string_list(self.next_actions, field_name="next_actions")
        self.data = _json_object_copy(self.data, context="run data")

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "RunState":
        allowed = {
            "schema_version",
            "run_id",
            "current_stage",
            "stage",
            "status",
            "tasks",
            "completed_artifacts",
            "next_actions",
            "data",
            "state_revision",
        }
        unknown = sorted(set(value) - allowed)
        if unknown:
            raise StateFormatError(f"unknown run-state fields: {', '.join(unknown)}")
        if "current_stage" in value and "stage" in value:
            raise StateFormatError("state cannot contain both 'current_stage' and 'stage'")
        raw_tasks = value.get("tasks", {})
        if not isinstance(raw_tasks, Mapping):
            raise StateFormatError("tasks must be a JSON object")
        invalid_task_ids = [
            str(task_id)
            for task_id, task in raw_tasks.items()
            if not isinstance(task, Mapping)
        ]
        if invalid_task_ids:
            raise StateFormatError(
                "task entries must be JSON objects: " + ", ".join(invalid_task_ids)
            )
        try:
            return cls(
                run_id=value["run_id"],
                current_stage=value.get("current_stage", value.get("stage")),
                status=value.get("status", RunStatus.WAITING.value),
                tasks={
                    str(task_id): TaskRecord.from_dict(task)
                    for task_id, task in raw_tasks.items()
                },
                completed_artifacts=value.get("completed_artifacts", []),
                next_actions=value.get("next_actions", []),
                data=value.get("data", {}),
                schema_version=value.get("schema_version", STATE_SCHEMA_VERSION),
                state_revision=value.get("state_revision", 0),
            )
        except KeyError as exc:
            raise StateFormatError(f"run state is missing {exc.args[0]!r}") from exc

    def to_dict(self) -> JsonObject:
        try:
            status = RunStatus(self.status).value
        except ValueError as exc:
            raise StateFormatError(f"invalid run status: {self.status!r}") from exc
        return _json_object_copy(
            {
                "schema_version": self.schema_version,
                "run_id": self.run_id,
                "current_stage": self.current_stage,
                "status": status,
                "tasks": {
                    task_id: self.tasks[task_id].to_dict()
                    for task_id in sorted(self.tasks)
                },
                "completed_artifacts": _string_list(
                    self.completed_artifacts,
                    field_name="completed_artifacts",
                ),
                "next_actions": _string_list(
                    self.next_actions,
                    field_name="next_actions",
                ),
                "data": self.data,
                "state_revision": self.state_revision,
            },
            context=f"run {self.run_id}",
        )

    def upsert_task(self, task: TaskRecord) -> None:
        existing = self.tasks.get(task.task_id)
        if existing is not None and existing.stage != task.stage:
            raise StateConflictError(
                f"task {task.task_id!r} cannot change stage from "
                f"{existing.stage!r} to {task.stage!r}"
            )
        self.tasks[task.task_id] = task

    def is_task_complete(self, task_id: str) -> bool:
        task = self.tasks.get(task_id)
        return task is not None and task.status is TaskStatus.COMPLETED


class StateStore:
    """Atomic ``state.json`` plus idempotent events and decisions ledgers."""

    def __init__(self, run_dir: str | Path) -> None:
        self.run_dir = Path(run_dir)
        self.state_path = self.run_dir / "state.json"
        self.events_path = self.run_dir / "events.jsonl"
        self.decisions_path = self.run_dir / "decisions.jsonl"

    def initialize(
        self,
        run_id: str,
        *,
        data: Mapping[str, Any] | None = None,
    ) -> RunState:
        """Create the state once, or return an existing state for the same run."""

        with _locked(self.state_path):
            if self.state_path.exists():
                state = self._load_unlocked()
                if state.run_id != run_id:
                    raise StateConflictError(
                        f"existing state belongs to {state.run_id!r}, not {run_id!r}"
                    )
                return state
            state = RunState(run_id=run_id, data=dict(data or {}))
            atomic_write_json(self.state_path, state.to_dict())
            return state

    def _load_unlocked(self) -> RunState:
        return RunState.from_dict(read_json_object(self.state_path))

    def load(self) -> RunState:
        with _locked(self.state_path, shared=True):
            return self._load_unlocked()

    def save(self, state: RunState) -> RunState:
        if not isinstance(state, RunState):
            raise TypeError("state must be a RunState")
        with _locked(self.state_path):
            if self.state_path.exists():
                existing = self._load_unlocked()
                if existing.run_id != state.run_id:
                    raise StateConflictError(
                        f"cannot replace run {existing.run_id!r} with {state.run_id!r}"
                    )
                if state.state_revision != existing.state_revision:
                    raise StateConflictError(
                        f"stale state revision {state.state_revision}; "
                        f"current revision is {existing.state_revision}"
                    )
                state = RunState.from_dict(state.to_dict())
                state.state_revision += 1
            elif state.state_revision != 0:
                raise StateConflictError("new state must start at state_revision 0")
            atomic_write_json(self.state_path, state.to_dict())
            return state

    def mutate(
        self,
        callback: Callable[[RunState], RunState | None],
    ) -> RunState:
        """Load, mutate and atomically save state under one exclusive lock."""

        with _locked(self.state_path):
            state = self._load_unlocked()
            original_run_id = state.run_id
            original_revision = state.state_revision
            replacement = callback(state)
            updated = state if replacement is None else replacement
            if not isinstance(updated, RunState):
                raise TypeError("state callback must return RunState or None")
            if updated.run_id != original_run_id:
                raise StateConflictError("a mutation cannot change run_id")
            if updated.state_revision != original_revision:
                raise StateConflictError("a mutation cannot change state_revision")
            # Round-trip validation catches invalid values introduced by direct
            # mutation of dataclass lists/dicts before anything reaches disk.
            updated = RunState.from_dict(updated.to_dict())
            updated.state_revision += 1
            atomic_write_json(self.state_path, updated.to_dict())
            return updated

    update = mutate

    def upsert_task(self, task: TaskRecord) -> RunState:
        def apply(state: RunState) -> None:
            state.upsert_task(task)

        return self.mutate(apply)

    def append_event(self, record: Mapping[str, Any]) -> bool:
        return append_jsonl_once(self.events_path, record, id_field="event_id")

    def append_decision(self, record: Mapping[str, Any]) -> bool:
        return append_jsonl_once(
            self.decisions_path,
            record,
            id_field="decision_id",
        )

    def events(self) -> list[JsonObject]:
        return read_jsonl(self.events_path)

    def decisions(self) -> list[JsonObject]:
        return read_jsonl(self.decisions_path)

    def reconcile(
        self,
        validate_output: Callable[[str], Any],
        *,
        discovered_outputs: Iterable[str] = (),
    ) -> "ReconciliationReport":
        return reconcile_task_outputs(
            self.load(),
            validate_output,
            discovered_outputs=discovered_outputs,
        )


@dataclass(frozen=True, slots=True)
class ReconciliationReport:
    """Pure resume guidance; applying a workflow transition stays explicit."""

    skippable_task_ids: tuple[str, ...]
    recoverable_task_ids: tuple[str, ...]
    incomplete_task_ids: tuple[str, ...]
    stale_completed_task_ids: tuple[str, ...]
    unexpected_empty_task_ids: tuple[str, ...]
    missing_outputs: Mapping[str, tuple[str, ...]]
    invalid_outputs: Mapping[str, Mapping[str, str]]
    orphan_outputs: tuple[str, ...]

    @property
    def clean(self) -> bool:
        return not (
            self.recoverable_task_ids
            or self.stale_completed_task_ids
            or self.unexpected_empty_task_ids
            or self.orphan_outputs
        )

    def can_skip(self, task_id: str) -> bool:
        return task_id in self.skippable_task_ids


def reconcile_task_outputs(
    state: RunState,
    validate_output: Callable[[str], Any],
    *,
    discovered_outputs: Iterable[str] = (),
) -> ReconciliationReport:
    """Compare task records with canonical artifacts without changing state.

    The validator should return any value for a valid artifact and either
    return ``False`` or raise for an invalid one.  A completed task is safe to
    skip only when every declared output validates.  Valid outputs attached to
    an unfinished task are reported as recoverable, leaving the workflow to
    verify its decision/event boundary before marking it complete.
    """

    skippable: list[str] = []
    recoverable: list[str] = []
    incomplete: list[str] = []
    stale: list[str] = []
    unexpected_empty: list[str] = []
    missing: dict[str, tuple[str, ...]] = {}
    invalid: dict[str, Mapping[str, str]] = {}
    referenced: set[str] = set()

    for task_id in sorted(state.tasks):
        task = state.tasks[task_id]
        referenced.update(task.outputs)
        task_missing: list[str] = []
        task_invalid: dict[str, str] = {}
        for output in task.outputs:
            try:
                result = validate_output(output)
                if result is False:
                    task_invalid[output] = "validator returned False"
            except FileNotFoundError:
                task_missing.append(output)
            except Exception as exc:  # The report must retain validator detail.
                task_invalid[output] = f"{type(exc).__name__}: {exc}"

        if task_missing:
            missing[task_id] = tuple(task_missing)
        if task_invalid:
            invalid[task_id] = task_invalid
        outputs_valid = not task_missing and not task_invalid

        empty_is_invalid = not task.outputs and task.stage not in EMPTY_OUTPUT_STAGES
        if task.status is TaskStatus.COMPLETED:
            if empty_is_invalid:
                stale.append(task_id)
                unexpected_empty.append(task_id)
            elif outputs_valid:
                skippable.append(task_id)
            else:
                stale.append(task_id)
        elif task.outputs and outputs_valid:
            recoverable.append(task_id)
        else:
            incomplete.append(task_id)

    discovered = {
        _required_text(item, field_name="discovered output")
        for item in discovered_outputs
    }
    return ReconciliationReport(
        skippable_task_ids=tuple(skippable),
        recoverable_task_ids=tuple(recoverable),
        incomplete_task_ids=tuple(incomplete),
        stale_completed_task_ids=tuple(stale),
        unexpected_empty_task_ids=tuple(unexpected_empty),
        missing_outputs=missing,
        invalid_outputs=invalid,
        orphan_outputs=tuple(sorted(discovered - referenced)),
    )


__all__ = [
    "JsonObject",
    "JsonValue",
    "EMPTY_OUTPUT_STAGES",
    "ReconciliationReport",
    "RunState",
    "RunStatus",
    "STATE_SCHEMA_VERSION",
    "StateConflictError",
    "StateError",
    "StateFormatError",
    "StateStore",
    "TaskRecord",
    "TaskStatus",
    "append_jsonl_once",
    "atomic_write_bytes",
    "atomic_write_json",
    "exclusive_path_lock",
    "fsync_directory",
    "read_json",
    "read_json_object",
    "read_jsonl",
    "reconcile_task_outputs",
    "stable_record_id",
    "stable_task_id",
]
