# Julia Avatar Lip-Sync (Wav2Lip) Runbook

**Status:** Validated Engineering Baseline
**Last validated:** 2026-08-14
**Purpose:** Wav2Lip lip-sync correction — root cause, frozen parameters, offline inference procedure, LiveTalking realtime alignment, asset inventory, and remote-preview findings.

---

## 1. Summary

Julia's avatar mouth motion was distorted (closed mouth and open mouth rendered simultaneously). Root cause was the base clip composition, not the model. This document freezes the corrected parameters and records the offline verification procedure.

**Outcome:** Lip-sync now correct — verified offline with real TTS audio, and the LiveTalking realtime path uses identical parameters.

---

## 2. Root Cause — Mouth Distortion

| Symptom | Root cause | Fix |
|---------|-----------|-----|
| Closed + open mouth shown together | Base clip was a close-up (face ≈ 2/3 of frame) at 16 fps → Wav2Lip mouth-crop region misaligned | Half-body base (face ≈ 1/3 of frame) + 25 fps + 704×896 |
| Mouth never moves (silent clip) | `inference_silence.py` forced `mel_batch = np.zeros` | `inference_audio.py` extracts real mel from audio |

**Why:** Wav2Lip needs the face to occupy roughly 1/3 of frame height for correct mouth-crop. A close-up makes the mouth crop land in the wrong place.

---

## 3. Frozen Lip-Sync Parameters

These are the validated baseline. Do not change during routine work.

| Category | Parameter | Value |
|----------|-----------|-------|
| Base clip composition | | half-body, face ≈ 1/3 frame |
| Resolution | width × height | 704 × 896 (vertical) |
| FPS | | 25 |
| Wav2Lip | img_size | 256 |
| | mel | 80-dim, step 16 |
| | mel idx multiplier | 80 / fps |
| Portrait source | | ChatGPT FaceTime images (NOT V4 LoRA output) |

---

## 4. Portrait Source (Important)

Use the ChatGPT FaceTime portraits. Do **not** use V4 face-LoRA generated images — the face does not match Julia.

- `julia_idle_phase0_frame.png`
- `julia_speaking_base_frame.png`
- `julia_facetime_source.png`

---

## 5. Offline Inference

Script: `avatars/wav2lip/inference_audio.py` (local backup at `~/Desktop/julia_lora_training/inference_audio.py`).

**Must run from the LiveTalking repo root** because `face_detection/api.py` hardcodes `avatars.wav2lip.face_detection...` imports:

```bash
cd /root/livetalking/LiveTalking
python -m avatars.wav2lip.inference_audio \
  --checkpoint_path ./models/wav2lip.pth \
  --face ./data/tmp/julia_av_idle_25fps.mp4 \
  --audio <tts_audio.wav> \
  --outfile <output.mp4>
```

Do **not** `cd avatars/wav2lip` and run directly — the `avatars` top-level import fails.

---

## 6. LiveTalking Realtime Alignment

Realtime avatar `wav2lip256_julia_v2` is parameter-aligned with offline:

| Field | Value |
|-------|-------|
| face_imgs | 256 × 256 |
| full_imgs | 704 × 896 |
| coords (face bbox) | face ≈ 1/3 of frame |
| mel | 80-dim, step 16 |

`wav2lip_avatar.py` inference path and the offline script therefore produce equivalent mouth motion.

---

## 7. Asset Inventory

Downloaded to `~/Desktop/julia_avatar_assets/` (2026-08-14):

```
julia_avatar_assets/
├── videos/
│   ├── julia_av_idle_25fps.mp4     ← idle.mp4 base (704×896, 25fps, 5s)
│   ├── julia_av_listen_25fps.mp4
│   └── julia_av_speak_25fps.mp4
├── source_images/                  ← ChatGPT FaceTime portraits (3)
└── wav2lip256_julia_v2.tar.gz      ← avatar data (face_imgs + full_imgs + coords.pkl, 93MB)
```

For a local LiveTalking deploy, extract the tarball into `data/avatars/` and use `--avatar_id wav2lip256_julia_v2` (skips avatar re-generation).

---

## 8. GPU Requirement

Wav2Lip realtime requires **NVIDIA CUDA**. It will not run in realtime on CPU, Intel iGPU, or macOS (no CUDA; MPS incompatible with face_detection dependencies).

- Model: 53M params, ~2-4 GB VRAM at 256 resolution.
- Entry-level NVIDIA dGPU (GTX 1060 6G / RTX 2060 / RTX 3050 4G+) is sufficient.

---

## 9. Remote Preview Findings

Local machine has no NVIDIA GPU, so LiveTalking stays on the GPU server. Remote preview via SSH tunnel fails because WebRTC media is UDP and SSH `-L` forwards TCP only.

| Approach | Result |
|----------|--------|
| Tailscale | Blocked — AutoDL container lacks NET_ADMIN (`CapEff` bit12 = 0); standard TUN `operation not permitted`; userspace-networking starts but no real interface, so WebRTC ICE gets no tailnet IP |
| SRS + rtcpush + HTTP-FLV | **Planned** — pure TCP, SSH-tunnel-friendly, 1-3s latency. LiveTalking → local SRS over localhost (UDP fine), browser pulls HTTP-FLV over TCP |

**Decision (2026-08-14):** Do not build the SRS remote-preview link now. Revisit when Electron integration is done.

---

## 10. Pending — Electron Integration

When Electron integration is complete, wire the realtime lip-sync path:

1. Serve LiveTalking output through SRS `rtcpush` → HTTP-FLV (pure TCP).
2. SSH-tunnel the SRS HTTP-FLV port to the Mac.
3. Electron/浏览器 pulls the stream via flv.js.

Revisit the frozen parameters in section 3 if the base clip is regenerated.

---

## 11. Hard Constraints

- ❌ Do not use close-up base clips (face > 1/3 frame).
- ❌ Do not use V4 face-LoRA images as portrait source.
- ❌ Do not force `mel_batch = np.zeros` in offline inference.
- ❌ Do not run offline inference outside the LiveTalking repo root.
- ❌ Do not assume Tailscale works on AutoDL (no NET_ADMIN).
- ❌ Do not store credentials in this document (see Secrets Policy).
