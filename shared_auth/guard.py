"""shared_auth.guard — the enforcement layer over the session registry.

`registry.py` says *what* the sites are and `sessions.py` says *where* their
sessions live. **This** module says *how the platform is allowed to treat those
sessions* — it is the one place the authorization invariants live, so every
process enforces the SAME rules instead of re-implementing (and drifting on)
login-detection, atomic writes, locking, redaction, and the password-fill
allowlist. See docs/SECURITY.md for the issue IDs each function prevents.

Stdlib-only (like `sessions.py`) so login_capture, every feature step, the Flask
dashboard, and the Meetings backend can all import it cheaply.

Invariants enforced here:
  * ONE origin-aware login/valid detector           → I7-detect, I10, I26
  * atomic, validity-guarded session writes          → I4a, I18
  * ONE advisory cross-process lock per session      → I4b, I4c, I22
  * an allowlist of origins where the W3ID password  → I7, I29
    may be typed (exact scheme+host, not substring)
  * URL redaction before anything is logged/shown     → leakage (SSO URLs carry
    SAMLResponse / codes / tokens in the query string)
  * 0600 perms on every session/secret-adjacent file → I19
  * an append-only, secret-free audit trail          → I9, I16
  * a single revoke/wipe path                         → I32
"""

import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlparse

from . import registry, sessions

# ── 1. Login / valid-session detection (one source of truth) ─────────────────
# These substring markers answer the READ-ONLY question "does this URL look like
# a login/SSO page?" — used to decide a saved session is dead. They are NEVER
# used to decide it is safe to type a password (that is PASSWORD_FILL_ORIGINS
# below — an exact-origin allowlist — because a substring test is a phishing
# hole, issue I7/I29).
LOGIN_URL_MARKERS = (
    "login.w3.ibm.com", "login.ibm.com", "w3id", "sso.ibm.com",
    "w3id-ns.sso.ibm.com", "password-blocked",
    "accounts.salesloft.com", "login.zoominfo.com", "okta", "idaas",
    "authsvc", "/saml", "/oidc", "/authorize", "/authenticate", "sign_in",
    "login.microsoftonline.com", "login.microsoft.com", "login.live.com",
    "microsoftonline", "/owa/auth", "accounts.google",
)


def is_login_url(url):
    """True if `url` looks like a login/SSO page (i.e. a saved session that lands
    here is expired). Read-only verdict only — do NOT gate a password fill on the
    negation of this (use `login_origin_allowed`)."""
    u = (url or "").lower()
    return any(m in u for m in LOGIN_URL_MARKERS)


def is_valid_app_url(service, url):
    """True only if the settled URL is actually the service's authenticated app:
    its host contains the registry `valid_host` AND it is not a login page. Uses
    the host, not a raw substring-in-full-URL, so an app route that merely
    contains 'authorize'/'sso' in a query param is not mistaken for a bounce
    (issue I26)."""
    cfg = registry.get(service) or {}
    valid_host = cfg.get("valid_host")
    if not valid_host:
        return False
    host = (urlparse(url or "").hostname or "").lower()
    # valid_host is sometimes a bare prefix like "outlook." — match on host, and
    # fall back to the documented substring contract for those prefix values.
    hit = valid_host in host if "." not in valid_host.rstrip(".") or valid_host.endswith(".") \
        else host.endswith(valid_host) or host == valid_host
    return bool(hit) and not is_login_url(url)


def session_verdict(service, final_url):
    """The single 'is this session alive?' decision, replacing the per-module
    `_raise_if_login_bounce` marker lists (issue I10). Returns 'valid' or
    'expired'. `password-blocked` is still 'expired' — the caller can add the
    'reset your W3ID password' hint via `is_password_blocked`."""
    if is_valid_app_url(service, final_url):
        return "valid"
    return "expired"


def is_password_blocked(url):
    """The IBM 'your password login is blocked' wall — a distinct remediation
    (reset W3ID password) from a plain session expiry."""
    return "password-blocked" in (url or "").lower()


# ── 2. Where the W3ID password may be typed (exact-origin allowlist) ─────────
# A password is only ever filled on one of these EXACT origins (scheme://host).
# Anything else — a lookalike host, an open-redirect landing page, a URL that
# merely contains 'w3id' as a substring — must never receive the secret (I7/I29).
PASSWORD_FILL_ORIGINS = frozenset({
    "https://login.w3.ibm.com",
    "https://login.ibm.com",
    "https://w3id-ns.sso.ibm.com",
    "https://login.microsoftonline.com",
    "https://login.microsoft.com",
    "https://login.zoominfo.com",
})


def login_origin_allowed(url):
    """True only if `url`'s exact scheme://host is a known SSO origin where it is
    safe to type the W3ID password. Call this before EVERY password fill."""
    p = urlparse(url or "")
    if p.scheme != "https" or not p.hostname:
        return False
    return f"{p.scheme}://{p.hostname}".lower() in PASSWORD_FILL_ORIGINS


# ── 3. Redaction (SSO URLs carry secrets in the query string) ────────────────
def redact_url(url):
    """scheme://host/path only — drop the query and fragment. IBM/Okta/Microsoft
    redirect URLs carry SAMLResponse / authorization codes / tokens in the query,
    so the full URL must be redacted before it reaches a log, a UI card, or an
    error message (issue: token leakage)."""
    try:
        p = urlparse(url or "")
        if not p.scheme:
            return url or ""
        base = f"{p.scheme}://{p.hostname}"
        if p.port:
            base += f":{p.port}"
        base += p.path or ""
        if p.query or p.fragment:
            base += " [?…redacted]"
        return base
    except Exception:
        return "[unparseable-url]"


# ── 4. File permissions ──────────────────────────────────────────────────────
def _chmod_600(path):
    """Best-effort 0600 (owner read/write only) on a session/secret file — they
    default to 0644 (world-readable) on a shared Mac otherwise (issue I19)."""
    try:
        os.chmod(path, 0o600)
    except Exception:
        pass


def harden_perms(service=None):
    """Tighten perms on one service's session file, or all of them. Idempotent —
    safe to call at startup to fix files written before this module existed."""
    svcs = [service] if service else registry.all_services()
    for svc in svcs:
        try:
            p = sessions.state_path(svc)
            if p.exists():
                _chmod_600(p)
        except Exception:
            pass


# ── 5. Atomic, validity-guarded session writes ───────────────────────────────
def atomic_save_state(service, context, final_url=None):
    """Persist a Playwright context's storage_state for `service` SAFELY:

      * writes to a temp file then os.replace()s it in — a reader can never see a
        half-written (torn) session (issue I4a); contrast the current in-place
        `context.storage_state(path=…)` writes.
      * refuses to persist a LOGGED-OUT session over a good one: if `final_url`
        is provided and its verdict is not 'valid', the save is skipped and False
        is returned (issue I18). Pass `page.url` here.
      * chmods the result to 0600 (issue I19).

    Returns True if written, False if skipped because the session looked dead.
    """
    if final_url is not None and session_verdict(service, final_url) != "valid":
        audit(service, "save_state", "skipped_not_valid", url=redact_url(final_url))
        return False
    dest = sessions.state_path(service)
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(dest.parent), prefix=".tmp_state_", suffix=".json")
    os.close(fd)
    try:
        context.storage_state(path=tmp)
        os.replace(tmp, dest)
        _chmod_600(dest)
    finally:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
    audit(service, "save_state", "ok")
    return True


# ── 6. One advisory cross-process lock per session ───────────────────────────
# A capture (writer) takes it EXCLUSIVE; a scrape or a probe (reader) takes it
# SHARED. The validator/auto-login skip a service whose exclusive lock is held.
# fcntl.flock is advisory + auto-released if the holder dies, so a crashed step
# never wedges the lock (issues I4b, I4c, I22).
def _lock_path(service):
    p = sessions.state_path(service)
    return p.parent / f".{p.name}.lock"


@contextmanager
def session_lock(service, exclusive=False, blocking=True):
    """Advisory flock over a service's session file. `with session_lock(svc,
    exclusive=True):` around a capture; `exclusive=False` around a scrape/probe.
    If non-blocking and the lock is unavailable, raises BlockingIOError so the
    caller can skip (e.g. the validator declining to probe mid-capture)."""
    import fcntl
    lp = _lock_path(service)
    lp.parent.mkdir(parents=True, exist_ok=True)
    mode = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
    if not blocking:
        mode |= fcntl.LOCK_NB
    f = open(lp, "a+")
    try:
        fcntl.flock(f.fileno(), mode)
        yield
    finally:
        try:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        finally:
            f.close()


def is_locked_exclusive(service):
    """True if some process holds the EXCLUSIVE (capture) lock right now — the
    validator uses this to skip probing a service mid-login without depending on
    the ISC-only 'scraping' flag (issue I4b)."""
    import fcntl
    lp = _lock_path(service)
    if not lp.exists():
        return False
    try:
        f = open(lp, "a+")
    except Exception:
        return False
    try:
        fcntl.flock(f.fileno(), fcntl.LOCK_SH | fcntl.LOCK_NB)
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        return False   # we got a shared lock → nobody holds it exclusive
    except BlockingIOError:
        return True
    finally:
        f.close()


# ── 7. Append-only, secret-free audit trail ──────────────────────────────────
_AUDIT_PATH = Path("~/.orum_pipeline/auth_audit.log").expanduser()


def audit(service, action, outcome, **extra):
    """Append one JSON line recording a session/credential USE — never a secret,
    never a full URL (extra values should already be redacted). Lets the user
    reconcile 'did the automation do this?' and spot anomalous use of their
    identity (issues I9, I16). Timestamped by the OS at read time is unavailable
    here (stdlib time is fine to import, but callers may run in restricted
    contexts) — we stamp with time.time() lazily."""
    try:
        import time as _t
        rec = {"ts": round(_t.time(), 3), "service": service,
               "action": action, "outcome": outcome}
        rec.update(extra)
        _AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(_AUDIT_PATH, "a") as f:
            f.write(json.dumps(rec) + "\n")
        _chmod_600(_AUDIT_PATH)
    except Exception:
        pass  # audit must never break the caller


# ── 8. Revocation / offboarding ──────────────────────────────────────────────
def wipe_all(include_credential=False):
    """Delete every captured session file (sign out everywhere) — the missing
    'revoke on device loss / offboarding' path (issue I32). Does NOT touch the
    Keychain credential unless include_credential=True (that lives in
    credential_store, imported lazily to keep this module dependency-free).
    Returns the list of removed paths."""
    removed = []
    for svc in registry.all_services():
        try:
            p = sessions.state_path(svc)
            if p.exists():
                p.unlink()
                removed.append(str(p))
            lp = _lock_path(svc)
            if lp.exists():
                lp.unlink()
        except Exception:
            pass
    if include_credential:
        try:
            import subprocess
            import credential_store
            subprocess.run(["/usr/bin/security", "delete-generic-password",
                            "-s", credential_store._svc_name("w3id")],
                           capture_output=True, text=True)
            removed.append("keychain:orum-pipeline-cred-w3id")
        except Exception:
            pass
    audit("*", "wipe_all", "ok", count=len(removed))
    return removed
