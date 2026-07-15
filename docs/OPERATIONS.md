# Operations Playbook

Install, run, test, and operate the Seller Dashboard. This is the how-to-run
reference. For *what each component does* see [ARCHITECTURE.md](ARCHITECTURE.md);
for *why the write-gates and auth exist* see [SECURITY.md](SECURITY.md).

All paths below are relative to the repo root (the folder containing
`run_pipeline.py`). The repo path contains spaces — **always quote paths** in shell
commands.

---

## 1. Environments — three separate virtualenvs

The platform is not one Python environment. It is **three**, each created and
maintained independently. Do **not** copy a `.venv`/`venv` between machines:
virtualenvs embed absolute paths (shebangs, `pyvenv.cfg`) and break once moved.
Recreate each one fresh on every new computer.

| Venv | Path | Serves | Python | Deps |
|---|---|---|---|---|
| Root shared | `.venv/` | `run_pipeline.py` + pipeline **steps 2–7** (IBM Scraper, Segmentation, Tiering, Call Planning, ZoomInfo, Salesloft), Bobby, Pipeline Review | 3.x | `requirements.txt` |
| ISC scraper | `ISC_Scraper_App/.venv/` | **Step 1** only (`launcher.py` / `http_scraper.py`) | 3.9 | playwright, openpyxl, flask |
| Meetings copilot | `live_transcribe_bot/venv/` | the **Meetings** tab backend (FastAPI subprocess) | 3.x | `live_transcribe_bot/requirements.txt` (FastAPI/Deepgram stack) |

### 1a. Root `.venv` (dashboard + steps 2–7)

```bash
cd "…/Seller_Dashboard"
cp .env.example .env          # first time only; fill real values if defaults don't fit
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/playwright install firefox
```

`requirements.txt` (root) pins the known-good set: `openpyxl==3.1.5`,
`flask==3.1.3`, `playwright==1.60.0` (Flask pulls werkzeug/jinja2/markupsafe/
itsdangerous/click/blinker transitively). This file explicitly does **not** cover
the ISC or Meetings environments — they have their own.

`Name Match.xlsx` at the repo root maps each coverage ID to its BTSS and TSS reps;
it turns a signed-in email into a set of territories. Keep it current as rep
assignments change.

### 1b. ISC scraper `.venv` (step 1)

Step 1 predates the shared convention and keeps its own venv. It is **not**
portable and is git-excluded — recreate it:

```bash
cd ISC_Scraper_App
python3 -m venv .venv
source .venv/bin/activate
pip install playwright openpyxl flask
playwright install firefox
```

No `.env` here — ISC auth is a Playwright storage-state file at
`~/.isc_scraper/auth_state.json`, created interactively on first login. Nothing to
configure ahead of time. (Note: a stale compiled `ISC_Scraper` PyInstaller binary
exists but predates the 2026-06-30 fixes — run via `python3 launcher.py` from this
venv, not the binary.)

### 1c. Meetings copilot `venv` (Meetings tab)

```bash
cd live_transcribe_bot
python3 -m venv venv
./venv/bin/python -m pip install -r requirements.txt
./venv/bin/python -m playwright install chromium
cp .env.example .env
```

Fill `live_transcribe_bot/.env`:

- `ANTHROPIC_API_KEY` — from console.anthropic.com. Also powers the company
  web-research step (Claude built-in web search — no separate search key).
- `DEEPGRAM_API_KEY` — from console.deepgram.com.

Optional keys in the same `.env`: `INTERNAL_DOMAINS`, `CALENDAR_LOOKAHEAD_DAYS`,
`BROWSER_HEADLESS`, `OUTLOOK_CALENDAR_URL`, `SALESLOFT_URL`, `ENDPOINTING_MS`,
`MIC_DIARIZE`, `LOOPBACK_ACTIVE_WINDOW_S`, `LOOPBACK_DEVICE`, `MIC_DEVICE`.

**Logins are shared with the dashboard** — when Meetings runs embedded, you do
**not** run `python -m backend.login`. Sign in to Outlook and Salesloft in the
dashboard's **Details ▸ Access** panel; the backend reads those sessions via
`shared_auth`. The standalone `backend.login` / `backend.auth_watch` flow is only
for running `live_transcribe_bot/` fully outside the dashboard.

**Optional BlackHole loopback** (speaker separation): the loopback device is now
optional — Deepgram diarization on the mic labels a second voice "Prospect". For a
clean split, install BlackHole 2ch, make a Multi-Output Device (speakers +
BlackHole) as the Teams speaker, and set `LOOPBACK_DEVICE=BlackHole`.

### Moving to a new computer

1. Recreate all three venvs (1a, 1b, 1c). **Never** zip/copy any venv.
2. `.venv/bin/python3 run_pipeline.py` → sign in at the IBM Login gate → open
   **Details** and log in to ISC / ZoomInfo / Salesloft / Outlook (all show
   "not logged in" at first — expected, not a bug).
3. Run the workflow: **Get My Accounts** → **Outbound Strategy** → **Fill Contacts
   to SalesLoft** (pick a cadence). Everything else in the repo is portable.

---

## 2. Running

### The dashboard (normal use)

```bash
cd "…/Seller_Dashboard"
.venv/bin/python3 run_pipeline.py
```

Opens the Flask app at `http://127.0.0.1:5488` (or the next free port if 5488 is
busy) and auto-opens a browser tab. On startup it wipes the previous run's
generated output so the UI opens on a clean slate (see §5), and best-effort
launches the Meetings backend as a subprocess on a free port (a missing
folder/venv just makes the Meetings tab report "unavailable"). First screen is the
IBM Login gate; if a login is already saved you skip straight to the main page.

**Live-write warning:** running **Fill Contacts** triggers the real ZoomInfo →
Salesloft write and the Salesloft cadence advance — a human action, not an agent
action. Run it yourself. (See [SECURITY.md](SECURITY.md) for the standing rule.)

### Running any step standalone

Each of the seven steps is a standalone folder runnable outside the dashboard.
The three dashboard buttons just drive them in sequence.

```bash
# Step 1 — ISC scraper (its own venv + UI on :5477)
cd ISC_Scraper_App && .venv/bin/python3 launcher.py

# Steps 2–7 — generic form (root venv)
cd <Step>/ && ../.venv/bin/python3 run.py [--flags]

# Pipeline Review (Pipeline tab module)
cd Pipeline_Review
../.venv/bin/python3 run.py            # TEST_MODE default: built-in sample, no browser
../.venv/bin/python3 run.py --live     # real scrape of the ISC Forecast dashboard
../.venv/bin/python3 preview.py        # standalone view preview on :5499 (never collides with 5488)

# Meetings copilot standalone (its own venv + UI on :8000)
cd live_transcribe_bot && ./venv/bin/python -m uvicorn backend.main:app --port 8000
# (or double-click start.command in Finder)
```

Every step the dashboard launches runs with **stdin closed** (`stdin=DEVNULL`), so
a stray `input()` prompt fails fast instead of blocking a run forever. Step 1
always processes its full scrape regardless of `TEST_MODE` (sampling to a small
test set happens in step 2's `sample_selection.py`, which needs a hand-picked
tier-diverse fixture).

---

## 3. Testing

### Dashboard test suite

```bash
.venv/bin/python -m pytest tests/ -q
```

This is the authorization/regression suite referenced by the audit
(`AUTHORIZATION_SPEC.md`; see [SECURITY.md](SECURITY.md)). Run it after any change
to `run_pipeline.py` auth or a step's I/O contract.

### Teams-captions pre-flight (MUST run HEADED)

The Meetings tab can read Microsoft Teams' own live captions instead of
mic+Deepgram. Teams' web DOM drifts, so **prove the path on your tenant before a
real call**. This test needs no mic and no second person — it feeds synthetic
speech into a solo meeting and reads the captions back:

```bash
cd live_transcribe_bot
# In Teams, click "Meet now" and copy the link, then:
PYTHONPATH="$(cd .. && pwd)" ./venv/bin/python -m backend.teams_selftest \
    --join-url "<paste the Meet-now link>" --fake-audio
```

**It must run headed** (the default): headless Chromium cannot complete the WebRTC
join, so the capture window is visible and the seller joins the call in it. Green
("READ N caption lines") ⇒ production-ready. Red ⇒ it saves
`browser_profile/debug_teams_captions.png` / `.html` showing exactly what it saw,
so the selectors in `teams_transcription.py` can be re-tuned (confirmed selectors:
More ▸ Language and speech ▸ `[data-tid="closed-captions-button-off"]`; captions
render in `closed-caption-v2-window-wrapper`, text in
`[data-tid="closed-caption-text"]`). There is also a **Run pre-flight test** button
on the live page (shown when Teams captions is selected) that runs the same check
in-app. For a mission-critical call, if the pre-flight isn't green, use the
reliable **Microphone** source.

### ISC scraper reliability tests

The ISC scraper has its own deterministic and live-reliability checks:

```bash
cd ISC_Scraper_App/_internal
python3 test_dedup.py            # deterministic dedup unit tests (9 scenarios, 28 assertions)
```

For live scrape reliability (guards against the intermittent Salesforce
false-zero / cold-cache transient documented in the ISC README Rounds 3–4), use
the reliability harness — `reliability_test.py` for a one-shot run and
`auto_reliability_watch.py` for a continuous watch — against the ground-truth
CovID fixture (the manually-confirmed FSS/Pub CA-North/South/HI/GU/MP CovIDs with
known counts 992/1642/41/143/6/2005/2875/83/148/14). An isolated retest returning
the same zero does **not** confirm a territory is empty — a second scraper call can
reproduce the same transient; verify against a real browser filter when in doubt.

### Pipeline Review tests

```bash
cd Pipeline_Review
../.venv/bin/python3 tests/test_staleness.py   # date/quarter/staleness, no browser
```

---

## 4. Gated-write / env-flag reference

Set flags in the repo-root `.env` (documented in `.env.example`); Meetings/audio
flags live in `live_transcribe_bot/.env`. **The four `*_SEND` / `*_ENABLE_*` write
gates all ship OFF by default on purpose** — every one guards a live external write
(send an email, advance a cadence, overwrite a Salesforce field). Build/QA
everything *up to* the write, then arm the gate only after calibrating on a single
record. The rationale is in [SECURITY.md](SECURITY.md).

### 4a. Live-write gates (default OFF — arm only after single-record calibration)

| Flag | Default | What it does | Safety note |
|---|---|---|---|
| `BOBBY_ENABLE_SEND` | unset (off) | Arms Bobby's **Send All**. Off ⇒ `bobby.send_all()` refuses; `/api/bobby/send` returns "sending not enabled". (Send is not implemented yet regardless — see the README pick-up point.) | Calibrate on ONE test person before setting `=1`. Nothing sends while unset. |
| `PIPELINE_ENABLE_UPDATE` | unset (off) | Arms Pipeline Review's Salesforce write (`update.py`: post prior note to Chatter, then overwrite the *Next Step* field). Off ⇒ validates + logs the plan, writes nothing ("gated off" message). | Calibrate on ONE opportunity first. The BP follow-up email is a `mailto` from the seller's own client — no gate needed. |
| `MEETING_REMINDERS_SEND` | unset (off) | Arms the day-before-3pm pre-meeting reminder email send (drives Outlook Web compose UI, best-effort DOM automation). Off ⇒ `/api/reminders` shows what it *would* send (status `queued`); the scheduler always drafts + queues. | Validate on one test contact before arming, like Bobby's Send-All. Sent reminders are deduped + persisted so nothing double-sends. Toggle scheduling off entirely in the Meetings header. |
| `MEETING_FOLLOWUP_SEND` | unset (off) | Arms the **Meeting follow up** email (summary + minutes drafted from the call, sent as reply-all on the invite). Off ⇒ draft + editable preview only. | Review the draft before arming. |
| `PIPELINE_ENABLE_SEND` | unset (off) | **Reserved** for a future gated Pipeline follow-up auto-send. Ships dark; the email button uses `mailto` regardless, so it is currently inert. | No effect today. |

### 4b. Auth (dashboard access control — see [SECURITY.md](SECURITY.md))

| Flag | Default | What it does | Safety note |
|---|---|---|---|
| `DASHBOARD_AUTH_TOKEN` | auto-generated (`secrets.token_urlsafe(32)`) | Bearer token accepted via the `X-Auth-Token` header for headless API calls. Set it in the env to use a known value; otherwise a random one is minted per process. | Treat as a secret. Needed to script the API. |
| `DASHBOARD_STRICT_AUTH` | unset (off) | `=1` enables strict local-auth mode (`_STRICT_LOCAL_AUTH`) hardening against localhost drive-by requests. | Enable for a hardened local posture; verify with `tests/`. |

### 4c. Operational tunables (no live-write risk)

| Flag | Default | What it does |
|---|---|---|
| `TEST_MODE` | `true` | `true` ⇒ steps 2+ process the fixed 5-account sample and steps 4/5 write to obviously-named test resources; Pipeline Review loads its built-in sample (no browser). `false` ⇒ live pulls/writes. |
| `ZOOMINFO_TIME_BUDGET_SEC` | `300` | Wall-clock ceiling for Tiering's ZoomInfo enrichment (gaps only). Progress is checkpointed, so cold runs are bounded and re-runs are near-instant. |
| `ZOOMINFO_CALL_PAUSE_THRESHOLD` / `SALESLOFT_CALL_PAUSE_THRESHOLD` | `20` | Placeholder pause-after-N-calls throttle for the ZoomInfo/Salesloft browser steps. Almost certainly too low for a full production run — confirm real quotas before raising, and only by explicit decision. |
| `PIPELINE_STALE_DAYS` | `7` | A *Next Steps* note older than this earns the ⚠ next to that note. |
| `PIPELINE_LOAD_ALL_ROWS` | `true` | Scroll + "Load more" until the whole Forecast deal list is captured. |
| `PIPELINE_FETCH_CHATTER` | `true` | Visit each record and read recent Chatter for context. |
| `PIPELINE_MAX_CHATTER_POSTS` | `5` | Max Chatter posts kept per opportunity. |
| `PIPELINE_CHATTER_TIME_BUDGET` | `240` | Seconds ceiling for the whole per-deal Chatter pass. |
| `PIPELINE_UPDATE_TIME_BUDGET` | `300` | Seconds ceiling for one gated write's browser work. |
| `PIPELINE_SCRAPE_HEADFUL` | `true` | Show Firefox during a live Pipeline scrape so a human can clear an MFA prompt. |
| `PIPELINE_DASHBOARD_NAME` / `PIPELINE_VIEW_NAME` / `PIPELINE_TABLE_TAB` | `Forecast` / `Lanie Form` / `Deal List by Opportunity` | Which dashboard, saved view, and table tab Pipeline Review recreates. |
| `MIC_DIARIZE` | (see `live_transcribe_bot` config) | Enables Deepgram diarization on the mic so a second voice is labelled "Prospect" without a loopback. |
| `LOOPBACK_ACTIVE_WINDOW_S` | (see config) | Window in which a clean loopback suppresses mic bleed of the prospect to avoid duplicate lines. |
| `ENDPOINTING_MS` | `1000` | Deepgram turn-endpointing threshold; raise/lower if turns lock too eagerly or too slowly. |
| `BROWSER_HEADLESS` | `true` | `false` ⇒ watch the Outlook/Salesloft scrapers drive (they dump `browser_profile/debug_*.png`/`.html` on a selector miss). |

---

## 5. Fresh-demo reset & persisted preferences

**Startup reset.** On every launch, `run_pipeline.py` calls
`_reset_for_fresh_demo()` (near `run_pipeline.py:3272`) to wipe the previous run's
generated output so the UI opens clean. The one thing kept is the expensive
ZoomInfo / web-signal enrichment cache — checkpoints in `<Feature>/checkpoints/`
are wiped before each run **except** files listed in `_DURABLE_CHECKPOINTS`
(`run_pipeline.py:85`). A dashboard restart also wipes Bobby's output. Bobby's
in-memory run state is deliberately never re-read from `output/latest.json` (disk
would show a stale presaved run).

**Persisted preferences** (e.g. the saved Salesloft cadence default) live in
`.orum_pipeline_state.json` at the repo root (`_load_state` / `_save_state`,
`run_pipeline.py:338`). **Delete this file to reset** those preferences.

**Session/login files** persist outside the repo and survive a demo reset:
`~/.isc_scraper/` (ISC: `auth_state.json`, `aura_bootstrap.json`) and
`~/.orum_pipeline/` (ZoomInfo / Salesloft / Outlook auth-state files) —
`shared_auth` owns the path mapping.
