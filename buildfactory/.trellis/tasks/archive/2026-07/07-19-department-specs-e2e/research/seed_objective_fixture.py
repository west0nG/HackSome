#!/usr/bin/env python3
"""为 Department E2E 建立确定性的 Company Objective 前置状态。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from orchestration.objective_store import ObjectiveStore
from orchestration.runtime_store import CompanyLayout
from orchestration.verifier_manager import VerifierManager


FIXTURE_OBJECTIVE = """Validate and establish a productized accessibility regression-QA service for small Shopify agencies maintaining multiple merchant storefronts. The buyer is an agency owner or technical lead facing accessibility work after launches, theme upgrades, app changes, merchant requests, or demand letters. Today the agency can use free WAVE/axe checks, Shopify guidance, low-cost scanner/overlay apps, specialist audits, or do nothing; Shopify has told Partners that EAA-era merchants require accessible storefronts, paid Shopify accessibility apps exist from $5 to $199 per month, and public reviews show both demand and failures of trust/support. W3C states that automated tools cannot determine accessibility alone, so the unresolved gap is not another score, badge, certification, or legal-compliance promise: it is reproducible browser/keyboard findings, screenshots and selectors, developer-ready fix tickets, scoped manual checks, and post-fix evidence across recurring storefront changes. Public storefronts make first users reachable through a permission-based sample showing a few reproducible issues, followed by a fixed-price portfolio pilot. Deliver the smallest real service for one consenting agency and storefront: inspect representative home, collection, product, cart, search, and interaction flows; report prioritized issues, reproduction, likely ownership only where supportable, suggested fixes, limitations, and one re-scan. Test approximately $99 fixed-price willingness before building an installed app. Facts: the need and paid adjacent products exist, and automated testing has known limits. Assumptions: agencies rather than merchants will pay, developer-ready evidence removes meaningful work, public samples earn attention, and enough useful work is possible without credentials. Unknowns: acquisition norms, attribution accuracy, manual-review depth, secure evidence handling, and whether recurrence is release-, store-, or portfolio-based. Within 21 days seek 10 qualified agency conversations, 3 consenting pilots, and at least 1 paid pilot; strengthen the direction only if the buyer confirms meaningful work removed, and reconsider or abandon it if existing tools are consistently sufficient, no qualified agency consents after 10 conversations, or nobody pays after 3 complete pilots."""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("state_root", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    layout = CompanyLayout.initialize(args.state_root)
    reviews = VerifierManager(layout.reviews)
    objectives = ObjectiveStore(layout.agents, reviews)
    proposal = objectives.propose(
        actor_id="ceo",
        objective_kind="company",
        text=FIXTURE_OBJECTIVE,
        requested_by="ceo",
        request_id="department-specs-e2e-company-objective-fixture",
    )
    launches = reviews.schedule()
    if len(launches) != 1:
        raise RuntimeError(f"expected one fixture review launch, got {len(launches)}")
    launch = launches[0]
    accepted = reviews.submit_verdict(
        launch.review_id,
        instance_id=launch.instance_id,
        verdict="PASS",
        reason=(
            "E2E fixture only: deterministically activated through production stores; "
            "this is not evidence of a real Company Objective model review."
        ),
    )
    if not accepted:
        raise RuntimeError("fixture verdict was not accepted")
    active = objectives.apply_review(launch.review_id)
    reviews.mark_routed(launch.review_id)
    if not reviews.confirm_instance_stopped(
        launch.review_id, instance_id=launch.instance_id
    ):
        raise RuntimeError("fixture verifier instance did not stop cleanly")

    review = reviews.get(launch.review_id)
    result = {
        "fixture_only": True,
        "real_model_reviewed": False,
        "state_root": str(layout.root),
        "proposal": {
            "id": proposal["id"],
            "actor_id": proposal["actor_id"],
            "objective_kind": proposal["objective_kind"],
            "revision": proposal["revision"],
            "review_id": proposal["review_id"],
        },
        "active_status": active["status"],
        "review": {
            "id": review["id"],
            "kind": review["kind"],
            "status": review["status"],
            "verdict": review["verdict"],
            "routed": review["routed"],
            "instance_id": review["instance_id"],
            "instance_state": review["instance_state"],
            "reason": review["reason"],
        },
        "objective_file_exists": layout.objective_path("ceo").is_file(),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
