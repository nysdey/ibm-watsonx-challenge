"""Deterministic account normalization and scoring."""

from __future__ import annotations

import math
import statistics
from typing import Iterable

from bobbee.infrastructure import demo_data

CORE_VERTICALS = {
    "Healthcare", "Government, Central/Federal",
    "Government, State/Provincial/Local", "Banking", "Financial Markets", "Insurance",
}
ADJACENT_VERTICALS = {
    "Telecommunications", "Life Sciences", "Retail", "Manufacturing", "Energy & Utilities",
}
RELATIONSHIP_SCORES = {
    "Existing (Continued)": 100, "Existing": 80, "Existing (PY New Client)": 80,
    "New (Active)": 55, "New (Pending)": 45, "New (Whitespace)": 30, "New (Dormant)": 15,
}
SIGNAL_POINTS = {
    "Funding": 30, "M&A": 30, "Expansion": 25, "Regulatory_Compliance": 20,
    "Security_Incident": 20, "Leadership_Change": 15, "Partnership": 15,
    "Product_Launch": 15, "ESG_Commitment": 10, "Earnings_Financial": 10,
    "Layoffs_Restructuring": -10,
}


def _install_counts(name: str, relationship: str) -> dict[str, int]:
    rng = demo_data._rng("web_installs", name)
    existing = relationship.startswith("Existing")
    return {
        "cloud": rng.randint(1, 5) if rng.random() < (0.62 if existing else 0.18) else 0,
        "power": rng.randint(1, 14) if rng.random() < (0.52 if existing else 0.10) else 0,
        "storage": rng.randint(1, 18) if rng.random() < (0.58 if existing else 0.12) else 0,
        "software": rng.randint(1, 12) if rng.random() < (0.44 if existing else 0.15) else 0,
        "competitive": rng.randint(2, 80) if rng.random() < 0.42 else 0,
    }


def normalize(raw: dict) -> dict:
    name = raw["name"]
    relationship = raw.get("tech_client_status") or "New (Whitespace)"
    zi = demo_data.zoominfo_enrichment(name)
    signals = [{
        "type": item["Type"],
        "date": item["Date"],
        "summary": item["Summary"],
        "source_url": item["Source_URL"],
    } for item in demo_data.signals_for(name)]
    return {
        "id": raw["account_number"],
        "name": name,
        "industry": raw.get("industry"),
        "sub_industry": raw.get("sub_industry"),
        "state": raw.get("state"),
        "city": raw.get("city"),
        "location": f"{raw.get('city')}, {raw.get('state')}",
        "coverage_ids": raw.get("coverage_ids", []),
        "relationship": relationship,
        "contact_count": raw.get("contact_count") or 0,
        "employees": raw.get("employees") or zi.get("ZI_Employee_Count"),
        "revenue": raw.get("location_revenue") or zi.get("ZI_Revenue_USD"),
        "global_revenue": raw.get("global_revenue"),
        "ibm_spend_current": raw.get("ibm_spend_current") or 0,
        "ibm_spend_prior": raw.get("ibm_spend_prior") or 0,
        "installs": _install_counts(name, relationship),
        "signals": signals,
        "tier": None,
        "score": None,
        "spend_trend": None,
        "play": None,
        "angle": None,
        "tags": [],
        "bucket": "unranked",
        "cadence": None,
        "rank": None,
    }


def _trend(current: float, prior: float) -> tuple[str, int]:
    if not prior:
        return ("New", 8) if current else ("Unknown", 0)
    if current >= prior * 1.10:
        return "Growing", 12
    if current <= prior * 0.90:
        return "Declining", -12
    return "Flat", 0


def _normalized_log(values: Iterable[float | int | None]) -> dict[float, float]:
    present = sorted(float(value) for value in values if value not in (None, 0))
    if not present:
        return {}
    logged = [math.log10(value + 1) for value in present]
    low, high = min(logged), max(logged)
    return {
        original: (100.0 if high == low else (logged_value - low) / (high - low) * 100)
        for original, logged_value in zip(present, logged)
    }


def _play(account: dict) -> str:
    installs = account["installs"]
    ibm_depth = sum(installs[key] for key in ("cloud", "power", "storage", "software"))
    relationship = account["relationship"]
    if relationship.startswith("New") and ibm_depth == 0:
        return "Land New Logo"
    if account["spend_trend"] == "Declining":
        return "Win-Back"
    if installs["competitive"] >= 20 and installs["competitive"] > ibm_depth:
        return "Displace Competitor"
    if installs["power"] + installs["storage"]:
        return "Hardware Refresh"
    if ibm_depth:
        return "Expand & Protect"
    return "Nurture"


def _tags(account: dict) -> list[str]:
    installs = account["installs"]
    labels = {"cloud": "Cloud", "power": "Power", "storage": "Storage", "software": "NonInfra"}
    tags = [f"Whitespace: {label}" for key, label in labels.items() if not installs[key]]
    if installs["cloud"]:
        tags.insert(0, "Bluemix footprint")
    if installs["competitive"]:
        tags.append("Competitive displacement")
    if account["spend_trend"] == "Growing":
        tags.append("Growing spend")
    elif account["spend_trend"] == "Declining":
        tags.append("At-risk spend")
    return tags


def score(accounts: list[dict]) -> list[dict]:
    revenue_scores = _normalized_log(account.get("revenue") for account in accounts)
    employee_scores = _normalized_log(account.get("employees") for account in accounts)
    revenue_default = statistics.median(revenue_scores.values()) if revenue_scores else 50
    employee_default = statistics.median(employee_scores.values()) if employee_scores else 50

    for account in accounts:
        trend, adjustment = _trend(account["ibm_spend_current"], account["ibm_spend_prior"])
        account["spend_trend"] = trend
        relationship = max(0, min(100, RELATIONSHIP_SCORES.get(account["relationship"], 25) + adjustment))
        size = 0.6 * revenue_scores.get(float(account.get("revenue") or 0), revenue_default)
        size += 0.4 * employee_scores.get(float(account.get("employees") or 0), employee_default)
        vertical = 100 if account["industry"] in CORE_VERTICALS else (70 if account["industry"] in ADJACENT_VERTICALS else 45)
        installs = account["installs"]
        footprint = min(100, installs["cloud"] * 6 + installs["power"] * 4 + installs["storage"] * 4 + installs["software"] * 3)
        displacement = min(100, installs["competitive"] * 2)
        signals = max(0, min(100, sum(SIGNAL_POINTS.get(item["type"], 0) for item in account["signals"])))
        contactability = min(100, 20 + math.log10(account["contact_count"] + 1) * 40) if account["contact_count"] else 0
        account["score"] = round(
            relationship * .22 + size * .20 + footprint * .15 + displacement * .13
            + vertical * .12 + signals * .10 + contactability * .08,
            1,
        )

    ranked = sorted(accounts, key=lambda account: account["score"], reverse=True)
    tier_one = math.ceil(len(ranked) * .20)
    tier_two = tier_one + math.ceil(len(ranked) * .35)
    for index, account in enumerate(ranked):
        account["tier"] = 1 if index < tier_one else (2 if index < tier_two else 3)
        account["play"] = _play(account)
        account["tags"] = _tags(account)
        signal = account["signals"][0]["type"].replace("_", " ").lower() if account["signals"] else "account fit"
        account["angle"] = f"Lead with {account['play'].lower()}; the strongest current signal is {signal}."
    return accounts

