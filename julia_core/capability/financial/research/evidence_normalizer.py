"""M3.2.7.2c Research Evidence Normalizer — CapabilityResult → EvidenceItem.

Bridges outer CapabilityManager success vs MCP inner status.
Supports nested value_path (e.g. "derived.regime_assessment.value").
Fail-closed on cardinality mismatch.
"""

from __future__ import annotations

from julia_core.capability.financial.research.models import EvidenceItem, ResearchProbe


class EvidenceCardinalityMismatch(Exception):
    """Probe count != result count — evidence chain broken."""


class ResearchEvidenceNormalizer:
    """Normalizes CapabilityResult → EvidenceItem with inner-status awareness.

    Rules:
      outer error/unavailable/denied → Evidence.error/unavailable
      outer success + inner unavailable → Evidence.unavailable
      outer success + inner live + value_path resolves → Evidence.success
      outer success + inner live + value_path miss → Evidence.insufficient_evidence
      missing_policy preserved from probe
    """

    def normalize(self, probe: ResearchProbe, capability_result) -> EvidenceItem:
        item = EvidenceItem(
            requirement_id=probe.requirement_id,
            probe_id=probe.probe_id,
            capability_request_id=probe.request.request_id if probe.request else "",
            derived_metric=probe.derive_metric,
            missing_policy=probe.missing_policy,
        )

        # Set requested_as_of from probe arguments (request-side provenance)
        # Applies to all return paths: success, unavailable, error, insufficient.
        if probe.request:
            req_args = getattr(probe.request, "arguments", {}) or {}
            req_as_of = req_args.get("as_of", "")
            if req_as_of:
                if not item.provenance:
                    item.provenance = {}
                item.provenance["requested_as_of"] = str(req_as_of)

        # Step 1: Outer status
        if hasattr(capability_result, 'status'):
            outer = capability_result.status
            if outer in ("denied", "unknown", "error", "unavailable"):
                item.status = outer
                item.provenance = {
                    "outer_status": outer,
                    "error": getattr(capability_result, 'error_message', ''),
                }
                return item

        # Step 2: Unwrap provider envelope
        data = getattr(capability_result, 'data', {}) or {}
        inner = data.get("data", data) if isinstance(data, dict) else {}

        # Step 3: Inner MCP status
        if isinstance(inner, dict):
            inner_status = inner.get("status", "live")
        else:
            inner_status = "live"

        if inner_status == "unavailable":
            item.status = "unavailable"
            item.provenance = {
                "reason": inner.get("reason", ""),
                "source_kind": inner.get("source_kind", ""),
            }
            return item

        # Step 4: Value extraction via value_path (P0-3: nested support)
        if inner_status in ("live", "success", "partial") and isinstance(inner, dict):
            value_path = probe.derive_metric  # e.g. "derived.regime_assessment.value"
            value, found = _resolve_path(inner, value_path) if value_path else (inner, True)

            if found and value is not None:
                item.derived_value = value
                item.status = "success"
            elif value_path:
                item.status = "insufficient_evidence"
                item.provenance = {
                    "reason": f"value_path '{value_path}' not resolved in live payload",
                    "available_keys": _top_keys(inner),
                    "source_kind": inner.get("source_kind", ""),
                }
            else:
                item.status = "success"
                item.raw_value = inner

            if not item.provenance:
                item.provenance = {}
            item.provenance["source_kind"] = inner.get("source_kind", "")
            item.provenance["data_note"] = inner.get("data_note", "")
            # Propagate temporal provenance for anti-hindsight as_of gate
            for ts_field in ("available_at", "observed_at", "effective_at"):
                val = inner.get(ts_field, "")
                if val:
                    item.provenance[ts_field] = str(val)
            return item

        item.status = "insufficient_evidence"
        return item


def _resolve_path(data: dict, path: str) -> tuple:
    """Resolve dotted path into nested dict. Returns (value, found)."""
    parts = path.split(".")
    current = data
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return (None, False)
    return (current, True)


def _top_keys(data: dict) -> list:
    return sorted(data.keys())[:10]


def normalize_bundle(
    probes: list[ResearchProbe],
    results: list,
) -> list[EvidenceItem]:
    """Normalize all probes → EvidenceItems. Fail on cardinality mismatch."""
    if len(probes) != len(results):
        raise EvidenceCardinalityMismatch(
            f"probe count {len(probes)} != result count {len(results)}"
        )
    normalizer = ResearchEvidenceNormalizer()
    return [normalizer.normalize(p, r) for p, r in zip(probes, results)]


__all__ = [
    "ResearchEvidenceNormalizer",
    "normalize_bundle",
    "EvidenceCardinalityMismatch",
]
