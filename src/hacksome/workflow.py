"""Explicit S0-S11 orchestration for the Useful Idea workflow.

The state machine in this module is intentionally concrete. It owns one Codex
runtime, one set of artifact contracts, and the bounded loops agreed for v0.1;
it is not a generic workflow DSL or provider layer.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
import shutil
import sys
from collections.abc import Awaitable, Callable, Collection, Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any, TypeVar, cast
from uuid import uuid4

from hacksome.artifacts import (
    ArtifactDocument,
    ArtifactStore,
    PromotionRequest,
    parse_markdown_file,
    safe_join,
    safe_relative_path,
    validate_document,
)
from hacksome.codex import CodexRunner
from hacksome.config import CodexConfig
from hacksome.models import CodexResult, CodexTask
from hacksome.prompting import PromptRenderer, RenderedPrompt
from hacksome.report import (
    EliminationSummary,
    ReportIdea,
    ReportInput,
    write_report,
)
from hacksome.state import (
    RunState,
    RunStatus,
    StateStore,
    TaskRecord,
    TaskStatus,
    atomic_write_bytes,
    atomic_write_json,
    read_json_object,
    stable_record_id,
    stable_task_id,
)


_SAFE_SEGMENT = re.compile(r"^[a-z0-9][a-z0-9-]{0,95}$")
_T = TypeVar("_T")


class WorkflowError(RuntimeError):
    """A required workflow transition could not be completed."""


class TaskExecutionError(WorkflowError):
    """One Codex task exhausted its infrastructure or format retry budget."""


@dataclass(frozen=True, slots=True)
class WorkflowSettings:
    researchers_per_audience: int = 3
    problem_writers_per_audience: int = 3
    idea_generators_per_problem: int = 5
    task_timeout_seconds: float = 20 * 60
    run_timeout_seconds: float = 6 * 60 * 60
    artifact_format_retries: int = 1
    output_language: str = "match-input"
    research_query_budget: int = 12
    competition_query_budget: int = 10
    team_size: int = 1
    local_environment: str = (
        f"Local machine; Python {sys.version_info.major}.{sys.version_info.minor}; "
        "Codex CLI; no Docker or VM; no assumed paid third-party accounts."
    )

    def __post_init__(self) -> None:
        for name in (
            "researchers_per_audience",
            "problem_writers_per_audience",
            "idea_generators_per_problem",
            "research_query_budget",
            "competition_query_budget",
            "team_size",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"{name} must be a positive integer")
        if (
            isinstance(self.artifact_format_retries, bool)
            or not isinstance(self.artifact_format_retries, int)
            or self.artifact_format_retries < 0
        ):
            raise ValueError("artifact_format_retries must be a non-negative integer")
        if (
            isinstance(self.task_timeout_seconds, bool)
            or not isinstance(self.task_timeout_seconds, (int, float))
            or self.task_timeout_seconds <= 0
        ):
            raise ValueError("task_timeout_seconds must be positive")
        if (
            isinstance(self.run_timeout_seconds, bool)
            or not isinstance(self.run_timeout_seconds, (int, float))
            or self.run_timeout_seconds <= 0
        ):
            raise ValueError("run_timeout_seconds must be positive")
        if not isinstance(self.output_language, str) or not self.output_language.strip():
            raise ValueError("output_language must not be empty")
        if (
            not isinstance(self.local_environment, str)
            or not self.local_environment.strip()
        ):
            raise ValueError("local_environment must not be empty")


@dataclass(frozen=True, slots=True)
class ArtifactTaskResult:
    task_id: str
    output_paths: tuple[str, ...]
    routing_metadata: Mapping[str, Mapping[str, Any]]
    session_id: str
    empty: bool = False

    def metadata_for(self, path: str) -> Mapping[str, Any]:
        try:
            return self.routing_metadata[path]
        except KeyError as exc:
            raise WorkflowError(
                f"task {self.task_id} has no saved routing metadata for {path}"
            ) from exc


@dataclass(frozen=True, slots=True)
class PassedProblem:
    problem_ref: str
    gateway_ref: str
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FinalIdea:
    idea_ref: str
    problem_ref: str
    gateway_ref: str
    evidence_refs: tuple[str, ...]
    competition_refs: tuple[str, ...]
    red_team_ref: str
    feasibility_ref: str


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def create_run_id() -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    return f"run-{stamp}-{uuid4().hex[:8]}"


def _json_data(value: Any) -> dict[str, Any]:
    # StateStore performs the authoritative JSON validation. This conversion
    # detaches YAML mappings and tuples before they enter RunState.data.
    copied = json.loads(json.dumps(value, ensure_ascii=False, allow_nan=False))
    if not isinstance(copied, dict):
        raise TypeError("expected a JSON object")
    return copied


def _safe_id(value: str, *, field: str) -> str:
    normalized = value.strip().lower()
    if value != normalized or not _SAFE_SEGMENT.fullmatch(normalized):
        raise WorkflowError(f"unsafe {field}: {value!r}")
    return normalized


def _posix(path: Path, root: Path) -> str:
    return PurePosixPath(*path.resolve().relative_to(root.resolve()).parts).as_posix()


def _sha256_file(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise WorkflowError(f"integrity-bound path is not a regular file: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _validate_bound_artifact(
    artifact_store: ArtifactStore,
    run_root: Path,
    run_id: str,
    reference: str,
    expected_metadata: Mapping[str, Any],
    expected_sha256: str | None = None,
) -> ArtifactDocument:
    """Validate an exact task output or its immutable Living Document snapshot."""

    current = artifact_store.validate_canonical(reference)
    if all(
        current.metadata.get(key) == value
        for key, value in expected_metadata.items()
    ):
        if expected_sha256 is not None:
            current_path = artifact_store.canonical_path(reference, must_exist=True)
            actual_sha256 = hashlib.sha256(current_path.read_bytes()).hexdigest()
            if actual_sha256 != expected_sha256:
                raise WorkflowError(
                    f"completed artifact content changed: {reference}"
                )
        return current
    expected_revision = expected_metadata.get("revision")
    current_revision = current.revision
    if (
        isinstance(expected_revision, int)
        and not isinstance(expected_revision, bool)
        and isinstance(current_revision, int)
        and expected_revision < current_revision
    ):
        snapshot_ref = artifact_store.snapshot_relative_path(
            reference, expected_revision
        )
        snapshot = parse_markdown_file(
            safe_join(
                run_root,
                snapshot_ref,
                must_exist=True,
                file_only=True,
            )
        )
        validated = validate_document(
            snapshot,
            run_root=run_root,
            relative_path=reference,
            expected_run_id=run_id,
            expected_metadata=expected_metadata,
        )
        if expected_sha256 is not None:
            snapshot_path = safe_join(
                run_root,
                snapshot_ref,
                must_exist=True,
                file_only=True,
            )
            actual_sha256 = hashlib.sha256(snapshot_path.read_bytes()).hexdigest()
            if actual_sha256 != expected_sha256:
                raise WorkflowError(
                    f"completed artifact snapshot changed: {snapshot_ref}"
                )
        return validated
    raise WorkflowError(
        f"canonical artifact no longer matches completed task binding: {reference}"
    )


def _structured_json_projection(
    structured_output: Mapping[str, Any], reference: str
) -> Mapping[str, Any]:
    projections = {
        "discovery-view.json": "discovery_view",
        "compliance-view.json": "compliance_view",
    }
    key = projections.get(reference)
    value: Any = structured_output if key is None else structured_output.get(key)
    if not isinstance(value, Mapping):
        raise WorkflowError(
            f"saved structured output has no object projection for {reference}"
        )
    return value


class UsefulIdeaWorkflow:
    """Run or resume one local Useful Idea pipeline."""

    def __init__(
        self,
        run_dir: str | Path,
        *,
        settings: WorkflowSettings | None = None,
        codex_config: CodexConfig | None = None,
        runner: CodexRunner | None = None,
        prompt_renderer: PromptRenderer | None = None,
    ) -> None:
        self.run_dir = Path(run_dir).expanduser().resolve()
        self.state_store = StateStore(self.run_dir)
        self.state = self.state_store.load()
        stored_settings = self.state.data.get("settings")
        if settings is None and isinstance(stored_settings, dict):
            settings = WorkflowSettings(
                **cast(dict[str, Any], stored_settings)
            )
        self.settings = settings or WorkflowSettings()
        if runner is None:
            if codex_config is None:
                stored_codex = self.state.data.get("codex_config")
                if isinstance(stored_codex, dict):
                    normalized_codex: dict[str, Any] = dict(stored_codex)
                    for key in ("disabled_features", "config_overrides"):
                        value = normalized_codex.get(key)
                        if isinstance(value, list):
                            normalized_codex[key] = tuple(value)
                    try:
                        codex_config = CodexConfig(**normalized_codex)
                    except (TypeError, ValueError) as exc:
                        raise WorkflowError(
                            f"saved Codex configuration is invalid: {exc}"
                        ) from exc
            config = codex_config or CodexConfig(
                default_timeout_seconds=self.settings.task_timeout_seconds
            )
            runner = CodexRunner(config)
        self.runner = runner
        self.prompts = prompt_renderer or PromptRenderer()
        self.artifacts = ArtifactStore(self.run_dir, run_id=self.state.run_id)

    @classmethod
    def create(
        cls,
        prompt: str,
        runs_dir: str | Path,
        *,
        settings: WorkflowSettings | None = None,
        codex_config: CodexConfig | None = None,
        runner: CodexRunner | None = None,
        prompt_renderer: PromptRenderer | None = None,
        run_id: str | None = None,
    ) -> "UsefulIdeaWorkflow":
        if not prompt.strip():
            raise ValueError("challenge prompt must not be empty")
        run_id = run_id or create_run_id()
        _safe_id(run_id, field="run id")
        root = Path(runs_dir).expanduser().resolve() / run_id
        root.mkdir(parents=True, exist_ok=False)
        challenge_path = root / "challenge.md"
        challenge_content = (prompt.rstrip() + "\n").encode("utf-8")
        atomic_write_bytes(challenge_path, challenge_content)
        chosen = settings or WorkflowSettings()
        chosen_codex = codex_config or CodexConfig(
            default_timeout_seconds=chosen.task_timeout_seconds
        )
        StateStore(root).initialize(
            run_id,
            data={
                "created_at": utc_now(),
                "completed_at": None,
                "challenge_ref": "challenge.md",
                "challenge_sha256": hashlib.sha256(challenge_content).hexdigest(),
                "settings": asdict(chosen),
                "codex_config": asdict(chosen_codex),
                "stage_statuses": {},
                "warnings": [],
                "eliminations": [],
                "final_ideas": [],
            },
        )
        return cls(
            root,
            settings=chosen,
            codex_config=chosen_codex,
            runner=runner,
            prompt_renderer=prompt_renderer,
        )

    async def execute(self) -> Path:
        self.state = self.state_store.load()
        challenge_path = self.artifacts.canonical_path(
            "challenge.md", must_exist=True
        )
        expected_challenge_hash = self.state.data.get("challenge_sha256")
        if not isinstance(expected_challenge_hash, str):
            raise WorkflowError("run state has no raw challenge integrity binding")
        if _sha256_file(challenge_path) != expected_challenge_hash:
            raise WorkflowError("raw challenge content changed after run creation")
        if self.state.status is RunStatus.COMPLETED:
            errors = validate_run(self.run_dir)
            if errors:
                raise WorkflowError(
                    "completed run failed validation: " + "; ".join(errors)
                )
            return self.run_dir / "idea-report.md"
        self._set_run(status=RunStatus.RUNNING)
        try:
            async with asyncio.timeout(self.settings.run_timeout_seconds):
                report = await self._execute_pipeline()
        except TimeoutError as exc:
            self._warn("Whole-run deadline reached; resume can continue saved tasks.")
            self._set_run(status=RunStatus.FAILED, next_actions=["resume"])
            raise WorkflowError("whole-run deadline reached") from exc
        except BaseException:
            self._set_run(status=RunStatus.FAILED, next_actions=["resume"])
            raise
        self._set_run(
            status=RunStatus.COMPLETED,
            current_stage="S11",
            next_actions=[],
        )
        return report

    async def _execute_pipeline(self) -> Path:
        brief = await self._stage_s0()
        audiences = await self._stage_s1(brief)
        research, verifications = await self._stage_s2_s3(brief, audiences)
        problems = await self._stage_s4(brief, audiences, research, verifications)
        passed = await self._stage_s5(
            brief, audiences, problems, research, verifications
        )
        ideas = await self._stage_s6(brief, passed)
        finals = await self._stage_s7_s10(brief, ideas, passed)
        return self._stage_s11(brief, finals)

    def _set_run(
        self,
        *,
        status: RunStatus | None = None,
        current_stage: str | None = None,
        next_actions: Sequence[str] | None = None,
        completed_at: str | None = None,
    ) -> None:
        def mutate(state: RunState) -> None:
            if status is not None:
                state.status = status
            if current_stage is not None:
                state.current_stage = current_stage
            if next_actions is not None:
                state.next_actions = list(next_actions)
            if completed_at is not None:
                state.data["completed_at"] = completed_at

        self.state = self.state_store.mutate(mutate)

    def _set_stage(self, stage: str, status: str) -> None:
        def mutate(state: RunState) -> None:
            state.current_stage = stage
            statuses = state.data.setdefault("stage_statuses", {})
            assert isinstance(statuses, dict)
            statuses[stage] = status

        self.state = self.state_store.mutate(mutate)

    def _warn(self, message: str) -> None:
        def mutate(state: RunState) -> None:
            warnings = state.data.setdefault("warnings", [])
            assert isinstance(warnings, list)
            if message not in warnings:
                warnings.append(message)

        self.state = self.state_store.mutate(mutate)

    def _task(self, task_id: str) -> TaskRecord | None:
        return self.state_store.load().tasks.get(task_id)

    def _save_task(self, task: TaskRecord) -> None:
        self.state = self.state_store.upsert_task(task)

    def _task_dir(self, task_id: str) -> Path:
        return self.artifacts.task_staging_dir(task_id)

    def _copy_context_refs(
        self,
        task_dir: Path,
        refs: Collection[str],
    ) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        for reference in sorted(dict.fromkeys(refs)):
            relative = safe_relative_path(reference, field_name="context reference")
            source = self.artifacts.canonical_path(relative.as_posix(), must_exist=True)
            destination = task_dir / "context" / Path(*relative.parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                if destination.read_bytes() != source.read_bytes():
                    raise WorkflowError(
                        f"stable task context changed unexpectedly: {reference}"
                    )
            else:
                shutil.copy2(source, destination)
            artifact_type = self._artifact_type(reference, source)
            entries.append(
                {
                    "artifact_type": artifact_type,
                    "canonical_ref": relative.as_posix(),
                    "relative_path": _posix(destination, task_dir),
                    "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                }
            )
        return entries

    @staticmethod
    def _artifact_type(reference: str, source: Path) -> str:
        if source.suffix.lower() == ".md" and reference != "challenge.md":
            return str(parse_markdown_file(source).metadata.get("artifact_type", "unknown"))
        names = {
            "brief.json": "challenge_brief",
            "discovery-view.json": "discovery_view",
            "compliance-view.json": "compliance_view",
            "audiences.json": "audience_list",
            "challenge.md": "raw_challenge",
        }
        return names.get(reference, "structured_input")

    def _render(
        self,
        stage: str,
        task_id: str,
        context_manifest: Mapping[str, Any],
        output_target: str,
        mode: str,
        attempt: int,
    ) -> RenderedPrompt:
        language = self.settings.output_language
        if language == "match-input":
            detected = self.state.data.get("input_language")
            language = (
                str(detected)
                if isinstance(detected, str) and detected.strip()
                else "the same language as the raw challenge"
            )
        return self.prompts.render(
            stage,
            {
                "run_id": self.state.run_id,
                "task_id": task_id,
                "language": language,
                "context_manifest": context_manifest,
                "output_target": output_target,
                "mode": mode,
                "attempt": attempt,
                "session_marker": "pending",
            },
        )

    @staticmethod
    def _recover_session(task_dir: Path) -> str | None:
        stdout = task_dir / "logs" / "stdout.jsonl"
        if not stdout.is_file():
            return None
        try:
            lines = stdout.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            return None
        for line in reversed(lines):
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            event = record.get("event") if isinstance(record, dict) else None
            if not isinstance(event, dict):
                continue
            session = event.get("thread_id") or event.get("session_id")
            thread = event.get("thread")
            if session is None and isinstance(thread, dict):
                session = thread.get("id") or thread.get("thread_id")
            if isinstance(session, str) and session.strip():
                return session
        return None

    async def _run_codex(
        self,
        *,
        stage: str,
        task_id: str,
        rendered: RenderedPrompt,
        output_schema: Path,
        web_search: bool,
        task_dir: Path,
        resume_session: str | None,
        extra_prompt: str = "",
    ) -> CodexResult:
        prompt = rendered.text + extra_prompt
        return await self.runner.run(
            CodexTask(
                task_id=task_id,
                prompt=prompt,
                cwd=task_dir,
                output_schema=output_schema,
                web_search=web_search,
                timeout_seconds=self.settings.task_timeout_seconds,
                session_id=resume_session,
                resume=resume_session is not None,
                log_dir=task_dir / "logs",
            )
        )

    def _mark_running(
        self,
        *,
        task_id: str,
        stage: str,
        rendered: RenderedPrompt,
        mode: str,
        context_manifest: Mapping[str, Any],
        output_target: str,
        prior: TaskRecord | None,
        session_id: str | None,
    ) -> TaskRecord:
        task = prior or TaskRecord(task_id=task_id, stage=stage)
        task.status = TaskStatus.RUNNING
        task.session_id = session_id
        task.last_error = None
        task.next_action = "wait-for-codex"
        task.data.update(
            {
                "mode": mode,
                "context_hash": rendered.context_hash,
                "prompt_hash": rendered.prompt_hash,
                "prompt_template_id": rendered.prompt_template_id,
                "prompt_version": rendered.prompt_version,
                "template_hash": rendered.template_hash,
                "output_target": output_target,
                "context_manifest": _json_data(dict(context_manifest)),
            }
        )
        self._save_task(task)
        return task

    def _mark_failed(self, task: TaskRecord, message: str, attempts: int = 0) -> None:
        task.status = TaskStatus.FAILED
        task.attempts += attempts
        task.data.pop("pending_attempts", None)
        task.last_error = message
        task.next_action = "resume"
        self._save_task(task)

    def _prepare_publication(
        self,
        task: TaskRecord,
        result: CodexResult,
        outputs: Sequence[str],
        *,
        attempts: int,
        routing_metadata: Mapping[str, Mapping[str, Any]] | None = None,
        output_hashes: Mapping[str, str] | None = None,
        structured_output: Mapping[str, Any] | None = None,
    ) -> None:
        """Persist enough state to recover a publish/state crash boundary."""

        task.session_id = result.session_id
        task.outputs = list(outputs)
        task.next_action = "verify-publication"
        task.data["publication_prepared"] = True
        task.data["pending_attempts"] = attempts
        task.data["usage"] = _json_data(dict(result.usage))
        task.data["started_at"] = result.started_at
        task.data["finished_at"] = result.finished_at
        if routing_metadata is not None:
            task.data["routing_metadata"] = _json_data(dict(routing_metadata))
        if output_hashes is not None:
            task.data["output_hashes"] = _json_data(dict(output_hashes))
        if structured_output is not None:
            task.data["structured_output"] = _json_data(dict(structured_output))
        self._save_task(task)

    def _finish_prepared_task(self, task: TaskRecord) -> None:
        pending_attempts = task.data.pop("pending_attempts", 0)
        if isinstance(pending_attempts, int) and not isinstance(pending_attempts, bool):
            task.attempts += pending_attempts
        task.data.pop("publication_prepared", None)
        task.status = TaskStatus.COMPLETED
        task.last_error = None
        task.next_action = None
        self._save_completed_task(task)

    def _save_completed_task(self, task: TaskRecord) -> None:
        def mutate(state: RunState) -> None:
            state.upsert_task(task)
            state.completed_artifacts = sorted(
                dict.fromkeys([*state.completed_artifacts, *task.outputs])
            )

        self.state = self.state_store.mutate(mutate)

    def _mark_completed(
        self,
        task: TaskRecord,
        result: CodexResult,
        outputs: Sequence[str],
        *,
        attempts: int | None = None,
        routing_metadata: Mapping[str, Mapping[str, Any]] | None = None,
        structured_output: Mapping[str, Any] | None = None,
    ) -> None:
        task.status = TaskStatus.COMPLETED
        task.session_id = result.session_id
        task.attempts += result.attempts if attempts is None else attempts
        task.outputs = list(outputs)
        task.last_error = None
        task.next_action = None
        task.data["usage"] = _json_data(dict(result.usage))
        task.data["started_at"] = result.started_at
        task.data["finished_at"] = result.finished_at
        task.data.pop("publication_prepared", None)
        task.data.pop("pending_attempts", None)
        if routing_metadata is not None:
            task.data["routing_metadata"] = _json_data(dict(routing_metadata))
        if structured_output is not None:
            task.data["structured_output"] = _json_data(dict(structured_output))
        self._save_completed_task(task)

    def _append_task_event(self, task: TaskRecord, result: CodexResult) -> None:
        record = {
            "event_id": stable_record_id(
                "event", task.task_id, result.started_at, result.status.value
            ),
            "type": "task.completed" if result.success else "task.failed",
            "task_id": task.task_id,
            "stage": task.stage,
            "status": result.status.value,
            "session_id": result.session_id,
            "attempts": result.attempts,
            "usage": result.usage,
            "started_at": result.started_at,
            "finished_at": result.finished_at,
        }
        self.state_store.append_event(record)

    async def _execute_json_task(
        self,
        *,
        stage: str,
        identity: Sequence[Any],
        mode: str,
        context_manifest: Mapping[str, Any],
        output_target: str,
        schema_name: str,
        output_paths: Sequence[str],
        publish: Callable[[Mapping[str, Any]], None],
    ) -> Mapping[str, Any]:
        task_id = stable_task_id(stage, self.state.run_id, *identity, mode)
        existing = self._task(task_id)
        if existing is not None and existing.status is TaskStatus.COMPLETED:
            saved = existing.data.get("structured_output")
            if isinstance(saved, dict):
                try:
                    for path in existing.outputs:
                        actual = read_json_object(
                            self.artifacts.canonical_path(path, must_exist=True)
                        )
                        expected = _structured_json_projection(saved, path)
                        if actual != expected:
                            raise WorkflowError(
                                f"completed JSON output changed: {path}"
                            )
                except Exception:
                    pass
                else:
                    return saved
        if (
            existing is not None
            and existing.data.get("publication_prepared") is True
            and existing.outputs
        ):
            try:
                for path in existing.outputs:
                    actual = read_json_object(
                        self.artifacts.canonical_path(path, must_exist=True)
                    )
                    saved = existing.data.get("structured_output")
                    if not isinstance(saved, dict):
                        raise WorkflowError("prepared task has no structured output")
                    if actual != _structured_json_projection(saved, path):
                        raise WorkflowError(f"prepared JSON output changed: {path}")
            except Exception:
                pass
            else:
                saved = existing.data.get("structured_output")
                if isinstance(saved, dict):
                    self._finish_prepared_task(existing)
                    return saved

        task_dir = self._task_dir(task_id)
        atomic_write_json(task_dir / "context-manifest.json", context_manifest)
        base_attempt = existing.attempts + 1 if existing else 1
        rendered = self._render(
            stage, task_id, context_manifest, output_target, mode, base_attempt
        )
        session_id = (existing.session_id if existing else None) or self._recover_session(task_dir)
        task = self._mark_running(
            task_id=task_id,
            stage=stage,
            rendered=rendered,
            mode=mode,
            context_manifest=context_manifest,
            output_target=output_target,
            prior=existing,
            session_id=session_id,
        )
        last_error: Exception | None = None
        total_attempts = 0
        for format_attempt in range(self.settings.artifact_format_retries + 1):
            if format_attempt:
                rendered = self._render(
                    stage,
                    task_id,
                    context_manifest,
                    output_target,
                    mode,
                    base_attempt + format_attempt,
                )
            correction = ""
            if last_error is not None:
                correction = (
                    "\n\nThe previous JSON result failed controller validation. "
                    "Return a corrected JSON object only. Validation errors:\n"
                    f"- {last_error}\n"
                )
            result = await self._run_codex(
                stage=stage,
                task_id=task_id,
                rendered=rendered,
                output_schema=self.prompts.schema_path(schema_name),
                web_search=False,
                task_dir=task_dir,
                resume_session=session_id,
                extra_prompt=correction,
            )
            total_attempts += result.attempts
            self._append_task_event(task, result)
            if not result.success:
                message = result.error.message if result.error else "Codex task failed"
                self._mark_failed(task, message, total_attempts)
                raise TaskExecutionError(f"{stage} {task_id}: {message}")
            session_id = result.session_id
            task.session_id = session_id
            self._save_task(task)
            try:
                self._validate_structured_identity(result.structured_output, task_id)
                self._prepare_publication(
                    task,
                    result,
                    output_paths,
                    attempts=total_attempts,
                    structured_output=result.structured_output,
                )
                publish(result.structured_output)
            except Exception as exc:
                last_error = exc
                if format_attempt >= self.settings.artifact_format_retries:
                    self._mark_failed(
                        task,
                        f"invalid structured output: {exc}",
                        total_attempts,
                    )
                    raise TaskExecutionError(
                        f"{stage} produced invalid output: {exc}"
                    ) from exc
                continue
            self._mark_completed(
                task,
                result,
                output_paths,
                # Attempts were saved at the publication boundary so recovery
                # and the normal path account for them exactly once.
                attempts=total_attempts,
                structured_output=result.structured_output,
            )
            return result.structured_output
        raise AssertionError("unreachable structured execution loop")

    def _validate_structured_identity(
        self, output: Mapping[str, Any], task_id: str
    ) -> None:
        if output.get("schema_version") != 1:
            raise WorkflowError("structured output schema_version must be 1")
        if output.get("run_id") != self.state.run_id:
            raise WorkflowError("structured output run_id does not match this run")
        if output.get("task_id") != task_id:
            raise WorkflowError("structured output task_id does not match this task")

    async def _execute_artifact_task(
        self,
        *,
        stage: str,
        identity: Sequence[Any],
        mode: str,
        context_manifest: Mapping[str, Any],
        context_refs: Collection[str],
        copy_refs: Collection[str] | None = None,
        output_target: str,
        expected_exact: Collection[str] | None = None,
        expected_prefix: str | None = None,
        allow_empty: bool = False,
        web_search: bool = False,
        replace_living: Collection[str] = (),
    ) -> ArtifactTaskResult:
        task_id = stable_task_id(stage, self.state.run_id, *identity, mode)
        existing = self._task(task_id)
        if existing is not None and existing.status is TaskStatus.COMPLETED:
            prior_routing_raw = existing.data.get("routing_metadata", {})
            prior_hashes_raw = existing.data.get("output_hashes", {})
            try:
                if not isinstance(prior_routing_raw, dict):
                    raise WorkflowError("completed task has invalid routing metadata")
                if not isinstance(prior_hashes_raw, dict):
                    raise WorkflowError("completed task has invalid output hashes")
                prior_routing = cast(
                    dict[str, Mapping[str, Any]], prior_routing_raw
                )
                prior_hashes = cast(dict[str, str], prior_hashes_raw)
                for output in existing.outputs:
                    expected = prior_routing.get(output)
                    expected_sha256 = prior_hashes.get(output)
                    if not isinstance(expected, dict):
                        raise WorkflowError(
                            f"completed task has no routing metadata for {output}"
                        )
                    if not isinstance(expected_sha256, str):
                        raise WorkflowError(
                            f"completed task has no content hash for {output}"
                        )
                    self._validate_saved_output(
                        output, expected, expected_sha256
                    )
            except Exception:
                pass
            else:
                return ArtifactTaskResult(
                    task_id=task_id,
                    output_paths=tuple(existing.outputs),
                    routing_metadata=prior_routing,
                    session_id=existing.session_id or "unknown",
                    empty=bool(existing.data.get("empty", False)),
                )
        if (
            existing is not None
            and existing.data.get("publication_prepared") is True
            and existing.outputs
        ):
            prepared_routing_raw = existing.data.get("routing_metadata", {})
            prepared_hashes_raw = existing.data.get("output_hashes", {})
            try:
                if not isinstance(prepared_routing_raw, dict):
                    raise WorkflowError("prepared task has invalid routing metadata")
                if not isinstance(prepared_hashes_raw, dict):
                    raise WorkflowError("prepared task has invalid output hashes")
                prepared_routing = cast(
                    dict[str, Mapping[str, Any]], prepared_routing_raw
                )
                prepared_hashes = cast(dict[str, str], prepared_hashes_raw)
                for output in existing.outputs:
                    expected = prepared_routing.get(output)
                    expected_sha256 = prepared_hashes.get(output)
                    if not isinstance(expected, dict):
                        raise WorkflowError(
                            f"prepared task has no routing metadata for {output}"
                        )
                    if not isinstance(expected_sha256, str):
                        raise WorkflowError(
                            f"prepared task has no content hash for {output}"
                        )
                    self.artifacts.validate_canonical(
                        output,
                        expected_metadata=expected,
                    )
                    path = self.artifacts.canonical_path(output, must_exist=True)
                    if hashlib.sha256(path.read_bytes()).hexdigest() != expected_sha256:
                        raise WorkflowError(
                            f"prepared artifact content changed: {output}"
                        )
            except Exception:
                pass
            else:
                self._finish_prepared_task(existing)
                return ArtifactTaskResult(
                    task_id=task_id,
                    output_paths=tuple(existing.outputs),
                    routing_metadata=prepared_routing,
                    session_id=existing.session_id or "unknown",
                    empty=False,
                )

        task_dir = self._task_dir(task_id)
        manifest = dict(context_manifest)
        refs_to_copy = context_refs if copy_refs is None else copy_refs
        manifest["artifacts"] = self._copy_context_refs(task_dir, refs_to_copy)
        atomic_write_json(task_dir / "context-manifest.json", manifest)
        base_attempt = existing.attempts + 1 if existing else 1
        rendered = self._render(
            stage, task_id, manifest, output_target, mode, base_attempt
        )
        session_id = (existing.session_id if existing else None) or self._recover_session(task_dir)
        task = self._mark_running(
            task_id=task_id,
            stage=stage,
            rendered=rendered,
            mode=mode,
            context_manifest=manifest,
            output_target=output_target,
            prior=existing,
            session_id=session_id,
        )

        last_error: Exception | None = None
        total_attempts = 0
        for format_attempt in range(self.settings.artifact_format_retries + 1):
            if format_attempt:
                rendered = self._render(
                    stage,
                    task_id,
                    manifest,
                    output_target,
                    mode,
                    base_attempt + format_attempt,
                )
            correction = ""
            if last_error is not None:
                correction = (
                    "\n\nThe previous staged result failed deterministic validation. "
                    "Correct only the assigned artifact(s) and return the completion "
                    f"envelope again. Validation errors:\n- {last_error}\n"
                )
            result = await self._run_codex(
                stage=stage,
                task_id=task_id,
                rendered=rendered,
                output_schema=self.prompts.schema_path("completion"),
                web_search=web_search,
                task_dir=task_dir,
                resume_session=session_id,
                extra_prompt=correction,
            )
            total_attempts += result.attempts
            self._append_task_event(task, result)
            if not result.success:
                message = result.error.message if result.error else "Codex task failed"
                self._mark_failed(task, message, total_attempts)
                raise TaskExecutionError(f"{stage} {task_id}: {message}")
            session_id = result.session_id
            task.session_id = session_id
            self._save_task(task)
            try:
                output_paths, empty = self._validate_completion_envelope(
                    result.structured_output,
                    task_id,
                    expected_exact=expected_exact,
                    expected_prefix=expected_prefix,
                    allow_empty=allow_empty,
                )
                routing_metadata: dict[str, Mapping[str, Any]] = {}
                published_hashes: dict[str, str] = {}
                requests: list[PromotionRequest] = []
                for output in output_paths:
                    staged = task_dir / Path(*PurePosixPath(output).parts)
                    document = self.artifacts.stamp_session(staged, session_id or "unknown")
                    routing_metadata[output] = _json_data(dict(document.metadata))
                    published_hashes[output] = hashlib.sha256(
                        staged.read_bytes()
                    ).hexdigest()
                    expected_metadata = self._expected_artifact_metadata(
                        stage=stage,
                        manifest=manifest,
                        session_id=session_id or "unknown",
                    )
                    requests.append(
                        PromotionRequest(
                            staged_path=staged,
                            canonical_path=output,
                            allowed_source_refs=context_refs,
                            expected_metadata=expected_metadata,
                            replace_living=output in replace_living,
                        )
                    )
                if requests:
                    self._prepare_publication(
                        task,
                        result,
                        output_paths,
                        attempts=total_attempts,
                        routing_metadata=routing_metadata,
                        output_hashes=published_hashes,
                        structured_output=result.structured_output,
                    )
                    self.artifacts.promote_many(requests)
            except Exception as exc:
                last_error = exc
                if format_attempt >= self.settings.artifact_format_retries:
                    self._mark_failed(
                        task,
                        f"artifact validation failed: {exc}",
                        total_attempts,
                    )
                    raise TaskExecutionError(
                        f"{stage} artifact validation failed: {exc}"
                    ) from exc
                continue

            task.data["empty"] = empty
            self._mark_completed(
                task,
                result,
                output_paths,
                attempts=total_attempts,
                routing_metadata=routing_metadata,
                structured_output=result.structured_output,
            )
            return ArtifactTaskResult(
                task_id=task_id,
                output_paths=tuple(output_paths),
                routing_metadata=routing_metadata,
                session_id=session_id or "unknown",
                empty=empty,
            )
        raise AssertionError("unreachable artifact execution loop")

    def _expected_artifact_metadata(
        self,
        *,
        stage: str,
        manifest: Mapping[str, Any],
        session_id: str,
    ) -> dict[str, Any]:
        artifact_types = {
            "S2": "research",
            "S3": "verification",
            "S4": "problem",
            "S5": "problem_gateway",
            "S6": "idea",
            "S7": "competition",
            "S8": "idea",
            "S9": "idea_red_team",
            "S10": "feasibility",
        }
        routing = manifest.get("routing", {})
        if not isinstance(routing, Mapping):
            raise WorkflowError("context manifest routing must be an object")
        expected: dict[str, Any] = {
            "schema_version": 1,
            "artifact_type": artifact_types[stage],
            "run_id": self.state.run_id,
            "stage": stage,
            "updated_by_session": session_id,
        }
        created = routing.get("original_created_by_session", session_id)
        expected["created_by_session"] = created
        for key in (
            "artifact_id",
            "audience_id",
            "researcher_id",
            "research_round",
            "research_ref",
            "verifier_id",
            "verification_round",
            "recheck_evidence_ids",
            "writer_id",
            "problem_id",
            "problem_ref",
            "gateway_id",
            "gateway_mode",
            "evidence_loop_count",
            "generator_id",
            "idea_id",
            "revision_reason",
            "idea_ref",
            "red_team_id",
            "review_mode",
            "review_id",
            "revision",
            "supersedes",
            "source_refs",
        ):
            if key in routing:
                expected[key] = routing[key]
        if "supersedes" not in expected:
            expected["supersedes"] = None
        return expected

    def _validate_completion_envelope(
        self,
        output: Mapping[str, Any],
        task_id: str,
        *,
        expected_exact: Collection[str] | None,
        expected_prefix: str | None,
        allow_empty: bool,
    ) -> tuple[list[str], bool]:
        self._validate_structured_identity(output, task_id)
        status = output.get("status")
        raw_paths = output.get("output_paths")
        if status not in {"completed", "empty"}:
            raise WorkflowError("completion status must be completed or empty")
        if not isinstance(raw_paths, list) or any(
            not isinstance(path, str) for path in raw_paths
        ):
            raise WorkflowError("output_paths must be a list of strings")
        paths = [
            safe_relative_path(path, field_name="completion output path").as_posix()
            for path in raw_paths
        ]
        if len(paths) != len(set(paths)):
            raise WorkflowError("completion output_paths contain duplicates")
        empty = status == "empty"
        if empty and (paths or not allow_empty):
            raise WorkflowError("this task does not permit an empty completion")
        if not empty and not paths:
            raise WorkflowError("completed artifact task must return at least one path")
        if expected_exact is not None and set(paths) != set(expected_exact):
            raise WorkflowError(
                f"completion paths {paths!r} do not match assigned paths "
                f"{sorted(expected_exact)!r}"
            )
        if expected_prefix is not None:
            prefix = safe_relative_path(expected_prefix, field_name="output prefix")
            for path in paths:
                candidate = PurePosixPath(path)
                if not candidate.is_relative_to(prefix) or candidate.suffix != ".md":
                    raise WorkflowError(
                        f"output {path!r} is outside assigned prefix {prefix.as_posix()!r}"
                    )
        return paths, empty

    async def _gather_partial(
        self,
        operations: Iterable[Awaitable[_T]],
        *,
        label: str,
    ) -> list[_T]:
        results = await asyncio.gather(*operations, return_exceptions=True)
        successful: list[_T] = []
        for result in results:
            if isinstance(result, BaseException):
                self._warn(f"{label} task failed: {result}")
            else:
                successful.append(result)
        return successful

    # Stage implementations are below. Keeping them on this concrete class
    # makes every transition and bounded loop visible in one auditable state machine.

    def _read_json_artifact(self, reference: str) -> dict[str, Any]:
        value = read_json_object(
            self.artifacts.canonical_path(reference, must_exist=True)
        )
        return _json_data(value)

    def _document(self, reference: str) -> ArtifactDocument:
        return self.artifacts.validate_canonical(reference)

    def _validate_saved_output(
        self,
        reference: str,
        expected_metadata: Mapping[str, Any],
        expected_sha256: str | None = None,
    ) -> ArtifactDocument:
        """Validate a task's exact output, even after a Living Document advanced."""

        return _validate_bound_artifact(
            self.artifacts,
            self.run_dir,
            self.state.run_id,
            reference,
            expected_metadata,
            expected_sha256,
        )

    @staticmethod
    def _source_refs(document: ArtifactDocument) -> tuple[str, ...]:
        value = document.metadata.get("source_refs", [])
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            raise WorkflowError("validated artifact has invalid source_refs")
        return tuple(value)

    async def _stage_s0(self) -> Mapping[str, Any]:
        self._set_stage("S0", "running")
        raw = self.artifacts.canonical_path("challenge.md", must_exist=True).read_text(
            encoding="utf-8"
        )
        context = {
            "inputs": [
                {
                    "artifact_type": "raw_challenge",
                    "canonical_ref": "challenge.md",
                    "content": raw,
                }
            ],
            "routing": {"source_ref": "challenge.md"},
        }

        def publish(output: Mapping[str, Any]) -> None:
            brief = output.get("challenge_brief")
            discovery = output.get("discovery_view")
            compliance = output.get("compliance_view")
            if not isinstance(brief, dict) or not isinstance(discovery, dict) or not isinstance(compliance, dict):
                raise WorkflowError("S0 must return brief and both views")
            if brief.get("source_ref") != "challenge.md":
                raise WorkflowError("S0 challenge source_ref must be challenge.md")
            atomic_write_json(self.run_dir / "brief.json", output)
            atomic_write_json(self.run_dir / "discovery-view.json", discovery)
            atomic_write_json(self.run_dir / "compliance-view.json", compliance)

        output = await self._execute_json_task(
            stage="S0",
            identity=("challenge.md",),
            mode="initial",
            context_manifest=context,
            output_target="brief.json",
            schema_name="s0",
            output_paths=("brief.json", "discovery-view.json", "compliance-view.json"),
            publish=publish,
        )
        input_language = output.get("input_language")
        if not isinstance(input_language, str) or not input_language.strip():
            raise WorkflowError("S0 did not return a usable input_language")

        def remember_language(state: RunState) -> None:
            state.data["input_language"] = input_language

        self.state = self.state_store.mutate(remember_language)
        self._set_stage("S0", "completed")
        return output

    async def _stage_s1(
        self, brief: Mapping[str, Any]
    ) -> list[dict[str, Any]]:
        self._set_stage("S1", "running")
        discovery = brief.get("discovery_view")
        if not isinstance(discovery, dict):
            raise WorkflowError("brief has no valid discovery_view")
        context = {
            "inputs": [
                {
                    "artifact_type": "discovery_view",
                    "canonical_ref": "discovery-view.json",
                    "content": discovery,
                }
            ],
            "routing": {"source_ref": "discovery-view.json"},
        }

        def publish(output: Mapping[str, Any]) -> None:
            if output.get("source_ref") != "discovery-view.json":
                raise WorkflowError("S1 source_ref must be discovery-view.json")
            audiences = output.get("audiences")
            if not isinstance(audiences, list):
                raise WorkflowError("S1 audiences must be a list")
            ids: list[str] = []
            for item in audiences:
                if not isinstance(item, dict):
                    raise WorkflowError("every S1 audience must be an object")
                audience_id = item.get("audience_id")
                if not isinstance(audience_id, str):
                    raise WorkflowError("every S1 audience needs audience_id")
                ids.append(_safe_id(audience_id, field="audience id"))
            if len(ids) != len(set(ids)):
                raise WorkflowError("S1 audience ids must be unique")
            atomic_write_json(self.run_dir / "audiences.json", output)

        output = await self._execute_json_task(
            stage="S1",
            identity=("discovery-view.json",),
            mode="initial",
            context_manifest=context,
            output_target="audiences.json",
            schema_name="s1",
            output_paths=("audiences.json",),
            publish=publish,
        )
        audiences = output.get("audiences", [])
        assert isinstance(audiences, list)
        self._set_stage("S1", "completed")
        return [dict(item) for item in audiences if isinstance(item, dict)]

    async def _run_research(
        self,
        *,
        discovery: Mapping[str, Any],
        audience: Mapping[str, Any],
        researcher_id: str,
        target: str,
        mode: str = "initial",
        evidence_gaps: Sequence[str] = (),
        prior_search_material: Sequence[Mapping[str, Any]] = (),
        identity_extra: Sequence[Any] = (),
    ) -> ArtifactTaskResult:
        audience_id = _safe_id(str(audience["audience_id"]), field="audience id")
        source_refs = ("discovery-view.json", "audiences.json")
        context = {
            "inputs": [
                {
                    "artifact_type": "discovery_view",
                    "canonical_ref": "discovery-view.json",
                    "content": discovery,
                },
                {
                    "artifact_type": "audience",
                    "canonical_ref": "audiences.json",
                    "content": audience,
                },
            ],
            "routing": {
                "artifact_id": stable_record_id(
                    "research", self.state.run_id, audience_id, researcher_id
                ),
                "audience_id": audience_id,
                "researcher_id": researcher_id,
                "research_round": 1 if mode == "initial" else 2,
                "source_refs": list(source_refs),
            },
            "search_budget": {"maximum_queries": self.settings.research_query_budget},
            "evidence_gaps": list(evidence_gaps),
            "prior_search_material": list(prior_search_material),
        }
        return await self._execute_artifact_task(
            stage="S2",
            identity=(audience_id, researcher_id, *identity_extra),
            mode=mode,
            context_manifest=context,
            context_refs=source_refs,
            copy_refs=(),
            output_target=target,
            expected_exact=(target,),
            web_search=True,
        )

    async def _run_verification(
        self,
        *,
        audience: Mapping[str, Any],
        research_ref: str,
        verifier_number: int,
        recheck_ids: Sequence[str] = (),
    ) -> ArtifactTaskResult:
        audience_id = _safe_id(str(audience["audience_id"]), field="audience id")
        research = self._document(research_ref)
        researcher_id = str(research.metadata["researcher_id"])
        verifier_id = f"verifier-{verifier_number:03d}"
        research_tail = PurePosixPath(research_ref).with_suffix("")
        target = (
            PurePosixPath("verification")
            / PurePosixPath(*research_tail.parts[1:])
            / f"{verifier_id}.md"
        ).as_posix()
        source_refs = (research_ref, "audiences.json")
        context = {
            "inputs": [
                {
                    "artifact_type": "audience",
                    "canonical_ref": "audiences.json",
                    "content": audience,
                }
            ],
            "routing": {
                "artifact_id": stable_record_id(
                    "verification",
                    self.state.run_id,
                    research_ref,
                    verifier_id,
                ),
                "audience_id": audience_id,
                "research_ref": research_ref,
                "researcher_id": researcher_id,
                "verifier_id": verifier_id,
                "verification_round": verifier_number,
                "recheck_evidence_ids": list(recheck_ids),
                "source_refs": list(source_refs),
            },
        }
        return await self._execute_artifact_task(
            stage="S3",
            identity=(research_ref, verifier_id),
            mode="initial" if verifier_number == 1 else "blind_recheck",
            context_manifest=context,
            context_refs=source_refs,
            copy_refs=(research_ref,),
            output_target=target,
            expected_exact=(target,),
            web_search=True,
        )

    async def _verify_research(
        self,
        audience: Mapping[str, Any],
        research_ref: str,
    ) -> list[str]:
        first = await self._run_verification(
            audience=audience,
            research_ref=research_ref,
            verifier_number=1,
        )
        refs = list(first.output_paths)
        metadata = first.metadata_for(refs[0])
        if metadata.get("needs_second_verifier") is True:
            recheck = metadata.get("recheck_evidence_ids", [])
            if not isinstance(recheck, list):
                raise WorkflowError("S3 recheck_evidence_ids must be a list")
            second = await self._run_verification(
                audience=audience,
                research_ref=research_ref,
                verifier_number=2,
                recheck_ids=[str(item) for item in recheck],
            )
            refs.extend(second.output_paths)
            self._record_transition(
                candidate_ref=research_ref,
                stage="S3",
                action="second-verifier",
                reason="The first verifier identified evidence claims requiring an independent recheck.",
                decision_refs=refs,
            )
        return refs

    async def _stage_s2_s3(
        self,
        brief: Mapping[str, Any],
        audiences: Sequence[Mapping[str, Any]],
    ) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
        discovery = brief.get("discovery_view")
        if not isinstance(discovery, dict):
            raise WorkflowError("brief has no valid discovery_view")
        self._set_stage("S2", "running")
        research: dict[str, list[str]] = {
            _safe_id(str(audience["audience_id"]), field="audience id"): []
            for audience in audiences
        }
        research_operations: list[Awaitable[ArtifactTaskResult]] = []
        for audience in audiences:
            audience_id = _safe_id(str(audience["audience_id"]), field="audience id")
            for index in range(1, self.settings.researchers_per_audience + 1):
                researcher_id = f"researcher-{index:03d}"
                target = f"research/{audience_id}/{researcher_id}.md"
                research_operations.append(
                    self._run_research(
                        discovery=discovery,
                        audience=audience,
                        researcher_id=researcher_id,
                        target=target,
                    )
                )
        research_results = await self._gather_partial(
            research_operations, label="S2"
        )
        for result in research_results:
            for path in result.output_paths:
                audience_id = str(result.metadata_for(path)["audience_id"])
                if audience_id not in research:
                    raise WorkflowError(
                        f"S2 output references an unknown Audience: {path}"
                    )
                research[audience_id].append(path)
        self._set_stage("S2", "completed")

        self._set_stage("S3", "running")
        verifications: dict[str, list[str]] = {}
        audience_by_id = {
            str(audience["audience_id"]): audience for audience in audiences
        }
        verification_operations = [
            self._verify_research(audience_by_id[audience_id], ref)
            for audience_id, refs in research.items()
            for ref in refs
        ]
        groups = await self._gather_partial(
            verification_operations, label="S3"
        )
        for group in groups:
            if not group:
                continue
            audience_id = str(self._document(group[0]).metadata["audience_id"])
            if audience_id not in verifications:
                verifications[audience_id] = []
            verifications[audience_id].extend(group)
        for audience_id in audience_by_id:
            verifications.setdefault(audience_id, [])
        self._set_stage("S3", "completed")
        return research, verifications

    async def _run_problem_writer(
        self,
        *,
        discovery: Mapping[str, Any],
        audience: Mapping[str, Any],
        writer_id: str,
        research_refs: Sequence[str],
        verification_refs: Sequence[str],
    ) -> ArtifactTaskResult:
        audience_id = _safe_id(str(audience["audience_id"]), field="audience id")
        prefix = f"problems/{audience_id}/{writer_id}"
        refs = tuple(
            ["discovery-view.json", "audiences.json"]
            + list(research_refs)
            + list(verification_refs)
        )
        context = {
            "inputs": [
                {
                    "artifact_type": "discovery_view",
                    "canonical_ref": "discovery-view.json",
                    "content": discovery,
                },
                {
                    "artifact_type": "audience",
                    "canonical_ref": "audiences.json",
                    "content": audience,
                },
            ],
            "routing": {
                "audience_id": audience_id,
                "writer_id": writer_id,
                "revision": 1,
                "path_pattern": f"{prefix}/problem-NNN.md",
                "source_refs": list(refs),
            },
        }
        return await self._execute_artifact_task(
            stage="S4",
            identity=(audience_id, writer_id, 1),
            mode="initial",
            context_manifest=context,
            context_refs=refs,
            copy_refs=tuple(
                [*research_refs, *verification_refs]
            ),
            output_target=prefix,
            expected_prefix=prefix,
            allow_empty=True,
        )

    async def _stage_s4(
        self,
        brief: Mapping[str, Any],
        audiences: Sequence[Mapping[str, Any]],
        research: Mapping[str, Sequence[str]],
        verifications: Mapping[str, Sequence[str]],
    ) -> list[str]:
        discovery = brief.get("discovery_view")
        if not isinstance(discovery, dict):
            raise WorkflowError("brief has no valid discovery_view")
        self._set_stage("S4", "running")
        operations = [
            self._run_problem_writer(
                discovery=discovery,
                audience=audience,
                writer_id=f"writer-{index:03d}",
                research_refs=research.get(str(audience["audience_id"]), ()),
                verification_refs=verifications.get(
                    str(audience["audience_id"]), ()
                ),
            )
            for audience in audiences
            for index in range(1, self.settings.problem_writers_per_audience + 1)
        ]
        results = await self._gather_partial(operations, label="S4")
        all_problems = [
            path for result in results for path in result.output_paths
        ]
        self._set_stage("S4", "completed")
        return sorted(dict.fromkeys(all_problems))

    async def _run_gateway(
        self,
        *,
        problem_ref: str,
        evidence_refs: Sequence[str],
        gateway_number: int,
        gateway_mode: str,
        evidence_loop_count: int,
    ) -> ArtifactTaskResult:
        problem = self._document(problem_ref)
        parts = PurePosixPath(problem_ref).with_suffix("").parts
        if len(parts) < 4:
            raise WorkflowError(f"unexpected Problem path: {problem_ref}")
        base = PurePosixPath("gateways", *parts[1:])
        gateway_id = f"gateway-{gateway_number:03d}"
        target = (base / f"{gateway_id}.md").as_posix()
        refs = tuple([problem_ref] + list(evidence_refs))
        context = {
            "routing": {
                "artifact_id": stable_record_id(
                    "gateway",
                    self.state.run_id,
                    problem_ref,
                    gateway_id,
                ),
                "problem_ref": problem_ref,
                "problem_revision": problem.revision,
                "gateway_id": gateway_id,
                "gateway_mode": gateway_mode,
                "evidence_loop_count": evidence_loop_count,
                "source_refs": list(refs),
            },
            "absolute_threshold": {
                "recurring_source_floor": 2,
                "severe_one_off_source_floor": 1,
                "no_ranking": True,
            },
        }
        return await self._execute_artifact_task(
            stage="S5",
            # Gateway number and mode identify the bounded decision slot. The
            # mutable Problem revision is input data, not task identity.
            identity=(problem_ref, gateway_id, gateway_mode),
            mode=gateway_mode,
            context_manifest=context,
            context_refs=refs,
            output_target=target,
            expected_exact=(target,),
        )

    def _record_elimination(
        self,
        *,
        candidate_ref: str,
        stage: str,
        rule: str,
        reason: str,
        decision_refs: Sequence[str],
    ) -> None:
        decision_id = stable_record_id(
            "elimination", candidate_ref, stage, rule, sorted(decision_refs)
        )
        record: dict[str, Any] = {
            "decision_id": decision_id,
            "type": "elimination",
            "candidate_ref": candidate_ref,
            "stage": stage,
            "rule": rule,
            "reason": reason.strip() or rule,
            "decision_refs": sorted(dict.fromkeys(decision_refs)),
        }
        self.state_store.append_decision(record)

        def mutate(state: RunState) -> None:
            eliminations = state.data.setdefault("eliminations", [])
            assert isinstance(eliminations, list)
            if not any(
                isinstance(item, dict) and item.get("decision_id") == decision_id
                for item in eliminations
            ):
                eliminations.append(record)

        self.state = self.state_store.mutate(mutate)

    def _record_transition(
        self,
        *,
        candidate_ref: str,
        stage: str,
        action: str,
        reason: str,
        decision_refs: Sequence[str],
    ) -> None:
        """Append one idempotent, content-addressed orchestration decision."""

        refs = sorted(dict.fromkeys(decision_refs))
        record = {
            "decision_id": stable_record_id(
                "decision", candidate_ref, stage, action, refs
            ),
            "type": "transition",
            "candidate_ref": candidate_ref,
            "stage": stage,
            "action": action,
            "reason": reason,
            "decision_refs": refs,
        }
        self.state_store.append_decision(record)

    def _research_search_material(
        self, refs: Sequence[str]
    ) -> list[dict[str, str]]:
        material: list[dict[str, str]] = []
        for ref in refs:
            document = self._document(ref)
            if document.metadata.get("artifact_type") != "research":
                continue
            material.append(
                {
                    "canonical_ref": ref,
                    "evidence_candidates": document.section("Evidence Candidates"),
                    "query_log": document.section("Query Log"),
                    "coverage_gaps": document.section("Coverage Gaps"),
                }
            )
        return material

    async def _targeted_problem_retry(
        self,
        *,
        brief: Mapping[str, Any],
        audience: Mapping[str, Any],
        problem_ref: str,
        research_refs: Sequence[str],
        verification_refs: Sequence[str],
        gaps: Sequence[str],
    ) -> tuple[str, list[str], list[str]]:
        discovery = brief.get("discovery_view")
        if not isinstance(discovery, dict):
            raise WorkflowError("brief has no valid discovery_view")
        audience_id = str(audience["audience_id"])
        token = stable_record_id("retry", problem_ref, length=12)
        researcher_id = f"researcher-{token}"
        research_target = f"research/{audience_id}/{researcher_id}.md"
        retry_research = await self._run_research(
            discovery=discovery,
            audience=audience,
            researcher_id=researcher_id,
            target=research_target,
            mode="targeted_evidence",
            evidence_gaps=gaps,
            prior_search_material=self._research_search_material(research_refs),
            identity_extra=(problem_ref,),
        )
        new_research = list(retry_research.output_paths)
        new_verifications: list[str] = []
        for ref in new_research:
            new_verifications.extend(await self._verify_research(audience, ref))

        current = self._document(problem_ref)
        revision = (current.revision or 1) + 1
        snapshot = self.artifacts.snapshot_relative_path(problem_ref, revision - 1)
        all_research = list(research_refs) + new_research
        all_verifications = list(verification_refs) + new_verifications
        context_refs = tuple(
            [problem_ref, "discovery-view.json", "audiences.json"]
            + all_research
            + all_verifications
        )
        prefix = PurePosixPath(problem_ref).parent.as_posix()
        context = {
            "inputs": [
                {
                    "artifact_type": "discovery_view",
                    "canonical_ref": "discovery-view.json",
                    "content": discovery,
                },
                {
                    "artifact_type": "audience",
                    "canonical_ref": "audiences.json",
                    "content": audience,
                },
            ],
            "routing": {
                "artifact_id": current.metadata["artifact_id"],
                "audience_id": current.metadata["audience_id"],
                "writer_id": current.metadata["writer_id"],
                "problem_id": current.metadata["problem_id"],
                "revision": revision,
                "assigned_paths": [problem_ref],
                "original_created_by_session": current.metadata["created_by_session"],
                "supersedes": snapshot,
                "source_refs": [
                    ref for ref in context_refs if ref != problem_ref
                ],
                "evidence_gaps": list(gaps),
            },
        }
        revised = await self._execute_artifact_task(
            stage="S4",
            # This is one bounded logical repair slot. Keeping the mutable
            # revision out prevents resume from creating another revision.
            identity=(problem_ref, "evidence_revision"),
            mode="evidence_revision",
            context_manifest=context,
            context_refs=context_refs,
            copy_refs=tuple(
                ref
                for ref in context_refs
                if ref not in {"discovery-view.json", "audiences.json"}
            ),
            output_target=prefix,
            expected_exact=(problem_ref,),
            replace_living=(problem_ref,),
        )
        if revised.output_paths != (problem_ref,):
            raise WorkflowError("S4 evidence revision did not preserve Problem path")
        return problem_ref, all_research, all_verifications

    async def _process_problem(
        self,
        *,
        brief: Mapping[str, Any],
        audience: Mapping[str, Any],
        problem_ref: str,
        research_refs: Sequence[str],
        verification_refs: Sequence[str],
    ) -> PassedProblem | None:
        current_research = list(research_refs)
        current_verifications = list(verification_refs)
        evidence_loop_count = 0
        gateway_number = 1
        decision_refs: list[str] = []

        while True:
            evidence_refs = current_research + current_verifications
            primary = await self._run_gateway(
                problem_ref=problem_ref,
                evidence_refs=evidence_refs,
                gateway_number=gateway_number,
                gateway_mode="initial" if evidence_loop_count == 0 else "post_evidence",
                evidence_loop_count=evidence_loop_count,
            )
            primary_ref = primary.output_paths[0]
            primary_meta = primary.metadata_for(primary_ref)
            decision_refs.append(primary_ref)
            status = primary_meta.get("status")
            if status == "pass":
                self._record_transition(
                    candidate_ref=problem_ref,
                    stage="S5",
                    action="pass-problem",
                    reason="The Problem met every absolute quality threshold.",
                    decision_refs=(primary_ref,),
                )
                return PassedProblem(
                    problem_ref=problem_ref,
                    gateway_ref=primary_ref,
                    evidence_refs=tuple(evidence_refs),
                )

            gaps = primary_meta.get("evidence_gaps", [])
            if not isinstance(gaps, list):
                gaps = []
            failed = primary_meta.get("failed_thresholds", [])
            if not isinstance(failed, list):
                failed = []

            if status == "reject_candidate":
                gateway_number += 1
                blind = await self._run_gateway(
                    problem_ref=problem_ref,
                    evidence_refs=evidence_refs,
                    gateway_number=gateway_number,
                    gateway_mode="blind_rejection_confirmation",
                    evidence_loop_count=evidence_loop_count,
                )
                blind_ref = blind.output_paths[0]
                blind_meta = blind.metadata_for(blind_ref)
                decision_refs.append(blind_ref)
                blind_failed = blind_meta.get("failed_thresholds", [])
                if not isinstance(blind_failed, list):
                    blind_failed = []
                shared_failures = sorted(set(failed) & set(blind_failed))
                if blind_meta.get("status") == "reject_candidate" and shared_failures:
                    self._record_elimination(
                        candidate_ref=problem_ref,
                        stage="S5",
                        rule=f"double-confirmed:{','.join(shared_failures)}",
                        reason="Two blind Gateways rejected the same required threshold.",
                        decision_refs=decision_refs,
                    )
                    return None
                blind_gaps = blind_meta.get("evidence_gaps", [])
                if isinstance(blind_gaps, list):
                    gaps = list(dict.fromkeys([*gaps, *blind_gaps]))
                if not gaps:
                    self._record_elimination(
                        candidate_ref=problem_ref,
                        stage="S5",
                        rule="unresolved-gateway-disagreement",
                        reason=(
                            "The independent Gateways disagreed but identified no "
                            "concrete searchable evidence gap for the bounded retry."
                        ),
                        decision_refs=decision_refs,
                    )
                    return None

            if evidence_loop_count >= 1:
                self._record_elimination(
                    candidate_ref=problem_ref,
                    stage="S5",
                    rule="evidence-loop-exhausted",
                    reason="The only evidence retry was used and the Problem still did not pass.",
                    decision_refs=decision_refs,
                )
                return None

            problem_ref, current_research, current_verifications = (
                # One bounded evidence loop is permitted for a concrete gap.
                await self._targeted_problem_retry(
                    brief=brief,
                    audience=audience,
                    problem_ref=problem_ref,
                    research_refs=current_research,
                    verification_refs=current_verifications,
                    gaps=[str(item) for item in gaps],
                )
            )
            self._record_transition(
                candidate_ref=problem_ref,
                stage="S5",
                action="targeted-evidence-retry",
                reason="A Gateway identified a concrete searchable evidence gap.",
                decision_refs=decision_refs,
            )
            evidence_loop_count = 1
            gateway_number += 1

    async def _stage_s5(
        self,
        brief: Mapping[str, Any],
        audiences: Sequence[Mapping[str, Any]],
        problems: Sequence[str],
        research: Mapping[str, Sequence[str]],
        verifications: Mapping[str, Sequence[str]],
    ) -> list[PassedProblem]:
        self._set_stage("S5", "running")
        audience_by_id = {
            str(audience["audience_id"]): audience for audience in audiences
        }
        operations: list[Awaitable[PassedProblem | None]] = []
        for problem_ref in problems:
            problem = self._document(problem_ref)
            audience_id = str(problem.metadata["audience_id"])
            operations.append(
                self._process_problem(
                    brief=brief,
                    audience=audience_by_id[audience_id],
                    problem_ref=problem_ref,
                    research_refs=research.get(audience_id, ()),
                    verification_refs=verifications.get(audience_id, ()),
                )
            )
        results = await self._gather_partial(operations, label="S5")
        passed = [result for result in results if result is not None]
        self._set_stage("S5", "completed")
        return passed

    async def _run_idea_generator(
        self,
        *,
        discovery: Mapping[str, Any],
        passed: PassedProblem,
        generator_id: str,
    ) -> ArtifactTaskResult:
        problem_tail = PurePosixPath(passed.problem_ref).with_suffix("")
        prefix = (
            PurePosixPath("ideas")
            / PurePosixPath(*problem_tail.parts[1:])
            / generator_id
        ).as_posix()
        refs = tuple(
            ["discovery-view.json", passed.problem_ref, passed.gateway_ref]
            + list(passed.evidence_refs)
        )
        context = {
            "inputs": [
                {
                    "artifact_type": "discovery_view",
                    "canonical_ref": "discovery-view.json",
                    "content": discovery,
                }
            ],
            "routing": {
                "problem_ref": passed.problem_ref,
                "generator_id": generator_id,
                "revision": 1,
                "path_pattern": f"{prefix}/idea-NNN.md",
                "source_refs": list(refs),
            },
        }
        return await self._execute_artifact_task(
            stage="S6",
            identity=(passed.problem_ref, generator_id),
            mode="initial",
            context_manifest=context,
            context_refs=refs,
            copy_refs=tuple(ref for ref in refs if ref != "discovery-view.json"),
            output_target=prefix,
            expected_prefix=prefix,
            allow_empty=True,
        )

    async def _stage_s6(
        self,
        brief: Mapping[str, Any],
        passed: Sequence[PassedProblem],
    ) -> list[str]:
        discovery = brief.get("discovery_view")
        if not isinstance(discovery, dict):
            raise WorkflowError("brief has no valid discovery_view")
        self._set_stage("S6", "running")
        operations = [
            self._run_idea_generator(
                discovery=discovery,
                passed=problem,
                generator_id=f"generator-{index:03d}",
            )
            for problem in passed
            for index in range(1, self.settings.idea_generators_per_problem + 1)
        ]
        results = await self._gather_partial(operations, label="S6")
        ideas = sorted(
            dict.fromkeys(path for result in results for path in result.output_paths)
        )
        self._set_stage("S6", "completed")
        return ideas

    @staticmethod
    def _idea_output_base(idea_ref: str, root: str) -> PurePosixPath:
        idea = PurePosixPath(idea_ref).with_suffix("")
        if not idea.parts or idea.parts[0] != "ideas":
            raise WorkflowError(f"unexpected Idea path: {idea_ref}")
        return PurePosixPath(root, *idea.parts[1:])

    async def _run_competition(
        self,
        *,
        idea_ref: str,
        passed: PassedProblem,
        researcher_number: int,
        gaps: Sequence[str] = (),
        prior_material: Sequence[Mapping[str, Any]] = (),
    ) -> ArtifactTaskResult:
        researcher_id = f"researcher-{researcher_number:03d}"
        target = (
            self._idea_output_base(idea_ref, "competition")
            / f"{researcher_id}.md"
        ).as_posix()
        refs = tuple(
            [idea_ref, passed.problem_ref, passed.gateway_ref]
            + list(passed.evidence_refs)
        )
        context = {
            "routing": {
                "artifact_id": stable_record_id(
                    "competition",
                    self.state.run_id,
                    idea_ref,
                    researcher_id,
                ),
                "idea_ref": idea_ref,
                "researcher_id": researcher_id,
                "research_round": researcher_number,
                "source_refs": list(refs),
            },
            "search_budget": {"maximum_queries": self.settings.competition_query_budget},
            "competition_gaps": list(gaps),
            "prior_search_material": list(prior_material),
        }
        return await self._execute_artifact_task(
            stage="S7",
            identity=(idea_ref, researcher_id, *gaps),
            mode="initial" if researcher_number == 1 else "targeted_gap",
            context_manifest=context,
            context_refs=refs,
            output_target=target,
            expected_exact=(target,),
            web_search=True,
        )

    def _competition_search_material(
        self, refs: Sequence[str]
    ) -> list[dict[str, str]]:
        material: list[dict[str, str]] = []
        for ref in refs:
            document = self._document(ref)
            material.append(
                {
                    "canonical_ref": ref,
                    "sources_and_queries": document.section("Sources and Query Log"),
                    "coverage_gaps": document.section(
                        "Counterevidence and Coverage Gaps"
                    ),
                }
            )
        return material

    async def _revise_idea(
        self,
        *,
        brief: Mapping[str, Any],
        idea_ref: str,
        passed: PassedProblem,
        competition_refs: Sequence[str],
        mode: str,
        trigger_ref: str | None = None,
    ) -> ArtifactTaskResult:
        current = self._document(idea_ref)
        revision = (current.revision or 1) + 1
        snapshot = self.artifacts.snapshot_relative_path(idea_ref, revision - 1)
        compliance = brief.get("compliance_view")
        if not isinstance(compliance, dict):
            raise WorkflowError("brief has no valid compliance_view")
        context_refs = [
            idea_ref,
            passed.problem_ref,
            passed.gateway_ref,
            *passed.evidence_refs,
            *competition_refs,
            "compliance-view.json",
        ]
        if trigger_ref is not None:
            context_refs.append(trigger_ref)
        source_refs = [ref for ref in context_refs if ref != idea_ref]
        context = {
            "inputs": [
                {
                    "artifact_type": "compliance_view",
                    "canonical_ref": "compliance-view.json",
                    "content": compliance,
                }
            ],
            "routing": {
                "artifact_id": current.metadata["artifact_id"],
                "idea_id": current.metadata["idea_id"],
                "problem_ref": passed.problem_ref,
                "generator_id": current.metadata["generator_id"],
                "revision_reason": mode,
                "revision": revision,
                "original_created_by_session": current.metadata[
                    "created_by_session"
                ],
                "supersedes": snapshot,
                "source_refs": source_refs,
                "trigger_ref": trigger_ref,
            },
        }
        return await self._execute_artifact_task(
            stage="S8",
            # Every repair mode has one bounded slot; revision is mutable input.
            identity=(idea_ref, mode, trigger_ref),
            mode=mode,
            context_manifest=context,
            context_refs=tuple(context_refs),
            copy_refs=tuple(
                ref for ref in context_refs if ref != "compliance-view.json"
            ),
            output_target=idea_ref,
            expected_exact=(idea_ref,),
            replace_living=(idea_ref,),
        )

    async def _run_red_team(
        self,
        *,
        idea_ref: str,
        passed: PassedProblem,
        competition_refs: Sequence[str],
        review_number: int,
        review_mode: str,
    ) -> ArtifactTaskResult:
        red_team_id = f"red-team-{review_number:03d}"
        target = (
            self._idea_output_base(idea_ref, "idea-reviews")
            / f"{red_team_id}.md"
        ).as_posix()
        refs = tuple(
            [idea_ref, passed.problem_ref, passed.gateway_ref]
            + list(passed.evidence_refs)
            + list(competition_refs)
        )
        context = {
            "routing": {
                "artifact_id": stable_record_id(
                    "red-team",
                    self.state.run_id,
                    idea_ref,
                    red_team_id,
                ),
                "idea_ref": idea_ref,
                "red_team_id": red_team_id,
                "review_mode": review_mode,
                "source_refs": list(refs),
            }
        }
        return await self._execute_artifact_task(
            stage="S9",
            identity=(idea_ref, red_team_id, review_mode),
            mode=review_mode,
            context_manifest=context,
            context_refs=refs,
            output_target=target,
            expected_exact=(target,),
        )

    async def _run_feasibility(
        self,
        *,
        brief: Mapping[str, Any],
        idea_ref: str,
        red_team_ref: str,
        review_number: int,
        review_mode: str,
    ) -> ArtifactTaskResult:
        review_id = f"review-{review_number:03d}"
        target = (
            self._idea_output_base(idea_ref, "feasibility")
            / f"{review_id}.md"
        ).as_posix()
        refs = (idea_ref, red_team_ref)
        compliance = brief.get("compliance_view", {})
        time_limit = compliance.get("time_limit") if isinstance(compliance, dict) else None
        context = {
            "routing": {
                "artifact_id": stable_record_id(
                    "feasibility",
                    self.state.run_id,
                    idea_ref,
                    review_id,
                ),
                "idea_ref": idea_ref,
                "review_id": review_id,
                "review_mode": review_mode,
                "source_refs": list(refs),
            },
            "build_constraints": {
                "challenge_time_limit": time_limit,
                "team_size": self.settings.team_size,
                "local_environment": self.settings.local_environment,
                "delivery_definition": (
                    "A repeatable path with real input, actual core processing, "
                    "and a usable result or real-world action."
                ),
            },
        }
        return await self._execute_artifact_task(
            stage="S10",
            identity=(idea_ref, review_id, review_mode),
            mode=review_mode,
            context_manifest=context,
            context_refs=refs,
            output_target=target,
            expected_exact=(target,),
        )

    async def _resolve_competitor_gap(
        self,
        *,
        brief: Mapping[str, Any],
        idea_ref: str,
        passed: PassedProblem,
        competition_refs: list[str],
        revision_result: ArtifactTaskResult,
        retry_used: bool,
    ) -> tuple[ArtifactTaskResult, bool]:
        metadata = revision_result.metadata_for(idea_ref)
        if metadata.get("needs_competitor_research") is not True:
            return revision_result, retry_used
        gaps = metadata.get("competitor_research_gaps", [])
        if not isinstance(gaps, list):
            gaps = []
        if retry_used:
            self._warn(
                f"S8 requested more competitor research after its only retry: {idea_ref}"
            )
            return revision_result, True
        targeted = await self._run_competition(
            idea_ref=idea_ref,
            passed=passed,
            researcher_number=2,
            gaps=[str(item) for item in gaps],
            prior_material=self._competition_search_material(competition_refs),
        )
        competition_refs.extend(targeted.output_paths)
        self._record_transition(
            candidate_ref=idea_ref,
            stage="S8",
            action="targeted-competitor-retry",
            reason="The first Idea revision identified a concrete competitor or adoption evidence gap.",
            decision_refs=tuple(competition_refs),
        )
        followup = await self._revise_idea(
            brief=brief,
            idea_ref=idea_ref,
            passed=passed,
            competition_refs=competition_refs,
            mode="competition_followup",
        )
        if followup.metadata_for(idea_ref).get("needs_competitor_research") is True:
            self._warn(
                f"S8 still reports a competitor gap after the bounded retry: {idea_ref}"
            )
        return followup, True

    def _review_reason(self, reference: str) -> str:
        try:
            return self._document(reference).section("Decision")
        except (KeyError, WorkflowError):
            return "The independent review did not pass the required gate."

    async def _process_idea(
        self,
        *,
        brief: Mapping[str, Any],
        idea_ref: str,
        passed: PassedProblem,
    ) -> FinalIdea | None:
        competition_first = await self._run_competition(
            idea_ref=idea_ref,
            passed=passed,
            researcher_number=1,
        )
        competition_refs = list(competition_first.output_paths)
        revision = await self._revise_idea(
            brief=brief,
            idea_ref=idea_ref,
            passed=passed,
            competition_refs=competition_refs,
            mode="competition_revision",
        )
        revision, competition_retry_used = await self._resolve_competitor_gap(
            brief=brief,
            idea_ref=idea_ref,
            passed=passed,
            competition_refs=competition_refs,
            revision_result=revision,
            retry_used=False,
        )

        red_number = 1
        red = await self._run_red_team(
            idea_ref=idea_ref,
            passed=passed,
            competition_refs=competition_refs,
            review_number=red_number,
            review_mode="initial",
        )
        red_ref = red.output_paths[0]
        red_status = red.metadata_for(red_ref).get("status")
        if red_status == "invalid":
            self._record_elimination(
                candidate_ref=idea_ref,
                stage="S9",
                rule="product-invalid",
                reason=self._review_reason(red_ref),
                decision_refs=(red_ref,),
            )
            return None
        if red_status == "repairable":
            self._record_transition(
                candidate_ref=idea_ref,
                stage="S9",
                action="product-repair",
                reason="The independent Red Team found one bounded, repairable product defect.",
                decision_refs=(red_ref,),
            )
            repaired = await self._revise_idea(
                brief=brief,
                idea_ref=idea_ref,
                passed=passed,
                competition_refs=competition_refs,
                mode="product_repair",
                trigger_ref=red_ref,
            )
            repaired, competition_retry_used = await self._resolve_competitor_gap(
                brief=brief,
                idea_ref=idea_ref,
                passed=passed,
                competition_refs=competition_refs,
                revision_result=repaired,
                retry_used=competition_retry_used,
            )
            red_number += 1
            red = await self._run_red_team(
                idea_ref=idea_ref,
                passed=passed,
                competition_refs=competition_refs,
                review_number=red_number,
                review_mode="product_recheck",
            )
            red_ref = red.output_paths[0]
            if red.metadata_for(red_ref).get("status") != "pass":
                self._record_elimination(
                    candidate_ref=idea_ref,
                    stage="S9",
                    rule="product-repair-exhausted",
                    reason=self._review_reason(red_ref),
                    decision_refs=(red_ref,),
                )
                return None
        elif red_status != "pass":
            raise WorkflowError(f"unexpected S9 status: {red_status!r}")

        feasibility_number = 1
        feasibility = await self._run_feasibility(
            brief=brief,
            idea_ref=idea_ref,
            red_team_ref=red_ref,
            review_number=feasibility_number,
            review_mode="initial",
        )
        feasibility_ref = feasibility.output_paths[0]
        feasibility_status = feasibility.metadata_for(feasibility_ref).get("status")
        if feasibility_status == "infeasible":
            self._record_elimination(
                candidate_ref=idea_ref,
                stage="S10",
                rule="build-infeasible",
                reason=self._review_reason(feasibility_ref),
                decision_refs=(feasibility_ref,),
            )
            return None
        if feasibility_status == "scope_reduction":
            self._record_transition(
                candidate_ref=idea_ref,
                stage="S10",
                action="scope-reduction",
                reason="The feasibility review found a bounded reduction that preserves the complete User Flow.",
                decision_refs=(feasibility_ref,),
            )
            reduced = await self._revise_idea(
                brief=brief,
                idea_ref=idea_ref,
                passed=passed,
                competition_refs=competition_refs,
                mode="scope_reduction",
                trigger_ref=feasibility_ref,
            )
            reduced, competition_retry_used = await self._resolve_competitor_gap(
                brief=brief,
                idea_ref=idea_ref,
                passed=passed,
                competition_refs=competition_refs,
                revision_result=reduced,
                retry_used=competition_retry_used,
            )
            red_number += 1
            red = await self._run_red_team(
                idea_ref=idea_ref,
                passed=passed,
                competition_refs=competition_refs,
                review_number=red_number,
                review_mode="scope_recheck",
            )
            red_ref = red.output_paths[0]
            if red.metadata_for(red_ref).get("status") != "pass":
                self._record_elimination(
                    candidate_ref=idea_ref,
                    stage="S9",
                    rule="scope-reduction-red-team-failed",
                    reason=self._review_reason(red_ref),
                    decision_refs=(red_ref, feasibility_ref),
                )
                return None
            feasibility_number += 1
            feasibility = await self._run_feasibility(
                brief=brief,
                idea_ref=idea_ref,
                red_team_ref=red_ref,
                review_number=feasibility_number,
                review_mode="scope_recheck",
            )
            feasibility_ref = feasibility.output_paths[0]
            if feasibility.metadata_for(feasibility_ref).get("status") != "feasible":
                self._record_elimination(
                    candidate_ref=idea_ref,
                    stage="S10",
                    rule="scope-reduction-exhausted",
                    reason=self._review_reason(feasibility_ref),
                    decision_refs=(feasibility_ref,),
                )
                return None
        elif feasibility_status != "feasible":
            raise WorkflowError(f"unexpected S10 status: {feasibility_status!r}")

        self._record_transition(
            candidate_ref=idea_ref,
            stage="S10",
            action="accept-idea",
            reason="The Idea passed the independent product and build-feasibility gates.",
            decision_refs=(red_ref, feasibility_ref),
        )
        return FinalIdea(
            idea_ref=idea_ref,
            problem_ref=passed.problem_ref,
            gateway_ref=passed.gateway_ref,
            evidence_refs=passed.evidence_refs,
            competition_refs=tuple(competition_refs),
            red_team_ref=red_ref,
            feasibility_ref=feasibility_ref,
        )

    async def _stage_s7_s10(
        self,
        brief: Mapping[str, Any],
        ideas: Sequence[str],
        passed: Sequence[PassedProblem],
    ) -> list[FinalIdea]:
        self._set_stage("S7", "running")
        by_problem = {problem.problem_ref: problem for problem in passed}
        operations: list[Awaitable[FinalIdea | None]] = []
        for idea_ref in ideas:
            idea = self._document(idea_ref)
            problem_ref = str(idea.metadata["problem_ref"])
            problem = by_problem.get(problem_ref)
            if problem is None:
                self._warn(f"S6 Idea references an unknown passed Problem: {idea_ref}")
                continue
            operations.append(
                self._process_idea(brief=brief, idea_ref=idea_ref, passed=problem)
            )
        results = await self._gather_partial(operations, label="S7-S10")
        finals = [result for result in results if result is not None]
        for stage in ("S7", "S8", "S9", "S10"):
            self._set_stage(stage, "completed")

        def mutate(state: RunState) -> None:
            state.data["final_ideas"] = [asdict(item) for item in finals]

        self.state = self.state_store.mutate(mutate)
        return finals

    def _stage_s11(
        self,
        brief: Mapping[str, Any],
        finals: Sequence[FinalIdea],
    ) -> Path:
        self._set_stage("S11", "running")
        report_ideas: list[ReportIdea] = []
        for final in finals:
            idea = self._document(final.idea_ref)
            red_team = self._document(final.red_team_ref)
            feasibility = self._document(final.feasibility_ref)
            if idea.metadata.get("stage") != "S8":
                raise WorkflowError(f"final Idea is not an S8 revision: {final.idea_ref}")
            if "compliance-view.json" not in self._source_refs(idea):
                raise WorkflowError(
                    f"final Idea never read ComplianceView: {final.idea_ref}"
                )
            if idea.metadata.get("problem_ref") != final.problem_ref:
                raise WorkflowError(
                    f"final Idea changed its passed Problem: {final.idea_ref}"
                )
            if red_team.status != "pass" or red_team.metadata.get("idea_ref") != final.idea_ref:
                raise WorkflowError(
                    f"final Idea has no matching passed S9 review: {final.idea_ref}"
                )
            if feasibility.status != "feasible":
                raise WorkflowError(
                    f"final Idea has no feasible S10 decision: {final.idea_ref}"
                )
            if feasibility.metadata.get("idea_ref") != final.idea_ref:
                raise WorkflowError(
                    f"final Feasibility review targets another Idea: {final.idea_ref}"
                )
            if final.red_team_ref not in self._source_refs(feasibility):
                raise WorkflowError(
                    f"final Feasibility review did not use the passed S9 review: {final.idea_ref}"
                )
            report_ideas.append(
                ReportIdea(
                    artifact_id=str(idea.metadata["artifact_id"]),
                    idea_ref=final.idea_ref,
                    target_user=idea.section("Target User"),
                    problem=idea.section("Problem"),
                    felt_value=idea.section("Felt Value"),
                    user_flow=idea.section("User Flow"),
                    core_mechanism=idea.section("Core Mechanism"),
                    minimum_features=idea.section("Minimum Features"),
                    alternatives_and_adoption=idea.section(
                        "Alternatives and Adoption"
                    ),
                    sponsor_technology=idea.section("Sponsor Technology"),
                    beta_scope=feasibility.section("Deliverable Beta Scope"),
                    highest_risk_dependencies=feasibility.section(
                        "Highest-Risk Dependencies"
                    ),
                    evidence_refs=tuple(
                        sorted(
                            dict.fromkeys(
                                [
                                    final.problem_ref,
                                    final.gateway_ref,
                                    *final.evidence_refs,
                                    *final.competition_refs,
                                ]
                            )
                        )
                    ),
                    review_refs=(final.red_team_ref, final.feasibility_ref),
                )
            )

        state = self.state_store.load()
        raw_eliminations = state.data.get("eliminations", [])
        eliminations: list[EliminationSummary] = []
        if isinstance(raw_eliminations, list):
            for item in raw_eliminations:
                if not isinstance(item, dict):
                    continue
                raw_decision_refs = item.get("decision_refs", [])
                if not isinstance(raw_decision_refs, list):
                    raw_decision_refs = []
                eliminations.append(
                    EliminationSummary(
                        candidate_ref=str(item.get("candidate_ref", "unknown")),
                        stage=str(item.get("stage", "unknown")),
                        rule=str(item.get("rule", "unknown")),
                        reason=str(item.get("reason", "")),
                        decision_refs=tuple(
                            str(ref) for ref in raw_decision_refs
                        ),
                    )
                )
        challenge = brief.get("challenge_brief", {})
        title = "Untitled challenge"
        if isinstance(challenge, dict):
            title = str(
                challenge.get("title")
                or challenge.get("summary")
                or title
            )
        statuses = state.data.get("stage_statuses", {})
        if not isinstance(statuses, dict):
            statuses = {}
        stage_statuses = {str(key): str(value) for key, value in statuses.items()}
        stage_statuses["S11"] = "completed"
        warnings = state.data.get("warnings", [])
        if not isinstance(warnings, list):
            warnings = []
        report_path = self.artifacts.canonical_path("idea-report.md")
        completed_at_value = state.data.get("completed_at")
        completed_at = (
            completed_at_value
            if isinstance(completed_at_value, str) and completed_at_value.strip()
            else utc_now()
        )
        write_report(
            report_path,
            ReportInput(
                run_id=state.run_id,
                challenge_title=str(title),
                challenge_ref="challenge.md",
                started_at=str(state.data.get("created_at", "unknown")),
                completed_at=completed_at,
                stage_statuses=stage_statuses,
                ideas=tuple(report_ideas),
                eliminations=tuple(eliminations),
                warnings=tuple(str(item) for item in warnings),
            ),
        )

        def mutate(completed: RunState) -> None:
            if "idea-report.md" not in completed.completed_artifacts:
                completed.completed_artifacts.append("idea-report.md")
            completed.data["completed_at"] = completed_at
            completed.data["report_sha256"] = _sha256_file(report_path)

        self.state = self.state_store.mutate(mutate)
        self._set_stage("S11", "completed")
        return report_path


def inspect_run(run_dir: str | Path) -> dict[str, Any]:
    root = Path(run_dir).expanduser().resolve()
    state = StateStore(root).load()
    statuses: dict[str, int] = {}
    for task in state.tasks.values():
        task_status = TaskStatus(task.status).value
        statuses[task_status] = statuses.get(task_status, 0) + 1
    final_ideas = state.data.get("final_ideas", [])
    eliminations = state.data.get("eliminations", [])
    return {
        "run_id": state.run_id,
        "status": RunStatus(state.status).value,
        "current_stage": state.current_stage,
        "task_counts": statuses,
        "completed_artifacts": state.completed_artifacts,
        "next_actions": state.next_actions,
        "warnings": state.data.get("warnings", []),
        "final_idea_count": len(final_ideas) if isinstance(final_ideas, list) else 0,
        "elimination_count": len(eliminations) if isinstance(eliminations, list) else 0,
    }


def validate_run(run_dir: str | Path) -> list[str]:
    root = Path(run_dir).expanduser().resolve()
    state_store = StateStore(root)
    state = state_store.load()
    artifact_store = ArtifactStore(root, run_id=state.run_id)
    errors: list[str] = []
    challenge_hash = state.data.get("challenge_sha256")
    try:
        challenge_path = artifact_store.canonical_path(
            "challenge.md", must_exist=True
        )
        if not isinstance(challenge_hash, str):
            raise WorkflowError("run state has no raw challenge integrity binding")
        if _sha256_file(challenge_path) != challenge_hash:
            raise WorkflowError("raw challenge content changed after run creation")
    except Exception as exc:
        errors.append(f"invalid challenge.md: {exc}")
    for ledger_name, reader in (
        ("events.jsonl", state_store.events),
        ("decisions.jsonl", state_store.decisions),
    ):
        try:
            reader()
        except Exception as exc:
            errors.append(f"invalid {ledger_name}: {exc}")
    for task_id, task in sorted(state.tasks.items()):
        if task.status is not TaskStatus.COMPLETED:
            continue
        if not task.outputs and not task.allow_empty_outputs:
            errors.append(f"{task_id}: completed task has no output")
            continue
        routing = task.data.get("routing_metadata", {})
        output_hashes = task.data.get("output_hashes", {})
        for output in task.outputs:
            path = artifact_store.canonical_path(output)
            if not path.is_file():
                errors.append(f"{task_id}: missing {output}")
                continue
            if path.suffix.lower() == ".md" and output != "challenge.md":
                try:
                    if not isinstance(routing, dict):
                        raise WorkflowError("task routing_metadata must be an object")
                    expected = routing.get(output)
                    expected_sha256 = (
                        output_hashes.get(output)
                        if isinstance(output_hashes, dict)
                        else None
                    )
                    if not isinstance(expected, dict):
                        raise WorkflowError(
                            "task has no saved metadata binding for this output"
                        )
                    if not isinstance(expected_sha256, str):
                        raise WorkflowError(
                            "task has no saved content hash for this output"
                        )
                    _validate_bound_artifact(
                        artifact_store,
                        root,
                        state.run_id,
                        output,
                        expected,
                        expected_sha256,
                    )
                except Exception as exc:
                    errors.append(f"{task_id}: invalid {output}: {exc}")
            elif path.suffix.lower() == ".json":
                try:
                    actual = read_json_object(path)
                    saved = task.data.get("structured_output")
                    if not isinstance(saved, dict):
                        raise WorkflowError(
                            "task has no saved structured output binding"
                        )
                    if actual != _structured_json_projection(saved, output):
                        raise WorkflowError(
                            "JSON content does not match its completed task"
                        )
                except Exception as exc:
                    errors.append(f"{task_id}: invalid JSON {output}: {exc}")
    if state.status is RunStatus.COMPLETED:
        report_hash = state.data.get("report_sha256")
        try:
            report_path = artifact_store.canonical_path(
                "idea-report.md", must_exist=True
            )
            if not isinstance(report_hash, str):
                raise WorkflowError("run state has no final report integrity binding")
            if _sha256_file(report_path) != report_hash:
                raise WorkflowError("final report content changed after rendering")
        except Exception as exc:
            errors.append(f"invalid idea-report.md: {exc}")
    return errors


__all__ = [
    "ArtifactTaskResult",
    "FinalIdea",
    "PassedProblem",
    "TaskExecutionError",
    "UsefulIdeaWorkflow",
    "WorkflowError",
    "WorkflowSettings",
    "create_run_id",
    "inspect_run",
    "validate_run",
]
