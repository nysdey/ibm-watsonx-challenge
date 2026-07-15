"""Central config for Step 3 — see ../Account_Tiering/config.py for the pattern
this follows (one place to look for every tunable, TEST_MODE included)."""
import os
from datetime import date
from pathlib import Path

from env_utils import load_env, REPO_ROOT

load_env()


def _bool_env(name, default):
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


TEST_MODE = _bool_env("TEST_MODE", True)

STEP_DIR = Path(__file__).resolve().parent
STEP2_LATEST = REPO_ROOT / "Account_Tiering" / "output" / "latest.xlsx"

OUTPUT_DIR = STEP_DIR / "output"
LOG_DIR = STEP_DIR / "logs"
for _d in (OUTPUT_DIR, LOG_DIR):
    _d.mkdir(exist_ok=True)

# The business goal is explicitly "through end of 2026," not a rolling window.
# The plan ALWAYS spans today → END_OF_YEAR (the calendar the seller sees), in
# both TEST_MODE and full runs — TEST_MODE no longer compresses the window, it
# just means a smaller account pool front-loads into the first working days.
END_OF_YEAR = date(2026, 12, 31)

# A seller's target account throughput per working day. The allocator front-
# loads the best accounts (Tier 1, then by score) into the earliest working
# days at up to this many per day; it automatically raises the per-day number
# if the pool wouldn't otherwise fit before END_OF_YEAR, so every account is
# always scheduled on or before Dec 31. Tune this to the team's real daily
# capacity (override with env CALLS_PER_WORKING_DAY).
CALLS_PER_WORKING_DAY = int(os.environ.get("CALLS_PER_WORKING_DAY", "6"))
