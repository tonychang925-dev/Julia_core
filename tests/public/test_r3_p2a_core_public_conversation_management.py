from __future__ import annotations

import hashlib
from types import SimpleNamespace

from julia_core.public import (
    CoreConversationConfig,
    CoreConversationIngress,
    CoreConversationRequest,
)


def _provider(monkeypatch):
    class Provider:
        def chat(self, messages, *, cognitive_mode=""):
            return "canonical reply"

    monkeypatch.setattr(
        "julia_core.providers.core_cognition._get_cognition_provider",
        lambda _name: Provider(),
    )
    monkeypatch.setattr(
        "julia_core.public.conversation._ensure_market_public_binding",
        lambda: None,
    )


def _ingress(monkeypatch, tmp_path):
    _provider(monkeypatch)
    return CoreConversationIngress(CoreConversationConfig(tmp_path / "conversations"))


def _tree_digest(root):
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def test_public_reads_return_canonical_runtime_results(monkeypatch, tmp_path):
    ingress = _ingress(monkeypatch, tmp_path)
    ingress.create_conversation("conversation-1")
    ingress.process(
        CoreConversationRequest("conversation-1", "turn-1", "text", "first")
    )

    listed = ingress.list_conversations()
    assert listed.error_code is None
    assert len(listed.conversations) == 1
    handle = listed.conversations[0]
    assert handle.conversation_id == "conversation-1"
    assert handle.state == "active"
    assert handle.message_count == 2
    assert set(handle.__dataclass_fields__) == {
        "conversation_id",
        "state",
        "created_at",
        "updated_at",
        "last_turn_id",
        "message_count",
    }

    detail = ingress.get_conversation("conversation-1")
    assert detail.error_code is None
    assert detail.conversation["id"] == "conversation-1"
    assert detail.conversation["state"] == "active"
    assert detail.conversation["message_count"] == 2

    messages = ingress.get_messages("conversation-1")
    assert messages.error_code is None
    assert [message["role"] for message in messages.messages] == ["user", "assistant"]
    assert [message["content"] for message in messages.messages] == [
        "first",
        "canonical reply",
    ]
    assert {message["turn_id"] for message in messages.messages} == {"turn-1"}
    assert all(message["status"] == "completed" for message in messages.messages)
    assert all(message["created_at"] for message in messages.messages)

    assert ingress.get_conversation("conversation-1") == detail
    assert ingress.get_messages("conversation-1") == messages


def test_archived_conversation_is_hidden_from_default_public_list(
    monkeypatch, tmp_path
):
    class FakeRuntime:
        def __init__(self, repository):
            self.repository = repository
            self.states = {}

        def create_conversation(self, conversation_id, title="New Conversation"):
            self.states[conversation_id] = "active"
            return type("Handle", (), {"conversation_id": conversation_id})()

        def archive_conversation(self, conversation_id):
            self.states[conversation_id] = "archived"
            return True

        def list_conversations(self):
            return [
                SimpleNamespace(
                    conversation_id=conversation_id,
                    state=state,
                    created_at="2026-01-01T00:00:00",
                    updated_at="2026-01-01T00:00:00",
                    last_turn_id="",
                    message_count=0,
                )
                for conversation_id, state in self.states.items()
                if state != "archived"
            ]

        def get_conversation(self, conversation_id):
            return {"id": conversation_id, "state": self.states[conversation_id]}

    runtime = FakeRuntime(None)
    monkeypatch.setattr(
        "julia_core.public.conversation.ConversationRuntime",
        lambda repository=None: runtime,
    )
    ingress = _ingress(monkeypatch, tmp_path)
    ingress.create_conversation("active-conversation")
    ingress.create_conversation("archived-conversation")
    runtime.archive_conversation("archived-conversation")

    listed = ingress.list_conversations()

    assert [handle.conversation_id for handle in listed.conversations] == [
        "active-conversation"
    ]
    assert ingress.get_conversation("archived-conversation").error_code is None


def test_public_read_errors_distinguish_invalid_not_found_and_storage(
    monkeypatch, tmp_path
):
    ingress = _ingress(monkeypatch, tmp_path)
    ingress.create_conversation("conversation-1")

    invalid = ingress.get_conversation("../invalid")
    missing = ingress.get_conversation("unknown-conversation")
    invalid_messages = ingress.get_messages("../invalid")
    missing_messages = ingress.get_messages("unknown-conversation")

    assert invalid.error_code == "INVALID_CONVERSATION_ID"
    assert invalid.conversation is None
    assert missing.error_code == "CONVERSATION_NOT_FOUND"
    assert missing.conversation is None
    assert invalid_messages.error_code == "INVALID_CONVERSATION_ID"
    assert invalid_messages.messages == ()
    assert missing_messages.error_code == "CONVERSATION_NOT_FOUND"
    assert missing_messages.messages == ()

    unavailable = CoreConversationIngress()
    assert unavailable.list_conversations().error_code == (
        "CORE_CONVERSATION_STORAGE_UNAVAILABLE"
    )
    assert unavailable.get_conversation("conversation-1").error_code == (
        "CORE_CONVERSATION_STORAGE_UNAVAILABLE"
    )
    assert unavailable.get_messages("conversation-1").error_code == (
        "CORE_CONVERSATION_STORAGE_UNAVAILABLE"
    )


def test_public_management_reads_are_read_only(monkeypatch, tmp_path):
    ingress = _ingress(monkeypatch, tmp_path)
    ingress.create_conversation("conversation-1")
    ingress.process(
        CoreConversationRequest("conversation-1", "turn-1", "text", "first")
    )
    before = _tree_digest(tmp_path / "conversations")

    ingress.list_conversations()
    ingress.get_conversation("conversation-1")
    ingress.get_messages("conversation-1")

    assert _tree_digest(tmp_path / "conversations") == before


def test_public_pagination_delegates_to_runtime(monkeypatch, tmp_path):
    _provider(monkeypatch)
    calls = []

    class FakeRuntime:
        def __init__(self, repository=None):
            self.repository = repository

        def list_conversations(self):
            return []

        def get_conversation(self, conversation_id):
            return {"id": conversation_id}

        def get_messages(self, conversation_id, max_messages=100, **kwargs):
            kwargs["conversation_id"] = conversation_id
            kwargs["max_messages"] = max_messages
            calls.append(kwargs)
            return [{"message_id": "message-1"}]

    monkeypatch.setattr(
        "julia_core.public.conversation.ConversationRuntime", FakeRuntime
    )
    ingress = CoreConversationIngress(
        CoreConversationConfig(tmp_path / "conversations")
    )

    result = ingress.get_messages(
        "conversation-1",
        25,
        before="message-0",
        after="message-2",
        limit=5,
    )

    assert result.error_code is None
    assert result.messages == ({"message_id": "message-1"},)
    assert calls == [
        {
            "conversation_id": "conversation-1",
            "max_messages": 25,
            "before": "message-0",
            "after": "message-2",
            "limit": 5,
        }
    ]


def test_management_reads_survive_cognition_unavailable_but_process_fails_closed(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(
        "julia_core.providers.core_cognition._get_cognition_provider",
        lambda _name: None,
    )
    monkeypatch.setattr(
        "julia_core.public.conversation._ensure_market_public_binding",
        lambda: (_ for _ in ()).throw(AssertionError("reads must not bind Market")),
    )
    ingress = CoreConversationIngress(
        CoreConversationConfig(tmp_path / "conversations")
    )

    assert ingress.list_conversations().error_code is None
    assert ingress.list_conversations().conversations == ()
    assert ingress.get_conversation("unknown-conversation").error_code == (
        "CONVERSATION_NOT_FOUND"
    )
    assert ingress.get_messages("unknown-conversation").error_code == (
        "CONVERSATION_NOT_FOUND"
    )

    response = ingress.process(
        CoreConversationRequest("conversation-1", "turn-1", "text", "hello")
    )
    assert response.status == "failed"
    assert response.error_code == "CORE_PROVIDER_UNAVAILABLE"
