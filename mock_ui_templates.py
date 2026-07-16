"""Mock tool UIs for BobBee.

Wherever the real dashboard would open one of the external tools — the sign-in
windows for ISC / ZoomInfo / Salesloft, and Salesloft itself (to show contacts
being loaded into a cadence) — the clone shows one of these self-contained mock
pages instead of a real site. Rendered via Flask's render_template_string from
run_pipeline.py. Jinja, inline CSS, no external assets.

Dark theme, IBM Plex Sans, matching ui_templates.py's design system — each mock
tool keeps its own brand accent color (Salesloft purple, ZoomInfo red, ISC blue)
since those represent the third-party product being simulated, not BobBee itself.
"""

_FONTS = """<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
"""

# ── Shared chrome ─────────────────────────────────────────────────────────────
_BASE_CSS = """
  *{box-sizing:border-box}
  body{margin:0;font-family:'IBM Plex Sans',-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;
       color:#f2f2f3;background:#0a0a0c;-webkit-font-smoothing:antialiased}
  a{color:inherit}
  .badge{display:inline-block;font-size:11px;font-weight:600;padding:3px 9px;border-radius:4px;background:#212124;color:#a8a8ae}
  .mockbar{position:fixed;top:0;left:0;right:0;height:30px;background:#000;color:#e8e8ea;font-size:12px;
           display:flex;align-items:center;justify-content:center;gap:8px;z-index:50;
           box-shadow:0 1px 4px rgba(0,0,0,.3);border-bottom:1px solid #29292d}
  .mockbar b{color:#f1c21b;font-weight:600}
  .wrap{padding:56px 28px 40px}
  table{box-shadow:0 1px 2px rgba(0,0,0,.2), 0 8px 20px rgba(0,0,0,.25)}
"""

# ── Login window (ISC / ZoomInfo / Salesloft) ─────────────────────────────────
MOCK_LOGIN_TEMPLATE = _FONTS + """
<style>
""" + _BASE_CSS + """
  .loginwrap{min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px;
             background:radial-gradient(900px 460px at 50% 10%, color-mix(in srgb, var(--brand) 16%, transparent), transparent 65%)}
  .card{width:400px;max-width:calc(100vw - 32px);background:#18181b;border:1px solid #29292d;border-radius:12px;
        padding:34px 32px;box-shadow:0 12px 40px rgba(0,0,0,.4);text-align:center}
  .logo{width:60px;height:60px;border-radius:10px;margin:0 auto 18px;display:flex;align-items:center;
        justify-content:center;color:#fff;font-weight:800;font-size:24px;box-shadow:0 6px 16px rgba(0,0,0,.3)}
  h1{font-size:20px;margin:0 0 4px;font-weight:600}
  .sub{color:#a8a8ae;font-size:13.5px;margin:0 0 22px}
  form{display:flex;flex-direction:column;gap:10px;text-align:left}
  label{font-size:11.5px;font-weight:600;color:#a8a8ae;margin-bottom:-4px}
  input{font:inherit;font-size:14px;padding:11px 13px;border:1px solid #2b2b2f;border-radius:4px;
        background:#212124;color:#f2f2f3;transition:border-color .15s,box-shadow .15s}
  input:focus{outline:none;border-color:var(--brand);box-shadow:0 0 0 3px color-mix(in srgb, var(--brand) 22%, transparent)}
  button{margin-top:8px;font:inherit;font-weight:600;font-size:14px;color:#fff;background:var(--brand);
         border:none;border-radius:4px;padding:12px;cursor:pointer;transition:filter .15s,transform .1s}
  button:hover{filter:brightness(1.1)}
  button:active{transform:scale(.98)}
  .sso{margin-top:14px;font-size:12px;color:#77777d}
  .note{margin-top:18px;font-size:11.5px;color:#77777d;line-height:1.5}
</style>
<div class="mockbar">Mock — this is a simulated {{ label }} sign-in. No real credentials, no network.</div>
<div class="loginwrap" style="--brand:{{ brand }}">
  <div class="card">
    <div class="logo" style="background:{{ brand }}">{{ label[0] }}</div>
    <h1>Sign in to {{ label }}</h1>
    <p class="sub">Continue with your IBM W3ID</p>
    <form method="POST" action="/mock/{{ service }}/signin">
      <label>Email</label>
      <input type="email" name="email" value="{{ email }}" placeholder="you@ibm.com" required>
      <label>Password</label>
      <input type="password" name="password" placeholder="••••••••" value="demo">
      <button type="submit">Sign in</button>
    </form>
    <div class="sso">Single sign-on via IBM W3ID (simulated)</div>
    <div class="note">This window stands in for the real {{ label }} login the dashboard would open.
      Nothing you type here is stored or sent anywhere.</div>
  </div>
</div>
"""

MOCK_CONNECTED_TEMPLATE = _FONTS + """
<style>
""" + _BASE_CSS + """
  .wrap2{min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
  .card{width:420px;max-width:calc(100vw - 32px);background:#18181b;border:1px solid #29292d;border-radius:12px;
        padding:38px 32px;box-shadow:0 12px 40px rgba(0,0,0,.4);text-align:center}
  .check{width:60px;height:60px;border-radius:50%;background:{{ brand }};color:#fff;font-size:30px;
         display:flex;align-items:center;justify-content:center;margin:0 auto 18px}
  h1{font-size:20px;margin:0 0 6px;font-weight:600}
  p{color:#a8a8ae;font-size:14px;margin:0 0 22px}
  .btns{display:flex;gap:10px;justify-content:center;flex-wrap:wrap}
  .btn{font-weight:600;font-size:13.5px;text-decoration:none;padding:11px 16px;border-radius:4px}
  .primary{background:{{ brand }};color:#fff}
  .ghost{background:#212124;color:#f2f2f3;border:1px solid #2b2b2f}
</style>
<div class="mockbar">Mock — {{ label }} (simulated)</div>
<div class="wrap2">
  <div class="card">
    <div class="check">&check;</div>
    <h1>Connected to {{ label }}</h1>
    <p>Your {{ label }} session is active in this demo. You can close this tab and return to the dashboard.</p>
    <div class="btns">
      {% if service == 'salesloft' %}<a class="btn primary" href="/mock/salesloft">Open Salesloft &rarr;</a>{% endif %}
      {% if service == 'zoominfo' %}<a class="btn primary" href="/mock/zoominfo">Open ZoomInfo &rarr;</a>{% endif %}
      {% if service == 'isc' %}<a class="btn primary" href="/mock/isc">Open ISC &rarr;</a>{% endif %}
      <a class="btn ghost" href="javascript:window.close()">Close tab</a>
    </div>
  </div>
</div>
"""

# ── Mock Salesloft app (cadence + loaded members) ─────────────────────────────
MOCK_SALESLOFT_TEMPLATE = _FONTS + """
<style>
""" + _BASE_CSS + """
  :root{--brand:#8a3ffc}
  .top{position:fixed;top:30px;left:0;right:0;height:56px;background:var(--brand);color:#fff;display:flex;
       align-items:center;padding:0 22px;gap:12px;z-index:40}
  .top .mark{font-weight:700;font-size:17px;letter-spacing:-.01em}
  .top .me{margin-left:auto;font-size:12.5px;opacity:.9}
  .layout{display:flex;min-height:100vh;padding-top:86px}
  .side{width:260px;flex:none;border-right:1px solid #29292d;background:#111113;padding:16px 0}
  .side h3{font-size:11px;font-weight:600;color:#77777d;margin:8px 18px}
  .cad{display:block;padding:11px 18px;text-decoration:none;font-size:13.5px;border-left:3px solid transparent;color:#c8c8cd}
  .cad:hover{background:#18181b}
  .cad.active{background:#1c1730;border-left-color:var(--brand);font-weight:600;color:#f2f2f3}
  .cad .n{font-size:11.5px;color:#77777d}
  .main{flex:1;padding:24px 30px;min-width:0}
  .h{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap}
  .h h1{font-size:20px;margin:0;font-weight:600}
  .stats{display:flex;gap:12px;margin:16px 0 22px;flex-wrap:wrap}
  .stat{background:#18181b;border:1px solid #29292d;border-radius:8px;padding:12px 16px;min-width:120px}
  .stat .v{font-size:20px;font-weight:700;font-family:'IBM Plex Mono',ui-monospace,monospace}
  .stat .l{font-size:11.5px;color:#77777d}
  .steps{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:22px}
  .step{background:#18181b;border:1px solid #29292d;border-radius:6px;padding:8px 12px;font-size:12px;color:#c8c8cd}
  .step .d{color:#77777d}
  .step.email{border-color:#4c3480;background:#1c1730}
  table{width:100%;border-collapse:collapse;background:#18181b;border:1px solid #29292d;border-radius:8px;overflow:hidden}
  th,td{text-align:left;padding:11px 14px;font-size:13px;border-bottom:1px solid #29292d}
  th{background:#212124;font-size:11px;font-weight:600;color:#a8a8ae}
  tr:last-child td{border-bottom:none}
  .pill{font-size:11px;font-weight:600;padding:3px 9px;border-radius:4px}
  .pill.s1{background:#2c2145;color:#b490ff}
  .pill.call{background:#123821;color:#42be65}
  .empty{background:#18181b;border:1px dashed #2b2b2f;border-radius:8px;padding:40px;text-align:center;color:#77777d}
</style>
<div class="mockbar">Mock — simulated Salesloft. Contacts here were loaded by the dashboard's Fill Contacts action.</div>
<div class="top"><span class="mark">Salesloft</span><span class="badge" style="background:rgba(255,255,255,.15);color:#fff">Demo</span><span class="me">Demo Seller &middot; demo.seller@ibm.com</span></div>
<div class="layout">
  <div class="side">
    <h3>Team cadences</h3>
    {% for c in cadences %}
      <a class="cad {{ 'active' if c.name == selected else '' }}" href="/mock/salesloft?cadence={{ c.name|urlencode }}">
        {{ c.name }}<div class="n">{{ c.count }} member{{ '' if c.count == 1 else 's' }}</div>
      </a>
    {% endfor %}
  </div>
  <div class="main">
    <div class="h"><h1>{{ selected }}</h1><span class="badge">Team cadence</span></div>
    <div class="stats">
      <div class="stat"><div class="v">{{ total }}</div><div class="l">People</div></div>
      <div class="stat"><div class="v">{{ at_step1 }}</div><div class="l">At step 1</div></div>
      <div class="stat"><div class="v">{{ at_call }}</div><div class="l">At call step</div></div>
      <div class="stat"><div class="v">{{ email_steps }}</div><div class="l">Email steps</div></div>
    </div>
    <div class="steps">
      {% for s in steps %}
        <div class="step {{ 'email' if s.type == 'email' else '' }}">
          <span class="d">Day {{ s.day }}</span> &middot; {{ s.name }} <span class="d">({{ s.type }})</span>
        </div>
      {% endfor %}
    </div>
    {% if members %}
    <table>
      <thead><tr><th>Name</th><th>Title</th><th>Company</th><th>Current step</th><th>Added</th></tr></thead>
      <tbody>
        {% for m in members %}
        <tr>
          <td>{{ m.first_name }} {{ m.last_name }}</td>
          <td>{{ m.title }}</td>
          <td>{{ m.company }}</td>
          <td><span class="pill {{ 'call' if m.step == 'Call' else 's1' }}">{{ m.step }}</span></td>
          <td>{{ m.added_at }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
    {% else %}
    <div class="empty">No one is loaded into this cadence yet.<br>
      Run Fill Contacts on the dashboard to load contacts here.</div>
    {% endif %}
  </div>
</div>
"""

# ── Mock ZoomInfo (company view of the demo's accounts) ────────────────────────
MOCK_ZOOMINFO_TEMPLATE = _FONTS + """
<style>
""" + _BASE_CSS + """
  .top{position:fixed;top:30px;left:0;right:0;height:56px;background:#e5352b;color:#fff;display:flex;
       align-items:center;padding:0 22px;gap:12px;z-index:40}
  .top .mark{font-weight:700;font-size:17px}
  .wrap{padding:100px 30px 40px}
  h1{font-size:20px;margin:0 0 4px;font-weight:600}
  .sub{color:#a8a8ae;margin:0 0 20px;font-size:13.5px}
  table{width:100%;border-collapse:collapse;background:#18181b;border:1px solid #29292d;border-radius:8px;overflow:hidden}
  th,td{text-align:left;padding:11px 14px;font-size:13px;border-bottom:1px solid #29292d}
  th{background:#241a19;font-size:11px;font-weight:600;color:#e08a85}
  tr:last-child td{border-bottom:none}
  td.num{text-align:right;font-variant-numeric:tabular-nums;font-family:'IBM Plex Mono',ui-monospace,monospace}
</style>
<div class="mockbar">Mock — simulated ZoomInfo. Company revenue/employee data is synthetic.</div>
<div class="top"><span class="mark">ZoomInfo</span><span class="badge" style="background:rgba(255,255,255,.15);color:#fff">Demo</span></div>
<div class="wrap">
  <h1>Companies</h1>
  <p class="sub">{{ rows|length }} companies in the current territory (Infra Outbound buyer group)</p>
  <table>
    <thead><tr><th>Company</th><th>Industry</th><th>Domain</th><th>Revenue</th><th>Employees</th></tr></thead>
    <tbody>
      {% for r in rows %}
      <tr><td>{{ r.name }}</td><td>{{ r.industry }}</td><td>{{ r.domain }}</td>
          <td class="num">{{ r.revenue }}</td><td class="num">{{ r.employees }}</td></tr>
      {% endfor %}
    </tbody>
  </table>
</div>
"""

# ── Mock ISC / Salesforce (account list) ──────────────────────────────────────
MOCK_ISC_TEMPLATE = _FONTS + """
<style>
""" + _BASE_CSS + """
  .top{position:fixed;top:30px;left:0;right:0;height:56px;background:#0176d3;color:#fff;display:flex;
       align-items:center;padding:0 22px;gap:12px;z-index:40}
  .top .mark{font-weight:700;font-size:17px}
  .wrap{padding:100px 30px 40px}
  h1{font-size:20px;margin:0 0 4px;font-weight:600}
  .sub{color:#a8a8ae;margin:0 0 20px;font-size:13.5px}
  table{width:100%;border-collapse:collapse;background:#18181b;border:1px solid #29292d;border-radius:8px;overflow:hidden}
  th,td{text-align:left;padding:11px 14px;font-size:13px;border-bottom:1px solid #29292d}
  th{background:#16232e;font-size:11px;font-weight:600;color:#5b96ff}
  tr:last-child td{border-bottom:none}
  .st{font-size:11px;font-weight:600;padding:3px 8px;border-radius:4px;background:#16233f;color:#7c9cff}
</style>
<div class="mockbar">Mock — simulated ISC (Salesforce Territory Prospecting). Accounts are synthetic.</div>
<div class="top"><span class="mark">ISC</span><span class="badge" style="background:rgba(255,255,255,.15);color:#fff">Territory Prospecting</span></div>
<div class="wrap">
  <h1>Accounts</h1>
  <p class="sub">{{ rows|length }} accounts across your coverage IDs</p>
  <table>
    <thead><tr><th>Account name</th><th>Coverage ID</th><th>Industry</th><th>Tech client status</th><th>Contacts</th></tr></thead>
    <tbody>
      {% for r in rows %}
      <tr><td>{{ r.name }}</td><td>{{ r.coverage }}</td><td>{{ r.industry }}</td>
          <td><span class="st">{{ r.status }}</span></td><td>{{ r.contacts }}</td></tr>
      {% endfor %}
    </tbody>
  </table>
</div>
"""
