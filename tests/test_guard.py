"""Unit tests for shared_auth.guard — the authorization enforcement layer.

Never touches the real ~/.orum_pipeline session files: the one test that writes
monkeypatches sessions.state_path into a tmp dir.
"""
import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared_auth import guard  # noqa: E402


# ── login/valid detection ────────────────────────────────────────────────────
def test_is_login_url_detects_bounces():
    assert guard.is_login_url("https://login.w3.ibm.com/saml/sps/auth")
    assert guard.is_login_url("https://w3id-ns.sso.ibm.com/pages/password-blocked.html")
    assert guard.is_login_url("https://accounts.salesloft.com/sign_in")
    assert guard.is_login_url("https://login.zoominfo.com")
    assert not guard.is_login_url("https://app.zoominfo.com/#/advanced-search")
    assert not guard.is_login_url("https://app.salesloft.com/app/cadences")


def test_is_valid_app_url_uses_host_not_substring():
    # Real app pages are valid.
    assert guard.is_valid_app_url("zoominfo", "https://app.zoominfo.com/#/search")
    assert guard.is_valid_app_url("salesloft", "https://app.salesloft.com/app")
    assert guard.is_valid_app_url("isc", "https://ibmsc.lightning.force.com/lightning/n/x")
    # An app route that merely CONTAINS a marker word in its path/query must not
    # be misread as a bounce (issue I26).
    assert guard.is_valid_app_url("salesloft", "https://app.salesloft.com/app?tab=authorize")
    # A real bounce to SSO is not valid.
    assert not guard.is_valid_app_url("zoominfo", "https://login.w3.ibm.com/saml/sps/auth")
    # outlook uses the "outlook." prefix valid_host — both hosts match.
    assert guard.is_valid_app_url("outlook", "https://outlook.office.com/calendar/view/week")
    assert guard.is_valid_app_url("outlook", "https://outlook.cloud.microsoft/mail")


def test_session_verdict():
    assert guard.session_verdict("zoominfo", "https://app.zoominfo.com/#/x") == "valid"
    assert guard.session_verdict("zoominfo", "https://login.w3.ibm.com/saml") == "expired"


def test_is_password_blocked():
    assert guard.is_password_blocked("https://w3id-ns.sso.ibm.com/pages/password-blocked.html")
    assert not guard.is_password_blocked("https://login.w3.ibm.com/authsvc")


# ── password-fill origin allowlist (I7 / I29) ────────────────────────────────
def test_login_origin_allowed_exact_origins_only():
    assert guard.login_origin_allowed("https://login.w3.ibm.com/authsvc/authenticator")
    assert guard.login_origin_allowed("https://login.microsoftonline.com/common/oauth2")
    assert guard.login_origin_allowed("https://login.zoominfo.com/")
    # A lookalike / evil host that merely CONTAINS an allowed host as substring
    # must be rejected (this is the whole point of exact-origin matching).
    assert not guard.login_origin_allowed("https://login.w3.ibm.com.evil.example/authsvc")
    assert not guard.login_origin_allowed("https://evil.example/?u=login.w3.ibm.com")
    # http (not https) rejected.
    assert not guard.login_origin_allowed("http://login.w3.ibm.com/authsvc")
    # An app page is not a password-fill origin.
    assert not guard.login_origin_allowed("https://app.zoominfo.com")
    assert not guard.login_origin_allowed("")
    assert not guard.login_origin_allowed(None)


# ── redaction (SSO URLs carry tokens in the query) ───────────────────────────
def test_redact_url_strips_query_and_fragment():
    r = guard.redact_url("https://login.w3.ibm.com/saml/sps/auth?SAMLResponse=SECRET&RelayState=x")
    assert "SECRET" not in r
    assert "SAMLResponse" not in r
    assert r.startswith("https://login.w3.ibm.com/saml/sps/auth")
    assert "redacted" in r
    # No query → unchanged base.
    assert guard.redact_url("https://app.zoominfo.com/home") == "https://app.zoominfo.com/home"
    assert guard.redact_url("") == ""


# ── atomic, validity-guarded save (I4a / I18) ────────────────────────────────
class _FakeContext:
    """Stand-in for a Playwright context: writes a marker JSON to the given path."""
    def __init__(self, payload):
        self.payload = payload
        self.calls = 0

    def storage_state(self, path):
        self.calls += 1
        Path(path).write_text(json.dumps(self.payload))


def test_atomic_save_skips_when_session_looks_dead(tmp_path, monkeypatch):
    dest = tmp_path / "zoominfo_auth_state.json"
    dest.write_text('{"cookies": "GOOD-EXISTING"}')
    monkeypatch.setattr(guard.sessions, "state_path", lambda svc: dest)
    ctx = _FakeContext({"cookies": "NEW-BUT-LOGGED-OUT"})

    # final_url is a login bounce → must NOT overwrite the good file (I18).
    wrote = guard.atomic_save_state("zoominfo", ctx, final_url="https://login.w3.ibm.com/saml")
    assert wrote is False
    assert ctx.calls == 0
    assert "GOOD-EXISTING" in dest.read_text()  # untouched


def test_atomic_save_writes_when_valid_and_sets_0600(tmp_path, monkeypatch):
    dest = tmp_path / "zoominfo_auth_state.json"
    monkeypatch.setattr(guard.sessions, "state_path", lambda svc: dest)
    ctx = _FakeContext({"cookies": "FRESH"})

    wrote = guard.atomic_save_state("zoominfo", ctx, final_url="https://app.zoominfo.com/#/x")
    assert wrote is True
    assert "FRESH" in dest.read_text()
    # 0600 perms (owner-only) — issue I19.
    assert (dest.stat().st_mode & 0o777) == 0o600
    # No stray temp files left behind.
    assert not list(tmp_path.glob(".tmp_state_*"))


def test_atomic_save_no_url_check_when_final_url_none(tmp_path, monkeypatch):
    dest = tmp_path / "salesloft_auth_state.json"
    monkeypatch.setattr(guard.sessions, "state_path", lambda svc: dest)
    ctx = _FakeContext({"cookies": "X"})
    assert guard.atomic_save_state("salesloft", ctx) is True


# ── advisory lock (I4b / I22) ────────────────────────────────────────────────
def test_session_lock_shared_then_exclusive_state(tmp_path, monkeypatch):
    dest = tmp_path / "zoominfo_auth_state.json"
    monkeypatch.setattr(guard.sessions, "state_path", lambda svc: dest)
    # Nobody holds it → not exclusive-locked.
    assert guard.is_locked_exclusive("zoominfo") is False
    with guard.session_lock("zoominfo", exclusive=False):
        # A shared holder is not an exclusive holder.
        assert guard.is_locked_exclusive("zoominfo") is False


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
