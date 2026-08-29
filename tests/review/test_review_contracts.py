"""External Code Review — Core-side contract tests.

Covers:
  - ReviewBundle required fields / schema validation
  - ReviewDecisionCandidate minimum fields / verdict recognition
  - identity isolation (no persona/continuity/self-model material)
  - deterministic digest stability
  - review correlation rules (review_id / candidate_id / candidate_sha /
    bundle_digest)
  - stale review rejection
"""

from __future__ import annotations

import pytest

from julia_core.review.contracts import (
    IdentityIsolationViolation,
    ReviewBundle,
    ReviewDecisionCandidate,
    ReviewErrorCode,
    ReviewVerdict,
    validate_identity_isolation,
)
from julia_core.review.digest import compute_bundle_digest, compute_text_digest, digests_equal
from julia_core.review.validation import (
    ReviewCorrelationError,
    assert_not_stale,
    assert_review_correlation,
    is_stale,
    validate_review_correlation,
)


def _bundle(**overrides) -> ReviewBundle:
    values = dict(
        review_id="rvw_1",
        task_id="task_1",
        candidate_id="cand_1",
        candidate_sha="abc123",
        repository="Julia_core",
        branch="feature/x",
        objective="review code",
        changed_files=("a.py",),
        questions=("Is it safe?",),
    )
    values.update(overrides)
    return ReviewBundle(**values)


def _candidate(**overrides) -> ReviewDecisionCandidate:
    values = dict(
        review_id="rvw_1",
        candidate_id="cand_1",
        candidate_sha="abc123",
        verdict=ReviewVerdict.PASS,
        notes=("looks good",),
    )
    values.update(overrides)
    return ReviewDecisionCandidate(**values)


# ── ReviewBundle schema ──────────────────────────────────────────────────────

def test_bundle_minimal_valid():
    assert _bundle().validate() == []


def test_bundle_required_fields_are_reported():
    errors = ReviewBundle().validate()
    assert "missing:review_id" in errors
    assert "missing:candidate_id" in errors
    assert "missing:candidate_sha" in errors
    assert "missing:changed_files" in errors
    assert "missing:questions" in errors


def test_bundle_identity_isolation_rejects_persona_material():
    bundle = _bundle()
    # persona material inside identity_projection must be rejected
    bad = ReviewBundle(
        review_id=bundle.review_id,
        candidate_id=bundle.candidate_id,
        candidate_sha=bundle.candidate_sha,
        repository=bundle.repository,
        objective=bundle.objective,
        changed_files=bundle.changed_files,
        questions=bundle.questions,
        identity_projection={"persona_projection": "Julia persona text"},
    )
    errors = bad.validate()
    assert any("identity_isolation" in e for e in errors)


def test_bundle_identity_isolation_allows_disabled_flags():
    payload = {
        "persona_projection": "DISABLED",
        "relationship_projection": "DISABLED",
        "continuity_restore": "DISABLED",
        "private_identity_memory": "DISABLED",
        "self_model_projection": "DISABLED",
    }
    validate_identity_isolation(payload)  # must not raise


@pytest.mark.parametrize("key", [
    "persona_projection", "continuity_restore", "private_diary",
    "golden_mira_persona", "relationship_memory", "self_model_projection",
])
def test_identity_isolation_rejects_non_disabled_material(key):
    with pytest.raises(IdentityIsolationViolation):
        validate_identity_isolation({key: "any material"})


# ── ReviewDecisionCandidate ──────────────────────────────────────────────────

def test_candidate_minimum_valid():
    assert _candidate().validate_minimum() == []


def test_candidate_missing_binding_fields_reported():
    errors = ReviewDecisionCandidate().validate_minimum()
    assert "missing:review_id" in errors
    assert "missing:candidate_id" in errors
    assert "missing:candidate_sha" in errors


def test_candidate_unknown_verdict_reported():
    errors = _candidate(verdict="SUPER_PASS").validate_minimum()
    assert "unknown:verdict" in errors


def test_candidate_all_verdicts_recognized():
    for verdict in ReviewVerdict:
        assert _candidate(verdict=verdict).validate_minimum() == []


# ── Digest ───────────────────────────────────────────────────────────────────

def test_text_digest_is_sha256_hex():
    digest = compute_text_digest("hello")
    assert len(digest) == 64
    assert digest == compute_text_digest("hello")


def test_bundle_digest_is_stable():
    assert compute_bundle_digest(_bundle()) == compute_bundle_digest(_bundle())


def test_bundle_digest_changes_when_payload_changes():
    assert compute_bundle_digest(_bundle()) != compute_bundle_digest(
        _bundle(candidate_sha="def456")
    )


def test_digests_equal():
    assert digests_equal("abc", "abc")
    assert not digests_equal("abc", "abd")
    assert not digests_equal("abc", 123)


# ── Correlation rules ────────────────────────────────────────────────────────

def test_correlation_passes_when_all_bound():
    assert validate_review_correlation(_bundle(), _candidate()) == []


def test_correlation_rejects_review_id_mismatch():
    errors = validate_review_correlation(_bundle(), _candidate(review_id="rvw_OTHER"))
    assert any(ReviewErrorCode.REVIEW_ID_MISMATCH.value in e for e in errors)


def test_correlation_rejects_candidate_id_mismatch():
    errors = validate_review_correlation(_bundle(), _candidate(candidate_id="cand_OTHER"))
    assert any(ReviewErrorCode.CANDIDATE_ID_MISMATCH.value in e for e in errors)


def test_correlation_rejects_candidate_sha_mismatch():
    errors = validate_review_correlation(_bundle(), _candidate(candidate_sha="deadbeef"))
    assert any(ReviewErrorCode.CANDIDATE_SHA_MISMATCH.value in e for e in errors)


def test_correlation_rejects_bundle_digest_mismatch():
    errors = validate_review_correlation(
        _bundle(), _candidate(), bundle_digest="0" * 64
    )
    assert any(ReviewErrorCode.BUNDLE_DIGEST_MISMATCH.value in e for e in errors)


def test_correlation_rejects_empty_response():
    candidate = _candidate(verdict=ReviewVerdict.UNPARSEABLE, notes=())
    errors = validate_review_correlation(_bundle(), candidate)
    assert any(ReviewErrorCode.REVIEW_EMPTY_RESPONSE.value in e for e in errors)


def test_correlation_rejects_response_over_size_limit():
    candidate = _candidate(notes=("x" * 200,))
    errors = validate_review_correlation(_bundle(), candidate, max_response_chars=50)
    assert any("response_size_exceeded" in e for e in errors)


def test_assert_correlation_raises_on_failure():
    with pytest.raises(ReviewCorrelationError):
        assert_review_correlation(_bundle(), _candidate(candidate_sha="deadbeef"))


# ── Stale review ─────────────────────────────────────────────────────────────

def test_stale_review_detected():
    assert is_stale(_bundle(), current_candidate_sha="newsha")
    assert not is_stale(_bundle(), current_candidate_sha="abc123")


def test_assert_not_stale_raises():
    with pytest.raises(ReviewCorrelationError) as exc_info:
        assert_not_stale(_bundle(), current_candidate_sha="newsha")
    assert ReviewErrorCode.STALE_REVIEW.value in str(exc_info.value)
