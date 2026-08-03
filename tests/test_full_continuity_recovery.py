from __future__ import annotations

import unittest

from julia_core.continuity import (
    ContinuityDecision,
    ContinuityEvent,
    ContinuityLevel,
    MemoryImportance,
    RecoveryTrigger,
    RecoveryTriggerInput,
    TTLPolicy,
    create_checkpoint,
    create_recovery_plan,
)
from julia_core.continuity.memory_governance_adapter import MemoryGovernanceAdapter
from julia_core.context_os import ContextReconstructionRequest, ContextReconstructor
from julia_core.context_os.continuity_adapter import ContextContinuityAdapter, ContextContinuityRequest
from julia_core.runtime.continuity_hook import RuntimeContinuityHook
from julia_core.runtime.trace_pipeline import ContinuityTracePipeline, RuntimeTraceContext


class FullContinuityRecoveryTest(unittest.TestCase):
    def _identity_checkpoint(self):
        governance = MemoryGovernanceAdapter().evaluate(
            {
                "agent_id": "julia",
                "memory_ref": "memory://event/julia-core-origin",
                "type": "project",
                "importance": MemoryImportance.CRITICAL,
                "signals": {
                    "identity_related": True,
                    "relationship_related": True,
                    "project_related": True,
                    "provider_independent": True,
                },
            }
        )
        decision = ContinuityDecision(
            decision_id="full-recovery-governance",
            request_id="full-recovery-memory",
            level=governance.continuity_level,
            preserve=governance.checkpoint_eligible,
            checkpoint_required=governance.checkpoint_eligible,
            reason=governance.reason,
            protected_refs=[governance.protected_ref] if governance.protected_ref else [],
            ttl_policy=TTLPolicy.PROTECT,
        )
        checkpoint = create_checkpoint(
            agent_id="julia",
            identity_refs=["persona://julia/v1"],
            relationship_refs=["memory://relationship/tony-julia"],
            active_project_refs=["project://julia-core"],
            decisions=[decision],
            checkpoint_id="checkpoint://julia/full-continuity-recovery",
        )
        return checkpoint

    def test_identity_survives_compact_without_session_or_context(self) -> None:
        checkpoint = self._identity_checkpoint()
        session_history = ["identity-forming conversation existed"]
        context_window = ["old context window existed"]

        session_history.clear()
        context_window.clear()

        recovery_decision = RecoveryTrigger().evaluate(
            RecoveryTriggerInput(
                event=ContinuityEvent.RUNTIME_RECOVERY,
                checkpoint_available=True,
            )
        )
        plan = create_recovery_plan(checkpoint, recovery_reason="compact", current_provider="gpt")
        requirements = ContextContinuityAdapter().build_requirements(
            ContextContinuityRequest(
                checkpoint_id=checkpoint.checkpoint_id,
                required_continuity_level="L3_IDENTITY",
                recovery_plan=plan,
            )
        )
        context_result = ContextReconstructor().reconstruct(
            checkpoint,
            plan,
            ContextReconstructionRequest(
                agent_id="julia",
                recovery_plan_id=plan.recovery_plan_id,
                checkpoint_id=checkpoint.checkpoint_id,
                current_intent="full_continuity_recovery",
            ),
        )

        self.assertEqual(session_history, [])
        self.assertEqual(context_window, [])
        self.assertTrue(recovery_decision.recovery_required)
        self.assertIn("persona://julia/v1", checkpoint.identity_refs)
        self.assertIn("memory://event/julia-core-origin", checkpoint.protected_memory_refs)
        self.assertTrue(any(req.required_type == "identity_anchor" for req in requirements.context_requirements))
        self.assertTrue(context_result.continuity_restored)
        self.assertIn("identity", [block.block_type for block in context_result.context_blocks])

    def test_provider_switch_survival_checkpoint_unchanged(self) -> None:
        checkpoint = self._identity_checkpoint()
        before = checkpoint.to_dict()

        decision = RecoveryTrigger().evaluate(
            RecoveryTriggerInput(
                event=ContinuityEvent.PROVIDER_SWITCH,
                checkpoint_available=True,
                provider_changed=True,
                previous_provider="deepseek",
                current_provider="gpt",
            )
        )
        hook = RuntimeContinuityHook(checkpoint_lookup=lambda _agent_id: checkpoint)
        inspection = hook.check_state(event=ContinuityEvent.PROVIDER_SWITCH)

        self.assertTrue(decision.provider_changed)
        self.assertFalse(decision.continuity_state_changed)
        self.assertEqual(before, checkpoint.to_dict())
        self.assertTrue(inspection.checkpoint_found)
        self.assertEqual(inspection.decision_level, "L3_IDENTITY")

    def test_session_loss_generates_recovery_plan_and_context_requirements(self) -> None:
        checkpoint = self._identity_checkpoint()
        old_session = {"session_id": "old-session", "state": "destroyed"}
        del old_session

        hook = RuntimeContinuityHook(checkpoint_lookup=lambda _agent_id: checkpoint)
        inspection = hook.check_state(event=ContinuityEvent.RUNTIME_RECOVERY)
        plan = create_recovery_plan(checkpoint, recovery_reason="session_loss")
        requirements = ContextContinuityAdapter().build_requirements(
            ContextContinuityRequest(
                checkpoint_id=checkpoint.checkpoint_id,
                required_continuity_level=inspection.decision_level,
                recovery_plan=plan,
            )
        )

        self.assertTrue(inspection.checkpoint_found)
        self.assertEqual(plan.checkpoint_id, checkpoint.checkpoint_id)
        self.assertGreater(len(requirements.context_requirements), 0)
        self.assertIn("identity_anchor", [req.required_type for req in requirements.context_requirements])

    def test_no_prompt_restoration_or_old_context_dependency(self) -> None:
        reconstructor = ContextReconstructor()
        adapter = ContextContinuityAdapter()
        hook = RuntimeContinuityHook()
        for obj in (reconstructor, adapter, hook):
            for forbidden in (
                "restore_prompt",
                "old_context_window",
                "load_old_context",
                "inject_prompt",
                "call_llm",
                "generate",
            ):
                self.assertFalse(hasattr(obj, forbidden), f"{obj!r} exposes {forbidden}")

    def test_full_recovery_trace_is_complete(self) -> None:
        checkpoint = self._identity_checkpoint()
        hook = RuntimeContinuityHook(checkpoint_lookup=lambda _agent_id: checkpoint)
        inspection = hook.check_state(event=ContinuityEvent.RUNTIME_RECOVERY)
        recovery_decision = RecoveryTrigger().evaluate(
            RecoveryTriggerInput(
                event=ContinuityEvent.RUNTIME_RECOVERY,
                checkpoint_available=inspection.checkpoint_found,
            )
        )
        plan = create_recovery_plan(checkpoint, recovery_reason="compact")
        context_result = ContextReconstructor().reconstruct(
            checkpoint,
            plan,
            ContextReconstructionRequest(
                agent_id="julia",
                recovery_plan_id=plan.recovery_plan_id,
                checkpoint_id=checkpoint.checkpoint_id,
                current_intent="trace_verification",
            ),
        )
        trace = ContinuityTracePipeline().build_trace(
            runtime=RuntimeTraceContext(
                runtime_id="julia-runtime",
                session_id="new-session-after-compact",
                event=ContinuityEvent.RUNTIME_RECOVERY,
            ),
            continuity={
                **inspection.to_trace(),
                "recovery_status": recovery_decision.recovery_status,
            },
        ).to_dict()

        checks = {
            "identity_preserved": bool(checkpoint.identity_refs),
            "checkpoint_restored": inspection.checkpoint_found,
            "session_loss_tolerated": trace["runtime"]["session_id"] == "new-session-after-compact",
            "context_rebuilt": context_result.continuity_restored,
            "provider_independent": checkpoint.integrity.get("provider_independent") is True,
            "no_prompt_dependency": "prompt" not in str(trace).lower(),
            "trace_complete": trace["trace_version"] == "1.1" and bool(trace["authority_chain"]),
        }

        self.assertEqual(trace["continuity"]["checkpoint_id"], checkpoint.checkpoint_id)
        self.assertEqual(trace["continuity"]["decision_level"], "L3_IDENTITY")
        self.assertEqual(trace["continuity"]["recovery_status"], "RECOVERY_REQUIRED")
        for name, passed in checks.items():
            self.assertTrue(passed, name)


if __name__ == "__main__":
    unittest.main()
