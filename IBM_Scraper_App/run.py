"""IBM Scraper orchestrator -- new Step 2 (runs between ISC Scraper and
Account Segmentation).

    cd IBM_Scraper_App
    python3 run.py                       # all available sub-scrapers, CovIDs auto-resolved
    python3 run.py --only power          # just one sub-scraper
    python3 run.py --covids T0016329,T0018004   # explicit CovIDs (testing/manual)

Resolves the selected CovIDs from the ISC step (see covid_source.py), then runs
each sub-scraper to produce its install-base file in output/. Sub-scrapers that
still need live-portal calibration are marked PENDING and skipped with a clear
note rather than failing the whole run.
"""
import argparse
import json
import logging
import sys
import time
from datetime import datetime

import config
import covid_source

# Sub-scraper registry. Browser-based ones are added as they're built out.
import sub_power
import sub_storage
import sub_cloud
import sub_isc_install

SUBSCRAPERS = {
    "power": {"label": "Power Install (local filter)", "fn": sub_power.run_power_install, "ready": True},
    "storage": {"label": "Storage Install (CID Dashboard)", "fn": sub_storage.run_storage_install, "ready": True},
    "cloud": {"label": "Cloud Install (GTM Navigator)", "fn": sub_cloud.run_cloud_install, "ready": True},
    "ibm_non_infra": {"label": "IBM Non-Infra Install (ISC dashboard)", "fn": sub_isc_install.run_ibm_non_infra, "ready": True},
    "competitive": {"label": "Competitive Install (ISC dashboard)", "fn": sub_isc_install.run_competitive, "ready": True},
}
# Full run produces ALL FIVE install files so downstream Account Segmentation
# always joins a consistent, same-run set (a partial run would leave a stale
# _latest.xlsx from a previous selection and silently mis-attach installs).
# ibm_non_infra's territory pull is large (~37k rows); if a demo needs it fast,
# skip it explicitly with `--skip ibm_non_infra` rather than dropping it here.
ORDER = ["storage", "cloud", "power", "ibm_non_infra", "competitive"]


def _setup_logging():
    # A dated log file (in addition to stdout) lets the pipeline dashboard show
    # a "last run" marker for this step without exposing the install files
    # themselves (STEPS["ibm"]["output"] is None on purpose).
    from datetime import datetime
    log_dir = config.APP_ROOT / "logs"
    log_dir.mkdir(exist_ok=True)
    log_path = log_dir / f"run_{datetime.now():%Y%m%d_%H%M%S}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler(log_path)],
    )


def _freshness(key, result, run_started):
    """Classify an output for the end-of-run summary. This is the accuracy
    guardrail: a browser sub-scraper that failed leaves last run's _latest.xlsx
    on disk, and downstream Segmentation would consume it as if current. Compare
    each expected output's mtime to this run's start so a stale/missing file is
    surfaced loudly instead of silently mis-attaching installs.

    Returns (state, detail) where state is one of:
      FRESH   -- produced by this run
      STALE   -- sub-scraper failed but an older _latest.xlsx still on disk
      MISSING -- failed/skipped and no output exists at all
      FAILED  -- ran with an error (state refined to STALE/MISSING via the file)
    """
    _, latest = config.dated_and_latest_paths(key)
    exists = latest.exists()
    mtime = latest.stat().st_mtime if exists else None
    if result.get("status") == "ok":
        # Trust the run only if it actually (re)wrote the file this run.
        if exists and mtime >= run_started - 1:
            return "FRESH", str(latest)
        return "STALE", f"ok but {latest.name} not refreshed this run"
    # error or pending
    if exists:
        age_h = (run_started - mtime) / 3600.0
        return "STALE", f"kept prior {latest.name} ({age_h:.1f}h old) — NOT from this run"
    return "MISSING", f"no {latest.name} on disk"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--covids", help="Comma-separated CovIDs; overrides auto-resolution")
    ap.add_argument("--only", choices=list(SUBSCRAPERS), help="Run only this sub-scraper")
    ap.add_argument("--skip", help="Comma-separated sub-scrapers to skip in a full run "
                                   "(e.g. --skip ibm_non_infra for a faster demo)")
    ap.add_argument("--source", help="Override POWER_INSTALL_ALL path (power only)")
    args = ap.parse_args()

    _setup_logging()
    log = logging.getLogger("ibm_scraper")
    run_started = time.time()

    explicit = [c.strip() for c in args.covids.split(",")] if args.covids else None
    covids, source = covid_source.resolve_covids(explicit)
    log.info("Resolved %d CovID(s) from %s", len(covids), source)
    log.info("CovIDs: %s", ", ".join(covids[:15]) + (" ..." if len(covids) > 15 else ""))

    skip = {s.strip() for s in args.skip.split(",")} if args.skip else set()
    bad_skip = skip - set(SUBSCRAPERS)
    if bad_skip:
        ap.error(f"--skip names unknown sub-scraper(s): {sorted(bad_skip)}")
    if args.only:
        keys = [args.only]
    else:
        keys = [k for k in ORDER if k not in skip]
        if skip:
            log.warning("Skipping %s this run (explicit --skip); their _latest.xlsx "
                        "will stay stale for downstream Segmentation.", sorted(skip))

    results = {}
    for key in keys:
        entry = SUBSCRAPERS[key]
        if not entry["ready"]:
            log.info("[%s] PENDING -- %s not yet calibrated against its live portal; skipping.",
                     key, entry["label"])
            results[key] = {"status": "pending"}
            continue
        log.info("[%s] %s ...", key, entry["label"])
        try:
            if key == "power":
                summary = entry["fn"](covids, source_path=(config.APP_ROOT / args.source) if args.source else None)
            else:
                summary = entry["fn"](covids)
            summary["status"] = "ok"
            results[key] = summary
            log.info("[%s] done: %s", key, {k: v for k, v in summary.items() if k != "per_covid"})
        except Exception as e:
            log.exception("[%s] FAILED: %s", key, e)
            results[key] = {"status": "error", "error": str(e)}

    _report(log, covids, source, keys, results, run_started)
    log.info("IBM Scraper run complete at %s", datetime.now().isoformat(timespec="seconds"))
    return results


def _report(log, covids, source, keys, results, run_started):
    """Emit an end-of-run accuracy summary + write output/run_manifest.json so the
    dashboard/human and downstream steps can tell which install files are truly
    current for this CovID selection versus stale leftovers."""
    manifest = {
        "run_at": datetime.now().isoformat(timespec="seconds"),
        "covid_source": source,
        "covids": covids,
        "outputs": {},
    }
    log.info("---- IBM Scraper output summary (selection: %d CovID(s)) ----", len(covids))
    stale_or_missing = []
    for key in keys:
        res = results.get(key, {"status": "skipped"})
        state, detail = _freshness(key, res, run_started)
        rows = res.get("matched_rows", res.get("total_rows"))
        manifest["outputs"][config.OUTPUT_NAMES[key]] = {
            "sub_scraper": key,
            "status": res.get("status"),
            "freshness": state,
            "rows": rows,
            "detail": detail,
        }
        rowtxt = f", {rows} rows" if rows is not None else ""
        log.info("  %-9s %-7s %s%s", key, state, detail, rowtxt)
        if state != "FRESH":
            stale_or_missing.append(key)

    manifest_path = config.OUTPUT_DIR / "run_manifest.json"
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2))
    log.info("  wrote manifest -> %s", manifest_path.name)
    if stale_or_missing:
        log.warning("ACCURACY WARNING: %d of %d outputs are NOT fresh from this run "
                    "(%s). Downstream Segmentation may join stale/absent install data "
                    "for the current CovID selection — re-run those sub-scrapers "
                    "(check portal logins) before relying on the results.",
                    len(stale_or_missing), len(keys), ", ".join(stale_or_missing))


if __name__ == "__main__":
    main()
