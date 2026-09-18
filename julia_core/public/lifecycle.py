"""Stable public lifecycle entry points for external transport adapters."""

from __future__ import annotations


def shutdown_core_runtime() -> None:
    """Shut down Core's process-singleton capability lifecycle.

    The return value and parameters intentionally carry no private runtime,
    provider, manager, or bridge objects. Callers express lifecycle intent only;
    Core owns initialization, in-flight draining, provider close, and loop stop.
    """
    from julia_core.runtime.capability_bridge import get_capability_bridge

    get_capability_bridge().close()


__all__ = ["shutdown_core_runtime"]
