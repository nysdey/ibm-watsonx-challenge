# BobBee — Executive Design Review & Redesign Strategy

**Prepared as a pre-launch design review for IBM leadership.**
Reviewer stance: Principal Product Designer. Brutally honest, grounded in the
*actual* shipping build (tokens, layout, and AI wiring as they exist in
`ui_templates.py` / `run_pipeline.py`), not a generic critique.

> **The one-sentence verdict.** BobBee is a *competent, Carbon-compliant
> enterprise dashboard with a chatbot attached* — which is precisely the thing
> your brief says it must **not** be. It is well-built and coherent. It is not
> yet an AI-native sales operating system. The gap is closable, and this
> document is the map.

---

## SECTION 1 — Executive Design Assessment

Scores are measured against your stated benchmark set (Linear, Vercel, Stripe,
Ramp, Notion, watsonx, Copilot, Einstein). Not against "typical IBM internal
tools" — against that bar BobBee would score ~8. Against *world-class 2026
SaaS*, here is the honest read:

| Dimension | Score | One-line reasoning |
|---|---|---|
| **Visual design** | 6.0 | Disciplined color system, real craft in places, but heavy 1px borders + card-on-card nesting + universal sharp corners read "enterprise 2018," not "premium 2026." |
| **Product maturity** | 6.0 | Deep functionality, but it feels like *assembled panels* rather than one designed system with a spine. |
| **Modernity** | 5.0 | Gradients-on-everything and boxed density fight the modernity Carbon otherwise gives you. |
| **Enterprise readiness** | 7.5 | Genuinely strong. Carbon compliance, dark/light, density tolerance, real data. This is your best axis. |
| **AI integration** | 4.0 | **The critical weakness.** A floating chatbot FAB + purple "sparkle" labels is *AI adjacency*, not AI-native. |
| **Information hierarchy** | 5.0 | The dashboard opens on an activity chart and stat tiles. "What do I do next" is present but not *dominant*. |
| **Usability** | 6.5 | Learnable, consistent nav, good affordances. Slowed by density and small type. |
| **Accessibility** | 5.5 | Carbon helps, but `--text3` on layer1, gradient-filled numerals (now fixed), and the many 11–12px labels you kept asking to enlarge are red flags. |
| **Data visualization** | 5.0 | Hand-rolled bars are fine; the choropleth is a science project; gradient fills reduce readability. |
| **Competitive differentiation** | 3.5 | **It looks like "an IBM Carbon app."** No distinctive product POV. A VP cannot tell it apart from six other internal tools at a glance. |

### Overall: **5.4 / 10**

**What that number means.** This is not a failing product — it's a *B-minus
enterprise tool being asked to be an A-plus flagship*. The 5.4 is dragged down by
two things that also happen to be the two things your brief cares most about: **AI
integration (4.0)** and **competitive differentiation (3.5)**. Fix those two and
the overall jumps to ~7.5 without touching anything else.

**The single most important sentence in this review:** *BobBee currently
optimizes for "show the seller everything," when the entire thesis of the product
is "tell the seller the one thing to do next." The information architecture is
inverted relative to the mission.*

---

## SECTION 2 — Screen-by-Screen Critique

### 2.1 — Dashboard

**What works**
- The "Today: Emails left / Calls right" split with progress meters and action
  buttons is a genuinely good instinct — it *is* action-oriented, and the
  meter→button pairing is the strongest AI-native-adjacent moment in the app.
- The blue = deterministic / purple = AI color convention is legitimately smart
  and rare. Keep it. It's a differentiator hiding in plain sight.
- Server-authoritative "today" and weekday-only logic show real product rigor.

**What doesn't work**
- **The page opens with equal visual weight across four competing regions**
  (Today tasks, Activity chart, Meetings & opportunities, Book of business). Four
  panels of similar size = no hierarchy = the seller's eye has nowhere to land.
  Your brief says *action before analytics*; the dashboard is ~60% analytics by
  area.
- **"Draft and send emails →" and "Start calling →" are neutral gray buttons.**
  These are the two most important actions in the entire product and they're
  styled like a tertiary "cancel." The primary daily verbs should be the most
  visually dominant controls on the screen.
- **No prioritization.** 21 emails and 12 calls are shown as flat lists in
  schedule order. Nowhere does the product say *"Start with these three — highest
  intent, closing this quarter."* That's the whole promise of an AI sales OS and
  it's absent.

**Biggest missed opportunity**
The dashboard should be a **plan of attack**, not a **status board**. Right now
it reports the day. It should *direct* the day: "Here are your 3 highest-leverage
moves this morning, here's why, do them in this order, I've pre-drafted them."

**Visual weaknesses**
- Every panel is a bordered box on a bordered box. Count the 1px `--border`
  lines on this screen — it's 15+. Premium products use **space and elevation**
  to separate regions, not hairlines. Notion/Linear/Vercel are nearly
  borderless.
- The activity chart's gradient bars + gradient ring + gradient panel edge =
  three gradients competing. Restraint reads as premium; gradient-everywhere
  reads as 2019 fintech.

**UX weaknesses**
- The Meetings & opportunities and Book-of-business panels are *reporting*.
  Reporting belongs one level down (an Insights/Analytics surface), not on the
  landing screen.

**AI experience weaknesses**
- There is **no AI on the dashboard**. The purple sparkle appears on buttons, but
  the model never *speaks* here — no recommendation, no "why this account," no
  proactive nudge. For an "AI-native" product this is the cardinal sin.

**IA issues**
- Four peer regions, no spine. See Section 3 for the fix.

**How modern products solve it**
- **Ramp** opens with "here's what needs your attention and the action to take,"
  not charts. **Linear** opens on *your* assigned work, prioritized. **Stripe**
  leads with the one number that matters + the next action. **Copilot** puts a
  generated summary + suggested actions *at the top*, analytics below the fold.

---

### 2.2 — Accounts

**What works**
- The grid table finally aligns (real CSS grid, shared column template). Signals
  moved on-palette. This is solid, honest enterprise table work.
- The sidebar of pre-made lists (per-cadence, Leftovers, No contacts, Future) is
  a good mental model.

**What doesn't work**
- **It's a spreadsheet.** 1,911 rows of account / industry / location / signals.
  Functional, but it's the *least differentiated* screen in the product — it
  could be any CRM from the last decade.
- **Signals are four colored dots with a hover tooltip.** The single richest
  piece of intelligence per account (whitespace, at-risk, growing) is encoded as
  dots you have to hover to decode. That's hiding your best data.
- No AI ranking surfaced in the default view. "Which of these 1,911 matter today"
  is the question; the table answers "here are 1,911 accounts alphabetically-ish."

**Missed opportunity**
- The account row should be an **intelligence object**, not a spreadsheet cell:
  name, a one-line AI "why now," the signal *in words*, the recommended play, and
  a one-click action. See Section 7.

**How modern products solve it**
- **Ramp** and **HubSpot** increasingly render list rows as *rich cards with an
  embedded next-action*. **Linear** turns every list item into a keyboard-driven,
  command-able object.

---

### 2.3 — Email

**What works**
- Draft-all with a real AI/deterministic fallback is genuinely good engineering.
- The kebab menu + contextual side panel (shift, don't cover) is a modern
  pattern, well executed. This is the most 2026-feeling interaction in the app.

**What doesn't work**
- The email cards are **tall and information-sparse** until drafted. A queue of
  "Draft not yet generated" cards is a queue of empty boxes.
- The AI draft appears *inside* the card with no sense of the model's reasoning.
  Modern copilots show *why* they wrote what they wrote ("Referenced their Q3
  cloud migration + your install base").

**AI weakness**
- Drafting is a batch button, not a conversation. The seller can't say "make it
  shorter" or "lead with the security angle" inline. That's the 2026 expectation.

---

### 2.4 — Call

**What works**
- Pre-call briefs, click-to-call, mark-as-called with a persisted progress meter —
  this is a real, usable call console.

**What doesn't work**
- Same density problem: contact blocks + brief bullets + cadence chips all at one
  visual weight.
- The brief is static text. In 2026 it should be a *living* brief you can
  interrogate ("what did we last talk about?", "what's the objection likely to
  be?").

---

### 2.5 — Schedule

**What works**
- Weekday-only, year→quarter→month→week→day drill-down, day panel below the
  header. Competent calendar work.

**What doesn't work**
- A calendar is a *reporting* metaphor. Sellers don't plan their quarter by
  staring at a month grid; they execute today's list. The calendar is over-built
  relative to its value. It should be a secondary view, not a top-level tab.

---

### 2.6 — Profile

**What works**
- The w3-style identity header is on-brand and correct. Good instinct to mirror
  the real IBM directory.
- The territory choropleth is *ambitious* and the discrete-region heat version is
  a real improvement.

**What doesn't work**
- **The choropleth is a science project that doesn't earn its space.** Hand-traced
  approximations of CA/HI/GU/MP with per-city heat is a lot of pixels to tell the
  seller something a 4-row bar chart tells them faster and more accurately.
- Profile mixes *identity*, *territory analytics*, *personalization*, and
  *system settings* — four different jobs in one tab.

---

### 2.7 — The Chatbot (Ask BobBee)

**What works**
- Clean panel, theme-aware logo, honest offline-labeling. The engineering is
  careful.

**What doesn't work — and this is structural**
- **A floating chat bubble in the bottom-right corner is the single most dated,
  most "bolted-on" pattern in the entire product.** It is the 2023 "we added AI"
  move. Every serious 2026 product has *moved away* from the corner bubble. More
  in Section 5.

---

## SECTION 3 — Complete Information Architecture Redesign

### The core problem with today's IA

The current nav — **Schedule · Accounts · Cadences · Email · Call** — is
organized around **objects and channels** (a calendar, a list, email, phone).
That's how the *system* is built. It is not how a seller *thinks*. A seller
thinks in three modes: **"What do I do now?" → "Who do I focus on?" → "How am I
doing?"**

### The redesigned model: three zones, not seven tabs

```
ZONE 1 — EXECUTE (the default, 80% of time here)
   • Today            ← the AI-planned daily run of work
   • Queue            ← unified email + call + task stream, prioritized

ZONE 2 — FOCUS (who & why)
   • Accounts         ← intelligence objects, AI-ranked
   • Cadences         ← the playbooks (mostly config, rarely visited)
   • Opportunities    ← AI-discovered plays (NEW, high-value)

ZONE 3 — REVIEW (pulled, not pushed)
   • Insights         ← performance + territory analytics (all reporting lives here)

PERSISTENT
   • Command bar (⌘K)  ← the real AI surface (Section 5)
   • Profile / Settings
```

### Full sitemap

```
BobBee
├── Today  (landing)
│    ├── Morning brief (AI-generated plan)
│    ├── Priority moves (3–5 AI-ranked actions)
│    ├── Today's queue (emails · calls · follow-ups, prioritized)
│    └── Pacing (behind/ahead of target — one glance, not a chart wall)
│
├── Queue  (the execution stream)
│    ├── Unified: email drafts, call list, tasks — one prioritized flow
│    ├── Inline AI: draft, revise, brief, "why this one"
│    └── Bulk actions
│
├── Accounts
│    ├── AI-ranked default view (intelligence rows, not spreadsheet)
│    ├── Lists (cadences, leftovers, no-contacts, future)
│    └── Account detail → right-rail dossier + AI dossier
│
├── Opportunities   ← NEW
│    ├── AI-surfaced plays ("3 accounts show renewal risk", "5 whitespace-cloud")
│    └── One-click "work this play" → generates a cadence
│
├── Cadences  (config-level, demoted from top nav)
│
├── Insights
│    ├── Performance (meetings, OI, pipeline influence)
│    ├── Territory (the map lives HERE, as one view among several)
│    └── Activity trends
│
└── Settings  (identity · appearance · access · personalization · about)
```

### The four journeys

- **How users enter:** land on **Today**. First thing they see is a one-paragraph
  AI brief and 3 ranked moves with a single **"Start my day"** CTA that enters a
  focused execution flow (one item at a time, keyboard-driven).
- **How users complete daily work:** **Queue** — a single prioritized stream.
  Draft → review → send → next. Call → brief → log → next. AI is inline at every
  step, never in a corner.
- **How users find opportunities:** **Opportunities** — the model *proactively*
  clusters the book into plays and hands the seller pre-built cadences.
- **How AI helps throughout:** a persistent **⌘K command bar** + inline
  suggestions + the proactive Opportunities surface. Not a chat bubble.

---

## SECTION 4 — Redesign the Dashboard ("Today")

The dashboard's job is to answer five questions **in priority order** and to make
the top of the screen a *plan*, not a *report*.

```
┌──────────────────────────────────────────────────────────────────────────┐
│  IBM BobBee    Today   Queue   Accounts   Opportunities   Insights    ⌘K ◐ │  ← 48px shell, ⌘K is the AI entry
└──────────────────────────────────────────────────────────────────────────┘

  Good morning, Tim.  ·  Monday, July 20  ·  You're on pace for 42 of 50 touches

  ┌────────────────────────────────────────────────────────────────────────┐
  │  ✦  YOUR MORNING BRIEF                                       from watsonx │  ← AI speaks FIRST, full width
  │                                                                          │
  │  You have 27 accounts to engage today. Three deserve your attention      │
  │  first: two show renewal risk and one just posted a funding round.       │
  │  I've drafted 21 emails and prepped 12 call briefs. Start with the       │
  │  priority moves below — that covers 60% of today's pipeline influence.   │
  │                                                                          │
  │            [  ▶  Start my day  ]        [ Ask about my book ]            │  ← ONE dominant primary action
  └────────────────────────────────────────────────────────────────────────┘

  PRIORITY MOVES  ·  ranked by intent × value × timing
  ┌────────────────────────────────────────────────────────────────────────┐
  │ 1 │ ✦ Monarch Mutual        Renewal risk · $131K at stake               │
  │   │   Spend down 18% QoQ, no touch in 34 days.                          │
  │   │   → Call first. Brief ready.            [ Call ]  [ Why? ]          │
  ├────────────────────────────────────────────────────────────────────────┤
  │ 2 │ ✦ Apex Pharma           Buying signal · Series C, $80M              │
  │   │   Funding 2 days ago. Cloud whitespace.                             │
  │   │   → Email drafted, leads with expansion.  [ Review & send ] [ Why? ]│
  ├────────────────────────────────────────────────────────────────────────┤
  │ 3 │ ✦ Vanguard Transport    Warm · opened last 2 emails                 │
  │   │   Engaged but no meeting booked.                                    │
  │   │   → Book a meeting.               [ Draft invite ]  [ Why? ]        │
  └────────────────────────────────────────────────────────────────────────┘

  TODAY'S QUEUE                                              21 emails · 12 calls
  ┌────────────────────────┐  ┌────────────────────────┐
  │  ✉  Emails      0 / 21  │  │  ☎  Calls       0 / 12 │      ← the two work engines,
  │  ▓░░░░░░░░░░░░░░░░░░░░   │  │  ▓░░░░░░░░░░░░░░░░░░    │        progress + ONE primary CTA each
  │  Next: Templeton Health │  │  Next: Harborview Assr. │
  │  [ ▶ Work emails ]      │  │  [ ▶ Start calling ]    │      ← PRIMARY buttons, not gray
  └────────────────────────┘  └────────────────────────┘

  ── everything below the fold is REVIEW, collapsed by default ──────────────

  ▸ Pacing & pipeline        (one row: 42/50 touches · 4 meetings · $360K OI)
  ▸ Opportunities to explore (3 AI plays — expand to see)
```

**What changed and why:**
- **AI speaks first, full width.** A generated brief is the top object. That
  single move converts "dashboard with a chatbot" into "AI-native OS."
- **One dominant primary action** ("Start my day"), not four gray buttons.
- **Priority moves are the hero** — ranked, reasoned, one-click. This is the
  literal answer to "what do I do next."
- **Analytics is demoted below the fold**, collapsed. Reporting is available, not
  dominant. This is *action before analytics* made structural.
- **"Why?" everywhere.** Every AI claim is interrogable. That's how you earn
  enterprise trust in a model.

---

## SECTION 5 — AI-First Experience Redesign

### Why the floating chat panel is wrong

1. **Spatially, it's an afterthought.** Corner = "optional helper." The brief says
   AI is the *operating system*, not a helper. Position encodes priority; the
   corner encodes "low priority."
2. **It's modal and separate.** The seller has to *leave* their work, ask a
   question in a detached box, read an answer, then *return* and act manually. AI
   should act *where the work is*, not narrate from the sideline.
3. **It's a 2023 pattern.** The corner bubble was how every product bolted GPT on
   in 2023. In 2026 it reads as dated the way a skeuomorphic leather calendar read
   as dated in 2015.
4. **It can't be proactive.** A bubble waits to be clicked. An AI OS *surfaces*
   things unprompted.

### Where AI should live instead — three surfaces

**1. Inline / ambient (the primary surface).**
AI lives *inside* every object. The account row has a "why now." The email card
has "revise: shorter / add security angle / more urgent" chips *right there*. The
call brief is interrogable in place. No context switch.

**2. Command bar (⌘K) — the deliberate surface.**
Replace the corner bubble with a **⌘K command palette** (Linear/Notion/Vercel/
Raycast pattern). It's summoned from anywhere, it's fast, it's keyboard-native,
and crucially it can *do* things, not just answer:
```
⌘K
> draft a follow-up to Apex Pharma leading with security
> which accounts haven't been touched in 30 days?
> book a meeting with Vanguard next Tuesday
> show me at-risk renewals over $100K
```
This positions AI as the *command layer of the whole product*, which is exactly
the "operating system" framing you want.

**3. Proactive (the Opportunities surface + morning brief).**
AI clusters the book overnight and pushes plays: *"3 accounts show renewal risk
this week."* The seller doesn't ask — the system tells. This is the difference
between a tool and an assistant.

### Concrete example — the difference

**Today (bolted-on):** seller opens corner chat → types "which accounts are at
risk" → reads a list → closes chat → goes to Accounts → searches each → acts.
Six context switches.

**2026 (AI-native):** seller lands on Today → the brief already says "2 renewal
risks, I put them at the top" → clicks "Call" on move #1 → the brief is right
there → after the call, ⌘K "log: left voicemail, retry Thursday" → done. Zero
context switches. The AI was the substrate, not a sidebar.

> **Keep the watsonx Assistant investment** — just relocate it from a corner
> bubble into (a) the ⌘K command bar and (b) the inline "Why?"/"Revise" chips.
> Same backend, radically more premium surface.

---

## SECTION 6 — Visual Design System (production-ready)

BobBee is on **IBM Carbon Gray 100**, which is a strong foundation. The
refinements below keep Carbon's DNA but pull it toward Linear/Vercel-grade
restraint: **softer elevation instead of hairline borders, one accent gradient
used sparingly, and a larger type floor.**

### Color — Dark (default)

| Token | Hex | Use |
|---|---|---|
| `bg` | `#0B0B0D` | App background (slightly deeper than current `#161616` for more contrast headroom) |
| `surface` | `#161618` | Cards / primary surface |
| `surface-elevated` | `#1F1F23` | Panels, popovers, elevated cards |
| `surface-hover` | `#26262B` | Row / control hover |
| `border-subtle` | `#26262B` | Use **sparingly** — prefer elevation |
| `border-strong` | `#3A3A40` | Only where separation is essential |
| `text-primary` | `#F4F4F5` | Headings, key values |
| `text-secondary` | `#B4B4BB` | Body |
| `text-tertiary` | `#7A7A82` | Captions, meta (floor — never lighter on dark) |
| `ibm-primary` | `#0F62FE` | IBM Blue 60 — deterministic data, primary actions |
| `ai-accent` | `#8A3FFC` | Purple 60 — AI-generated content |
| `ai-gradient` | `linear-gradient(135deg,#4589FF,#8A3FFC)` | AI moments only — brief header, ⌘K, sparkle |
| `success` | `#42BE65` | |
| `warning` | `#F1C21B` | |
| `error` | `#FA4D56` | |
| `info` | `#4589FF` | |

### Color — Light

| Token | Hex |
|---|---|
| `bg` | `#FCFCFD` |
| `surface` | `#FFFFFF` |
| `surface-elevated` | `#FFFFFF` (+ shadow) |
| `border-subtle` | `#EAEAEC` |
| `text-primary` | `#161616` |
| `text-secondary` | `#4B4B52` |
| `text-tertiary` | `#75757E` |
| `ibm-primary` | `#0F62FE` |
| `ai-accent` | `#8A3FFC` |

### Typography — IBM Plex Sans (keep), with a **larger floor**

The recurring "everything's too small" feedback is real. New floor is **13px**,
not 11px.

| Style | Size / Line / Weight | Use |
|---|---|---|
| Display | 40 / 44 / 300 | Profile name, big moments |
| H1 | 28 / 34 / 400 | Page title |
| H2 | 20 / 28 / 600 | Section header |
| H3 | 16 / 22 / 600 | Card title |
| Body-lg | 15 / 24 / 400 | Primary reading |
| Body | 14 / 22 / 400 | Default |
| Label | 13 / 18 / 500 | Meta, table headers (sentence case, **never all-caps**) |
| Mono | 14 / 20 / 500 | Numerals, IDs (IBM Plex Mono) |

Numerals in KPI moments: **32 / 36 / 600, solid `text-primary`** (never
gradient-filled — you already learned this).

### Spacing — 4px base

`4 · 8 · 12 · 16 · 20 · 24 · 32 · 40 · 48 · 64`
- Card padding: **20px** (24px for hero cards)
- Section spacing: **32px** between major regions (up from the current ~14px —
  the density is the enemy of premium)
- Page margins: **32px** desktop, max content width **1280px**

### Borders & Radii — the biggest single visual upgrade

- **Introduce an 8px radius.** Carbon's `radius:0` is a deliberate IBM signature,
  but it is the #1 thing making BobBee read "2018 enterprise." A subtle **8px**
  on cards/buttons/inputs modernizes the entire product in one variable.
  (If IBM brand governance forbids it, use **4px** — but use *something*.)
- **Retire most 1px borders.** Replace hairline separation with elevation +
  spacing. Keep borders only for tables and inputs.

### Shadows (this is what replaces borders)

```
shadow-sm:  0 1px 2px rgba(0,0,0,.24)
shadow-md:  0 4px 12px rgba(0,0,0,.28)
shadow-lg:  0 12px 32px rgba(0,0,0,.36)
shadow-ai:  0 0 0 1px rgba(138,63,252,.30), 0 8px 24px rgba(138,63,252,.14)
```
`shadow-ai` is the "this is an AI object" glow — subtle, premium, and it does the
job the sparkle currently does but with far more sophistication.

### Grid

12-column, 24px gutter, 1280px max. Dashboard: 8-col main / 4-col rail.

---

## SECTION 7 — Component Redesign

**KPI card.** Kill the bordered box. A KPI is: label (13/500/tertiary) · value
(32/600/solid) · delta (13, colored, with ▲/▼) · optional sparkline. No border,
sits on `surface` with 20px padding, separated by space not lines. Use a KPI
*only* for a single number that matters; never a wall of them.

**Navigation.** 48px shell. Left: wordmark. Center: the three-zone nav (Today ·
Queue · Accounts · Opportunities · Insights). Right: ⌘K affordance (visible, not
hidden), then avatar. Active item: 2px `ai-gradient` underline (you have this).
Kill the giant search field — replace with the ⌘K pattern.

**Tables.** For Accounts, move from spreadsheet to **intelligence rows**:
```
┌─────────────────────────────────────────────────────────────────────┐
│ ✦ Monarch Mutual          Insurance · Long Beach, CA                 │
│   Renewal risk — spend down 18% QoQ, 34 days cold      $131K         │
│   [ Call ]  [ Add to cadence ]  [ Why? ]              ● ● signals    │
└─────────────────────────────────────────────────────────────────────┘
```
Row height ~72px, hover reveals actions, the *reasoning is in words*, not dots.

**Lists / queues.** Email & call queue items = compact cards with: recipient,
one-line AI rationale, the drafted subject (email) or objective (call), and
inline action + revise chips. Keyboard: `j/k` to move, `e` to send, `⌘Enter` to
send-all-reviewed.

**Account detail.** A right-rail *dossier* (not a modal), sections: AI summary
(top, `shadow-ai`), Sales Cloud, ZoomInfo, Salesloft, Signals. Every AI line has
"Why?".

**AI panel → AI is not a panel.** Replaced by ⌘K + inline (Section 5).

**Insights panel.** Cards that lead with a *sentence* ("You're 8 touches behind
pace this week"), then the supporting viz. Insight-first, chart-second.

**Empty states.** Never a dashed box with "No data." Always: an illustration +
one sentence + one primary action + (for an AI product) a *suggested* AI action.
"No accounts yet — import your book, or ask BobBee to pull your territory."

**Charts.** See Section 8.

---

## SECTION 8 — Dashboard Analytics Redesign

**Critique of current analytics:**
- **Gradient-filled bars** reduce value-reading accuracy and read as decorative.
- **The progress ring labeled "worked"** is a donut doing a job a single number +
  a thin bar does better.
- **KPI tiles and charts compete** at equal weight with no narrative.
- **The choropleth** is high-effort, low-accuracy, and low-decision-value.

**When to use a KPI vs a chart:**
- **KPI number:** when the seller needs *one value and a direction* (touches
  today, meetings booked, OI $). 90% of a sales OS is this.
- **Bar/column:** comparing a *small set* of discrete buckets (activity by
  weekday). Solid fills, single hue, one highlighted bar (today).
- **Line/area:** trend over time (pace vs. target across the quarter). One line,
  a target reference line, no gradient.
- **Never a pie/donut** for progress — use a labeled bar.
- **Territory:** replace the choropleth with a **ranked horizontal bar list**
  (CA 1,143 · HI 446 · GU 213 · MP 109). It's faster, accurate, accessible, and
  honest. Keep a map *only* if it becomes interactive drill-down in Insights —
  never as decoration on Profile.

**Redesigned analytics principle:** every chart earns its place by answering a
*decision*. "Am I behind?" → pace line with target. "Where's my volume?" → weekday
bars. Everything else is a number.

```
PACING                                          ▲ on track
  Touches   ▓▓▓▓▓▓▓▓▓▓▓▓░░░░  42 / 50    ── target ─────
  Meetings                    4 booked · 2 held
  Pipeline influence          $360K identified
```

---

## SECTION 9 — What Makes This Feel Old

Ranked by impact:

1. **Universal sharp corners (`radius:0`).** The strongest "2018 IBM" signal.
   Modern premium = soft 8px. → Introduce a radius token.
2. **Hairline borders everywhere (15+ per screen).** Boxes-in-boxes is a 2015
   dashboard tell. → Elevation + space instead.
3. **The corner chatbot bubble.** The 2023 "we added AI" cliché. → ⌘K + inline.
4. **Gradient-on-everything.** Bars, rings, panel edges, numerals. → One gradient,
   reserved for AI moments only.
5. **Density with no breathing room** (~14px between major regions). → 32px.
6. **Small type floor (11–12px labels).** → 13px floor.
7. **All-caps labels** (mostly fixed) — dated and lower legibility. → Sentence case.
8. **KPI tile walls.** Four equal stat panels = no hierarchy. → One hero number +
   narrative.
9. **The spreadsheet Accounts table.** → Intelligence rows.
10. **Charts as decoration** (choropleth, gradient donut). → Charts as decisions.

**How leaders solve each:** Linear (borderless, keyboard, ⌘K), Vercel
(elevation + restraint, one accent), Stripe (number-first, narrative analytics),
Ramp (action-first landing, proactive AI), Notion (space, ⌘K, calm surfaces).

---

## SECTION 10 — Design Like It's 2026

Trends BobBee should adopt (and how):

- **AI as substrate, not sidebar.** Generated brief on landing, inline revise
  chips, ⌘K command layer. *(Copilot, Notion AI, Linear's agents.)*
- **Command-driven interaction.** ⌘K everywhere; keyboard-first execution.
  *(Linear, Raycast, Vercel.)*
- **Proactive intelligence.** The product surfaces plays before you ask.
  *(Einstein, Fabric's Copilot, Ramp Intelligence.)*
- **Calm, borderless surfaces.** Elevation + generous space; one accent.
  *(Vercel, Linear, Notion.)*
- **Narrative analytics.** Charts lead with a sentence; a KPI states a
  conclusion. *(Stripe, Ramp.)*
- **Streaming, explainable AI.** Answers stream; every claim has "Why?".
  *(watsonx's own governance story — lean into it, it's an IBM advantage.)*
- **Soft geometry + restrained motion.** 8px radii, purposeful transitions, no
  gratuitous gradient.
- **Density with air.** Enterprise data density *plus* whitespace — the Ramp
  synthesis. Dense ≠ cramped.

Trends to **avoid:** glassmorphism, neon-on-black "AI dashboard" clichés, 3D map
gimmicks, over-animation, rainbow gradients.

---

## SECTION 11 — Final Vision

*It's 7:40 AM. Tim opens BobBee.*

There is no dashboard to parse. There is a sentence, and it's talking to him:
*"Good morning, Tim. Two of your accounts hit renewal risk overnight and one just
raised a Series C. I've reordered your day around them and drafted everything.
Start here."* Below it, three moves — ranked, reasoned, each a single click. The
numbers he used to hunt for are one collapsed row at the bottom, there if he wants
them, out of the way if he doesn't.

He presses **Start my day**. BobBee drops him into a single focused stream — not a
calendar, not a spreadsheet, just the next right action. The first is a call to
Monarch Mutual; the brief is already open, the last touchpoint summarized, the
likely objection flagged. He calls. It goes to voicemail. He hits ⌘K, types *"log
voicemail, retry Thursday 10am,"* and he's already on the next move — an email to
Apex Pharma that BobBee drafted, leading with their funding round and the cloud
whitespace, in Tim's own voice. He tightens one line with a *"make it shorter"*
chip, sends, moves on.

He never opened a chatbot. He never asked the AI for help. The AI was simply
*there* — in the ranking, in the draft, in the brief, in the command he typed
without thinking. By 9:15 he's done 60% of the pipeline-moving work of his day,
and the two accounts that mattered most got touched first, because the system
knew they mattered before he did.

That is the product: **not a dashboard with a chatbot attached, but a sales
operating system that thinks a half-step ahead of the seller and clears the path
to the next action.** It feels less like software he operates and more like a
sharp chief of staff who has already read the room, done the prep, and is quietly
handing him the right thing at the right moment — all day, every day.

That is the version of BobBee worth putting in front of a VP. The distance
between here and there is not a rebuild. It is: **lead with AI, demote the
analytics, kill the corner bubble, soften the geometry, and rank the work.** Five
moves. Do them, and BobBee stops looking like an IBM app and starts looking like
the future of enterprise sales.

---

*Prepared for internal design review. Grounded in the shipping build; all token
values are concrete and implementable against the current `ui_templates.py`
system.*
