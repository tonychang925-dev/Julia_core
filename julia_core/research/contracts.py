"""C1 Market-event research contracts.

This module keeps provider-derived research semantics separate from runtime
source observations. It defines no final Julia judgment and invokes no model.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from julia_core.capability.models import Evidence, ToolResult


class VerificationState(str, Enum):
    """Core-owned source verification states."""

    SOURCE_VERIFIED = "SOURCE_VERIFIED"
    REPORT_ONLY = "REPORT_ONLY"
    NOT_PROVEN = "NOT_PROVEN"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True)
class MarketEventRelation:
    """One relation from the frozen M0 market.event.read contract."""

    subject_key: str
    subject_name: str
    relation_type: str
    confidence: float
    match_reason: str
    evidence: str
    source: str
    source_trace_id: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class MarketEvent:
    """Exact frozen M0 market.event.read payload.

    No unrelated symbol, entity, severity, lifecycle, or analyst field is
    admitted here.
    """

    event_id: int
    event_type: str
    summary: str
    direction: str
    confidence: float
    occurred_at: str | None
    title: str | None
    source_category: str
    source_name: str | None
    source_url: str | None
    source_trace_id: str
    news_id: int | None


@dataclass(frozen=True, slots=True)
class MarketEventContext:
    """The complete M0 event read payload passed to research enrichment."""

    event: MarketEvent
    theme_relations: tuple[MarketEventRelation, ...] = ()


@dataclass(frozen=True, slots=True)
class ResearchClaim:
    """Provider semantic claim; never source truth by itself."""

    text: str
    source_record_ids: tuple[str, ...]
    claim_id: str = ""
    provider_verification_state: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "text", str(self.text))
        object.__setattr__(self, "source_record_ids", tuple(self.source_record_ids))
        object.__setattr__(self, "provider_verification_state", str(self.provider_verification_state))
        if not self.text.strip():
            raise ValueError("research claim text is required")
        if not self.claim_id:
            object.__setattr__(self, "claim_id", f"claim_{abs(hash((self.text, self.source_record_ids)))}")


@dataclass(frozen=True, slots=True)
class ResearchSemanticResult:
    """Provider semantic plane for research.event.enrich output."""

    factual_summary: str
    claims: tuple[ResearchClaim, ...] = ()
    contradictions: tuple[str, ...] = ()
    unknowns: tuple[str, ...] = ()
    timeline: tuple[dict[str, Any], ...] = ()
    related_entities: tuple[dict[str, Any], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "claims", tuple(self.claims))
        object.__setattr__(self, "contradictions", tuple(self.contradictions))
        object.__setattr__(self, "unknowns", tuple(self.unknowns))
        object.__setattr__(self, "timeline", tuple(dict(item) for item in self.timeline))
        object.__setattr__(self, "related_entities", tuple(dict(item) for item in self.related_entities))


@dataclass(frozen=True, slots=True)
class SourceRecord:
    """A provider/runtime source pointer or retained material record."""

    source_record_id: str
    source_kind: str
    source_ref: str
    capture_status: str = "pending"
    fetch_status: str = "pending"
    observed_at: str = ""
    source_url: str | None = None
    raw_response_ref: str = ""
    content_ref: str = ""
    content_digest: str = ""
    provenance: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ContentBinding:
    """Claim-source material binding required for SOURCE_VERIFIED."""

    source_record_id: str
    content_ref: str
    digest: str
    extract_ref: str = ""
    locator: str = ""
    provenance: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SourceObservationFailure:
    """Exact observation-plane failure truth."""

    code: str
    message: str
    retryable: bool | None = None


@dataclass(frozen=True, slots=True)
class SourceObservationEvidence:
    """Runtime observation plane; deliberately not ResearchSemanticResult."""

    source_records: tuple[SourceRecord, ...]
    content_bindings: tuple[ContentBinding, ...]
    evidence: tuple[Evidence, ...]
    raw_response_refs: tuple[str, ...]
    observed_at: str
    provenance: dict[str, Any]
    correlation_id: str
    available: bool
    failure: SourceObservationFailure | None = None
    claim_verification_states: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class NormalizedResearchEnrichment:
    """Normalized C1 output carrying the two separated truth planes."""

    semantic_result: ResearchSemanticResult
    observation: SourceObservationEvidence
    tool_result: ToolResult


__all__ = [
    "ContentBinding",
    "MarketEvent",
    "MarketEventContext",
    "MarketEventRelation",
    "NormalizedResearchEnrichment",
    "ResearchClaim",
    "ResearchSemanticResult",
    "SourceObservationEvidence",
    "SourceObservationFailure",
    "SourceRecord",
    "VerificationState",
]
