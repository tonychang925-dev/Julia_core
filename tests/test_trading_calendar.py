"""MB-P2.2a-R3.1: Trading Calendar Sabotage Tests."""

from datetime import date
from julia_core.capability.financial.trading_calendar import (
    is_trading_day,
    next_trading_day,
    trading_days_between,
)


def test_weekday_is_trading_day():
    """Monday-Friday are trading days (no holiday)."""
    assert is_trading_day(date(2026, 7, 14))  # Tuesday
    assert is_trading_day(date(2026, 7, 17))  # Friday


def test_saturday_not_trading():
    assert not is_trading_day(date(2026, 7, 11))


def test_sunday_not_trading():
    assert not is_trading_day(date(2026, 7, 12))


def test_fri_next_is_mon():
    """Friday → next trading day is Monday."""
    fri = date(2026, 7, 17)
    mon = date(2026, 7, 20)
    assert next_trading_day(fri) == mon


def test_thu_next_is_fri():
    """Thursday → Friday."""
    thu = date(2026, 7, 16)
    fri = date(2026, 7, 17)
    assert next_trading_day(thu) == fri


def test_sunday_next_is_mon():
    """Sunday → Monday (not a trading day itself)."""
    sun = date(2026, 7, 19)
    mon = date(2026, 7, 20)
    assert next_trading_day(sun) == mon


def test_holiday_skipped():
    """During Spring Festival, trading day skips holiday weekdays."""
    # Feb 17, 2026 (Tuesday of Spring Festival) → next trading day
    spring_festival_tue = date(2026, 2, 17)
    nxt = next_trading_day(spring_festival_tue)
    assert nxt is not None
    # Should be after the holiday period
    assert nxt >= date(2026, 2, 25)


def test_july_2026_has_no_holidays():
    """July 2026: no known holidays, all weekdays are trading days."""
    weekdays = 0
    for d in range(1, 32):
        dt = date(2026, 7, d)
        if dt.weekday() < 5:
            weekdays += 1
            assert is_trading_day(dt), f"{dt} should be a trading day"
    assert weekdays >= 22  # July 2026 has ~22-23 weekdays


def test_trading_days_between_july_2026():
    """trading_days_between for July 1-15, 2026."""
    days = trading_days_between(date(2026, 7, 1), date(2026, 7, 15))
    assert len(days) == 11  # 11 weekdays, no holidays


def test_trading_days_between_includes_endpoints():
    """Inclusive of both start and end."""
    days = trading_days_between(date(2026, 7, 14), date(2026, 7, 14))
    assert len(days) == 1
    assert days[0] == date(2026, 7, 14)
