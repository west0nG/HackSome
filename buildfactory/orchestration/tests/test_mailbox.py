"""Domain-wide Company mailbox registry and per-Company mail journal tests."""

import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import ANY

import pytest

import orchestration.mailbox as mailbox


REPO = Path(mailbox.__file__).resolve().parents[1]


@pytest.fixture
def registry(tmp_path):
    return tmp_path / "global-mail"


def claim(registry, company, name, **kwargs):
    return mailbox.claim_company_mailbox(company, name, root=registry, **kwargs)


@pytest.mark.parametrize(
    "bad",
    [
        "a",
        "a" * 33,
        "Maya",
        "-lead",
        "lead-",
        ".dot",
        "dot.",
        "_ab",
        "ab_",
        "no space",
        "user+tag",
        "a@b",
        "",
    ],
)
def test_claim_rejects_bad_names(registry, bad):
    with pytest.raises(mailbox.MailboxValidationError):
        claim(registry, "acme", bad)
    assert mailbox.read_registry(registry) == []


def test_claim_rejects_non_text_name_and_label(registry):
    with pytest.raises(mailbox.MailboxValidationError, match="name must be text"):
        claim(registry, "acme", 7)
    with pytest.raises(mailbox.MailboxValidationError, match="label must be text"):
        claim(registry, "acme", "maya", label=["external"])
    assert mailbox.read_registry(registry) == []


@pytest.mark.parametrize("reserved", sorted(mailbox.RESERVED_NAMES))
def test_claim_rejects_reserved_names(registry, reserved):
    with pytest.raises(mailbox.MailboxValidationError):
        claim(registry, "acme", reserved)


@pytest.mark.parametrize(
    "good", ["a1", "maya", "hello", "dev.rel", "x_y-z.9", "a" + "b" * 30 + "c"]
)
def test_claim_accepts_valid_names_and_resolves_company(registry, good):
    result = claim(registry, "acme", good)
    assert result["created"] is True
    assert result["company"] == "acme"
    assert result["address"] == f"{good}@foundagent.net"
    assert mailbox.resolve_company(good.upper(), registry) == "acme"


def test_claim_records_company_label_and_ceo_attribution(registry):
    result = claim(registry, "acme", "maya", label=" persona identity ")
    assert result["label"] == "persona identity"
    (event,) = mailbox.read_registry(registry)
    assert event["company"] == "acme"
    assert event["by"] == "ceo"
    assert event["detail"] == {"label": "persona identity"}


def test_same_company_reclaim_is_idempotent(registry):
    first = claim(registry, "acme", "maya", now="2026-07-20T00:00:00+00:00")
    second = claim(registry, "acme", "maya", label="ignored")
    assert first["created"] is True
    assert second["created"] is False
    assert second["claimed_at"] == first["claimed_at"]
    assert second["label"] is None
    assert len(mailbox.read_registry(registry)) == 1


def test_other_company_cannot_claim_or_own_address(registry):
    claim(registry, "acme", "maya")
    with pytest.raises(mailbox.MailboxConflictError):
        claim(registry, "other", "maya")
    assert mailbox.company_owns("acme", "maya", registry)
    assert not mailbox.company_owns("other", "maya", registry)


def test_company_cap_is_fixed_at_five_and_ignores_old_env(registry, monkeypatch):
    monkeypatch.setenv("MAILBOX_CAP", "99")
    for index in range(1, 6):
        result = claim(registry, "acme", f"mail{index}")
        assert result["used"] == index
        assert result["limit"] == 5
    with pytest.raises(mailbox.MailboxCapError) as error:
        claim(registry, "acme", "mail6")
    assert "5/5" in str(error.value)
    assert mailbox.resolve_company("mail6", registry) is None


def test_cap_is_per_company_and_list_is_company_scoped(registry):
    claim(registry, "acme", "hello", label="front door")
    claim(registry, "other", "maya")
    assert mailbox.list_company_mailboxes("acme", registry) == [
        {
            "name": "hello",
            "company": "acme",
            "label": "front door",
            "claimed_at": ANY,
        }
    ]
    assert [row["name"] for row in mailbox.list_company_mailboxes("other", registry)] == [
        "maya"
    ]


def test_registry_fails_closed_for_invalid_json_and_old_agent_shape(registry):
    registry.mkdir(parents=True)
    mailbox.registry_path(registry).write_text("{not json\n", encoding="utf-8")
    with pytest.raises(mailbox.MailboxStoreError):
        mailbox.resolve_company("maya", registry)

    mailbox.registry_path(registry).write_text(
        '{"event":"claim","name":"maya","by":"builder","detail":{}}\n',
        encoding="utf-8",
    )
    with pytest.raises(mailbox.MailboxStoreError):
        mailbox.resolve_company("maya", registry)


def test_registry_taxonomy_has_no_mutating_lifecycle_functions():
    for forbidden in (
        "release",
        "rename",
        "transfer",
        "add_receiver",
        "remove_receiver",
        "mine",
    ):
        assert not hasattr(mailbox, forbidden)


def test_direct_mailbox_cli_is_disabled(capsys):
    assert mailbox.main() == 2
    assert "Company Hub" in capsys.readouterr().err


def test_concurrent_company_claims_have_exactly_one_winner(registry):
    code = """
import sys
from pathlib import Path
from orchestration.mailbox import claim_company_mailbox, MailboxConflictError
try:
    claim_company_mailbox(sys.argv[2], "maya", root=Path(sys.argv[1]))
except MailboxConflictError:
    raise SystemExit(1)
"""
    base = os.environ.copy()
    base["PYTHONPATH"] = str(REPO) + os.pathsep + base.get("PYTHONPATH", "")
    processes = [
        subprocess.Popen(
            [sys.executable, "-c", code, str(registry), company],
            cwd=REPO,
            env=base,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        for company in ("acme", "other")
    ]
    assert sorted(process.wait(timeout=30) for process in processes) == [0, 1]
    events = mailbox.read_registry(registry)
    assert len(events) == 1
    assert events[0]["company"] in {"acme", "other"}


def message(index: int, *, received_at: float | None = None, text: str = "code 1234"):
    source_key = f"inbox/{index}.eml"
    return {
        "id": mailbox.stable_mail_id(source_key),
        "received_at": float(index if received_at is None else received_at),
        "address": "hello@foundagent.net",
        "from": "service@example.com",
        "subject": f"Verify {index}",
        "text": text,
        "links": [f"https://example.com/{index}"],
        "message_id": f"<message-{index}>",
        "source_key": source_key,
    }


def test_company_mail_append_is_stable_and_idempotent(tmp_path):
    store = mailbox.CompanyMailStore(tmp_path / "mailboxes")
    row = message(1)
    assert store.append(row) is True
    assert store.append(row) is False
    assert store.read_messages() == [mailbox.normalize_message(row)]
    assert store.seen_path.read_text(encoding="utf-8").splitlines() == [row["id"]]


def test_company_mail_normalizes_limits_and_public_projection_hides_source(tmp_path):
    store = mailbox.CompanyMailStore(tmp_path / "mailboxes")
    row = message(1, text="x" * (mailbox.BODY_TEXT_MAX + 20))
    row["links"] = ["https://example.com/" + "x" * 3_000] * 60
    store.append(row)
    (public,) = store.peek()
    assert len(public["text"]) == mailbox.BODY_TEXT_MAX
    assert len(public["links"]) == mailbox.LINK_MAX
    assert all(len(link) <= mailbox.LINK_TEXT_MAX for link in public["links"])
    assert "source_key" not in public


def test_company_mail_normalization_bounds_untrusted_headers():
    row = message(1)
    row.update(
        {
            "address": "a" * 500 + "@foundagent.net",
            "from": "f" * 2_000,
            "subject": "s" * 2_000,
            "message_id": "m" * 2_000,
        }
    )

    normalized = mailbox.normalize_message(row)

    assert len(normalized["address"]) == mailbox.ADDRESS_TEXT_MAX
    assert len(normalized["from"]) == mailbox.HEADER_TEXT_MAX
    assert len(normalized["subject"]) == mailbox.HEADER_TEXT_MAX
    assert len(normalized["message_id"]) == mailbox.MESSAGE_ID_TEXT_MAX

    row.update({"from": "", "subject": ""})
    normalized = mailbox.normalize_message(row)
    assert normalized["from"] == "?"
    assert normalized["subject"] == "(无主题)"


def test_peek_filters_since_takes_latest_hundred_then_orders_ascending(tmp_path):
    store = mailbox.CompanyMailStore(tmp_path / "mailboxes")
    for index in range(130):
        store.append(message(index, received_at=float(index)))
    rows = store.peek(since=10.0)
    assert len(rows) == 100
    assert [row["received_at"] for row in rows] == list(map(float, range(30, 130)))
    assert store.peek(since=125.0, limit=100)[0]["received_at"] == 125.0


def test_peek_is_non_consuming_and_ceo_cursor_is_independent(tmp_path):
    store = mailbox.CompanyMailStore(tmp_path / "mailboxes")
    store.append(message(1))
    store.append(message(2))
    assert len(store.peek()) == 2
    assert store.peek_for_ceo()["id"] == message(1)["id"]
    assert len(store.peek()) == 2
    store.ack_for_ceo(message(1)["id"])
    assert store.peek_for_ceo()["id"] == message(2)["id"]
    assert len(store.peek()) == 2


def test_ceo_ack_rejects_non_head_and_bad_cursor(tmp_path):
    store = mailbox.CompanyMailStore(tmp_path / "mailboxes")
    store.append(message(1))
    with pytest.raises(mailbox.MailboxStoreError):
        store.ack_for_ceo("not-the-head")
    store.cursor_path.write_text("99", encoding="utf-8")
    with pytest.raises(mailbox.MailboxStoreError):
        store.peek_for_ceo()


def test_corrupt_company_mail_journal_fails_closed(tmp_path):
    store = mailbox.CompanyMailStore(tmp_path / "mailboxes")
    store.root.mkdir(parents=True)
    store.messages_path.write_text("{bad json\n", encoding="utf-8")
    with pytest.raises(mailbox.MailboxStoreError):
        store.peek()


def test_render_message_preserves_untrusted_marker_address_and_source_time():
    headline, body, source_time = mailbox.render_message(message(1, received_at=1.0))
    assert headline == "新邮件：service@example.com · Verify 1"
    assert body.splitlines()[0] == mailbox.UNTRUSTED_MARKER
    assert "发往 hello@foundagent.net" in body
    assert "code 1234" in body
    assert "链接: https://example.com/1" in body
    assert source_time == "1970-01-01T00:00:01+00:00"
