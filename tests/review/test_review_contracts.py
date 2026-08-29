"""External Code Review — Core-side contract & snapshot tests.

Covers:
  - ReviewBundle / ReviewDecisionCandidate schema
  - identity isolation
  - digest stability
  - deep-sealed snapshot (C): immutable, owned digest, mutation-proof
  - correlation rules (D): review_id / candidate_id / candidate_sha / digest
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
from julia_core.review.snapshot import SealedReviewBundle, seal_review_bundle, snapshot_digest
from julia_core.review.validation import (
    CandidateShaSourceUnavailable,
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
    bad = ReviewBundle(
        review_id="rvw_1", candidate_id="cand_1", candidate_sha="abc123",
        repository="Julia_core", objective="x", changed_files=("a.py",), questions=("q",),
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
    validate_identity_isolation(payload)


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
    assert len(compute_text_digest("hello")) == 64
    assert compute_text_digest("hello") == compute_text_digest("hello")


def test_bundle_digest_is_stable():
    assert compute_bundle_digest(_bundle()) == compute_bundle_digest(_bundle())


def test_bundle_digest_changes_when_payload_changes():
    assert compute_bundle_digest(_bundle()) != compute_bundle_digest(_bundle(candidate_sha="def456"))


def test_digests_equal():
    assert digests_equal("abc", "abc")
    assert not digests_equal("abc", "abd")
    assert not digests_equal("abc", 123)


# ── Deep-sealed snapshot (C) ─────────────────────────────────────────────────

def test_seal_produces_immutable_snapshot_with_digest():
    snapshot = seal_review_bundle(_bundle())
    assert isinstance(snapshot, SealedReviewBundle)
    assert snapshot.review_id == "rvw_1"
    assert len(snapshot.digest) == 64
    assert snapshot_digest(snapshot) == snapshot.digest


def test_seal_rejects_invalid_bundle_before_digest():
    with pytest.raises(ValueError):
        seal_review_bundle(ReviewBundle())


def test_seal_deep_copies_nested_payload():
    """S4/S5: mutating the original caller object must NOT change the snapshot."""
    bundle = _bundle(
        diff_blocks=({"path": "a.py", "content": "v1"},),
        limits={"max_response_chars": 12000, "allow_scope_expansion": False},
    )
    snapshot = seal_review_bundle(bundle)
    before = snapshot.to_payload()
    digest_before = snapshot.digest

    # Mutate the original bundle's nested structures aggressively.
    # (ReviewBundle is frozen; mutate the nested mutable dicts/tuples.)
    nested_blocks = bundle.diff_blocks
    nested_blocks[0]["content"] = "MUTATED"
    nested_blocks[0]["tab_id"] = 999  # inserted after validation
    bundle.limits["max_response_chars"] = 1
    bundle.limits["browser_command"] = "goto"
    changed_files = list(bundle.changed_files)
    changed_files.append("evil.py")
    object.__setattr__(bundle, "changed_files", tuple(changed_files))

    after = snapshot.to_payload()
    assert before == after  # byte/semantic identical
    assert snapshot.digest == digest_before  # owned digest stable
    assert after["diff_blocks"][0]["content"] == "v1"
    assert "tab_id" not in after["diff_blocks"][0]
    assert after["limits"]["max_response_chars"] == 12000
    assert "evil.py" not in after["changed_files"]


def test_snapshot_payload_returns_fresh_copy_each_call():
    snapshot = seal_review_bundle(_bundle(diff_blocks=({"path": "a.py"},)))
    p1 = snapshot.to_payload()
    p2 = snapshot.to_payload()
    assert p1 == p2
    # Mutating one returned copy must not affect the snapshot or the next copy.
    p1["diff_blocks"][0]["path"] = "MUTATED"
    assert snapshot.to_payload()["diff_blocks"][0]["path"] == "a.py"


# ── Correlation rules (D) ────────────────────────────────────────────────────

def test_correlation_passes_when_all_bound():
    snapshot = seal_review_bundle(_bundle())
    assert validate_review_correlation(snapshot, _candidate()) == []


def test_correlation_rejects_review_id_mismatch():
    snapshot = seal_review_bundle(_bundle())
    errors = validate_review_correlation(snapshot, _candidate(review_id="rvw_OTHER"))
    assert any(ReviewErrorCode.REVIEW_ID_MISMATCH.value in e for e in errors)


def test_correlation_rejects_candidate_id_mismatch():
    snapshot = seal_review_bundle(_bundle())
    errors = validate_review_correlation(snapshot, _candidate(candidate_id="cand_OTHER"))
    assert any(ReviewErrorCode.CANDIDATE_ID_MISMATCH.value in e for e in errors)


def test_correlation_rejects_candidate_sha_mismatch():
    snapshot = seal_review_bundle(_bundle())
    errors = validate_review_correlation(snapshot, _candidate(candidate_sha="deadbeef"))
    assert any(ReviewErrorCode.CANDIDATE_SHA_MISMATCH.value in e for e in errors)


def test_correlation_uses_snapshot_digest_not_caller_digest():
    """The digest is compared against the snapshot's OWNED digest, never a
    caller-supplied digest string (no self-supplied authority)."""
    snapshot = seal_review_bundle(_bundle())
    # Even if the caller knew the digest, there is no digest argument to pass —
    # correlation is always against the trusted snapshot.
    errors = validate_review_correlation(snapshot, _candidate())
    assert errors == []


def test_correlation_rejects_empty_response():
    snapshot = seal_review_bundle(_bundle())
    candidate = _candidate(verdict=ReviewVerdict.UNPARSEABLE, notes=())
    errors = validate_review_correlation(snapshot, candidate)
    assert any(ReviewErrorCode.REVIEW_EMPTY_RESPONSE.value in e for e in errors)


def test_correlation_rejects_response_over_size_limit():
    snapshot = seal_review_bundle(_bundle())
    candidate = _candidate(notes=("x" * 200,))
    errors = validate_review_correlation(snapshot, candidate, max_response_chars=50)
    assert any("response_size_exceeded" in e for e in errors)


def test_assert_correlation_raises_on_failure():
    snapshot = seal_review_bundle(_bundle())
    with pytest.raises(ReviewCorrelationError):
        assert_review_correlation(snapshot, _candidate(candidate_sha="deadbeef"))


# ── Stale (E) ────────────────────────────────────────────────────────────────

def test_stale_without_source_fails_closed():
    """Without a canonical CandidateShaSource, stale validation MUST NOT trust a
    caller-supplied current SHA — it fails closed (E)."""
    snapshot = seal_review_bundle(_bundle())
    with pytest.raises(CandidateShaSourceUnavailable):
        is_stale(snapshot, None)


def test_stale_detected_via_canonical_source():
    class Source:
        def current_candidate_sha(self, *, review_id, candidate_id):
            return "newsha"

    snapshot = seal_review_bundle(_bundle())
    assert is_stale(snapshot, Source()) is True
    with pytest.raises(ReviewCorrelationError):
        assert_not_stale(snapshot, Source())


def test_not_stale_when_canonical_source_matches():
    class Source:
        def current_candidate_sha(self, *, review_id, candidate_id):
            return "abc123"

    snapshot = seal_review_bundle(_bundle())
    assert is_stale(snapshot, Source()) is False
    assert_not_stale(snapshot, Source())  # no raise
