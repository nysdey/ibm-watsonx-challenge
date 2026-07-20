from pathlib import Path

import pytest

from bobbee import create_app


@pytest.fixture()
def app(tmp_path: Path):
    return create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret",
        "DATA_PATH": str(tmp_path / "state.json"),
        "TARGET_ACCOUNTS": 48,
    })


@pytest.fixture()
def client(app):
    return app.test_client()

