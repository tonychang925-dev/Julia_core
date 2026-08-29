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
    ReviewErrorCode,
    ReviewTransportTrace,
    ReviewVerdict,
    validate_identity_isolation,
)
from julia_core.review.digest import (
    compute_bundle_digest,
    compute_text_digest,
    digests_equal,
)
from julia_core.review.governance import ReviewGovernanceRecord, ReviewGovernanceService
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
    submit_review,
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
    "CandidateShaSource",
    "CandidateShaSourceUnavailable",
    "EXTERNAL_REVIEW_CAPABILITY",
    "EXTERNAL_REVIEW_PROVIDER",
    "EXTERNAL_REVIEW_SCOPE",
    "GuardedReviewProvider",
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
    "ReviewRetryUnsafeError",
    "ReviewTokenConsumedError",
    "ReviewTransaction",
    "ReviewTransactionLedger",
    "ReviewTransportTrace",
    "ReviewUntrustedSnapshotError",
    "ReviewUntrustedTransactionError",
    "ReviewVerdict",
    "SealedReviewBundle",
    "assert_not_stale",
    "assert_review_correlation",
    "assert_transport_completed",
    "build_review_request",
    "compute_bundle_digest",
    "compute_text_digest",
    "digests_equal",
    "install_review_guard",
    "is_stale",
    "is_trusted_snapshot",
    "make_external_review_definition",
    "raw_response_digest_matches",
    "register_external_review_capability",
    "seal_review_bundle",
    "snapshot_digest",
    "submit_review",
    "transport_completed",
    "validate_identity_isolation",
    "validate_review_correlation",
    "validate_transaction_correlation",
    "validate_transport_completion",
]
