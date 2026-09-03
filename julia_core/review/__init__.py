"""Julia Core External Code Review Capability Module.

Core owns the semantic capability contract for ``engineering.code_review``:
ReviewBundle / ReviewDecisionCandidate contracts, deep-sealed snapshot, digest,
transaction binding, correlation, transport-completion truth, governance
record, and the manual/explicit invocation path.

Ownership boundary (canonical CRB v1.1.2):
  Julia Core            — semantic capability contract, validation, governance
  Julia-AI-Assistant    — EngineeringCodeReviewCapabilityProvider (external_review)
  Browser Extension     — browser session / tab / DOM transport

Core does NOT implement or import browser/DOM/ChatGPT transport, does NOT
perform automatic cognitive routing, and does NOT allow arbitrary
CapabilityRequest ingress to reach the provider (guarded ingress).
"""

from julia_core.review.contracts import (
    IdentityIsolationViolation,
    ReviewBundle,
    ReviewDecisionCandidate,
    ReviewEvidenceBinding,
    ReviewEvidenceBindingKind,
    ReviewFindingCandidate,
    ReviewFindingSeverity,
    ReviewErrorCode,
    ReviewTransportTrace,
    ReviewVerdict,
    validate_identity_isolation,
)
from julia_core.review.admission import (
    CandidateAdmissionComposition,
    CandidateAdmissionError,
    CandidateAdmissionRecord,
    CandidateAdmissionSource,
    CandidateAdmissionSourceBinding,
    assert_candidate_admission,
    is_trusted_candidate_admission_binding,
    resolve_candidate_admission,
)
from julia_core.review.digest import (
    compute_bundle_digest,
    compute_text_digest,
    digests_equal,
)
from julia_core.review.governance import (
    ReviewGovernanceRecord,
    ReviewGovernanceService,
    is_trusted_review_governance_record,
)
from julia_core.review.guard import (
    GuardedReviewProvider,
    REVIEW_SEMANTIC_ARG,
    REVIEW_TOKEN_ARG,
    install_review_guard,
)
from julia_core.review.invocation import (
    BrowserAuthorityInRequestError,
    EXTERNAL_REVIEW_CAPABILITY,
    EXTERNAL_REVIEW_SCOPE,
    ReviewInvocationResult,
    build_review_request,
    is_trusted_invocation,
    submit_review,
)
from julia_core.review.parser import (
    CoreReviewParser,
    ReviewMachineResponseParseError,
    get_core_review_parser_binding,
    parse_review_response,
)
from julia_core.review.registration import (
    EXTERNAL_REVIEW_PROVIDER,
    INPUT_SCHEMA,
    make_external_review_definition,
    register_external_review_capability,
)
from julia_core.review.snapshot import (
    SealedReviewBundle,
    is_trusted_snapshot,
    seal_review_bundle,
    snapshot_digest,
)
from julia_core.review.candidate_artifact import (
    SealedCandidate,
    is_trusted_candidate,
)
from julia_core.review.source_binding import (
    CandidateShaSourceBinding,
    is_trusted_source_binding,
)
from julia_core.review.transaction import (
    ReviewDuplicateError,
    ReviewRetryUnsafeError,
    ReviewTokenConsumedError,
    ReviewTransaction,
    ReviewTransactionLedger,
    ReviewUntrustedSnapshotError,
    ReviewUntrustedTransactionError,
)
from julia_core.review.validation import (
    CandidateShaSource,
    CandidateShaSourceUnavailable,
    ReviewCorrelationError,
    assert_not_stale,
    assert_review_correlation,
    assert_transport_completed,
    is_stale,
    raw_response_digest_matches,
    transport_completed,
    validate_review_correlation,
    validate_transaction_correlation,
    validate_transport_completion,
)

__all__ = [
    "BrowserAuthorityInRequestError",
    "CandidateAdmissionComposition",
    "CandidateAdmissionError",
    "CandidateAdmissionRecord",
    "CandidateAdmissionSource",
    "CandidateAdmissionSourceBinding",
    "CandidateShaSource",
    "CandidateShaSourceBinding",
    "CandidateShaSourceUnavailable",
    "EXTERNAL_REVIEW_CAPABILITY",
    "EXTERNAL_REVIEW_PROVIDER",
    "EXTERNAL_REVIEW_SCOPE",
    "GuardedReviewProvider",
    "CoreReviewParser",
    "INPUT_SCHEMA",
    "IdentityIsolationViolation",
    "REVIEW_SEMANTIC_ARG",
    "REVIEW_TOKEN_ARG",
    "ReviewBundle",
    "ReviewCorrelationError",
    "ReviewDecisionCandidate",
    "ReviewDuplicateError",
    "ReviewErrorCode",
    "ReviewGovernanceRecord",
    "ReviewGovernanceService",
    "ReviewInvocationResult",
    "ReviewMachineResponseParseError",
    "ReviewRetryUnsafeError",
    "ReviewTokenConsumedError",
    "ReviewTransaction",
    "ReviewTransactionLedger",
    "ReviewTransportTrace",
    "ReviewEvidenceBinding",
    "ReviewEvidenceBindingKind",
    "ReviewFindingCandidate",
    "ReviewFindingSeverity",
    "ReviewUntrustedSnapshotError",
    "ReviewUntrustedTransactionError",
    "ReviewVerdict",
    "SealedCandidate",
    "SealedReviewBundle",
    "assert_not_stale",
    "assert_candidate_admission",
    "assert_review_correlation",
    "assert_transport_completed",
    "build_review_request",
    "compute_bundle_digest",
    "compute_text_digest",
    "digests_equal",
    "install_review_guard",
    "is_stale",
    "is_trusted_invocation",
    "is_trusted_review_governance_record",
    "is_trusted_snapshot",
    "is_trusted_source_binding",
    "make_external_review_definition",
    "raw_response_digest_matches",
    "register_external_review_capability",
    "seal_review_bundle",
    "parse_review_response",
    "get_core_review_parser_binding",
    "snapshot_digest",
    "submit_review",
    "transport_completed",
    "validate_identity_isolation",
    "validate_review_correlation",
    "validate_structured_finding_bindings",
    "validate_transaction_correlation",
    "validate_transport_completion",
    "is_trusted_candidate",
    "is_trusted_candidate_admission_binding",
]
