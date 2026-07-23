#!/usr/bin/env python3
"""Webhook adapter (design §4): a generic inbound HTTP event → IME. This is the
SECOND source — added with ZERO core change (AC2): just this file + one line in
`manifest.ADAPTERS`. A webhook may target a specific agent via native `to`."""

from __future__ import annotations

import json

from orchestration.inbox import make_ime

SOURCE = "webhook"


def to_ime(native: dict) -> dict:
    event = native.get("event", "webhook")
    text = f"Webhook: {event}"[:120]
    body = native.get("summary") or json.dumps(native, ensure_ascii=False)
    return make_ime(to=native.get("to"), text=text, body=body, id=native.get("id"))
