# FRA-E2B1: RECOVERY BASELINE RECONSTRUCTION MATRIX
**Date: 2026-08-11 | Mode: READ ONLY**

## RECOVERY AUTHORITY MATRIX

| COMPONENT | RUNBOOK CLAIM | CURRENT AUTODL DISK | HISTORICAL GOLDEN | MATCH? | AUTHORITY |
|-----------|--------------|--------------------|-------------------|--------|-----------|
| Python | NOT SPECIFIED | 3.10.8 | 3.10.8 | ✅ | HISTORICAL GOLDEN |
| torch | NOT SPECIFIED | 2.5.0+cu121 | **2.13.0+cu130** | ❌ DOWNGRADED | GOLDEN = 2.13.0 |
| torchaudio | NOT SPECIFIED | 2.5.0+cu121 | **2.11.0** | ❌ DOWNGRADED | GOLDEN = 2.11.0 |
| transformers | NOT SPECIFIED | 4.57.3 | 4.57.3 | ✅ | GOLDEN = 4.57.3 |
| faster-whisper | NOT SPECIFIED | 1.2.1 | 1.2.1 | ✅ | GOLDEN |
| CTranslate2 | NOT SPECIFIED | 4.8.1 | 4.8.1 | ✅ | GOLDEN |
| speech-to-speech | 0.2.12 | 0.2.12 | 0.2.12 | ✅ | GOLDEN |
| qwen-tts | NOT SPECIFIED | 0.1.1 | 0.1.1 | ✅ | GOLDEN |
| faster-qwen3-tts | NOT SPECIFIED | 0.3.2 | 0.3.2 | ✅ | GOLDEN |
| VAD thresh | 0.6 | 0.6 | 0.6 | ✅ | GOLDEN |
| VAD min_silence | **800ms** | **800ms** | **1200ms** | ❌ MISMATCH | GOLDEN = 1200 |
| launch_s2s.py | APPROVED | present | best candidate | 🟡 | NOT RE-ATTESTED |
| start_frontend.sh | APPROVED | present | present | 🟡 | NOT RE-ATTESTED |
| main.js | GOLDEN READ-ONLY | unknown version | hash in attestation | ❌ | MISMATCH |
| voice-workspace.js | NOT SPECIFIED | **0 BYTES** | non-empty | ❌ | CORRUPTED |
| chat.js | GOLDEN READ-ONLY | unknown version | hash in attestation | ❌ | MISMATCH |
| Brain endpoint | frozen-865ffc4 | /v1/chat/completions | E2-A: live code ≠ frozen | ❌ | STALE |
| Electron version | 8fa1f36 | 12fd0fb + dirty | lineage diverged | ❌ | STALE |

## KEY FINDINGS

### F001: torch/torchaudio DOWNGRADED from Golden
```
Golden baseline (golden-baseline.json, 2026-08-08):
  torch:      2.13.0+cu130
  torchaudio: 2.11.0

Current AutoDL disk:
  torch:      2.5.0+cu121  ← DOWNGRADED on 2026-08-10 recovery
  torchaudio: 2.5.0+cu121  ← DOWNGRADED

requirements.freeze.txt ALSO confirms torch 2.13.0 as frozen.

The 2026-08-10 "recovery" that downgraded torch was a WORKAROUND
for libcudart.so.13 not being in LD_LIBRARY_PATH — not a fix.
```

### F002: VAD min_silence DISCREPANCY
```
Golden baseline:  1200ms
launch_s2s.py:    800ms
Runbook §3:       800ms (declared canonical)

Runbook declares 800 as canonical; Golden baseline declares 1200.
Historical rollback reference in runbook §3 also mentions 1200ms.
```

### F003: Frontend files CORRUPTED
```
voice-workspace.js: 0 bytes (empty) — deploy failure
main.js: unknown version, no version markers
chat.js: unknown version
```

## VERDICT

```
RECOVERY AUTHORITY:      NOT ESTABLISHED
RUNBOOK:                 HOLD — DO NOT EXECUTE AS-IS
GOLDEN BASELINE:         PARTIALLY RECOVERABLE from golden-baseline.json
REQUIREMENTS.FREEZE:     AUTHORITATIVE for package versions (torch 2.13.0 era)
CURRENT DISK:            DEGRADED (torch downgrade + frontend corruption)
```
