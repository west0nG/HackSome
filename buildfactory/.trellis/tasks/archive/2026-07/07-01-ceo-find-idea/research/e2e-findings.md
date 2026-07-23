# e2e findings — find-opportunity skeleton (2026-07-01)

Ran `CEO_HEARTBEAT_SECS=45 make up`, observed real CEO heartbeat wakes (`make logs` / `docker logs foundagent-ceo`), then `make down`.

## What passed
- **Materialization ✓** — CEO loadout line: `skills=['send-goal', 'find-opportunity', 'decide-direction']`. New skill dir reaches the container via the `./agents:/opt/foundagent-orch/agents` bind mount; charter via `./agents/assets:/opt/foundagent-orch/charters` bind mount (so charter edits take effect on the NEXT wake, no rebuild).
- **Full judgment chain runs live ✓** — after the charter fix (below), the CEO ran research signal → `decide-direction` with an **independent reviewer that returned RESHAPE** ("valid niche, but validate with a real buyer on a narrow wedge before building the full agent") → dispatched a narrowed Goal to `growth`. The decide-direction half is verified working end-to-end against a real LLM.

## Bug found & fixed during e2e (charter conflict)
- **First heartbeat wake: find-opportunity did NOT fire.** CEO output: *"No open tasks or goals — nothing needs doing right now."* — it stopped instead of generating direction.
- **Root cause:** `ceo-charter.md` Principle *"Don't busy-work. On a heartbeat with nothing to do, say so in one line and stop."* out-competed the find-opportunity nudge. For an empty company, "no direction" is NOT "nothing to do" — it's the cue to generate one.
- **Fix (declarative, zero .py):** rewrote that Principle to carve out "no direction in flight at all is NOT nothing to do → generate direction", and strengthened the find-opportunity paragraph to "an idle heartbeat with no direction is your cue to find one, not a reason to stop." After the fix the CEO became active on heartbeat.

## First run caveat (masked by persistent state)
- The default `/company` volume (`./companies/foundagent`) carried **persistent state from prior runs**: `mission.md` (+ `research/niche_brief.md`) already locked a **product** direction ("freight exception handling for SMB 3PLs"). So the CEO continued that product direction and never hit the "no direction in hand → find-opportunity" path. Re-ran on a clean company (below).

## ✅ AC7 PASS — clean empty company (`PUMP_COMPANY=e2e-findopp`, fresh CEO session)
Brought the stack up with a throwaway empty company dir (cold-start; `company.py` auto-creates MAP.md) and a fresh CEO session. First heartbeat wake, CEO turn:
> "Research goal `bf5806cb…` dispatched to `researcher` — looking for real demand signals for **info-products/research-as-a-service**. Will generate 2-3 candidate directions once results come back."

Every design intent fired:
- **Business-form aware, NON-product** — the CEO picked a **service / info-product** form (info-products / research-as-a-service), not "build software." find-opportunity's core new value confirmed live.
- **Signal-first, don't fabricate** — instead of inventing a direction it dispatched a research Goal FIRST, and said it would produce 2-3 candidates once results return (the "get real signal before you imagine anything" + "2-3 distinct candidates" discipline).
- **Grounded research** — the dispatched Goal asks for real demand on real marketplaces (Gumroad/Patreon/Substack/Fiverr) and real communities (Reddit/HN/indie-hacker), "specific examples of real demand, not general trends" — Sales-Safari-style, even though per-form methods are still placeholders (the general signal-first path produced the right kind of research).
- **Charter trigger** — on the empty company the CEO did NOT say "nothing to do"; it recognized "no direction → generate one." (The `295a11d` charter fix works.)

## Status vs AC7 — all ACs now verified
- Materialization + charter-trigger + decide-direction chain + **find-opportunity's own form-aware, signal-grounded, from-scratch generation**: **verified live.** AC1-AC7 pass.
