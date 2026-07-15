# Security & Authorization

Consolidated from AUTHORIZATION_SPEC.md + shared_auth/README.md (2026-07-15)

Read this before touching anything that authenticates, captures a session, writes a
credential/token file, or serves a local HTTP endpoint. It is the canonical catalog of
authorization failure modes for the Seller Dashboard: who may do what, against which
third-party system, with which secret, and when that permission is (or is only *believed*
to be) valid.

The findings came from a five-front sweep — the session core, the Meetings backend, the
Flask/HTTP surface, the ISC/IBM scrapers, and a secret-leakage pass — cross-checked
against live on-disk state and `git`. Severity: **P0** immediate (causes today's failure
or a live drive-by) · **P1** latent correctness/security · **P2** robustness /
future-proofing.

- Component architecture is in [ARCHITECTURE.md](ARCHITECTURE.md).
- Operational how-to (re-login, resetting W3ID, running services) is in [OPERATIONS.md](OPERATIONS.md).

---

## 1. Threat model

### 1.1 First principles (F1–F10)

Every one of the 67 issues below is one of these irreducible truths showing through the
code. Fix the principle, not just the symptom.

| # | Principle | Consequence here |
|---|---|---|
| **F1** | A bearer credential is **opaque and unverifiable except by use.** Session cookies / `storage_state` / JWTs carry no reliable client-visible expiry. | The only honest check is "navigate and see if it bounces." Every proxy (a file exists, a 150-s badge, a URL substring) can lie. |
| **F2** | **Time-of-check ≠ time-of-use (TOCTOU).** | Any gap between verify and use is a window to die in. The probe is ≤150 s stale; a scrape runs minutes. |
| **F3** | **Shared mutable state across processes needs coordination.** | Session/token files are read/written by many processes with **no lock, non-atomic writes, and world-readable perms**. |
| **F4** | **Delegation concentrates authority; unscoped delegation maximizes blast radius.** | One `w3id` password + federated SSO unlocks six services; one live state file re-mints all of them. |
| **F5** | **Ambient authority acts without a fresh human decision — and any local caller is trusted.** | Auto-fill types the password on substring-trust; the dashboard + two backends trust *any* local process/browser tab (localhost drive-by). |
| **F6** | **Duplicated truth drifts.** | The "single source of truth" is bypassed by ~10 modules with their own path strings and login-marker lists. |
| **F7** | **Identity ≠ entitlement, and entitlement is time-varying.** | email→CovID is a static xlsx; fuzzy name matching can bind to another seller's book; buyer-groups/credits change server-side. |
| **F8** | **Secrets rotate, lock, and get deprecated.** | W3ID expiry, MFA, and IBM's **mandatory-passkey** push (the whole `password-blocked` dance) will break auto-fill for all six at once. |
| **F9** | **Replayed sessions have no attribution, and secrets leak through the exhaust.** | No local audit; and tokens/URLs/DOM leak into logs, status files, error text, screenshots, and world-readable caches. |
| **F10** | **Failure must be safe and legible, not silent or destructive.** | Gates are coarse env flags; "0 rows" is read as "empty" not "unauthorized"; a follow-up can send to the wrong meeting. |

### 1.2 The dominant threat is *local*, not the network

Every server binds loopback (`127.0.0.1`), so this is **not** LAN-exposed. But loopback is
worthless against the two real adversaries:

- **(a) any other process / UNIX account on the Mac** — reads the world-readable session &
  token files, hits the unauthenticated local ports.
- **(b) any web page the seller visits** — can `fetch()`/`WebSocket()` to `127.0.0.1` and,
  because the dashboard has no CSRF defense and the Meetings backend uses wildcard CORS,
  *drive and read* the seller's authenticated sessions (a "localhost drive-by" /
  DNS-rebinding surface).

Treat both as in-scope.

### 1.3 Where the credentials/sessions live (map)

- **Password:** macOS Keychain item `orum-pipeline-cred-w3id` (`credential_store.py`) — one `w3id` for all six IBM-federated services.
- **Captured sessions:** Playwright `storage_state` JSON — `~/.isc_scraper/auth_state.json` (ISC) and `~/.orum_pipeline/{zoominfo,salesloft,cid,gtmnav,outlook}_auth_state.json`. **Originally mode 0644 (world-readable); now hardened to 0600.**
- **Derived tokens:** ISC Aura bootstrap `~/.isc_scraper/aura_bootstrap.json` (a 2nd copy of the SF cookie); intercepted Salesloft/OWA JWTs cached at `live_transcribe_bot/browser_profile/{salesloft,outlook}_token.json` (**in the repo tree**).
- **Control/observability:** `.orum_login_control/login_status_<svc>.json` (records live URLs); per-step logs (`<Step>/logs/`); `IBM_Scraper_App/_login_debug/*.png` (was git-tracked, now untracked+gitignored).
- **Registry:** `shared_auth/registry.py` (the partly-bypassed single source of truth) + `shared_auth/guard.py` (enforcement).

### 1.4 The immediate issue (the screenshot) — I1

`Fill Contacts to SalesLoft` stopped with *"Your ZoomInfo session has expired (bounced to
`https://login.w3.ibm.com/saml/sps/auth`)."* Today's log
(`ZoomInfo_Contact_Readiness/logs/run_20260715_091623.log`) shows the exact bounce;
`.orum_login_control/login_status_zoominfo.json` is the only service not `"saved"` — stuck
at `{"state":"launching"}`.

**Root cause (not just "log back in").** `_run_fill_contacts`
([run_pipeline.py:1378](../run_pipeline.py#L1378)) gates on `LOGIN_SERVICES[svc].exists()` —
*"is there a file on disk?"* — when the background validator **already knows** the probe
verdict (`_login_status(svc)["state"]` = `ready`/`expired`). It ignores that, launches the
whole ZoomInfo automation, and rediscovers the dead session by bouncing mid-run. This is
**I1**, and the *trust-a-cheap-proxy* pattern behind it recurs throughout (F1/F2). Fixed by
the JIT probe gate (§3).

---

## 2. The guard / shared_auth package

Two packages carry the authorization model: `shared_auth` (the registry — where sessions
live) and `shared_auth/guard.py` (the enforcement library). See
[ARCHITECTURE.md](ARCHITECTURE.md) for how callers wire them together.

### 2.1 shared_auth registry — single source of truth

`shared_auth` is the single source of truth for every site the dashboard signs into. A
session captured once is shared by *every* part of the platform — the Outbound pipeline
steps **and** the Meetings live-call assistant. Only on-disk presence + location live here
(stdlib-only, cheap to import from any process).

There are **two distinct things**:

| | What it is | Where it lives | Who writes it | Who reads it |
|---|---|---|---|---|
| **Saved password** | your IBM W3ID email + password | macOS **Keychain** (`credential_store.py`) | you, via *Details ▸ Saved password* | `login_capture.py` (only to auto-fill the SSO form) |
| **Captured session** | a Playwright `storage_state` (cookies + localStorage) | a JSON file under `~/.orum_pipeline/` (ISC: `~/.isc_scraper/`) | `login_capture.py`, once, via a visible browser | every headless scrape |

The **captured session** is what actually authorizes a scrape. The **saved password** is
optional convenience (auto-fills the W3ID prompt). Every IBM-federated site shares the
single `w3id` credential because they all bounce to IBM W3ID SSO. `storage_state` is
**browser-engine-agnostic** — a Firefox-captured session is reused by Chromium scrapers
without conversion.

The service table (authoritative copy in `registry.py`):

| Service | Site | Login method | Session file | Used by |
|---|---|---|---|---|
| `isc` | ISC (Salesforce Lightning) | IBM W3ID SSO + MFA | `~/.isc_scraper/auth_state.json` | Outbound |
| `zoominfo` | ZoomInfo | SSO → IBM W3ID | `~/.orum_pipeline/zoominfo_auth_state.json` | Outbound |
| `salesloft` | Salesloft | W3ID SSO on email entry | `~/.orum_pipeline/salesloft_auth_state.json` | **Outbound + Meetings** |
| `cid` | IBM Client Insights | IBM W3ID SSO | `~/.orum_pipeline/cid_auth_state.json` | Outbound |
| `gtmnav` | GTM Navigator | IBM W3ID SSO | `~/.orum_pipeline/gtmnav_auth_state.json` | Outbound |
| `outlook` | Outlook Web calendar | M365 (IBM tenant) → W3ID SSO | `~/.orum_pipeline/outlook_auth_state.json` | **Meetings** |

The heavier **is-it-still-valid?** check (navigate headless, see if it bounces to a login
page) is `login_capture.py:probe_service`, driven by the dashboard's background validator.

### 2.2 guard.py invariants

`shared_auth/guard.py` is the central prevention library, unit-tested 10/10
(`tests/test_guard.py`). These invariants MUST hold — do not weaken them:

- **Exact-origin password-fill allowlist** — `guard.login_origin_allowed` fills the
  password **only** on an exact scheme+host allowlist, asserted against the **top-frame**
  origin; never inside a cross-origin iframe or open-redirect landing page (I7, I29). This
  replaces the loose substring match (`w3id`/`okta`/`sso`/`signin` anywhere in the URL).
- **No-save-on-bounce** — `guard.atomic_save_state(final_url=page.url)` **refuses to
  persist a non-valid session**, so a run that ended on a login bounce cannot overwrite a
  good session with a logged-out one (I18).
- **Atomic, validity-guarded 0600 writes** — session/token writes go through
  `guard.atomic_save_state`: written via `mkstemp(mode=0o600)`, validity-guarded, then
  atomically renamed. `guard.harden_perms()` is a one-shot to fix existing files to 0600
  (I19, I23, I67).
- **flock** — cross-process coordination via `guard.session_lock` (flock) +
  `guard.is_locked_exclusive`; the validator honors the lock and does not fire competing
  probes during an automation run (I4).
- **Redaction-before-persist** — `guard.redact_url` strips OIDC/SAML query params
  (`code`/`state`/`SAMLResponse`) and persists **host only** for login URLs, applied
  before any status file, error string, or log line is written (I64, I65).
- **Audit log** — `guard.audit`: append-only, secret-free log of session/credential use so
  replay is distinguishable from the human (I16).
- **Wipe** — `guard.wipe_all(include_credential=…)`: revocation / offboarding path that
  signs out everywhere (I32).

Full surface: `is_login_url` / `is_valid_app_url` / `session_verdict`,
`login_origin_allowed`, `atomic_save_state`, `session_lock` / `is_locked_exclusive`,
`redact_url`, `harden_perms`, `audit`, `wipe_all`.

### 2.3 The local-HTTP `before_request` guard

The dashboard (`run_pipeline.py`) enforces, in a single `before_request` hook, a
**loopback + Origin/Referer + Host + per-launch-token** guard — the fix for the
confused-deputy cluster (I46/I47/I48/I49). Verified live:

- **Host-header check** — validate `Host ∈ {127.0.0.1:<port>, localhost}`; DNS-rebinding → 403.
- **Origin/Referer allowlist** — cross-origin mutating POST → 403; same-origin UI → 200. Reject non-`application/json`.
- **Per-launch secret token** — checked in `before_request`; token path → 200. No UI change needed.

### 2.4 JIT probe, self-healing watchdog, circuit breaker

- **JIT probe** — `_ensure_services_ready` runs a just-in-time blocking `_probe_login_once`
  and requires `state=="ready"` before Fill Contacts / Get My Accounts launches (I1). The
  150-s "ready" badge is advisory; the pre-run probe is authoritative (I2).
- **Self-healing watchdog** — `_maybe_auto_login` is automation-aware, lock-aware, and
  circuit-broken after `_MAX_AUTO_LOGIN_FAILS`; `/api/auth/health` exposes it (I8, I15, I34).
- **Circuit breaker** — after N failed auto-fills, stop and prompt "update your saved W3ID
  password" rather than re-submitting a stale password across six services into account
  lockout / MFA fatigue (I15, I34).

**MFA note:** self-healing re-login drives the SSO auto-fill but a human still taps MFA —
irreducible for MFA-gated SSO. The watchdog does everything up to that tap; the breaker
stops it from nagging.

---

## 3. Issue register (67)

Format: **location · failure · principle · solution · severity.** Grouped by principle.
Guard-fixed items name the `shared_auth.guard` function. Landed/verified status is in §4.

### A. Verified-validity gating & TOCTOU (F1, F2)

| ID | Finding | Fix | Sev |
|---|---|---|---|
| **I1** | `run_pipeline.py:1378`,`:1259` gate on `.exists()` not the probe verdict → dead session launches full automation, bounces mid-run (the screenshot). | Just-in-time blocking `_probe_login_once` + require `state=="ready"` before launch. | **P0** |
| **I2** | `_LOGIN_PROBE_INTERVAL=150` — the "ready" badge is ≤150 s stale. | Badge advisory, pre-run probe authoritative (with I1). | **P1** |
| **I3** | `_run_fill_contacts` aborts the whole action on mid-run expiry; checkpoints exist but aren't used to resume. | Pause → re-auth → resume-from-checkpoint. | **P1** |

### B. Session store — locking, atomicity, at-rest hygiene (F3)

| ID | Finding | Fix | Sev |
|---|---|---|---|
| **I4** | No cross-process lock + non-atomic in-place `storage_state(path=…)` writes (`login_capture.py:652`, every `bootstrap_if_needed`) → torn reads; the validator (`scraping` flag is ISC-only) fires competing probes during a Fill Contacts run. | `guard.atomic_save_state` + `guard.session_lock` (flock); validator honors `guard.is_locked_exclusive`. | **P1** |
| **I18** | Scrapes re-save state on exit unconditionally (`isc_scraper.py:573`) → a run that ended on a bounce overwrites a good session with a logged-out one. | `guard.atomic_save_state(final_url=page.url)` refuses to persist a non-valid session. | **P1** |
| **I19** | All session/token files are **0644 (world-readable)** in 0755 dirs (verified live). | `guard` writes 0600; `guard.harden_perms()` one-shot for existing files. | **P1** |
| **I20** | Unbounded local session lifetime — a file works until the *server* expires it (can be long). | Local max-age; force re-capture after N days. | **P2** |
| **I21** | Two dashboard instances / two OS users collide on fixed paths, ports (5488/5477), and control files. | Namespace state + ports per OS user/instance; single-instance pidfile. | **P2** |
| **I22** | Control-file signaling (`SAVE_/RELOAD_<svc>`) is unauthenticated and racy — a stray/leftover marker can force a save at the wrong moment. | Nonce in the marker tied to the live login proc; only honor if `_LOGIN_PROCS[svc]` is alive. | **P1** |
| **I23** | Aura bootstrap keeps a **second plaintext copy** of the SF session cookie (`http_scraper.py:359-366`), no chmod. | 0600; treat as the secret it is (folds into I19). | **P1** |

### C. Concentrated / unscoped authority (F4)

| ID | Finding | Fix | Sev |
|---|---|---|---|
| **I5** | One `w3id` + federated SSO = single point of total failure; a blocked password shows six separate "expired" errors. | Detect the shared root once → one "W3ID blocked, all IBM services will fail" message. | **P1** |
| **I6** | Intercepted Salesloft JWT carries the app's full scopes (`emails:create`, `system:all`); expiry mid-batch → 401s; interception is fragile. | First-class Salesloft **OAuth app**, least-privilege scopes, read-only vs send split. | **P1** |
| **I24** | `w3id_seed` loads a full `storage_state` into each service's browser and re-saves — copying the **master `login.w3.ibm.com` SSO cookies into every service file** (`cid_login.py`, `gtm_login.py`, `w3id_login_chrome.py:178`). One file = all-IBM bearer. | Seed only the target-domain cookie; strip foreign-domain cookies before persisting. | **P1** |
| **I30** | The captured session / intercepted token grant far more than the "review" steps need; no read-only mode. | Least-privilege capture/token for enumeration, write-capable only at the gated export. | **P2** |
| **I31** | ZoomInfo **credit spend** is authorization-to-spend real money; a bug that reveals paid fields spends org credits under the seller's entitlement. | Hard guard any reveal path; treat credit spend as a gated write; set the (currently guessed) threshold deliberately. | **P2** |

### D. Ambient authority — password fill & auto-login (F5)

| ID | Finding | Fix | Sev |
|---|---|---|---|
| **I7** | `login_capture._looks_like_login` matches loose substrings (`w3id`,`okta`,`sso`,`signin`) anywhere in the URL, and auto-fill types the password on any page matching its selectors. | `guard.login_origin_allowed` — fill only on an exact scheme+host allowlist. | **P1 (security)** |
| **I8** | `_maybe_auto_login` opens visible browser windows autonomously (only the ISC `scraping` flag guards it) → windows pop mid-run. | Gate behind the real "automation in progress" lock (I4); opt-in. | **P1** |
| **I28** | `PLAYWRIGHT_BROWSERS_PATH` is honored from env with a default; a poisoned path / rogue browser on PATH runs with the seller's session. | Pin the browsers path; don't honor an untrusted override. | **P2** |
| **I29** | Password fill can occur inside a cross-origin iframe or an open-redirect landing page. | `guard.login_origin_allowed` asserts the top-frame origin; never fill in cross-origin frames. | **P1 (security)** |
| **I34** | Auto-login can fire repeatedly across services, each an MFA push → MFA fatigue / blind approval. | Rate-limit + circuit-break auto-login; never >1 MFA-triggering login without explicit user action. | **P1** |
| **I61** | The CDP **virtual authenticator** (`w3id_login_chrome.py:142-155`, `automaticPresenceSimulation:True`) is installed context-wide and left armed through password entry + session save → a "set up a passkey" auto-nudge could register a phantom passkey absorbed by the ephemeral authenticator. | Install only for the specific `get()`-blocking step; `removeVirtualAuthenticator` immediately after. | **P1** |

### E. Confused deputy — the local HTTP surface trusts any caller (F5)

> The highest-severity cluster: a web page the seller visits, or any local process, can
> drive/read authenticated sessions.

| ID | Finding | Fix | Sev |
|---|---|---|---|
| **I46** | Dashboard has **zero local-user auth** (`Flask(__name__)`, no session/token/`before_request`). Any local process/tab = full control. | Per-launch secret token checked in `before_request`. | **P0 (security)** |
| **I47** | **No CSRF/Origin/Referer check** on bodyless mutating POSTs (`/api/step1/launch`, `/api/pipeline/run_all`, `/api/get_my_accounts/run`, `/api/bobby/send`, `/api/login/<svc>/start|confirm`, …) → cross-site drive-by. (JSON-body routes get *accidental* preflight protection only.) | Origin allowlist + CSRF token in `before_request`; reject non-`application/json`. | **P0 (security)** |
| **I48** | **No Host-header check** → DNS-rebinding makes the identity/state GETs (`/api/seller` = IBM email, `/api/state`, `/api/status`, `/api/credentials/status`) cross-origin-readable. | Validate `Host ∈ {127.0.0.1:<port>, localhost}`. | **P1 (security)** |
| **I49** | `/api/login/<svc>/confirm` (`:1009`) just `touch`es `SAVE_<svc>` with no check that a login proc is running → a CSRF POST force-saves the current session. | Honor only when `_LOGIN_PROCS[svc]` is alive + CSRF (I47). | **P1 (security)** |
| **I36** | Meetings backend: **wildcard CORS** (`main.py:20-26`, `allow_origins=["*"]`) on a session-bearing API + **zero endpoint auth** → any origin invokes *and reads* `/api/state` (live transcript, notes, attendee PII), `/api/meetings`, etc. | Exact-origin allowlist + per-launch token; never `*` on a session-bearing backend. | **P0 (security)** |
| **I37** | Meetings **WebSocket `/ws`** (`main.py:309-320`) `accept()`s with no auth/Origin → any page the seller has open eavesdrops the live call in real time. | Verify Origin + require a handshake token before `accept()`. | **P0 (security)** |
| **I38** | `/api/transcription/teams/selftest` (unauth) takes `payload["join_url"]` and drives the seller's authenticated Teams identity to **join an attacker-supplied meeting** (`TEAMS_AUTO_JOIN` default true). | Auth-gate + constrain to the seller's own calendar join_urls. | **P0 (security)** |
| **I39** | Cross-origin-reachable `/api/followup/send` (sends mail via the seller's Outlook when armed) and `/api/reminders/config` (persistent config change). | Same as I36 + per-send confirmation token. | **P1 (security)** |
| **I50** | Send/write gates are coarse **process-wide env flags** (`BOBBY_ENABLE_SEND`, `PIPELINE_ENABLE_UPDATE`, `MEETING_FOLLOWUP_SEND`) read inside child subprocesses; the HTTP handlers never re-check them. A stray `export …=1` makes every CSRF POST live-fire. | Per-request confirmation token at the endpoint, not just an env read downstream. | **P1** |
| **I51** | The most dangerous write endpoints skip the allowlist validation the others do: `/api/step4/run` (`:945`) accepts unvalidated `mode`/`date`/`accounts`; step5 manual accepts an arbitrary cadence. | Validate `mode∈{auto,manual}`, ISO date, cadence/accounts allowlists before building argv. | **P1** |
| **I52** | Free-port TOCTOU + `s2.bind(("",0))` (all interfaces, momentary) + unconditional `webbrowser.open` (`:4485-4492`; same in the Meetings + ISC launchers). | Bind loopback first and hand the live socket to the server; probe on 127.0.0.1. | **P2** |
| **I53** | ISC launcher `/run` + `/progress` (`launcher.py:872`,`830`) are unauthenticated local action-triggers — any local caller scrapes the seller's territory. | Per-session token or a Unix socket. | **P1 (security)** |

### F. Duplicated / substring truth that drifts (F6)

| ID | Finding | Fix | Sev |
|---|---|---|---|
| **I10** | `_LOGIN_BOUNCE_MARKERS`/login checks duplicated across ~10 modules → they diverge when IBM adds an SSO host (some fail fast, some mis-read a login page as valid). | `guard.is_login_url` / `guard.session_verdict`, imported everywhere. | **P1** |
| **I11** | Steps resolve auth paths via `os.environ.get("*_AUTH_STATE_PATH", default)` independently of `shared_auth.state_path` → dashboard verifies file A while the step loads file B. | One resolver honoring the same override on both sides. | **P1** |
| **I26** | The substring "looks like login" test also **false-positives**: an app URL containing `authorize`/`sso` in a path/query is mis-read as a bounce → needless re-auth loops. | `guard.is_valid_app_url` (host + not-login), not substring-in-full-URL. | **P2** |
| **I59** | Validity judged by URL host/substring, not authorized *content*: a `cid.ibm.com` error/denied page (still on-domain) is **saved as a valid session** and reused (`cid_login.py:33-34,85-87`; GTM/ISC-install similar). | Gate validity on an authenticated-only DOM anchor or a 200 from an authorized API call. | **P1** |
| **I60** | "0 rows" conflated with "not authorized / expired": `http_scraper` treats `numberOfAccounts==0` as legitimately empty, `sub_cloud` returns `[]` on a non-list Dash response → an unauthorized/expired session looks like a complete empty export. | Assert an authorized sentinel before trusting any 0. | **P1** |

### G. Identity ≠ entitlement (F7)

| ID | Finding | Fix | Sev |
|---|---|---|---|
| **I12** | email→CovID is a static `Name Match.xlsx`; stale rep assignments grant/deny the wrong territories. | Freshness stamp + reconcile against ISC's live territory data on login. | **P2** |
| **I13** | Entitlement failures (renamed buyer group "Infra Outbound", moved cadence, exhausted credits) masquerade as "session expired". | Split *authentication* (bounced to login) from *entitlement* (logged in, thing not available) with distinct messages. | **P2** |
| **I23-id** | No binding between the captured session's authenticated identity and the signed-in seller (Keychain email / Name-Match). | Read each app's `/me` after capture; assert it matches; refuse on mismatch. | **P1** |
| **I62** | `sub_isc_install` uses `IBM_TERRITORY_USER` even when absent from the dataset, else fuzzy-matches `displayName` with `difflib` cutoff 0.6 → can scrape **another seller's install base** and look successful. | Exact, identity-verified territory-user match; fail closed on ambiguity. | **P1** |

### H. Secret rotation / deprecation (F8)

| ID | Finding | Fix | Sev |
|---|---|---|---|
| **I14** | The entire auto-fill `password-blocked` → "Click here (4h)" → back → other-methods dance depends on IBM's password-bypass link existing; mandatory passkeys break all six at once. | Make auto-fill strictly best-effort (degrade to "human completes login, we just save the session"); migrate API-capable services off interactive login. | **P2** |
| **I15** | A stale saved password is auto-submitted repeatedly across six services → risk of account lockout. | Circuit-breaker after N failed auto-fills → "update your saved W3ID password". | **P1** |
| **I27** | Expiry decisions use local wall-clock / fixed TZ (contexts pinned America/Los_Angeles; ~1h JWTs). | Use server-provided expiry / validate by use, not clock arithmetic. | **P2** |

### I. Leakage & no attribution (F9)

| ID | Finding | Fix | Sev |
|---|---|---|---|
| **I16** | No local audit of session/credential use — replay is indistinguishable from the human, and you can't answer "did the automation do this?". | `guard.audit` append-only, secret-free log. | **P2** |
| **I40** | Intercepted JWTs cached **cleartext in the repo tree** (`browser_profile/{outlook,salesloft}_token.json`, 0644) — in `~/Downloads` (Time Machine/iCloud-eligible). | In-memory only, or Keychain; if cached, 0600 + short TTL + outside the repo. | **P1** |
| **I41** | `live_transcribe_bot/.env` (0644) holds live `ANTHROPIC_API_KEY=sk-ant-…` + `DEEPGRAM_API_KEY` in cleartext, guarded only by a nested `.gitignore`. | Keychain / root-ignored secrets file; 0600. | **P1** |
| **I42** | Debug DOM dumps (`teams_transcription.py:393` `page.content()`, plus `debug_outlook.html` etc., 0644) capture full authenticated OWA/Salesloft/Teams DOM incl. inline tokens + PII. | Gate behind a debug flag, 0600, scrub, delete after. | **P1** |
| **I43** | The OWA token cache trusts an attacker-influenceable `host` (`outlook_api.py:114,138-140`) → a local writer can redirect the live bearer to an attacker host. | Pin `host` to an OWA allowlist; re-derive `exp` from the JWT. | **P1** |
| **I45** | Prospect/company identity auto-egresses to Anthropic web_search + Google News RSS on dashboard-open prefetch, no gate. | Make external research opt-in; document the egress. | **P2** |
| **I64** | `login_capture.py:668` writes the raw `page.url` (mid-bounce OIDC/SAML URLs with `code`/`state`/`SAMLResponse`) to `login_status_<svc>.json` every ~2s, then shown in the UI. | `guard.redact_url` — persist host only for login URLs. | **P1** |
| **I65** | Session-expired errors interpolate the **full** `page.url` (`zoominfo_import.py:74`, `salesloft_api.py:64`, `sub_storage.py:204`, `sub_cloud.py:156`); `run_pipeline` surfaces it to the UI `log_tail` + log files (confirmed materialized in `IBM_Scraper_App/logs/run_20260715_083935.log`). | `guard.redact_url` in every error string. | **P1** |
| **I66** | `IBM_Scraper_App/_login_debug/*.png` (screenshots of the W3ID login flow with the seller's email in the form) are **git-tracked**; `_login_debug/` is in no `.gitignore`. | Gitignore + `git rm --cached` + gate `shot()` behind a debug flag; consider history purge. | **P1** |
| **I67** | Atomic writers leave world-readable `<file>.tmp<pid>` secret copies on crash, never swept (a live `meetings_cache.json.tmp61936` on disk now); same for `aura_bootstrap.json.tmp<pid>`. | `mkstemp(mode=0o600)` + sweep stale `*.tmp*` on startup. | **P1** |

### J. Unsafe / illegible failure & no revocation (F10)

| ID | Finding | Fix | Sev |
|---|---|---|---|
| **I17** | `TEST_MODE=true` bypasses auth → a green run can mean "no live session at all". | Badge every result LIVE vs TEST_MODE. | **P1** |
| **I32** | No revocation / offboarding path — on device loss / seller change, the files + Keychain live on. | `guard.wipe_all(include_credential=…)` — sign out everywhere. | **P2** |
| **I33** | No single auth-health view: cid/gtmnav are hidden from the Details panel (`run_pipeline.py:90-91`) and the intercepted-token surfaces aren't shown — a CID/GTM/Meetings auth failure is invisible until a scrape fails. | One health view across all surfaces. | **P2** |
| **I35** | Output `.xlsx/.json` embed identity-linked contact data at rest, unencrypted (gitignored, but backed up). | Same at-rest posture as sessions; persist the minimum. | **P2** |
| **I44** | Meetings follow-up reply-all falls back to the **first calendar event** when the subject match misses (`followup.py:191-198`) → an armed send leaks one prospect's call summary to a different meeting's attendees. | Abort unless the subject-matched event is positively identified; confirm recipients. | **P1** |
| **I57** | Bootstrap is fully regenerated on **every** `/run` when list-creation selectors drift (`launcher.py:710-714`) — no backoff/cap, a valid token thrown away forever. | Cache the "list-creation failed" outcome; don't gate token reuse on a separately-failing side effect. | **P1** |
| **I55** | Launcher concurrency guards are `threading`-only; a second launcher process (readily created by I54) re-opens the torn-bootstrap / duplicate-list-id races the code claims to fix. | Cross-process `flock`/pidfile around bootstrap + list-ID reservation. | **P1** |
| **I54** | ISC port-fallback confused-deputy: if `:5477` is taken, `_ISC_PORT` still becomes 5477 and the dashboard POSTs the seller's CovIDs to whatever squats there (`run_pipeline.py:650-660`). | Read the child's actually-bound port; refuse to POST if unknown. | **P1 (security)** |
| **I63** | `ISC_NO_BROWSER=1`/headless can silently flip into a **headful/interactive** login (`bootstrap_aura` 300 s `wait_for_url`; `isc_scraper.py` `input()` prompts) → hangs or `EOFError` on DEVNULL stdin. | In headless mode, fail fast with "re-login required," never fall back to interactive. | **P1** |

---

## 4. Landed vs remaining (2026-07-15)

### LANDED & verified

**Central library** `shared_auth/guard.py` (unit-tested 10/10 — `tests/test_guard.py`):
`is_login_url`/`is_valid_app_url`/`session_verdict`, `login_origin_allowed`,
`atomic_save_state`, `session_lock`/`is_locked_exclusive`, `redact_url`, `harden_perms`,
`audit`, `wipe_all`.

**Dashboard (`run_pipeline.py`, tested — `tests/test_run_pipeline_auth.py` 15/15 + live curl):**

- **I1** JIT probe gate — `_ensure_services_ready` probes live before Fill Contacts / Get My Accounts (the screenshot fix).
- **I46/I47/I48/I49** `before_request` Host + Origin/Referer guard + per-launch token: DNS-rebinding → 403, cross-origin POST → 403, same-origin UI → 200, token path → 200 (all verified live). No UI change needed.
- **I8/I15/I34** self-healing watchdog: `_maybe_auto_login` is automation-aware, lock-aware, and circuit-broken after `_MAX_AUTO_LOGIN_FAILS`; `/api/auth/health` exposes it.
- **I54/I53** ISC launcher: reads the real bound port from a pid-matched handshake (verified: bound 64195 when 5477 was squatted) + shares a token.
- **I65** `_last_step_error` redacts URLs before the UI/logs see them.

**Session layer (`login_capture.py`, `zoominfo_import.py`, `salesloft_advance.py` — WP-B, smoke-tested):**

- **I7/I29** origin-allowlist password fill · **I18/I19** atomic 0600 save that refuses a bounced session · **I64/I65** redacted status/error URLs · **I15** autofill circuit-breaker.

**Meetings backend (`live_transcribe_bot/backend/` — WP-C, live-tested via uvicorn):**

- **I36** restrictive CORS + `local_auth` token + Host check · **I37** WS Origin/token gate · **I38** Teams-join URL allowlist · **I40/I42/I43** token caches 0600, debug dumps opt-in+0600, OWA host pinned. (**I39/I44** now behind auth; I44 fail-closed target-meeting resolution in progress.)

**ISC/IBM (`ISC_Scraper_App/`, `IBM_Scraper_App/` — WP-D, smoke-tested):**

- **I18/I19** no-save-on-bounce + 0600 · **I57** bounded bootstrap regen · **I59/I60** content-based validity + auth signal · **I61** virtual-authenticator scoped/removed before password entry · **I62** exact territory match (fail-closed) · **I63** headless never flips to interactive.

**Leakage / at-rest (`secure_auth_files.py` ran, `.gitignore`, git):**

- **I19/I23/I40/I41/I42/I67** 27 secret files → 0600, dirs → 0700 · **I66** 66 login screenshots untracked + gitignored.

### REMAINING (documented; mitigated, gated, or structural)

- **I3** mid-run session-death resume — *mitigated* (JIT probe shrinks the window; on failure the watchdog self-heals in the background and the re-run succeeds). Full pause→resume not implemented.
- **I11** unify the env-override path with `shared_auth.state_path` — only bites under a deliberate non-default `*_AUTH_STATE_PATH`; defaults already agree.
- **I5** single "W3ID blocked → all IBM services" message · **I23** identity binding (assert `/me` == Keychain email) · **I33** surface cid/gtm health.
- **Structural (P2):** **I6** Salesloft OAuth · **I14** passkey-graceful fallback · **I12/I13** entitlement reconciliation · **I20** session TTL · **I28** pin browser path · **I30/I31** least-privilege / credit-spend gate · **I35** output at-rest.
- **MFA note:** self-healing re-login drives the SSO auto-fill but a human still taps MFA — that is irreducible for MFA-gated SSO; the watchdog does everything up to that tap and the breaker stops it from nagging.

---

## 5. How to verify

Run the auth test suite from the repo root:

```
.venv/bin/python -m pytest tests/ -q
```

This covers `tests/test_guard.py` (guard invariants, 10/10) and
`tests/test_run_pipeline_auth.py` (dashboard `before_request` guard + JIT probe, 15/15),
plus the session-layer, Meetings, and ISC/IBM work-package tests. The
`before_request`/CORS/WS gates were additionally confirmed with live `curl` / `uvicorn`
runs (DNS-rebinding → 403, cross-origin POST → 403, token path → 200).

---

## 6. The one sentence

Every issue here is the same mistake in a different costume: **the system trusts a cheap
proxy for "am I / is this caller authorized?" — a file exists, a badge is green, a URL
contains a substring, a spreadsheet says so, the request reached localhost — when the only
real answer is to try the actual capability against the actual server, at the moment of
use, under a lock, over a 0600 file, with an authenticated caller and the narrowest secret
that will do the job.**
