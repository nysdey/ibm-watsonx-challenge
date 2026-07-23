"""Commands that mutate the seller's book of business."""

from __future__ import annotations

from datetime import datetime, timezone

from bobbee.domain import scoring, scheduling
from bobbee.domain.constants import DECISION_MAKER_TITLES
from bobbee.domain.time import quarter, today
from bobbee.infrastructure import demo_data, territories
from bobbee.infrastructure.repository import JsonRepository
from bobbee.integrations import watsonx


class AccountService:
    def __init__(self, repository: JsonRepository, target_accounts: int = 1911):
        self.repository = repository
        self.target_accounts = target_accounts

    def resolve_seller(self, email: str) -> dict:
        try:
            seller = territories.resolve_seller(email)
        except (FileNotFoundError, ValueError):
            seller = {"matched": False, "seller_name": None, "covids": []}
        if not seller.get("covids"):
            seller["covids"] = demo_data.demo_covids_for_email(email)
        if not seller.get("seller_name"):
            seller["seller_name"] = email.split("@", 1)[0].replace(".", " ").replace("_", " ").title()
        seller["email"] = email
        return seller

    def import_accounts(self, email: str, progress) -> None:
        progress(phase="territory", message="Resolving your territory…")
        seller = self.resolve_seller(email)
        progress(
            phase="accounts",
            message=f"Building the account book for {len(seller['covids'])} coverage IDs…",
            seller=seller["seller_name"],
            covids=len(seller["covids"]),
        )
        raw_accounts = demo_data.accounts_for_covids(
            seller["covids"], target=self.target_accounts
        )
        accounts = []
        for index, raw in enumerate(raw_accounts, 1):
            accounts.append(scoring.normalize(raw))
            if index % 250 == 0:
                progress(
                    phase="accounts",
                    message=f"Prepared {index:,} of {len(raw_accounts):,} accounts…",
                    counts={"prepared": index, "total": len(raw_accounts)},
                )
        state = {
            "schema_version": 1,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "seller": seller,
            "accounts": accounts,
            "strategy": None,
            "schedule": None,
            "emails": [],
        }
        self.repository.save(state)
        progress(
            active=False,
            done=True,
            phase="done",
            message=f"Your accounts are ready — {len(accounts):,} accounts imported.",
            counts={"prepared": len(accounts), "total": len(accounts)},
        )

    def strategize(self, progress) -> None:
        state = self.repository.load()
        accounts = state.get("accounts") or []
        if not accounts:
            raise RuntimeError("Import accounts first — there is no account book to strategize.")

        progress(phase="contacts", message="Checking decision-maker coverage…")
        no_contacts = 0
        for index, account in enumerate(accounts, 1):
            contacts = demo_data.contacts_for_accounts([account["name"]])
            account["has_decision_maker"] = any(
                contact.get("title") in DECISION_MAKER_TITLES for contact in contacts
            )
            no_contacts += not account["has_decision_maker"]
            if index % 250 == 0:
                progress(
                    phase="contacts",
                    message=f"Checked {index:,} of {len(accounts):,} accounts…",
                    counts={"checked": index, "total": len(accounts), "no_contacts": no_contacts},
                )

        progress(phase="scoring", message="Scoring account fit and urgency…")
        scoring.score(accounts)

        if watsonx.available():
            progress(phase="ai", message="Asking Granite to refine plays and sales angles…")
            advice = watsonx.advise_accounts([{
                "account": account["name"],
                "tier": account["tier"],
                "industry": account["industry"],
                "relationship": account["relationship"],
                "spend_trend": account["spend_trend"],
                "ibm_spend_current": account["ibm_spend_current"],
                "ibm_install": account["installs"],
                "revenue": account["revenue"],
                "employees": account["employees"],
                "contacts": account["contact_count"],
                "signals": [signal["type"] for signal in account["signals"]],
                "deterministic_play": account["play"],
            } for account in accounts])
            for account in accounts:
                item = advice.get(account["name"], {})
                account["play"] = item.get("play") or account["play"]
                account["angle"] = item.get("angle") or account["angle"]

        current_quarter = quarter()
        progress(phase="cadences", message="Assigning and ranking cadences…")
        strategy = scheduling.build_strategy(accounts, current_quarter)
        progress(phase="schedule", message="Distributing touches across the quarter…")
        schedule = scheduling.build_schedule(accounts, strategy, today().year)

        state.update(
            accounts=accounts,
            strategy=strategy,
            schedule=schedule,
            updated_at=datetime.now(timezone.utc).isoformat(),
        )
        self.repository.save(state)
        cadence_total = sum(len(members) for members in strategy["cadences"].values())
        activity_total = sum(len(items) for items in schedule["days"].values())
        progress(
            active=False,
            done=True,
            phase="done",
            message=f"Done — {cadence_total} accounts and {activity_total} scheduled touches.",
            counts={
                "total": len(accounts),
                "no_contacts": len(strategy["no_contacts"]),
                "leftovers": len(strategy["leftovers"]),
                "cadences": {name: len(ids) for name, ids in strategy["cadences"].items()},
                "scheduled_activities": activity_total,
            },
        )

