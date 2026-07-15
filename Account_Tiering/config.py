"""Central config for Step 2 — TEST_MODE, paths, rate caps. Every other script in
this folder reads settings from here rather than `os.environ` directly, so there's
exactly one place to look when tuning a threshold."""
import os
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

# Step 1's fixed handoff filename — see ../SCHEMA_CONTRACT.md. This is how Step 2
# "auto-locates" Step 1's output without the user telling it which file to use.
STEP1_LATEST = REPO_ROOT / "ISC_Scraper_App" / "output" / "latest.xlsx"

# Preferred input: Account Segmentation's output (the reworked pipeline inserts
# Segmentation BEFORE Tiering). SEGMENTED_ACCOUNTS is a superset of DEDUPED — it
# carries every base column PLUS the fuzzy/id-joined IBM install intel — so
# reading it here flows that intel through Tiering → Call Planning → export
# instead of orphaning the whole Segmentation step. Falls back to STEP1_LATEST
# (raw DEDUPED) when Segmentation hasn't run yet.
SEGMENTED_LATEST = REPO_ROOT / "Account_Segmentation" / "output" / "latest.xlsx"

OUTPUT_DIR = STEP_DIR / "output"
CHECKPOINT_DIR = STEP_DIR / "checkpoints"
LOG_DIR = STEP_DIR / "logs"
for _d in (OUTPUT_DIR, CHECKPOINT_DIR, LOG_DIR):
    _d.mkdir(exist_ok=True)

# --- ZoomInfo (browser automation — see zoominfo_enrich.py) ---
ZOOMINFO_BASE_URL = os.environ.get("ZOOMINFO_BASE_URL", "https://app.zoominfo.com")
ZOOMINFO_AUTH_STATE_PATH = Path(
    os.environ.get("ZOOMINFO_AUTH_STATE_PATH", "~/.orum_pipeline/zoominfo_auth_state.json")
).expanduser()

# PLACEHOLDER (user confirmed "pause every 20 calls, per run" on 2026-07-01 without
# a real ZoomInfo quota number behind it yet — see ../SCHEMA_CONTRACT.md and
# ../.env.example). Confirm actual quota before running against the full ~700-account
# pool and raise this deliberately, don't just delete the cap.
ZOOMINFO_CALL_PAUSE_THRESHOLD = int(os.environ.get("ZOOMINFO_CALL_PAUSE_THRESHOLD", "20"))

# In TEST_MODE, GROUND_TRUTH_ACCOUNTS (see sample_selection.py) should be filled in
# with a real Account Name the user already knows the "correct" tier for, so the test
# run has an actual answer to check against instead of just "did it not crash."
GROUND_TRUTH_ACCOUNTS = [a for a in os.environ.get("GROUND_TRUTH_ACCOUNTS", "").split(",") if a.strip()]

# Ad-hoc override for exploratory/live-integration testing (2026-07-01 goal: exercise
# Steps 2/4/5 against real ZoomInfo/Salesloft with varying random batches). When set,
# TEST_MODE uses a true-random N-account sample instead of the deterministic 5-category
# one in sample_selection.select_test_sample() — a different, non-reproducible sample
# on every run, on purpose (the whole point is to stress different real accounts each
# pass, not to reproduce the same test). Unset (default) preserves the original
# deterministic sample used for the "does the mechanism work" dry run.
RANDOM_SAMPLE_SIZE = int(os.environ.get("RANDOM_SAMPLE_SIZE", "50"))  # demo: 50 accounts
