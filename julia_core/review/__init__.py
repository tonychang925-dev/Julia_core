"""Julia Core External Code Review Capability Module.

Core owns the semantic capability contract for ``engineering.code_review``:
ReviewBundle / ReviewDecisionCandidate contracts, digest, correlation rules,
governance record, and the manual/explicit invocation path.

Ownership boundary (canonical CRB v1.1.2):
  Julia Core            — semantic capability contract, validation, governance
  Julia-AI-Assistant    — EngineeringCodeReviewCapabilityProvider (external_review)
  Browser Extension     — browser session / tab / DOM transport

Core does NOT implement or import browser/DOM/ChatGPT transport, and does NOT
perform automatic cognitive routing.
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
from julia_core.review.governance import ReviewGovernanceRecord, build_governance_record
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
from julia_core.review.validation import (
    ReviewCorrelationError,
    assert_not_stale,
    assert_review_correlation,
    is_stale,
    validate_review_correlation,
)

__all__ = [
    "BrowserAuthorityInRequestError",
    "EXTERNAL_REVIEW_CAPABILITY",
    "EXTERNAL_REVIEW_PROVIDER",
    "EXTERNAL_REVIEW_SCOPE",
    "INPUT_SCHEMA",
    "IdentityIsolationViolation",
    "ReviewBundle",
    "ReviewCorrelationError",
    "ReviewDecisionCandidate",
    "ReviewErrorCode",
    "ReviewGovernanceRecord",
    "ReviewInvocationResult",
    "ReviewTransportTrace",
    "ReviewVerdict",
    "assert_not_stale",
    "assert_review_correlation",
    "build_governance_record",
    "build_review_request",
    "compute_bundle_digest",
    "compute_text_digest",
    "digests_equal",
    "is_stale",
    "make_external_review_definition",
    "register_external_review_capability",
    "submit_review",
    "validate_identity_isolation",
    "validate_review_correlation",
]
