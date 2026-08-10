"""MB-P2.2a-R3.1: Trading Calendar — authoritative T+1 pairing.

NOT next_available_directory(). T+1 = next_trading_day(T).
Chinese A-share market calendar. Weekend + known holiday skipping.
"""

from __future__ import annotations

from datetime import date, timedelta

# Known A-share holidays (2025-2026) — extend as needed.
# These are market-closed weekdays.
_CN_HOLIDAYS: set[date] = set()

# Spring Festival 2025
_fest_2025_start = date(2025, 1, 27)
_fest_2025 = {_fest_2025_start + timedelta(days=i) for i in range(10)}
_CN_HOLIDAYS.update(_fest_2025)

# Spring Festival 2026
_fest_2026_start = date(2026, 2, 16)
_fest_2026 = {_fest_2026_start + timedelta(days=i) for i in range(9)}
_CN_HOLIDAYS.update(_fest_2026)

# Qingming 2025
_qingming_2025 = date(2025, 4, 4)
_CN_HOLIDAYS.update({_qingming_2025 + timedelta(days=i) for i in range(3)})

# Qingming 2026
_qingming_2026 = date(2026, 4, 5)
_CN_HOLIDAYS.update({_qingming_2026 + timedelta(days=i) for i in range(3)})

# Labor Day 2025
_labor_2025 = date(2025, 5, 1)
_CN_HOLIDAYS.update({_labor_2025 + timedelta(days=i) for i in range(5)})

# Labor Day 2026
_labor_2026 = date(2026, 5, 1)
_CN_HOLIDAYS.update({_labor_2026 + timedelta(days=i) for i in range(5)})

# Dragon Boat 2025
_CN_HOLIDAYS.add(date(2025, 6, 2))

# Dragon Boat 2026
_CN_HOLIDAYS.add(date(2026, 6, 19))

# Mid-Autumn + National Day 2025
_midautumn_2025 = date(2025, 10, 1)
_CN_HOLIDAYS.update({_midautumn_2025 + timedelta(days=i) for i in range(8)})

# Mid-Autumn + National Day 2026
_midautumn_2026 = date(2026, 10, 1)
_CN_HOLIDAYS.update({_midautumn_2026 + timedelta(days=i) for i in range(8)})


def is_trading_day(d: date) -> bool:
    """True if d is an A-share trading day (not weekend, not holiday)."""
    if d.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    if d in _CN_HOLIDAYS:
        return False
    return True


def next_trading_day(d: date) -> date | None:
    """Return the next trading day after d, or None if beyond calendar."""
    current = d + timedelta(days=1)
    # Safety: don't search forever
    for _ in range(14):
        if is_trading_day(current):
            return current
        current += timedelta(days=1)
    return None


def trading_days_between(start: date, end: date) -> list[date]:
    """All trading days in [start, end] inclusive."""
    days: list[date] = []
    current = start
    while current <= end:
        if is_trading_day(current):
            days.append(current)
        current += timedelta(days=1)
    return days


__all__ = [
    "is_trading_day",
    "next_trading_day",
    "trading_days_between",
]
