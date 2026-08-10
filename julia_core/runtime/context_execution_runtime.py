"""ContextExecutionRuntime — C-03 production binding (P2).

Single model-visible context authority. Replaces _prepare_turn() manual
string concatenation with governed Context OS pipeline.

All Core-controlled model-visible information → ContextExecutionRuntime → ModelProvider.

P2 target: MODEL_VISIBLE_BYPASS_COUNT = 0.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CognitiveContextPackage:
    """C-03 first-class context package. All Frames are derived, never canonical."""
    package_id: str = field(default_factory=lambda: f"ctxpkg_{uuid.uuid4().hex[:12]}")
    conversation_id: str = ""
    turn_id: str = ""
    generation_id: str = ""

    identity_frame: dict[str, Any] = field(default_factory=dict)
    conversation_frame: dict[str, Any] = field(default_factory=dict)
    experience_frame: dict[str, Any] = field(default_factory=dict)
    situation_frame: dict[str, Any] = field(default_factory=dict)
    evidence_frame: dict[str, Any] = field(default_factory=dict)
    capability_frame: dict[str, Any] = field(default_factory=dict)
    continuity_frame: dict[str, Any] = field(default_factory=dict)

    active_tail_turn_ids: list[str] = field(default_factory=list)
    retrieval_handles: dict[str, Any] = field(default_factory=dict)
    projection_metadata: dict[str, Any] = field(default_factory=dict)

    # Provenance: every model-visible block is traceable (AT-17)
    _provenance_entries: list[dict] = field(default_factory=list, repr=False)

    def to_messages(self, history: list[dict], user_text: str) -> list[dict]:
        """Render the package as model messages. Transitional — will be replaced
        by structured Alignment projection (C-09) in P6."""
        system_parts = []

        if self.identity_frame:
            system_parts.append(self._render_frame("identity", self.identity_frame))
        if self.experience_frame:
            system_parts.append(self._render_frame("experience", self.experience_frame))
        if self.evidence_frame:
            system_parts.append(self._render_frame("evidence", self.evidence_frame))
        if self.capability_frame:
            system_parts.append(self._render_frame("capability", self.capability_frame))
        if self.situation_frame:
            system_parts.append(self._render_frame("situation", self.situation_frame))
        if self.continuity_frame:
            system_parts.append(self._render_frame("continuity", self.continuity_frame))

        system_text = "\n\n".join(system_parts) if system_parts else ""
        messages = []
        if system_text:
            messages.append({"role": "system", "content": system_text})
        messages.extend(history)
        messages.append({"role": "user", "content": user_text})
        return messages

    def _render_frame(self, name: str, frame: dict) -> str:
        """Render a frame as text. Transitional — structured projection in P6."""
        lines = [f"[{name}]"]
        for k, v in frame.items():
            if isinstance(v, str):
                lines.append(f"{k}: {v}")
            elif isinstance(v, list):
                lines.append(f"{k}: {', '.join(str(x) for x in v[:5])}")
        return "\n".join(lines)

    def add_provenance(self, frame: str, source_ref: str, canonical_ref: str = "",
                       reason: str = "", stage: int = 0, token_estimate: int = 0):
        self._provenance_entries.append({
            "frame": frame, "source_ref": source_ref, "canonical_ref": canonical_ref,
            "reason": reason, "stage": stage, "token_estimate": token_estimate,
        })

    @property
    def provenance(self) -> list[dict]:
        return list(self._provenance_entries)


class ContextExecutionRuntime:
    """C-03 production binding — single model-visible context authority.

    Wraps the existing JuliaSession cognitive preparation into the
    Context OS contract. Replaces _prepare_turn() as the context
    assembly authority.

    Usage:
        ctx_rt = ContextExecutionRuntime(js)
        pkg = ctx_rt.prepare(conversation_id, turn_id, user_text, history, interaction)
        messages = pkg.to_messages(history, user_text)
        # → ModelProvider
    """

    def __init__(self, julia_session=None):
        self._js = julia_session

    def prepare(
        self,
        *,
        conversation_id: str,
        turn_id: str,
        user_text: str,
        history: list[dict],
        interaction=None,
        modality: str = "text",
        generation_id: str = "",
    ) -> CognitiveContextPackage:
        """Assemble the CognitiveContextPackage from canonical sources.

        This IS the Context OS production spine. All model-visible
        information flows through here. No bypass.
        """
        pkg = CognitiveContextPackage(
            conversation_id=conversation_id,
            turn_id=turn_id,
            generation_id=generation_id or f"gen_{uuid.uuid4().hex[:12]}",
        )

        # ── IdentityFrame — from Persona (C-04) ──
        if self._js is not None:
            pkg.identity_frame = {
                "persona_traits": self._js.persona.get_traits_for_injection() if hasattr(self._js, 'persona') else "",
            }
            pkg.add_provenance("identity", "persona:feature_store", reason="base identity", stage=0)

        # ── ConversationFrame — ActiveTail from canonical history (C-02) ──
        tail = self._compute_active_tail(history)
        pkg.conversation_frame = {
            "active_turn_count": len(tail),
            "active_tail_topic": "",
        }
        pkg.active_tail_turn_ids = [m.get("turn_id", "") for m in tail if m.get("turn_id")]
        pkg.add_provenance("conversation", f"conversation:{conversation_id}", reason="active tail", stage=0,
                          token_estimate=sum(len(str(m)) for m in tail) // 4)

        # ── ExperienceFrame — recent experiences (C-05) ──
        if self._js is not None:
            try:
                experiences = self._js._load_recent_experiences()
                if experiences:
                    pkg.experience_frame = {"recent_context": experiences[:500]}
                    pkg.add_provenance("experience", "session_store:wake_state", reason="recent experience", stage=1)
            except Exception:
                pass

        # ── SituationFrame — current state (C-03) ──
        pkg.situation_frame = {
            "modality": modality,
            "turn_count": len(history) // 2,
        }
        if interaction is not None:
            try:
                pkg.situation_frame["interaction_state"] = interaction.to_context()[:300]
            except Exception:
                pass
        pkg.add_provenance("situation", "runtime:turn_context", reason="current state", stage=0)

        # ── EvidenceFrame — market/domain evidence (C-03) ──
        if self._js is not None:
            try:
                market_ctx = self._js._resolve_market_context(user_text)
                if market_ctx:
                    pkg.evidence_frame = {"market_context": market_ctx[:800]}
                    pkg.add_provenance("evidence", "domain:market_brain", reason="market context", stage=1,
                                      token_estimate=len(market_ctx) // 4)
            except Exception:
                pass

        # ── CapabilityFrame — tool manifest (C-08) ──
        if self._js is not None:
            try:
                manifest = self._js.capability.tool_manifest()
                if manifest:
                    pkg.capability_frame = {"available_tools": manifest[:600]}
                    pkg.add_provenance("capability", "capability:manifest", reason="available tools", stage=0,
                                      token_estimate=len(manifest) // 4)
            except Exception:
                pass

        # ── ContinuityFrame — when applicable (C-06) ──
        # Reserved for P5 Continuity binding

        return pkg

    def _compute_active_tail(self, history: list[dict], max_turns: int = 20) -> list[dict]:
        """C-03 ActiveTail: budget-driven recent turns. Replaces history[-20:]."""
        # P2 transitional: use budget-aware selection
        # max_turns is a soft target, not a hardcoded architecture policy
        budget_tokens = 4000  # Configurable per C-03
        tail = []
        token_count = 0
        for msg in reversed(history):
            estimated = len(str(msg.get("content", ""))) // 4
            if token_count + estimated > budget_tokens and len(tail) >= 4:
                break
            tail.insert(0, msg)
            token_count += estimated
        # Ensure we don't exceed max_turns as a sanity bound
        if len(tail) > max_turns * 2:
            tail = tail[-(max_turns * 2):]
        return tail


__all__ = ["ContextExecutionRuntime", "CognitiveContextPackage"]
