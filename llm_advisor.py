"""Optional live-watsonx enrichment shared by Account Tiering (Step 4) and Call
Planning (Step 5).

Two-layer design, per the pipeline's "involve an LLM in the planning logic"
requirement:

  1. The scoring/pacing LOGIC itself was designed by an LLM (see
     Account_Tiering/tiering.py and Call_Planning/call_planning.py module
     docstrings) and runs DETERMINISTICALLY — reproducible, no network, no key
     required. This is what runs in the demo, and what decides tier numbers and
     calendar dates.

  2. This module adds a live watsonx.ai layer ON TOP that turns the numeric
     result into seller-facing judgment: for each account a Primary Play + a
     one-line Sales Angle, and for the call plan a short strategy note. It only
     ENRICHES the human-readable narrative — it never changes a tier number or
     a planned date, so results stay reproducible. It is fully fail-soft: if
     WATSONX_API_KEY / WATSONX_PROJECT_ID / WATSONX_URL aren't all set, the
     network is unavailable, or the API errors, callers keep their
     deterministic text and the pipeline runs exactly as before.

Uses the stdlib urllib against the IBM watsonx.ai REST API (IAM token exchange
+ POST /ml/v1/text/chat). Model defaults to an IBM Granite instruct model
(override with WATSONX_MODEL_ID).

Loads the repo-root .env itself (via python-dotenv) so WATSONX_* credentials
are picked up whether this module is imported by run_pipeline.py (the web app)
or run standalone (e.g. `python3 Account_Tiering/run.py` from a terminal,
which has no parent process to load .env for it). Never overrides a variable
already set in the real environment.
"""
import json
import os
import random
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

IAM_TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"
WATSONX_API_VERSION = os.environ.get("WATSONX_API_VERSION", "2024-05-31")
DEFAULT_MODEL = os.environ.get("WATSONX_MODEL_ID", "ibm/granite-4-h-small")

# Telemetry for the last live call this process made — surfaced in the UI's AI
# activity panel (Bobby, tiering) so the "is this actually calling a model"
# claim is backed by a real request, not a static label. Thread-safe: Bobby
# drafts emails from a pool of worker threads.
_LAST_CALL_LOCK = threading.Lock()
_LAST_CALL = {}

# Cached IAM bearer token — valid up to 60 minutes; refreshed a little early
# (55 min) to avoid racing expiry mid-request. Shared across the thread pool
# Bobby drafts emails from, guarded by the same lock.
_TOKEN_LOCK = threading.Lock()
_TOKEN_CACHE = {"access_token": None, "expires_at": 0.0}


def last_call_info():
    """A copy of the most recent _complete() call's telemetry (model, latency_ms,
    tokens, status), or {} if this process hasn't made a live call yet."""
    with _LAST_CALL_LOCK:
        return dict(_LAST_CALL)


def available():
    """True when a live watsonx.ai call can be attempted (API key, project id,
    and region URL are all present). Callers use this only to log which path
    they took — every function here is already safe to call unconditionally
    and returns an empty result if credentials are missing."""
    return bool(
        os.environ.get("WATSONX_API_KEY")
        and os.environ.get("WATSONX_PROJECT_ID")
        and os.environ.get("WATSONX_URL")
    )


def _get_iam_token(api_key, force=False):
    """Exchange (or reuse a cached) IBM Cloud API key for an IAM bearer token.
    Returns the token string, or None on any failure — never raises."""
    with _TOKEN_LOCK:
        now = time.monotonic()
        if not force and _TOKEN_CACHE["access_token"] and now < _TOKEN_CACHE["expires_at"]:
            return _TOKEN_CACHE["access_token"]
        data = urllib.parse.urlencode({
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey": api_key,
        }).encode("utf-8")
        req = urllib.request.Request(
            IAM_TOKEN_URL,
            data=data,
            headers={
                "content-type": "application/x-www-form-urlencoded",
                "accept": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except Exception:
            return None
        token = body.get("access_token")
        if not token:
            return None
        # expires_in is ~3600s; refresh 5 minutes early to be safe.
        expires_in = body.get("expires_in", 3600)
        _TOKEN_CACHE["access_token"] = token
        _TOKEN_CACHE["expires_at"] = now + max(60, expires_in - 300)
        return token


def _complete(system, user, max_tokens=2000, model=None, timeout=90):
    """Single watsonx.ai chat completion. Returns the assistant text, or None on
    ANY problem (missing credentials, network error, non-200, malformed body)
    — never raises, so it can be dropped into a pipeline step without a
    try/except at every call site."""
    text, _meta = complete_with_meta(system, user, max_tokens=max_tokens, model=model, timeout=timeout)
    return text


def complete_with_meta(system, user, max_tokens=2000, model=None, timeout=90):
    """Same call as _complete(), but returns (text, meta) with this specific
    call's telemetry — race-free under concurrent callers (Bobby drafts emails
    from a thread pool, so the shared _LAST_CALL global alone isn't enough to
    attribute latency/tokens to the right person). meta is {} if credentials
    aren't set."""
    api_key = os.environ.get("WATSONX_API_KEY")
    project_id = os.environ.get("WATSONX_PROJECT_ID")
    base_url = os.environ.get("WATSONX_URL")
    if not (api_key and project_id and base_url):
        return None, {}

    model_id = model or DEFAULT_MODEL
    payload = {
        "model_id": model_id,
        "project_id": project_id,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_tokens": max_tokens,
    }
    url = base_url.rstrip("/") + f"/ml/v1/text/chat?version={WATSONX_API_VERSION}"

    started = time.monotonic()
    token = _get_iam_token(api_key)
    if not token:
        return None, _record_call(model_id, started, ok=False)

    def _call(bearer):
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "content-type": "application/json",
                "accept": "application/json",
                "authorization": f"Bearer {bearer}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    # Bobby drafts emails from an 8-way thread pool, all hitting watsonx.ai at
    # once — on a Lite-plan project that reliably trips rate limiting, so most
    # of a burst would silently fall back to the template without a retry.
    # Retry transient failures (429 rate limit, 5xx, network hiccups) with
    # backoff + jitter (jitter matters: 8 threads retrying in lockstep would
    # just re-trigger the same rate limit together).
    data = None
    for attempt in range(_MAX_ATTEMPTS):
        try:
            data = _call(token)
            break
        except urllib.error.HTTPError as e:
            if e.code == 401:
                # Token may have just expired — refresh and retry immediately.
                token = _get_iam_token(api_key, force=True)
                if token:
                    continue
                break
            if e.code in _RETRYABLE_STATUS and attempt < _MAX_ATTEMPTS - 1:
                time.sleep(_retry_delay(e, attempt))
                continue
            break
        except Exception:
            if attempt < _MAX_ATTEMPTS - 1:
                time.sleep(_retry_delay(None, attempt))
                continue
            break

    if data is None:
        return None, _record_call(model_id, started, ok=False)

    choices = data.get("choices") or []
    text = ""
    if choices:
        text = (choices[0].get("message") or {}).get("content", "") or ""
    text = text.strip()
    usage = data.get("usage") or {}
    meta = _record_call(
        model_id, started, ok=bool(text),
        tokens_in=usage.get("prompt_tokens"), tokens_out=usage.get("completion_tokens"),
    )
    return (text or None), meta


_MAX_ATTEMPTS = 4  # 1 initial try + 3 retries
_RETRYABLE_STATUS = {408, 409, 429, 500, 502, 503, 504}


def _retry_delay(http_error, attempt):
    """Seconds to wait before the next retry attempt (0-indexed). Honors the
    server's Retry-After header on a 429 if present; otherwise exponential
    backoff (0.5s, 1s, 2s, ...) with jitter so parallel callers don't all
    retry in lockstep and re-trigger the same rate limit together."""
    if http_error is not None and http_error.headers:
        retry_after = http_error.headers.get("Retry-After")
        if retry_after:
            try:
                return min(float(retry_after), 10.0)
            except ValueError:
                pass
    base = 0.5 * (2 ** attempt)
    return base + random.uniform(0, base * 0.5)


def _record_call(model, started_at, ok, tokens_in=None, tokens_out=None):
    total_tokens = None
    if tokens_in is not None and tokens_out is not None:
        total_tokens = tokens_in + tokens_out
    meta = {
        "model": model,
        "status": "success" if ok else "error",
        "latency_ms": round((time.monotonic() - started_at) * 1000),
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "tokens_total": total_tokens,
        "at": time.time(),
    }
    with _LAST_CALL_LOCK:
        _LAST_CALL.update(meta)
    return meta


def _extract_json(text):
    """Pull the first JSON value out of a model reply, tolerating ```json fences
    and surrounding prose. Returns the parsed object/list, or None."""
    if not text:
        return None
    t = text.strip()
    if t.startswith("```"):
        # ```json ... ```  ->  inner block
        segments = t.split("```")
        if len(segments) >= 2:
            t = segments[1]
        if t.lstrip().lower().startswith("json"):
            t = t.lstrip()[4:]
    for open_c, close_c in (("[", "]"), ("{", "}")):
        i, j = t.find(open_c), t.rfind(close_c)
        if 0 <= i < j:
            try:
                return json.loads(t[i:j + 1])
            except Exception:
                continue
    return None


_TIER_SYSTEM = (
    "You are a senior IBM infrastructure sales strategist coaching a phone-based "
    "seller. For each account you are given the deterministic tier and the raw "
    "sales signals behind it (IBM relationship, spend trend, IBM install "
    "footprint, competitor footprint, size, vertical, buying signals). Your job "
    "is NOT to re-score — trust the tier. Your job is to name the single best "
    "PLAY and give one sharp, specific reason to call, in a seller's voice. "
    "Be concrete: reference the actual installs / competitors / spend movement, "
    "never generic filler. Return ONLY JSON."
)

# Play labels the deterministic classifier also uses — keeping the LLM on the
# same vocabulary makes the two paths interchangeable in the UI.
PLAYS = [
    "Expand & Protect", "Displace Competitor", "Hardware Refresh",
    "Land New Logo", "Win-Back", "Nurture",
]


def advise_accounts(accounts, max_accounts=120):
    """accounts: list of compact per-account intel dicts (see
    Account_Tiering/tiering.py's _llm_intel). Returns
    {account_name: {"play": str, "angle": str}} for whatever the model returned,
    or {} when the live layer is unavailable/errored (caller keeps its
    deterministic Play/Angle). One batched call for the whole run, not one per
    account."""
    if not accounts or not available():
        return {}
    compact = accounts[:max_accounts]
    user = (
        "Accounts (JSON):\n" + json.dumps(compact, indent=2, default=str) +
        "\n\nReturn a JSON array, one object per account, each: "
        '{"account": <exact account name>, "play": <one of ' + json.dumps(PLAYS) +
        '>, "angle": <=140 chars, one specific reason to call this account now>}.'
    )
    parsed = _extract_json(_complete(_TIER_SYSTEM, user, max_tokens=4000))
    if not isinstance(parsed, list):
        return {}
    out = {}
    for item in parsed:
        if isinstance(item, dict) and item.get("account"):
            play = str(item.get("play", "")).strip()
            angle = str(item.get("angle", "")).strip()
            if angle:
                out[item["account"]] = {"play": play, "angle": angle}
    return out


_PLAN_SYSTEM = (
    "You are a sales-operations planner. Given a call-plan's shape (how many "
    "accounts, how they're tiered, how many working days remain in the year, and "
    "the per-day pacing), write a 2-sentence coaching note the seller sees at the "
    "top of their calendar: what to prioritize and why the plan is front-loaded. "
    "Plain, concrete, no fluff. Return ONLY the two sentences, no preamble."
)


def advise_plan_summary(stats):
    """stats: dict with keys like total_accounts, tier_counts, working_days,
    per_day_target, front_load_days. Returns a short string, or "" when
    unavailable (caller falls back to a deterministic sentence)."""
    if not available():
        return ""
    text = _complete(_PLAN_SYSTEM, json.dumps(stats, default=str), max_tokens=250)
    return (text or "").strip()
