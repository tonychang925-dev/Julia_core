"""Governed Julia Diary semantic domain.

AT-12 boundary: ReflectionTrigger is only an opportunity; NO_ENTRY is a valid
terminal reflection result and creates no canonical Diary artifact.
"""

from .provenance import (
    DiaryProvenanceReport,
    DiarySourceResolution,
    DiarySourceResolver,
    SourceRefState,
    classify_source_namespace,
    validate_diary_provenance,
)
from .models import (
    AcceptedDiaryEntry,
    DiaryCandidate,
    DiaryProvenance,
    DiarySourceRef,
    NoEntry,
    NO_ENTRY,
    ReflectionResult,
)
from .reflection_decision import ReflectionOpportunity, decide_trivial_reflection
from .repository_protocol import DiaryRepository
from .reflection_pipeline import ReflectionExecutionResult, run_trivial_reflection_opportunity
from .significant_event import (
    DiaryDurableCommit,
    DiaryGovernanceAcceptance,
    GroundedSignificantEvent,
    commit_accepted_entry_durable,
    create_diary_candidate,
    promote_candidate_to_accepted_entry,
    validate_canonical_source_refs,
    validate_first_person_reflection_body,
)

__all__ = [
    "AcceptedDiaryEntry",
    "DiaryCandidate",
    "DiaryProvenance",
    "DiaryProvenanceReport",
    "DiarySourceResolution",
    "DiarySourceResolver",
    "DiaryRepository",
    "DiarySourceRef",
    "DiaryDurableCommit",
    "DiaryGovernanceAcceptance",
    "GroundedSignificantEvent",
    "NoEntry",
    "NO_ENTRY",
    "ReflectionExecutionResult",
    "ReflectionOpportunity",
    "ReflectionResult",
    "SourceRefState",
    "decide_trivial_reflection",
    "commit_accepted_entry_durable",
    "classify_source_namespace",
    "create_diary_candidate",
    "promote_candidate_to_accepted_entry",
    "validate_canonical_source_refs",
    "validate_diary_provenance",
    "validate_first_person_reflection_body",
    "run_trivial_reflection_opportunity",
]
