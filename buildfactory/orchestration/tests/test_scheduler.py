from orchestration.scheduler import (
    CANCELLED,
    CLAIMED,
    DONE,
    FAILED_TIME,
    OPEN,
    RUNNING,
    VERIFYING,
    GoalScheduler,
)
from orchestration.runtime_store import atomic_write_json


def _goal(scheduler, number, owner="researcher"):
    return scheduler.create_goal(
        owner_department=owner,
        intent=f"deliver result {number}",
        acceptance=f"verify result {number}",
        request_id=f"request-{number}",
    )


def _start(scheduler, goal_id, started_at=100.0):
    launch = scheduler.schedule_one()
    assert launch.goal_id == goal_id
    scheduler.worker_started(goal_id, worker_id=launch.worker_id, started_at=started_at)
    return launch


def test_goal_creation_is_idempotent_and_fifo_sequence_is_explicit(tmp_path):
    scheduler = GoalScheduler(tmp_path / "ledger")
    first = _goal(scheduler, 1)
    second = _goal(scheduler, 2)

    assert _goal(scheduler, 1) == first
    assert [row["id"] for row in scheduler.list_goals()] == [first, second]
    assert [row["enqueue_seq"] for row in scheduler.list_goals()] == [1, 2]


def test_deadline_is_written_once_at_worker_start_and_never_rearmed(tmp_path):
    scheduler = GoalScheduler(tmp_path / "ledger", goal_timeout_secs=10800)
    goal_id = _goal(scheduler, 1)
    launch = _start(scheduler, goal_id, started_at=500.0)

    assert scheduler.get(goal_id)["deadline_at"] == 11300.0
    scheduler.worker_started(goal_id, worker_id=launch.worker_id, started_at=999.0)
    assert scheduler.get(goal_id)["deadline_at"] == 11300.0
    assert scheduler.get(goal_id)["deadline_at"] == 11300.0


def test_verifier_fail_resumes_same_worker_without_attempt_limit(tmp_path):
    scheduler = GoalScheduler(tmp_path / "ledger")
    goal_id = _goal(scheduler, 1)
    launch = _start(scheduler, goal_id)

    for attempt in range(6):
        scheduler.submit_result(
            goal_id,
            worker_id=launch.worker_id,
            session_token="session-one",
        )
        review_id = f"review-{attempt}"
        scheduler.begin_verification(goal_id, review_id=review_id)
        assert scheduler.get(goal_id)["status"] == VERIFYING
        scheduler.verification_failed(goal_id, review_id=review_id, feedback="improve it")
        assert scheduler.get(goal_id)["worker_id"] == launch.worker_id
        scheduler.worker_resumed(
            goal_id, worker_id=launch.worker_id, session_token="session-one"
        )

    assert scheduler.get(goal_id)["status"] == RUNNING
    assert scheduler.get(goal_id)["attempts"] == 6
    assert scheduler.get(goal_id)["deadline_at"] == 10900.0


def test_pass_is_done_but_slot_releases_only_after_worker_stop_ack(tmp_path):
    scheduler = GoalScheduler(tmp_path / "ledger", max_workers=1)
    first = _goal(scheduler, 1)
    second = _goal(scheduler, 2)
    launch = _start(scheduler, first)
    scheduler.submit_result(
        first,
        worker_id=launch.worker_id,
        session_token="s1",
    )
    scheduler.begin_verification(first, review_id="review-1")
    scheduler.verification_passed(first, review_id="review-1")

    assert scheduler.get(first)["status"] == DONE
    assert scheduler.schedule_one() is None

    scheduler.worker_stopped(first, worker_id=launch.worker_id)
    assert scheduler.schedule_one().goal_id == second


def test_worker_start_failure_retries_same_head_without_letting_later_goal_pass(tmp_path):
    scheduler = GoalScheduler(tmp_path / "ledger", max_workers=5)
    first = _goal(scheduler, 1)
    _goal(scheduler, 2)
    launch = scheduler.schedule_one()

    scheduler.worker_start_failed(first, worker_id=launch.worker_id, reason="docker error")
    retry = scheduler.schedule_one()

    assert retry.goal_id == first
    assert retry.worker_id == launch.worker_id
    assert scheduler.list_goals()[1]["status"] == OPEN

    scheduler.worker_started(first, worker_id=retry.worker_id, started_at=100)
    recovered = scheduler.get(first)
    assert recovered["latest_feedback"] is None
    assert recovered["start_attempts"] == 2


def test_global_five_worker_limit_and_fifo(tmp_path):
    scheduler = GoalScheduler(tmp_path / "ledger", max_workers=5)
    goal_ids = [_goal(scheduler, number) for number in range(1, 8)]
    launched = []
    for index in range(5):
        launch = scheduler.schedule_one()
        launched.append(launch.goal_id)
        scheduler.worker_started(launch.goal_id, worker_id=launch.worker_id, started_at=100 + index)

    assert launched == goal_ids[:5]
    assert scheduler.schedule_one() is None
    assert [row["status"] for row in scheduler.list_goals()[5:]] == [OPEN, OPEN]


def test_deadline_failure_and_cancel_are_distinct_terminal_states(tmp_path):
    scheduler = GoalScheduler(tmp_path / "ledger", goal_timeout_secs=10)
    timed = _goal(scheduler, 1)
    timed_launch = _start(scheduler, timed, started_at=100)
    cancelled = _goal(scheduler, 2)

    expired = scheduler.sweep_deadlines(now=111)
    assert expired == [{"goal_id": timed, "review_id": None}]
    assert scheduler.get(timed)["status"] == FAILED_TIME
    scheduler.worker_stopped(timed, worker_id=timed_launch.worker_id)

    assert scheduler.cancel(cancelled, cancelled_by="ceo", reason="strategy changed")
    assert scheduler.get(cancelled)["status"] == CANCELLED
    assert scheduler.get(cancelled)["cancelled_by"] == "ceo"


def test_completion_declaration_has_no_result_fields_and_prunes_legacy_values(tmp_path):
    scheduler = GoalScheduler(tmp_path / "ledger")
    goal_id = _goal(scheduler, 1)
    launch = _start(scheduler, goal_id)
    goal = scheduler.get(goal_id)
    assert "latest_summary" not in goal
    assert "company_refs" not in goal

    goal["latest_summary"] = "legacy summary"
    goal["company_refs"] = ["/company/legacy.md"]
    atomic_write_json(scheduler.root / f"{goal_id}.json", goal)

    assert scheduler.submit_result(
        goal_id,
        worker_id=launch.worker_id,
        session_token=None,
    )
    advanced = scheduler.get(goal_id)
    assert "latest_summary" not in advanced
    assert "company_refs" not in advanced


def test_runtime_failure_retries_same_worker_without_terminal_goal(tmp_path):
    scheduler = GoalScheduler(tmp_path / "ledger", goal_timeout_secs=100)
    goal_id = scheduler.create_goal(
        owner_department="researcher",
        intent="deliver runtime result",
        acceptance=None,
        request_id="runtime-failure",
    )
    launch = _start(scheduler, goal_id, started_at=10)

    assert scheduler.worker_turn_failed(
        goal_id, worker_id=launch.worker_id, reason="runtime exited"
    ) is True
    goal = scheduler.get(goal_id)
    assert goal["status"] == "running"
    assert goal["worker_state"] == "resuming"
    assert goal["worker_id"] == launch.worker_id
    assert goal["deadline_at"] == 110


def test_manager_and_worker_operation_replays_are_idempotent(tmp_path):
    scheduler = GoalScheduler(tmp_path / "ledger", goal_timeout_secs=100)
    goal_id = _goal(scheduler, 1)
    launch = scheduler.schedule_one()
    scheduler.worker_started(goal_id, worker_id=launch.worker_id, started_at=10)
    scheduler.worker_started(goal_id, worker_id=launch.worker_id, started_at=999)
    assert scheduler.get(goal_id)["deadline_at"] == 110

    assert scheduler.worker_turn_failed(
        goal_id,
        worker_id=launch.worker_id,
        reason="runtime failed",
        operation_id="turn-one",
    )
    assert not scheduler.worker_turn_failed(
        goal_id,
        worker_id=launch.worker_id,
        reason="runtime failed",
        operation_id="turn-one",
    )
    scheduler.worker_resumed(goal_id, worker_id=launch.worker_id, session_token=None)
    scheduler.worker_resumed(goal_id, worker_id=launch.worker_id, session_token=None)

    assert scheduler.submit_result(
        goal_id,
        worker_id=launch.worker_id,
        session_token="session-1",
        operation_id="result-one",
    )
    assert not scheduler.submit_result(
        goal_id,
        worker_id=launch.worker_id,
        session_token="session-2",
        operation_id="result-one",
    )


def test_v7_scheduler_has_no_supersede_or_generic_kill_api(tmp_path):
    scheduler = GoalScheduler(tmp_path / "ledger")

    assert not hasattr(scheduler, "supersede_goal")
    assert not hasattr(scheduler, "kill")
    assert {DONE, FAILED_TIME, CANCELLED}.isdisjoint({"killed"})


def test_owner_filter_supports_department_duplicate_judgment(tmp_path):
    scheduler = GoalScheduler(tmp_path / "ledger")
    research = _goal(scheduler, 1, owner="researcher")
    _goal(scheduler, 2, owner="builder")

    assert [row["id"] for row in scheduler.list_goals(owner_department="researcher")] == [research]
    assert scheduler.get(research)["status"] == OPEN
