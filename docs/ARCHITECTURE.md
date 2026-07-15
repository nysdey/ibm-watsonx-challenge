# Architecture — Seller Dashboard

How the platform is built. This is the canonical "how it works" reference: the system
model, the orchestration hub, the file-handoff contract every step obeys, and a deep
section per sub-app.

Related docs (don't duplicate these here):

- Install / run / test commands, venv setup, moving to a new machine → [OPERATIONS.md](OPERATIONS.md)
- The authorization audit (I1–I67, F1–F10) and the `guard.py` / auth invariants → [SECURITY.md](SECURITY.md)
- Dated change history → [CHANGELOG.md](CHANGELOG.md)
- Inline-JS escaping rules and the latent XSS traps → [GOTCHAS.md](GOTCHAS.md)

---

## 1. System overview

The Seller Dashboard is a **local Flask web app** (`run_pipeline.py`, ~3300 lines) that
lets a seller pull their own book of accounts, score and schedule them, and load contacts
into Salesloft — end to end. The stated goal is ~200 high-quality contacts/day staged in
Salesloft, sourced from the seller's territory, refreshed through end of 2026.

It runs at `http://127.0.0.1:5488` (or the next free port if 5488 is busy) and auto-opens
a browser tab. On startup it wipes the previous run's generated output so the UI opens on
a clean slate — the expensive ZoomInfo/web-signal caches are the one thing kept (see
[§6 Deliberate-design rationale](#6-deliberate-design-rationale-why-it-looks-heavier-than-it-is)).

The app is three user-facing tabs plus a session-management panel:

| Tab | What it is | Backed by |
|---|---|---|
| **Outbound** (default) | The 7-step data pipeline, driven by three combined action buttons | Steps 1–7 (§4) |
| **Meetings** | The live-call copilot | `live_transcribe_bot/` FastAPI subprocess (§4.9) |
| **Pipeline** | Deal-list review over the ISC Forecast dashboard | `Pipeline_Review/` subprocess (§4.10) |
| **Details** button (top-right) | Session/login management (ISC / ZoomInfo / Salesloft / Outlook) + saved-password form | `shared_auth/` + `credential_store.py` (§3) |

Plus **Bobby, the AI Emailer** — a bolt-on Outbound section independent of the three-button
workflow (§4.11).

### Identity → territory

Login is an IBM sign-in on first screen. The seller's **email is their identity**:
`seller_accounts.resolve_seller(email)` maps email → seller name → every Coverage ID
(CovID) assigned to them (as BTSS **or** TSS rep) in `Name Match.xlsx` at the repo root.
Two reps share each CovID by design. There is no territory-map picker in the dashboard
flow — the ISC scraper runs headless on the seller's Name-Match CovIDs. A saved login
skips straight to the main page.

### The three Outbound buttons

Each button runs a fixed sequence of the underlying steps with live, plain-language
progress (raw logs tucked behind a "Show details" toggle):

| Button | Runs | Result |
|---|---|---|
| **Get My Accounts** | ISC Scraper → IBM Scraper → Account Segmentation | "Show results" → segmented accounts |
| **Outbound Strategy** | Account Tiering → Call Planning | "Show results" → tiering table + dial calendar |
| **Fill Contacts to SalesLoft** | ZoomInfo Contact Readiness → Salesloft | pick a cadence, then loads ready contacts into it |

---

## 2. The orchestration model

`run_pipeline.py` is **the shell**. It owns the Flask app, the single-page HTML/CSS/JS UI
(all inline as `*_TEMPLATE` strings), the 2-second status-polling loop, the login/session
panel, and the orchestrators that drive work. Almost all "wire a feature into the
dashboard" work happens in this one file.

**Real work lives in sibling folders.** Each pipeline step (and each bolt-on) is a
standalone folder with its own `run.py`, runnable directly outside the dashboard. The
dashboard never imports a step's internals — it `subprocess.Popen`s the folder's `run.py`
and reads its output file.

```
   run_pipeline.py (Flask hub, :5488)
        │  subprocess.Popen(<Step>/run.py, stdin=DEVNULL)
        │  streams stdout → card live-log; checks return code + last error line
        ▼
   <Step>/run.py  ──writes──▶  <Step>/output/latest.xlsx
                                        │  (file-only seam)
                                        ▼
   next <Step>/run.py  ──reads──▶  validates required columns, or raises
```

**Steps talk to each other only through files** (`<Step>/output/latest.xlsx`), never
through Python calls. The column-level contract those files obey is the File Handoff
Schema Contract (§3).

### Key symbols in `run_pipeline.py`

| Thing | Symbol | ~Line |
|---|---|---|
| Step registry | `STEPS` | `:87` |
| Subprocess launcher (`stdin=DEVNULL`) | `_launch` | `:486` |
| Run-to-completion helper → `(returncode, error)` | `_launch_and_wait` | `:1089` |
| Extract the meaningful failure line from a log | `_last_step_error` | `:1102` |
| Per-step status (state / row count / last-run / log tail) | `_step_status` | `:375` |
| Combined status endpoint + `_actions` block | `api_status` | `:557` / `:561` |
| Fast, mtime-cached row counter | `_row_count` | `:357` |
| Action state dicts | `_GMA_STATE`, `_STRATEGY_STATE`, `_FILL_STATE`, `_BOBBY_STATE` | `:1072`+ |
| Simple subprocess orchestrator | `_run_outbound_strategy` | `:1250` |
| Streaming + watchdog orchestrator | `_run_bobby` | `:1329` |
| Main HTML/CSS/JS template | `PAGE_TEMPLATE` | `ui_templates.py` |
| Card → state applier (JS) | `updateAction` | in `PAGE_TEMPLATE` (`ui_templates.py`) |
| Status poll (JS) | `fetchStatus` | in `PAGE_TEMPLATE` (`ui_templates.py`) |
| Signed-in email | `_signed_in_email` | `:1083` |
| Fresh-demo reset (wipes generated output on startup) | `_reset_for_fresh_demo` | `:3272` |

### The action shape (every user-facing button)

Every action follows the same three-part shape; the UI is built to consume it:

1. **A module-level state dict** — `{"active", "phase", "message", "error", "done"}`.
2. **A worker function** on a background thread that drives the subprocess and keeps the
   state dict current. Fast-fails on missing prerequisites (input file exists? session
   exists?) *before* launching heavy machinery, so the seller sees a clear "do X first"
   message.
3. **A POST endpoint** that guards against double-runs and kicks the worker onto a thread.
   The state dict is exposed through the `_actions` block in `api_status()`, so the
   2-second poll carries it to the browser, where `updateAction(key, ...)` applies it to
   the card (toggles working/done, sets the dot color, streams the live log, disables the
   button while active, renders a results link).

Anything slow runs async on a background thread with a polled state dict — never
synchronously inside a request handler (that freezes the UI). Bobby additionally uses a
**watchdog timer** to kill a hung browser after a ceiling, and a `finally` to clear the
`active` flag.

### Persisted state

- **UI preferences** (e.g. the saved Salesloft cadence default) → `.orum_pipeline_state.json`
  at the repo root (`_load_state`/`_save_state`, `:338`). Delete it to reset.
- **Login sessions** → `~/.isc_scraper/` (ISC) and `~/.orum_pipeline/` (ZoomInfo /
  Salesloft / CID / GTM Nav / Outlook). `shared_auth` knows the paths (§3, [SECURITY.md](SECURITY.md)).
- **Saved W3ID password** → macOS Keychain via `credential_store.py` (never a file).

---

## 3. `shared_auth` — the single login layer

`shared_auth/` is the platform's **single source of truth for every site the dashboard
signs into and how**. A session captured once is shared by *every* corner — the Outbound
pipeline steps **and** the Meetings copilot — instead of each part inventing its own login.
(It replaced the Meetings copilot's former standalone `backend.login` /
`live_transcribe_bot/browser_profile/state.json` flow.)

It distinguishes two things that are easy to conflate:

| | What it is | Where it lives | Written by | Read by |
|---|---|---|---|---|
| **Saved password** | IBM W3ID email + password | macOS Keychain (`credential_store.py`) | you, via *Details ▸ Saved password* | `login_capture.py`, only to auto-fill the SSO form |
| **Captured session** | a Playwright `storage_state` (cookies + localStorage) | JSON under `~/.orum_pipeline/` (ISC: `~/.isc_scraper/`) | `login_capture.py`, once, via a visible browser | every headless scrape |

The captured session is what actually authorizes a scrape; the saved password is optional
convenience. Every IBM-federated site shares the single `w3id` credential because they all
bounce to IBM W3ID SSO. `storage_state` is **browser-engine-agnostic** — a session captured
with Firefox (`login_capture.py`) is reused by Chromium (the Meetings scrapers) without
conversion.

The authoritative site table lives in `registry.py`:

| Service key | Site | Login method | Session file | Used by |
|---|---|---|---|---|
| `isc` | ISC (Salesforce Lightning) | IBM W3ID SSO + MFA | `~/.isc_scraper/auth_state.json` | Outbound |
| `zoominfo` | ZoomInfo | SSO → IBM W3ID | `~/.orum_pipeline/zoominfo_auth_state.json` | Outbound |
| `salesloft` | Salesloft | W3ID SSO on email entry | `~/.orum_pipeline/salesloft_auth_state.json` | **Outbound + Meetings** |
| `cid` | IBM Client Insights | IBM W3ID SSO | `~/.orum_pipeline/cid_auth_state.json` | Outbound |
| `gtmnav` | GTM Navigator | IBM W3ID SSO | `~/.orum_pipeline/gtmnav_auth_state.json` | Outbound |
| `outlook` | Outlook Web calendar | M365 (IBM tenant) → W3ID SSO | `~/.orum_pipeline/outlook_auth_state.json` | **Meetings** |

`salesloft` and `outlook` are the two the Meetings tab needs — and `salesloft` is literally
the same session Outbound already uses.

**Architectural role only** — `shared_auth` is stdlib-only and cheap to import from any
process; it exposes on-disk presence + location (`state_path`, `exists`, `resolve_state_path`,
`services_for`, `credential_key`, `all_services`, `SERVICES`). The heavier *is-it-still-valid?*
probe is `login_capture.py:probe_service`, driven by the dashboard's background validator.
The session/expiry hardening, the drive-by-request guards, and the rest of the authorization
model live in [SECURITY.md](SECURITY.md).

Who imports it: `login_capture.py` (per-service capture config), `run_pipeline.py` (sources
its `LOGIN_SERVICES` map here, so Details ▸ Access lists Outlook alongside ISC/ZoomInfo/
Salesloft), and `live_transcribe_bot/backend/integrations/browser.py` (resolves each scrape's
`storage_state`, falling back to its own legacy `browser_profile/state.json` only if the
shared package isn't importable). Session-expiry handling (an expired ZoomInfo/Salesloft
session bounces to W3ID SSO / `password-blocked.html`; scrapers detect the bounce and
fail fast ~7s with a clear "re-log in via Details" message) is covered in [SECURITY.md](SECURITY.md).

---

## 4. Per-component deep sections

The seven pipeline steps each write a dated file plus an overwritten `latest.xlsx`;
each validates required input columns on load and fails loudly; each supports `TEST_MODE`;
each external-lookup step checkpoints and is safely re-runnable; credentials live in the
Keychain/`.env` (never hardcoded); each logs success/failure/skip-reason per record.

| # | Folder | What it does | Status |
|---|---|---|---|
| 1 | `ISC_Scraper_App/` | Scrape + dedupe accounts off ISC → `DEDUPED_ACCOUNTS`; writes `selected_covids.json` for Step 2 | Working (driven headless by Get My Accounts) |
| 2 | `IBM_Scraper_App/` | Five install-base files scoped to the selected CovIDs | Power local + verified; 4 browser sub-scrapers fail-soft, need portal logins |
| 3 | `Account_Segmentation/` | Deterministically join the 5 install files onto `DEDUPED_ACCOUNTS` by exact IBM IDs → `SEGMENTED_ACCOUNTS` | Working |
| 4 | `Account_Tiering/` | ZoomInfo enrichment (gaps only), buying signals, Tier 1/2/3 scoring | Working |
| 5 | `Call_Planning/` | Distribute tiered accounts across working days through EOY 2026, Tier-1 front-loaded | Working |
| 6 | `ZoomInfo_Contact_Readiness/` | Import list → ZoomInfo → buyer group → export to a Salesloft cadence | Live-verified through the export dialog |
| 7 | `Salesloft_Cadence_Readiness/` | Advance everyone at cadence step 1 into the call step | Built; needs a live Salesloft session |

### 4.1 Step 1 — ISC Scraper (`ISC_Scraper_App/`)

**Purpose.** Scrapes IBM Salesforce (ISC) Territory Prospecting accounts by Coverage ID and
produces a deduped, company-level Excel export. Entry point of the whole pipeline; depends
on no other step. Serves its own Flask UI at `http://127.0.0.1:5477` when run standalone
(clickable US map + industry pills), but Get My Accounts drives it headless.

**Key files.**
- `launcher.py` — Flask UI + bootstrap/parallel dispatch orchestration.
- `_internal/http_scraper.py` — **PRIMARY** scraper: replays Salesforce's internal **Aura**
  endpoint (`POST /aura?...ApexAction.execute=1`, method
  `TerritoryProspectingController.getAccountPageContents`) over HTTP, no full browser.
- `_internal/isc_scraper.py` — LEGACY Playwright browser scraper, fallback only (still works,
  and its `create_prospecting_list`/`add_state_column`/`filter_by_coverage_id` functions are
  the ground-truth verifier).
- `_internal/dedup.py` — dedup + intel tabs; `run_dedup(input, output)` is the real entry point.
- `_internal/CovID.xlsx` — master list: CovID → account name → geo → industry.

**How it works.** A **bootstrap** phase runs once per session: launch headless Firefox,
navigate to Territory Prospecting, intercept the first outgoing Aura POST to capture the real
`aura.token` / `aura.context` / `Referer` / `Origin` / `User-Agent` headers off the wire, save
to `~/.isc_scraper/aura_bootstrap.json`. If redirected to login, a visible Firefox opens for the
human, then cookies are saved to `~/.isc_scraper/auth_state.json`. The **scrape** phase fires one
subprocess per CovID, all parallel (up to `MAX_CONCURRENCY = 20`), each POSTing the Aura endpoint
with its CovID filter and paging (300 rows/call; `page N≥2: limitValue = (N-1)*300 - 1,
preserveCount=False`). The **merge** phase combines chunk files → dedup → `output/
territory_prospecting_export_{run_id}_deduped.xlsx`, then overwrites `output/latest.xlsx`.

**Concurrency design (hard-won — see `CONTEXT.md`).** Concurrent `getAccountPageContents` calls
against the *same* prospect list ID race and clobber each other's filter server-side (returns
0 rows), so each concurrent worker gets its own distinct list ID via a process-wide,
lock-protected `_ListIdRegistry` that coordinates across overlapping `/run` calls. Each `/run`
gets a `run_id` (`{timestamp}_{uuid6}`) in every chunk/output filename so overlapping runs never
clobber. A suspicious 0-row first page retries up to 3× (intermittent Salesforce cache warm-up —
a false-zero is a real bug class, not "empty territory"). Transient network errors retry with
exponential backoff; `_merge_and_dedup` merges whatever chunks succeeded rather than all-or-nothing.

**Dedup design.** Two-stage in `_internal/dedup.py`:
- **Stage 1** (`dedup_exact_duplicates`) — collapse exact-duplicate *location* rows via **CMR
  Number** identity (fallback: exact Name+Address+City+State when CMR blank), MAX-ing quantifiable
  fields within a group so a location scraped twice never double-counts. CMR Number is the correct
  identity key: populated 100%, and only true byte-identical duplicates repeat.
- **Stage 2** (`rollup_by_company`) — the deliverable: group by **Account Name** (fallback Name)
  into one row per real company. Sum per-location metrics (Contact Count, Employee Count, Location
  Annual Revenue, Total IT Spend, Cloud Spend, all 4 IBM Spend columns); **MAX** Global Annual
  Revenue (already an aggregate figure); consolidate Technology Client Status by "most engaged
  wins", Coverage ID into a set, Headquarters to Yes/No/Unknown; drop location-specific/internal
  codes. Every row carries `Distinct Locations` + `Merged From Row(s)` backtrace, and a hard
  invariant check aborts rather than ship a broken backtrace.

**Design notes.** This step always processes its **full** scrape regardless of `TEST_MODE` —
sampling to a small test set happens in Step 4's `sample_selection.py`, because a 5-account
fixture needs to be handpicked for tier diversity. No `.env`; auth is the storage-state file.
Formula-injection (CWE-1236) is neutralized by `_sanitize_cell()` (prefixes leading `= + - @`
with an apostrophe) before writing — external Salesforce names are untrusted. Alongside
`latest.xlsx` it writes `selected_covids.json`, the authoritative set of CovIDs scraped
(including any that returned 0 rows), which Step 2 reads to scope its pulls.

### 4.2 Step 2 — IBM Scraper (`IBM_Scraper_App/`)

**Purpose.** Runs between ISC Scraper and Account Segmentation. Produces five install-base
files, all scoped to the selected CovIDs, by replaying each portal's own data API rather than
scraping canvas.

| Output | Source | Nature | Status |
|---|---|---|---|
| `POWER_INSTALL` | local `POWER_INSTALL_ALL` export, filter col **DQ** (`local coverage type id`) by CovID | pure local, no browser | **Working & verified** |
| `STORAGE_INSTALL` | CID Dashboard (`cid.ibm.com`, Kibana) — `#device-type-selector` → FlashSystem+SVC / Tape / DS8K / SAN → Download CSV, unioned | browser (IBMid → w3id SSO) | Working (live-verified) |
| `CLOUD_INSTALL` | GTM Navigator → Revenue Analysis (Plotly Dash) → replay `/_dash-update-component`, filter `local_coverage_type_id in [CovID]`, `revenue_amt` = T12M spend | browser (w3id SSO) | Working (live-verified) |
| `IBM_NON_INFRA_INSTALL` | ISC Wave dashboard → replay `/wave/query` SAQL on `C360ClientInstallTerritory` | browser (ISC session) | Working (live-verified) |
| `COMPETITIVE_INSTALL` | same dashboard → `C360CompetitorInstallTerritory` | browser (ISC session) | Working (live-verified) |

**How it works.** `python3 run.py` runs all five sub-scrapers; CovIDs auto-resolve via
`covid_source.py` (`--covids` override → `../ISC_Scraper_App/output/selected_covids.json` →
distinct `Coverage ID` in `DEDUPED_ACCOUNTS`). A full run always produces all five so Step 3
joins a consistent set. Each run writes `output/run_manifest.json` and an end-of-run summary
marking every output **FRESH** / **STALE** (a browser sub-scraper failed but an older
`_latest.xlsx` is still on disk — do NOT trust it) / **MISSING**. A browser sub-scraper failing
(expired login, off-VPN) never fails the whole run — stale install data is flagged, never
silently fed downstream.

**Component notes.** Storage: `cid_login.py` seeds the CID session from the **freshest** available
w3id seed (via `w3id_seed.py`, falling back across ISC/gtmnav/cid state files — the ISC session is
refreshed on every Step-1 run, so a live seed is nearly always present). No CovID filter (CID only
shows your own accounts). Cloud: `gtm_login.ensure_session()` **auto-refreshes** its ~daily w3id
expiry unattended via `w3id_login_chrome.py` (automated password login + a CDP virtual authenticator
that no-ops the passkey prompt). IBM-Non-Infra + Competitive share one Wave/CRM-Analytics dashboard
(`Client Install (Territory)`, asset `0FK3h000000gTKLGA2`), reuse the ISC session, and page the
deal-list SAQL (`offset`/`limit` 10000) filtered to the territory user — one query returns the whole
territory. Power reads the monthly `POWER_INSTALL_ALL` export (sheet `Data`, 128 cols; path via
`POWER_INSTALL_ALL_PATH`), exact-matching the trimmed CovID string. Outputs land as
`<NAME>_YYYYMMDD.xlsx` + `<NAME>_latest.xlsx`; the dashboard shows progress but not the files
(`output=None` in `STEPS`).

### 4.3 Step 3 — Account Segmentation (`Account_Segmentation/`)

**Purpose.** Takes `DEDUPED_ACCOUNTS` as the base and **deterministically** joins the five IBM
install files onto it by IBM account identifier (not fuzzy name), then sorts by how many install
types each account has. Output: `output/SEGMENTED_ACCOUNTS_YYYYMMDD.xlsx` + `output/latest.xlsx`
(sheet **`Segmented Accounts`**).

**Inputs.** `DEDUPED_ACCOUNTS` (`../ISC_Scraper_App/output/latest.xlsx`), the account crosswalk
(`../ISC_Scraper_App/output/account_crosswalk.json`, customer-number → account key), and the 5
`*_INSTALL_latest.xlsx` files. Missing install files are treated as "no installs", so it runs fine
before all five IBM sub-scrapers are calibrated.

**The join (`id_match.py`) — deterministic, 100% correct.** Fuzzy name matching produced *wrong*
matches at scale (e.g. `CHEVRON FEDERAL CREDIT UNION` scored 0.85 against an unrelated `CBC FEDERAL
CREDIT UNION`). Instead every install row resolves to a DEDUPED account by trying, in order:
1. **IBM client / buying-group hierarchy code** (`GC…/DC…/GB…/DB…`) — kept on each account as
   `Account Number`.
2. **IBM customer / CMR number** — via `account_crosswalk.json`.
3. **Exact same-system account name** — for ISM/Competitive files whose `L1_ACCOUNT_NAME` is the
   identical ISC string.

A hit is equality, not similarity → guaranteed correct. `<Label>_Match_Basis` records which key
matched (`code` / `customer_number` / `name_exact`). If the base lacks `Account Number` (old
export), it falls back to the legacy fuzzy matcher (`name_match.py`, flagged `review`). When an
account matches several rows, numeric columns are summed and text columns joined (distinct).

**Output columns.** Base DEDUPED columns, then `Install_Types_Count`, `Install_Types`; per type
`<Label>_Present`, `<Label>_Rows`, `<Label>_Match_Score`, `<Label>_Matched_Name`, `<Label>_Match_Basis`;
and (if `ATTACH_INSTALL_COLUMNS`, default on) every install-file column prefixed `<Label>: <col>`.
**Sort:** `Install_Types_Count` descending, tie-broken by presence in priority order
**Cloud → Power → Storage → NonInfra → Competitive**, then Account Name.

### 4.4 Step 4 — Account Tiering (`Account_Tiering/`)

**Purpose.** Enriches the account list with ZoomInfo revenue/employee data and web signals, then
scores and tiers every account 1/2/3. Standalone, manually triggered; auto-locates its input.

> **Input note.** The step README documents reading `../ISC_Scraper_App/output/latest.xlsx`
> directly. In the current dashboard flow, IBM Scraper + Segmentation sit between the ISC scrape
> and Tiering, so Tiering actually reads `SEGMENTED_ACCOUNTS` (which carries the ISC columns plus
> IBM install intel). Required columns validated on load: `Account Name`, `Industry`
> (`schema_io.SchemaError` on miss).

**Outputs.** `output/accounts_tiered_{YYYYMMDD}.xlsx` (or `accounts_tiered_test_{YYYYMMDD}.xlsx`
in TEST_MODE — different prefix so a test run is never mistaken for a real export) + `output/latest.xlsx`,
sheet **`Tiered Accounts`**.

**ZoomInfo matching.** Name-based only (the export has no company-domain column). `ZI_Match_Status`
is `Matched` / `Unmatched` / `Ambiguous`. Unmatched accounts are **never dropped** — they stay with
blank `ZI_*` fields and get median-filled revenue/employee scores rather than being penalized for a
data gap. Tiering looks ZoomInfo up **only for accounts missing revenue/employees** in the
Segmentation data (the rest are sized from their own figures), under a wall-clock budget
(`ZOOMINFO_TIME_BUDGET_SEC`, default 300s), checkpointed per-account so re-runs are near-instant.

**Buying signals.** Scores each account partly on recent buying signals (M&A, funding, layoffs,
leadership change, expansion, earnings, lawsuits) from **Google News RSS** (`signal_scraper.py`) —
a keyless public feed carrying real publish dates. A precision filter requires the company name to
*lead* the headline, so passing mentions don't create false positives. Lookups run in parallel
(~0.06s/account). *(Note: the `Account_Tiering` README / `SIGNAL_DEFINITIONS.md` describe an earlier
DuckDuckGo-HTML backend behind the same `search(query) -> list[SearchResult]` interface, which was
CAPTCHA-blocked in the sandbox build; the top-level README and the Meetings copilot both document
Google News RSS as the current, corroborated backbone. The fixed 11-type taxonomy below is stable
across either backend.)*

Signal taxonomy (`signal_scraper.py` emits exactly one of these as `Signal_{N}_Type`): `Funding`,
`M&A`, `Security_Incident`, `ESG_Commitment`, `Leadership_Change`, `Expansion`, `Earnings_Financial`,
`Partnership`, `Product_Launch`, `Layoffs_Restructuring`, `Regulatory_Compliance`. A signal must name
the specific company (name leads the headline), have a source URL, and is deduplicated to one row per
real event. Zero signals is a legitimate "low-signal account", not an error.

**Scoring — five weighted components** (see the strategy doc; **needs sign-off before running against
the real ~700-account pool**):

| Component | Weight | Column |
|---|---|---|
| Existing IBM relationship | **25%** | `Score_IBM_Relationship` |
| Revenue | 20% | `Score_Revenue` |
| Signal strength | 20% | `Score_Signal` |
| Vertical fit | 20% | `Score_Vertical` |
| Employee count | 15% | `Score_Employees` |

`Tier_Score = 0.25*Relationship + 0.20*Revenue + 0.20*Signal + 0.20*Vertical + 0.15*Employees`

- **Relationship** — base score from `Technology Client Status` (`Existing (Continued)`=100 down to
  `New (Dormant)`=10), adjusted ±10 by IBM spend trend (`IBM Spend Current Year` vs `Prior Year`).
- **Revenue / Employees** — from `ZI_Revenue_USD` / `ZI_Employee_Count` (falling back to Step 1's
  `Location Annual Revenue`/`Employee Count`), log-scaled and percentile-ranked within the run's pool.
  Blank accounts get the **median** matched score (not zero), noted in `Tier_Reasoning`.
- **Signal** — points by type (`Funding`/`M&A` +30 … `Layoffs_Restructuring` **-10**), summed and
  capped [0,100], with a recency multiplier once dates are populated. Zero signals scores 0 (a real
  finding, not median-filled).
- **Vertical fit** — mapped from `Industry`: Core (100) = Healthcare, Government, Banking, Financial
  Markets, Insurance; Adjacent (75) = Telecom, Life Sciences; Baseline (50) = everything else. (The
  strategy doc flags this component as the one most needing review.)

**Score → Tier is percentile-based, not fixed thresholds:** Tier 1 = top 20%, Tier 2 = next 35%,
Tier 3 = remaining 45%, computed within each run's pool — so pool sizes stay predictable (~140/245/315
of ~700) regardless of scoring drift, which keeps Step 5's daily allocation math stable. Every row keeps
all five component scores plus `Tier_Score` and a human-readable `Tier_Reasoning` one-liner.

**Idempotency.** ZoomInfo (`checkpoints/zoominfo_checkpoint.json`) and signals
(`checkpoints/signals_checkpoint.json`) checkpoint per-account; re-running skips completed accounts.
Delete a checkpoint to force a fresh re-lookup.

### 4.5 Step 5 — Call Planning (`Call_Planning/`)

**Purpose.** Distributes every tiered account across working days from today through end of 2026, so
the full pool is exhausted by year-end, and tags each account with the day and tier it was assigned —
the hook for a future planned-vs-actual feedback loop. Auto-locates Step 4's `latest.xlsx`; required
columns `Account Name`, `Tier`, `Tier_Score`. Output: `output/call_plan_{YYYYMMDD}.xlsx` (or
`call_plan_test_` in TEST_MODE) + `output/latest.xlsx`, sheet **`Call Plan`**.

**Design (needs sign-off before the real plan).** Every working day gets a blended list from all
three tiers (never a pure-Tier-3 day) — keeping the tier-vs-outcome feedback loop live across all
tiers from week one. Each tier paces via a per-tier cumulative target curve: **Tier 1 front-loaded**
(50% of Tier 1 targeted within the first 25% of working days, rest linear), **Tier 2/3 linear**.
Within a tier, accounts dial in `Tier_Score` descending order. Within a day, `Day_Sequence_Number`
orders Tier 1 → 2 → 3. Front-load fraction/window are named config constants
(`TIER1_FRONT_LOAD_TARGET_FRACTION`, `TIER1_FRONT_LOAD_WINDOW_FRACTION`).

Daily list size is **accounts/day** (`total_accounts / total_working_days`), deliberately not the
same as the ~200-*contacts*/day goal (contacts-per-account is a downstream ZoomInfo yield, retuned
later via a config quota). Working days = Mon–Fri minus US federal holidays, computed by rule in
`us_holidays.py` (not a hardcoded list). `call_planning.allocate()` asserts every account is assigned
to exactly one day before returning; leftovers land on the final working day (logged). TEST_MODE
compresses pacing to `TEST_MODE_PACING_DAYS` (default 3) so the mechanism is reviewable on a 5-account
sample.

### 4.6 Step 6 — ZoomInfo Contact Readiness (`ZoomInfo_Contact_Readiness/`)

**Purpose.** Triggered manually **per date**: pulls that day's account list from Step 5, imports it
into ZoomInfo as a list, applies the "Infra Outbound" buyer-group filter, and exports the resulting
contacts to a Salesloft cadence — using ZoomInfo's native **Export to Salesloft** integration.
Calibrated live 2026-07-01 (every selector in `zoominfo_import.py` verified against the real app).

**Architecture correction (2026-07-01).** There is no separate Salesloft-login script for the
transfer. ZoomInfo's Export dropdown includes Salesloft; picking it opens a dialog to "Add People To
Salesloft Cadence", switch owner from My Cadences to **Team Cadences**, and pick the cadence — all
inside ZoomInfo, server-side. The old `salesloft_export.py` was deleted;
`zoominfo_import.py`'s `export_to_salesloft()` does the whole thing.

**How it works.** Auto mode (default): load the date's accounts from
`../Call_Planning/output/latest.xlsx` (required: `Account Name`, `Planned_Call_Date`, `Planned_Tier`),
upload as a ZoomInfo company list (Lists → Upload → Text Input), open in Search, apply the Infra
Outbound quick filter, write a review file, export to Salesloft (no confirmation prompt, removed
2026-07-05). Manual mode (`--mode manual`) opens Step 4's full tiered list so you can pick account
names yourself.

**Design notes.** Because revealing emails/phones costs ZoomInfo credits and the transfer happens
server-side, the review file captures **name/title/company text per row**, not scraped emails.
Output `output/contacts_{YYYYMMDD}_{HHMMSS}.xlsx` is never overwritten (each is a human-approval
checkpoint artifact, not a "latest" pointer). Idempotency via `checkpoints/zoominfo_import_{date}.json`.
Live quirks handled: a "Switch to Chrome" nag overlay (dismissed), the org's default buying-group filter
is *not* Infra Outbound (must be switched every time), and the Export → Salesloft cadence picker makes a
real Salesloft API call that can take 10–45s to populate. The `Buyer_Group` filter alone is the quality
bar (no extra seniority/verified-email filtering).

### 4.7 Step 7 — Salesloft Cadence Readiness (`Salesloft_Cadence_Readiness/`)

**Purpose.** Advances everyone currently sitting at cadence step 1 into the call step, via cadence
settings. No input file — reads live from Salesloft. Output:
`output/step_advance_log_{YYYYMMDD}.xlsx` (log only; nothing downstream reads it).

**Redesign (2026-07-05).** The original per-contact design matched exact emails from Step 6's output;
that broke when Step 6 stopped capturing literal emails. Rather than patch matching, this step now
does what the original spec asked: it advances **everyone at step 1** in the given cadence, with no
dependency on Step 6's file. A deliberate simplification, safe as long as Step 7 runs soon after each
Step 6 export (so step 1 never accumulates a previous batch). Idempotency via
`checkpoints/advance_{date}.json` (by name, since there are no emails).

**Status.** Selectors need live calibration — not done as of the 2026-07-05 rework. The placeholder
step names (`CADENCE_FIRST_STEP_NAME = "Step 1"`, `CADENCE_CALL_STEP_NAME = "Call"` in `config.py`)
and the bulk-move UI selectors in `salesloft_advance.py` are unverified guesses; confirm against a
live cadence before trusting.

### 4.8 The Fill Contacts live-write boundary

Running **Fill Contacts** triggers the real ZoomInfo → Salesloft write and the Salesloft cadence
advance — the actions this project's standing rule reserves for the **human** running the script, not
an autonomous agent. Pushing to the real (non-TEST) cadence is treated by Claude Code's own safety
tooling as requiring an explicit permission-settings change, not just in-chat approval. The human runs
this themselves. See [SECURITY.md](SECURITY.md) for the live-write rule and the gating convention.

### 4.9 Meetings — the live-call copilot (`live_transcribe_bot/`)

**Purpose.** A weekly sales-call copilot: reads the Outlook calendar, preps each external call, and
coaches the seller live during it. Formerly standalone, now embedded as the **Meetings** tab.

**How it's wired in.** The copilot is a **FastAPI + WebSocket** app owning the heavy machinery
(Outlook/Salesloft scrape, Claude web-research briefing, Deepgram real-time transcription, local mic +
loopback audio). Rather than re-port it into Flask, `run_pipeline.py` launches its backend as a
**subprocess on a free port** at startup (`_start_meeting_backend`, best-effort — a missing folder/venv
just makes the tab report "unavailable"). The dashboard's Meetings UI talks to that backend over
HTTP + WebSocket (CORS enabled on the backend for exactly this). Nothing in the Outbound flow was
touched. This is the same subprocess-child pattern as the pipeline steps, just with a long-lived server
instead of a one-shot `run.py`.

**Shared login.** The Meetings tab has no separate sign-in. Launched with the dashboard root on
`PYTHONPATH`, its `integrations/browser.py` imports `shared_auth` and resolves each scrape's
`storage_state` — `shared_auth.state_path("outlook")` for the calendar, `"salesloft"` for enrichment
(the same Salesloft session Outbound uses) — falling back to a legacy standalone `browser_profile/
state.json` only if run fully outside the dashboard.

**Module map** (`backend/`):

| Module | Role |
|---|---|
| `integrations/browser.py` | Playwright session layer (storage_state via `shared_auth`) + `jwt_exp` |
| `integrations/outlook_api.py` | `fetch_meetings(days)` via OWA JSON API (`GetCalendarView` + `GetCalendarEvent`) |
| `integrations/salesloft_api.py` | `lookup_people(emails)` via REST `/v2/people.json`, batched |
| `meetings.py` | pipeline entry: scrape → drop internal-only → enrich → derive purpose |
| `briefing.py` | `setup_from_meeting` / `generate_overview` — web research + conversation flow |
| `live_assistant.py` | LLM reasoning: topic segmenter (chunking) + next-question + note filing |
| `orchestrator.py` | real-time turn-taking + topic-chunk gating (audio → STT → LLM → state) + diarization |
| `audio_capture.py` | mic + optional loopback (BlackHole) capture via sounddevice |
| `transcription.py` | Deepgram streaming client |
| `teams_transcription.py` | Microsoft Teams live-captions capture (alternative source) |
| `research_news.py` | Google News RSS briefing source |
| `prefetch.py` | background research for every meeting on tab open |
| `reminders.py` | day-before-3pm reminder scheduler (gated Outlook-compose send) |
| `followup.py` | post-call summary + minutes email draft |
| `state.py` | in-memory `CallState` + websocket pub/sub — **process SINGLETON** |
| `main.py` | FastAPI REST + WebSocket surface, serves `frontend/` |

**HTTP/WebSocket surface** (the loose-coupling seam the dashboard uses): `GET /api/meetings`,
`POST /api/meetings/refresh`, `GET /api/meetings/{id}`, `POST /api/meetings/{id}/prep` (returns
`ready`), `POST /api/research/prefetch`, `GET /api/research/status`, `POST /api/start`·`/api/stop`,
`GET`·`POST /api/transcription/source` `{source: deepgram|teams}`, `POST /api/followup/draft`,
`POST /api/followup/send` (gated `MEETING_FOLLOWUP_SEND=1`), `GET /api/state`, and `WS /ws`
(events: `transcript`, `note`, `question_candidate`, `question_locked`, `chunk`, `chunk_closed`,
`overview`, `overview_error`, `prep_pending`).

**How it works.** On program start and each stale (>3 min) tab open it pulls the next 7 days from
Outlook, drops internal-only (`@ibm.com`-only) meetings, enriches each external attendee from
Salesloft, and lays them on a week calendar — researching every account in the background
(`prefetch.py`) so prep is instant. Clicking a meeting: if research is done, jumps straight to the
two-pane live page (left = scrollable call prep; right = live copilot); if not, an intermediate holding
page (`/meetings/prep`) hands off the moment the briefing is ready. Recording auto-starts only if the
meeting is ≤10 min out.

**Design details.**
- **Calendar read (fast + correct).** Calls Outlook's own API (`GetCalendarView` +
  `GetCalendarEvent`) over plain `urllib`, reading real `RequiredAttendees`/`OptionalAttendees` SMTP
  addresses so the include rule is exactly "any meeting with a non-IBM invitee". Perceived instant
  (last scrape cached to disk); warm refresh ≈1.4s (the data-dependency floor: `GetCalendarView` 0.4s →
  `GetCalendarEvent` fanned into parallel chunks ~0.7s → Salesloft 0.2s); cold ≈5s ~hourly (minting a
  fresh bearer token needs a headless browser). Tokens cached in-memory + on disk; the Salesloft token
  is warmed in parallel under the Outlook scrape. Occurrence date/subject come from `GetCalendarView`
  (authoritative per-occurrence), not `GetCalendarEvent` (which can echo a series master date).
- **Chunking engine (why questions don't churn).** Blocks the conversation into topical chunks and
  tracks each chunk's arc (opening → developing → resolving → resolved). On each completed prospect turn
  it asks Claude *is this still the same topic?* and *has it run its course?* — the next-question box
  holds steady while a topic develops, and a new painpoint-hunting question emerges only when the topic
  wraps or the prospect switches subject.
- **Speaker separation.** Mic = "you", loopback (BlackHole) = "the prospect". Loopback is now optional:
  with Deepgram diarization on the mic, a second voice there is labelled "Prospect". Tune with
  `MIC_DIARIZE` / `LOOPBACK_ACTIVE_WINDOW_S`.
- **Teams captions.** A header toggle switches the source from mic+Deepgram to Microsoft Teams' own
  live captions (`teams_transcription.py`) — the tool opens a **visible** browser, the seller joins the
  call in it (not a ghost bot), opens the meeting's join-URL deep link, turns captions on, and reads
  them. **Must run headed** — headless Chromium can't complete the WebRTC join. Confirmed selectors:
  More ▸ Language and speech ▸ `[data-tid="closed-captions-button-off"]`; captions in
  `closed-caption-v2-window-wrapper` / `[data-tid="closed-caption-text"]`. A **Run pre-flight test**
  button (and `backend.teams_selftest --fake-audio`) validates captions on your tenant before a real
  call.
- **Reliable research.** Briefing "Recent signals & news" is primarily **Google News RSS**
  (`research_news.py`, the same backbone Account_Tiering uses), with Claude `web_search` layered on only
  when the feed is thin, and always a deterministic template fallback so the call page never stalls.
- **Reminders + follow-up.** Every external meeting is scheduled a reminder email the day before at 3pm
  local; the actual send is gated behind `MEETING_REMINDERS_SEND=1` (drives Outlook Web compose UI).
  The post-call **Meeting follow up** drafts a summary + minutes email and reply-alls the invite, gated
  behind `MEETING_FOLLOWUP_SEND=1`. Both stay dark until validated on one contact.

**Embedding assumptions to revisit** (from the standalone integration guide): `state.py` is a process
singleton (single active call — make it per-session for concurrency); everything is in-memory (no
persistence of meetings/transcripts/notes); audio capture is a local Mac mic + BlackHole loopback (a
server deployment must feed PCM frames some other way); one local browser session. Config lives in
`live_transcribe_bot/.env` (`ANTHROPIC_API_KEY`, `DEEPGRAM_API_KEY`, `CLAUDE_MODEL`, `INTERNAL_DOMAINS`,
`CALENDAR_LOOKAHEAD_DAYS`, `BROWSER_HEADLESS`, `OUTLOOK_CALENDAR_URL`, `SALESLOFT_URL`, `MIC_DEVICE`,
`LOOPBACK_DEVICE`, `ENDPOINTING_MS`); its own `venv`; standalone it serves a dashboard at
`http://localhost:8000`.

### 4.10 Pipeline — deal-list review (`Pipeline_Review/`)

**Purpose.** Recreates the ISC **Forecast** dashboard's *Deal List by Opportunity* table inside the
**Pipeline** tab, flags opportunities whose *Next Steps* note has gone stale (>7 days), and lets the
seller push a fresh next step back into Salesforce — the old note preserved in Chatter first. A
self-contained **Shape A** module (§5); dashboard key `pipeline_review`; wired via file-only subprocess
seam per the parallel-build handoff (see **Contributing / parallel builds** below).

**Key files.**

```
run.py               CLI: pull the pipeline → latest.xlsx + latest.json (sample or --live)
update.py            CLI + perform_update(): the GATED write-back (Chatter + Next Step edit)
draft_email.py       CLI: draft a BP follow-up email from latest.json → JSON (read-only, no send)
pipeline_scraper.py  Playwright read: view switch, load-ALL rows, table extract, per-deal Chatter
staleness.py         pure date/quarter/staleness logic (unit-tested)
suggestions.py       BP-led detection, ISC record link, suggested next step, follow-up email draft
sample_data.py       real screenshot rows + synthetic demo rows for scale (TEST_MODE)
schema_io.py         write dated + latest xlsx and latest.json; validate on load
config.py            all paths/tunables/URLs/the gate flags in one place
view_template.py     the results-view HTML (linked table, filters, warnings, update + suggested cols)
preview.py           standalone demo server on :5499 (verify without the dashboard)
```

**How it works.** **Read** (`run.py` + `pipeline_scraper.py`): opens the Forecast dashboard on the
shared `isc` session, switches the saved-view picker from **Modified** to **Lanie Form**, opens the
**Deal List by Opportunity** tab, **loads every row** (scroll + "Load more"), reads each opportunity's
Chatter for context, and writes `output/latest.xlsx` + `output/latest.json`. Per row it derives: ISC
deep-link, Quarter (from Close Date), staleness (from the note's leading `M/D` timestamp — older than
`PIPELINE_STALE_DAYS`=7 earns ⚠ *next to that note*), BP-led (owner is a Business-Partner company like
"CDW Corporation"), and a suggested next step (Claude via `../llm_advisor.py`, else a deterministic
template). **View** (`view_template.py`): the recreated table with Quarter / "needs a refresh only" /
"BP-led only" filters, per-deal Chatter popovers, an inline **Update Next Step** box on every row, and
a BP **Email follow up** button. **Write** (`update.py`, GATED): reads the current Next Step, posts it
to Chatter (so the prior note is kept), then overwrites the Next Step field.

**Design notes.** File-only seam — the dashboard drives `run.py`, `update.py --json`, and
`draft_email.py` as subprocesses (`VENV_PYTHON`, `cwd=Pipeline_Review`, `stdin=DEVNULL`) and never
imports the module (`/api/pipeline_review/data` reads `latest.json` verbatim, so new row fields flow to
the view for free). The live write (`update.py`) is **off by default**, refusing unless
`PIPELINE_ENABLE_UPDATE=1` — exactly like Bobby's Send All; calibrate on one opportunity first. The BP
follow-up email is **not** a server send — the view opens the seller's mail client via `mailto`, so it
needs no gate (`PIPELINE_ENABLE_SEND` reserved, ships dark). `TEST_MODE=true` (default) loads the
built-in sample instantly (no browser/login); `false` or `run.py --live` does a real scrape on the
shared `isc` session. `latest.json` shape:
`{pulled_at, source, count, quarters[], stale_count, opportunities[]}` — written last via atomic swap
after the dated xlsx + `latest.xlsx`. `preview.py` (port **5499**, never collides with 5488) serves the
identical view + endpoints for standalone verification and is **not** part of the integration.

### 4.11 Bobby, the AI Emailer (`Bobby_AI_Emailer/`)

**Purpose.** A separate Outbound section (independent of the three-button workflow). Modules:
`config.py`, `salesloft_api.py`, `emailer.py`, `bobby.py`, `run.py`; dashboard glue in `run_pipeline.py`
(search "Bobby"). Status: everything works and is QA'd **up to — but not including — actually sending**.

**How it works.** The seller picks a Salesloft cadence (hardcoded radios "Targeted Outreach Cadence 3/4",
`BOBBY_CADENCES` in `run_pipeline.py`). **Run Bobby** navigates to `/bobby`, which finds the cadence,
reads every step and identifies email steps (and their cadence day), reads every person on each email
step (name/title/company), writes a personalized email per person keyed to their cadence day + title +
company, and shows the drafts grouped by email step with a **Send All** button.

**How it reads Salesloft — the reliable pattern.** Salesloft's web app is a virtualized React app (no
stable selectors) and its internal `/api/teams/team_cadences` returns empty. Instead `salesloft_api.py`
opens the saved Salesloft session headless, **intercepts the bearer JWT** from the app's own request
`Authorization` header, then calls the **public** REST API `https://api.salesloft.com/v2` with it
(stdlib urllib): `/cadences.json` (fetch ALL — 1000+; a small cap misses "…Cadence 3"), `/steps.json`,
`/cadence_memberships.json`, `/people/{id}.json`. Company is `person_company_name`; a step is an email
step when `type == "email"`; a person is "on" a step when `membership.currently_on_cadence` **and**
`membership.step.id == step.id`. The API client is **read-only** (only `_get`).

**Email generation** (`emailer.py`): Claude via `llm_advisor._complete` when `ANTHROPIC_API_KEY` is set,
else a deterministic still-personalized template (drafts show as "Template" when no key).

**Real-time, never presaved (design).** `/api/bobby/state` returns only in-memory run state — it must
NOT read `output/latest.json` off disk (that showed a stale presaved run). Each run wipes prior drafts;
leaving `/bobby` fires `/api/bobby/reset` (`pagehide` → `sendBeacon`); a dashboard restart wipes Bobby's
output. "already running" self-recovers via a live-process check (`_bobby_running()`); a 600s watchdog
kills a hung browser; per-person fetch+draft is parallelized (8 workers); the token-intercept browser is
closed in a `finally`.

**Endpoints:** `POST /api/bobby/run` {cadence}, `GET /api/bobby/state`, `POST /api/bobby/reset`,
`POST /api/bobby/send` (gated), `GET /bobby`.

**Send is deliberately NOT implemented.** `bobby.send_all()` refuses unless `BOBBY_ENABLE_SEND=1`, and
even then currently raises "not implemented" — nothing sends, there is no send code. This is the
canonical example of the live-write gate every external write in the platform follows (see
[SECURITY.md](SECURITY.md)). Continuing it means implementing the per-person send inside
`bobby.send_all()` (drafts in `output/latest.json` carry `person_id`, `membership_id`, `subject`, `body`,
`email`), making it async with progress like `_run_bobby`, and only arming `BOBBY_ENABLE_SEND=1` after
verifying on one test person.

---

## 5. File Handoff Schema Contract

This is the single source of truth for every column that crosses a step boundary. **Read this before
touching any step's code.** Every step validates its input against this contract on load and fails
loudly (raises, does not silently coerce/drop) if a required column is missing.

Every step's output folder follows:

```
<Step>/output/
    <prefix>_YYYYMMDD.xlsx       # dated, immutable once written
    latest.xlsx                  # copy of the most recent dated file — downstream steps read this
```

`latest.xlsx` is a **copy, not a symlink** (symlinks inside a folder that gets zipped/emailed/synced
are a recurring "why is this file 4kb" source). Every writer overwrites `latest.xlsx` as its **final**
action, after the dated file is fully and successfully written — so a crash mid-write never leaves
`latest.xlsx` pointing at a half-written file.

> The current dashboard flow inserts **IBM Scraper** and **Account Segmentation** between the ISC
> scrape and Account Tiering, so Tiering reads `SEGMENTED_ACCOUNTS` (the ISC columns below plus IBM
> install intel) rather than `DEDUPED_ACCOUNTS` directly. The column contracts below still hold for the
> ISC → … handoff.

### Step 1 → downstream: `ISC_Scraper_App/output/latest.xlsx`

Sheet **`Company Rollup`**. One row per deduped company.

| Column | Type | Notes |
|---|---|---|
| `Name` | str | Raw scraped name |
| `Country` | str | |
| `Account Name` | str | Canonical company identity used for rollup |
| `Coverage ID` | str | Comma/list of CovIDs the company's locations appeared under |
| `Technology Client Status` | str | e.g. `Existing (Continued)`, `New (Whitespace)` |
| `Contact Count` | int | Summed across locations |
| `Industry` | str | |
| `Sub Industry` | str | |
| `Employee Count` | int/blank | Summed; **often sparse — why Tiering re-enriches gaps via ZoomInfo rather than trusting this column** |
| `Location Annual Revenue` | float/blank | Summed; same sparsity caveat |
| `Global Annual Revenue` | float/blank | MAX across locations (already an aggregate per row) |
| `Total IT Spend` | float/blank | Summed |
| `Cloud Spend` | float/blank | Summed |
| `Headquarters` | str | `Yes` / `No` / `Unknown` |
| `Headquarters Country` | str | |
| `LinkedIn URL` | str/blank | |
| `IBM Spend Current Year` | float/blank | Summed |
| `IBM Spend Prior Year` | float/blank | Summed |
| `IBM Spend Prior Year - 1` | float/blank | Summed |
| `IBM Spend Prior Year - 2` | float/blank | Summed |
| `Distinct Locations` | int | Backtrace count |
| `Merged From Row(s)` | str | Backtrace row numbers |

**Required downstream:** `Account Name`, `Industry`. Everything else may be blank per-row (enrichment
fills gaps), but the columns themselves must exist.

Alongside this file, the ISC step also writes `selected_covids.json` (the authoritative set of CovIDs
scraped, including any that returned 0 rows) — the IBM Scraper reads it to scope its install-base pulls.

### Account Tiering output: `Account_Tiering/output/latest.xlsx`

Sheet **`Tiered Accounts`**. All upstream columns, **plus**:

**ZoomInfo enrichment columns** (fixed width — always present, may be blank):

| Column | Type | Notes |
|---|---|---|
| `ZI_Match_Status` | str | `Matched` / `Unmatched` / `Ambiguous` |
| `ZI_Match_Method` | str | `domain` / `name` / blank if unmatched |
| `ZI_Domain` | str/blank | Domain used or discovered during matching |
| `ZI_Revenue_USD` | float/blank | From ZoomInfo, blank if unmatched or not looked up |
| `ZI_Employee_Count` | int/blank | From ZoomInfo, blank if unmatched or not looked up |
| `ZI_Lookup_Timestamp` | ISO datetime str | When this row was looked up (checkpoint/resume marker) |

**Signal columns** (dynamic width). Repeating group, `N` = 1, 2, 3… up to however many signals were
found for that row. The sheet's column count is the max N across all rows; rows with fewer signals have
blank higher-N cells. **Downstream code must never assume a fixed signal column count.**

| Column pattern | Type | Notes |
|---|---|---|
| `Signal_{N}_Type` | str | One of the fixed taxonomy (M&A, Funding, Layoffs_Restructuring, Leadership_Change, Expansion, Earnings_Financial, Partnership, Product_Launch, Security_Incident, Regulatory_Compliance, ESG_Commitment) |
| `Signal_{N}_Date` | date str (`YYYY-MM-DD`)/blank | Real publish date; blank if undated |
| `Signal_{N}_Summary` | str | Headline / short summary |
| `Signal_{N}_Source_URL` | str | |

**Tiering output columns:**

| Column | Type | Notes |
|---|---|---|
| `Tier` | int | `1`, `2`, or `3` |
| `Tier_Score` | float | 0-100 |
| `Primary_Play` | str | Expand & Protect / Displace Competitor / Hardware Refresh / Land New Logo / Win-Back / Nurture |
| `Sales_Angle` | str | Human "why call" one-liner (includes any recent signal) |
| `Spend_Trend` | str | Growing / Declining / Lapsed / New / Flat / Unknown |
| `Score_*` | float | Component scores (relationship, size, footprint, displacement, vertical, signal, contactability) |
| `Tier_Reasoning` | str | Human-readable one-liner explaining the tier assignment |

**Required downstream:** `Account Name`, `Tier`, `Tier_Score`.

### Call Planning output: `Call_Planning/output/latest.xlsx`

Sheet **`Call Plan`**. All Tiering columns, **plus**:

| Column | Type | Notes |
|---|---|---|
| `Planned_Call_Date` | date str (`YYYY-MM-DD`) | Working day this account is assigned to |
| `Planned_Tier` | int | Copy of `Tier` at planning time — frozen so planned-vs-actual stays meaningful |
| `Day_Sequence_Number` | int | 1-based index within that day's batch |

**Required downstream:** `Account Name`, `Planned_Call_Date`, `Planned_Tier`.

### ZoomInfo Contact Readiness output (review/audit only)

`ZoomInfo_Contact_Readiness/output/contacts_{date}_{time}.xlsx`. ZoomInfo's own Export → Salesloft
flow does the actual transfer server-side (no separate Salesloft-login script), and revealing
individual emails/phones in ZoomInfo's UI costs paid credits — so this file carries just enough for a
human to recognize who's included, not per-contact emails. Sheets: **`Contacts For Review`** (before the
export) and **`Contacts Exported`** (after — a log that the export was triggered).

| Column | Type | Notes |
|---|---|---|
| `Raw_Row_Text` | str | First ~300 chars of the contact row's visible text |
| `Buyer_Group` | str | Should always be `Infra Outbound` |
| `Import_Batch_ID` | str | `{date}_{HHMMSS}` |
| `Exported_To_Cadence` | str | The Salesloft cadence chosen in the Fill Contacts dropdown |

### Salesloft: no input handoff — operates directly on cadence step 1

Salesloft Cadence Readiness advances *everyone currently at cadence step 1* in the chosen cadence into
the call step (rather than matching specific contacts). Safe as long as it runs promptly after each
ZoomInfo export. Output: `Salesloft_Cadence_Readiness/output/step_advance_log_YYYYMMDD.xlsx` — log only
(`Contact_Name`, `Cadence_Name`, `Previous_Step`, `New_Step`, `Timestamp`, `Status`).

---

## 6. Deliberate-design rationale (why it looks heavier than it is)

The platform is a Flask hub launching independent subprocesses that hand off via xlsx files. That looks
like more moving parts than a monolith — the separation is intentional, and each part earns its place:

- **Subprocess-per-step with independent venvs = crash isolation + standalone-runnable.** A step is a
  standalone folder with its own `run.py`; the dashboard `subprocess.Popen`s it and never imports its
  internals. A crash, hang, or dependency conflict in one step can't take down the Flask hub or another
  step. Step 1 (`ISC_Scraper_App/`) even carries its own pre-existing `.venv` separate from the shared
  Steps-2–7 venv. Every step can be run directly (`cd <Step>/ && .venv/bin/python3 run.py …`) for
  debugging, exactly as the dashboard runs it.
- **`stdin=DEVNULL` = no interactive hangs.** Every subprocess is launched with stdin closed, so a stray
  `input()` (a ZoomInfo/Salesloft login gate, an old pause) becomes an instant `EOFError` and fails fast
  instead of blocking a run forever. Steps are designed to take all parameters as CLI args, never a
  terminal prompt.
- **File-only xlsx seams = a clean parallel-build boundary.** Steps communicate only through
  `<Step>/output/latest.xlsx`, validated on load against §5. This is what lets a feature be built in a
  sibling folder in total isolation (§7) and lets the dated-file-then-copy-`latest` convention guarantee
  downstream never reads a half-written file.
- **Meetings copilot as a child process, not a re-port.** The copilot is a full FastAPI+WebSocket app
  with heavy machinery (real-time audio, Deepgram, browser scrapes). Rather than re-port it into Flask,
  the hub launches its backend as a subprocess on a free port and talks to it over HTTP/WS — the same
  isolation seam, applied to a long-lived server. A missing folder/venv just degrades the tab to
  "unavailable" instead of breaking the app.
- **`(path, mtime)` row-count cache = cheap status polling.** The row counts on each card are cached by
  file mtime (`_row_count`), so the 2-second `/api/status` poll stays ~1 ms even though the Segmentation
  workbook is ~4 MB / 600+ columns. The seller's Segmentation results view shows only the ~11 columns a
  seller reads (cached and pre-warmed), not all 600+.
- **Durable ZoomInfo/signals checkpoints = bounded cold runs, near-instant re-runs.** External-lookup
  steps checkpoint progress per-account (`checkpoints/*.json`). The fresh-demo reset wipes generated
  output and checkpoints on startup so the UI opens clean — **except** the expensive-to-rebuild caches
  in `_DURABLE_CHECKPOINTS` (ZoomInfo enrichment, web signals), which persist across restarts. Tiering
  enriches only accounts missing revenue/employees, under a wall-clock budget, so a cold run is bounded
  and a re-run is near-instant.

---

## 7. Contributing / parallel builds

New functionality is built in **isolation, in a sibling folder, then wired in additively** — never by
editing the pipeline steps or their schema contract. The full engineering brief is
the parallel-build workflow (consolidated into this section); the essentials:

**Two shapes of feature.**
- **Shape A — standalone module + dashboard glue** (like a pipeline step, or Bobby, or Pipeline Review):
  the feature does real work (scrapes, enriches, calls an API, produces a file). Create a **new sibling
  folder** with its own `run.py`; add a thin orchestrator + card + endpoint in `run_pipeline.py` that
  drives it as a subprocess. **The folder is 100% yours** — the only shared file is `run_pipeline.py`,
  touched only in a few clearly-bounded spots. This is the norm and the most parallel-friendly. Copy
  `Account_Tiering/` as the cleanest skeleton (`run.py`, `config.py`, `env_utils.py`, `schema_io.py`,
  `<domain>.py`, `README.md`, `output/`, `checkpoints/`, `logs/`).
- **Shape B — pure dashboard glue**: something small and presentation-y (a new view over an existing
  `latest.xlsx`, a read-only `/api/…`, a settings toggle) that needs no subprocess and no new output.
  Lives entirely inside `run_pipeline.py`. If unsure, choose Shape A.

**Non-negotiable module rules** (the platform's global contract): `run.py` runs headless and
non-interactively (`stdin=DEVNULL`, never `input()`); print plain-language progress to stdout (the
dashboard streams it into the card log); exit non-zero on hard failure (don't report false success);
validate inputs on load and fail loudly; write the dated file first then overwrite `latest.xlsx` as the
final action (a copy, never a symlink); never hardcode credentials (Keychain/`.env`, add new keys to
`.env.example`); support `TEST_MODE`.

**The additive wiring in `run_pipeline.py`** (each spot is append-a-block, don't rewrite): an optional
`STEPS` entry (`output=None` to show a run marker but never surface a file); a `_MYFEATURE_STATE` dict;
a `_run_myfeature` worker on a background thread (fast-fail on missing prerequisites first); a
`/api/myfeature/run` POST endpoint that guards double-runs; one line adding the state dict to
`api_status`'s `_actions` block; a card in the right `<section>` of `PAGE_TEMPLATE`; a `runMyFeature()`
handler + one `updateAction('myfeature', …)` line in `fetchStatus`. A whole new tab adds a nav button +
a `<section>` (the JS `showPage()` toggles `.active` by `data-page`/`id`).

**Shared services to lean on** (don't rebuild): `llm_advisor._complete` (Claude, guard with
`.available()`); `shared_auth.state_path/exists/load_state` (saved sessions — never write a new login
flow); `credential_store.save/get/has` (Keychain); `_signed_in_email()` +
`seller_accounts.resolve_seller(email)` (email → territories); `_row_count(path, sheet)` (mtime-cached);
the Google-News-RSS buying-signal pattern in `Account_Tiering/signal_scraper.py`.

**The parallel-build handoff.** A module built in isolation ships with an **INTEGRATION.md** — the exact,
copy-paste, additive `run_pipeline.py` snippets to wire it in, applied *only when told to integrate*.
Pipeline Review's integration handoff is the worked example: nine numbered
spots (module dir + view template, `STEPS` entry, state dict, worker, five routes, `_actions` line, card
markup, JS hooks, `.env.example` keys). The rule the memory index states plainly: **don't touch
`run_pipeline.py` until told** — build against the file-only seam, hand back an INTEGRATION.md, and let
the session that owns `run_pipeline.py` apply it.

**The live-write rule.** Anything that *sends* an email, advances a cadence, or writes to an external
system is reserved for the human running the script — an autonomous agent must not fire it. Ship the
write path **gated off by default** behind an explicit env flag (`BOBBY_ENABLE_SEND`,
`PIPELINE_ENABLE_UPDATE`, `MEETING_REMINDERS_SEND`, `MEETING_FOLLOWUP_SEND`), calibrate on ONE record
first, and build/QA everything *up to* the write while leaving the trigger dark. The rule and its
rationale are in [SECURITY.md](SECURITY.md); the inline-JS escaping and latent-XSS traps to avoid when
editing the template are in [GOTCHAS.md](GOTCHAS.md).
