"""Cloud Install sub-scraper — MOCKED for the BobBee.

The real module replayed the GTM Navigator Revenue Analysis Dash callbacks per CovID.
Here it synthesizes the fixed 8-column Cloud schema from the shared fake-data pool,
keyed so Account Segmentation joins it (Unique Account Key / Global Buying Group ID
carry the account hierarchy code). Same entry point + output contract (sheet
``Cloud Install``, dated + _latest).
"""
import logging
import sys

import config

sys.path.insert(0, str(config.REPO_ROOT))
import fake_data  # noqa: E402

logger = logging.getLogger("sub_cloud")


def run_cloud_install(covids):
    accounts = fake_data.accounts_for_covids(covids)
    headers, rows = fake_data.cloud_install(accounts, covids)
    dated, latest = config.dated_and_latest_paths("cloud")
    fake_data.write_workbook(dated, "Cloud Install", headers, rows)
    fake_data.write_workbook(latest, "Cloud Install", headers, rows)
    logger.info("Cloud Install (mock): %d rows across %d CovIDs -> %s", len(rows), len(covids), latest.name)
    return {"total_rows": len(rows), "matched_rows": len(rows), "source": "mock"}
