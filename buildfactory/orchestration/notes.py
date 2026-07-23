"""Private cross-wake Notes for resident CEO/Department agents."""

from __future__ import annotations

from pathlib import Path

from orchestration.runtime_store import (
    atomic_write_json,
    atomic_write_text,
    file_lock,
    require_identifier,
)


NOTES_MAX_CHARS = 12000


class NotesError(ValueError):
    pass


class NotesStore:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._lock_path = self.root / ".notes.lock"

    def _path(self, actor_id: str) -> Path:
        return self.root / require_identifier(actor_id, label="notes actor") / "notes.md"

    def read(self, actor_id: str) -> str | None:
        path = self._path(actor_id)
        if not path.is_file():
            return None
        text = path.read_text(encoding="utf-8").strip()
        return text or None

    def write(self, actor_id: str, text: str, *, request_id: str) -> dict:
        if not isinstance(text, str):
            raise NotesError("Notes must be text")
        text = text.strip()
        if len(text) > NOTES_MAX_CHARS:
            raise NotesError(f"Notes exceed {NOTES_MAX_CHARS} characters")
        path = self._path(actor_id)
        receipt = path.parent / "requests" / f"{request_id}.json"
        with file_lock(self._lock_path):
            if receipt.is_file():
                import json

                return json.loads(receipt.read_text(encoding="utf-8"))
            path.parent.mkdir(parents=True, exist_ok=True)
            atomic_write_text(path, text + ("\n" if text else ""))
            result = {"actor_id": actor_id, "chars": len(text), "empty": not bool(text)}
            atomic_write_json(receipt, result)
            return result
