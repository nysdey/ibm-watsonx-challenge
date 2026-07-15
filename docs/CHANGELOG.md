# Changelog

Reverse-chronological history of the Seller Dashboard. Newest first. See also
[ARCHITECTURE.md](ARCHITECTURE.md), [SECURITY.md](SECURITY.md),
[OPERATIONS.md](OPERATIONS.md), and [GOTCHAS.md](GOTCHAS.md).

## 2026-07-15 — Architecture review + Phase 0/1 cleanup + docs consolidation
- Reviewed the whole project (adversarially verified); verdict: architecture is deliberately sound (crash isolation, file-handoff, audited local-auth) — no from-scratch rewrite. Real wins are packaging + dead weight.
- Deleted dead weight: Pipeline_Review/staged_pipeline_v2 + staged_pipeline_v3 (already-applied staging artifacts, ~3,821 LOC); the abandoned 3.4M ISC_Scraper PyInstaller binary; 12M of IBM login-debug screenshots.
- Added a pinned root requirements.txt (openpyxl 3.1.5, flask 3.1.3, playwright 1.60.0) for the shared .venv.
- Dedup: removed credential_store.SERVICE_CREDENTIAL in favor of shared_auth.credential_key (single source of truth); extracted credential_store._read_email; secure_auth_files.py now unions registry-derived session paths (auto-hardens new services).
- Docs: consolidated the project's 16 scattered .md files into 6 (README + docs/ARCHITECTURE/SECURITY/OPERATIONS/CHANGELOG/GOTCHAS). `live_transcribe_bot/` is a separate embedded git repo and keeps its own README/INTEGRATION docs (its component is summarized in ARCHITECTURE.md).
- UI extraction: moved the 8 page templates (~2,648 lines, 56% of the file) out of `run_pipeline.py` into `ui_templates.py`, **verbatim** and still rendered via `render_template_string` (byte-identical — verified against a pre-extraction snapshot; the escaping contract in GOTCHAS.md is unchanged). `run_pipeline.py` is now 2,052 lines of Python (routing/auth/orchestration) with the UI decoupled. Also fixed the 4 stale doc-comment refs in `run_pipeline.py`.
- Still deferred: the Python-logic package split (app/orchestrators/process_manager/auth_watchdog), converting the templates to real Jinja `.html` files (needs route-by-route headed-browser verification), idle-aware auth-probe backoff, the Phase-4 auth-marker unification (needs live SSO/MFA creds to verify), and the ISC `_internal` vendored-dep cleanup (on `sys.path` at runtime).

---

## Undated — Pipeline latent-bug findings (ready-to-apply)

The following are verified latent bugs found by review of the Pipeline feature. The app
runs fine; these are latent. They were staged to apply when macOS file access to
`Seller_Dashboard` was restored (the same macOS-TCC block affects all three rounds below).
Round numbering preserved from source.

### Round 1 — concurrency, hangs, scraper, winback, UX

#### HIGH — concurrency & hangs (`run_pipeline.py`)

**1+2+3. TOCTOU races on the run guards** (endpoints ~1619-1634)
Both `/run` endpoints check `active` then set it *False*, and only set True inside the
worker thread — so two near-simultaneous POSTs both pass and launch two subprocesses that
race the SHARED tmp file (`latest.json.tmp` / `winback.json.tmp`) → possible corruption.
Fix: add module locks near the state dicts (~line 1120), after `import threading`:

```python
_PIPELINE_RUN_LOCK = threading.Lock()
_WINBACK_RUN_LOCK  = threading.Lock()
```

Replace `api_pipeline_review_run` (1619-1625):

```python
@app.route("/api/pipeline_review/run", methods=["POST"])
def api_pipeline_review_run():
    with _PIPELINE_RUN_LOCK:
        if _PIPELINE_REVIEW_STATE["active"]:
            return jsonify({"ok": False, "error": "already running"})
        _PIPELINE_REVIEW_STATE.update(active=True, done=False, error=None, phase="working")
    threading.Thread(target=_run_pipeline_review, daemon=True).start()
    return jsonify({"ok": True})
```

Replace `api_pipeline_review_winback_run` (1628-1634) the same way with `_WINBACK_RUN_LOCK`
and `_WINBACK_STATE`. (Workers already reset `active=False` on done/error, so setting True
synchronously here cannot wedge.)

**4+5+9. `subprocess.run` / `_launch_and_wait` have NO timeout**
A hung child (live browser MFA wait, stalled load loop) blocks the worker/request thread
forever; for winback it leaves `_WINBACK_STATE` active=True permanently → tab spins, every
retry refused.
- `_run_winback` `subprocess.run` (~1326): add `timeout=1800` and
  `except subprocess.TimeoutExpired:` → set `phase="error"`, `active=False`, actionable message.
- `api_pipeline_review_update` / `_draft_email` `subprocess.run` (~1671, ~1706): add
  `timeout=config-derived (UPDATE_TIME_BUDGET+60)`; on TimeoutExpired return a clean JSON error.
- `_launch_and_wait` (~1147): bound the wait; on expiry `terminate()`/`kill()` the Popen and
  return an error so the worker sets `active=False`/`phase=error`.

**6. `_launch`: unlocked poll-then-Popen** (~519)
Racing threads both spawn `run.py` and the 2nd overwrites `_PROCESSES[key]`, orphaning the
1st. Wrap the check-and-register in a module lock; register the entry before releasing it.

#### MEDIUM — scraper (`pipeline_scraper.py`, live-mode only)

**7. `_switch_view` false-negative** (~303)
`_picker_label` returns the first visible combobox, not necessarily the saved-view picker,
so a correctly-switched "Lanie Form" view can be wrongly rejected. Scope the label lookup
to the actual saved-view picker element (nearby label text / stable attr), or assert the
element that was clicked now shows the target text.

**8. `_load_all_rows` ~8-min stall** (~421)
If a "Load more" control stays visible but stops adding rows, the loop runs all 400
iterations. Increment `stable` whenever `now <= last` regardless of `clicked`, break at the
threshold, and add an overall wall-clock budget.

#### LOW — winback (`winback.py`)

**10. Whitespace-only owner → IndexError** (~216)
`owner.split()[0]` crashes `analyze()` / the whole run on a whitespace owner.

```python
owner = (deal.get("owner") or "").strip() or "there"
first = owner.split()[0] if owner.split() else "there"
```

Optionally wrap each deal in `analyze()` in try/except so one bad row can't sink the run.

#### UX / robustness (JS review came back clean otherwise)

**A. "Other IBM" filter trap** (`PL.passes`, `run_pipeline.py` inline JS)
`passes()` applies `FILTER.attn` / `closeWin` in Other-IBM mode, but the tiles that toggle
them are hidden there → a filter set in My Pipeline silently hides Other-IBM deals with no
visible reset. Gate them:
`if(MODE!=='other'){ if(!inCloseWin(o))return false; if(FILTER.attn&&!needsAttention(o))return false; }`

**B. Malformed request → 400/415 HTML** (pipeline endpoints)
`body = request.json or {}` raises on bad/mistyped body. Use
`body = request.get_json(silent=True) or {}` for graceful JSON errors.

**C. Headline band cosmetic off-by-band** — "N need your attention" (≥2) vs "Act now" band (≥3).

### Round 2 — first-principles findings (correctness + efficiency)

#### CORRECTNESS

**D1. `product_class` name-pollution — account/opportunity words can override the real product**
`product_class._text_of()` concatenates `product`/`product_line` + `opportunity` name +
`full` product columns into ONE blob, and `classify()` checks ALL infra markers before ANY
other-IBM marker. So a genuinely non-infra deal whose OPPORTUNITY or ACCOUNT name happens to
contain an infra word gets mis-tagged infra. E.g. `product_line` "watsonx.data" in an opp
named "Storage Modernization – watsonx.data" → "storage" matches first → classified Infra,
wrong tab. FIX: classify the explicit `product_line`/`product` FIRST; only fall back to the
opportunity-name text when `product_line` is empty — i.e. try `classify(product_line)`; if
it returns the "Unclassified" default, THEN widen to the full text.

**D2. Timezone off-by-one in the JS date math (LOW)**
PL JS `closeDate` does `new Date("YYYY-MM-DD")` (parsed as UTC midnight) but `today()` is
LOCAL midnight. `Math.round` absorbs the skew for zones within ~±11h, but at UTC±12+ a deal
can show one day off (past-due / closing-soon / quarter-flag). FIX: parse as local —
`const [y,m,d]=o.close_date.split('-').map(Number); return new Date(y,m-1,d);`

#### EFFICIENCY / FAILURE MODES

**E1. Perpetual high-frequency polling**
The dashboard polls `/api/status` + `/api/login/status` every 2s AND `/progress` ~2×/sec,
FOREVER — even when idle and even when that tab isn't open (observed in the live log: a
steady stream of `GET /progress 200`). Wasteful CPU/battery/log-noise on a local tool.
FIX: (a) pause polling when `document.hidden`; (b) back off `/progress` to on-demand (only
while a scrape's `active`); (c) widen the idle status interval (e.g. 2s→10s when nothing is
running).

**E2. `_reset_for_fresh_demo()` forces a full re-scrape on every app restart**
It wipes every step's `output/` on startup, discarding a perfectly valid `latest.json`.
Fine for a demo; in real use the seller restarts → the Pipeline tab auto-pulls → a
multi-minute live ISC scrape they didn't ask for. FIX: gate the wipe behind an explicit
DEMO env flag (default OFF in real use), or keep `latest.json` and let the Refresh button
be the only re-pull trigger.

**E3. Win-back drafts every deal, including below-threshold ones**
`winback.analyze()` calls `outreach_draft()` for ALL won/lost deals, but only those with
`score >= min_score` are shown/recommended. With `use_llm=True` that's an LLM call per
throwaway deal. FIX: only draft for deals at/above `min_score` (draft lazily, or filter
before the draft loop).

**E4. `api_pipeline_review_data` re-reads + re-parses the 213KB `latest.json` every request**
No mtime cache. Under the render/poll cadence this re-parses the full JSON repeatedly.
Minor, but a trivial mtime-keyed cache removes it.

(Note: these need normal file access to fix — same macOS-TCC block as Round 1. D1 and E1
are the highest-value here: a real mis-tag, and a steady resource drain.)

### Round 3 — error handling & atomicity

**G1. Data/Win-back GET endpoints 500 on a malformed JSON file (no try/except)** [MED, real]
`api_pipeline_review_data` does `json.loads(p.read_text())` and
`api_pipeline_review_winback` does `json.loads(p.read_text())` with NO exception handling.
If `latest.json` / `winback.json` is ever malformed — a partial write from a killed/again-
running process, a disk-full truncation, or the concurrent-pull race (findings #2/#3)
racing the shared `.tmp` — the GET throws and Flask returns a raw 500 HTML page. The
client's `res.json()` then throws, and the tab looks permanently broken. FIX: wrap each in
try/except and fall back to the empty payload the endpoints already define for the "file
missing" case (they handle `p.exists()` false but not "exists-but-corrupt"). This is the
defensive complement to the race/atomicity fixes.

**G2. `latest.xlsx` / dated `.xlsx` writes are NOT atomic (`schema_io.write_outputs`)** [LOW-MED]
`latest.json` is written atomically (tmp → replace), but `wb.save(dated)` +
`shutil.copyfile(dated, latest_xlsx)` write in place. Under the concurrent-pull race, two
writers corrupt these `.xlsx` files (and both target the SAME dated filename
`pipeline_review_YYYYMMDD.xlsx`). The race fix removes the concurrency; if you want belt-
and-suspenders, save to a temp `.xlsx` and `os.replace()` into place too.

**G3. `parse_amount` silently drops ranges / malformed amounts (`pipeline_scraper`)** [LOW]
`re.sub(r"[^\d.\-]", "", "$1,000-2,000")` → `"1000-2000"` → `float()` raises → None, so a
deal with a range/odd amount cell shows "—" and is excluded from every $ total with no
warning. FIX: on parse failure, log the raw cell and/or take the first numeric run, rather
than silently nulling.

**G4. winback GET reports running from `_WINBACK_STATE` but data from disk — can disagree** [LOW]
`api_pipeline_review_winback` returns disk `winback.json` + `running=_WINBACK_STATE["active"]`.
Right after a run finishes, `active` flips to False before/around the file write; a poll
landing in that gap can report `running=False` with stale/absent data, making the JS think
it's done early. Minor with the tmp+replace write, but tightening the worker to set
`active=False` strictly AFTER the file is on disk removes the window.
