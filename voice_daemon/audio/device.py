"""Audio device management — detect and configure input/output devices."""

from __future__ import annotations

from typing import Optional


def get_default_input_device() -> Optional[dict]:
    """Get the default audio input device info."""
    try:
        import sounddevice as sd
        idx = sd.default.device[0]
        if idx is not None and idx < len(sd.query_devices()):
            dev = sd.query_devices()[idx]
            return {
                "index": idx,
                "name": dev['name'],
                "channels": dev['max_input_channels'],
                "sample_rate": int(dev['default_samplerate']),
            }
    except Exception:
        pass
    return None


def get_default_output_device() -> Optional[dict]:
    """Get the default audio output device info."""
    try:
        import sounddevice as sd
        idx = sd.default.device[1]
        if idx is not None and idx < len(sd.query_devices()):
            dev = sd.query_devices()[idx]
            return {
                "index": idx,
                "name": dev['name'],
                "channels": dev['max_output_channels'],
                "sample_rate": int(dev['default_samplerate']),
            }
    except Exception:
        pass
    return None


def list_all_devices() -> tuple[list[dict], list[dict]]:
    """List all input and output devices. Returns (inputs, outputs)."""
    inputs, outputs = [], []
    try:
        import sounddevice as sd
        for i, dev in enumerate(sd.query_devices()):
            info = {
                "index": i,
                "name": dev['name'],
                "sample_rate": int(dev['default_samplerate']),
            }
            if dev['max_input_channels'] > 0:
                info["channels"] = dev['max_input_channels']
                inputs.append(info)
            if dev['max_output_channels'] > 0:
                info["channels"] = dev['max_output_channels']
                outputs.append(info)
    except Exception:
        pass
    return inputs, outputs


def test_audio() -> dict:
    """Quick audio subsystem check. Returns status dict."""
    return {
        "input": get_default_input_device(),
        "output": get_default_output_device(),
        "sounddevice_available": _check_sounddevice(),
    }


def _check_sounddevice() -> bool:
    try:
        import sounddevice
        return True
    except ImportError:
        return False
