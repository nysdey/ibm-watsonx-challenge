"""Shared config for the IBM Scraper step (new Step 2).

The IBM Scraper produces five install-base files scoped to the CovIDs that were
selected in the ISC Scraper step (Step 1):

    STORAGE_INSTALL        (CID Dashboard)         -- browser
    CLOUD_INSTALL          (GTM Navigator)         -- browser
    POWER_INSTALL          (local POWER_INSTALL_ALL) -- pure local filter
    IBM_NON_INFRA_INSTALL  (ISC dashboard)         -- browser
    COMPETITIVE_INSTALL    (ISC dashboard)         -- browser

Every output lands in output/ as both a dated file and an overwritten
<NAME>_latest.xlsx, matching the repo-wide handoff convention in
../SCHEMA_CONTRACT.md.
"""
import os
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent
REPO_ROOT = APP_ROOT.parent
OUTPUT_DIR = APP_ROOT / "output"

# --- Step 1 (ISC) handoff: where selected CovIDs and DEDUPED_ACCOUNTS live ---
ISC_OUTPUT_DIR = REPO_ROOT / "ISC_Scraper_App" / "output"
DEDUPED_ACCOUNTS_PATH = ISC_OUTPUT_DIR / "latest.xlsx"          # DEDUPED_ACCOUNTS
SELECTED_COVIDS_PATH = ISC_OUTPUT_DIR / "selected_covids.json"  # written by launcher on each run

# --- POWER_INSTALL_ALL: the monthly all-territories power install-base export ---
# User-specific, monthly-dated file (e.g. "AMR Jan 2026 Install Base US Select.xlsx").
# Override with env POWER_INSTALL_ALL_PATH; otherwise the default below is used.
POWER_INSTALL_ALL_PATH = Path(
    os.environ.get(
        "POWER_INSTALL_ALL_PATH",
        "/Users/timzhou/Desktop/Tim Zhou 2026/Install Base/Power/AMR Jan 2026 Install Base US Select.xlsx",
    )
).expanduser()

# The Power file's own layout (verified against the real Jan-2026 export):
POWER_DATA_SHEET = "Data"
POWER_COVID_COLUMN_LETTER = "DQ"        # header: "local coverage type id"
POWER_COVID_HEADER = "local coverage type id"

# Output file base names (per the new architecture contract).
OUTPUT_NAMES = {
    "storage": "STORAGE_INSTALL",
    "cloud": "CLOUD_INSTALL",
    "power": "POWER_INSTALL",
    "ibm_non_infra": "IBM_NON_INFRA_INSTALL",
    "competitive": "COMPETITIVE_INSTALL",
}


def dated_and_latest_paths(key):
    """(dated_path, latest_path) for a given sub-scraper key."""
    from datetime import datetime
    name = OUTPUT_NAMES[key]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dated = OUTPUT_DIR / f"{name}_{datetime.now():%Y%m%d}.xlsx"
    latest = OUTPUT_DIR / f"{name}_latest.xlsx"
    return dated, latest
