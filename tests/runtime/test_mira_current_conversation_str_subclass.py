import json
import pytest

from julia_core.runtime.mira_composition import MiraCompositionError, _project_recent_conversation


class ProviderAuthorizedText(str):
    pass


def test_str_subclass_is_accepted_and_normalized_to_plain_str():
    content = ProviderAuthorizedText('recent assistant reply')
    history = [{
        'conversation_id': 'conversation-str-subclass',
        'role': 'assistant',
        'content': content,
        'turn_id': 'turn-1',
        'message_id': 'message-1',
    }]

    projection = _project_recent_conversation(
        history, conversation_id='conversation-str-subclass'
    )
    projected = json.loads(projection['messages'][0])

    assert isinstance(content, str)
    assert type(content) is not str
    assert projected['content'] == 'recent assistant reply'
    assert type(projected['content']) is str


def test_non_string_content_still_fails_closed():
    history = [{
        'conversation_id': 'conversation-non-string',
        'role': 'assistant',
        'content': {'text': 'not canonical text'},
        'turn_id': 'turn-1',
        'message_id': 'message-1',
    }]

    with pytest.raises(MiraCompositionError, match='content is inexact'):
        _project_recent_conversation(
            history, conversation_id='conversation-non-string'
        )
