"""Step 5 synthesis — Call Planning.

LOGIC DESIGN (LLM-designed, 2026-07-10). The plan turns the tiered account list
into a working-day-by-working-day dial calendar spanning TODAY → end of year.

Strategy: front-loaded, tier-ordered fill.
  * Accounts are ordered Tier 1 first, then by Tier_Score descending — the
    highest-value accounts come first.
  * They fill the earliest working days up to `per_day_capacity` accounts per
    day. Because we fill day-by-day in value order, Tier 1 naturally lands on
    the first days, Tier 2 in the middle, Tier 3 toward the end — the seller
    always works their best accounts first, while money is still on the table
    for the year.
  * `per_day` auto-scales up if the pool wouldn't fit before Dec 31, so every
    account is guaranteed a date on or before END_OF_YEAR and no account is ever
    dropped or double-booked (hard invariant, asserted below — same philosophy
    as ISC_Scraper_App/_internal/dedup.py: never silently ship a broken plan).

A live-watsonx pass (see ../llm_advisor.py) optionally writes the one-line
coaching note shown atop the calendar; it never changes a planned date.
"""
import logging
import math

logger = logging.getLogger("call_planning")


def allocate(rows, working_days, per_day_capacity):
    """rows: list of dicts with at least Account Name, Tier, Tier_Score.
    working_days: list[date] ascending, weekends/holidays already excluded.
    per_day_capacity: target accounts per working day (auto-raised to fit).

    Returns (rows, per_day) with rows mutated in place to add Planned_Call_Date,
    Planned_Tier, Day_Sequence_Number. Raises AssertionError if the invariant
    (every input row scheduled exactly once, within the window) doesn't hold.
    """
    total_days = len(working_days)
    if total_days == 0:
        raise ValueError("No working days in the planning window — nothing to allocate.")

    n = len(rows)
    # Guarantee the whole pool fits before the last working day: never schedule
    # past END_OF_YEAR. If the requested capacity is too small for the pool,
    # raise it just enough (ceil) so the fill lands on the final day at worst.
    per_day = max(1, per_day_capacity, math.ceil(n / total_days))

    ordered = sorted(rows, key=lambda r: (r.get("Tier", 9), -r.get("Tier_Score", 0)))
    total_assigned = 0
    for i, row in enumerate(ordered):
        d = min(i // per_day, total_days - 1)
        row["Planned_Call_Date"] = working_days[d].strftime("%Y-%m-%d")
        row["Planned_Tier"] = row["Tier"]
        row["Day_Sequence_Number"] = (i % per_day) + 1
        total_assigned += 1

    assert total_assigned == len(rows), (
        f"Call planning invariant violated: {total_assigned} accounts assigned but "
        f"{len(rows)} were input. Refusing to write a plan that drops or duplicates "
        f"accounts — this is a bug in allocate(), not something to silently ignore."
    )
    return rows, per_day
