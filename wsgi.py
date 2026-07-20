"""WSGI entry point for production-compatible servers."""

from bobbee import create_app

app = create_app()

__all__ = ["app"]
