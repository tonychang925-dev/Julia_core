"""ContextExecutionRuntime — C-03 production binding (P2).

Single model-visible context authority. Replaces _prepare_turn() manual
string concatenation with governed Context OS pipeline.

All Core-controlled model-visible information → ContextExecutionRuntime → ModelProvider.

P2 target: MODEL_VISIBLE_BYPASS_COUNT = 0.
"""

from __future__ import annotations

import copy
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Sequence

from julia_core.capability.models import CapabilityStatus, Evidence, ToolResult
from julia_core.capability.policy import AuthorizationDecision, AuthorizationStatus


class ContextNotReady(Exception):
    """Raised when a CognitiveContextPackage has unsatisfied required frames.

    Critical identity/continuity context failure must NOT proceed to model
    cognition. No fallback, no empty-context continuation, no synthetic text.
    """


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
    validated_invocation_policy: dict[str, Any] = field(default_factory=dict)
    control_frame: dict[str, Any] = field(default_factory=dict)
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
        if self.control_frame:
            system_parts.append(self._render_frame("control", self.control_frame))
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
        if self.turn_id:
            admitted_history = [
                message
                for message in admitted_history
                if not (
                    message.get("role") == "user"
                    and message.get("turn_id") == self.turn_id
                )
            ]
        messages.extend(admitted_history)
        messages.append({"role": "user", "content": user_text})
        return messages

    def _render_frame(self, name: str, frame: dict) -> str:
        """Render one frame without dropping an oversized structured value.

        The structured Context OS projection stays complete. Rendering applies a
        model-visible character budget recursively so a large first value (for
        example a tool payload) cannot cause the entire evidence item to vanish.
        The renderer is domain-agnostic: it does not know or prioritize Market,
        Research, or any provider-specific semantic field.
        """
        lines = [f"[{name}]"]
        total = len(lines[0])
        budget = self._RENDER_MAX_FRAME_CHARS
        for key, value in frame.items():
            prefix = f"{key}: "
            remaining = budget - total - len(prefix) - 1
            if remaining <= len(self._RENDER_TRUNC_MARKER):
                lines.append(self._RENDER_TRUNC_MARKER + f"[frame budget {budget} chars]")
                break
            rendered = self._render_value(value, depth=0, char_budget=remaining)
            line = prefix + rendered
            lines.append(line)
            total += len(line) + 1
            if total >= budget:
                break
        return "\n".join(lines)

    _RENDER_MAX_SCALAR = 2000
    _RENDER_MAX_ITEMS = 20
    _RENDER_MAX_DEPTH = 4
    _RENDER_MAX_FRAME_CHARS = 8000
    _RENDER_TRUNC_MARKER = "…[truncated]"

    def _render_value(self, value: Any, *, depth: int, char_budget: int | None = None) -> str:
        """Deterministically render a nested value inside an explicit budget.

        Container budgets are shared across their children rather than rendering
        an unbounded child first and discarding the whole parent afterwards.
        Mappings retain stable sorted-key order. Truncation changes only the
        rendered view; the structured Context OS projection remains untouched.
        """
        budget = self._RENDER_MAX_FRAME_CHARS if char_budget is None else max(char_budget, 0)
        marker = self._RENDER_TRUNC_MARKER

        def bounded_scalar(text: str, limit: int) -> str:
            scalar_limit = min(self._RENDER_MAX_SCALAR, max(limit, 0))
            if len(text) <= scalar_limit:
                return text
            if scalar_limit <= len(marker):
                return marker[:scalar_limit]
            return text[: scalar_limit - len(marker)] + marker

        if isinstance(value, str):
            return bounded_scalar(value, budget)

        if isinstance(value, dict):
            if depth >= self._RENDER_MAX_DEPTH:
                compact = "{…}" + marker
                return compact if len(compact) <= budget else compact[:budget]
            items = sorted(value.items(), key=lambda item: str(item[0]))
            if budget <= 4:
                return "{}"[:budget]
            remaining = budget - 4  # "{ " + " }"
            parts: list[str] = []
            truncated = False
            for index, (key, child) in enumerate(items):
                separator = ", " if parts else ""
                key_prefix = f"{key}="
                if remaining <= len(separator) + len(key_prefix):
                    truncated = True
                    break
                remaining_items = max(len(items) - index, 1)
                fair_share = max(
                    1,
                    (remaining - len(separator) - len(key_prefix)) // remaining_items,
                )
                child_text = self._render_value(
                    child,
                    depth=depth + 1,
                    char_budget=fair_share,
                )
                part = separator + key_prefix + child_text
                if len(part) > remaining:
                    truncated = True
                    break
                parts.append(part)
                remaining -= len(part)
                if marker in child_text:
                    truncated = True
            if len(parts) < len(items):
                truncated = True
            body = "".join(parts)
            if truncated:
                note = (", " if body else "") + marker
                if len(note) <= remaining:
                    body += note
            return "{ " + body + " }"

        if isinstance(value, (list, tuple)):
            if depth >= self._RENDER_MAX_DEPTH:
                compact = "[…]" + marker
                return compact if len(compact) <= budget else compact[:budget]

            total_items = len(value)
            visible_items = value[: self._RENDER_MAX_ITEMS]
            if budget <= 2:
                return "[]"[:budget]

            remaining = budget - 2
            omitted_count = total_items - len(visible_items)
            omission_note = marker + (f"[{omitted_count} more]" if omitted_count else "")

            # Always reserve enough space for an explicit container-level
            # truncation marker before allocating child budgets. This prevents
            # a bounded prefix from looking like a complete list when tail
            # items were omitted or rendering stopped early.
            note_reserve = min(remaining, len(omission_note) + 2)
            content_remaining = max(0, remaining - note_reserve)

            parts: list[str] = []
            stopped_early = False
            for index, child in enumerate(visible_items):
                separator = ", " if parts else ""
                if content_remaining <= len(separator):
                    stopped_early = True
                    break
                remaining_items = max(len(visible_items) - index, 1)
                fair_share = max(
                    1,
                    (content_remaining - len(separator)) // remaining_items,
                )
                child_text = self._render_value(
                    child,
                    depth=depth + 1,
                    char_budget=fair_share,
                )
                part = separator + child_text
                if len(part) > content_remaining:
                    stopped_early = True
                    break
                parts.append(part)
                content_remaining -= len(part)

            if len(parts) < len(visible_items):
                stopped_early = True

            body = "".join(parts)
            if omitted_count or stopped_early:
                note = (", " if body else "") + omission_note
                available = remaining - len(body)
                if len(note) <= available:
                    body += note
                else:
                    # Extreme tiny-budget case: prefer an explicit truncation
                    # signal over a normal-looking but incomplete prefix.
                    body = bounded_scalar(omission_note, remaining)

            return "[" + body + "]"

        return bounded_scalar(str(value), budget)

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

    @staticmethod
    def _invocation_policy_failure(policy: Any) -> str | None:
        if not isinstance(policy, dict):
            return "invocation policy must be a structured mapping"
        for section in ("invocation_protocol", "epistemic_rules", "evidence_role", "limits"):
            if not isinstance(policy.get(section), dict):
                return f"invocation policy section '{section}' must be a mapping"
        protocol = policy["invocation_protocol"]
        if not isinstance(protocol.get("format"), str) or not protocol["format"].strip():
            return "invocation protocol format must be a non-empty string"
        if protocol.get("structured_call_required") is not True:
            return "structured_call_required must be True"
        if protocol.get("raw_user_text_routing") is not False:
            return "raw_user_text_routing must be False"
        exact_transport_fields = (
            ("whole_response_must_be_tool_call", True),
            ("surrounding_prose_allowed", False),
            ("multiple_tool_call_fences_allowed", False),
        )
        for field_name, expected_value in exact_transport_fields:
            if protocol.get(field_name) is not expected_value:
                return (
                    "invocation protocol "
                    f"{field_name} must be {expected_value}"
                )
        transport_rule = protocol.get("response_transport_rule")
        if not isinstance(transport_rule, str) or not transport_rule.strip():
            return "invocation protocol response_transport_rule must be a non-empty string"
        request_envelope = protocol.get("request_envelope")
        if not isinstance(request_envelope, dict):
            return "invocation protocol request_envelope must be a mapping"
        for field in ("name", "arguments"):
            semantics = request_envelope.get(field)
            if not isinstance(semantics, str) or not semantics.strip():
                return (
                    "invocation protocol request_envelope."
                    f"{field} semantics must be a non-empty string"
                )
        epistemic_rules = policy["epistemic_rules"]
        file_rule = epistemic_rules.get("file")
        if not isinstance(file_rule, dict):
            return "epistemic_rules.file must be a mapping"
        if file_rule.get("capability_prefix") != "file.*":
            return "file capability_prefix must be 'file.*'"
        if file_rule.get("requires_explicit_user_intent") is not True:
            return "file requires_explicit_user_intent must be True"
        external_rule = epistemic_rules.get("external_evidence")
        if not isinstance(external_rule, dict):
            return "epistemic_rules.external_evidence must be a mapping"
        prefixes = external_rule.get("capability_prefixes")
        if (
            not isinstance(prefixes, list)
            or not all(isinstance(prefix, str) and prefix.strip() for prefix in prefixes)
            or "market.*" not in prefixes
            or "research.*" not in prefixes
            or any(prefix == "file.*" or prefix.startswith("file.") for prefix in prefixes)
        ):
            return "external evidence capability_prefixes must include market.* and research.* without file namespaces"
        if external_rule.get("read_only") is not True:
            return "external evidence read_only must be True"
        if external_rule.get("julia_may_request_when_evidence_missing") is not True:
            return "julia_may_request_when_evidence_missing must be True"
        if external_rule.get("explicit_user_request_requires_execution") is not True:
            return "explicit_user_request_requires_execution must be True"
        explicit_request_rule = external_rule.get("explicit_request_rule")
        if not isinstance(explicit_request_rule, str) or not explicit_request_rule.strip():
            return "external evidence explicit_request_rule must be a non-empty string"
        evidence_role = policy["evidence_role"]
        if evidence_role.get("tool_result_is_evidence_not_final_judgment") is not True:
            return "tool_result_is_evidence_not_final_judgment must be True"
        if evidence_role.get("julia_second_pass_interpretation_required") is not True:
            return "julia_second_pass_interpretation_required must be True"
        if policy["limits"].get("max_tool_calls_per_model_response") != 1:
            return "max_tool_calls_per_model_response must be 1"
        return None

    def _get_bootstrap_frames(self) -> dict[str, str]:
        """Load classified bootstrap once per session, then cache.

        Bootstrap is a one-time world-model initialization (J0.12.2); reading
        the memory files on every turn would be wasteful. ContextExecutionRuntime
        is a session-scoped singleton held by JuliaSession, so instance caching
        is safe.
        """
        if not hasattr(self, "_bootstrap_frames_cache"):
            from julia_core.narrative.bootstrap import load_bootstrap_frames
            # May raise BootstrapNotReady on missing critical inputs. Do NOT
            # cache failure as empty success — propagate for prepare() to record.
            self._bootstrap_frames_cache = load_bootstrap_frames()
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
            # Bootstrap is identity/continuity-critical: missing world-model
            # material must be observable, not silently optional.
            pkg.mark_frame_failure("bootstrap", str(exc), required=True)

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
            # Wake state (recent experiences) — explicit degradation, not silent.
            try:
                experiences = self._sanitize_legacy_diary_text(self._js._load_recent_experiences())
            except Exception as exc:
                pkg.mark_frame_failure("experience", str(exc), required=False)
                experiences = ""
            # Density (non-authority legacy context) — distinguish NO DATA from
            # LOAD ERROR; a load error is recorded explicitly, not swallowed.
            try:
                density_context = self._sanitize_density_diary_text(self._load_density_experience())
            except Exception as exc:
                pkg.mark_frame_failure("experience:density", str(exc), required=False)
                density_context = ""
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

        self._project_current_turn_temporal_context(
            pkg,
            conversation_id=conversation_id,
            turn_id=turn_id,
            scoped_history=scoped_history,
        )

        # EvidenceFrame is populated only by typed capability execution below.
        # Raw conversational text must not create pre-cognition Market evidence.

        # ── CapabilityFrame — structured registry catalog (C-08) ──
        # `available_tools` is the structured advertised/registered capability
        # catalog for this Context OS path. It is NOT authoritative proof that
        # every entry is executable at this instant; execution availability is
        # governed later by authorization, provider readiness, and lifecycle.
        if self._js is not None:
            try:
                definitions = [
                    definition
                    for definition in self._js.capability.registry.all()
                    if definition.status == CapabilityStatus.AVAILABLE
                ]
                entries = sorted(
                    (
                        {
                            "capability_id": d.name,
                            "description": d.description,
                            "input_schema": copy.deepcopy(d.input_schema),
                        }
                        for d in definitions
                    ),
                    key=lambda entry: entry["capability_id"],
                )
                if entries:
                    capability_frame: dict[str, Any] = {}
                    policy_provider = getattr(
                        self._js.capability,
                        "invocation_policy",
                        None,
                    )
                    invocation_policy = None
                    if not callable(policy_provider):
                        pkg.mark_frame_failure(
                            "capability:invocation_policy",
                            "capability runtime does not expose invocation_policy",
                            required=True,
                        )
                    else:
                        try:
                            invocation_policy = policy_provider()
                        except Exception as exc:
                            pkg.mark_frame_failure(
                                "capability:invocation_policy",
                                f"invocation policy failed: {exc}",
                                required=True,
                            )
                        else:
                            policy_failure = self._invocation_policy_failure(
                                invocation_policy
                            )
                            if policy_failure is not None:
                                pkg.mark_frame_failure(
                                    "capability:invocation_policy",
                                policy_failure,
                                required=True,
                            )
                            else:
                                capability_frame["invocation_policy"] = copy.deepcopy(
                                    invocation_policy
                                )
                                pkg.validated_invocation_policy = copy.deepcopy(invocation_policy)
                    capability_frame["available_tools"] = entries
                    pkg.capability_frame = capability_frame
                    pkg.add_provenance("capability", "capability:registry",
                                      reason="structured capability catalog", stage=0,
                                      token_estimate=len(entries))
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
        tool_result: ToolResult,
        evidence: Sequence[Evidence] = (),
        generation_id: str = "",
    ) -> CognitiveContextPackage:
        """P3.1A: typed capability outcome projection (C-03 §11, C-08 §9, C-12 §2).

        Receives ONE exact canonical ToolResult plus its supplied Evidence
        collection. The Context OS frame is a structured derived projection,
        never canonical truth. Does not query the Manager, does not select among
        multiple ToolResults, and does not infer correlation from ordering.

        Only the canonical ToolResult contract is accepted. Legacy flattened
        strings and arbitrary payloads fail closed instead of becoming evidence.
        """
        if not isinstance(tool_result, ToolResult):
            raise TypeError("project_tool_result accepts canonical ToolResult only")

        resolved_evidence = self._resolve_evidence_refs(tool_result, evidence)

        pkg = self._new_projection(
            parent_package,
            generation_id,
            require_generation_id=True,
        )
        inherited_ledger = self._validated_turn_evidence_ledger(parent_package)
        if any(entry.get("generation_id") == generation_id for entry in inherited_ledger):
            raise ValueError(f"duplicate projection generation_id: {generation_id}")
        inherited_ledger.append({
            "generation_id": generation_id,
            "tool_result": self._project_tool_result_view(tool_result),
            "evidence": [self._project_evidence_view(e) for e in resolved_evidence],
        })
        pkg.evidence_frame = {
            "tool_result": self._project_tool_result_view(tool_result),
            "evidence": [self._project_evidence_view(e) for e in resolved_evidence],
            "source": "capability_execution",
            "turn_evidence_ledger": inherited_ledger,
        }
        pkg.situation_frame = {"mode": "tool_continuation"}
        pkg.add_provenance("evidence", "capability:tool_result",
                          reason="tool execution result (typed)", stage=2)
        return pkg

    def project_authorization_outcome(
        self,
        *,
        parent_package: CognitiveContextPackage | None = None,
        authorization_decision: AuthorizationDecision,
        generation_id: str = "",
    ) -> CognitiveContextPackage:
        """P3.1A: structured projection of a non-ALLOW AuthorizationDecision.

        Authorization/control material is NOT external Evidence. CapabilityCall,
        ToolResult and Evidence are all NONE; nothing here renders as a
        TOOL_OBSERVATION.
        """
        decision_value = (
            authorization_decision.decision.value
            if hasattr(authorization_decision.decision, "value")
            else str(authorization_decision.decision)
        )
        if decision_value == AuthorizationStatus.ALLOW.value:
            raise ValueError(
                "project_authorization_outcome only accepts non-ALLOW AuthorizationDecision"
            )
        pkg = self._new_projection(
            parent_package,
            generation_id,
            require_generation_id=True,
        )
        pkg.evidence_frame = self._inherited_evidence_frame(parent_package)
        pkg.control_frame = {
            "kind": "authorization_outcome",
            "decision": decision_value,
            "scope": authorization_decision.scope,
            "reason": authorization_decision.reason,
            "capability_call_id": None,
            "tool_result": None,
            "evidence": [],
        }
        pkg.situation_frame = {"mode": "authorization_outcome"}
        pkg.add_provenance("control", "capability:authorization_outcome",
                          reason="authorization-only outcome", stage=2)
        return pkg

    def project_capability_resolution_failure(
        self,
        *,
        parent_package: CognitiveContextPackage,
        capability_id: str,
        reason: str,
        generation_id: str,
    ) -> CognitiveContextPackage:
        """P3.2.3A: structured projection of a pre-authorization capability
        resolution failure (UNKNOWN / DISABLED / GOVERNED_INGRESS_REQUIRED).

        This is a NON-CANONICAL runtime control fact, NOT Evidence. It is
        projected into the dedicated control_frame (never evidence_frame),
        turn/generation scoped, and mutates no identity/memory/relationship/
        continuity authority. A concrete parent_package and non-empty
        generation_id are required (fail closed otherwise).

        GOVERNED_INGRESS_REQUIRED is an additive control reason introduced by
        the External Code Review module: the generic model tool-call path may
        not invoke engineering.code_review (manual/explicit ingress only).
        """
        if reason not in ("UNKNOWN", "DISABLED", "GOVERNED_INGRESS_REQUIRED"):
            raise ValueError(f"invalid capability resolution reason: {reason!r}")
        if not capability_id or not str(capability_id).strip():
            raise ValueError("capability resolution failure requires a non-empty capability_id")
        if parent_package is None:
            raise ValueError("capability resolution failure projection requires a parent_package")
        if not generation_id or not generation_id.strip():
            raise ValueError("capability resolution failure projection requires a non-empty generation_id")

        pkg = self._new_projection(parent_package, generation_id, require_generation_id=True)
        pkg.evidence_frame = self._inherited_evidence_frame(parent_package)
        pkg.control_frame = {
            "kind": "capability_resolution_failure",
            "capability_id": capability_id,
            "reason": reason,
        }
        pkg.situation_frame = {"mode": "capability_resolution_failure"}
        pkg.add_provenance("control", "capability:resolution_failure",
                          reason=f"{capability_id} {reason}", stage=2)
        return pkg

    def project_retry_control(
        self,
        *,
        parent_package: CognitiveContextPackage,
        reason: str,
        generation_id: str,
    ) -> CognitiveContextPackage:
        """P3.3A: structured projection of derived retry/control state.

        Represents "evidence/tool use was required but no explicit tool
        invocation was decoded; retry under capability-aware context". This is
        derived execution-control state, NOT Evidence / ToolResult /
        CapabilityCall / AuthorizationDecision / CapabilityPreAuthorizationFailure.

        This is an additive discriminated-union extension of the control_frame
        (kind discriminator); it does not alter the frozen
        capability_resolution_failure variant.
        """
        if reason != "required_tool_call_missing":
            raise ValueError(f"unsupported retry control reason: {reason!r}")
        if parent_package is None:
            raise ValueError("retry control projection requires a parent_package")
        if not generation_id or not generation_id.strip():
            raise ValueError("retry control projection requires a non-empty generation_id")

        pkg = self._new_projection(parent_package, generation_id, require_generation_id=True)
        pkg.evidence_frame = self._inherited_evidence_frame(parent_package)
        pkg.control_frame = {
            "kind": "retry_control",
            "reason": reason,
        }
        pkg.situation_frame = {"mode": "retry_control"}
        pkg.add_provenance("control", "capability:retry_control",
                          reason=reason, stage=2)
        return pkg

    def project_tool_call_decode_failure(
        self,
        *,
        parent_package: CognitiveContextPackage,
        reason: str,
        generation_id: str,
    ) -> CognitiveContextPackage:
        if reason not in ("MALFORMED_JSON", "MISSING_NAME", "INVALID_CALL_SHAPE"):
            raise ValueError(f"invalid tool-call decode failure reason: {reason!r}")
        protocol = parent_package.validated_invocation_policy.get(
            "invocation_protocol"
        )
        if not isinstance(protocol, dict):
            raise ValueError(
                "retry control projection requires a validated invocation protocol"
            )
        return self._project_turn_control(
            parent_package=parent_package,
            kind="tool_call_decode_failure",
            reason=reason,
            expected_invocation_protocol=copy.deepcopy(protocol),
            continuation_instruction=(
                "Correct the immediately preceding structured capability-call attempt "
                "before doing any new reasoning or selecting a different capability. "
                "If that response contains a recoverable tool_call with a name and "
                "arguments, preserve that intended name and arguments and re-emit "
                "exactly one valid tool_call block with no surrounding prose. Do not "
                "switch capabilities merely because the previous call shape was "
                "invalid. If the intended call cannot be recovered, continue the same "
                "unresolved evidence goal using the validated invocation protocol."
            ),
            generation_id=generation_id,
            mode="tool_call_decode_failure",
            provenance_source="capability:tool_call_decode_failure",
        )

    def project_duplicate_capability_call_rejected(
        self,
        *,
        parent_package: CognitiveContextPackage,
        capability_id: str,
        arguments: dict[str, Any],
        generation_id: str,
    ) -> CognitiveContextPackage:
        return self._project_turn_control(
            parent_package=parent_package,
            kind="duplicate_capability_call_rejected",
            capability_id=capability_id,
            arguments=copy.deepcopy(arguments),
            continuation_instruction=(
                "This exact capability call has already been executed in this turn. "
                "Do not repeat the same capability+arguments. Inspect the existing "
                "evidence first. If more evidence is still needed, choose a different "
                "available capability that addresses the remaining evidence need; "
                "otherwise produce Julia's final judgment."
            ),
            generation_id=generation_id,
            mode="duplicate_capability_call_rejected",
            provenance_source="capability:duplicate_call_rejected",
        )

    def project_tool_budget_exceeded(
        self,
        *,
        parent_package: CognitiveContextPackage,
        limit: int,
        generation_id: str,
    ) -> CognitiveContextPackage:
        return self._project_turn_control(
            parent_package=parent_package,
            kind="tool_call_budget_exceeded",
            limit=limit,
            generation_id=generation_id,
            mode="tool_budget_exceeded",
            provenance_source="capability:tool_budget_exceeded",
        )

    def _project_turn_control(
        self,
        *,
        parent_package: CognitiveContextPackage,
        kind: str,
        generation_id: str,
        mode: str,
        provenance_source: str,
        **control: Any,
    ) -> CognitiveContextPackage:
        pkg = self._new_projection(parent_package, generation_id, require_generation_id=True)
        pkg.evidence_frame = self._inherited_evidence_frame(parent_package)
        pkg.control_frame = {"kind": kind, **control}
        pkg.situation_frame = {"mode": mode}
        pkg.add_provenance("control", provenance_source, reason=kind, stage=2)
        return pkg

    def _new_projection(
        self,
        parent_package: CognitiveContextPackage | None,
        generation_id: str,
        *,
        require_generation_id: bool = False,
    ) -> CognitiveContextPackage:
        if require_generation_id and (not generation_id or not generation_id.strip()):
            raise ValueError("C03 projection requires a non-empty generation_id")
        pkg = CognitiveContextPackage(
            conversation_id=parent_package.conversation_id if parent_package else "",
            turn_id=parent_package.turn_id if parent_package else "",
            generation_id=generation_id,
        )
        if parent_package is None:
            return pkg
        pkg.active_tail_messages = copy.deepcopy(parent_package.active_tail_messages)
        pkg.projection_metadata = copy.deepcopy(parent_package.projection_metadata)
        seen_generation_ids = set(
            pkg.projection_metadata.get("seen_generation_ids", [])
        )
        seen_generation_ids.add(parent_package.generation_id)
        if require_generation_id and generation_id in seen_generation_ids:
            raise ValueError(f"duplicate projection generation_id: {generation_id}")
        seen_generation_ids.add(generation_id)
        pkg.projection_metadata["seen_generation_ids"] = sorted(seen_generation_ids)
        if parent_package.validated_invocation_policy:
            pkg.validated_invocation_policy = copy.deepcopy(
                parent_package.validated_invocation_policy
            )
            pkg.capability_frame = {
                "invocation_policy": copy.deepcopy(pkg.validated_invocation_policy)
            }
            pkg.add_provenance(
                "capability",
                "capability:validated_invocation_policy",
                reason="validated invocation policy retained for continuation",
                stage=2,
            )
            available_tools = parent_package.capability_frame.get("available_tools")
            if isinstance(available_tools, list):
                pkg.capability_frame["available_tools"] = copy.deepcopy(available_tools)
        return pkg

    def _validated_turn_evidence_ledger(
        self,
        parent_package: CognitiveContextPackage | None,
    ) -> list[dict[str, Any]]:
        if parent_package is None:
            return []
        ledger = parent_package.evidence_frame.get("turn_evidence_ledger", [])
        if not isinstance(ledger, list):
            raise ValueError("turn_evidence_ledger must be a list")
        generation_ids: set[str] = set()
        for index, entry in enumerate(ledger):
            if not isinstance(entry, dict):
                raise ValueError(f"turn_evidence_ledger[{index}] must be a mapping")
            if (
                "tool_result" not in entry
                or not isinstance(entry["tool_result"], dict)
                or "evidence" not in entry
                or not isinstance(entry["evidence"], list)
            ):
                raise ValueError(
                    f"turn_evidence_ledger[{index}] has malformed tool observation provenance"
                )
            generation_id = entry.get("generation_id")
            if not isinstance(generation_id, str) or not generation_id.strip():
                raise ValueError(f"turn_evidence_ledger[{index}].generation_id is invalid")
            if generation_id in generation_ids:
                raise ValueError(
                    f"duplicate turn_evidence_ledger generation_id: {generation_id}"
                )
            generation_ids.add(generation_id)
        return copy.deepcopy(ledger)

    def _inherited_evidence_frame(
        self,
        parent_package: CognitiveContextPackage | None,
    ) -> dict[str, Any]:
        if parent_package is None or "turn_evidence_ledger" not in parent_package.evidence_frame:
            return {}
        return {
            "turn_evidence_ledger": self._validated_turn_evidence_ledger(parent_package),
        }

    # ── P3.1A helpers ─────────────────────────────────────────────────────

    def _resolve_evidence_refs(
        self,
        tool_result: ToolResult,
        evidence: Sequence[Evidence],
    ) -> list[Evidence]:
        """Validate ToolResult.evidence_refs against supplied Evidence (fail closed).

        - duplicate supplied Evidence.evidence_id -> ValueError
        - dangling ToolResult.evidence_refs -> ValueError
        - unrelated supplied Evidence is not projected
        - repeated evidence_refs are deduped preserving first-reference order
        - projection order follows evidence_refs order, not supplied-list order
        """
        by_id: dict[str, Evidence] = {}
        for e in evidence:
            if e.evidence_id in by_id:
                raise ValueError(f"duplicate supplied Evidence.evidence_id: {e.evidence_id}")
            by_id[e.evidence_id] = e

        resolved: list[Evidence] = []
        emitted: set[str] = set()
        for ref in tool_result.evidence_refs:
            if ref not in by_id:
                raise ValueError(f"dangling ToolResult.evidence_refs: {ref}")
            if ref in emitted:
                continue
            emitted.add(ref)
            resolved.append(by_id[ref])
        return resolved

    def _project_tool_result_view(self, tr: ToolResult) -> dict[str, Any]:
        """Explicit whitelist projection of ToolResult fields (no asdict dump)."""
        status = tr.status.value if hasattr(tr.status, "value") else str(tr.status)
        side_effect = (
            tr.side_effect_state.value
            if hasattr(tr.side_effect_state, "value")
            else str(tr.side_effect_state)
        )
        view: dict[str, Any] = {
            "capability_call_id": tr.capability_call_id,
            "status": status,
            "evidence_refs": list(tr.evidence_refs),
            "provider": tr.provider,
            "side_effect_state": side_effect,
        }
        if tr.structured_output:
            view["structured_output"] = copy.deepcopy(dict(tr.structured_output))
        if tr.error is not None:
            view["error"] = copy.deepcopy(dict(tr.error))
        return view

    def _project_evidence_view(self, e: Evidence) -> dict[str, Any]:
        """Explicit whitelist projection of Evidence fields (no asdict dump)."""
        source_type = e.source_type.value if hasattr(e.source_type, "value") else str(e.source_type)
        provenance = {
            k: e.provenance[k]
            for k in ("capability_request_id", "capability_call_id", "capability_id", "provider")
            if k in e.provenance
        }
        return {
            "evidence_id": e.evidence_id,
            "source_type": source_type,
            "source_ref": e.source_ref,
            "observed_at": e.observed_at,
            "content_ref": e.content_ref,
            "freshness": e.freshness,
            "confidence": e.confidence,
            "correlation_id": e.correlation_id,
            "provenance": provenance,
        }

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
        # No silent catch: a missing module or a load error propagates so
        # prepare() records an explicit "experience:density" degradation,
        # distinguishable from a legitimate no-data empty state.
        try:
            from julia_core.context_assembly.density_restorer import get_experience_context_block
        except ImportError as exc:
            raise RuntimeError(f"density restorer unavailable: {exc}") from exc
        ctx = get_experience_context_block(max_tokens=2000)
        if ctx:
            self._density_cache = ctx  # type: ignore[attr-defined]
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

    def _project_current_turn_temporal_context(
        self,
        pkg: CognitiveContextPackage,
        *,
        conversation_id: str,
        turn_id: str,
        scoped_history: list[dict],
    ) -> None:
        """Project the C02 event time of the exact current user message."""
        if not conversation_id or not turn_id:
            return

        matches = [
            message
            for message in scoped_history
            if message.get("conversation_id") == conversation_id
            and message.get("turn_id") == turn_id
            and message.get("role") == "user"
            and message.get("status") == "completed"
            and isinstance(message.get("created_at"), str)
            and message["created_at"]
        ]
        if not matches:
            return
        if len(matches) != 1:
            pkg.mark_frame_failure(
                "situation:temporal",
                "current-turn canonical user message is ambiguous",
                required=False,
            )
            return

        source = matches[0]
        raw_timestamp = source["created_at"]
        try:
            timestamp = datetime.fromisoformat(raw_timestamp)
            offset = timestamp.utcoffset()
            if timestamp.tzinfo is None or offset is None:
                raise ValueError("timezone-naive timestamp")
            total_minutes = int(offset.total_seconds()) // 60
            sign = "+" if total_minutes >= 0 else "-"
            absolute_minutes = abs(total_minutes)
            utc_offset = f"{sign}{absolute_minutes // 60:02d}:{absolute_minutes % 60:02d}"
        except (TypeError, ValueError, OverflowError) as exc:
            pkg.mark_frame_failure(
                "situation:temporal",
                f"current-turn timestamp unavailable: {exc}",
                required=False,
            )
            return

        pkg.situation_frame.update({
            "current_turn_timestamp": raw_timestamp,
            "current_date": timestamp.date().isoformat(),
            "utc_offset": utc_offset,
        })
        pkg.add_provenance(
            "situation",
            "C02 canonical current user ConversationMessage",
            canonical_ref=(
                f"conversation:{conversation_id}:turn:{turn_id}:"
                f"message:{source.get('message_id', '')}"
            ),
            reason="C03 current-turn temporal projection",
            stage=0,
        )

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
