"""shared_auth — the Seller Dashboard's one shared login/session layer.

Every site the platform signs into, and where each site's session lives, is described
once in `registry.py`. Presence/location helpers live in `sessions.py`. Both the
Outbound pipeline and the embedded Meetings live-call assistant import this package, so
a session captured once (via the Details/Access panel) is shared by every surface — the
Meetings tab does NOT need its own separate login.

See README.md for the full picture (sites, methods, and how sessions are shared).

Typical use:

    import shared_auth
    shared_auth.state_path("salesloft")     # Path to the Salesloft storage_state
    shared_auth.exists("outlook")           # is Outlook signed in on this machine?
    shared_auth.services_for("meetings")    # ['salesloft', 'outlook']
"""

from . import guard, registry, sessions
from .guard import (
    atomic_save_state,
    audit,
    is_login_url,
    is_password_blocked,
    is_valid_app_url,
    login_origin_allowed,
    redact_url,
    session_lock,
    session_verdict,
    wipe_all,
)
from .registry import (
    SERVICES,
    all_services,
    credential_key,
    get,
    services_for,
)
from .sessions import (
    exists,
    load_state,
    resolve_state_path,
    state_path,
)

__all__ = [
    "registry",
    "sessions",
    "guard",
    "SERVICES",
    "all_services",
    "services_for",
    "get",
    "credential_key",
    "state_path",
    "exists",
    "load_state",
    "resolve_state_path",
    # guard — the enforcement layer (see guard.py / docs/SECURITY.md)
    "is_login_url",
    "is_valid_app_url",
    "session_verdict",
    "is_password_blocked",
    "login_origin_allowed",
    "redact_url",
    "atomic_save_state",
    "session_lock",
    "audit",
    "wipe_all",
]
