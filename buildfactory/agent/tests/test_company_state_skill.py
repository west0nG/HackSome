"""Static contracts for native Company State discovery and maintenance."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILLS = ROOT / "agents" / "assets" / "skills"
WRITABLE = SKILLS / "company-state" / "SKILL.md"
READONLY = SKILLS / "company-state-readonly" / "SKILL.md"


def _words(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def test_company_state_teaches_native_progressive_discovery_and_maintenance():
    text = _words(WRITABLE)
    for phrase in (
        "use it everytime",
        "native file tools directly",
        "Before writing",
        "Inspect the target directory",
        "Search that area",
        "current authoritative leaf",
        "Re-read a shared target",
    ):
        assert phrase in text


def test_company_state_skills_do_not_restore_the_removed_storage_protocol():
    text = _words(WRITABLE) + " " + _words(READONLY)
    for removed in (
        "company.py",
        "COMPANY_ROOT",
        "MAP.md",
        "OVERVIEW.md",
        ".company.lock",
    ):
        assert removed not in text


def test_readonly_company_state_starts_from_evidence_and_forbids_mutation():
    text = _words(READONLY)
    for phrase in (
        "mounted read-only",
        "identifies an exact `/company/...` path, inspect it first",
        "narrowly scoped search",
        "assume every completed Goal must leave a Company State artifact",
        "Never write, create, move, rename, delete, or reorganize",
    ):
        assert phrase in text
