"""Account commands and query endpoints."""

import hashlib

from flask import Blueprint, jsonify, request, session

from bobbee.integrations import watsonx

from .helpers import services

blueprint = Blueprint("accounts", __name__, url_prefix="/api")


def _deterministic_email(name: str, first: str, step: str, context: dict) -> dict:
    """A varied, on-brand fallback draft when watsonx is unavailable.

    Structure, subject and CTA change by cadence step, and a per-account seed
    picks between phrasings and weaves in real context (product fit, angle,
    install base, latest signal) so each draft reads distinctly rather than
    from one template.
    """
    sc = context.get("sales_cloud") or {}
    product = context.get("best_product_fit") or "IBM's infrastructure platform"
    play = context.get("recommended_play") or ""
    install = sc.get("install_summary") or ""
    relationship = (sc.get("relationship") or "").lower()
    news = context.get("recent_news") or []
    signal = (news[0].get("summary") if news and isinstance(news[0], dict) else "") or ""
    # The stored "angle" is seller advice ("Lead with ..."), not email copy — so we
    # build a grammatical goal phrase (an infinitive) from the recommended play and
    # slot it after "to" / "help you" / "how to" so the sentences read cleanly.
    goal = {
        "Displace Competitor": "move workloads off a competing platform onto IBM",
        "Land New Logo": "get a first IBM workload into your environment",
        "Win-Back": "rebuild momentum where IBM spend has slipped",
        "Hardware Refresh": "modernize the infrastructure that's due for a refresh",
        "Expand & Protect": "expand what's already working and protect the estate",
        "Nurture": "line up the right next step for when the timing is right",
    }.get(play, "modernize your infrastructure")
    step_l = step.lower()
    # Subject, opener, value line and CTA are each hashed independently, so two
    # accounts on the *same* cadence step still land on different combinations.
    def pick(options, key):
        idx = int(hashlib.md5(f"{name}|{step}|{key}".encode("utf-8")).hexdigest(), 16) % len(options)
        return options[idx]

    sig = f" I also saw that {signal[0].lower() + signal[1:]}." if signal else ""

    if "intro" in step_l:
        subjects = [f"{product} at {name}", f"An idea for {name}'s roadmap",
                    f"Worth a quick look, {first}?", f"{first} — a thought on {name}'s stack",
                    f"Helping {name} move faster"]
        openers = [f"Hi {first},\n\nI partner with teams like yours on {product}.",
                   f"Hi {first},\n\nReaching out because {name}'s footprint lines up with what we're seeing work in {product}.",
                   f"Hi {first},\n\nQuick introduction — I focus on {product} for {relationship or 'growing'} organizations.",
                   f"Hi {first},\n\nI'll keep this short."]
        values = [f"Teams like {name} are usually looking to {goal}, and {product} is where that tends to start.{sig}",
                  f"A few {relationship or 'similar'}-stage teams have used {product} to {goal} without adding headcount.{sig}",
                  f"The short version of why I'm writing: I think we can help you {goal}.{sig}",
                  f"Most groups in your position begin by working out how to {goal}.{sig}"]
        ctas = ["Would a 20-minute intro next week be useful?",
                "Open to a short conversation to see if it's relevant?",
                "Could we find 15 minutes this week?",
                "Worth a quick call to see if it maps to your priorities?"]
    elif "value" in step_l or "follow" in step_l:
        subjects = [f"Following up — {product} for {name}", f"One more angle for {name}",
                    f"{first}, a concrete next step", f"Where {product} usually starts",
                    f"A quick idea for {name}"]
        openers = [f"Hi {first},\n\nCircling back on my last note.",
                   f"Hi {first},\n\nAdding a little more color to why I reached out.",
                   f"Hi {first},\n\nFollowing the thread from last week.",
                   f"Hi {first},\n\nOne concrete thought since we haven't connected yet."]
        values = [f"The reason {product} tends to fit {name}: it's the cleanest way to {goal}, and there's usually a small first step to scope together.",
                  f"Teams with a {relationship or 'comparable'} profile typically use {product} to {goal}.{sig}",
                  f"The fastest win for most groups in your position is to {goal}.",
                  f"Practically, we could map a small pilot around {product} — enough to {goal} — in a couple of weeks."]
        ctas = ["Happy to walk through it — does Thursday work?",
                f"Want me to put together a short overview tailored to {name}?",
                "Would 20 minutes this week be worth it?",
                "Should I sketch out what a first step could look like?"]
    elif "case" in step_l or "study" in step_l:
        subjects = [f"How a similar team approached this", f"A {relationship or 'peer'} example for {name}",
                    f"{first} — thought this might resonate", f"A parallel to {name}",
                    f"What worked for a team like yours"]
        openers = [f"Hi {first},\n\nSharing a quick example that reminded me of {name}.",
                   f"Hi {first},\n\nThought of {name} while reviewing a recent {product} rollout.",
                   f"Hi {first},\n\nA short story that might be relevant.",
                   f"Hi {first},\n\nNo pitch here — just a comparison I thought you'd find useful."]
        values = [f"A comparable organization used {product} to {goal}, and the outcome was a measurable step-change without a rip-and-replace.",
                  f"They started from a situation a lot like yours{('— ' + signal) if signal else ''}, and got to value in weeks.",
                  f"The parallel to {name} is close: same {relationship or 'stage'}, same push to {goal}.",
                  f"What made the difference was sequencing — {play or product} first, everything else after."]
        ctas = [f"If useful, I can send the write-up or walk through the parallels to {name}.",
                "Would a short call to compare notes be worthwhile?",
                "Want the one-page version?",
                "Happy to tailor it to your environment if you're curious."]
    else:  # break-up / re-engage
        subjects = [f"Should I close the loop, {first}?", f"Last note on {product} for {name}",
                    f"Timing on {name}", f"Closing the loop for now",
                    f"{first} — I'll step back"]
        openers = [f"Hi {first},\n\nI don't want to crowd your inbox, so this is my last note for now.",
                   f"Hi {first},\n\nIt seems the timing may not be right — no problem at all.",
                   f"Hi {first},\n\nI'll take the hint and step back for now.",
                   f"Hi {first},\n\nOne final note, then I'll get out of your inbox."]
        values = [f"If helping you {goal} lands on the roadmap this year, I'm glad to pick it back up.",
                  f"If {product} becomes a priority for {name}, my door is open.",
                  f"Should the priorities shift, I'm one reply away.",
                  f"No urgency at all — I just didn't want to keep chasing without a reason."]
        ctas = ["Just reply and I'll pick things back up.",
                "Wishing you a strong quarter.",
                "Either way, thanks for the time.",
                "Happy to reconnect whenever it's useful."]

    body = "\n\n".join([pick(openers, "open"), pick(values, "value"), pick(ctas, "cta")])
    subject = pick(subjects, "subject")
    return {"subject": subject, "body": body + "\n\nBest,\n[Your name]"}


@blueprint.get("/status")
def status():
    service = services()
    state = service.repository.load()
    account_count = len(state.get("accounts") or [])
    return jsonify({
        "segment": {"state": "done", "rows": account_count} if account_count else {"state": "pending", "rows": 0},
        "_actions": {
            "get_my_accounts": service.jobs.status("import_accounts"),
            "strategize": service.jobs.status("strategize"),
        },
    })


@blueprint.post("/get_my_accounts/run")
def import_accounts():
    email = session.get("email")
    if not email:
        return jsonify({"ok": False, "error": "sign in first"}), 401
    service = services()
    started = service.jobs.start(
        "import_accounts", lambda progress: service.accounts.import_accounts(email, progress)
    )
    return jsonify({"ok": started, "error": None if started else "already running"})


@blueprint.post("/strategize/run")
def strategize():
    service = services()
    started = service.jobs.start("strategize", service.accounts.strategize)
    return jsonify({"ok": started, "error": None if started else "already running"})


@blueprint.get("/accounts/list")
def accounts_list():
    return jsonify(services().account_queries.accounts())


@blueprint.get("/accounts/detail")
def account_detail():
    name = (request.args.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name required"}), 400
    detail = services().account_queries.detail(name)
    return jsonify(detail) if detail else (jsonify({"error": "account not found"}), 404)


@blueprint.get("/accounts/details")
def account_details():
    names = [name.strip() for name in (request.args.get("names") or "").split("\x1f") if name.strip()][:200]
    return jsonify({"accounts": services().account_queries.details(names)})


@blueprint.get("/accounts/leftovers")
def leftovers():
    return jsonify({"accounts": services().account_queries.named_bucket("leftovers")})


@blueprint.get("/accounts/no_contacts")
def no_contacts():
    return jsonify({"accounts": services().account_queries.named_bucket("no_contacts")})


@blueprint.get("/accounts/other_quarters")
def other_quarters():
    return jsonify(services().account_queries.other_quarters())


@blueprint.get("/schedule")
def schedule():
    return jsonify(services().account_queries.schedule())


@blueprint.get("/cadences")
def cadences():
    return jsonify(services().account_queries.cadences())


@blueprint.get("/call_brief")
def call_brief():
    name = (request.args.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name required"}), 400
    context, deterministic = services().account_queries.brief_context(name)
    generated = watsonx.advise_call_brief(context) if watsonx.available() else []
    return jsonify({"account": name, "bullets": generated or deterministic,
                    "source": "watsonx" if generated else "deterministic"})


@blueprint.get("/email_draft")
def email_draft():
    name = (request.args.get("name") or "").strip()
    first = (request.args.get("first") or "there").strip()
    step = (request.args.get("step") or "").strip()
    if not name:
        return jsonify({"error": "name required"}), 400
    context, _ = services().account_queries.brief_context(name)
    context.update(contact_first_name=first, email_step=step)
    industry = (context.get("sales_cloud") or {}).get("industry")
    examples = services().emails.top_examples_for_prompt(industry)
    generated = watsonx.advise_email(context, examples=examples) if watsonx.available() else {}
    if generated:
        result, source = generated, "watsonx"
    else:
        result, source = _deterministic_email(name, first, step, context), "deterministic"
    return jsonify({"account": name, **result, "source": source})

