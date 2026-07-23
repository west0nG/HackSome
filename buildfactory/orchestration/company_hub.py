"""V7 deterministic Company Hub.

The Hub is the only component that joins resident Agent methods, reliable
Inbox delivery, Goal scheduling, Objective activation, Department creation,
and ephemeral verifier routing.  LLM runtimes never receive paths for these
stores; they see only projections returned by the methods registered here.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable

from orchestration.departments import (
    DepartmentCatalog,
    DepartmentController,
    DepartmentError,
)
from orchestration.inbox import CEO_KEY, FileInbox, make_ime
from orchestration.email_send import send_company_email as dispatch_company_email
from orchestration.mailbox import (
    COMPANY_CAP,
    PEEK_LIMIT,
    CompanyMailStore,
    claim_company_mailbox,
    global_mail_root,
    list_company_mailboxes,
    mail_domain,
    render_message,
)
from orchestration.method_adapter import ActorContext, MethodAdapter, MethodError
from orchestration.notes import NotesStore
from orchestration.objective_store import ObjectiveStore
from orchestration.run_logs import RunLogRecorder
from orchestration.runtime_store import (
    CompanyLayout,
    atomic_write_json,
    file_lock,
    read_json,
    require_identifier,
)
from orchestration.scheduler import NON_TERMINAL, GoalScheduler, WorkerLaunch
from orchestration.verifier_manager import ReviewLaunch, VerifierManager


MESSAGE_MAX_BYTES = 64 * 1024
ALLOWED_MESSAGE_TYPES = frozenset(
    {
        "company_idle",
        "objective_verdict",
        "objective_changed",
        "department_started",
        "provision_failed",
        "department_message",
        "department_escalation",
        "external_event",
        "goal_verifier_failed",
        "goal_done",
        "goal_failed_time",
        "goal_cancelled",
    }
)

CEO_CAPABILITIES = (
    "claim_company_mailbox",
    "list_company_mailboxes",
    "list_department_options",
    "create_department",
    "propose_company_objective",
    "propose_department_objective",
    "cancel_goal",
    "inspect",
    "read_notes",
    "write_notes",
)

DEPARTMENT_CAPABILITIES = (
    "list_company_mailboxes",
    "peek_company_email",
    "send_company_email",
    "create_goal",
    "list_my_goals",
    "cancel_goal",
    "send_department_message",
    "read_notes",
    "write_notes",
)


class HubError(ValueError):
    pass


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_id(prefix: str, *parts: object) -> str:
    raw = "\x1f".join(str(part) for part in parts)
    return f"{prefix}-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def _payload_fields(
    payload: dict,
    *,
    required: set[str] | frozenset[str] = frozenset(),
    optional: set[str] | frozenset[str] = frozenset(),
) -> None:
    keys = set(payload)
    missing = set(required) - keys
    extra = keys - set(required) - set(optional)
    if missing:
        raise HubError(f"missing payload fields: {sorted(missing)}")
    if extra:
        raise HubError(f"unknown payload fields: {sorted(extra)}")


class CompanyHub:
    """Persistent V7 control plane for one brand-new company."""

    def __init__(
        self,
        root: str | os.PathLike,
        *,
        department_specs_path: str | os.PathLike | None = None,
        max_workers: int = 5,
        max_verifiers: int = 3,
        goal_timeout_secs: int = 10800,
        company_id: str | None = None,
        mail_global_root: str | os.PathLike | None = None,
    ):
        self.layout = CompanyLayout.initialize(root)
        self.company_id = require_identifier(
            company_id or self.layout.root.name,
            label="company id",
        )
        self.mail_global_root = Path(
            mail_global_root or (self.layout.root.parent / "_mail")
        ).resolve()
        self.mail_store = CompanyMailStore(self.layout.mailboxes)
        department_specs_path = department_specs_path or (
            Path(__file__).resolve().parents[1] / "agents" / "departments"
        )
        self.inbox = FileInbox(self.layout.inbox, poll_tick=0.05)
        self.scheduler = GoalScheduler(
            self.layout.ledger,
            max_workers=max_workers,
            goal_timeout_secs=goal_timeout_secs,
        )
        self.reviews = VerifierManager(self.layout.reviews, max_instances=max_verifiers)
        self.objectives = ObjectiveStore(self.layout.agents, self.reviews)
        self.departments = DepartmentController(
            self.layout.departments,
            catalog=DepartmentCatalog.load(department_specs_path),
            objectives=self.objectives,
        )
        self.notes = NotesStore(self.layout.notes)
        self.adapter = MethodAdapter(self.layout)
        self._hub_lock = self.layout.control / ".hub.lock"
        self._idle_path = self.layout.control / "idle.json"
        self._idle_sequence_path = self.layout.control / "idle-sequence.json"
        self._register_methods()

    # -- method boundary -------------------------------------------------

    def _register(
        self,
        method: str,
        actors: set[str],
        handler: Callable[[ActorContext, dict, str], object],
        *,
        cache_response: bool = True,
        audit_result: Callable[[object], object] | None = None,
    ) -> None:
        def guarded(actor: ActorContext, payload: dict, request_id: str):
            try:
                with file_lock(self._hub_lock):
                    return handler(actor, payload, request_id)
            except MethodError:
                raise
            except (ValueError, RuntimeError) as exc:
                raise MethodError("invalid_state", str(exc)) from exc

        self.adapter.register(  # type: ignore[arg-type]
            method,
            actors=actors,
            handler=guarded,
            cache_response=cache_response,
            audit_result=audit_result,
        )

    def _register_methods(self) -> None:
        self._register("wake_context", {"ceo", "department"}, self._wake_context)
        self._register("peek_message", {"ceo", "department"}, self._peek_message)
        self._register("ack_message", {"ceo", "department"}, self._ack_message_method)
        self._register("wake_completed", {"ceo", "department"}, self._wake_completed)

        self._register("list_department_options", {"ceo"}, self._list_department_options)
        self._register("create_department", {"ceo"}, self._create_department)
        self._register("propose_company_objective", {"ceo"}, self._propose_company_objective)
        self._register("propose_department_objective", {"ceo"}, self._propose_department_objective)
        self._register("inspect", {"ceo"}, self._inspect)
        self._register("claim_company_mailbox", {"ceo"}, self._claim_company_mailbox)
        self._register(
            "list_company_mailboxes",
            {"ceo", "department", "worker"},
            self._list_company_mailboxes,
        )
        self._register(
            "peek_company_email",
            {"department", "worker"},
            self._peek_company_email,
            cache_response=False,
            audit_result=self._mail_peek_audit_result,
        )
        self._register(
            "send_company_email",
            {"department", "worker"},
            self._send_company_email,
        )

        self._register("create_goal", {"department"}, self._create_goal)
        self._register("list_my_goals", {"department"}, self._list_my_goals)
        self._register(
            "send_department_message",
            {"department"},
            self._send_department_message,
        )
        self._register("cancel_goal", {"ceo", "department"}, self._cancel_goal)
        self._register("read_notes", {"ceo", "department"}, self._read_notes)
        self._register("write_notes", {"ceo", "department"}, self._write_notes)

        self._register("submit_result", {"worker"}, self._submit_result)
        self._register("submit_verdict", {"verifier"}, self._submit_verdict)

        self._register("worker_started", {"manager"}, self._worker_started)
        self._register("worker_start_failed", {"manager"}, self._worker_start_failed)
        self._register("worker_resumed", {"manager"}, self._worker_resumed)
        self._register("worker_turn_finished", {"manager"}, self._worker_turn_finished)
        self._register("worker_stopped", {"manager"}, self._worker_stopped)
        self._register(
            "verifier_instance_stopped",
            {"manager"},
            self._verifier_instance_stopped,
        )
        self._register(
            "verifier_instance_failed",
            {"manager"},
            self._verifier_instance_failed,
        )
        self._register("department_started", {"manager"}, self._department_started)
        self._register(
            "department_provision_failed",
            {"manager"},
            self._department_provision_failed,
        )
        self._register("deliver_external_event", {"manager"}, self._deliver_external_event)

    def call(self, actor: ActorContext, request: object) -> dict:
        return self.adapter.call(actor, request)

    # -- projections / actor checks -------------------------------------

    def _require_resident(self, actor: ActorContext) -> None:
        if actor.kind == "ceo":
            if actor.actor_id != CEO_KEY:
                raise HubError("CEO actor_id must be ceo")
            return
        if actor.kind != "department" or actor.actor_id != actor.department_id:
            raise HubError("Department actor context is not self-bound")
        self.departments.get(actor.actor_id)

    @staticmethod
    def _require_manager(actor: ActorContext, manager_id: str) -> None:
        if actor.kind != "manager" or actor.actor_id != manager_id:
            raise HubError(f"method requires {manager_id}")

    def _require_worker_goal(self, actor: ActorContext) -> dict:
        if actor.kind != "worker" or not actor.goal_id:
            raise HubError("Worker context has no Goal")
        goal = self.scheduler.get(actor.goal_id)
        if goal.get("worker_id") != actor.actor_id:
            raise HubError("Worker does not own this Goal")
        if goal.get("status") not in NON_TERMINAL:
            raise HubError("Worker Goal is no longer active")
        return goal

    def _require_mail_reader_or_sender(self, actor: ActorContext) -> dict | None:
        if actor.kind == "department":
            self._require_resident(actor)
            return None
        return self._require_worker_goal(actor)

    @staticmethod
    def _mail_peek_audit_result(result: object) -> dict:
        messages = result.get("messages", []) if isinstance(result, dict) else []
        timestamps = [
            float(message["received_at"])
            for message in messages
            if isinstance(message, dict)
            and isinstance(message.get("received_at"), (int, float))
        ]
        return {
            "redacted": True,
            "count": len(messages),
            "oldest_received_at": min(timestamps) if timestamps else None,
            "newest_received_at": max(timestamps) if timestamps else None,
        }

    # -- Company mail --------------------------------------------------

    def _claim_company_mailbox(
        self, actor: ActorContext, payload: dict, request_id: str
    ) -> dict:
        _payload_fields(payload, required={"name"}, optional={"label"})
        self._require_resident(actor)
        return claim_company_mailbox(
            self.company_id,
            payload["name"],
            label=payload.get("label"),
            root=self.mail_global_root,
        )

    def _mailbox_projection(self) -> dict:
        rows = list_company_mailboxes(self.company_id, root=self.mail_global_root)
        mailboxes = [
            {
                "name": row["name"],
                "address": f"{row['name']}@{mail_domain()}",
                "label": row.get("label"),
                "claimed_at": row.get("claimed_at"),
            }
            for row in rows
        ]
        return {
            "mailboxes": mailboxes,
            "used": len(mailboxes),
            "limit": COMPANY_CAP,
        }

    def _list_company_mailboxes(
        self, actor: ActorContext, payload: dict, request_id: str
    ) -> dict:
        _payload_fields(payload)
        if actor.kind == "worker":
            self._require_worker_goal(actor)
        else:
            self._require_resident(actor)
        return self._mailbox_projection()

    def _peek_company_email(
        self, actor: ActorContext, payload: dict, request_id: str
    ) -> dict:
        _payload_fields(payload)
        goal = self._require_mail_reader_or_sender(actor)
        since = float(goal["created_at"]) if goal is not None else None
        messages = self.mail_store.peek(since=since, limit=PEEK_LIMIT)
        return {"messages": messages, "count": len(messages)}

    def _send_company_email(
        self, actor: ActorContext, payload: dict, request_id: str
    ) -> dict:
        _payload_fields(
            payload,
            required={"mailbox", "to", "subject", "text"},
            optional={"html", "from_name"},
        )
        self._require_mail_reader_or_sender(actor)
        return dispatch_company_email(
            company=self.company_id,
            global_mail_root=self.mail_global_root,
            company_mail_root=self.layout.mailboxes,
            by=actor.actor_id,
            request_id=request_id,
            sender=payload["mailbox"],
            to=payload["to"],
            subject=payload["subject"],
            text=payload["text"],
            html=payload.get("html"),
            from_name=payload.get("from_name"),
        )

    def _wake_context(self, actor: ActorContext, payload: dict, request_id: str) -> dict:
        _payload_fields(payload)
        self._require_resident(actor)
        capabilities = CEO_CAPABILITIES if actor.kind == "ceo" else DEPARTMENT_CAPABILITIES
        return {
            "actor_id": actor.actor_id,
            "objective": self.objectives.current(actor.actor_id),
            "objective_revision": self.objectives.active_metadata(actor.actor_id),
            "objective_reviews_in_flight": self.objectives.in_review(
                requested_by=CEO_KEY if actor.kind == "ceo" else None,
                actor_id=None if actor.kind == "ceo" else actor.actor_id,
            ),
            "notes": self.notes.read(actor.actor_id),
            "capabilities": list(capabilities),
        }

    def _list_department_options(
        self, actor: ActorContext, payload: dict, request_id: str
    ) -> list[dict]:
        _payload_fields(payload)
        self._require_resident(actor)
        return self.departments.list_options()

    def _read_notes(self, actor: ActorContext, payload: dict, request_id: str) -> dict:
        _payload_fields(payload)
        self._require_resident(actor)
        return {"text": self.notes.read(actor.actor_id)}

    def _write_notes(self, actor: ActorContext, payload: dict, request_id: str) -> dict:
        _payload_fields(payload, required={"text"})
        self._require_resident(actor)
        return self.notes.write(actor.actor_id, payload["text"], request_id=request_id)

    # -- Objective / Department ----------------------------------------

    def _propose_company_objective(
        self, actor: ActorContext, payload: dict, request_id: str
    ) -> dict:
        _payload_fields(payload, required={"objective"})
        self._require_resident(actor)
        proposal = self.objectives.propose(
            actor_id=CEO_KEY,
            objective_kind="company",
            text=payload["objective"],
            requested_by=CEO_KEY,
            request_id=request_id,
        )
        self._schedule_verifiers()
        self._ensure_idle()
        return proposal

    def _propose_department_objective(
        self, actor: ActorContext, payload: dict, request_id: str
    ) -> dict:
        _payload_fields(payload, required={"department_id", "objective"})
        self._require_resident(actor)
        department_id = payload["department_id"]
        self.departments.get(department_id)
        proposal = self.objectives.propose(
            actor_id=department_id,
            objective_kind="department",
            text=payload["objective"],
            requested_by=CEO_KEY,
            request_id=request_id,
        )
        self._schedule_verifiers()
        return proposal

    def _create_department(
        self, actor: ActorContext, payload: dict, request_id: str
    ) -> dict:
        _payload_fields(payload, required={"option_id", "initial_objective"})
        self._require_resident(actor)
        request = self.departments.request_creation(
            option_id=payload["option_id"],
            initial_objective=payload["initial_objective"],
            requested_by=CEO_KEY,
            request_id=request_id,
        )
        self._schedule_verifiers()
        return request

    def _department_started(
        self, actor: ActorContext, payload: dict, request_id: str
    ) -> dict:
        self._require_manager(actor, "department-provisioner")
        _payload_fields(payload, required={"creation_id", "service_name"})
        department = self.departments.mark_active(
            payload["creation_id"], service_name=payload["service_name"]
        )
        self._message(
            to=department["id"],
            message_type="department_started",
            text=f"{department['name']} 已启动",
            sender="system",
            data={
                "department_id": department["id"],
                "objective": self.objectives.current(department["id"]),
            },
            message_id=_stable_id("msg", "department-started", payload["creation_id"]),
        )
        self._message(
            to=CEO_KEY,
            message_type="department_started",
            text=f"Department {department['id']} 已启动",
            sender="system",
            data={"department_id": department["id"]},
            message_id=_stable_id("msg", "ceo-department-started", payload["creation_id"]),
        )
        self._ensure_idle()
        return department

    def _department_provision_failed(
        self, actor: ActorContext, payload: dict, request_id: str
    ) -> dict:
        self._require_manager(actor, "department-provisioner")
        _payload_fields(payload, required={"creation_id", "reason"})
        row = self.departments.mark_provision_failed(
            payload["creation_id"], reason=payload["reason"]
        )
        self._message(
            to=CEO_KEY,
            message_type="provision_failed",
            text=f"Department {row['option_id']} 启动失败",
            sender="system",
            data={"department_id": row["option_id"], "reason": row["reason"]},
            message_id=_stable_id("msg", "provision-failed", payload["creation_id"]),
        )
        self._ensure_idle()
        return row

    # -- Goal methods ---------------------------------------------------

    def _create_goal(self, actor: ActorContext, payload: dict, request_id: str) -> dict:
        _payload_fields(payload, required={"intent"}, optional={"acceptance"})
        self._require_resident(actor)
        goal_id = self.scheduler.create_goal(
            owner_department=actor.actor_id,
            intent=payload["intent"],
            acceptance=payload.get("acceptance"),
            request_id=request_id,
        )
        self._schedule_workers()
        self._ensure_idle()
        return self._goal_projection(self.scheduler.get(goal_id))

    def _list_my_goals(self, actor: ActorContext, payload: dict, request_id: str) -> dict:
        _payload_fields(payload)
        self._require_resident(actor)
        return {
            "goals": [
                self._goal_projection(row)
                for row in self.scheduler.list_goals(owner_department=actor.actor_id)
            ]
        }

    def _cancel_goal(self, actor: ActorContext, payload: dict, request_id: str) -> dict:
        _payload_fields(payload, required={"goal_id", "reason"})
        if actor.kind in ("ceo", "department"):
            self._require_resident(actor)
        goal = self.scheduler.get(payload["goal_id"])
        if actor.kind == "department" and goal["owner_department"] != actor.actor_id:
            raise HubError("Department can cancel only its own Goal")
        review_id = goal.get("active_review_id")
        changed = self.scheduler.cancel(
            goal["id"], cancelled_by=actor.actor_id, reason=payload["reason"]
        )
        goal = self.scheduler.get(goal["id"])
        if changed and review_id:
            self.reviews.cancel(review_id, reason="Goal cancelled")
        if goal.get("worker_id") and goal.get("worker_state") == "stopping":
            self._write_worker_stop(goal)
        if changed:
            self._message_goal(goal, "goal_cancelled", "Goal 已取消")
        self._emit_stopping_verifiers()
        self._ensure_idle()
        return {"changed": changed, "goal": self._goal_projection(goal)}

    def _submit_result(self, actor: ActorContext, payload: dict, request_id: str) -> dict:
        _payload_fields(payload)
        if not actor.goal_id:
            raise HubError("Worker context has no Goal")
        self._expire_due_goals()
        goal = self.scheduler.get(actor.goal_id)
        if goal.get("worker_id") != actor.actor_id:
            raise HubError("Worker does not own this Goal")
        changed = self.scheduler.submit_result(
            actor.goal_id,
            worker_id=actor.actor_id,
            session_token=goal.get("session_token"),
            operation_id=request_id,
        )
        goal = self.scheduler.get(actor.goal_id)
        if not changed and goal["status"] != "reported":
            return {
                "goal_id": goal["id"],
                "review_id": goal.get("active_review_id") or goal.get("last_review_id"),
                "status": goal["status"],
            }
        review_id = self.reviews.enqueue(
            kind="goal_result",
            subject_id=goal["id"],
            requested_by=actor.actor_id,
            payload={
                "goal_id": goal["id"],
                "owner_department": goal["owner_department"],
                "intent": goal["intent"],
                "acceptance": goal.get("acceptance"),
                "deadline_at": goal["deadline_at"],
            },
            request_id=f"goal-result:{request_id}",
        )
        self.scheduler.begin_verification(goal["id"], review_id=review_id)
        self._schedule_verifiers()
        return {"goal_id": goal["id"], "review_id": review_id, "status": "verifying"}

    # -- Worker Manager callbacks --------------------------------------

    def _worker_started(self, actor: ActorContext, payload: dict, request_id: str) -> dict:
        self._require_manager(actor, "worker-manager")
        _payload_fields(payload, required={"goal_id", "worker_id"}, optional={"started_at"})
        self.scheduler.worker_started(
            payload["goal_id"],
            worker_id=payload["worker_id"],
            started_at=payload.get("started_at"),
        )
        self._schedule_workers()
        return self._goal_projection(self.scheduler.get(payload["goal_id"]))

    def _worker_start_failed(
        self, actor: ActorContext, payload: dict, request_id: str
    ) -> dict:
        self._require_manager(actor, "worker-manager")
        _payload_fields(payload, required={"goal_id", "worker_id", "reason"})
        self.scheduler.worker_start_failed(
            payload["goal_id"],
            worker_id=payload["worker_id"],
            reason=payload["reason"],
            operation_id=request_id,
        )
        self._schedule_workers()
        return self._goal_projection(self.scheduler.get(payload["goal_id"]))

    def _worker_resumed(self, actor: ActorContext, payload: dict, request_id: str) -> dict:
        self._require_manager(actor, "worker-manager")
        _payload_fields(
            payload,
            required={"goal_id", "worker_id"},
            optional={"session_token"},
        )
        self._expire_due_goals()
        self.scheduler.worker_resumed(
            payload["goal_id"],
            worker_id=payload["worker_id"],
            session_token=payload.get("session_token"),
        )
        return self._goal_projection(self.scheduler.get(payload["goal_id"]))

    def _worker_turn_finished(
        self, actor: ActorContext, payload: dict, request_id: str
    ) -> dict:
        self._require_manager(actor, "worker-manager")
        _payload_fields(
            payload,
            required={"goal_id", "worker_id", "ok"},
            optional={"session_token", "error"},
        )
        self._expire_due_goals()
        if payload.get("session_token"):
            self.scheduler.record_session_token(
                payload["goal_id"],
                worker_id=payload["worker_id"],
                session_token=payload["session_token"],
            )
        goal = self.scheduler.get(payload["goal_id"])
        # A fast Verifier may FAIL after submit_result but before this model
        # process exits. In that race the Goal is already running/resuming and
        # a resume command with the real verifier feedback already exists;
        # never overwrite it with "turn ended without submit_result".
        if goal["status"] == "running" and goal.get("worker_state") == "running":
            reason = (
                payload.get("error")
                if not payload["ok"]
                else "Worker turn ended without submit_result"
            ) or "Worker runtime failed"
            changed = self.scheduler.worker_turn_failed(
                payload["goal_id"],
                worker_id=payload["worker_id"],
                reason=reason,
                operation_id=request_id,
            )
            goal = self.scheduler.get(payload["goal_id"])
            if changed:
                self._write_worker_resume(goal)
        return self._goal_projection(goal)

    def _worker_stopped(self, actor: ActorContext, payload: dict, request_id: str) -> dict:
        self._require_manager(actor, "worker-manager")
        _payload_fields(payload, required={"goal_id", "worker_id"})
        self.scheduler.worker_stopped(payload["goal_id"], worker_id=payload["worker_id"])
        self._schedule_workers()
        self._ensure_idle()
        return self._goal_projection(self.scheduler.get(payload["goal_id"]))

    # -- Verifier methods / routing ------------------------------------

    def _submit_verdict(self, actor: ActorContext, payload: dict, request_id: str) -> dict:
        _payload_fields(
            payload,
            required={"verdict", "reason"},
            optional={"review_id"},
        )
        if not actor.review_id:
            raise HubError("Verifier context has no review")
        if payload.get("review_id") not in (None, actor.review_id):
            raise HubError("Verifier can submit only its bound review")
        # A verifier response arriving after the immutable Goal deadline loses
        # the race even if the periodic watchdog has not fired yet.
        self._expire_due_goals()
        review = self.reviews.get(actor.review_id)
        if review.get("instance_id") != actor.actor_id:
            raise HubError("Verifier instance does not own this review")
        accepted = self.reviews.submit_verdict(
            actor.review_id,
            instance_id=actor.actor_id,
            verdict=payload["verdict"],
            reason=payload["reason"],
        )
        if accepted:
            self._route_review(self.reviews.get(actor.review_id))
            self.reviews.mark_routed(actor.review_id)
        self._emit_stopping_verifiers()
        self._schedule_verifiers()
        self._ensure_idle()
        return {"accepted": accepted, "review": self._review_projection(self.reviews.get(actor.review_id))}

    def _verifier_instance_stopped(
        self, actor: ActorContext, payload: dict, request_id: str
    ) -> dict:
        self._require_manager(actor, "verifier-manager")
        _payload_fields(payload, required={"review_id", "instance_id"})
        changed = self.reviews.confirm_instance_stopped(
            payload["review_id"], instance_id=payload["instance_id"]
        )
        self._schedule_verifiers()
        return {"changed": changed, "pool": self.reviews.inspect_pool()}

    def _verifier_instance_failed(
        self, actor: ActorContext, payload: dict, request_id: str
    ) -> dict:
        self._require_manager(actor, "verifier-manager")
        _payload_fields(payload, required={"review_id", "instance_id", "reason"})
        changed = self.reviews.instance_failed(
            payload["review_id"],
            instance_id=payload["instance_id"],
            reason=payload["reason"],
        )
        self._schedule_verifiers()
        return {"changed": changed, "pool": self.reviews.inspect_pool()}

    def _route_review(self, review: dict) -> None:
        if review["kind"] in ("company_objective", "department_objective"):
            proposal = self.objectives.apply_review(review["id"])
            self._message(
                to=CEO_KEY,
                message_type="objective_verdict",
                text=f"Objective 审核 {review['verdict']}",
                sender="verifier",
                data={
                    "actor_id": proposal["actor_id"],
                    "revision": proposal["revision"],
                    "verdict": review["verdict"],
                    "reason": review["reason"],
                },
                message_id=_stable_id("msg", "objective-verdict", review["id"]),
            )
            if proposal["status"] == "active":
                if proposal["actor_id"] == CEO_KEY:
                    self._message(
                        to=CEO_KEY,
                        message_type="objective_changed",
                        text="Company Objective 已生效",
                        sender="system",
                        data={"revision": proposal["revision"]},
                        message_id=_stable_id("msg", "objective-changed", review["id"]),
                    )
                else:
                    try:
                        self.departments.get(proposal["actor_id"])
                    except DepartmentError:
                        pass
                    else:
                        self._message(
                            to=proposal["actor_id"],
                            message_type="objective_changed",
                            text="Department Objective 已生效",
                            sender="system",
                            data={"revision": proposal["revision"]},
                            message_id=_stable_id(
                                "msg", "department-objective-changed", review["id"]
                            ),
                        )
            self._reconcile_creation_for_review(review["id"])
            return

        goal = self.scheduler.get(review["subject_id"])
        if goal["status"] in ("done", "failed_time", "cancelled") and not (
            review["verdict"] == "PASS"
            and goal["status"] == "done"
            and goal.get("last_review_id") == review["id"]
        ):
            # A later explicit cancel/time failure wins over an unrouted
            # verdict. The review is still marked routed by the caller.
            return
        if review["verdict"] == "PASS":
            self.scheduler.verification_passed(goal["id"], review_id=review["id"])
            goal = self.scheduler.get(goal["id"])
            if goal["status"] == "done" and goal.get("last_review_id") == review["id"]:
                self._message_goal(goal, "goal_done", "Goal 已通过验收")
                self._write_worker_stop(goal)
            return
        self.scheduler.verification_failed(
            goal["id"], review_id=review["id"], feedback=review["reason"]
        )
        goal = self.scheduler.get(goal["id"])
        if goal["status"] == "running" and goal.get("last_review_id") == review["id"]:
            self._message_goal(goal, "goal_verifier_failed", "Goal 需要继续返工")
            self._write_worker_resume(goal)

    def _reconcile_creation_for_review(self, review_id: str) -> None:
        for path in (self.layout.departments / "requests").glob("department-*.json"):
            row = read_json(path)
            if not isinstance(row, dict) or row.get("objective_review_id") != review_id:
                continue
            self.departments.reconcile_creation(row["id"])
            return

    # -- Inbox / reliable wake -----------------------------------------

    def _peek_message(self, actor: ActorContext, payload: dict, request_id: str):
        _payload_fields(payload)
        self._require_resident(actor)
        return {"message": self.inbox.peek_one(actor.actor_id)}

    def _ack_receipt_path(self, actor_id: str, message_id: str) -> Path:
        digest = hashlib.sha256(message_id.encode("utf-8")).hexdigest()
        return self.layout.control / "acks" / actor_id / f"{digest}.json"

    def _ack_bound_message(self, actor_id: str, message_id: str) -> bool:
        if not isinstance(message_id, str) or not message_id:
            raise HubError("message_id must be non-empty")
        receipt = self._ack_receipt_path(actor_id, message_id)
        if receipt.is_file():
            return False
        head = self.inbox.peek_one(actor_id)
        if not head or head.get("id") != message_id:
            if self.inbox.was_consumed(actor_id, message_id):
                atomic_write_json(
                    receipt,
                    {
                        "actor_id": actor_id,
                        "message_id": message_id,
                        "acked_at": _utc_now(),
                        "recovered_after_cursor_advance": True,
                    },
                )
                return False
            raise HubError("message is not the current FIFO head")
        self.inbox.ack_one(actor_id)
        atomic_write_json(
            receipt,
            {"actor_id": actor_id, "message_id": message_id, "acked_at": _utc_now()},
        )
        return True

    def _ack_message_method(
        self, actor: ActorContext, payload: dict, request_id: str
    ) -> dict:
        _payload_fields(payload, required={"message_id"})
        self._require_resident(actor)
        changed = self._ack_bound_message(actor.actor_id, payload["message_id"])
        self._clear_idle(actor.actor_id, payload["message_id"])
        self._ensure_idle()
        return {"acked": changed, "message_id": payload["message_id"]}

    def _wake_completed(self, actor: ActorContext, payload: dict, request_id: str) -> dict:
        _payload_fields(
            payload,
            required={"wake_id", "finished_at"},
            optional={"message_id"},
        )
        self._require_resident(actor)
        message_id = payload.get("message_id")
        acked = False
        if message_id is not None:
            acked = self._ack_bound_message(actor.actor_id, message_id)
            self._clear_idle(actor.actor_id, message_id)
        completion_path = self.layout.control / "wake-completions" / f"{payload['wake_id']}.json"
        atomic_write_json(
            completion_path,
            {
                "agent_id": actor.actor_id,
                "message_id": message_id,
                "wake_id": payload["wake_id"],
                "finished_at": payload["finished_at"],
            },
        )
        self._ensure_idle()
        return {"recorded": True, "acked": acked}

    def _send_department_message(
        self, actor: ActorContext, payload: dict, request_id: str
    ) -> dict:
        _payload_fields(payload, required={"to", "subject", "body"})
        self._require_resident(actor)
        self.departments.get(payload["to"])
        if not isinstance(payload["subject"], str) or not payload["subject"].strip():
            raise HubError("subject must be non-empty text")
        if not isinstance(payload["body"], str) or not payload["body"].strip():
            raise HubError("body must be non-empty text")
        message_id = _stable_id("msg", "department-message", actor.actor_id, request_id)
        message = self._message(
            to=payload["to"],
            message_type="department_message",
            text=payload["subject"].strip(),
            sender=actor.actor_id,
            data={
                "subject": payload["subject"].strip(),
                "body": payload["body"].strip(),
            },
            message_id=message_id,
        )
        return {
            "message_id": message["id"],
            "time": message["time"],
            "from": actor.actor_id,
            "to": payload["to"],
            "subject": payload["subject"].strip(),
            "body": payload["body"].strip(),
        }

    def _deliver_external_event(
        self, actor: ActorContext, payload: dict, request_id: str
    ) -> dict:
        self._require_manager(actor, "peripheral")
        _payload_fields(
            payload,
            required={"to", "text", "body", "message_id"},
            optional={"time"},
        )
        target = payload["to"] or CEO_KEY
        if not isinstance(payload["text"], str) or not payload["text"].strip():
            raise HubError("external event text must be non-empty")
        if not isinstance(payload["message_id"], str) or not payload["message_id"]:
            raise HubError("external event message_id must be non-empty")
        message = self._message(
            to=target,
            message_type="external_event",
            text=payload["text"].strip(),
            sender="external",
            data={
                "body": payload["body"],
                "source_time": payload.get("time"),
                "source_message_id": payload["message_id"],
            },
            message_id=_stable_id(
                "msg", "external-event", target, payload["message_id"]
            ),
        )
        return {"message_id": message["id"], "to": target}

    def _message(
        self,
        *,
        to: str,
        message_type: str,
        text: str,
        sender: str,
        data: dict,
        message_id: str,
    ) -> dict:
        if message_type not in ALLOWED_MESSAGE_TYPES:
            raise HubError(f"unknown message type: {message_type}")
        if to != CEO_KEY:
            self.departments.get(to)
        body = {"v": 1, "type": message_type, "from": sender, "data": data}
        event = make_ime(to, text, body, id=message_id)
        encoded = json.dumps(event, ensure_ascii=False).encode("utf-8")
        if len(encoded) > MESSAGE_MAX_BYTES:
            raise HubError(f"message exceeds {MESSAGE_MAX_BYTES} bytes")
        self.inbox.append(to, event)
        return event

    def _message_goal(self, goal: dict, message_type: str, text: str) -> None:
        self._message(
            to=goal["owner_department"],
            message_type=message_type,
            text=text,
            sender="system",
            data={
                "goal_id": goal["id"],
                "status": goal["status"],
                "feedback": goal.get("latest_feedback"),
            },
            message_id=_stable_id("msg", message_type, goal["id"], goal.get("last_review_id")),
        )

    # -- anti-idle ------------------------------------------------------

    def _idle_registry(self) -> dict:
        row = read_json(self._idle_path, default={})
        return row if isinstance(row, dict) else {}

    def _save_idle_registry(self, row: dict) -> None:
        atomic_write_json(self._idle_path, row)

    def _next_idle_sequence(self) -> int:
        row = read_json(self._idle_sequence_path, default={})
        current = int(row.get("last", 0)) if isinstance(row, dict) else 0
        value = current + 1
        atomic_write_json(self._idle_sequence_path, {"last": value})
        return value

    def _clear_idle(self, recipient: str, message_id: str) -> None:
        registry = self._idle_registry()
        if registry.get(recipient, {}).get("message_id") == message_id:
            registry.pop(recipient, None)
            self._save_idle_registry(registry)

    def _ensure_idle(self) -> None:
        if any(goal["status"] in NON_TERMINAL for goal in self.scheduler.list_goals()):
            return
        recipients = [CEO_KEY] + [row["id"] for row in self.departments.list_departments()]
        registry = self._idle_registry()
        changed = False
        for recipient in recipients:
            unread_idle = [
                event
                for event in self.inbox.peek(recipient)
                if isinstance(event.get("body"), dict)
                and event["body"].get("type") == "company_idle"
            ]
            registered = registry.get(recipient)
            if registered and any(
                event.get("id") == registered.get("message_id") for event in unread_idle
            ):
                continue
            if unread_idle:
                registry[recipient] = {"message_id": unread_idle[0]["id"]}
                changed = True
                continue
            sequence = self._next_idle_sequence()
            message_id = _stable_id("msg", "company-idle", recipient, sequence)
            registry[recipient] = {"message_id": message_id}
            self._save_idle_registry(registry)
            self._message(
                to=recipient,
                message_type="company_idle",
                text="公司当前没有进行中的 Goal，请主动推进",
                sender="system",
                data={"sequence": sequence},
                message_id=message_id,
            )
            changed = True
        stale = set(registry) - set(recipients)
        for recipient in stale:
            registry.pop(recipient, None)
            changed = True
        if changed:
            self._save_idle_registry(registry)

    # -- command emission / tick ---------------------------------------

    def _write_worker_start(self, launch: WorkerLaunch) -> None:
        atomic_write_json(
            self.layout.workers / "commands" / f"{launch.command_id}.json",
            {
                "version": 1,
                "command_id": launch.command_id,
                "action": "start_worker",
                "goal_id": launch.goal_id,
                "worker_id": launch.worker_id,
                "owner_department": launch.owner_department,
                "intent": launch.intent,
            },
        )

    def _write_worker_resume(self, goal: dict) -> None:
        command_id = f"resume:{goal['id']}:{goal['attempts']}"
        atomic_write_json(
            self.layout.workers / "commands" / f"{command_id}.json",
            {
                "version": 1,
                "command_id": command_id,
                "action": "resume_worker",
                "goal_id": goal["id"],
                "worker_id": goal["worker_id"],
                "feedback": goal["latest_feedback"],
                "remaining_seconds": self.scheduler.remaining_seconds(goal["id"]),
                "session_token": goal.get("session_token"),
            },
        )

    def _write_worker_stop(self, goal: dict) -> None:
        command_id = f"stop:{goal['id']}"
        atomic_write_json(
            self.layout.workers / "commands" / f"{command_id}.json",
            {
                "version": 1,
                "command_id": command_id,
                "action": "stop_worker",
                "goal_id": goal["id"],
                "worker_id": goal["worker_id"],
            },
        )

    def _write_verifier_start(self, launch: ReviewLaunch) -> None:
        atomic_write_json(
            self.layout.reviews / "commands" / f"start:{launch.instance_id}.json",
            {
                "version": 1,
                "command_id": f"start:{launch.instance_id}",
                "action": "start_verifier",
                "review_id": launch.review_id,
                "review_seq": launch.review_seq,
                "instance_id": launch.instance_id,
                "kind": launch.kind,
                "subject_id": launch.subject_id,
                "payload": launch.payload,
            },
        )

    def _write_verifier_stop(self, review: dict) -> None:
        instance_id = review.get("instance_id")
        if not instance_id:
            return
        atomic_write_json(
            self.layout.reviews / "commands" / f"stop:{instance_id}.json",
            {
                "version": 1,
                "command_id": f"stop:{instance_id}",
                "action": "stop_verifier",
                "review_id": review["id"],
                "instance_id": instance_id,
            },
        )

    def _schedule_workers(self) -> None:
        for launch in self.scheduler.starting_launches():
            self._write_worker_start(launch)
        launch = self.scheduler.schedule_one()
        if launch is not None:
            self._write_worker_start(launch)

    def _schedule_verifiers(self) -> None:
        for launch in self.reviews.running_launches():
            self._write_verifier_start(launch)
        for launch in self.reviews.schedule():
            self._write_verifier_start(launch)

    def _emit_stopping_verifiers(self) -> None:
        for review in self.reviews.stopping_instances():
            self._write_verifier_stop(review)

    def _expire_due_goals(self, *, now: float | None = None) -> list[dict]:
        expired = self.scheduler.sweep_deadlines(now=now)
        for item in expired:
            if item.get("review_id"):
                self.reviews.cancel(item["review_id"], reason="Goal deadline elapsed")
            goal = self.scheduler.get(item["goal_id"])
            self._write_worker_stop(goal)
            self._message_goal(goal, "goal_failed_time", "Goal 已到达总时间上限")
        if expired:
            self._emit_stopping_verifiers()
        return expired

    def _route_company_email_notifications(self) -> int:
        """Project each durable Company email to CEO exactly once.

        Inbox deduplicates the stable event id.  The Company-mail cursor moves
        only after that append, so a crash between the two writes is replay
        safe and never loses a CEO notification.
        """

        delivered = 0
        while True:
            message = self.mail_store.peek_for_ceo()
            if message is None:
                return delivered
            headline, body, source_time = render_message(message)
            encoded = body.encode("utf-8")
            if len(encoded) > 48 * 1024:
                body = encoded[: 48 * 1024].decode("utf-8", "ignore") + "\n…（通知已截断）"
            self._message(
                to=CEO_KEY,
                message_type="external_event",
                text=headline,
                sender="external",
                data={
                    "body": body,
                    "source_time": source_time,
                    "source_message_id": message.get("message_id") or message["id"],
                    "mail_id": message["id"],
                    "address": message["address"],
                },
                message_id=_stable_id("msg", "company-email", message["id"]),
            )
            self.mail_store.ack_for_ceo(message["id"])
            delivered += 1

    def tick(self, *, now: float | None = None) -> dict:
        with file_lock(self._hub_lock):
            # A terminal review was accepted only after an inline deadline
            # check. Route that persisted decision before a post-crash timeout
            # sweep, otherwise a pre-deadline PASS could be lost merely because
            # the process died between the two durable writes.
            for review in self.reviews.terminal_unrouted():
                self._route_review(review)
                self.reviews.mark_routed(review["id"])
            expired = self._expire_due_goals(now=now)
            for goal in self.scheduler.list_goals():
                if goal.get("worker_state") == "stopping" and goal.get("worker_id"):
                    self._write_worker_stop(goal)
            self._emit_stopping_verifiers()
            self._schedule_workers()
            self._schedule_verifiers()
            mail_notifications = self._route_company_email_notifications()
            self._ensure_idle()
            return {
                "expired": [row["goal_id"] for row in expired],
                "workers": self.scheduler.inspect()["active_workers"],
                "verifiers": self.reviews.inspect_pool(),
                "mail_notifications": mail_notifications,
            }

    # -- CEO inspect ----------------------------------------------------

    @staticmethod
    def _goal_projection(goal: dict) -> dict:
        return {
            key: goal.get(key)
            for key in (
                "id",
                "owner_department",
                "intent",
                "status",
                "enqueue_seq",
                "worker_id",
                "worker_state",
                "deadline_at",
                "attempts",
                "latest_feedback",
                "created_at",
                "updated_at",
            )
        }

    @staticmethod
    def _review_projection(review: dict) -> dict:
        return {
            key: review.get(key)
            for key in (
                "id",
                "review_seq",
                "kind",
                "subject_id",
                "status",
                "verdict",
                "reason",
            )
        }

    def _inspect(self, actor: ActorContext, payload: dict, request_id: str) -> dict:
        _payload_fields(payload, optional={"department_id", "goal_id"})
        self._require_resident(actor)
        if payload.get("department_id") and payload.get("goal_id"):
            raise HubError("inspect accepts department_id or goal_id, not both")
        if payload.get("goal_id"):
            goal = self.scheduler.get(payload["goal_id"])
            review = None
            if goal.get("last_review_id"):
                review = self._review_projection(self.reviews.get(goal["last_review_id"]))
            return {"goal": self._goal_projection(goal), "last_review": review}
        if payload.get("department_id"):
            department = self.departments.get(payload["department_id"])
            return {
                "department": {
                    "id": department["id"],
                    "name": department["name"],
                    "status": department["status"],
                    "objective": self.objectives.current(department["id"]),
                    "objective_revision": self.objectives.active_metadata(department["id"]),
                },
                "goals": [
                    self._goal_projection(row)
                    for row in self.scheduler.list_goals(owner_department=department["id"])
                ],
            }
        inspection = self.scheduler.inspect()
        return {
            "company_objective_revision": self.objectives.active_metadata(CEO_KEY),
            "departments": [
                {
                    "id": row["id"],
                    "name": row["name"],
                    "status": row["status"],
                    "objective_revision": self.objectives.active_metadata(row["id"]),
                }
                for row in self.departments.list_departments()
            ],
            "goal_counts": inspection["counts"],
            "workers": {
                "active": inspection["active_workers"],
                "max": inspection["max_workers"],
            },
            "verifiers": self.reviews.inspect_pool(),
            "anomalies": {
                "failed_time": inspection["counts"].get("failed_time", 0),
                "provision_failed": sum(
                    1
                    for path in (self.layout.departments / "requests").glob("*.json")
                    if (row := read_json(path)) and row.get("status") == "provision_failed"
                ),
            },
        }


class HubHTTPServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address: tuple[str, int], hub: CompanyHub):
        self.hub = hub
        super().__init__(address, HubHTTPRequestHandler)


class HubHTTPRequestHandler(BaseHTTPRequestHandler):
    server: HubHTTPServer
    protocol_version = "HTTP/1.1"

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def _json(self, status: int, value: dict) -> None:
        body = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._json(200, {"ok": True})
            return
        self._json(404, {"ok": False, "error": {"code": "not_found"}})

    def do_POST(self) -> None:  # noqa: N802
        if self.path == "/v1/run-archive":
            self._archive_run()
            return
        if self.path != "/v1/method":
            self._json(404, {"ok": False, "error": {"code": "not_found"}})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 1024 * 1024:
                raise HubError("invalid request size")
            raw = json.loads(self.rfile.read(length))
            actor = ActorContext(
                kind=self.headers.get("X-Foundagent-Actor-Kind", ""),  # type: ignore[arg-type]
                actor_id=self.headers.get("X-Foundagent-Actor-Id", ""),
                department_id=self.headers.get("X-Foundagent-Department") or None,
                goal_id=self.headers.get("X-Foundagent-Goal") or None,
                review_id=self.headers.get("X-Foundagent-Review") or None,
            )
            self._json(200, self.server.hub.call(actor, raw))
        except Exception as exc:  # noqa: BLE001 — transport boundary
            self._json(
                400,
                {
                    "version": 1,
                    "request_id": None,
                    "ok": False,
                    "error": {"code": "invalid_transport", "message": str(exc)},
                },
            )

    def _archive_run(self) -> None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            maximum = int(os.environ.get("RUN_ARCHIVE_MAX_BYTES", str(256 * 1024 * 1024)))
            if length <= 0 or length > maximum:
                raise HubError("invalid run archive size")
            raw = json.loads(self.rfile.read(length))
            if not isinstance(raw, dict):
                raise HubError("run archive must be an object")
            allowed = {
                "run_id",
                "metadata",
                "raw_output",
                "stderr",
                "model_output",
                "harness_log",
                "container_log",
            }
            if set(raw) - allowed or not {"run_id", "metadata", "raw_output", "stderr", "model_output"} <= set(raw):
                raise HubError("invalid run archive fields")
            actor = ActorContext(
                kind=self.headers.get("X-Foundagent-Actor-Kind", ""),  # type: ignore[arg-type]
                actor_id=self.headers.get("X-Foundagent-Actor-Id", ""),
                department_id=self.headers.get("X-Foundagent-Department") or None,
            )
            if actor.kind not in ("lead", "ceo", "department"):
                raise HubError("only resident harnesses may archive resident wakes")
            if not isinstance(raw["metadata"], dict) or raw["metadata"].get("agent_id") != actor.actor_id:
                raise HubError("run archive actor does not match metadata")
            run_dir = RunLogRecorder(self.server.hub.layout.telemetry / "runs").record(
                run_id=raw["run_id"],
                metadata=raw["metadata"],
                raw_output=raw["raw_output"],
                stderr=raw["stderr"],
                model_output=raw["model_output"],
                harness_log=raw.get("harness_log", ""),
                container_log=raw.get("container_log", ""),
            )
            self._json(200, {"ok": True, "run_id": raw["run_id"], "stored": run_dir.name})
        except Exception as exc:  # noqa: BLE001 — transport boundary
            self._json(400, {"ok": False, "error": {"code": "archive_failed", "message": str(exc)}})


def _state_root() -> Path:
    explicit = os.environ.get("COMPANY_STATE_ROOT")
    if explicit:
        return Path(explicit)
    repo = Path(__file__).resolve().parents[1]
    return repo / "state" / os.environ.get("COMPANY", "v7-test")


def main() -> None:
    hub = CompanyHub(
        _state_root(),
        company_id=os.environ.get("COMPANY", "v7-test"),
        mail_global_root=global_mail_root(),
        max_workers=int(os.environ.get("WORKER_MAX", "5")),
        max_verifiers=int(os.environ.get("VERIFIER_MAX", "3")),
        goal_timeout_secs=int(os.environ.get("GOAL_TIMEOUT_SECS", "10800")),
    )
    hub.tick()
    interval = float(os.environ.get("HUB_TICK_SECS", "0.5"))

    def watchdog() -> None:
        while True:
            try:
                hub.tick()
            except Exception as exc:  # noqa: BLE001 — service remains recoverable
                print(f"[company-hub] tick failed: {exc!r}", flush=True)
            time.sleep(max(0.05, interval))

    threading.Thread(target=watchdog, name="company-hub-watchdog", daemon=True).start()
    port = int(os.environ.get("HUB_PORT", "8910"))
    server = HubHTTPServer(("0.0.0.0", port), hub)
    print(f"[company-hub] ready root={hub.layout.root} port={port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
