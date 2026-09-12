"""Canonical Runtime transport for admitted C03 semantics."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from julia_core.alignment_os import ProviderAlignmentBoundary, ProviderExecutionEnvelope
from julia_core.context_admission import AdmittedSemanticBundle


@dataclass(frozen=True, slots=True)
class RuntimeTurnRequest:
    """Exact Runtime ingress; no independent semantic source is permitted."""

    binding: AdmittedSemanticBundle
    provider_id: str
    input_mode: str = "text"

    def __post_init__(self) -> None:
        if type(self.binding) is not AdmittedSemanticBundle:
            raise TypeError("Runtime requires an exact AdmittedSemanticBundle")
        self.binding.verify()
        if type(self.provider_id) is not str or not self.provider_id:
            raise ValueError("provider_id is required")
        if type(self.input_mode) is not str:
            raise ValueError("input_mode is inexact")
        if self.input_mode not in {"text", "voice"}:
            raise ValueError("input_mode is unsupported")

    def to_dict(self) -> dict[str, Any]:
        return {
            "binding": self.binding.to_dict(),
            "provider_id": self.provider_id,
            "input_mode": self.input_mode,
        }


@dataclass(frozen=True, slots=True)
class RuntimeBindingTrace:
    """Non-semantic provenance for one Runtime turn."""

    conversation_id: str
    turn_id: str
    gate_receipt: str
    semantic_fingerprint: str
    provider_id: str
    input_mode: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "runtime": {"status": "PASS", "semantic_authority": False},
            "context": {
                "conversation_id": self.conversation_id,
                "turn_id": self.turn_id,
                "gate_receipt": self.gate_receipt,
                "semantic_fingerprint": self.semantic_fingerprint,
            },
            "provider": {"id": self.provider_id, "transport_called": False},
            "interaction": {"mode": self.input_mode},
        }


class JuliaAssistantRuntime:
    """Transport/orchestration owner for the frozen C03-to-Provider seam."""

    def __init__(self, boundary: ProviderAlignmentBoundary | None = None) -> None:
        self.boundary = boundary or ProviderAlignmentBoundary()
        if type(self.boundary) is not ProviderAlignmentBoundary:
            raise TypeError("Runtime requires an exact ProviderAlignmentBoundary")

    def prepare(self, request: RuntimeTurnRequest) -> ProviderExecutionEnvelope:
        if type(self) is not JuliaAssistantRuntime:
            raise TypeError("Runtime requires the exact JuliaAssistantRuntime")
        if type(request) is not RuntimeTurnRequest:
            raise TypeError("Runtime requires an exact RuntimeTurnRequest")
        request.binding.verify()
        envelope = self.boundary.resolve(
            request.binding,
            provider_id=request.provider_id,
            cognitive_mode="conversation",
        )
        envelope.verify()
        return envelope

    def trace(self, request: RuntimeTurnRequest) -> RuntimeBindingTrace:
        if type(request) is not RuntimeTurnRequest:
            raise TypeError("Runtime requires an exact RuntimeTurnRequest")
        request.binding.verify()
        return RuntimeBindingTrace(
            conversation_id=request.binding.conversation_id,
            turn_id=request.binding.turn_id,
            gate_receipt=request.binding.gate_receipt,
            semantic_fingerprint=request.binding.semantic_fingerprint(),
            provider_id=request.provider_id,
            input_mode=request.input_mode,
        )
