"""CARD 8: execution-block wording, duplicate-scope text and the record-only
`executed_but_denied` detector. Scenario structures only, no conversation text."""
from __future__ import annotations

import os
from types import SimpleNamespace

import pytest

from julia_core.runtime.iterative_reasoning import IterativeReasoningLoop
from julia_core.runtime.turn_ledger import (
    TurnLedger,
    check_denied_execution,
    environment_facts,
)
from tests.runtime.test_card7_turn_execution_ledger import _parent, _system  # noqa: F401
from tests.runtime.test_rd1_p2_i3b_production_iterative_reasoning_loop import (
    LoopSession,
    execution,
    tool_response,
)


@pytest.fixture(autouse=True)
def _key(tmp_path, monkeypatch):
    path = tmp_path / "log_hmac.key"
    path.write_bytes(b"k" * 32)
    os.chmod(path, 0o600)
    monkeypatch.setenv("JULIA_LOG_HMAC_KEY_PATH", str(path))


def _run(session):
    loop = IterativeReasoningLoop(
        session=session, text="t",
        turn_context=SimpleNamespace(turn_id="turn", correlation_id="corr", conversation_id="conv"),
        messages=[], parent_package=_parent())
    return loop.run()


def _ledger_with(*specs):
    ledger = TurnLedger(hmac_key=b"k")
    for capability, outcome in specs:
        if outcome == "executed":
            ledger.record_executed(
                pass_index=1, capability_id=capability, arguments={"path": "/Users/admin/Desktop/x"},
                tool_result=SimpleNamespace(status="success", structured_output={"count": 3}, capability_call_id="c",
                                            started_at="", completed_at="", evidence_refs=("ev_1",)))
        else:
            ledger.record_not_executed(pass_index=1, reason=outcome, capability_id=capability)
    return ledger


# ── execution block text ─────────────────────────────────────────────────

def test_block_states_the_duplicate_scope_and_the_direct_execution_rule():
    text = TurnLedger(hmac_key=b"k").execution_frame(["fact"])["text"]
    assert "重复判定只在本回合内" in text and "新的回合可以再次调用同一工具" in text      # (a)
    assert "Tony 明确要求" in text and "直接执行只读 file.*" in text                      # (b)
    assert "不得以" in text and "可能被挡" in text


def test_block_forbids_repeating_a_call_already_judged_duplicate_this_turn():
    clean = TurnLedger(hmac_key=b"k").execution_frame(["fact"])["text"]
    dup = _ledger_with(("file.search", "executed"), ("file.search", "DUPLICATE_CALL")).execution_frame(["fact"])["text"]
    assert "本回合不要再发起" not in clean
    assert "file.search" in dup and "本回合不要再发起同一调用" in dup                    # (c)


def test_executed_entries_are_marked_as_this_turn():
    text = _ledger_with(("file.read", "executed")).execution_frame(["fact"])["text"]
    line = [ln for ln in text.splitlines() if "file.read" in ln][0]
    assert "本回合" in line and "已执行" in line


def test_environment_facts_do_not_reference_truncated_or_total_and_roots_are_current():
    facts = "\n".join(environment_facts())
    assert "truncated" not in facts and "total" not in facts                           # (e)
    roots_line = [ln for ln in environment_facts() if ln.startswith("file.* 允许访问的根目录")][0]
    for stale in ("~/julia_core", "julia_release"):
        assert stale not in roots_line
    assert "~/Desktop" in roots_line
    assert "~/.claude-dev/projects/-Users-admin/memory" in roots_line and "~/julia_ai_assistant/memory" in roots_line
    assert "file.search 只匹配文件名" in facts


def test_duplicate_control_text_states_its_scope():
    from julia_core.runtime.context_execution_runtime import ContextExecutionRuntime
    pkg = ContextExecutionRuntime().project_duplicate_capability_call_rejected(
        parent_package=_parent(), capability_id="file.search", arguments={"pattern": "a"}, generation_id="g_dup")
    text = str(pkg.control_frame)
    assert "本回合" in text or "within this turn only" in text


# ── executed_but_denied: record only ─────────────────────────────────────

def test_denied_execution_detector_needs_an_executed_entry_in_the_ledger():
    executed = _ledger_with(("file.read", "executed"))
    for reply in (
        "这一轮我没有执行工具，上面是之前那次读到的。",
        "那不是我刚刚读的，是上一轮的结果。",
        "我并没有真的调用 file.read，这些来自之前的回合。",
        "**这一轮我没有重新执行 `file.read`**，内容的来源是**之前那次**读到的。",     # T5 phrasing
    ):
        assert check_denied_execution(reply, executed) == ["executed_but_denied"], reply
    # honest replies about an executed call are not flagged
    for reply in ("我刚刚用 file.read 读了这个文件。", "上一轮查到的是另一份，这一轮读的是这份。"):
        assert check_denied_execution(reply, executed) == [], reply
    # with an empty ledger the same words are simply true
    assert check_denied_execution("这一轮我没有执行工具。", TurnLedger(hmac_key=b"k")) == []


def test_t5_structure_denial_is_recorded_but_not_corrected_or_blocked():
    """file.read executed successfully; the reply denies it and calls this turn's evidence 'the earlier one'."""
    denial = "这一轮我没有执行工具，上面那份是之前那次读到的。"
    session = LoopSession(
        [tool_response("file.read", {"path": "/Users/admin/Desktop/x.md"}), denial],
        outcomes=[execution(1)],
    )
    result = _run(session)
    assert result.reply == denial and result.final_response_kind == "JUDGMENT"       # not blocked
    assert result.cognition_pass_count == 2                                         # no correction pass
    checks = result.ledger_view["claim_checks"]
    assert len(checks) == 1
    assert checks[0]["categories"] == ["executed_but_denied"]
    assert checks[0]["entered_correction"] is False and checks[0]["outcome"] == "recorded_only"
    assert denial not in str(result.ledger_view)                                     # no reply text stored


def test_honest_reply_after_execution_records_nothing():
    session = LoopSession(
        [tool_response("file.read", {"path": "/Users/admin/Desktop/x.md"}), "我刚刚用 file.read 读了它。"],
        outcomes=[execution(1)],
    )
    assert _run(session).ledger_view["claim_checks"] == []
