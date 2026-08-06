"""M3.2.1 Intelligence Adapter — DecisionEnvelope → ObservationEvent.

ADR-030 Section 1: The designated boundary between domain intelligence
and Julia cognitive runtime. ai_theme_app internal fields (theme_id,
gate_score, embedding) MUST NOT leak through this adapter.

This is a thin translator, not an analyst. Zero LLM dependency.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from julia_core.awareness.models import ObservationEvent


# ── Forbidden field names that must NOT appear in ObservationEvent ──────────

FORBIDDEN_DOMAIN_FIELDS = frozenset({
    "theme_id", "gate_score", "embedding", "vector_score",
    "source_table", "internal_rank", "algorithm_version",
})


@dataclass
class IntelligenceAdapter:
    """Converts domain intelligence output → Julia ObservationEvents.

    Rules:
      1. Strip domain-specific internal fields
      2. Map signal_level → ObservationEvent delta
      3. Preserve evidence_refs for audit trail
      4. Attach provider metadata
    """

    def convert(self, capability_result: dict) -> list[ObservationEvent]:
        """Convert a market.intelligence.observe result to ObservationEvents.

        Returns one ObservationEvent per observation in the result.
        Silently strips forbidden domain fields.
        """
        observations = capability_result.get("observations", [])
        if not observations:
            return []

        provider_name = capability_result.get("source", "unknown")
        schema_version = capability_result.get("schema_version", "1.0")
        generated_at = capability_result.get("generated_at", "")

        events = []
        for obs in observations:
            event = ObservationEvent(
                source=provider_name,
                domain="market",
                event_type=self._map_event_type(obs.get("type", "unknown")),
                subject=obs.get("theme", obs.get("subject", "unknown")),
                change_type=obs.get("type", "unknown"),
                delta=str(obs.get("signal_level", "L1")),
                payload=self._clean_payload(obs, provider_name, schema_version, generated_at),
                evidence_refs=self._extract_evidence_refs(obs),
                confidence=float(obs.get("confidence", 0.5)),
            )
            events.append(event)

        return events

    def _map_event_type(self, obs_type: str) -> str:
        """Map domain event type → Julia observation event type."""
        return f"world.market.{obs_type.replace('.', '_')}"

    def _clean_payload(self, obs: dict, provider: str, schema: str, generated_at: str) -> dict:
        """Extract safe payload fields. Strip forbidden domain fields."""
        payload = {
            "provider_name": provider,
            "schema_version": schema,
            "generated_at": generated_at,
            "summary": obs.get("summary", ""),
            "evidence_labels": obs.get("evidence", []),
            "prediction_id": obs.get("prediction_id", ""),
            "decision_envelope_ref": obs.get("decision_envelope_ref", ""),
            "signal_level": obs.get("signal_level", "L1"),
        }
        # Explicitly filter forbidden fields
        for key in list(payload.keys()):
            if key in FORBIDDEN_DOMAIN_FIELDS:
                del payload[key]
        return payload

    def _extract_evidence_refs(self, obs: dict) -> tuple[str, ...]:
        refs = []
        if obs.get("prediction_id"):
            refs.append(obs["prediction_id"])
        if obs.get("decision_envelope_ref"):
            refs.append(obs["decision_envelope_ref"])
        return tuple(refs)

    def validate_schema(self, capability_result: dict) -> tuple[bool, str]:
        """Validate incoming schema version. Unknown versions → reject."""
        version = capability_result.get("schema_version", "")
        if not version:
            return False, "missing schema_version"
        # M3.2: accept 1.0 or 1.1
        if version in ("1.0", "1.1"):
            return True, "ok"
        return False, f"unknown schema_version: {version} — must be 1.0 or 1.1"


__all__ = ["IntelligenceAdapter", "FORBIDDEN_DOMAIN_FIELDS"]
