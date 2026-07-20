"""Local demo authentication.

Identity lives in Flask's signed session cookie. Passwords are accepted only to
preserve the demo sign-in interaction and are never stored.
"""

from flask import Blueprint, jsonify, request, session

from .helpers import services

blueprint = Blueprint("auth", __name__, url_prefix="/api")


@blueprint.get("/credentials/status")
def credentials_status():
    email = session.get("email")
    return jsonify({"w3id": bool(email), "email": email})


@blueprint.post("/credentials/<key>")
def credentials_save(key: str):
    if key != "w3id":
        return jsonify({"ok": False, "error": "unsupported credential"}), 404
    body = request.get_json(silent=True) or {}
    email = (body.get("email") or "").strip().lower()
    if not email or not body.get("password"):
        return jsonify({"ok": False, "error": "email and password are required"}), 400
    session.clear()
    session["email"] = email
    return jsonify({"ok": True})


@blueprint.post("/logout")
def logout():
    session.clear()
    return jsonify({"ok": True})


@blueprint.post("/demo/reset")
def reset_demo():
    services().repository.reset()
    return jsonify({"ok": True})


@blueprint.get("/seller")
def seller():
    return jsonify(services().account_queries.seller(session.get("email")))


@blueprint.get("/login/status")
def login_status():
    return jsonify({service: {"state": "ready"} for service in ("isc", "zoominfo", "salesloft")})


@blueprint.post("/login/<service>/start")
def login_start(service: str):
    if service not in {"isc", "zoominfo", "salesloft"}:
        return jsonify({"ok": False, "error": "unknown service"}), 404
    return jsonify({"ok": True, "mock_url": f"/mock/{service}/login"})


@blueprint.post("/login/<service>/confirm")
def login_confirm(service: str):
    if service not in {"isc", "zoominfo", "salesloft"}:
        return jsonify({"ok": False, "error": "unknown service"}), 404
    return jsonify({"ok": True})

