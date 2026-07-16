"""Advance everyone at cadence step 1 into the call step — MOCKED for the BobBee.

The real module drove the Salesloft web UI to bulk-move step-1 members. Here it acts on
the clone's mock Salesloft store (the same one Fill Contacts loaded contacts into), so
the demo's Salesloft view visibly moves people from "Step 1" to "Call" — no browser, no
Salesloft. Same public surface run.py depends on (``SessionExpired`` +
``advance_all_at_step_one`` returning ``(advanced_names, skipped)``).
"""
import logging
import sys

import config

sys.path.insert(0, str(config.STEP_DIR.parent))
import mock_salesloft  # noqa: E402

logger = logging.getLogger("salesloft_advance")


class SessionExpired(Exception):
    """Kept for run.py's except-clause parity; the mock never raises it."""


def advance_all_at_step_one(target_date_str, cadence_name):
    state = mock_salesloft.cadence_state(cadence_name)
    at_step_one = [
        (f"{m.get('first_name', '')} {m.get('last_name', '')}".strip() or m.get("company", "Unknown"))
        for m in state.get("members", []) if m.get("step") == mock_salesloft.FIRST_STEP
    ]
    logger.info("Salesloft (mock): %d member(s) at step 1 of '%s' to advance.",
                len(at_step_one), cadence_name)
    mock_salesloft.advance_step_one(cadence_name)
    logger.info("Advanced %d member(s) into the call step (mock).", len(at_step_one))
    return at_step_one, []
