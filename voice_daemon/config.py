"""Configuration loader for Julia Voice Daemon.

Reads from config.yaml with environment variable substitution.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional


def _resolve_env(value: str) -> str:
    """Resolve ${VAR:-default} patterns in config values."""
    if not isinstance(value, str):
        return value
    pattern = r'\$\{(\w+)(?::-([^}]*))?\}'
    def replacer(m):
        var = m.group(1)
        default = m.group(2) or ""
        return os.environ.get(var, default)
    return re.sub(pattern, replacer, value)


def load_config(config_path: Optional[str] = None) -> dict:
    """Load voice daemon configuration from YAML file.

    Returns a dict with resolved environment variables.
    """
    config_path = config_path or Path(__file__).parent / "config.yaml"

    try:
        import yaml
    except ImportError:
        # No PyYAML — return defaults
        return _default_config()

    if not Path(config_path).exists():
        return _default_config()

    try:
        with open(config_path) as f:
            raw = yaml.safe_load(f)
        return _walk_resolve(raw)
    except Exception:
        return _default_config()


def _walk_resolve(obj):
    """Recursively resolve env vars in config dict."""
    if isinstance(obj, dict):
        return {k: _walk_resolve(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_walk_resolve(v) for v in obj]
    elif isinstance(obj, str):
        return _resolve_env(obj)
    return obj


def _default_config() -> dict:
    """Minimal default config when no config file exists."""
    return {
        "daemon": {"name": "julia-voice-daemon", "version": "4.1.1"},
        "audio": {"sample_rate": 16000, "channels": 1, "chunk_size": 1024},
        "transport": {
            "runtime_url": "ws://localhost:9000/ws",
            "reconnect_interval": 3.0,
            "heartbeat_interval": 30.0,
        },
        "stt": {
            "server_url": os.environ.get("WHISPER_SERVER_URL", "http://localhost:8001"),
            "language": "zh",
            "beam_size": 5,
        },
        "tts": {
            "api_key": os.environ.get("ELEVENLABS_API_KEY", ""),
            "voice_id": os.environ.get("ELEVENLABS_VOICE_ID", "tOuLUAIdXShmWH7PEUrU"),
        },
    }
