"""Seller Dashboard UI templates — extracted verbatim from run_pipeline.py.

These 8 page templates are rendered with flask.render_template_string (NOT
render_template), so the double-escaping contract is UNCHANGED and load-bearing:
JS backslash/regex escapes stay doubled, and no literal {{ or {% may appear in the
JS. See docs/GOTCHAS.md. Keeping them in their own module (byte-identical to the
originals) decouples every CSS/JS edit from the security-audited backend so a UI
tweak no longer shares a diff with auth/orchestration code.
"""

PAGE_TEMPLATE = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Seller Dashboard</title>
<style>
  :root{
    --ink:#1d1d1f; --ink2:#6e6e73; --ink3:#a1a1a6; --line:#ececf0;
    --soft:#f5f5f7; --accent:#0071e3;
    --green:#34c759; --amber:#ff9f0a; --blue:#0071e3; --gray:#c7c7cc; --red:#ff3b30;
  }
  *{ box-sizing:border-box; }
  html,body{ background:#fff; }
  body{
    font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","SF Pro Text","Helvetica Neue",Helvetica,Arial,sans-serif;
    color:var(--ink); margin:0; font-size:15px; line-height:1.5;
    -webkit-font-smoothing:antialiased; text-rendering:optimizeLegibility;
  }
  .btn{ font:inherit; font-size:14px; font-weight:500; color:var(--ink); background:var(--soft);
        border:none; border-radius:980px; padding:8px 17px; cursor:pointer; transition:background .15s,transform .06s; white-space:nowrap; }
  .btn:hover{ background:#e9e9ee; }
  .btn:active{ transform:scale(.97); }
  .btn.primary{ background:var(--accent); color:#fff; }
  .btn.primary:hover{ background:#0077ed; }
  .btn.primary:disabled,.btn:disabled{ background:#d2d2d7; color:#fff; cursor:not-allowed; }
  .btn.big{ padding:11px 24px; font-size:15px; }
  .link{ color:var(--accent); font-size:13.5px; font-weight:500; cursor:pointer; background:none; border:none; padding:0; font-family:inherit; }
  .link:hover{ text-decoration:underline; }

  .dot{ display:inline-block; width:8px; height:8px; border-radius:50%; background:var(--gray); flex:none; }
  .dot.done{ background:var(--green); }
  .dot.running{ background:var(--amber); }
  .dot.err{ background:var(--red); }
  .dot.pending{ background:var(--gray); }
  .dot.running{ animation:pulse 1.4s ease-in-out infinite; }
  @keyframes pulse{ 0%,100%{ opacity:1; } 50%{ opacity:.3; } }

  /* ── login gate ─────────────────────────────────────────────── */
  .gate{ position:fixed; inset:0; background:#fff; display:flex; align-items:center; justify-content:center; z-index:500; }
  .gate-card{ width:380px; max-width:calc(100vw - 40px); text-align:center; }
  .gate-logo{ font-weight:800; font-size:26px; letter-spacing:.06em; color:#161616; margin-bottom:22px;
              font-family:"Helvetica Neue",Helvetica,Arial,sans-serif; }
  .gate-card h1{ font-size:28px; font-weight:600; letter-spacing:-.02em; margin:0 0 6px; }
  .gate-sub{ color:var(--ink2); font-size:15px; margin:0 0 24px; }
  .gate-card form{ display:flex; flex-direction:column; gap:10px; }
  .gate-card input{ font:inherit; font-size:15px; border:1px solid var(--line); border-radius:12px; padding:12px 14px; background:#fff; color:var(--ink); }
  .gate-card input:focus{ outline:none; border-color:var(--accent); }
  .gate-card .btn{ margin-top:6px; }
  .gate-err{ color:var(--red); font-size:13.5px; min-height:18px; text-align:left; }
  .gate-note{ color:var(--ink3); font-size:12px; line-height:1.5; margin-top:20px; }

  /* ── top bar ────────────────────────────────────────────────── */
  .topbar{ position:sticky; top:0; z-index:50; background:rgba(255,255,255,.85); backdrop-filter:saturate(180%) blur(20px);
           border-bottom:1px solid var(--line); display:grid; grid-template-columns:1fr auto 1fr; align-items:center;
           padding:12px 24px; }
  .brand{ font-size:17px; font-weight:600; letter-spacing:-.01em; }
  .tabs{ display:flex; gap:4px; background:var(--soft); border-radius:980px; padding:3px; }
  .tab{ font:inherit; font-size:14px; font-weight:500; color:var(--ink2); background:none; border:none; cursor:pointer;
        padding:7px 18px; border-radius:980px; transition:background .15s,color .15s; }
  .tab:hover{ color:var(--ink); }
  .tab.active{ background:#fff; color:var(--ink); box-shadow:0 1px 3px rgba(0,0,0,.08); }
  .topbar .right{ justify-self:end; }
  .detailsbtn{ position:relative; }
  .warndot{ position:absolute; top:4px; right:6px; width:8px; height:8px; border-radius:50%; background:var(--red); }

  main{ max-width:760px; margin:0 auto; padding:44px 24px 120px; }
  .page{ display:none; }
  .page.active{ display:block; }
  .page-head{ margin-bottom:26px; }
  .page-head h2{ font-size:30px; font-weight:600; letter-spacing:-.02em; margin:0; }
  .page-head p{ color:var(--ink3); font-size:16px; margin:6px 0 0; }
  .page-head.split{ display:flex; align-items:flex-start; justify-content:space-between; gap:16px; }
  .page-head.split .grow{ flex:1; min-width:0; }
  .btn.refresh{ font-size:13px; padding:6px 15px; flex:none; margin-top:6px; }

  /* ── action cards ───────────────────────────────────────────── */
  .acard{ background:#fff; border:1px solid var(--line); border-radius:20px; padding:22px 24px; margin-bottom:16px;
          transition:border-color .2s,box-shadow .2s; }
  .acard.working{ border-color:#ffe1ac; box-shadow:0 0 0 4px rgba(255,159,10,.07); }
  .acard.done{ border-color:#c9efd5; }
  .ahead{ display:flex; align-items:flex-start; gap:16px; }
  .ahead .grow{ flex:1; min-width:0; }
  .atitle{ font-size:19px; font-weight:600; letter-spacing:-.01em; }
  .asub{ color:var(--ink3); font-size:13.5px; margin-top:3px; }
  .aseller{ color:var(--ink2); font-size:13px; margin-top:7px; }
  .aseller b{ color:var(--ink); font-weight:600; }
  .aacts{ display:flex; align-items:center; gap:10px; flex:none; flex-wrap:wrap; justify-content:flex-end; }
  .sel{ font:inherit; font-size:14px; border:1px solid var(--line); border-radius:980px; padding:8px 14px; background:#fff; color:var(--ink); cursor:pointer; }
  .sel:focus{ outline:none; border-color:var(--accent); }
  .choices{ display:flex; gap:10px; flex-wrap:wrap; margin-top:16px; }
  .choice{ display:inline-flex; align-items:center; gap:8px; font-size:13.5px; color:var(--ink); background:var(--soft);
           border:1px solid var(--line); border-radius:12px; padding:9px 14px; cursor:pointer; }
  .choice input{ accent-color:var(--accent); }
  .acard.bobby{ border-color:#e6dcff; }
  .acard.bobby .atitle::before{ content:"✍️ "; }

  .achips{ display:flex; gap:16px; flex-wrap:wrap; margin-top:16px; }
  .achip{ display:inline-flex; align-items:center; gap:7px; font-size:12.5px; color:var(--ink2); }
  .astatus{ display:flex; align-items:center; gap:9px; margin-top:15px; padding-top:15px; border-top:1px solid var(--line);
            font-size:14px; color:var(--ink2); }
  .astatus .amsg{ flex:1; min-width:0; }
  .astatus.err .amsg{ color:var(--red); }
  .asub2{ display:block; color:var(--ink3); font-size:12.5px; margin-top:3px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
  .alog{ margin-top:12px; background:var(--soft); border-radius:14px; padding:14px 16px; max-height:220px; overflow-y:auto;
         font:12px/1.65 "SF Mono",ui-monospace,Menlo,monospace; color:#515154; display:none; }
  .alog.show{ display:block; }
  .alog div{ padding:1px 0; word-break:break-word; }
  .showlog{ margin-top:10px; }

  .blank{ text-align:center; color:var(--ink3); font-size:16px; padding:90px 20px; border:1px dashed var(--line); border-radius:20px; }

  /* ── details modal (Access) ─────────────────────────────────── */
  .modal{ position:fixed; inset:0; background:rgba(0,0,0,.28); display:none; align-items:flex-start; justify-content:center; z-index:200; padding:60px 20px; overflow-y:auto; }
  .modal.show{ display:flex; }
  .modal-card{ background:#fff; border-radius:22px; width:640px; max-width:100%; padding:26px 28px 30px; box-shadow:0 24px 60px rgba(0,0,0,.22); }
  .modal-head{ display:flex; align-items:center; justify-content:space-between; margin-bottom:6px; }
  .modal-head h2{ font-size:22px; font-weight:600; letter-spacing:-.01em; margin:0; }
  .signed-as{ color:var(--ink2); font-size:13.5px; margin:2px 0 20px; }
  .signed-as b{ color:var(--ink); }
  .panel{ background:#fff; border:1px solid var(--line); border-radius:16px; padding:18px 20px; margin-bottom:14px; }
  .panel h3{ font-size:12px; font-weight:600; text-transform:uppercase; letter-spacing:.07em; color:var(--ink3); margin:0 0 12px; }
  .lrow{ display:flex; align-items:center; gap:12px; padding:10px 0; border-top:1px solid var(--line); }
  .lrow:first-of-type{ border-top:none; }
  .lrow .svc{ width:88px; font-weight:500; font-size:14.5px; }
  .lrow .fill{ flex:1; color:var(--ink2); font-size:13px; display:flex; align-items:center; gap:10px; flex-wrap:wrap; }
  .pill{ display:inline-flex; align-items:center; gap:6px; font-size:12.5px; font-weight:500; color:var(--ink2); white-space:nowrap; }
  .pill .dot{ background:var(--gray); }
  .pill.ready .dot{ background:var(--green); }
  .pill.expired .dot,.pill.error .dot{ background:var(--red); }
  .pill.checking .dot,.pill.waiting .dot{ background:var(--amber); animation:pulse 1.4s ease-in-out infinite; }
  .alert{ background:#fdecec; color:#c0271f; border-radius:12px; padding:11px 15px; margin-bottom:10px; font-size:13.5px; font-weight:500; display:none; }
  .alert.show{ display:block; }
  .note{ color:var(--ink3); font-size:12.5px; line-height:1.55; margin-bottom:6px; }
  .panel input[type=text],.panel input[type=password]{ font:inherit; font-size:14px; border:1px solid var(--line); border-radius:10px; padding:8px 12px; margin:8px 8px 4px 0; background:#fff; color:var(--ink); }
  .panel input:focus{ outline:none; border-color:var(--accent); }
</style>
</head>
<body>

<!-- ── IBM Login gate ─────────────────────────────────────────── -->
<div class="gate" id="loginGate" style="display:none">
  <div class="gate-card">
    <div class="gate-logo">IBM</div>
    <h1>Seller Dashboard</h1>
    <p class="gate-sub">Sign in with your IBM ID to continue.</p>
    <form onsubmit="submitLogin(event)">
      <input type="email" id="loginEmail" placeholder="you@ibm.com" autocomplete="username" required>
      <input type="password" id="loginPw" placeholder="Password" autocomplete="current-password" required>
      <div class="gate-err" id="loginErr"></div>
      <button class="btn primary big" type="submit" id="loginBtn">Sign in</button>
    </form>
    <div class="gate-note">Demo sign-in — this clone uses mock data and never contacts IBM. Only your email is kept (locally), to pick the accounts in your territory; the password is discarded. Any email works.</div>
  </div>
</div>

<!-- ── main app ───────────────────────────────────────────────── -->
<div id="app" style="display:none">
  <header class="topbar">
    <div class="brand">Seller Dashboard</div>
    <nav class="tabs">
      <button class="tab active" data-page="outbound" onclick="showPage('outbound')">Outbound</button>
    </nav>
    <div class="right">
      <button class="btn detailsbtn" onclick="openDetails()">Details<span class="warndot" id="detailsWarn" style="display:none"></span></button>
    </div>
  </header>

  <main>
    <!-- Outbound -->
    <section id="page-outbound" class="page active">
      <div class="page-head">
        <h2>Outbound</h2>
        <p>Pull your accounts, build a strategy, and load contacts — end to end.</p>
      </div>

      <!-- Get My Accounts -->
      <div class="acard" id="card-gma">
        <div class="ahead">
          <div class="grow">
            <div class="atitle">Get My Accounts</div>
            <div class="asub">ISC Scraper &rarr; IBM Scraper &rarr; Account Segmentation</div>
            <div class="aseller" id="gmaSeller"></div>
          </div>
          <div class="aacts">
            <span id="gmaResults"></span>
            <button class="btn primary big" id="gmaBtn" onclick="runGetMyAccounts()">Get My Accounts</button>
          </div>
        </div>
        <div class="achips" id="gmaChips"></div>
        <div class="astatus" id="gmaStatus"><span class="dot pending"></span><span class="amsg">Pulls every account in your territory, adds IBM install intel, and segments them.</span></div>
        <button class="link showlog" id="gmaLogToggle" onclick="toggleLog('gma')" style="display:none">Show details</button>
        <div class="alog" id="gmaLog"></div>
      </div>

      <!-- Outbound Strategy -->
      <div class="acard" id="card-strategy">
        <div class="ahead">
          <div class="grow">
            <div class="atitle">Outbound Strategy</div>
            <div class="asub">Account Tiering &rarr; Call Planning</div>
          </div>
          <div class="aacts">
            <span id="strategyResults"></span>
            <button class="btn primary big" id="strategyBtn" onclick="runStrategy()">Outbound Strategy</button>
          </div>
        </div>
        <div class="achips" id="strategyChips"></div>
        <div class="astatus" id="strategyStatus"><span class="dot pending"></span><span class="amsg">Scores and tiers your accounts, then lays out a call calendar to year-end.</span></div>
        <button class="link showlog" id="strategyLogToggle" onclick="toggleLog('strategy')" style="display:none">Show details</button>
        <div class="alog" id="strategyLog"></div>
      </div>

      <!-- Fill Contacts to SalesLoft -->
      <div class="acard" id="card-fill">
        <div class="ahead">
          <div class="grow">
            <div class="atitle">Fill Contacts to SalesLoft</div>
            <div class="asub">ZoomInfo Contact Readiness &rarr; Salesloft cadence</div>
          </div>
          <div class="aacts">
            <select class="sel" id="fillCadence">{% for c in cadences %}<option value="{{ c }}">{{ c }}</option>{% endfor %}</select>
            <button class="btn primary big" id="fillBtn" onclick="runFill()">Fill Contacts to SalesLoft</button>
          </div>
        </div>
        <div class="achips" id="fillChips"></div>
        <div class="astatus" id="fillStatus"><span class="dot pending"></span><span class="amsg">Readies contacts in ZoomInfo and loads them into the Salesloft cadence you choose.</span></div>
        <button class="link showlog" id="fillLogToggle" onclick="toggleLog('fill')" style="display:none">Show details</button>
        <div class="alog" id="fillLog"></div>
      </div>

      <!-- Bobby, the AI Emailer -->
      <div class="acard bobby" id="card-bobby">
        <div class="ahead">
          <div class="grow">
            <div class="atitle">Bobby, the AI Emailer</div>
            <div class="asub">Writes a personalized email for every person in a Salesloft cadence — by their cadence day, title, and company.</div>
          </div>
          <div class="aacts">
            <button class="btn primary big" id="bobbyBtn" onclick="runBobby()">Run Bobby</button>
          </div>
        </div>
        <div class="choices" id="bobbyChoices">
          {% for c in bobby_cadences %}
          <label class="choice"><input type="radio" name="bobbyCadence" value="{{ c }}"{{ ' checked' if loop.first else '' }}> {{ c }}</label>
          {% endfor %}
        </div>
        <div class="asub" style="margin-top:14px;">Reads the cadence's email steps and everyone on them, drafts a tailored email per person, and opens a review page with a <b>Send All</b> button.</div>
        <div class="astatus" id="bobbyStatus"><span class="dot pending"></span><span class="amsg">Pick a cadence, then Bobby drafts a tailored email for each person on an email step.</span></div>
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

// ── page nav ──────────────────────────────────────────────────
function showPage(name){
  document.querySelectorAll('.page').forEach(p => p.classList.toggle('active', p.id === 'page-' + name));
  document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.page === name));
}

// ── details modal ─────────────────────────────────────────────
let _detailsOpen = false;
function openDetails(){
  _detailsOpen = true;
  document.getElementById('detailsModal').classList.add('show');
  fetchLoginStatus(); fetchCredStatus(); fetchSeller();
}
function closeDetails(){
  _detailsOpen = false;
  document.getElementById('detailsModal').classList.remove('show');
}

// ── app boot ──────────────────────────────────────────────────
let _pollTimer = null;
function startApp(){
  document.getElementById('app').style.display = 'block';
  fetchStatus(); fetchSeller(); fetchLoginStatus();
  if (!_pollTimer) _pollTimer = setInterval(() => { fetchStatus(); fetchLoginStatus(); }, 2000);
}

// ── seller identity ───────────────────────────────────────────
async function fetchSeller(){
  let d = {};
  try { d = await (await fetch('/api/seller')).json(); } catch(e){ return; }
  const el = document.getElementById('gmaSeller');
  const signed = document.getElementById('signedAs');
  if (d.signed_in && d.seller_name && d.covids){
    el.innerHTML = `Signed in as <b>${esc(d.seller_name)}</b> &middot; ${d.covids} coverage ID${d.covids===1?'':'s'} in your territory`;
  } else if (d.signed_in && !d.matched){
    el.innerHTML = `Signed in as <b>${esc(d.email||'')}</b> — no matching territories found in the Name Match list.`;
  } else {
    el.textContent = '';
  }
  if (signed){
    signed.innerHTML = d.signed_in
      ? `Signed in as <b>${esc(d.email||'')}</b>${d.seller_name ? ' &middot; ' + esc(d.seller_name) : ''}`
      : 'Not signed in.';
  }
}

// ── action cards ──────────────────────────────────────────────
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
    `<span class="achip"><span class="dot ${chipDotClass(data[sk])}"></span>${esc(label)}</span>`).join('');
}

function collectLog(key, data){
  const lines = [];
  for (const [sk] of GROUPS[key]){
    const tail = (data[sk] && data[sk].log_tail) || [];
    for (const l of tail){ const c = cleanLine(l); if (c) lines.push(c); }
  }
  return lines.slice(-60);
}

function updateAction(key, a, data, resultsHtml){
  const card = document.getElementById('card-' + key);
  card.classList.toggle('working', !!(a && a.active));
  card.classList.toggle('done', !!(a && a.done && !a.active));

  const status = document.getElementById(key + 'Status');
  const dotCls = actDotClass(a);
  const msg = (a && a.message) ? a.message : status.querySelector('.amsg').textContent;
  status.classList.toggle('err', dotCls === 'err');

  // Live log (distilled) — also feeds the "what's happening right now" sub-line.
  const logLines = collectLog(key, data);
  // While active, show the running step's latest distilled log line beneath the
  // headline so a long step (e.g. tiering's per-account ZoomInfo/signal work)
  // visibly ticks along instead of looking frozen.
  let sub = '';
  if (a && a.active && logLines.length){
    const live = logLines[logLines.length - 1];
    if (live && live !== msg) sub = `<span class="asub2">${esc(live)}</span>`;
  }
  status.innerHTML = `<span class="dot ${dotCls}"></span><span class="amsg">${esc(msg)}${sub}</span>`;

  const btn = document.getElementById(key + 'Btn');
  if (a && a.active){ btn.disabled = true; }
  else { btn.disabled = false; }

  // Not every card has a results slot (e.g. Fill has none) — guard so a missing
  // element can't throw and abort the rest of fetchStatus (Bobby + Pipeline update after this).
  const resultsEl = document.getElementById(key + 'Results');
  if (resultsEl) resultsEl.innerHTML = resultsHtml || '';
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

  const gmaResults = (data.segment && data.segment.state === 'done')
    ? `<a class="link" href="/view/segment" target="_blank">Show results &#8599;</a>` : '';
  updateAction('gma', acts.get_my_accounts, data, gmaResults);

  const stratDone = (data.step2 && data.step2.state === 'done') || (data.step3 && data.step3.state === 'done');
  const stratResults = stratDone
    ? `<a class="link" href="/view/strategy" target="_blank">Show results &#8599;</a>` : '';
  updateAction('strategy', acts.outbound_strategy, data, stratResults);

  const fillCad = (acts.fill_contacts && acts.fill_contacts.cadence) || '';
  const fillResults = (acts.fill_contacts && acts.fill_contacts.done)
    ? `<a class="link" href="/mock/salesloft?cadence=${encodeURIComponent(fillCad)}" target="_blank">Open in Salesloft &#8599;</a>` : '';
  updateAction('fill', acts.fill_contacts, data, fillResults);
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
  // Bobby's drafts + Send All live on its own page.
  const open = (a && (a.active || a.done || a.error))
    ? ` <a class="link" href="/bobby">Open Bobby &#8599;</a>` : '';
  status.innerHTML = `<span class="dot ${dotCls}"></span><span class="amsg">${esc(msg)}${open}</span>`;
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
  // Bobby has its own page — go watch it draft, review, and Send All there.
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
// In the WatsonX Clone every session is mocked and always shows "logged in"; the
// "Log in" button opens an in-app mock sign-in page and "Open" opens the mock tool.
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
  if (body.mock_url) window.open(body.mock_url, '_blank');   // in-app mock sign-in page
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
      `<div style="font-size:13.5px;display:flex;align-items:center;gap:10px;margin-bottom:8px;"><span style="font-weight:500;">${CRED_LABELS[key]}</span>`
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
<style>
  :root{ --ink:#1d1d1f; --ink3:#a1a1a6; --line:#ececf0; --soft:#f5f5f7; --accent:#0071e3; }
  *{ box-sizing:border-box; }
  body{ font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","SF Pro Text","Helvetica Neue",Helvetica,Arial,sans-serif;
        background:#fff; color:var(--ink); margin:0; padding:40px 32px 80px; -webkit-font-smoothing:antialiased; }
  h1{ font-size:28px; font-weight:600; letter-spacing:-.02em; margin:0 0 6px; }
  .meta{ color:var(--ink3); font-size:13.5px; margin-bottom:20px; }
  input#filter{ font:inherit; font-size:14px; padding:9px 14px; width:340px; margin-bottom:18px;
                border:1px solid var(--line); border-radius:980px; background:var(--soft); }
  input#filter:focus{ outline:none; border-color:var(--accent); background:#fff; }
  table{ border-collapse:separate; border-spacing:0; width:100%; font-size:12.5px; }
  th, td{ padding:9px 14px; text-align:left; white-space:nowrap; border-bottom:1px solid var(--line); }
  th{ background:#fff; position:sticky; top:0; cursor:pointer; font-weight:600; color:#6e6e73;
      border-bottom:1px solid #d2d2d7; }
  th:hover{ color:var(--ink); }
  tr:hover td{ background:#fafafccc; }
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


TIER_VIEW_TEMPLATE = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Account Tiering — Seller Worklist</title>
<style>
  :root{ --ink:#1d1d1f; --ink2:#6e6e73; --ink3:#a1a1a6; --line:#ececf0; --soft:#f5f5f7; --accent:#0071e3; }
  *{ box-sizing:border-box; }
  body{ font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","SF Pro Text","Helvetica Neue",Helvetica,Arial,sans-serif;
        background:#fff; color:var(--ink); margin:0; padding:40px 32px 90px; -webkit-font-smoothing:antialiased; }
  h1{ font-size:28px; font-weight:600; letter-spacing:-.02em; margin:0 0 6px; }
  .meta{ color:var(--ink3); font-size:13.5px; margin-bottom:18px; }
  .legend{ display:flex; gap:10px; flex-wrap:wrap; margin-bottom:16px; }
  .chip{ font-size:13px; font-weight:600; padding:7px 14px; border-radius:980px; cursor:pointer; border:1px solid transparent; user-select:none; }
  .chip.off{ opacity:.4; }
  .chip.c1{ background:#eafaef; color:#1c7a35; }
  .chip.c2{ background:#eaf3fd; color:#0b62c4; }
  .chip.c3{ background:#f0f0f2; color:#5b5b60; }
  input#filter{ font:inherit; font-size:14px; padding:9px 14px; width:320px; margin-bottom:16px;
                border:1px solid var(--line); border-radius:980px; background:var(--soft); }
  input#filter:focus{ outline:none; border-color:var(--accent); background:#fff; }
  table{ border-collapse:separate; border-spacing:0; width:100%; font-size:12.5px; }
  th,td{ padding:9px 11px; text-align:left; border-bottom:1px solid var(--line); vertical-align:top; }
  th{ background:#fff; position:sticky; top:0; z-index:2; font-weight:600; color:#6e6e73; white-space:nowrap;
      border-bottom:1px solid #d2d2d7; cursor:pointer; }
  th:hover{ color:var(--ink); }
  td.num{ font-variant-numeric:tabular-nums; white-space:nowrap; }
  tr.hidden{ display:none; }
  tr.t1{ background:#f5fcf8; }
  tr.t2{ background:#f6faff; }
  tr:hover td{ background:#fbfbfd; }
  .tb{ display:inline-block; min-width:30px; text-align:center; font-weight:700; font-size:11px; padding:3px 8px; border-radius:7px; }
  .tb1{ background:#34c759; color:#fff; }
  .tb2{ background:#0071e3; color:#fff; }
  .tb3{ background:#c7c7cc; color:#fff; }
  .acct{ font-weight:600; color:var(--ink); max-width:230px; white-space:normal; }
  .why{ color:var(--ink2); max-width:340px; white-space:normal; line-height:1.45; }
  .play{ display:inline-block; font-size:11px; font-weight:600; padding:3px 9px; border-radius:980px; white-space:nowrap; }
  .p-expand{ background:#eafaef; color:#1c7a35; }
  .p-displace{ background:#f3ecfd; color:#6c3fd0; }
  .p-refresh{ background:#eaf3fd; color:#0b62c4; }
  .p-land{ background:#e6f7f5; color:#0a7d70; }
  .p-winback{ background:#fff4e5; color:#8a5a00; }
  .p-nurture{ background:#f0f0f2; color:#5b5b60; }
  .tr-up{ color:#1c7a35; font-weight:600; }
  .tr-down{ color:#c0271f; font-weight:600; }
  .tr-new{ color:#6c3fd0; font-weight:600; }
  .tr-flat,.tr-unknown{ color:var(--ink3); }
  .comp-yes{ color:#6c3fd0; font-weight:600; }
</style>
</head>
<body>
{% set PLAY_CLS = {'Expand & Protect':'p-expand','Displace Competitor':'p-displace','Hardware Refresh':'p-refresh','Land New Logo':'p-land','Win-Back':'p-winback','Nurture':'p-nurture'} %}
{% set TREND = {'Growing':['&#9650;','tr-up'],'Declining':['&#9660;','tr-down'],'Lapsed':['&#9660;','tr-down'],'New':['&#10022;','tr-new'],'Flat':['&#9644;','tr-flat'],'Unknown':['&ndash;','tr-unknown']} %}
<h1>Account Tiering — Seller Worklist</h1>
<div class="meta">{{ path }} — {{ total }} accounts, sorted best-first. Seller-relevant fields only; raw IBM codes hidden.</div>
<div class="legend">
  <span class="chip c1" data-tier="1" onclick="toggleTier(this)">Tier 1 · {{ counts[1] }}</span>
  <span class="chip c2" data-tier="2" onclick="toggleTier(this)">Tier 2 · {{ counts[2] }}</span>
  <span class="chip c3" data-tier="3" onclick="toggleTier(this)">Tier 3 · {{ counts[3] }}</span>
</div>
<input id="filter" type="text" placeholder="Filter (account, industry, play...)" oninput="filterRows()">
<table id="tbl">
<thead><tr>
  <th onclick="sortByCol(0,true)">#</th>
  <th onclick="sortByCol(1,true)">Tier</th>
  <th onclick="sortByCol(2)">Account</th>
  <th onclick="sortByCol(3)">Industry</th>
  <th onclick="sortByCol(4)">Play</th>
  <th onclick="sortByCol(5,true)">Score</th>
  <th onclick="sortByCol(6)">Relationship</th>
  <th onclick="sortByCol(7)">Spend trend</th>
  <th onclick="sortByCol(8)">IBM spend</th>
  <th onclick="sortByCol(9)">Revenue</th>
  <th onclick="sortByCol(10)">Employees</th>
  <th onclick="sortByCol(11)">IBM install</th>
  <th onclick="sortByCol(12)">Competitor</th>
  <th onclick="sortByCol(13)">Contacts</th>
  <th onclick="sortByCol(14)">Why call</th>
</tr></thead>
<tbody>
{% for r in rows %}
<tr class="t{{ r.tier }}" data-tier="{{ r.tier }}">
  <td class="num">{{ r.rank }}</td>
  <td><span class="tb tb{{ r.tier }}">T{{ r.tier }}</span></td>
  <td class="acct">{{ r.account }}</td>
  <td>{{ r.industry }}</td>
  <td><span class="play {{ PLAY_CLS.get(r.play,'p-nurture') }}">{{ r.play }}</span></td>
  <td class="num">{{ '%.1f'|format(r.score|float) if r.score is not none else '—' }}</td>
  <td>{{ r.relationship }}</td>
  <td class="{{ TREND.get(r.trend,['','tr-unknown'])[1] }}">{{ TREND.get(r.trend,['&ndash;',''])[0]|safe }} {{ r.trend }}</td>
  <td class="num">{{ r.spend }}</td>
  <td class="num">{{ r.revenue }}</td>
  <td class="num">{{ r.employees }}</td>
  <td>{{ r.install }}</td>
  <td class="{{ 'comp-yes' if r.competitor.startswith('Yes') else '' }}">{{ r.competitor }}</td>
  <td class="num">{{ r.contacts }}</td>
  <td class="why">{{ r.angle }}</td>
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
<title>Call Planning — Dial Calendar</title>
<style>
  :root{ --ink:#1d1d1f; --ink2:#6e6e73; --ink3:#a1a1a6; --line:#ececf0; --soft:#f5f5f7; --accent:#0071e3; }
  *{ box-sizing:border-box; }
  body{ font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","SF Pro Text","Helvetica Neue",Helvetica,Arial,sans-serif;
        background:#fff; color:var(--ink); margin:0; padding:40px 32px 90px; -webkit-font-smoothing:antialiased; }
  h1{ font-size:28px; font-weight:600; letter-spacing:-.02em; margin:0 0 6px; }
  .meta{ color:var(--ink3); font-size:13.5px; margin-bottom:16px; }
  .note{ background:#f5f8ff; border:1px solid #e3ecfb; border-radius:14px; padding:14px 18px; margin-bottom:16px; font-size:14.5px; line-height:1.5; color:#26456f; }
  .stats{ display:flex; gap:10px; flex-wrap:wrap; margin-bottom:18px; }
  .stat{ background:var(--soft); border-radius:12px; padding:9px 15px; font-size:13px; }
  .stat b{ font-weight:600; font-size:15px; }
  .legend{ display:flex; gap:16px; flex-wrap:wrap; margin-bottom:20px; font-size:12.5px; color:var(--ink2); align-items:center; }
  .legend .sw{ display:inline-block; width:12px; height:12px; border-radius:4px; margin-right:5px; vertical-align:-1px; }
  .layout{ display:flex; gap:26px; align-items:flex-start; }
  .cals{ flex:1; min-width:0; display:grid; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); gap:22px; }
  .month{ border:1px solid var(--line); border-radius:16px; padding:14px 14px 10px; }
  .month h3{ font-size:15px; font-weight:600; margin:0 0 10px; letter-spacing:-.01em; }
  table.cal{ border-collapse:collapse; width:100%; table-layout:fixed; }
  table.cal th{ font-size:10.5px; color:var(--ink3); font-weight:600; padding:2px 0 6px; text-align:center; }
  table.cal td{ height:40px; text-align:center; vertical-align:middle; padding:1px; }
  .cell{ position:relative; height:38px; border-radius:9px; display:flex; flex-direction:column; align-items:center; justify-content:center; font-size:12px; color:var(--ink); }
  .cell .d{ font-size:11px; line-height:1; }
  .cell .cnt{ font-size:10px; font-weight:700; margin-top:2px; line-height:1; }
  .cell.out{ color:var(--ink3); opacity:.35; }
  .cell.wknd,.cell.holi{ color:var(--ink3); background:repeating-linear-gradient(45deg,#fafafa,#fafafa 4px,#f2f2f4 4px,#f2f2f4 8px); }
  .cell.today{ box-shadow:inset 0 0 0 2px var(--accent); }
  .cell.has{ cursor:pointer; font-weight:600; }
  .cell.has:hover{ filter:brightness(.96); }
  .cell.t1{ background:#d7f4e0; color:#125b28; }
  .cell.t2{ background:#dcebfb; color:#0b4d9c; }
  .cell.t3{ background:#ececed; color:#4a4a4f; }
  .panel{ width:340px; flex:none; position:sticky; top:24px; border:1px solid var(--line); border-radius:16px; padding:18px; max-height:calc(100vh - 60px); overflow:auto; }
  .panel .ph{ font-size:12px; text-transform:uppercase; letter-spacing:.06em; color:var(--ink3); font-weight:600; }
  .panel h2{ font-size:19px; margin:4px 0 3px; font-weight:600; }
  .panel .psub{ color:var(--ink2); font-size:13px; margin-bottom:14px; }
  .accard{ border:1px solid var(--line); border-radius:12px; padding:11px 13px; margin-bottom:10px; }
  .accard.t1{ border-left:4px solid #34c759; }
  .accard.t2{ border-left:4px solid #0071e3; }
  .accard.t3{ border-left:4px solid #c7c7cc; }
  .accard .an{ font-weight:600; font-size:14px; }
  .accard .am{ color:var(--ink3); font-size:12px; margin:3px 0 6px; }
  .accard .play{ display:inline-block; font-size:10.5px; font-weight:600; padding:2px 8px; border-radius:980px; background:#f0f0f2; color:#5b5b60; }
  .accard .aa{ color:var(--ink2); font-size:12.5px; line-height:1.45; margin-top:7px; }
  .empty{ color:var(--ink3); font-size:14px; margin-top:30px; text-align:center; }
  @media(max-width:820px){ .layout{ flex-direction:column; } .panel{ width:100%; position:static; } }
</style>
</head>
<body>
<h1>Call Planning — Dial Calendar</h1>
<div class="meta">{{ path }} — {{ total }} accounts, today through year-end. Click any highlighted day to see its accounts.</div>
{% if meta.summary %}<div class="note">{{ meta.summary }}</div>{% endif %}
<div class="stats">
  <div class="stat"><b>{{ total }}</b> accounts</div>
  {% if meta.per_day %}<div class="stat">up to <b>{{ meta.per_day }}</b>/day</div>{% endif %}
  {% if meta.used_days %}<div class="stat"><b>{{ meta.used_days }}</b> active days</div>{% endif %}
  {% if meta.working_days %}<div class="stat"><b>{{ meta.working_days }}</b> working days to Dec 31</div>{% endif %}
  {% if meta.tier_counts %}<div class="stat">T1 <b>{{ meta.tier_counts['1'] }}</b> · T2 <b>{{ meta.tier_counts['2'] }}</b> · T3 <b>{{ meta.tier_counts['3'] }}</b></div>{% endif %}
</div>
<div class="legend">
  <span><span class="sw" style="background:#d7f4e0"></span>Tier 1 day</span>
  <span><span class="sw" style="background:#dcebfb"></span>Tier 2 day</span>
  <span><span class="sw" style="background:#ececed"></span>Tier 3 day</span>
  <span><span class="sw" style="background:#f2f2f4"></span>Weekend / holiday</span>
</div>
<div class="layout">
  <div class="cals">
    {% for mo in months %}
    <div class="month">
      <h3>{{ mo.label }}</h3>
      <table class="cal">
        <thead><tr><th>Su</th><th>Mo</th><th>Tu</th><th>We</th><th>Th</th><th>Fr</th><th>Sa</th></tr></thead>
        <tbody>
        {% for week in mo.weeks %}
          <tr>
          {% for c in week %}
            {% if c.blank %}<td></td>
            {% else %}
              {% set cls = 'cell' %}
              {% if not c.in_range %}{% set cls = cls + ' out' %}{% endif %}
              {% if c.count > 0 %}{% set cls = cls + ' has t' + c.tier|string %}
              {% elif c.holiday %}{% set cls = cls + ' holi' %}
              {% elif c.weekend %}{% set cls = cls + ' wknd' %}{% endif %}
              {% if c.today %}{% set cls = cls + ' today' %}{% endif %}
              <td>{% if c.count > 0 %}<div class="{{ cls }}" onclick="showDay('{{ c.iso }}')"><span class="d">{{ c.day }}</span><span class="cnt">{{ c.count }}</span></div>
                  {% else %}<div class="{{ cls }}"><span class="d">{{ c.day }}</span></div>{% endif %}</td>
            {% endif %}
          {% endfor %}
          </tr>
        {% endfor %}
        </tbody>
      </table>
    </div>
    {% endfor %}
  </div>
  <div class="panel" id="panel">
    <div class="ph">Selected day</div>
    <div class="empty">Click a highlighted day<br>to see its accounts.</div>
  </div>
</div>
<script>
const ACCTS = {{ accounts_json|safe }};
const PLAY_CLS = {'Expand & Protect':'p-expand','Displace Competitor':'p-displace','Hardware Refresh':'p-refresh','Land New Logo':'p-land','Win-Back':'p-winback','Nurture':'p-nurture'};
function esc(s){ return String(s==null?'':s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }
function fmtDate(iso){ const d = new Date(iso+'T00:00:00'); return d.toLocaleDateString(undefined,{weekday:'long',month:'long',day:'numeric'}); }
function showDay(iso){
  const list = ACCTS[iso] || [];
  const panel = document.getElementById('panel');
  const cards = list.map(a =>
    `<div class="accard t${a.tier}"><div class="an">${esc(a.name)}</div>`
    + `<div class="am">Tier ${a.tier} · score ${a.score==null?'—':a.score} · ${esc(a.industry||'')}</div>`
    + `<span class="play">${esc(a.play||'')}</span>`
    + (a.install ? `<div class="aa"><b>Install:</b> ${esc(a.install)}</div>` : '')
    + (a.angle ? `<div class="aa">${esc(a.angle)}</div>` : '')
    + `</div>`).join('');
  panel.innerHTML = `<div class="ph">Selected day</div><h2>${esc(fmtDate(iso))}</h2>`
    + `<div class="psub">${list.length} account${list.length===1?'':'s'} to dial</div>${cards}`;
}
</script>
</body>
</html>
"""


STRATEGY_TEMPLATE = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Outbound Strategy — Results</title>
<style>
  :root{ --ink:#1d1d1f; --ink2:#6e6e73; --ink3:#a1a1a6; --line:#ececf0; --soft:#f5f5f7; --accent:#0071e3; }
  *{ box-sizing:border-box; }
  html,body{ height:100%; }
  body{ font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","SF Pro Text","Helvetica Neue",Helvetica,Arial,sans-serif;
        background:#fff; color:var(--ink); margin:0; display:flex; flex-direction:column; height:100vh; -webkit-font-smoothing:antialiased; }
  header{ padding:20px 32px 0; }
  h1{ font-size:24px; font-weight:600; letter-spacing:-.02em; margin:0 0 12px; }
  .tabs{ display:flex; gap:6px; border-bottom:1px solid var(--line); }
  .tab{ font:inherit; font-size:14.5px; font-weight:600; color:var(--ink2); background:none; border:none; cursor:pointer;
        padding:10px 18px; border-bottom:2px solid transparent; margin-bottom:-1px; }
  .tab:hover{ color:var(--ink); }
  .tab.active{ color:var(--accent); border-bottom-color:var(--accent); }
  .frames{ flex:1; min-height:0; position:relative; }
  iframe{ position:absolute; inset:0; width:100%; height:100%; border:none; display:none; }
  iframe.active{ display:block; }
  .missing{ display:none; color:var(--ink3); font-size:15px; padding:40px 32px; }
  .missing.active{ display:block; }
</style>
</head>
<body>
<header>
  <h1>Outbound Strategy</h1>
  <div class="tabs">
    <button class="tab active" onclick="showTab('tier')">Account Tiering</button>
    <button class="tab" onclick="showTab('plan')">Call Planning</button>
  </div>
</header>
<div class="frames">
  {% if has_tier %}<iframe id="f-tier" class="active" src="/view/step2"></iframe>
  {% else %}<div id="f-tier" class="missing active">Account Tiering hasn't run yet — click Outbound Strategy first.</div>{% endif %}
  {% if has_plan %}<iframe id="f-plan" src="/view/step3"></iframe>
  {% else %}<div id="f-plan" class="missing">Call Planning hasn't run yet — click Outbound Strategy first.</div>{% endif %}
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


BOBBY_PAGE_TEMPLATE = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Bobby, the AI Emailer</title>
<style>
  :root{ --ink:#1d1d1f; --ink2:#6e6e73; --ink3:#a1a1a6; --line:#ececf0; --soft:#f5f5f7; --accent:#0071e3;
         --green:#34c759; --amber:#ff9f0a; --red:#ff3b30; }
  *{ box-sizing:border-box; }
  body{ font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","SF Pro Text","Helvetica Neue",Helvetica,Arial,sans-serif;
        background:#fff; color:var(--ink); margin:0; padding:0 0 100px; -webkit-font-smoothing:antialiased; }
  .top{ position:sticky; top:0; z-index:20; background:rgba(255,255,255,.9); backdrop-filter:saturate(180%) blur(20px);
        border-bottom:1px solid var(--line); padding:16px 32px; display:flex; align-items:center; gap:18px; }
  .top .grow{ flex:1; min-width:0; }
  .top h1{ font-size:20px; font-weight:600; letter-spacing:-.01em; margin:0; }
  .top .sub{ color:var(--ink3); font-size:13px; margin-top:2px; }
  .top .sub b{ color:var(--ink2); }
  .back{ color:var(--accent); font-size:13.5px; text-decoration:none; }
  .btn{ font:inherit; font-size:14px; font-weight:600; border:none; border-radius:980px; padding:10px 20px; cursor:pointer; }
  .btn.primary{ background:var(--accent); color:#fff; } .btn.primary:disabled{ background:#d2d2d7; cursor:not-allowed; }
  .wrap{ max-width:1100px; margin:0 auto; padding:26px 32px; }

  .banner{ border-radius:14px; padding:13px 16px; margin-bottom:18px; font-size:14px; line-height:1.5; }
  .banner.run{ background:#fff8ec; color:#8a5a00; } .banner.err{ background:#fdecec; color:#c0271f; }
  .banner.ok{ background:#eafaef; color:#1c7a35; }
  .spin{ display:inline-block; width:8px; height:8px; border-radius:50%; background:var(--amber); margin-right:8px;
         animation:pulse 1.3s ease-in-out infinite; } @keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}

  .stephead{ display:flex; align-items:center; gap:12px; margin:26px 0 12px; }
  .stephead .badge{ font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.05em; color:#6c3fd0; background:#f3ecfd; padding:4px 11px; border-radius:980px; }
  .stephead h2{ font-size:17px; font-weight:600; margin:0; }
  .stephead .cnt{ color:var(--ink3); font-size:13px; }
  .grid{ display:grid; grid-template-columns:repeat(auto-fill,minmax(430px,1fr)); gap:14px; }
  .card{ border:1px solid var(--line); border-radius:16px; padding:16px 18px; }
  .who{ display:flex; align-items:baseline; justify-content:space-between; gap:10px; }
  .who .name{ font-size:15.5px; font-weight:600; }
  .who .by{ font-size:10.5px; font-weight:600; text-transform:uppercase; letter-spacing:.04em; color:#1c7a35; background:#eafaef; padding:3px 9px; border-radius:980px; white-space:nowrap; }
  .who .by.tmpl{ color:#5b5b60; background:#f0f0f2; }
  .role{ color:var(--ink2); font-size:12.5px; margin:3px 0 10px; }
  .subj{ font-weight:600; font-size:13.5px; margin-bottom:8px; }
  .subj span{ color:var(--ink3); font-weight:400; }
  .body{ white-space:pre-wrap; font-size:13px; line-height:1.55; color:#3a3a3c; border-top:1px solid var(--line); padding-top:10px; }
  .empty{ color:var(--ink3); font-size:15px; padding:40px 0; }
</style>
</head>
<body>
<div class="top">
  <div class="grow">
    <h1>Bobby, the AI Emailer <a class="back" href="/" style="font-weight:400;font-size:13px;margin-left:10px;">&larr; Dashboard</a></h1>
    <div class="sub" id="sub">Starting…</div>
  </div>
  <button class="btn primary" id="sendBtn" onclick="sendAll()" disabled>Send All</button>
</div>
<div class="wrap">
  <div id="banner"></div>
  <div id="steps"><div class="empty" id="loading">Loading…</div></div>
</div>
<script>
function esc(s){ return String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }
let _rendered = false;

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
  const haveDrafts = !!(sum && (sum.drafted||0) > 0);
  if (s.active){
    banner.className='banner run'; banner.innerHTML=`<span class="spin"></span>${esc(s.message||'Working…')}`;
  } else if (s.phase==='error' || (s.error && !s.done)){
    banner.className='banner err'; banner.textContent = s.message || s.error || 'Bobby stopped.';
  } else if (haveDrafts){
    banner.className='banner ok'; banner.textContent = s.message || 'Drafts ready. Review below, then Send All.';
  } else {
    banner.className=''; banner.textContent='';
  }
  // Send All is available whenever drafts exist and Bobby isn't mid-run.
  sendBtn.disabled = s.active || !haveDrafts;

  // Render the step-grouped drafts once available (idempotent).
  if (sum && sum.steps && !_rendered){
    renderSteps(sum.steps);
    _rendered = true;
  }
  if (!sum && !s.active){
    document.getElementById('loading').textContent = 'No drafts yet — go back and click Run Bobby.';
  }
  if (s.active) setTimeout(poll, 1500);
}

function renderSteps(steps){
  const host = document.getElementById('steps');
  const withPeople = steps.filter(st => (st.people||[]).length);
  if (!withPeople.length){ host.innerHTML = '<div class="empty">No people are currently sitting on an email step in this cadence.</div>'; return; }
  host.innerHTML = withPeople.map(st => {
    const cards = (st.people||[]).map(p => `
      <div class="card">
        <div class="who"><span class="name">${esc(p.name)}</span>
          <span class="by ${p.written_by==='Claude'?'':'tmpl'}">${esc(p.written_by)}</span></div>
        <div class="role">${esc(p.title||'')}${p.company?' &middot; '+esc(p.company):''}${p.email?' &middot; '+esc(p.email):''}</div>
        <div class="subj"><span>Subject:</span> ${esc(p.subject)}</div>
        <div class="body">${esc(p.body)}</div>
      </div>`).join('');
    return `<div class="stephead"><span class="badge">Day ${st.day}</span><h2>${esc(st.display_name||st.name)}</h2>
              <span class="cnt">${(st.people||[]).length} person(s)</span></div>
            <div class="grid">${cards}</div>`;
  }).join('');
}

async function sendAll(){
  const btn = document.getElementById('sendBtn');
  if (!confirm('Send every drafted email in Salesloft, one by one? This actually sends to prospects.')) return;
  btn.disabled = true; const old = btn.textContent; btn.textContent = 'Sending…';
  let body;
  try { body = await (await fetch('/api/bobby/send',{method:'POST'})).json(); }
  catch(e){ body = {ok:false, error:String(e)}; }
  btn.textContent = old; btn.disabled = false;
  const banner = document.getElementById('banner');
  if (body.ok){ banner.className='banner ok'; banner.textContent = body.message || 'Sent.'; }
  else { banner.className='banner err'; banner.textContent = body.error || 'Could not send.'; }
}

poll();

// Leaving Bobby resets it — so returning starts clean (a fresh real-time run),
// never the previous cadence's presaved drafts. The reset endpoint no-ops while a
// run is genuinely in progress, so navigating away mid-run doesn't cancel it.
window.addEventListener('pagehide', () => {
  try { navigator.sendBeacon('/api/bobby/reset'); } catch(e){}
});
</script>
</body>
</html>
"""
