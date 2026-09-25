"""Fail-closed isolated Golden Mira runtime composition root."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from dataclasses import replace
from pathlib import Path
from typing import Any

from julia_core.alignment_os import ProviderExecutionEnvelope
from julia_core.canonical_authority_source import CanonicalSemanticAuthoritySource
from julia_core.conversation_state.legacy_json_repository import (
    LegacyJsonConversationRepository,
)
from julia_core.context_admission import (
    CanonicalConversationProvenance,
    CanonicalConversationSource,
    CurrentConversationalTaskContext,
    ExactPersonaSelfBoundSemanticBinder,
    ExclusiveAdmissionGate,
    ExclusiveAdmissionRequest,
    PersonaSelfBindingSemanticBindingRequest,
    PersonaSelfBoundSemanticBundle,
)
from julia_core.context_admission.gate import C03_PRODUCTION_CONTRACT_VERSION
from julia_core.durable_authority.filesystem_adapter import (
    EXPECTED_IDENTITY_REFS,
    EXPECTED_IDENTITY_VERSIONS,
    EXPECTED_MEMORY_REFS,
    EXPECTED_MEMORY_VERSIONS,
    FilesystemDurableAuthorityReader,
)
from julia_core.durable_authority.reconstruction import (
    reconstruct_from_durable_authority,
)
from julia_core.identity import IdentityRef, IdentityRepository, IdentityResolver
from julia_core.memory_experience import (
    MemoryExperienceRef,
    MemoryExperienceRepository,
    MemoryExperienceResolver,
)
from julia_core.persona_self_binding import (
    PersonaSelfBindingProjection,
    PersonaSelfBindingProjectorV2,
    PersonaSelfBindingProjectionV2,
    PersonaSelfBindingRecord,
    PersonaSelfBindingStore,
)
from julia_core.projection import ExperienceFrameSet, IdentityFrameSet
from julia_core.runtime.assistant_runtime import (
    JuliaAssistantRuntime,
    RuntimeTurnRequest,
)
from julia_core.runtime.conversation_runtime import ConversationRuntime
from julia_core.runtime.provider_persona_separation import (
    DispatchReceipt,
    ExecutionSubstrateDescriptor,
    GoldenMiraDispatchGate,
    GoldenMiraSealedTransport,
    GoldenMiraTransportBoundary,
    ProviderDispatchPreparation,
)


_SHA_PATTERN = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
_PERSONA_ID = "golden-mira"
_PSB_BINDING_ID = "golden-mira-persona-self-binding-v1"
_PSB_BINDING_VERSION = "v2"
_PSB_LINEAGE_ID = "golden-mira-persona-self-binding"
_PSB_OBJECT_DIGEST = "a6167069289a0704b207292cd44a509a8f6e2844a143e5dbb7673fbcac38b525"
_PSB_PROJECTED_DIGEST = (
    "4d833b044957d9642fa4785367088fca63b00d6b0b97f7be5c5e7a15e9e084dd"
)
_RECENT_CONVERSATION_MESSAGE_LIMIT = 6
_RECENT_CONVERSATION_CONTENT_BYTE_LIMIT = 80
_RECENT_CONVERSATION_ENCODED_BYTE_LIMIT = 1408


class MiraCompositionError(RuntimeError):
    """Fail-closed isolated Mira composition failure."""


@dataclass(frozen=True, slots=True)
class MiraRuntimeShaPins:
    expected_core_sha: str
    observed_core_sha: str
    expected_assistant_sha: str
    observed_assistant_sha: str

    def __post_init__(self) -> None:
        for field_name in (
            "expected_core_sha",
            "observed_core_sha",
            "expected_assistant_sha",
            "observed_assistant_sha",
        ):
            value = getattr(self, field_name)
            if type(value) is not str or _SHA_PATTERN.fullmatch(value) is None:
                raise MiraCompositionError(f"{field_name} must be an exact SHA")
        if self.expected_core_sha != self.observed_core_sha:
            raise MiraCompositionError("Core SHA pin mismatch")
        if self.expected_assistant_sha != self.observed_assistant_sha:
            raise MiraCompositionError("Assistant SHA pin mismatch")


@dataclass(frozen=True, slots=True)
class MiraProviderEnvelopeRequest:
    conversation_id: str
    turn_id: str
    task_domain: str
    input_mode: str
    input_text: str
    observed_at: str
    provider_id: str

    def __post_init__(self) -> None:
        for field_name in (
            "conversation_id",
            "turn_id",
            "task_domain",
            "input_mode",
            "input_text",
            "observed_at",
            "provider_id",
        ):
            if type(getattr(self, field_name)) is not str or not getattr(
                self, field_name
            ):
                raise MiraCompositionError(
                    f"provider envelope request {field_name} is required"
                )
        if self.input_mode != "text":
            raise MiraCompositionError("P1-B supports the exact text input mode only")


@dataclass(frozen=True, slots=True)
class MiraCompositionEvidence:
    persona_id: str
    identity_count: int
    memory_experience_count: int
    ordered_identity_refs: tuple[str, ...]
    ordered_memory_experience_refs: tuple[str, ...]
    c03_contract_version: str
    binder: type[ExactPersonaSelfBoundSemanticBinder]
    active_persona_self_binding_id: str
    active_persona_self_binding_version: str
    active_persona_self_binding_digest: str
    active_persona_self_binding_projected_digest: str
    conversation_store_path: Path
    sha_pins_matched: bool
    provider_transport_called: bool


class GoldenMiraRuntimeComposition:
    """Explicit isolated object graph; no implicit Julia product state."""

    def __init__(
        self,
        *,
        authority_root: Path,
        conversation_store_path: Path,
        identity_repository: IdentityRepository,
        memory_repository: MemoryExperienceRepository,
        identity_frames: IdentityFrameSet,
        experience_frames: ExperienceFrameSet,
        conversation_runtime: ConversationRuntime,
        assistant_runtime: JuliaAssistantRuntime,
        sha_pins: MiraRuntimeShaPins,
        psb_store_root: Path,
        persona_self_binding: PersonaSelfBindingRecord,
        persona_self_binding_projection: PersonaSelfBindingProjectionV2,
    ) -> None:
        object.__setattr__(self, "_authority_root", authority_root)
        object.__setattr__(self, "_conversation_store_path", conversation_store_path)
        object.__setattr__(self, "_identity_repository", identity_repository)
        object.__setattr__(self, "_memory_repository", memory_repository)
        object.__setattr__(self, "_identity_frames", identity_frames)
        object.__setattr__(self, "_experience_frames", experience_frames)
        object.__setattr__(self, "_conversation_runtime", conversation_runtime)
        object.__setattr__(self, "_assistant_runtime", assistant_runtime)
        object.__setattr__(self, "_sha_pins", sha_pins)
        object.__setattr__(self, "_psb_store_root", psb_store_root)
        object.__setattr__(self, "_persona_self_binding", persona_self_binding)
        object.__setattr__(
            self,
            "_persona_self_binding_projection",
            persona_self_binding_projection,
        )
        object.__setattr__(
            self,
            "_semantic_authority_source",
            CanonicalSemanticAuthoritySource(
                identity_resolver=IdentityResolver(identity_repository),
                memory_resolver=MemoryExperienceResolver(memory_repository),
            ),
        )

    @property
    def authority_root(self) -> Path:
        return self._authority_root

    @property
    def psb_store_root(self) -> Path:
        return self._psb_store_root

    @property
    def conversation_store_path(self) -> Path:
        return self._conversation_store_path

    @property
    def conversation_runtime(self) -> ConversationRuntime:
        return self._conversation_runtime

    @property
    def assistant_runtime(self) -> JuliaAssistantRuntime:
        return self._assistant_runtime

    @property
    def identity_repository(self) -> IdentityRepository:
        return self._identity_repository

    @property
    def memory_repository(self) -> MemoryExperienceRepository:
        return self._memory_repository

    @property
    def semantic_authority_source(self) -> CanonicalSemanticAuthoritySource:
        return self._semantic_authority_source

    @property
    def persona_self_binding(self) -> PersonaSelfBindingRecord:
        return self._persona_self_binding

    def evidence(self) -> MiraCompositionEvidence:
        return MiraCompositionEvidence(
            persona_id=_PERSONA_ID,
            identity_count=len(self._identity_frames.frames),
            memory_experience_count=len(self._experience_frames.frames),
            ordered_identity_refs=tuple(
                frame.source_ref.lineage_id for frame in self._identity_frames.frames
            ),
            ordered_memory_experience_refs=tuple(
                frame.source_ref.experience_id
                for frame in self._experience_frames.frames
            ),
            c03_contract_version=C03_PRODUCTION_CONTRACT_VERSION,
            binder=ExactPersonaSelfBoundSemanticBinder,
            active_persona_self_binding_id=self._persona_self_binding.binding.binding_id,
            active_persona_self_binding_version=(
                self._persona_self_binding.binding.binding_version
            ),
            active_persona_self_binding_digest=(
                self._persona_self_binding.object_digest
            ),
            active_persona_self_binding_projected_digest=(
                self._persona_self_binding_projection.digest()
            ),
            conversation_store_path=self._conversation_store_path,
            sha_pins_matched=True,
            provider_transport_called=False,
        )

    def prepare_provider_envelope(
        self, request: MiraProviderEnvelopeRequest
    ) -> ProviderExecutionEnvelope:
        binding = self._prepare_persona_self_bound_semantics(request)
        return self._assistant_runtime.prepare(
            RuntimeTurnRequest(
                binding=binding,
                provider_id=request.provider_id,
                input_mode=request.input_mode,
            )
        )

    def prepare_provider_dispatch(
        self,
        request: MiraProviderEnvelopeRequest,
        *,
        execution_substrate: ExecutionSubstrateDescriptor,
        expected_runtime_instance_id: str,
    ) -> ProviderDispatchPreparation:
        descriptor = execution_substrate.verify(
            expected_runtime_instance_id=expected_runtime_instance_id
        )
        if request.provider_id != descriptor.provider_id:
            raise MiraCompositionError(
                "provider request and execution substrate are inexact"
            )
        binding = self._prepare_persona_self_bound_semantics(request)
        envelope = self._assistant_runtime.prepare(
            RuntimeTurnRequest(
                binding=binding,
                provider_id=request.provider_id,
                input_mode=request.input_mode,
            )
        )
        receipt = DispatchReceipt.bind(
            binding=binding,
            envelope=envelope,
            execution_substrate=descriptor,
        )
        preparation = ProviderDispatchPreparation(
            semantic_binding=binding,
            envelope=envelope,
            execution_substrate=descriptor,
            dispatch_receipt=receipt,
            expected_runtime_instance_id=expected_runtime_instance_id,
        )
        preparation.verify()
        return preparation

    def dispatch_to_transport_boundary(
        self,
        request: MiraProviderEnvelopeRequest,
        *,
        execution_substrate: ExecutionSubstrateDescriptor,
        expected_runtime_instance_id: str,
        dispatch_gate: GoldenMiraDispatchGate,
        transport_boundary: GoldenMiraTransportBoundary,
    ) -> GoldenMiraSealedTransport:
        if type(dispatch_gate) is not GoldenMiraDispatchGate:
            raise MiraCompositionError("Golden Mira dispatch gate is inexact")
        if type(transport_boundary) is not GoldenMiraTransportBoundary:
            raise MiraCompositionError("Golden Mira transport boundary is inexact")
        if dispatch_gate.expected_runtime_instance_id != expected_runtime_instance_id:
            raise MiraCompositionError(
                "Golden Mira dispatch gate runtime pin is inexact"
            )
        preparation = self.prepare_provider_dispatch(
            request,
            execution_substrate=execution_substrate,
            expected_runtime_instance_id=expected_runtime_instance_id,
        )
        authorization = dispatch_gate.authorize(preparation)
        return transport_boundary.seal(authorization)

    def _prepare_persona_self_bound_semantics(
        self, request: MiraProviderEnvelopeRequest
    ) -> PersonaSelfBoundSemanticBundle:
        if type(request) is not MiraProviderEnvelopeRequest:
            raise MiraCompositionError("provider envelope request is inexact")
        current_task = self._current_task_context(request)
        package = ExclusiveAdmissionGate().seal(
            ExclusiveAdmissionRequest(
                identity_frames=self._identity_frames,
                experience_frames=self._experience_frames,
                current_task_context=current_task,
            )
        )
        binding = ExactPersonaSelfBoundSemanticBinder().bind(
            PersonaSelfBindingSemanticBindingRequest(
                package=package,
                persona_self_binding=self._persona_self_binding.binding,
                persona_self_binding_projection=(self._persona_self_binding_projection),
                identity_frames=self._identity_frames,
                experience_frames=self._experience_frames,
                current_task_context=current_task,
            )
        )
        binding.verify()
        return binding

    def _current_task_context(
        self, request: MiraProviderEnvelopeRequest
    ) -> CurrentConversationalTaskContext:
        history = self._conversation_runtime.get_canonical_history(
            request.conversation_id
        )
        recent_conversation = _project_recent_conversation(
            history,
            conversation_id=request.conversation_id,
        )
        history_digest = _sha256_text(_canonical_json(history))
        ingress = {
            "conversation_id": request.conversation_id,
            "turn_id": request.turn_id,
            "input_mode": request.input_mode,
            "input_sha256": _sha256_text(request.input_text),
            "history_sha256": history_digest,
            "recent_conversation": recent_conversation,
            "recent_conversation_sha256": _semantic_projection_digest(
                recent_conversation
            ),
        }
        current_task = CurrentConversationalTaskContext(
            schema_version="1.0.0",
            conversation_id=request.conversation_id,
            turn_id=request.turn_id,
            task_intent=request.input_text,
            task_domain=request.task_domain,
            current_modality=request.input_mode,
            bounded_state=ingress,
            provenance=CanonicalConversationProvenance(
                source_type=CanonicalConversationSource.CONVERSATION_RUNTIME,
                source_ref="conversation_runtime://golden-mira/current-task",
                source_digest=_sha256_text(_canonical_json(ingress)),
                observed_at=request.observed_at,
            ),
        )
        verified_history = self._conversation_runtime.get_canonical_history(
            request.conversation_id
        )
        verified_history_digest = _sha256_text(_canonical_json(verified_history))
        _verify_recent_conversation_projection(
            current_task,
            conversation_id=request.conversation_id,
            history_digest=verified_history_digest,
            expected_projection=_project_recent_conversation(
                verified_history,
                conversation_id=request.conversation_id,
            ),
        )
        return current_task

    def __setattr__(self, name: str, value: object) -> None:
        raise TypeError("Golden Mira runtime compositions are immutable")

    def __delattr__(self, name: str) -> None:
        raise TypeError("Golden Mira runtime compositions are immutable")


def compose_golden_mira_runtime(
    *,
    authority_root: Path,
    conversation_store_path: Path,
    psb_store_root: Path,
    sha_pins: MiraRuntimeShaPins,
) -> GoldenMiraRuntimeComposition:
    if not isinstance(authority_root, Path) or not authority_root.is_absolute():
        raise MiraCompositionError("authority_root must be an explicit absolute Path")
    if (
        not isinstance(conversation_store_path, Path)
        or not conversation_store_path.is_absolute()
    ):
        raise MiraCompositionError(
            "conversation_store_path must be an explicit absolute Path"
        )
    if not isinstance(psb_store_root, Path) or not psb_store_root.is_absolute():
        raise MiraCompositionError("psb_store_root must be an explicit absolute Path")
    if type(sha_pins) is not MiraRuntimeShaPins:
        raise MiraCompositionError("SHA pins must use the exact MiraRuntimeShaPins")

    reader = FilesystemDurableAuthorityReader(authority_root)
    identity_repository, memory_repository = reconstruct_from_durable_authority(reader)
    authority_source = CanonicalSemanticAuthoritySource(
        identity_resolver=IdentityResolver(identity_repository),
        memory_resolver=MemoryExperienceResolver(memory_repository),
    )
    identity_frames = IdentityFrameSet(
        schema_version="1.0.0",
        frames=tuple(
            _with_canonical_binding(
                authority_source.resolve_identity_frame(_identity_ref(ref, version))
            )
            for ref, version in zip(EXPECTED_IDENTITY_REFS, EXPECTED_IDENTITY_VERSIONS)
        ),
    )
    experience_frames = ExperienceFrameSet(
        schema_version="1.0.0",
        frames=tuple(
            _with_canonical_binding(
                authority_source.resolve_experience_frame(_memory_ref(ref, version))
            )
            for ref, version in zip(EXPECTED_MEMORY_REFS, EXPECTED_MEMORY_VERSIONS)
        ),
    )
    if tuple(
        (frame.source_ref.lineage_id, frame.source_ref.version_id)
        for frame in identity_frames.frames
    ) != tuple(zip(EXPECTED_IDENTITY_REFS, EXPECTED_IDENTITY_VERSIONS)) or tuple(
        (frame.source_ref.experience_id, frame.source_ref.version_id)
        for frame in experience_frames.frames
    ) != tuple(
        zip(EXPECTED_MEMORY_REFS, EXPECTED_MEMORY_VERSIONS)
    ):
        raise MiraCompositionError("durable Golden Mira ordering is inexact")
    identity_projected_digest = _semantic_projection_digest(
        identity_frames.model_visible_projection()
    )
    experience_projected_digest = _semantic_projection_digest(
        experience_frames.model_visible_projection()
    )
    try:
        persona_self_binding = PersonaSelfBindingStore(psb_store_root).resolve_active(
            _PERSONA_ID
        )
        binding = persona_self_binding.binding
        if (
            binding.binding_id != _PSB_BINDING_ID
            or binding.binding_version != _PSB_BINDING_VERSION
            or binding.lineage_id != _PSB_LINEAGE_ID
        ):
            raise MiraCompositionError(
                "active PersonaSelfBinding identity or lineage is inexact"
            )
        if persona_self_binding.object_digest != _PSB_OBJECT_DIGEST:
            raise MiraCompositionError("active PersonaSelfBinding digest is inexact")
        if (
            binding.identity_authority.source_digest != identity_frames.digest()
            or binding.identity_authority.projected_digest != identity_projected_digest
        ):
            raise MiraCompositionError(
                "active PersonaSelfBinding identity authority is inexact"
            )
        if (
            binding.experience_authority.source_digest != experience_frames.digest()
            or binding.experience_authority.projected_digest
            != experience_projected_digest
        ):
            raise MiraCompositionError(
                "active PersonaSelfBinding experience authority is inexact"
            )
        persona_self_binding_projection = PersonaSelfBindingProjectorV2.project(binding)
        if persona_self_binding_projection.digest() != _PSB_PROJECTED_DIGEST:
            raise MiraCompositionError(
                "active PersonaSelfBinding projection digest is inexact"
            )
    except MiraCompositionError:
        raise
    except Exception as error:
        raise MiraCompositionError(
            "active governed PersonaSelfBinding authority failed"
        ) from error
    repository = LegacyJsonConversationRepository(conversation_store_path)
    return GoldenMiraRuntimeComposition(
        authority_root=authority_root,
        conversation_store_path=conversation_store_path,
        identity_repository=identity_repository,
        memory_repository=memory_repository,
        identity_frames=identity_frames,
        experience_frames=experience_frames,
        conversation_runtime=ConversationRuntime(repository),
        assistant_runtime=JuliaAssistantRuntime(),
        sha_pins=sha_pins,
        psb_store_root=psb_store_root,
        persona_self_binding=persona_self_binding,
        persona_self_binding_projection=persona_self_binding_projection,
    )


def _identity_ref(canonical_ref: str, version: str) -> IdentityRef:
    prefix = "mira-golden:"
    if type(canonical_ref) is not str or not canonical_ref.startswith(prefix):
        raise MiraCompositionError("Golden Mira identity ref is malformed")
    return IdentityRef(lineage_id=canonical_ref, version_id=version)


def _memory_ref(canonical_ref: str, version: str) -> MemoryExperienceRef:
    if type(canonical_ref) is not str or not canonical_ref.startswith("golden-mira:"):
        raise MiraCompositionError("Golden Mira memory ref is malformed")
    return MemoryExperienceRef(experience_id=canonical_ref, version_id=version)


def _project_recent_conversation(
    history: list[dict[str, Any]],
    *,
    conversation_id: str,
) -> dict[str, Any]:
    if type(history) is not list:
        raise MiraCompositionError("canonical conversation history is inexact")
    for message in history:
        if type(message) is not dict:
            raise MiraCompositionError("canonical conversation message is inexact")
        message_conversation_id = message.get("conversation_id")
        if message_conversation_id != conversation_id:
            raise MiraCompositionError(
                "canonical conversation history scope is inexact"
            )
        if message.get("role") not in ("user", "assistant"):
            raise MiraCompositionError("canonical conversation role is inexact")

    history_digest = _sha256_text(_canonical_json(history))
    selected = history[-_RECENT_CONVERSATION_MESSAGE_LIMIT:]
    omitted_history_message_count = len(history) - len(selected)
    projected_messages = []
    for message in selected:
        content = message.get("content")
        if not isinstance(content, str):
            raise MiraCompositionError("canonical conversation content is inexact")
        content = str(content)
        content_bytes = content.encode("utf-8")
        if len(content_bytes) <= _RECENT_CONVERSATION_CONTENT_BYTE_LIMIT:
            projected_content = content
            omitted_content_bytes = 0
            content_truncated = False
        else:
            prefix_length = _RECENT_CONVERSATION_CONTENT_BYTE_LIMIT
            while prefix_length > 0 and not _is_utf8_prefix(
                content_bytes, prefix_length
            ):
                prefix_length -= 1
            projected_content = content_bytes[:prefix_length].decode("utf-8")
            omitted_content_bytes = len(content_bytes) - prefix_length
            content_truncated = True
        projected_messages.append(
            _canonical_json(
                {
                    "role": message.get("role"),
                    "content": projected_content,
                    "turn_id": message.get("turn_id", ""),
                    "content_truncated": content_truncated,
                    "omitted_content_bytes": omitted_content_bytes,
                }
            )
        )

    projection = {
        "source": "ConversationRuntime",
        "conversation_id": conversation_id,
        "canonical_history_sha256": history_digest,
        "canonical_message_count": len(history),
        "omitted_history_message_count": omitted_history_message_count,
        "bounding": {
            "selection": "last_completed_messages",
            "ordering": "canonical_ascending",
            "max_messages": _RECENT_CONVERSATION_MESSAGE_LIMIT,
            "max_content_bytes": _RECENT_CONVERSATION_CONTENT_BYTE_LIMIT,
        },
        "messages": projected_messages,
    }
    while (
        len(_canonical_json(projection).encode("utf-8"))
        > _RECENT_CONVERSATION_ENCODED_BYTE_LIMIT
        and projection["messages"]
    ):
        projection["messages"] = projection["messages"][1:]
        projection["omitted_history_message_count"] += 1
    if len(_canonical_json(projection).encode("utf-8")) > (
        _RECENT_CONVERSATION_ENCODED_BYTE_LIMIT
    ):
        raise MiraCompositionError("recent conversation projection exceeds budget")
    return projection


def _is_utf8_prefix(value: bytes, length: int) -> bool:
    try:
        value[:length].decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def _verify_recent_conversation_projection(
    current_task: CurrentConversationalTaskContext,
    *,
    conversation_id: str,
    history_digest: str,
    expected_projection: dict[str, Any],
) -> None:
    history = current_task.bounded_state.get("recent_conversation")
    if _canonical_json(dict(history)) != _canonical_json(expected_projection):
        raise MiraCompositionError("recent conversation projection is inexact")
    if history.get("conversation_id") != conversation_id:
        raise MiraCompositionError("recent conversation identity is inexact")
    if history.get("canonical_history_sha256") != history_digest:
        raise MiraCompositionError("recent conversation history digest is inexact")
    if current_task.bounded_state.get("recent_conversation_sha256") != (
        _semantic_projection_digest(history)
    ):
        raise MiraCompositionError("recent conversation projection digest is inexact")


def _with_canonical_binding(frame):
    binding = {
        "source_ref": frame.source_ref.uri,
        "source_digest": frame.source_digest,
    }
    return replace(frame, provenance_refs=(*frame.provenance_refs, binding))


def _sha256_text(value: str) -> str:
    if type(value) is not str:
        raise MiraCompositionError("SHA-256 input must be text")
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_json(value: object) -> str:
    return json.dumps(
        _plain_json_tree(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _plain_json_tree(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _plain_json_tree(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain_json_tree(item) for item in value]
    return value


def _semantic_projection_digest(value: object) -> str:
    return _sha256_text(_canonical_json(value))


__all__ = [
    "GoldenMiraRuntimeComposition",
    "MiraCompositionError",
    "MiraCompositionEvidence",
    "MiraProviderEnvelopeRequest",
    "MiraRuntimeShaPins",
    "compose_golden_mira_runtime",
]
