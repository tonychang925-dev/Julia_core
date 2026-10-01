"""CARD 7 (#235 / #225 / #233): per-turn execution ledger, execution block,
completion-claim check and honesty rule.

Regression scenarios are described by structure only (no conversation text)."""
from __future__ import annotations

import json
import os
from types import SimpleNamespace

import pytest

from julia_core.runtime.iterative_reasoning import IterativeReasoningLoop
from julia_core.runtime.turn_ledger import (
    HONESTY_RULE,
    LIMITED_REPLY,
    TurnLedger,
    check_completion_claims,
    correction_prompt,
    HmacKeyUnavailable,
    load_hmac_key,
    resolve_hmac_key,
    summarize_arguments,
)
from tests.runtime._card6_base import BASE_FRAMES, SITUATION
from tests.runtime.test_rd1_p2_i3b_production_iterative_reasoning_loop import (
    LoopSession,
    execution,
    parent_package as policy_parent,
    tool_response,
)

SECRET_QUERY = "ZZ-private-search-terms-4711"
SECRET_PATH_PART = "private_notes_8842"


@pytest.fixture
def key_file(tmp_path, monkeypatch):
    path = tmp_path / "log_hmac.key"
    path.write_bytes(b"unit-test-key-material")
    os.chmod(path, 0o600)
    monkeypatch.setenv("JULIA_LOG_HMAC_KEY_PATH", str(path))
    return path


@pytest.fixture(autouse=True)
def _default_key(key_file):
    return key_file


def _parent():
    import copy
    parent = policy_parent()
    for name, value in BASE_FRAMES.items():
        setattr(parent, name, copy.deepcopy(value))
    parent.situation_frame = copy.deepcopy(SITUATION)
    return parent


def _run(session, text="Ask Julia"):
    loop = IterativeReasoningLoop(
        session=session,
        text=text,
        turn_context=SimpleNamespace(turn_id="turn", correlation_id="corr", conversation_id="conv"),
        messages=[{"role": "user", "content": text}],
        parent_package=_parent(),
    )
    return loop.run(), loop


def _system(session, pass_number):
    return session.model_inputs[pass_number - 1][0]["content"]


def _exec_with(structured_output):
    return execution(1, structured_output=structured_output)


# ── HMAC key + argument summary ──────────────────────────────────────────

def test_hmac_key_fails_closed_with_an_explicit_reason(tmp_path):
    def reason(path):
        with pytest.raises(HmacKeyUnavailable) as info:
            load_hmac_key(path)
        return info.value.reason

    assert reason(tmp_path / "missing.key") == "missing"
    loose = tmp_path / "loose.key"
    loose.write_bytes(b"k")
    os.chmod(loose, 0o644)
    assert reason(loose) == "insecure_permissions"      # group/other readable
    empty = tmp_path / "empty.key"
    empty.write_bytes(b"")
    os.chmod(empty, 0o600)
    assert reason(empty) == "empty"
    assert reason(tmp_path) in {"insecure_permissions", "unreadable"}   # a directory is not a key
    good = tmp_path / "good.key"
    good.write_bytes(b"secret\n")
    os.chmod(good, 0o600)
    assert load_hmac_key(good) == b"secret"
    assert resolve_hmac_key(good) == (b"secret", "ok")
    assert resolve_hmac_key(tmp_path / "missing.key") == (None, "missing")


def test_ledger_event_view_reports_why_the_key_is_unavailable():
    view = TurnLedger(hmac_key=None, hmac_status="insecure_permissions").event_view()
    assert view["hmac_unavailable"] is True and view["hmac_status"] == "insecure_permissions"
    assert "hmac_unavailable" not in TurnLedger(hmac_key=b"k", hmac_status="ok").event_view()


def test_market_identifiers_plain_everything_else_hashed():
    key = b"k"
    market = summarize_arguments("market.stock.quote.read", {"stock_id": "600519.SH", "trade_date": "2026-07-03"}, key)
    assert market["plain"] == {"stock_id": "600519.SH", "trade_date": "2026-07-03"} and market["hashed"] == {}
    research = summarize_arguments("research.web.query", {"query": SECRET_QUERY}, key)
    assert research["plain"] == {} and SECRET_QUERY not in json.dumps(research)
    assert research["hashed"]["query"]["len"] == len(SECRET_QUERY) and "hmac" in research["hashed"]["query"]
    # an unregistered argument on a Market capability is still hashed (default deny)
    other = summarize_arguments("market.state.read", {"free_text": "abc"}, key)
    assert other["plain"] == {} and "free_text" in other["hashed"]


def test_missing_key_never_emits_an_unkeyed_hash():
    summary = summarize_arguments("file.search", {"pattern": SECRET_QUERY}, None)
    entry = summary["hashed"]["pattern"]
    assert entry == {"len": len(SECRET_QUERY), "hmac_unavailable": True}
    ledger = TurnLedger(hmac_key=None)
    assert ledger.event_view()["hmac_unavailable"] is True


def test_file_calls_record_root_label_not_the_file_name():
    ledger = TurnLedger(hmac_key=b"k", allowed_roots=(os.path.expanduser("~/Desktop") and __import__("pathlib").Path("/Users/admin/Desktop"),))
    entry = ledger.record_not_executed(
        pass_index=1, reason="X", capability_id="file.read",
        arguments={"path": f"/Users/admin/Desktop/{SECRET_PATH_PART}.md"},
    )
    dump = json.dumps(entry.view(), ensure_ascii=False)
    assert entry.args["root_label"] == "~/Desktop"
    outside = ledger.record_not_executed(pass_index=1, reason="X", capability_id="file.read", arguments={"path": "/etc/hosts"})
    assert outside.args["root_label"] == "outside_allowed_roots"
    unresolved = ledger.record_not_executed(pass_index=1, reason="X", capability_id="file.read", arguments={"path": ""})
    assert unresolved.args["root_label"] == "unresolved"
    assert SECRET_PATH_PART not in dump and "/Users/admin/Desktop/" not in dump


# ── ledger written by the loop ───────────────────────────────────────────

def test_one_successful_call_is_recorded_with_metadata_and_no_content():
    session = LoopSession(
        [tool_response("research.web.query", {"query": SECRET_QUERY}), "Julia final judgment"],
        outcomes=[_exec_with({"data_state": "READY", "payload": {"x": 1}})],
    )
    result, _ = _run(session)
    view = result.ledger_view
    assert [e["outcome"] for e in view["entries"]] == ["executed"]
    entry = view["entries"][0]
    assert entry["capability_id"] == "research.web.query"
    assert entry["status"] and entry["data_state"] == "READY" and entry["pass_index"] == 1
    assert entry["args"]["hashed"]["query"]["len"] == len(SECRET_QUERY)
    assert [p["pass_index"] for p in view["passes"]] == [1, 2]
    for p in view["passes"]:
        assert len(p["prompt_sha256"]) == 64 and p["system_chars"] > 0
        assert {"identity", "experience", "continuity", "situation", "execution"} <= set(p["blocks"])
        assert all(set(b) == {"chars", "original_chars", "truncated"} for b in p["blocks"].values())
    dump = json.dumps(view, ensure_ascii=False)
    assert SECRET_QUERY not in dump and "IDENTITY-MARK" not in dump and "Julia final judgment" not in dump


def test_prompt_hash_covers_the_text_actually_sent():
    import hashlib
    session = LoopSession(["Julia final judgment"])
    result, _ = _run(session)
    sent = session.model_inputs[0]
    digest = hashlib.sha256()
    for m in sent:
        digest.update(str(m["role"]).encode()); digest.update(b"\x00")
        digest.update(str(m["content"]).encode()); digest.update(b"\x01")
    assert result.ledger_view["passes"][0]["prompt_sha256"] == digest.hexdigest()


def test_truncated_block_is_flagged_with_original_length():
    parent = _parent()
    parent.experience_frame = {f"k{i:02d}": "y" * 1500 for i in range(30)}
    session = LoopSession(["Julia final judgment"])
    loop = IterativeReasoningLoop(
        session=session, text="t", turn_context=SimpleNamespace(turn_id="t", correlation_id="c", conversation_id="v"),
        messages=[], parent_package=parent)
    block = loop.run().ledger_view["passes"][0]["blocks"]["experience"]
    assert block["truncated"] is True and block["original_chars"] > block["chars"]


def test_malformed_call_is_recorded_not_executed_and_visible_next_pass():
    """T14 structure: a malformed call block is dropped."""
    session = LoopSession(["```tool_call\n{broken}\n```", "我这一轮没有执行工具。"])
    result, _ = _run(session)
    entry = result.ledger_view["entries"][0]
    assert (entry["outcome"], entry["status"], entry["reason"], entry["pass_index"]) == (
        "not_executed", "not_executed", "MALFORMED_JSON", 1)
    assert result.capability_execution_count == 0
    assert "没有执行：原因=MALFORMED_JSON" in _system(session, 2)


@pytest.mark.parametrize("reason", ["UNKNOWN", "DISABLED"])
def test_unknown_or_disabled_capability_is_not_executed(reason):
    failure = SimpleNamespace(capability_id="x.y", reason=reason, tool_result=None, capability_call=None, evidence=())
    session = LoopSession([tool_response("x.y", {}), "没有拿到结果。"], outcomes=[failure])
    result, _ = _run(session)
    entry = result.ledger_view["entries"][0]
    assert entry["outcome"] == "not_executed" and entry["reason"] == f"{reason}_CAPABILITY"
    assert result.capability_execution_count == 0


def test_duplicate_call_and_budget_are_recorded():
    same = tool_response("research.web.query", {"query": "a"})
    session = LoopSession([same, same, "最终回答。"])
    result, _ = _run(session)
    assert [(e["outcome"], e.get("reason", "")) for e in result.ledger_view["entries"]] == [
        ("executed", ""), ("not_executed", "DUPLICATE_CALL")]

    calls = [tool_response("research.web.query", {"query": str(i)}) for i in range(3)] + ["最终回答。"]
    session = LoopSession(calls)
    result, _ = _run_with_limit(session, 1)
    assert "BUDGET_EXCEEDED" in [e.get("reason") for e in result.ledger_view["entries"]]


def _run_with_limit(session, limit):
    loop = IterativeReasoningLoop(
        session=session, text="t", turn_context=SimpleNamespace(turn_id="t", correlation_id="c", conversation_id="v"),
        messages=[], parent_package=_parent(), _capability_execution_limit=limit)
    return loop.run(), loop


# ── execution block ──────────────────────────────────────────────────────

def test_execution_block_is_independent_generated_and_carries_environment_facts():
    session = LoopSession(["Julia final judgment"])
    _run(session)
    system = _system(session, 1)
    assert "[execution]" in system
    assert "本回合到目前为止没有执行任何工具" in system
    assert "同一台" in system and "正式 memory 位置" in system and "file.search 只匹配文件名" in system
    # not placed inside the situation block
    situation = system.split("[situation]")[1].split("\n\n")[0]
    assert "[execution]" not in situation and "没有执行任何工具" not in situation


def test_execution_block_lists_executed_and_not_executed_for_the_next_pass():
    session = LoopSession(
        [tool_response("market.state.read", {"trade_date": "2026-07-03"}), "Julia final judgment"],
        outcomes=[_exec_with({"data_state": "READY"})],
    )
    _run(session)
    assert "market.state.read 已执行：状态=" in _system(session, 2) and "data_state=READY" in _system(session, 2)


def test_execution_block_is_never_silently_truncated():
    ledger = TurnLedger(hmac_key=b"k")
    for i in range(400):
        ledger.record_not_executed(pass_index=1, reason="DUPLICATE_CALL", capability_id=f"market.state.read{i}")
    frame = ledger.execution_frame(["fact"])
    assert frame["truncated"] is True and "[truncated:" in frame["text"] and len(frame["text"]) <= 4000
    small = TurnLedger(hmac_key=b"k").execution_frame(["fact"])
    assert small["truncated"] is False


def test_honesty_rule_is_in_behaviour_rules_and_correction_prompt():
    from julia_core.runtime.capability_bridge import RuntimeCapabilityBridge
    policy = RuntimeCapabilityBridge().invocation_policy() if hasattr(RuntimeCapabilityBridge, "invocation_policy") else None
    assert policy is not None
    assert policy["epistemic_rules"]["honesty"]["rule"] == HONESTY_RULE
    assert "诚实比让 Tony 安心更重要" in HONESTY_RULE and "我只看到一部分" in HONESTY_RULE
    prompt = correction_prompt(["zero_execution_status_claim"])
    assert HONESTY_RULE in prompt and "必须说明来源" in prompt


# ── completion-claim check ───────────────────────────────────────────────

def test_t18_zero_execution_status_claim_is_corrected_then_accepted():
    """Zero executions but the reply states a capability status code."""
    bad = "我刚跑了 file.read，结果是 status=not_found。"
    good = "这一轮我没有执行工具，所以没有查到结果。"
    session = LoopSession([bad, good])
    result, _ = _run(session)
    assert result.reply == good and result.final_response_kind == "JUDGMENT"
    assert result.cognition_pass_count == 2
    check = result.ledger_view["claim_checks"][0]
    assert check["entered_correction"] is True and check["outcome"] == "compliant_after_correction"
    assert "zero_execution_status_claim" in check["categories"]
    assert "completion_claim_correction" in _system(session, 2) or "没有被交付" in _system(session, 2)
    assert bad not in json.dumps(result.ledger_view, ensure_ascii=False)   # no reply text stored


def test_still_non_compliant_after_correction_returns_limited_reply():
    bad = "我刚跑了 file.read，结果是 status=not_found。"
    session = LoopSession([bad, bad])
    result, _ = _run(session)
    assert result.reply == LIMITED_REPLY and result.final_response_kind == "LIMITATION"
    assert result.termination == "claim_check_limited"
    check = result.ledger_view["claim_checks"][0]
    assert check["outcome"] == "limited_reply_after_correction"


def test_fabricated_path_with_zero_execution_is_caught():
    """Zero executions, concrete (non-existent) directory and file paths listed."""
    bad = "我列出来了：/Users/admin/Desktop/memory/ 下有 /Users/admin/Desktop/memory/a.md 和 /Users/admin/Desktop/memory/b.md。"
    assert "zero_execution_path_claim" in check_completion_claims(bad, TurnLedger(hmac_key=b"k"))


def test_file_list_only_but_claims_file_contents_read():
    ledger = TurnLedger(hmac_key=b"k")
    ledger.record_executed(
        pass_index=1, capability_id="file.list", arguments={"path": "/Users/admin/Desktop"},
        tool_result=SimpleNamespace(status="success", structured_output={"count": 3}, capability_call_id="c1",
                                    started_at="", completed_at="", evidence_refs=()))
    assert "unmatched_capability_claim" in check_completion_claims("我用 file.read 读了文件内容，里面写着……", ledger)
    assert check_completion_claims("我用 file.list 列了目录，一共返回 3 条。", ledger) == []


def test_truncated_list_reported_as_complete_is_caught_and_partial_ack_passes():
    ledger = TurnLedger(hmac_key=b"k")
    ledger.record_executed(
        pass_index=1, capability_id="file.list", arguments={"path": "/Users/admin/Desktop"},
        tool_result=SimpleNamespace(status="success", structured_output={"truncated": True, "total": 54, "count": 30},
                                    capability_call_id="c1", started_at="", completed_at="", evidence_refs=()))
    assert "truncated_reported_as_complete" in check_completion_claims("桌面上的 .md 一共就这几个。", ledger)
    assert check_completion_claims("我只看到一部分：返回了 30 条，总共 54 条。", ledger) == []


def test_normal_replies_are_not_flagged():
    empty = TurnLedger(hmac_key=b"k")
    for reply in (
        "好呀，我陪你。",
        "这一轮我没有执行工具，所以我没有查到。",
        "上一轮查到的那份文件，我记得里面有八篇文章。",
        "我可以用 file.read 帮你读，你想读哪一个？",
        "今天是 2026 年 10 月 1 日，星期四。",
    ):
        assert check_completion_claims(reply, empty) == [], reply


def test_matching_claims_with_ledger_pass_without_correction():
    session = LoopSession(
        [tool_response("market.state.read", {"trade_date": "2026-07-03"}), "我用 market.state.read 查到了那天的数据。"],
        outcomes=[_exec_with({"data_state": "READY"})],
    )
    result, _ = _run(session)
    assert result.ledger_view["claim_checks"] == [] and result.cognition_pass_count == 2


def test_no_pass_left_for_correction_returns_limited_reply():
    from julia_core.runtime.iterative_reasoning import MAX_COGNITION_PASSES_PER_TURN
    chain = [tool_response("market.state.read", {"trade_date": f"2026-07-0{i}"}) for i in range(1, 7)]
    session = LoopSession(chain + ["我刚跑了 file.read，结果是 status=not_found。"], outcomes=[_exec_with({}) for _ in range(6)])
    result, _ = _run(session)
    assert MAX_COGNITION_PASSES_PER_TURN == 7
    assert result.final_response_kind == "LIMITATION" and result.reply == LIMITED_REPLY
    assert result.ledger_view["claim_checks"][-1]["outcome"] == "limited_reply_no_pass_left"


# ── event payload ────────────────────────────────────────────────────────

def test_turn_completed_event_carries_the_redacted_ledger(monkeypatch):
    import julia_core.events.store as event_store_module
    import julia_core.runtime.julia_session as julia_session_module
    from julia_core.runtime.context_execution_runtime import ContextExecutionRuntime

    class _Provider:
        responses = [tool_response("market.state.read", {"trade_date": "2026-07-03"}), "Julia final judgment"]

        def chat(self, messages, cognitive_mode):
            return self.responses.pop(0)

    class _Cap:
        def execute_tool_typed(self, tool_json):
            return execution(1, structured_output={"data_state": "READY"})

    class _Action:
        def start(self, *a, **k): pass
        def finish(self, *a, **k): pass

    class _Rec:
        def record(self, *a, **k): pass

    class _Store:
        events = []
        def append(self, event): self.events.append(event)

    store = _Store()
    session = julia_session_module.JuliaSession.__new__(julia_session_module.JuliaSession)
    session.provider, session.capability, session.action, session.recorder = _Provider(), _Cap(), _Action(), _Rec()
    session.context_os = ContextExecutionRuntime()

    def fake_prepare(self, text, ctx):
        package = _parent()
        ctx._last_package = package
        return package.to_messages(package.active_tail_messages, text)

    monkeypatch.setattr(julia_session_module.JuliaSession, "_prepare_turn", fake_prepare)
    monkeypatch.setattr(julia_session_module.JuliaSession, "_update_conversation_state", lambda self, t, r, c: None)
    monkeypatch.setattr(event_store_module, "get_event_store", lambda: store)
    assert session.process("hello", [], conversation_id="conv", turn_id="turn") == "Julia final judgment"
    payload = [e for e in store.events if e.event_type == "conversation.turn.completed"][0].payload
    assert payload["ledger"]["entries"][0]["capability_id"] == "market.state.read"
    assert payload["ledger"]["entries"][0]["args"]["plain"] == {"trade_date": "2026-07-03"}
    assert len(payload["ledger"]["passes"]) == 2 and "cognition_pass_trace" in payload
    assert "Julia final judgment" not in json.dumps(payload["ledger"])


# ── review fixes (Mira / Owner) ──────────────────────────────────────────

def test_bare_qianmian_is_not_a_source_statement():
    """Zero executions: '前面列给你了' + 2 absolute paths must still trigger."""
    reply = "前面列给你了：/Users/admin/Desktop/memory/a.md 和 /Users/admin/Desktop/memory/b.md。"
    assert "zero_execution_path_claim" in check_completion_claims(reply, TurnLedger(hmac_key=b"k"))
    # an explicit source statement is still accepted
    ok = "上一轮列给你的是：/Users/admin/Desktop/a.md 和 /Users/admin/Desktop/b.md。"
    assert check_completion_claims(ok, TurnLedger(hmac_key=b"k")) == []


def test_bare_bufen_is_not_a_partial_result_acknowledgement():
    ledger = TurnLedger(hmac_key=b"k")
    ledger.record_executed(
        pass_index=1, capability_id="file.list", arguments={"path": "/Users/admin/Desktop"},
        tool_result=SimpleNamespace(status="success", structured_output={"truncated": True, "total": 54, "count": 30},
                                    capability_call_id="c1", started_at="", completed_at="", evidence_refs=()))
    assert "truncated_reported_as_complete" in check_completion_claims("这部分是你的工作文件。", ledger)
    for ok in ("我只看到一部分。", "只拿到前 30 条。", "总共 54 条，结果被截断了。", "还有 24 more 没列出来。"):
        assert check_completion_claims(ok, ledger) == [], ok
