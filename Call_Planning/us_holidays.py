"""US federal holidays, computed by rule rather than hardcoded per-year so this
stays correct for any year without manual upkeep. Weekend-observed dates shift to
the nearest weekday per the standard federal rule (Saturday -> preceding Friday,
Sunday -> following Monday)."""
from datetime import date, timedelta


def _nth_weekday(year, month, weekday, n):
    """weekday: Monday=0 .. Sunday=6. n=1 for first, -1 for last (in that month)."""
    if n > 0:
        d = date(year, month, 1)
        offset = (weekday - d.weekday()) % 7
        d += timedelta(days=offset + 7 * (n - 1))
        return d
    d = date(year, month + 1, 1) - timedelta(days=1) if month < 12 else date(year, 12, 31)
    offset = (d.weekday() - weekday) % 7
    return d - timedelta(days=offset)


def _observed(d):
    """Shift a fixed-date holiday landing on a weekend to the nearest weekday."""
    if d.weekday() == 5:  # Saturday
        return d - timedelta(days=1)
    if d.weekday() == 6:  # Sunday
        return d + timedelta(days=1)
    return d


def federal_holidays(year):
    """Returns a set[date] of US federal holidays observed in `year`."""
    return {
        _observed(date(year, 1, 1)),        # New Year's Day
        _nth_weekday(year, 1, 0, 3),         # MLK Day - 3rd Monday of January
        _nth_weekday(year, 2, 0, 3),         # Presidents Day - 3rd Monday of February
        _nth_weekday(year, 5, 0, -1),        # Memorial Day - last Monday of May
        _observed(date(year, 6, 19)),        # Juneteenth
        _observed(date(year, 7, 4)),         # Independence Day
        _nth_weekday(year, 9, 0, 1),         # Labor Day - 1st Monday of September
        _nth_weekday(year, 10, 0, 2),        # Columbus Day - 2nd Monday of October
        _observed(date(year, 11, 11)),       # Veterans Day
        _nth_weekday(year, 11, 3, 4),        # Thanksgiving - 4th Thursday of November
        _observed(date(year, 12, 25)),       # Christmas
    }


def working_days_between(start, end):
    """Returns a sorted list[date] of Mon-Fri days in [start, end] inclusive,
    excluding US federal holidays. Spans multiple years correctly (recomputes the
    holiday set per calendar year touched)."""
    holidays = set()
    for year in range(start.year, end.year + 1):
        holidays |= federal_holidays(year)

    days = []
    d = start
    while d <= end:
        if d.weekday() < 5 and d not in holidays:
            days.append(d)
        d += timedelta(days=1)
    return days
