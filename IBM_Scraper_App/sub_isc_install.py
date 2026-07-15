"""IBM Non-Infra Install + Competitive Install sub-scrapers — MOCKED for the
WatsonX Clone.

The real module replayed the ISC CRM-Analytics "Client Install (Territory)" /wave/query
REST calls. Here both files are synthesized from the shared fake-data pool, with
``L1_ACCOUNT_NAME`` set to the exact ISC account name so Account Segmentation's
name-exact join attaches them. Same public entry points (``run_ibm_non_infra`` /
``run_competitive``) + output contract (sheets ``IBM Install`` / ``Competitive
Install``, dated + _latest).
"""
import logging
import sys

import config

sys.path.insert(0, str(config.REPO_ROOT))
import fake_data  # noqa: E402

logger = logging.getLogger("sub_isc_install")


def run_ibm_non_infra(covids=None):
    accounts = fake_data.accounts_for_covids(covids or [])
    headers, rows = fake_data.ibm_non_infra_install(accounts, covids or [])
    dated, latest = config.dated_and_latest_paths("ibm_non_infra")
    fake_data.write_workbook(dated, "IBM Install", headers, rows)
    fake_data.write_workbook(latest, "IBM Install", headers, rows)
    logger.info("IBM Non-Infra Install (mock): %d rows -> %s", len(rows), latest.name)
    return {"total_rows": len(rows), "matched_rows": len(rows), "source": "mock"}


def run_competitive(covids=None):
    accounts = fake_data.accounts_for_covids(covids or [])
    headers, rows = fake_data.competitive_install(accounts, covids or [])
    dated, latest = config.dated_and_latest_paths("competitive")
    fake_data.write_workbook(dated, "Competitive Install", headers, rows)
    fake_data.write_workbook(latest, "Competitive Install", headers, rows)
    logger.info("Competitive Install (mock): %d rows -> %s", len(rows), latest.name)
    return {"total_rows": len(rows), "matched_rows": len(rows), "source": "mock"}
