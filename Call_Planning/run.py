"""Step 5 orchestrator — Call Planning. Standalone, manually triggered:

    cd Call_Planning
    python3 run.py

Auto-locates Step 4's output via ../Account_Tiering/output/latest.xlsx. The plan
always spans TODAY → END_OF_YEAR (see CALL_PLANNING logic in call_planning.py);
TEST_MODE no longer compresses the window — a smaller pool simply front-loads
into the first working days.
"""
import json
import logging
import sys
from collections import Counter
from datetime import date, datetime

import call_planning
import config
import schema_io
import us_holidays

# Shared live-Claude enrichment lives at the repo root — put it on the path.
sys.path.insert(0, str(config.STEP_DIR.parent))
import llm_advisor  # noqa: E402


def _setup_logging():
    log_path = config.LOG_DIR / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        handlers=[logging.FileHandler(log_path), logging.StreamHandler(sys.stdout)],
    )
    return log_path


def _plan_summary(stats, logger):
    """One-line coaching note atop the calendar. Live Claude when a key is set,
    else a deterministic sentence — never blank, never raises."""
    if llm_advisor.available():
        logger.info("LLM advisor: asking Claude (%s) for the plan coaching note...",
                    llm_advisor.DEFAULT_MODEL)
        note = llm_advisor.advise_plan_summary(stats)
        if note:
            return note
        logger.info("LLM advisor: no note returned — using deterministic summary.")
    else:
        logger.info("LLM advisor: no ANTHROPIC_API_KEY — using deterministic plan summary.")
    t1 = stats["tier_counts"].get("1", stats["tier_counts"].get(1, 0))
    return (f"{stats['total_accounts']} accounts scheduled across {stats['working_days']} "
            f"working days to year-end at up to {stats['per_day']}/day. The {t1} Tier-1 "
            f"accounts are front-loaded into the first days — work them while the year "
            f"still has runway.")


def main():
    log_path = _setup_logging()
    logger = logging.getLogger("run")
    logger.info("Step 5 starting. TEST_MODE=%s. Log: %s", config.TEST_MODE, log_path)

    step2_header, rows = schema_io.load_step2_accounts(config.STEP2_LATEST)
    logger.info("Loaded %d tiered accounts from %s", len(rows), config.STEP2_LATEST)

    working_days = us_holidays.working_days_between(date.today(), config.END_OF_YEAR)
    logger.info("%d working day(s) from today through %s", len(working_days), config.END_OF_YEAR)
    if not working_days:
        logger.error("No working days between today and %s — nothing to plan.", config.END_OF_YEAR)
        return

    tier_counts = {t: sum(1 for r in rows if r.get("Tier") == t) for t in (1, 2, 3)}
    logger.info("Input tier distribution: %s", tier_counts)

    rows, per_day = call_planning.allocate(rows, working_days, config.CALLS_PER_WORKING_DAY)

    per_day_counts = Counter(row["Planned_Call_Date"] for row in rows)
    for row in rows:
        logger.info("%s -> %s (Tier %d, seq %d)", row["Account Name"],
                    row["Planned_Call_Date"], row["Planned_Tier"], row["Day_Sequence_Number"])
    logger.info("Per-day account counts: %s", dict(sorted(per_day_counts.items())))
    logger.info("Plan spans %s .. %s across %d working day(s), up to %d/day.",
                min(per_day_counts), max(per_day_counts), len(per_day_counts), per_day)

    # Meta the dashboard calendar reads for its header note + range.
    stats = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "total_accounts": len(rows),
        "tier_counts": {str(k): v for k, v in tier_counts.items()},
        "working_days": len(working_days),
        "used_days": len(per_day_counts),
        "per_day": per_day,
        "first_day": min(per_day_counts),
        "last_day": max(per_day_counts),
        "window_start": working_days[0].isoformat(),
        "window_end": config.END_OF_YEAR.isoformat(),
    }
    stats["summary"] = _plan_summary(stats, logger)
    (config.OUTPUT_DIR / "plan_meta.json").write_text(json.dumps(stats, indent=2))
    logger.info("Plan note: %s", stats["summary"])

    full_header = step2_header + ["Planned_Call_Date", "Planned_Tier", "Day_Sequence_Number"]
    prefix = "call_plan_test" if config.TEST_MODE else "call_plan"
    dated, latest = schema_io.write_dated_and_latest(rows, full_header, config.OUTPUT_DIR, prefix, "Call Plan")
    logger.info("Wrote %s and %s", dated, latest)
    logger.info("Step 5 complete.")


if __name__ == "__main__":
    main()
