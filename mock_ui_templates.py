"""Mock tool UIs for the WatsonX Clone.

Wherever the real dashboard would open one of the external tools — the sign-in
windows for ISC / ZoomInfo / Salesloft, and Salesloft itself (to show contacts
being loaded into a cadence) — the clone shows one of these self-contained mock
pages instead of a real site. Rendered via Flask's render_template_string from
run_pipeline.py. Jinja, inline CSS, no external assets.
"""

# ── Shared chrome ─────────────────────────────────────────────────────────────
_BASE_CSS = """
  *{box-sizing:border-box}
  body{margin:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
       color:#1d1d1f;background:#f5f5f7}
  a{color:inherit}
  .badge{display:inline-block;font-size:11px;font-weight:600;letter-spacing:.04em;text-transform:uppercase;
         padding:3px 8px;border-radius:999px;background:#eee;color:#555}
  .mockbar{position:fixed;top:0;left:0;right:0;height:30px;background:#111;color:#fff;font-size:12px;
           display:flex;align-items:center;justify-content:center;gap:8px;z-index:50;letter-spacing:.02em}
  .mockbar b{color:#ffd60a}
  .wrap{padding:56px 28px 40px}
"""

# ── Login window (ISC / ZoomInfo / Salesloft) ─────────────────────────────────
MOCK_LOGIN_TEMPLATE = """
<style>
""" + _BASE_CSS + """
  .loginwrap{min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
  .card{width:400px;max-width:calc(100vw - 32px);background:#fff;border-radius:16px;padding:34px 32px;
        box-shadow:0 12px 40px rgba(0,0,0,.12);text-align:center}
  .logo{width:64px;height:64px;border-radius:16px;margin:0 auto 18px;display:flex;align-items:center;
        justify-content:center;color:#fff;font-weight:800;font-size:26px}
  h1{font-size:22px;margin:0 0 4px}
  .sub{color:#6e6e73;font-size:14px;margin:0 0 22px}
  form{display:flex;flex-direction:column;gap:10px;text-align:left}
  label{font-size:12px;font-weight:600;color:#6e6e73;margin-bottom:-4px}
  input{font:inherit;font-size:15px;padding:11px 13px;border:1px solid #d2d2d7;border-radius:10px}
  input:focus{outline:none;border-color:var(--brand)}
  button{margin-top:8px;font:inherit;font-weight:600;font-size:15px;color:#fff;background:var(--brand);
         border:none;border-radius:10px;padding:12px;cursor:pointer}
  .sso{margin-top:14px;font-size:12px;color:#86868b}
  .note{margin-top:18px;font-size:11.5px;color:#aeaeb2;line-height:1.5}
</style>
<div class="mockbar">🧪 <b>MOCK</b> — this is a simulated {{ label }} sign-in. No real credentials, no network.</div>
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
    <div class="sso">🔒 Single sign-on via IBM W3ID (simulated)</div>
    <div class="note">This window stands in for the real {{ label }} login the dashboard would open.
      Nothing you type here is stored or sent anywhere.</div>
  </div>
</div>
"""

MOCK_CONNECTED_TEMPLATE = """
<style>
""" + _BASE_CSS + """
  .wrap2{min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
  .card{width:420px;max-width:calc(100vw - 32px);background:#fff;border-radius:16px;padding:38px 32px;
        box-shadow:0 12px 40px rgba(0,0,0,.12);text-align:center}
  .check{width:66px;height:66px;border-radius:50%;background:{{ brand }};color:#fff;font-size:34px;
         display:flex;align-items:center;justify-content:center;margin:0 auto 18px}
  h1{font-size:22px;margin:0 0 6px}
  p{color:#6e6e73;font-size:14.5px;margin:0 0 22px}
  .btns{display:flex;gap:10px;justify-content:center;flex-wrap:wrap}
  .btn{font-weight:600;font-size:14px;text-decoration:none;padding:11px 16px;border-radius:10px}
  .primary{background:{{ brand }};color:#fff}
  .ghost{background:#f0f0f2;color:#1d1d1f}
</style>
<div class="mockbar">🧪 <b>MOCK</b> — {{ label }} (simulated)</div>
<div class="wrap2">
  <div class="card">
    <div class="check">✓</div>
    <h1>Connected to {{ label }}</h1>
    <p>Your {{ label }} session is active in this demo. You can close this tab and return to the dashboard.</p>
    <div class="btns">
      {% if service == 'salesloft' %}<a class="btn primary" href="/mock/salesloft">Open Salesloft →</a>{% endif %}
      {% if service == 'zoominfo' %}<a class="btn primary" href="/mock/zoominfo">Open ZoomInfo →</a>{% endif %}
      {% if service == 'isc' %}<a class="btn primary" href="/mock/isc">Open ISC →</a>{% endif %}
      <a class="btn ghost" href="javascript:window.close()">Close tab</a>
    </div>
  </div>
</div>
"""

# ── Mock Salesloft app (cadence + loaded members) ─────────────────────────────
MOCK_SALESLOFT_TEMPLATE = """
<style>
""" + _BASE_CSS + """
  :root{--brand:#6b4ce6}
  .top{position:fixed;top:30px;left:0;right:0;height:56px;background:var(--brand);color:#fff;display:flex;
       align-items:center;padding:0 22px;gap:12px;z-index:40}
  .top .mark{font-weight:800;font-size:18px;letter-spacing:-.01em}
  .top .me{margin-left:auto;font-size:13px;opacity:.9}
  .layout{display:flex;min-height:100vh;padding-top:86px}
  .side{width:270px;flex:none;border-right:1px solid #e5e5ea;background:#fff;padding:16px 0}
  .side h3{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:#86868b;margin:8px 18px}
  .cad{display:block;padding:11px 18px;text-decoration:none;font-size:14px;border-left:3px solid transparent}
  .cad:hover{background:#faf9ff}
  .cad.active{background:#f3f0ff;border-left-color:var(--brand);font-weight:600}
  .cad .n{font-size:12px;color:#86868b}
  .main{flex:1;padding:24px 30px;min-width:0}
  .h{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap}
  .h h1{font-size:22px;margin:0}
  .stats{display:flex;gap:12px;margin:16px 0 22px;flex-wrap:wrap}
  .stat{background:#fff;border:1px solid #e5e5ea;border-radius:12px;padding:12px 16px;min-width:120px}
  .stat .v{font-size:22px;font-weight:700}
  .stat .l{font-size:12px;color:#86868b}
  .steps{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:22px}
  .step{background:#fff;border:1px solid #e5e5ea;border-radius:10px;padding:8px 12px;font-size:12.5px}
  .step .d{color:#86868b}
  .step.email{border-color:#c9b8ff;background:#faf8ff}
  table{width:100%;border-collapse:collapse;background:#fff;border:1px solid #e5e5ea;border-radius:12px;overflow:hidden}
  th,td{text-align:left;padding:11px 14px;font-size:13.5px;border-bottom:1px solid #f0f0f2}
  th{background:#faf9ff;font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:#86868b}
  tr:last-child td{border-bottom:none}
  .pill{font-size:11px;font-weight:600;padding:3px 9px;border-radius:999px}
  .pill.s1{background:#e9e3ff;color:#5b34d6}
  .pill.call{background:#d6f5e0;color:#1c7a45}
  .empty{background:#fff;border:1px dashed #d2d2d7;border-radius:12px;padding:40px;text-align:center;color:#86868b}
</style>
<div class="mockbar">🧪 <b>MOCK</b> — simulated Salesloft. Contacts here were loaded by the dashboard's <b>Fill Contacts</b> action.</div>
<div class="top"><span class="mark">Salesloft</span><span class="badge" style="background:rgba(255,255,255,.2);color:#fff">Demo</span><span class="me">Demo Seller · demo.seller@ibm.com</span></div>
<div class="layout">
  <div class="side">
    <h3>Team Cadences</h3>
    {% for c in cadences %}
      <a class="cad {{ 'active' if c.name == selected else '' }}" href="/mock/salesloft?cadence={{ c.name|urlencode }}">
        {{ c.name }}<div class="n">{{ c.count }} member{{ '' if c.count == 1 else 's' }}</div>
      </a>
    {% endfor %}
  </div>
  <div class="main">
    <div class="h"><h1>{{ selected }}</h1><span class="badge">Team Cadence</span></div>
    <div class="stats">
      <div class="stat"><div class="v">{{ total }}</div><div class="l">People</div></div>
      <div class="stat"><div class="v">{{ at_step1 }}</div><div class="l">At Step 1</div></div>
      <div class="stat"><div class="v">{{ at_call }}</div><div class="l">At Call step</div></div>
      <div class="stat"><div class="v">{{ email_steps }}</div><div class="l">Email steps</div></div>
    </div>
    <div class="steps">
      {% for s in steps %}
        <div class="step {{ 'email' if s.type == 'email' else '' }}">
          <span class="d">Day {{ s.day }}</span> · {{ s.name }} <span class="d">({{ s.type }})</span>
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
      Run <b>Fill Contacts to SalesLoft</b> on the dashboard to load contacts here.</div>
    {% endif %}
  </div>
</div>
"""

# ── Mock ZoomInfo (company view of the demo's accounts) ────────────────────────
MOCK_ZOOMINFO_TEMPLATE = """
<style>
""" + _BASE_CSS + """
  .top{position:fixed;top:30px;left:0;right:0;height:56px;background:#e5352b;color:#fff;display:flex;
       align-items:center;padding:0 22px;gap:12px;z-index:40}
  .top .mark{font-weight:800;font-size:18px}
  .wrap{padding:100px 30px 40px}
  h1{font-size:22px;margin:0 0 4px}
  .sub{color:#6e6e73;margin:0 0 20px;font-size:14px}
  table{width:100%;border-collapse:collapse;background:#fff;border:1px solid #e5e5ea;border-radius:12px;overflow:hidden}
  th,td{text-align:left;padding:11px 14px;font-size:13.5px;border-bottom:1px solid #f0f0f2}
  th{background:#fff5f4;font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:#b23b3b}
  tr:last-child td{border-bottom:none}
  td.num{text-align:right;font-variant-numeric:tabular-nums}
</style>
<div class="mockbar">🧪 <b>MOCK</b> — simulated ZoomInfo. Company revenue/employee data is synthetic.</div>
<div class="top"><span class="mark">ZoomInfo</span><span class="badge" style="background:rgba(255,255,255,.2);color:#fff">Demo</span></div>
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
MOCK_ISC_TEMPLATE = """
<style>
""" + _BASE_CSS + """
  .top{position:fixed;top:30px;left:0;right:0;height:56px;background:#0176d3;color:#fff;display:flex;
       align-items:center;padding:0 22px;gap:12px;z-index:40}
  .top .mark{font-weight:800;font-size:18px}
  .wrap{padding:100px 30px 40px}
  h1{font-size:22px;margin:0 0 4px}
  .sub{color:#6e6e73;margin:0 0 20px;font-size:14px}
  table{width:100%;border-collapse:collapse;background:#fff;border:1px solid #e5e5ea;border-radius:12px;overflow:hidden}
  th,td{text-align:left;padding:11px 14px;font-size:13.5px;border-bottom:1px solid #f0f0f2}
  th{background:#eef6fd;font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:#0d6ab5}
  tr:last-child td{border-bottom:none}
  .st{font-size:11px;font-weight:600;padding:3px 8px;border-radius:999px;background:#eef;color:#3452b4}
</style>
<div class="mockbar">🧪 <b>MOCK</b> — simulated ISC (Salesforce Territory Prospecting). Accounts are synthetic.</div>
<div class="top"><span class="mark">ISC</span><span class="badge" style="background:rgba(255,255,255,.2);color:#fff">Territory Prospecting</span></div>
<div class="wrap">
  <h1>Accounts</h1>
  <p class="sub">{{ rows|length }} accounts across your coverage IDs</p>
  <table>
    <thead><tr><th>Account Name</th><th>Coverage ID</th><th>Industry</th><th>Tech Client Status</th><th>Contacts</th></tr></thead>
    <tbody>
      {% for r in rows %}
      <tr><td>{{ r.name }}</td><td>{{ r.coverage }}</td><td>{{ r.industry }}</td>
          <td><span class="st">{{ r.status }}</span></td><td>{{ r.contacts }}</td></tr>
      {% endfor %}
    </tbody>
  </table>
</div>
"""
