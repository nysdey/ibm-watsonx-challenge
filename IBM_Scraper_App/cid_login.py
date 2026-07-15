"""Establish/refresh the CID (Client Insights Dashboard) session.

CID (cid.ibm.com) authenticates through IBMid (login.ibm.com), which for IBM
employees federates straight to w3id SSO. So we don't need a fresh passkey
dance: we seed the browser with an already-valid w3id session (the saved gtmnav
or ISC state), navigate to CID, complete the one IBMid "Continue" step, and the
w3id session silently finishes the federation -- landing on the seller
dashboard. The resulting cid.ibm.com cookies are saved to cid_auth_state.json.

If no valid w3id seed exists, run w3id_login_chrome.py first (that establishes a
GTM/w3id session), then this.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from playwright.sync_api import sync_playwright
import login_capture as lc
import w3id_seed

CID_URL = "https://cid.ibm.com"
CID_DASHBOARD = "https://cid.ibm.com/cid/sellerDashboard"
CID_OUT = Path("~/.orum_pipeline/cid_auth_state.json").expanduser()
_LOGIN_MARKERS = ("login.ibm.com", "login.w3.ibm.com", "authsvc", "/authorize", "/authenticate")


def _looks_like_login(url):
    return any(m in (url or "").lower() for m in _LOGIN_MARKERS)


def _on_cid_dashboard(url):
    return "cid.ibm.com" in (url or "") and not _looks_like_login(url)


def session_valid(headless=True):
    """Quick headless probe: does the saved CID session reach the dashboard?"""
    if not CID_OUT.exists():
        return False
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(channel="chrome", headless=headless)
            ctx = b.new_context(storage_state=str(CID_OUT))
            pg = ctx.new_page()
            pg.goto(CID_DASHBOARD, wait_until="domcontentloaded", timeout=45000)
            pg.wait_for_timeout(4000)
            ok = _on_cid_dashboard(pg.url)
            ctx.close(); b.close()
            return ok
    except Exception:
        return False


def _try_seed(p, seed, email, headless):
    """Attempt CID federation from one w3id seed. Returns True (and saves the CID
    state) if it lands on the dashboard, else False so the caller can try the
    next-freshest seed."""
    b = p.chromium.launch(channel="chrome", headless=headless)
    ctx = b.new_context(storage_state=str(seed), locale="en-US",
                        timezone_id="America/Los_Angeles")
    pg = ctx.new_page()
    try:
        pg.goto(CID_URL, wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(6000)
        if "login.ibm.com" in pg.url:
            # IBMid entry: fill the IBMid and Continue; federation to w3id then
            # completes silently thanks to the seeded (live) w3id session.
            for sel in ("#username", "input[name='username']", "input[type='email']"):
                el = pg.query_selector(sel)
                if el and el.is_visible():
                    el.click(); el.fill(email); break
            for sel in ("#continue-button", "button:has-text('Continue')", "button[type='submit']"):
                el = pg.query_selector(sel)
                if el and el.is_visible():
                    el.click(); break
            pg.wait_for_timeout(6000)
        # wait for the federation redirects to settle on cid.ibm.com
        for _ in range(8):
            pg.wait_for_timeout(3000)
            if _on_cid_dashboard(pg.url):
                break
        if not _on_cid_dashboard(pg.url):
            return False
        CID_OUT.parent.mkdir(parents=True, exist_ok=True)
        ctx.storage_state(path=str(CID_OUT))
        return True
    finally:
        ctx.close(); b.close()


def refresh(headless=True):
    """(Re)establish the CID session by seeding from the freshest live w3id
    session on the machine. Tries candidates freshest-first (the ISC state is
    refreshed on every Step-1 run, so it's usually the live one) and falls back
    across them, rather than trusting a single hardcoded — often stale — file."""
    creds = lc.credential_store.get("w3id")
    email = (creds or {}).get("email")
    if not email:
        raise RuntimeError("No w3id credential in Keychain (needed for the IBMid step).")

    seeds = w3id_seed.w3id_seeds_by_freshness()
    if not seeds:
        raise RuntimeError(
            "No w3id seed session found. Run w3id_login_chrome.py first to "
            "establish a GTM/w3id session, then retry."
        )

    with sync_playwright() as p:
        tried = []
        for seed in seeds:
            tried.append(seed.name)
            if _try_seed(p, seed, email, headless):
                return CID_OUT
    raise RuntimeError(
        f"Could not establish CID session from any w3id seed ({', '.join(tried)}). "
        f"All are likely expired -- refresh via w3id_login_chrome.py (or re-run "
        f"Step 1 / ISC login), then retry."
    )


def ensure_session(headless=True):
    """Return a valid CID session path, refreshing it if needed."""
    if session_valid(headless=headless):
        return CID_OUT
    return refresh(headless=headless)


if __name__ == "__main__":
    print("CID session valid?" , session_valid())
    path = ensure_session()
    print("CID session ready ->", path)
