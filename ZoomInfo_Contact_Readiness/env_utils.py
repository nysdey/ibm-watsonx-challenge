"""Tiny .env loader — avoids adding python-dotenv as a dependency for a handful of
KEY=VALUE lines. Real environment variables always win over .env file values."""
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def load_env(env_path=None):
    path = Path(env_path) if env_path else REPO_ROOT / ".env"
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if key and key not in os.environ:
            os.environ[key] = value
