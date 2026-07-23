from pathlib import Path
import subprocess

import pytest

import orchestration.verifier_runtime as verifier_runtime
import orchestration.worker_manager as worker_manager
import orchestration.team_store as team_store
from orchestration.lead_loop import build_lead_wake_prompt
from orchestration.method_adapter import ActorContext
from orchestration.runtime_store import StoreError, read_json
from orchestration.team_hub import TeamHub
from orchestration.team_store import CONTROL_DOMAINS, TeamLayout
from orchestration.verifier_runtime import (
    DockerVerifierBackend,
    VerifierDefinition,
    team_verifier_prompt,
)
from orchestration.worker_manager import (
    DockerWorkerBackend,
    WorkerDefinition,
    team_initial_worker_prompt,
    team_resume_worker_prompt,
)
from orchestration.scheduler import WorkerLaunch


def _call(hub, actor, method, payload, request_id):
    response = hub.call(
        actor,
        {
            "version": 1,
            "request_id": request_id,
            "method": method,
            "payload": payload,
        },
    )
    assert response["ok"], response
    return response["result"]


def test_team_bootstrap_creates_only_two_project_references(tmp_path):
    layout = TeamLayout.bootstrap(
        tmp_path / "team",
        challenge_markdown="# Challenge\n",
        initial_idea_card_markdown="# Idea\n",
    )

    assert sorted(
        path.relative_to(layout.project).as_posix()
        for path in layout.project.rglob("*")
    ) == [
        "reference",
        "reference/challenge.md",
        "reference/initial-idea-card.md",
    ]
    assert layout.project_mount() == {
        "source": str(layout.project),
        "target": "/project",
        "mode": "rw",
    }
    assert layout.project_mount(read_only=True)["mode"] == "ro"
    assert {path.name for path in layout.root.iterdir()} == {
        "project",
        *CONTROL_DOMAINS,
    }
    with pytest.raises(StoreError, match="already exist"):
        TeamLayout.bootstrap(
            layout.root,
            challenge_markdown="replacement",
            initial_idea_card_markdown="replacement",
        )


def test_team_bootstrap_does_not_leave_partial_references(tmp_path, monkeypatch):
    real_write = team_store.atomic_write_text
    writes = 0

    def fail_second_write(path, value):
        nonlocal writes
        writes += 1
        if writes == 2:
            raise OSError("simulated write failure")
        real_write(path, value)

    monkeypatch.setattr(team_store, "atomic_write_text", fail_second_write)
    root = tmp_path / "team"
    with pytest.raises(StoreError, match="atomically initialize"):
        TeamLayout.bootstrap(
            root,
            challenge_markdown="# Challenge\n",
            initial_idea_card_markdown="# Idea\n",
        )
    assert not (root / "project" / "reference").exists()
    assert list((root / "project").iterdir()) == []


def test_role_prompts_are_self_contained_and_keep_acceptance_private():
    lead = build_lead_wake_prompt(
        None,
        "wake-1",
        "heartbeat",
        "2026-07-23T00:00:00+00:00",
    )
    assert "/project/reference/challenge.md" in lead
    assert "create_goal" in lead
    assert "list_my_goals" in lead
    assert "cancel_goal" in lead
    assert "--request-id 'goal-<stable-purpose-id>'" in lead
    assert "no deadline, completion state" in lead
    assert "CURRENT OBJECTIVE" not in lead

    launch = WorkerLaunch(
        goal_id="goal-1",
        worker_id="worker-1",
        intent="Build the real demo",
        acceptance="SECRET VERIFIER CONTEXT",
        owner_department="lead",
        command_id="start:goal-1:1",
    )
    worker = team_initial_worker_prompt(launch)
    assert "Build the real demo" in worker
    assert "SECRET VERIFIER CONTEXT" not in worker
    assert "submit_result" in worker
    assert "--request-id 'result-goal-1-<meaningful-revision>'" in worker
    assert "deadline_at" not in worker

    rework = team_resume_worker_prompt(
        goal_id="goal-1", feedback="The deployed flow returns 500"
    )
    assert "same Worker, workspace, home, and session" in rework
    assert "remaining_seconds" not in rework

    verifier = team_verifier_prompt(
        {
            "review_id": "review-1",
            "kind": "goal_result",
            "subject_id": "goal-1",
            "payload": {
                "goal_id": "goal-1",
                "intent": "Build the real demo",
                "acceptance": "SECRET VERIFIER CONTEXT",
            },
        }
    )
    assert "SECRET VERIFIER CONTEXT" in verifier
    assert "Canonical /project is mounted read-only" in verifier
    assert "submit_verdict" in verifier
    assert "--request-id 'verdict-review-1'" in verifier


def test_two_goal_fifo_fail_resume_pass_and_batch_drained(tmp_path):
    root = tmp_path / "team"
    TeamLayout.bootstrap(
        root,
        challenge_markdown="# Challenge\n",
        initial_idea_card_markdown="# Idea\n",
    )
    hub = TeamHub(root, team_id="demo")
    lead = ActorContext("lead", "lead")
    worker_manager = ActorContext("manager", "worker-manager")
    verifier_manager = ActorContext("manager", "verifier-manager")

    first = _call(
        hub,
        lead,
        "create_goal",
        {"intent": "first", "acceptance": "private-first"},
        "goal-first",
    )
    second = _call(
        hub,
        lead,
        "create_goal",
        {"intent": "second"},
        "goal-second",
    )
    assert first["status"] == "claimed"
    assert second["status"] == "open"
    assert second["worker_id"] is None
    replayed_first = _call(
        hub,
        lead,
        "create_goal",
        {"intent": "first", "acceptance": "private-first"},
        "goal-first",
    )
    assert replayed_first["id"] == first["id"]
    assert len(hub.scheduler.list_goals()) == 2

    _call(
        hub,
        worker_manager,
        "worker_started",
        {"goal_id": first["id"], "worker_id": first["worker_id"]},
        "manager-start-first",
    )
    first_worker = ActorContext(
        "worker", first["worker_id"], goal_id=first["id"]
    )
    first_result = _call(
        hub, first_worker, "submit_result", {}, "result-first"
    )
    first_review = hub.reviews.get(first_result["review_id"])
    assert first_review["payload"]["acceptance"] == "private-first"
    verifier = ActorContext(
        "verifier",
        first_review["instance_id"],
        review_id=first_review["id"],
    )
    _call(
        hub,
        verifier,
        "submit_verdict",
        {"verdict": "PASS", "reason": "observed first"},
        "verdict-first",
    )
    _call(
        hub,
        verifier_manager,
        "verifier_instance_stopped",
        {
            "review_id": first_review["id"],
            "instance_id": verifier.actor_id,
        },
        "manager-verifier-stopped-first",
    )
    _call(
        hub,
        worker_manager,
        "worker_stopped",
        {"goal_id": first["id"], "worker_id": first["worker_id"]},
        "manager-worker-stopped-first",
    )

    second = hub.scheduler.get(second["id"])
    assert second["status"] == "claimed"
    assert second["worker_id"] == "worker-2"
    _call(
        hub,
        worker_manager,
        "worker_started",
        {"goal_id": second["id"], "worker_id": second["worker_id"]},
        "manager-start-second",
    )
    second_worker = ActorContext(
        "worker", second["worker_id"], goal_id=second["id"]
    )
    result = _call(hub, second_worker, "submit_result", {}, "result-second-a")
    review = hub.reviews.get(result["review_id"])
    verifier = ActorContext(
        "verifier", review["instance_id"], review_id=review["id"]
    )
    _call(
        hub,
        verifier,
        "submit_verdict",
        {"verdict": "FAIL", "reason": "missing real check"},
        "verdict-second-a",
    )
    failed = hub.scheduler.get(second["id"])
    assert failed["worker_id"] == second["worker_id"]
    assert failed["worker_state"] == "resuming"
    assert failed["latest_feedback"] == "missing real check"
    resume_command = read_json(
        hub.layout.workers
        / "commands"
        / f"resume:{second['id']}:{failed['attempts']}.json"
    )
    assert "remaining_seconds" not in resume_command

    _call(
        hub,
        verifier_manager,
        "verifier_instance_stopped",
        {"review_id": review["id"], "instance_id": verifier.actor_id},
        "manager-verifier-stopped-second-a",
    )
    _call(
        hub,
        worker_manager,
        "worker_resumed",
        {
            "goal_id": second["id"],
            "worker_id": second["worker_id"],
            "session_token": "same-session",
        },
        "manager-resume-second",
    )
    result = _call(hub, second_worker, "submit_result", {}, "result-second-b")
    review = hub.reviews.get(result["review_id"])
    assert review["instance_id"] != verifier.actor_id
    verifier = ActorContext(
        "verifier", review["instance_id"], review_id=review["id"]
    )
    _call(
        hub,
        verifier,
        "submit_verdict",
        {"verdict": "PASS", "reason": "observed repaired result"},
        "verdict-second-b",
    )
    _call(
        hub,
        verifier_manager,
        "verifier_instance_stopped",
        {"review_id": review["id"], "instance_id": verifier.actor_id},
        "manager-verifier-stopped-second-b",
    )
    _call(
        hub,
        worker_manager,
        "worker_stopped",
        {"goal_id": second["id"], "worker_id": second["worker_id"]},
        "manager-worker-stopped-second",
    )

    goals = hub.scheduler.list_goals()
    assert [goal["status"] for goal in goals] == ["done", "done"]
    assert all("deadline_at" not in goal for goal in goals)
    assert "failed_time" not in str(goals)
    assert [event["body"]["type"] for event in hub.inbox.peek("lead")] == [
        "team_started",
        "goal_batch_drained",
    ]
    restarted = TeamHub(root, team_id="demo")
    restarted.tick()
    assert [event["body"]["type"] for event in restarted.inbox.peek("lead")] == [
        "team_started",
        "goal_batch_drained",
    ]


def test_team_hub_exposes_only_team_methods(tmp_path):
    hub = TeamHub(tmp_path / "team")
    lead = ActorContext("lead", "lead")
    for forbidden in (
        "propose_company_objective",
        "create_department",
        "read_notes",
        "claim_company_mailbox",
        "send_department_message",
    ):
        response = hub.call(
            lead,
            {
                "version": 1,
                "request_id": f"forbidden-{forbidden}",
                "method": forbidden,
                "payload": {},
            },
        )
        assert response["ok"] is False
        assert response["error"]["code"] == "unknown_method"


def test_dynamic_worker_and_verifier_project_mount_permissions(tmp_path, monkeypatch):
    calls = []

    def fake_run(args):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, "ok\n", "")

    monkeypatch.setattr(
        worker_manager, "materialize_ephemeral_home", lambda *args, **kwargs: None
    )
    monkeypatch.setattr(
        verifier_runtime, "materialize_ephemeral_home", lambda *args, **kwargs: None
    )
    monkeypatch.setattr(worker_manager, "prepare_container_tree", lambda *args, **kwargs: None)
    monkeypatch.setattr(verifier_runtime, "prepare_container_tree", lambda *args, **kwargs: None)
    monkeypatch.setattr(worker_manager, "wait_for_computer_server", lambda *args, **kwargs: True)
    monkeypatch.setattr(verifier_runtime, "wait_for_computer_server", lambda *args, **kwargs: True)

    project = tmp_path / "project"
    worker_backend = DockerWorkerBackend(
        repo=Path(__file__).resolve().parents[2],
        company_id="demo-team",
        spec_path=Path(__file__).resolve().parents[2]
        / "agents"
        / "ephemeral"
        / "team-worker.yaml",
        shared_mount_target="/project",
        team_mode=True,
    )
    monkeypatch.setattr(worker_backend, "_run", fake_run)
    worker_backend.create(
        WorkerDefinition(
            company_id="demo-team",
            worker_id="worker-1",
            goal_id="goal-1",
            owner_department="lead",
            container_name="demo-team-worker-1",
            home=tmp_path / "worker-home",
            workspace=tmp_path / "worker-workspace",
            company_dir=project,
        )
    )
    worker_run = next(args for args in calls if args[:3] == ["docker", "run", "-d"])
    assert f"{project}:/project" in worker_run
    assert f"{project}:/project:ro" not in worker_run
    assert "hacksome.team=demo-team" in worker_run

    calls.clear()
    verifier_backend = DockerVerifierBackend(
        repo=Path(__file__).resolve().parents[2],
        company_id="demo-team",
        spec_path=Path(__file__).resolve().parents[2]
        / "agents"
        / "ephemeral"
        / "team-verifier.yaml",
        shared_mount_target="/project",
        team_mode=True,
    )
    monkeypatch.setattr(verifier_backend, "_run", fake_run)
    verifier_backend.create(
        VerifierDefinition(
            company_id="demo-team",
            review_id="review-1",
            instance_id="verifier-1-1",
            container_name="demo-team-verifier-1-1",
            home=tmp_path / "verifier-home",
            workspace=tmp_path / "verifier-workspace",
            company_dir=project,
        )
    )
    verifier_run = next(args for args in calls if args[:3] == ["docker", "run", "-d"])
    assert f"{project}:/project:ro" in verifier_run
    assert f"{project}:/project" not in verifier_run
    assert "hacksome.team=demo-team" in verifier_run
