"""Web signal scraper — Step 2 data gathering, part 2.

For each account, searches recent news for buying/risk signals matching the taxonomy in
SIGNAL_DEFINITIONS.md (read that first) and returns a dynamic-width list of signal
dicts per account.

Backend: **Google News RSS** (`news.google.com/rss/search`), queried via urllib only
(no `requests` dependency, matching ISC_Scraper_App's convention). This replaced the
old DuckDuckGo HTML endpoint (2026-07-10), which bot-challenged (CAPTCHA) essentially
every query from this network and so returned zero real signals. Google News RSS is a
public feed: no key, no JS, not bot-blocked, and — unlike the old backend — it carries
a real `pubDate`, so signal dates are genuine instead of blank.

Precision matters more than recall here: a wrong signal ("this account just did an
M&A") shown to a seller is worse than a missed one. Two guardrails enforce that:
  1. The cleaned company name must LEAD the headline (news headlines lead with their
     subject) — this rejects articles that merely mention the company in passing
     (e.g. a rival's acquisition that name-drops it), the main false-positive class.
  2. Only news within SIGNAL_RECENCY_DAYS counts — a two-year-old funding round is
     not a current buying signal.

Checkpointed and resumable: `checkpoints/signals_checkpoint.json` records one entry
per Account Name as soon as it's processed, so a re-run only processes accounts not
already resolved.
"""
import email.utils
import json
import logging
import os
import re
import threading
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone

import config

import sys as _sys
_sys.path.insert(0, str(config.STEP_DIR.parent))
import fake_data  # noqa: E402  (BobBee: buying signals are mocked)

logger = logging.getLogger("signal_scraper")

CHECKPOINT_PATH = config.CHECKPOINT_DIR / "signals_checkpoint.json"

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search"

# Signal lookups are independent HTTP fetches of a public feed, so they parallelize
# cleanly (unlike the browser-driven ZoomInfo step) — this is what keeps signal
# gathering to seconds even for a full account pool.
SIGNAL_WORKERS = int(os.environ.get("SIGNAL_WORKERS", "8"))

# News older than this isn't a *current* buying signal (≈18 months).
SIGNAL_RECENCY_DAYS = 550

# A single comprehensive query per account: the quoted (cleaned) company name plus an
# OR-bag of signal verbs. One request covers the whole taxonomy — Google News returns
# up to ~100 items, which is plenty. Keep this a list so the batch loop is unchanged.
QUERY_TEMPLATES = [
    '"{name}" (acquisition OR merger OR acquires OR funding OR raises OR partnership '
    'OR "new CEO" OR appoints OR layoffs OR "lays off" OR expansion OR earnings '
    'OR restructuring OR lawsuit OR breach)',
]

# Keyword -> taxonomy type. Checked against the headline, first match wins (ordered so
# more specific/high-value categories are checked before generic ones).
KEYWORD_TO_TYPE = [
    (r"\b(data breach|ransomware|cyberattack|security incident|hacked)\b", "Security_Incident"),
    (r"\b(acquir\w*|merger|merges with|to be acquired|buyout|takeover|to acquire)\b", "M&A"),
    (r"\b(series [a-e]\b|raises \$|raises [0-9]|funding round|venture capital|\bipo\b|secures \$)\b", "Funding"),
    (r"\b(net.zero|sustainability report|esg commitment|carbon neutral)\b", "ESG_Commitment"),
    (r"\b(names new|appoints|steps down|resigns|new ceo|new cfo|new ciso|new cio|names .* (ceo|cfo|cio|president))\b", "Leadership_Change"),
    (r"\b(opens new|new facility|new plant|expands into|new office|expansion|to open|breaks ground)\b", "Expansion"),
    (r"\b(q[1-4] (earnings|results)|quarterly results|annual report|beats estimates|earnings call|reports .* (revenue|profit))\b", "Earnings_Financial"),
    (r"\b(partners with|strategic partnership|teams up with|collaborat\w+ with)\b", "Partnership"),
    (r"\b(launches|unveils|announces new|new platform|rolls out)\b", "Product_Launch"),
    (r"\b(layoffs|lays off|job cuts|restructuring|plant closure|to cut \d+|cutting \d+)\b", "Layoffs_Restructuring"),
    (r"\b(sec fine|regulatory action|fined by|compliance violation|lawsuit|settlement|to pay \$)\b", "Regulatory_Compliance"),
]

MAX_SIGNALS_PER_ACCOUNT = 5

# Legal/entity suffixes + geographic filler stripped from a name before it becomes a
# search query, so "ADVENTIST HEALTH (WEST)" searches as "Adventist Health" (the actual
# newsworthy entity) rather than an over-specific phrase that matches nothing.
_LEGAL_TOKENS = re.compile(
    r"\b(inc|incorporated|llc|l\.l\.c|llp|lp|ltd|limited|corp|corporation|co|company|"
    r"plc|group|holdings?|the|usa)\b\.?", re.I)


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    date: str = ""   # ISO YYYY-MM-DD when known (Google News pubDate), else ""


class SearchBlocked(Exception):
    """Raised when the search backend is unreachable/challenged for EVERY query of an
    account (not "zero results" — an outage). With the Google News RSS backend this is
    rare (it's a public feed), but the distinction is preserved so a backend outage is
    retried next run rather than silently recorded as "this account has no signals."
    """


def clean_company_name(name):
    """Newsworthy core of a company name for searching: drop parentheticals, legal
    suffixes, and punctuation. 'ADVENTIST HEALTH (WEST)' -> 'ADVENTIST HEALTH'."""
    n = re.sub(r"\([^)]*\)", " ", str(name or ""))
    n = _LEGAL_TOKENS.sub(" ", n)
    n = re.sub(r"[^A-Za-z0-9&\s]", " ", n)
    return re.sub(r"\s+", " ", n).strip()


def _parse_pubdate(raw):
    try:
        return email.utils.parsedate_to_datetime(raw)
    except Exception:
        return None


def search_google_news(query, timeout=15):
    """Recent-news search via Google News RSS. Returns a list of SearchResult (with
    real dates). Returns [] on a transient network/parse error — one bad query
    shouldn't abort an account. Raises SearchBlocked only if the feed is outright
    unreachable in a way that will recur (handled by the caller as retry-next-run)."""
    url = GOOGLE_NEWS_RSS + "?" + urllib.parse.urlencode(
        {"q": query, "hl": "en-US", "gl": "US", "ceid": "US:en"})
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
    except Exception as e:
        logger.warning("Google News search failed for query %r: %s", query, e)
        return []
    try:
        root = ET.fromstring(body)
    except Exception as e:
        logger.warning("Google News returned unparseable content for %r: %s", query, e)
        return []
    results = []
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        if not title:
            continue
        dt = _parse_pubdate(item.findtext("pubDate") or "")
        results.append(SearchResult(
            title=title,
            url=(item.findtext("link") or "").strip(),
            snippet=title,
            date=dt.date().isoformat() if dt else "",
        ))
    return results


def classify(text):
    text_lower = text.lower()
    for pattern, sig_type in KEYWORD_TO_TYPE:
        if re.search(pattern, text_lower):
            return sig_type
    return None


def _leads_headline(core_lower, title_lower):
    """True when the company name is the SUBJECT of the headline — it appears at the
    very start (allowing a short lead-in like 'The '). This is the precision guard
    that rejects passing mentions ('Rival Corp acquires X, name-dropping Acme')."""
    pos = title_lower.find(core_lower)
    return 0 <= pos <= 5


def gather_signals_for_account(account_name):
    """Returns a list of signal dicts: {Type, Date, Summary, Source_URL}, at most one
    per taxonomy type (the most recent), capped at MAX_SIGNALS_PER_ACCOUNT and ordered
    most-recent-first. Date is a real ISO date from the news item's pubDate.

    BobBee: signals are synthesized deterministically per account name by
    ``fake_data`` instead of fetched from Google News — no network. The search/
    classify/recency helpers above are kept intact (unused by this mock) so the module's
    public surface and taxonomy are unchanged.
    """
    return fake_data.signals_for(account_name)[:MAX_SIGNALS_PER_ACCOUNT]


def _iso_to_dt(iso):
    if not iso:
        return None
    try:
        return datetime.strptime(iso, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _load_checkpoint():
    if CHECKPOINT_PATH.exists():
        return json.loads(CHECKPOINT_PATH.read_text())
    return {}


def _save_checkpoint(state):
    tmp = CHECKPOINT_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2))
    tmp.replace(CHECKPOINT_PATH)  # atomic, avoids a torn write on crash mid-save


def _resolve_one(name):
    """Signal-gather one account -> a checkpoint entry dict. Never raises."""
    try:
        signals = gather_signals_for_account(name)
        return {"status": "ok", "signals": signals, "timestamp": datetime.now().isoformat()}
    except SearchBlocked as e:
        return {"status": "blocked", "error": str(e), "signals": [],
                "timestamp": datetime.now().isoformat()}
    except Exception as e:  # noqa: BLE001 - best-effort, one account never aborts the batch
        return {"status": "failed", "error": str(e), "signals": [],
                "timestamp": datetime.now().isoformat()}


def gather_signals_for_accounts(account_names):
    """Resumable batch entry point. Returns {account_name: [signal dicts]}.

    Runs up to SIGNAL_WORKERS lookups concurrently — each is an independent Google
    News RSS fetch, so this scales to seconds even for a large pool. Checkpoint writes
    are serialized under a lock. An account whose checkpoint status is "blocked" is NOT
    treated as resolved — it's re-attempted next run (a backend outage is transient,
    not a fact about that account)."""
    state = _load_checkpoint()
    todo = [n for n in account_names
            if not (n in state and state[n]["status"] != "blocked")]
    for n in account_names:
        if n not in todo:
            logger.info("Skipping %s — already in signals checkpoint", n)
    if not todo:
        return {name: state[name]["signals"] for name in account_names if name in state}

    lock = threading.Lock()
    blocked_names = []
    done = 0
    workers = max(1, min(SIGNAL_WORKERS, len(todo)))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_resolve_one, name): name for name in todo}
        for fut in as_completed(futures):
            name = futures[fut]
            entry = fut.result()
            with lock:
                state[name] = entry
                if entry["status"] == "blocked":
                    blocked_names.append(name)
                _save_checkpoint(state)
                done += 1
            n_sig = len(entry.get("signals") or [])
            if entry["status"] == "ok":
                logger.info("[%d/%d] %s: %d signal(s) found", done, len(todo), name, n_sig)
            else:
                logger.info("[%d/%d] %s: %s", done, len(todo), name, entry["status"])

    if blocked_names:
        logger.error(
            "%d/%d account(s) hit a signal-backend outage this run and were NOT "
            "meaningfully searched: %s. They'll be retried next run.",
            len(blocked_names), len(account_names), blocked_names,
        )
    return {name: state[name]["signals"] for name in account_names if name in state}
