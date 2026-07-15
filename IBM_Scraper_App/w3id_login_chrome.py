"""GTM Navigator login via Chrome — exact 3-tab passkey-bypass sequence.

Verified flow (user-confirmed 2026-07-09):

  ROUND 1 — Tab A (first GTM tab):
    1. Click Login → password form → enter email+password → Sign in
    2. → password-blocked: click "Click here" (keep password 4 hours)
    3. → browser BACK
    4. → click "sign in methods" link
    5. → method chooser → "w3id Password"
    6. → enter email+password → Sign in
    7. → GTM "Session expired" page — close tab

  ROUND 2 — Tab B:
    8.  Open GTM → (may need Login click) → password-blocked again
    9.  → "Click here" → "Log out" — close tab

  ROUND 3 — Tab C:
    10. Open GTM → native passkey dialog appears
        → CDP virtual authenticator makes it fail fast & auto-dismiss
    11. → "choose a different sign-in option" link on page
    12. → method chooser → "w3id Password"
    13. → enter email+password → Sign in → YOU ARE IN → save session

The virtual authenticator (installed on every tab) makes Chrome's native
WebAuthn passkey picker fail instantly instead of blocking for user input.
"""
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from playwright.sync_api import sync_playwright
import login_capture as lc

SC       = Path(__file__).resolve().parent / "_login_debug"
SC.mkdir(exist_ok=True)
ISC_AUTH = Path("~/.isc_scraper/auth_state.json").expanduser()
GTM_OUT  = Path("~/.orum_pipeline/gtmnav_auth_state.json").expanduser()
GTM_URL  = "https://w3.ibm.com/sales/gtm-navigator/login/app"
ISC_URL  = "https://ibmsc.lightning.force.com/lightning/n/TerritoryProspecting"
STOP     = SC / "STOP"

def log(msg): print(msg, flush=True)

def shot(pg, name):
    try: pg.screenshot(path=str(SC / name))
    except Exception: pass

def txt(pg):
    try: return pg.inner_text("body").lower()
    except Exception: return ""

def is_login_url(url):
    return any(m in (url or "").lower() for m in
        ("login.w3.ibm.com", "authsvc", "idaas", "password-blocked",
         "w3id-ns.sso", "/authorize", "/authenticate"))

def on_gtm_app(url, t):
    return ("w3.ibm.com/sales/gtm-navigator" in url
            and not is_login_url(url) and "session expired" not in t)

def click_sel(pg, selectors):
    for sel in selectors:
        try:
            el = pg.query_selector(sel)
            if el and el.is_visible(): el.click(); return True
        except Exception: continue
    return False

def click_txt(pg, texts, exact=False, ms=2500):
    if isinstance(texts, str): texts = [texts]
    for t in texts:
        for fn in (
            lambda t=t: pg.get_by_text(t, exact=exact).first.click(timeout=ms),
            lambda t=t: pg.get_by_role("button", name=t).first.click(timeout=ms),
            lambda t=t: pg.get_by_role("link",   name=t).first.click(timeout=ms),
        ):
            try: fn(); return True
            except Exception: continue
    return False

def click_app_login(pg):
    return click_sel(pg, ["button:has-text('Login')", "a:has-text('Login')",
                           "button:has-text('Log in')", "a:has-text('Log in')"])

def click_w3id_password(pg):
    if click_sel(pg, ["#credsDiv", "[id='credsDiv']"]): return True
    try:
        el = pg.evaluate_handle("""() => {
            const n = [...document.querySelectorAll('a,button,div,li,[role=button],[role=link]')];
            const h = n.find(e => (e.innerText||'').trim().toLowerCase().startsWith('w3id password'));
            return h ? (h.closest('a,button,[role=button],[role=link]') || h) : null;
        }""").as_element()
        if el: el.click(); return True
    except Exception: pass
    return click_txt(pg, "w3id Password", exact=False)

def type_into(pg, el, value):
    """Real key events for React-controlled inputs."""
    el.click(); pg.wait_for_timeout(100)
    el.click(click_count=3)
    pg.keyboard.press("Control+a")
    pg.keyboard.type(value, delay=30)
    pg.wait_for_timeout(150)

def fill_and_submit(pg, email, pw, label=""):
    log(f"  fill+submit ({label})")
    email_el = pw_el = None
    for sel in ["input[placeholder*='IBM email']", "input[placeholder*='email address']",
                "#user-name-input", "input[name='username']", "input[type='email']"]:
        try:
            el = pg.query_selector(sel)
            if el and el.is_visible(): email_el = el; break
        except Exception: continue
    for sel in ["input[placeholder='Password']", "input[placeholder*='assword']",
                "#password-input", "input[type='password']"]:
        try:
            el = pg.query_selector(sel)
            if el and el.is_visible(): pw_el = el; break
        except Exception: continue
    if email_el: type_into(pg, email_el, email)
    else: log("    WARNING: no email field")
    if pw_el:    type_into(pg, pw_el, pw)
    else: log("    WARNING: no password field")
    pg.wait_for_timeout(300)
    shot(pg, f"filled_{label}.png")
    if not click_sel(pg, ["button:has-text('Sign in')", "#login-button", "button[type='submit']"]):
        pg.keyboard.press("Enter")

def has_pw_form(pg):
    for sel in ["input[placeholder*='IBM email']", "input[placeholder='Password']",
                "#password-input", "input[type='password']"]:
        try:
            el = pg.query_selector(sel)
            if el and el.is_visible(): return True
        except Exception: continue
    return False

# Every virtual authenticator we install, so it can be torn down once the
# passkey-blocking step is past — it must NOT stay armed through password entry
# + session save, where a "set up a passkey" auto-nudge could register a phantom
# passkey into the ephemeral authenticator (I61).
_VAUTHS = []  # list of (cdp_session, authenticator_id)


def install_vauth(ctx, pg):
    """Install a CDP virtual authenticator so passkey get() fails fast,
    causing Chrome to auto-dismiss the native dialog instead of blocking.
    Registers it in _VAUTHS so remove_vauths() can scope it to just the
    passkey step (I61)."""
    try:
        cdp = ctx.new_cdp_session(pg)
        cdp.send("WebAuthn.enable")
        res = cdp.send("WebAuthn.addVirtualAuthenticator", {"options": {
            "protocol": "ctap2", "transport": "internal",
            "hasResidentKey": True, "hasUserVerification": True,
            "isUserVerified": False, "automaticPresenceSimulation": True,
        }})
        _VAUTHS.append((cdp, (res or {}).get("authenticatorId")))
        log("  virtual authenticator installed")
    except Exception as e:
        log(f"  vauth: {e}")


def remove_vauths():
    """Tear down every virtual authenticator installed via install_vauth so it is
    no longer armed during password entry + session save (I61). Best-effort — a
    closed tab's CDP session may already be gone; never fatal."""
    for cdp, auth_id in _VAUTHS:
        try:
            if auth_id:
                cdp.send("WebAuthn.removeVirtualAuthenticator",
                         {"authenticatorId": auth_id})
            cdp.send("WebAuthn.disable")
        except Exception as e:
            log(f"  vauth remove: {e}")
    _VAUTHS.clear()
    log("  virtual authenticator(s) removed")

def new_gtm_tab(ctx):
    """Open a new GTM tab with virtual authenticator pre-installed."""
    pg = ctx.new_page()
    install_vauth(ctx, pg)
    pg.goto(GTM_URL, wait_until="domcontentloaded", timeout=45000)
    pg.bring_to_front()
    pg.wait_for_timeout(1500)
    return pg

# ── credentials ───────────────────────────────────────────────────────────────
creds = lc.credential_store.get("w3id")
if not creds or not creds.get("email") or not creds.get("password"):
    log("ERROR: no w3id credentials in Keychain"); sys.exit(1)
EMAIL, PW = creds["email"], creds["password"]
log(f"credentials: {EMAIL}")

# ── main ──────────────────────────────────────────────────────────────────────
with sync_playwright() as p:
    log("launching Chrome")
    browser = p.chromium.launch(channel="chrome", headless=False,
                                args=["--start-maximized"])
    ctx = browser.new_context(storage_state=str(ISC_AUTH), locale="en-US",
                              timezone_id="America/Los_Angeles", no_viewport=True)

    # Tab 0: ISC — warm W3ID session
    log("Tab 0: ISC warm-up")
    isc = ctx.new_page()
    install_vauth(ctx, isc)
    isc.goto(ISC_URL, wait_until="domcontentloaded", timeout=60000)
    isc.wait_for_timeout(2000)
    log(f"  ISC: {isc.url[:70]}")

    # ── ROUND 1 ───────────────────────────────────────────────────────────────
    log("\n── ROUND 1 ──")
    t1 = new_gtm_tab(ctx)
    log(f"  r1 initial: {t1.url[:70]}")
    shot(t1, "r1_00_initial.png")

    # click Login if on app page
    if click_app_login(t1): log("  clicked Login"); t1.wait_for_timeout(2000)
    shot(t1, "r1_01_after_login.png")

    # fill password form
    if has_pw_form(t1):
        fill_and_submit(t1, EMAIL, PW, "r1a")
        t1.wait_for_timeout(3000)
    shot(t1, "r1_02_after_submit.png")
    log(f"  r1 post-submit: {t1.url[:70]}")

    # password-blocked → Click here
    if "password-blocked" in t1.url or "password-blocked" in txt(t1):
        log("  blocked: clicking 'Click here'")
        if not click_sel(t1, ["a[href='#']"]):
            click_txt(t1, ["Click here", "continue using your password",
                           "password for the next 4 hours"], exact=False)
        t1.wait_for_timeout(1000)
        shot(t1, "r1_03_after_click_here.png")

    # browser BACK
    log("  BACK")
    try: t1.go_back(wait_until="domcontentloaded", timeout=6000)
    except Exception as e: log(f"  go_back: {e}")
    t1.wait_for_timeout(1000)
    log(f"  r1 after back: {t1.url[:70]}")
    shot(t1, "r1_04_after_back.png")

    # "sign in methods" link — avoid the passkey one
    clicked = False
    for el in t1.query_selector_all("#back-button, [id='back-button']"):
        try:
            t = (el.inner_text() or "").lower()
            if el.is_visible() and "sign in methods" in t and "passkey" not in t:
                el.click(); clicked = True; log("  clicked 'sign in methods'"); break
        except Exception: pass
    if not clicked:
        click_txt(t1, ["View other sign in methods", "sign in methods",
                       "different sign-in option"], exact=False)
    t1.wait_for_timeout(1500)
    shot(t1, "r1_05_after_methods.png")

    # method chooser → w3id Password
    if "single-sign on method" in txt(t1):
        log("  chooser: w3id Password")
        click_w3id_password(t1); t1.wait_for_timeout(2000)

    # fill again
    if has_pw_form(t1):
        fill_and_submit(t1, EMAIL, PW, "r1b")
        t1.wait_for_timeout(4000)
    log(f"  r1 final: {t1.url[:70]}")
    shot(t1, "r1_06_final.png")
    t1.close(); time.sleep(0.5)

    # ── ROUND 2 ───────────────────────────────────────────────────────────────
    log("\n── ROUND 2 ──")
    t2 = new_gtm_tab(ctx)
    log(f"  r2 initial: {t2.url[:70]}")
    shot(t2, "r2_00_initial.png")

    if click_app_login(t2): log("  clicked Login"); t2.wait_for_timeout(2000)

    if has_pw_form(t2):
        fill_and_submit(t2, EMAIL, PW, "r2")
        t2.wait_for_timeout(3000)

    log(f"  r2 after login: {t2.url[:70]}")
    shot(t2, "r2_01_after_login.png")

    # password-blocked → Click here
    if "password-blocked" in t2.url or "password-blocked" in txt(t2):
        log("  blocked: clicking 'Click here'")
        if not click_sel(t2, ["a[href='#']"]):
            click_txt(t2, ["Click here", "continue using your password",
                           "password for the next 4 hours"], exact=False)
        t2.wait_for_timeout(1000)
        shot(t2, "r2_02_after_click_here.png")

    # Log out
    log("  clicking Log out")
    if not click_txt(t2, ["Log out", "Logout"], exact=True, ms=3000):
        click_txt(t2, ["Log out", "Logout", "Sign out"], exact=False)
    t2.wait_for_timeout(1500)
    log(f"  r2 after logout: {t2.url[:70]}")
    shot(t2, "r2_03_after_logout.png")
    t2.close(); time.sleep(0.5)

    # ── ROUND 3 ───────────────────────────────────────────────────────────────
    log("\n── ROUND 3 (final) ──")
    # Virtual authenticator makes the native passkey dialog fail fast & dismiss.
    t3 = new_gtm_tab(ctx)
    log(f"  r3 initial: {t3.url[:70]}")
    shot(t3, "r3_00_initial.png")

    if click_app_login(t3): log("  clicked Login"); t3.wait_for_timeout(2500)
    log(f"  r3 after login: {t3.url[:70]}")
    shot(t3, "r3_01_after_login.png")

    # The virtual authenticator should have auto-dismissed the native dialog.
    # Now the IBM page itself shows "choose a different sign-in option".
    # Give it a moment to settle after the passkey attempt fails.
    t3.wait_for_timeout(2000)

    # click "choose a different sign-in option"
    log("  clicking 'choose a different sign-in option'")
    if not click_txt(t3, ["choose a different sign-in option", "sign in methods",
                          "View other sign in methods", "different sign-in option"],
                     exact=False, ms=4000):
        click_sel(t3, ["#back-button", "a#back-button"])
    t3.wait_for_timeout(1500)
    shot(t3, "r3_02_after_diff_method.png")

    # method chooser → w3id Password
    if "single-sign on method" in txt(t3):
        log("  chooser: w3id Password")
        click_w3id_password(t3); t3.wait_for_timeout(2000)
    shot(t3, "r3_03_after_w3id.png")

    # Passkey step is past and we're on the password path — disarm the virtual
    # authenticator BEFORE password entry + session save so a "set up a passkey"
    # nudge can't register a phantom passkey into it (I61).
    remove_vauths()

    # fill email+password
    if has_pw_form(t3):
        fill_and_submit(t3, EMAIL, PW, "r3")
        t3.wait_for_timeout(5000)
    log(f"  r3 final: {t3.url[:70]}")
    shot(t3, "r3_04_final.png")

    # ── save and exit immediately ─────────────────────────────────────────────
    if on_gtm_app(t3.url, txt(t3)):
        GTM_OUT.parent.mkdir(parents=True, exist_ok=True)
        ctx.storage_state(path=str(GTM_OUT))
        shot(t3, "success.png")
        log(f"\n✓✓ SUCCESS — GTM session saved → {GTM_OUT}")
        try: browser.close()
        except Exception: pass
        log("done")
        sys.exit(0)

    # Didn't reach app — keep window open for manual finish + STOP sentinel.
    log(f"\nnot on GTM app yet (url={t3.url[:70]})")
    log(f"Finish manually, then: touch {STOP}")
    for _ in range(450):
        if STOP.exists():
            STOP.unlink(missing_ok=True)
            GTM_OUT.parent.mkdir(parents=True, exist_ok=True)
            ctx.storage_state(path=str(GTM_OUT))
            log(f"STOP: session saved → {GTM_OUT}")
            break
        try:
            u, t = t3.url, txt(t3)
        except Exception:
            break
        if on_gtm_app(u, t):
            GTM_OUT.parent.mkdir(parents=True, exist_ok=True)
            ctx.storage_state(path=str(GTM_OUT))
            shot(t3, "success_manual.png")
            log(f"✓✓ SUCCESS (manual) — saved → {GTM_OUT}")
            break
        time.sleep(2)

    try: browser.close()
    except Exception: pass

log("done")
