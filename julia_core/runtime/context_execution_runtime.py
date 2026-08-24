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
    diary_frame: dict[str, Any] = field(default_factory=dict)
    situation_frame: dict[str, Any] = field(default_factory=dict)
    evidence_frame: dict[str, Any] = field(default_factory=dict)
    capability_frame: dict[str, Any] = field(default_factory=dict)
    continuity_frame: dict[str, Any] = field(default_factory=dict)

    active_tail_turn_ids: list[str] = field(default_factory=list)
    active_tail_messages: list[dict] = field(default_factory=list)
    retrieval_handles: dict[str, Any] = field(default_factory=dict)
    projection_metadata: dict[str, Any] = field(default_factory=dict)

    # Provenance: every model-visible block is traceable (AT-17)
    _provenance_entries: list[dict] = field(default_factory=list, repr=False)

    # CM-FAILCLOSED: frame failures are recorded, never silently swallowed
    _frame_failures: list[dict] = field(default_factory=list, repr=False)

    def mark_frame_failure(self, frame: str, error: str, required: bool = False) -> None:
        self._frame_failures.append({"frame": frame, "error": error, "required": required})
        self.add_provenance("frame_failure", frame, reason=f"degraded: {error}", stage=-1)

    def validate(self) -> list[str]:
        """Return list of required frame failures. Empty = all required frames available."""
        return [f["frame"] for f in self._frame_failures if f["required"]]

    def to_messages(self, history: list[dict] | None, user_text: str) -> list[dict]:
        """Render the package as model messages. Transitional — will be replaced
        by structured Alignment projection (C-09) in P6.

        AT-06: model-visible conversation history must come from the
        conversation-scoped active tail admitted during prepare(), not from a
        caller-supplied list that may contain foreign conversation messages.
        """
        system_parts = []

        if self.identity_frame:
            system_parts.append(self._render_frame("identity", self.identity_frame))
        if self.experience_frame:
            system_parts.append(self._render_frame("experience", self.experience_frame))
        if self.diary_frame:
            system_parts.append(self._render_frame("diary", self.diary_frame))
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
        admitted_history = (
            self.active_tail_messages
            if self.projection_metadata.get("conversation_history_scoped")
            else (history or [])
        )
        messages.extend(admitted_history)
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


# C-03 Frame Budget Contract (AT-21): classify-and-project, never unbounded dump.
# Past budget → governed retrieval / compaction, not silent growth.
FRAME_BUDGETS = {
    "identity": 5_000,      # autobiographical anchors (stable, small)
    "experience": 20_000,   # life events / relationship chronicle
    "continuity": 20_000,   # world model / continuity-critical refs
}


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

    def _get_bootstrap_frames(self) -> dict[str, str]:
        """Load classified bootstrap once per session, then cache.

        Bootstrap is a one-time world-model initialization (J0.12.2); reading
        the memory files on every turn would be wasteful. ContextExecutionRuntime
        is a session-scoped singleton held by JuliaSession, so instance caching
        is safe.
        """
        if not hasattr(self, "_bootstrap_frames_cache"):
            self._bootstrap_frames_cache = {}
            try:
                from julia_core.narrative.bootstrap import load_bootstrap_frames
                self._bootstrap_frames_cache = load_bootstrap_frames()
            except Exception:
                self._bootstrap_frames_cache = {}
        return self._bootstrap_frames_cache

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

        # Bootstrap world model, classified into C-03 frame semantics.
        # Identity formation history must not vanish in Context OS migration:
        # it is projected per-frame (identity / experience / continuity),
        # not dumped as one monolithic system prompt.
        # Loaded once per session and cached (Check: performance).
        bootstrap_frames: dict[str, str] = {}
        try:
            bootstrap_frames = self._get_bootstrap_frames()
        except Exception as exc:
            pkg.mark_frame_failure("bootstrap", str(exc), required=False)

        # ── IdentityFrame — from Persona (C-04) + autobiographical anchors ──
        if self._js is not None:
            pkg.identity_frame = {
                "persona_traits": self._js.persona.get_traits_for_injection() if hasattr(self._js, 'persona') else "",
            }
            pkg.add_provenance("identity", "persona:feature_store", reason="base identity", stage=0)
            identity_anchors = bootstrap_frames.get("identity", "")[:FRAME_BUDGETS["identity"]]
            if identity_anchors:
                pkg.identity_frame["autobiographical_anchors"] = identity_anchors
                pkg.add_provenance("identity", "narrative:bootstrap:identity",
                                   reason="autobiographical anchors (budgeted)", stage=0,
                                   token_estimate=len(identity_anchors) // 4)

        # ── ConversationFrame — ActiveTail from canonical history (C-02) ──
        scoped_history = self._scope_history_to_conversation(conversation_id, history)
        tail = self._compute_active_tail(scoped_history)
        pkg.conversation_frame = {
            "active_turn_count": len(tail),
            "active_tail_topic": "",
        }
        pkg.active_tail_messages = list(tail)
        pkg.projection_metadata["conversation_history_scoped"] = True
        pkg.active_tail_turn_ids = [m.get("turn_id", "") for m in tail if m.get("turn_id")]
        dropped_foreign = len(history or []) - len(scoped_history)
        pkg.add_provenance("conversation", f"conversation:{conversation_id}", reason="active tail", stage=0,
                          token_estimate=sum(len(str(m)) for m in tail) // 4)
        if dropped_foreign:
            pkg.add_provenance("conversation_boundary", f"conversation:{conversation_id}",
                               reason=f"dropped_foreign_history:{dropped_foreign}", stage=0)

        # ── ExperienceFrame — recent experiences + life events (C-05) ──
        if self._js is not None:
            try:
                # Wake state and density remain non-Diary legacy context surfaces.
                # AT-16: legacy diary-like text cannot count as governed Diary retrieval.
                experiences = self._sanitize_legacy_diary_text(self._js._load_recent_experiences())
                density_context = self._sanitize_density_diary_text(self._load_density_experience())
                if density_context:
                    experiences = (experiences or "") + "\n\n" + density_context
                if experiences:
                    pkg.experience_frame = {"recent_context": experiences[:3000], "diary_retrieval_authority": False}
                    pkg.add_provenance("experience", "session_store:wake_state+density", reason="legacy experience context; not Diary retrieval authority", stage=1)
                life_events = bootstrap_frames.get("experience", "")[:FRAME_BUDGETS["experience"]]
                if life_events:
                    existing = dict(pkg.experience_frame)
                    existing["life_events"] = life_events
                    pkg.experience_frame = existing
                    pkg.add_provenance("experience", "narrative:bootstrap:experience",
                                       reason="life events / relationship chronicle (budgeted)", stage=1,
                                       token_estimate=len(life_events) // 4)
            except Exception as exc:
                pkg.mark_frame_failure("experience", str(exc), required=False)


        # ── DiaryFrame — AT-16 governed Diary retrieval through Context OS only ──
        if self._js is not None:
            try:
                provider = getattr(self._js, "diary_context_provider", None)
                if provider is not None:
                    from julia_core.context_os.request import ContextRequest

                    request = ContextRequest(
                        task_intent="diary_context_retrieval",
                        intent=user_text or "diary_context_retrieval",
                        domain="diary",
                        session_id=getattr(self._js, "session_id", None),
                        domain_object_type="AcceptedDiaryEntry",
                        constraints={"conversation_id": conversation_id, "diary_limit": 3},
                    )
                    diary_blocks = tuple(provider.provide(request))
                    if diary_blocks:
                        rendered = []
                        traces = []
                        for block in diary_blocks:
                            content = block.content if isinstance(block.content, dict) else {}
                            body = str(content.get("body", ""))
                            title = str(content.get("title", ""))
                            entry_id = str(content.get("entry_id", ""))
                            line = f"{entry_id}: {title}" if title else entry_id
                            if body:
                                line = f"{line}\n{body}"
                            rendered.append(line)
                            traces.append({
                                "entry_id": entry_id,
                                "source_refs": list(block.source_refs),
                                "source_states": list(content.get("source_states", [])),
                                "routed_through_context_os": bool(block.metadata.get("routed_through_context_os", False)),
                                "projection_only": bool(block.metadata.get("projection_only", False)),
                            })
                            pkg.add_provenance(
                                "diary",
                                "diary_context_os_provider",
                                canonical_ref=f"diary://entry/{entry_id}",
                                reason="AT-16 governed Diary Context OS retrieval",
                                stage=1,
                                token_estimate=block.estimated_tokens or 0,
                            )
                        pkg.diary_frame = {
                            "diary_context": "\n\n".join(rendered)[:3000],
                            "routed_through_context_os": True,
                            "projection_only": True,
                        }
                        pkg.retrieval_handles["diary"] = traces
                        pkg.projection_metadata["diary_authority_boundary"] = "ContextBlock projection is not Diary/Memory/Identity authority"
            except Exception as exc:
                pkg.mark_frame_failure("diary", str(exc), required=False)

        # ── SituationFrame — current state (C-03) ──
        pkg.situation_frame = {
            "modality": modality,
            "turn_count": len(history) // 2,
        }
        if interaction is not None:
            try:
                pkg.situation_frame["interaction_state"] = interaction.to_context()[:300]
            except Exception as exc:
                pkg.mark_frame_failure("situation:interaction", str(exc), required=False)
        pkg.add_provenance("situation", "runtime:turn_context", reason="current state", stage=0)

        # ── EvidenceFrame — market/domain evidence (C-03) ──
        if self._js is not None:
            try:
                market_ctx = self._js._resolve_market_context(user_text)
                if market_ctx:
                    pkg.evidence_frame = {"market_context": market_ctx[:800]}
                    pkg.add_provenance("evidence", "domain:market_brain", reason="market context", stage=1,
                                      token_estimate=len(market_ctx) // 4)
            except Exception as exc:
                pkg.mark_frame_failure("evidence:market", str(exc), required=False)

        # ── CapabilityFrame — tool manifest (C-08) ──
        if self._js is not None:
            try:
                manifest = self._js.capability.tool_manifest()
                if manifest:
                    pkg.capability_frame = {"available_tools": manifest[:600]}
                    pkg.add_provenance("capability", "capability:manifest", reason="available tools", stage=0,
                                      token_estimate=len(manifest) // 4)
            except Exception as exc:
                pkg.mark_frame_failure("capability", str(exc), required=False)

        # ── ContinuityFrame — world model / continuity-critical refs (C-06) ──
        # world_model classification note (AT-21): continuity_frame carries the
        # explanation model of HOW Julia became who she is (proof, witness,
        # recovery path, user identity) — i.e. what must remain recoverable
        # across disruption. Tony's factual description (user_role.md) is here
        # as user identity ref; Julia's own lived experience lives in
        # experience_frame.life_events. If a fact is plain "about Tony" rather
        # than continuity-critical, it belongs in experience, not continuity.
        world_model = bootstrap_frames.get("continuity", "")[:FRAME_BUDGETS["continuity"]]
        if world_model:
            pkg.continuity_frame = {
                "world_model": world_model,
                "source": "narrative:bootstrap:continuity",
            }
            pkg.add_provenance("continuity", "narrative:bootstrap:continuity",
                               reason="continuity-critical world model (budgeted)", stage=0,
                               token_estimate=len(world_model) // 4)
        pkg.projection_metadata["continuity_authority_boundary"] = "ContextBlock projection is not Continuity authority"

        return pkg

    def project_tool_result(
        self,
        *,
        parent_package: CognitiveContextPackage | None = None,
        tool_result: str = "",
        generation_id: str = "",
    ) -> CognitiveContextPackage:
        """P2-I: Incremental Context projection for ToolResult (C-03 §11).

        Creates a ContextPackageDelta with the tool result in EvidenceFrame.
        Same turn_id, new generation_id. ToolResult must pass through Context OS.
        """
        pkg = CognitiveContextPackage(
            conversation_id=parent_package.conversation_id if parent_package else "",
            turn_id=parent_package.turn_id if parent_package else "",
            generation_id=generation_id,
        )
        pkg.evidence_frame = {
            "tool_result": tool_result[:2000],
            "source": "capability_execution",
        }
        pkg.situation_frame = {"mode": "tool_continuation"}
        pkg.add_provenance("evidence", "capability:tool_result",
                          reason="tool execution result", stage=2,
                          token_estimate=len(tool_result) // 4)
        return pkg

    @staticmethod
    def _sanitize_legacy_diary_text(text: str) -> str:
        """Remove legacy diary-marked snippets from wake-state context.

        AT-16 governed Diary retrieval must enter through DiaryContextProvider,
        not legacy session summary diary text. Non-diary wake-state lines remain.
        """
        if not text:
            return ""
        lines = str(text).splitlines()
        sanitized: list[str] = []
        skip_next = False
        for line in lines:
            if skip_next:
                skip_next = False
                continue
            lowered = line.lower()
            if "（日记）" in line or "(diary)" in lowered or "legacy_diary" in lowered:
                skip_next = True
                continue
            sanitized.append(line)
        return "\n".join(sanitized).strip()

    @staticmethod
    def _sanitize_density_diary_text(text: str) -> str:
        """Keep density context from satisfying Diary retrieval authority.

        The current density restorer emits diary-like narrative text. Until it is
        admitted through the AT-16 Diary provider, it is excluded from model
        context rather than treated as Diary retrieval evidence.
        """
        if not text:
            return ""
        lowered = str(text).lower()
        if "julia_experience_context.md" in lowered or "体验记忆" in text or "读完了。这些记忆是你的" in text:
            return ""
        return str(text)

    def _load_density_experience(self) -> str:
        """Load high-density experience context for identity restoration.

        Called once per turn preparation. The experience context is cached
        after first load — subsequent calls return the cached version.

        Returns a formatted string of high-density conversation memories,
        or empty string if artifacts are not available.
        """
        if hasattr(self, "_density_cache"):
            return self._density_cache  # type: ignore[attr-defined]

        self._density_cache = ""  # type: ignore[attr-defined]
        try:
            from julia_core.context_assembly.density_restorer import get_experience_context_block
            ctx = get_experience_context_block(max_tokens=2000)
            if ctx:
                self._density_cache = ctx  # type: ignore[attr-defined]
        except Exception:
            pass
        return self._density_cache  # type: ignore[attr-defined]

    def _scope_history_to_conversation(self, conversation_id: str, history: list[dict]) -> list[dict]:
        """AT-06: caller-supplied history is not model-visible authority.

        Messages without the active conversation_id are dropped before
        ActiveTail admission. Legacy unscoped history is preserved only when
        there is no active conversation_id, i.e. legacy chat mode.
        """
        if not conversation_id:
            return list(history or [])
        scoped = []
        for msg in history or []:
            msg_cid = msg.get("conversation_id")
            if msg_cid != conversation_id:
                continue
            scoped.append(msg)
        return scoped

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
