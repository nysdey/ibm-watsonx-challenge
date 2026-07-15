"""Pick the freshest usable w3id SSO session on this machine.

Every IBM portal in this step (CID, GTM Navigator, and the ISC install
dashboard) ultimately rides the same **w3id** single-sign-on session. That
session is short-lived (~a workday), but the pipeline refreshes it on *every*
run because Step 1 (ISC) logs in right before Step 2 (IBM Scraper) starts — so
at run time there is almost always a fresh w3id session sitting in the ISC state
file, even when the older CID/GTM state files have gone stale.

The historical bug was seeding CID/GTM from a *hardcoded* state file (gtmnav)
chosen because it merely *exists* on disk — so an 18-hour-old expired gtmnav seed
was used while a 1-hour-old valid ISC seed sat right next to it. This module
returns the candidate w3id session files ordered **freshest first (by mtime)** so
callers can seed from — or fall back across — whichever session is actually live.
"""
from pathlib import Path

# All state files that carry live login.w3.ibm.com SSO cookies, most-commonly
# fresh first is irrelevant — we sort by mtime at call time.
_W3ID_SESSION_FILES = [
    Path("~/.isc_scraper/auth_state.json").expanduser(),        # refreshed every ISC (Step 1) run
    Path("~/.orum_pipeline/gtmnav_auth_state.json").expanduser(),
    Path("~/.orum_pipeline/cid_auth_state.json").expanduser(),
]


def w3id_seeds_by_freshness(extra=None):
    """Existing w3id session files, freshest (most recently written) first.

    `extra` lets a caller prepend portal-specific candidates (e.g. GTM's own
    app-session file) that should be preferred when present.
    """
    candidates = list(extra or []) + _W3ID_SESSION_FILES
    # De-dup while preserving intent, then sort existing ones by mtime desc.
    seen, existing = set(), []
    for p in candidates:
        p = Path(p).expanduser()
        if p in seen:
            continue
        seen.add(p)
        if p.exists():
            existing.append(p)
    existing.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return existing
