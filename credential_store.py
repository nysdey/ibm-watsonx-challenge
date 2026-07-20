"""Local identity store for the BobBee's sign-in gate.

In the real app this wrapped the macOS Keychain to hold the seller's IBM W3ID
email + password for the automated logins. The clone has no real logins — every
service is mocked — so there is nothing to authenticate and no password to keep.

This store therefore records ONLY the signed-in email (the thing that maps a
seller to their territory/accounts), in a small local JSON file. The password
typed into the sign-in gate is accepted for a familiar UX but immediately
discarded — never persisted, logged, or echoed. The public API (save / has /
get_email / get) is unchanged so run_pipeline.py is untouched.
"""
import json
from pathlib import Path

_STORE_PATH = Path(__file__).resolve().parent / ".watsonx_identity.json"


def _load():
    if _STORE_PATH.exists():
        try:
            return json.loads(_STORE_PATH.read_text())
        except Exception:
            return {}
    return {}


def _save_store(data):
    _STORE_PATH.write_text(json.dumps(data, indent=2))


def save(key, email, password):
    """Record the signed-in email for `key`. The password is intentionally ignored
    and never stored (the clone has no real login). Returns (ok, error)."""
    if not email:
        return False, "email is required"
    data = _load()
    data[key] = {"email": email}      # password deliberately dropped
    try:
        _save_store(data)
        return True, None
    except Exception as e:
        return False, str(e)


def clear(key):
    """Forget the signed-in identity for `key` (logout). Returns (ok, error)."""
    data = _load()
    if key in data:
        del data[key]
        try:
            _save_store(data)
        except Exception as e:
            return False, str(e)
    return True, None


def has(key):
    return key in _load()


def get_email(key):
    return (_load().get(key) or {}).get("email")


def get(key):
    """Return {'email': ..., 'password': ''} for `key`, or None. The password is
    always empty — the clone never stores one."""
    entry = _load().get(key)
    if not entry:
        return None
    return {"email": entry.get("email"), "password": ""}
