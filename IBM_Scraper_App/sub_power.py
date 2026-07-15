"""Power Install sub-scraper — MOCKED for the WatsonX Clone.

The real module filtered a local monthly POWER_INSTALL_ALL export by CovID. Here it
synthesizes Power install rows from the shared fake-data pool instead, keyed to the
same account hierarchy codes the ISC step produced so Account Segmentation joins them.
Same public entry point + output contract (sheet ``Power Install``, dated + _latest).
"""
import logging
import sys

import config

sys.path.insert(0, str(config.REPO_ROOT))
import fake_data  # noqa: E402

logger = logging.getLogger("sub_power")


def run_power_install(covids, source_path=None):
    accounts = fake_data.accounts_for_covids(covids)
    headers, rows = fake_data.power_install(accounts, covids)
    dated, latest = config.dated_and_latest_paths("power")
    fake_data.write_workbook(dated, "Power Install", headers, rows)
    fake_data.write_workbook(latest, "Power Install", headers, rows)
    logger.info("Power Install (mock): %d rows across %d CovIDs -> %s", len(rows), len(covids), latest.name)
    return {"total_rows": len(rows), "matched_rows": len(rows), "source": "mock"}
