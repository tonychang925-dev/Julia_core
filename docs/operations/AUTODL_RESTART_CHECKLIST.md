# AutoDL Restart Checklist

**10 actions after AutoDL reboot. Do not deviate.**

---

## Preflight

- [ ] 1. Verify Mac Julia Brain healthy
  ```bash
  curl -fsS http://127.0.0.1:18089/internal/v1/voice/health
  ```
  Expect: `status=ok, julia_core=frozen-865ffc4`

## R1 — Reverse Tunnel

- [ ] 2. Restore AutoDL → Mac reverse SSH tunnel
  ```bash
  ssh -i ~/.ssh/autodl_ed25519 -o ExitOnForwardFailure=yes -f -N \
    -R 8089:127.0.0.1:18089 -p <PORT> root@<HOST>
  ```

- [ ] 3. Verify tunnel from AutoDL
  ```bash
  curl -fsS http://127.0.0.1:8089/internal/v1/voice/health
  ```

## R2 — S2S

- [ ] 4. Confirm no existing S2S process
  ```bash
  ps aux | grep '[s]peech-to-speech' || true
  ```

- [ ] 5. Launch S2S
  ```bash
  nohup /root/miniconda3/bin/python /root/julia_voice_v2/golden/launch_s2s.py \
    >/tmp/julia-recovery-launch-s2s.log 2>&1 </dev/null &
  ```

- [ ] 6. Wait for :8765 LISTEN (may take 5-10 min)
  ```bash
  ss -lntp | grep ':8765'
  ```

## R3 — Frontend

- [ ] 7. Launch frontend
  ```bash
  nohup /root/julia_voice_v2/golden/start_frontend.sh \
    >/tmp/julia-recovery-frontend.log 2>&1 </dev/null &
  ```

- [ ] 8. Confirm :7860 LISTEN
  ```bash
  ss -lntp | grep ':7860'
  ```

## R4 — Smoke

- [ ] 9. Safari: open `http://localhost:7860`, verify Mic/STT/Julia/TTS

- [ ] 10. Electron: `cd ~/julia_electron_v2 && npm run start:http`, verify Mic/STT/Julia/TTS/barge-in

---

**All 10 boxes checked → BASELINE RUNTIME RESTORED. STOP.**
