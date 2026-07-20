"""Canonical Flask application factory."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from dotenv import load_dotenv
from flask import Flask

from bobbee.api import blueprints
from bobbee.api.helpers import require_loopback
from bobbee.config import data_path, default_config
from bobbee.infrastructure.repository import JsonRepository
from bobbee.services.container import build_services
from bobbee.paths import PACKAGE_ROOT, PROJECT_ROOT


def create_app(config: Mapping[str, Any] | None = None) -> Flask:
    """Build the complete BobBee application and its service container."""
    load_dotenv(PROJECT_ROOT / ".env")
    app = Flask(
        "bobbee",
        template_folder=str(PACKAGE_ROOT / "templates"),
        static_folder=str(PACKAGE_ROOT / "static"),
        static_url_path="/static",
        instance_relative_config=True,
    )
    app.config.from_mapping(default_config())
    if config:
        app.config.update(config)
    repository = JsonRepository(data_path(app.instance_path, app.config.get("DATA_PATH")))
    app.extensions["bobbee.services"] = build_services(
        repository, int(app.config["TARGET_ACCOUNTS"])
    )
    for blueprint in blueprints():
        app.register_blueprint(blueprint)
    app.before_request(require_loopback)
    return app
