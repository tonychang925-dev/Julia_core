"""Session guard (#237): tests must never touch the live system.

Fail closed: if the guard cannot be installed the whole session is refused.
"""
import pytest


def pytest_configure(config):
    try:
        from julia_core.testing import live_guard

        live_guard.install()
    except Exception as exc:  # noqa: BLE001 - any failure must stop the session
        pytest.exit(f"live-system guard could not be installed: {exc!r}", returncode=3)
