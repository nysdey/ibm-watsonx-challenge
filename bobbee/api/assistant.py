"""Product-help assistant endpoints."""

from flask import Blueprint, jsonify, request

from bobbee.integrations import assistant

blueprint = Blueprint("assistant", __name__, url_prefix="/api/assistant")


@blueprint.get("/status")
def status():
    return jsonify({"configured": assistant.is_configured()})


@blueprint.post("/message")
def message():
    body = request.get_json(silent=True) or {}
    text = (body.get("text") or "").strip()[:1000]
    client_id = (body.get("client_id") or "default")[:64]
    return jsonify(assistant.ask(text, client_id))

