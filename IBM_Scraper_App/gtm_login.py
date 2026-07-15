"""Ensure a live GTM Navigator (gtmnav) session, auto-refreshing it unattended.

The GTM Navigator *app* session dies roughly daily, and its re-login normally
hits a w3id passkey wall (login.w3.ibm.com / w3id-ns.sso password-blocked) that a
seeded SSO cookie can't get past. `w3id_login_chrome.py` automates *past* that
wall using the stored w3id password plus a CDP virtual authenticator that makes
Chrome's native passkey picker fail fast — no human passkey tap required. It
seeds from the fresh ISC w3id session and saves gtmnav_auth_state.json.

This module wraps that script the same way `cid_login` wraps the CID refresh:
probe the saved session, and when it's stale run the login script as a
subprocess so the `cloud` sub-scraper refreshes itself unattended instead of
failing. (The refresh opens a visible Chrome window briefly — that's required
for the WebAuthn virtual-authenticator trick; it cannot be fully headless.)
"""
import logging
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

log = logging.getLogger("ibm_scraper.gtm_login")

GTM_OUT = Path("~/.orum_pipeline/gtmnav_auth_state.json").expanduser()
GTM_APP_URL = "https://w3.ibm.com/sales/gtm-navigator/app"
LOGIN_SCRIPT = Path(__file__).resolve().parent / "w3id_login_chrome.py"

# Reaching any of these after loading the app means the session is dead.
_BAD_MARKERS = (
    "/gtm-navigator/login", "login.w3.ibm.com", "login.ibm.com", "w3id-ns.sso",
    "password-blocked", "authsvc", "/authorize", "/authenticate", "idaas",
)


def _session_dead(url):
    return any(m in (url or "") for m in _BAD_MARKERS)


def session_valid(headless=True):
    """Quick probe: does the saved gtmnav session still reach the GTM app?"""
    if not GTM_OUT.exists():
        return False
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(channel="chrome", headless=headless)
            ctx = b.new_context(storage_state=str(GTM_OUT), locale="en-US",
                                timezone_id="America/Los_Angeles")
            pg = ctx.new_page()
            pg.goto(GTM_APP_URL, wait_until="domcontentloaded", timeout=45000)
            pg.wait_for_timeout(4000)
            ok = not _session_dead(pg.url)
            ctx.close(); b.close()
            return ok
    except Exception:
        return False


def refresh(timeout=300):
    """Run w3id_login_chrome.py to (re)establish the gtmnav session unattended."""
    before = GTM_OUT.stat().st_mtime if GTM_OUT.exists() else 0
    log.info("GTM session stale -> refreshing via w3id_login_chrome.py "
             "(opens Chrome; automated w3id password login, no passkey tap)")
    try:
        r = subprocess.run(
            [sys.executable, str(LOGIN_SCRIPT)], cwd=str(LOGIN_SCRIPT.parent),
            timeout=timeout, capture_output=True, text=True,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(
            f"GTM auto-login timed out after {timeout}s. The automated password "
            f"dance stalled — run it by hand to finish: cd IBM_Scraper_App && "
            f"../.venv/bin/python3 w3id_login_chrome.py"
        )
    refreshed = GTM_OUT.exists() and GTM_OUT.stat().st_mtime > before
    if r.returncode != 0 or not refreshed:
        tail = ((r.stdout or "") + (r.stderr or ""))[-400:]
        raise RuntimeError(
            f"GTM auto-login did not establish a session (exit {r.returncode}). "
            f"Retry by hand: ../.venv/bin/python3 w3id_login_chrome.py . "
            f"Last output: ...{tail}"
        )
    log.info("GTM session refreshed -> %s", GTM_OUT)
    return GTM_OUT


def ensure_session(headless=True):
    """Return a valid gtmnav session path, auto-refreshing it if stale."""
    if session_valid(headless=headless):
        log.info("GTM session already valid")
        return GTM_OUT
    return refresh()


if __name__ == "__main__":
    print("GTM session valid?", session_valid())
    print("GTM session ready ->", ensure_session())
