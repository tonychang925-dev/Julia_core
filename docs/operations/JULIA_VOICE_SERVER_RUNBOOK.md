# Julia Voice / Electron Server Operations Runbook

**Status:** Production Operations Baseline
**Baseline:** BASELINE RUNTIME RESTORED
**Last validated:** 2026-08-08
**Purpose:** Julia Voice / Electron V2 runtime startup, recovery, verification, and incident handling.

---

## 1. Operational Principle

This document describes the **known-good runtime**, not a proposed architecture.

When recovering after AutoDL shutdown/restart:

1. Restore the known-good runtime first.
2. Do not redesign, patch, or re-audit already validated architecture unless a real failure occurs.

Operational rule:

```
KNOWN-GOOD FIRST
    ↓
START MISSING SERVICE
    ↓
VERIFY
    ↓
ONLY DEBUG ACTUAL FAILURE
```

Do not turn runtime recovery into architecture investigation.

---

## 2. Frozen Production Topology

```
Mac
│
├─ Julia Brain
│    localhost:18089
│    julia_ai_assistant
│    julia_core @ frozen-865ffc4
│    persona / memory / diary / tools
│    DeepSeek true SSE streaming
│
│   AutoDL reverse SSH tunnel
│   AutoDL:127.0.0.1:8089 → Mac:127.0.0.1:18089
│
└──────────────────────────────────────────────

AutoDL RTX3090
│
├─ HF Speech-to-Speech :8765
│    Silero VAD
│    faster-whisper large-v3 zh
│    Smart Turn
│    Julia Brain via http://127.0.0.1:8089/v1
│    Qwen3-TTS Base
│
├─ Golden HF Web Voice frontend :7860
│
└──────────────────────────────────────────────

Mac local SSH forwards
│
├─ localhost:7860 → AutoDL:7860
└─ localhost:8765 → AutoDL:8765

Safari / Electron V2
        ↓
http://localhost:7860
        ↓
Golden HF Web Voice
        ↓
ws://localhost:8765/v1/realtime
        ↓
S2S → AutoDL :8089 → Mac Julia Brain → DeepSeek → Qwen3-TTS
```

---

## 3. Frozen Voice Baseline

The following parameters are production baseline and **must not be changed** during routine recovery.

| Category | Parameter | Value |
|----------|-----------|-------|
| Mode | | `realtime` |
| **WebSocket** | host | `0.0.0.0` |
| | port | `8765` |
| **STT** | backend | `faster-whisper` |
| | model | `large-v3` |
| | language | `zh` |
| | live transcription | OFF |
| **VAD** | threshold | `0.6` |
| | min_speech_ms | `500` |
| | min_silence_ms | `800` |
| | speech_pad_ms | `300` |
| | short_segment_merge_ms | `800` |
| | speculative_reopen_ms | `2500` |
| **LLM** | backend | `chat-completions` |
| | API | `http://127.0.0.1:8089/v1` |
| | streaming | ON |
| **TTS** | backend | Qwen3-TTS |
| | model | `Qwen/Qwen3-TTS-12Hz-1.7B-Base` |
| | runtime | torch |

**Canonical VAD baseline:** `MIN_SILENCE_MS = 800`
**Historical rollback reference:** `1200ms`

Do not modify either value during recovery.

---

## 4. Frozen Components

### 4.1 Golden Voice

- **Directory:** `/root/julia_voice_v2/golden/`
- **Policy:** GOLDEN = READ-ONLY
- **Exception:** Runtime-generated logs may be written by already-approved launchers.
- **Never** patch Golden source during an operational incident.

### 4.2 Electron V2

- **Repository:** `/Users/admin/julia_electron_v2`
- **Validated baseline commit:** `8fa1f36`
- **Architecture:** `BrowserWindow → http://localhost:7860`
- Electron does NOT own: PCM, audio buffers, VAD, STT, TTS, playback scheduling, media pipeline.
- Electron main / IPC must never transport PCM audio.

### 4.3 Julia Brain

- **Runtime:** `Mac localhost:18089`
- **Health endpoint:** `GET /internal/v1/voice/health`

Expected response:
```json
{
  "status": "ok",
  "contract_version": "1.0.0",
  "julia_core": "frozen-865ffc4"
}
```

**Important:** `/health` is NOT the Julia Brain health endpoint. A 404 from `/health` does not mean Julia Brain is down.

---

## 5. Normal Recovery Order

After AutoDL restart, always restore in this order:

```
R1  Julia Brain transport
        ↓
R2  S2S :8765
        ↓
R3  Golden frontend :7860
        ↓
R4  Safari / Electron smoke
```

Do not start Candidate runtime during baseline recovery.

---

## 6. R0 — Static Preflight

Before starting anything, verify existing state.

**Mac:**
```bash
curl -fsS http://127.0.0.1:18089/internal/v1/voice/health
```

Expected: `status = ok`, `contract_version = 1.0.0`, `julia_core = frozen-865ffc4`

Confirm existing SSH forwarding processes before creating duplicates.
- Do not kill broad SSH process groups.
- Never use: `pkill ssh`

---

## 7. R1 — Julia Brain Reverse Transport

Required topology: `AutoDL localhost:8089 → Mac localhost:18089`

This is currently a documented manual infrastructure step. It is not yet represented by a canonical launcher/service file.

**Typical form:**
```bash
ssh \
  -i ~/.ssh/autodl_ed25519 \
  -o ExitOnForwardFailure=yes \
  -f -N \
  -R 8089:127.0.0.1:18089 \
  -p <AUTODL_SSH_PORT> \
  root@<AUTODL_HOST>
```

**Do not put credentials into this document.**

**Acceptance test from AutoDL:**
```bash
curl -fsS http://127.0.0.1:8089/internal/v1/voice/health
```

Expected:
```json
{"status": "ok", "contract_version": "1.0.0", "julia_core": "frozen-865ffc4"}
```

R1 PASS only after this succeeds.

---

## 8. R2 — Start Golden S2S

**Approved recovery launcher:** `/root/julia_voice_v2/golden/launch_s2s.py`

**Important:** `launch_s2s.py` internally runs `pkill -f speech-to-speech`.

### HARD PRECONDITION
Existing `speech-to-speech` process count = 0

**Preflight:**
```bash
ps aux | grep '[s]peech-to-speech' || true
ss -lntp | grep ':8765' || true
```

Required: `speech-to-speech = none`, `8765 listener = none`

**Launch:**
```bash
nohup /root/miniconda3/bin/python \
  /root/julia_voice_v2/golden/launch_s2s.py \
  >/tmp/julia-recovery-launch-s2s.log \
  2>&1 </dev/null &
```

Do not repeatedly launch it because 8765 does not immediately appear. Model initialization can take several minutes.

---

## 9. S2S Startup Observation

**Read-only monitoring:**
```bash
ps aux | grep '[s]peech-to-speech'
nvidia-smi
ss -lntp | grep ':8765' || true
tail -100 /root/julia_voice_v2/golden/logs/s2s.log
```

**Known startup sequence observed in production:**

```
S2S process starts
        ↓
Smart Turn initialization
        ↓
LLM warmup
        ↓
Julia Brain :8089 responds 200
        ↓
Qwen3-TTS initialization
        ↓
Tokenizer / model loading
        ↓
GPU model loading
        ↓
:8765 LISTEN
```

A quiet log during early Smart Turn/model initialization does not automatically mean failure.

**Do not restart** solely because: process alive + 8765 not listening yet.

**Actual R2 readiness criterion:** `:8765 LISTEN`

---

## 10. R3 — Start Golden Frontend

**Launcher:** `/root/julia_voice_v2/golden/start_frontend.sh`

**Launch:**
```bash
nohup /root/julia_voice_v2/golden/start_frontend.sh \
  >/tmp/julia-recovery-frontend.log \
  2>&1 </dev/null &
```

**Expected:** frontend :7860, S2S URL: `ws://localhost:8765/v1/realtime`

**Verify:**
```bash
ss -lntp | grep ':7860'
```

Expected: `7860 LISTEN`

---

## 11. Mac Local Forwarding

Required local forwarding:
- `Mac localhost:7860 → AutoDL localhost:7860`
- `Mac localhost:8765 → AutoDL localhost:8765`

Candidate runtime may additionally use `localhost:7861` but 7861 is NOT part of baseline recovery.

Do not rebuild working tunnels unnecessarily.

---

## 12. R4 — Baseline Smoke

### Safari Control

Open `http://localhost:7860`

Verify:
- microphone PASS
- STT PASS
- Julia response PASS
- TTS PASS

Julia-specific persona / memory response is strong evidence that the real chain is active (S2S → AutoDL :8089 → Mac Julia Brain → DeepSeek) and not a baseline mock.

### Electron V2

```bash
cd /Users/admin/julia_electron_v2
npm run start:http
```

Minimal smoke:
- Mic PASS
- STT PASS
- Julia reply PASS
- TTS PASS
- barge-in PASS

Do not repeat full historical Electron validation during ordinary recovery.

Electron V2 has already passed: E0 Chromium compatibility, 5-turn smoke, 20-turn regression, barge-in. Recovery needs only a smoke test.

---

## 13. Recovery Success Definition

Recovery is complete when:

| Gate | Status |
|------|--------|
| R1 Brain transport | PASS |
| R2 S2S :8765 | PASS |
| R3 frontend :7860 | PASS |
| R4 Electron Golden smoke | PASS |

**Official state:** `BASELINE RUNTIME RESTORED`

At that moment: **STOP RECOVERY WORK.** Do not immediately mix Candidate experiments into the recovery session.

---

## 14. Current Validated Production Chain

```
Electron V2
→ http://localhost:7860
→ Golden HF Web Voice
→ S2S :8765
→ AutoDL :8089
→ Mac Julia Voice / Julia Brain
→ DeepSeek
→ Qwen3-TTS
```

Validated with real Julia persona/memory behavior.

---

## 15. Incident Rule — Failure-Driven Debugging

Do not debug components that have already passed.

Example: If Safari Voice PASS, Julia persona PASS, TTS PASS — then do NOT investigate Julia Brain, R1, S2S, or TTS unless new evidence specifically points there.

Debug only the first failing boundary.

```
FIRST FAILED BOUNDARY → DIAGNOSE THAT BOUNDARY ONLY
```

---

## 16. SSH / DNS Incident Lesson

2026-08-08 recovery encountered unstable hostname resolution when creating new SSH sessions.

**Observed:** System DNS, Cloudflare, and Google all resolved the hostname — but some new `ssh` invocations failed with "Could not resolve hostname." Existing R1 TCP connection remained alive.

**Lesson:** Existing established SSH tunnel does not require repeated DNS resolution. Do not destroy a healthy existing tunnel because creation of a new SSH session fails.

Temporary IP transport may be considered only with explicit Gate and verified server identity. Do not permanently hardcode a dynamic AutoDL IP into `/etc/hosts`, scripts, Golden, or application configuration. Canonical identity remains the AutoDL hostname.

---

## 17. Host Key Policy

- Never casually bypass server identity checks during normal operation.
- Do not automatically change: `known_hosts`, `HostKeyAlias`, SSH trust configuration.
- If host identity changes unexpectedly: **STOP. VERIFY.**
- Do not "fix" a host-key mismatch by deleting the old key without first establishing why it changed.

---

## 18. Golden Log Preservation

`launch_s2s.py` opens `/root/julia_voice_v2/golden/logs/s2s.log` in truncate/write mode.

Therefore, when an old S2S log is being used as incident evidence, **preserve it before launching S2S.**

Evidence should be stored outside Golden:
```
/root/julia_voice_v2/evidence/<incident>/
```

Verify preservation using `SHA256` / `cmp`. Never modify Golden merely to preserve evidence.

---

## 19. Secrets Policy

Never store in Git, documentation, terminal transcripts committed to Git, logs, or screenshots intended for publication:

- password
- API key
- SSH private key
- access token
- cookie
- credential

During the 2026-08-08 incident an AutoDL credential appeared in terminal/chat output.

**Operational action:** ROTATE THAT CREDENTIAL after runtime recovery. Do not reuse the exposed password as a documented automation credential. Prefer SSH key authentication.

---

## 20. Hard Operational Prohibitions

During routine recovery:

- ❌ modify Golden source
- ❌ modify VAD parameters
- ❌ change STT
- ❌ change TTS
- ❌ change S2S behavior
- ❌ patch Julia Brain
- ❌ patch Electron
- ❌ start Candidate :7861
- ❌ run M2.4 experiments
- ❌ broad `pkill`
- ❌ git changes
- ❌ architecture redesign

Recovery is **service restoration only.**

---

## 21. Git Safety Gate

Before any future `git add`, `git commit`, `git push`:

1. `git status --short`
2. `git diff`
3. `git diff --cached`
4. List exact planned files / contents
5. Explicit review / GO

Never: `git add .`

---

## 22. Candidate Runtime Is Separate

Candidate `:7861` — M2.4-LC Candidate Runtime Proof is NOT part of baseline recovery.

| | Control | Experiment |
|---|---|---|
| Electron → | Golden :7860 | Candidate :7861 |
| S2S | same | same |
| Julia Brain | same | same |

Only variable: Golden frontend JS vs Candidate lifecycle JS.

Do not begin RP-0 ~ RP-6 until a separate Candidate Runtime Proof Gate is explicitly opened.

---

## 23. Five-Minute Operator Checklist

After AutoDL reboot:

- [ ] Mac Julia Brain :18089 healthy
- [ ] R1 reverse tunnel restored
- [ ] AutoDL :8089 → Julia health PASS
- [ ] Confirm S2S process count = 0
- [ ] Start `launch_s2s.py`
- [ ] Wait for :8765 LISTEN
- [ ] Start `start_frontend.sh`
- [ ] Confirm :7860 LISTEN
- [ ] Safari `http://localhost:7860` smoke
- [ ] Electron `npm run start:http` smoke
- [ ] Julia persona / STT / TTS confirmed
- [ ] **BASELINE RUNTIME RESTORED**

If all boxes pass: **STOP.** Do not investigate further.

---

## 24. Golden Recovery Philosophy

The system has already been validated.

The default assumption after infrastructure restart should be:

```
SERVICES NEED RESTORATION
```

not:

```
ARCHITECTURE NEEDS REVALIDATION
```

Only actual runtime evidence can promote a component from `KNOWN GOOD` to `SUSPECT`.

This principle exists specifically to prevent another recovery session from turning a simple service restart into a full-system archaeological investigation.
