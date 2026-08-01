from __future__ import annotations


def estimate_tokens(text: str) -> int:
    """Deterministic rough token estimator.

    Chinese-heavy voice/runtime text does not map cleanly to 4 chars/token, so
    use a conservative lower denominator while keeping dependency-free tests.
    """

    cleaned = (text or "").strip()
    if not cleaned:
        return 0
    return max(1, (len(cleaned) + 2) // 3)
