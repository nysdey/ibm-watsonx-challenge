"""Generalized login-capture tool for all 3 services this pipeline touches:
ISC (Salesforce), ZoomInfo, Salesloft. All three use SSO + MFA, which cannot be
scripted — a human has to be physically present to approve it. This launches a
*visible* Firefox window, lets the user log in normally, then saves the
session (Playwright storage_state) to the same file each step's own script
already reads.

    python3 login_capture.py isc|zoominfo|salesloft [control_dir]

Driven by control files (polled every 2s) rather than requiring a
keyboard/mouse handoff, since the caller (run_pipeline.py) has no way to
listen for a keypress in this separate process:
  <control_dir>/SAVE_<service>   -> save storage_state and exit cleanly
  <control_dir>/RELOAD_<service> -> page.reload(), then cleared

Status is written continuously to <control_dir>/login_status_<service>.json
so a caller can poll it (current URL + elapsed time) without needing to
screenshot.

This is the same pattern used ad-hoc mid-session on 2026-07-05 for ZoomInfo/
Salesloft; generalized here (added ISC, made it a first-class repo file
instead of a scratchpad throwaway) so a fresh computer's first run can drive
all 3 logins consistently from the dashboard.
"""
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault(
    "PLAYWRIGHT_BROWSERS_PATH",
    str(Path.home() / "Library" / "Caches" / "ms-playwright"),
)
from playwright.sync_api import sync_playwright

import shared_auth

# The shared enforcement layer (origin-gated password fills, URL redaction, and
# atomic validity-guarded session saves). login_capture runs at REPO_ROOT so the
# plain import works; wrapped so the tool still runs if shared_auth is missing.
try:
    from shared_auth import guard
except Exception:  # pragma: no cover
    guard = None

# The per-service capture config (base URL, session file path, valid host) comes
# straight from the shared registry (shared_auth/registry.py) — the ONE place that
# describes every site the platform logs into. This file adds the login *mechanics*
# (the W3ID/Microsoft SSO state machine below); the registry owns the "what/where".
# Includes `outlook`, so the Meetings tab's calendar session is captured through the
# very same dashboard login flow as ISC/ZoomInfo/Salesloft — no separate login.
SERVICES = {
    svc: {
        "base_url": cfg["base_url"],
        "auth_path": shared_auth.state_path(svc),
        "valid_host": cfg["valid_host"],
    }
    for svc, cfg in shared_auth.SERVICES.items()
}

# Any final-URL host/path containing one of these means we landed on a login /
# SSO page, i.e. the saved session is dead. Verified against real expired ISC/
# ZoomInfo sessions (both bounce to login.w3.ibm.com/authsvc) and a real
# expired Salesloft (accounts.salesloft.com/sign_in) on 2026-07-06.
LOGIN_URL_MARKERS = (
    "login.w3.ibm.com", "login.ibm.com", "w3id",
    "accounts.salesloft.com", "sign_in", "signin",
    "login.zoominfo.com", "okta",
    "authsvc", "idaas", "/authorize", "/authenticate",
    # IBM consumer login portal (GTM Navigator entry point)
    "login.ibm.com/authsvc",
    # Microsoft 365 sign-in (Outlook, IBM tenant) before it federates to W3ID.
    "login.microsoftonline.com", "login.microsoft.com", "login.live.com",
    "microsoftonline", "/owa/auth",
)

POLL_INTERVAL_SECONDS = 2
TIMEOUT_SECONDS = 900
# Probe: poll the page URL every 500ms until it stabilises (stops changing)
# for two consecutive polls, or until this hard cap is hit. Much faster than
# a fixed sleep for sessions that are already valid (they settle in ~1s) while
# still handling the slow IBM SSO redirect chains (~3-4s) correctly.
PROBE_SETTLE_MAX_MS = 8000
PROBE_POLL_MS = 500


def _looks_like_login(url):
    u = (url or "").lower()
    return any(m in u for m in LOGIN_URL_MARKERS)


def probe_service(service):
    """Headless-navigate to the service with its saved session and report
    whether the session is still valid. Returns one of:
      'valid'   — landed on the authenticated app
      'expired' — bounced to a login/SSO page
      'missing' — no saved session file at all
      'error'   — navigation failed (network/browser problem, unknown)
    Pure function of on-disk state; makes no changes. Isolated in its own
    process (invoked as `login_capture.py probe <service>`) so a browser
    crash never takes down the dashboard that calls it.

    Uses URL-stabilisation polling instead of a fixed sleep: polls every
    PROBE_POLL_MS until the URL hasn't changed for 2 consecutive polls, up
    to PROBE_SETTLE_MAX_MS. Valid sessions settle in ~1s; expired ones that
    redirect through IBM SSO settle in ~3-4s. Much faster than a fixed 6s."""
    cfg = SERVICES[service]
    if not cfg["auth_path"].exists():
        return "missing", None
    try:
        state = json.loads(cfg["auth_path"].read_text())
    except Exception:
        return "error", None
    try:
        with sync_playwright() as p:
            browser = p.firefox.launch(headless=True)
            try:
                ctx = browser.new_context(storage_state=state)
                page = ctx.new_page()
                try:
                    page.goto(cfg["base_url"], wait_until="domcontentloaded", timeout=20000)
                except Exception:
                    return "error", None
                # Poll until URL stabilises (2 identical consecutive reads)
                prev_url, stable = "", 0
                elapsed = 0
                while elapsed < PROBE_SETTLE_MAX_MS:
                    cur = page.url
                    if cur == prev_url:
                        stable += 1
                        if stable >= 2:
                            break
                    else:
                        stable = 0
                    prev_url = cur
                    page.wait_for_timeout(PROBE_POLL_MS)
                    elapsed += PROBE_POLL_MS
                final = page.url
            finally:
                browser.close()
    except Exception:
        return "error", None
    if _looks_like_login(final):
        return "expired", final
    if cfg["valid_host"] in (final or ""):
        return "valid", final
    return "expired", final


# ── W3ID / SSO auto-fill ─────────────────────────────────────────────────────
# Credential lookup is optional — auto-fill only kicks in if a password was
# saved via the dashboard's Save Passwords form. Imported lazily so this file
# still runs (manual login) even if credential_store has an issue.
try:
    import credential_store
except Exception:  # pragma: no cover
    credential_store = None

# Selector candidates for each step of the IBM W3ID password flow. Kept here as
# lists so the whole thing can be re-calibrated in ONE place after watching a
# real login — every enterprise SSO page differs slightly and these are the
# best-effort starting guesses, tried in order until one matches.
# Verified against live IBM W3ID page (2026-07-08):
#   email field:    input[type="email"] name="username" id="user-name-input"
#                   placeholder="IBM email address (e.g. jdoe@ibm.com)"
#   password field: input[type="password"] id="password-input"
#   submit button:  button#login-button  text="Sign in"
# ZoomInfo uses its own plain form with similar structure.
_USERNAME_SELECTORS = [
    "input#user-name-input",                        # IBM W3ID (verified live)
    "input[placeholder*='IBM email']",
    "input[placeholder*='email address']",
    "input[type='email']",
    "input#username", "input[name='username']",
    "input[name='j_username']",
    "input[autocomplete='username']",
    "input[placeholder*='sername']",
]
_PASSWORD_SELECTORS = [
    "input#password-input",                         # IBM W3ID (verified live)
    "input#password", "input[name='password']",
    "input[name='j_password']",
    "input[type='password']",
    "input[autocomplete='current-password']",
]
_CONTINUE_TEXTS = ["Sign in", "Log in", "Login", "Continue", "Next", "Submit"]
# The W3ID method chooser sometimes appears ("Choose a Single-Sign On method")
# — always take the password path. Also used if it reappears after back-nav.
_PASSWORD_METHOD_TEXTS = ["w3id Password", "w3id password"]
# The passkey nag appears as inline text on the SAME page as the login fields
# (verified live 2026-07-08 — it is NOT a separate page). After submitting
# credentials successfully, the page may also show a passkey-setup prompt
# before landing on the app. The bypass link text is "sign in methods"
# (id="back-button", live-verified), not "View other sign in methods".
_ENABLE_PASSWORD_TEXTS = [
    "Click here", "continue using your password", "password for the next 4 hours",
    "continue with password", "use password",
]
# "View other sign in methods" link — live page (2026-07-08) renders this as
# partial text "sign in methods" (id="back-button"). The state machine tries
# the id selector directly first; these text variants are text-match fallbacks
# for _try_click_text (do NOT put a raw CSS selector string here).
_OTHER_OPTIONS_TEXTS = [
    "sign in methods",
    "View other sign in methods", "other sign in methods",
    "log in via a different option", "different option", "other ways to log in",
]


def _try_fill(page, selectors, value, log, what):
    for sel in selectors:
        try:
            el = page.query_selector(sel)
            if el and el.is_visible():
                el.click()
                el.fill("")
                el.fill(value)
                log(f"  filled {what} via {sel}")
                return True
        except Exception:
            continue
    log(f"  could NOT find {what} field (tried {len(selectors)} selectors) — leaving for human")
    return False


def _fill_password_gated(page, password, log):
    """Fill the W3ID password ONLY if the current origin is an allowlisted SSO
    origin (guard.login_origin_allowed — exact scheme+host, not a substring). On a
    lookalike / open-redirect landing page the secret is refused and only a log
    line is emitted (spec I7/I29). Falls back to filling if the guard is
    unavailable, so a standalone run still works."""
    if guard is not None and not guard.login_origin_allowed(page.url):
        try:
            shown = guard.redact_url(page.url)
        except Exception:
            shown = "<url>"
        log(f"  refusing to type password on non-SSO origin {shown} — skipping password fill")
        return False
    return _try_fill(page, _PASSWORD_SELECTORS, password, log, "password")


def _try_click_text(page, texts, log, what, timeout_each=1500):
    for t in texts:
        # case-insensitive text match on buttons/links
        for sel in (f"button:has-text(\"{t}\")", f"a:has-text(\"{t}\")",
                    f"[role=button]:has-text(\"{t}\")", f"text=/{t}/i"):
            try:
                el = page.wait_for_selector(sel, timeout=timeout_each, state="visible")
                if el:
                    el.click()
                    log(f"  clicked {what} ('{t}')")
                    return True
            except Exception:
                continue
    log(f"  could NOT find {what} button (tried {len(texts)} labels) — leaving for human")
    return False


def _submit(page, log):
    if _try_click_text(page, _CONTINUE_TEXTS, log, "continue/submit"):
        return True
    try:
        page.keyboard.press("Enter")
        log("  pressed Enter to submit")
        return True
    except Exception:
        return False


def _find_visible(page, selectors):
    for sel in selectors:
        try:
            el = page.query_selector(sel)
            if el and el.is_visible():
                return el
        except Exception:
            continue
    return None


def _page_has_text(page, needle):
    try:
        return needle.lower() in (page.inner_text("body") or "").lower()
    except Exception:
        return False


def attempt_login_autofill(page, service, log):
    """Automates the IBM W3ID password login flow as a page-by-page state
    machine. The exact flow (verified from live screenshots + DOM inspection
    2026-07-08):

      Step A — Method chooser (url: login.w3.ibm.com/idaas/...)
               "Sign in with w3id / Choose a Single-Sign On method"
               → click div#credsDiv ("w3id Password")

      Step B — Login page (url: login.w3.ibm.com/authsvc/...)
               Fields: #user-name-input (email), #password-input (password)
               → fill both → click button#login-button ("Sign in")

      Step C — Password-blocked page (url: w3id-ns.sso.ibm.com/pages/password-blocked.html)
               "Your use of a password to log in has been blocked."
               Link: a:text("Click here") href="#"
               → click "Click here"

      Step D — Browser BACK (no button click — literal browser history back)
               → returns to the login page (Step B's URL)

      Step E — Login page again, now with "View other sign in methods" link
               Link: a#back-button text "sign in methods"
               → click it

      Step F — Method chooser again (same as Step A)
               → click div#credsDiv ("w3id Password") again

      Step G — Login page final time
               → fill both fields → click Sign in → lands on app ✓

    ZoomInfo uses its own plain login form (no method chooser, no passkey
    dance) — it's also a combined email+password page, handled by Step B's
    branch.

    Runs in the VISIBLE window so the human can finish by hand if anything
    stalls. The poll loop in main() auto-saves once the app is reached.
    Watch the [service] log lines to trace each decision.
    """
    if credential_store is None:
        log("  autofill: credential_store unavailable — skipping, log in manually")
        return
    key = shared_auth.credential_key(service)
    creds = credential_store.get(key)
    if not creds or not creds.get("email") or not creds.get("password"):
        log(f"  autofill: no saved credentials for '{key}' — log in manually (or use Save Passwords)")
        return
    email, password = creds["email"], creds["password"]
    valid_host = cfg_valid_host(service)
    log(f"  autofill: starting W3ID flow for '{key}'")

    passkey_workaround_done = False
    fills_done = 0

    for step in range(20):
        try:
            url = page.url
        except Exception:
            break

        # ── Success ──────────────────────────────────────────────────────────
        if valid_host and valid_host in url and not _looks_like_login(url):
            log("  autofill: reached the authenticated app ✓")
            return

        # ── Step MS: Microsoft 365 sign-in (Outlook, IBM tenant) ─────────────
        # URL: login.microsoftonline.com / login.live.com. Outlook is on IBM's
        # Microsoft 365 tenant, which federates to IBM W3ID — but Microsoft asks
        # for the email FIRST (its own page, field name="loginfmt" / #i0116). Fill
        # it and click Next; Microsoft then redirects into login.w3.ibm.com, after
        # which the normal W3ID method-chooser → password-blocked dance takes over.
        if ("login.microsoftonline.com" in url or "login.live.com" in url
                or "login.microsoft.com" in url):
            # If Microsoft shows a "Pick an account" tile for this email, take it.
            try:
                tile = page.query_selector(f"div[data-test-id='{email}'], "
                                           f"div[role='button']:has-text('{email}')")
                if tile and tile.is_visible():
                    tile.click()
                    log(f"  step {step}: Microsoft — picked existing account tile")
                    page.wait_for_timeout(1800)
                    continue
            except Exception:
                pass
            ms_el = None
            for sel in ("input[name='loginfmt']", "#i0116", "input[type='email']"):
                try:
                    el = page.query_selector(sel)
                    if el and el.is_visible():
                        ms_el = el
                        break
                except Exception:
                    pass
            if ms_el:
                try:
                    ms_el.click()
                    ms_el.fill("")
                    ms_el.fill(email)
                    log(f"  step {step}: Microsoft sign-in — filled email, clicking Next")
                    nxt = page.query_selector("#idSIButton9, input[type='submit'], "
                                              "button:has-text('Next')")
                    if nxt and nxt.is_visible():
                        nxt.click()
                    else:
                        page.keyboard.press("Enter")
                    page.wait_for_timeout(2200)
                except Exception as e:
                    log(f"  step {step}: Microsoft email fill raised: {e}")
            else:
                # No email field — likely the "Stay signed in?" (KMSI) prompt or
                # another interstitial. Click its primary button to proceed (clicking
                # "Yes" on KMSI also makes the captured session persistent).
                clicked = False
                for sel in ("#idSIButton9", "input[type='submit']",
                            "button:has-text('Yes')", "button:has-text('Continue')"):
                    try:
                        el = page.query_selector(sel)
                        if el and el.is_visible():
                            el.click()
                            clicked = True
                            log(f"  step {step}: Microsoft interstitial — clicked primary button")
                            break
                    except Exception:
                        pass
                if not clicked:
                    log(f"  step {step}: Microsoft page, no field/button matched — waiting")
                page.wait_for_timeout(1600 if clicked else 1200)
            continue

        # ── Step Y: IBM consumer login (login.ibm.com) ───────────────────────
        # GTM Navigator and some other services redirect to login.ibm.com
        # (NOT login.w3.ibm.com) — a plain "Log in to IBM" page with just an
        # IBMid email field + Continue button. Fill email → click Continue →
        # redirects into w3id SSO, after which the normal flow takes over.
        # Confirmed live 2026-07-09 (screenshot from user).
        if "login.ibm.com" in url and "login.w3.ibm.com" not in url:
            ibmid_el = None
            for sel in ("input[name='username']", "input[type='email']",
                        "input[placeholder*='IBMid']", "input[placeholder*='email']",
                        "#username"):
                try:
                    el = page.query_selector(sel)
                    if el and el.is_visible():
                        ibmid_el = el
                        break
                except Exception:
                    pass
            if ibmid_el:
                try:
                    ibmid_el.click()
                    ibmid_el.fill("")
                    ibmid_el.fill(email)
                    log(f"  step {step}: IBM login — filled IBMid email, clicking Continue")
                    # Button is labelled "Continue" with an arrow
                    cont = page.query_selector("button:has-text('Continue')")
                    if cont and cont.is_visible():
                        cont.click()
                    else:
                        page.keyboard.press("Enter")
                    page.wait_for_timeout(2000)
                except Exception as e:
                    log(f"  step {step}: IBM login fill raised: {e}")
            else:
                log(f"  step {step}: IBM login page but no email field found — waiting")
                page.wait_for_timeout(1500)
            continue

        # ── Step Z: ZoomInfo SSO entry point ─────────────────────────────────
        # URL: login.zoominfo.com — ZoomInfo's own login page (NOT an IBM page).
        # login.zoominfo.com is in LOGIN_URL_MARKERS (so _looks_like_login is
        # True here), but we still need to act on it — click button#sso-btn
        # ("Single Sign-On (SSO)") which redirects into IBM W3ID, after which
        # the method chooser → password-blocked dance proceeds exactly like ISC.
        if "login.zoominfo.com" in url:
            sso_el = None
            for sel in ("#sso-btn", "button[id='sso-btn']"):
                try:
                    el = page.query_selector(sel)
                    if el and el.is_visible():
                        sso_el = el
                        break
                except Exception:
                    pass
            if sso_el:
                log(f"  step {step}: ZoomInfo login — clicking 'Single Sign-On (SSO)' (#sso-btn)")
                sso_el.click()
                page.wait_for_timeout(1500)
                continue

        # ── Step C: password-blocked page ────────────────────────────────────
        # URL: w3id-ns.sso.ibm.com/pages/password-blocked.html
        # "No time to set up a passkey right now? Click here to continue..."
        # The "Click here" link has href="#" — click it, then browser BACK.
        if "password-blocked" in url and not passkey_workaround_done:
            log(f"  step {step}: password-blocked — clicking 'Click here'")
            try:
                el = page.query_selector("a[href='#']")
                if el and el.is_visible():
                    el.click()
                    log("  clicked 'Click here' (keep password 4h)")
                else:
                    _try_click_text(page, _ENABLE_PASSWORD_TEXTS, log, "'Click here'", timeout_each=1000)
            except Exception as e:
                log(f"  'Click here' raised: {e}")
                _try_click_text(page, _ENABLE_PASSWORD_TEXTS, log, "'Click here'", timeout_each=1000)
            page.wait_for_timeout(800)
            # ── Step D: browser BACK ─────────────────────────────────────────
            log(f"  step {step}: browser BACK")
            try:
                page.go_back(wait_until="domcontentloaded", timeout=8000)
                page.wait_for_timeout(1000)
                log(f"  after BACK: {page.url[:80]}")
            except Exception as e:
                log(f"  go_back() failed ({e})")
            continue

        # ── Step E: back on login page — click "sign in methods" ─────────────
        # After BACK we're on the authsvc login page. There are TWO #back-button
        # links: the first says "sign-in with your passkey" (DON'T click that),
        # the second says "sign in methods" (click that). Query ALL and pick the
        # one whose text contains "sign in methods", not "passkey".
        if fills_done >= 1 and not passkey_workaround_done:
            log(f"  step {step}: looking for 'sign in methods' link (not the passkey one)")
            all_back = page.query_selector_all("#back-button, [id='back-button']")
            clicked = False
            for el in all_back:
                try:
                    txt = (el.inner_text() or "").lower()
                    if el.is_visible() and "sign in methods" in txt and "passkey" not in txt:
                        el.click()
                        log("  clicked 'sign in methods' link")
                        clicked = True
                        passkey_workaround_done = True
                        page.wait_for_timeout(1000)
                        break
                except Exception:
                    pass
            if not clicked:
                # Text-match fallback — same guard: avoid anything saying "passkey"
                for t in _OTHER_OPTIONS_TEXTS:
                    for sel in (f'a:has-text("{t}")', f'[role=button]:has-text("{t}")'):
                        try:
                            el = page.wait_for_selector(sel, timeout=800, state="visible")
                            if el and "passkey" not in (el.inner_text() or "").lower():
                                el.click()
                                log(f"  clicked sign-in-methods via text '{t}'")
                                clicked = True
                                passkey_workaround_done = True
                                page.wait_for_timeout(1000)
                                break
                        except Exception:
                            pass
                    if clicked:
                        break
            if clicked:
                continue

        # ── Step A / Step F: method chooser ──────────────────────────────────
        # URL: login.w3.ibm.com/idaas/...  "Choose a Single-Sign On method"
        # div#credsDiv = "w3id Password". Do NOT click #fido (passkey).
        if _page_has_text(page, "Single-Sign On method") or _page_has_text(page, "Choose a Single-Sign"):
            log(f"  step {step}: method chooser — clicking 'w3id Password' (#credsDiv)")
            clicked = False
            for sel in ("#credsDiv", "[id='credsDiv']"):
                try:
                    el = page.query_selector(sel)
                    if el and el.is_visible():
                        el.click()
                        clicked = True
                        log("  clicked #credsDiv")
                        break
                except Exception:
                    pass
            if not clicked:
                _try_click_text(page, _PASSWORD_METHOD_TEXTS, log, "w3id Password", timeout_each=1000)
            page.wait_for_timeout(1200)
            continue

        # ── Step B / Step G: login form ───────────────────────────────────────
        # Fields #user-name-input + #password-input, button #login-button.
        pw_el = _find_visible(page, _PASSWORD_SELECTORS)
        user_el = _find_visible(page, _USERNAME_SELECTORS)
        # Circuit breaker (spec I15): the password has already been submitted
        # twice and we're STILL on a login form → the saved W3ID password is
        # likely outdated. Stop retrying so we don't drive it into a lockout.
        if pw_el and fills_done >= 2:
            log("  saved W3ID password may be outdated — update it in Details")
            return
        if user_el and pw_el:
            log(f"  step {step}: login form fill #{fills_done + 1}")
            _try_fill(page, _USERNAME_SELECTORS, email, log, "email")
            _fill_password_gated(page, password, log)
            submitted = False
            for sel in ("#login-button", "button[id='login-button']"):
                try:
                    el = page.query_selector(sel)
                    if el and el.is_visible():
                        el.click()
                        log("  clicked #login-button")
                        submitted = True
                        break
                except Exception:
                    pass
            if not submitted:
                _submit(page, log)
            fills_done += 1
            page.wait_for_timeout(2500)
            continue

        if pw_el:
            _fill_password_gated(page, password, log)
            _submit(page, log)
            fills_done += 1
            page.wait_for_timeout(2000)
            continue

        if user_el:
            _try_fill(page, _USERNAME_SELECTORS, email, log, "email")
            _submit(page, log)
            page.wait_for_timeout(1500)
            continue

        # Unrecognised page — wait for redirect to settle.
        log(f"  autofill: step {step}: waiting on {url[:80]}")
        page.wait_for_timeout(1200)

    log("  autofill: flow complete"
        + (" (passkey workaround ran)" if passkey_workaround_done else "")
        + " — if not logged in, finish manually; it auto-saves once you reach the app.")


def cfg_valid_host(service):
    return SERVICES.get(service, {}).get("valid_host")


_PROBE_EXIT = {"valid": 0, "expired": 2, "missing": 3, "error": 4}


def main():
    # `probe` mode: report saved-session validity and exit (used by the
    # dashboard's background login-status validator). Prints a one-line JSON
    # result and exits with a per-status code so the caller can read either.
    if len(sys.argv) >= 3 and sys.argv[1] == "probe" and sys.argv[2] in SERVICES:
        service = sys.argv[2]
        status, final = probe_service(service)
        print(json.dumps({"service": service, "status": status, "final_url": final}), flush=True)
        sys.exit(_PROBE_EXIT.get(status, 4))

    if len(sys.argv) < 2 or sys.argv[1] not in SERVICES:
        print(f"Usage: {sys.argv[0]} {'|'.join(SERVICES)} [control_dir]   |   {sys.argv[0]} probe <service>", flush=True)
        sys.exit(1)

    service = sys.argv[1]
    control_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parent / ".orum_login_control"
    control_dir.mkdir(parents=True, exist_ok=True)
    cfg = SERVICES[service]
    log = lambda msg: print(f"[{service}] {msg}", flush=True)

    status_path = control_dir / f"login_status_{service}.json"
    save_signal_path = control_dir / f"SAVE_{service}"
    reload_signal_path = control_dir / f"RELOAD_{service}"
    for p in (save_signal_path, reload_signal_path):
        p.unlink(missing_ok=True)

    def write_status(**kw):
        # Redact any URL before it is PERSISTED to the status JSON — SSO redirect
        # URLs carry SAMLResponse / auth codes / tokens in the query string (spec
        # I64). The poll loop's own valid_host/_looks_like_login logic still runs
        # on the real page.url; only what lands on disk is redacted.
        if guard is not None and kw.get("url"):
            try:
                kw["url"] = guard.redact_url(kw["url"])
            except Exception:
                pass
        status_path.write_text(json.dumps(kw))

    log(f"launching visible Firefox -> {cfg['base_url']}")
    write_status(state="launching", url=cfg["base_url"], elapsed=0)

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        context = browser.new_context(locale="en-US", timezone_id="America/Los_Angeles")
        page = context.new_page()
        page.goto(cfg["base_url"])
        log(f"watching. Control files in {control_dir}: SAVE_{service} to save+exit, RELOAD_{service} to reload.")

        # If the page lands on a login/SSO screen and credentials are saved,
        # take one shot at auto-filling it (the W3ID passkey dance). Done once,
        # up front, in this visible window — if it stalls, the human finishes
        # by hand and clicks Confirm. Never fatal.
        try:
            page.wait_for_timeout(1500)  # let the initial redirect settle
            if _looks_like_login(page.url):
                attempt_login_autofill(page, service, log)
            else:
                log("  already authenticated / not on a login page — no autofill needed")
        except Exception as e:
            log(f"  autofill raised (continuing, finish manually if needed): {e}")

        def save_and_exit(why, cur_url):
            log(f"{why} — saving session.")
            cfg["auth_path"].parent.mkdir(parents=True, exist_ok=True)
            # Atomic + validity-guarded write (spec I18/I19): tmp+os.replace, 0600,
            # and REFUSE to persist a logged-out/bounced session over a good one —
            # pass the live page.url so a save while still on a login page is skipped.
            if guard is not None:
                saved = guard.atomic_save_state(service, context, final_url=page.url)
            else:
                context.storage_state(path=str(cfg["auth_path"]))
                saved = True
            save_signal_path.unlink(missing_ok=True)
            write_status(state="saved", url=cur_url, elapsed=elapsed)
            log(f"SAVED session to {cfg['auth_path']}" if saved
                else "NOT saved — page was not on the authenticated app (logged-out session refused)")
            browser.close()
            log("DONE")

        elapsed = 0
        authed_polls = 0  # consecutive polls sitting on the authenticated app
        while elapsed < TIMEOUT_SECONDS:
            if page.is_closed():
                log("STOPPED: page was closed. Nothing saved.")
                write_status(state="stopped", url=None, elapsed=elapsed)
                sys.exit(3)
            try:
                cur_url = page.url
                write_status(state="waiting", url=cur_url, elapsed=elapsed)
            except Exception as e:
                log(f"STOPPED: couldn't read page state ({e}).")
                write_status(state="stopped", url=None, elapsed=elapsed)
                sys.exit(3)

            if reload_signal_path.exists():
                reload_signal_path.unlink(missing_ok=True)
                log("reload signal received — reloading.")
                try:
                    page.reload(wait_until="networkidle", timeout=30000)
                except Exception as e:
                    log(f"reload raised (may still be fine): {e}")

            if save_signal_path.exists():
                save_and_exit("save signal received", cur_url)
                return

            # Auto-save once we've landed on the authenticated app and stayed
            # there for two consecutive polls (~4s) — this is what makes an
            # auto-login finish on its own, with no Confirm click. The
            # stability check avoids saving mid-redirect during the SSO bounce.
            vh = cfg.get("valid_host")
            if vh and vh in (cur_url or "") and not _looks_like_login(cur_url):
                authed_polls += 1
                if authed_polls >= 2:
                    save_and_exit("detected authenticated app (auto-login complete)", cur_url)
                    return
            else:
                authed_polls = 0

            time.sleep(POLL_INTERVAL_SECONDS)
            elapsed += POLL_INTERVAL_SECONDS

        log(f"TIMED OUT after {TIMEOUT_SECONDS}s.")
        write_status(state="timed_out", url=None, elapsed=elapsed)
        browser.close()
        sys.exit(2)


if __name__ == "__main__":
    main()
