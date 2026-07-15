"""Bobby's email writer.

Given a prospect (first name, title, company) and the cadence email step they're on
(which day / step number), produce a personalized {subject, body}. Uses Claude when
ANTHROPIC_API_KEY is set (via the repo-root llm_advisor's Anthropic client), and
otherwise falls back to a deterministic, still-personalized template — so Bobby always
produces real, per-person emails whether or not a key is configured.
"""
import json
import logging
import sys
from pathlib import Path

# Reuse the shared Anthropic client (stdlib urllib, fail-soft) from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import llm_advisor  # noqa: E402

logger = logging.getLogger("bobby.emailer")

_SYSTEM = (
    "You are Bobby, an AI SDR writing outbound sales emails on behalf of an IBM "
    "infrastructure seller (Power, Storage, Cloud, and software). You write concise, "
    "specific, human-sounding emails — no fluff, no 'I hope this finds you well'. You "
    "personalize to the prospect's ROLE and COMPANY and to WHERE they are in the "
    "outreach cadence (an early step is a first-touch intro; a later step is a "
    "follow-up or a short break-up). Keep the body under ~110 words. Return ONLY JSON."
)


def _cadence_intent(step_number, day):
    if step_number <= 1:
        return "first touch — a crisp intro that earns a reply"
    if step_number == 2:
        return "second touch — add one concrete piece of value and a soft ask"
    return "later touch — brief, a little more direct, easy to say yes or no to"


def generate_email(person, step, cadence_name):
    """Returns {"subject": str, "body": str, "source": "claude"|"template"}."""
    first = (person.get("first_name") or "there").strip()
    title = (person.get("title") or "").strip()
    company = (person.get("company") or "").strip()
    day = step.get("day") or 1
    step_no = step.get("step_number") or 1
    intent = _cadence_intent(step_no, day)

    if llm_advisor.available():
        user = (
            "Write one outbound email.\n"
            f"Prospect first name: {first}\n"
            f"Prospect title: {title or 'unknown'}\n"
            f"Prospect company: {company or 'unknown'}\n"
            f"Cadence: {cadence_name}\n"
            f"This is cadence Day {day}, email step {step_no} — {intent}.\n\n"
            'Return JSON: {"subject": <=70 chars, "body": the email body with a greeting '
            'and a sign-off placeholder "[Your name]"}. Reference their role/company '
            "specifically; tie it to an IBM infrastructure angle."
        )
        parsed = llm_advisor._extract_json(llm_advisor._complete(_SYSTEM, user, max_tokens=600))
        if isinstance(parsed, dict) and parsed.get("body"):
            return {
                "subject": str(parsed.get("subject") or _fallback_subject(company, step_no)).strip(),
                "body": str(parsed["body"]).strip(),
                "source": "claude",
            }
        logger.info("Claude returned no usable email for %s — using template.", first)

    return _template_email(first, title, company, cadence_name, day, step_no)


def _fallback_subject(company, step_no):
    if step_no <= 1:
        return f"Infrastructure at {company}" if company else "A quick idea for your team"
    if step_no == 2:
        return f"Following up — {company}" if company else "Following up"
    return "Worth a quick chat?"


def _template_email(first, title, company, cadence_name, day, step_no):
    """Deterministic, personalized fallback — varies by cadence step."""
    role_line = f"as {title}" if title else "in your role"
    co = company or "your company"
    if step_no <= 1:
        body = (
            f"Hi {first},\n\n"
            f"I work with infrastructure teams on IBM Power, Storage, and hybrid-cloud "
            f"projects, and reached out because {role_line} at {co} you likely own "
            f"decisions about performance, resiliency, and cost of the core environment.\n\n"
            f"Worth a 15-minute call to compare notes on what peers are doing this quarter?\n\n"
            f"Best,\n[Your name]"
        )
    elif step_no == 2:
        body = (
            f"Hi {first},\n\n"
            f"Following up on my note. Teams like {co}'s are using IBM infrastructure to "
            f"cut refresh cost and tighten resiliency without re-platforming. Given your "
            f"focus {role_line}, I think one idea in particular would land.\n\n"
            f"Open to a short call this week or next?\n\n"
            f"Best,\n[Your name]"
        )
    else:
        body = (
            f"Hi {first},\n\n"
            f"I'll keep this short — if modernizing the infrastructure at {co} is on your "
            f"radar this year, I'd love 15 minutes. If the timing's off, just let me know "
            f"and I'll circle back later in the year.\n\n"
            f"Best,\n[Your name]"
        )
    return {"subject": _fallback_subject(company, step_no), "body": body, "source": "template"}
