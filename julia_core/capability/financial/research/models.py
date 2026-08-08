"""M3.2.7 Research Models — typed Hypothesis, ResearchPlan, EvidenceBundle.

StrategyCard provides: what to investigate.
These models provide: how Julia structures and tracks the investigation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from uuid import uuid4

CST = timezone(timedelta(hours=8))


@dataclass
class Hypothesis:
    """One candidate interpretation from a StrategyCard. Initially untested."""
    state: str                        # "leader_divergence.active_divergence"
    canonical_state: str              # "active_divergence"
    evidence_pattern: dict = field(default_factory=dict)
    strategy_guidance: dict = field(default_factory=dict)
    status: str = "untested"          # untested | supported | contradicted | partial | insufficient_evidence


@dataclass
class ResearchProbe:
    """One capability request with stable identity. No regex on reason strings."""
    probe_id: str = field(default_factory=lambda: f"probe_{uuid4().hex}")
    requirement_id: str = ""
    binding_id: str = ""
    request: Any = None
    derive_metric: str = ""
    missing_policy: str = "INSUFFICIENT_EVIDENCE"


@dataclass
class ResearchPlan:
    """Compiled plan: StrategyCard + SubjectContext → executable research."""
    research_case_id: str = field(default_factory=lambda: f"rc_{uuid4().hex}")
    subject_key: str = ""
    subject_name: str = ""
    trade_date: str = ""
    triggered_card: str = ""
    trigger_transition: str = ""
    parent_case_id: str = ""
    candidate_hypotheses: list[dict] = field(default_factory=list)
    probes: list[ResearchProbe] = field(default_factory=list)
    research_questions: list[dict] = field(default_factory=list)
    missing_requirements: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(CST).isoformat())

    @property
    def capability_requests(self) -> list:
        """Compatibility: extract CapabilityRequests from probes."""
        return [p.request for p in self.probes if p.request is not None]


@dataclass
class EvidenceItem:
    """One piece of evidence gathered for a research requirement."""
    requirement_id: str
    probe_id: str = ""
    capability_request_id: str = ""
    status: str = "pending"           # pending | success | unavailable | error
    raw_value: object = None
    derived_metric: str = ""
    derived_value: object = None
    provenance: dict = field(default_factory=dict)
    missing_policy: str = "INSUFFICIENT_EVIDENCE"


@dataclass
class EvidenceBundle:
    """All evidence gathered for one ResearchPlan execution."""
    research_case_id: str
    subject_key: str
    as_of: str
    evidence: list[EvidenceItem] = field(default_factory=list)
    evidence_count: int = 0
    success_count: int = 0
    unavailable_count: int = 0
    error_count: int = 0


# Import at bottom to avoid circular
from julia_core.capability.models import CapabilityRequest  # noqa


__all__ = ["Hypothesis", "ResearchProbe", "ResearchPlan", "EvidenceItem", "EvidenceBundle"]
