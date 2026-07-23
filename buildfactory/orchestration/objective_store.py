"""V7 Company/Department Objective proposals backed by the global review pool."""

from __future__ import annotations

import hashlib
import time
from pathlib import Path

from orchestration.runtime_store import (
    atomic_write_json,
    atomic_write_text,
    file_lock,
    read_json,
    require_identifier,
)
from orchestration.verifier_manager import FAILED, PASSED, VerifierManager


class ObjectiveError(ValueError):
    pass


class ObjectiveStore:
    def __init__(self, agents_root: str | Path, reviews: VerifierManager):
        self.root = Path(agents_root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.reviews = reviews
        self._lock_path = self.root / ".objectives.lock"

    @staticmethod
    def _proposal_id(request_id: str) -> str:
        return "objective-" + hashlib.sha256(request_id.encode("utf-8")).hexdigest()[:16]

    def _actor_root(self, actor_id: str) -> Path:
        return self.root / require_identifier(actor_id, label="objective actor")

    def _proposal_path(self, actor_id: str, proposal_id: str) -> Path:
        return self._actor_root(actor_id) / "proposals" / f"{proposal_id}.json"

    def _find_by_review(self, review_id: str) -> tuple[Path, dict]:
        for path in self.root.glob("*/proposals/objective-*.json"):
            proposal = read_json(path)
            if isinstance(proposal, dict) and proposal.get("review_id") == review_id:
                return path, proposal
        raise ObjectiveError(f"no Objective proposal for review: {review_id}")

    def propose(
        self,
        *,
        actor_id: str,
        objective_kind: str,
        text: str,
        requested_by: str,
        request_id: str,
    ) -> dict:
        actor_id = require_identifier(actor_id, label="objective actor")
        if objective_kind not in ("company", "department"):
            raise ObjectiveError(f"unknown Objective kind: {objective_kind!r}")
        if objective_kind == "company" and actor_id != "ceo":
            raise ObjectiveError("Company Objective belongs to ceo")
        if not isinstance(text, str) or not text.strip():
            raise ObjectiveError("Objective must be non-empty")
        proposal_id = self._proposal_id(request_id)
        path = self._proposal_path(actor_id, proposal_id)
        with file_lock(self._lock_path):
            existing = read_json(path)
            if isinstance(existing, dict):
                return existing
            actor_root = self._actor_root(actor_id)
            actor_root.mkdir(parents=True, exist_ok=True)
            revisions = [
                int(row.get("revision", 0))
                for candidate in (actor_root / "proposals").glob("objective-*.json")
                if isinstance((row := read_json(candidate)), dict)
            ] if (actor_root / "proposals").is_dir() else []
            revision = max(revisions, default=0) + 1
            review_id = self.reviews.enqueue(
                kind=("company_objective" if objective_kind == "company" else "department_objective"),
                subject_id=actor_id,
                requested_by=requested_by,
                payload={
                    "proposal_id": proposal_id,
                    "actor_id": actor_id,
                    "objective_kind": objective_kind,
                    "revision": revision,
                    "text": text.strip(),
                    "current": self.current(actor_id),
                },
                request_id=f"objective-review:{request_id}",
            )
            now = time.time()
            proposal = {
                "id": proposal_id,
                "actor_id": actor_id,
                "objective_kind": objective_kind,
                "revision": revision,
                "text": text.strip(),
                "requested_by": requested_by,
                "review_id": review_id,
                "status": "reviewing",
                "reason": None,
                "created_at": now,
                "updated_at": now,
            }
            atomic_write_json(path, proposal)
            return proposal

    def apply_review(self, review_id: str) -> dict:
        with file_lock(self._lock_path):
            path, proposal = self._find_by_review(review_id)
            if proposal["status"] in ("active", "rejected"):
                return proposal
            review = self.reviews.get(review_id)
            if review["status"] not in (PASSED, FAILED):
                raise ObjectiveError(f"review {review_id} has no terminal verdict")
            proposal["reason"] = review.get("reason")
            proposal["updated_at"] = time.time()
            if review["status"] == FAILED:
                proposal["status"] = "rejected"
                atomic_write_json(path, proposal)
                return proposal
            proposal["status"] = "active"
            actor_root = self._actor_root(proposal["actor_id"])
            actor_root.mkdir(parents=True, exist_ok=True)
            objective_path = actor_root / "objective.md"
            atomic_write_text(objective_path, proposal["text"].rstrip() + "\n")
            atomic_write_json(
                actor_root / "objective.active.json",
                {
                    "proposal_id": proposal["id"],
                    "review_id": review_id,
                    "revision": proposal["revision"],
                    "objective_kind": proposal["objective_kind"],
                    "activated_at": proposal["updated_at"],
                },
            )
            history = actor_root / "history"
            history.mkdir(parents=True, exist_ok=True)
            atomic_write_text(
                history / f"revision-{proposal['revision']}.md",
                proposal["text"].rstrip() + "\n",
            )
            atomic_write_json(path, proposal)
            return proposal

    def current(self, actor_id: str) -> str | None:
        path = self._actor_root(actor_id) / "objective.md"
        if not path.is_file():
            return None
        text = path.read_text(encoding="utf-8").strip()
        return text or None

    def active_metadata(self, actor_id: str) -> dict | None:
        row = read_json(self._actor_root(actor_id) / "objective.active.json")
        return row if isinstance(row, dict) else None

    def in_review(
        self,
        *,
        actor_id: str | None = None,
        requested_by: str | None = None,
    ) -> list[dict]:
        """Return controlled proposal projections still awaiting a verdict."""

        rows: list[dict] = []
        for path in self.root.glob("*/proposals/objective-*.json"):
            proposal = read_json(path)
            if not isinstance(proposal, dict) or proposal.get("status") != "reviewing":
                continue
            if actor_id is not None and proposal.get("actor_id") != actor_id:
                continue
            if requested_by is not None and proposal.get("requested_by") != requested_by:
                continue
            rows.append(
                {
                    "proposal_id": proposal["id"],
                    "review_id": proposal["review_id"],
                    "actor_id": proposal["actor_id"],
                    "objective_kind": proposal["objective_kind"],
                    "revision": proposal["revision"],
                    "text": proposal["text"],
                    "status": proposal["status"],
                }
            )
        return sorted(rows, key=lambda row: (row["actor_id"], row["revision"]))
