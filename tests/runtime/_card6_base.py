"""CARD 6 shared fixture: a pass-1 parent package with populated base frames."""
from julia_core.runtime.context_execution_runtime import CognitiveContextPackage

BASE_FRAMES = {
    "identity_frame": {"persona_traits": "IDENTITY-MARK 温柔台湾腔"},
    "experience_frame": {"recent_context": "EXPERIENCE-MARK 上次聊到市场", "diary_retrieval_authority": False},
    "diary_frame": {"diary_context": "DIARY-MARK"},
    "continuity_frame": {"narrative": "CONTINUITY-MARK 我们的关系"},
}
SITUATION = {"current_date": "2026-07-03", "current_turn_timestamp": "2026-07-03T09:30:00+08:00", "utc_offset": "+08:00", "interaction_state": "calm"}


def populated_parent(**kw) -> CognitiveContextPackage:
    import copy
    pkg = CognitiveContextPackage(**{"conversation_id": "c", "turn_id": "t", "generation_id": "g", **kw})
    for name, value in BASE_FRAMES.items():
        setattr(pkg, name, copy.deepcopy(value))
    pkg.situation_frame = copy.deepcopy(SITUATION)
    return pkg


def assert_inherits_base(delta, parent, *, mode):
    for name in BASE_FRAMES:
        assert getattr(delta, name) == getattr(parent, name), name
        assert getattr(delta, name) is not getattr(parent, name), name
    assert delta.situation_frame == {**parent.situation_frame, "mode": mode}
    assert delta.situation_frame is not parent.situation_frame
