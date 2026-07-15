#!/usr/bin/env python3
"""One-shot hardening for every on-disk credential/session artifact.

Fixes docs/SECURITY.md issues I19/I23/I40/I41/I42/I67 for files that already
exist (files written *after* this are hardened at write time by
shared_auth.guard.atomic_save_state). Protective only: it tightens permissions to
owner-only (0600 files / 0700 dirs) — the owner keeps full read/write — and lists
any orphaned `*.tmp*` secret copies. Re-runnable and safe.

    python3 secure_auth_files.py            # report + harden
    python3 secure_auth_files.py --list     # report only, change nothing

Revocation (separate, destructive — deletes sessions) lives in
shared_auth.guard.wipe_all(); this script never deletes anything.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from shared_auth import guard  # noqa: E402

REPO = Path(__file__).resolve().parent
HOME = Path.home()

# Secret files (→ 0600) and their dirs (→ 0700).
SECRET_DIRS = [HOME / ".orum_pipeline", HOME / ".isc_scraper"]
SECRET_GLOBS = [
    (HOME / ".orum_pipeline", "*_auth_state.json"),
    (HOME / ".orum_pipeline", "auth_audit.log"),
    (HOME / ".isc_scraper", "auth_state.json"),
    (HOME / ".isc_scraper", "aura_bootstrap.json"),
]
SECRET_FILES = [REPO / ".env"]
# Dirs to scan for orphaned atomic-write temp copies of secrets.
TMP_SCAN_DIRS = [HOME / ".orum_pipeline", HOME / ".isc_scraper"]

# Auto-include every registered service's session file + its parent dir, so a
# newly-registered service (shared_auth registry) is hardened without editing this
# script. Purely ADDITIVE to the explicit lists above — it can only widen coverage,
# never shrink it (a security script must never silently harden fewer files).
try:
    import shared_auth  # noqa: E402
    _reg_files = [Path(p) for p in
                  (shared_auth.resolve_state_path(s) for s in shared_auth.all_services()) if p]
    for _f in _reg_files:
        if _f not in SECRET_FILES:
            SECRET_FILES.append(_f)
        if _f.parent not in SECRET_DIRS:
            SECRET_DIRS.append(_f.parent)
        if _f.parent not in TMP_SCAN_DIRS:
            TMP_SCAN_DIRS.append(_f.parent)
except Exception as _e:  # registry unavailable -> explicit lists still fully work
    print(f"note: registry-derived targets unavailable ({_e}); using explicit lists",
          file=sys.stderr)


def _mode(p):
    try:
        return oct(p.stat().st_mode & 0o777)
    except Exception:
        return "?"


def main():
    list_only = "--list" in sys.argv
    changed, orphans = [], []

    for d in SECRET_DIRS:
        if d.exists() and (d.stat().st_mode & 0o777) != 0o700:
            print(f"dir  {d}  {_mode(d)} -> 0o700" + ("  (would)" if list_only else ""))
            if not list_only:
                try:
                    os.chmod(d, 0o700); changed.append(d)
                except Exception as e:
                    print(f"     ! {e}")

    targets = list(SECRET_FILES)
    for base, pat in SECRET_GLOBS:
        if base.exists():
            targets += sorted(base.glob(pat))
    for f in targets:
        if f.exists() and f.is_file() and (f.stat().st_mode & 0o777) != 0o600:
            print(f"file {f}  {_mode(f)} -> 0o600" + ("  (would)" if list_only else ""))
            if not list_only:
                guard._chmod_600(f); changed.append(f)

    for d in TMP_SCAN_DIRS:
        if d.exists():
            for t in d.glob("*.tmp*"):
                orphans.append(t)
                if not list_only and t.is_file():
                    guard._chmod_600(t)  # secure it; leave deletion to the human

    print("\n--- summary ---")
    print(f"hardened: {len(changed)} path(s)")
    if orphans:
        print(f"orphaned temp secret copies found (review/delete): {len(orphans)}")
        for t in orphans:
            print(f"  {t}  {_mode(t)}")
    else:
        print("orphaned temp secret copies: none")
    if list_only:
        print("(--list: nothing was changed)")


if __name__ == "__main__":
    main()
