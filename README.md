# HackSome

HackSome is a local, Codex-only orchestrator for finding evidence-backed
`Useful` hackathon ideas. Version 0.1 implements the complete idea workflow:

```text
challenge -> audiences -> research -> verification -> problems -> gateway
          -> ideas -> competitor research -> revision -> red team
          -> build feasibility -> idea-report.md
```

It deliberately does not rank candidates, force different directions, or keep
only a fixed number. Every candidate that clears the same absolute quality
gates remains in the report.

## Install

Python 3.11 or newer and a logged-in `codex` CLI are required.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/hacksome doctor
```

Do not use a bare `pip3` on machines where it may point at a different Python.

## Run

Pass either a file or literal text:

```bash
hacksome run challenge.md
hacksome run --prompt "Build something useful for local communities"
```

By default, runs are stored under `./runs/<run-id>/` and at most four Codex
sessions execute at once. Stage sessions use workspace-scoped writes; live web
search is enabled only for problem research, evidence verification, and
competitor research.

```bash
hacksome run challenge.md --runs-dir ./runs --max-concurrency 6
hacksome status ./runs/<run-id>
hacksome validate ./runs/<run-id>
hacksome resume ./runs/<run-id>
```

Each run keeps the raw prompt, immutable research/review artifacts, Living
Document revision snapshots, per-session JSONL logs, `state.json`, an
append-only decision ledger, and the deterministic final `idea-report.md`.

## Safety boundary

Version 0.1 runs locally without Docker or a VM. Codex receives write access
only to a task-specific run directory, never `danger-full-access`. Publishing,
dependency installation for generated products, Build, GitHub operations, and
Pitch generation are outside this release.

## Tests

The default suite uses a scripted runner and a fake Codex executable, so it
does not spend model tokens:

```bash
python3 -m unittest discover -s tests -v
```

A real model run is always explicit through `hacksome run`; there is no paid
smoke test in the default quality gate.
