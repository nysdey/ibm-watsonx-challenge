"""Wait for an ISC login, then automatically run the random-territory
reliability test and capture the verdict — so item 3's empirical confirmation
completes itself the moment the session goes live, with no manual step.

Safe by construction: it only ever launches the *headless* login probe (no
visible browser) to decide whether the session is up. It runs the actual test
(reliability_test.py) only after the probe reports 'valid', so it never pops a
browser or hangs on a dead session. Standalone — touches nothing in the
dashboard or launcher.

    ISC_Scraper_App/.venv/bin/python3 auto_reliability_watch.py [--minutes 120] [--sample 20] [--rounds 3]

Writes the verdict to ISC_Scraper_App/output/reliability_verdict.txt.
"""
import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent
REPO_ROOT = APP_ROOT.parent
ROOT_PY = REPO_ROOT / ".venv" / "bin" / "python3"
ISC_PY = APP_ROOT / ".venv" / "bin" / "python3"
LOGIN_CAPTURE = REPO_ROOT / "login_capture.py"
HARNESS = APP_ROOT / "reliability_test.py"
VERDICT_FILE = APP_ROOT / "output" / "reliability_verdict.txt"

POLL_SECONDS = 60


def _probe_isc():
    """Headless probe → 'valid' / 'expired' / 'missing' / 'error'. No popup."""
    try:
        r = subprocess.run([str(ROOT_PY), str(LOGIN_CAPTURE), "probe", "isc"],
                           capture_output=True, text=True, timeout=90)
        out = (r.stdout or "").strip().splitlines()
        if out:
            return json.loads(out[-1]).get("status", "error")
    except Exception:
        pass
    return "error"


def _write(msg):
    VERDICT_FILE.parent.mkdir(parents=True, exist_ok=True)
    VERDICT_FILE.write_text(msg)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=int, default=120, help="max time to wait for a login")
    ap.add_argument("--sample", type=int, default=20)
    ap.add_argument("--rounds", type=int, default=3)
    args = ap.parse_args()

    deadline = time.time() + args.minutes * 60
    print(f"[auto-reliability] waiting up to {args.minutes} min for an ISC login "
          f"(polling headless probe every {POLL_SECONDS}s)...", flush=True)

    while time.time() < deadline:
        status = _probe_isc()
        print(f"[auto-reliability] {datetime.now():%H:%M:%S} ISC probe = {status}", flush=True)
        if status == "valid":
            print("[auto-reliability] ISC is live — running the random-territory reliability test...", flush=True)
            proc = subprocess.run(
                [str(ISC_PY), str(HARNESS), "--sample", str(args.sample), "--rounds", str(args.rounds)],
                capture_output=True, text=True,
            )
            verdict = f"=== reliability run {datetime.now():%Y-%m-%d %H:%M:%S} (exit {proc.returncode}) ===\n"
            verdict += (proc.stdout or "") + ("\n[stderr]\n" + proc.stderr if proc.stderr else "")
            _write(verdict)
            print(verdict, flush=True)
            print(f"[auto-reliability] verdict written to {VERDICT_FILE}", flush=True)
            sys.exit(proc.returncode)
        time.sleep(POLL_SECONDS)

    msg = f"[auto-reliability] no ISC login within {args.minutes} min — nothing tested."
    _write(msg + "\n")
    print(msg, flush=True)
    sys.exit(2)


if __name__ == "__main__":
    main()
