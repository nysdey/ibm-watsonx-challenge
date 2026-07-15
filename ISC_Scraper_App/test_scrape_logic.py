"""Session-free correctness tests for the scraper's not-miss logic.

The live "random-territory" confirmation (reliability_test.py) needs an ISC
login. But a whole class of "misses" would come from the scraper CODE itself,
independent of any live session — e.g. dropping accounts past page 1 of a big
territory, or accepting a cold-cache 0 without retrying. Those are verifiable
right now by driving scrape_cov_id against synthetic aura responses.

    ISC_Scraper_App/.venv/bin/python3 test_scrape_logic.py
"""
import sys
from pathlib import Path

INTERNAL = Path(__file__).resolve().parent / "_internal"
sys.path.insert(0, str(INTERNAL))
import http_scraper as hs


def _resp(results, total):
    return {"actions": [{"returnValue": {"returnValue": {
        "numberOfAccounts": total, "results": results}}}]}


def _accounts(n, start=0):
    return [{"DOM_COMP_NAME": f"Company {i}"} for i in range(start, start + n)]


def test_paginates_all_pages():
    """A 700-account territory must return all 700 rows across 3 pages — the
    core 'don't miss large lists' property."""
    total = 700
    pages = [_accounts(300, 0), _accounts(300, 300), _accounts(100, 600)]
    calls = {"n": 0}

    def fake_post(cookies, token, ctx, method, params, headers=None):
        i = calls["n"]; calls["n"] += 1
        return _resp(pages[i] if i < len(pages) else [], total)

    hs._aura_post = fake_post
    rows = hs.scrape_cov_id("T_TEST", "listid", {}, "t", {}, {})
    assert len(rows) == 700, f"expected 700 rows, got {len(rows)} (pagination dropped accounts!)"
    print(f"  PASS paginates_all_pages: assembled all {len(rows)} rows across 3 pages")


def test_retries_cold_cache_zero(monkeypatch_sleep):
    """A cold-cache 0 on the first call must be recovered by the built-in
    retry, not accepted as an empty territory."""
    seq = [_resp([], 0), _resp([], 0), _resp(_accounts(42), 42)]
    calls = {"n": 0}

    def fake_post(cookies, token, ctx, method, params, headers=None):
        i = calls["n"]; calls["n"] += 1
        return seq[i] if i < len(seq) else _resp([], 42)

    hs._aura_post = fake_post
    rows = hs.scrape_cov_id("T_TEST", "listid", {}, "t", {}, {})
    assert len(rows) == 42, f"expected 42 rows after cold-cache retry, got {len(rows)}"
    print(f"  PASS retries_cold_cache_zero: recovered {len(rows)} rows after two empty responses")


def test_genuinely_empty_stays_empty(monkeypatch_sleep):
    """A territory that is 0 on every attempt must return 0 (no false rows)."""
    def fake_post(cookies, token, ctx, method, params, headers=None):
        return _resp([], 0)
    hs._aura_post = fake_post
    rows = hs.scrape_cov_id("T_EMPTY", "listid", {}, "t", {}, {})
    assert rows == [], f"expected 0 rows for a truly-empty territory, got {len(rows)}"
    print("  PASS genuinely_empty_stays_empty: 0 stays 0 (no fabricated rows)")


def test_count_extraction():
    """numberOfAccounts / results must be read from the real nested shape."""
    accounts, total = hs._extract_rows(_resp(_accounts(5), 5))
    assert total == 5 and len(accounts) == 5, f"extract mismatch: total={total} n={len(accounts)}"
    print("  PASS count_extraction: nested returnValue shape parsed correctly")


def main():
    import time
    orig_post, orig_sleep = hs._aura_post, time.sleep
    time.sleep = lambda *_a, **_k: None  # skip the retry backoff waits
    failures = 0
    for name, fn in [
        ("paginates_all_pages", test_paginates_all_pages),
        ("retries_cold_cache_zero", lambda: test_retries_cold_cache_zero(True)),
        ("genuinely_empty_stays_empty", lambda: test_genuinely_empty_stays_empty(True)),
        ("count_extraction", test_count_extraction),
    ]:
        try:
            fn()
        except AssertionError as e:
            failures += 1
            print(f"  FAIL {name}: {e}")
        finally:
            hs._aura_post = orig_post
    time.sleep = orig_sleep
    print("\nVERDICT:", "PASS — scraper logic cannot silently drop accounts"
          if not failures else f"FAIL — {failures} test(s) failed")
    sys.exit(0 if not failures else 1)


if __name__ == "__main__":
    main()
