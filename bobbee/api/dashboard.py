"""Dashboard and territory read-model routes."""

from flask import Blueprint, jsonify, request

from .helpers import services

blueprint = Blueprint("dashboard", __name__, url_prefix="/api")


@blueprint.get("/dashboard")
def dashboard():
    return jsonify(services().dashboard_queries.dashboard())


@blueprint.get("/today")
def today():
    return jsonify(services().dashboard_queries.today())


@blueprint.get("/dashboard/progress")
def progress():
    period = (request.args.get("period") or "week").lower()
    if period not in {"day", "week", "month", "quarter"}:
        return jsonify({"error": "bad period"}), 400
    try:
        offset = max(-24, min(24, int(request.args.get("offset") or 0)))
    except ValueError:
        offset = 0
    return jsonify(services().dashboard_queries.progress(period, offset))


@blueprint.get("/book")
def book():
    scope = (request.args.get("mtg_scope") or "quarter").lower()
    if scope not in {"quarter", "week"}:
        scope = "quarter"
    try:
        offset = int(request.args.get("mtg_offset") or 0)
    except ValueError:
        offset = 0
    return jsonify(services().dashboard_queries.book(scope, offset))


@blueprint.get("/territory")
def territory():
    view = (request.args.get("view") or "accounts").lower()
    if view not in {"accounts", "cadences", "spend", "industries"}:
        return jsonify({"error": "bad view"}), 400
    return jsonify(services().dashboard_queries.territory(view))

