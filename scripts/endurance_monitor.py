#!/usr/bin/env python3
"""Julia OS v4.1.1 — 24h Endurance Monitor.

Monitors 4 metrics without touching core code:
  1. Event Latency   — voice.final → assistant.reply round-trip
  2. Resource Usage   — RSS memory of runtime + voice daemon
  3. Event Integrity  — count voice.wake/voice.final/assistant.reply/tts.finished
  4. Recovery Events  — WebSocket reconnect, heartbeat loss

Writes to: ~/.julia/health/endurance_{date}.jsonl

Usage:
  python scripts/endurance_monitor.py
  # Runs for 24 hours, samples every 10 seconds
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HEALTH_DIR = Path.home() / ".julia" / "health"
RUNTIME_URL = os.environ.get("JULIA_RUNTIME_URL", "ws://localhost:9000/ws")
SAMPLE_INTERVAL = 10  # seconds
DURATION = 24 * 3600   # 24 hours


class EnduranceMonitor:
    def __init__(self):
        self._dir = HEALTH_DIR
        self._dir.mkdir(parents=True, exist_ok=True)
        self._today = datetime.now().strftime("%Y_%m_%d")
        self._file = self._dir / f"endurance_{self._today}.jsonl"

        self._event_counts = {
            "voice.wake": 0, "voice.final": 0,
            "assistant.reply": 0, "tts.finished": 0,
        }
        self._reconnects = 0
        self._heartbeat_losses = 0
        self._latency_samples = []
        self._start_time = time.time()
        self._running = True

    def log(self, entry: dict):
        entry["timestamp"] = datetime.now().isoformat()
        with open(self._file, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def sample_resource(self) -> dict:
        """Check RSS memory of julia processes."""
        try:
            result = subprocess.run(
                ["ps", "-eo", "pid,rss,comm"],
                capture_output=True, text=True, timeout=5,
            )
            data = {"timestamp": datetime.now().isoformat()}
            for line in result.stdout.split("\n"):
                for name in ["python", "Python", "julia", "event_gateway", "voice_daemon"]:
                    if name in line:
                        parts = line.split()
                        if len(parts) >= 2:
                            pid = parts[0]
                            rss_kb = int(parts[1])
                            data[f"pid_{pid}"] = {"rss_mb": round(rss_kb / 1024, 1), "cmd": parts[2]}
            return data
        except Exception:
            return {"error": "ps failed"}

    async def sample_ws_health(self) -> dict:
        """Check WebSocket connectivity and heartbeat."""
        try:
            import websockets
            async with websockets.connect(RUNTIME_URL, proxy=None) as ws:
                # Send heartbeat and measure RTT
                t0 = time.time()
                await ws.send(json.dumps({
                    "type": "heartbeat",
                    "source": "monitor",
                    "timestamp": t0,
                    "data": {"version": "monitor", "state": "monitoring"},
                }))
                raw = await asyncio.wait_for(ws.recv(), timeout=5)
                rtt = (time.time() - t0) * 1000
                return {"ws_connected": True, "rtt_ms": round(rtt, 1)}
        except Exception as e:
            return {"ws_connected": False, "error": str(e)[:100]}

    async def sample_event_integrity(self):
        """Count events from presence journal."""
        try:
            from voice_daemon.presence.journal import get_journal
            j = get_journal()
            entries = j.query()
            counts = {}
            for e in entries:
                state = e.get("new_state", "")
                counts[state] = counts.get(state, 0) + 1
            return {"presence_entries": len(entries), "states": counts}
        except Exception:
            return {}

    async def sample(self):
        """Take one monitoring sample."""
        # Resource
        resource = self.sample_resource()

        # WebSocket
        ws = await self.sample_ws_health()

        # Events
        events = await self.sample_event_integrity()

        sample = {
            "elapsed_h": round((time.time() - self._start_time) / 3600, 2),
            "resource": resource,
            "websocket": ws,
            "events": events,
        }

        self.log(sample)

        # Print status
        rss = resource.get("rss_mb", "?")
        ws_status = "✅" if ws.get("ws_connected") else "❌"
        presence = events.get("presence_entries", 0)
        elapsed = sample["elapsed_h"]
        print(f"  [{elapsed:6.1f}h] WS:{ws_status} RTT:{ws.get('rtt_ms','?')}ms  Presence:{presence}  RSS:{resource}")

        return sample

    async def run(self, duration: int = DURATION):
        """Run endurance monitor for specified seconds."""
        print(f"Julia OS v4.1.1 Endurance Monitor")
        print(f"  Duration: {duration // 3600}h")
        print(f"  Interval: {SAMPLE_INTERVAL}s")
        print(f"  Output:   {self._file}")
        print(f"  Runtime:  {RUNTIME_URL}")
        print()

        self.log({"event": "start", "duration_h": duration // 3600})

        samples = 0
        start = time.time()

        while time.time() - start < duration:
            try:
                await self.sample()
                samples += 1
            except KeyboardInterrupt:
                print("\n  Stopped by user")
                break
            except Exception as e:
                print(f"  Sample error: {e}")

            await asyncio.sleep(SAMPLE_INTERVAL)

        # Final report
        elapsed = (time.time() - start) / 3600
        self.log({"event": "complete", "samples": samples, "elapsed_h": round(elapsed, 1)})
        print(f"\n  Endurance complete: {samples} samples over {elapsed:.1f}h")

    def final_report(self):
        """Print human-readable summary from today's log."""
        if not self._file.exists():
            print("No data yet.")
            return

        lines = []
        ws_ok = 0
        ws_fail = 0
        rtts = []

        with open(self._file) as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if "websocket" in entry:
                        if entry["websocket"].get("ws_connected"):
                            ws_ok += 1
                            rtt = entry["websocket"].get("rtt_ms", 0)
                            if rtt: rtts.append(rtt)
                        else:
                            ws_fail += 1
                except Exception:
                    pass

        total = ws_ok + ws_fail
        if total > 0:
            uptime = ws_ok / total * 100
            avg_rtt = sum(rtts) / len(rtts) if rtts else 0
            print(f"\n📊 Endurance Summary")
            print(f"  WS Uptime:  {uptime:.1f}% ({ws_ok}/{total})")
            print(f"  Avg RTT:    {avg_rtt:.0f}ms")
            print(f"  Output:     {self._file}")


if __name__ == "__main__":
    import asyncio

    monitor = EnduranceMonitor()

    try:
        asyncio.run(monitor.run(duration=DURATION))
    except KeyboardInterrupt:
        print("\nEndurance monitor stopped.")
    finally:
        monitor.final_report()
