"""Julia Voice Daemon v4.1.1 — Embodied Runtime.

Architecture:
  Mac mic → VAD → Wake Word → STT (GPU Whisper) → WebSocket → Julia Runtime → TTS → Speaker

This daemon is a THIN CLIENT. It does not reason.
It converts physical world audio into events, and events into audio.
All understanding happens in the Julia Runtime (:9000).

Components:
  audio/     — microphone capture, audio streaming
  wakeword/  — wake word detection ("婉婉")
  vad/       — voice activity detection (Silero VAD)
  stt/       — speech-to-text (GPU Whisper server)
  tts/       — text-to-speech (ElevenLabs)
  transport/ — WebSocket client to Julia Runtime
  presence/  — Julia state management (sleeping/idle/listening/thinking/speaking/away)

Usage:
  python -m voice_daemon.main
"""
