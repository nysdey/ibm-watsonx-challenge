"""Step 2 orchestrator — Account Tiering. Standalone, manually triggered:

    cd Account_Tiering
    python3 run.py

Auto-locates Step 1's output via ../ISC_Scraper_App/output/latest.xlsx (still
requires a manual `python3 run.py` — no auto-chaining, per the pipeline's global
rules). Reads TEST_MODE from config (env var / .env), which controls whether this
runs the full ~700-4k account pool or the 5-account sample from sample_selection.py.

Pipeline: load Step 1 -> (TEST_MODE: sample down to 5) -> ZoomInfo enrich -> web
signal scrape -> tier -> write dated + latest.xlsx output.
"""
import logging
import sys
from datetime import datetime

import config
import sample_selection
import schema_io
import signal_scraper
import tiering

# Shared live-watsonx enrichment lives at the repo root — put it on the path.
sys.path.insert(0, str(config.STEP_DIR.parent))
import llm_advisor  # noqa: E402


def _has_value(row, *keys):
    for k in keys:
        v = row.get(k)
        if v not in (None, "", 0):
            try:
                if float(str(v).replace(",", "").replace("$", "")) > 0:
                    return True
            except (TypeError, ValueError):
                if str(v).strip():
                    return True
    return False


def _needs_zoominfo(row):
    """True when Segmentation can't already size this account — i.e. it's missing
    revenue OR employee count, the two facts ZoomInfo contributes. Accounts that
    already have both are scored straight from the Segmentation figures, so looking
    them up again would only cost a slow browser round-trip for no new data."""
    has_rev = _has_value(row, "Location Annual Revenue", "Global Annual Revenue ")
    has_emp = _has_value(row, "Employee Count")
    return not (has_rev and has_emp)


def _apply_llm_advice(rows, logger):
    """Fail-soft live-watsonx enrichment of Primary Play + Sales Angle. Never
    raises and never changes a tier number."""
    if not llm_advisor.available():
        logger.info("LLM advisor: no WATSONX_API_KEY/WATSONX_PROJECT_ID/WATSONX_URL — "
                    "using deterministic play/angle (set all three to enable live "
                    "watsonx.ai enrichment).")
        return
    logger.info("LLM advisor: querying watsonx.ai (%s) for %d accounts' play/angle...",
                llm_advisor.DEFAULT_MODEL, len(rows))
    try:
        advice = llm_advisor.advise_accounts(tiering.llm_intel(rows))
    except Exception as e:  # defense in depth; advise_accounts already swallows errors
        logger.warning("LLM advisor errored (%s) — keeping deterministic play/angle.", e)
        return
    applied = tiering.apply_llm_advice(rows, advice)
    logger.info("LLM advisor: enriched %d/%d accounts (%d unchanged / deterministic).",
                applied, len(rows), len(rows) - applied)


def _setup_logging():
    log_path = config.LOG_DIR / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        handlers=[logging.FileHandler(log_path), logging.StreamHandler(sys.stdout)],
    )
    return log_path


def _build_signal_columns(rows, signals_by_account):
    """Flattens each account's variable-length signal list into Signal_{N}_* columns
    per ../SCHEMA_CONTRACT.md, and returns the extra header columns needed (the max N
    found across all rows in this run)."""
    max_n = max((len(signals_by_account.get(r.get("Account Name"), [])) for r in rows), default=0)
    signal_header = []
    for n in range(1, max_n + 1):
        signal_header += [f"Signal_{n}_Type", f"Signal_{n}_Date", f"Signal_{n}_Summary", f"Signal_{n}_Source_URL"]

    for row in rows:
        signals = signals_by_account.get(row.get("Account Name"), [])
        for n in range(1, max_n + 1):
            if n <= len(signals):
                sig = signals[n - 1]
                row[f"Signal_{n}_Type"] = sig["Type"]
                row[f"Signal_{n}_Date"] = sig["Date"]
                row[f"Signal_{n}_Summary"] = sig["Summary"]
                row[f"Signal_{n}_Source_URL"] = sig["Source_URL"]
            else:
                row[f"Signal_{n}_Type"] = None
                row[f"Signal_{n}_Date"] = None
                row[f"Signal_{n}_Summary"] = None
                row[f"Signal_{n}_Source_URL"] = None
    return signal_header


def main():
    log_path = _setup_logging()
    logger = logging.getLogger("run")
    logger.info("Step 2 starting. TEST_MODE=%s. Log: %s", config.TEST_MODE, log_path)

    # load_step1_accounts prefers SEGMENTED_ACCOUNTS (carrying IBM install intel)
    # and logs the actual source it used; falls back to raw DEDUPED.
    step1_header, rows = schema_io.load_step1_accounts(config.STEP1_LATEST)
    logger.info("Loaded %d base accounts (%d columns)", len(rows), len(step1_header))

    if config.TEST_MODE:
        if config.RANDOM_SAMPLE_SIZE:
            rows = sample_selection.select_random_sample(rows, config.RANDOM_SAMPLE_SIZE)
            logger.info("TEST_MODE (RANDOM_SAMPLE_SIZE=%d): reduced to %d random accounts",
                       config.RANDOM_SAMPLE_SIZE, len(rows))
        else:
            rows = sample_selection.select_test_sample(rows, config.GROUND_TRUTH_ACCOUNTS)
            logger.info("TEST_MODE: reduced to %d sample accounts", len(rows))
        if not rows:
            logger.error("TEST_MODE sample selection returned 0 accounts — nothing to process. Aborting.")
            return

    account_names = [r["Account Name"] for r in rows]

    # Only look ZoomInfo up for accounts the Segmentation data can't already size
    # (missing BOTH revenue AND employee count). Segmentation already carries
    # revenue/employees for ~half the pool; enriching only the gaps is both faster
    # (fewer slow browser lookups) and better targeted — the size score falls back
    # to the Segmentation figures for everyone else. A hard time budget inside
    # enrich_accounts bounds even this set, with the rest resumed on the next run.
    needs_zi = [r["Account Name"] for r in rows if _needs_zoominfo(r)]
    logger.info("ZoomInfo enrichment: %d/%d accounts need a lookup (rest already sized "
                "from Segmentation)...", len(needs_zi), len(account_names))
    try:
        zi_fields_by_account = zoominfo_enrich_safe(needs_zi, logger) if needs_zi else {}
    except Exception as e:
        logger.error("ZoomInfo enrichment aborted: %s. Continuing with blank ZI_* fields "
                     "for accounts not yet looked up — they'll be flagged Unmatched, not dropped.", e)
        zi_fields_by_account = {}

    for row in rows:
        fields = zi_fields_by_account.get(row["Account Name"])
        if fields:
            row.update(fields)
        else:
            row.update({
                "ZI_Match_Status": "Unmatched", "ZI_Match_Method": "", "ZI_Domain": "",
                "ZI_Revenue_USD": None, "ZI_Employee_Count": None, "ZI_Lookup_Timestamp": "",
            })
            logger.warning("%s: no ZoomInfo enrichment result — flagged Unmatched.", row["Account Name"])

    logger.info("Starting web signal scraping for %d accounts...", len(account_names))
    signals_by_account = signal_scraper.gather_signals_for_accounts(account_names)
    checkpoint_state = signal_scraper._load_checkpoint()
    blocked_names = {n for n in account_names if checkpoint_state.get(n, {}).get("status") == "blocked"}
    for name in account_names:
        n = len(signals_by_account.get(name, []))
        logger.info("%s: %d signal(s)", name, n) if n else logger.info("%s: no signals found", name)

    logger.info("Scoring and tiering...")
    tiering.tier_accounts(rows, signals_by_account)
    for row in rows:
        if row["Account Name"] in blocked_names:
            row["Tier_Reasoning"] += "; WARNING: signal search was blocked this run, zero-signal result is not reliable"

    # Optional live-watsonx pass: enrich each account's Primary Play + Sales Angle
    # with LLM judgment (see ../llm_advisor.py). Fully fail-soft — with no
    # WATSONX_* credentials it's a no-op and the deterministic play/angle stand,
    # so tier numbers stay reproducible either way.
    _apply_llm_advice(rows, logger)

    for row in rows:
        logger.info("%s -> Tier %d [%s]: %s", row["Account Name"], row["Tier"],
                    row["Primary_Play"], row["Sales_Angle"])

    zi_columns = ["ZI_Match_Status", "ZI_Match_Method", "ZI_Domain", "ZI_Revenue_USD",
                  "ZI_Employee_Count", "ZI_Lookup_Timestamp"]
    # Seller-facing tier columns first (Play / Angle / Trend / Install), then the
    # component scores (kept for auditability, hidden from the seller view in the
    # dashboard). The dashboard's tiering Results screen curates these into a
    # color-coded, seller-only table — see run_pipeline.py.
    tier_columns = ["Tier", "Tier_Score", "Primary_Play", "Sales_Angle", "Spend_Trend",
                    "Install_Summary", "Competitive_Displacement",
                    "Score_Relationship", "Score_Size", "Score_Footprint",
                    "Score_Displacement", "Score_Vertical", "Score_Signal",
                    "Score_Contactability", "Tier_Reasoning"]
    signal_columns = _build_signal_columns(rows, signals_by_account)
    for row in rows:
        # Drop every internal scratch key (underscore-prefixed) so it never
        # lands in the workbook.
        for k in [k for k in row if k.startswith("_")]:
            row.pop(k, None)

    full_header = step1_header + zi_columns + signal_columns + tier_columns
    prefix = "accounts_tiered_test" if config.TEST_MODE else "accounts_tiered"
    dated, latest = schema_io.write_dated_and_latest(rows, full_header, config.OUTPUT_DIR, prefix, "Tiered Accounts")
    logger.info("Wrote %s and %s", dated, latest)
    logger.info("Step 2 complete. Tier distribution: %s", _tier_counts(rows))


def zoominfo_enrich_safe(account_names, logger):
    try:
        import zoominfo_enrich
    except ImportError as e:
        logger.error("Playwright not installed (%s) — skipping ZoomInfo enrichment, "
                     "all accounts will be Unmatched. Run: pip install playwright && playwright install firefox", e)
        return {}
    return zoominfo_enrich.enrich_accounts(account_names)


def _tier_counts(rows):
    counts = {1: 0, 2: 0, 3: 0}
    for r in rows:
        counts[r["Tier"]] = counts.get(r["Tier"], 0) + 1
    return counts


if __name__ == "__main__":
    main()
