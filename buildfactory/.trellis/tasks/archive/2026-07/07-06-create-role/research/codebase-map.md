# Research: Codebase map — what runtime role-creation must touch

- **Query**: What would have to change for a NEW agent role to be created at RUNTIME by the CEO agent (instead of statically checked into the repo)?
- **Scope**: internal
- **Date**: 2026-07-06

---

## 1. Anatomy of a role today

A role = **4 static artifacts + 1 compose service**. Nothing else.

| Artifact | Path | Consumed by |
|---|---|---|
| Role yaml | `agents/<role>.yaml` | `agent/spec.py` (both run paths), `agent/resident_loadout.py`, `orchestration/agent_loop.py:_role_config`, `agent/loadout_check.py` |
| Charter | `agents/assets/<role>-charter.md` | resident path: compose env `AGENT_CHARTER`; ephemeral path: yaml `system_prompt` |
| MCP config | `agents/mcp/<role>.json` | yaml `mcp_config` → `--mcp-config` per wake |
| Skills | `agents/assets/skills/<name>/SKILL.md` (pool) | yaml `skills:` list → materialized into claude home at container startup |
| Compose service | `docker-compose.yml` services block | `make up` — this is what actually *runs* the role |

### Role yaml fields (`agent/spec.py`)

- Known fields: `_FIELDS` at `agent/spec.py:33-44` — `name, provider, credentials, model, effort, system_prompt, skills, hooks, mcp_config, permission_mode`. Unknown keys are ignored (forward-compatible).
- **Nothing is strictly required**: `name` defaults from the filename (`spec.py:72-73`); every other field has a default (`spec.py:48-61`). Defaults: `provider=claude-code`, `credentials=subscription`, `model=claude-opus-4-8` / `effort=xhigh` (`spec.py:29-30`), `mcp_config=/opt/foundagent/mcp.json` (roleless fallback), `permission_mode=bypass`.
- Asset paths (`system_prompt`, `skills`, `hooks`, relative `mcp_config`) resolve **relative to the yaml's own directory** (`spec.py:79-93`), so a yaml outside `agents/` can't reference `assets/skills/...` relatively unless the mechanism accounts for it.
- Examples read: `agents/ceo.yaml` (skills 14-19, mcp 20), `agents/builder.yaml` (hooks 13: `../company_state_kit/hooks/settings.snippet.json`), `agents/growth.yaml` (7 skills), `agents/verifier.yaml` (deliberately **no hooks** — the record Stop hook would clobber the final `VERDICT:` line, verifier.yaml:14-15), `agents/researcher.yaml` (`credentials: api-key` variant).

### Charter is wired TWICE (important for a create mechanism)

1. Yaml `system_prompt: assets/<role>-charter.md` — used by the **ephemeral** `broker.spawn`/`run_task` path (`agent/runner.py:99`).
2. Compose env `AGENT_CHARTER: /opt/foundagent-orch/charters/<role>-charter.md` — used by the **resident** path (`docker-compose.yml:98,108,118,128,138` → `orchestration/agent_loop.py:348`). The charters dir is a bind mount of `agents/assets/` (`docker-compose.yml:46`).

A `role create` must keep both pointing at the same file (write charter once, reference twice).

### Skills attachment

- Declared in yaml `skills:` as paths (convention: `assets/skills/<name>`).
- Resident path: materialized ONCE at container startup by `vm/docker/agent_startup.sh:32` → `agent/resident_loadout.py:materialize_for` (`resident_loadout.py:50-81`) → `agent/loadout.py:materialize` (`loadout.py:46-92`), which copies each skill dir into `<claude_home>/skills/<name>/` and merges hook snippets into `settings.json`, with a reconcile manifest (`.loadout-manifest.json`, `loadout.py:31`) so removed skills get cleaned up on next start. `claude_home` = `CLAUDE_CONFIG_DIR` = `/sessions/<role>` (`resident_loadout.py:36-38`, compose:99 etc.).
- **Consequence: changing a role's skills requires a container restart** — materialization is startup-only.
- Skill file convention (`agents/assets/skills/*/SKILL.md`): YAML frontmatter `name` + trigger-phrased `description` ("Use when/whenever ..."), second-person imperative body, concrete fenced commands. See `send-goal/SKILL.md`, `receive-goal/SKILL.md`, `set-objective/SKILL.md`. No existing skill scaffolds/creates files-on-disk artifacts; the closest structural template for role-creation is the **set-objective / review-objective / objective-CLI triad** (drafting skill + reviewer-exclusive rubric skill + pure-mechanism CLI).

---

## 2. Role name → running agent (resident path)

Boot chain: compose service → kasm desktop → `vm/docker/agent_startup.sh` (computer-server bg at :25-26; `agent.resident_loadout` at :32; `orchestration.agent_loop` fg at :34) → `agent_loop.main()`.

`agent_loop.main()` (`orchestration/agent_loop.py:339-375`):

- `AGENT_KEY` env = the role (`:347`). `AGENT_CHARTER` env = charter path (`:348`).
- `_role_config(key)` (`:315-336`) reads `agents/<AGENT_KEY>.yaml` from `AGENTS_DIR` (env, default `/opt/foundagent-orch/agents`, `:324`) for model/effort/mcp_config. **Missing yaml → pure fleet defaults, no crash** (`:326-327`).
- MCP precedence (`:353-357`): `AGENT_MCP` env (manual override) > yaml `mcp_config` > `DEFAULT_MCP_CONFIG=/opt/foundagent/mcp.json` (`:44`).
- Company overlay may swap/off charter+mcp (`_overlay_charter_mcp`, `:283-312`).
- Objective: `AGENT_OBJECTIVE` env, default `/agents/<key>/objective.md`; **dir auto-created** (`:364-369`); re-read fresh EVERY wake and prepended to the wake prompt (`:259-271`, `build_wake_prompt` `:55-80`, cap 6000 chars `:50`).
- Each wake = `claude -p <prompt> --resume <sid> --append-system-prompt <charter> --mcp-config <json> --model --effort --strict-mcp-config --dangerously-skip-permissions` (`build_claude_argv` `:132-160`; `--strict-mcp-config` unconditional `:158`).
- Session id persisted to `AGENT_SESSION_FILE` (compose: `/sessions/<role>/session_id`).

### Hardcoded vs filesystem-discovered role list

**Filesystem-discovered (free for a new role):**

- `agent_loop._role_config` — reads `agents/<key>.yaml` per-container at boot (`agent_loop.py:324-327`).
- `agent/resident_loadout.py:57-60` — reads `agents/<key>.yaml`; missing = charter-only, never bricks.
- `agent/loadout_check.py:38-39` — known roles = `glob(agents/*.yaml)`; a new yaml automatically becomes a valid overlay target.
- Inbox: `FileInbox.append` creates `<key>.jsonl` for ANY key (`orchestration/inbox.py:136-152`); the loop polls its own key (`agent_loop.py:259`).
- Objective dir auto-mkdir (`agent_loop.py:366`).
- Ledger `role`/`assignee` are free-form strings (`orchestration/goal_ledger.py:165-196`).

**Hardcoded (a `role create` must handle):**

- `docker-compose.yml:92-140` — five static services (differ ONLY by `AGENT_KEY`, `AGENT_CHARTER`, `CLAUDE_CONFIG_DIR`, `AGENT_SESSION_FILE`; shared `x-agent` anchor :33-76 + `x-agent-env` :78-89).
- `Makefile:16` — `ROLES := ceo researcher builder growth verifier`; `shared` target (`:18-24`) pre-creates + chmod-777s `state/<company>/sessions/<role>` only for these.
- `agents/assets/ceo-charter.md:48` — "Departments you can send to: `researcher`, `builder`, `growth`" — the CEO's routing knowledge is **prompt-static**.
- `orchestration/hub.py:54` — `VERIFIER_KEY = "verifier"` (only pinned role key; contract comment :50-53).
- `agent/tests/test_mcp_assets.py:28` — `ROLES` list (test-only; new roles simply not covered).

### Ephemeral path (dormant, for reference)

`orchestration/broker.py:spawn` (`:46-140`): host-side `materialize()` into `vm/data/op-<id>/claude` (`:63-67`), `docker run` with account env-file/`/account` mount/proxy (`:68-93`), then `agent/runner.py:run_task` via `docker exec` (`:76-125`). Compose keeps the broker container alive-but-dormant (`docker-compose.yml:164-185`, `sleep infinity`). ⚠️ `broker.py:34` `DEFAULT_SPEC = agents/operator.yaml` — **this file no longer exists**; the dormant default-spec path would crash if revived unchanged.

---

## 3. Orchestration Hub: routing & department registration

**There is no department registry.** The Hub is registration-free:

- `DISPATCH to=<key>` → the Hub creates+claims the goal and does `inbox.append(msg["to"], _work_ime(...))` (`orchestration/hub.py:250-270`, append at `:269`). Any string is a valid key; `FileInbox.append` will create the file.
- A "department" is *defined* as: a live `agent_loop` instance polling that inbox key. Nothing else.
- **Goal to an unknown department**: no error at dispatch. The work IME lands in an inbox nobody drains; the deadline sweep (`hub.py:377-401`) times it out after `HUB_DEADLINE_SECS` (default 1800s, `:57`), retries to the same assignee up to `HUB_MAX_ATTEMPTS` (default 3, `:59`), then kills + notifies the parent (`_done_ime` `:199-214`). Fails slow-but-safe.
- **Late-started department works**: if the container comes up before the deadline, the message is already sitting in its inbox (poll drains the backlog); `reconcile` (`hub.py:404-445`) also re-issues in-flight work with deterministic ids (`_route_id` `:146-151`), deduped by the receiver's `.seen` set (`inbox.py:144-150`).
- doer≠judge is sender-identity enforced: work-report accepted only from `goal["assignee"]` (`hub.py:285-287`); verdict accepted only from `VERIFIER_KEY` (`hub.py:300-301`). Neither gate needs to know the role set in advance.

**So dynamic registration requires ZERO Hub/state-machine/ledger/reconcile changes.** The only "registration" is (a) getting the container running, and (b) telling *dispatchers* (mainly the CEO) that the key exists — today that lives only in `ceo-charter.md:48` + the CEO's session memory.

Reserved keys a new role must not take: `hub` (`inbox.py:33`), `ceo` (`inbox.py:29`), `verifier` (`hub.py:54`), plus `harness` is used as an ad-hoc reply key in live state (`state/foundagent/inbox/harness.jsonl`).

---

## 4. Docker / VM layer

- **One container per role**, all from the SAME image `foundagent/cua-agent:latest` (compose `x-agent` :33-34). Role identity arrives 100% via env + bind mounts; the image is role-agnostic.
- Baked into the image (`vm/docker/Dockerfile.agent`): claude CLI (:38), gh/vercel/wrangler CLIs (:42-56), and the pinned MCP servers — dataforseo 2.9.11 (:63-65), playwright-mcp 0.0.77 + chromium at `/opt/ms-playwright` (:73-79), analytics-mcp 0.6.0 + mcp-gsc 0.1.0 (:86-90), thin cua MCP + roleless fallback `/opt/foundagent/mcp.json` (:93-94). **Nothing per-role is baked** → a runtime role needs NO image rebuild *as long as its MCP config only references already-baked servers*. A genuinely new MCP server = image rebuild (or cold install at runtime).
- Per-role compose env (the only per-service delta): `AGENT_KEY`, `AGENT_CHARTER`, `CLAUDE_CONFIG_DIR=/sessions/<role>`, `AGENT_SESSION_FILE=/sessions/<role>/session_id` (`docker-compose.yml:96-140`).
- Shared mounts every agent gets (compose :44-75): `orchestration/`, `agent/`, `agents/` (**read-only**, :51), `agents/assets` as `/opt/foundagent-orch/charters` (**ro**, :46), `company_state_kit`, `/company`, `/shared/ledger`, `/shared/inbox`, config overlay (ro), `/agents` (objectives, rw), `/sessions`, `/account` (ro), `agent_startup.sh`.
- Credentials are company-level, not role-level: `vm/.env.local` + `accounts/<ACCOUNT>/secrets.env` env-files (compose :35-43) — a new role container reuses them unchanged.

**What breaks for a runtime-created role:**

1. No compose service → no container → its inbox never drained (goals to it time out, §3).
2. `agents/` and `agents/assets/` are mounted **ro** into every agent container (compose :46,51) → **the CEO cannot write the role yaml/charter/mcp/skills from inside its own container**.
3. Agent containers have **no docker.sock** (compose :76) → the CEO cannot start the new container either. The **broker** container is the only one with the sock + the repo mounted **rw at the identical host path** (compose :171-175) — the natural execution point for a spawn step (or host-side `make`/CLI).
4. `state/<company>/sessions/<newrole>/` isn't pre-created (`Makefile:18-24` only covers static ROLES). Parent `sessions/` is chmod 777, so it *can* be created at runtime, but the mechanism should mkdir+chmod it explicitly (containers write as uid 1000).
5. Restart semantics: whatever starts the container must survive `make down` / `make up` — either a generated compose override (e.g. `docker-compose.roles.yml` merged via `COMPOSE_FILE`) or re-invocation on boot; a bare `docker run` diverges from the compose lifecycle.

---

## 5. `company_state_kit/` and `state/`

- `company_state_kit/company.py` — the `/company` wiki CLI (read/write/tree/record + nav reconcile). **No role registry, no role references.** Nothing to update on role creation.
- `state/<company>/` layout (all runtime artifacts, gitignored):
  - `sessions/<role>/` — per-role claude home (materialized skills + `settings.json` + session). **Must exist & be writable for a new role** (see §4.4).
  - `agents/<role>/objective.md` — auto-created by `agent_loop.py:366`. Free.
  - `inbox/<role>.jsonl|.cursor|.seen` — auto-created on first append/poll. Free.
  - `config/loadout.yaml` — company overlay; `roles.<name>` validated against `glob(agents/*.yaml)` (`loadout_check.py:38-43`), so a new yaml is automatically legal. Free.
  - `ledger/` — goal files; `role`/`assignee` free-form. Free.

---

## 6. Quality-gate / review patterns to reuse

### The `objective propose` gate (`orchestration/objective.py`) — the exact template

- Pure-mechanism CLI, zero judgment in code (module docstring :16-17): drafting judgment lives in the proposer's skill (`set-objective`), review judgment in the reviewer's skill (`review-objective`).
- Reviewer = a **fresh** `claude -p` (no `--resume`, none of the proposer's context) with the rubric skill injected via `--append-system-prompt` (`run_reviewer` :128-138). Rubric path: `DEFAULT_REVIEWER_SKILL = agents/assets/skills/review-objective/SKILL.md` (:53-54), env-overridable (`OBJECTIVE_REVIEWER`).
- **Rubric is reviewer-exclusive**: deliberately NOT in the CEO's loadout — `agents/ceo.yaml:19` comment: "review-objective is deliberately NOT wired here — the rubric belongs to the reviewer; the objective CLI loads it itself (doer≠judge)".
- Injection guard: proposal fenced as content-under-review, not instructions (`build_review_prompt` :95-125).
- Verdict: last `VERDICT: GO|RESHAPE|DROP` line wins (:59, :81-92); **fail-closed** (exit 2) on missing skill / reviewer crash / unparseable verdict (:176-204); GO → archive previous to `objective.history.md` + atomic temp-file+`os.replace` write (`_write_go` :141-161). Exit codes 0/1/2 (:30-34).
- Rubric skill structure to copy: `agents/assets/skills/review-objective/SKILL.md` — frontmatter says "NOT for the proposing agent"; numbered walk-every-criterion checks; "Output contract" section pinning the exact final `VERDICT:` line.

### Hub doer≠judge (already covered §3)

Sender-identity gates at `hub.py:285-287` (assignee) and `hub.py:300-301` (verifier).

### The human SOP the CEO-facing skill should encode

`aiworkforce/SOP-adding-roles-and-skills.md` — 8-phase gated process (scope→research→三道检验→赋能vs限制→标定体量→落点charter/skill/reference→实现+单测→真跑e2e→迭代). A `create-role` drafting skill is essentially this SOP compressed for an LLM proposer; a `review-role` rubric is its gate criteria.

---

## 7. Full MCP set (2026-07-06 decision) — evidence in code

- All five `agents/mcp/*.json` are **byte-identical** (md5 `833f065c4a1b4409a95015320f7b3206` for every role). Content = full set `{cua-local, dataforseo, gsc, ga4, playwright}` with `${VAR}` credential expansions.
- Enforced by `agent/tests/test_mcp_assets.py`: `FULL_SERVER_SET` (:21), `test_json_parses_with_full_server_set` (:36-38), credential-literal ban (:80-86), yaml→file resolution check (:89-94). Docstring (:2-8) records the decision: "don't pre-assume which role uses which tool — give everything to everyone, prune later"; "the per-role FILE mechanism is kept so roles can diverge again later; only the contents are uniform today."
- Every role yaml carries the comment `# full server set (07-06 capability-first)` (`ceo.yaml:20`, `builder.yaml:14`, `researcher.yaml:14`, `growth.yaml:24`, `verifier.yaml:16`).
- Applied at runtime by `agent_loop._role_config` (`agent_loop.py:315-336`) → `--mcp-config` per wake; `--strict-mcp-config` always (`agent_loop.py:158`). Compose comment `docker-compose.yml:84-88` documents the precedence.
- **Consequence for `role create`**: the new role's `agents/mcp/<name>.json` is a verbatim copy of the canonical full-set file — no per-role MCP decision needed; keep the per-role file (convention) rather than sharing one file.

---

## Minimal touch list for a `role create <name>` operation

### Must WRITE (host-side or broker-side — agent containers see these paths ro)

| # | Artifact | Notes |
|---|---|---|
| 1 | `agents/<name>.yaml` | fields per §1; skills reference the pool `assets/skills/...`; `mcp_config: mcp/<name>.json`; `hooks: ../company_state_kit/hooks/settings.snippet.json` iff memory-enabled (omit for judge-type roles, cf. verifier.yaml:14-15) |
| 2 | `agents/assets/<name>-charter.md` | referenced twice: yaml `system_prompt` + container env `AGENT_CHARTER=/opt/foundagent-orch/charters/<name>-charter.md` |
| 3 | `agents/mcp/<name>.json` | copy of the canonical full server set (07-06 decision, §7) |
| 4 | (optional) `agents/assets/skills/<skill>/SKILL.md` | only for genuinely new custom skills; existing pool skills are referenced, not copied |
| 5 | `state/<company>/sessions/<name>/` | mkdir + chmod 777 (Makefile `shared` only covers static ROLES, `Makefile:16-24`) |
| 6 | A container definition + start | the ONLY new mechanism. Replicate the `x-agent` template with 4 env deltas (`AGENT_KEY`, `AGENT_CHARTER`, `CLAUDE_CONFIG_DIR`, `AGENT_SESSION_FILE`); options: generated compose override merged into `make up`, or `docker run` from the broker (sock + rw repo at identical path, compose:171-175; NB dormant path's `broker.py:34` default-spec points at a deleted `agents/operator.yaml`) |

### Must NOTIFY

| # | Target | Notes |
|---|---|---|
| 7 | The CEO's dispatch knowledge | `agents/assets/ceo-charter.md:48` hardcodes the department list; charter is static per-wake. If the CEO itself creates the role, session memory covers the current session; durable knowledge needs either a charter regeneration, an inbox IME, or making the list dynamic (e.g. derived from `agents/*.yaml` in the send-goal skill) |

### Already free (filesystem-discovered — zero changes)

- Hub routing to any key (`hub.py:269`) + state machine / ledger / reconcile / watchdog (§3)
- Inbox files auto-created per key (`inbox.py:136-152`)
- Objective dir + `objective.md` auto-created, injected per wake (`agent_loop.py:364-369`, `:259-271`)
- Role yaml discovery at container boot (`agent_loop.py:324-327`, `resident_loadout.py:57-60`)
- Skills/hooks materialization at startup (`agent_startup.sh:32` → `loadout.py:46`)
- `loadout_check` role validation (glob, `loadout_check.py:38-39`) and overlay `roles.<name>` legality
- Credentials (company-level env_files, role-agnostic, compose :35-43)
- The image itself (role-agnostic; all four external MCP servers + playwright chromium pre-baked, `Dockerfile.agent:63-90`)
- `objective propose` review-gate machinery, directly reusable as the shape of a `role propose` gate (§6)

### Watch-outs / constraints

- Reserved keys: `ceo`, `hub`, `verifier` (+ `harness` in live state). Role name is used as a filename, an inbox key, a container-name suffix, and a docker-compose service name — must be validated (safe charset).
- Skill/loadout changes for an existing role require container restart (startup-only materialization, §1).
- `agents/` tree writes from runtime make the git worktree dirty — the repo treats `agents/` as checked-in config (`.trellis` memory: autonomous git commits are allowed; alternatively a runtime roles dir + `AGENTS_DIR` env is possible but `AGENTS_DIR` is a single dir, no search path, and the charters mount is pinned to `agents/assets`).
- `agent/tests/test_mcp_assets.py:28` hardcodes the 5-role list — runtime-created roles are simply untested by it (no failure), but if the mechanism is meant to keep the invariants (full set, no credential literals), reusing that test's checks in the CLI's validation step is cheap.
- A goal dispatched to a not-yet-started role is safe but slow-fails after `HUB_DEADLINE_SECS × HUB_MAX_ATTEMPTS` (§3) — start the container before announcing the role to dispatchers.

## Caveats / Not Found

- No existing CLI or skill anywhere in the repo creates roles/files-on-disk today; `role create` would be the first (CLI-first convention per MCP-provisioning memory).
- `agents/operator.yaml` referenced by dormant `broker.py:34` does not exist — pre-existing dangling reference, noted, not fixed.
- Did not inspect `vm/docker/Dockerfile` (base image) or `peripheral/` internals in depth — neither is role-aware beyond what's documented above.
