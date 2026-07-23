#!/usr/bin/env python3
"""Deterministic Company-level outbound email used only by Company Hub.

The caller supplies an already-bound Company and actor identity.  This module
then verifies that the requested from-address belongs to that Company in the
global registry, reserves quota in the Company's private mail ledger, and
sends through Resend.  No Agent receiver/owner concept exists.

Quota is based on reservations in a rolling 24-hour window: 30 per Company
and 15 per address by default.  A failed provider attempt still consumes its
slot.  The Hub method request id is both the durable reservation id and the
Resend idempotency key.  Consequently, a retry after a process crash can
re-enter safely without issuing a logically distinct send.

This module intentionally has no sending CLI.  Department and Worker runtimes
must use ``send_company_email`` through Company Hub; they never receive the
global registry or Company mail store as raw mounts.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from email.utils import parseaddr
from pathlib import Path

from orchestration import mailbox
from orchestration.runtime_store import append_jsonl, file_lock, require_identifier


DEFAULT_COMPANY_DAILY = 30
DEFAULT_PER_ADDRESS_DAILY = 15
WINDOW = timedelta(hours=24)
RESEND_ENDPOINT = "https://api.resend.com/emails"
HTTP_TIMEOUT_SECS = 30
_REQUEST_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


class EmailSendError(RuntimeError):
    """Base class for controlled outbound-email failures."""


class EmailValidationError(EmailSendError):
    pass


class EmailIdentityError(EmailSendError):
    pass


class EmailQuotaError(EmailSendError):
    pass


class EmailStoreError(EmailSendError):
    pass


class EmailProviderError(EmailSendError):
    pass


def ledger_path(company_mail_root: Path) -> Path:
    return Path(company_mail_root) / "send_ledger.jsonl"


def _limit(env_name: str, default: int) -> int:
    raw = os.environ.get(env_name, "")
    try:
        return int(raw) if raw else default
    except ValueError:
        print(
            f"[email-send] WARNING: {env_name}={raw!r} is not an integer — "
            f"using {default}",
            file=sys.stderr,
            flush=True,
        )
        return default


def _now() -> datetime:
    return datetime.now(timezone.utc)


def read_ledger(company_mail_root: Path) -> list[dict]:
    path = ledger_path(company_mail_root)
    if not path.is_file():
        return []
    rows: list[dict] = []
    try:
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise EmailStoreError(f"send ledger row {line_number} is not an object")
            rows.append(row)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise EmailStoreError(f"send ledger unreadable: {exc}") from exc
    return rows


def _append_ledger(
    company_mail_root: Path,
    *,
    event: str,
    reservation_id: str,
    sender: str,
    to: str,
    by: str,
    detail: dict,
    now: datetime,
) -> dict:
    row = {
        "ts": now.isoformat(),
        "event": event,
        "id": reservation_id,
        "from": sender,
        "to": to,
        "by": by,
        "detail": detail,
    }
    try:
        append_jsonl(ledger_path(company_mail_root), row)
    except OSError as exc:
        raise EmailStoreError(f"send ledger append failed: {exc}") from exc
    return row


def _reserves_in_window(
    events: list[dict], now: datetime
) -> list[tuple[datetime, dict]]:
    cutoff = now - WINDOW
    rows: list[tuple[datetime, dict]] = []
    for event in events:
        if event.get("event") != "reserve":
            continue
        try:
            timestamp = datetime.fromisoformat(event["ts"])
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
        except (KeyError, TypeError, ValueError):
            # Malformed quota evidence must over-count, never under-count.
            timestamp = now
        if timestamp > cutoff:
            rows.append((timestamp, event))
    return rows


def _quota_reject(
    window: list[tuple[datetime, dict]],
    sender: str,
    company_limit: int,
    address_limit: int,
) -> str | None:
    if company_limit <= 0:
        return "EMAIL_SEND_DAILY_COMPANY disables outbound email"
    if address_limit <= 0:
        return "EMAIL_SEND_DAILY_PER_ADDRESS disables outbound email"

    def frees(entries: list[tuple[datetime, dict]]) -> str:
        return (min(timestamp for timestamp, _ in entries) + WINDOW).isoformat(
            timespec="seconds"
        )

    if len(window) >= company_limit:
        return (
            f"Company outbound quota reached ({len(window)}/{company_limit}); "
            f"earliest capacity returns at {frees(window)}; failed sends are not refunded"
        )
    address_rows = [
        (timestamp, event)
        for timestamp, event in window
        if event.get("from") == sender
    ]
    if len(address_rows) >= address_limit:
        return (
            f"Address outbound quota reached for {sender} "
            f"({len(address_rows)}/{address_limit}); earliest capacity returns at "
            f"{frees(address_rows)}; failed sends are not refunded"
        )
    return None


def _post_resend(payload: dict, idempotency_key: str) -> tuple[bool, str]:
    """The sole network boundary; returns provider id or verbatim failure."""

    api_key = os.environ.get("RESEND_API_KEY", "")
    if not api_key:
        return False, "RESEND_API_KEY is not set; reservation consumed, nothing sent"
    request = urllib.request.Request(
        RESEND_ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Idempotency-Key": idempotency_key,
            "User-Agent": "foundagent-email-send/2.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECS) as response:
            body = response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        with contextlib.suppress(OSError):
            return False, exc.read().decode("utf-8", "replace") or str(exc)
        return False, str(exc)
    except (urllib.error.URLError, OSError) as exc:
        return False, f"network error: {exc}"
    try:
        provider_id = json.loads(body).get("id", "")
    except (json.JSONDecodeError, AttributeError):
        provider_id = ""
    return True, provider_id or body


def _from_header(localpart: str, from_name: str | None) -> str:
    display = (from_name or localpart).replace('"', "'").strip() or localpart
    return f'"{display}" <{localpart}@{mailbox.mail_domain()}>'


def _validate_request(
    *,
    company: str,
    by: str,
    request_id: str,
    sender: str,
    to: str,
    subject: str,
    text: str,
    html: str | None,
    from_name: str | None,
) -> tuple[str, str, str, str, str | None, str | None]:
    try:
        require_identifier(company, label="company id")
        require_identifier(by, label="actor id")
    except (TypeError, ValueError) as exc:
        raise EmailValidationError(str(exc)) from exc
    if not isinstance(request_id, str) or not _REQUEST_ID.fullmatch(request_id):
        raise EmailValidationError("request_id has an invalid format")
    if not isinstance(sender, str):
        raise EmailValidationError("from must be a mailbox localpart")
    sender = sender.strip().lower()
    normalized, errors = mailbox.validate_name(sender)
    if errors or normalized != sender:
        raise EmailValidationError(f"invalid from localpart {sender!r}")
    if not isinstance(to, str) or "\r" in to or "\n" in to:
        raise EmailValidationError("to must be one email address")
    to = to.strip()
    parsed_to = parseaddr(to)[1]
    if not parsed_to or "@" not in parsed_to or len(parsed_to) > 320:
        raise EmailValidationError(f"invalid recipient address: {to!r}")
    if not isinstance(subject, str) or not subject.strip():
        raise EmailValidationError("subject must be non-empty text")
    if "\r" in subject or "\n" in subject:
        raise EmailValidationError("subject must not contain newlines")
    if not isinstance(text, str) or not text.strip():
        raise EmailValidationError("text must be non-empty text")
    if html is not None and not isinstance(html, str):
        raise EmailValidationError("html must be text or null")
    if from_name is not None and not isinstance(from_name, str):
        raise EmailValidationError("from_name must be text or null")
    if from_name is not None and ("\r" in from_name or "\n" in from_name):
        raise EmailValidationError("from_name must not contain newlines")
    if from_name is not None and len(from_name) > 200:
        raise EmailValidationError("from_name is too long")
    return sender, parsed_to, subject.strip(), text, html, from_name


def _fingerprint(
    *,
    company: str,
    by: str,
    sender: str,
    to: str,
    subject: str,
    text: str,
    html: str | None,
    from_name: str | None,
) -> str:
    canonical = json.dumps(
        {
            "company": company,
            "by": by,
            "from": sender,
            "to": to,
            "subject": subject,
            "text": text,
            "html": html,
            "from_name": from_name,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _prior_result(
    events: list[dict], reservation_id: str, fingerprint: str
) -> tuple[str, str | None] | None:
    matching = [event for event in events if event.get("id") == reservation_id]
    if not matching:
        return None
    reserve = next((event for event in matching if event.get("event") == "reserve"), None)
    if reserve is None:
        raise EmailStoreError("send ledger has completion without reservation")
    detail = reserve.get("detail")
    if not isinstance(detail, dict) or detail.get("fingerprint") != fingerprint:
        if not isinstance(detail, dict):
            raise EmailStoreError("send reservation detail is malformed")
        raise EmailValidationError("request_id was already used for a different email")
    completion = next(
        (
            event
            for event in reversed(matching)
            if event.get("event") in ("sent", "failed")
        ),
        None,
    )
    if completion is None:
        return ("reserved", None)
    completion_detail = completion.get("detail") or {}
    if not isinstance(completion_detail, dict):
        raise EmailStoreError("send completion detail is malformed")
    if completion["event"] == "sent":
        return ("sent", completion_detail.get("resend_id"))
    return ("failed", completion_detail.get("error") or "provider send failed")


def send_company_email(
    *,
    company: str,
    global_mail_root: Path,
    company_mail_root: Path,
    by: str,
    request_id: str,
    sender: str,
    to: str,
    subject: str,
    text: str,
    html: str | None = None,
    from_name: str | None = None,
) -> dict:
    """Validate, reserve, and send one idempotent Company email."""

    sender, to, subject, text, html, from_name = _validate_request(
        company=company,
        by=by,
        request_id=request_id,
        sender=sender,
        to=to,
        subject=subject,
        text=text,
        html=html,
        from_name=from_name,
    )
    try:
        owned = mailbox.company_owns(company, sender, root=Path(global_mail_root))
    except Exception as exc:  # noqa: BLE001 - registry failures always fail closed
        raise EmailStoreError(f"global mailbox registry unreadable: {exc}") from exc
    address = f"{sender}@{mailbox.mail_domain()}"
    if not owned:
        raise EmailIdentityError(f"{address} is not owned by Company {company}")

    fingerprint = _fingerprint(
        company=company,
        by=by,
        sender=sender,
        to=to,
        subject=subject,
        text=text,
        html=html,
        from_name=from_name,
    )
    company_mail_root = Path(company_mail_root)
    lock_path = company_mail_root / ".send.lock"
    replayed = False

    with file_lock(lock_path):
        events = read_ledger(company_mail_root)
        prior = _prior_result(events, request_id, fingerprint)
        if prior and prior[0] == "sent":
            return {
                "sent": True,
                "replayed": True,
                "reservation_id": request_id,
                "provider_id": prior[1],
                "from": address,
                "to": to,
                "subject": subject,
            }
        if prior and prior[0] == "failed":
            raise EmailProviderError(
                f"prior attempt failed and its quota is not refunded: {prior[1]}"
            )
        if prior is not None:
            replayed = True
        else:
            now = _now()
            window = _reserves_in_window(events, now)
            rejection = _quota_reject(
                window,
                sender,
                _limit("EMAIL_SEND_DAILY_COMPANY", DEFAULT_COMPANY_DAILY),
                _limit("EMAIL_SEND_DAILY_PER_ADDRESS", DEFAULT_PER_ADDRESS_DAILY),
            )
            if rejection:
                raise EmailQuotaError(rejection)
            _append_ledger(
                company_mail_root,
                event="reserve",
                reservation_id=request_id,
                sender=sender,
                to=to,
                by=by,
                detail={"subject": subject, "fingerprint": fingerprint},
                now=now,
            )

    payload = {
        "from": _from_header(sender, from_name),
        "to": [to],
        "subject": subject,
        "text": text,
    }
    if html is not None:
        payload["html"] = html
    ok, provider_detail = _post_resend(payload, request_id)

    try:
        with file_lock(lock_path):
            events = read_ledger(company_mail_root)
            prior = _prior_result(events, request_id, fingerprint)
            if prior and prior[0] == "sent":
                ok, provider_detail = True, prior[1] or provider_detail
            elif prior and prior[0] == "failed":
                ok, provider_detail = False, prior[1] or provider_detail
            else:
                _append_ledger(
                    company_mail_root,
                    event="sent" if ok else "failed",
                    reservation_id=request_id,
                    sender=sender,
                    to=to,
                    by=by,
                    detail=(
                        {"resend_id": provider_detail}
                        if ok
                        else {"error": provider_detail}
                    ),
                    now=_now(),
                )
    except EmailStoreError:
        # If Resend succeeded but audit backfill failed, report failure so the
        # caller retries with the same provider idempotency key.
        raise

    if not ok:
        raise EmailProviderError(
            f"send failed; reservation is not refunded; provider response: {provider_detail}"
        )
    return {
        "sent": True,
        "replayed": replayed,
        "reservation_id": request_id,
        "provider_id": provider_detail,
        "from": address,
        "to": to,
        "subject": subject,
    }


def main() -> int:
    print(
        "Direct email sending is disabled; use Company Hub method "
        "send_company_email from a Department or Worker.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
