"""Filesystem helpers over the shared session registry.

Stdlib-only (no Playwright, no Flask) so ANY part of the platform — the Flask
dashboard, the login-capture subprocess, or the FastAPI Meetings backend — can import
it cheaply to answer "where does service X's session live?" and "is it present?".

Actual *validity* (is the saved session still alive server-side?) is a heavier check
that navigates a headless browser — that lives in `login_capture.py:probe_service`,
not here. These helpers only speak to on-disk presence and location.
"""

import json
from pathlib import Path

from . import registry


def state_path(service):
    """Absolute path to a service's captured storage_state JSON (`~` expanded).

    Raises KeyError for an unknown service so typos fail loudly rather than
    silently pointing at a nonexistent file.
    """
    cfg = registry.SERVICES[service]
    return Path(cfg["auth_path"]).expanduser()


def exists(service):
    """True if a captured session file is present on disk for this service."""
    try:
        return state_path(service).exists()
    except KeyError:
        return False


def load_state(service):
    """Parsed storage_state dict for a service, or None if missing/unreadable."""
    try:
        p = state_path(service)
    except KeyError:
        return None
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except Exception:
        return None


def resolve_state_path(service):
    """The storage_state path to load for a scrape, or None if there is no saved
    session yet. Convenience wrapper: returns a str path when present, else None —
    the shape Playwright's `new_context(storage_state=...)` wants."""
    if exists(service):
        return str(state_path(service))
    return None
