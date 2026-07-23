"""Sent-email tracking, seller feedback, and the RAG training-data bank.

This is the feedback loop: every send is recorded, the seller can rate it,
(mocked) Salesloft engagement fills in over the following demo days, and the
emails that clear the quality bar become few-shot examples watsonx retrieves
the next time it drafts — see EmailService.top_examples_for_prompt and
bobbee/integrations/watsonx.py's advise_email(examples=...).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from bobbee.domain import feedback as feedback_domain
from bobbee.domain.time import today
from bobbee.infrastructure import demo_data
from bobbee.infrastructure.repository import JsonRepository


class EmailService:
    def __init__(self, repository: JsonRepository):
        self.repository = repository

    # ── commands ─────────────────────────────────────────────────────────
    def record_sent(self, *, account, industry=None, tier=None, play=None,
                     contact_first=None, contact_last=None, contact_title=None,
                     cadence=None, step=None, subject, body, source=None) -> dict:
        record = {
            "id": uuid.uuid4().hex[:12],
            "account": account,
            "industry": industry,
            "tier": tier,
            "play": play,
            "contact": {"first_name": contact_first, "last_name": contact_last, "title": contact_title},
            "cadence": cadence,
            "step": step,
            "subject": subject,
            "body": body,
            "source": source,
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "sent_date": today().isoformat(),
            "feedback": None,
        }

        def change(state):
            state.setdefault("emails", []).append(record)

        self.repository.update(change)
        return record

    def submit_feedback(self, email_id: str, ratings: dict, notes: str | None) -> dict | None:
        result = {}

        def change(state):
            for record in state.get("emails") or []:
                if record["id"] == email_id:
                    record["feedback"] = {
                        "ratings": ratings,
                        "notes": (notes or "").strip(),
                        "submitted_at": datetime.now(timezone.utc).isoformat(),
                    }
                    result.update(record)
                    break

        self.repository.update(change)
        return result or None

    # ── read models ──────────────────────────────────────────────────────
    def _engagement(self, record: dict) -> dict:
        try:
            sent_date = datetime.strptime(record["sent_date"], "%Y-%m-%d").date()
            days_elapsed = max(0, (today() - sent_date).days)
        except (KeyError, ValueError):
            days_elapsed = 0
        return demo_data.mock_engagement(record["id"], days_elapsed, record.get("tier"))

    def _scored(self, record: dict) -> dict:
        engagement = self._engagement(record)
        feedback = record.get("feedback") or {}
        ratings = feedback.get("ratings") or {}
        score = feedback_domain.composite_score(ratings, engagement)
        badges = feedback_domain.badges_for(score)
        contact = record.get("contact") or {}
        style = feedback_domain.style_tags(
            record.get("subject"), record.get("body"),
            first_name=contact.get("first_name"), account=record.get("account"),
        )
        return {
            "id": record["id"],
            "account": record["account"],
            "industry": record.get("industry"),
            "cadence": record.get("cadence"),
            "step": record.get("step"),
            "subject": record.get("subject"),
            "body": record.get("body"),
            "prompt": f"Generate email for {record['account']} contact about {record.get('play') or record.get('step') or 'outreach'}",
            "sent_at": record.get("sent_at"),
            "score": score,
            "badges": badges,
            "is_training_example": bool(badges),
            "style_tags": style,
            "engagement": engagement,
            "ratings": ratings,
            "notes": feedback.get("notes"),
            "has_feedback": bool(feedback),
        }

    def email_status(self, email_id: str) -> dict | None:
        state = self.repository.load()
        for record in state.get("emails") or []:
            if record["id"] == email_id:
                return self._scored(record)
        return None

    def training_data(self, query: str = "") -> dict:
        state = self.repository.load()
        rows = [self._scored(r) for r in (state.get("emails") or []) if r.get("feedback")]
        rows = [r for r in rows if r["is_training_example"]]
        rows.sort(key=lambda r: r["score"], reverse=True)
        if query:
            q = query.strip().lower()
            rows = [
                r for r in rows
                if q in (r["account"] or "").lower()
                or q in (r["industry"] or "").lower()
                or q in (r["subject"] or "").lower()
            ]
        return {"count": len(rows), "examples": rows}

    def top_examples_for_prompt(self, industry: str | None = None, limit: int = 2) -> list[dict]:
        """The live RAG retrieval call: the best rated + best performing sent
        emails, preferring ones from the same industry as the account being
        drafted for. Returns [] until at least one email has cleared the
        quality bar, so the caller (watsonx.advise_email) can fall back to its
        static exemplars — a cold-start problem, not an error."""
        state = self.repository.load()
        scored = [self._scored(r) for r in (state.get("emails") or []) if r.get("feedback")]
        scored = [r for r in scored if r["is_training_example"]]
        if not scored:
            return []
        scored.sort(key=lambda r: (r["industry"] == industry, r["score"]), reverse=True)
        return [{"subject": r["subject"], "body": r["body"], "tags": r["style_tags"]} for r in scored[:limit]]
