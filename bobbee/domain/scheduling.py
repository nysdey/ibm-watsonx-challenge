"""Cadence assignment and quarter scheduling rules."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

from bobbee.domain.constants import CADENCE_CAP, PLAY_TO_CADENCE, STARTS_PER_DAY
from bobbee.domain.time import next_weekday, quarter_bounds
from bobbee.infrastructure import demo_data


def assigned_quarter(account_name: str) -> int:
    return demo_data._rng("account_quarter", account_name).randint(1, 4)


def build_strategy(accounts: list[dict], current_quarter: int) -> dict:
    no_contacts = [account for account in accounts if not account.get("has_decision_maker")]
    eligible = [account for account in accounts if account.get("has_decision_maker")]
    quarters = {number: [] for number in range(1, 5)}
    for account in eligible:
        quarters[assigned_quarter(account["name"])].append(account)

    cadences: dict[str, list[dict]] = {}
    for account in quarters[current_quarter]:
        cadence = PLAY_TO_CADENCE.get(account["play"], "Targeted Outreach Cadence 3")
        cadences.setdefault(cadence, []).append(account)

    leftovers: list[dict] = []
    for cadence, members in cadences.items():
        members.sort(key=lambda account: account["score"], reverse=True)
        leftovers.extend(members[CADENCE_CAP:])
        cadences[cadence] = members[:CADENCE_CAP]
        for rank, account in enumerate(cadences[cadence], 1):
            account.update(bucket="cadence", cadence=cadence, rank=rank)

    for account in no_contacts:
        account["bucket"] = "no_contacts"
    for account in leftovers:
        account["bucket"] = "leftovers"
    for number, members in quarters.items():
        if number != current_quarter:
            for account in members:
                account["bucket"] = "future"

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "current_quarter": current_quarter,
        "cadences": {name: [account["id"] for account in members] for name, members in cadences.items()},
        "no_contacts": [account["id"] for account in no_contacts],
        "leftovers": [account["id"] for account in leftovers],
        "other_quarters": {
            f"Q{number}": [account["id"] for account in members]
            for number, members in quarters.items() if number != current_quarter
        },
    }


def build_schedule(accounts: list[dict], strategy: dict, year: int) -> dict:
    by_id = {account["id"]: account for account in accounts}
    number = strategy["current_quarter"]
    start, end = quarter_bounds(number, year)
    queue: list[tuple[str, dict]] = []
    longest = max((len(members) for members in strategy["cadences"].values()), default=0)
    for index in range(longest):
        for cadence, ids in strategy["cadences"].items():
            if index < len(ids):
                queue.append((cadence, by_id[ids[index]]))

    days: dict[str, list[dict]] = {}
    start_day, started = next_weekday(start), 0
    for cadence, account in queue:
        if start_day > end:
            break
        for step in demo_data.salesloft_cadence_steps(cadence):
            if step["type"] not in {"email", "phone"}:
                continue
            activity_day = next_weekday(start_day + timedelta(days=step["day"] - 1))
            if activity_day <= end:
                days.setdefault(activity_day.isoformat(), []).append({
                    "account": account["name"],
                    "account_id": account["id"],
                    "cadence": cadence,
                    "type": "email" if step["type"] == "email" else "call",
                    "step": step["name"],
                })
        started += 1
        if started >= STARTS_PER_DAY:
            start_day, started = next_weekday(start_day + timedelta(days=1)), 0

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "quarter": number,
        "q_start": start.isoformat(),
        "q_end": end.isoformat(),
        "days": dict(sorted(days.items())),
    }

