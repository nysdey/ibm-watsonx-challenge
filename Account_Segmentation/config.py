"""Config for Account Segmentation (runs after IBM Scraper, before Account Tiering).

Base = DEDUPED_ACCOUNTS (ISC step). The five IBM install files are joined onto it
by a DETERMINISTIC IBM account key (client/buying-group hierarchy code, then IBM
customer number, then same-system exact name) -- not fuzzy name matching, which
was unreliable because the same account is spelled differently across IBM's
source systems. See id_match.py. The result is sorted by how many install types
each account has and written as SEGMENTED_ACCOUNTS.
"""
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent
REPO_ROOT = APP_ROOT.parent
OUTPUT_DIR = APP_ROOT / "output"

# --- Base: DEDUPED_ACCOUNTS from the ISC step ---
DEDUPED_ACCOUNTS_PATH = REPO_ROOT / "ISC_Scraper_App" / "output" / "latest.xlsx"
BASE_NAME_COLUMN = "Account Name"   # the identity column in DEDUPED_ACCOUNTS
# The IBM account/buying-group hierarchy code (DC…/DB…) the ISC step now keeps on
# each rolled-up account -- the primary deterministic join key.
BASE_ACCOUNT_KEY_COLUMN = "Account Number"
# customer-number -> account-key crosswalk the ISC dedup writes next to latest.xlsx
# (bridges Cloud / ISM / Competitive rows that carry an IBM customer number but a
# differently-spelled name). Absent => id-join falls back to code + exact name only.
ACCOUNT_CROSSWALK_PATH = REPO_ROOT / "ISC_Scraper_App" / "output" / "account_crosswalk.json"

_IBM_OUT = REPO_ROOT / "IBM_Scraper_App" / "output"

# Install types in TIE-BREAK PRIORITY ORDER (Cloud -> Power -> Storage ->
# Non-Infra -> Competitive). This order drives both the sort and the column
# layout. Each: key, human label, install-file path.
INSTALL_TYPES = [
    ("cloud",         "Cloud",       _IBM_OUT / "CLOUD_INSTALL_latest.xlsx"),
    ("power",         "Power",       _IBM_OUT / "POWER_INSTALL_latest.xlsx"),
    ("storage",       "Storage",     _IBM_OUT / "STORAGE_INSTALL_latest.xlsx"),
    ("ibm_non_infra", "NonInfra",    _IBM_OUT / "IBM_NON_INFRA_INSTALL_latest.xlsx"),
    ("competitive",   "Competitive", _IBM_OUT / "COMPETITIVE_INSTALL_latest.xlsx"),
]

# --- Deterministic id-join spec, per install type ---
# For each install file, which columns carry:
#   codes: IBM client/buying-group hierarchy codes (GC…/DC…/GB…/DB…). Matched
#          directly against the account key set. For Cloud the code is the prefix
#          of "Unique Account Key" (GC…-<covid>-…), handled by the extractor.
#   custs: IBM customer / CMR numbers, matched via the crosswalk (normalized:
#          numeric part before any country-code suffix, leading zeros dropped).
#   names: account-name columns whose spelling is authoritative (same ISC/
#          Salesforce system as the base) -> exact normalized-name match.
ID_COLUMNS = {
    "cloud": {
        "codes": ["Unique Account Key", "Global Buying Group ID"],
        "custs": ["IBM Customer Number with Country Code"],
        "names": ["Account Name"],
    },
    "power": {
        "codes": ["global client id", "domestic client id",
                  "global buying group id", "domestic buying group id"],
        "custs": ["Customer Number", "SAP CUST Number"],
        "names": [],
    },
    "storage": {
        "codes": ["gbl_client_id", "dom_client_id", "gbl_buy_grp_id", "dom_buy_grp_id"],
        "custs": ["cust_no", "updated_cust_no"],
        "names": [],
    },
    "ibm_non_infra": {
        "codes": [],
        "custs": ["CUST_NO"],
        "names": ["L1_ACCOUNT_NAME"],   # same ISC system as base -> exact
    },
    "competitive": {
        "codes": [],
        "custs": ["CUST_NO"],
        "names": ["L1_ACCOUNT_NAME"],
    },
}

# Optional per-file override of the account-name column, used only by the legacy
# fuzzy fallback (when no id-join key is available). Keyed by install type key.
NAME_COLUMN_OVERRIDES = {
    # "power": "Primary Customer Name",
    # "ibm_non_infra": "Parent Account",
}

# Auto-detect name-column preference (first matching header wins, case-insensitive
# substring). Tuned for the five files' real headers.
NAME_COLUMN_PREFERENCE = [
    "parent account", "primary customer name", "account name", "customer name",
    "client name", "company name", "top-of-tree name", "account", "customer", "name",
]

# Attach every column from each install file (aggregated per account) in
# addition to the compact presence/count/score columns. Per the spec ("that
# account will get as many columns as the storage excel, as well as cloud,
# power..."). Set False for a compact output (presence/count/score only).
ATTACH_INSTALL_COLUMNS = True

# When an account matches multiple rows in an install file, text columns are
# joined (distinct, capped) and numeric columns summed. Cap for joined text.
MAX_JOINED_TEXT_LEN = 300

OUTPUT_BASENAME = "SEGMENTED_ACCOUNTS"


def dated_and_latest_paths():
    from datetime import datetime
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dated = OUTPUT_DIR / f"{OUTPUT_BASENAME}_{datetime.now():%Y%m%d}.xlsx"
    latest = OUTPUT_DIR / "latest.xlsx"
    return dated, latest
