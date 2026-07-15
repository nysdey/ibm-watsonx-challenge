"""Auth-hardening tests for run_pipeline.py (docs/SECURITY.md I1/I8/I15/I46-48).

Guard behaviors are tested against a NON-EXISTENT route so before_request runs
without triggering any real automation: a blocked request → 403 (from the guard),
an allowed request → 404 (routing, i.e. the guard let it through).
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.argv = ["run_pipeline.py"]
import run_pipeline as rp  # noqa: E402

DEAD = "/api/__nonexistent_guard_probe__"


@pytest.fixture
def client():
    return rp.app.test_client()


# ── before_request guard (I46/I47/I48) ───────────────────────────────────────
def test_get_same_origin_allowed(client):
    # loopback Host, GET → guard allows (routes to 404, not 403).
    r = client.get(DEAD, environ_overrides={"HTTP_HOST": "127.0.0.1:5488"})
    assert r.status_code == 404


def test_dns_rebinding_host_blocked(client):
    # Attacker hostname resolving to 127.0.0.1 sends its own Host → 403 (I48).
    r = client.get(DEAD, environ_overrides={"HTTP_HOST": "evil.example"})
    assert r.status_code == 403
    assert "host" in r.get_json()["error"]


def test_cross_origin_post_blocked(client):
    # Browser drive-by: cross-origin POST always carries a non-loopback Origin → 403 (I47).
    r = client.post(DEAD, environ_overrides={"HTTP_HOST": "127.0.0.1:5488"},
                    headers={"Origin": "https://evil.example"})
    assert r.status_code == 403
    assert "cross-origin" in r.get_json()["error"]


def test_cross_origin_referer_blocked(client):
    r = client.post(DEAD, environ_overrides={"HTTP_HOST": "127.0.0.1:5488"},
                    headers={"Referer": "https://evil.example/x"})
    assert r.status_code == 403


def test_same_origin_post_allowed(client):
    # The real UI: same-origin POST carries a loopback Origin → guard allows (404).
    r = client.post(DEAD, environ_overrides={"HTTP_HOST": "127.0.0.1:5488"},
                    headers={"Origin": "http://127.0.0.1:5488"})
    assert r.status_code == 404


def test_token_allows_local_tool(client, monkeypatch):
    monkeypatch.setattr(rp, "_DASHBOARD_AUTH_TOKEN", "SECRET123")
    r = client.post(DEAD, environ_overrides={"HTTP_HOST": "127.0.0.1:5488"},
                    headers={"X-Auth-Token": "SECRET123"})
    assert r.status_code == 404


def test_tokenless_originless_post_allowed_by_default(client):
    # Default (non-strict): a local curl with no Origin is allowed (compat).
    r = client.post(DEAD, environ_overrides={"HTTP_HOST": "127.0.0.1:5488"})
    assert r.status_code == 404


def test_strict_mode_blocks_tokenless_originless(client, monkeypatch):
    monkeypatch.setattr(rp, "_STRICT_LOCAL_AUTH", True)
    r = client.post(DEAD, environ_overrides={"HTTP_HOST": "127.0.0.1:5488"})
    assert r.status_code == 403


def test_index_still_renders(client):
    r = client.get("/", environ_overrides={"HTTP_HOST": "127.0.0.1:5488"})
    assert r.status_code == 200


# ── Mocked auth (WatsonX Clone) ───────────────────────────────────────────────
# In the clone every service is mocked, so the JIT session gate is a no-op: it always
# reports ready (there is no real session to be missing or to expire), and the
# per-service probe always returns "valid". A demo never dead-ends on a login.
def test_ensure_services_ready_always_ok(monkeypatch, tmp_path):
    missing = tmp_path / "nope.json"
    monkeypatch.setitem(rp.LOGIN_SERVICES, "zoominfo", missing)   # even with no session file
    assert rp._ensure_services_ready(["isc", "zoominfo", "salesloft"]) == (True, None)


def test_probe_and_status_are_mocked():
    assert rp._probe_login_once("zoominfo") == "valid"
    assert rp._login_status("salesloft")["state"] == "ready"


def test_ensure_services_ready_valid(monkeypatch, tmp_path):
    present = tmp_path / "z.json"; present.write_text("{}")
    monkeypatch.setitem(rp.LOGIN_SERVICES, "zoominfo", present)
    monkeypatch.setattr(rp, "_probe_login_once", lambda svc: "valid")
    ok, msg = rp._ensure_services_ready(["zoominfo"])
    assert ok is True and msg is None


# ── self-healing watchdog: circuit breaker (I15/I34) + automation-aware (I8) ──
def test_auto_login_circuit_breaker(monkeypatch):
    launched = []
    monkeypatch.setattr(rp.credential_store, "has", lambda k: True)
    monkeypatch.setattr(rp, "_start_login_proc", lambda svc: launched.append(svc))
    monkeypatch.setattr(rp, "_LOGIN_PROCS", {})
    # zoominfo perpetually expired.
    with rp._LOGIN_VALIDITY_LOCK:
        rp._LOGIN_VALIDITY.clear()
        rp._LOGIN_VALIDITY["zoominfo"] = {"status": "expired", "checked_at": 0}
    rp._AUTO_LOGIN_ATTEMPTED.clear()
    rp._AUTO_LOGIN_FAILS.clear()
    monkeypatch.setattr(rp, "LOGIN_SERVICES", {"zoominfo": Path("/x")})
    # Repeated ticks: it should launch, then count fails, then STOP at the cap.
    for _ in range(6):
        rp._maybe_auto_login(busy=False)
    assert rp._AUTO_LOGIN_FAILS.get("zoominfo", 0) >= rp._MAX_AUTO_LOGIN_FAILS
    # Never launched more than the cap+the in-flight attempts (bounded, not spamming).
    assert len(launched) <= rp._MAX_AUTO_LOGIN_FAILS
    rp._AUTO_LOGIN_ATTEMPTED.clear(); rp._AUTO_LOGIN_FAILS.clear()


def test_auto_login_skips_when_busy(monkeypatch):
    launched = []
    monkeypatch.setattr(rp.credential_store, "has", lambda k: True)
    monkeypatch.setattr(rp, "_start_login_proc", lambda svc: launched.append(svc))
    rp._maybe_auto_login(busy=True)
    assert launched == []


def test_automation_active_reflects_state(monkeypatch):
    monkeypatch.setitem(rp._FILL_STATE, "active", False)
    assert rp._automation_active() is False
    monkeypatch.setitem(rp._FILL_STATE, "active", True)
    assert rp._automation_active() is True
    monkeypatch.setitem(rp._FILL_STATE, "active", False)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
