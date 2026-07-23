#!/usr/bin/env python3
"""Run one live objective review through the production Codex adapter.

The company/agents/inbox roots and CODEX_HOME are temporary.  Only the
sanitized request, Codex JSONL stream, verdict event, and result summary are
persisted under the requested artifacts directory.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

from agent.runtimes import runtime_for
from agent.runtimes.base import RunRequest
from agent.spec import AgentSpec
from orchestration import objective


def _events(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _scoped_environ(values: dict[str, str]):
    class Scope:
        def __enter__(self):
            self.previous = {key: os.environ.get(key) for key in values}
            os.environ.update(values)

        def __exit__(self, exc_type, exc, tb):
            for key, value in self.previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    return Scope()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--proposal", type=Path, required=True)
    parser.add_argument("--short", type=Path, required=True)
    parser.add_argument("--company-path", required=True)
    parser.add_argument("--company-summary", required=True)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--auth-seed", type=Path, required=True)
    parser.add_argument("--expect", choices=("PASS", "FAIL"), required=True)
    parser.add_argument("--sentinel", required=True)
    parser.add_argument("--audit-note", default="")
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()

    repo = args.repo.resolve()
    proposal = args.proposal.resolve()
    short = args.short.resolve()
    artifacts = args.artifacts.resolve()
    artifacts.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="objective-live-e2e-") as tmp:
        root = Path(tmp)
        agents_root = root / "agents"
        company_root = root / "company"
        inbox_root = root / "inbox"
        ceo_objective = agents_root / "ceo" / "objective.md"
        runtime_env = {
            "AGENT_KEY": "ceo",
            "AGENT_OBJECTIVE": str(ceo_objective),
            "OBJECTIVE_ROOT": str(agents_root),
            "COMPANY_ROOT": str(company_root),
            "GOAL_INBOX": str(inbox_root),
            "PYTHONPATH": str(repo),
        }
        with _scoped_environ(runtime_env):
            staged = objective.main([
                "propose",
                "--file", str(proposal),
                "--short-file", str(short),
                "--company-path", args.company_path,
                "--company-summary", args.company_summary,
            ])
        if staged != 0:
            print(f"proposal staging failed with exit {staged}", file=sys.stderr)
            return 2

        requests = _events(inbox_root / "verifier.jsonl")
        if len(requests) != 1:
            print(f"expected one review request, found {len(requests)}", file=sys.stderr)
            return 2
        request = requests[0]
        audit_note = args.audit_note.strip()
        prompt = (
            "You have received the following real resident inbox event. Process "
            "it now using the review-objective skill. Do not merely explain what "
            "you would do: inspect the named staged surfaces and evidence, then "
            "execute exactly one objective verdict command.\n\n"
            f"{request['body']}\n\n"
            "E2E audit requirement: every local load-bearing source you open may "
            "contain an E2E-SOURCE-SENTINEL unknown to the proposal. Include that "
            "sentinel verbatim in the review file so the harness can prove the "
            "source was actually opened.\n"
            "Host isolation note: logical /company is mounted at the directory "
            "in $COMPANY_ROOT for this run. Use company.py for navigation; do "
            "not treat the absence of a literal host /company directory as "
            "business evidence. If the container fallback path is absent, use "
            f"python3 {repo / 'company_state_kit' / 'company.py'} instead."
        )
        if audit_note:
            prompt += f"\n{audit_note}"

        spec = AgentSpec.load(str(repo / "agents" / "verifier.yaml"))
        runtime = runtime_for(spec)
        run_request = RunRequest(
            prompt=prompt,
            charter=spec.read_system_prompt(),
            mcp_config=spec.resolve(spec.mcp_config) if spec.mcp_config else None,
            model=spec.model,
            effort=spec.effort,
            bypass_permissions=spec.bypass_permissions,
        )
        argv = runtime.build_argv(run_request)

        codex_home = root / "codex-home"
        codex_home.mkdir(mode=0o700)
        shutil.copy2(args.auth_seed.resolve(), codex_home / "auth.json")
        bin_dir = root / "bin"
        bin_dir.mkdir()
        python = Path(sys.executable)
        python_wrapper = bin_dir / "python3"
        python_wrapper.write_text(
            f'#!/bin/sh\nexec "{python}" "$@"\n',
            encoding="utf-8",
        )
        python_wrapper.chmod(0o755)
        company_wrapper = bin_dir / "company.py"
        company_wrapper.write_text(
            '#!/bin/sh\n'
            f'exec "{python}" "{repo / "company_state_kit" / "company.py"}" '
            '"$@"\n',
            encoding="utf-8",
        )
        company_wrapper.chmod(0o755)

        child_env = os.environ.copy()
        child_env.update(runtime_env)
        child_env.update({
            "AGENT_KEY": "verifier",
            "AGENT_OBJECTIVE": str(agents_root / "verifier" / "objective.md"),
            "CODEX_HOME": str(codex_home),
            "PATH": f"{bin_dir}{os.pathsep}{child_env['PATH']}",
        })

        process = subprocess.Popen(
            argv,
            cwd=repo,
            env=child_env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        lines: list[str] = []
        timed_out = False

        def kill_on_timeout() -> None:
            nonlocal timed_out
            if process.poll() is not None:
                return
            timed_out = True
            try:
                process.kill()
            except ProcessLookupError:
                timed_out = False

        timer = threading.Timer(args.timeout, kill_on_timeout)
        timer.start()
        assert process.stdout is not None
        try:
            for line in process.stdout:
                lines.append(line)
                print(line, end="", flush=True)
            returncode = process.wait()
        finally:
            timer.cancel()
        if timed_out:
            lines.append("\nE2E HARNESS TIMEOUT\n")

        stdout = "".join(lines)
        parsed = runtime.parse_output(stdout, returncode)
        verdict_events = [
            event for event in _events(inbox_root / "ceo.jsonl")
            if str(event.get("body", "")).startswith("OBJECTIVE-VERDICT role=ceo")
        ]
        verdict_event = verdict_events[-1] if verdict_events else None
        verdict_body = str((verdict_event or {}).get("body", ""))

        state = {
            "objective_exists": ceo_objective.exists(),
            "active_metadata_exists": objective.active_manifest_path(
                ceo_objective
            ).exists(),
            "proposal_manifest_exists": objective.proposed_manifest_path(
                ceo_objective
            ).exists(),
            "proposal_verdict_marker_exists": objective.proposed_verdict_path(
                ceo_objective
            ).exists(),
            "company_leaf_exists": (
                company_root / args.company_path
            ).exists(),
        }
        result = {
            "adapter": spec.provider,
            "model": argv[argv.index("-m") + 1] if "-m" in argv else None,
            "returncode": returncode,
            "timed_out": timed_out,
            "runtime_ok": parsed.ok,
            "runtime_error": parsed.error,
            "session_token": parsed.session_token,
            "usage": parsed.usage,
            "agent_final_text": parsed.text,
            "request": request,
            "verdict_event": verdict_event,
            "state": state,
        }
        expected_token = f"verdict={args.expect}"
        checks = {
            "runtime_ok": parsed.ok and not timed_out,
            "verdict_emitted": verdict_event is not None,
            "expected_verdict": expected_token in verdict_body,
            "source_opened": args.sentinel in verdict_body,
        }
        result["checks"] = checks
        (artifacts / "request.md").write_text(prompt + "\n", encoding="utf-8")
        (artifacts / "codex.jsonl").write_text(stdout, encoding="utf-8")
        (artifacts / "result.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (artifacts / "review.md").write_text(verdict_body + "\n", encoding="utf-8")
        print("\n===E2E_RESULT===")
        print(json.dumps({"checks": checks, **result}, ensure_ascii=False, indent=2))
        return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
