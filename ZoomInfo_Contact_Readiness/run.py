"""Step 4 orchestrator — ZoomInfo Contact Readiness. Standalone, manually
triggered, by the user themselves, in their own terminal:

    cd ZoomInfo_Contact_Readiness
    python3 run.py --date 2026-07-01           # auto mode (default): today's Step 3 plan
    python3 run.py --mode manual               # manual mode: pick accounts yourself

Auto mode auto-locates Step 3's output, pulls that day's account list, imports
into ZoomInfo, applies the "Infra Outbound" buyer group filter, and exports the
resulting contacts to Salesloft — no interactive confirmation prompt.

Manual mode (added 2026-07-05) opens Step 2's full tiered account list
(Account_Tiering/output/latest.xlsx) in your spreadsheet app so you can see
every account's tier/revenue/signals/etc., then asks you to type which
account names to run through Step 4 — ignoring Step 3's date-based plan
entirely for this run.

**Gate removed 2026-07-05, explicit user decision.** The original design (see
../README.md and CONTEXT.md history) had this step print the contact list and
require typing "YES" before touching Salesloft, per the pipeline's own original
spec: "print/export the day's account + contact list for me to review before
executing the ZoomInfo import / Salesloft push — not fire automatically. We'll
remove this gate once I trust the upstream output." The user explicitly said
they now trust it and will be the one running this script themselves (not an
autonomous agent), so the interactive prompt was removed. The review file is
still written before the export for an audit trail — just no longer blocking.
"""
import logging
import sys
from datetime import date, datetime

import config
import schema_io
import zoominfo_import


def _parse_args():
    import argparse
    parser = argparse.ArgumentParser(description="Step 4: ZoomInfo Contact Readiness")
    parser.add_argument("--date", default=date.today().isoformat(),
                         help="Target call-plan date, YYYY-MM-DD (default: today). In manual mode, "
                              "only used for naming the ZoomInfo list / output files.")
    parser.add_argument("--mode", choices=["auto", "manual"], default="auto",
                         help="auto (default): use today's Step 3 plan. manual: pick accounts yourself "
                              "from Step 2's full tiered list.")
    parser.add_argument("--accounts", default=None,
                         help="manual mode only: pipe-separated ('|') exact Account Name(s), or 'all'. "
                              "Pipe, not comma, because real account names routinely contain commas "
                              "(e.g. 'OPENAI, INC.') which a comma-split would silently mangle. "
                              "If omitted in manual mode, prompts interactively instead (CLI use only — "
                              "the web dashboard always passes this explicitly, never prompts).")
    parser.add_argument("--cadence", default=None,
                         help="Salesloft cadence to export the pulled contacts into. The dashboard's "
                              "Fill Contacts dropdown passes this; defaults to config.salesloft_cadence_name().")
    return parser.parse_args()


def _manual_account_selection(accounts_arg):
    """Manual mode's account list. If `accounts_arg` is given (the web
    dashboard always supplies this — see ../run_pipeline.py), uses it directly,
    non-interactively. Otherwise (CLI-only convenience), opens Step 2's full
    tiered account list in the OS default app (Excel/Numbers) so the user can
    see tier/revenue/signals/everything, then prompts for which account names
    to run through Step 4."""
    path = config.STEP2_LATEST
    if not path.exists():
        raise schema_io.SchemaError(
            f"Manual mode needs Step 2's output at {path}, but it doesn't exist. Run Account_Tiering/run.py first."
        )
    _, rows = schema_io.load_all_step2_accounts(path)

    if accounts_arg is None:
        import subprocess
        print(f"Opening {path} — review the full tiered account list...")
        subprocess.run(["open", str(path)])
        accounts_arg = input(
            "\nType the exact Account Name(s) to run through Step 4, separated by '|' "
            "(not comma — account names routinely contain commas) "
            "(or 'all' to use every account in the file): "
        ).strip()

    if accounts_arg.lower() == "all":
        return [r["Account Name"] for r in rows]
    wanted = {n.strip() for n in accounts_arg.split("|") if n.strip()}
    matched = [r["Account Name"] for r in rows if r["Account Name"] in wanted]
    missing = wanted - set(matched)
    if missing:
        print(f"WARNING: {len(missing)} name(s) not found in Step 2's output, skipping: {missing}")
    return matched


def _setup_logging():
    log_path = config.LOG_DIR / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        handlers=[logging.FileHandler(log_path), logging.StreamHandler(sys.stdout)],
    )
    return log_path


def main():
    args = _parse_args()

    log_path = _setup_logging()
    logger = logging.getLogger("run")
    logger.info("Step 4 starting for date %s. TEST_MODE=%s. Log: %s", args.date, config.TEST_MODE, log_path)

    if args.mode == "manual":
        account_names = _manual_account_selection(args.accounts)
        if not account_names:
            logger.warning("No accounts selected in manual mode. Nothing to do.")
            return
        logger.info("Manual mode: %d account(s) selected: %s", len(account_names), account_names)
        accounts = account_names  # only used for a len() below
    else:
        accounts = schema_io.load_accounts_for_date(config.STEP3_LATEST, args.date)
        if not accounts:
            logger.warning("No accounts found for %s in %s. Nothing to do.", args.date, config.STEP3_LATEST)
            return
        logger.info("Loaded %d account(s) planned for %s", len(accounts), args.date)
        account_names = [a["Account Name"] for a in accounts]

    # Cadence comes from the dashboard's Fill Contacts dropdown (--cadence); falls
    # back to the config default for a bare CLI run.
    cadence_name = args.cadence or config.salesloft_cadence_name()
    # Single-session flow: filter -> pull contacts -> export to the cadence, all
    # in one browser (see zoominfo_import.import_and_export_to_salesloft).
    try:
        contacts_count_text, raw_contacts = zoominfo_import.import_and_export_to_salesloft(
            args.date, account_names, cadence_name)
    except ImportError as e:
        logger.error("Playwright not installed (%s) — cannot reach ZoomInfo. "
                     "Run: pip install playwright && playwright install firefox", e)
        sys.exit(1)
    except zoominfo_import.SessionExpired as e:
        # A login/session problem, not a code bug — log the clean, actionable
        # message (no traceback) so it lands in the log file and the dashboard tail.
        logger.error("%s", e)
        sys.exit(2)
    except Exception as e:
        # Any other automation failure: log the full traceback to the LOG FILE
        # (not just stdout) so it's recoverable, then exit non-zero.
        logger.exception("ZoomInfo Contact Readiness failed: %s", e)
        sys.exit(1)

    if not raw_contacts:
        logger.warning("Zero contacts pulled from the '%s' buyer group for %s (tab showed %r). "
                       "Nothing exported — check the ZoomInfo list manually.",
                       config.BUYER_GROUP_NAME, args.date, contacts_count_text)
        return

    import_batch_id = f"{args.date}_{datetime.now().strftime('%H%M%S')}"
    review_rows = [{
        "Raw_Row_Text": c["raw"],
        "Buyer_Group": config.BUYER_GROUP_NAME,
        "Import_Batch_ID": import_batch_id,
        "Exported_To_Cadence": cadence_name,
    } for c in raw_contacts]
    review_header = list(review_rows[0].keys())

    exported_path = schema_io.write_contact_export(
        review_rows, review_header, config.OUTPUT_DIR, args.date, "Contacts Exported"
    )
    logger.info("Exported %d contact(s) to cadence '%s' (%s). Audit file: %s",
                len(review_rows), cadence_name, contacts_count_text, exported_path)
    logger.info("Step 4 complete for %s.", args.date)


if __name__ == "__main__":
    main()
