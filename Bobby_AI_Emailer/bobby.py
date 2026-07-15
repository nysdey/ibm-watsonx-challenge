"""Bobby, the AI Emailer — orchestration.

Flow for a chosen Salesloft cadence:
  1. Connect to Salesloft (bearer token from the saved session).
  2. Resolve the cadence by name (clear error listing options if it isn't there).
  3. Read ALL steps; identify the EMAIL steps (their day + step number).
  4. For each email step, read every person currently sitting on it (name, title,
     company) — this mirrors the per-step people counts in Salesloft's cadence view.
  5. Write a personalized email for every one of those people, keyed to their cadence
     day + title + company (Claude if a key is set, else a deterministic template).
  6. Save the result grouped by email step to output/latest.json (rendered at /bobby).

`send_all` (a separate, explicit action) then sends the drafts one-by-one in Salesloft.
run_bobby never sends — it only drafts.
"""
import json
import logging
from datetime import datetime

import config
import emailer
import salesloft_api

logger = logging.getLogger("bobby")

SessionExpired = salesloft_api.SessionExpired


class CadenceNotFound(RuntimeError):
    """The chosen cadence name isn't in this Salesloft account."""


def _company_of(person):
    # Salesloft puts the company on the person as `person_company_name`;
    # `account` is only a {id,_href} link (no name).
    if person.get("person_company_name"):
        return person["person_company_name"]
    acct = person.get("account")
    if isinstance(acct, dict) and acct.get("name"):
        return acct["name"]
    return person.get("company_name") or ""


def run_bobby(cadence_name, on_progress=None):
    def progress(msg):
        logger.info(msg)
        if on_progress:
            try:
                on_progress(msg)
            except Exception:
                pass

    progress("Connecting to Salesloft…")
    client = salesloft_api.SalesloftClient.from_session()
    me = client.me()
    progress(f"Signed in to Salesloft as {me.get('name') or me.get('email') or 'you'}. "
             f"Finding the “{cadence_name}” cadence…")

    cadences = client.list_cadences()
    cadence = client.find_cadence(cadence_name, cadences)
    if not cadence:
        names = sorted((c.get("name") or "") for c in cadences)
        sample = "; ".join(n for n in names if "targeted outreach" in n.lower())[:300] \
            or "; ".join(n for n in names[:15] if n)[:300]
        raise CadenceNotFound(
            f"No Salesloft cadence named “{cadence_name}” was found "
            f"({len(cadences)} cadences searched). Cadences that exist: {sample}")

    cid = cadence["id"]
    email_steps, by_step = client.people_at_email_steps(cid)
    total_people = sum(len(v) for v in by_step.values())
    progress(f"“{cadence.get('name')}” has {len(email_steps)} email step(s) with "
             f"{total_people} person(s) on them — writing personalized emails…")
    if not email_steps:
        raise RuntimeError(f"Cadence “{cadence.get('name')}” has no email steps.")

    # Collect (step, membership) tasks up to the safety cap, then fetch each person +
    # draft their email IN PARALLEL — the per-person Salesloft lookups are the slow
    # part, so this keeps a "real-time" run to seconds even for a big email step.
    tasks = []
    for step in email_steps:
        for m in by_step.get(step["id"], []):
            if len(tasks) >= config.MAX_PEOPLE:
                break
            tasks.append((step, m))
    target = len(tasks)

    import threading
    from concurrent.futures import ThreadPoolExecutor
    lock = threading.Lock()
    counter = {"n": 0}

    def _one(step, m):
        pinfo = m.get("person") if isinstance(m.get("person"), dict) else {}
        pid = pinfo.get("id")
        try:
            person = client.person(pid) if pid else pinfo
        except Exception:
            person = pinfo
        pdata = {
            "first_name": person.get("first_name") or pinfo.get("first_name") or "",
            "last_name": person.get("last_name") or pinfo.get("last_name") or "",
            "title": person.get("title") or "",
            "company": _company_of(person),
            "email": person.get("email_address") or "",
        }
        email = emailer.generate_email(pdata, step, cadence.get("name"))
        name = (pdata["first_name"] + " " + pdata["last_name"]).strip() or "(unknown)"
        with lock:
            counter["n"] += 1
            progress(f"[{counter['n']}/{target}] {step.get('display_name')}: "
                     f"wrote email for {name} ({pdata['title'] or 'unknown title'})")
        return step["id"], {
            "membership_id": m.get("id"),
            "person_id": pid,
            "name": name,
            "title": pdata["title"],
            "company": pdata["company"],
            "email": pdata["email"],
            "subject": email["subject"],
            "body": email["body"],
            "written_by": "Claude" if email["source"] == "claude" else "Template",
            "sent": False,
        }

    by_step_people = {step["id"]: [] for step in email_steps}
    with ThreadPoolExecutor(max_workers=8) as pool:
        for sid, person_row in pool.map(lambda t: _one(*t), tasks):
            by_step_people[sid].append(person_row)

    steps_out = [{
        "step_id": step["id"],
        "day": step.get("day"),
        "step_number": step.get("step_number"),
        "name": step.get("name"),
        "display_name": step.get("display_name"),
        "people": by_step_people.get(step["id"], []),
    } for step in email_steps]
    written = target

    out = {
        "cadence": cadence.get("name"),
        "cadence_id": cid,
        "generated_at": datetime.now().isoformat(),
        "email_step_count": len(email_steps),
        "people_count": total_people,
        "drafted": written,
        "claude_written": sum(1 for s in steps_out for p in s["people"] if p["written_by"] == "Claude"),
        "steps": steps_out,
    }
    _write_output(out)
    progress(f"Done — {written} personalized email(s) drafted across {len(email_steps)} "
             f"email step(s) for “{cadence.get('name')}”.")
    return out


def _write_output(out):
    """Save the structured drafts to latest.json (rendered at /bobby) + a flat xlsx."""
    (config.OUTPUT_DIR / "latest.json").write_text(json.dumps(out, indent=2))
    import openpyxl
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Bobby Drafts"
    ws.append(["Email_Step", "Day", "Person", "Title", "Company", "Email",
               "Subject", "Body", "Written_By"])
    for s in out["steps"]:
        for p in s["people"]:
            ws.append([s.get("display_name"), s.get("day"), p["name"], p["title"],
                       p["company"], p["email"], p["subject"], p["body"], p["written_by"]])
    wb.save(config.OUTPUT_DIR / f"bobby_drafts_{stamp}.xlsx")


# ── sending (explicit, separate action) ──────────────────────────────────────
def load_latest():
    path = config.OUTPUT_DIR / "latest.json"
    return json.loads(path.read_text()) if path.exists() else None


def send_all(on_progress=None):
    """Send every drafted email one-by-one in Salesloft.

    *** NOT YET LIVE-CALIBRATED — see README. *** Sending a per-person cadence email
    requires driving Salesloft's compose/send UI (or an internal send endpoint), which
    cannot be verified without actually sending. This function is intentionally a guarded
    stub that refuses to run until BOBBY_ENABLE_SEND=1, so a Send-All click can't fire an
    un-tested bulk send. The review page + drafts are the deliverable up to this point.
    """
    import os
    drafts = load_latest()
    if not drafts:
        raise RuntimeError("No drafted emails to send — run Bobby first.")
    if os.environ.get("BOBBY_ENABLE_SEND") != "1":
        raise RuntimeError(
            "Sending is not enabled yet. Bobby has drafted the emails and they're ready "
            "for review; the live Salesloft send needs to be calibrated and turned on "
            "(set BOBBY_ENABLE_SEND=1) before Send All will actually send. See the README.")
    # Placeholder for the calibrated send loop (per-person compose + send in Salesloft).
    raise RuntimeError("Live send not implemented yet.")
