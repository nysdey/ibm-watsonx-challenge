"""Send tracking, seller feedback, and the training-data read model.

Together these are the feedback loop: /email_send records what actually went
out, /email_feedback attaches the seller's star ratings, and /training_data
lists what has cleared the bar to be retrieved as a few-shot example the next
time watsonx drafts (see EmailService.top_examples_for_prompt).
"""

from flask import Blueprint, jsonify, request

from bobbee.domain.feedback import RATING_KEYS

from .helpers import services

blueprint = Blueprint("emails", __name__, url_prefix="/api")


@blueprint.post("/email_send")
def email_send():
    data = request.get_json(silent=True) or {}
    account = (data.get("account") or "").strip()
    subject = (data.get("subject") or "").strip()
    body = (data.get("body") or "").strip()
    if not account or not body:
        return jsonify({"error": "account and body required"}), 400
    contact = data.get("contact") or {}
    record = services().emails.record_sent(
        account=account,
        industry=data.get("industry"),
        tier=data.get("tier"),
        play=data.get("play"),
        contact_first=contact.get("first_name"),
        contact_last=contact.get("last_name"),
        contact_title=contact.get("title"),
        cadence=data.get("cadence"),
        step=data.get("step"),
        subject=subject,
        body=body,
        source=data.get("source"),
    )
    return jsonify({"ok": True, "email_id": record["id"]})


@blueprint.post("/email_feedback")
def email_feedback():
    data = request.get_json(silent=True) or {}
    email_id = (data.get("email_id") or "").strip()
    if not email_id:
        return jsonify({"error": "email_id required"}), 400
    raw_ratings = data.get("ratings") or {}
    ratings = {}
    for key in RATING_KEYS:
        try:
            value = int(raw_ratings.get(key))
        except (TypeError, ValueError):
            continue
        if 1 <= value <= 5:
            ratings[key] = value
    if not ratings:
        return jsonify({"error": "at least one 1-5 rating required"}), 400
    updated = services().emails.submit_feedback(email_id, ratings, data.get("notes"))
    if not updated:
        return jsonify({"error": "email not found"}), 404
    return jsonify({"ok": True, "email": services().emails.email_status(email_id)})


@blueprint.get("/email_status")
def email_status():
    email_id = (request.args.get("email_id") or "").strip()
    if not email_id:
        return jsonify({"error": "email_id required"}), 400
    status = services().emails.email_status(email_id)
    return jsonify(status) if status else (jsonify({"error": "email not found"}), 404)


@blueprint.get("/training_data")
def training_data():
    return jsonify(services().emails.training_data(request.args.get("q") or ""))
