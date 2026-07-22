"""Command-line interface for the local Useful Idea workflow."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

from hacksome.codex import CodexRunner
from hacksome.config import CodexConfig
from hacksome.models import CodexDoctorResult
from hacksome.state import StateError, StateStore
from hacksome.workflow import (
    UsefulIdeaWorkflow,
    WorkflowError,
    WorkflowSettings,
    inspect_run,
    validate_run,
)


_DEFAULT_CODEX = CodexConfig()
_DEFAULT_WORKFLOW = WorkflowSettings()


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
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


def _add_runtime_arguments(
    parser: argparse.ArgumentParser,
    *,
    defaults: bool,
) -> None:
    parser.add_argument(
        "--codex",
        default=_DEFAULT_CODEX.executable if defaults else None,
        metavar="PATH",
        help="Codex CLI executable (default: codex)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Codex model override",
    )
    parser.add_argument(
        "--max-concurrency",
        type=_positive_int,
        default=_DEFAULT_CODEX.max_concurrency if defaults else None,
        metavar="N",
        help="maximum simultaneous Codex sessions (default: 4)",
    )
    parser.add_argument(
        "--infrastructure-retries",
        type=_non_negative_int,
        default=_DEFAULT_CODEX.infrastructure_retries if defaults else None,
        metavar="N",
        help="retries for transient Codex failures (default: 1)",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hacksome",
        description="Find evidence-backed Useful hackathon ideas with local Codex sessions.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="start a new Useful Idea run")
    run_parser.add_argument(
        "challenge",
        nargs="?",
        type=Path,
        help="UTF-8 file containing the hackathon prompt",
    )
    run_parser.add_argument(
        "--prompt",
        help="literal hackathon prompt instead of a file",
    )
    run_parser.add_argument(
        "--runs-dir",
        type=Path,
        default=Path("runs"),
        help="parent directory for run outputs (default: ./runs)",
    )
    run_parser.add_argument(
        "--run-id",
        help="explicit run id; otherwise a timestamped id is generated",
    )
    _add_runtime_arguments(run_parser, defaults=True)
    run_parser.add_argument(
        "--task-timeout",
        type=_positive_float,
        default=_DEFAULT_WORKFLOW.task_timeout_seconds,
        metavar="SECONDS",
        help="deadline for one Codex task (default: 1200)",
    )
    run_parser.add_argument(
        "--run-timeout",
        type=_positive_float,
        default=_DEFAULT_WORKFLOW.run_timeout_seconds,
        metavar="SECONDS",
        help="deadline for the whole workflow (default: 21600)",
    )
    run_parser.add_argument(
        "--researchers-per-audience",
        type=_positive_int,
        default=_DEFAULT_WORKFLOW.researchers_per_audience,
        metavar="N",
        help="parallel problem researchers per audience (default: 3)",
    )
    run_parser.add_argument(
        "--problem-writers-per-audience",
        type=_positive_int,
        default=_DEFAULT_WORKFLOW.problem_writers_per_audience,
        metavar="N",
        help="parallel problem writers per audience (default: 3)",
    )
    run_parser.add_argument(
        "--idea-generators-per-problem",
        type=_positive_int,
        default=_DEFAULT_WORKFLOW.idea_generators_per_problem,
        metavar="N",
        help="parallel idea generators per passed problem (default: 5)",
    )

    resume_parser = subparsers.add_parser("resume", help="continue a saved run")
    resume_parser.add_argument("run_dir", type=Path, help="existing run directory")
    _add_runtime_arguments(resume_parser, defaults=False)

    status_parser = subparsers.add_parser("status", help="inspect a saved run")
    status_parser.add_argument("run_dir", type=Path, help="existing run directory")
    status_parser.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON",
    )

    validate_parser = subparsers.add_parser(
        "validate", help="validate completed task outputs"
    )
    validate_parser.add_argument("run_dir", type=Path, help="existing run directory")

    doctor_parser = subparsers.add_parser(
        "doctor", help="check Codex CLI capabilities and login"
    )
    doctor_parser.add_argument(
        "--codex",
        default=_DEFAULT_CODEX.executable,
        metavar="PATH",
        help="Codex CLI executable (default: codex)",
    )
    doctor_parser.add_argument(
        "--timeout",
        type=_positive_float,
        default=_DEFAULT_CODEX.doctor_timeout_seconds,
        metavar="SECONDS",
        help="timeout for each diagnostic probe (default: 10)",
    )
    doctor_parser.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON",
    )
    return parser


def _read_challenge(args: argparse.Namespace, parser: argparse.ArgumentParser) -> str:
    if (args.challenge is None) == (args.prompt is None):
        parser.error("run requires exactly one of CHALLENGE or --prompt")
    if args.prompt is not None:
        if not args.prompt.strip():
            parser.error("--prompt must not be empty")
        return args.prompt
    assert args.challenge is not None
    try:
        prompt = args.challenge.expanduser().read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"challenge file is not valid UTF-8: {args.challenge}") from exc
    if not prompt.strip():
        raise ValueError(f"challenge file is empty: {args.challenge}")
    return prompt


def _workflow_settings(args: argparse.Namespace) -> WorkflowSettings:
    return WorkflowSettings(
        researchers_per_audience=args.researchers_per_audience,
        problem_writers_per_audience=args.problem_writers_per_audience,
        idea_generators_per_problem=args.idea_generators_per_problem,
        task_timeout_seconds=args.task_timeout,
        run_timeout_seconds=args.run_timeout,
    )


def _codex_config(
    args: argparse.Namespace,
    *,
    task_timeout: float,
    base: CodexConfig | None = None,
) -> CodexConfig:
    base = base or _DEFAULT_CODEX
    return replace(
        base,
        executable=args.codex or base.executable,
        model=base.model if args.model is None else args.model,
        max_concurrency=args.max_concurrency or base.max_concurrency,
        default_timeout_seconds=task_timeout,
        infrastructure_retries=(
            base.infrastructure_retries
            if args.infrastructure_retries is None
            else args.infrastructure_retries
        ),
    )


def _stored_settings(run_dir: Path) -> WorkflowSettings:
    state = StateStore(run_dir.expanduser().resolve()).load()
    raw = state.data.get("settings")
    if raw is None:
        return WorkflowSettings()
    if not isinstance(raw, dict):
        raise ValueError("saved workflow settings must be a JSON object")
    return WorkflowSettings(**cast(dict[str, Any], raw))


def _stored_codex_config(run_dir: Path) -> CodexConfig:
    state = StateStore(run_dir.expanduser().resolve()).load()
    raw = state.data.get("codex_config")
    if raw is None:
        return CodexConfig()
    if not isinstance(raw, dict):
        raise ValueError("saved Codex configuration must be a JSON object")
    normalized: dict[str, Any] = dict(raw)
    for key in ("disabled_features", "config_overrides"):
        value = normalized.get(key)
        if isinstance(value, list):
            normalized[key] = tuple(value)
    return CodexConfig(**normalized)


def _run_command(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    prompt = _read_challenge(args, parser)
    settings = _workflow_settings(args)
    config = _codex_config(args, task_timeout=settings.task_timeout_seconds)
    workflow = UsefulIdeaWorkflow.create(
        prompt,
        args.runs_dir,
        settings=settings,
        codex_config=config,
        run_id=args.run_id,
    )
    print(f"Run directory: {workflow.run_dir}")
    report = asyncio.run(workflow.execute())
    print(f"Report: {report}")
    return 0


def _resume_command(args: argparse.Namespace) -> int:
    has_override = any(
        value is not None
        for value in (
            args.codex,
            args.model,
            args.max_concurrency,
            args.infrastructure_retries,
        )
    )
    if has_override:
        settings = _stored_settings(args.run_dir)
        config = _codex_config(
            args,
            task_timeout=settings.task_timeout_seconds,
            base=_stored_codex_config(args.run_dir),
        )
        workflow = UsefulIdeaWorkflow(args.run_dir, codex_config=config)
    else:
        workflow = UsefulIdeaWorkflow(args.run_dir)
    print(f"Resuming: {workflow.run_dir}")
    report = asyncio.run(workflow.execute())
    print(f"Report: {report}")
    return 0


def _status_payload(run_dir: Path) -> dict[str, Any]:
    return inspect_run(run_dir)


def _status_command(args: argparse.Namespace) -> int:
    payload = _status_payload(args.run_dir)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    print(f"Run: {payload['run_id']}")
    print(f"Status: {payload['status']}")
    print(f"Current stage: {payload.get('current_stage') or '-'}")
    task_counts = payload.get("task_counts", {})
    if isinstance(task_counts, dict) and task_counts:
        rendered = ", ".join(
            f"{status}={count}" for status, count in sorted(task_counts.items())
        )
    else:
        rendered = "none"
    print(f"Tasks: {rendered}")
    print(f"Final ideas: {payload.get('final_idea_count', 0)}")
    print(f"Eliminations: {payload.get('elimination_count', 0)}")
    warnings = payload.get("warnings", [])
    if isinstance(warnings, list) and warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    next_actions = payload.get("next_actions", [])
    if isinstance(next_actions, list) and next_actions:
        print("Next actions:")
        for action in next_actions:
            print(f"  - {action}")
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
    runner = CodexRunner(
        CodexConfig(
            executable=args.codex,
            doctor_timeout_seconds=args.timeout,
        )
    )
    result = asyncio.run(runner.doctor())
    payload = _doctor_payload(result)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"Codex: {'healthy' if result.healthy else 'unhealthy'}")
        print(f"Executable: {result.executable}")
        print(f"Available: {'yes' if result.available else 'no'}")
        print(f"Version: {result.version or '-'}")
        authenticated = "unknown"
        if result.authenticated is not None:
            authenticated = "yes" if result.authenticated else "no"
        print(f"Authenticated: {authenticated}")
        if result.capabilities:
            print("Capabilities:")
            for name, available in sorted(result.capabilities.items()):
                print(f"  - {name}: {'yes' if available else 'no'}")
        if result.error:
            print(f"Error: {result.error}")
    return 0 if result.healthy else 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "run":
            return _run_command(args, parser)
        if args.command == "resume":
            return _resume_command(args)
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
