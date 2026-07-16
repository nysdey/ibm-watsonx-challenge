# BobBee — self-contained demo of the Seller Dashboard

A **fully mocked, offline clone** of the Seller Dashboard, rebranded and redesigned
as **BobBee**: a four-step AI-powered outbound workflow (Accounts → Strategy →
Contacts → Bobby AI). It looks and behaves like the real app — the same IBM sign-in,
the same three Outbound actions, the same results screens and Bobby the AI Emailer —
but **every external connection is faked**, so it runs on any machine with no logins,
no VPN, and no internet.

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
cd "…/WatsonX Clone"
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt   # just Flask + openpyxl
.venv/bin/python3 run_pipeline.py
```

Opens the dashboard at `http://127.0.0.1:5488` (auto-opens a browser tab). On the
**IBM Login gate**, sign in with *any* email (e.g. `demo.seller@ibm.com`) and any
password — the email picks your (demo) territory; nothing is sent anywhere.

## What you see

1. **IBM Login gate** — a demo sign-in. Any email works; a stable demo territory is
   assigned when the email isn't a real rep in `Name Match.xlsx`.
2. **Outbound tab** (the only tab) with three combined action buttons:

   | Button | Runs | Result |
   |---|---|---|
   | **Get My Accounts** | ISC (fake) → IBM install base (fake) → Account Segmentation | ~280 segmented accounts |
   | **Outbound Strategy** | Account Tiering (mock ZoomInfo + signals) → Call Planning | tier table + dial calendar |
   | **Fill Contacts to SalesLoft** | ZoomInfo Contact Readiness (mock) → Salesloft advance (mock) | loads contacts into a mock cadence |

   Plus **Bobby, the AI Emailer** — reads a (mock) Salesloft cadence's email steps and
   drafts a personalized email per person (Claude if `ANTHROPIC_API_KEY` is set, else a
   deterministic template).
3. **Details** (top-right) → **Access** — all sessions show "logged in" (mocked). The
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
