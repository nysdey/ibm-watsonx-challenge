"""Deterministic scoring for the email feedback / RAG training-data loop.

Two inputs feed a training example's quality: the seller's own star ratings
and (mocked) Salesloft engagement. Nothing here calls watsonx or touches
storage — same separation as bobbee/domain/scoring.py.
"""

from __future__ import annotations

import re

RATING_KEYS = ("relevance", "personalization", "clarity", "cta_strength", "tone")

RATING_LABELS = {
    "relevance": "Relevance to Prospect",
    "personalization": "Personalization Quality",
    "clarity": "Clarity & Conciseness",
    "cta_strength": "Call-to-Action Strength",
    "tone": "Professional Tone",
}

# Star ratings can carry an email to 70 of 100 points on their own; engagement
# (opened/clicked/replied) contributes the remaining 30. A well-rated email
# that nobody opens still qualifies as "good"; a well-rated email that also
# got a reply is what earns "top".
_RATING_WEIGHT = 70
_ENGAGEMENT_POINTS = {"opened": 8, "clicked": 10, "replied": 12}

_TIER_THRESHOLDS = (("top", 88), ("high", 78), ("good", 65))

TIER_BADGES = {
    "top": ("Good Example", "Top Example"),
    "high": ("Good Example", "High Priority"),
    "good": ("Good Example",),
    None: (),
}


def composite_score(ratings: dict, engagement: dict) -> float:
    """0-100 quality score for one sent email. `ratings` holds whichever of
    RATING_KEYS the seller filled in (1-5 each); `engagement` is the dict
    returned by demo_data.mock_engagement (or the real Salesloft shape later —
    same three boolean keys)."""
    values = [ratings[key] for key in RATING_KEYS if ratings.get(key)]
    rating_avg = (sum(values) / len(values)) if values else 0.0
    score = (rating_avg / 5) * _RATING_WEIGHT
    score += sum(points for flag, points in _ENGAGEMENT_POINTS.items() if engagement.get(flag))
    return round(min(100.0, score), 1)


def classify(score: float) -> str | None:
    """Which quality tier a score falls into, or None if it doesn't clear the
    bar to be a training example at all."""
    for label, threshold in _TIER_THRESHOLDS:
        if score >= threshold:
            return label
    return None


def badges_for(score: float) -> list[str]:
    return list(TIER_BADGES[classify(score)])


_TIMELY_RE = re.compile(r"\brecent(ly)?\b|\bnoticed\b|\bsaw\b|\bannounced\b|\bthis (week|month|quarter)\b", re.I)
_METRIC_RE = re.compile(r"\d+%|\$\s?\d|\b\d+(\.\d+)?\s?(PB|TB|GB|FTE)\b", re.I)
_SOCIAL_RE = re.compile(r"\bhelped\b|\bteams like\b|\bcustomers\b|\bclients\b|\bsimilar\b|\bpeer\b|\bothers\b", re.I)


def style_tags(subject: str, body: str, first_name: str | None = None, account: str | None = None) -> list[str]:
    """Lightweight content tags shown on a training-data card (Personalized,
    Timely, etc.) — heuristic, not a claim about ground truth."""
    text = f"{subject or ''}\n{body or ''}"
    tags = []
    if (first_name and first_name.lower() in (body or "").lower()) or (account and account.lower() in text.lower()):
        tags.append("Personalized")
    if _TIMELY_RE.search(text):
        tags.append("Timely")
    if _METRIC_RE.search(text):
        tags.append("Specific metrics")
    if _SOCIAL_RE.search(text):
        tags.append("Social proof")
    return tags
