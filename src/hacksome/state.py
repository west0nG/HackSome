"""Small durable JSON primitives used by the run Hub.

The Idea workflow has one state owner.  This module deliberately contains no
stage logic: it only provides strict JSON decoding, atomic replacement, content
hashing, and idempotent append-only ledgers.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import threading
from pathlib import Path
from typing import Any


class StateError(RuntimeError):
    """Base class for persisted-state failures."""


class StateFormatError(StateError):
    """Persisted JSON does not satisfy the strict on-disk contract."""


class StateConflictError(StateError):
    """A stable record identifier was reused for different content."""


_LOCKS: dict[str, threading.RLock] = {}
_LOCKS_GUARD = threading.Lock()


def _lock_for(path: Path) -> threading.RLock:
    key = str(path.resolve(strict=False))
    with _LOCKS_GUARD:
        return _LOCKS.setdefault(key, threading.RLock())


def _normalize_json(value: Any, *, label: str) -> Any:
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
        raise StateFormatError(f"{label} is not strict JSON: {exc}") from exc


def atomic_write_bytes(path: str | Path, content: bytes) -> Path:
    """Atomically replace one regular file on the same filesystem."""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_symlink():
        raise StateError(f"refusing to replace symlink: {destination}")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return destination


def atomic_write_text(path: str | Path, content: str) -> Path:
    if not isinstance(content, str):
        raise TypeError("text content must be a string")
    return atomic_write_bytes(path, content.encode("utf-8"))


def atomic_write_json(path: str | Path, value: Any) -> Path:
    normalized = _normalize_json(value, label="JSON value")
    text = json.dumps(
        normalized, ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True
    ) + "\n"
    return atomic_write_text(path, text)


def read_json(path: str | Path) -> Any:
    source = Path(path)
    try:
        raw = source.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise StateFormatError(f"{source} is not valid UTF-8") from exc
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise StateFormatError(
            f"{source} contains invalid JSON at line {exc.lineno}: {exc.msg}"
        ) from exc
    return _normalize_json(value, label=str(source))


def read_json_object(path: str | Path) -> dict[str, Any]:
    value = read_json(path)
    if not isinstance(value, dict):
        raise StateFormatError(f"{Path(path)} must contain a JSON object")
    return value


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_text(content: str) -> str:
    return sha256_bytes(content.encode("utf-8"))


def sha256_file(path: str | Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def append_jsonl(
    path: str | Path,
    record: dict[str, Any],
    *,
    id_field: str,
) -> bool:
    """Append a strict JSON record once, rejecting conflicting stable IDs."""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    normalized = _normalize_json(record, label="JSONL record")
    if not isinstance(normalized, dict):
        raise StateFormatError("JSONL record must be an object")
    record_id = normalized.get(id_field)
    if not isinstance(record_id, str) or not record_id:
        raise StateFormatError(f"JSONL record requires non-empty {id_field!r}")

    lock = _lock_for(destination)
    with lock:
        existing: dict[str, Any] | None = None
        if destination.exists():
            for number, line in enumerate(
                destination.read_text(encoding="utf-8").splitlines(), start=1
            ):
                if not line.strip():
                    continue
                try:
                    candidate = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise StateFormatError(
                        f"{destination}:{number} is invalid JSONL: {exc.msg}"
                    ) from exc
                if isinstance(candidate, dict) and candidate.get(id_field) == record_id:
                    existing = _normalize_json(candidate, label="existing JSONL record")
                    break
        if existing is not None:
            if existing != normalized:
                raise StateConflictError(
                    f"{id_field} {record_id!r} already exists with different content"
                )
            return False
        with destination.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(normalized, ensure_ascii=False, sort_keys=True) + "\n"
            )
            handle.flush()
            os.fsync(handle.fileno())
        return True


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    source = Path(path)
    if not source.exists():
        return []
    records: list[dict[str, Any]] = []
    for number, line in enumerate(
        source.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise StateFormatError(
                f"{source}:{number} is invalid JSONL: {exc.msg}"
            ) from exc
        if not isinstance(value, dict):
            raise StateFormatError(f"{source}:{number} must be a JSON object")
        records.append(_normalize_json(value, label=f"{source}:{number}"))
    return records
