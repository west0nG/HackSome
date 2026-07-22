from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from hacksome.report import (
    EliminationSummary,
    ReportIdea,
    ReportInput,
    render_report,
    write_report,
)


class ReportTests(unittest.TestCase):
    def test_keeps_similar_ideas_without_ranking(self) -> None:
        ideas = tuple(
            ReportIdea(
                artifact_id=f"idea-{number:03d}",
                idea_ref=f"ideas/problem/generator-{number:03d}/idea-001.md",
                target_user="Teachers",
                problem="Repeated manual preparation",
                felt_value=f"Value {number}",
                user_flow="Input -> processing -> usable result",
                core_mechanism="Automation",
                minimum_features="One complete path",
                alternatives_and_adoption="Less manual work",
                sponsor_technology="Not required",
                beta_scope="One real workflow",
                highest_risk_dependencies="Input quality",
            )
            for number in (2, 1)
        )
        report = render_report(
            ReportInput(
                run_id="run-001",
                challenge_title="A challenge",
                challenge_ref="challenge.md",
                started_at="2026-07-23T00:00:00Z",
                completed_at="2026-07-23T01:00:00Z",
                stage_statuses={"S11": "completed"},
                ideas=ideas,
            )
        )

        self.assertIn("### idea-001", report)
        self.assertIn("### idea-002", report)
        self.assertNotIn("rank", report.lower())
        self.assertLess(report.index("### idea-001"), report.index("### idea-002"))

    def test_zero_ideas_still_renders_elimination_trace(self) -> None:
        report = render_report(
            ReportInput(
                run_id="run-empty",
                challenge_title="No fit",
                challenge_ref="challenge.md",
                started_at="2026-07-23T00:00:00Z",
                completed_at="2026-07-23T00:10:00Z",
                stage_statuses={"S5": "completed", "S11": "completed"},
                eliminations=(
                    EliminationSummary(
                        candidate_ref="problems/a/problem-001.md",
                        stage="S5",
                        rule="gate-2",
                        reason="No verified cost or workaround.",
                        decision_refs=("gateways/a/gateway-001.md",),
                    ),
                ),
            )
        )

        self.assertIn("No Idea passed", report)
        self.assertIn("Elimination Appendix", report)
        self.assertIn("No verified cost", report)

    def test_write_report_is_atomic_at_destination(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "idea-report.md"
            data = ReportInput(
                run_id="run-001",
                challenge_title="Challenge",
                challenge_ref="challenge.md",
                started_at="now",
                completed_at="later",
                stage_statuses={},
            )
            write_report(path, data)
            self.assertTrue(path.exists())
            self.assertFalse(path.with_name(".idea-report.md.tmp").exists())


if __name__ == "__main__":
    unittest.main()
