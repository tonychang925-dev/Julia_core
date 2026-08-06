"""M2.4 Market Brief Artifact — preserved output of Julia's market analysis.

Stores the structured record of a Market Brief execution for:
  - Evidence traceability (what did Julia base this on?)
  - M7 Feedback Loop (was Julia's interpretation accurate?)
  - Experience formation (what did Julia learn?)

ADR-026 P5: Provider output ≠ Identity truth. Artifacts are governed experience,
not identity or memory.

Market Brief Artifacts do NOT:
  ❌ Write to Identity Memory
  ❌ Mutate Persona
  ❌ Become Relationship Memory
  ✅ Record market observations with provenance
  ✅ Enable future accuracy calibration (M7)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any

CST = timezone(timedelta(hours=8))


@dataclass
class MarketBriefArtifact:
    """A single Market Brief execution record.

    Stores the full trace: what was asked, what capability was invoked,
    what provider supplied, what Julia concluded. This enables:
      - Auditing: "why did Julia say that?"
      - Calibration: "was Julia's interpretation accurate?" (M7)
      - Learning: "what patterns improve Julia's accuracy over time?"
    """

    brief_id: str
    date: str = field(default_factory=lambda: datetime.now(CST).strftime("%Y-%m-%d"))

    # Source trace
    user_query: str = ""
    intent: str = ""

    # Capability trace
    capability_name: str = ""
    capability_status: str = ""
    capability_request_id: str = ""
    provider: str = ""
    schema_version: str = ""

    # Content
    prediction_ids: tuple[str, ...] = ()
    context_block_types: tuple[str, ...] = ()
    julia_response: str = ""

    # Governance
    generated_at: str = field(default_factory=lambda: datetime.now(CST).isoformat())
    mutates_identity: bool = False
    mutates_memory: bool = False
    requires_review: bool = False

    # Evidence chain for M7 feedback
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "brief_id": self.brief_id,
            "date": self.date,
            "user_query": self.user_query,
            "intent": self.intent,
            "capability_name": self.capability_name,
            "capability_status": self.capability_status,
            "capability_request_id": self.capability_request_id,
            "provider": self.provider,
            "schema_version": self.schema_version,
            "prediction_ids": list(self.prediction_ids),
            "context_block_types": list(self.context_block_types),
            "julia_response": self.julia_response[:500],
            "generated_at": self.generated_at,
            "governance": {
                "mutates_identity": self.mutates_identity,
                "mutates_memory": self.mutates_memory,
                "requires_review": self.requires_review,
            },
            "evidence": self.evidence,
        }

    @classmethod
    def from_brief_result(cls, result, julia_response: str = "") -> "MarketBriefArtifact":
        """Create artifact from MarketBriefPipeline result."""
        from julia_core.reasoning.market_brief_pipeline import MarketBriefResult

        return cls(
            brief_id=result.brief_id,
            user_query=result.user_query,
            intent=result.intent.value if hasattr(result.intent, 'value') else str(result.intent),
            capability_name="market.snapshot.read",
            capability_status=result.capability_status,
            capability_request_id=result.capability_request_id,
            provider=result.provider,
            schema_version=result.schema_version,
            prediction_ids=result.prediction_ids,
            context_block_types=tuple(b.block_type for b in result.context_blocks),
            julia_response=julia_response,
            evidence=result.evidence,
            mutates_identity=False,
            mutates_memory=False,
            requires_review=False,
        )


__all__ = ["MarketBriefArtifact"]
