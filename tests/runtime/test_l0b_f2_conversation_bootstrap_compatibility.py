from __future__ import annotations

import io
import socket
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

import julia_core.runtime.conversation_runtime as conversation_runtime_module
from julia_core.conversation_state.legacy_json_repository import (
    LegacyJsonConversationRepository,
)
from julia_core.runtime.conversation_runtime import (
    ConversationCutoverRequired,
    configure_conversation_runtime,
    get_conversation_runtime,
)

ASSISTANT_SOURCE_REPO = Path("/Users/admin/glm-workspace/b1_assistant")
ASSISTANT_FROZEN_SHA = "03de982a3ad60cdbe067fe68e1be1db8a4202de4"


@pytest.fixture(autouse=True)
def isolated_canonical_runtime(monkeypatch):
    monkeypatch.setattr(conversation_runtime_module, "_runtime", None)
    yield


@pytest.fixture(scope="module")
def frozen_assistant_root(tmp_path_factory) -> Path:
    root = tmp_path_factory.mktemp("frozen-assistant") / "assistant"
    archive = subprocess.run(
        [
            "git",
            "-C",
            str(ASSISTANT_SOURCE_REPO),
            "archive",
            ASSISTANT_FROZEN_SHA,
            "private_data",
            "voice_api",
        ],
        check=True,
        stdout=subprocess.PIPE,
    ).stdout
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as archive_file:
        archive_file.extractall(root, filter="data")
    return root


def test_f01_frozen_assistant_bootstrap_import_succeeds(frozen_assistant_root, monkeypatch):
    monkeypatch.syspath_prepend(str(frozen_assistant_root))
    import private_data.wiring

    assert private_data.wiring.wire_legacy_composition is not None


def test_f02_f03_canonical_singleton_is_configured(tmp_path):
    repository = LegacyJsonConversationRepository(tmp_path / "canonical.json")
    configured = configure_conversation_runtime(repository)
    assert get_conversation_runtime() is configured
    assert configured._repository is repository


def test_f04_same_configuration_is_idempotent(tmp_path):
    repository = LegacyJsonConversationRepository(tmp_path / "canonical.json")
    first = configure_conversation_runtime(repository)
    second = configure_conversation_runtime(repository)
    assert first is second


def test_f05_conflicting_configuration_fails_closed(tmp_path):
    first = LegacyJsonConversationRepository(tmp_path / "first.json")
    second = LegacyJsonConversationRepository(tmp_path / "second.json")
    configured = configure_conversation_runtime(first)
    with pytest.raises(ConversationCutoverRequired):
        configure_conversation_runtime(second)
    assert get_conversation_runtime() is configured
    assert configured._repository is first


def test_f06_no_second_runtime_authority_is_created(tmp_path):
    repository = LegacyJsonConversationRepository(tmp_path / "canonical.json")
    configured = configure_conversation_runtime(repository)
    assert configure_conversation_runtime(repository) is configured
    assert get_conversation_runtime() is configured


def test_f07_controlled_state_roots_remain_isolated(tmp_path):
    first = LegacyJsonConversationRepository(tmp_path / "state-a" / "canonical.json")
    second = LegacyJsonConversationRepository(tmp_path / "state-b" / "canonical.json")
    runtime = configure_conversation_runtime(first)
    runtime.get_or_create("conversation-a", create=True)
    with pytest.raises(ConversationCutoverRequired):
        configure_conversation_runtime(second)
    assert [session.id for session in second.list_all()] == []


def test_f08_streaming_commit_settles_once(tmp_path):
    repository = LegacyJsonConversationRepository(tmp_path / "canonical.json")
    runtime = configure_conversation_runtime(repository)
    runtime.get_or_create("conversation", create=True)
    context = runtime.begin_turn_streaming(
        conversation_id="conversation",
        turn_id="turn-commit",
        modality="text",
        input="accepted",
    )
    runtime.commit_streaming_turn(context, "assistant")
    with pytest.raises(RuntimeError, match="already settled"):
        runtime.commit_streaming_turn(context, "assistant duplicate")
    messages = repository.find_turn("conversation", "turn-commit")
    assert [message.role for message in messages] == ["user", "assistant"]


def test_f09_streaming_cancel_preserves_accepted_user_turn(tmp_path):
    repository = LegacyJsonConversationRepository(tmp_path / "canonical.json")
    runtime = configure_conversation_runtime(repository)
    runtime.get_or_create("conversation", create=True)
    context = runtime.begin_turn_streaming(
        conversation_id="conversation",
        turn_id="turn-cancel",
        modality="text",
        input="accepted",
    )
    runtime.cancel_streaming_turn(context)
    with pytest.raises(RuntimeError, match="already settled"):
        runtime.commit_streaming_turn(context, "late assistant")
    messages = repository.find_turn("conversation", "turn-cancel")
    assert [message.role for message in messages] == ["user"]
    assert messages[0].status == "completed"


def test_f10_assistant_canonical_route_imports(frozen_assistant_root, monkeypatch):
    monkeypatch.syspath_prepend(str(frozen_assistant_root))
    from voice_api.conversation_routes import router

    assert router is not None


def test_f14_compatibility_has_no_live_execution(monkeypatch):
    monkeypatch.setattr(socket, "socket", None)
    repository = LegacyJsonConversationRepository("/tmp/l0b-f2-no-live.json")
    assert configure_conversation_runtime(repository) is get_conversation_runtime()
