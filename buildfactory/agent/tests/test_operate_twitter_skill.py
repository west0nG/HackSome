"""Static contracts for Growth's stateful public Twitter/X skill.

The tests pin routing and system-specific boundaries without translating
business judgment into a Python score. Runtime behavior is covered separately
by the real-account E2E in the owning Trellis task.
"""

import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "agents" / "assets" / "skills" / "operate-twitter"
HOST = SKILL / "SKILL.md"
PLAYBOOKS = {
    "references/bootstrap-or-reposition.md",
    "references/publish.md",
    "references/engage.md",
    "references/maintain.md",
}
MD_LINK = re.compile(r"\]\(([^)#]+\.md)(?:#[^)]+)?\)")


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _frontmatter(text: str) -> dict:
    assert text.startswith("---\n")
    _empty, raw, _body = text.split("---", 2)
    return yaml.safe_load(raw)


def test_operate_twitter_frontmatter_is_a_complete_trigger():
    meta = _frontmatter(_text(HOST))
    assert set(meta) == {"name", "description"}
    assert meta["name"] == "operate-twitter"
    description = meta["description"].lower()
    for trigger in (
        "twitter/x",
        "authenticated browser",
        "audits",
        "profile edits",
        "posts",
        "replies",
        "deletion",
    ):
        assert trigger in description
    assert "not direct messages" in description


def test_operate_twitter_routes_directly_to_all_playbooks():
    links = set(MD_LINK.findall(_text(HOST)))
    assert links == PLAYBOOKS
    for relative in links:
        assert (SKILL / relative).is_file()


def test_operate_twitter_pins_the_system_specific_loop_and_boundaries():
    host = _text(HOST)
    host_words = " ".join(host.split())
    required = (
        "native progressive-disclosure workflow",
        "Company memory may be stale; the live account wins",
        "Posting is not the default",
        "currently displayed account",
        "A click, a toast, or a closed dialog is not sufficient evidence",
        "Do not enumerate the complete account history",
        "write the recoverable current-state baseline before the first mutation",
        "Never snapshot every item in a long feed",
        "directly with native file tools",
        "V7 has no session-end record marker",
        "authenticated Playwright browser",
        "Do not read, send, or manage Direct Messages",
    )
    for phrase in required:
        assert phrase in host_words

    all_markdown = "\n".join(_text(path) for path in SKILL.rglob("*.md"))
    assert "company.py" not in all_markdown
    assert "/company/channels/" not in all_markdown
    assert "@Solvotheagent" not in all_markdown


def test_playbooks_keep_public_scope_and_precise_delete_semantics():
    engage = _text(SKILL / "references" / "engage.md")
    maintain = _text(SKILL / "references" / "maintain.md")
    maintain_words = " ".join(maintain.split())
    assert "Do not enter Direct Messages" in engage
    assert "There is no daily interaction quota" in engage
    for phrase in (
        "exact post/reply URL",
        "author, text, timestamp, and conversation context",
        "reopen the canonical URL and the public profile",
        "Do not leave a cleanup promise for the next wake",
        "stop before the next mutation if the operator cancels",
    ):
        assert phrase in maintain_words

    # Progressive disclosure is load-bearing: no individual playbook should
    # grow into a second monolithic social-media skill.
    for path in (SKILL / "references").glob("*.md"):
        assert len(_text(path).splitlines()) < 120
