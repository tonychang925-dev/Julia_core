"""TEST-ONLY authority fixtures for the external review module.

This module is outside ``julia_core`` and is not installed with the production
package. It deliberately uses production private registries only from tests;
the production package exposes no generic test binder or arbitrary registrar.
"""

from __future__ import annotations

import secrets
from typing import Any

from julia_core.review import source_binding as _source_binding
from julia_core.review.candidate_artifact import (
    _seal_candidate_with_trusted_authorities,
)
from julia_core.review.source_binding import _binding_fingerprint


class TestCandidateShaSource:
    def current_candidate_sha(self, *, review_id: str, candidate_id: str) -> str:
        raise NotImplementedError


class TestCandidateCreator:
    def create_candidate(self, *, raw_observation: Any):
        raise NotImplementedError


def register_test_candidate_sha_source(adapter: TestCandidateShaSource):
    if not isinstance(adapter, TestCandidateShaSource):
        raise TypeError("test source binder requires TestCandidateShaSource")
    binding = _source_binding.CandidateShaSourceBinding(
        binding_id=f"sha_src_{secrets.token_urlsafe(16)}"
    )
    _source_binding._TRUSTED_BINDINGS[binding.binding_id] = (
        binding,
        adapter,
        _binding_fingerprint(binding),
    )
    return binding


def register_test_candidate_creator(creator: TestCandidateCreator):
    if not isinstance(creator, TestCandidateCreator):
        raise TypeError("test creator binder requires TestCandidateCreator")
    for binding, registered_creator, _ in _source_binding._CREATOR_BINDINGS.values():
        if registered_creator is creator:
            return binding
    binding = _source_binding.CandidateCreatorBinding(
        binding_id=f"cand_creator_{secrets.token_urlsafe(16)}"
    )
    _source_binding._CREATOR_BINDINGS[binding.binding_id] = (
        binding,
        creator,
        _binding_fingerprint(binding),
    )
    return binding


def _creator_binding_for(creator: TestCandidateCreator):
    for binding, registered_creator, _ in _source_binding._CREATOR_BINDINGS.values():
        if registered_creator is creator:
            return binding
    raise ValueError("creator is not registered by the test-only binder")


def seal_test_candidate(
    candidate,
    *,
    creator: TestCandidateCreator,
    raw_observation: Any,
):
    """Seal through the exact test creator binding and exact raw observation."""
    binding = _creator_binding_for(creator)
    return _seal_candidate_with_trusted_authorities(
        candidate,
        creator_binding=binding,
        creator=creator,
        raw_observation=raw_observation,
    )


__all__ = [
    "TestCandidateCreator",
    "TestCandidateShaSource",
    "register_test_candidate_creator",
    "register_test_candidate_sha_source",
    "seal_test_candidate",
]
