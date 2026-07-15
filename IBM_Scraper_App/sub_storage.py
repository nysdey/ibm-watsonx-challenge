"""Storage Install sub-scraper — MOCKED for the WatsonX Clone.

The real module drove the CID Dashboard (cid.ibm.com) to download four storage-family
CSVs and unioned them. Here it synthesizes the same shape (a ``Storage Category`` tag
column + join keys) from the shared fake-data pool. Same public entry point + output
contract (sheet ``Storage Install``, dated + _latest).
"""
import logging
import sys

import config

sys.path.insert(0, str(config.REPO_ROOT))
import fake_data  # noqa: E402

logger = logging.getLogger("sub_storage")


def run_storage_install(covids=None):
    accounts = fake_data.accounts_for_covids(covids or [])
    headers, rows = fake_data.storage_install(accounts, covids or [])
    dated, latest = config.dated_and_latest_paths("storage")
    fake_data.write_workbook(dated, "Storage Install", headers, rows)
    fake_data.write_workbook(latest, "Storage Install", headers, rows)
    logger.info("Storage Install (mock): %d rows -> %s", len(rows), latest.name)
    return {"total_rows": len(rows), "matched_rows": len(rows), "source": "mock"}
