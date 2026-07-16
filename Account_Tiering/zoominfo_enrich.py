"""ZoomInfo enrichment — MOCKED for the BobBee.

The real module drove a headless ZoomInfo browser session to read each account's
revenue + employee count. Here those come from the shared deterministic fake-data
generator instead — no browser, no session, instant. Same public entry point and
output shape (``enrich_accounts(names) -> {name: {ZI_* fields}}``) and the same
per-account checkpoint file, so the rest of Account Tiering is unchanged.
"""
import json
import logging
import sys

import config

sys.path.insert(0, str(config.STEP_DIR.parent))
import fake_data  # noqa: E402

logger = logging.getLogger("zoominfo_enrich")

CHECKPOINT_PATH = config.CHECKPOINT_DIR / "zoominfo_checkpoint.json"


def _load_checkpoint():
    if CHECKPOINT_PATH.exists():
        try:
            return json.loads(CHECKPOINT_PATH.read_text())
        except Exception:
            return {}
    return {}


def _save_checkpoint(state):
    tmp = CHECKPOINT_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2))
    tmp.replace(CHECKPOINT_PATH)


def enrich_accounts(account_names):
    """Resumable batch entry point. Returns {account_name: {ZI_* fields}}. Deterministic
    per name (a re-run yields the identical enrichment), checkpointed so it's instant."""
    state = _load_checkpoint()
    to_process = [n for n in account_names if n not in state]
    for name in to_process:
        state[name] = {"fields": fake_data.zoominfo_enrichment(name)}
        logger.info("%s: %s (mock)", name, state[name]["fields"]["ZI_Match_Status"])
    if to_process:
        _save_checkpoint(state)
    return {n: state[n]["fields"] for n in account_names if n in state}
