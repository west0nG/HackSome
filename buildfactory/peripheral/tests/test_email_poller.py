"""Company mail-router tests.  Everything runs against local files and MockBackend."""

import json
from email.message import EmailMessage

from orchestration.mailbox import (
    CompanyMailStore,
    claim_company_mailbox,
    stable_mail_id,
)
from peripheral.email import poller
from peripheral.email.poller import MockBackend, parse_mail, run_once


def _claim(registry_root, company, name):
    return claim_company_mailbox(
        company,
        name,
        root=registry_root,
        now="2026-07-20T00:00:00+00:00",
    )


def _store(companies_root, company):
    return CompanyMailStore(companies_root / company / "mailboxes")


def _eml(
    frm="Signup Bot <no-reply@svc.test>",
    subject="Verify your email",
    text="your code is 424242 https://svc.test/verify",
    html=None,
    message_id="<m1@svc.test>",
):
    message = EmailMessage()
    message["From"] = frm
    message["To"] = "maya@foundagent.net"
    message["Subject"] = subject
    if message_id:
        message["Message-ID"] = message_id
    message.set_content(text)
    if html:
        message.add_alternative(html, subtype="html")
    return message.as_bytes()


def test_claimed_address_routes_to_company_journal_and_archives(tmp_path):
    registry = tmp_path / "global"
    companies = tmp_path / "companies"
    _claim(registry, "acme", "maya")
    backend = MockBackend()
    backend.add(
        "inbox/1.eml",
        _eml(),
        {"to": "Maya@Foundagent.net", "from": "bounce@svc.test"},
    )

    stats = run_once(
        backend,
        registry_root=registry,
        companies_root=companies,
        clock=lambda: 123.5,
    )

    assert stats == {"processed": 1, "unmatched": 0, "deferred": 0}
    assert backend.processed == ["inbox/1.eml"]
    assert not backend.pending and not backend.unmatched
    rows = _store(companies, "acme").read_messages()
    assert rows == [
        {
            "id": stable_mail_id("inbox/1.eml"),
            "received_at": 123.5,
            "address": "maya@foundagent.net",
            "from": "no-reply@svc.test",
            "subject": "Verify your email",
            "text": "your code is 424242 https://svc.test/verify\n",
            "links": ["https://svc.test/verify"],
            "message_id": "<m1@svc.test>",
            "source_key": "inbox/1.eml",
        }
    ]


def test_batch_routes_each_address_to_its_company_only(tmp_path):
    registry = tmp_path / "global"
    companies = tmp_path / "companies"
    _claim(registry, "acme", "sales")
    _claim(registry, "bravo", "billing")
    backend = MockBackend()
    backend.add("inbox/a.eml", _eml(subject="A"), {"to": "sales@foundagent.net"})
    backend.add(
        "inbox/b.eml", _eml(subject="B"), {"to": "billing@foundagent.net"}
    )

    timestamps = iter((10.0, 20.0))
    stats = run_once(
        backend,
        registry_root=registry,
        companies_root=companies,
        clock=lambda: next(timestamps),
    )

    assert stats == {"processed": 2, "unmatched": 0, "deferred": 0}
    assert [row["subject"] for row in _store(companies, "acme").read_messages()] == [
        "A"
    ]
    assert [row["subject"] for row in _store(companies, "bravo").read_messages()] == [
        "B"
    ]


def test_provider_receive_time_survives_router_backlog(tmp_path):
    registry = tmp_path / "global"
    companies = tmp_path / "companies"
    _claim(registry, "acme", "maya")
    backend = MockBackend()
    backend.add(
        "inbox/backlog.eml",
        _eml(),
        {"to": "maya@foundagent.net"},
        received_at=11.0,
    )

    run_once(
        backend,
        registry_root=registry,
        companies_root=companies,
        clock=lambda: 999.0,
    )

    assert _store(companies, "acme").read_messages()[0]["received_at"] == 11.0


def test_unclaimed_address_is_archived_unmatched_without_company_store(tmp_path):
    registry = tmp_path / "global"
    companies = tmp_path / "companies"
    _claim(registry, "acme", "maya")
    backend = MockBackend()
    backend.add("inbox/2.eml", _eml(), {"to": "nobody@foundagent.net"})

    stats = run_once(
        backend, registry_root=registry, companies_root=companies, clock=lambda: 1
    )

    assert stats == {"processed": 0, "unmatched": 1, "deferred": 0}
    assert backend.unmatched == ["inbox/2.eml"]
    assert not (companies / "acme").exists()


def test_claimed_localpart_on_another_domain_never_routes_to_company(tmp_path):
    registry = tmp_path / "global"
    companies = tmp_path / "companies"
    _claim(registry, "acme", "maya")
    backend = MockBackend()
    backend.add("inbox/foreign.eml", _eml(), {"to": "maya@example.net"})

    stats = run_once(
        backend, registry_root=registry, companies_root=companies, clock=lambda: 1
    )

    assert stats == {"processed": 0, "unmatched": 1, "deferred": 0}
    assert backend.unmatched == ["inbox/foreign.eml"]
    assert not (companies / "acme").exists()


def test_registry_error_leaves_blob_pending_and_never_marks_unmatched(
    tmp_path, monkeypatch
):
    backend = MockBackend()
    backend.add("inbox/3.eml", _eml(), {"to": "maya@foundagent.net"})

    def fail_resolution(*_args, **_kwargs):
        raise OSError("registry unavailable")

    monkeypatch.setattr(poller, "resolve_company", fail_resolution)
    stats = run_once(
        backend,
        registry_root=tmp_path / "global",
        companies_root=tmp_path / "companies",
    )

    assert stats == {"processed": 0, "unmatched": 0, "deferred": 1}
    assert "inbox/3.eml" in backend.pending
    assert not backend.unmatched


def test_store_error_leaves_provider_blob_pending(tmp_path, monkeypatch):
    registry = tmp_path / "global"
    companies = tmp_path / "companies"
    _claim(registry, "acme", "maya")
    backend = MockBackend()
    backend.add("inbox/4.eml", _eml(), {"to": "maya@foundagent.net"})

    class BrokenStore:
        def __init__(self, _root):
            pass

        def append(self, _message):
            raise OSError("disk unavailable")

    monkeypatch.setattr(poller, "CompanyMailStore", BrokenStore)
    stats = run_once(
        backend, registry_root=registry, companies_root=companies, clock=lambda: 4
    )

    assert stats == {"processed": 0, "unmatched": 0, "deferred": 1}
    assert "inbox/4.eml" in backend.pending
    assert not backend.processed


def test_archive_failure_retry_deduplicates_company_journal(tmp_path, monkeypatch):
    registry = tmp_path / "global"
    companies = tmp_path / "companies"
    _claim(registry, "acme", "maya")
    backend = MockBackend()
    backend.add("inbox/5.eml", _eml(), {"to": "maya@foundagent.net"})
    real_archive = backend.archive_processed
    calls = 0

    def fail_once(key):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise OSError("copy succeeded slowly")
        real_archive(key)

    monkeypatch.setattr(backend, "archive_processed", fail_once)
    first = run_once(
        backend, registry_root=registry, companies_root=companies, clock=lambda: 5
    )
    second = run_once(
        backend, registry_root=registry, companies_root=companies, clock=lambda: 6
    )

    assert first == {"processed": 0, "unmatched": 0, "deferred": 1}
    assert second == {"processed": 1, "unmatched": 0, "deferred": 0}
    assert backend.processed == ["inbox/5.eml"]
    rows = _store(companies, "acme").read_messages()
    assert len(rows) == 1
    assert rows[0]["received_at"] == 5.0


def test_one_archive_error_does_not_stop_later_blob(tmp_path, monkeypatch):
    registry = tmp_path / "global"
    companies = tmp_path / "companies"
    _claim(registry, "acme", "maya")
    backend = MockBackend()
    backend.add("inbox/6.eml", _eml(), {"to": "ghost@foundagent.net"})
    backend.add("inbox/7.eml", _eml(), {"to": "maya@foundagent.net"})

    monkeypatch.setattr(
        backend,
        "archive_unmatched",
        lambda _key: (_ for _ in ()).throw(RuntimeError("provider hiccup")),
    )
    stats = run_once(
        backend, registry_root=registry, companies_root=companies, clock=lambda: 7
    )

    assert stats == {"processed": 1, "unmatched": 0, "deferred": 1}
    assert backend.processed == ["inbox/7.eml"]
    assert "inbox/6.eml" in backend.pending


def test_corrupt_registry_fails_closed(tmp_path):
    registry = tmp_path / "global"
    registry.mkdir()
    (registry / "registry.jsonl").write_text("not json\n", encoding="utf-8")
    backend = MockBackend()
    backend.add("inbox/8.eml", _eml(), {"to": "maya@foundagent.net"})

    stats = run_once(
        backend, registry_root=registry, companies_root=tmp_path / "companies"
    )

    assert stats == {"processed": 0, "unmatched": 0, "deferred": 1}
    assert "inbox/8.eml" in backend.pending


def test_parse_multipart_prefers_text_plain():
    parsed = parse_mail(
        _eml(
            text="plain body https://x.test/a",
            html="<p>html body https://x.test/hidden</p>",
        )
    )
    assert "plain body" in parsed["text"]
    assert "html body" not in parsed["text"]
    assert parsed["links"] == ["https://x.test/a"]


def test_parse_html_only_mail_keeps_code_and_link():
    message = EmailMessage()
    message["From"] = "verify@example.test"
    message["Subject"] = "HTML verification"
    message.set_content(
        '<p>Your code is 778899</p><a href="https://example.test/verify">Verify</a>',
        subtype="html",
    )

    parsed = parse_mail(message.as_bytes())

    assert "778899" in parsed["text"]
    assert parsed["links"] == ["https://example.test/verify"]


def test_parse_links_strip_trailing_punctuation_and_deduplicate():
    parsed = parse_mail(
        _eml(
            text="see https://x.test/verify. or (https://x.test/alt) "
            "again https://x.test/verify."
        )
    )
    assert parsed["links"] == ["https://x.test/verify", "https://x.test/alt"]


def test_missing_message_id_is_still_stably_routed(tmp_path):
    registry = tmp_path / "global"
    companies = tmp_path / "companies"
    _claim(registry, "acme", "maya")
    backend = MockBackend()
    backend.add(
        "inbox/no-id.eml", _eml(message_id=None), {"to": "maya@foundagent.net"}
    )

    stats = run_once(
        backend, registry_root=registry, companies_root=companies, clock=lambda: 8
    )

    assert stats["processed"] == 1
    row = _store(companies, "acme").read_messages()[0]
    assert row["message_id"] is None
    assert row["id"] == stable_mail_id("inbox/no-id.eml")


def test_parse_from_falls_back_to_raw_header():
    message = EmailMessage()
    message["From"] = "no-reply@svc.test"
    message["Subject"] = "s"
    message.set_content("x")
    assert parse_mail(message.as_bytes())["from"] == "no-reply@svc.test"


def test_localpart_extraction():
    assert poller._localpart("Maya@Foundagent.net") == "maya"
    assert poller._localpart("Maya <maya@foundagent.net>") == "maya"
    assert poller._localpart("") == ""
    assert poller._localpart("no-at-sign") == "no-at-sign"


def test_missing_envelope_recipient_goes_unmatched(tmp_path):
    registry = tmp_path / "global"
    _claim(registry, "acme", "maya")
    backend = MockBackend()
    backend.add("inbox/9.eml", _eml(), {})

    stats = run_once(
        backend,
        registry_root=registry,
        companies_root=tmp_path / "companies",
    )

    assert stats == {"processed": 0, "unmatched": 1, "deferred": 0}
    assert backend.unmatched == ["inbox/9.eml"]


def test_persisted_journal_is_jsonl_not_agent_delivery(tmp_path):
    registry = tmp_path / "global"
    companies = tmp_path / "companies"
    _claim(registry, "acme", "maya")
    backend = MockBackend()
    backend.add("inbox/10.eml", _eml(), {"to": "maya@foundagent.net"})

    run_once(backend, registry_root=registry, companies_root=companies)

    path = companies / "acme" / "mailboxes" / "messages.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 1
    assert "to" not in rows[0]
    assert "receivers" not in rows[0]
