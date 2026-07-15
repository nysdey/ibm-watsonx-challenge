"""Random-territory scrape reliability harness for Step 1.

Purpose (per the standing requirement "random test this until you can confirm
it will not miss"): the aura HTTP endpoint intermittently returns 0 rows for a
territory that actually has accounts — a Salesforce-side cold-cache transient
(see CONTEXT.md Round 4). A single scrape can't tell a *genuinely empty*
territory from a *transiently-missed* one. This harness surfaces the difference
empirically by querying a random sample of CovIDs across ALL industries several
times and flagging any whose count is inconsistent between rounds — that
flip-flop (0 one round, >0 another) is the exact signature of a silent miss.

    ISC_Scraper_App/.venv/bin/python3 reliability_test.py [--sample N] [--rounds R] [--seed S]

Exit codes:
    0  every sampled CovID was consistent across all rounds (no miss detected)
    1  at least one CovID flip-flopped (a real miss risk) or errored
    2  no live ISC session (log in via the dashboard first, then re-run)

This is read-only: it only issues count queries, never writes lists or files.
Requires a live ISC login — it self-reports and exits 2 if the session is dead.
"""
import argparse
import random
import sys
import time
import urllib.error
from collections import defaultdict
from pathlib import Path

import openpyxl

INTERNAL = Path(__file__).resolve().parent / "_internal"
sys.path.insert(0, str(INTERNAL))
import http_scraper as hs  # noqa: E402

COVID_XLSX = INTERNAL / "CovID.xlsx"


def _all_cov_ids():
    """Every CovID in the source workbook (col 0), deduped, order-stable."""
    wb = openpyxl.load_workbook(COVID_XLSX, read_only=True, data_only=True)
    ws = wb.active
    seen, out = set(), []
    for row in ws.iter_rows(min_row=2, values_only=True):
        cid = str(row[0]).strip() if row and row[0] else ""
        if cid and cid.upper().startswith("T") and cid not in seen:
            seen.add(cid)
            out.append(cid)
    wb.close()
    return out


def _count_for(cov_id, list_id, boot):
    """One getAccountPageContents call → (status, count). status is 'ok',
    'expired' (401 / dead session), or 'error'. No retry here on purpose — the
    whole point is to observe raw per-call behavior across rounds."""
    cookies, token, context, headers = boot
    params = {
        "id": list_id, "type": "IBM Accounts", "accountColumns": hs.ACCOUNT_COLUMNS,
        "filters": [{"id": "covId", "operator": "equals", "values": [cov_id]}],
        "sortOrder": "asc", "sortBy": "DOM_COMP_NAME", "filterListRemoved": [],
    }
    try:
        resp = hs._aura_post(cookies, token, context, "getAccountPageContents", params, headers)
    except urllib.error.HTTPError as e:
        if e.code == 401:
            return "expired", None
        return "error", None
    except Exception:
        return "error", None
    actions = resp.get("actions", [])
    if not actions:
        return "error", None
    outer = actions[0].get("returnValue")
    if outer is None:
        return "error", None
    return "ok", (outer.get("returnValue") or {}).get("numberOfAccounts", 0)


def _live_session_or_refresh(boot):
    """Return (boot, pool) for a live session, regenerating the aura bootstrap
    once if the cached token is stale. Right after a re-login, auth_state.json
    is fresh but the cached aura_bootstrap.json still holds the old 401 token —
    so a single getProspectLists failure isn't 'not logged in', it's 'derived
    token needs refreshing'. Returns (None, None) only if a freshly-generated
    token still fails (genuinely not logged in)."""
    import subprocess
    for attempt in range(2):
        if boot:
            try:
                pool = hs.get_all_prospect_list_ids(*boot)
                if pool:
                    return boot, pool
            except urllib.error.HTTPError as e:
                if e.code != 401:
                    raise
            except Exception:
                pass
        if attempt == 0:
            # Regenerate the aura token from whatever session is saved now.
            # On a live session this completes in ~15s; on a dead one the
            # bootstrap browser hangs waiting for an interactive login, so bound
            # it — a timeout here means "session genuinely dead, not just stale
            # token" and we fail fast instead of hanging for minutes.
            print("Refreshing aura token from the current session (bounded)...")
            try:
                subprocess.run([sys.executable, str(INTERNAL / "http_scraper.py"), "--bootstrap-only"],
                               cwd=str(INTERNAL), timeout=90)
            except subprocess.TimeoutExpired:
                return None, None
            boot = hs.load_bootstrap()
    return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=15, help="how many random CovIDs to test")
    ap.add_argument("--rounds", type=int, default=3, help="how many times to re-query each (catches intermittency)")
    ap.add_argument("--seed", type=int, default=None, help="fix the random sample for reproducibility")
    args = ap.parse_args()

    boot = hs.load_bootstrap()
    boot, pool = _live_session_or_refresh(boot)
    if boot is None:
        print("ISC session is not usable (HTTP 401) — log in via the dashboard, then re-run.")
        sys.exit(2)

    all_ids = _all_cov_ids()
    if args.seed is not None:
        random.seed(args.seed)
    sample = random.sample(all_ids, min(args.sample, len(all_ids)))
    print(f"Testing {len(sample)} random CovIDs x {args.rounds} rounds "
          f"(pool={len(pool)} lists, {len(all_ids)} total CovIDs available)\n")

    # cov_id -> list of counts per round ('ERR' entries mark failed calls)
    results = defaultdict(list)
    for rnd in range(1, args.rounds + 1):
        print(f"--- round {rnd}/{args.rounds} ---")
        for i, cov in enumerate(sample):
            status, count = _count_for(cov, pool[i % len(pool)], boot)
            if status == "expired":
                print("\nISC session expired mid-run (HTTP 401) — log in and re-run.")
                sys.exit(2)
            results[cov].append(count if status == "ok" else "ERR")
            print(f"  {cov}: {results[cov][-1]}")
            time.sleep(0.2)
        print()

    # Verdict: a CovID is a MISS RISK if its non-error counts disagree across
    # rounds (e.g. 0 then 1163), or if any round errored.
    consistent_nonzero, consistent_zero, flaky, errored = [], [], [], []
    for cov, counts in results.items():
        if "ERR" in counts:
            errored.append((cov, counts))
            continue
        distinct = set(counts)
        if len(distinct) > 1:
            flaky.append((cov, counts))
        elif counts[0] == 0:
            consistent_zero.append(cov)
        else:
            consistent_nonzero.append((cov, counts[0]))

    print("=" * 60)
    print(f"consistent non-zero : {len(consistent_nonzero)}")
    print(f"consistent zero     : {len(consistent_zero)}  (likely genuinely empty)")
    print(f"FLAKY (miss risk)   : {len(flaky)}")
    print(f"errored             : {len(errored)}")
    if flaky:
        print("\n!! These CovIDs returned different counts across rounds — the")
        print("   intermittent-miss bug. A single scrape of these WOULD miss:")
        for cov, counts in flaky:
            print(f"     {cov}: {counts}")
    if errored:
        print("\n!! These CovIDs errored on at least one call:")
        for cov, counts in errored:
            print(f"     {cov}: {counts}")
    if consistent_zero:
        print(f"\n   Consistently-zero CovIDs (verify against the real UI if unexpected): "
              f"{', '.join(consistent_zero)}")

    ok = not flaky and not errored
    print("\nVERDICT:", "PASS — no misses across rounds" if ok
          else "FAIL — miss risk detected, do not trust a single-pass scrape as-is")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
