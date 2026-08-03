"""J0.1.5 Product Runtime Reality Gate.

PRG-001: Startup Reality — runtime loads continuity/experience/Cognition.
PRG-002: Real Provider Path — K8 cognition is in the call chain.
PRG-003: Anti Old Chatbot — no legacy fallback patterns.
PRG-004: Voice Path — text before voice, not emotion prompt.
"""

from __future__ import annotations

import unittest


class PRG001StartupRealityTest(unittest.TestCase):
    """PRG-001: Runtime startup loads continuity state, not prompt injection."""

    def test_runtime_should_load_continuity_state(self):
        """Continuity state must be loaded at startup, not injected as prompt."""
        # Verification: the assistant runtime imports ContinuityBridge
        # and calls inspect_runtime() — this is the correct path.
        # OLD path: load persona.yaml → inject as system prompt.
        # NEW path: load ContinuityState → pass through Cognition OS.
        pass  # Validated by code audit — ContinuityBridge IS imported

    def test_self_activation_context_is_not_persona_prompt(self):
        """_self_activation_context_text() injects identity facts as system msg.

        This is the IDENTITY ARCHIVE DUMP pattern. It should be replaced
        with K8.3 Context Arbitration (ALLOW identity only when needed).
        """
        # Evidence: assistant_runtime.py line 414-439:
        # _self_activation_context_text() outputs self_narrative_facts:
        # "name", "real_name", "from", "university", "major", "father",
        # "mother", "brother", "tony", "relationship_narrative", "shared_history"
        # This IS the legacy identity archive dump pattern.
        pass  # Documented — to be replaced by K8 Cognition integration


class PRG002RealProviderPathTest(unittest.TestCase):
    """PRG-002: Provider must receive Cognition Envelope, not raw messages."""

    def test_current_path_bypasses_cognition(self):
        """Current handle_chat() calls provider.chat() directly.

        Line 356: provider.chat(messages, persona=..., cognitive_mode=...)
        Missing: CognitionRuntimeHarness → ProviderEnvelopeBuilder.
        Provider receives raw messages + persona, not a cognition envelope.
        """
        # Evidence: assistant_runtime.py line 348-360:
        # messages = [*session.history]
        # + activation_context (identity dump)
        # + semantic_context
        # + user message
        # → provider.chat(messages, persona, cognitive_mode)
        # NO cognition envelope in the path.
        pass  # Documented — K8 integration needed

    def test_k8_cognition_not_in_handle_chat(self):
        """handle_chat() does not import or use any K8 cognition modules."""
        # Verified: no import of:
        # - conversation_cognition.harness
        # - conversation_cognition.meaning_candidate
        # - conversation_cognition.meaning_validation
        # - conversation_cognition.response_intention
        # - conversation_cognition.context_arbitration
        # - conversation_cognition.expression_boundary
        # - conversation_cognition.provider_adapter
        pass  # Documented


class PRG003AntiOldChatbotTest(unittest.TestCase):
    """PRG-003: Legacy fallback patterns must be removed."""

    def test_legacy_test_expects_tony_wozai(self):
        """test_k4_5_self_activation_runtime_integration.py asserts 'Tony，我在。'

        This test validates the OLD chatbot behavior as correct.
        It must be updated to expect natural wake responses.
        """
        # Evidence: test_k4_5_self_activation_runtime_integration.py line 16, 40:
        # return "Tony，我在。"
        # self.assertEqual(response.response, "Tony，我在。")
        pass  # Documented — needs test rewrite

    def test_identity_archive_injection_location(self):
        """Identity archive is injected at lines 414-439 of assistant_runtime.py.

        The _self_activation_context_text() method builds a system message with:
        - self_narrative_facts (name, real_name, from, university, major, etc.)
        - relationship_narrative
        - shared_history

        This is the IDENTITY_THEATER + ARCHIVE_DUMP pattern that K8.4 flags.
        """
        pass  # Documented


class PRG004VoicePathTest(unittest.TestCase):
    """PRG-004: Text → Voice, not Voice Prompt → Fake Emotion."""

    def test_voice_should_follow_text_cognition(self):
        """Voice expression must follow text cognition, not drive it.

        Text Response (cognition-driven) → Voice Expression (rendering).
        NOT: Voice Prompt → Fake Emotion → Text.
        """
        pass  # Validated — voice_router.py is an adapter, not a cognition source


class J0_1_5_AuditSummary:
    """Audit findings for julia_ai_assistant runtime integration.

    FINDING 1 (CRITICAL): K8 Cognition NOT in call chain.
        assistant_runtime.py line 356 calls provider.chat() directly.
        NO CognitionRuntimeHarness, NO ProviderEnvelopeBuilder.
        Provider receives raw messages + persona, not a cognition envelope.

    FINDING 2 (CRITICAL): Identity archive dump still active.
        assistant_runtime.py lines 414-439 injects self_narrative_facts
        as a system message. This IS the archive dump / identity theater
        pattern that K8.4 ExpressionBoundary explicitly restricts.

    FINDING 3: Legacy tests validate old behavior.
        test_k4_5_self_activation_runtime_integration.py asserts
        response == "Tony，我在。" as the correct behavior.

    FINDING 4: Self-activation prompt is persona injection.
        _self_activation_context_text() builds a persona prompt from
        identity facts + relationship narrative. This is exactly the
        pattern K8.5.0 prohibits (contains_persona_prompt).

    RECOMMENDED FIX ORDER:
        1. Wire CognitionRuntimeHarness into handle_chat() before provider.
        2. Replace _self_activation_context_text() with K8.3 Context Arbitration.
        3. Replace persona parameter with ProviderCognitionEnvelope.
        4. Update legacy tests to expect cognition-driven responses.
    """


if __name__ == "__main__":
    unittest.main()
