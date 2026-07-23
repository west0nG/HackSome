"""Operator-only Docker log snapshots for resident V7 Agent containers."""

from __future__ import annotations

import re
import subprocess
import time
from pathlib import Path
from typing import Callable

from orchestration.runtime_store import atomic_write_json, atomic_write_text


_CONTAINER_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_RESIDENT_KINDS = {"ceo", "department"}


class ResidentLogSnapshotter:
    """Copy retained Docker stdout/stderr outside every LLM runtime.

    The provisioner already owns the Docker control socket, so this helper
    runs there. It never mounts telemetry into an Agent container and never
    injects log content into a prompt.
    """

    def __init__(
        self,
        root: str | Path,
        *,
        company_id: str,
        run_command: Callable[[list[str]], subprocess.CompletedProcess],
    ):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.company_id = company_id
        self.run_command = run_command

    def _containers(self) -> list[tuple[str, str]]:
        result = self.run_command(
            [
                "docker",
                "ps",
                "-a",
                "--filter",
                f"label=foundagent.company={self.company_id}",
                "--format",
                '{{.Names}}\t{{.Label "foundagent.kind"}}',
            ]
        )
        if result.returncode != 0:
            raise RuntimeError(f"docker ps failed: {result.stderr.strip()}")
        rows: list[tuple[str, str]] = []
        for line in result.stdout.splitlines():
            name, separator, kind = line.partition("\t")
            if (
                separator
                and _CONTAINER_NAME.fullmatch(name)
                and kind in _RESIDENT_KINDS
            ):
                rows.append((name, kind))
        return sorted(rows)

    def snapshot_once(self) -> int:
        captured = 0
        for name, kind in self._containers():
            result = self.run_command(
                ["docker", "logs", "--timestamps", name]
            )
            metadata = {
                "container_name": name,
                "kind": kind,
                "captured_at": time.time(),
                "ok": result.returncode == 0,
                "error": None if result.returncode == 0 else result.stderr.strip(),
            }
            atomic_write_json(self.root / f"{name}.json", metadata)
            if result.returncode != 0:
                continue
            # Snapshot the complete Docker-retained streams atomically. A
            # later poll replaces the prior snapshot, avoiding duplicate
            # lines after service or collector restarts.
            atomic_write_text(self.root / f"{name}.stdout.log", result.stdout or "")
            atomic_write_text(self.root / f"{name}.stderr.log", result.stderr or "")
            captured += 1
        return captured
