"""Core-side Market event research contracts and adapter seam."""

from julia_core.research.adapter import (
    MARKET_EVENT_CONTRACT_VERSION,
    MarketEventContractError,
    MarketEventResearchAdapter,
    RESEARCH_EVENT_ENRICH_CAPABILITY,
    RESEARCH_EVENT_ENRICH_SCOPE,
)
from julia_core.research.contracts import (
    ContentBinding,
    MarketEvent,
    MarketEventContext,
    MarketEventRelation,
    NormalizedResearchEnrichment,
    ResearchClaim,
    ResearchSemanticResult,
    SourceObservationEvidence,
    SourceObservationFailure,
    SourceRecord,
    VerificationState,
)
from julia_core.research.normalizer import (
    ResearchEvidenceNormalizer,
    ResearchNormalizationError,
)
from julia_core.research.judgment import (
    PRELIMINARY_RESEARCH_JUDGMENT_VERSION,
    PreliminaryResearchJudgment,
    ResearchJudgmentContextBuilder,
    ResearchJudgmentInputError,
    ResearchJudgmentParseError,
    ResearchJudgmentParser,
)
from julia_core.research.registration import (
    RESEARCH_EVENT_ENRICH_PROVIDER,
    register_research_event_enrichment,
)

__all__ = [
    "ContentBinding",
    "MARKET_EVENT_CONTRACT_VERSION",
    "MarketEvent",
    "MarketEventContext",
    "MarketEventContractError",
    "MarketEventRelation",
    "MarketEventResearchAdapter",
    "NormalizedResearchEnrichment",
    "PRELIMINARY_RESEARCH_JUDGMENT_VERSION",
    "RESEARCH_EVENT_ENRICH_CAPABILITY",
    "RESEARCH_EVENT_ENRICH_PROVIDER",
    "RESEARCH_EVENT_ENRICH_SCOPE",
    "ResearchClaim",
    "ResearchEvidenceNormalizer",
    "ResearchJudgmentContextBuilder",
    "ResearchJudgmentInputError",
    "ResearchJudgmentParseError",
    "ResearchJudgmentParser",
    "ResearchNormalizationError",
    "ResearchSemanticResult",
    "SourceObservationEvidence",
    "SourceObservationFailure",
    "SourceRecord",
    "VerificationState",
    "register_research_event_enrichment",
]
