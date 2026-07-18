"""watsonx Assistant (v2 REST API) — the in-app help chatbot.

Scope is deliberately narrow: this answers questions *about BobBee* (how
cadences are built, what a tag means, where a number comes from). It is NOT
given the seller's book. No account names, contacts, spend figures or schedule
data are ever sent to the service — see `_SYSTEM_CONTEXT` for everything that
leaves this machine.

Wire-up, all from the Assistant instance in IBM Cloud:

    WXA_API_KEY        IBM Cloud API key with access to the Assistant service
    WXA_SERVICE_URL    e.g. https://api.us-south.assistant.watson.cloud.ibm.com/instances/<id>
    WXA_ASSISTANT_ID   the assistant (or environment) ID you want to talk to
    WXA_API_VERSION    optional; defaults below

Fail-soft by design, exactly like llm_advisor: any missing config, network
blip, or bad response degrades to a local canned answer rather than raising.
The app must keep working offline — that's a property of this demo, and a
chatbot is not worth breaking it for.

Session handling: the v2 API is session-based. Sessions expire server-side
(inactivity timeout is set on the instance), so a stale session is retried
once with a fresh one rather than surfaced as an error.
"""
import json
import os
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

IAM_TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"
API_VERSION = os.environ.get("WXA_API_VERSION", "2024-08-25")

_TOKEN_LOCK = threading.Lock()
_TOKEN_CACHE = {"access_token": None, "expires_at": 0.0}

# assistant-session cache: one session reused across turns for a given browser
# session id, so multi-turn context works without a session round-trip per
# message.
_SESSION_LOCK = threading.Lock()
_SESSIONS = {}   # client_id -> {"session_id": str, "created": float}
_SESSION_MAX_AGE = 25 * 60   # re-create well inside a typical 30-min timeout

# What the assistant is allowed to know. Product facts only — no seller data.
_SYSTEM_CONTEXT = (
    "BobBee is an IBM seller tool that turns a territory account list into a "
    "ranked, cadenced, day-by-day outreach plan. Tabs: Schedule (the quarter as "
    "a calendar), Accounts (the book plus cadence lists), Cadences (playbook "
    "definitions), Email and Call (today's work), Dashboard (today's tasks and "
    "activity), Profile (identity, territory map, settings)."
)

# Local answers for the common questions, used when the service is unreachable
# so the panel still does something useful offline.
_FALLBACKS = [
    (("cadence", "cadences"),
     "A cadence is a playbook: an ordered set of email and call steps on set "
     "days. Strategize assigns each account to one, ranks it, and spreads the "
     "starts across the quarter's weekdays."),
    (("leftover", "leftovers"),
     "Leftovers are accounts that scored below a cadence's cap. They're set "
     "aside rather than left unreachable, and rejoin the pool for a future "
     "quarter."),
    (("no contact", "no contacts", "decision maker"),
     "Accounts with no IT decision-maker in ZoomInfo go to the No contacts "
     "list, so you don't work an account you can't actually reach."),
    (("ai", "watsonx", "granite"),
     "Two things are model-generated: the play and sales angle on an account, "
     "and the pre-call briefs. Both are marked purple with a sparkle. "
     "Everything else — scoring, ranking, cadence assignment, the schedule — "
     "is deterministic."),
    (("tier", "score", "scoring"),
     "Account Tiering scores on IBM spend and trend, install base, company "
     "size, and recent buying signals. That score drives cadence rank."),
]

_OFFLINE_DEFAULT = (
    "I can't reach watsonx Assistant right now, so I'm answering from a small "
    "built-in set of topics. Try asking about cadences, leftovers, no-contact "
    "accounts, scoring, or where AI is used."
)


def _config():
    """(api_key, service_url, assistant_id) or None if not fully configured."""
    key = (os.environ.get("WXA_API_KEY") or "").strip()
    url = (os.environ.get("WXA_SERVICE_URL") or "").strip().rstrip("/")
    aid = (os.environ.get("WXA_ASSISTANT_ID") or "").strip()
    if not (key and url and aid):
        return None
    return key, url, aid


def is_configured():
    return _config() is not None


def _get_iam_token(api_key, force=False):
    """Exchange (or reuse) an IBM Cloud API key for an IAM bearer token.
    Returns the token, or None on any failure — never raises."""
    with _TOKEN_LOCK:
        now = time.monotonic()
        if not force and _TOKEN_CACHE["access_token"] and now < _TOKEN_CACHE["expires_at"]:
            return _TOKEN_CACHE["access_token"]
        data = urllib.parse.urlencode({
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey": api_key,
        }).encode("utf-8")
        req = urllib.request.Request(
            IAM_TOKEN_URL, data=data, method="POST",
            headers={"content-type": "application/x-www-form-urlencoded",
                     "accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except Exception:
            return None
        token = body.get("access_token")
        if not token:
            return None
        _TOKEN_CACHE["access_token"] = token
        _TOKEN_CACHE["expires_at"] = now + max(60, body.get("expires_in", 3600) - 300)
        return token


def _request(method, url, token, payload=None, timeout=30):
    """Signed JSON call. Returns (status, parsed_body_or_None)."""
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/json",
                 "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8"))
        except Exception:
            return e.code, None
    except Exception:
        return 0, None


def _new_session(token, url, aid):
    status, body = _request(
        "POST", f"{url}/v2/assistants/{aid}/sessions?version={API_VERSION}", token, payload={})
    if status in (200, 201) and body:
        return body.get("session_id")
    return None


def _session_for(client_id, token, url, aid, force_new=False):
    with _SESSION_LOCK:
        rec = _SESSIONS.get(client_id)
        fresh = rec and (time.monotonic() - rec["created"]) < _SESSION_MAX_AGE
        if rec and fresh and not force_new:
            return rec["session_id"]
    sid = _new_session(token, url, aid)
    if sid:
        with _SESSION_LOCK:
            _SESSIONS[client_id] = {"session_id": sid, "created": time.monotonic()}
    return sid


def _extract_text(body):
    """Pull the text replies out of a v2 message response."""
    out = []
    for g in ((body or {}).get("output") or {}).get("generic") or []:
        if g.get("response_type") == "text" and g.get("text"):
            out.append(g["text"])
        elif g.get("response_type") == "option":
            # Options carry their prompt as the useful part for a text panel.
            if g.get("title"):
                out.append(g["title"])
    return "\n\n".join(out).strip()


def _fallback(text):
    q = (text or "").lower()
    for keys, answer in _FALLBACKS:
        if any(k in q for k in keys):
            return answer
    return _OFFLINE_DEFAULT


def ask(text, client_id="default"):
    """Send one turn. Always returns a dict — never raises.

    {"reply": str, "live": bool, "error": str|None}

    live=False means the answer came from the local fallback set, so the UI can
    say so instead of passing off a canned string as the assistant's answer.
    """
    text = (text or "").strip()
    if not text:
        return {"reply": "", "live": False, "error": "empty message"}

    cfg = _config()
    if not cfg:
        return {"reply": _fallback(text), "live": False, "error": "not configured"}
    api_key, url, aid = cfg

    token = _get_iam_token(api_key)
    if not token:
        return {"reply": _fallback(text), "live": False, "error": "auth failed"}

    def _send(session_id):
        return _request(
            "POST",
            f"{url}/v2/assistants/{aid}/sessions/{session_id}/message?version={API_VERSION}",
            token,
            payload={
                "input": {"message_type": "text", "text": text,
                          "options": {"return_context": False}},
                # Product context only. Deliberately no seller/account data.
                "context": {"skills": {"actions skill": {"skill_variables": {
                    "app_context": _SYSTEM_CONTEXT}}}},
            },
        )

    sid = _session_for(client_id, token, url, aid)
    if not sid:
        return {"reply": _fallback(text), "live": False, "error": "no session"}

    status, body = _send(sid)
    # A dead session reads as 404; rebuild once rather than surfacing an error.
    if status == 404:
        sid = _session_for(client_id, token, url, aid, force_new=True)
        if sid:
            status, body = _send(sid)

    if status == 200:
        reply = _extract_text(body)
        if reply:
            return {"reply": reply, "live": True, "error": None}
        return {"reply": "I don't have an answer for that one yet.",
                "live": True, "error": None}

    return {"reply": _fallback(text), "live": False, "error": f"http {status}"}
