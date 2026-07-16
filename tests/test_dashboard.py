"""Per-function tests for the WatsonX Clone dashboard code (run with the clone .venv).

    .venv/bin/python3 tests/test_dashboard.py

Covers: the mocked auth (every service reports ready, no real login), the removal of
the Meetings + Pipeline tabs, the deterministic fake-data generators + install joins,
and the mock tool UIs (login windows + Salesloft/ZoomInfo/ISC views).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

_passed = 0
def ok(cond, label):
    global _passed
    assert cond, "FAIL: " + label
    _passed += 1


def test_fake_data_deterministic_and_joins():
    import fake_data as fd
    covids = ["T0016156", "T0016158", "T0018075"]
    a1 = fd.accounts_for_covids(covids)
    a2 = fd.accounts_for_covids(covids)
    ok(len(a1) > 0, "accounts generated")
    ok([x["name"] for x in a1] == [x["name"] for x in a2], "accounts deterministic")
    ok(a1[0]["account_number"] == a2[0]["account_number"], "identity deterministic")
    # ISC rollup schema — the trailing-space header is reproduced verbatim
    h, rows = fd.company_rollup(a1)
    ok(len(h) == 23 and h[11] == "Global Annual Revenue ", "23-col rollup w/ trailing-space header")
    # install rows carry join keys that hit the account set (so Segmentation attaches)
    codes = {x["account_number"] for x in a1}
    names = {x["account_name"] for x in a1}
    _, cloud = fd.cloud_install(a1, covids)
    ok(cloud and all(r[4] in codes for r in cloud), "cloud rows join by hierarchy code")
    _, noninfra = fd.ibm_non_infra_install(a1, covids)
    ok(noninfra and all(r[0] in names for r in noninfra), "non-infra rows join by exact name")
    # mocks present
    ok(fd.zoominfo_enrichment("Acme")["ZI_Match_Status"] in ("Matched", "Unmatched", "Ambiguous"), "zi mock")
    ok(isinstance(fd.signals_for("Acme"), list), "signals mock")
    ok("Targeted Outreach Cadence 4" in fd.SALESLOFT_CADENCES, "salesloft cadences")


def test_mock_salesloft_store():
    import mock_salesloft as ms
    ms.reset()
    ms.add_people("Targeted Outreach Cadence 4",
                  [{"first_name": "A", "last_name": "B", "title": "CIO", "company": "X"}])
    st = ms.cadence_state("Targeted Outreach Cadence 4")
    ok(len(st["members"]) == 1 and st["members"][0]["step"] == ms.FIRST_STEP, "add_people at step 1")
    n = ms.advance_step_one("Targeted Outreach Cadence 4")
    ok(n == 1 and ms.cadence_state("Targeted Outreach Cadence 4")["members"][0]["step"] == ms.CALL_STEP,
       "advance moves step 1 -> call")
    ms.reset()
    ok(ms.all_state()["cadences"] == {}, "reset clears state")


def test_run_pipeline_wiring():
    sys.argv = ["run_pipeline.py"]
    import run_pipeline as rp
    ok(rp._PANEL_LOGIN_SERVICES == ["isc", "zoominfo", "salesloft"], "panel services (no outlook)")
    ok("pipeline_review" not in rp.STEPS, "no pipeline_review step")
    ok(set(rp.STEPS) == {"step1", "ibm", "segment", "step2", "step3", "step4", "step5"}, "7 pipeline steps")
    ok(not hasattr(rp, "_meeting_api_base"), "meeting api helper removed")
    ok(not hasattr(rp, "_start_meeting_backend"), "meeting backend launcher removed")
    # mocked auth: always ready, never a real probe
    ok(rp._probe_login_once("isc") == "valid", "probe always valid")
    ok(rp._login_status("zoominfo")["state"] == "ready", "login status always ready")
    ok(rp._ensure_services_ready(["isc", "zoominfo", "salesloft"]) == (True, None), "services always ready")


def test_routes():
    import run_pipeline as rp
    c = rp.app.test_client()
    idx = c.get("/").get_data(as_text=True)
    ok('id="page-outbound"' in idx, "outbound page present")
    ok('data-page="meetings"' not in idx and 'data-page="pipeline"' not in idx, "no meetings/pipeline tabs")
    ok("{{ meeting_api }}" not in idx, "no unrendered placeholder")
    # removed routes 404
    ok(c.get("/meetings/live").status_code == 404, "/meetings/live gone")
    ok(c.get("/view/pipeline_review").status_code == 404, "/view/pipeline_review gone")
    # kept + new routes render
    ok(c.get("/bobby").status_code == 200, "/bobby renders")
    ok(c.get("/mock/salesloft").status_code == 200, "/mock/salesloft renders")
    ok(c.get("/mock/zoominfo").status_code == 200, "/mock/zoominfo renders")
    ok(c.get("/mock/isc").status_code == 200, "/mock/isc renders")
    ok(c.get("/mock/salesloft/login").status_code == 200, "/mock/salesloft/login renders")
    ok(c.get("/mock/bogus/login").status_code == 404, "unknown mock service 404")
    # api shape
    st = json.loads(c.get("/api/status").get_data())
    acts = st.get("_actions", {})
    ok(set(acts) == {"get_my_accounts", "outbound_strategy", "fill_contacts", "bobby"}, "actions (no pipeline_review)")
    lg = json.loads(c.get("/api/login/status").get_data())
    ok(set(lg) == {"isc", "zoominfo", "salesloft"} and all(v["state"] == "ready" for v in lg.values()),
       "login status: 3 services, all ready")
    start = json.loads(c.post("/api/login/salesloft/start").get_data())
    ok(start.get("mock_url") == "/mock/salesloft/login", "login start returns mock url")


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for t in tests:
        t()
        print(f"  ✓ {t.__name__}")
    print(f"\nALL {len(tests)} dashboard test groups passed — {_passed} individual assertions.")


if __name__ == "__main__":
    main()
