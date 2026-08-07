"""M3.2.7.2b Research Evidence Normalizer — CapabilityResult → EvidenceItem.

Bridges the semantic gap between CapabilityManager's binary success/error
and the MCP tool's inner status (live/unavailable/insufficient).

Rules:
  - MCP inner status=unavailable → Evidence.unavailable (even if outer=success)
  - metric exists in payload → Evidence.success
  - metric missing but payload live → Evidence.insufficient_evidence
  - outer error → Evidence.error
  - missing_policy from probe is preserved
"""

from __future__ import annotations

from julia_core.capability.financial.research.models import EvidenceItem, ResearchProbe

# ── Normalizer ──────────────────────────────────────────────────────────────

class ResearchEvidenceNormalizer:
    """Maps CapabilityResult → EvidenceItem with inner-status awareness.

    CapabilityManager returns 'success' whenever provider.execute() doesn't throw.
    But MCP tools return {"status": "unavailable", ...} inside the data payload.
    This normalizer inspects the inner semantic status.
    """

    def normalize(self, probe: ResearchProbe, capability_result) -> EvidenceItem:
        """Normalize one CapabilityResult into an EvidenceItem.

        Args:
            probe: the ResearchProbe that generated this request
            capability_result: CapabilityResult from CapabilityManager.execute()

        Returns:
            EvidenceItem with resolved status, derived_value, provenance
        """
        item = EvidenceItem(
            requirement_id=probe.requirement_id,
            probe_id=probe.probe_id,
            capability_request_id=capability_result.capability_name
                if hasattr(capability_result, 'capability_name') else "",
            derived_metric=probe.derive_metric,
            missing_policy=probe.missing_policy,
        )

        # Step 1: Outer status — CapabilityManager-level errors
        if hasattr(capability_result, 'status'):
            outer = capability_result.status
            if outer in ("denied", "unknown", "error"):
                item.status = outer
                item.provenance = {"error": getattr(capability_result, 'error_message', '')}
                return item
            if outer == "unavailable":
                item.status = "unavailable"
                item.provenance = {"error": getattr(capability_result, 'error_message', '')}
                return item

        # Step 2: Unwrap provider envelope {"provider", "data": {...}}
        data = getattr(capability_result, 'data', {}) or {}
        inner = data.get("data", data) if isinstance(data, dict) else {}

        # Step 3: Inner MCP tool status
        inner_status = inner.get("status", "live") if isinstance(inner, dict) else "live"

        if inner_status == "unavailable":
            item.status = "unavailable"
            item.provenance = {
                "reason": inner.get("reason", ""),
                "data_status": inner.get("data_status", ""),
                "source_kind": inner.get("source_kind", ""),
            }
            return item

        if inner_status in ("error", "denied"):
            item.status = inner_status
            return item

        # Step 4: Metric extraction
        if inner_status in ("live", "success", "partial") and isinstance(inner, dict):
            metric = probe.derive_metric
            if metric and metric in inner:
                item.derived_value = inner[metric]
                item.status = "success"
            elif metric:
                # Metric not present in live response → insufficient
                item.status = "insufficient_evidence"
                item.provenance = {
                    "reason": f"metric '{metric}' not found in live payload",
                    "available_keys": sorted(inner.keys())[:10],
                    "source_kind": inner.get("source_kind", ""),
                }
            else:
                item.status = "success"
                item.raw_value = inner

            # Preserve provenance
            item.provenance = {
                **(item.provenance or {}),
                "source_kind": inner.get("source_kind", ""),
                "data_note": inner.get("data_note", ""),
            }
            return item

        # Fallback
        item.status = "insufficient_evidence"
        return item


def normalize_bundle(
    probes: list[ResearchProbe],
    results: list,  # CapabilityResult[]
) -> list[EvidenceItem]:
    """Normalize all probe results into EvidenceItems."""
    normalizer = ResearchEvidenceNormalizer()
    items = []
    for probe, result in zip(probes, results):
        items.append(normalizer.normalize(probe, result))
    return items


__all__ = ["ResearchEvidenceNormalizer", "normalize_bundle"]
