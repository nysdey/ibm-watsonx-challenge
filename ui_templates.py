"""BobBee UI templates — extracted verbatim from run_pipeline.py.

These page templates are rendered with flask.render_template_string (NOT
render_template), so the double-escaping contract is UNCHANGED and load-bearing:
JS backslash/regex escapes stay doubled, and no literal {{ or {% may appear in the
JS. See docs/GOTCHAS.md. Keeping them in their own module (byte-identical to the
originals) decouples every CSS/JS edit from the security-audited backend so a UI
tweak no longer shares a diff with auth/orchestration code.

Design system: dark, IBM-inspired (IBM Blue for deterministic pipeline data, IBM
Purple reserved ONLY for watsonx/Granite-generated content), IBM Plex Sans/Mono.
_FONTS + _DESIGN_CSS are shared across every page the same way mock_ui_templates.py
shares _BASE_CSS — one visual language, edited in one place.
"""

_FONTS = """<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
"""

# A single reusable 4-point sparkle — the one visual marker of "this came from
# Granite," per the design rule: deterministic pipeline data is blue, anything
# the model generated is purple AND carries this icon. Never used elsewhere.
_SPARKLE = '<svg class="spark" viewBox="0 0 24 24" fill="currentColor"><path d="M12 1c.7 5.1 2.6 7 7.7 7.7-5.1.7-7 2.6-7.7 7.7-.7-5.1-2.6-7-7.7-7.7C9.4 8 11.3 6.1 12 1z"/></svg>'

_DESIGN_CSS = """
  :root{
    --bg:#0a0a0c; --layer1:#18181b; --layer2:#212124; --layer3:#29292d;
    --border:#2b2b2f; --border-strong:#3c3c41;
    --text1:#f2f2f3; --text2:#a8a8ae; --text3:#77777d;
    --blue:#0f62fe; --blue-text:#5b96ff; --blue-soft:rgba(15,98,254,.14); --blue-border:rgba(91,150,255,.3);
    --purple:#8a3ffc; --purple-text:#b490ff; --purple-soft:rgba(138,63,252,.14); --purple-border:rgba(180,144,255,.32);
    --green:#42be65; --amber:#f1c21b; --red:#fa4d56;
    --r-sm:4px; --r-md:8px; --r-lg:12px;
    --font:'IBM Plex Sans',-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;
    --mono:'IBM Plex Mono',ui-monospace,'SF Mono',Menlo,monospace;
  }
  *{ box-sizing:border-box; }
  html,body{ background:var(--bg); }
  body{ font-family:var(--font); color:var(--text1); margin:0; font-size:14px; line-height:1.55; -webkit-font-smoothing:antialiased; }
  ::selection{ background:rgba(91,150,255,.3); }
  ::-webkit-scrollbar{ width:10px; height:10px; }
  ::-webkit-scrollbar-track{ background:transparent; }
  ::-webkit-scrollbar-thumb{ background:var(--border-strong); border-radius:8px; border:2px solid transparent; background-clip:content-box; }
  a{ color:var(--blue-text); }
  h1,h2,h3{ font-weight:600; letter-spacing:-.01em; margin:0; color:var(--text1); }
  .mono{ font-family:var(--mono); }

  .btn{ font:inherit; font-size:13.5px; font-weight:500; color:var(--text1); background:var(--layer2);
        border:1px solid var(--border); border-radius:var(--r-sm); padding:9px 16px; cursor:pointer;
        transition:background .15s,border-color .15s,transform .08s; white-space:nowrap; }
  .btn:hover{ background:var(--layer3); border-color:var(--border-strong); }
  .btn:active{ transform:scale(.98); }
  .btn.primary{ background:var(--blue); border-color:var(--blue); color:#fff; }
  .btn.primary:hover{ background:#0353e9; border-color:#0353e9; }
  .btn.primary:disabled,.btn:disabled{ background:var(--layer1); border-color:var(--border); color:var(--text3); cursor:not-allowed; }
  .btn.ai{ background:var(--purple); border-color:var(--purple); color:#fff; }
  .btn.ai:hover{ background:#7a2ff0; }
  .btn.big{ padding:11px 20px; font-size:14px; width:100%; }
  .link{ color:var(--blue-text); font-size:13.5px; font-weight:500; cursor:pointer; background:none; border:none; padding:0; font-family:inherit; }
  .link:hover{ text-decoration:underline; }

  .card{ background:var(--layer1); border:1px solid var(--border); border-radius:var(--r-lg); }

  .badge{ display:inline-flex; align-items:center; gap:5px; font-size:11.5px; font-weight:500; padding:4px 10px;
          border-radius:var(--r-sm); border:1px solid transparent; line-height:1.3; white-space:nowrap; }
  .badge.blue{ background:var(--blue-soft); color:var(--blue-text); border-color:var(--blue-border); }
  .badge.ai{ background:var(--purple-soft); color:var(--purple-text); border-color:var(--purple-border); }
  .badge.green{ background:rgba(66,190,101,.13); color:var(--green); border-color:rgba(66,190,101,.3); }
  .badge.neutral{ background:var(--layer2); color:var(--text2); border-color:var(--border); }
  .spark{ width:11px; height:11px; flex:none; }

  .dot{ display:inline-block; width:7px; height:7px; border-radius:50%; background:var(--text3); flex:none; }
  .dot.done{ background:var(--green); }
  .dot.running{ background:var(--amber); animation:pulse 1.4s ease-in-out infinite; }
  .dot.err{ background:var(--red); }
  .dot.pending{ background:var(--text3); }
  @keyframes pulse{ 0%,100%{ opacity:1; } 50%{ opacity:.35; } }
  @keyframes spin{ to{ transform:rotate(360deg); } }
  .spinner{ width:13px; height:13px; border-radius:50%; border:2px solid var(--purple-border);
            border-top-color:var(--purple-text); animation:spin .7s linear infinite; flex:none; }

  table{ border-collapse:separate; border-spacing:0; width:100%; font-size:12.5px; background:var(--layer1);
         border:1px solid var(--border); border-radius:var(--r-md); overflow:hidden; }
  th,td{ padding:10px 14px; text-align:left; border-bottom:1px solid var(--border); vertical-align:top; }
  th{ background:var(--layer2); font-weight:600; color:var(--text2); cursor:pointer; white-space:nowrap; }
  th:hover{ color:var(--text1); }
  tr:hover td{ background:var(--layer2); }
  tr:last-child td{ border-bottom:none; }

  input[type=text],input[type=email],input[type=password]{ font:inherit; font-size:14px; border:1px solid var(--border);
         border-radius:var(--r-sm); padding:10px 13px; background:var(--layer2); color:var(--text1);
         transition:border-color .15s,background .15s; }
  input:focus{ outline:none; border-color:var(--blue-text); background:var(--layer1); box-shadow:0 0 0 3px var(--blue-soft); }
  select{ font:inherit; font-size:13.5px; border:1px solid var(--border); border-radius:var(--r-sm); padding:8px 13px;
          background:var(--layer2); color:var(--text1); cursor:pointer; width:100%; }
"""

PAGE_TEMPLATE = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>BobBee</title>
""" + _FONTS + """
<style>
""" + _DESIGN_CSS + """
  /* ── login gate ─────────────────────────────────────────────── */
  .gate{ position:fixed; inset:0; display:flex; align-items:center; justify-content:center; z-index:500;
         background:radial-gradient(1000px 520px at 50% 10%, rgba(138,63,252,.08), transparent 65%), var(--bg); }
  .gate-card{ width:380px; max-width:calc(100vw - 40px); text-align:center; background:var(--layer1);
              border:1px solid var(--border); border-radius:var(--r-lg); padding:40px 34px 34px; }
  .gate-logo-img{ width:56px; height:56px; margin:0 auto 18px; display:block; }
  .gate-card h1{ font-size:24px; margin:0 0 6px; }
  .gate-sub{ color:var(--text2); font-size:14.5px; margin:0 0 24px; }
  .gate-card form{ display:flex; flex-direction:column; gap:10px; }
  .gate-card .btn{ margin-top:6px; }
  .gate-err{ color:var(--red); font-size:13.5px; min-height:18px; text-align:left; }
  .gate-note{ color:var(--text3); font-size:12px; line-height:1.55; margin-top:20px; }

  /* ── top bar ────────────────────────────────────────────────── */
  .topbar{ position:sticky; top:0; z-index:50; background:rgba(10,10,12,.85); backdrop-filter:saturate(160%) blur(16px);
           border-bottom:1px solid var(--border); display:flex; align-items:center; justify-content:space-between;
           padding:12px 28px; gap:16px; }
  .brand{ display:flex; align-items:center; gap:11px; }
  .brand-logo{ width:32px; height:32px; flex:none; }
  .brand-name{ font-size:16px; font-weight:600; letter-spacing:-.01em; }
  .brand-sub{ font-size:11.5px; color:var(--text3); margin-top:1px; }
  .topbar .right{ display:flex; align-items:center; gap:8px; flex-wrap:wrap; justify-content:flex-end; }
  .detailsbtn{ position:relative; }
  .warndot{ position:absolute; top:4px; right:6px; width:8px; height:8px; border-radius:50%; background:var(--red);
            box-shadow:0 0 0 3px rgba(250,77,86,.18); }

  main{ max-width:1180px; margin:0 auto; padding:36px 28px 100px; }
  .page{ display:none; } .page.active{ display:block; }
  .page-head{ margin-bottom:24px; }
  .page-head h2{ font-size:24px; }
  .page-head p{ color:var(--text3); font-size:14.5px; margin:5px 0 0; }

  /* ── pipeline ───────────────────────────────────────────────── */
  .pipeline{ display:flex; align-items:stretch; gap:0; margin-bottom:28px; }
  .pipe-arrow{ display:flex; align-items:center; justify-content:center; flex:none; width:30px; color:var(--text3); }
  .pipe-step{ flex:1; min-width:0; background:var(--layer1); border:1px solid var(--border); border-radius:var(--r-lg);
              padding:18px 18px 16px; display:flex; flex-direction:column; transition:border-color .2s,box-shadow .2s; }
  .pipe-step.working{ border-color:var(--blue-border); box-shadow:0 0 0 3px var(--blue-soft); }
  .pipe-step.done{ border-color:rgba(66,190,101,.32); }
  .pipe-step.ai{ border-color:var(--purple-border); }
  .pipe-step.ai.working{ border-color:var(--purple-border); box-shadow:0 0 0 3px var(--purple-soft); }
  .pipe-num{ font-family:var(--mono); font-size:11px; color:var(--text3); margin-bottom:6px; }
  .pipe-title{ font-size:15.5px; font-weight:600; letter-spacing:-.005em; display:flex; align-items:center; gap:6px; }
  .pipe-step.ai .pipe-title{ color:var(--purple-text); }
  .pipe-sub{ color:var(--text3); font-size:12px; margin-top:3px; min-height:15px; }
  .pipe-status{ display:flex; align-items:flex-start; gap:8px; margin-top:14px; font-size:12.5px; color:var(--text2); flex:1; }
  .pipe-status .amsg{ flex:1; min-width:0; }
  .pipe-status.err .amsg{ color:var(--red); }
  .pipe-seller{ color:var(--text3); font-size:11.5px; margin-top:6px; }
  .pipe-foot{ margin-top:14px; display:flex; flex-direction:column; gap:8px; }
  .pipe-select{ margin-bottom:2px; }
  .pipe-records{ font-family:var(--mono); font-size:12px; color:var(--text1); }
  .pipe-choices{ display:flex; flex-direction:column; gap:6px; margin:10px 0 4px; }
  .pipe-choice{ display:flex; align-items:center; gap:8px; font-size:12.5px; color:var(--text2); cursor:pointer; }
  .pipe-choice input{ accent-color:var(--purple); }
  .pipe-chips{ display:flex; gap:10px; flex-wrap:wrap; margin-top:12px; }
  .pipe-chip{ display:inline-flex; align-items:center; gap:6px; font-size:11px; color:var(--text3); }
  .showlog{ margin-top:10px; align-self:flex-start; }
  .alog{ margin-top:10px; background:var(--layer2); border-radius:var(--r-sm); padding:12px 14px; max-height:180px;
         overflow-y:auto; font:11.5px/1.6 var(--mono); color:var(--text2); display:none; }
  .alog.show{ display:block; }
  .alog div{ padding:1px 0; word-break:break-word; }

  /* ── KPI hero ───────────────────────────────────────────────── */
  .kpis{ display:grid; grid-template-columns:repeat(5,1fr); gap:14px; margin-bottom:32px; }
  .kpi{ background:var(--layer1); border:1px solid var(--border); border-radius:var(--r-lg); padding:20px 20px 18px; }
  .kpi.ai{ border-color:var(--purple-border); }
  .kval{ font-family:var(--mono); font-size:30px; font-weight:600; color:var(--text1); line-height:1; }
  .kpi.ai .kval{ color:var(--purple-text); }
  .klabel{ color:var(--text3); font-size:12px; margin-top:9px; display:flex; align-items:center; gap:5px; }

  /* ── ROI ────────────────────────────────────────────────────── */
  .roi-head{ margin:8px 0 14px; }
  .roi-head h3{ font-size:16px; }
  .roi-head p{ color:var(--text3); font-size:13px; margin:4px 0 0; }
  .roi{ display:grid; grid-template-columns:repeat(4,1fr); gap:14px; }
  .roi-card{ background:var(--layer1); border:1px solid var(--border); border-radius:var(--r-lg); padding:18px 20px; }
  .roi-card.ai{ border-color:var(--purple-border); }
  .rlabel{ color:var(--text3); font-size:12px; }
  .rval{ font-family:var(--mono); font-size:22px; font-weight:600; margin-top:8px; color:var(--text1); }
  .rval.blue{ color:var(--blue-text); }
  .roi-card.ai .rval{ color:var(--purple-text); }

  @media(max-width:980px){
    .pipeline{ flex-direction:column; } .pipe-arrow{ width:auto; height:22px; transform:rotate(90deg); }
    .kpis,.roi{ grid-template-columns:repeat(2,1fr); }
  }

  /* ── details modal (Access) ────────────────────────────────── */
  .modal{ position:fixed; inset:0; background:rgba(0,0,0,.55); backdrop-filter:blur(3px); display:none;
          align-items:flex-start; justify-content:center; z-index:200; padding:60px 20px; overflow-y:auto; }
  .modal.show{ display:flex; }
  .modal-card{ background:var(--layer1); border:1px solid var(--border); border-radius:var(--r-lg); width:640px;
               max-width:100%; padding:26px 28px 30px; box-shadow:0 24px 60px rgba(0,0,0,.5); }
  .modal-head{ display:flex; align-items:center; justify-content:space-between; margin-bottom:6px; }
  .modal-head h2{ font-size:19px; }
  .signed-as{ color:var(--text2); font-size:13px; margin:2px 0 20px; }
  .signed-as b{ color:var(--text1); }
  .panel{ background:var(--layer2); border:1px solid var(--border); border-radius:var(--r-md); padding:16px 18px; margin-bottom:12px; }
  .panel h3{ font-size:12.5px; font-weight:600; color:var(--text2); margin:0 0 12px; }
  .lrow{ display:flex; align-items:center; gap:12px; padding:10px 0; border-top:1px solid var(--border); }
  .lrow:first-of-type{ border-top:none; }
  .lrow .svc{ width:80px; font-weight:500; font-size:13.5px; }
  .lrow .fill{ flex:1; color:var(--text2); font-size:12.5px; display:flex; align-items:center; gap:10px; flex-wrap:wrap; }
  .pill{ display:inline-flex; align-items:center; gap:6px; font-size:12px; font-weight:500; color:var(--text2); white-space:nowrap; }
  .pill .dot{ background:var(--text3); }
  .pill.ready .dot{ background:var(--green); }
  .pill.expired .dot,.pill.error .dot{ background:var(--red); }
  .pill.checking .dot,.pill.waiting .dot{ background:var(--amber); animation:pulse 1.4s ease-in-out infinite; }
  .alert{ background:rgba(250,77,86,.12); color:#ff8790; border-radius:var(--r-sm); padding:11px 15px; margin-bottom:10px;
          font-size:13px; font-weight:500; display:none; }
  .alert.show{ display:block; }
  .note{ color:var(--text3); font-size:12.5px; line-height:1.55; margin-bottom:6px; }
  .panel input[type=text],.panel input[type=password]{ margin:8px 8px 4px 0; }
</style>
</head>
<body>

<!-- ── IBM Login gate ─────────────────────────────────────────── -->
<div class="gate" id="loginGate" style="display:none">
  <div class="gate-card">
    <img class="gate-logo-img" src="/static/logo.png" alt="BobBee">
    <h1>Sign in to BobBee</h1>
    <p class="gate-sub">Use your IBM ID to continue.</p>
    <form onsubmit="submitLogin(event)">
      <input type="email" id="loginEmail" placeholder="you@ibm.com" autocomplete="username" required>
      <input type="password" id="loginPw" placeholder="Password" autocomplete="current-password" required>
      <div class="gate-err" id="loginErr"></div>
      <button class="btn primary big" type="submit" id="loginBtn">Sign in</button>
    </form>
    <div class="gate-note">Demo sign-in — this uses mock data and never contacts IBM. Only your email is kept (locally), to pick the accounts in your territory; the password is discarded. Any email works.</div>
  </div>
</div>

<!-- ── main app ───────────────────────────────────────────────── -->
<div id="app" style="display:none">
  <header class="topbar">
    <div class="brand">
      <img class="brand-logo" src="/static/logo.png" alt="">
      <div>
        <div class="brand-name">BobBee</div>
        <div class="brand-sub">AI-powered outbound planning and personalization</div>
      </div>
    </div>
    <div class="right">
      <span class="badge blue" id="territoryBadge">Territory</span>
      <span class="badge green">Watsonx connected</span>
      <span class="badge ai">""" + _SPARKLE + """Granite active</span>
      <button class="btn detailsbtn" onclick="openDetails()">Details<span class="warndot" id="detailsWarn" style="display:none"></span></button>
    </div>
  </header>

  <main>
    <section id="page-outbound" class="page active">
      <div class="page-head">
        <h2>Territory to personalization, in four steps</h2>
        <p>Pull your accounts, build a strategy, load contacts, and let Bobby write the outreach.</p>
      </div>

      <div class="pipeline">
        <!-- Step 1: Accounts -->
        <div class="pipe-step" id="card-gma">
          <div class="pipe-num">Step 1</div>
          <div class="pipe-title">Accounts</div>
          <div class="pipe-sub">ISC + IBM install base + segmentation</div>
          <div class="pipe-status" id="gmaStatus"><span class="dot pending"></span><span class="amsg">Not started</span></div>
          <div class="pipe-seller" id="gmaSeller"></div>
          <div class="pipe-foot">
            <span class="pipe-records" id="gmaResults"></span>
            <button class="btn primary" id="gmaBtn" onclick="runGetMyAccounts()">Run step</button>
          </div>
          <div class="pipe-chips" id="gmaChips"></div>
          <button class="link showlog" id="gmaLogToggle" onclick="toggleLog('gma')" style="display:none">Show details</button>
          <div class="alog" id="gmaLog"></div>
        </div>
        <div class="pipe-arrow">&rarr;</div>

        <!-- Step 2: Strategy -->
        <div class="pipe-step" id="card-strategy">
          <div class="pipe-num">Step 2</div>
          <div class="pipe-title">Strategy</div>
          <div class="pipe-sub">Account tiering + call planning</div>
          <div class="pipe-status" id="strategyStatus"><span class="dot pending"></span><span class="amsg">Not started</span></div>
          <div class="pipe-foot">
            <span class="pipe-records" id="strategyResults"></span>
            <button class="btn primary" id="strategyBtn" onclick="runStrategy()">Run step</button>
          </div>
          <div class="pipe-chips" id="strategyChips"></div>
          <button class="link showlog" id="strategyLogToggle" onclick="toggleLog('strategy')" style="display:none">Show details</button>
          <div class="alog" id="strategyLog"></div>
        </div>
        <div class="pipe-arrow">&rarr;</div>

        <!-- Step 3: Contacts -->
        <div class="pipe-step" id="card-fill">
          <div class="pipe-num">Step 3</div>
          <div class="pipe-title">Contacts</div>
          <div class="pipe-sub">ZoomInfo readiness + Salesloft cadence</div>
          <div class="pipe-status" id="fillStatus"><span class="dot pending"></span><span class="amsg">Not started</span></div>
          <div class="pipe-foot">
            <select class="sel pipe-select" id="fillCadence">{% for c in cadences %}<option value="{{ c }}">{{ c }}</option>{% endfor %}</select>
            <span class="pipe-records" id="fillResults"></span>
            <button class="btn primary" id="fillBtn" onclick="runFill()">Run step</button>
          </div>
          <div class="pipe-chips" id="fillChips"></div>
          <button class="link showlog" id="fillLogToggle" onclick="toggleLog('fill')" style="display:none">Show details</button>
          <div class="alog" id="fillLog"></div>
        </div>
        <div class="pipe-arrow">&rarr;</div>

        <!-- Step 4: Bobby AI -->
        <div class="pipe-step ai" id="card-bobby">
          <div class="pipe-num">Step 4</div>
          <div class="pipe-title">""" + _SPARKLE + """Bobby AI</div>
          <div class="pipe-sub">Personalized email per contact, written by Granite</div>
          <div class="pipe-status" id="bobbyStatus"><span class="dot pending"></span><span class="amsg">Pick a cadence</span></div>
          <div class="pipe-choices" id="bobbyChoices">
            {% for c in bobby_cadences %}
            <label class="pipe-choice"><input type="radio" name="bobbyCadence" value="{{ c }}"{{ ' checked' if loop.first else '' }}> {{ c }}</label>
            {% endfor %}
          </div>
          <div class="pipe-foot">
            <button class="btn ai" id="bobbyBtn" onclick="runBobby()">Run step</button>
          </div>
        </div>
      </div>

      <div class="kpis">
        <div class="kpi"><div class="kval" id="kpiAccounts">—</div><div class="klabel">Accounts analyzed</div></div>
        <div class="kpi"><div class="kval" id="kpiTier1">—</div><div class="klabel">Tier 1 accounts</div></div>
        <div class="kpi"><div class="kval" id="kpiContacts">—</div><div class="klabel">Contacts staged</div></div>
        <div class="kpi ai"><div class="kval" id="kpiEmails">—</div><div class="klabel">""" + _SPARKLE + """Emails generated</div></div>
        <div class="kpi"><div class="kval" id="kpiTime">—</div><div class="klabel">Time saved</div></div>
      </div>

      <div class="roi-head">
        <h3>Productivity impact</h3>
        <p>Manual outbound prep versus one BobBee run.</p>
      </div>
      <div class="roi">
        <div class="roi-card"><div class="rlabel">Manual process</div><div class="rval">6+ hrs / week</div></div>
        <div class="roi-card"><div class="rlabel">BobBee</div><div class="rval blue">~10 minutes</div></div>
        <div class="roi-card ai"><div class="rlabel">""" + _SPARKLE + """Emails personalized</div><div class="rval" id="roiEmails">—</div></div>
        <div class="roi-card"><div class="rlabel">Estimated productivity gain</div><div class="rval blue">94%</div></div>
      </div>
    </section>
  </main>
</div>

<!-- ── Details (Access) modal ─────────────────────────────────── -->
<div class="modal" id="detailsModal" onclick="if(event.target===this) closeDetails()">
  <div class="modal-card">
    <div class="modal-head">
      <h2>Access</h2>
      <button class="link" onclick="closeDetails()">Close</button>
    </div>
    <div class="signed-as" id="signedAs"></div>

    <div class="panel">
      <h3>Sessions</h3>
      <div class="alert" id="loginAlert"></div>
      <div id="loginRows"></div>
    </div>

    <div class="panel">
      <h3>Saved password</h3>
      <div class="note">One IBM W3ID sign-in covers ISC, ZoomInfo, and Salesloft (all SSO through IBM). In this clone the login is mocked — only the email is kept locally, the password is discarded.</div>
      <div id="credRows"></div>
    </div>
  </div>
</div>

<script>

function esc(s){ return String(s==null?'':s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }

// Distill a raw log line ("2026-07-10 15:00:12,348 INFO [run] Uploading…") down
// to the human part ("Uploading…") — never a bare terminal dump.
function cleanLine(line){
  return String(line||'')
    .replace(/^\\d{4}-\\d\\d-\\d\\d[ T]\\d\\d:\\d\\d:\\d\\d[.,]\\d+\\s+/, '')
    .replace(/^(INFO|WARNING|WARN|ERROR|DEBUG)\\s+/, '')
    .replace(/^\\[[^\\]]+\\]\\s+/, '')
    .trim();
}

// ── auth gate ─────────────────────────────────────────────────
async function checkAuth(){
  let saved = {};
  try {
    const res = await fetch('/api/credentials/status');
    saved = await res.json();
  } catch(e) {}
  if (saved.w3id) startApp();
  else document.getElementById('loginGate').style.display = 'flex';
}

async function submitLogin(ev){
  ev.preventDefault();
  const email = document.getElementById('loginEmail').value.trim();
  const password = document.getElementById('loginPw').value;
  const errEl = document.getElementById('loginErr');
  const btn = document.getElementById('loginBtn');
  errEl.textContent = '';
  if (!email || !password){ errEl.textContent = 'Enter your IBM email and password.'; return; }
  btn.disabled = true; btn.textContent = 'Signing in…';
  try {
    const res = await fetch('/api/credentials/w3id', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({email, password}),
    });
    const body = await res.json();
    if (!body.ok){ errEl.textContent = body.error || 'Sign-in failed.'; return; }
    document.getElementById('loginPw').value = '';
    document.getElementById('loginGate').style.display = 'none';
    startApp();
  } finally {
    btn.disabled = false; btn.textContent = 'Sign in';
  }
}

// ── details modal ─────────────────────────────────────────────
function openDetails(){
  document.getElementById('detailsModal').classList.add('show');
  fetchLoginStatus(); fetchCredStatus(); fetchSeller();
}
function closeDetails(){
  document.getElementById('detailsModal').classList.remove('show');
}

// ── app boot ──────────────────────────────────────────────────
let _pollTimer = null;
function startApp(){
  document.getElementById('app').style.display = 'block';
  fetchStatus(); fetchSeller(); fetchLoginStatus(); fetchKpis();
  if (!_pollTimer) _pollTimer = setInterval(() => { fetchStatus(); fetchLoginStatus(); fetchKpis(); }, 2000);
}

// ── seller identity / territory ─────────────────────────────────
async function fetchSeller(){
  let d = {};
  try { d = await (await fetch('/api/seller')).json(); } catch(e){ return; }
  const el = document.getElementById('gmaSeller');
  const signed = document.getElementById('signedAs');
  const territory = document.getElementById('territoryBadge');
  if (d.signed_in && d.seller_name && d.covids){
    el.innerHTML = `Signed in as <b>${esc(d.seller_name)}</b> &middot; ${d.covids} coverage ID${d.covids===1?'':'s'}`;
    const industries = Object.keys(d.industries || {});
    territory.textContent = industries.length ? `${industries[0]} territory` : `${d.seller_name}'s territory`;
  } else if (d.signed_in && !d.matched){
    el.innerHTML = `Signed in as <b>${esc(d.email||'')}</b> — no matching territory found.`;
  } else {
    el.textContent = '';
  }
  if (signed){
    signed.innerHTML = d.signed_in
      ? `Signed in as <b>${esc(d.email||'')}</b>${d.seller_name ? ' &middot; ' + esc(d.seller_name) : ''}`
      : 'Not signed in.';
  }
}

// ── KPI hero row ────────────────────────────────────────────────
function fmtNum(n){ return (n === null || n === undefined) ? '—' : n.toLocaleString(); }
async function fetchKpis(){
  let k;
  try { k = await (await fetch('/api/kpis')).json(); } catch(e){ return; }
  document.getElementById('kpiAccounts').textContent = fmtNum(k.accounts_analyzed);
  document.getElementById('kpiTier1').textContent = fmtNum(k.tier1_accounts);
  document.getElementById('kpiContacts').textContent = fmtNum(k.contacts_staged);
  document.getElementById('kpiEmails').textContent = fmtNum(k.emails_generated);
  document.getElementById('kpiTime').textContent = (k.time_saved_hours === null || k.time_saved_hours === undefined)
    ? '—' : `${k.time_saved_hours} hrs`;
  document.getElementById('roiEmails').textContent = fmtNum(k.emails_generated);
}

// ── pipeline steps ──────────────────────────────────────────────
const GROUPS = {
  gma:      [['step1','ISC Scraper'],['ibm','IBM Scraper'],['segment','Segmentation']],
  strategy: [['step2','Account Tiering'],['step3','Call Planning']],
  fill:     [['step4','ZoomInfo'],['step5','Salesloft']],
};
const _openLogs = new Set();

function chipDotClass(s){
  if (!s) return 'pending';
  if (s.running) return 'running';
  if (s.state === 'done' || s.state === 'ran') return 'done';
  return 'pending';
}
function actDotClass(a){
  if (!a) return 'pending';
  if (a.error) return 'err';
  if (a.active) return 'running';
  if (a.done) return 'done';
  return 'pending';
}

function renderChips(key, data){
  const el = document.getElementById(key + 'Chips');
  el.innerHTML = GROUPS[key].map(([sk,label]) =>
    `<span class="pipe-chip"><span class="dot ${chipDotClass(data[sk])}"></span>${esc(label)}</span>`).join('');
}

function collectLog(key, data){
  const lines = [];
  for (const [sk] of GROUPS[key]){
    const tail = (data[sk] && data[sk].log_tail) || [];
    for (const l of tail){ const c = cleanLine(l); if (c) lines.push(c); }
  }
  return lines.slice(-60);
}

function updateAction(key, a, data, recordsHtml){
  const card = document.getElementById('card-' + key);
  card.classList.toggle('working', !!(a && a.active));
  card.classList.toggle('done', !!(a && a.done && !a.active));

  const status = document.getElementById(key + 'Status');
  const dotCls = actDotClass(a);
  const msg = (a && a.message) ? a.message : status.querySelector('.amsg').textContent;
  status.classList.toggle('err', dotCls === 'err');

  const logLines = collectLog(key, data);
  let sub = '';
  if (a && a.active && logLines.length){
    const live = logLines[logLines.length - 1];
    if (live && live !== msg) sub = `<br><span style="color:var(--text3);font-size:11.5px;">${esc(live)}</span>`;
  }
  status.innerHTML = `<span class="${a && a.active ? 'spinner' : 'dot ' + dotCls}"></span><span class="amsg">${esc(msg)}${sub}</span>`;

  const btn = document.getElementById(key + 'Btn');
  if (a && a.active){ btn.disabled = true; } else { btn.disabled = false; }

  const resultsEl = document.getElementById(key + 'Results');
  if (resultsEl) resultsEl.innerHTML = recordsHtml || '';
  renderChips(key, data);

  const toggle = document.getElementById(key + 'LogToggle');
  const logEl = document.getElementById(key + 'Log');
  if (logLines.length){
    toggle.style.display = '';
    const open = _openLogs.has(key);
    logEl.classList.toggle('show', open);
    logEl.innerHTML = logLines.map(l => `<div>${esc(l)}</div>`).join('');
    toggle.textContent = open ? 'Hide details' : 'Show details';
    if (open) logEl.scrollTop = logEl.scrollHeight;
  } else {
    toggle.style.display = 'none';
    logEl.classList.remove('show');
    logEl.innerHTML = '';
  }
}

function toggleLog(key){
  if (_openLogs.has(key)) _openLogs.delete(key); else _openLogs.add(key);
  const logEl = document.getElementById(key + 'Log');
  const open = _openLogs.has(key);
  logEl.classList.toggle('show', open);
  document.getElementById(key + 'LogToggle').textContent = open ? 'Hide details' : 'Show details';
  if (open) logEl.scrollTop = logEl.scrollHeight;
}

async function fetchStatus(){
  let data;
  try { data = await (await fetch('/api/status')).json(); } catch(e){ return; }
  const acts = data._actions || {};

  const gmaDone = data.segment && data.segment.state === 'done';
  const gmaRecords = gmaDone
    ? `${data.segment.rows ?? '—'} accounts &middot; <a class="link" href="/view/segment" target="_blank">View &#8599;</a>` : '';
  updateAction('gma', acts.get_my_accounts, data, gmaRecords);

  const stratDone = (data.step2 && data.step2.state === 'done') || (data.step3 && data.step3.state === 'done');
  const stratRecords = stratDone
    ? `${data.step2 && data.step2.rows != null ? data.step2.rows + ' tiered &middot; ' : ''}<a class="link" href="/view/strategy" target="_blank">View &#8599;</a>` : '';
  updateAction('strategy', acts.outbound_strategy, data, stratRecords);

  const fillDone = acts.fill_contacts && acts.fill_contacts.done;
  const fillRecords = fillDone
    ? `<a class="link" href="/view/fill" target="_blank">View &#8599;</a>` : '';
  updateAction('fill', acts.fill_contacts, data, fillRecords);
  updateBobby(acts.bobby);
}

function updateBobby(a){
  const card = document.getElementById('card-bobby');
  const status = document.getElementById('bobbyStatus');
  const btn = document.getElementById('bobbyBtn');
  const dotCls = actDotClass(a);
  card.classList.toggle('working', !!(a && a.active));
  card.classList.toggle('done', !!(a && a.done && !a.active));
  status.classList.toggle('err', dotCls === 'err');
  const msg = (a && a.message) ? a.message : status.querySelector('.amsg').textContent;
  const open = (a && (a.active || a.done || a.error))
    ? ` <a class="link" href="/bobby">Open Bobby &#8599;</a>` : '';
  status.innerHTML = `<span class="${a && a.active ? 'spinner' : 'dot ' + dotCls}"></span><span class="amsg">${esc(msg)}${open}</span>`;
  if (btn) btn.disabled = !!(a && a.active);
}
async function runBobby(){
  const el = document.querySelector('input[name="bobbyCadence"]:checked');
  if (!el){ alert('Pick a cadence for Bobby.'); return; }
  const res = await fetch('/api/bobby/run', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({cadence: el.value}),
  });
  const body = await res.json();
  if (!body.ok){ alert('Error: ' + body.error); return; }
  window.location.href = '/bobby';
}

async function runGetMyAccounts(){
  const res = await fetch('/api/get_my_accounts/run', {method:'POST'});
  const body = await res.json();
  if (!body.ok) alert('Error: ' + body.error);
  fetchStatus();
}
async function runStrategy(){
  const res = await fetch('/api/outbound_strategy/run', {method:'POST'});
  const body = await res.json();
  if (!body.ok) alert('Error: ' + body.error);
  fetchStatus();
}
async function runFill(){
  const cadence = document.getElementById('fillCadence').value;
  const res = await fetch('/api/fill_contacts/run', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({cadence}),
  });
  const body = await res.json();
  if (!body.ok) alert('Error: ' + body.error);
  fetchStatus();
}

// ── sessions + saved password (Access, in Details) ────────────
const LOGIN_LABELS = {isc:'ISC', zoominfo:'ZoomInfo', salesloft:'Salesloft'};
const LOGIN_ORDER = ['isc','zoominfo','salesloft'];
function openMockTool(service){ window.open('/mock/' + service, '_blank'); }
let _loginState = {};

async function fetchLoginStatus(){
  let data;
  try { data = await (await fetch('/api/login/status')).json(); } catch(e){ return; }
  _loginState = data;
  const container = document.getElementById('loginRows');
  const BADGE_TEXT = {ready:'logged in', expired:'session expired', checking:'checking…',
                      error:'check failed', missing:'not logged in', waiting:'waiting'};
  container.innerHTML = '';
  for (const svc of LOGIN_ORDER){
    const s = _loginState[svc] || {state:'missing'};
    let action = '';
    if (s.state === 'ready') action = `<button class="btn" onclick="openMockTool('${svc}')">Open ${LOGIN_LABELS[svc]} &#8599;</button>`;
    else if (s.state === 'checking') action = 'probing saved session…';
    else if (s.state === 'waiting') action = `check the browser window, log in, then <button class="btn" onclick="confirmLogin('${svc}')">Confirm logged in</button>`;
    else if (s.state === 'expired') action = `saved session no longer works <button class="btn" onclick="startLogin('${svc}')">Re-log in</button>`;
    else if (s.state === 'error') action = `could not verify (network?) <button class="btn" onclick="startLogin('${svc}')">Re-log in</button>`;
    else action = `<button class="btn" onclick="startLogin('${svc}')">Log in</button>`;
    const row = document.createElement('div');
    row.className = 'lrow';
    row.innerHTML = `<span class="svc">${LOGIN_LABELS[svc]}</span>`
      + `<span class="pill ${s.state}"><span class="dot"></span>${BADGE_TEXT[s.state] || s.state}</span>`
      + `<span class="fill">${action}</span>`;
    container.appendChild(row);
  }
  const needLogin = LOGIN_ORDER.filter(svc => {
    const st = (_loginState[svc] || {}).state;
    return st === 'expired' || st === 'missing' || st === 'error';
  });
  const alertEl = document.getElementById('loginAlert');
  if (needLogin.length){
    alertEl.textContent = 'Needs login: ' + needLogin.map(s => LOGIN_LABELS[s]).join(', ')
      + ' — those steps can\\'t run until re-authenticated.';
    alertEl.classList.add('show');
  } else {
    alertEl.classList.remove('show');
  }
  document.getElementById('detailsWarn').style.display = needLogin.length ? '' : 'none';
}

async function startLogin(service){
  const res = await fetch(`/api/login/${service}/start`, {method:'POST'});
  const body = await res.json();
  if (!body.ok){ alert('Error: ' + body.error); return; }
  if (body.mock_url) window.open(body.mock_url, '_blank');
  fetchLoginStatus();
}
async function confirmLogin(service){
  await fetch(`/api/login/${service}/confirm`, {method:'POST'});
  fetchLoginStatus();
}

const CRED_LABELS = {w3id:'IBM W3ID (ISC, ZoomInfo, Salesloft — all SSO through IBM)'};
async function fetchCredStatus(){
  let saved;
  try { saved = await (await fetch('/api/credentials/status')).json(); } catch(e){ return; }
  const container = document.getElementById('credRows');
  container.innerHTML = '';
  for (const key of ['w3id']){
    const isSaved = !!saved[key];
    const div = document.createElement('div');
    div.style.margin = '10px 0 4px';
    div.innerHTML =
      `<div style="font-size:13px;display:flex;align-items:center;gap:10px;margin-bottom:8px;"><span style="font-weight:500;">${CRED_LABELS[key]}</span>`
      + `<span class="pill ${isSaved ? 'ready' : ''}"><span class="dot"></span>${isSaved ? 'saved' : 'not saved'}</span></div>`
      + `<input type="text" id="cred-email-${key}" placeholder="email / username" style="min-width:220px;">`
      + `<input type="password" id="cred-pw-${key}" placeholder="password" style="min-width:180px;">`
      + `<button class="btn primary" onclick="saveCredential('${key}')">${isSaved ? 'Update' : 'Save'}</button>`;
    container.appendChild(div);
  }
}
async function saveCredential(key){
  const email = document.getElementById('cred-email-' + key).value;
  const password = document.getElementById('cred-pw-' + key).value;
  if (!email || !password){ alert('Enter both email and password.'); return; }
  const res = await fetch('/api/credentials/' + key, {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({email, password}),
  });
  const body = await res.json();
  if (!body.ok){ alert('Error: ' + body.error); return; }
  document.getElementById('cred-pw-' + key).value = '';
  fetchCredStatus(); fetchSeller();
}

window.__today = "{{ today }}";
checkAuth();
</script>
</body>
</html>
"""


VIEW_TEMPLATE = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>{{ title }} — Results</title>
""" + _FONTS + """
<style>
""" + _DESIGN_CSS + """
  body{ padding:36px 32px 80px; }
  h1{ font-size:22px; margin:0 0 6px; }
  .meta{ color:var(--text3); font-size:13px; margin-bottom:18px; }
  input#filter{ font-size:13.5px; padding:9px 14px; width:320px; margin-bottom:16px; }
  tr.hidden{ display:none; }
</style>
</head>
<body>
<h1>{{ title }}</h1>
<div class="meta">{{ path }} — {{ row_count }} row(s). Click a column header to sort.</div>
<input id="filter" type="text" placeholder="Filter rows (any column)..." oninput="filterRows()">
<table id="tbl">
<thead><tr>{% for h in header %}<th onclick="sortByCol({{ loop.index0 }})">{{ h }}</th>{% endfor %}</tr></thead>
<tbody>
{% for row in rows %}
<tr>{% for cell in row %}<td>{{ cell if cell is not none else '' }}</td>{% endfor %}</tr>
{% endfor %}
</tbody>
</table>
<script>
function filterRows() {
  const q = document.getElementById('filter').value.toLowerCase();
  document.querySelectorAll('#tbl tbody tr').forEach(tr => {
    tr.classList.toggle('hidden', q && !tr.textContent.toLowerCase().includes(q));
  });
}
let sortDir = {};
function sortByCol(colIdx) {
  const tbody = document.querySelector('#tbl tbody');
  const rows = Array.from(tbody.querySelectorAll('tr'));
  sortDir[colIdx] = !sortDir[colIdx];
  rows.sort((a, b) => {
    const av = a.children[colIdx].textContent, bv = b.children[colIdx].textContent;
    const an = parseFloat(av), bn = parseFloat(bv);
    let cmp = (!isNaN(an) && !isNaN(bn)) ? an - bn : av.localeCompare(bv);
    return sortDir[colIdx] ? cmp : -cmp;
  });
  rows.forEach(r => tbody.appendChild(r));
}
</script>
</body>
</html>
"""


STEP1_VIEW_TEMPLATE = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Accounts — BobBee</title>
""" + _FONTS + """
<style>
""" + _DESIGN_CSS + """
  body{ padding:36px 32px 90px; }
  .wrap{ max-width:1180px; margin:0 auto; }
  h1{ font-size:22px; margin:0 0 6px; }
  .meta{ color:var(--text3); font-size:13px; margin-bottom:22px; }
  .summary{ display:grid; grid-template-columns:repeat(3,1fr); gap:14px; margin-bottom:26px; }
  .sc{ background:var(--layer1); border:1px solid var(--border); border-radius:var(--r-lg); padding:18px 20px; }
  .sc .v{ font-family:var(--mono); font-size:26px; font-weight:600; }
  .sc .l{ color:var(--text3); font-size:12px; margin-top:7px; }
  .tierbox{ background:var(--layer1); border:1px solid var(--border); border-radius:var(--r-lg); padding:20px 22px; margin-bottom:26px; }
  .tierbox h3{ font-size:13.5px; margin-bottom:14px; }
  .tierbox .empty{ color:var(--text3); font-size:13px; }
  .trow{ display:flex; align-items:center; gap:12px; margin-bottom:10px; }
  .trow:last-child{ margin-bottom:0; }
  .trow .tl{ width:56px; flex:none; font-size:12.5px; color:var(--text2); }
  .trow .track{ flex:1; height:8px; background:var(--layer2); border-radius:4px; overflow:hidden; }
  .trow .fill{ height:100%; border-radius:4px; }
  .trow .fill.t1{ background:var(--blue); } .trow .fill.t2{ background:var(--blue-text); } .trow .fill.t3{ background:var(--text3); }
  .trow .tc{ width:34px; text-align:right; font-family:var(--mono); font-size:12.5px; }
  input#filter{ font-size:13.5px; padding:9px 14px; width:320px; margin-bottom:16px; }
  td.tier{ font-family:var(--mono); }
  tr.hidden{ display:none; }
</style>
</head>
<body>
<div class="wrap">
<h1>Your accounts</h1>
<div class="meta">{{ path }} — {{ total }} accounts pulled and segmented.</div>

<div class="summary">
  <div class="sc"><div class="v">{{ total }}</div><div class="l">Accounts pulled</div></div>
  <div class="sc"><div class="v">{{ install_matches }}</div><div class="l">Install base matches</div></div>
  <div class="sc"><div class="v">{{ competitor_count }}</div><div class="l">Accounts with competitor presence</div></div>
</div>

<div class="tierbox">
  <h3>Tier breakdown</h3>
  {% if tiered %}
  <div class="trow"><span class="tl">Tier 1</span><span class="track"><span class="fill t1" style="width:{{ (tier_counts[1] / total * 100) if total else 0 }}%"></span></span><span class="tc">{{ tier_counts[1] }}</span></div>
  <div class="trow"><span class="tl">Tier 2</span><span class="track"><span class="fill t2" style="width:{{ (tier_counts[2] / total * 100) if total else 0 }}%"></span></span><span class="tc">{{ tier_counts[2] }}</span></div>
  <div class="trow"><span class="tl">Tier 3</span><span class="track"><span class="fill t3" style="width:{{ (tier_counts[3] / total * 100) if total else 0 }}%"></span></span><span class="tc">{{ tier_counts[3] }}</span></div>
  {% else %}
  <div class="empty">Not scored yet — run Strategy (Step 2) to tier these accounts.</div>
  {% endif %}
</div>

<input id="filter" type="text" placeholder="Filter accounts..." oninput="filterRows()">
<table id="tbl">
<thead><tr>
  <th onclick="sortByCol(0)">Account name</th>
  <th onclick="sortByCol(1)">Industry</th>
  <th onclick="sortByCol(2)">Install base</th>
  <th onclick="sortByCol(3)">Spend trend</th>
  <th onclick="sortByCol(4)">Competitor</th>
  <th onclick="sortByCol(5,true)">Tier</th>
</tr></thead>
<tbody>
{% for r in rows %}
<tr>
  <td>{{ r.account }}</td>
  <td>{{ r.industry }}</td>
  <td>{{ r.install }}</td>
  <td>{{ r.spend_trend }}</td>
  <td>{{ r.competitor }}</td>
  <td class="tier">{{ 'T' + r.tier|string if r.tier else 'Pending' }}</td>
</tr>
{% endfor %}
</tbody>
</table>
</div>
<script>
function filterRows() {
  const q = document.getElementById('filter').value.toLowerCase();
  document.querySelectorAll('#tbl tbody tr').forEach(tr => {
    tr.classList.toggle('hidden', q && !tr.textContent.toLowerCase().includes(q));
  });
}
let sortDir = {};
function sortByCol(colIdx, numeric) {
  const tbody = document.querySelector('#tbl tbody');
  const rows = Array.from(tbody.querySelectorAll('tr'));
  sortDir[colIdx] = !sortDir[colIdx];
  rows.sort((a, b) => {
    const av = a.children[colIdx].textContent.trim(), bv = b.children[colIdx].textContent.trim();
    let cmp;
    if (numeric) cmp = (parseFloat(av.replace(/[^0-9.\\-]/g,''))||0) - (parseFloat(bv.replace(/[^0-9.\\-]/g,''))||0);
    else cmp = av.localeCompare(bv);
    return sortDir[colIdx] ? cmp : -cmp;
  });
  rows.forEach(r => tbody.appendChild(r));
}
</script>
</body>
</html>
"""


TIER_VIEW_TEMPLATE = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Account Tiering — BobBee</title>
""" + _FONTS + """
<style>
""" + _DESIGN_CSS + """
  body{ padding:36px 32px 90px; }
  h1{ font-size:22px; margin:0 0 6px; }
  .meta{ color:var(--text3); font-size:13px; margin-bottom:16px; }
  .legend{ display:flex; gap:10px; flex-wrap:wrap; margin-bottom:16px; }
  .chip{ font-size:12.5px; font-weight:600; padding:7px 14px; border-radius:var(--r-sm); cursor:pointer; border:1px solid transparent; user-select:none; transition:opacity .15s; }
  .chip.off{ opacity:.35; }
  .chip.c1{ background:rgba(66,190,101,.14); color:var(--green); border-color:rgba(66,190,101,.3); }
  .chip.c2{ background:var(--blue-soft); color:var(--blue-text); border-color:var(--blue-border); }
  .chip.c3{ background:var(--layer2); color:var(--text2); border-color:var(--border); }
  input#filter{ font-size:13.5px; padding:9px 14px; width:300px; margin-bottom:16px; }
  th,td{ padding:9px 11px; }
  td.num{ font-variant-numeric:tabular-nums; font-family:var(--mono); white-space:nowrap; }
  tr.hidden{ display:none; }
  tr.t1 td{ background:rgba(66,190,101,.04); }
  tr.t2 td{ background:rgba(91,150,255,.04); }
  .tb{ display:inline-block; min-width:26px; text-align:center; font-weight:700; font-size:10.5px; padding:3px 7px; border-radius:var(--r-sm); font-family:var(--mono); }
  .tb1{ background:var(--green); color:#0a1f10; } .tb2{ background:var(--blue); color:#fff; } .tb3{ background:var(--text3); color:#0a0a0c; }
  .acct{ font-weight:600; color:var(--text1); max-width:220px; white-space:normal; }
  /* AI-generated columns — purple, sparkle, distinct from deterministic blue data */
  .ai-cell{ background:var(--purple-soft); }
  .play-badge{ display:inline-flex; align-items:center; gap:5px; font-size:11px; font-weight:600; padding:3px 9px; border-radius:var(--r-sm);
               background:rgba(138,63,252,.18); color:var(--purple-text); white-space:nowrap; }
  .angle{ color:var(--text1); max-width:320px; white-space:normal; line-height:1.5; font-size:12.5px; }
  .granite-tag{ display:inline-flex; align-items:center; gap:4px; font-size:10px; color:var(--purple-text); margin-top:4px; opacity:.85; }
  .tr-up{ color:var(--green); font-weight:600; } .tr-down{ color:var(--red); font-weight:600; }
  .tr-new{ color:var(--purple-text); font-weight:600; } .tr-flat,.tr-unknown{ color:var(--text3); }
  .comp-yes{ color:var(--purple-text); font-weight:600; }
</style>
</head>
<body>
{% set PLAY_CLS = {'Expand & Protect':'p-expand','Displace Competitor':'p-displace','Hardware Refresh':'p-refresh','Land New Logo':'p-land','Win-Back':'p-winback','Nurture':'p-nurture'} %}
{% set TREND = {'Growing':['&#9650;','tr-up'],'Declining':['&#9660;','tr-down'],'Lapsed':['&#9660;','tr-down'],'New':['&#10022;','tr-new'],'Flat':['&#9644;','tr-flat'],'Unknown':['&ndash;','tr-unknown']} %}
<h1>Account tiering</h1>
<div class="meta">{{ path }} — {{ total }} accounts, sorted best-first. Score/Tier are deterministic; Play/Angle are """ + _SPARKLE + """generated by Granite.</div>
<div class="legend">
  <span class="chip c1" data-tier="1" onclick="toggleTier(this)">Tier 1 &middot; {{ counts[1] }}</span>
  <span class="chip c2" data-tier="2" onclick="toggleTier(this)">Tier 2 &middot; {{ counts[2] }}</span>
  <span class="chip c3" data-tier="3" onclick="toggleTier(this)">Tier 3 &middot; {{ counts[3] }}</span>
</div>
<input id="filter" type="text" placeholder="Filter (account, industry, play...)" oninput="filterRows()">
<table id="tbl">
<thead><tr>
  <th onclick="sortByCol(0,true)">#</th>
  <th onclick="sortByCol(1,true)">Tier</th>
  <th onclick="sortByCol(2)">Account</th>
  <th onclick="sortByCol(3)">Industry</th>
  <th onclick="sortByCol(4)">""" + _SPARKLE + """Granite play</th>
  <th onclick="sortByCol(5,true)">Score</th>
  <th onclick="sortByCol(6)">Relationship</th>
  <th onclick="sortByCol(7)">Spend trend</th>
  <th onclick="sortByCol(8)">IBM spend</th>
  <th onclick="sortByCol(9)">Revenue</th>
  <th onclick="sortByCol(10)">Employees</th>
  <th onclick="sortByCol(11)">IBM install</th>
  <th onclick="sortByCol(12)">Competitor</th>
  <th onclick="sortByCol(13)">Contacts</th>
  <th onclick="sortByCol(14)">""" + _SPARKLE + """Granite sales angle</th>
</tr></thead>
<tbody>
{% for r in rows %}
<tr class="t{{ r.tier }}" data-tier="{{ r.tier }}">
  <td class="num">{{ r.rank }}</td>
  <td><span class="tb tb{{ r.tier }}">T{{ r.tier }}</span></td>
  <td class="acct">{{ r.account }}</td>
  <td>{{ r.industry }}</td>
  <td class="ai-cell"><span class="play-badge">{{ r.play }}</span></td>
  <td class="num">{{ '%.1f'|format(r.score|float) if r.score is not none else '—' }}</td>
  <td>{{ r.relationship }}</td>
  <td class="{{ TREND.get(r.trend,['','tr-unknown'])[1] }}">{{ TREND.get(r.trend,['&ndash;',''])[0]|safe }} {{ r.trend }}</td>
  <td class="num">{{ r.spend }}</td>
  <td class="num">{{ r.revenue }}</td>
  <td class="num">{{ r.employees }}</td>
  <td>{{ r.install }}</td>
  <td class="{{ 'comp-yes' if r.competitor.startswith('Yes') else '' }}">{{ r.competitor }}</td>
  <td class="num">{{ r.contacts }}</td>
  <td class="ai-cell angle">{{ r.angle }}<div class="granite-tag">""" + _SPARKLE + """Generated by Granite</div></td>
</tr>
{% endfor %}
</tbody>
</table>
<script>
const hiddenTiers = new Set();
function toggleTier(el){
  const t = el.dataset.tier;
  if (hiddenTiers.has(t)) { hiddenTiers.delete(t); el.classList.remove('off'); }
  else { hiddenTiers.add(t); el.classList.add('off'); }
  filterRows();
}
function filterRows(){
  const q = document.getElementById('filter').value.toLowerCase();
  document.querySelectorAll('#tbl tbody tr').forEach(tr => {
    const hideTier = hiddenTiers.has(tr.dataset.tier);
    const hideText = q && !tr.textContent.toLowerCase().includes(q);
    tr.classList.toggle('hidden', hideTier || hideText);
  });
}
let sortDir = {};
function sortByCol(colIdx, numeric){
  const tbody = document.querySelector('#tbl tbody');
  const rows = Array.from(tbody.querySelectorAll('tr'));
  sortDir[colIdx] = !sortDir[colIdx];
  rows.sort((a,b) => {
    let av = a.children[colIdx].textContent.trim(), bv = b.children[colIdx].textContent.trim();
    let cmp;
    if (numeric) { cmp = (parseFloat(av.replace(/[^0-9.\\-]/g,''))||0) - (parseFloat(bv.replace(/[^0-9.\\-]/g,''))||0); }
    else { cmp = av.localeCompare(bv); }
    return sortDir[colIdx] ? cmp : -cmp;
  });
  rows.forEach(r => tbody.appendChild(r));
}
</script>
</body>
</html>
"""


CALENDAR_TEMPLATE = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Call Planning — BobBee</title>
""" + _FONTS + """
<style>
""" + _DESIGN_CSS + """
  body{ padding:36px 32px 90px; }
  .wrap{ max-width:800px; margin:0 auto; }
  h1{ font-size:22px; margin:0 0 6px; }
  .meta{ color:var(--text3); font-size:13px; margin-bottom:16px; }
  .note{ background:var(--blue-soft); border:1px solid var(--blue-border); border-radius:var(--r-md); padding:14px 18px;
         margin-bottom:20px; font-size:13.5px; line-height:1.5; color:var(--blue-text); }
  .stats{ display:flex; gap:10px; flex-wrap:wrap; margin-bottom:24px; }
  .stat{ background:var(--layer1); border:1px solid var(--border); border-radius:var(--r-md); padding:9px 15px; font-size:12.5px; }
  .stat b{ font-weight:600; font-size:14px; font-family:var(--mono); }
  .week{ margin-bottom:26px; }
  .week h2{ font-size:13px; color:var(--text3); font-weight:600; margin-bottom:12px; text-transform:none; }
  .day{ display:flex; gap:18px; padding:13px 0; border-top:1px solid var(--border); }
  .day:first-child{ border-top:none; }
  .day .dname{ width:100px; flex:none; font-weight:600; font-size:13.5px; padding-top:2px; }
  .accts{ flex:1; display:flex; flex-wrap:wrap; gap:8px; }
  .achip{ background:var(--layer1); border:1px solid var(--border); border-radius:var(--r-sm); padding:8px 13px 8px 11px;
          font-size:12.5px; display:flex; align-items:center; gap:8px; border-left:3px solid var(--text3); }
  .achip.t1{ border-left-color:var(--green); } .achip.t2{ border-left-color:var(--blue); } .achip.t3{ border-left-color:var(--text3); }
  .achip .n{ font-weight:500; color:var(--text1); }
  .achip .p{ color:var(--text3); font-size:11px; }
  .empty{ color:var(--text3); font-size:14px; text-align:center; padding:60px 0; }
</style>
</head>
<body>
<div class="wrap">
<h1>Call planning timeline</h1>
<div class="meta">{{ path }} — {{ total }} accounts scheduled through year-end.</div>
{% if meta.summary %}<div class="note">{{ meta.summary }}</div>{% endif %}
<div class="stats">
  <div class="stat"><b>{{ total }}</b> accounts</div>
  {% if meta.per_day %}<div class="stat">up to <b>{{ meta.per_day }}</b> / day</div>{% endif %}
  {% if meta.used_days %}<div class="stat"><b>{{ meta.used_days }}</b> active days</div>{% endif %}
  {% if meta.working_days %}<div class="stat"><b>{{ meta.working_days }}</b> working days to Dec 31</div>{% endif %}
</div>

{% if weeks %}
{% for w in weeks %}
<div class="week">
  <h2>{{ w.label }}</h2>
  {% for d in w.days %}
  <div class="day">
    <div class="dname">{{ d.label }}</div>
    <div class="accts">
      {% for a in d.accounts %}
      <span class="achip t{{ a.tier }}"><span class="n">{{ a.name }}</span>{% if a.play %}<span class="p">{{ a.play }}</span>{% endif %}</span>
      {% endfor %}
    </div>
  </div>
  {% endfor %}
</div>
{% endfor %}
{% else %}
<div class="empty">No calls scheduled yet.</div>
{% endif %}
</div>
</body>
</html>
"""


STRATEGY_TEMPLATE = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Outbound Strategy — BobBee</title>
""" + _FONTS + """
<style>
""" + _DESIGN_CSS + """
  html,body{ height:100%; }
  body{ display:flex; flex-direction:column; height:100vh; }
  header{ padding:20px 32px 0; }
  h1{ font-size:20px; margin:0 0 12px; }
  .tabs{ display:flex; gap:6px; border-bottom:1px solid var(--border); }
  .tab{ font:inherit; font-size:13.5px; font-weight:600; color:var(--text3); background:none; border:none; cursor:pointer;
        padding:10px 16px; border-bottom:2px solid transparent; margin-bottom:-1px; transition:color .15s; }
  .tab:hover{ color:var(--text1); }
  .tab.active{ color:var(--blue-text); border-bottom-color:var(--blue-text); }
  .frames{ flex:1; min-height:0; position:relative; }
  iframe{ position:absolute; inset:0; width:100%; height:100%; border:none; display:none; }
  iframe.active{ display:block; }
  .missing{ display:none; color:var(--text3); font-size:14.5px; padding:40px 32px; }
  .missing.active{ display:block; }
</style>
</head>
<body>
<header>
  <h1>Outbound strategy</h1>
  <div class="tabs">
    <button class="tab active" onclick="showTab('tier')">Account tiering</button>
    <button class="tab" onclick="showTab('plan')">Call planning</button>
  </div>
</header>
<div class="frames">
  {% if has_tier %}<iframe id="f-tier" class="active" src="/view/step2"></iframe>
  {% else %}<div id="f-tier" class="missing active">Account tiering hasn't run yet — click Strategy first.</div>{% endif %}
  {% if has_plan %}<iframe id="f-plan" src="/view/step3"></iframe>
  {% else %}<div id="f-plan" class="missing">Call planning hasn't run yet — click Strategy first.</div>{% endif %}
</div>
<script>
function showTab(which){
  for (const t of ['tier','plan']){
    document.getElementById('f-' + t).classList.toggle('active', t === which);
  }
  document.querySelectorAll('.tab').forEach((b,i) => b.classList.toggle('active', i === (which === 'tier' ? 0 : 1)));
}
</script>
</body>
</html>
"""


FILL_VIEW_TEMPLATE = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Contacts — BobBee</title>
""" + _FONTS + """
<style>
""" + _DESIGN_CSS + """
  body{ padding:36px 32px 90px; }
  .wrap{ max-width:900px; margin:0 auto; }
  h1{ font-size:22px; margin:0 0 6px; }
  .meta{ color:var(--text3); font-size:13px; margin-bottom:28px; }
  .funnel{ display:flex; flex-direction:column; align-items:center; gap:4px; margin-bottom:32px; }
  .fstage{ width:100%; max-width:460px; background:var(--layer1); border:1px solid var(--border); border-radius:var(--r-lg);
           padding:16px 22px; display:flex; align-items:center; justify-content:space-between; }
  .fstage .fl{ font-size:13.5px; color:var(--text2); }
  .fstage .fv{ font-family:var(--mono); font-size:22px; font-weight:600; color:var(--text1); }
  .farrow{ color:var(--text3); font-size:16px; }
  .cards{ display:grid; grid-template-columns:repeat(auto-fill,minmax(260px,1fr)); gap:12px; }
  .ccard{ background:var(--layer1); border:1px solid var(--border); border-radius:var(--r-md); padding:14px 16px; }
  .ccard .cn{ font-weight:600; font-size:14px; }
  .ccard .ct{ color:var(--text2); font-size:12.5px; margin:3px 0 8px; }
  .ccard .cs{ display:inline-flex; align-items:center; gap:5px; font-size:11px; color:var(--green); }
</style>
</head>
<body>
<div class="wrap">
<h1>Contacts staged</h1>
<div class="meta">Cadence: {{ cadence }}</div>

<div class="funnel">
  <div class="fstage"><span class="fl">Accounts touched</span><span class="fv">{{ account_count }}</span></div>
  <div class="farrow">&darr;</div>
  <div class="fstage"><span class="fl">Contacts identified (ZoomInfo)</span><span class="fv">{{ contact_count }}</span></div>
  <div class="farrow">&darr;</div>
  <div class="fstage"><span class="fl">Salesloft ready</span><span class="fv">{{ contact_count }}</span></div>
</div>

<div class="cards">
  {% for m in members %}
  <div class="ccard">
    <div class="cn">{{ m.first_name }} {{ m.last_name }}</div>
    <div class="ct">{{ m.title }}{% if m.title and m.company %} &middot; {% endif %}{{ m.company }}</div>
    <span class="cs"><span class="dot done"></span>{{ m.step }}</span>
  </div>
  {% endfor %}
</div>
</div>
</body>
</html>
"""


BOBBY_PAGE_TEMPLATE = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Bobby AI — BobBee</title>
""" + _FONTS + """
<style>
""" + _DESIGN_CSS + """
  body{ padding:0 0 100px; }
  .top{ position:sticky; top:0; z-index:20; background:rgba(10,10,12,.9); backdrop-filter:saturate(160%) blur(16px);
        border-bottom:1px solid var(--border); padding:16px 28px; display:flex; align-items:center; gap:18px; }
  .top .grow{ flex:1; min-width:0; }
  .top h1{ font-size:17px; display:flex; align-items:center; gap:7px; }
  .top .sub{ color:var(--text3); font-size:12.5px; margin-top:2px; }
  .top .sub b{ color:var(--text2); }
  .back{ color:var(--blue-text); font-size:13px; text-decoration:none; font-weight:400; margin-left:8px; }
  .wrap{ max-width:1320px; margin:0 auto; padding:24px 28px; }
  .banner{ border-radius:var(--r-md); padding:12px 16px; margin-bottom:18px; font-size:13.5px; line-height:1.5; }
  .banner.run{ background:var(--blue-soft); color:var(--blue-text); }
  .banner.err{ background:rgba(250,77,86,.12); color:#ff8790; }
  .banner.ok{ background:var(--purple-soft); color:var(--purple-text); }

  .stephead{ display:flex; align-items:center; gap:12px; margin:24px 0 12px; }
  .stephead .badge-step{ font-size:11px; font-weight:600; color:var(--text2); background:var(--layer2); padding:4px 10px; border-radius:var(--r-sm); }
  .stephead h2{ font-size:15px; }
  .stephead .cnt{ color:var(--text3); font-size:12.5px; }

  .hero{ display:grid; grid-template-columns:260px 1fr 280px; gap:16px; margin-bottom:8px; }
  .hpanel{ background:var(--layer1); border:1px solid var(--border); border-radius:var(--r-lg); padding:18px 20px; }
  .hpanel h3{ font-size:11.5px; color:var(--text3); font-weight:600; margin-bottom:14px; }

  .contact-name{ font-size:17px; font-weight:600; }
  .contact-role{ color:var(--text2); font-size:13px; margin-top:2px; }
  .contact-co{ color:var(--text3); font-size:12.5px; margin-top:1px; }
  .signals{ margin-top:18px; display:flex; flex-direction:column; gap:9px; }
  .signal{ display:flex; align-items:center; gap:8px; font-size:12.5px; color:var(--text2); }
  .signal svg{ width:13px; height:13px; color:var(--green); flex:none; }
  .granite-badge{ margin-top:18px; display:inline-flex; align-items:center; gap:6px; font-size:11.5px; font-weight:500;
                  color:var(--purple-text); background:var(--purple-soft); border:1px solid var(--purple-border);
                  padding:6px 12px; border-radius:var(--r-sm); }

  .email-card{ border:1px solid var(--purple-border); box-shadow:0 0 0 1px var(--purple-border), 0 12px 28px rgba(138,63,252,.1); }
  .email-field{ margin-bottom:14px; }
  .email-field .fl{ font-size:11px; color:var(--text3); margin-bottom:5px; }
  .email-subject{ font-size:14.5px; font-weight:600; color:var(--text1); }
  .email-body{ white-space:pre-wrap; font-size:13.5px; line-height:1.6; color:var(--text1); }
  .email-sig{ color:var(--text3); font-size:12.5px; margin-top:10px; }

  .telemetry-row{ display:flex; justify-content:space-between; align-items:center; padding:9px 0; border-top:1px solid var(--border); font-size:12.5px; }
  .telemetry-row:first-child{ border-top:none; }
  .telemetry-row .tl{ color:var(--text2); }
  .telemetry-row .tv{ font-family:var(--mono); color:var(--text1); }
  .telemetry-row .tv.ok{ color:var(--green); }
  .telemetry-row .tv.warn{ color:var(--amber); }

  .grid{ display:grid; grid-template-columns:repeat(auto-fill,minmax(430px,1fr)); gap:14px; }
  .card{ padding:16px 18px; }
  .who{ display:flex; align-items:baseline; justify-content:space-between; gap:10px; cursor:pointer; }
  .who .name{ font-size:15px; font-weight:600; }
  .who .by{ font-size:10px; font-weight:600; color:var(--green); background:rgba(66,190,101,.13); padding:3px 9px; border-radius:var(--r-sm); white-space:nowrap; }
  .who .by.tmpl{ color:var(--text3); background:var(--layer2); }
  .role{ color:var(--text2); font-size:12.5px; margin:3px 0 10px; }
  .subj{ font-weight:600; font-size:13px; margin-bottom:8px; }
  .subj span{ color:var(--text3); font-weight:400; }
  .body{ white-space:pre-wrap; font-size:12.5px; line-height:1.55; color:var(--text2); border-top:1px solid var(--border); padding-top:10px; }
  .empty{ color:var(--text3); font-size:14px; padding:40px 0; }

  .btn{ width:auto; }
  .btn.primary{ background:linear-gradient(135deg,var(--blue),var(--purple)); border:none; }
  .btn.primary:hover{ filter:brightness(1.1); }
  .btn.primary:disabled{ background:var(--layer1); border:1px solid var(--border); }
  @media(max-width:1050px){ .hero{ grid-template-columns:1fr; } }
</style>
</head>
<body>
<div class="top">
  <div class="grow">
    <h1>""" + _SPARKLE + """Bobby AI<a class="back" href="/">&larr; Dashboard</a></h1>
    <div class="sub" id="sub">Starting…</div>
  </div>
  <button class="btn primary big" id="sendBtn" onclick="sendAll()" disabled style="width:auto;">Send all</button>
</div>
<div class="wrap">
  <div id="banner"></div>

  <div class="hero" id="hero" style="display:none">
    <div class="hpanel">
      <h3>Contact</h3>
      <div class="contact-name" id="hName">—</div>
      <div class="contact-role" id="hTitle"></div>
      <div class="contact-co" id="hCompany"></div>
      <div class="signals" id="hSignals"></div>
      <div class="granite-badge" id="hBadge" style="display:none">""" + _SPARKLE + """Powered by IBM Granite</div>
    </div>
    <div class="hpanel email-card">
      <h3>Generated email</h3>
      <div class="email-field"><div class="fl">Subject</div><div class="email-subject" id="eSubject">—</div></div>
      <div class="email-field"><div class="fl">Body</div><div class="email-body" id="eBody">—</div></div>
      <div class="email-sig" id="eSig"></div>
    </div>
    <div class="hpanel">
      <h3>Watsonx activity</h3>
      <div class="telemetry-row"><span class="tl">Model</span><span class="tv" id="tModel">—</span></div>
      <div class="telemetry-row"><span class="tl">Project</span><span class="tv" id="tProject">active</span></div>
      <div class="telemetry-row"><span class="tl">Request type</span><span class="tv" id="tType">—</span></div>
      <div class="telemetry-row"><span class="tl">Status</span><span class="tv" id="tStatus">—</span></div>
      <div class="telemetry-row"><span class="tl">Latency</span><span class="tv" id="tLatency">—</span></div>
      <div class="telemetry-row"><span class="tl">Tokens</span><span class="tv" id="tTokens">—</span></div>
    </div>
  </div>

  <div id="steps"><div class="empty" id="loading">Loading…</div></div>
</div>
<script>
function esc(s){ return String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }
let _rendered = false;
let _people = [];

const SIGNAL_ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M20 6L9 17l-5-5"/></svg>';

function selectPerson(idx){
  const p = _people[idx];
  if (!p) return;
  document.getElementById('hero').style.display = 'grid';
  document.getElementById('hName').textContent = p.name || '—';
  document.getElementById('hTitle').textContent = p.title || '';
  document.getElementById('hCompany').textContent = p.company || '';
  const signals = [
    p.install ? 'Existing IBM footprint' : 'Territory install data',
    'Growth opportunity signal',
    'Competitor presence check',
    'Cadence step context',
    'Title-based personalization',
  ];
  document.getElementById('hSignals').innerHTML = signals.map(s =>
    `<div class="signal">${SIGNAL_ICON}${esc(s)}</div>`).join('');
  const badge = document.getElementById('hBadge');
  badge.style.display = p.written_by === 'Claude' ? 'inline-flex' : 'none';
  document.getElementById('eSubject').textContent = p.subject || '—';
  document.getElementById('eBody').textContent = p.body || '—';
  document.getElementById('eSig').textContent = '[Your name]';

  const ai = window._aiActivity || {};
  document.getElementById('tModel').textContent = ai.model || '—';
  document.getElementById('tType').textContent = ai.request_type || 'Email personalization';
  const status = ai.status || 'not called';
  const statusEl = document.getElementById('tStatus');
  statusEl.textContent = status;
  statusEl.className = 'tv ' + (status === 'success' ? 'ok' : (status.includes('error') ? 'warn' : ''));
  document.getElementById('tLatency').textContent = ai.avg_latency_ms ? `${ai.avg_latency_ms} ms` : '—';
  document.getElementById('tTokens').textContent = ai.total_tokens ? ai.total_tokens.toLocaleString() : '—';
}

async function poll(){
  let s;
  try { s = await (await fetch('/api/bobby/state')).json(); } catch(e){ setTimeout(poll,2000); return; }
  const sum = s.summary;
  const sub = document.getElementById('sub');
  const banner = document.getElementById('banner');
  const sendBtn = document.getElementById('sendBtn');

  if (sum && sum.cadence){
    sub.innerHTML = `Cadence <b>${esc(sum.cadence)}</b> &middot; ${sum.email_step_count||0} email step(s) &middot; ${sum.drafted||0} email(s) drafted`;
  }
  if (sum && sum.ai_activity) window._aiActivity = sum.ai_activity;
  const haveDrafts = !!(sum && (sum.drafted||0) > 0);
  if (s.active){
    banner.className='banner run'; banner.innerHTML=`<span class="spinner" style="display:inline-block;vertical-align:-2px;margin-right:8px;"></span>${esc(s.message||'Working…')}`;
  } else if (s.phase==='error' || (s.error && !s.done)){
    banner.className='banner err'; banner.textContent = s.message || s.error || 'Bobby stopped.';
  } else if (haveDrafts){
    banner.className='banner ok'; banner.textContent = s.message || 'Drafts ready. Review below, then Send All.';
  } else {
    banner.className=''; banner.textContent='';
  }
  sendBtn.disabled = s.active || !haveDrafts;

  if (sum && sum.steps && !_rendered){
    renderSteps(sum.steps);
    _rendered = true;
  }
  if (!sum && !s.active){
    document.getElementById('loading').textContent = 'No drafts yet — go back and run Step 4.';
  }
  if (s.active) setTimeout(poll, 1500);
}

function renderSteps(steps){
  const host = document.getElementById('steps');
  const withPeople = steps.filter(st => (st.people||[]).length);
  if (!withPeople.length){ host.innerHTML = '<div class="empty">No one is currently sitting on an email step in this cadence.</div>'; return; }
  _people = [];
  withPeople.forEach(st => (st.people||[]).forEach(p => _people.push(p)));
  host.innerHTML = withPeople.map(st => {
    const cards = (st.people||[]).map(p => {
      const idx = _people.indexOf(p);
      return `
      <div class="card email-card" onclick="selectPerson(${idx})">
        <div class="who"><span class="name">${esc(p.name)}</span>
          <span class="by ${p.written_by==='Claude'?'':'tmpl'}">${esc(p.written_by)}</span></div>
        <div class="role">${esc(p.title||'')}${p.company?' &middot; '+esc(p.company):''}</div>
        <div class="subj"><span>Subject:</span> ${esc(p.subject)}</div>
        <div class="body">${esc(p.body)}</div>
      </div>`;
    }).join('');
    return `<div class="stephead"><span class="badge-step">Day ${st.day}</span><h2>${esc(st.display_name||st.name)}</h2>
              <span class="cnt">${(st.people||[]).length} person(s)</span></div>
            <div class="grid">${cards}</div>`;
  }).join('');
  if (_people.length) selectPerson(0);
}

async function sendAll(){
  const btn = document.getElementById('sendBtn');
  btn.disabled = true; btn.textContent = 'Sending…';
  try {
    const res = await fetch('/api/bobby/send', {method:'POST'});
    const body = await res.json();
    if (!body.ok){ alert('Error: ' + (body.error || 'send failed')); btn.disabled = false; btn.textContent = 'Send all'; return; }
    btn.textContent = 'Sent';
  } catch(e){
    alert('Send failed: ' + e);
    btn.disabled = false; btn.textContent = 'Send all';
  }
}

poll();
</script>
</body>
</html>
"""
