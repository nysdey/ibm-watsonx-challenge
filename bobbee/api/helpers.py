"""Shared HTTP helpers."""

from __future__ import annotations

from flask import current_app, jsonify, request


def services():
    return current_app.extensions["bobbee.services"]


def require_loopback():
    host = (request.host or "").split(":", 1)[0].strip("[]").lower()
    if host not in {"127.0.0.1", "localhost", "::1"}:
        return jsonify({"error": "BobBee only accepts loopback requests."}), 403
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        origin = request.headers.get("Origin") or request.headers.get("Referer")
        if origin and not any(token in origin for token in ("127.0.0.1", "localhost", "[::1]")):
            return jsonify({"error": "Cross-origin writes are not allowed."}), 403
    return None

