"""Application configuration."""

from __future__ import annotations

import os
from pathlib import Path


def default_config() -> dict:
    """Read environment-backed defaults when an application is created."""
    return {
        "SECRET_KEY": os.environ.get("BOBBEE_SECRET_KEY", "bobbee-local-demo-session"),
        "JSON_SORT_KEYS": False,
        "TEMPLATES_AUTO_RELOAD": True,
        "DATA_PATH": os.environ.get("BOBBEE_DATA_PATH"),
        "TARGET_ACCOUNTS": int(os.environ.get("BOBBEE_ACCOUNT_COUNT", "1911")),
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SAMESITE": "Lax",
    }


def data_path(app_instance_path: str, configured: str | None) -> Path:
    return Path(configured).expanduser() if configured else Path(app_instance_path) / "state.json"
