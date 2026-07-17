# PRD — BobBee: AI Account Intelligence for IBM Sellers

Status: **watsonx.ai integration live and verified** · Owner: Sydney Chin ·
Submission targets (IBMer watsonx Challenge): 3-min demo video, 599-word problem
statement, 500-word technical statement. Judging weights **productivity impact** and
**effective use of watsonx** most heavily — this document is built around both.

> Change from the previous PRD: the AI layer is no longer a plan — it is implemented
> against a real watsonx.ai project (Granite `ibm/granite-4-h-small`, IAM + `/ml/v1/text/chat`)
> and confirmed end-to-end (`"source": "watsonx"` in live responses). The old
> Anthropic/Claude backend is gone. The product also moved from a linear 3-button
> pipeline to an **account-intelligence workspace** (Accounts → cadences → a daily
> plan), described below.

---

## 1. Problem statement (source for the 599-word field)

A B2B infrastructure seller's outbound motion is stitched together from disconnected
systems: a Salesforce-based territory tool for which accounts are theirs, an internal
install-base portal for what those accounts already own, ZoomInfo for company/contact
enrichment, and Salesloft for running outreach cadences — plus whatever news the rep
happens to catch. To turn a raw territory into a week of good outbound, a seller has to
pull every account, cross-reference install data by hand, figure out which accounts
even have a reachable IT decision-maker, judge which are worth the effort and why,
group them into sensible campaigns, decide an order, and then spread all of that across
the calendar so each day has a realistic call-and-email list. None of these systems
talk to each other, so the seller either burns hours a week doing it manually or skips
it and defaults to the same few top-of-mind accounts — which means under-covered
territory and generic outreach.

BobBee automates that whole chain into one action. A seller imports their accounts and
clicks **Sort into cadences**; BobBee removes accounts with no IT decision-maker,
scores the rest on private signals (IBM spend, IT spend, revenue, install footprint,
headcount) and public signals (industry trends, news), portions them across the
quarters, groups the current quarter into ranked Salesloft cadences, and distributes
the work across the calendar — producing a day-by-day plan of exactly who to email and
call. The seller's Dashboard then shows only *today*; the Plan tab shows the whole
quarter; the Call tab hands them an AI pre-call brief for each conversation.

The judgment layer is where a foundation model earns its place. **watsonx.ai (Granite)**
names the sales **play** for each account and writes its one-line **"why call now"
angle** during scoring, and — on demand — writes each account's **pre-call brief** as
tight bullets synthesized from Sales Cloud, ZoomInfo, Salesloft, and recent news. Every
number that must be trustworthy (tiers, scores, cadence membership, rank, the schedule)
stays deterministic; watsonx only supplies the human-readable judgment on top, always
grounded in the structured context the pipeline already assembled. That grounding is
what makes the output usable without heavy editing rather than a generic mail-merge —
and it collapses a multi-hour, multi-tool weekly ritual into a run a seller can do
before their first call block.

*(~330 words — trim/expand to fit 599 with intro/close framing.)*

---

## 2. Solution overview

A single local Flask web app (`run_pipeline.py`) presenting an account-intelligence
workspace: **Dashboard · Plan · Accounts · Cadences · Email · Call**. Every external
system (IBM Sales Cloud/ISC, IBM install base, ZoomInfo, Salesloft, news signals) is
**mocked with deterministic fake data** (`fake_data.py`) so it demos anywhere with no
VPN, logins, or customer data. The **one live integration is IBM watsonx.ai**, against
a real project, fail-soft.

**Design principle — the deterministic/AI split:** watsonx supplies judgment and
narrative; deterministic Python owns every number and decision that must be
reproducible and auditable. The model never changes a tier, score, cadence, rank, or
date. The UI encodes this: **blue = deterministic**, **purple + ✦ = watsonx-generated**.

---

## 3. Target user & personas

- **Primary: IBM infrastructure seller (BTSS/TSS / Client Executive).** Owns a
  territory, judged on coverage and activity, currently does this planning by hand or
  skips it. (The demo persona is "Tim," a Client Executive.)
- **Secondary (challenge judge): IBM technical/sales leadership** evaluating whether
  watsonx can be embedded in a real internal workflow — not a bolted-on chatbot.

---

## 4. Functional scope (what's built)

| Area | Capability |
|---|---|
| **Accounts** | Import (mock CSV/territory pull); **Sort into cadences** (the intelligence pipeline); searchable all-accounts list; tag filters; sidebar lists (All, per-cadence, Leftovers, No contacts, Future quarters); per-account detail popup spanning Sales Cloud + ZoomInfo + Salesloft + news + ✦ AI analysis. |
| **Intelligence pipeline** | Contact-DM filter → score + quarter split → ranked cadences → cap top-8/cadence (overflow → Leftovers) → distribute across the quarter. Outputs JSON in `Account_Intelligence/output/`. |
| **Plan** | Quarter/Month/Week/Day calendar; per-day activity load; click a day → right-side panel grouped **Emails** then **Calls**. |
| **Dashboard** | Today only: emails/calls/accounts-touched + activity list; week totals; cadence snapshot (active/pending/completed); notable news for the week's accounts. |
| **Cadences** | Cadence definitions (steps), rosters, per-account progress vs. today. |
| **Email** | Today's scheduled emails; draft-all + edit/redraft/send; **Send all gated until drafted**. Drafts are deterministic templates grounded in account data. |
| **Call** | Today's calls; contacts + click-to-call; **✦ watsonx pre-call briefs** (bulleted), fail-soft to deterministic bullets. |
| **Profile** | Identity, personalization, access/sessions (mock). |
| **Infra** | Fixed port 3000 (`BOBBEE_PORT` override, clear error if busy); live-reload that preserves data; sign-in with any email; every tab gated on "import accounts first." |

---

## 5. Where watsonx is used, and its limits

**Two call sites in the main flow** (`llm_advisor.py`):

1. **Account Play + Sales Angle** — `advise_accounts()`, one **batched** call during the
   scoring stage, **capped at 120 accounts/run**. Names each account's sales play and
   writes its "why call now" angle. The play then drives cadence assignment; the angle
   surfaces in the account detail and feeds briefs.
2. **Pre-call briefs** — `advise_call_brief()`, **one call per account, on demand**
   (Call tab → *Generate all briefings*). Synthesizes Sales Cloud + ZoomInfo +
   Salesloft + news into 4–6 bullets.

Everything else — segmentation, tier numbers/scores, the DM check, quarter split,
cadence membership, ranking, the schedule, email drafts, KPIs — is deterministic.

**Limits (the answer to "how much AI is there?"):**
- *By design:* AI is confined to those two narrative touchpoints; it is not invoked per
  row/click/page. The Play/Angle call is one batched request (≤120 accounts); briefs are
  one-per-account and only on click.
- *By plan quota:* Granite inference bills tokens as Resource Units. The free **Lite**
  plan caps monthly usage (~300k tokens, ~20 CUH) — fine for demos/light use, not
  unlimited. Over quota or rate-limited (429) → calls fail and the app **fail-softs to
  deterministic**; a within-run retry-with-backoff absorbs transient 429s. Paid plan
  raises the ceiling with no code change.

**Reliability property:** because tiers/scores/schedule never depend on the model, the
app is reproducible and never breaks when AI is unavailable — it just shows
deterministic text instead of Granite text.

---

## 6. Architecture (technical)

- **`run_pipeline.py`** — Flask app: routes, the `_run_strategize` orchestrator, all
  `/api/*` endpoints (`accounts/list`, `accounts/detail`, `call_brief`, `schedule`,
  `dashboard`, `cadences`, `strategize/run`, set-aside lists). Loads `.env` via
  python-dotenv; fixed port + Werkzeug live-reload (reset-on-first-launch only, so
  reloads preserve data).
- **`llm_advisor.py`** — watsonx.ai REST client: IBM Cloud IAM token exchange →
  `POST /ml/v1/text/chat`, standard-library `urllib` only (no SDK), token caching,
  retry with exponential backoff + jitter, per-call telemetry (model/latency/tokens/
  status), and JSON-array extraction for the brief/play outputs.
- **`ui_templates.py`** — all HTML/CSS/JS as `render_template_string` templates; one
  dark IBM-Carbon design system.
- **`fake_data.py`** — seeded deterministic data engine; stable per-account identity
  across every step so the exact-match joins actually attach.
- **`mock_salesloft.py`**, **`mock_ui_templates.py`** — the mock Salesloft store and the
  in-app mock tool windows.
- **`Account_Tiering/`** — deterministic scoring subprocess that also invokes the
  watsonx Play/Angle enrichment.
- **`Account_Intelligence/output/`** — `latest.json` (cadences), `schedule.json`,
  `no_contacts.json`, `leftovers.json`, `other_quarters.json`.

Every mocked integration keeps the real integration's function signature (see the
`MOCK` docstrings), so the mocks are swap points for real ISC/ZoomInfo/Salesloft
connectors.

---

## 7. Goals & success metrics

| Goal | Metric | Target |
|---|---|---|
| Collapse the manual planning cycle | Time from raw accounts → full ranked, cadenced, scheduled quarter plan | One click, ~seconds on screen |
| watsonx output is usable, not generic | Briefs/angles that cite real account specifics (spend, install, contact, news) | 100% cite at least one real signal |
| Prove it's really watsonx | Live call visible (`source: watsonx`, model/latency/tokens) | Shown on screen, not narrated |
| Reproducible where it counts | Tiers/scores/schedule identical run-to-run | Deterministic by construction |

---

## 8. Demo video plan (target 3:00)

1. **The pain (0:00–0:25)** — montage of the disconnected systems (Sales Cloud,
   install base, ZoomInfo, Salesloft, news). VO: hours of manual stitching before a
   single dial.
2. **Import + Sort into cadences (0:25–1:00)** — Accounts tab: import, then *Sort into
   cadences*; show the 4-stage progress (contacts filter → scoring → cadences →
   distribute). Land on the ranked, tagged account list + sidebar lists.
3. **The watsonx moment (1:00–1:50)** *(most important)* — open an account popup; call
   out the ✦ **Play + Angle** ("that reasoning is watsonx, not a template"). Then the
   Call tab → *Generate all briefings* → the bulleted **pre-call brief**; show
   `source: watsonx` / the activity panel to make the live call undeniable.
4. **The payoff (1:50–2:30)** — Plan calendar: switch Quarter→Month→Day; click a day →
   the grouped Emails/Calls panel. Dashboard: "today only," week totals, cadence
   snapshot, notable news. VO: one click turned a territory into a day-by-day plan.
5. **Close (2:30–3:00)** — deterministic/AI split as the punchline: "every number is
   auditable Python; watsonx does the judgment." End card: *Built with IBM watsonx.ai
   (Granite)*.

Production notes: speed up any waits in the edit; caption throughout (judges may watch
muted); record the brief-generation take 2–3× for a clean live call.

---

## 9. Technical statement outline (source for the 500-word field)

1. **What it is** (~60w): a Flask account-intelligence workspace that turns a raw
   territory into a ranked, cadenced, day-by-day outbound plan; watsonx.ai in the
   judgment layer.
2. **The pipeline** (~120w): DM-contact filter → deterministic scoring + quarter split →
   ranked cadences (top-8, overflow to Leftovers) → quarter-wide schedule; outputs as
   JSON that the Plan/Email/Call/Dashboard read.
3. **Where watsonx sits** (~140w): two call sites — Play/Angle (batched, ≤120 accounts)
   and pre-call briefs (per-account, on demand) — Granite via IAM + `/ml/v1/text/chat`,
   prompts grounded in structured multi-source context, JSON-contract outputs, retry +
   fail-soft.
4. **Why the split matters** (~120w): tiers/scores/schedule are deterministic and
   auditable; the model never controls a business number, only the human-facing
   narrative — a pattern that generalizes to other IBM seller tooling; bounded AI
   footprint + plan-quota-aware fail-soft.
5. **What's mocked & next** (~60w): external systems deterministically faked for a
   portable demo behind real-shaped interfaces; next is real connectors + a paid
   watsonx plan to lift the quota.

---

## 10. Risks & mitigations

| Risk | Mitigation |
|---|---|
| watsonx quota exhausted mid-demo (Lite plan) | Fail-soft keeps the app working; pre-generate briefs before filming; consider a paid plan for the recording. |
| Transient 429 rate limiting | In-run retry with backoff + jitter already absorbs it. |
| Granite output quality varies | Prompts constrained to JSON + grounded context; deterministic fallback is always present. |
| Judge can't tell the AI is real | `source: watsonx` in responses + the activity panel; call it out on screen. |
| Reviewer expects live web search in briefs | Be explicit: BobBee is offline; "news" is the mock signal feed (a stand-in for a real news/intent integration); Granite synthesizes it, it does not browse. |

---

## 11. Open questions (verify against the challenge portal)

- Exact judging rubric / weighting; team-size eligibility.
- Whether a public repo link is required, or video + statements are the whole submission.
- Which watsonx.ai region/plan is available to participants (affects `WATSONX_URL`,
  model availability, and the token quota above).
