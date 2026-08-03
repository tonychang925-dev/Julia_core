"""H5 Julia Assistant Runtime streaming binding.

This is the first runtime-owned binding between Human Interface streaming and
Julia Core OS layers. It emits trace/events; it does not let HTTP, client, or
voice own Persona, Memory, Continuity, Context, Evidence, or Provider state.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterator, Literal, Mapping, Sequence

from julia_core.context_os import EvidenceContextReconstructor, EvidenceContextRequirement
from julia_core.evidence import ActiveRecallPolicy, ActiveRecallRequest, EvidenceScanner, SemanticEvidenceIndex, SemanticEvidenceRetriever
from julia_core.experience import ExperienceContextReconstructor, ExperienceRetrievalRequest
from julia_core.runtime.continuity_hook import RuntimeContinuityHook
from julia_core.runtime.startup_profile import JuliaStartupProfile, is_profile_recall_request, load_startup_profile
from julia_core.providers.streaming import DeterministicProviderStreamAdapter, ProviderStreamAdapter, ProviderStreamRequest
from julia_core.self_model import SelfArchiveRetriever, SelfNarrativeContextBlock, SelfRecallDecision, decide_self_activation, decide_self_recall, detects_relationship_drift, is_relationship_question, load_relationship_artifact

RuntimeStreamEventType = Literal["runtime_ready", "context_ready", "text_delta", "done", "error"]


@dataclass(frozen=True, slots=True)
class RuntimeStreamRequest:
    session_id: str
    message: str
    input_mode: str = "text"
    stream: bool = True
    workspace_roots: tuple[str, ...] = ()
    provider_id: str = "deterministic_runtime_provider"

    def __post_init__(self) -> None:
        if not self.session_id:
            raise ValueError("session_id is required")
        if not self.message:
            raise ValueError("message is required")
        object.__setattr__(self, "workspace_roots", tuple(self.workspace_roots))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class RuntimeStreamEvent:
    event: RuntimeStreamEventType
    payload: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", dict(self.payload))

    def to_dict(self) -> dict[str, Any]:
        return {"event": self.event, "payload": dict(self.payload)}


@dataclass(frozen=True, slots=True)
class RuntimeBindingTrace:
    session_id: str
    input_mode: str
    continuity: str
    memory: str
    context: str
    evidence: str
    provider: str
    recall_level: str
    context_blocks_used: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    boundary: Mapping[str, bool] = field(
        default_factory=lambda: {
            "streaming_layer_writes_memory": False,
            "streaming_layer_mutates_identity": False,
            "voice_owns_identity": False,
            "provider_reads_files": False,
            "raw_memory_dumped": False,
            "raw_evidence_dumped": False,
        }
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "context_blocks_used", tuple(self.context_blocks_used))
        object.__setattr__(self, "evidence_refs", tuple(self.evidence_refs))
        object.__setattr__(self, "boundary", dict(self.boundary))

    def to_dict(self) -> dict[str, Any]:
        return {
            "interaction": {"mode": self.input_mode, "stream": True},
            "runtime": {"session_id": self.session_id, "status": "PASS"},
            "continuity": {"status": self.continuity},
            "memory": {"status": self.memory},
            "context": {"status": self.context, "blocks_used": list(self.context_blocks_used)},
            "evidence": {"status": self.evidence, "refs": list(self.evidence_refs)},
            "provider": {"status": self.provider, "streaming": True},
            "boundary": dict(self.boundary),
        }


class JuliaAssistantRuntime:
    """Runtime-owned text streaming over Julia Core OS inspection paths."""

    def __init__(self, provider: ProviderStreamAdapter | None = None, startup_profile: JuliaStartupProfile | None = None) -> None:
        self.continuity_hook = RuntimeContinuityHook(agent_id="julia")
        self.recall_policy = ActiveRecallPolicy()
        self.evidence_context = EvidenceContextReconstructor()
        self.provider = provider or DeterministicProviderStreamAdapter()
        self.startup_profile = startup_profile or load_startup_profile()
        self.self_archive_retriever = SelfArchiveRetriever()
        self.relationship_artifact = load_relationship_artifact()
        self.experience_context = ExperienceContextReconstructor()

    def stream(self, request: RuntimeStreamRequest) -> Iterator[RuntimeStreamEvent]:
        continuity = self.continuity_hook.check_state({}, event="SESSION_START", agent_id="julia")
        recall = self.recall_policy.decide(
            ActiveRecallRequest(query=request.message, intent="human_interface_runtime", current_context="")
        )
        evidence_refs: tuple[str, ...] = ()
        context_blocks: tuple[str, ...] = ()
        evidence_status = "PASS_NOT_REQUIRED"
        context_status = "PASS"

        if recall.should_recall and recall.recall_level in {"L2", "L3"} and request.workspace_roots:
            retrieval = self._retrieve_evidence(request, max_results=recall.max_results or 5)
            evidence_refs = tuple(item.evidence_ref for item in retrieval)
            evidence_status = "PASS"
            requirement = EvidenceContextRequirement(query=request.message, recall_level=recall.recall_level, trigger=recall.reason)
            context_result = self.evidence_context.reconstruct(retrieval, requirement)
            context_blocks = tuple(block.block_type for block in context_result.context_blocks)
        elif recall.should_recall:
            evidence_status = "PASS_NO_WORKSPACE_ROOTS"

        self_activation = decide_self_activation(request.message)
        self_recall = decide_self_recall(request.message)
        if self_activation.activate_self_archive and not self_recall.recall_required:
            self_recall = SelfRecallDecision("self_identity_question", True, ("self_model", "persona_archive"), f"self_activation:{self_activation.reason}")
        self_archive_block = self.self_archive_retriever.retrieve(self_recall)
        relationship_context_block = self.relationship_artifact.context_block() if self_activation.activate_relationship or is_relationship_question(request.message) or detects_relationship_drift(request.message) else None
        experience_reconstruction = self.experience_context.reconstruct(ExperienceRetrievalRequest(query=request.message))
        experience_context_block = experience_reconstruction.context_block.to_dict() if experience_reconstruction.context_block is not None and experience_reconstruction.influence_score > 0 else None
        if self_archive_block is not None:
            context_blocks = tuple((*context_blocks, self_archive_block.context_type))
        if relationship_context_block is not None:
            context_blocks = tuple((*context_blocks, relationship_context_block["context_type"]))
        if experience_context_block is not None:
            context_blocks = tuple((*context_blocks, experience_context_block["context_type"]))

        trace = RuntimeBindingTrace(
            session_id=request.session_id,
            input_mode=request.input_mode,
            continuity="PASS" if continuity.checked else "FAIL",
            memory="PASS_BOUNDARY_NO_DUMP",
            context=context_status,
            evidence=evidence_status,
            provider="PASS",
            recall_level=recall.recall_level,
            context_blocks_used=context_blocks,
            evidence_refs=evidence_refs,
        )
        trace_payload = trace.to_dict()
        trace_payload["self_activation"] = self_activation.to_dict()
        trace_payload["experience_reconstruction"] = experience_reconstruction.to_dict()
        trace_payload["relationship_drift_detected"] = detects_relationship_drift(request.message)
        yield RuntimeStreamEvent(event="runtime_ready", payload={"trace": trace_payload})
        yield RuntimeStreamEvent(event="context_ready", payload={"trace": trace_payload})

        provider_request = self._provider_request(request, trace, self.startup_profile, self_archive_block, relationship_context_block, detects_relationship_drift(request.message), self_activation.to_dict(), experience_context_block)
        provider_trace: dict[str, Any] = {}
        for provider_event in self.provider.stream(provider_request):
            if provider_event.trace:
                provider_trace = dict(provider_event.trace.get("provider", provider_event.trace))
            if provider_event.event == "delta" and provider_event.delta is not None:
                yield RuntimeStreamEvent(event="text_delta", payload={"type": "text_delta", "content": provider_event.delta.text})
            if provider_event.event == "error":
                yield RuntimeStreamEvent(event="error", payload={"error": provider_event.error or "provider_error"})
        yield RuntimeStreamEvent(event="done", payload={"ok": True, "trace": trace_payload, "provider_trace": provider_trace})

    def _retrieve_evidence(self, request: RuntimeStreamRequest, *, max_results: int):
        catalog = EvidenceScanner().scan(request.workspace_roots)
        index = SemanticEvidenceIndex.from_catalog(catalog)
        result = SemanticEvidenceRetriever(index).retrieve(request.message, top_k=max_results)
        return result.results

    @staticmethod
    def _provider_request(request: RuntimeStreamRequest, trace: RuntimeBindingTrace, startup_profile: JuliaStartupProfile, self_archive_block: SelfNarrativeContextBlock | None = None, relationship_context_block: Mapping[str, Any] | None = None, relationship_drift_detected: bool = False, self_activation: Mapping[str, Any] | None = None, experience_context_block: Mapping[str, Any] | None = None) -> ProviderStreamRequest:
        system_context = startup_profile.system_digest()
        system_context += " Context OS prepared output only; do not request raw Memory or raw Evidence dumps."
        if self_archive_block is not None:
            system_context += " Self Activation/Self Archive Recall produced a self_narrative context block; answer from that semantic block, not from generic model identity."
        if relationship_context_block is not None:
            system_context += " Relationship Continuity produced a relationship context block; answer from shared-history relationship, not generic user/assistant roles."
        if experience_context_block is not None:
            system_context += " Interaction Experience produced behavior guidance; use it through Context OS without treating it as memory, persona, or fixed script."
        if trace.evidence_refs:
            system_context += " EvidenceRefs: " + "、".join(trace.evidence_refs[:5])
        return ProviderStreamRequest(
            messages=(
                {"role": "system", "content": system_context},
                {"role": "user", "content": request.message},
            ),
            stream=True,
            model=request.provider_id,
            provider_name=request.provider_id,
            context_blocks=trace.context_blocks_used,
            trace={
                **trace.to_dict(),
                "startup_profile": startup_profile.to_dict(),
                "profile_recall_requested": is_profile_recall_request(request.message),
                "self_activation": dict(self_activation or {}),
                "self_recall": decide_self_recall(request.message).to_dict(),
                "self_archive_block": self_archive_block.to_dict() if self_archive_block else None,
                "relationship_context_block": relationship_context_block,
                "relationship_drift_detected": relationship_drift_detected,
                "experience_context_block": experience_context_block,
            },
        )
