"""Command-line interface for the local Idea-only workflow."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from hacksome.codex import CodexRunner
from hacksome.config import CodexConfig
from hacksome.models import CodexDoctorResult
from hacksome.state import StateError
from hacksome.workflow import (
    UsefulIdeaWorkflow,
    WorkflowError,
    WorkflowSettings,
    inspect_run,
    validate_run,
)


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return parsed


def _audience_limit(value: str) -> int:
    parsed = _positive_int(value)
    if parsed > 5:
        raise argparse.ArgumentTypeError("must not exceed 5 in v1")
    return parsed


def _non_negative_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("must not be negative")
    return parsed


def _positive_float(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a number") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    defaults = WorkflowSettings()
    codex_defaults = CodexConfig()
    parser = argparse.ArgumentParser(
        prog="hacksome",
        description="Find evidence-backed Useful hackathon Ideas with local Codex sessions.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    run = commands.add_parser("run", help="start a new Idea discovery run")
    run.add_argument("challenge", nargs="?", type=Path, help="UTF-8 challenge file")
    run.add_argument("--prompt", help="literal challenge instead of a file")
    run.add_argument("--runs-dir", type=Path, default=Path("runs"))
    run.add_argument("--run-id")
    run.add_argument("--codex", default=codex_defaults.executable, metavar="PATH")
    run.add_argument("--model")
    run.add_argument(
        "--max-concurrency",
        type=_positive_int,
        default=codex_defaults.max_concurrency,
    )
    run.add_argument(
        "--infrastructure-retries",
        type=_non_negative_int,
        default=codex_defaults.infrastructure_retries,
    )
    run.add_argument(
        "--max-audiences", type=_audience_limit, default=defaults.max_audiences
    )
    run.add_argument(
        "--researchers-per-audience",
        type=_positive_int,
        default=defaults.researchers_per_audience,
    )
    run.add_argument(
        "--idea-generators-per-problem",
        type=_positive_int,
        default=defaults.idea_generators_per_problem,
    )
    run.add_argument(
        "--task-timeout",
        type=_positive_float,
        default=defaults.task_timeout_seconds,
        metavar="SECONDS",
    )
    run.add_argument(
        "--run-timeout",
        type=_positive_float,
        default=defaults.run_timeout_seconds,
        metavar="SECONDS",
    )

    status = commands.add_parser("status", help="inspect a saved run")
    status.add_argument("run_dir", type=Path)
    status.add_argument("--json", action="store_true")

    validate = commands.add_parser("validate", help="validate a saved run offline")
    validate.add_argument("run_dir", type=Path)

    doctor = commands.add_parser("doctor", help="check Codex CLI and login")
    doctor.add_argument("--codex", default=codex_defaults.executable, metavar="PATH")
    doctor.add_argument(
        "--timeout",
        type=_positive_float,
        default=codex_defaults.doctor_timeout_seconds,
    )
    doctor.add_argument("--json", action="store_true")
    return parser


def _read_challenge(args: argparse.Namespace, parser: argparse.ArgumentParser) -> str:
    if (args.challenge is None) == (args.prompt is None):
        parser.error("run requires exactly one of CHALLENGE or --prompt")
    if args.prompt is not None:
        if not args.prompt.strip():
            parser.error("--prompt must not be empty")
        return args.prompt
    assert args.challenge is not None
    content = args.challenge.expanduser().read_text(encoding="utf-8")
    if not content.strip():
        raise ValueError(f"challenge file is empty: {args.challenge}")
    return content


def _run_command(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    challenge = _read_challenge(args, parser)
    settings = WorkflowSettings(
        max_audiences=args.max_audiences,
        researchers_per_audience=args.researchers_per_audience,
        idea_generators_per_problem=args.idea_generators_per_problem,
        task_timeout_seconds=args.task_timeout,
        run_timeout_seconds=args.run_timeout,
    )
    config = CodexConfig(
        executable=args.codex,
        model=args.model,
        max_concurrency=args.max_concurrency,
        infrastructure_retries=args.infrastructure_retries,
        default_timeout_seconds=args.task_timeout,
    )
    workflow = UsefulIdeaWorkflow.create(
        challenge,
        args.runs_dir,
        settings=settings,
        codex_config=config,
        run_id=args.run_id,
    )
    print(f"Run directory: {workflow.run_dir}")
    index = asyncio.run(workflow.execute())
    print(f"Idea Cards: {index}")
    return 0


def _status_command(args: argparse.Namespace) -> int:
    payload = inspect_run(args.run_dir)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    print(f"Run: {payload['run_id']}")
    print(f"Status: {payload['status']}")
    print(f"Current stage: {payload.get('current_stage') or '-'}")
    counts = payload.get("task_counts", {})
    rendered = ", ".join(
        f"{status}={count}" for status, count in sorted(counts.items())
    ) if isinstance(counts, dict) and counts else "none"
    print(f"Tasks: {rendered}")
    print(f"Decisions: {payload.get('decision_count', 0)}")
    print(f"Idea Cards: {payload.get('idea_card_count', 0)}")
    return 0


def _validate_command(args: argparse.Namespace) -> int:
    errors = validate_run(args.run_dir)
    if errors:
        print(f"Validation failed with {len(errors)} error(s):", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    print("Run is valid.")
    return 0


def _doctor_payload(result: CodexDoctorResult) -> dict[str, Any]:
    return {
        "healthy": result.healthy,
        "executable": result.executable,
        "available": result.available,
        "version": result.version,
        "authenticated": result.authenticated,
        "capabilities": result.capabilities,
        "error": result.error,
    }


def _doctor_command(args: argparse.Namespace) -> int:
    result = asyncio.run(
        CodexRunner(
            CodexConfig(executable=args.codex, doctor_timeout_seconds=args.timeout)
        ).doctor()
    )
    payload = _doctor_payload(result)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"Codex: {'healthy' if result.healthy else 'unhealthy'}")
        print(f"Executable: {result.executable}")
        print(f"Version: {result.version or '-'}")
        print(f"Authenticated: {result.authenticated}")
        if result.error:
            print(f"Error: {result.error}")
    return 0 if result.healthy else 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "run":
            return _run_command(args, parser)
        if args.command == "status":
            return _status_command(args)
        if args.command == "validate":
            return _validate_command(args)
        if args.command == "doctor":
            return _doctor_command(args)
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130
    except (OSError, StateError, ValueError, WorkflowError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    parser.error(f"unknown command: {args.command}")
    return 2


__all__ = ["build_parser", "main"]
