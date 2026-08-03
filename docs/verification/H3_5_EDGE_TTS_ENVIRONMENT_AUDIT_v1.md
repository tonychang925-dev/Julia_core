# H3.5 Edge TTS Environment Audit v1

Status: RECORDED
Generated At: 2026-08-02

## Finding

The previous julia_agent repository contains Edge TTS bytecode cache artifacts, but the checked runtime environment did not expose an importable `edge_tts` module from `julia_agent/.venv`.

Checked:

```text
/Users/admin/julia_agent/.venv/bin/python  -> missing edge_tts
/Users/admin/julia_core/.venv/bin/python   -> edge_tts 7.2.8
system python                              -> missing edge_tts
```

## Decision

Do not reinstall blindly.

Operational rule:

```text
Julia Voice Service uses whichever Python environment starts server.py.
If that environment has edge_tts, /api/voice/synthesize returns audio/mpeg.
If not, the endpoint returns 503 and the browser falls back to speechSynthesis.
```

## Recommended Startup

For Edge TTS voice output now:

```bash
cd /Users/admin/julia_core
./.venv/bin/python server.py
```

If Tony wants to reuse another existing environment later, start `server.py` with that environment's Python after confirming:

```bash
/path/to/python -c "import edge_tts; print(edge_tts.__version__)"
```
