"""Account commands and query endpoints."""

from flask import Blueprint, jsonify, request, session

from bobbee.integrations import watsonx

from .helpers import services

blueprint = Blueprint("accounts", __name__, url_prefix="/api")


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
    generated = watsonx.advise_email(context) if watsonx.available() else {}
    if generated:
        result, source = generated, "watsonx"
    else:
        result, source = {
            "subject": f"Quick idea for {name}",
            "body": (f"Hi {first},\n\nI’m reaching out because {context.get('sales_angle') or 'there is a timely infrastructure opportunity.'} "
                     "I’d be glad to share what similar teams are doing with IBM.\n\nOpen to a quick conversation?\n\nBest,\n[Your name]"),
        }, "deterministic"
    return jsonify({"account": name, **result, "source": source})

