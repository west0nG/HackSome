# AI Trader Gateway v3 E2E Results

## Run

- Directory: `runs/ai-trader-e2e-v2-gateway-v3-20260723`
- Model: `gpt-5.6-terra`
- Reasoning effort: `high`
- Problem Gateway: v3
- Idea Generator: v4
- Idea Red Team: v3
- Status: completed and offline-validated
- Tasks: 138 succeeded, 0 failed
- Wall clock: approximately 29.5 minutes

## Funnel

```text
5 Audiences
→ 5 Research
→ 19 Problems
→ 14 Problem pass / 5 reject
→ 42 Generator Sessions
→ 65 Ideas
→ 36 Idea pass / 29 reject
→ 36 Idea Cards
```

## Findings

1. Gateway v3 no longer demanded audit-grade proof and retained grounded
   Problems with observed failures or repeated, costly, fragile workarounds.
2. The five rejected Problems still matched the intended hard boundaries:
   generic responsibility, governance requirement without observed failure,
   invented causal chain, or unsupported root cause.
3. The Red Team rejected all Ideas for validation-set contamination and risk
   limit closure because they could not control off-system observation or
   obtain execution evidence.
4. The strongest products were earnings-model evidence writeback, executable
   backtest contracts, transaction-cost survival boundaries, earnings-number
   verification, and point-in-time data evidence.
5. The main new quality issue is Generator convergence: ten passing titles use
   “账本”, ten use “台”, and ten use “证据”.
6. The larger valid Problem pool increased downstream Generator and Red Team
   tasks from 8 in v1 to 107 in v2.

## Analysis

`runs/ai-trader-e2e-v2-gateway-v3-20260723/analysis/e2e-evaluation.md`
