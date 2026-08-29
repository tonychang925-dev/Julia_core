"""TEST-ONLY trusted-binding infrastructure (round-6 §B).

This module is explicitly test-only and is NOT imported by the production
review surface. Positive-path test helpers live here and cannot be imported as
production review authority.

Bindings created here require the adapter to be an instance of the explicit
test base classes below, so an arbitrary duck-typed FakeSource / FakeCreator
can never become trusted through this seam either.

Future canonical adapters may add their own trusted composition without
changing the Core semantic contract.
"""

from __future__ import annotations

from typing import Any

from julia_core.review import source_binding as _sb


class TestCandidateShaSource:
    """Base class for TEST-ONLY candidate SHA sources.

    Production code must never import this; only test fixtures subclass it.
    """

    def current_candidate_sha(self, *, review_id: str, candidate_id: str) -> str:
        raise NotImplementedError


class TestCandidateCreator:
    """Base class for TEST-ONLY candidate creators (round-6 §C).

    Subclasses must return a SealedCandidate (see candidate_artifact.py).
    """

    def create_candidate(self, *, raw_response: str, raw_response_ref: str):
        raise NotImplementedError


def register_test_candidate_sha_source(adapter: TestCandidateShaSource):
    """TEST-ONLY binder: requires an explicit TestCandidateShaSource subclass.

    A raw duck-typed FakeSource is rejected (F3).
    """
    if not isinstance(adapter, TestCandidateShaSource):
        raise TypeError(
            "test source binder requires a TestCandidateShaSource instance; "
            "arbitrary duck-typed adapters cannot become trusted (F3)"
        )
    binding = _sb._make_source_binding()
    _sb._register_source_binding(binding, adapter)
    return binding


def register_test_candidate_creator(creator: TestCandidateCreator):
    """TEST-ONLY binder: requires an explicit TestCandidateCreator subclass.

    A raw duck-typed FakeCreator is rejected (F4).
    """
    if not isinstance(creator, TestCandidateCreator):
        raise TypeError(
            "test creator binder requires a TestCandidateCreator instance; "
            "arbitrary duck-typed creators cannot become trusted (F4)"
        )
    binding = _sb._make_creator_binding()
    _sb._register_creator_binding(binding, creator)
    return binding


__all__ = [
    "TestCandidateCreator",
    "TestCandidateShaSource",
    "register_test_candidate_creator",
    "register_test_candidate_sha_source",
]
