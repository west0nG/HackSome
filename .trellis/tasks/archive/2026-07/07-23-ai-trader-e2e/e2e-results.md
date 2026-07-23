# AI Trader E2E Results

## Run

- Directory: `runs/ai-trader-e2e-v1-20260723`
- Model: `gpt-5.6-terra`
- Reasoning effort: `high`
- Idea Generator: v4
- Idea Red Team: v3
- Status: completed and offline-validated
- Wall clock: approximately 14 minutes

## Funnel

```text
5 Audiences
→ 5 Research
→ 23 Problems
→ 1 Problem pass / 22 reject
→ 3 Generator Sessions
→ 5 Ideas
→ 2 Idea pass / 3 reject
→ 2 Idea Cards
```

## Findings

1. The real-product framing worked: no Idea proposed a fake/synthetic core input or a one-off demonstration as its first version.
2. Both passing cards express the same product thesis: a decision-date data gate that creates a point-in-time validation receipt and blocks unvalidated backtests from being treated as evidence.
3. Red Team distinguished a real blocking control from reports or simulations that could not reconstruct missing historical facts.
4. Problem Gateway remained at an approximately 4% pass rate, matching the miHoYo run despite richer public finance evidence.
5. Gateway rejected several real workflows because prevalence, quantified loss, or a directly observed final failure was missing. It also rejected a point-in-time lineage Problem for quantitative researchers while passing a highly similar Problem for financial technology teams.
6. The next quality change should relax evidentiary sufficiency without relaxing the realness bar: direct task/failure/workaround evidence or strong multi-source inference should pass even when public sources do not quantify total loss.

## Local Analysis

`runs/ai-trader-e2e-v1-20260723/analysis/e2e-evaluation.md`
