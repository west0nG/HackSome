from orchestration.objective_store import ObjectiveStore
from orchestration.verifier_manager import VerifierManager


def _verdict(manager, review_id, verdict, reason="clear and aligned"):
    launch = next(item for item in manager.schedule() if item.review_id == review_id)
    manager.submit_verdict(
        review_id,
        instance_id=launch.instance_id,
        verdict=verdict,
        reason=reason,
    )


def test_objective_is_not_visible_until_independent_review_passes(tmp_path):
    reviews = VerifierManager(tmp_path / "reviews")
    store = ObjectiveStore(tmp_path / "agents", reviews)
    proposal = store.propose(
        actor_id="ceo",
        objective_kind="company",
        text="Build useful products and reach paying customers.",
        requested_by="ceo",
        request_id="company-objective-1",
    )

    assert store.current("ceo") is None
    _verdict(reviews, proposal["review_id"], "PASS")
    applied = store.apply_review(proposal["review_id"])

    assert applied["status"] == "active"
    assert store.current("ceo") == "Build useful products and reach paying customers."
    assert store.active_metadata("ceo")["revision"] == 1


def test_failed_objective_does_not_replace_current_revision(tmp_path):
    reviews = VerifierManager(tmp_path / "reviews")
    store = ObjectiveStore(tmp_path / "agents", reviews)
    first = store.propose(
        actor_id="ceo",
        objective_kind="company",
        text="First approved direction",
        requested_by="ceo",
        request_id="objective-1",
    )
    _verdict(reviews, first["review_id"], "PASS")
    store.apply_review(first["review_id"])

    second = store.propose(
        actor_id="ceo",
        objective_kind="company",
        text="Vague replacement",
        requested_by="ceo",
        request_id="objective-2",
    )
    _verdict(reviews, second["review_id"], "FAIL", "too vague")
    rejected = store.apply_review(second["review_id"])

    assert rejected["status"] == "rejected"
    assert store.current("ceo") == "First approved direction"
    assert store.active_metadata("ceo")["revision"] == 1


def test_company_and_department_objectives_share_the_same_review_fifo(tmp_path):
    reviews = VerifierManager(tmp_path / "reviews", max_instances=1)
    store = ObjectiveStore(tmp_path / "agents", reviews)
    company = store.propose(
        actor_id="ceo",
        objective_kind="company",
        text="Company direction",
        requested_by="ceo",
        request_id="objective-company",
    )
    department = store.propose(
        actor_id="researcher",
        objective_kind="department",
        text="Own evidence quality",
        requested_by="ceo",
        request_id="objective-research",
    )

    assert reviews.schedule()[0].review_id == company["review_id"]
    assert reviews.get(department["review_id"])["status"] == "queued"


def test_in_review_projection_can_scope_ceo_owned_and_actor_proposals(tmp_path):
    reviews = VerifierManager(tmp_path / "reviews")
    store = ObjectiveStore(tmp_path / "agents", reviews)
    company = store.propose(
        actor_id="ceo",
        objective_kind="company",
        text="Company direction",
        requested_by="ceo",
        request_id="pending-company",
    )
    department = store.propose(
        actor_id="builder",
        objective_kind="department",
        text="Build outcome",
        requested_by="ceo",
        request_id="pending-builder",
    )

    assert [row["proposal_id"] for row in store.in_review(requested_by="ceo")] == [
        department["id"],
        company["id"],
    ]
    assert [row["proposal_id"] for row in store.in_review(actor_id="builder")] == [
        department["id"]
    ]

    _verdict(reviews, company["review_id"], "PASS")
    store.apply_review(company["review_id"])
    assert [row["proposal_id"] for row in store.in_review(requested_by="ceo")] == [
        department["id"]
    ]
