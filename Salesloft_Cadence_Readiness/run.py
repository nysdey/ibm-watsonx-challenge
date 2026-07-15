"""Step 5 orchestrator — Salesloft Cadence Readiness. Standalone, manually
triggered, by the user themselves in their own terminal:

    cd Salesloft_Cadence_Readiness
    python3 run.py                              # uses config's default cadence
    python3 run.py --cadence "Targeted Outreach 4 - TEST"   # explicit override

Advances everyone currently at cadence step 1 to the call step (see
salesloft_advance.py's module docstring for why this no longer depends on
Step 4's output — that per-contact-email design broke and was replaced with a
simpler, literal reading of the original spec). No interactive confirmation
gate — removed 2026-07-05, same explicit user decision as Step 4 (see
../ZoomInfo_Contact_Readiness/run.py's module docstring).

Auto vs manual cadence selection is a concern of run_pipeline.py (the
repo-root dashboard), not this script — this script just takes whatever
`--cadence` it's given (or falls back to config.salesloft_cadence_name()),
so it stays runnable standalone too.
"""
import logging
import sys
from datetime import date, datetime

import config


def _parse_args():
    import argparse
    parser = argparse.ArgumentParser(description="Step 5: Salesloft Cadence Readiness")
    parser.add_argument("--date", default=date.today().isoformat(),
                         help="Date, used only for naming the log file (default: today).")
    parser.add_argument("--cadence", default=None,
                         help="Cadence to advance step-1 people in (default: config.salesloft_cadence_name()).")
    return parser.parse_args()


def _setup_logging():
    log_path = config.LOG_DIR / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        handlers=[logging.FileHandler(log_path), logging.StreamHandler(sys.stdout)],
    )
    return log_path


def _write_advance_log(rows, header, target_date_str):
    import openpyxl
    path = config.OUTPUT_DIR / f"step_advance_log_{target_date_str.replace('-', '')}.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Step Advance Log"
    ws.append(header)
    for row in rows:
        ws.append([row.get(col) for col in header])
    wb.save(path)
    return path


def main():
    args = _parse_args()
    cadence_name = args.cadence or config.salesloft_cadence_name()

    log_path = _setup_logging()
    logger = logging.getLogger("run")
    logger.info("Step 5 starting. Cadence: '%s'. Log: %s", cadence_name, log_path)

    import salesloft_advance
    try:
        advanced, skipped = salesloft_advance.advance_all_at_step_one(args.date, cadence_name)
    except salesloft_advance.SessionExpired as e:
        logger.error("%s", e)
        sys.exit(2)
    except ImportError as e:
        logger.error("Playwright not installed (%s) — run: pip install playwright && "
                     "playwright install firefox", e)
        sys.exit(1)
    except Exception as e:
        logger.exception("Salesloft Cadence Readiness failed: %s", e)
        sys.exit(1)

    log_rows = []
    now_iso = datetime.now().isoformat()
    for name in advanced:
        log_rows.append({
            "Contact_Name": name, "Cadence_Name": cadence_name,
            "Previous_Step": config.CADENCE_FIRST_STEP_NAME,
            "New_Step": config.CADENCE_CALL_STEP_NAME, "Timestamp": now_iso, "Status": "Advanced",
        })
    for name, reason in skipped:
        log_rows.append({
            "Contact_Name": name, "Cadence_Name": cadence_name,
            "Previous_Step": "", "New_Step": "", "Timestamp": now_iso, "Status": f"Failed: {reason}",
        })

    header = ["Contact_Name", "Cadence_Name", "Previous_Step", "New_Step", "Timestamp", "Status"]
    if log_rows:
        log_path_out = _write_advance_log(log_rows, header, args.date)
        logger.info("Advanced %d, %d skipped/failed. Log: %s", len(advanced), len(skipped), log_path_out)
    else:
        logger.info("Nothing to advance (step 1 was empty or already clear).")
    logger.info("Step 5 complete.")

    # Hard failure (nothing advanced AND everything failed) must exit non-zero so
    # the dashboard shows an error rather than a false success.
    if not advanced and skipped:
        reason = skipped[0][1] if skipped and len(skipped[0]) > 1 else "cadence navigation failed"
        logger.error("Salesloft advance made no progress: %s", reason)
        sys.exit(1)


if __name__ == "__main__":
    main()
