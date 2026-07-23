# e2e evidence — 2026-07-08, company `e2e207` (ceo + builder only, heartbeat 45s)

Run: `make shared COMPANY=e2e207 ACCOUNT=foundagent` +
`COMPANY=e2e207 ACCOUNT=foundagent CEO_HEARTBEAT_SECS=45 docker compose -f docker-compose.yml up -d ceo builder`,
two heartbeat wakes each, then teardown (`docker stop/rm e2e207-ceo e2e207-builder`).
State kept at `state/e2e207/` (gitignored).

## Boot lines (session policy resolved from yaml)

```
[agent_loop] boot key=builder ... session=fresh
[agent_loop:builder] start heartbeat=45s session=fresh-per-wake
[agent_loop] boot key=ceo ... session=resume
[agent_loop:ceo] start heartbeat=45s session=(new)
```

## AC2 — telemetry (`state/e2e207/telemetry/wake.*.jsonl`)

| key | wake | session_id | cost_usd | ok |
|---|---|---|---|---|
| builder | 1 | cec97df6-… | $0.254 | ✓ |
| builder | 2 | 63f22f68-… (≠ wake 1) | $0.256 | ✓ |
| ceo | 1 | 722e93a7-… | $0.447 | ✓ |
| ceo | 2 | 722e93a7-… (= wake 1) | $0.090 | ✓ |

- builder: two wakes, two distinct session ids; `sessions/builder/session_id`
  file NEVER created.
- ceo: same id across wakes; `sessions/ceo/session_id` contains it.

## AC1 — auto-memory dead

- `find state/e2e207/sessions -type d -name memory` → **0 dirs** (claude never
  even created the memory directory under projects/-home-kasm-user/).
- builder wake-1 transcript
  (`projects/-home-kasm-user/cec97df6….jsonl`): 0 hits for
  `MEMORY.md|auto memory|memory directory` → the harness memory guidance is
  gone from the system prompt entirely.

## AC5 — orientation prefix (behavioral)

- Transcript contains `Before acting, orient yourself` (4 hits).
- builder wake-2 final text: “…the only company activity is the CEO's
  in-flight research goal owned by the researcher” — a FRESH session knew
  company state it was never told in-prompt, i.e. it followed the orient
  instruction and read /company.

## AC4 direction (deferred to next longrun for the formal check)

Idle-heartbeat cost on a fresh session: **$0.25** (builder) vs **$12.57** on
the resume-forever firsttest fat session — two orders of magnitude, and flat
across wakes by construction (no accumulating history to re-read).
