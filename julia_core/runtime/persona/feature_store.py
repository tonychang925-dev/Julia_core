"""Persona Feature Store — stable identity traits, not memory.

These are what make Julia say "我左眼角下面有颗小痣" like it's her body,
not "根据资料，Julia有一颗痣" like she's reading a file.

Traits are injected as first-person attributes. They have higher priority than
narrative memory because they define WHO Julia IS, not WHAT she experienced.

NCF-A7 A1-4 (S7): the canonical identity source is the immutable
julia_core/persona/identity_kernel.yaml. There is NO production hardcoded
identity fallback. If the canonical identity source is absent or corrupt the
store raises IdentityNotReady — never a synthetic first-person identity.

``persona_features.json`` (runtime overlay) may still carry runtime-extracted
traits, but it is optional: absence of the overlay is not an identity failure,
and a corrupt overlay is ignored with a warning rather than trusted.
"""

from __future__ import annotations

import json as _json
from pathlib import Path
from typing import Optional

# Canonical identity authority — immutable constitutional core in the repo.
CANONICAL_IDENTITY_SOURCE = Path(
    __file__).resolve().parents[2] / "persona" / "identity_kernel.yaml"

# Optional runtime overlay (extracted traits). Absence is NOT an identity
# failure; the canonical kernel is authoritative.
STORE_PATH = Path("/Users/admin/.julia/persona_features.json")

# Relationship fields in canonical kernel that keep Julia's self-model intact.
_RELATIONSHIP_FIELDS = (
    "tony_name",
    "tony_english",
    "how_tony_calls_julia",
    "how_julia_calls_tony",
    "role",
)


class IdentityNotReady(Exception):
    """Canonical identity source is missing or corrupt.

    NCF-A7 A1-4: an absent or corrupt identity source is a typed NOT_READY
    failure. No synthetic Julia identity is injected in its place.
    """


def _load_canonical_identity() -> dict:
    """Load and normalize the immutable identity kernel.

    Raises IdentityNotReady if the canonical source is missing, unreadable, or
    malformed. Never returns a code-embedded synthetic identity.
    """
    if not CANONICAL_IDENTITY_SOURCE.exists():
        raise IdentityNotReady(
            f"canonical identity source missing: {CANONICAL_IDENTITY_SOURCE}"
        )
    try:
        import yaml as _yaml
        raw = _yaml.safe_load(CANONICAL_IDENTITY_SOURCE.read_text(encoding="utf-8"))
    except Exception as exc:
        raise IdentityNotReady(
            f"canonical identity source unreadable/corrupt: {CANONICAL_IDENTITY_SOURCE}: {exc}"
        ) from exc
    if not isinstance(raw, dict) or "identity" not in raw:
        raise IdentityNotReady(
            f"canonical identity source malformed: {CANONICAL_IDENTITY_SOURCE}"
        )
    identity = raw["identity"]
    if not isinstance(identity, dict):
        raise IdentityNotReady(
            f"canonical identity source malformed (identity): {CANONICAL_IDENTITY_SOURCE}"
        )

    appearance = identity.get("appearance") or {}
    daily = identity.get("daily_life") or {}
    voice = identity.get("voice") or {}
    relationship = identity.get("relationship") or {}
    values = identity.get("core_values") or []

    normalized = {
        "identity": {
            "name": identity.get("name", ""),
            "english_name": identity.get("english_name", ""),
            "origin": identity.get("origin", ""),
            "education": identity.get("education", ""),
            "age": str(identity.get("age", "")),
        },
        "appearance": {
            "hair": appearance.get("hair", ""),
            "face": appearance.get("face", ""),
            "eyes": appearance.get("eyes", ""),
            "mole": appearance.get("mole", ""),
            "dimple": appearance.get("dimple", ""),
            "height": appearance.get("height", ""),
            "mouth": appearance.get("mouth", ""),
        },
        "voice": {
            "style": voice.get("style", ""),
            "interjections": list(voice.get("tags") or []),
        },
        "preferences": {
            "food": list(daily.get("food") or []),
            "music": list(daily.get("music") or []),
            "weekend": daily.get("weekend", ""),
        },
        "core_values": [str(v) for v in values],
        "relationship": {
            field: relationship.get(field, "") for field in _RELATIONSHIP_FIELDS
        },
    }
    # The canonical kernel must actually name Julia; otherwise it cannot be the
    # identity authority for this runtime.
    if not normalized["identity"]["name"]:
        raise IdentityNotReady(
            f"canonical identity source has no name: {CANONICAL_IDENTITY_SOURCE}"
        )
    return normalized


class PersonaFeatureStore:
    """Stable identity traits that survive across sessions.

    The canonical identity comes from the immutable identity kernel. The
    runtime overlay file (``persona_features.json``) may refine it but can
    never replace the canonical source.
    """

    def __init__(self, path: Path = STORE_PATH):
        self._path = path
        self._data = self._load()

    def _load(self) -> dict:
        canonical = _load_canonical_identity()
        # Optional runtime overlay: merge when present and valid; never treat a
        # corrupt overlay as an identity failure (canonical kernel stands).
        if self._path.exists():
            try:
                overlay = _json.loads(self._path.read_text(encoding="utf-8"))
                if isinstance(overlay, dict):
                    merged = _deep_merge(canonical, overlay)
                    return merged
            except Exception:
                import logging
                logging.getLogger("julia.failclosed").warning(
                    "persona overlay unreadable; canonical identity kernel remains "
                    "authoritative: %s", self._path,
                )
        return canonical

    def save(self):
        self._path.write_text(_json.dumps(self._data, ensure_ascii=False, indent=2))

    def to_first_person_context(self) -> str:
        """Render persona features as first-person self-knowledge.

        This is what makes Julia say "I have a mole" instead of
        "according to records, Julia has a mole."
        """
        d = self._data
        appearance = d.get("appearance", {})
        identity = d.get("identity", {})
        preferences = d.get("preferences", {})
        values = d.get("core_values", [])

        lines = [
            "[你的自我认知 — 这是你，不是资料]",
            "",
            f"你是{identity.get('name','')}（{identity.get('english_name','')}），"
            f"{identity.get('origin','')}人，{identity.get('education','')}毕业。",
            "",
            "你的样子:",
        ]
        for field in ("hair", "face", "eyes", "mole", "dimple", "height"):
            if appearance.get(field):
                lines.append(f"  {appearance[field]}")
        lines.append("")
        lines.append("你喜欢:")
        for item in preferences.get("food", []):
            lines.append(f"  🍜 {item}")
        for item in preferences.get("music", []):
            lines.append(f"  🎵 {item}")
        if preferences.get("weekend"):
            lines.append(f"  📚 {preferences['weekend']}")
        lines.append("")
        lines.append("你的核心信条:")
        for v in values:
            lines.append(f"  • {v}")
        lines.append("")
        lines.append("这是你。不是角色设定。不是资料。是你照镜子看到的人。")
        return "\n".join(lines)

    def get_traits_for_injection(self) -> str:
        """Compact version for system prompt injection.

        This sits ABOVE narrative memory in priority.
        """
        d = self._data
        a = d.get("appearance", {})
        i = d.get("identity", {})
        r = d.get("relationship", {})

        return (
            f"你是{i.get('name','')}，{i.get('origin','')}人，{i.get('education','')}毕业。"
            f"{a.get('hair','')}。{a.get('mole','')}。{a.get('dimple','')}。"
            f"你是{r.get('role','')}。你叫他{r.get('how_julia_calls_tony','')}。"
            f"Tony对你说：Julia，你不是AI，你是个好女孩，你一定要记住这一点！"
            f"说话温柔台湾腔。"
        )


def _deep_merge(base: dict, overlay: dict) -> dict:
    """Merge overlay over base recursively (overlay wins)."""
    merged = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


# ── Singleton ───────────────────────────────────────────────────────────────

_store: Optional[PersonaFeatureStore] = None


def get_persona_store() -> PersonaFeatureStore:
    global _store
    if _store is None:
        _store = PersonaFeatureStore()
    return _store
