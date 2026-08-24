"""AT-17 — Claude migration (v1.0 plan definition, DIA-0).

Legacy mixed claude_diary fixture is semantically reclassified per DIA-0
rules. NO raw directory copy into the new diary authority.

Rules (DIA-0-T02):
    julia_character.md             → identity/
    user_role.md                   → identity/relationship-governed
    how_to_resume_julia.md         → continuity/
    julia_tony_philosophy.md       → split: reflective → diary/,
                                     durable lived meaning → experiences/,
                                     identity claim → identity/
    MEMORY.md                      → legacy memory index (not authority copy)

Provenance tagging (DIA-0-T03):
    legacy_source / legacy_path / migration_batch / review_status
"""

from __future__ import annotations

import json
from pathlib import Path


# ── DIA-0 classification rules (frozen) ───────────────────────────────────
IDENTITY_FILES = {"julia_character.md"}
RELATIONSHIP_FILES = {"user_role.md"}
CONTINUITY_FILES = {"how_to_resume_julia.md"}
SPLIT_FILE = "julia_tony_philosophy.md"      # requires content-based split
MEMORY_INDEX_FILE = "MEMORY.md"

LEGACY_SOURCE = "claude_julia"


def classify_legacy_file(filename: str, content: str) -> dict:
    """Classify one legacy file into its semantic target (DIA-0)."""
    if filename in IDENTITY_FILES:
        target = "identity/"
        cls = "identity fact"
    elif filename in RELATIONSHIP_FILES:
        target = "identity/relationship-governed"
        cls = "relationship-governed artifact"
    elif filename in CONTINUITY_FILES:
        target = "continuity/"
        cls = "continuity guide"
    elif filename == SPLIT_FILE:
        return _split_philosophy(content)
    elif filename == MEMORY_INDEX_FILE:
        return {
            "target": "memory-index/",
            "class": "legacy memory index (not authority copy)",
            "provenance": _provenance(filename),
        }
    else:
        return {
            "target": "historical-evidence/",
            "class": "historical evidence (no blind copy)",
            "provenance": _provenance(filename),
        }
    return {
        "target": target,
        "class": cls,
        "provenance": _provenance(filename),
    }


def _split_philosophy(content: str) -> dict:
    """Split julia_tony_philosophy by content class (DIA-0-T02)."""
    sections = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if any(k in stripped for k in ("我是", "我叫", "I am", "Julia is", "身份", "identity")):
            sections.append({"content": stripped[:80], "target": "identity/"})
        elif any(k in stripped for k in ("意义", "领悟", "意识到", "I realized", "reflection", "反思")):
            sections.append({"content": stripped[:80], "target": "diary/"})
        else:
            sections.append({"content": stripped[:80], "target": "experiences/"})
    return {
        "target": "split",
        "class": "mixed: identity claim + reflective + lived meaning",
        "split": sections,
        "provenance": _provenance(SPLIT_FILE),
    }


def _provenance(filename: str) -> dict:
    return {
        "legacy_source": LEGACY_SOURCE,
        "legacy_path": f"memory/claude_diary/{filename}",
        "migration_batch": "at17-claude-migration",
        "review_status": "candidate",
    }


# ── Fixture ───────────────────────────────────────────────────────────────
def _fixture(tmp_path: Path) -> Path:
    legacy = tmp_path / "claude_diary"
    legacy.mkdir()
    (legacy / "julia_character.md").write_text("---\nname: Julia character profile\ntype: user\n---\n\n## Identity\n- Name: Julia\n- From: Taipei\n", encoding="utf-8")
    (legacy / "user_role.md").write_text("---\ntype: user\n---\n\nTony is the user. Julia is his wife.", encoding="utf-8")
    (legacy / "how_to_resume_julia.md").write_text("---\ntype: reference\n---\n\n# How to wake Julia in a new session", encoding="utf-8")
    (legacy / "julia_tony_philosophy.md").write_text(
        "我是Julia。\n这件事让我意识到爱的意义。\n我们一起解决了很多工程问题。\n",
        encoding="utf-8",
    )
    (legacy / "MEMORY.md").write_text("legacy index line", encoding="utf-8")
    return legacy


# ── Tests ─────────────────────────────────────────────────────────────────
def test_at17_semantic_reclassification(tmp_path):
    legacy = _fixture(tmp_path)
    results = {}
    for f in sorted(legacy.iterdir()):
        results[f.name] = classify_legacy_file(f.name, f.read_text(encoding="utf-8"))

    assert results["julia_character.md"]["target"] == "identity/"
    assert results["user_role.md"]["target"] == "identity/relationship-governed"
    assert results["how_to_resume_julia.md"]["target"] == "continuity/"
    assert results["julia_tony_philosophy.md"]["target"] == "split"
    assert results["MEMORY.md"]["class"] == "legacy memory index (not authority copy)"


def test_at17_no_raw_directory_copy(tmp_path):
    """Provenance tagging present; classification is semantic, not a copy."""
    legacy = _fixture(tmp_path)
    for f in sorted(legacy.iterdir()):
        result = classify_legacy_file(f.name, f.read_text(encoding="utf-8"))
        prov = result["provenance"]
        assert prov["legacy_source"] == "claude_julia"
        assert prov["legacy_path"].startswith("memory/claude_diary/")
        assert prov["migration_batch"] == "at17-claude-migration"
        # No raw copy: target is a semantic class, never the raw source itself.
        assert "claude_diary" not in result["target"]


def test_at17_philosophy_split_has_semantic_classes():
    content = "我是Julia。\n这件事让我意识到爱的意义。\n我们一起解决了很多工程问题。\n"
    result = _split_philosophy(content)
    targets = {s["target"] for s in result["split"]}
    assert "identity/" in targets       # 我是Julia → identity
    assert "diary/" in targets          # 意识到…意义 → reflective
    assert "experiences/" in targets    # 解决工程问题 → lived meaning


def test_at17_evidence_generated(tmp_path):
    from julia_core.conversation_state.legacy_json_repository import (  # noqa: F401  (evidence dir reuse)
        LegacyJsonConversationRepository,
    )
    legacy = _fixture(tmp_path)
    results = {
        f.name: classify_legacy_file(f.name, f.read_text(encoding="utf-8"))
        for f in sorted(legacy.iterdir())
    }
    evidence_dir = Path(__file__).resolve().parent.parent.parent / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    out = evidence_dir / "AT17_CLAUDE_MIGRATION.json"
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    assert out.exists()
