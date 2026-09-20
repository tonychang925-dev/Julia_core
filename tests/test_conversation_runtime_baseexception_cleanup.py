from __future__ import annotations

import pytest

from julia_core.conversation_state.legacy_json_repository import (
    LegacyJsonConversationRepository,
)
from julia_core.runtime.conversation_runtime import ConversationRuntime


class ControlledBaseException(BaseException):
    pass


class FailAfterAddRepository(LegacyJsonConversationRepository):
    def __init__(self, path, conversation_id, turn_id):
        super().__init__(path)
        self.fail_conversation_id = conversation_id
        self.fail_turn_id = turn_id

    def add_message(self, session_id, role, content, **kwargs):
        result = super().add_message(session_id, role, content, **kwargs)
        if (
            session_id == self.fail_conversation_id
            and kwargs.get("turn_id") == self.fail_turn_id
        ):
            raise ControlledBaseException("controlled begin failure")
        return result


def test_baseexception_after_user_persistence_releases_conversation_lock(tmp_path):
    conversation_id = "conv-baseexception-cleanup"
    failed_turn_id = "turn-baseexception-cleanup"
    repository = FailAfterAddRepository(
        tmp_path / "conversations.json", conversation_id, failed_turn_id
    )
    runtime = ConversationRuntime(repository)
    runtime.get_or_create(conversation_id, create=True)

    with pytest.raises(ControlledBaseException):
        runtime.begin_turn_streaming(
            conversation_id=conversation_id,
            turn_id=failed_turn_id,
            modality="text",
            input="first",
        )

    assert not runtime._get_lock(conversation_id).locked()
    assert len(runtime.get_messages(conversation_id)) == 1

    next_ctx = runtime.begin_turn_streaming(
        conversation_id=conversation_id,
        turn_id="turn-baseexception-next",
        modality="text",
        input="second",
    )
    assert next_ctx.conversation_id == conversation_id
    runtime.cancel_streaming_turn(next_ctx)
    assert not runtime._get_lock(conversation_id).locked()
