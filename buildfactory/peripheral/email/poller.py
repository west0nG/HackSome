#!/usr/bin/env python3
"""Platform mail router: R2 inbound spool -> one Company's private journal.

The Cloudflare Email Worker remains deliberately dumb: it writes raw MIME and
the envelope sender/recipient to R2.  This singleton service owns domain-wide
routing.  It resolves the envelope localpart through the permanent global
``localpart -> company`` registry, normalizes the message, and appends it to
``state/<company>/mailboxes/messages.jsonl``.

There is no Agent/Department fan-out and no HTTP content delivery.  Company
Hub is the only runtime API over the private journal.  A blob moves to
``processed/`` only after the journal append succeeds; unclaimed addresses
move to ``unmatched/``.  Journal IDs derive from the R2 source key, so a crash
after append but before archive is safe to retry without duplicating mail.

Live environment:
    R2_ENDPOINT, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY  required R2 access
    R2_BUCKET                                           default foundagent-mail
    MAIL_GLOBAL_ROOT                                    default /mail-global
    COMPANIES_STATE_ROOT                                default /companies-state
    MAIL_POLL_INTERVAL                                  default 30 seconds
"""

from __future__ import annotations

import email
import email.policy
import os
import re
import sys
import time
from dataclasses import dataclass, field
from email.utils import parseaddr
from pathlib import Path
from typing import Callable

from orchestration.mailbox import (
    CompanyMailStore,
    mail_domain,
    resolve_company,
    stable_mail_id,
)


PENDING_PREFIX = "inbox/"
PROCESSED_PREFIX = "processed/"
UNMATCHED_PREFIX = "unmatched/"

DEFAULT_BUCKET = "foundagent-mail"
DEFAULT_GLOBAL_ROOT = Path("/mail-global")
DEFAULT_COMPANIES_ROOT = Path("/companies-state")
DEFAULT_POLL_INTERVAL = 30.0

_LINK_RE = re.compile(r"https?://[^\s<>\"']+")
_LINK_TRAILING = ".,;:!?)]}"


@dataclass
class MailBlob:
    """One raw message waiting in the provider spool."""

    key: str
    raw_bytes: bytes
    metadata: dict = field(default_factory=dict)
    received_at: float | None = None


class MailBackend:
    """Provider seam used by the routing loop."""

    def fetch_batch(self) -> list[MailBlob]:
        raise NotImplementedError

    def archive_processed(self, key: str) -> None:
        raise NotImplementedError

    def archive_unmatched(self, key: str) -> None:
        raise NotImplementedError


class R2Backend(MailBackend):
    """Cloudflare R2 implementation over its S3-compatible API."""

    def __init__(
        self,
        endpoint: str,
        access_key_id: str,
        secret_access_key: str,
        bucket: str = DEFAULT_BUCKET,
        batch_size: int = 50,
    ):
        import boto3  # lazy: unit tests and Hub do not need this dependency

        self._s3 = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name="auto",
        )
        self.bucket = bucket
        self._batch_size = batch_size

    def fetch_batch(self) -> list[MailBlob]:
        response = self._s3.list_objects_v2(
            Bucket=self.bucket,
            Prefix=PENDING_PREFIX,
            MaxKeys=self._batch_size,
        )
        blobs: list[MailBlob] = []
        for item in response.get("Contents", []):
            got = self._s3.get_object(Bucket=self.bucket, Key=item["Key"])
            last_modified = item.get("LastModified")
            blobs.append(
                MailBlob(
                    key=item["Key"],
                    raw_bytes=got["Body"].read(),
                    metadata=dict(got.get("Metadata") or {}),
                    received_at=(
                        float(last_modified.timestamp())
                        if hasattr(last_modified, "timestamp")
                        else None
                    ),
                )
            )
        return blobs

    def _move(self, key: str, prefix: str) -> None:
        destination = prefix + key.split("/", 1)[-1]
        self._s3.copy_object(
            Bucket=self.bucket,
            Key=destination,
            CopySource={"Bucket": self.bucket, "Key": key},
        )
        self._s3.delete_object(Bucket=self.bucket, Key=key)

    def archive_processed(self, key: str) -> None:
        self._move(key, PROCESSED_PREFIX)

    def archive_unmatched(self, key: str) -> None:
        self._move(key, UNMATCHED_PREFIX)


class MockBackend(MailBackend):
    """In-memory provider used by unit tests."""

    def __init__(self, blobs: list[MailBlob] | None = None):
        self.pending: dict[str, MailBlob] = {blob.key: blob for blob in (blobs or [])}
        self.processed: list[str] = []
        self.unmatched: list[str] = []

    def add(
        self,
        key: str,
        raw_bytes: bytes,
        metadata: dict | None = None,
        *,
        received_at: float | None = None,
    ) -> None:
        self.pending[key] = MailBlob(
            key=key,
            raw_bytes=raw_bytes,
            metadata=dict(metadata or {}),
            received_at=received_at,
        )

    def fetch_batch(self) -> list[MailBlob]:
        return list(self.pending.values())

    def archive_processed(self, key: str) -> None:
        del self.pending[key]
        self.processed.append(key)

    def archive_unmatched(self, key: str) -> None:
        del self.pending[key]
        self.unmatched.append(key)


def _body_text(message) -> str:
    """Prefer text/plain, then HTML so HTML-only verification links survive."""

    try:
        part = message.get_body(preferencelist=("plain", "html"))
        if part is not None:
            return part.get_content()
    except Exception:  # noqa: BLE001 - malformed external data must not stop a batch
        pass
    payload = message.get_payload(decode=True)
    if isinstance(payload, (bytes, bytearray)):
        return bytes(payload).decode("utf-8", "replace")
    return str(payload or "") if not message.is_multipart() else ""


def parse_mail(raw_bytes: bytes) -> dict:
    """Parse provider MIME into the provider-independent message fields."""

    message = email.message_from_bytes(raw_bytes, policy=email.policy.default)
    raw_from = str(message.get("From", "") or "")
    sender = parseaddr(raw_from)[1] or raw_from
    body = _body_text(message)
    links = list(
        dict.fromkeys(url.rstrip(_LINK_TRAILING) for url in _LINK_RE.findall(body))
    )
    provider_id = message.get("Message-ID")
    return {
        "from": sender,
        "subject": str(message.get("Subject", "") or ""),
        "text": body,
        "links": links,
        "message_id": str(provider_id).strip() if provider_id else None,
    }


def _envelope_address(envelope_to: str) -> str:
    parsed = parseaddr(envelope_to or "")[1] or (envelope_to or "")
    return parsed.strip().lower()


def _localpart(envelope_to: str) -> str:
    """Extract the case-normalized routing key from SMTP RCPT TO metadata."""

    return _envelope_address(envelope_to).split("@", 1)[0].strip()


def _routable_address(envelope_to: str) -> tuple[str, str] | None:
    """Return ``(address, localpart)`` only for the configured mail domain."""

    address = _envelope_address(envelope_to)
    if address.count("@") != 1:
        return None
    localpart, domain = address.rsplit("@", 1)
    if not localpart or domain != mail_domain().strip().lower():
        return None
    return address, localpart


def _handle_blob(
    backend: MailBackend,
    blob: MailBlob,
    *,
    registry_root: Path,
    companies_root: Path,
    received_at: float,
) -> str:
    """Route one blob and return ``processed``, ``unmatched``, or ``deferred``."""

    routed = _routable_address(blob.metadata.get("to", ""))
    if routed is None:
        backend.archive_unmatched(blob.key)
        return "unmatched"
    envelope_address, localpart = routed
    try:
        company = resolve_company(localpart, root=registry_root)
    except Exception as exc:  # noqa: BLE001 - never classify registry failure as unclaimed
        print(
            f"[mail-router] WARN: registry unreadable resolving {localpart!r} "
            f"({exc!r}) — {blob.key} stays queued",
            flush=True,
        )
        return "deferred"

    if company is None:
        backend.archive_unmatched(blob.key)
        return "unmatched"

    parsed = parse_mail(blob.raw_bytes)
    message = {
        **parsed,
        "id": stable_mail_id(blob.key),
        "received_at": received_at,
        "address": envelope_address,
        "source_key": blob.key,
    }
    try:
        CompanyMailStore(companies_root / company / "mailboxes").append(message)
    except Exception as exc:  # noqa: BLE001 - provider object must remain retryable
        print(
            f"[mail-router] WARN: store append failed company={company!r} "
            f"key={blob.key!r} ({exc!r}) — mail stays queued",
            flush=True,
        )
        return "deferred"

    # If this move fails, run_once records a deferred result.  A later retry
    # observes the same stable message id, skips the duplicate append, and can
    # finish the archive operation safely.
    backend.archive_processed(blob.key)
    return "processed"


def run_once(
    backend: MailBackend,
    *,
    registry_root: Path,
    companies_root: Path,
    clock: Callable[[], float] = time.time,
) -> dict[str, int]:
    """Run one resilient routing cycle over the provider's current batch."""

    stats = {"processed": 0, "unmatched": 0, "deferred": 0}
    for blob in backend.fetch_batch():
        try:
            outcome = _handle_blob(
                backend,
                blob,
                registry_root=Path(registry_root),
                companies_root=Path(companies_root),
                received_at=(
                    float(blob.received_at)
                    if blob.received_at is not None
                    else float(clock())
                ),
            )
        except Exception as exc:  # noqa: BLE001 - one bad message never stops the batch
            print(
                f"[mail-router] WARN: {blob.key} failed ({exc!r}) — left queued",
                flush=True,
            )
            outcome = "deferred"
        stats[outcome] += 1
    return stats


def main() -> None:
    missing = [
        name
        for name in ("R2_ENDPOINT", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY")
        if not os.environ.get(name)
    ]
    if missing:
        print(
            f"[mail-router] ERROR: missing env: {', '.join(missing)}",
            file=sys.stderr,
            flush=True,
        )
        raise SystemExit(1)

    backend = R2Backend(
        endpoint=os.environ["R2_ENDPOINT"],
        access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        bucket=os.environ.get("R2_BUCKET") or DEFAULT_BUCKET,
    )
    registry_root = Path(os.environ.get("MAIL_GLOBAL_ROOT") or DEFAULT_GLOBAL_ROOT)
    companies_root = Path(
        os.environ.get("COMPANIES_STATE_ROOT") or DEFAULT_COMPANIES_ROOT
    )
    raw_interval = os.environ.get("MAIL_POLL_INTERVAL", "")
    try:
        interval = float(raw_interval) if raw_interval else DEFAULT_POLL_INTERVAL
    except ValueError:
        print(
            f"[mail-router] WARNING: MAIL_POLL_INTERVAL={raw_interval!r} is not "
            f"a number — using {DEFAULT_POLL_INTERVAL:g}s",
            file=sys.stderr,
            flush=True,
        )
        interval = DEFAULT_POLL_INTERVAL

    print(
        f"[mail-router] polling bucket={backend.bucket!r} every {interval:g}s; "
        f"registry={registry_root}; companies={companies_root}",
        flush=True,
    )
    while True:
        try:
            stats = run_once(
                backend,
                registry_root=registry_root,
                companies_root=companies_root,
            )
            if any(stats.values()):
                print(
                    f"[mail-router] cycle: processed={stats['processed']} "
                    f"unmatched={stats['unmatched']} deferred={stats['deferred']}",
                    flush=True,
                )
        except Exception as exc:  # noqa: BLE001 - transient R2 error must not brick service
            print(
                f"[mail-router] WARN: poll cycle failed ({exc!r}) — retrying "
                f"in {interval:g}s",
                flush=True,
            )
        time.sleep(interval)


if __name__ == "__main__":
    main()
