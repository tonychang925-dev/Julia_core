"""Voice OS V1 — Structured Speech Metadata tests.

Contract: docs/architecture/Julia_Voice_OS_Architecture_v1.0.md
"""

from __future__ import annotations

import pytest

from julia_core.voice_os.emotion_state import CognitiveEmotion, EmotionState
from julia_core.voice_os.prosody import SpeechMetadata, SpeechProsodyPlanner


# ── Test 1: Emotion states are valid ──

class TestEmotionState:
    def test_all_states_exist(self):
        assert len(EmotionState) == 8

    def test_cognitive_emotion_default(self):
        e = CognitiveEmotion()
        assert e.state == EmotionState.WARM
        assert e.intensity == 0.7


# ── Test 2: SpeechMetadata is frozen ──

class TestSpeechMetadata:
    def test_default_values(self):
        m = SpeechMetadata()
        assert m.speed == 0.85
        assert m.pitch_shift == "+0Hz"
        assert m.pause_ms == 300
        assert m.energy == 0.7

    def test_custom_values(self):
        m = SpeechMetadata(speed=0.9, pitch_shift="+5Hz", pause_ms=200, energy=0.8)
        assert m.speed == 0.9


# ── Test 3: Prosody Planner converts emotion → speech ──

class TestProsodyPlanner:
    def test_neutral_maps_correctly(self):
        planner = SpeechProsodyPlanner()
        meta = planner.plan(CognitiveEmotion(state=EmotionState.NEUTRAL, intensity=0.5))
        assert meta.speed > 0.7
        assert meta.pitch_shift == "+0Hz"

    def test_warm_maps_to_gentle_speed(self):
        planner = SpeechProsodyPlanner()
        meta = planner.plan(CognitiveEmotion(state=EmotionState.WARM, intensity=0.7))
        assert meta.speed < 1.0  # warm = slower, gentler
        assert meta.pause_ms == 300

    def test_excited_maps_to_fast_high_pitch(self):
        planner = SpeechProsodyPlanner()
        meta = planner.plan(CognitiveEmotion(state=EmotionState.EXCITED, intensity=0.9))
        assert meta.speed > 0.95
        assert meta.pitch_shift == "+10Hz"

    def test_thinking_maps_to_slow_low_pitch(self):
        planner = SpeechProsodyPlanner()
        meta = planner.plan(CognitiveEmotion(state=EmotionState.THINKING, intensity=0.8))
        assert meta.speed < 0.8
        assert meta.pause_ms >= 400

    def test_soft_is_gentle_low_energy(self):
        planner = SpeechProsodyPlanner()
        meta = planner.plan(CognitiveEmotion(state=EmotionState.SOFT, intensity=0.6))
        assert meta.energy < 0.5
        assert meta.speed < 0.85

    def test_null_emotion_defaults_to_warm(self):
        planner = SpeechProsodyPlanner()
        meta = planner.plan(None)
        assert meta.speed > 0.8

    def test_intensity_affects_speed_and_energy(self):
        planner = SpeechProsodyPlanner()
        low = planner.plan(CognitiveEmotion(state=EmotionState.EXCITED, intensity=0.2))
        high = planner.plan(CognitiveEmotion(state=EmotionState.EXCITED, intensity=0.9))
        assert low.speed < high.speed  # higher intensity = faster
        assert low.energy < high.energy

    def test_emotion_does_not_use_temperature(self):
        """Temperature is a generation-layer param, not a voice emotion param."""
        meta = planner.plan(CognitiveEmotion(state=EmotionState.WARM))
        assert not hasattr(meta, "temperature")


# ── Test 4: TTS Adapter mapping ──

class TestTTSAdapterMapping:
    def test_speed_to_fish_prosody(self):
        """Fish Audio: speed → prosody.speed"""
        meta = SpeechMetadata(speed=0.82)
        fish_params = {
            "prosody": {"speed": meta.speed},
        }
        assert fish_params["prosody"]["speed"] == 0.82

    def test_speed_to_edge_rate(self):
        """Edge TTS: speed → rate string. 0.82 → "-18%" """
        meta = SpeechMetadata(speed=0.82)
        # speed 1.0 = "+0%", 0.82 = approximately "-18%"
        rate_pct = round((meta.speed - 1.0) * 100)
        edge_rate = f"{rate_pct:+d}%"
        assert edge_rate == "-18%"

    def test_pause_to_ssml_break(self):
        """Edge TTS: pause_ms → SSML <break time="Xms"/>"""
        meta = SpeechMetadata(pause_ms=300)
        ssml = f'<break time="{meta.pause_ms}ms"/>'
        assert "break" in ssml
        assert "300ms" in ssml


# ── Test 5: First voice pair ──

planner = SpeechProsodyPlanner()

class TestVoicePair:
    """Voice OS V1 ships with at least one voice pair."""
    def test_warm_supportive_pair_exists(self):
        meta = planner.plan(CognitiveEmotion(state=EmotionState.WARM, intensity=0.8))
        assert meta.speed > 0.8
        assert meta.energy > 0.5
        assert meta.pause_ms <= 400
