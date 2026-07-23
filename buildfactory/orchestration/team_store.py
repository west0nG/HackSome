"""Filesystem contract for one autonomous Hackathon Team.

Only ``project/`` is mounted into model runtimes. Every other directory is
control-plane state and is reachable only through deterministic Hub methods.
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path

from orchestration.runtime_store import StoreError, atomic_write_text


CONTROL_DOMAINS = (
    "ledger",
    "inbox",
    "workers",
    "reviews",
    "control",
    "sessions",
    "telemetry",
)


def _validated_markdown(value: str, *, label: str) -> str:
    if not isinstance(value, str):
        raise StoreError(f"{label} must be text")
    if "\x00" in value:
        raise StoreError(f"{label} contains a NUL byte")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise StoreError(f"{label} is not valid UTF-8 text") from exc
    return value


@dataclass(frozen=True)
class TeamLayout:
    """Persistent state layout for one Team."""

    root: Path

    @classmethod
    def initialize(cls, root: str | os.PathLike) -> "TeamLayout":
        layout = cls(Path(root).resolve())
        layout.root.mkdir(parents=True, exist_ok=True)
        layout.project.mkdir(parents=True, exist_ok=True)
        for domain in CONTROL_DOMAINS:
            (layout.root / domain).mkdir(parents=True, exist_ok=True)
        for path in (
            layout.workers / "commands",
            layout.reviews / "commands",
            layout.reviews / "homes",
            layout.control / "requests",
            layout.telemetry / "index",
            layout.telemetry / "runs",
            layout.telemetry / "services",
        ):
            path.mkdir(parents=True, exist_ok=True)
        return layout

    @classmethod
    def bootstrap(
        cls,
        root: str | os.PathLike,
        *,
        challenge_markdown: str,
        initial_idea_card_markdown: str,
    ) -> "TeamLayout":
        """Initialize the exact two reference files for a new Team.

        Existing project content is never overwritten. This keeps bootstrap
        retry-safe without treating the initializer as immutable thereafter.
        """

        layout = cls.initialize(root)
        references = layout.project / "reference"
        references.mkdir(parents=True, exist_ok=True)
        values = {
            references / "challenge.md": _validated_markdown(
                challenge_markdown, label="challenge_markdown"
            ),
            references / "initial-idea-card.md": _validated_markdown(
                initial_idea_card_markdown, label="initial_idea_card_markdown"
            ),
        }
        conflicts = [str(path) for path in values if path.exists()]
        if conflicts:
            raise StoreError(f"Team references already exist: {conflicts}")
        for path, value in values.items():
            atomic_write_text(path, value)
        return layout

    @property
    def project(self) -> Path:
        return self.root / "project"

    @property
    def ledger(self) -> Path:
        return self.root / "ledger"

    @property
    def inbox(self) -> Path:
        return self.root / "inbox"

    @property
    def workers(self) -> Path:
        return self.root / "workers"

    @property
    def reviews(self) -> Path:
        return self.root / "reviews"

    @property
    def control(self) -> Path:
        return self.root / "control"

    @property
    def sessions(self) -> Path:
        return self.root / "sessions"

    @property
    def telemetry(self) -> Path:
        return self.root / "telemetry"

    def project_mount(self, *, read_only: bool = False) -> dict[str, str]:
        return {
            "source": str(self.project),
            "target": "/project",
            "mode": "ro" if read_only else "rw",
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize one Hackathon Team")
    parser.add_argument("--root", required=True)
    parser.add_argument("--challenge-file", required=True)
    parser.add_argument("--idea-card-file", required=True)
    args = parser.parse_args()
    TeamLayout.bootstrap(
        args.root,
        challenge_markdown=Path(args.challenge_file).read_text(encoding="utf-8"),
        initial_idea_card_markdown=Path(args.idea_card_file).read_text(encoding="utf-8"),
    )


if __name__ == "__main__":
    main()
