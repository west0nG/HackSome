"""Configuration for the concrete local Codex runtime."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


SandboxMode = Literal["read-only", "workspace-write", "danger-full-access"]
ApprovalPolicy = Literal["untrusted", "on-failure", "on-request", "never"]


@dataclass(frozen=True, slots=True)
class CodexConfig:
    """Runtime defaults shared by all Codex tasks.

    The defaults deliberately describe the v0.1 local execution boundary. They
    keep Codex inside the task workspace, prevent interactive approval prompts,
    and suppress ambient configuration that could make two stage sessions see
    different tools or instructions.
    """

    executable: str = "codex"
    max_concurrency: int = 4
    default_timeout_seconds: float = 20 * 60
    infrastructure_retries: int = 1
    termination_grace_seconds: float = 5.0
    doctor_timeout_seconds: float = 10.0
    subprocess_stream_limit_bytes: int = 1024 * 1024
    sandbox: SandboxMode = "workspace-write"
    approval_policy: ApprovalPolicy = "never"
    model: str | None = None
    ignore_user_config: bool = True
    ignore_rules: bool = True
    skip_git_repo_check: bool = True
    strict_config: bool = True
    disabled_features: tuple[str, ...] = (
        "hooks",
        "apps",
        "goals",
        "multi_agent",
        "multi_agent_v2",
        "enable_fanout",
        "enable_mcp_apps",
        "plugins",
        "plugin_sharing",
        "browser_use",
        "browser_use_external",
        "browser_use_full_cdp_access",
        "computer_use",
        "image_generation",
        "in_app_browser",
    )
    config_overrides: tuple[str, ...] = (
        "project_doc_max_bytes=0",
        "skills.include_instructions=false",
    )

    def __post_init__(self) -> None:
        if not isinstance(self.executable, str) or not self.executable.strip():
            raise ValueError("Codex executable must not be empty")
        if (
            isinstance(self.max_concurrency, bool)
            or not isinstance(self.max_concurrency, int)
            or self.max_concurrency < 1
        ):
            raise ValueError("max_concurrency must be at least 1")
        if (
            isinstance(self.default_timeout_seconds, bool)
            or not isinstance(self.default_timeout_seconds, (int, float))
            or self.default_timeout_seconds <= 0
        ):
            raise ValueError("default_timeout_seconds must be positive")
        if (
            isinstance(self.infrastructure_retries, bool)
            or not isinstance(self.infrastructure_retries, int)
            or self.infrastructure_retries < 0
        ):
            raise ValueError("infrastructure_retries must be a non-negative integer")
        if (
            isinstance(self.termination_grace_seconds, bool)
            or not isinstance(self.termination_grace_seconds, (int, float))
            or self.termination_grace_seconds < 0
        ):
            raise ValueError("termination_grace_seconds must not be negative")
        if (
            isinstance(self.doctor_timeout_seconds, bool)
            or not isinstance(self.doctor_timeout_seconds, (int, float))
            or self.doctor_timeout_seconds <= 0
        ):
            raise ValueError("doctor_timeout_seconds must be positive")
        if (
            isinstance(self.subprocess_stream_limit_bytes, bool)
            or not isinstance(self.subprocess_stream_limit_bytes, int)
            or self.subprocess_stream_limit_bytes < 64 * 1024
        ):
            raise ValueError(
                "subprocess_stream_limit_bytes must be at least 65536 bytes"
            )
        if self.sandbox not in {"read-only", "workspace-write", "danger-full-access"}:
            raise ValueError(f"unsupported sandbox mode: {self.sandbox!r}")
        if self.approval_policy not in {
            "untrusted",
            "on-failure",
            "on-request",
            "never",
        }:
            raise ValueError(
                f"unsupported approval policy: {self.approval_policy!r}"
            )
        if self.model is not None and (
            not isinstance(self.model, str) or not self.model.strip()
        ):
            raise ValueError("model must be omitted or non-empty")
        for name, values in (
            ("disabled_features", self.disabled_features),
            ("config_overrides", self.config_overrides),
        ):
            if not isinstance(values, tuple) or any(
                not isinstance(value, str) or not value.strip() for value in values
            ):
                raise ValueError(f"{name} must be a tuple of non-empty strings")
