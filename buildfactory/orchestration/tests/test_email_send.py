"""Company-level outbound email tests; provider HTTP is always mocked or keyless."""

import fcntl
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

import orchestration.email_send as email_send
from orchestration.mailbox import claim_company_mailbox


@pytest.fixture
def world(tmp_path, monkeypatch):
    global_root = tmp_path / "global-mail"
    company_mail_root = tmp_path / "state" / "acme" / "mailboxes"
    claim_company_mailbox("acme", "maya", root=global_root)
    for name in (
        "EMAIL_SEND_DAILY_COMPANY",
        "EMAIL_SEND_DAILY_PER_ADDRESS",
        "MAIL_DOMAIN",
        "RESEND_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)
    calls = []

    def post(payload, idempotency_key):
        calls.append(SimpleNamespace(payload=payload, key=idempotency_key))
        return True, f"re-{len(calls)}"

    monkeypatch.setattr(email_send, "_post_resend", post)
    return SimpleNamespace(
        global_root=global_root,
        company_mail_root=company_mail_root,
        calls=calls,
    )


def _send(world, **overrides):
    values = {
        "company": "acme",
        "global_mail_root": world.global_root,
        "company_mail_root": world.company_mail_root,
        "by": "worker-a",
        "request_id": "send-1",
        "sender": "maya",
        "to": "human@example.com",
        "subject": "Hello",
        "text": "A useful message",
    }
    values.update(overrides)
    return email_send.send_company_email(**values)


def _events(world, event=None):
    rows = email_send.read_ledger(world.company_mail_root)
    return [row for row in rows if event is None or row["event"] == event]


def test_company_owned_address_sends_with_request_id_and_audit_ledger(world):
    result = _send(world, from_name='Maya "Ops"', html="<b>Hello</b>")

    assert result == {
        "sent": True,
        "replayed": False,
        "reservation_id": "send-1",
        "provider_id": "re-1",
        "from": "maya@foundagent.net",
        "to": "human@example.com",
        "subject": "Hello",
    }
    assert len(world.calls) == 1
    call = world.calls[0]
    assert call.key == "send-1"
    assert call.payload == {
        "from": '"Maya \'Ops\'" <maya@foundagent.net>',
        "to": ["human@example.com"],
        "subject": "Hello",
        "text": "A useful message",
        "html": "<b>Hello</b>",
    }
    assert [row["event"] for row in _events(world)] == ["reserve", "sent"]
    assert all(row["id"] == "send-1" for row in _events(world))
    assert _events(world, "reserve")[0]["by"] == "worker-a"


def test_sender_case_is_normalized(world):
    result = _send(world, sender="MAYA")
    assert result["from"] == "maya@foundagent.net"


def test_unclaimed_or_other_company_address_is_rejected_before_reserve(world):
    with pytest.raises(email_send.EmailIdentityError, match="not owned"):
        _send(world, sender="nobody")
    claim_company_mailbox("bravo", "billing", root=world.global_root)
    with pytest.raises(email_send.EmailIdentityError, match="not owned"):
        _send(world, sender="billing")

    assert _events(world) == []
    assert world.calls == []


def test_corrupt_global_registry_fails_closed(world):
    (world.global_root / "registry.jsonl").write_text("not json\n", encoding="utf-8")
    with pytest.raises(email_send.EmailStoreError, match="registry unreadable"):
        _send(world)
    assert world.calls == []


def test_same_request_is_idempotent_without_second_provider_call(world):
    first = _send(world)
    second = _send(world)

    assert first["provider_id"] == second["provider_id"] == "re-1"
    assert first["replayed"] is False
    assert second["replayed"] is True
    assert len(world.calls) == 1
    assert [row["event"] for row in _events(world)] == ["reserve", "sent"]


def test_request_id_cannot_be_reused_for_different_email(world):
    _send(world)
    with pytest.raises(email_send.EmailValidationError, match="different email"):
        _send(world, text="different body")
    assert len(world.calls) == 1


def test_reserved_only_crash_retry_uses_same_provider_idempotency_key(
    world, monkeypatch
):
    attempts = 0

    def crash_then_send(_payload, key):
        nonlocal attempts
        attempts += 1
        assert key == "send-1"
        if attempts == 1:
            raise RuntimeError("process died before response")
        return True, "re-recovered"

    monkeypatch.setattr(email_send, "_post_resend", crash_then_send)
    with pytest.raises(RuntimeError, match="process died"):
        _send(world)
    result = _send(world)

    assert result["sent"] is True
    assert result["replayed"] is True
    assert result["provider_id"] == "re-recovered"
    assert attempts == 2
    assert [row["event"] for row in _events(world)] == ["reserve", "sent"]


def test_provider_failure_consumes_slot_and_is_not_blindly_retried(
    world, monkeypatch
):
    monkeypatch.setenv("EMAIL_SEND_DAILY_COMPANY", "1")
    attempts = []

    def fail(_payload, key):
        attempts.append(key)
        return False, '{"message":"domain not verified"}'

    monkeypatch.setattr(email_send, "_post_resend", fail)
    with pytest.raises(email_send.EmailProviderError, match="not refunded"):
        _send(world)
    with pytest.raises(email_send.EmailProviderError, match="prior attempt failed"):
        _send(world)
    with pytest.raises(email_send.EmailQuotaError, match="quota reached"):
        _send(world, request_id="send-2")

    assert attempts == ["send-1"]
    assert [row["event"] for row in _events(world)] == ["reserve", "failed"]


def test_company_quota_counts_all_addresses(world, monkeypatch):
    claim_company_mailbox("acme", "ivy", root=world.global_root)
    monkeypatch.setenv("EMAIL_SEND_DAILY_COMPANY", "2")
    monkeypatch.setenv("EMAIL_SEND_DAILY_PER_ADDRESS", "10")

    _send(world, request_id="company-1", sender="maya")
    _send(world, request_id="company-2", sender="ivy")
    with pytest.raises(email_send.EmailQuotaError, match=r"2/2"):
        _send(world, request_id="company-3", sender="maya")

    assert len(_events(world, "reserve")) == 2


def test_per_address_quota_does_not_block_another_company_address(
    world, monkeypatch
):
    claim_company_mailbox("acme", "ivy", root=world.global_root)
    monkeypatch.setenv("EMAIL_SEND_DAILY_COMPANY", "10")
    monkeypatch.setenv("EMAIL_SEND_DAILY_PER_ADDRESS", "1")

    _send(world, request_id="address-1", sender="maya")
    with pytest.raises(email_send.EmailQuotaError, match="Address outbound quota"):
        _send(world, request_id="address-2", sender="maya")
    _send(world, request_id="address-3", sender="ivy")

    assert len(_events(world, "reserve")) == 2


def test_reservation_older_than_24_hours_no_longer_counts(world, monkeypatch):
    now = datetime(2026, 7, 20, tzinfo=timezone.utc)
    monkeypatch.setattr(email_send, "_now", lambda: now)
    monkeypatch.setenv("EMAIL_SEND_DAILY_COMPANY", "1")
    world.company_mail_root.mkdir(parents=True, exist_ok=True)
    old = {
        "ts": (now - timedelta(hours=25)).isoformat(),
        "event": "reserve",
        "id": "old",
        "from": "maya",
        "to": "old@example.com",
        "by": "growth",
        "detail": {"fingerprint": "old"},
    }
    email_send.ledger_path(world.company_mail_root).write_text(
        json.dumps(old) + "\n", encoding="utf-8"
    )

    assert _send(world)["sent"] is True


def test_zero_or_invalid_quota_environment_is_safe(world, monkeypatch, capsys):
    monkeypatch.setenv("EMAIL_SEND_DAILY_COMPANY", "0")
    with pytest.raises(email_send.EmailQuotaError, match="disables"):
        _send(world)
    assert _events(world) == []

    monkeypatch.setenv("EMAIL_SEND_DAILY_COMPANY", "banana")
    assert _send(world, request_id="fallback")["sent"] is True
    assert "using 30" in capsys.readouterr().err


def test_ledger_corruption_fails_closed_before_provider(world):
    world.company_mail_root.mkdir(parents=True, exist_ok=True)
    email_send.ledger_path(world.company_mail_root).write_text(
        "{not json\n", encoding="utf-8"
    )
    with pytest.raises(email_send.EmailStoreError, match="ledger unreadable"):
        _send(world)
    assert world.calls == []


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"to": "not-an-address"}, "recipient"),
        ({"subject": ""}, "subject"),
        ({"subject": "hello\nBcc: x@y.z"}, "newlines"),
        ({"text": ""}, "text"),
        ({"sender": "bad+tag"}, "localpart"),
        ({"html": 7}, "html"),
        ({"request_id": "bad\nrequest"}, "request_id"),
        ({"from_name": "Maya\nBcc: x@y.z"}, "from_name"),
    ],
)
def test_invalid_payload_is_rejected_without_reservation(world, overrides, message):
    with pytest.raises(email_send.EmailValidationError, match=message):
        _send(world, **overrides)
    assert _events(world) == []


def test_http_runs_outside_quota_lock(world, monkeypatch):
    observed = []

    def probe(_payload, _key):
        fd = os.open(world.company_mail_root / ".send.lock", os.O_RDWR)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            observed.append("unlocked")
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)
        return True, "re-lock-test"

    monkeypatch.setattr(email_send, "_post_resend", probe)
    _send(world)
    assert observed == ["unlocked"]


def test_malformed_matching_ledger_event_fails_closed(world):
    world.company_mail_root.mkdir(parents=True, exist_ok=True)
    bad = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": "reserve",
        "id": "send-1",
        "from": "maya",
        "to": "human@example.com",
        "by": "worker-a",
        "detail": "not-an-object",
    }
    email_send.ledger_path(world.company_mail_root).write_text(
        json.dumps(bad) + "\n", encoding="utf-8"
    )

    with pytest.raises(email_send.EmailStoreError, match="detail is malformed"):
        _send(world)
    assert world.calls == []


def test_real_http_boundary_sets_resend_idempotency_header(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "secret")
    captured = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b'{"id":"re-live"}'

    def urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr(email_send.urllib.request, "urlopen", urlopen)
    ok, detail = email_send._post_resend(
        {"from": "x", "to": ["a@b.c"], "subject": "s", "text": "b"},
        "hub-request-7",
    )

    assert (ok, detail) == (True, "re-live")
    assert captured["request"].get_header("Idempotency-key") == "hub-request-7"
    assert captured["request"].get_header("Authorization") == "Bearer secret"
    assert captured["timeout"] == email_send.HTTP_TIMEOUT_SECS


def test_direct_cli_is_disabled(capsys):
    assert email_send.main() == 2
    assert "Company Hub" in capsys.readouterr().err


def test_two_processes_cannot_oversubscribe_last_company_slot(tmp_path):
    global_root = tmp_path / "global"
    company_root = tmp_path / "state" / "acme" / "mailboxes"
    claim_company_mailbox("acme", "maya", root=global_root)
    repo = Path(email_send.__file__).resolve().parents[1]
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(repo) + os.pathsep + environment.get(
        "PYTHONPATH", ""
    )
    environment["EMAIL_SEND_DAILY_COMPANY"] = "1"
    environment.pop("RESEND_API_KEY", None)
    code = """
import sys
from pathlib import Path
from orchestration.email_send import send_company_email
try:
    send_company_email(
        company='acme', global_mail_root=Path(sys.argv[1]),
        company_mail_root=Path(sys.argv[2]), by='worker-a',
        request_id=sys.argv[3], sender='maya', to='human@example.com',
        subject='s', text='b')
except Exception as exc:
    print(type(exc).__name__)
"""
    processes = [
        subprocess.Popen(
            [
                sys.executable,
                "-c",
                code,
                str(global_root),
                str(company_root),
                f"race-{index}",
            ],
            cwd=repo,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for index in range(2)
    ]
    outputs = [process.communicate(timeout=30)[0].strip() for process in processes]

    assert sorted(outputs) == ["EmailProviderError", "EmailQuotaError"]
    reserves = [
        row
        for row in email_send.read_ledger(company_root)
        if row["event"] == "reserve"
    ]
    assert len(reserves) == 1
