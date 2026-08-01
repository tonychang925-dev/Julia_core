#!/usr/bin/env python3
"""Julia Core CLI — generic chat debugging tool.

Usage:
    python3 scripts/core_cli.py "Hello"                  # One-shot text
    python3 scripts/core_cli.py -i                       # Interactive
    python3 scripts/core_cli.py "你好" --tts             # With voice output
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DEFAULT_API = os.environ.get("CORE_API_URL", "http://127.0.0.1:8001/chat")
EDGE_TTS = os.environ.get("EDGE_TTS", "/Users/admin/Desktop/tmp/el_speak_edge.py")


def speak(text: str) -> None:
    """Free Edge TTS, no quota."""
    if not os.path.exists(EDGE_TTS):
        return
    subprocess.run(["python3", EDGE_TTS, text],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)


def chat(api_url: str, text: str) -> dict:
    """Send text to Core Chat endpoint."""
    data = json.dumps({"text": text}).encode()
    req = urllib.request.Request(api_url, data=data)
    req.add_header("Content-Type", "application/json")
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e), "reply": "", "intent": "?"}


def print_response(resp: dict) -> None:
    err = resp.get("error", "")
    if err:
        print(f"❌ {err}")
        return
    reply = resp.get("reply", resp.get("text", ""))
    intent = resp.get("intent", "?")
    print(f"🤖 [{intent}] {reply}")
    print()


def interactive(api_url: str, use_tts: bool) -> None:
    print("Julia Core CLI — /exit to quit.\n")
    while True:
        try:
            line = input("📤 > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break
        if not line:
            continue
        if line.lower() in ("/exit", "/quit"):
            print("Bye!")
            break
        resp = chat(api_url, line)
        print_response(resp)
        if use_tts and resp.get("reply"):
            speak(resp["reply"])


def main() -> int:
    ap = argparse.ArgumentParser(description="Julia Core CLI")
    ap.add_argument("text", nargs="*", help="One-shot query")
    ap.add_argument("--url", default=DEFAULT_API, help="Core chat endpoint")
    ap.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    ap.add_argument("--tts", action="store_true", help="Enable Edge TTS output")
    args = ap.parse_args()

    text = " ".join(args.text).strip() if args.text else ""

    if args.interactive or not text:
        interactive(args.url, args.tts)
    else:
        resp = chat(args.url, text)
        print_response(resp)
        if args.tts and resp.get("reply"):
            speak(resp["reply"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
