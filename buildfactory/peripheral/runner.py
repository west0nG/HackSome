#!/usr/bin/env python3
"""Foundagent peripheral layer — runner (design §1/§4).

The resident peripheral container's job: take native signals from external
sources, run each through its source-specific adapter into a 5-field IME, and
deliver it to the Company Hub. Adding a new source = a new adapter module + one
line in `manifest.ADAPTERS` — ZERO change here (the seam; AC2).

`ingest(source, native, inbox)` is the testable core. `main()` runs a tiny HTTP
listener so the outside world can POST events (a real push path; stdlib only).
Live pollers for compatible sources can post through this Hub-bound path.
Inbound email is deliberately separate: the singleton mail-router writes the
Company mail journal and Company Hub tick projects a notification to CEO.
"""

from __future__ import annotations

import importlib
import hashlib
import json
import os
from typing import Protocol

from orchestration.control_client import BoundActor, HubClient
from orchestration.inbox import CEO_KEY
from peripheral.manifest import ADAPTERS

_REGISTRY: dict | None = None


def _registry() -> dict:
    """source-name → adapter module, built once from the fixed manifest."""
    global _REGISTRY
    if _REGISTRY is None:
        reg = {}
        for name in ADAPTERS:
            mod = importlib.import_module(f"peripheral.adapters.{name}")
            reg[mod.SOURCE] = mod
        _REGISTRY = reg
    return _REGISTRY


class InboxSink(Protocol):
    def append(self, key: str, event: dict) -> None: ...


class HubInboxSink:
    """Peripheral projection into Hub; no raw Inbox mount is required."""

    def __init__(self, client: HubClient | None = None):
        self.client = client or HubClient(actor=BoundActor("manager", "peripheral"))

    def append(self, key: str, event: dict) -> None:
        target = event.get("to") or CEO_KEY
        if key != target:
            raise ValueError("external event routing key disagrees with IME target")
        source_id = str(event.get("id"))
        request_id = "external-event-" + hashlib.sha256(
            source_id.encode("utf-8")
        ).hexdigest()[:24]
        self.client.call(
            "deliver_external_event",
            {
                "to": target,
                "text": event.get("text", ""),
                "body": event.get("body"),
                "message_id": event.get("id"),
                "time": event.get("time"),
            },
            request_id=request_id,
        )


def ingest(source: str, native: dict, inbox: InboxSink) -> dict:
    """Normalize one native signal from `source` into an IME and deliver it to the
    addressee's inbox. Returns the IME. Routes by `ime['to']` (None → CEO); never
    inspects text/body."""
    reg = _registry()
    if source not in reg:
        raise KeyError(f"no adapter for source {source!r}; "
                       f"add it to peripheral.manifest.ADAPTERS")
    ime = reg[source].to_ime(native)
    inbox.append(ime["to"] or CEO_KEY, ime)
    return ime


def main() -> None:
    """Resident HTTP listener: POST /ingest/<source> with a JSON body → ingest().
    A real 'external world pushes in' path, stdlib only."""
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    inbox: InboxSink = HubInboxSink()
    sources = set(_registry())

    class Handler(BaseHTTPRequestHandler):
        def _reply(self, code: int, body: bytes = b"") -> None:
            # always send Content-Length so the client finishes immediately
            # (no waiting for connection close).
            self.send_response(code)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if body:
                self.wfile.write(body)

        def do_POST(self):
            parts = self.path.strip("/").split("/")
            if len(parts) != 2 or parts[0] != "ingest" or parts[1] not in sources:
                self._reply(404)
                return
            n = int(self.headers.get("Content-Length", 0))
            try:
                native = json.loads(self.rfile.read(n) or b"{}")
                ime = ingest(parts[1], native, inbox)
            except Exception as e:  # noqa: BLE001 — return the error to the caller
                self._reply(400, str(e).encode())
                return
            self._reply(200, ime["id"].encode())

        def log_message(self, *_a):  # quiet
            pass

    port = int(os.environ.get("PERIPHERAL_PORT", "8900"))
    print(f"[peripheral] listening :{port} sources={sorted(sources)}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
