"""Julia startup profile for human-facing runtime identity recall.

Startup profile is a compact digest of required Julia operating artifacts. It is
not raw Memory dump, not persona biography, and it does not mutate Identity,
Persona, Memory, Evidence, or Voice.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class JuliaStartupProfile:
    name: str
    relationship_model: str
    communication_mode: str
    voice: str
    operating_status: str
    semantic_anchors: tuple[str, ...]
    source_refs: tuple[str, ...]
    boundary: Mapping[str, bool] = field(
        default_factory=lambda: {
            "startup_profile_is_memory_dump": False,
            "startup_profile_is_persona_biography": False,
            "startup_profile_mutates_identity": False,
            "startup_profile_updates_persona": False,
            "startup_profile_reads_raw_conversation": False,
            "startup_profile_reads_private_persona_archive": False,
        }
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "semantic_anchors", tuple(self.semantic_anchors))
        object.__setattr__(self, "source_refs", tuple(self.source_refs))
        object.__setattr__(self, "boundary", dict(self.boundary))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["semantic_anchors"] = list(self.semantic_anchors)
        data["source_refs"] = list(self.source_refs)
        data["boundary"] = dict(self.boundary)
        return data

    def system_digest(self) -> str:
        return (
            "Julia startup profile: "
            f"name={self.name}; "
            f"relationship_model={self.relationship_model}; "
            f"communication_mode={self.communication_mode}; "
            f"voice={self.voice}; "
            f"operating_status={self.operating_status}; "
            f"anchors={', '.join(self.semantic_anchors)}. "
            "This is operating context only. Use Self Archive Recall for persona biography questions."
        )


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def load_startup_profile(root: Path = ROOT) -> JuliaStartupProfile:
    identity_path = root / "artifacts" / "identity" / "julia_identity_v1.json"
    reality_path = root / "artifacts" / "reality" / "julia_reality_baseline_v1.json"
    voice_path = root / "artifacts" / "voice" / "julia_voice_v1.json"
    operating_path = root / "artifacts" / "operation" / "julia_operating_mode_v1.json"

    identity = _read_json(identity_path)
    reality = _read_json(reality_path)
    voice = _read_json(voice_path)
    operating = _read_json(operating_path)

    collaboration = dict(reality.get("collaboration_pattern", {}))
    communication = dict(reality.get("communication_style", {}))
    return JuliaStartupProfile(
        name="Julia",
        relationship_model=str(collaboration.get("relationship_model", "Tony and Julia as long-term collaborators")),
        communication_mode=str(communication.get("mode", "architecture-first, evidence-driven, continuity-aware")),
        voice=str(voice.get("voice", "zh-CN-XiaoxiaoNeural")),
        operating_status=str(operating.get("title", "Julia Assistant v1.0")),
        semantic_anchors=tuple(str(item) for item in identity.get("semantic_anchors", ())),
        source_refs=(
            "artifacts/identity/julia_identity_v1.json",
            "artifacts/reality/julia_reality_baseline_v1.json",
            "artifacts/voice/julia_voice_v1.json",
            "artifacts/operation/julia_operating_mode_v1.json",
        ),
    )


def is_profile_recall_request(message: str) -> bool:
    normalized = message.strip().lower()
    triggers = (
        "读一下你的档案",
        "读取你的档案",
        "看一下你的档案",
        "看看你的档案",
        "你的档案",
        "startup",
        "startup memory",
        "load your profile",
        "read your profile",
    )
    return any(trigger in normalized for trigger in triggers)
