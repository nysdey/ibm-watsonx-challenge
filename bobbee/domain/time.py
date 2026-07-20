"""Date rules used by schedules and dashboard read models."""

from __future__ import annotations

from datetime import date, datetime, timedelta
import os


def today() -> date:
    raw = (os.environ.get("BOBBEE_DEMO_DATE") or "").strip().lower()
    if not raw:
        return date.today()
    if raw in {"monday", "mon"}:
        current = date.today()
        return current + timedelta(days=(7 - current.weekday()) % 7 or 7)
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        return date.today()


def workday(value: date | None = None) -> date:
    value = value or today()
    while value.weekday() >= 5:
        value += timedelta(days=1)
    return value


def next_weekday(value: date) -> date:
    while value.weekday() >= 5:
        value += timedelta(days=1)
    return value


def quarter(value: date | None = None) -> int:
    value = value or today()
    return (value.month - 1) // 3 + 1


def quarter_bounds(number: int, year: int) -> tuple[date, date]:
    final_month = number * 3
    final_day = {3: 31, 6: 30, 9: 30, 12: 31}[final_month]
    return date(year, final_month - 2, 1), date(year, final_month, final_day)

