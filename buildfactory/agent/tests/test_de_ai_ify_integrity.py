"""End-to-end integrity of the V7 Worker's reusable `de-ai-ify` skill.

Materializes growth's resident loadout through the real container-startup path,
then walks the materialized `de-ai-ify` tree and asserts every LOCAL markdown
reference (both `[text](path.md)` links and inline `` `path.md` `` mentions)
resolves to a file that actually exists.

This locks shut the exact class of defect a blind review caught in the first cut:
the Chinese half was vendored as leaf reference files whose links pointed at a
control layer and sibling files that were never copied in, leaving dead pointers.
Incomplete vendoring now fails a fast, deterministic test instead of silently
shipping a half-wired skill.
"""

import os
import re

from agent import resident_loadout

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AGENTS = os.path.join(REPO, "agents")

_MD_LINK = re.compile(r"\]\(([^)]+)\)")          # [text](target) — a real link
_CODE_PATH = re.compile(r"`([^`]+\.md)`")         # `some/path.md` — inline mention


def _clean(raw):
    """Normalize a raw href/mention to a local .md path, or None to skip.

    URLs, mail links, anchors and non-.md targets are dropped: only local
    markdown files are candidates for the resolve check.
    """
    ref = raw.strip().split("#", 1)[0].strip()
    if not ref or ref.startswith(("http://", "https://", "mailto:")):
        return None
    return ref if ref.endswith(".md") else None


def _resolves(skill_root, base, ref):
    return os.path.exists(os.path.normpath(os.path.join(base, ref))) or os.path.exists(
        os.path.normpath(os.path.join(str(skill_root), ref))
    )


def test_de_ai_ify_reference_links_resolve_end_to_end(tmp_path, monkeypatch):
    # Codex discovers Skills under ~/.agents/skills rather than CLAUDE_HOME.
    # Isolate HOME so this test follows the selected runtime without touching
    # or depending on the developer's real Skill installation.
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv(
        "AGENT_SPEC", os.path.join(AGENTS, "ephemeral", "worker.yaml")
    )
    resident_loadout.materialize_for(
        "worker", agents_dir=AGENTS, claude_home=str(tmp_path / "claude")
    )
    skill_root = home / ".agents" / "skills" / "de-ai-ify"
    host = skill_root / "SKILL.md"
    assert host.exists(), "de-ai-ify did not materialize"

    md_files = [
        os.path.join(dp, f)
        for dp, _dirs, files in os.walk(skill_root)
        for f in files
        if f.endswith(".md")
    ]
    assert md_files, "no markdown found under the materialized de-ai-ify skill"

    broken = []
    for path in md_files:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        base = os.path.dirname(path)
        # Every real markdown link `](target.md)` must resolve — this is the
        # dead-pointer class the blind review found in the vendored zh/ tree.
        refs = {m.group(1) for m in _MD_LINK.finditer(text)}
        # For the host SKILL.md (ours), inline `path.md` mentions are routing
        # pointers, so check those too. Vendored files use inline code for prose
        # mentions (short names / repo-relative paths), so we do NOT check those.
        if os.path.abspath(path) == os.path.abspath(str(host)):
            refs |= {m.group(1) for m in _CODE_PATH.finditer(text)}

        for raw in refs:
            ref = _clean(raw)
            if ref and not _resolves(skill_root, base, ref):
                broken.append(f"{os.path.relpath(path, skill_root)} -> {ref}")

    assert not broken, "dead reference pointers in de-ai-ify:\n" + "\n".join(sorted(broken))
