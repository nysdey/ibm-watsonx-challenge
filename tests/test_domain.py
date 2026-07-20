from copy import deepcopy

from bobbee.domain import scoring, scheduling
from bobbee.infrastructure import demo_data


def test_demo_accounts_and_scores_are_deterministic():
    raw_one = demo_data.accounts_for_covids(["T0016156", "T0016158"], target=24)
    raw_two = demo_data.accounts_for_covids(["T0016156", "T0016158"], target=24)
    assert raw_one == raw_two
    normalized = [scoring.normalize(account) for account in raw_one]
    first = scoring.score(deepcopy(normalized))
    second = scoring.score(deepcopy(normalized))
    assert [(row["id"], row["tier"], row["score"], row["play"]) for row in first] == [
        (row["id"], row["tier"], row["score"], row["play"]) for row in second
    ]


def test_strategy_and_schedule_have_clean_references():
    accounts = [scoring.normalize(account) for account in demo_data.accounts_for_covids(["T0016156"], target=32)]
    scoring.score(accounts)
    for account in accounts:
        account["has_decision_maker"] = True
    strategy = scheduling.build_strategy(accounts, 3)
    schedule = scheduling.build_schedule(accounts, strategy, 2026)
    known_ids = {account["id"] for account in accounts}
    assert all(account_id in known_ids for ids in strategy["cadences"].values() for account_id in ids)
    assert all(item["account_id"] in known_ids for items in schedule["days"].values() for item in items)
    assert all(date_key.startswith("2026-") for date_key in schedule["days"])

