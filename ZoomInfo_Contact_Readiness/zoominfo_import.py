"""ZoomInfo side of Step 6 — MOCKED for the WatsonX Clone.

The real module drove a headless ZoomInfo browser to upload the day's account list,
apply the "Infra Outbound" buyer-group filter, pull the resulting contacts, and fire
ZoomInfo's native Export-to-Salesloft. Here the contacts are synthesized deterministically
from the shared fake-data pool and "exported" into the clone's mock Salesloft store — no
browser, no ZoomInfo, no Salesloft. Same public surface run.py depends on
(``SessionExpired`` + ``import_and_export_to_salesloft`` returning ``(text, raw_contacts)``).
"""
import logging
import sys

import config

sys.path.insert(0, str(config.REPO_ROOT))
import fake_data  # noqa: E402
import mock_salesloft  # noqa: E402

logger = logging.getLogger("zoominfo_import")


class SessionExpired(Exception):
    """Kept for run.py's except-clause parity; the mock never raises it."""


def import_and_export_to_salesloft(target_date_str, account_names, cadence_name):
    """Single-session mock: 'upload' the accounts, apply the buyer group, pull contacts,
    and 'export' them to the Salesloft cadence (into the clone's mock Salesloft store).
    Returns (count_text, raw_contacts) exactly like the real single-browser flow."""
    logger.info("ZoomInfo (mock): uploading %d account(s) as a list, applying '%s' buyer group...",
                len(account_names), config.BUYER_GROUP_NAME)
    contacts = fake_data.contacts_for_accounts(account_names)
    logger.info("ZoomInfo (mock): '%s' buyer group returned %d contact(s).",
                config.BUYER_GROUP_NAME, len(contacts))
    logger.info("Exporting %d contact(s) to Salesloft cadence '%s' (mock native export)...",
                len(contacts), cadence_name)
    total = mock_salesloft.add_people(cadence_name, contacts)
    logger.info("Salesloft cadence '%s' now holds %d member(s) at step 1 (mock).", cadence_name, total)
    return f"{len(contacts)} contacts", contacts


# Kept for API parity with the real module (run.py uses only the combined call above).
def export_to_salesloft(target_date_str, cadence_name):
    return import_and_export_to_salesloft(target_date_str, [], cadence_name)
