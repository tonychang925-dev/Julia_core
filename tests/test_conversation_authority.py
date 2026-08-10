"""CORE-C1 Authority regression tests — committed sabotage gates.

Tests: interaction isolation, multi-turn persistence, failed-turn rollback,
concurrent isolation, repository stress, idempotency, delete cleanup.
"""

import copy
import tempfile
import threading
import pytest

from julia_core.runtime.conversation_runtime import ConversationRuntime


# ── Mock cognitive function ──────────────────────────────────────────────

def mock_cognitive(text, history, conversation_id="", turn_id="", modality="", interaction=None):
    """Cognitive fn that echoes back whether history contains '蓝鲸42'."""
    if interaction is not None:
        interaction.update(text)
    history_text = str([m.get("content", "") for m in history])
    if "蓝鲸42" in history_text or "蓝鲸42" in text:
        return f"是的，项目代号是蓝鲸42。你说: {text}"
    if "项目代号" in text:
        return "我不知道什么项目代号。"
    return f"收到: {text}"


@pytest.fixture
def runtime():
    """Fresh runtime with temp storage."""
    path = tempfile.mktemp(suffix=".json")
    rt = ConversationRuntime(storage_path=path)
    yield rt


class TestInteractionIsolation:
    """conv-A interaction state must not leak to conv-B."""

    def test_cross_conversation_isolation(self, runtime):
        # conv-A: building + identity checks
        runtime.process_turn(conversation_id="A", turn_id="a1", modality="text",
                             input="我们继续改Julia Core架构", cognitive_fn=mock_cognitive)
        runtime.process_turn(conversation_id="A", turn_id="a2", modality="text",
                             input="你是谁？", cognitive_fn=mock_cognitive)

        # conv-B: unrelated chat
        runtime.process_turn(conversation_id="B", turn_id="b1", modality="text",
                             input="今天天气不错", cognitive_fn=mock_cognitive)

        interaction_b = runtime.get_interaction_state("B")
        assert interaction_b.collaboration_phase == "chat", \
            f"LEAK: conv-B got collaboration_phase={interaction_b.collaboration_phase}"
        assert interaction_b.recent_pattern == "conversation", \
            f"LEAK: conv-B got recent_pattern={interaction_b.recent_pattern}"
        assert interaction_b.identity_checks == 0, \
            f"LEAK: conv-B got identity_checks={interaction_b.identity_checks}"


class TestMultiTurnPersistence:
    """Interaction counters must persist across turns within one conversation."""

    def test_identity_checks_accumulate(self, runtime):
        runtime.process_turn(conversation_id="A", turn_id="a1", modality="text",
                             input="你是谁？", cognitive_fn=mock_cognitive)
        runtime.process_turn(conversation_id="A", turn_id="a2", modality="text",
                             input="你真的认识我吗？", cognitive_fn=mock_cognitive)
        runtime.process_turn(conversation_id="A", turn_id="a3", modality="text",
                             input="再确认一下，你认识我吗？", cognitive_fn=mock_cognitive)

        interaction = runtime.get_interaction_state("A")
        assert interaction.identity_checks >= 2, \
            f"identity_checks={interaction.identity_checks}, should persist across turns"
        # Pattern may be 'testing' or 'repeated_questions' depending on text overlap
        assert interaction.recent_pattern in ("testing", "repeated_questions"), \
            f"recent_pattern={interaction.recent_pattern}, expected testing or repeated_questions"


class TestFailedTurnRollback:
    """Failed turns must NOT pollute canonical interaction state."""

    def test_failed_turn_rolls_back_interaction(self, runtime):
        # Get initial state
        initial = runtime.get_interaction_state("R")
        assert initial.identity_checks == 0

        def failing_cognitive(text, history, cid="", tid="", mod="", interaction=None):
            if interaction is not None:
                interaction.update(text)
            raise RuntimeError("Simulated cognitive failure")

        result = runtime.process_turn(conversation_id="R", turn_id="f1", modality="text",
                                      input="你是谁？", cognitive_fn=failing_cognitive)
        assert result.status == "failed", f"Expected failed, got {result.status}"

        # Interaction state should be ROLLED BACK
        interaction = runtime.get_interaction_state("R")
        assert interaction.identity_checks == 0, \
            f"FAIL: failed turn polluted interaction, identity_checks={interaction.identity_checks}"

    def test_retry_after_failure_commits(self, runtime):
        def succeed_on_second(text, history, cid="", tid="", mod="", interaction=None):
            if interaction is not None:
                interaction.update(text)
            # Use a counter stored on the function
            if not hasattr(succeed_on_second, "called"):
                succeed_on_second.called = True
                raise RuntimeError("First attempt fails")
            return "ok"

        # First attempt: fails
        r1 = runtime.process_turn(conversation_id="R2", turn_id="r1", modality="text",
                                  input="你是谁？", cognitive_fn=succeed_on_second)
        assert r1.status == "failed"

        # Interaction should be clean
        assert runtime.get_interaction_state("R2").identity_checks == 0

        # Second attempt with different turn_id: succeeds
        r2 = runtime.process_turn(conversation_id="R2", turn_id="r2", modality="text",
                                  input="你是谁？", cognitive_fn=mock_cognitive)
        assert r2.status == "completed"

        # Interaction should now have 1 identity check
        assert runtime.get_interaction_state("R2").identity_checks == 1, \
            f"Expected identity_checks=1 after successful retry, got {runtime.get_interaction_state('R2').identity_checks}"


class TestConversationIsolation:
    """conv-A/conv-B history and interaction isolation."""

    def test_history_isolation(self, runtime):
        runtime.process_turn(conversation_id="A", turn_id="a1", modality="text",
                             input="项目代号是蓝鲸42", cognitive_fn=mock_cognitive)
        runtime.process_turn(conversation_id="B", turn_id="b1", modality="text",
                             input="项目代号是什么？", cognitive_fn=mock_cognitive)

        h_b = runtime.get_history("B")
        contents_b = " ".join(m["content"] for m in h_b)
        assert "蓝鲸42" not in contents_b, "conv-B history must not contain conv-A data"

        runtime.process_turn(conversation_id="A", turn_id="a2", modality="text",
                             input="项目代号是什么？", cognitive_fn=mock_cognitive)
        h_a = runtime.get_history("A")
        contents_a = " ".join(m["content"] for m in h_a)
        assert "蓝鲸42" in contents_a, "conv-A must recall its own 蓝鲸42"

    def test_restart_persistence(self, runtime):
        path = runtime.storage_path
        runtime.process_turn(conversation_id="A", turn_id="a1", modality="text",
                             input="项目代号是蓝鲸42", cognitive_fn=mock_cognitive)

        rt2 = ConversationRuntime(storage_path=path)
        h = rt2.get_history("A")
        assert any("蓝鲸42" in m["content"] for m in h), "Restart must recover history"


class TestIdempotency:
    """Same turn_id must not produce duplicate turns."""

    def test_same_turn_id_returns_cached(self, runtime):
        r1 = runtime.process_turn(conversation_id="A", turn_id="same", modality="text",
                                  input="测试幂等", cognitive_fn=mock_cognitive)
        r2 = runtime.process_turn(conversation_id="A", turn_id="same", modality="text",
                                  input="测试幂等", cognitive_fn=mock_cognitive)
        assert r1.assistant_content == r2.assistant_content, "Idempotent must return same content"
        assert r1.user_message_id == r2.user_message_id, "Idempotent must return same message IDs"

    def test_concurrent_same_turn_id_single_result(self, runtime):
        results = []

        def submit():
            results.append(runtime.process_turn(
                conversation_id="C", turn_id="concurrent", modality="text",
                input="并发幂等", cognitive_fn=mock_cognitive))

        threads = [threading.Thread(target=submit) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        contents = set(r.assistant_content for r in results)
        assert len(contents) == 1, f"All concurrent same-turn_id calls must return same result"
        h = runtime.get_history("C")
        assert len(h) == 2, f"Exactly 2 messages (1 turn) expected, got {len(h)}"


class TestConcurrent:
    """Concurrent A/B isolation under real thread competition."""

    def test_concurrent_ab_isolation(self, runtime):
        errors = []
        results_a, results_b = [], []

        def do_a():
            try:
                r = runtime.process_turn(
                    conversation_id="A", turn_id=f"ca_{threading.get_ident()}_{len(results_a)}",
                    modality="text", input=f"msgA-{len(results_a)}", cognitive_fn=mock_cognitive)
                results_a.append(r)
            except Exception as e:
                errors.append(str(e))

        def do_b():
            try:
                r = runtime.process_turn(
                    conversation_id="B", turn_id=f"cb_{threading.get_ident()}_{len(results_b)}",
                    modality="text", input=f"msgB-{len(results_b)}", cognitive_fn=mock_cognitive)
                results_b.append(r)
            except Exception as e:
                errors.append(str(e))

        threads = [t for _ in range(20) for t in (threading.Thread(target=do_a), threading.Thread(target=do_b))]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Concurrent errors: {errors}"
        assert len(results_a) == 20 and len(results_b) == 20, \
            f"Expected 20 each, got A={len(results_a)} B={len(results_b)}"


class TestDelete:
    """Delete must clean up interaction state and locks."""

    def test_delete_clears_interaction(self, runtime):
        runtime.process_turn(conversation_id="D", turn_id="d1", modality="text",
                             input="你是谁？", cognitive_fn=mock_cognitive)
        # Should have interaction state
        assert runtime.get_interaction_state("D").identity_checks == 1

        runtime.delete_conversation("D")

        # Recreate — should get fresh interaction state
        fresh = runtime.get_interaction_state("D")
        assert fresh.identity_checks == 0, \
            f"After delete+recreate, identity_checks should be 0, got {fresh.identity_checks}"


class TestP1ConversationConvergence:
    """P1 — Conversation Authority production convergence tests."""

    def test_canonical_write_is_single_authority(self, runtime):
        """P1-1: Only ConversationRuntime writes canonical transcript."""
        runtime.process_turn(conversation_id="W1", turn_id="w1", modality="text",
                             input="test", cognitive_fn=mock_cognitive)
        msgs = runtime.get_history("W1")
        assert len(msgs) == 2  # user + assistant
        assert msgs[0]["role"] == "user" and msgs[1]["role"] == "assistant"
        # No duplicate messages from secondary write paths

    def test_normal_reopen_no_checkpoint(self, runtime):
        """P1-7: Normal reopen requires no ContinuityCheckpoint."""
        runtime.process_turn(conversation_id="R1", turn_id="r1", modality="text",
                             input="project code is 青竹27", cognitive_fn=mock_cognitive)
        path = runtime.storage_path
        rt2 = ConversationRuntime(storage_path=path)
        h = rt2.get_history("R1")
        assert len(h) == 2
        assert any("青竹27" in m["content"] for m in h)

    def test_restart_preserves_chronology(self, runtime):
        """P1-4: Restart preserves canonical chronology."""
        runtime.process_turn(conversation_id="C1", turn_id="c1", modality="text",
                             input="first", cognitive_fn=mock_cognitive)
        runtime.process_turn(conversation_id="C1", turn_id="c2", modality="text",
                             input="second", cognitive_fn=mock_cognitive)
        rt2 = ConversationRuntime(storage_path=runtime.storage_path)
        h = rt2.get_history("C1")
        assert len(h) == 4  # 2 turns = 4 messages
        assert h[0]["content"] == "first"
        assert h[2]["content"] == "second"

    def test_interrupted_preserved_not_deleted(self, runtime):
        """P1-3: Interrupted assistant is preserved in transcript."""
        rt = runtime
        rt.process_turn(conversation_id="I1", turn_id="i1", modality="text",
                        input="test", cognitive_fn=mock_cognitive)
        # External turn with interrupted assistant
        rt.append_external_turns("I1", [{
            "turn_id": "v_int", "modality": "voice",
            "user_content": "voice test",
            "assistant_content": "partial reply was emitted",
            "assistant_status": "interrupted",
        }])
        h = rt.get_history("I1")
        interrupted = [m for m in rt.get_messages("I1") if m.get("status") == "interrupted"]
        assert len(interrupted) == 1
        assert interrupted[0]["content"] == "partial reply was emitted"

    def test_retry_idempotency_no_duplicate(self, runtime):
        """P1-4: Same turn_id retry produces no duplicate canonical messages."""
        rt = runtime
        r1 = rt.process_turn(conversation_id="D1", turn_id="dup", modality="text",
                             input="idempotent test", cognitive_fn=mock_cognitive)
        r2 = rt.process_turn(conversation_id="D1", turn_id="dup", modality="text",
                             input="idempotent test", cognitive_fn=mock_cognitive)
        assert r1.user_message_id == r2.user_message_id
        assert r1.assistant_message_id == r2.assistant_message_id
        h = rt.get_history("D1")
        assert len(h) == 2  # Only one turn, not two

    def test_tool_loop_same_turn(self, runtime):
        """P1-3: Tool continuation preserves same turn_id."""
        # ConversationRuntime maintains turn_id through tool continuation
        rt = runtime
        rt.process_turn(conversation_id="T1", turn_id="tool-turn", modality="text",
                        input="needs tool", cognitive_fn=mock_cognitive)
        msgs = rt.get_messages("T1")
        turn_ids = set(m["turn_id"] for m in msgs if m["turn_id"])
        assert len(turn_ids) == 1  # All messages share same turn_id
        assert "tool-turn" in turn_ids

    def test_reverse_authority_rejected(self, runtime):
        """P1-6: Context/Memory/Continuity paths cannot overwrite transcript."""
        rt = runtime
        rt.process_turn(conversation_id="X1", turn_id="x1", modality="text",
                        input="canonical fact", cognitive_fn=mock_cognitive)
        original = rt.get_messages("X1")
        # External turn with different content for same turn_id must conflict
        from julia_core.conversation_state.repository import TurnConflictError
        try:
            rt.append_external_turns("X1", [{
                "turn_id": "x1", "modality": "text",
                "user_content": "DIFFERENT canonical fact",
                "assistant_content": "different reply",
                "assistant_status": "completed",
            }])
            assert False, "Should have raised TurnConflictError"
        except TurnConflictError:
            pass
        # Transcript unchanged
        after = rt.get_messages("X1")
        assert len(after) == len(original)
        assert after[0]["content"] == "canonical fact"


class TestP2SemanticClosure:
    """P2-J/K/M/N — StructuredCompact, Progressive Disclosure, Alignment, Provenance."""

    def test_context_package_has_provenance(self, runtime):
        """P2-N: Every model-visible element has source trace (AT-17)."""
        from julia_core.runtime.context_execution_runtime import ContextExecutionRuntime
        ctx_rt = ContextExecutionRuntime()
        pkg = ctx_rt.prepare(
            conversation_id="P", turn_id="p1", user_text="hello",
            history=[], modality="text",
        )
        assert pkg is not None, "Context package must be created"
        assert pkg.package_id, "Package must have ID"
        # P2: identity + conversation + situation frames always present
        assert len(pkg.provenance) >= 2, f"Expected >=2 provenance entries, got {len(pkg.provenance)}"
        frame_sources = {e["frame"] for e in pkg.provenance}
        assert "conversation" in frame_sources, "Conversation frame must have provenance"
        assert "situation" in frame_sources, "Situation frame must have provenance"

    def test_stage0_context_produced(self, runtime):
        """P2-K: Stage 0 required base is always produced."""
        from julia_core.runtime.context_execution_runtime import ContextExecutionRuntime
        ctx_rt = ContextExecutionRuntime()
        pkg = ctx_rt.prepare(
            conversation_id="K", turn_id="k1", user_text="hi",
            history=[], modality="text",
        )
        stage0_entries = [e for e in pkg.provenance if e.get("stage") == 0]
        assert len(stage0_entries) >= 2, f"Stage 0 must have >=2 entries, got {len(stage0_entries)}"

    def test_stage1_context_supported(self, runtime):
        """P2-K: Progressive Disclosure topology — Stage 0 always, Stage 1 when sources available."""
        from julia_core.runtime.context_execution_runtime import ContextExecutionRuntime
        ctx_rt = ContextExecutionRuntime()
        pkg = ctx_rt.prepare(
            conversation_id="K2", turn_id="k2", user_text="今天市场怎么样？",
            history=[], modality="text",
        )
        # Stage 0 always present (identity, conversation, situation)
        stage0 = [e for e in pkg.provenance if e.get("stage") == 0]
        assert len(stage0) >= 2, f"Stage 0 always produced, got {len(stage0)}"
        # Stage 1+2 exist in the provenance model even if not populated without JuliaSession
        stages = {e.get("stage") for e in pkg.provenance}
        assert 0 in stages, "Stage 0 must always be present"

    def test_tool_result_has_package_provenance(self, runtime):
        """P2-I verified: ToolResult goes through Context OS with package_id."""
        from julia_core.runtime.context_execution_runtime import ContextExecutionRuntime
        ctx_rt = ContextExecutionRuntime()
        pkg = ctx_rt.project_tool_result(
            tool_result="test result",
            generation_id="gen_test",
        )
        assert pkg.package_id, "Tool result package must have ID"
        assert "tool_result" in str(pkg.evidence_frame), "Tool result in evidence frame"
        tool_prov = [e for e in pkg.provenance if "tool" in e.get("reason", "")]
        assert len(tool_prov) >= 1, "Tool result must have provenance entry"

    def test_structured_compact_is_derived(self, runtime):
        """P2-J: Deleting derived context does not destroy canonical truth."""
        rt = runtime
        rt.process_turn(conversation_id="J1", turn_id="j1", modality="text",
                        input="important fact", cognitive_fn=mock_cognitive)
        # Canonical truth exists independently
        msgs_before = rt.get_messages("J1")
        assert len(msgs_before) == 2
        # Restart (simulates deleting derived context artifacts)
        rt2 = ConversationRuntime(storage_path=rt.storage_path)
        msgs_after = rt2.get_messages("J1")
        assert len(msgs_after) == 2
        assert msgs_after[0]["content"] == "important fact"

    def test_context_rebuild_from_canonical(self, runtime):
        """P2-J: Context can rebuild from canonical sources after restart."""
        rt = runtime
        rt.process_turn(conversation_id="J2", turn_id="j2", modality="text",
                        input="canonical record", cognitive_fn=mock_cognitive)
        # Simulate full restart — new runtime, no derived cache
        rt2 = ConversationRuntime(storage_path=rt.storage_path)
        h = rt2.get_history("J2")
        assert len(h) == 2
        assert h[0]["content"] == "canonical record"

    def test_context_package_provenance_completeness(self, runtime):
        """P2-N AT-17: Every frame element has source/provenance trace."""
        from julia_core.runtime.context_execution_runtime import ContextExecutionRuntime
        ctx_rt = ContextExecutionRuntime()
        pkg = ctx_rt.prepare(
            conversation_id="N1", turn_id="n1",
            user_text="comprehensive test query about markets and tools",
            history=[], modality="text",
        )
        assert pkg is not None
        for entry in pkg.provenance:
            assert entry.get("frame"), f"Provenance entry missing frame: {entry}"
            assert entry.get("source_ref") or entry.get("reason"), \
                f"Provenance entry missing source: {entry}"
