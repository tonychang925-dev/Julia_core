"""DIA-7 R2.0 — Assistant Continuity Integration canonical contract.

Assistant continuity integration consumes DIA-7 ContinuityState snapshots. It
binds an assistant session to the exact projected state identity it consumed;
it does not create, mutate, repair, or reinterpret continuity truth.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Protocol, runtime_checkable

from julia_core.continuity_projection import ContinuityState, ProjectedContinuityClaim

CANONICAL_VERSION = "dia7-assistant-continuity-r2-v1"
PACKAGE_DOMAIN_SEPARATOR = "julia_core.assistant_continuity.package.v1"
BINDING_DOMAIN_SEPARATOR = "julia_core.assistant_continuity.session_binding.v1"
STORE_DOMAIN_SEPARATOR = "julia_core.assistant_continuity.binding_store.v1"
RESPONSE_CONTEXT_DOMAIN_SEPARATOR = "julia_core.assistant_continuity.response_context.v1"
BINDING_ALGORITHM_REVISION = "dia7-r2-binding-v1"
PACKAGE_ALGORITHM_REVISION = "dia7-r2-package-v1"


def _require_non_empty_str(name: str, value: object) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{name} must be a non-empty str")


def _require_tuple(name: str, value: object) -> None:
    if type(value) is not tuple:
        raise ValueError(f"{name} must be a tuple")


def _require_sha256_hex(name: str, value: object) -> None:
    _require_non_empty_str(name, value)
    if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        raise ValueError(f"{name} must be a 64-character lowercase SHA-256 hex digest")


def _frame(value: str) -> bytes:
    _require_non_empty_str("canonical field", value)
    encoded = value.encode("utf-8")
    return str(len(encoded)).encode("ascii") + b":" + encoded + b"\n"


def _field(name: str, value: str) -> bytes:
    return _frame(name) + _frame(value)


def _digest_hex(data: bytes) -> str:
    return sha256(data).hexdigest()


@dataclass(frozen=True, init=False)
class AssistantContinuityStatePackage:
    continuity_state: ContinuityState
    continuity_state_digest: str
    source_graph_digest: str
    projection_policy_fingerprint: str
    active_claims: tuple[ProjectedContinuityClaim, ...]
    unresolved_conflicts: tuple[ProjectedContinuityClaim, ...]
    package_digest: str
    schema_version: str

    def __init__(self, continuity_state: ContinuityState) -> None:
        if type(continuity_state) is not ContinuityState:
            raise ValueError("AssistantContinuityStatePackage requires exact ContinuityState")
        expected_digest = _digest_hex(continuity_state.semantic_canonical_bytes(include_digest=False))
        if continuity_state.continuity_state_digest != expected_digest:
            raise ValueError("ContinuityState digest mismatch")
        active_claims = continuity_state.active_claims
        unresolved_conflicts = continuity_state.unresolved_conflicts
        _require_tuple("AssistantContinuityStatePackage.active_claims", active_claims)
        _require_tuple("AssistantContinuityStatePackage.unresolved_conflicts", unresolved_conflicts)
        if not all(type(claim) is ProjectedContinuityClaim for claim in active_claims + unresolved_conflicts):
            raise ValueError("AssistantContinuityStatePackage claims must be projected continuity claims")
        object.__setattr__(self, "continuity_state", continuity_state)
        object.__setattr__(self, "continuity_state_digest", continuity_state.continuity_state_digest)
        object.__setattr__(self, "source_graph_digest", continuity_state.source_graph_digest)
        object.__setattr__(self, "projection_policy_fingerprint", continuity_state.projection_policy_fingerprint)
        object.__setattr__(self, "active_claims", active_claims)
        object.__setattr__(self, "unresolved_conflicts", unresolved_conflicts)
        object.__setattr__(self, "schema_version", CANONICAL_VERSION)
        object.__setattr__(self, "package_digest", _digest_hex(self.semantic_canonical_bytes(include_digest=False)))

    @classmethod
    def from_state(cls, continuity_state: ContinuityState) -> "AssistantContinuityStatePackage":
        return cls(continuity_state)

    def semantic_canonical_bytes(self, *, include_digest: bool = True) -> bytes:
        out = (
            _field("package.domain", PACKAGE_DOMAIN_SEPARATOR)
            + _field("package.schema_version", self.schema_version)
            + _field("package.algorithm_revision", PACKAGE_ALGORITHM_REVISION)
            + _field("package.state_digest", self.continuity_state_digest)
            + _field("package.source_graph_digest", self.source_graph_digest)
            + _field("package.policy_fingerprint", self.projection_policy_fingerprint)
            + _field("package.active_claim_count", str(len(self.active_claims)))
        )
        for claim in self.active_claims:
            out += _field("package.active_claim", claim.canonical_bytes().decode("utf-8"))
        out += _field("package.unresolved_conflict_count", str(len(self.unresolved_conflicts)))
        for claim in self.unresolved_conflicts:
            out += _field("package.unresolved_conflict", claim.canonical_bytes().decode("utf-8"))
        if include_digest:
            out += _field("package.digest", self.package_digest)
        return out


@dataclass(frozen=True, init=False)
class AssistantContinuitySessionBinding:
    session_id: str
    continuity_state_digest: str
    source_graph_digest: str
    projection_policy_fingerprint: str
    package_digest: str
    binding_digest: str
    schema_version: str

    def __init__(self, session_id: str, package: AssistantContinuityStatePackage) -> None:
        _require_non_empty_str("AssistantContinuitySessionBinding.session_id", session_id)
        _validate_package_integrity(package)
        object.__setattr__(self, "session_id", session_id)
        object.__setattr__(self, "continuity_state_digest", package.continuity_state_digest)
        object.__setattr__(self, "source_graph_digest", package.source_graph_digest)
        object.__setattr__(self, "projection_policy_fingerprint", package.projection_policy_fingerprint)
        object.__setattr__(self, "package_digest", package.package_digest)
        object.__setattr__(self, "schema_version", CANONICAL_VERSION)
        object.__setattr__(self, "binding_digest", _digest_hex(self.semantic_canonical_bytes(include_digest=False)))

    @classmethod
    def bind(cls, session_id: str, package: AssistantContinuityStatePackage) -> "AssistantContinuitySessionBinding":
        return cls(session_id, package)

    def semantic_canonical_bytes(self, *, include_digest: bool = True) -> bytes:
        out = (
            _field("binding.domain", BINDING_DOMAIN_SEPARATOR)
            + _field("binding.schema_version", self.schema_version)
            + _field("binding.algorithm_revision", BINDING_ALGORITHM_REVISION)
            + _field("binding.session_id", self.session_id)
            + _field("binding.state_digest", self.continuity_state_digest)
            + _field("binding.source_graph_digest", self.source_graph_digest)
            + _field("binding.policy_fingerprint", self.projection_policy_fingerprint)
            + _field("binding.package_digest", self.package_digest)
        )
        if include_digest:
            out += _field("binding.digest", self.binding_digest)
        return out


@dataclass(frozen=True)
class ContinuityConsumptionAudit:
    session_id: str
    binding_digest: str
    continuity_state_digest: str
    diagnostics: tuple[str, ...]
    consumed_at: str

    def __post_init__(self) -> None:
        _require_non_empty_str("ContinuityConsumptionAudit.session_id", self.session_id)
        _require_sha256_hex("ContinuityConsumptionAudit.binding_digest", self.binding_digest)
        _require_sha256_hex("ContinuityConsumptionAudit.continuity_state_digest", self.continuity_state_digest)
        _require_tuple("ContinuityConsumptionAudit.diagnostics", self.diagnostics)
        if not all(type(item) is str for item in self.diagnostics):
            raise ValueError("ContinuityConsumptionAudit.diagnostics must contain str only")
        _require_non_empty_str("ContinuityConsumptionAudit.consumed_at", self.consumed_at)


@dataclass(frozen=True, init=False)
class AssistantContinuityResponseContext:
    session_id: str
    session_binding: AssistantContinuitySessionBinding
    active_claims: tuple[ProjectedContinuityClaim, ...]
    unresolved_conflicts: tuple[ProjectedContinuityClaim, ...]
    response_context_digest: str
    schema_version: str

    def __init__(self, binding: AssistantContinuitySessionBinding, package: AssistantContinuityStatePackage) -> None:
        if type(binding) is not AssistantContinuitySessionBinding:
            raise ValueError("AssistantContinuityResponseContext requires exact AssistantContinuitySessionBinding")
        if type(package) is not AssistantContinuityStatePackage:
            raise ValueError("AssistantContinuityResponseContext requires exact AssistantContinuityStatePackage")
        _validate_binding_integrity(binding)
        _validate_package_integrity(package)
        _assert_binding_matches_package(binding, package)
        object.__setattr__(self, "session_id", binding.session_id)
        object.__setattr__(self, "session_binding", binding)
        object.__setattr__(self, "active_claims", package.active_claims)
        object.__setattr__(self, "unresolved_conflicts", package.unresolved_conflicts)
        object.__setattr__(self, "schema_version", CANONICAL_VERSION)
        object.__setattr__(self, "response_context_digest", _digest_hex(self.semantic_canonical_bytes(include_digest=False)))

    def semantic_canonical_bytes(self, *, include_digest: bool = True) -> bytes:
        out = (
            _field("response_context.domain", RESPONSE_CONTEXT_DOMAIN_SEPARATOR)
            + _field("response_context.schema_version", self.schema_version)
            + _field("response_context.session_id", self.session_id)
            + _field("response_context.binding_digest", self.session_binding.binding_digest)
            + _field("response_context.state_digest", self.session_binding.continuity_state_digest)
            + _field("response_context.source_graph_digest", self.session_binding.source_graph_digest)
            + _field("response_context.policy_fingerprint", self.session_binding.projection_policy_fingerprint)
            + _field("response_context.active_claim_count", str(len(self.active_claims)))
        )
        for claim in self.active_claims:
            out += _field("response_context.active_claim", claim.canonical_bytes().decode("utf-8"))
        out += _field("response_context.unresolved_conflict_count", str(len(self.unresolved_conflicts)))
        for claim in self.unresolved_conflicts:
            out += _field("response_context.unresolved_conflict", claim.canonical_bytes().decode("utf-8"))
        if include_digest:
            out += _field("response_context.digest", self.response_context_digest)
        return out


class ContinuityStateBindingStore:
    """R2.0 in-memory binding store contract for restart/replay validation.

    Persistence is deliberately outside R2.0. This store only models exact
    binding lookup and cross-binding validation semantics.
    """

    def __init__(self) -> None:
        self._bindings: dict[str, AssistantContinuitySessionBinding] = {}

    def save(self, binding: AssistantContinuitySessionBinding) -> None:
        _validate_binding_integrity(binding)
        existing = self._bindings.get(binding.session_id)
        if existing is not None and existing.binding_digest != binding.binding_digest:
            raise ValueError("session already bound to different continuity state")
        self._bindings[binding.session_id] = binding

    def load(self, session_id: str) -> AssistantContinuitySessionBinding:
        _require_non_empty_str("ContinuityStateBindingStore.session_id", session_id)
        binding = self._bindings.get(session_id)
        if binding is None:
            raise ValueError("no continuity binding for session")
        _validate_binding_integrity(binding)
        return binding

    def replay_validate(self, session_id: str, package: AssistantContinuityStatePackage) -> AssistantContinuitySessionBinding:
        binding = self.load(session_id)
        _validate_package_integrity(package)
        _assert_binding_matches_package(binding, package)
        return binding


@runtime_checkable
class ContinuityStateInputPort(Protocol):
    def read_package(self, session_id: str) -> AssistantContinuityStatePackage:
        ...


class StrictAssistantContinuityBinder:
    def bind_for_session(
        self,
        session_id: str,
        package: AssistantContinuityStatePackage,
        *,
        expected_state_digest: str,
        expected_source_graph_digest: str,
        expected_projection_policy_fingerprint: str,
    ) -> AssistantContinuitySessionBinding:
        _require_sha256_hex("expected_state_digest", expected_state_digest)
        _require_sha256_hex("expected_source_graph_digest", expected_source_graph_digest)
        _require_sha256_hex("expected_projection_policy_fingerprint", expected_projection_policy_fingerprint)
        _validate_package_integrity(package)
        if package.continuity_state_digest != expected_state_digest:
            raise ValueError("continuity state digest mismatch")
        if package.source_graph_digest != expected_source_graph_digest:
            raise ValueError("source graph digest mismatch")
        if package.projection_policy_fingerprint != expected_projection_policy_fingerprint:
            raise ValueError("projection policy fingerprint mismatch")
        return AssistantContinuitySessionBinding.bind(session_id, package)

    def response_context(self, binding: AssistantContinuitySessionBinding, package: AssistantContinuityStatePackage) -> AssistantContinuityResponseContext:
        return AssistantContinuityResponseContext(binding, package)


def _validate_package_integrity(package: AssistantContinuityStatePackage) -> None:
    if type(package) is not AssistantContinuityStatePackage:
        raise ValueError("expected exact AssistantContinuityStatePackage")
    if type(package.continuity_state) is not ContinuityState:
        raise ValueError("package continuity_state must be exact ContinuityState")
    expected_state_digest = _digest_hex(package.continuity_state.semantic_canonical_bytes(include_digest=False))
    if expected_state_digest != package.continuity_state_digest:
        raise ValueError("package continuity state digest mismatch")
    if package.continuity_state.continuity_state_digest != package.continuity_state_digest:
        raise ValueError("package stale continuity state digest")
    if package.source_graph_digest != package.continuity_state.source_graph_digest:
        raise ValueError("package source graph digest mismatch")
    if package.projection_policy_fingerprint != package.continuity_state.projection_policy_fingerprint:
        raise ValueError("package projection policy fingerprint mismatch")
    if package.active_claims != package.continuity_state.active_claims:
        raise ValueError("package active claims mismatch")
    if package.unresolved_conflicts != package.continuity_state.unresolved_conflicts:
        raise ValueError("package unresolved conflicts mismatch")
    expected_package_digest = _digest_hex(package.semantic_canonical_bytes(include_digest=False))
    if expected_package_digest != package.package_digest:
        raise ValueError("package digest mismatch")


def _validate_binding_integrity(binding: AssistantContinuitySessionBinding) -> None:
    if type(binding) is not AssistantContinuitySessionBinding:
        raise ValueError("expected exact AssistantContinuitySessionBinding")
    _require_non_empty_str("binding.session_id", binding.session_id)
    _require_sha256_hex("binding.continuity_state_digest", binding.continuity_state_digest)
    _require_sha256_hex("binding.source_graph_digest", binding.source_graph_digest)
    _require_sha256_hex("binding.projection_policy_fingerprint", binding.projection_policy_fingerprint)
    _require_sha256_hex("binding.package_digest", binding.package_digest)
    expected_binding_digest = _digest_hex(binding.semantic_canonical_bytes(include_digest=False))
    if expected_binding_digest != binding.binding_digest:
        raise ValueError("binding digest mismatch")


def _assert_binding_matches_package(binding: AssistantContinuitySessionBinding, package: AssistantContinuityStatePackage) -> None:
    if binding.continuity_state_digest != package.continuity_state_digest:
        raise ValueError("binding continuity state digest mismatch")
    if binding.source_graph_digest != package.source_graph_digest:
        raise ValueError("binding source graph digest mismatch")
    if binding.projection_policy_fingerprint != package.projection_policy_fingerprint:
        raise ValueError("binding projection policy fingerprint mismatch")
    if binding.package_digest != package.package_digest:
        raise ValueError("binding package digest mismatch")
