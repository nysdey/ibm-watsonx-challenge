"""Central config for Step 4 — see ../Account_Tiering/config.py for the pattern."""
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
STEP3_LATEST = REPO_ROOT / "Call_Planning" / "output" / "latest.xlsx"
STEP2_LATEST = REPO_ROOT / "Account_Tiering" / "output" / "latest.xlsx"

OUTPUT_DIR = STEP_DIR / "output"
LOG_DIR = STEP_DIR / "logs"
CHECKPOINT_DIR = STEP_DIR / "checkpoints"
for _d in (OUTPUT_DIR, LOG_DIR, CHECKPOINT_DIR):
    _d.mkdir(exist_ok=True)

# --- ZoomInfo (browser automation, shared auth convention with Account_Tiering) ---
ZOOMINFO_BASE_URL = os.environ.get("ZOOMINFO_BASE_URL", "https://app.zoominfo.com")
ZOOMINFO_AUTH_STATE_PATH = Path(
    os.environ.get("ZOOMINFO_AUTH_STATE_PATH", "~/.orum_pipeline/zoominfo_auth_state.json")
).expanduser()
ZOOMINFO_CALL_PAUSE_THRESHOLD = int(os.environ.get("ZOOMINFO_CALL_PAUSE_THRESHOLD", "20"))

BUYER_GROUP_NAME = "Infra Outbound"

# PLACEHOLDER — no test-list naming convention was given for the ZoomInfo side (the
# Salesloft test cadence name WAS given explicitly, see SALESLOFT_CADENCE_TEST below).
# Confirm a real naming convention before running Step 4 in TEST_MODE against a real
# ZoomInfo org — a wrong guess here risks the test list colliding with something real.
ZOOMINFO_TEST_LIST_PREFIX = "ORUM Pipeline TEST"

# --- Salesloft cadence names only — the actual transfer happens natively inside
# ZoomInfo's own Export flow (see zoominfo_import.py), so no separate Salesloft
# login/base-URL/rate-cap is needed in this step. ---
SALESLOFT_CADENCE_PROD = "Targeted Outreach Cadence 4"
SALESLOFT_CADENCE_TEST = "Targeted Outreach 4 - TEST"


def salesloft_cadence_name():
    # Demo/production cadence is always the real "Targeted Outreach 4" (user
    # requirement 2026-07-10) — never the "- TEST" variant, even in TEST_MODE.
    return SALESLOFT_CADENCE_PROD


def zoominfo_list_name(target_date):
    # Unique per run (HHMMSS) so ZoomInfo never rejects a duplicate list name.
    import datetime as _dt
    stamp = _dt.datetime.now().strftime("%H%M%S")
    if TEST_MODE:
        return f"{ZOOMINFO_TEST_LIST_PREFIX} {target_date.isoformat()} {stamp}"
    return f"ORUM Daily Import {target_date.isoformat()}"
