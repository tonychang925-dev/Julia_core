"""Governed Julia Diary semantic domain.

AT-12 boundary: ReflectionTrigger is only an opportunity; NO_ENTRY is a valid
terminal reflection result and creates no canonical Diary artifact.
"""

from .context_os_retrieval import (
    DiaryContextAdmission,
    DiaryContextAssemblyTrace,
    DiaryContextCandidate,
    DiaryContextProvider,
    DiaryReadRepository,
    admit_diary_for_context,
    assert_not_diary_context_authority_object,
    build_diary_context_block,
    trace_diary_context_block,
)
from .memory_boundary import (
    DiaryMemorySeparationResult,
    assert_not_memory_persistence_input,
    is_diary_authority_object,
    prove_diary_does_not_mutate_memory,
)
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
    "DiaryContextAdmission",
    "DiaryContextAssemblyTrace",
    "DiaryContextCandidate",
    "DiaryContextProvider",
    "DiaryReadRepository",
    "DiaryCandidate",
    "DiaryProvenance",
    "DiaryProvenanceReport",
    "DiarySourceResolution",
    "DiarySourceResolver",
    "DiaryRepository",
    "DiarySourceRef",
    "DiaryDurableCommit",
    "DiaryGovernanceAcceptance",
    "DiaryMemorySeparationResult",
    "GroundedSignificantEvent",
    "NoEntry",
    "NO_ENTRY",
    "ReflectionExecutionResult",
    "ReflectionOpportunity",
    "ReflectionResult",
    "SourceRefState",
    "decide_trivial_reflection",
    "admit_diary_for_context",
    "assert_not_diary_context_authority_object",
    "assert_not_memory_persistence_input",
    "build_diary_context_block",
    "commit_accepted_entry_durable",
    "classify_source_namespace",
    "create_diary_candidate",
    "promote_candidate_to_accepted_entry",
    "is_diary_authority_object",
    "validate_canonical_source_refs",
    "prove_diary_does_not_mutate_memory",
    "validate_diary_provenance",
    "trace_diary_context_block",
    "validate_first_person_reflection_body",
    "run_trivial_reflection_opportunity",
]
