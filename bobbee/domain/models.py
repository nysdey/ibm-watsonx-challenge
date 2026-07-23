"""JSON-serializable aggregate shapes.

The app deliberately stores one small document: this is a local single-user demo,
not a system that benefits from a database server. Keeping the schema explicit here
prevents routes from inventing their own state shapes.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

SCHEMA_VERSION = 1


def empty_state() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "seller": None,
        "accounts": [],
        "strategy": None,
        "schedule": None,
        # Sent emails, one record per send. Each accumulates seller-submitted
        # star-rating feedback and (mocked) Salesloft engagement, and together
        # they form the RAG example bank email drafting retrieves from — see
        # bobbee/domain/feedback.py and bobbee/services/emails.py.
        "emails": [],
    }

