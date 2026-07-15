# Gotchas — Durable Engineering Hazards

Traps that MUST survive refactors. Each is a real bug class already paid for once. Each entry is a **Symptom** (what you'll see) plus a **Rule** (what to do / never do). For the *why* behind the architecture, see [ARCHITECTURE.md](ARCHITECTURE.md); for the auth/threat model, see [SECURITY.md](SECURITY.md).

---

## 1. `ui_templates.py` inline-UI escaping contract

The dashboard's entire HTML/CSS/JS UI lives as Python triple-quoted `*_TEMPLATE` strings in `ui_templates.py` (extracted from `run_pipeline.py` on 2026-07-15, byte-identical), rendered via `render_template_string` — so each template is **one Jinja source**. Jinja and the JS share the same text, and a single stray backslash bridges them destructively. **This contract is unchanged by the extraction** (still `render_template_string`, still Python string literals) — if you ever convert these to real Jinja `.html` files served by `render_template`, every doubled backslash must be halved, and that conversion must be browser-verified route-by-route (a mis-parse still returns HTTP 200).

**Symptom:** the UI silently dies — `showPage` is `undefined`, tabs don't switch, nothing responds — after what looked like a harmless UI edit. The server still returns **HTTP 200**; AST parsing and pytest stay green. A mis-parsed regex or a broken JS string doesn't fail any test, because nothing evaluates the JS except a real browser.

**Rule:**
- A stray backslash in a single-quoted JS string (e.g. `\'`) can break the **ENTIRE** script, not just that line — it corrupts Jinja's parse of the whole template. Do not write `\'`.
- JS `\n` and any regex must be **double-backslashed** (`\\n`, `\\d`) so one backslash survives Jinja and reaches the JS.
- No literal `{{` or `{%` may appear anywhere in the JS — Jinja will try to interpret them.
- **AST/pytest do NOT catch this.** After ANY UI edit, **browser-verify each page** — load it and confirm the tabs actually switch and the console is clean. A 200 response proves nothing.

---

## 2. Latent XSS — `accounts_json` embedded raw in a `<script>`

**Symptom:** the Call-Planning calendar / tier views serialize `accounts_json` and drop it **raw into a `<script>` tag**. A crafted account name containing the literal `</script>` closes the script element early and breaks out into HTML — a stored-XSS primitive. Low risk today only because account names are internal IBM data, not attacker-controlled; it is **not yet hardened**.

**Rule:** if you touch those views (or add any view that embeds a JSON blob inside a `<script>`), **JSON-escape `<`** in the embedded blob (e.g. emit `<` as `<`) so no account-name payload can terminate the tag. Don't just trust that names are "internal."

---

## 3. ISC concurrency — never move the HTTP workers in-process

**Symptom:** concurrent `getAccountPageContents` calls against the **same** Salesforce prospect-list ID race and clobber each other's filter server-side, returning **0 rows** with no error (verified: 4 CovIDs fired in parallel against one list → 3 came back empty; 6 simultaneous `/run` calls → ~100 zero-row results). The `ISC_Scraper_App` subprocess model exists specifically to fix these real zero-row races — it gives each concurrent worker its own distinct list ID via the process-wide, lock-protected `_ListIdRegistry`, serializes bootstrap behind a lock, and writes `aura_bootstrap.json` atomically.

**Rule:** **Do NOT move the ISC HTTP workers in-process.** The subprocess-per-CovID structure plus the shared list-ID registry is load-bearing against Salesforce-side zero-row corruption. Keep the seam. (Full history: `ISC_Scraper_App/CONTEXT.md` Rounds 2–4.)

---

## 4. Standalone-step + `stdin=DEVNULL` contract

**Symptom:** a step calls `input()` (a login prompt, a "press enter to continue" pause) and the run wedges — except it doesn't hang, it dies instantly with `EOFError`. The dashboard launches every step with `stdin=subprocess.DEVNULL`, so stdin is closed on launch and any prompt becomes immediate EOF **by design** (this fail-fast is the intended behavior — it beats blocking a run forever).

**Rule:**
- Every step must stay **runnable on its own** (`cd <Step>/ && .venv/bin/python3 run.py …`) — the dashboard only sequences standalone steps, it never imports their internals.
- A step must **never call `input()`**. All parameters arrive as **CLI args**, never a terminal prompt. See the `_launch` docstring (`run_pipeline.py:486`).

---

## 5. Bobby — "real-time, never presaved"

**Symptom:** `/api/bobby/state` shows a **stale, presaved run** — drafts from a previous session — because it read `output/latest.json` off disk instead of the current in-memory run.

**Rule:** `/api/bobby/state` must return **only the in-memory run state**. It must **NEVER read `output/latest.json` off disk** to answer "what's the current run." (Disk is fine for the *send* step, which reads persisted drafts — but not for live run state.) This generalizes: **state on disk is not "live state."** Any feature with a "current run" concept follows the same rule.

---

## 6. `latest.xlsx` is a COPY, not a symlink

**Symptom:** "why is this file only 4kb?" tickets. A symlink inside a folder that also gets zipped / emailed / synced doesn't survive the round-trip — downstream steps then read a dead or tiny link instead of the real workbook.

**Rule:**
- Every step's `latest.xlsx` is a **copy** of the most recent dated file, **never a symlink**.
- Write the dated file (`<prefix>_YYYYMMDD.xlsx`) **first, fully and successfully**; then overwrite `latest.xlsx` as the writer's **final action**. That ordering guarantees a crash mid-write never leaves `latest.xlsx` pointing at a half-written file. See the File Handoff Schema Contract in [../README.md](../README.md).

---

## 7. Live writes ship gated OFF by default

**Symptom:** a newly-built feature that *sends* email, advances a cadence, or writes to Salesforce/ZoomInfo fires an un-calibrated bulk action on first click.

**Rule:** any external **write** ships **gated off by default** and refuses unless an explicit env flag is set — calibrate on **one** record before enabling. Established flags: `BOBBY_ENABLE_SEND=1` (Bobby Send All), `PIPELINE_ENABLE_UPDATE=1` (Pipeline next-step overwrite + Chatter post), `MEETING_REMINDERS_SEND=1` (pre-meeting reminder email), `MEETING_FOLLOWUP_SEND=1` (follow-up minutes email). Build and QA everything *up to* the write; leave the trigger dark. Threat/authorization detail lives in [SECURITY.md](SECURITY.md).

---

## 8. Async for anything slow — never block the request thread

**Symptom:** the UI freezes for the duration of a job because the work ran synchronously inside the Flask request handler.

**Rule:** a long job runs on a **background thread** with a polled state dict (surfaced through `api_status`'s `_actions` block). If the work spawns a browser, add a **watchdog timer** to kill a hung browser after a ceiling (Bobby uses a 600 s watchdog) and clear the `active` flag in a `finally` so a crash can't wedge the card as permanently "running." Fast-fail on missing prerequisites (input file / session) **before** launching heavy machinery.
