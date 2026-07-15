"""Optional live-Claude enrichment shared by Account Tiering (Step 4) and Call
Planning (Step 5).

Two-layer design, per the pipeline's "involve an LLM in the planning logic"
requirement:

  1. The scoring/pacing LOGIC itself was designed by an LLM (see
     Account_Tiering/tiering.py and Call_Planning/call_planning.py module
     docstrings) and runs DETERMINISTICALLY — reproducible, no network, no key
     required. This is what runs in the demo, and what decides tier numbers and
     calendar dates.

  2. This module adds a live Claude layer ON TOP that turns the numeric result
     into seller-facing judgment: for each account a Primary Play + a one-line
     Sales Angle, and for the call plan a short strategy note. It only ENRICHES
     the human-readable narrative — it never changes a tier number or a planned
     date, so results stay reproducible. It is fully fail-soft: if
     ANTHROPIC_API_KEY isn't set, the network is unavailable, or the API errors,
     callers keep their deterministic text and the pipeline runs exactly as
     before.

Uses the stdlib urllib against the Anthropic Messages API, so there is no new
package dependency. Model defaults to Claude Opus 4.8 (override with LLM_MODEL).
"""
import json
import os
import urllib.error
import urllib.request

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_MODEL = os.environ.get("LLM_MODEL", "claude-opus-4-8")


def available():
    """True when a live Claude call can be attempted (an API key is present).
    Callers use this only to log which path they took — every function here is
    already safe to call unconditionally and returns an empty result if the key
    is missing."""
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def _complete(system, user, max_tokens=2000, model=None, timeout=90):
    """Single Messages API call. Returns the assistant text, or None on ANY
    problem (missing key, network error, non-200, malformed body) — never
    raises, so it can be dropped into a pipeline step without a try/except at
    every call site."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    payload = {
        "model": model or DEFAULT_MODEL,
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    req = urllib.request.Request(
        ANTHROPIC_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "content-type": "application/json",
            "x-api-key": key,
            "anthropic-version": ANTHROPIC_VERSION,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        parts = [b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"]
        text = "".join(parts).strip()
        return text or None
    except Exception:
        return None


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
