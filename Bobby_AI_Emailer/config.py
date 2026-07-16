"""Config for Bobby, the AI Emailer.

Bobby reads a Salesloft cadence's email steps + enrolled people via Salesloft's
REST API (authenticated by a bearer token lifted from the saved browser session),
writes a personalized email per person with watsonx.ai (fail-soft to a deterministic
template), and records them for review / best-effort push back into Salesloft.
"""
import os
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent
REPO_ROOT = APP_ROOT.parent

# Same saved Salesloft session the Salesloft Cadence Readiness step uses.
SALESLOFT_AUTH_STATE_PATH = Path(
    os.environ.get("SALESLOFT_AUTH_STATE_PATH", "~/.orum_pipeline/salesloft_auth_state.json")
).expanduser()

SALESLOFT_APP_URL = os.environ.get("SALESLOFT_BASE_URL", "https://app.salesloft.com")
SALESLOFT_API_BASE = os.environ.get("SALESLOFT_API_BASE", "https://api.salesloft.com/v2")

OUTPUT_DIR = APP_ROOT / "output"
LOG_DIR = APP_ROOT / "logs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Bobby drafts for EVERY person on an email step; this is only a runaway safety cap
# for an unusually large cadence.
MAX_PEOPLE = int(os.environ.get("BOBBY_MAX_PEOPLE", "500"))
