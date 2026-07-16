# BobBee — self-contained demo of the Seller Dashboard

A **fully mocked, offline clone** of the Seller Dashboard, rebranded and redesigned
as **BobBee**: a four-step AI-powered outbound workflow (Accounts → Strategy →
Contacts → Bobby AI). It looks and behaves like the real app — the same IBM sign-in,
the same three underlying Outbound actions, the same results screens and Bobby the
AI Emailer — but **every external connection is faked** (ISC, IBM install base,
ZoomInfo, Salesloft), so it runs on any machine with no logins, no VPN, and no
internet.

The one connection that's **real**: **IBM watsonx.ai**. Bobby's email drafts and
the tiering Play/Angle are live model calls (Granite, `ibm/granite-4-h-small`) when
`.env` is configured — confirmed working end-to-end, including a retry-with-backoff
layer so watsonx.ai's rate limits on lower service tiers don't silently degrade every
call to the deterministic fallback (see [Configuring live AI](#configuring-live-ai-watsonxai)).

Run it with `npm start` (see [Quick start](#quick-start)).

What's different from the original (by design):

| Area | Original | This clone |
|---|---|---|
| **Meetings tab** (live-call copilot) | `live_transcribe_bot/` FastAPI backend | **Removed** |
| **Pipeline tab** (deal-list review) | `Pipeline_Review/` | **Removed** |
| **IBM data** (ISC accounts + 5 install-base files) | live Salesforce/CID/GTM scrapes | **Faked** — `fake_data.py` generates a realistic, deterministic account pool |
| **ZoomInfo** (tiering enrichment + contact readiness) | headless ZoomInfo browser | **Mocked** — deterministic revenue/employees + contacts |
| **Salesloft** (Fill Contacts load, cadence advance, Bobby) | real `api.salesloft.com` / web UI | **Mocked** — an in-app "Salesloft server" (`mock_salesloft.py`) |
| **Buying signals** (Google News) | live RSS feed | **Mocked** — deterministic signals |
| **Logins** (IBM W3ID SSO) | real SSO + macOS Keychain | **Mocked** — any email works; only the email is kept locally, the password is discarded |
| **Tool windows** (the sites the app opens) | real ISC / ZoomInfo / Salesloft | **Mock UIs** served in-app (`/mock/...`) |

Everything else — the pipeline architecture, the file-handoff contract between steps,
the scoring/tiering/call-planning logic, and the UI — is the **same code** as the
original, running on the fake/mock data.

## Quick start

```bash
npm start   # first run: creates .venv, installs Flask + openpyxl, launches the app
```

Equivalent manual steps, run from this repo's root:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt   # Flask + openpyxl + python-dotenv
.venv/bin/python3 run_pipeline.py
```

Opens the dashboard at `http://127.0.0.1:5488` (auto-opens a browser tab). On the
**IBM Login gate**, sign in with *any* email (e.g. `demo.seller@ibm.com`) and any
password — the email picks your (demo) territory; nothing is sent anywhere.

### Configuring live AI (watsonx.ai)

Bobby's email drafts, the tiering Play/Angle, and the call-plan coaching note are all
enriched by a live watsonx.ai call when credentials are present — and fall back to
deterministic templates when they aren't, so the app runs fine either way.

1. `cp .env.example .env` at the repo root.
2. Fill in `WATSONX_API_KEY`, `WATSONX_PROJECT_ID`, and `WATSONX_URL` (your
   project's region endpoint) — see the comments in `.env.example` for where to find
   each in the watsonx.ai console. `WATSONX_MODEL_ID` defaults to
   `ibm/granite-4-h-small`.
3. Restart the app — `run_pipeline.py` loads `.env` itself (via `python-dotenv`) at
   startup, so no manual `export` is needed. Every pipeline step runs as its own
   subprocess and inherits this environment, so one `.env` at the repo root covers
   Bobby, Account Tiering, and Call Planning.
4. Check it actually worked: run **Bobby** (Step 4), then look at its **Watsonx
   Activity** panel — `status: success` with a real `latency`/`tokens` means the
   live call went through; `status: partial` means some of that run's calls
   succeeded and some fell back to the template after exhausting retries (see
   below); `status: error` means credentials are set but the call itself is
   failing (see troubleshooting below); `status: not called` means credentials
   aren't set at all.

**On rate limits:** Bobby drafts emails from an 8-way parallel thread pool, which
reliably trips rate limiting on a Lite-plan watsonx.ai project. `llm_advisor.py`
retries a rate-limited or transient-error call up to 3 times with exponential
backoff + jitter before falling back to the template for that one person — in
testing this took a cadence from ~15% live-AI emails to ~92%. `status: partial`
with a handful of template fallbacks in a large batch is expected on a Lite plan,
not a bug.

**Troubleshooting a failed call** (`status: error` in the Watsonx Activity panel) —
these are the two errors this project actually hit setting it up:

- `container_not_found: Failed to find project_id ...` — either the project ID is
  wrong, or `WATSONX_URL`'s region doesn't match where the project actually lives
  (`us-south`, `eu-de`, `eu-gb`, `jp-tok`). Re-copy the Project ID from **watsonx.ai
  console → Project → Manage → General**, and match the region in the URL bar.
- `no_associated_service_instance_error: project_id ... is not associated with a WML
  instance` — the project exists and the ID is right, but it has no **Watson Machine
  Learning** service instance associated with it (that's the actual compute that runs
  inference). Fix in the console: **Project → Manage → Services & integrations** →
  associate (or create) a Watson Machine Learning instance.

## What you see

A single dark, IBM-themed dashboard — no tabs. The visual language is deliberate:
**blue** is deterministic pipeline data, **purple + a sparkle icon** is anything
watsonx.ai actually generated. Nothing in the UI blurs that line.

1. **IBM Login gate** — a demo sign-in. Any email works; a stable demo territory is
   assigned when the email isn't a real rep in `Name Match.xlsx`.
2. **A 4-step pipeline**, each step its own card with a live status dot and a
   **Run step** button:

   | Step | Runs | Result |
   |---|---|---|
   | **1. Accounts** | ISC (fake) → IBM install base (fake) → Account Segmentation | ~280 segmented accounts, viewable with tier breakdown bars |
   | **2. Strategy** | Account Tiering (mock ZoomInfo + signals, watsonx.ai Play/Angle) → Call Planning | tier table (blue deterministic Score/Tier + purple watsonx Play/Angle) + a weekly call-plan timeline |
   | **3. Contacts** | ZoomInfo Contact Readiness (mock) → Salesloft advance (mock) | a funnel view (accounts → contacts identified → Salesloft-ready) + contact cards |
   | **4. Bobby AI** | reads a (mock) Salesloft cadence's email steps and drafts a personalized email per person via watsonx.ai (falls back to a deterministic template per-person if the live call fails) | a 3-panel review page: contact + signals, the generated email, and a **Watsonx Activity** panel showing the real model/latency/tokens/status of that email's live call |

3. **5 KPI cards** (accounts analyzed, Tier 1 accounts, contacts staged, emails
   generated, time saved) and a **productivity-impact** section below the pipeline —
   both update live as steps complete.
4. **Details** (top-right) → **Access** — all sessions show "logged in" (mocked). The
   **Log in** buttons open in-app mock sign-in pages; **Open** buttons open the mock tools.

## The mock tool UIs

Wherever the real app would open an external tool, this clone opens a self-contained
mock instead (each marked with a "🧪 MOCK" banner):

- `GET /mock/salesloft` — a Salesloft-style cadence view showing the contacts Fill
  Contacts loaded and whether they're at Step 1 or advanced to the Call step.
- `GET /mock/zoominfo` — a ZoomInfo-style company table of the current territory.
- `GET /mock/isc` — an ISC / Salesforce-style account list.
- `GET /mock/<isc|zoominfo|salesloft>/login` — branded mock sign-in windows.

## How the faking is wired

- **`fake_data.py`** — the deterministic (seeded) core. Given a set of Coverage IDs it
  produces a stable account pool; the same account keeps one identity (hierarchy code,
  customer number, revenue, install rows) across every step, which is what lets Account
  Segmentation's *exact* join actually attach the install files. Also generates the
  ZoomInfo enrichment, buying signals, and Salesloft cadences/people.
- **`mock_salesloft.py`** — a tiny JSON-backed "Salesloft server": Fill Contacts loads
  people into it, the advance step moves them, and `/mock/salesloft` renders it.
- **`mock_ui_templates.py`** — the mock tool UIs.
- Each pipeline step's external-facing module was replaced with a fake that keeps the
  same public entry point + output schema (search the tree for the `MOCK` docstrings):
  `run_pipeline._isc_scrape`, `IBM_Scraper_App/sub_*.py`,
  `Account_Tiering/zoominfo_enrich.py` + `signal_scraper.py`,
  `ZoomInfo_Contact_Readiness/zoominfo_import.py`,
  `Salesloft_Cadence_Readiness/salesloft_advance.py`, `Bobby_AI_Emailer/salesloft_api.py`.

## Tests

```bash
.venv/bin/python3 tests/test_dashboard.py         # clone invariants (no pytest needed)
.venv/bin/pip install pytest
.venv/bin/python3 -m pytest tests/ -q             # + auth-guard / guard tests
```

## Documentation

The deep docs in [`docs/`](docs/) describe the **original** Seller Dashboard's design —
the 7-step pipeline, the file-handoff schema contract, and the auth model. They still
apply to this clone's architecture, with two exceptions: the Meetings and Pipeline tabs
are gone, and every external data source is mocked (this README is the source of truth
for those differences).
