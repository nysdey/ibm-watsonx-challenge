"""HTTP blueprint assembly."""

from .accounts import blueprint as accounts_blueprint
from .assistant import blueprint as assistant_blueprint
from .auth import blueprint as auth_blueprint
from .dashboard import blueprint as dashboard_blueprint
from .web import blueprint as web_blueprint


def blueprints():
    return (
        web_blueprint,
        auth_blueprint,
        accounts_blueprint,
        dashboard_blueprint,
        assistant_blueprint,
    )


__all__ = ["blueprints"]

