"""W1-F2A-R3 — ConversationRuntime binding/cutover semantics.

configure_conversation_runtime: same repository idempotent; different
repository → ConversationCutoverRequired (F2-I11). get unconfigured → fail
closed (F2-I07).
"""
from __future__ import annotations

import pytest

import julia_core.runtime.conversation_runtime as crt_module
from julia_core.runtime.conversation_runtime import (
    ConversationCutoverRequired,
    configure_conversation_runtime,
    get_conversation_runtime,
)
from julia_core.conversation_state.legacy_json_repository import LegacyJsonConversationRepository


@pytest.fixture(autouse=True)
def reset_runtime():
    crt_module._runtime = None
    yield
    crt_module._runtime = None


def test_configure_same_repository_idempotent(tmp_path):
    repo = LegacyJsonConversationRepository(tmp_path / "a.json")
    rt1 = configure_conversation_runtime(repo)
    rt2 = configure_conversation_runtime(repo)  # same binding → idempotent
    assert rt1 is rt2


def test_configure_different_repository_cutover_required(tmp_path):
    repo_a = LegacyJsonConversationRepository(tmp_path / "a.json")
    repo_b = LegacyJsonConversationRepository(tmp_path / "b.json")
    configure_conversation_runtime(repo_a)
    with pytest.raises(ConversationCutoverRequired):
        configure_conversation_runtime(repo_b)  # different → authority cutover


def test_get_unconfigured_fails_closed():
    with pytest.raises(RuntimeError):
        get_conversation_runtime()
