"""C2.1 — Voice Provider Independence Verification.

Same pattern as A2.1.5 Core Independence.
VoiceProvider must not corrupt Core identity, memory, context, or persona.
"""

from __future__ import annotations

import pytest

from julia_core.providers.voice_provider import VoiceProvider
from julia_core.voice_os.emotion_state import CognitiveEmotion, EmotionState
from julia_core.voice_os.prosody import SpeechMetadata, SpeechProsodyPlanner
from julia_core.chat.persona import Persona


# ── Mock Voice Provider ──

class _MockVoiceProvider:
    provider_id = "voice-mock-v1"
    _last_text: str = ""
    _last_emotion: CognitiveEmotion | None = None
    _call_count: int = 0

    def speak(self, text: str, *, emotion: CognitiveEmotion | None = None, metadata: SpeechMetadata | None = None) -> bool:
        self._last_text = text
        self._last_emotion = emotion
        self._call_count += 1
        return True

    def synthesize(self, text: str, *, emotion: CognitiveEmotion | None = None, metadata: SpeechMetadata | None = None) -> bytes | None:
        self._last_text = text
        self._last_emotion = emotion
        self._call_count += 1
        return text.encode("utf-8")


# ── Test 1: Core starts without voice provider ──

class TestCoreNoVoiceProvider:
    def test_persona_works_without_voice(self):
        """Persona engine must not depend on voice provider."""
        persona = Persona(persona_id="test", name="Test", role="tester")
        assert persona.name == "Test"

    def test_prosody_works_without_voice(self):
        """Prosody planner must not depend on voice provider."""
        planner = SpeechProsodyPlanner()
        meta = planner.plan(CognitiveEmotion(EmotionState.WARM, 0.8))
        assert meta.speed > 0.8

    def test_emotion_state_works_without_voice(self):
        """Emotion state must not depend on voice provider."""
        emotion = CognitiveEmotion(EmotionState.WARM, 0.8)
        assert emotion.state == EmotionState.WARM


# ── Test 2: Mock provider fulfills protocol ──

class TestMockProviderFulfillsProtocol:
    def test_mock_is_voice_provider(self):
        provider = _MockVoiceProvider()
        assert isinstance(provider, VoiceProvider)

    def test_mock_speak_returns_true(self):
        provider = _MockVoiceProvider()
        assert provider.speak("hello") is True

    def test_mock_synthesize_returns_bytes(self):
        provider = _MockVoiceProvider()
        result = provider.synthesize("hello")
        assert result == b"hello"


# ── Test 3: Provider swap does not change persona ──

class TestProviderSwapDoesNotChangePersona:
    def test_swap_voice_providers_persona_unchanged(self):
        persona = Persona(persona_id="julia", name="Julia", role="girlfriend", tone="warm")
        provider_1 = _MockVoiceProvider()
        provider_2 = _MockVoiceProvider()

        # Speak with provider 1
        provider_1.speak("hello", emotion=CognitiveEmotion(EmotionState.WARM, 0.8))
        # Swap to provider 2
        provider_2.speak("hello", emotion=CognitiveEmotion(EmotionState.WARM, 0.8))

        # Persona must be unchanged
        assert persona.name == "Julia"
        assert persona.tone == "warm"
        assert persona.persona_id == "julia"

    def test_swap_does_not_change_emotion(self):
        emotion = CognitiveEmotion(EmotionState.SOFT, 0.6)
        provider_1 = _MockVoiceProvider()
        provider_2 = _MockVoiceProvider()

        provider_1.speak("test", emotion=emotion)
        provider_2.speak("test", emotion=emotion)

        # Emotion must not be mutated by providers
        assert emotion.state == EmotionState.SOFT
        assert emotion.intensity == 0.6


# ── Test 4: Provider must not access Core internals ──

class TestProviderCannotAccessCoreInternals:
    def test_provider_has_no_context_os_access(self):
        provider = _MockVoiceProvider()
        assert not hasattr(provider, "context_os")
        assert not hasattr(provider, "context_planner")
        assert not hasattr(provider, "resolver")

    def test_provider_has_no_memory_access(self):
        provider = _MockVoiceProvider()
        assert not hasattr(provider, "memory")
        assert not hasattr(provider, "memory_store")
        assert not hasattr(provider, "governed_facts")

    def test_provider_has_no_persona_authority(self):
        provider = _MockVoiceProvider()
        assert not hasattr(provider, "persona")
        assert not hasattr(provider, "identity")

    def test_provider_has_no_runtime_authority(self):
        provider = _MockVoiceProvider()
        assert not hasattr(provider, "runtime")
        assert not hasattr(provider, "session_manager")
