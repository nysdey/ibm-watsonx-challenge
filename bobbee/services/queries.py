"""Read models tailored to the browser UI.

Routes do no data shaping. They validate HTTP inputs and return these query
results, keeping presentation contracts independently testable.
"""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta
import hashlib

from bobbee.domain.constants import CADENCE_DESCRIPTIONS, DECISION_MAKER_TITLES
from bobbee.domain.time import next_weekday, today, workday
from bobbee.infrastructure import demo_data
from bobbee.infrastructure.repository import JsonRepository


def _money(value) -> str:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "—"
    magnitude = abs(value)
    if magnitude >= 1e9:
        return f"${value / 1e9:.1f}B"
    if magnitude >= 1e6:
        return f"${value / 1e6:.1f}M"
    if magnitude >= 1e3:
        return f"${value / 1e3:.0f}K"
    return f"${value:,.0f}"


def _account_index(state: dict) -> dict[str, dict]:
    return {account["id"]: account for account in state.get("accounts") or []}


def _name_index(state: dict) -> dict[str, dict]:
    return {account["name"]: account for account in state.get("accounts") or []}


def _install_summary(account: dict) -> str:
    labels = {"power": "Power", "storage": "Storage", "cloud": "Cloud", "software": "Non-Infra"}
    parts = [f"{label}×{account['installs'][key]}" for key, label in labels.items() if account["installs"].get(key)]
    return " · ".join(parts) if parts else "No IBM installs"


class AccountQueries:
    def __init__(self, repository: JsonRepository):
        self.repository = repository

    def seller(self, email: str | None) -> dict:
        seller = self.repository.load().get("seller") or {}
        return {
            "signed_in": bool(email),
            "email": email,
            "matched": bool(seller),
            "seller_name": seller.get("seller_name"),
            "covids": len(seller.get("covids") or []),
        }

    def accounts(self) -> dict:
        state = self.repository.load()
        accounts = state.get("accounts") or []
        if not accounts:
            return {"has_accounts": False}
        strategy = state.get("strategy")
        response = [{
            "account": account["name"],
            "industry": account["industry"],
            "install": _install_summary(account),
            "location": account["location"],
            "tags": account.get("tags") or [],
            "cadence": account.get("cadence"),
            "rank": account.get("rank"),
            "tier": account.get("tier"),
            "bucket": account.get("bucket", "unranked"),
        } for account in accounts]
        if not strategy:
            return {"has_accounts": True, "strategized": False, "accounts": response}
        return {
            "has_accounts": True,
            "strategized": True,
            "current_quarter": strategy["current_quarter"],
            "accounts": response,
            "lists": {
                "cadences": {name: len(ids) for name, ids in strategy["cadences"].items()},
                "leftovers": len(strategy["leftovers"]),
                "no_contacts": len(strategy["no_contacts"]),
                "future": sum(len(ids) for ids in strategy["other_quarters"].values()),
                "all": len(accounts),
            },
        }

    def detail(self, name: str) -> dict | None:
        state = self.repository.load()
        account = _name_index(state).get(name)
        if not account:
            return None
        contacts = []
        for raw in demo_data.contacts_for_accounts([name]):
            contacts.append({
                "first_name": raw.get("first_name"),
                "last_name": raw.get("last_name"),
                "title": raw.get("title"),
                "company": raw.get("company"),
                "email": raw.get("work_email"),
                "work_email": raw.get("work_email"),
                "direct_phone": raw.get("direct_phone"),
                "decision_maker": raw.get("title") in DECISION_MAKER_TITLES,
            })
        touches = []
        for iso, activities in (state.get("schedule") or {}).get("days", {}).items():
            touches.extend({"date": iso, "type": item["type"], "step": item["step"]}
                           for item in activities if item.get("account_id") == account["id"])
        whitespace = [tag.split(": ", 1)[1] for tag in account.get("tags", []) if tag.startswith("Whitespace: ")]
        product = {
            "Cloud": "IBM Cloud", "Power": "IBM Power", "Storage": "IBM Storage", "NonInfra": "IBM Software"
        }.get(whitespace[0], "Expand existing footprint") if whitespace else "Expand existing footprint"
        urgency = {1: "High", 2: "Medium", 3: "Low"}.get(account.get("tier"), "Not yet scored")
        return {
            "account": name,
            "sales_cloud": {
                "industry": account["industry"],
                "coverage_id": ", ".join(account["coverage_ids"]),
                "relationship": account["relationship"],
                "ibm_spend_current": account["ibm_spend_current"],
                "ibm_spend_prior": account["ibm_spend_prior"],
                "spend_trend": account.get("spend_trend"),
                "install_summary": _install_summary(account),
            },
            "zoominfo": {
                "revenue": account["revenue"],
                "employees": account["employees"],
                "contacts": contacts,
            },
            "salesloft": {
                "cadence": account.get("cadence"),
                "rank": account.get("rank"),
                "touches": sorted(touches, key=lambda item: item["date"]),
            },
            "signals": account["signals"],
            "tags": account.get("tags") or [],
            "ai": {
                "urgency": urgency,
                "tier": account.get("tier"),
                "score": account.get("score"),
                "product": product,
                "product_fit": product,
                "play": account.get("play"),
                "angle": account.get("angle"),
            },
        }

    def details(self, names: list[str]) -> dict:
        return {name: detail for name in names if (detail := self.detail(name)) is not None}

    def named_bucket(self, name: str) -> list[str]:
        state = self.repository.load()
        strategy = state.get("strategy") or {}
        ids = strategy.get(name, [])
        index = _account_index(state)
        return [index[account_id]["name"] for account_id in ids if account_id in index]

    def other_quarters(self) -> dict:
        state = self.repository.load()
        strategy = state.get("strategy") or {}
        index = _account_index(state)
        return {
            "current_quarter": strategy.get("current_quarter"),
            "other": {
                label: [index[account_id]["name"] for account_id in ids if account_id in index]
                for label, ids in strategy.get("other_quarters", {}).items()
            },
        }

    def schedule(self) -> dict:
        schedule = self.repository.load().get("schedule")
        if not schedule:
            return {"has_schedule": False}
        days = {}
        for iso, activities in schedule["days"].items():
            days[iso] = {
                "emails": sum(item["type"] == "email" for item in activities),
                "calls": sum(item["type"] == "call" for item in activities),
                "accounts": sorted({item["account"] for item in activities}),
                "items": activities,
            }
        return {
            "has_schedule": True,
            "quarter": schedule["quarter"],
            "q_start": schedule["q_start"],
            "q_end": schedule["q_end"],
            "days": days,
        }

    def cadences(self) -> dict:
        state = self.repository.load()
        strategy, schedule = state.get("strategy"), state.get("schedule")
        if not strategy:
            return {"has_cadences": False}
        index = _account_index(state)
        current = today().isoformat()
        result = []
        for name, ids in strategy["cadences"].items():
            next_touch, last_touch = {}, {}
            for iso, activities in (schedule or {}).get("days", {}).items():
                for activity in activities:
                    account_id = activity["account_id"]
                    touch = {"step": activity["step"], "date": iso, "type": activity["type"]}
                    if iso >= current and account_id not in next_touch:
                        next_touch[account_id] = touch
                    if iso <= current:
                        last_touch[account_id] = touch
            members = []
            for account_id in ids:
                account = index[account_id]
                previous, upcoming = last_touch.get(account_id), next_touch.get(account_id)
                status = "not_started" if previous is None else ("completed" if upcoming is None else "in_progress")
                members.append({
                    "account": account["name"], "rank": account["rank"],
                    "industry": account["industry"], "tier": account["tier"],
                    "tags": account["tags"], "status": status,
                    "next_touch": upcoming, "last_touch": previous,
                })
            result.append({
                "name": name,
                "description": CADENCE_DESCRIPTIONS.get(name, "Outbound cadence."),
                "account_count": len(members),
                "steps": [{
                    "day": step["day"],
                    "type": {"phone": "Call", "email": "Email", "other": "Other"}.get(step["type"], step["type"]),
                    "name": step["name"], "step_number": step["step_number"],
                } for step in demo_data.salesloft_cadence_steps(name)],
                "accounts": members,
            })
        return {"has_cadences": True, "cadences": result}

    def brief_context(self, name: str) -> tuple[dict, list[str]]:
        detail = self.detail(name)
        if not detail:
            return {"account": name}, ["No account intelligence is available yet."]
        sc, zi, ai = detail["sales_cloud"], detail["zoominfo"], detail["ai"]
        decision_maker = next((contact for contact in zi["contacts"] if contact["decision_maker"]), None)
        context = {
            "account": name,
            "sales_cloud": sc,
            "zoominfo": {
                "annual_revenue": zi["revenue"], "employees": zi["employees"],
                "decision_maker": (
                    f"{decision_maker['first_name']} {decision_maker['last_name']}, {decision_maker['title']}"
                    if decision_maker else None
                ),
            },
            "salesloft": detail["salesloft"],
            "recent_news": detail["signals"],
            "recommended_play": ai["play"],
            "best_product_fit": ai["product_fit"],
            "urgency": ai["urgency"],
            "sales_angle": ai["angle"],
        }
        bullets = [
            f"Relationship: {sc['relationship']} · IBM spend {_money(sc['ibm_spend_current'])} vs {_money(sc['ibm_spend_prior'])} prior year.",
            f"Install base: {sc['install_summary']}.",
            f"Company: {_money(zi['revenue'])} revenue · {zi['employees'] or '—'} employees.",
        ]
        if decision_maker:
            bullets.append(f"Key contact: {decision_maker['first_name']} {decision_maker['last_name']}, {decision_maker['title']}.")
        if detail["signals"]:
            signal = detail["signals"][0]
            bullets.append(f"Recent signal ({signal['date']}): {signal['summary']}")
        bullets.append(f"Play: {ai['play']} · best fit {ai['product_fit']} · urgency {ai['urgency']}.")
        if ai["angle"]:
            bullets.append(f"Why call now: {ai['angle']}")
        return context, bullets


class DashboardQueries:
    def __init__(self, repository: JsonRepository):
        self.repository = repository

    def _state_schedule(self) -> tuple[dict, dict | None]:
        state = self.repository.load()
        return state, state.get("schedule")

    def dashboard(self) -> dict:
        _state, schedule = self._state_schedule()
        if not schedule:
            return {"has_schedule": False}
        focus = workday().isoformat()
        items = schedule["days"].get(focus, [])
        return {"has_schedule": True, "today": {"date": focus, "items": items}}

    def today(self) -> dict:
        state, schedule = self._state_schedule()
        if not schedule:
            return {"has_schedule": False}
        real_day, focus_day = today(), workday()
        activities = schedule["days"].get(focus_day.isoformat(), [])
        week_start = real_day - timedelta(days=real_day.weekday())
        week_end = week_start + timedelta(days=6)
        weekly = [
            (datetime.strptime(iso, "%Y-%m-%d").date(), item)
            for iso, items in schedule["days"].items()
            if week_start <= datetime.strptime(iso, "%Y-%m-%d").date() <= week_end
            for item in items
        ]
        account_count = len({item["account"] for item in activities})
        emails = sum(item["type"] == "email" for item in activities)
        calls = sum(item["type"] == "call" for item in activities)
        brief = (
            f"You have {account_count} accounts to engage today. "
            f"I’ve prepared {emails} emails and {calls} call briefs. Start at the top; "
            "the list is ranked by account urgency and cadence position."
        )
        return {
            "has_schedule": True,
            "looking_ahead": focus_day != real_day,
            "date_label": real_day.strftime("%A, %B %-d"),
            "focus_label": focus_day.strftime("%A, %B %-d"),
            "brief": brief,
            "pace": {"done": sum(day <= real_day for day, _item in weekly),
                     "total": len(weekly)},
            "moves": activities,
        }

    def progress(self, period: str, offset: int) -> dict:
        _state, schedule = self._state_schedule()
        if not schedule:
            return {"has_schedule": False}
        current = today()
        if period == "day":
            anchor = current + timedelta(days=offset)
            low = high = anchor
            keys = [(anchor.strftime("%a"), low, high)]
        elif period == "week":
            anchor = current + timedelta(weeks=offset)
            low = anchor - timedelta(days=anchor.weekday())
            high = low + timedelta(days=6)
            keys = [((low + timedelta(days=index)).strftime("%a"), low + timedelta(days=index), low + timedelta(days=index)) for index in range(7)]
        elif period == "month":
            month_index = current.month - 1 + offset
            low = date(current.year + month_index // 12, month_index % 12 + 1, 1)
            high = (low + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            keys = []
            cursor = low
            while cursor <= high:
                label = f"Wk {((cursor.day + low.weekday() - 1) // 7) + 1}"
                if not keys or keys[-1][0] != label:
                    week_high = min(high, cursor + timedelta(days=6 - cursor.weekday()))
                    keys.append((label, cursor, week_high))
                cursor = keys[-1][2] + timedelta(days=1)
        else:
            quarter_index = ((current.month - 1) // 3) + offset
            year = current.year + quarter_index // 4
            q = quarter_index % 4
            low = date(year, q * 3 + 1, 1)
            high = (date(year + (q == 3), 1 if q == 3 else q * 3 + 4, 1) - timedelta(days=1))
            keys = []
            cursor = low
            while cursor <= high:
                next_month = (cursor + timedelta(days=32)).replace(day=1)
                keys.append((cursor.strftime("%b"), cursor, min(high, next_month - timedelta(days=1))))
                cursor = next_month

        parsed = {datetime.strptime(iso, "%Y-%m-%d").date(): items for iso, items in schedule["days"].items()}
        series = []
        for label, start, end in keys:
            items = [item for day, activities in parsed.items() if start <= day <= end for item in activities]
            series.append({
                "label": label,
                "emails": sum(item["type"] == "email" for item in items),
                "calls": sum(item["type"] == "call" for item in items),
                "accounts": len({item["account"] for item in items}),
            })
        window_items = [(day, item) for day, activities in parsed.items() if low <= day <= high for item in activities]
        labels = {"day": low.strftime("%A, %B %-d"), "week": f"Week of {low.strftime('%B %-d')}",
                  "month": low.strftime("%B %Y"), "quarter": f"Q{(low.month - 1) // 3 + 1} {low.year}"}
        return {
            "has_schedule": True, "period": period, "offset": offset, "label": labels[period],
            "series": series,
            "totals": {"emails": sum(item["emails"] for item in series),
                       "calls": sum(item["calls"] for item in series),
                       "accounts": len({item["account"] for _, item in window_items})},
            "elapsed": sum(day <= current for day, _ in window_items),
            "upcoming": sum(day > current for day, _ in window_items),
            "today_short": current.strftime("%a"), "today_month": current.strftime("%b"),
        }

    @staticmethod
    def _draw(name: str, salt: str) -> float:
        digest = hashlib.md5(f"{salt}:{name}".encode()).hexdigest()
        return int(digest[:8], 16) % 1000 / 10

    def meetings(self, schedule: dict, scope: str, offset: int) -> dict:
        current = today()
        low = high = None
        if scope == "week":
            anchor = current + timedelta(weeks=offset)
            low, high = anchor - timedelta(days=anchor.weekday()), anchor + timedelta(days=6-anchor.weekday())
        first_touch = {}
        for iso, activities in schedule["days"].items():
            day = datetime.strptime(iso, "%Y-%m-%d").date()
            if low and not low <= day <= high:
                continue
            for item in activities:
                first_touch[item["account"]] = min(day, first_touch.get(item["account"], day))
        total = booked = completed = upcoming = cancelled = oi_count = oi_value = 0
        for name, touch in first_touch.items():
            if self._draw(name, "book") >= 24:
                continue
            total += 1
            if self._draw(name, "cancel") < 9:
                cancelled += 1
                continue
            booked += 1
            if next_weekday(touch + timedelta(days=7)) <= current:
                completed += 1
                if self._draw(name, "oi") < 46:
                    oi_count += 1
                    oi_value += 40000 + int(self._draw(name, "amount") / 100 * 36) * 10000
            else:
                upcoming += 1
        return {
            "total": total, "booked": booked, "completed": completed,
            "upcoming": upcoming, "cancelled": cancelled, "oi_count": oi_count,
            "oi_value": oi_value, "worked_accounts": len(first_touch), "scope": scope,
            "offset": offset,
            "label": f"Week of {low.strftime('%B %-d')}" if low else f"Q{(current.month-1)//3+1} {current.year} to date",
        }

    def book(self, scope: str, offset: int) -> dict:
        state, schedule = self._state_schedule()
        accounts = state.get("accounts") or []
        if not accounts:
            return {"has_accounts": False}
        industries = Counter(account["industry"] or "Unknown" for account in accounts)
        territories = Counter(account["state"] for account in accounts)
        covered = sum(bool(account.get("cadence")) for account in accounts)
        top = lambda values, size: [{"label": label, "value": count} for label, count in values.most_common(size)]
        return {
            "has_accounts": True, "total": len(accounts), "covered": covered,
            "spend": round(sum(account["ibm_spend_current"] for account in accounts)),
            "industry_count": len(industries), "industries": top(industries, 6),
            "territories": top(territories, 6),
            "meetings": self.meetings(schedule, scope, offset) if schedule else None,
        }

    def territory(self, view: str) -> dict:
        state = self.repository.load()
        accounts = state.get("accounts") or []
        if not accounts:
            return {"has_accounts": False}
        meta, industries, cities = {}, {}, {}
        for account in accounts:
            territory = account["state"]
            meta.setdefault(territory, {"accounts": 0, "cadences": 0, "spend": 0})
            meta[territory]["accounts"] += 1
            meta[territory]["cadences"] += bool(account.get("cadence"))
            meta[territory]["spend"] += account["ibm_spend_current"]
            industries.setdefault(territory, set()).add(account["industry"])
            cities.setdefault(territory, Counter())[account["city"]] += 1
        values = {
            territory: (details[view] if view in {"accounts", "cadences", "spend"} else len(industries[territory]))
            for territory, details in meta.items()
        }
        labels = {"accounts": "Accounts", "cadences": "In a Q3 cadence",
                  "spend": "IBM spend (current year)", "industries": "Distinct industries"}
        return {
            "has_accounts": True, "view": view, "label": labels[view],
            "format": "currency" if view == "spend" else "number",
            "values": values, "max": max(values.values(), default=0),
            "total": round(sum(values.values())), "states_covered": sum(bool(value) for value in values.values()),
            "detail": meta, "cities": {key: dict(value) for key, value in cities.items()},
        }
