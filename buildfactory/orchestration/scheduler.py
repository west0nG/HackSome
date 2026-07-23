"""V7 Goal ledger and strict-FIFO Worker scheduler.

This module owns Goal truth.  A Goal has no blocked/waiting state and no
attempt-based failure path: after a Worker starts, PASS, explicit cancellation,
or the immutable absolute deadline are the only ways out.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from pathlib import Path

from orchestration.runtime_store import atomic_write_json, file_lock, read_json, require_identifier


OPEN = "open"
CLAIMED = "claimed"
RUNNING = "running"
REPORTED = "reported"
VERIFYING = "verifying"
DONE = "done"
FAILED_TIME = "failed_time"
CANCELLED = "cancelled"

NON_TERMINAL = (OPEN, CLAIMED, RUNNING, REPORTED, VERIFYING)
TERMINAL = (DONE, FAILED_TIME, CANCELLED)
ACTIVE_WORKER_STATES = ("starting", "running", "awaiting_verdict", "resuming", "stopping")


class GoalError(ValueError):
    pass


def _now() -> float:
    return time.time()


def _goal_id(request_id: str) -> str:
    return "goal-" + hashlib.sha256(request_id.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class WorkerLaunch:
    goal_id: str
    worker_id: str
    intent: str
    acceptance: str | None
    owner_department: str
    command_id: str


class GoalScheduler:
    """Persistent single-writer model for Goals and five Worker lifecycles."""

    def __init__(
        self,
        root: str | Path,
        *,
        max_workers: int = 5,
        goal_timeout_secs: int = 10800,
    ):
        if max_workers <= 0:
            raise ValueError("max_workers must be positive")
        if goal_timeout_secs <= 0:
            raise ValueError("goal_timeout_secs must be positive")
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.max_workers = max_workers
        self.goal_timeout_secs = goal_timeout_secs
        self._lock_path = self.root / ".scheduler.lock"
        self._sequence_path = self.root / "sequence.json"

    def _path(self, goal_id: str) -> Path:
        return self.root / f"{goal_id}.json"

    def _load(self, goal_id: str) -> dict:
        goal = read_json(self._path(goal_id))
        if not isinstance(goal, dict):
            raise GoalError(f"no such goal: {goal_id}")
        return goal

    def _save(self, goal: dict) -> None:
        goal["updated_at"] = _now()
        atomic_write_json(self._path(goal["id"]), goal)

    def _next_sequence(self) -> int:
        row = read_json(self._sequence_path, default={})
        current = int(row.get("last", 0)) if isinstance(row, dict) else 0
        value = current + 1
        atomic_write_json(self._sequence_path, {"last": value})
        return value

    def get(self, goal_id: str) -> dict:
        return self._load(goal_id)

    def list_goals(self, *, owner_department: str | None = None) -> list[dict]:
        rows = []
        for path in self.root.glob("goal-*.json"):
            row = read_json(path)
            if not isinstance(row, dict):
                continue
            if owner_department is None or row["owner_department"] == owner_department:
                rows.append(row)
        return sorted(rows, key=lambda row: row["enqueue_seq"])

    def create_goal(
        self,
        *,
        owner_department: str,
        intent: str,
        acceptance: str | None,
        request_id: str,
    ) -> str:
        owner_department = require_identifier(owner_department, label="department id")
        if not isinstance(intent, str) or not intent.strip():
            raise GoalError("intent must be non-empty")
        if acceptance is not None and (not isinstance(acceptance, str) or not acceptance.strip()):
            raise GoalError("acceptance must be non-empty when provided")
        goal_id = _goal_id(request_id)
        with file_lock(self._lock_path):
            if self._path(goal_id).is_file():
                return goal_id
            now = _now()
            goal = {
                "id": goal_id,
                "owner_department": owner_department,
                "intent": intent.strip(),
                "acceptance": acceptance.strip() if acceptance else None,
                "status": OPEN,
                "enqueue_seq": self._next_sequence(),
                "worker_id": None,
                "worker_state": None,
                "start_command_pending": False,
                "start_attempts": 0,
                "last_start_failure_operation": None,
                "deadline_at": None,
                "attempts": 0,
                "latest_feedback": None,
                "last_result_operation": None,
                "last_turn_failure_operation": None,
                "session_token": None,
                "active_review_id": None,
                "last_review_id": None,
                "cancelled_by": None,
                "cancel_reason": None,
                "cancelled_at": None,
                "created_at": now,
                "updated_at": now,
            }
            self._save(goal)
        return goal_id

    def _active_worker_count(self) -> int:
        return sum(
            1 for goal in self.list_goals() if goal.get("worker_state") in ACTIVE_WORKER_STATES
        )

    @staticmethod
    def _launch(goal: dict) -> WorkerLaunch:
        return WorkerLaunch(
            goal_id=goal["id"],
            worker_id=goal["worker_id"],
            intent=goal["intent"],
            acceptance=goal.get("acceptance"),
            owner_department=goal["owner_department"],
            command_id=f"start:{goal['id']}:{goal['start_attempts']}",
        )

    def schedule_one(self) -> WorkerLaunch | None:
        """Return one start command, preserving head-of-line retry semantics.

        A failed/in-flight start remains ahead of later open Goals.  After its
        successful ``worker_started`` acknowledgement, the next call may claim
        the following Goal; a fast Hub loop still fills all five slots.
        """
        with file_lock(self._lock_path):
            starting = [
                goal
                for goal in self.list_goals()
                if goal["status"] == CLAIMED and goal.get("worker_state") == "starting"
            ]
            if starting:
                head = min(starting, key=lambda row: row["enqueue_seq"])
                if head.get("start_command_pending"):
                    head["start_command_pending"] = False
                    self._save(head)
                    return self._launch(head)
                return None
            if self._active_worker_count() >= self.max_workers:
                return None
            opens = [goal for goal in self.list_goals() if goal["status"] == OPEN]
            if not opens:
                return None
            goal = min(opens, key=lambda row: row["enqueue_seq"])
            goal["status"] = CLAIMED
            goal["worker_id"] = f"worker-{goal['enqueue_seq']}"
            goal["worker_state"] = "starting"
            goal["start_attempts"] = 1
            goal["start_command_pending"] = False
            self._save(goal)
            return self._launch(goal)

    def starting_launches(self) -> list[WorkerLaunch]:
        """Reconstruct idempotent start commands after a Hub/Manager restart."""
        return [
            self._launch(goal)
            for goal in self.list_goals()
            if goal["status"] == CLAIMED and goal.get("worker_state") == "starting"
        ]

    def record_session_token(self, goal_id: str, *, worker_id: str, session_token: str) -> None:
        if not session_token:
            return
        with file_lock(self._lock_path):
            goal = self._load(goal_id)
            self._require(
                goal,
                (RUNNING, REPORTED, VERIFYING, DONE, FAILED_TIME, CANCELLED),
                "record_session_token",
            )
            self._require_worker(goal, worker_id)
            goal["session_token"] = session_token
            self._save(goal)

    def worker_turn_failed(
        self,
        goal_id: str,
        *,
        worker_id: str,
        reason: str,
        operation_id: str | None = None,
    ) -> bool:
        """Retry a runtime/tool failure on the same Worker before the deadline.

        A late manager report after ``submit_result`` or a terminal race is a
        harmless no-op.  This failure is not a Goal terminal state and never
        creates a replacement Worker.
        """
        if not isinstance(reason, str) or not reason.strip():
            raise GoalError("worker turn failure reason must be non-empty")
        with file_lock(self._lock_path):
            goal = self._load(goal_id)
            self._require_worker(goal, worker_id)
            if operation_id and goal.get("last_turn_failure_operation") == operation_id:
                return False
            if goal["status"] != RUNNING:
                return False
            goal["worker_state"] = "resuming"
            goal["attempts"] += 1
            goal["latest_feedback"] = reason.strip()
            goal["last_turn_failure_operation"] = operation_id
            self._save(goal)
            return True

    def worker_start_failed(
        self,
        goal_id: str,
        *,
        worker_id: str,
        reason: str,
        operation_id: str | None = None,
    ) -> bool:
        with file_lock(self._lock_path):
            goal = self._load(goal_id)
            if operation_id and goal.get("last_start_failure_operation") == operation_id:
                return False
            self._require(goal, (CLAIMED,), "worker_start_failed")
            self._require_worker(goal, worker_id)
            goal["worker_state"] = "starting"
            goal["start_attempts"] += 1
            goal["start_command_pending"] = True
            goal["latest_feedback"] = reason
            goal["last_start_failure_operation"] = operation_id
            self._save(goal)
            return True

    def worker_started(self, goal_id: str, *, worker_id: str, started_at: float | None = None) -> None:
        with file_lock(self._lock_path):
            goal = self._load(goal_id)
            if (
                goal["status"] == RUNNING
                and goal.get("worker_id") == worker_id
                and goal.get("deadline_at") is not None
            ):
                return
            self._require(goal, (CLAIMED,), "worker_started")
            self._require_worker(goal, worker_id)
            if goal.get("deadline_at") is not None:
                raise GoalError("deadline_at is immutable once written")
            started = _now() if started_at is None else float(started_at)
            goal["status"] = RUNNING
            goal["worker_state"] = "running"
            goal["deadline_at"] = started + self.goal_timeout_secs
            # A transient container-start error is useful while the head is
            # retrying, but becomes a misleading "current" problem after the
            # same Worker successfully starts.  start_attempts and the last
            # operation id retain the audit history.
            goal["latest_feedback"] = None
            self._save(goal)

    def submit_result(
        self,
        goal_id: str,
        *,
        worker_id: str,
        session_token: str | None,
        operation_id: str | None = None,
    ) -> bool:
        with file_lock(self._lock_path):
            goal = self._load(goal_id)
            if operation_id and goal.get("last_result_operation") == operation_id:
                return False
            self._require(goal, (RUNNING,), "submit_result")
            self._require_worker(goal, worker_id)
            goal["status"] = REPORTED
            goal["worker_state"] = "awaiting_verdict"
            # Older V7 ledgers may still carry the former Worker-authored
            # result payload.  A completion declaration never consumes or
            # republishes it, so prune it when this Goal next advances.
            goal.pop("latest_summary", None)
            goal.pop("company_refs", None)
            goal["session_token"] = session_token
            goal["last_result_operation"] = operation_id
            self._save(goal)
            return True

    def begin_verification(self, goal_id: str, *, review_id: str) -> None:
        with file_lock(self._lock_path):
            goal = self._load(goal_id)
            if goal["status"] == VERIFYING and goal.get("active_review_id") == review_id:
                return
            self._require(goal, (REPORTED,), "begin_verification")
            goal["status"] = VERIFYING
            goal["active_review_id"] = review_id
            self._save(goal)

    def verification_passed(self, goal_id: str, *, review_id: str) -> bool:
        with file_lock(self._lock_path):
            goal = self._load(goal_id)
            if goal.get("last_review_id") == review_id and goal["status"] == DONE:
                return False
            self._require_review(goal, review_id)
            self._require(goal, (VERIFYING,), "verification_passed")
            goal["status"] = DONE
            goal["worker_state"] = "stopping"
            goal["active_review_id"] = None
            goal["last_review_id"] = review_id
            self._save(goal)
            return True

    def verification_failed(self, goal_id: str, *, review_id: str, feedback: str) -> bool:
        if not isinstance(feedback, str) or not feedback.strip():
            raise GoalError("verification feedback must be non-empty")
        with file_lock(self._lock_path):
            goal = self._load(goal_id)
            if goal.get("last_review_id") == review_id and goal["status"] == RUNNING:
                return False
            self._require_review(goal, review_id)
            self._require(goal, (VERIFYING,), "verification_failed")
            goal["status"] = RUNNING
            goal["worker_state"] = "resuming"
            goal["attempts"] += 1
            goal["latest_feedback"] = feedback.strip()
            goal["active_review_id"] = None
            goal["last_review_id"] = review_id
            self._save(goal)
            return True

    def worker_resumed(self, goal_id: str, *, worker_id: str, session_token: str | None) -> None:
        with file_lock(self._lock_path):
            goal = self._load(goal_id)
            if (
                goal["status"] == RUNNING
                and goal.get("worker_id") == worker_id
                and goal.get("worker_state") == "running"
            ):
                return
            self._require(goal, (RUNNING,), "worker_resumed")
            self._require_worker(goal, worker_id)
            if goal.get("worker_state") != "resuming":
                raise GoalError("worker is not awaiting a resume turn")
            goal["worker_state"] = "running"
            if session_token:
                goal["session_token"] = session_token
            self._save(goal)

    def cancel(self, goal_id: str, *, cancelled_by: str, reason: str) -> bool:
        if not isinstance(reason, str) or not reason.strip():
            raise GoalError("cancel reason must be non-empty")
        with file_lock(self._lock_path):
            goal = self._load(goal_id)
            if goal["status"] in TERMINAL:
                return False
            goal["status"] = CANCELLED
            goal["cancelled_by"] = cancelled_by
            goal["cancel_reason"] = reason.strip()
            goal["cancelled_at"] = _now()
            goal["active_review_id"] = None
            goal["worker_state"] = "stopping" if goal.get("worker_id") else None
            self._save(goal)
            return True

    def sweep_deadlines(self, *, now: float | None = None) -> list[dict]:
        timestamp = _now() if now is None else float(now)
        expired: list[dict] = []
        with file_lock(self._lock_path):
            for goal in self.list_goals():
                deadline = goal.get("deadline_at")
                if goal["status"] not in (RUNNING, REPORTED, VERIFYING):
                    continue
                if deadline is None or deadline > timestamp:
                    continue
                review_id = goal.get("active_review_id")
                goal["status"] = FAILED_TIME
                goal["worker_state"] = "stopping"
                goal["active_review_id"] = None
                goal["latest_feedback"] = "goal deadline elapsed before verifier PASS"
                self._save(goal)
                expired.append({"goal_id": goal["id"], "review_id": review_id})
        return expired

    def worker_stopped(self, goal_id: str, *, worker_id: str) -> None:
        with file_lock(self._lock_path):
            goal = self._load(goal_id)
            if (
                goal["status"] in TERMINAL
                and goal.get("worker_id") == worker_id
                and goal.get("worker_state") == "stopped"
            ):
                return
            self._require(goal, TERMINAL, "worker_stopped")
            self._require_worker(goal, worker_id)
            if goal.get("worker_state") != "stopping":
                raise GoalError("worker is not stopping")
            goal["worker_state"] = "stopped"
            self._save(goal)

    def remaining_seconds(self, goal_id: str, *, now: float | None = None) -> float | None:
        goal = self._load(goal_id)
        deadline = goal.get("deadline_at")
        if deadline is None:
            return None
        return max(0.0, deadline - (_now() if now is None else float(now)))

    def inspect(self, *, goal_id: str | None = None, owner_department: str | None = None) -> dict:
        if goal_id:
            goal = self.get(goal_id)
            return {"goal": goal, "max_workers": self.max_workers}
        goals = self.list_goals(owner_department=owner_department)
        counts = {state: 0 for state in (*NON_TERMINAL, *TERMINAL)}
        for goal in goals:
            counts[goal["status"]] += 1
        return {
            "counts": counts,
            "active_workers": self._active_worker_count(),
            "max_workers": self.max_workers,
            "goals": goals,
        }

    @staticmethod
    def _require(goal: dict, allowed: tuple[str, ...], action: str) -> None:
        if goal["status"] not in allowed:
            raise GoalError(
                f"illegal {action}: goal {goal['id']} is {goal['status']!r}; expected {allowed}"
            )

    @staticmethod
    def _require_worker(goal: dict, worker_id: str) -> None:
        if goal.get("worker_id") != worker_id:
            raise GoalError("worker does not own this goal")

    @staticmethod
    def _require_review(goal: dict, review_id: str) -> None:
        if goal.get("active_review_id") != review_id:
            raise GoalError("review does not own this Goal transition")
