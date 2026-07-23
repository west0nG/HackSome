"""Active Peripheral adapter contracts. Email must use the Company mail-router."""

import pytest

from orchestration.inbox import CEO_KEY, FileInbox
from peripheral.manifest import ADAPTERS
from peripheral.runner import ingest


def _inbox(tmp_path):
    return FileInbox(tmp_path / "inbox", poll_tick=0.01)


def _take(inbox, key):
    message = inbox.peek_one(key)
    if message is not None:
        inbox.ack_one(key)
    return message


def test_manifest_excludes_email_ingress_bypass():
    assert ADAPTERS == ["webhook"]


def test_webhook_adapter_produces_five_field_ime(tmp_path):
    inbox = _inbox(tmp_path)
    ime = ingest(
        "webhook",
        {"event": "payment.succeeded", "id": "w1", "summary": "Stripe $49"},
        inbox=inbox,
    )

    assert set(ime) == {"id", "time", "to", "text", "body"}
    message = _take(inbox, CEO_KEY)
    assert message is not None
    assert "payment.succeeded" in message["text"]
    assert "Stripe" in message["body"]


def test_webhook_can_target_a_specific_department(tmp_path):
    inbox = _inbox(tmp_path)
    ingest("webhook", {"event": "ping", "id": "w2", "to": "growth"}, inbox=inbox)
    assert _take(inbox, CEO_KEY) is None
    assert _take(inbox, "growth")["text"] == "Webhook: ping"


def test_email_source_is_rejected_so_it_cannot_skip_company_journal(tmp_path):
    with pytest.raises(KeyError, match="no adapter"):
        ingest("email", {"to": "growth", "text": "bypass"}, inbox=_inbox(tmp_path))


def test_unknown_source_raises(tmp_path):
    with pytest.raises(KeyError):
        ingest("telegram", {}, inbox=_inbox(tmp_path))
