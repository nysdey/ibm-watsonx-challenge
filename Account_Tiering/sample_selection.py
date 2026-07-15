"""TEST_MODE sample selection for Step 2 onward.

Per the pipeline's global rules: in TEST_MODE, Step 2+ operate on a small,
DELIBERATELY CHOSEN sample — not the first N rows, not a random slice — so a test
run actually exercises tier diversity instead of whatever Step 1 happened to scrape
first. Selection logic is explicit and fully deterministic (same 5 accounts every
time, for a given Step 1 export), so a re-run of the test pipeline is comparable to
the last one.

The 5 slots and how each is chosen from Step 1's `Company Rollup` output:

1. Healthcare       — Industry == "Healthcare". Deterministic tiebreak: largest
                       `Distinct Locations` (a bigger, more real account is a more
                       useful test case than a single-location edge case).
2. Fintech           — Industry in {"Banking", "Financial Markets", "Insurance"}.
                       Same tiebreak.
3. High-signal proxy — Technology Client Status starts with "Existing" (an active
                        IBM relationship implies more public activity to find —
                        earnings mentions, press releases, LinkedIn presence) AND
                        has a non-blank LinkedIn URL. Tiebreak: highest
                        `IBM Spend Current Year` (a bigger existing account is more
                        likely to have real news to find, which is the actual
                        property we're trying to sample for — this is a proxy
                        computed at selection time, before Step 2's own signal
                        scraper has run, so it can't use actual signal counts).
4. Low-signal proxy  — Technology Client Status == "New (Whitespace)" AND
                        LinkedIn URL is blank AND Employee Count is blank (minimal
                        public footprint — the opposite proxy from #3). Tiebreak:
                        alphabetically first Account Name (arbitrary but stable).
5. Ground truth      — the first entry in `config.GROUND_TRUTH_ACCOUNTS` (an exact
                        `Account Name` match) that is found in this Step 1 export.
                        This list starts EMPTY — the user has not yet told us which
                        account(s) they already know the "correct" tier for. Until
                        `GROUND_TRUTH_ACCOUNTS` is populated (env var, comma-
                        separated Account Names), this slot falls back to the
                        account with the single highest `Distinct Locations` count
                        across the whole export (deterministic, but NOT a real
                        ground-truth check) and a warning is logged so this
                        limitation is visible in the run log, not silently ignored.

If a category can't be filled (e.g. no Healthcare account in this particular Step 1
export), that slot is skipped and logged — the sample may then be fewer than 5
accounts, which is preferable to silently substituting an unrelated account.

Slots are filled in the order above, and an account already claimed by an earlier
slot is never reused for a later one (checked by Account Name).
"""
import logging

logger = logging.getLogger("sample_selection")


def _is_fintech(industry):
    return industry in ("Banking", "Financial Markets", "Insurance")


def _pick(rows, predicate, tiebreak_key, exclude_names):
    candidates = [r for r in rows if r.get("Account Name") not in exclude_names and predicate(r)]
    if not candidates:
        return None
    candidates.sort(key=tiebreak_key, reverse=True)
    return candidates[0]


def select_test_sample(rows, ground_truth_accounts=()):
    """rows: list[dict] from schema_io.load_step1_accounts(). Returns list[dict],
    length <= 5, each tagged with '_test_sample_reason' explaining why it was picked
    (useful in logs/output — this is a test fixture, not silent magic)."""
    chosen = []
    claimed_names = set()

    def _distinct_locations(r):
        try:
            return int(r.get("Distinct Locations") or 0)
        except (TypeError, ValueError):
            return 0

    def _ibm_spend_cy(r):
        try:
            return float(r.get("IBM Spend Current Year") or 0)
        except (TypeError, ValueError):
            return 0.0

    healthcare = _pick(
        rows, lambda r: r.get("Industry") == "Healthcare", _distinct_locations, claimed_names
    )
    if healthcare:
        healthcare["_test_sample_reason"] = "healthcare"
        chosen.append(healthcare)
        claimed_names.add(healthcare["Account Name"])
    else:
        logger.warning("No Healthcare account found in Step 1 export — skipping that test slot.")

    fintech = _pick(
        rows, lambda r: _is_fintech(r.get("Industry")), _distinct_locations, claimed_names
    )
    if fintech:
        fintech["_test_sample_reason"] = "fintech"
        chosen.append(fintech)
        claimed_names.add(fintech["Account Name"])
    else:
        logger.warning("No fintech (Banking/Financial Markets/Insurance) account found — skipping.")

    high_signal = _pick(
        rows,
        lambda r: str(r.get("Technology Client Status") or "").startswith("Existing")
        and bool(r.get("LinkedIn URL")),
        _ibm_spend_cy,
        claimed_names,
    )
    if high_signal:
        high_signal["_test_sample_reason"] = "high_signal_proxy"
        chosen.append(high_signal)
        claimed_names.add(high_signal["Account Name"])
    else:
        logger.warning("No high-signal-proxy account found (Existing status + LinkedIn URL) — skipping.")

    # _pick sorts descending by tiebreak_key; the low-signal slot wants ascending
    # (alphabetically first) order, so the key is inverted per-character rather
    # than adding a sort-direction parameter to _pick for one caller.
    low_signal = _pick(
        rows,
        lambda r: r.get("Technology Client Status") == "New (Whitespace)"
        and not r.get("LinkedIn URL")
        and not r.get("Employee Count"),
        lambda r: "".join(chr(255 - ord(c)) for c in (r.get("Account Name") or "").lower()),
        claimed_names,
    )
    if low_signal:
        low_signal["_test_sample_reason"] = "low_signal_proxy"
        chosen.append(low_signal)
        claimed_names.add(low_signal["Account Name"])
    else:
        logger.warning("No low-signal-proxy account found (New (Whitespace) + no LinkedIn/employee data) — skipping.")

    ground_truth_row = None
    for name in ground_truth_accounts:
        match = next((r for r in rows if r.get("Account Name") == name and name not in claimed_names), None)
        if match:
            ground_truth_row = match
            ground_truth_row["_test_sample_reason"] = f"ground_truth:{name}"
            break
    if not ground_truth_row:
        if ground_truth_accounts:
            logger.warning(
                "GROUND_TRUTH_ACCOUNTS was set but none of %s were found (or all already "
                "claimed) in this Step 1 export.", ground_truth_accounts
            )
        else:
            logger.warning(
                "GROUND_TRUTH_ACCOUNTS is empty — no user-confirmed ground-truth account "
                "configured. Falling back to largest-Distinct-Locations account as a stand-in. "
                "This slot is NOT a real ground-truth check until GROUND_TRUTH_ACCOUNTS is set."
            )
        ground_truth_row = _pick(rows, lambda r: True, _distinct_locations, claimed_names)
        if ground_truth_row:
            ground_truth_row["_test_sample_reason"] = "ground_truth_fallback_no_config"
    if ground_truth_row:
        chosen.append(ground_truth_row)
        claimed_names.add(ground_truth_row["Account Name"])

    logger.info(
        "TEST_MODE sample: %d accounts selected — %s",
        len(chosen),
        [(r["Account Name"], r["_test_sample_reason"]) for r in chosen],
    )
    return chosen


def select_random_sample(rows, n):
    """Ad-hoc override for live-integration testing against real ZoomInfo/Salesloft
    (2026-07-01 goal) — true-random N-account sample, intentionally NOT seeded, so
    repeated runs exercise different real accounts rather than reproducing the same
    5-category fixture from select_test_sample(). Only accounts with a non-blank
    Account Name are eligible (same baseline as schema_io's load filter)."""
    import random

    eligible = [r for r in rows if r.get("Account Name")]
    n = min(n, len(eligible))
    chosen = random.sample(eligible, n)
    for row in chosen:
        row["_test_sample_reason"] = "random_sample"
    logger.info("RANDOM_SAMPLE_SIZE=%d: selected %s", n, [r["Account Name"] for r in chosen])
    return chosen
