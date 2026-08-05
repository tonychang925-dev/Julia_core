#!/usr/bin/env python3
"""Minimal GPU voice loop — uses existing working components.

sounddevice → GPU Whisper → Event Gateway → LLM → EdgeTTS → speaker
"""

import asyncio, sys, threading, time
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, "/Users/admin/julia_ai_assistant")

import sounddevice as sd
from voice_daemon.stt.whisper_client import WhisperClient


async def main():
    # 1. STT — existing GPU Whisper
    whisper = WhisperClient()
    if not whisper.is_available():
        print("❌ GPU Whisper not available at http://localhost:8001")
        return
    print(f"✅ GPU Whisper connected ({whisper.ping()*1000:.0f}ms)")

    # 2. Connect to Event Gateway
    import websockets
    print("Connecting to Event Gateway ws://localhost:9000/ws ...")
    async with websockets.connect("ws://127.0.0.1:9000/ws", proxy=None) as ws:
        # Wait for runtime.started
        raw = await ws.recv()
        print(f"✅ Gateway connected: {raw}")

        import json, io, tempfile, os, subprocess

        SR = 16000
        DURATION = 4  # record 4 seconds after each ENTER

        print("\n🎤 按 Enter 开始录音 (4秒)，说完话等待回复")
        print("   Ctrl+C 退出\n")

        while True:
            try:
                input(">>> 按 Enter 开始说话...")
            except (EOFError, KeyboardInterrupt):
                break

            # Record
            print("   🔴 录音中...")
            audio = sd.rec(int(DURATION * SR), samplerate=SR, channels=1, dtype='float32')
            sd.wait()

            # Convert to int16 WAV bytes for Whisper
            int16 = (audio.flatten() * 32767).astype(np.int16)
            wav = io.BytesIO()
            import wave
            with wave.open(wav, 'wb') as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
                w.writeframes(int16.tobytes())

            # Save temp file for curl
            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            tmp.write(wav.getvalue())
            tmp.close()

            # 3. STT
            t0 = time.time()
            result = whisper.transcribe_file(tmp.name)
            os.unlink(tmp.name)
            text = result.get("text", "").strip()
            if not text:
                print(f"   (未识别到语音)")
                continue
            print(f"   📝 {text} ({((time.time()-t0)*1000):.0f}ms)")

            # 4. Send to Event Gateway → LLM
            from voice_daemon.transport.protocol import voice_final_event, JuliaEvent
            await ws.send(voice_final_event(text).to_json())

            # 5. Wait for reply
            reply = None
            while True:
                raw = await asyncio.wait_for(ws.recv(), timeout=30)
                event = JuliaEvent.from_json(raw)
                if event.type == "assistant.reply":
                    reply = event.data.get("text", "")
                    break
                if event.type == "tts.speak":
                    # TTS payload is in the next event
                    pass

            if not reply:
                print("   (无回复)")
                continue

            print(f"   💬 {reply[:120]}...")

            # 6. TTS — EdgeTTS (existing Julia Core)
            try:
                import edge_tts
                communicate = edge_tts.Communicate(reply, "zh-CN-XiaoxiaoNeural")
                mp3_path = f"/tmp/julia_tts_{int(time.time())}.mp3"
                await communicate.save(mp3_path)
                subprocess.run(["afplay", mp3_path], timeout=30)
                os.unlink(mp3_path)
            except ImportError:
                print("   ⚠️ edge_tts not installed, skipping TTS")
                # Use existing Julia Core TTS via HTTP
                import urllib.request
                body = json.dumps({"text": reply}).encode()
                req = urllib.request.Request("http://localhost:8002/api/voice/synthesize",
                    data=body, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=30) as resp:
                    audio_data = resp.read()
                tmp2 = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
                tmp2.write(audio_data); tmp2.close()
                subprocess.run(["afplay", tmp2.name], timeout=30)
                os.unlink(tmp2.name)

asyncio.run(main())
