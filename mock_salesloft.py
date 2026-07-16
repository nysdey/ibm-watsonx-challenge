"""Shared mock "Salesloft server" state for the BobBee.

There is no real Salesloft in the clone, but several parts of the app act on one:
Fill Contacts loads people into a cadence, the cadence-advance step (Step 7) moves
everyone at step 1 into the call step, and the dashboard's ``/mock/salesloft`` view
renders the result so a demo can literally *show* Salesloft. They coordinate through
this tiny JSON-backed store (a stand-in for Salesloft's server-side state) instead of
the real ``api.salesloft.com``.

Backed by one JSON file at the repo root (gitignored). Process-safe via a lock; the
subprocess steps and the Flask app all import this module and hit the same file.
"""
import json
import threading
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
STATE_PATH = REPO_ROOT / ".mock_salesloft_state.json"
_LOCK = threading.Lock()

FIRST_STEP = "Step 1"
CALL_STEP = "Call"


def _load():
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text())
        except Exception:
            pass
    return {"cadences": {}}


def _save(state):
    tmp = STATE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2))
    tmp.replace(STATE_PATH)


def add_people(cadence, people):
    """Enroll people at the cadence's first step. `people` are dicts carrying at least
    first_name/last_name/title/company (email optional). Returns the new member count."""
    with _LOCK:
        state = _load()
        cad = state["cadences"].setdefault(cadence, {"members": []})
        now = datetime.now().isoformat(timespec="seconds")
        for p in people:
            cad["members"].append({
                "first_name": p.get("first_name", ""),
                "last_name": p.get("last_name", ""),
                "title": p.get("title", ""),
                "company": p.get("company", ""),
                "email": p.get("email", ""),
                "step": FIRST_STEP,
                "added_at": now,
            })
        _save(state)
        return len(cad["members"])


def advance_step_one(cadence):
    """Move everyone currently at the first step into the call step. Returns the count
    advanced (mirrors Salesloft_Cadence_Readiness's real behavior)."""
    with _LOCK:
        state = _load()
        cad = state["cadences"].get(cadence)
        if not cad:
            return 0
        n = 0
        for m in cad["members"]:
            if m["step"] == FIRST_STEP:
                m["step"] = CALL_STEP
                n += 1
        _save(state)
        return n


def cadence_state(cadence):
    with _LOCK:
        return _load()["cadences"].get(cadence, {"members": []})


def all_state():
    with _LOCK:
        return _load()


def reset():
    with _LOCK:
        _save({"cadences": {}})
