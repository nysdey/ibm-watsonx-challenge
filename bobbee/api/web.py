"""HTML shell and local mock-tool pages."""

from flask import Blueprint, abort, render_template

from bobbee.domain.time import today

blueprint = Blueprint("web", __name__)


@blueprint.get("/")
def index():
    current = today()
    return render_template("index.html", today=current.isoformat(), real_today=current.isoformat())


@blueprint.get("/mock/<service>/login")
def mock_login(service: str):
    labels = {"isc": "ISC", "zoominfo": "ZoomInfo", "salesloft": "Salesloft"}
    if service not in labels:
        abort(404)
    return render_template("mocks/login.html", service=service, label=labels[service])


@blueprint.get("/mock/<service>")
def mock_tool(service: str):
    templates = {
        "isc": "mocks/isc.html",
        "zoominfo": "mocks/zoominfo.html",
        "salesloft": "mocks/salesloft.html",
    }
    if service not in templates:
        abort(404)
    return render_template(templates[service])

