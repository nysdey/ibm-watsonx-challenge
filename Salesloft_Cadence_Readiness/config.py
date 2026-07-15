"""Central config for Step 5 — see ../Account_Tiering/config.py for the pattern."""
import os
from pathlib import Path

from env_utils import load_env

load_env()


def _bool_env(name, default):
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


TEST_MODE = _bool_env("TEST_MODE", True)

STEP_DIR = Path(__file__).resolve().parent

OUTPUT_DIR = STEP_DIR / "output"
LOG_DIR = STEP_DIR / "logs"
CHECKPOINT_DIR = STEP_DIR / "checkpoints"
for _d in (OUTPUT_DIR, LOG_DIR, CHECKPOINT_DIR):
    _d.mkdir(exist_ok=True)

SALESLOFT_BASE_URL = os.environ.get("SALESLOFT_BASE_URL", "https://app.salesloft.com")
SALESLOFT_AUTH_STATE_PATH = Path(
    os.environ.get("SALESLOFT_AUTH_STATE_PATH", "~/.orum_pipeline/salesloft_auth_state.json")
).expanduser()
SALESLOFT_CALL_PAUSE_THRESHOLD = int(os.environ.get("SALESLOFT_CALL_PAUSE_THRESHOLD", "20"))

SALESLOFT_CADENCE_PROD = "Targeted Outreach Cadence 4"
SALESLOFT_CADENCE_TEST = "Targeted Outreach 4 - TEST"

# PLACEHOLDER — the exact step names/numbering in the real "Targeted Outreach 4"
# cadence weren't confirmed (only "step one" -> "the call step" was described).
# Confirm the real step names before running this against a live cadence — a wrong
# guess here could advance people into the wrong step.
CADENCE_FIRST_STEP_NAME = "Step 1"
CADENCE_CALL_STEP_NAME = "Call"


def salesloft_cadence_name():
    # Demo/production cadence is always the real "Targeted Outreach 4" (user
    # requirement 2026-07-10) — never the "- TEST" variant, even in TEST_MODE.
    return SALESLOFT_CADENCE_PROD
