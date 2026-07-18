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
    /* Carbon Gray 100 dark theme — the *neutral* ramp used across IBM product
       UI. (Cool gray reads green-tinted on screen; that was the wrong ramp.) */
    --bg:#161616; --layer1:#262626; --layer2:#393939; --layer3:#525252;
    --border:#393939; --border-strong:#6f6f6f;
    --header-bg:#161616;
    /* Bright type ramp — gray body text was hard to read on the dark layers, so
       hierarchy stays in the top three Carbon steps and never dims below #c6c6c6. */
    --text1:#ffffff; --text2:#f4f4f4; --text3:#c6c6c6;
    --blue:#0f62fe; --blue-text:#78a9ff; --blue-soft:rgba(15,98,254,.14); --blue-border:rgba(120,169,255,.4);
    --purple:#8a3ffc; --purple-text:#be95ff; --purple-soft:rgba(138,63,252,.14); --purple-border:rgba(190,149,255,.4);
    --green:#42be65; --amber:#f1c21b; --red:#fa4d56;
    /* Gradients. IBM's brand gradient runs blue 60 → purple 60; keep every
       gradient on that axis so "futuristic" never drifts off-palette. Surface
       gradients stay near-black so they read as depth, not as color. */
    --grad-brand:linear-gradient(135deg,#0f62fe 0%,#8a3ffc 100%);
    --grad-brand-soft:linear-gradient(135deg,rgba(15,98,254,.18) 0%,rgba(138,63,252,.18) 100%);
    --grad-surface:linear-gradient(160deg,#262626 0%,#1c1c1c 100%);
    --grad-glow:radial-gradient(900px 420px at 15% -10%,rgba(15,98,254,.16),transparent 60%),
                radial-gradient(760px 400px at 95% 0%,rgba(138,63,252,.13),transparent 62%);
    /* IBM Carbon: sharp, rectangular corners everywhere. */
    --r-sm:0; --r-md:0; --r-lg:0;
    --font:'IBM Plex Sans',-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;
    --mono:'IBM Plex Mono',ui-monospace,'SF Mono',Menlo,monospace;
  }
  *{ box-sizing:border-box; }
  html,body{ background:var(--bg); }
  body{ font-family:var(--font); color:var(--text1); margin:0; font-size:15px; line-height:1.55; -webkit-font-smoothing:antialiased; }
  ::selection{ background:rgba(91,150,255,.3); }
  ::-webkit-scrollbar{ width:10px; height:10px; }
  ::-webkit-scrollbar-track{ background:transparent; }
  ::-webkit-scrollbar-thumb{ background:var(--border-strong); border-radius:0; border:2px solid transparent; background-clip:content-box; }
  a{ color:var(--blue-text); }
  h1,h2,h3{ font-weight:600; letter-spacing:-.01em; margin:0; color:var(--text1); }
  .mono{ font-family:var(--mono); }

  .btn{ font:inherit; font-size:14.5px; font-weight:500; color:var(--text1); background:var(--layer2);
        border:1px solid var(--border); border-radius:var(--r-sm); padding:9px 16px; cursor:pointer;
        transition:background .15s,border-color .15s,transform .08s; white-space:nowrap; }
  .btn:hover{ background:var(--layer3); border-color:var(--border-strong); }
  .btn:active{ transform:scale(.98); }
  .btn.primary{ background:var(--blue); border-color:var(--blue); color:#fff; }
  .btn.primary:hover{ background:#0353e9; border-color:#0353e9; }
  .btn.primary:disabled,.btn:disabled{ background:var(--layer1); border-color:var(--border); color:var(--text3); cursor:not-allowed; }
  .btn.ai{ background:var(--purple); border-color:var(--purple); color:#fff; }
  .btn.ai:hover{ background:#7a2ff0; }
  .btn.big{ padding:11px 20px; font-size:15px; width:100%; }
  .link{ color:var(--blue-text); font-size:14.5px; font-weight:500; cursor:pointer; background:none; border:none; padding:0; font-family:inherit; }
  .link:hover{ text-decoration:underline; }

  .card{ background:var(--layer1); border:1px solid var(--border); border-radius:var(--r-lg); }

  .badge{ display:inline-flex; align-items:center; gap:5px; font-size:12.5px; font-weight:500; padding:4px 10px;
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

  table{ border-collapse:separate; border-spacing:0; width:100%; font-size:13.5px; background:var(--layer1);
         border:1px solid var(--border); border-radius:var(--r-md); overflow:hidden; }
  th,td{ padding:10px 14px; text-align:left; border-bottom:1px solid var(--border); vertical-align:top; }
  th{ background:var(--layer2); font-weight:600; color:var(--text2); cursor:pointer; white-space:nowrap; }
  th:hover{ color:var(--text1); }
  tr:hover td{ background:var(--layer2); }
  tr:last-child td{ border-bottom:none; }

  input[type=text],input[type=email],input[type=password]{ font:inherit; font-size:15px; border:1px solid var(--border);
         border-radius:var(--r-sm); padding:10px 13px; background:var(--layer2); color:var(--text1);
         transition:border-color .15s,background .15s; }
  input:focus{ outline:none; border-color:var(--blue-text); background:var(--layer1); box-shadow:0 0 0 3px var(--blue-soft); }
  select{ font:inherit; font-size:14.5px; border:1px solid var(--border); border-radius:var(--r-sm); padding:8px 13px;
          background:var(--layer2); color:var(--text1); cursor:pointer; width:100%; }
"""

PAGE_TEMPLATE = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>IBM BobBee</title>
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

  /* ── profile page ───────────────────────────────────────────── */
  .profile-page{ max-width:1360px; }

  /* ── w3-style identity header ───────────────────────────────── */
  /* w3 renders the person's name very large and very light. */
  .w3-name{ font-size:68px; font-weight:300; letter-spacing:-.01em; line-height:1.15; }
  .w3-head{ display:flex; gap:28px; align-items:flex-start; padding-bottom:26px; }
  .w3-avatar{ width:132px; height:132px; flex:none; display:flex; align-items:center;
              justify-content:center; font-size:34px; font-weight:500; color:#fff;
              background:var(--grad-brand); letter-spacing:.02em; }
  .w3-ident{ min-width:0; padding-top:4px; }
  /* w3 sets the role line large and light, above a small function label. */
  .w3-role{ font-size:23px; font-weight:300; color:var(--text1); line-height:1.3; }
  .w3-fn{ font-size:15px; font-weight:300; color:var(--text2); margin-top:4px; }
  .w3-loc{ margin-top:22px; font-size:14px; color:var(--text2); display:flex;
           align-items:center; gap:10px; flex-wrap:wrap; }
  .w3-sep{ color:var(--border-strong); }
  .w3-org{ font-size:14px; color:var(--text2); margin-top:8px; }
  .w3-meta{ font-size:14px; color:var(--text2); margin-top:3px; }
  .w3-link{ color:var(--blue-text); text-decoration:none; }
  .w3-link:hover{ text-decoration:underline; }
  .w3-contact{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr));
               gap:14px; padding:24px 0 28px; border-top:1px solid var(--border); }
  .w3-ctile{ background:var(--layer1); border:1px solid var(--border); padding:18px 20px 20px; }
  .w3-ctile.off{ opacity:.5; }
  .w3-cicon{ width:38px; height:38px; display:flex; align-items:center; justify-content:center;
             border-radius:50%; background:var(--layer2); color:var(--text2); font-size:17px;
             margin-bottom:26px; }
  .w3-cicon.blue{ background:var(--grad-brand); color:#fff; }
  .w3-cicon.purple{ background:linear-gradient(135deg,#8a3ffc,#be95ff); color:#fff; }
  .w3-clabel{ font-size:12.5px; color:var(--text3); margin-bottom:3px; }
  .w3-cval{ font-size:13.5px; color:var(--text2); }

  /* Details column + sticky map column. */
  .prof-split{ display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1fr); gap:20px;
               align-items:start; }
  /* Not sticky — both columns scroll together so the two sides stay level. */
  .prof-aside{ min-width:0; }
  .map-card{ margin-bottom:0; }
  .map-card .usmap{ max-width:none; }
  .seg-wrap{ flex-wrap:wrap; }
  @media(max-width:1080px){ .prof-split{ grid-template-columns:1fr; } }

  .w3-rows{ display:flex; flex-direction:column; }
  .w3-row{ display:grid; grid-template-columns:minmax(120px,34%) 1fr; gap:16px;
           padding:11px 0; border-bottom:1px solid var(--border); font-size:13.5px; }
  .w3-row:last-child{ border-bottom:none; }
  .w3-row .k{ color:var(--text3); }
  .w3-row .v{ color:var(--text2); }
  .w3-row .dim{ color:var(--text3); font-size:12.5px; }
  .w3-exp{ display:flex; flex-direction:column; gap:18px; }
  .w3-expitem{ padding-left:12px; border-left:2px solid transparent; border-image:var(--grad-brand) 1; }
  .w3-expname{ font-size:13.5px; font-weight:600; color:var(--text1); }
  .w3-expdesc{ font-size:12.5px; color:var(--text3); margin:4px 0 8px; line-height:1.5; }
  .w3-creds{ display:flex; flex-direction:column; gap:10px; }
  .w3-cred{ font-size:13px; color:var(--text2); padding:11px 14px; background:var(--layer2);
            border-left:2px solid transparent; border-image:var(--grad-brand) 1; }
  .profile-tabs{ display:flex; gap:0; border-bottom:1px solid var(--border); margin-bottom:28px; }
  .profile-tab{ font:inherit; font-size:13.5px; font-weight:500; color:var(--text3); background:none; border:none;
                border-bottom:2px solid transparent; cursor:pointer; padding:10px 20px; margin-bottom:-1px; }
  .profile-tab:hover{ color:#fff; }
  /* Same blue indicator as the vertical section nav, laid horizontally. */
  .profile-tab.active{ color:#fff; border-bottom-color:var(--blue); }
  .profile-section{ display:none; }
  .profile-section.active{ display:block; }
  .prof-card{ background:var(--layer1); border:1px solid var(--border); padding:24px 26px; margin-bottom:16px; }
  .prof-card-head{ display:flex; align-items:center; justify-content:space-between; margin-bottom:18px; }
  .prof-card-head h3{ font-size:14px; font-weight:600; margin:0; }
  .field-grid{ display:grid; grid-template-columns:1fr 1fr; gap:14px 20px; }
  .field-grid.single{ grid-template-columns:1fr; }
  .field{ display:flex; flex-direction:column; gap:5px; }
  .field label{ font-size:12px; font-weight:600; color:var(--text3); }
  .field input[type=text],.field input[type=email],.field textarea,.field select{
    font:inherit; font-size:13.5px; border:1px solid var(--border); background:var(--layer2);
    color:#fff; padding:9px 12px; outline:none; width:100%; resize:vertical; }
  .field input:focus,.field textarea:focus,.field select:focus{
    border-color:var(--blue-text); box-shadow:0 0 0 2px var(--blue-soft); }
  .field input[readonly]{ color:var(--text3); background:var(--layer1); cursor:default; }
  .field textarea{ min-height:80px; font-family:var(--font); font-size:13px; line-height:1.55; }
  .field .hint{ font-size:11.5px; color:var(--text3); margin-top:2px; }
  .pref-row{ display:flex; align-items:center; gap:14px; padding:11px 0; border-top:1px solid var(--border); }
  .pref-row:first-of-type{ border-top:none; }
  .pref-row label{ font-size:13px; flex:1; min-width:0; }
  .pref-row .pref-hint{ font-size:11.5px; color:var(--text3); }
  .pref-row input[type=number]{ width:72px; font:inherit; font-size:13.5px; border:1px solid var(--border);
    background:var(--layer2); color:#fff; padding:7px 10px; outline:none; text-align:center; }
  .pref-row input[type=number]:focus{ border-color:var(--blue-text); }
  .pref-row select{ width:180px; font:inherit; font-size:13px; border:1px solid var(--border);
    background:var(--layer2); color:#fff; padding:7px 10px; outline:none; }
  .reset-link{ font:inherit; font-size:12px; color:var(--text3); background:none; border:none; cursor:pointer; padding:0; text-decoration:underline; }
  .reset-link:hover{ color:#fff; }
  /* Purple = watsonx output. Personalization is entirely about model behaviour,
     so it carries the accent as a whole rather than only on individual controls. */
  .ai-note{ display:flex; gap:12px; align-items:flex-start; padding:14px 16px; margin-bottom:18px;
            background:var(--grad-brand-soft); border-left:2px solid var(--purple);
            font-size:13px; color:var(--text2); line-height:1.55; }
  .ai-note-mark{ color:var(--purple-text); flex:none; display:flex; padding-top:1px; }
  .ai-note b{ color:var(--purple-text); font-weight:600; }
  #ptab-personalization .prof-card{ border-left:2px solid var(--purple-border); }
  #ptab-personalization .prof-card-head h3{ color:var(--purple-text); }

  /* ── Settings tab: sidebar + section body ───────────────────── */
  .set-split{ display:grid; grid-template-columns:236px minmax(0,1fr); gap:24px; align-items:start; }
  .set-nav{ display:flex; flex-direction:column; border:1px solid var(--border); background:var(--layer1); }
  .set-navlink{ font:inherit; font-size:13.5px; text-align:left; color:var(--text2); background:none;
                border:none; border-left:2px solid transparent; cursor:pointer; padding:12px 16px;
                border-bottom:1px solid var(--border); transition:background .12s,color .12s; }
  .set-navlink:last-child{ border-bottom:none; }
  .set-navlink:hover{ background:var(--layer2); color:#fff; }
  .set-navlink.active{ color:#fff; background:var(--layer2); border-left-color:var(--blue); font-weight:600; }
  /* Every section is rendered; the sidebar scrolls to one rather than swapping
     which is mounted, so you can also just read straight down the page. */
  .set-sec{ display:block; scroll-margin-top:72px; margin-bottom:28px; }
  .set-sec:last-child{ margin-bottom:0; }
  .set-nav{ position:sticky; top:70px; }
  .set-p{ font-size:13.5px; color:var(--text2); line-height:1.62; margin:0 0 10px; }
  .set-steps{ margin:6px 0 0; padding-left:20px; display:flex; flex-direction:column; gap:11px; }
  .set-steps li{ font-size:13px; color:var(--text2); line-height:1.6; }
  .set-list{ margin:4px 0 12px; padding-left:20px; display:flex; flex-direction:column; gap:7px; }
  .set-list li{ font-size:13px; color:var(--text2); line-height:1.6; }
  @media(max-width:900px){ .set-split{ grid-template-columns:1fr; } }

  .access-link{ display:inline-flex; align-items:center; gap:6px; font-size:13px; color:var(--blue-text); background:none;
                border:none; cursor:pointer; font:inherit; padding:0; margin-top:4px; }
  .access-link:hover{ text-decoration:underline; }
  @media(max-width:640px){ .field-grid{ grid-template-columns:1fr; } }

  /* ── top bar ────────────────────────────────────────────────── */
  /* Carbon UI Shell: a 48px black bar, hairline bottom border, full-height nav
     items that carry a 3px brand-gradient underline when active. */
  /* w3-scale shell: a taller bar, a brand block that reads as its own tile on
     the left, and roomy nav items with a gradient underline when active. */
  .topbar{ position:sticky; top:0; z-index:50; height:56px; background:var(--header-bg);
           border-bottom:1px solid var(--border); display:flex; align-items:stretch;
           justify-content:space-between; padding:0; gap:0; }
  .brand{ display:flex; align-items:center; gap:11px; cursor:pointer; background:none; border:none;
          padding:0 20px; flex:none; border-right:1px solid var(--border); }
  .brand:hover{ background:var(--layer2); }
  .brand-logo{ width:29px; height:29px; flex:none; }
  /* Echoes the IBM wordmark's light+bold split ("IBM Platform" → "IBM BobBee"). */
  .brand-name{ font-size:17px; font-weight:400; letter-spacing:.01em; color:var(--text1);
               white-space:nowrap; }
  .brand-name b{ font-weight:600; }
  .topnav{ display:flex; align-items:stretch; gap:0; flex:none; }
  /* Every item the same width, so the bar reads as an even row of tabs rather
     than spacing that tracks word length. */
  .navlink{ font:inherit; font-size:14.5px; font-weight:400; color:var(--text2); background:none;
            border:none; cursor:pointer; padding:0 8px; width:118px; flex:none;
            position:relative; transition:background .11s,color .11s; }
  .navlink:hover{ color:#ffffff; background:var(--layer2); }
  .navlink.active{ color:#ffffff; background:var(--layer1); }
  .navlink.active::after{ content:''; position:absolute; left:0; right:0; bottom:0; height:3px;
                          background:var(--grad-brand); }
  /* w3-style global search: fills the bar between the nav and the avatar. */
  .topsearch{ flex:0 1 420px; display:flex; align-items:center; gap:12px; min-width:0;
              margin-left:auto; padding:0 18px; background:var(--layer1);
              border-left:1px solid var(--border); border-right:1px solid var(--border); }
  .topsearch svg{ width:18px; height:18px; flex:none; color:var(--text3); }
  .topsearch input{ flex:1; min-width:0; font:inherit; font-size:14.5px; background:none;
                    border:none; color:var(--text1); padding:0; height:36px; }
  .topsearch input::placeholder{ color:var(--text3); }
  .topsearch input:focus{ outline:none; }
  .topsearch:focus-within{ background:var(--layer2); box-shadow:inset 0 -2px 0 var(--blue); }
  .topbar-actions{ display:flex; align-items:stretch; flex:none; }
  .icon-btn{ width:48px; background:none; border:none; color:var(--text2); cursor:pointer;
             display:flex; align-items:center; justify-content:center; transition:background .11s,color .11s; }
  .icon-btn:hover{ background:var(--layer2); color:#ffffff; }
  .icon-btn svg{ width:20px; height:20px; }
  .profile-wrap{ position:relative; flex:none; display:flex; align-items:center; gap:10px;
                 padding:0 22px; border-left:1px solid var(--border); }
  .profile-btn{ width:44px; height:44px; border-radius:50%; background:var(--layer2); border:1px solid var(--border);
                color:var(--text1); font-size:12px; font-weight:600; font-family:var(--font); cursor:pointer;
                display:flex; align-items:center; justify-content:center; }
  .profile-btn:hover{ border-color:var(--border-strong); }
  .profile-menu{ position:absolute; top:calc(100% + 10px); right:0; background:var(--layer1); border:1px solid var(--border);
                 border-radius:var(--r-md); min-width:180px; box-shadow:0 16px 36px rgba(0,0,0,.45); display:none;
                 overflow:hidden; z-index:60; }
  .profile-menu.show{ display:block; }
  .profile-menu button{ display:block; width:100%; text-align:left; font:inherit; font-size:13.5px; color:var(--text1);
                         background:none; border:none; padding:11px 15px; cursor:pointer; }
  .profile-menu button:hover{ background:var(--layer2); }
  .detailsbtn{ position:relative; }
  .warndot{ position:absolute; top:4px; right:6px; width:8px; height:8px; border-radius:50%; background:var(--red);
            box-shadow:0 0 0 3px rgba(250,77,86,.18); }

  main{ max-width:1180px; margin:0 auto; padding:36px 28px 100px; }
  .page{ display:none; } .page.active{ display:block; }
  .page-head{ margin-bottom:24px; }
  .page-head h2{ font-size:24px; }
  .page-head p{ color:#ffffff; font-size:14.5px; margin:5px 0 0; }

  /* ── dashboard ──────────────────────────────────────────────── */
  .empty-state{ text-align:center; padding:70px 20px; background:var(--layer1); border:1px solid var(--border);
                border-radius:var(--r-lg); }
  .empty-state h3{ font-size:18px; margin-bottom:8px; }
  .empty-state p{ color:#ffffff; font-size:14px; margin:0 0 20px; }
  .empty-state .btn{ width:auto; }
  /* Same segmented control as the dashboard/profile toggles (.seg / .seg-btn) —
     one control style for "pick a view" everywhere in the app. */
  .range-toggle{ display:inline-flex; border:1px solid var(--border); margin-bottom:18px; }
  .range-btn{ font:inherit; font-size:12.5px; font-weight:500; color:var(--text3); background:none;
              border:none; border-right:1px solid var(--border); cursor:pointer; padding:7px 15px;
              transition:background .13s,color .13s; }
  .range-btn:last-child{ border-right:none; }
  .range-btn:hover{ color:#fff; background:var(--layer2); }
  .range-btn.active{ color:#fff; background:var(--grad-brand-soft); box-shadow:inset 0 -2px 0 var(--blue); }
  .aitem{ display:flex; align-items:center; gap:14px; padding:13px 16px; background:var(--layer1); border:1px solid var(--border);
          border-radius:var(--r-md); margin-bottom:8px; }
  .aitem .adate{ width:78px; flex:none; font-size:11px; color:var(--text3); font-family:var(--mono); }
  .aitem .aname{ flex:1; font-weight:500; font-size:13.5px; min-width:0; }
  .aitem .aplay{ font-size:11px; color:var(--text3); flex:none; }
  .aitems-empty{ color:var(--text3); font-size:13.5px; padding:26px; text-align:center; background:var(--layer1);
                 border:1px dashed var(--border); border-radius:var(--r-md); }
  .stub{ text-align:center; padding:110px 20px; color:#ffffff; }
  .stub h3{ color:#ffffff; font-size:18px; margin-bottom:6px; }

  /* ── accounts tab ───────────────────────────────────────────── */
  .accts-head{ display:flex; align-items:center; justify-content:space-between; gap:16px; margin-bottom:20px; }
  .accts-count{ color:#ffffff; font-size:13px; }
  .acct-list{ max-height:600px; overflow-y:auto; overflow-x:auto; border:1px solid var(--border);
              border-radius:var(--r-lg); background:var(--layer1); }
  /* Rows are grid, so they'd otherwise shrink-to-fit the scroll container. */
  .acct-list > .acct-row{ min-width:max-content; }
  /* Real grid, not flex: header and body rows share one column template set on
     the list (--acct-cols), so every cell lines up regardless of how many
     optional columns the current view shows or how long a value wraps. */
  .acct-row{ display:grid; grid-template-columns:var(--acct-cols); align-items:center;
             gap:0 14px; padding:11px 18px; border-bottom:1px solid var(--border); }
  .acct-row:last-child{ border-bottom:none; }
  .acct-row > span{ min-width:0; }
  .acct-row .arank{ font-family:var(--mono); font-size:12px; color:var(--text3); }
  .acct-row .an{ font-weight:500; font-size:13.5px; overflow:hidden; text-overflow:ellipsis;
                 white-space:nowrap; }
  .acct-row .ai,
  .acct-row .aloc{ color:var(--text3); font-size:12.5px; overflow:hidden;
                   text-overflow:ellipsis; white-space:nowrap; }
  .acct-row .aiv{ color:var(--text3); font-size:12px; overflow:hidden;
                  text-overflow:ellipsis; white-space:nowrap; }
  .acct-row .atags{ display:flex; gap:5px; flex-wrap:nowrap; justify-content:flex-end; }
  /* Carbon data-table header: sits on layer2, sticks while the list scrolls. */
  .acct-head{ position:sticky; top:0; z-index:2; background:var(--layer2); cursor:default;
              border-bottom:1px solid var(--border-strong); }
  .acct-head span{ font-size:11px !important; font-weight:600 !important; letter-spacing:.16px;
                   color:var(--text2) !important; }
  .acct-head .atags{ justify-content:flex-end; }

  .stages{ display:flex; flex-direction:column; gap:10px; margin-bottom:24px; }
  .stage{ display:flex; align-items:flex-start; gap:12px; padding:15px 18px; background:var(--layer1);
          border:1px solid var(--border); border-radius:var(--r-md); transition:border-color .2s,box-shadow .2s; }
  .stage.running{ border-color:var(--blue-border); box-shadow:0 0 0 3px var(--blue-soft); }
  .stage.done{ border-color:rgba(66,190,101,.32); }
  .stage.err{ border-color:rgba(250,77,86,.4); }
  .stage .sicon{ margin-top:2px; flex:none; }
  .stage .stitle{ font-weight:600; font-size:13.5px; }
  .stage .smsg{ color:var(--text3); font-size:12.5px; margin-top:3px; }

  .side-lists{ display:flex; gap:10px; margin-bottom:24px; }
  .side-badge{ font:inherit; font-size:12.5px; color:#ffffff; background:var(--layer1); border:1px solid var(--border);
               border-radius:var(--r-sm); padding:8px 14px; cursor:pointer; }
  .side-badge:hover{ border-color:var(--border-strong); color:#ffffff; }
  .side-badge b{ color:#ffffff; font-family:var(--mono); }

  .cad-finished{ margin-top:34px; padding-top:20px; border-top:1px solid var(--border); }
  .cad-finished-head{ display:flex; align-items:baseline; gap:12px; margin-bottom:14px; }
  .cad-finished-head h3{ font-size:14.5px; }
  .cad-finished-note{ font-size:12px; color:var(--text3); }
  .cad-finished .cad-card{ opacity:.66; }
  .cad-finished .cad-card:hover{ opacity:1; }

  .cadence-group{ margin-bottom:22px; }
  .cadence-head{ display:flex; align-items:center; gap:10px; margin-bottom:10px; }
  .cadence-head h3{ font-size:14.5px; }
  .cadence-head .cnt{ color:var(--text3); font-size:12px; }
  .acct-card{ display:flex; align-items:center; gap:14px; padding:12px 16px; background:var(--layer1);
              border:1px solid var(--border); border-radius:var(--r-md); margin-bottom:6px; }
  .acct-card .arank{ width:26px; flex:none; font-family:var(--mono); font-size:12px; color:var(--text3); text-align:center; }
  .acct-card .abody{ flex:1; min-width:0; }
  .acct-card .aname{ font-weight:500; font-size:13.5px; }
  .acct-card .ameta{ color:var(--text3); font-size:11.5px; margin-top:2px; }
  .acct-card .atags{ display:flex; gap:6px; flex-wrap:wrap; flex:none; max-width:340px; justify-content:flex-end; }
  /* Tags: white text on a transparent box (border-only), IBM Carbon style —
     the border color alone carries the category. */
  .tagpill{ font-size:10.5px; font-weight:500; color:#fff; background:transparent; border:1px solid var(--border-strong);
            border-radius:0; padding:3px 9px; white-space:nowrap; cursor:pointer; position:relative; }
  .tagpill.white{ border-color:var(--blue-border); }
  .tagpill.risk{ border-color:rgba(250,77,86,.55); }
  .tagpill.up{ border-color:rgba(66,190,101,.55); }
  .tagpill.on{ background:#fff; color:#0a0a0c; border-color:#fff; }
  /* tag tooltip */
  .tagpill[data-tip]:hover::after{
    content:attr(data-tip); position:absolute; bottom:calc(100% + 6px); left:50%; transform:translateX(-50%);
    background:var(--layer3); color:#fff; border:1px solid var(--border-strong);
    font-size:11px; font-weight:400; line-height:1.45; padding:6px 10px; white-space:normal;
    width:200px; z-index:100; pointer-events:none; text-align:left; }
  /* tag dots in account rows — compact colored circles replacing full pills */
  .tagdot{ display:inline-block; width:9px; height:9px; border-radius:50%; flex:none; cursor:default; position:relative; }
  .tagdot[data-tip]:hover::after{
    content:attr(data-tip); position:absolute; bottom:calc(100% + 6px); left:50%; transform:translateX(-50%);
    background:var(--layer3); color:#fff; border:1px solid var(--border-strong);
    font-size:11px; font-weight:400; line-height:1.45; padding:6px 10px; white-space:normal;
    width:190px; z-index:100; pointer-events:none; text-align:left; }
  .tagdot.white{ background:var(--blue-text); }
  .tagdot.risk{ background:var(--red); }
  .tagdot.up{ background:var(--green); }
  .tagdot.neutral{ background:var(--border-strong); }
  /* tag legend row */
  .tag-legend{ display:flex; gap:14px; flex-wrap:wrap; font-size:11.5px; margin-top:8px; padding:8px 0 2px; border-top:1px solid var(--border); }
  .tag-legend-item{ display:flex; align-items:center; gap:5px; color:var(--text3); }

  /* ── accounts layout (sidebar lists + search/filter) ─────────── */
  .accts-layout{ display:flex; gap:18px; align-items:flex-start; }
  .accts-sidebar{ width:230px; flex:none; background:var(--layer1); border:1px solid var(--border); }
  .accts-sidebar h4{ font-size:11.5px; font-weight:600; color:var(--text3); padding:12px 14px 6px; }
  .slist{ display:block; width:100%; text-align:left; font:inherit; font-size:13px; color:#ffffff; background:none;
          border:none; border-left:3px solid transparent; padding:9px 14px; cursor:pointer; }
  .slist:hover{ background:var(--layer2); color:#ffffff; }
  .slist.active{ background:var(--layer2); color:#ffffff; border-left-color:var(--blue); font-weight:600; }
  .slist .n{ float:right; font-family:var(--mono); font-size:11.5px; color:#ffffff; }
  .accts-main{ flex:1; min-width:0; }
  .accts-tools{ display:flex; flex-direction:column; gap:10px; margin-bottom:14px; }
  .accts-tools input{ width:320px; max-width:100%; }
  .tag-filters{ display:flex; gap:6px; flex-wrap:wrap; }

  /* ── dashboard panels ───────────────────────────────────────── */
  .dash-grid{ display:flex; gap:14px; align-items:stretch; }
  .dash-grid > .dash-panel{ flex:1.4; min-width:0; }
  .dash-side{ flex:1; display:flex; flex-direction:column; gap:14px; }
  .dash-panel{ background:var(--layer1); border:1px solid var(--border); padding:18px 20px; }
  .dash-panel h3{ font-size:13.5px; margin-bottom:14px; }
  .dash-nums{ display:flex; gap:26px; margin-bottom:12px; flex-wrap:wrap; }
  .dnum .v{ display:block; font-family:var(--mono); font-size:26px; font-weight:600; }
  .dnum .l{ font-size:11.5px; color:var(--text3); }
  .news-item{ display:flex; gap:12px; padding:10px 0; border-top:1px solid var(--border); font-size:12.5px; }
  .news-item:first-child{ border-top:none; }
  .news-item .nd{ width:80px; flex:none; font-family:var(--mono); font-size:11px; color:var(--text3); }
  .news-item .nb{ flex:1; min-width:0; }
  .news-item .na{ font-weight:600; }
  @media(max-width:900px){ .dash-grid{ flex-direction:column; } }

  /* ── dashboard activity visualization ───────────────────────── */
  .viz-panel{ position:relative; overflow:hidden; margin-bottom:14px;
              background:var(--grad-surface); }
  /* Brand-gradient hairline along the top edge + a soft glow behind the chart. */
  .viz-panel::before{ content:''; position:absolute; inset:0 0 auto 0; height:2px;
                      background:var(--grad-brand); }
  .viz-panel::after{ content:''; position:absolute; inset:0; background:var(--grad-glow);
                     pointer-events:none; }
  .viz-panel > *{ position:relative; z-index:1; }
  .viz-head{ display:flex; align-items:flex-start; justify-content:space-between; gap:16px;
             flex-wrap:wrap; margin-bottom:18px; }
  .viz-label{ font-size:12.5px; color:var(--text3); margin:3px 0 0; }
  .seg{ display:flex; border:1px solid var(--border); flex:none; }
  .seg-btn{ font:inherit; font-size:12.5px; font-weight:500; color:var(--text3); background:none;
            border:none; border-right:1px solid var(--border); padding:7px 14px; cursor:pointer;
            transition:background .13s,color .13s; }
  .seg-btn:last-child{ border-right:none; }
  .seg-btn:hover{ color:#fff; background:var(--layer2); }
  .seg-btn.active{ color:#fff; background:var(--grad-brand-soft); box-shadow:inset 0 -2px 0 var(--blue); }
  .viz-body{ display:flex; flex-direction:column; gap:16px; }
  .viz-stats{ display:flex; align-items:center; gap:34px; flex-wrap:wrap; }
  .vstat .v{ display:block; font-family:var(--mono); font-size:30px; font-weight:600;
             color:var(--text1); }
  .vstat .l{ font-size:11.5px; color:var(--text3); }
  .viz-ring-wrap{ position:relative; width:78px; height:78px; margin-left:auto; flex:none; }
  .viz-ring{ width:78px; height:78px; transform:rotate(-90deg); }
  .ring-track{ fill:none; stroke:var(--layer2); stroke-width:10; }
  .ring-fill{ fill:none; stroke:url(#ringGrad); stroke-width:10; stroke-linecap:butt;
              transition:stroke-dashoffset .55s cubic-bezier(.4,.14,.3,1); }
  .viz-ring-txt{ position:absolute; inset:0; display:flex; flex-direction:column;
                 align-items:center; justify-content:center; gap:1px; }
  .viz-ring-txt span{ font-family:var(--mono); font-size:15px; font-weight:600; color:#fff; }
  .viz-ring-txt small{ font-size:9px; color:var(--text3); }
  /* carbon-charts layout: a labelled y-axis on the left, horizontal gridlines
     behind the plot, and a zero-rule the bars sit on. */
  .viz-plot{ display:flex; gap:12px; }
  .viz-yaxis{ display:flex; flex-direction:column; justify-content:space-between;
              align-items:flex-end; height:140px; flex:none; padding-bottom:22px; }
  .viz-ytick{ font-family:var(--mono); font-size:10px; color:var(--text3); line-height:1; }
  .viz-grid{ position:relative; flex:1; min-width:0; }
  .viz-gridline{ position:absolute; left:0; right:0; height:1px; background:var(--border); opacity:.55; }
  .viz-gridline.zero{ opacity:1; background:var(--border-strong); }
  /* Bars are grid columns so labels stay aligned no matter the bucket count. */
  .viz-chart{ position:relative; display:grid; grid-auto-flow:column; grid-auto-columns:1fr;
              gap:10px; align-items:end; min-height:150px; padding-top:6px; }
  .vbar{ display:flex; flex-direction:column; align-items:center; gap:7px; min-width:0; }
  .vbar-stack{ display:flex; flex-direction:column; justify-content:flex-end; gap:2px;
               width:100%; max-width:46px; height:120px; }
  .vbar-seg{ width:100%; transition:height .5s cubic-bezier(.4,.14,.3,1); }
  /* Carbon's dark-theme data-viz gradients: Blue 30→50 and Purple 30→50. (The
     60-level stops are the *light*-theme pairing and go muddy on #161616.) */
  .vbar-seg.email{ background:linear-gradient(180deg,#a6c8ff 0%,#4589ff 100%); }
  .vbar-seg.call{ background:linear-gradient(180deg,#d4bbff 0%,#a56eff 100%); }
  .vbar-seg.zero{ background:var(--layer2); height:2px; }
  /* "Today" marker goes under the label, not around .vbar-stack — the stack is
     always full height, so outlining it drew an empty box above short bars. */
  .vbar.now .vbar-lbl{ color:#fff; font-weight:600; position:relative; }
  .vbar.now .vbar-lbl::after{ content:''; position:absolute; left:0; right:0; bottom:-4px;
                              height:2px; background:var(--grad-brand); }
  .vbar-lbl{ font-size:10.5px; color:var(--text3); text-align:center; white-space:nowrap;
             overflow:hidden; text-overflow:ellipsis; max-width:100%; }
  .vbar-val{ font-family:var(--mono); font-size:11px; color:var(--text2); }
  .viz-legend{ display:flex; gap:18px; font-size:11.5px; color:var(--text3); }
  .viz-legend i{ display:inline-block; width:10px; height:10px; margin-right:6px; }
  .sw-email{ background:linear-gradient(180deg,#a6c8ff,#4589ff); }
  .sw-call{ background:linear-gradient(180deg,#d4bbff,#a56eff); }
  .viz-empty{ color:var(--text3); font-size:13px; padding:34px 0; text-align:center; }
  /* Period stepping on the Activity / Meetings panels. */
  .viz-nav{ display:flex; align-items:center; gap:8px; margin-top:3px; }
  .viz-nav .viz-label{ margin:0; min-width:150px; }
  .step-btn{ font:inherit; font-size:14px; line-height:1; color:var(--text3); background:none;
             border:1px solid var(--border); cursor:pointer; padding:4px 9px;
             transition:color .12s,border-color .12s; }
  .step-btn:hover{ color:#fff; border-color:var(--border-strong); }
  .step-now{ font:inherit; font-size:12px; color:var(--blue-text); background:none;
             border:none; cursor:pointer; padding:2px 4px; }
  .step-now:hover{ text-decoration:underline; }
  /* Arrow on a navigation action — the button leaves this page. */
  .go-arrow{ margin-left:2px; }
  .cal-month-link{ cursor:pointer; }
  .cal-month-link:hover{ color:var(--blue-text); text-decoration:underline; }

  .list-loading{ display:flex; align-items:center; justify-content:center; gap:10px;
                 color:var(--text3); font-size:13px; padding:44px 0; }
  .list-loading .spin{ width:14px; height:14px; border:2px solid var(--border-strong);
                       border-top-color:var(--blue-text); border-radius:50%;
                       animation:spin .7s linear infinite; display:inline-block; }

  /* ── book-of-business snapshot ──────────────────────────────── */
  .bob-grid{ display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:26px; }
  .bob-title{ font-size:11px; font-weight:600; letter-spacing:.16px;
              color:var(--text2); margin-bottom:14px; }
  .bar-list{ display:flex; flex-direction:column; gap:11px; }
  .bar-item{ display:grid; grid-template-columns:1fr auto; gap:4px 10px; font-size:12.5px; }
  .bar-item .bl{ color:var(--text2); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
  .bar-item .bv{ font-family:var(--mono); font-size:11.5px; color:var(--text3); }
  .bar-track{ grid-column:1/-1; height:7px; background:var(--layer2); }
  .bar-fill{ height:100%; background:var(--grad-brand); transition:width .5s cubic-bezier(.4,.14,.3,1); }
  /* Coverage meter: filled portion = accounts already in a cadence. */
  .bar-meter{ display:flex; flex-direction:column; gap:9px; }
  .meter-track{ height:26px; background:var(--layer2); position:relative; overflow:hidden; }
  .meter-fill{ height:100%; background:var(--grad-brand); transition:width .55s cubic-bezier(.4,.14,.3,1); }
  .meter-legend{ display:flex; justify-content:space-between; font-size:12px; color:var(--text3); }
  .meter-legend b{ color:var(--text1); font-family:var(--mono); font-weight:600; }

  /* ── territory choropleth (per-territory outlines) ──────────── */
  .usmap{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px; flex:1; }
  .usmap.single{ grid-template-columns:1fr; }
  .terr{ font:inherit; text-align:center; background:var(--layer1); border:1px solid var(--border);
         cursor:pointer; padding:14px 12px 12px; display:flex; flex-direction:column;
         align-items:center; gap:2px; transition:border-color .13s,background .13s; }
  .terr:hover{ border-color:var(--border-strong); background:var(--layer2); }
  .terr.empty{ opacity:.45; }
  /* Isometric presentation: tilt the plate the shape sits on, so the maps read
     as objects in space rather than flat clip-art. */
  .terr-iso{ width:100%; perspective:640px; margin-bottom:10px; }
  .usmap.single .terr-iso{ max-width:420px; margin-inline:auto; }
  /* Enough tilt to read as isometric, not so much that the outline stops being
     recognisable — the shape has to stay identifiable as the territory. */
  .terr-svg{ width:100%; height:110px; display:block;
             transform:rotateX(26deg) rotateZ(-15deg) scale(1.04);
             transform-style:preserve-3d;
             filter:drop-shadow(4px 9px 8px rgba(0,0,0,.6)); }
  .usmap.single .terr-svg{ height:230px; }
  /* Dark plate so the heat blobs carry the colour rather than fighting a grey. */
  .terr-base{ fill:#2a2130; }
  .terr-edge{ fill:none; stroke:rgba(255,255,255,.34); stroke-width:1.4;
              vector-effect:non-scaling-stroke; }
  .terr-code{ font-family:var(--mono); font-size:12px; font-weight:600; color:var(--text1); }
  .terr-name{ font-size:11px; color:var(--text3); line-height:1.35; }
  .terr-val{ font-family:var(--mono); font-size:15px; font-weight:600; color:var(--text1); margin-top:4px; }
  .terr-cities{ width:100%; margin-top:12px; border-top:1px solid var(--border); padding-top:10px; }
  .terr-city{ display:flex; justify-content:space-between; font-size:12px; color:var(--text3);
              padding:4px 2px; }
  .terr-city b{ font-family:var(--mono); color:var(--text1); font-weight:600; }
  /* Map card fills the aside so both profile columns end level. */
  .map-card{ display:flex; flex-direction:column; height:100%; }
  .prof-split{ align-items:stretch; }
  @media(max-width:520px){ .usmap{ grid-template-columns:1fr; } }
  .map-foot{ display:flex; align-items:center; justify-content:space-between; gap:16px;
             flex-wrap:wrap; margin-top:16px; }
  .map-scale{ display:flex; align-items:center; gap:9px; font-family:var(--mono);
              font-size:11px; color:var(--text3); }
  /* Low→high runs Purple 70 up to Purple 10, matching the reference legend. */
  .scale-bar{ display:block; width:180px; height:10px;
              background:linear-gradient(90deg,#6929c4 0%,#8a3ffc 28%,#a56eff 50%,#be95ff 68%,#d4bbff 82%,#f6f2ff 100%); }
  .map-note{ font-size:11.5px; color:var(--text3); }
  .map-tip{ margin-top:14px; padding:12px 14px; background:var(--layer2);
            border-left:2px solid transparent; border-image:var(--grad-brand) 1;
            font-size:12.5px; }
  .map-tip b{ font-weight:600; }
  .map-tip .mt-row{ color:var(--text3); margin-top:3px; }

  /* ── plan calendar ──────────────────────────────────────────── */
  .cal-toolbar{ display:flex; align-items:center; justify-content:space-between; gap:14px; margin-bottom:16px; flex-wrap:wrap; }
  .cal-nav{ display:flex; align-items:center; gap:10px; }
  .cal-nav .btn{ padding:6px 12px; }
  .cal-label{ font-weight:600; font-size:14px; min-width:150px; text-align:center; }
  .cal-month{ background:var(--layer1); border:1px solid var(--border); padding:14px; }
  .cal-month h4{ font-size:13px; margin-bottom:10px; }
  .cal-grid{ display:grid; grid-template-columns:repeat(5,1fr); gap:2px; }
  .cal-grid .dow{ font-size:10.5px; color:var(--text3); text-align:center; padding:4px 0; }
  /* Empty days recede into the card; only days with work take the lighter
     layer2 fill, so the month reads as activity rather than a slab of gray. */
  .cal-cell{ min-height:56px; background:transparent; padding:5px 7px; cursor:default;
             border:1px solid var(--border); }
  .cal-cell.out{ opacity:.3; }
  .cal-cell.today{ border-color:#fff; }
  .cal-cell.has{ cursor:pointer; background:var(--layer2); border-color:var(--blue-border); }
  .cal-cell.has:hover{ background:var(--layer3); }
  .cal-cell.sel{ background:var(--blue-soft); border-color:var(--blue); }
  .cal-cell .d{ font-family:var(--mono); font-size:11px; color:#ffffff; }
  .cal-cell .acts{ font-size:10.5px; margin-top:4px; color:#ffffff; }
  .cal-cell.compact{ min-height:34px; }
  .cal-quarter{ display:grid; grid-template-columns:repeat(3,1fr); gap:14px; }
  /* Year view: four quarter blocks, each a labelled row of three months. */
  .cal-year{ display:flex; flex-direction:column; gap:22px; }
  .cal-qhead{ display:flex; align-items:baseline; gap:12px; margin-bottom:9px;
              padding-bottom:7px; border-bottom:1px solid var(--border); }
  .cal-qhead h4{ font-size:13px; font-weight:600; letter-spacing:.16px;
                 color:var(--text2); margin:0; }
  .cal-qsum{ font-size:11.5px; color:var(--text3); font-family:var(--mono); }
  @media(max-width:1100px){ .cal-quarter{ grid-template-columns:1fr; } }
  .cal-week{ display:grid; grid-template-columns:repeat(5,1fr); gap:8px; }
  .cal-weekday{ background:var(--layer1); border:1px solid var(--border); padding:12px; min-height:150px; cursor:pointer; }
  .cal-weekday:hover{ background:var(--layer2); }
  .cal-weekday.sel{ border-color:var(--blue); }
  .cal-weekday h5{ font-size:12px; margin-bottom:8px; }
  .cal-weekday .cnt{ font-size:11.5px; color:#ffffff; margin-bottom:8px; }
  /* ── day-detail side panel (Plan tab) ──────────────────────── */
  .day-panel{ position:fixed; top:0; right:0; width:360px; max-width:100vw; height:100vh; background:var(--layer1);
              border-left:1px solid var(--border); z-index:120; transform:translateX(100%);
              transition:transform .22s ease; display:flex; flex-direction:column; overflow:hidden; }
  .day-panel.open{ transform:translateX(0); }
  /* Make room for the panel rather than letting it cover the content. */
  main{ transition:padding-right .22s ease; }
  body.day-panel-open main,
  body.side-panel-open main{ padding-right:396px; }
  @media(max-width:900px){ body.day-panel-open main,
                           body.side-panel-open main{ padding-right:0; } }

  /* Contextual panel on the Email/Call tabs — same mechanics as the day panel. */
  .side-panel{ position:fixed; top:0; right:0; width:380px; max-width:100vw; height:100vh;
               background:var(--layer1); border-left:1px solid var(--border); z-index:120;
               transform:translateX(100%); transition:transform .22s ease; display:flex;
               flex-direction:column; overflow:hidden; }
  .side-panel.open{ transform:translateX(0); }
  .side-panel-body{ flex:1; overflow-y:auto; padding:18px 20px 28px; }
  .sp-title{ font-size:17px; font-weight:600; }
  .sp-sub{ font-size:13px; color:var(--text3); margin-top:3px; }
  .sp-block{ margin-top:16px; }
  .sp-row{ display:grid; grid-template-columns:44% 1fr; gap:10px; padding:9px 0;
           border-bottom:1px solid var(--border); font-size:13.5px; }
  .sp-row:last-child{ border-bottom:none; }
  .sp-row .k{ color:var(--text3); }
  .sp-row .v{ color:var(--text2); word-break:break-word; }
  .sp-ai{ margin-top:18px; padding:14px 15px; background:var(--grad-brand-soft);
          border-left:2px solid var(--purple); }
  .sp-ai-head{ display:flex; align-items:center; gap:7px; font-size:12.5px; font-weight:600;
               color:var(--purple-text); margin-bottom:6px; }
  /* The card the panel is about. */
  .email-card.focused, .call-card.focused{ border-color:var(--blue); box-shadow:0 0 0 1px var(--blue); }

  /* Kebab menu on cards. */
  .kebab-wrap{ position:relative; }
  .kebab{ font:inherit; font-size:17px; line-height:1; background:none; border:none;
          color:var(--text3); cursor:pointer; padding:2px 6px; }
  .kebab:hover{ color:#fff; }
  .kebab-menu{ display:none; position:absolute; top:calc(100% + 4px); right:0; z-index:60;
               min-width:206px; background:var(--layer2); border:1px solid var(--border-strong);
               box-shadow:0 14px 30px rgba(0,0,0,.5); }
  .kebab-menu.show{ display:block; }
  .kebab-menu button{ display:block; width:100%; text-align:left; font:inherit; font-size:13.5px;
                      background:none; border:none; color:var(--text2); cursor:pointer;
                      padding:10px 14px; }
  .kebab-menu button:hover{ background:var(--layer3); color:#fff; }
  .kebab-menu button.danger{ color:var(--red); border-top:1px solid var(--border); }
  .link{ cursor:pointer; }
  .email-card-to.link:hover, .call-card-name:hover{ color:var(--blue-text); text-decoration:underline; }
  .day-panel-head{ display:flex; align-items:center; justify-content:space-between; padding:18px 20px 14px;
                   border-bottom:1px solid var(--border); flex:none; }
  .day-panel-head h3{ font-size:14px; margin:0; }
  .day-panel-close{ font:inherit; font-size:18px; background:none; border:none; color:var(--text3); cursor:pointer; padding:0 4px; line-height:1; }
  .day-panel-close:hover{ color:#fff; }
  .day-panel-sums{ padding:14px 20px 10px; flex:none; border-bottom:1px solid var(--border); font-size:13px; color:#ffffff; }
  .day-panel-items{ flex:1; overflow-y:auto; padding:10px 20px 20px; }
  .day-panel-section{ font-size:11px; font-weight:600; color:var(--text2); text-transform:none;
                      padding:14px 0 6px; border-bottom:1px solid var(--border-strong); margin-bottom:2px; }
  .panel-act{ display:flex; gap:10px; align-items:flex-start; padding:10px 0; border-top:1px solid var(--border); }
  .panel-act:first-child{ border-top:none; }
  .day-panel-section + .panel-act{ border-top:none; }
  .panel-act .act-type{ margin-top:1px; }
  .panel-act-body{ flex:1; min-width:0; }
  .panel-act-body .pa-acct{ font-weight:500; font-size:12.5px; color:#fff; word-break:break-word; }
  .panel-act-body .pa-step{ font-size:11px; color:var(--text3); margin-top:2px; }
  /* legacy inline detail (kept for day-view fallback, hidden by default) */
  .day-detail{ margin-top:16px; background:var(--layer1); border:1px solid var(--border); padding:18px 20px; display:none; }
  .day-detail h3{ font-size:14px; margin-bottom:6px; }
  .day-detail .sums{ color:#ffffff; font-size:13px; margin-bottom:12px; }
  .act-row{ display:flex; gap:12px; align-items:center; padding:8px 0; border-top:1px solid var(--border); font-size:12.5px; }
  .act-row:first-of-type{ border-top:none; }
  .act-type{ width:52px; flex:none; font-size:10.5px; font-weight:600; text-align:center; border:1px solid var(--border-strong); padding:2px 0; }
  .act-type.email{ border-color:var(--purple-border); }
  .act-type.call{ border-color:var(--blue-border); }

  /* ── today's tasks (top of the dashboard) ───────────────────── */
  .today-head{ display:flex; align-items:baseline; gap:14px; margin-bottom:12px; }
  .today-head h3{ font-size:17px; }
  .today-sub{ font-size:13px; color:var(--text3); }
  /* Two equal columns that stay equal — 1fr each, and the cards stretch so the
     Emails and Calls rectangles match height whatever their list length. */
  .today-grid{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:14px;
               align-items:stretch; }
  .task-card{ display:flex; flex-direction:column; background:var(--layer1);
              border:1px solid var(--border); padding:18px 20px 18px; min-height:560px; }
  .task-top{ display:flex; align-items:center; gap:9px; margin-bottom:12px; }
  .task-top h4{ font-size:14px; font-weight:600; margin:0; flex:1; }
  .task-dot{ width:10px; height:10px; flex:none; }
  .task-dot.email{ background:linear-gradient(180deg,#a6c8ff,#4589ff); }
  .task-dot.call{ background:linear-gradient(180deg,#d4bbff,#a56eff); }
  .task-count{ font-size:12px; color:var(--text3); }
  .task-count b{ font-family:var(--mono); color:var(--text1); font-weight:600; }
  .task-meter{ height:6px; background:var(--layer2); margin-bottom:12px; }
  .task-fill{ height:100%; width:0; transition:width .5s cubic-bezier(.4,.14,.3,1); }
  .task-fill.email{ background:linear-gradient(90deg,#4589ff,#a6c8ff); }
  .task-fill.call{ background:linear-gradient(90deg,#a56eff,#d4bbff); }
  .task-list{ flex:1; overflow-y:auto; max-height:470px; margin-bottom:14px; }
  .task-row{ display:flex; align-items:baseline; gap:10px; padding:8px 0;
             border-bottom:1px solid var(--border); font-size:13px; }
  .task-row:last-child{ border-bottom:none; }
  .task-tick{ width:14px; flex:none; color:var(--green); font-size:12px; }
  .task-acct{ font-weight:500; color:var(--text1); }
  .task-step{ color:var(--text3); font-size:12.5px; margin-left:auto; }
  .task-row.done .task-acct,
  .task-row.done .task-step{ color:var(--text3); text-decoration:line-through; }
  .task-action{ width:100%; justify-content:center; display:flex; align-items:center; gap:7px; }
  @media(max-width:900px){ .today-grid{ grid-template-columns:1fr; } }

  /* Today's to-do, grouped by activity type instead of per-row tags. */
  .todo-sec{ margin-top:18px; }
  .todo-sec:first-child{ margin-top:6px; }
  .todo-head{ display:flex; align-items:center; gap:8px; font-size:11.5px; font-weight:600;
              letter-spacing:.16px; color:var(--text2);
              padding-bottom:8px; border-bottom:1px solid var(--border); }
  .todo-dot{ width:9px; height:9px; flex:none; }
  .todo-dot.email{ background:linear-gradient(180deg,#a6c8ff,#4589ff); }
  .todo-dot.call{ background:linear-gradient(180deg,#d4bbff,#a56eff); }
  .todo-count{ margin-left:auto; font-family:var(--mono); font-size:11px; color:var(--text3); }
  .todo-row{ display:flex; align-items:baseline; gap:12px; padding:9px 0;
             border-bottom:1px solid var(--border); font-size:13px; }
  .todo-row:last-child{ border-bottom:none; }
  .todo-acct{ font-weight:500; color:var(--text1); }
  .todo-step{ color:var(--text3); font-size:12.5px; margin-left:auto; }
  @media(max-width:980px){ .cal-quarter{ grid-template-columns:1fr; } .cal-week{ grid-template-columns:1fr; } .accts-layout{ flex-direction:column; } .accts-sidebar{ width:100%; } }

  /* ── cadences tab ───────────────────────────────────────────── */
  .cad-card{ background:var(--layer1); border:1px solid var(--border); margin-bottom:12px; }
  .cad-header{ display:flex; align-items:center; gap:14px; padding:18px 20px; cursor:pointer; }
  .cad-header:hover{ background:var(--layer2); }
  .cad-chevron{ font-size:11px; flex:none; transition:transform .2s; color:var(--text3); }
  .cad-card.open .cad-chevron{ transform:rotate(90deg); }
  .cad-meta{ flex:1; min-width:0; }
  .cad-name{ font-weight:600; font-size:14.5px; }
  .cad-desc{ font-size:12.5px; color:var(--text3); margin-top:3px; line-height:1.5; }
  .cad-count{ font-family:var(--mono); font-size:12px; flex:none; }
  .cad-status{ display:flex; gap:10px; flex:none; }
  .cad-body{ display:none; border-top:1px solid var(--border); }
  .cad-card.open .cad-body{ display:block; }
  .cad-steps{ padding:16px 20px 10px; border-bottom:1px solid var(--border); }
  .cad-steps h4{ font-size:11.5px; font-weight:600; color:var(--text3); margin-bottom:12px; }
  .step-timeline{ display:flex; gap:0; align-items:flex-start; overflow-x:auto; padding-bottom:4px; }
  .step-node{ display:flex; flex-direction:column; align-items:center; min-width:90px; position:relative; }
  .step-node:not(:last-child)::after{ content:''; position:absolute; top:12px; left:calc(50% + 12px);
    right:calc(-50% + 12px); height:1px; background:var(--border); }
  .step-dot{ width:24px; height:24px; border:1px solid var(--border-strong); background:var(--layer2);
             display:flex; align-items:center; justify-content:center; font-size:9.5px; font-weight:600; z-index:1; }
  .step-dot.email{ border-color:var(--purple-border); background:var(--purple-soft); }
  .step-dot.call{ border-color:var(--blue-border); background:var(--blue-soft); }
  .step-label{ font-size:10px; margin-top:5px; text-align:center; color:var(--text3); max-width:80px; line-height:1.35; }
  .step-day{ font-family:var(--mono); font-size:9.5px; color:var(--text3); margin-top:2px; }
  .cad-accounts{ padding:0; }
  .cad-acct-row{ display:flex; align-items:center; gap:0; padding:10px 20px; border-bottom:1px solid var(--border);
                 font-size:12.5px; }
  .cad-acct-row:last-child{ border-bottom:none; }
  .cad-acct-row:hover{ background:var(--layer2); }
  .cad-acct-rank{ width:28px; flex:none; font-family:var(--mono); font-size:11.5px; color:var(--text3); }
  .cad-acct-name{ flex:1; font-weight:500; cursor:pointer; padding-right:12px; }
  .cad-acct-name:hover{ color:var(--blue-text); text-decoration:underline; }
  .cad-acct-ind{ width:150px; flex:none; color:var(--text3); font-size:11.5px; padding-right:12px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
  .cad-acct-next{ flex:1; font-size:11.5px; color:var(--text3); }
  .cad-acct-status{ width:90px; flex:none; }
  .status-pill{ font-size:10.5px; font-weight:600; padding:2px 9px; border:1px solid transparent; }
  .status-pill.not_started{ border-color:var(--border-strong); color:var(--text3); }
  .status-pill.in_progress{ border-color:var(--blue-border); color:var(--blue-text); }
  .status-pill.completed{ border-color:rgba(66,190,101,.4); color:var(--green); }

  /* ── email tab ──────────────────────────────────────────────── */
  .email-toolbar{ display:flex; align-items:center; justify-content:space-between; margin-bottom:18px; flex-wrap:wrap; gap:12px; }
  .email-grid{ display:grid; grid-template-columns:repeat(auto-fill, minmax(380px, 1fr)); gap:14px; }
  .email-card{ background:var(--layer1); border:1px solid var(--border); padding:18px 20px; display:flex; flex-direction:column; gap:10px; }
  .email-card-head{ display:flex; align-items:flex-start; justify-content:space-between; gap:10px; }
  .email-card-head-actions{ display:flex; align-items:center; gap:6px; flex:none; }
  .email-card-to{ font-weight:600; font-size:13.5px; }
  .email-card-addr{ font-size:11.5px; color:var(--blue-text); font-family:var(--mono); margin-top:1px; }
  .email-card-sub{ font-size:12px; color:var(--text3); margin-top:3px; }
  .email-card-cadence{ font-size:11px; color:var(--purple-text); margin-top:2px; }
  .email-card-subject{ font-size:12.5px; font-weight:600; color:#fff; margin:8px 0 2px; }
  .email-card-subject span{ font-weight:400; color:var(--text3); }
  .email-body-wrap{ border-top:1px solid var(--border); padding-top:10px; flex:1; }
  .email-body-text{ font:12.5px/1.6 var(--mono); white-space:pre-wrap; color:var(--text2); min-height:100px; }
  .email-body-text.empty{ color:var(--text3); font-style:italic; font-family:var(--font); font-size:12.5px; }
  .email-body-edit{ font:12.5px/1.6 var(--mono); white-space:pre-wrap; color:var(--text2);
                    background:var(--layer2); border:1px solid var(--border); padding:10px 12px;
                    min-height:130px; width:100%; resize:vertical; outline:none; display:none; }
  .email-body-edit.active{ display:block; }
  .email-body-edit:focus{ border-color:var(--blue-text); box-shadow:0 0 0 2px var(--blue-soft); }
  .email-foot{ display:flex; gap:8px; border-top:1px solid var(--border); padding-top:10px; align-items:center; }
  .email-sent{ font-size:12px; color:var(--green); display:none; }
  .email-sent.show{ display:inline; }
  .icon-btn{ font:inherit; font-size:14px; background:none; border:none; cursor:pointer; color:var(--text3); padding:4px 6px; line-height:1; }
  .icon-btn:hover{ color:#fff; }

  /* ── call tab ───────────────────────────────────────────────── */
  .call-toolbar{ display:flex; align-items:center; justify-content:space-between; margin-bottom:18px; flex-wrap:wrap; gap:12px; }
  .call-list{ display:flex; flex-direction:column; gap:10px; }
  .call-card{ background:var(--layer1); border:1px solid var(--border); padding:18px 20px; }
  .call-card-head{ display:flex; align-items:center; gap:14px; margin-bottom:14px; }
  .call-card-rank{ font-family:var(--mono); font-size:12px; color:var(--text3); width:24px; flex:none; }
  .call-card-acct{ font-size:12px; color:var(--text3); }
  .call-card-name{ font-weight:600; font-size:14px; flex:1; cursor:pointer; }
  .call-card-name:hover{ color:var(--blue-text); text-decoration:underline; }
  .call-card-step{ font-size:11.5px; color:var(--blue-text); }
  .call-card.done{ opacity:.62; }
  .call-done-btn{ font:inherit; font-size:11.5px; margin-left:auto; background:none;
                  border:1px solid var(--border-strong); color:var(--text3); cursor:pointer;
                  padding:4px 11px; white-space:nowrap; transition:color .12s,border-color .12s; }
  .call-done-btn:hover{ color:#fff; border-color:#fff; }
  .call-done-btn.on{ color:var(--green); border-color:rgba(66,190,101,.5); }
  .call-card-body{ display:grid; grid-template-columns:1fr 1fr; gap:12px; }
  .call-contacts{ background:var(--layer2); border:1px solid var(--border); padding:12px 14px; }
  .call-contacts h4{ font-size:11.5px; font-weight:600; color:var(--text3); margin-bottom:10px; }
  .call-person{ padding:8px 0; border-top:1px solid var(--border); }
  .call-person:first-of-type{ border-top:none; }
  .call-person-name{ font-weight:600; font-size:13px; display:flex; align-items:center; gap:8px; }
  .call-person-title{ font-size:11.5px; color:var(--text3); margin-top:2px; }
  .call-person-info{ display:flex; gap:14px; margin-top:6px; flex-wrap:wrap; }
  .call-person-phone{ font-family:var(--mono); font-size:11.5px; color:var(--blue-text); }
  .call-person-email{ font-family:var(--mono); font-size:11px; color:var(--text3); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width:200px; }
  .btn.call{ background:var(--green); border-color:var(--green); color:#000; font-weight:600; padding:4px 12px; font-size:12px; }
  .btn.call:hover{ background:#37a659; }
  .call-brief{ background:var(--purple-soft); border:1px solid var(--purple-border); padding:12px 14px; }
  .call-brief h4{ font-size:11.5px; font-weight:600; color:var(--purple-text); margin-bottom:8px; display:flex; align-items:center; gap:5px; }
  .call-brief p{ font-size:12px; line-height:1.6; margin:0; }
  .call-brief.loading p{ color:var(--text3); font-style:italic; }
  .brief-bullets{ margin:0; padding-left:16px; list-style:disc; }
  .brief-bullets li{ font-size:12px; line-height:1.55; margin-bottom:5px; color:#fff; }
  .brief-bullets li:last-child{ margin-bottom:0; }
  @media(max-width:700px){ .call-card-body{ grid-template-columns:1fr; } .email-grid{ grid-template-columns:1fr; } }

  /* ── account detail modal ──────────────────────────────────── */
  .modal-card.wide{ width:820px; }
  .detail-grid{ display:grid; grid-template-columns:1fr 1fr; gap:12px; }
  .detail-grid .panel.full{ grid-column:1 / -1; }
  .kv{ display:flex; justify-content:space-between; gap:12px; padding:6px 0; border-top:1px solid var(--border); font-size:12.5px; }
  .kv:first-of-type{ border-top:none; }
  .kv .k{ color:var(--text3); }
  .kv .v{ font-family:var(--mono); text-align:right; }
  .contact-row{ display:flex; gap:10px; padding:7px 0; border-top:1px solid var(--border); font-size:12.5px; align-items:center; }
  .contact-row:first-of-type{ border-top:none; }
  .contact-row .cn{ flex:1; font-weight:500; }
  .contact-row .ct{ color:var(--text3); }
  .dm-badge{ font-size:10px; font-weight:600; border:1px solid rgba(66,190,101,.55); padding:1px 7px; color:#fff; }
  .ai-panel{ border-color:var(--purple-border) !important; }
  .ai-panel h3{ color:var(--purple-text) !important; display:flex; align-items:center; gap:6px; }

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
  .klabel{ color:#ffffff; font-size:12px; margin-top:9px; display:flex; align-items:center; gap:5px; }

  /* ── ROI ────────────────────────────────────────────────────── */
  .roi-head{ margin:8px 0 14px; }
  .roi-head h3{ font-size:16px; }
  .roi-head p{ color:var(--text3); font-size:13px; margin:4px 0 0; }
  .roi{ display:grid; grid-template-columns:repeat(4,1fr); gap:14px; }
  .roi-card{ background:var(--layer1); border:1px solid var(--border); border-radius:var(--r-lg); padding:18px 20px; }
  .roi-card.ai{ border-color:var(--purple-border); }
  .rlabel{ color:#ffffff; font-size:12px; }
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
  .note{ color:#ffffff; font-size:12.5px; line-height:1.55; margin-bottom:6px; }
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
    <button class="brand" onclick="showPage('dashboard')">
      <img class="brand-logo" src="/static/logo.png" alt="">
      <div class="brand-name">IBM <b>BobBee</b></div>
    </button>
    <nav class="topnav">
      <button class="navlink" data-page="plan" onclick="showPage('plan')">Schedule</button>
      <button class="navlink" data-page="accounts" onclick="showPage('accounts')">Accounts</button>
      <button class="navlink" data-page="cadences" onclick="showPage('cadences')">Cadences</button>
      <button class="navlink" data-page="email" onclick="showPage('email')">Email</button>
      <button class="navlink" data-page="call" onclick="showPage('call')">Call</button>
    </nav>
    <div class="topsearch">
      <svg viewBox="0 0 32 32" fill="currentColor" aria-hidden="true"><path d="M29 27.586l-7.552-7.552a11.018 11.018 0 10-1.414 1.414L27.586 29zM4 13a9 9 0 119 9 9.01 9.01 0 01-9-9z"/></svg>
      <input type="text" id="globalSearch" placeholder="Search accounts, cadences and more"
             autocomplete="off" oninput="globalSearch(this.value)"
             onkeydown="if(event.key==='Enter') globalSearchGo()">
    </div>
    <div class="topbar-actions">
      <div class="profile-wrap">
        <button class="profile-btn" id="profileBtn" onclick="showPage('profile')">?</button>
      </div>
    </div>
  </header>

  <main>
    <!-- Dashboard (home) -->
    <section id="page-dashboard" class="page active">
      <div class="page-head">
        <h2>Dashboard</h2>
        <p id="dashSub">Your day at a glance.</p>
      </div>

      <div id="dashboardEmpty" class="empty-state" style="display:none">
        <h3>Import accounts to get started</h3>
        <p>BobBee builds your day from your accounts. Import them first.</p>
        <button class="btn primary" onclick="showPage('accounts')">Go to Accounts</button>
      </div>
      <div id="dashboardStrat" class="empty-state" style="display:none">
        <h3>Strategize your accounts</h3>
        <p>Your accounts are in — run Strategize to build cadences and your daily plan.</p>
        <button class="btn primary" onclick="showPage('accounts')">Go to Accounts</button>
      </div>

      <div id="dashboardBody" style="display:none">
        <div class="today-head">
          <h3 id="dashTodayLabel">Today</h3>
          <span class="today-sub" id="dashTodaySub">—</span>
        </div>
        <div class="today-grid">
          <section class="task-card">
            <div class="task-top">
              <span class="task-dot email"></span>
              <h4>Emails</h4>
              <span class="task-count"><b id="taskEmailDone">0</b> of <b id="taskEmailTotal">0</b> sent</span>
            </div>
            <div class="task-meter"><div class="task-fill email" id="taskEmailFill"></div></div>
            <div class="task-list" id="taskEmailList"></div>
            <button class="btn task-action" onclick="showPage('email')">Draft and send emails <span class="go-arrow">&#8594;</span></button>
          </section>
          <section class="task-card">
            <div class="task-top">
              <span class="task-dot call"></span>
              <h4>Calls</h4>
              <span class="task-count"><b id="taskCallDone">0</b> of <b id="taskCallTotal">0</b> done</span>
            </div>
            <div class="task-meter"><div class="task-fill call" id="taskCallFill"></div></div>
            <div class="task-list" id="taskCallList"></div>
            <button class="btn task-action" onclick="showPage('call')">Start calling <span class="go-arrow">&#8594;</span></button>
          </section>
        </div>

        <div class="dash-panel viz-panel" style="margin-top:14px;">
          <div class="viz-head">
            <div>
              <h3>Activity</h3>
              <div class="viz-nav">
                <button class="step-btn" onclick="stepViz(-1)" title="Previous">&#8592;</button>
                <p class="viz-label" id="vizLabel">—</p>
                <button class="step-btn" onclick="stepViz(1)" title="Next">&#8594;</button>
                <button class="step-now" id="vizNowBtn" onclick="stepVizNow()" style="display:none">Today</button>
              </div>
            </div>
            <div class="seg" id="vizPeriods">
              <button class="seg-btn" data-period="day" onclick="setVizPeriod('day')">Daily</button>
              <button class="seg-btn active" data-period="week" onclick="setVizPeriod('week')">Weekly</button>
              <button class="seg-btn" data-period="month" onclick="setVizPeriod('month')">Monthly</button>
              <button class="seg-btn" data-period="quarter" onclick="setVizPeriod('quarter')">Quarterly</button>
            </div>
          </div>
          <div class="viz-body">
            <div class="viz-stats">
              <div class="vstat"><span class="v" id="vizEmails">0</span><span class="l">Emails</span></div>
              <div class="vstat"><span class="v" id="vizCalls">0</span><span class="l">Calls</span></div>
              <div class="vstat"><span class="v" id="vizAccounts">0</span><span class="l">Accounts</span></div>
              <div class="viz-ring-wrap">
                <svg class="viz-ring" viewBox="0 0 120 120" aria-hidden="true">
                  <defs>
                    <linearGradient id="ringGrad" x1="0" y1="0" x2="1" y2="1">
                      <stop offset="0%" stop-color="#0f62fe"/><stop offset="100%" stop-color="#8a3ffc"/>
                    </linearGradient>
                  </defs>
                  <circle cx="60" cy="60" r="52" class="ring-track"/>
                  <circle cx="60" cy="60" r="52" class="ring-fill" id="vizRing"/>
                </svg>
                <div class="viz-ring-txt"><span id="vizPct">0%</span><small>worked</small></div>
              </div>
            </div>
            <div class="viz-plot">
              <div class="viz-yaxis" id="vizYAxis"></div>
              <div class="viz-grid">
                <div id="vizGrid"></div>
                <div class="viz-chart" id="vizChart"></div>
              </div>
            </div>
            <div class="viz-legend">
              <span><i class="sw sw-email"></i>Emails</span>
              <span><i class="sw sw-call"></i>Calls</span>
            </div>
          </div>
        </div>

        <div class="dash-panel viz-panel" style="margin-top:14px;">
          <div class="viz-head">
            <div>
              <h3>Meetings &amp; opportunities</h3>
              <div class="viz-nav">
                <button class="step-btn" id="mtgPrev" onclick="stepMtg(-1)" title="Previous week">&#8592;</button>
                <p class="viz-label" id="mtgLabel">—</p>
                <button class="step-btn" id="mtgNext" onclick="stepMtg(1)" title="Next week">&#8594;</button>
              </div>
            </div>
            <div class="seg" id="mtgScope">
              <button class="seg-btn active" data-scope="quarter" onclick="setMtgScope('quarter')">Quarter</button>
              <button class="seg-btn" data-scope="week" onclick="setMtgScope('week')">Week</button>
            </div>
          </div>
          <div class="viz-stats">
            <div class="vstat"><span class="v" id="mtgTotal">0</span><span class="l">Total meetings</span></div>
            <div class="vstat"><span class="v" id="mtgBooked">0</span><span class="l">Booked meetings</span></div>
            <div class="vstat"><span class="v" id="mtgCompleted">0</span><span class="l">Completed meetings</span></div>
            <div class="vstat"><span class="v" id="mtgUpcoming">0</span><span class="l">Upcoming</span></div>
            <div class="vstat"><span class="v" id="mtgCancelled">0</span><span class="l">Cancelled</span></div>
            <div class="vstat"><span class="v" id="mtgOI">0</span><span class="l">OI (opportunities identified)</span></div>
            <div class="vstat"><span class="v" id="mtgOIValue">—</span><span class="l">OI value</span></div>
          </div>
        </div>

        <div class="dash-panel viz-panel" style="margin-top:14px;">
          <div class="viz-head">
            <div>
              <h3>Book of business</h3>
              <p class="viz-label" id="bobLabel">—</p>
            </div>
          </div>
          <div class="viz-stats" style="margin-bottom:20px;">
            <div class="vstat"><span class="v" id="bobTotal">0</span><span class="l">Accounts</span></div>
            <div class="vstat"><span class="v" id="bobCovered">0</span><span class="l">In a cadence</span></div>
            <div class="vstat"><span class="v" id="bobSpend">—</span><span class="l">IBM spend</span></div>
            <div class="vstat"><span class="v" id="bobIndustries">0</span><span class="l">Industries</span></div>
          </div>
          <div class="bob-grid">
            <div class="bob-block">
              <div class="bob-title">Coverage</div>
              <div class="bar-meter" id="bobCoverage"></div>
            </div>
            <div class="bob-block">
              <div class="bob-title">Top industries</div>
              <div class="bar-list" id="bobIndList"></div>
            </div>
            <div class="bob-block">
              <div class="bob-title">By territory</div>
              <div class="bar-list" id="bobTerrList"></div>
            </div>
          </div>
        </div>

      </div>
    </section>

    <!-- Plan -->
    <section id="page-plan" class="page">
      <div class="page-head">
        <h2>Schedule</h2>
        <p>Your quarter, distributed — who to email and call, every day.</p>
      </div>

      <div id="planEmpty" class="empty-state" style="display:none">
        <h3>Import accounts to get started</h3>
        <p>The schedule is built from your strategized accounts.</p>
        <button class="btn primary" onclick="showPage('accounts')">Go to Accounts</button>
      </div>
      <div id="planStrat" class="empty-state" style="display:none">
        <h3>Strategize your accounts</h3>
        <p>Run Strategize on the Accounts tab to distribute cadences across the quarter.</p>
        <button class="btn primary" onclick="showPage('accounts')">Go to Accounts</button>
      </div>

      <div id="planBody" style="display:none">
        <div class="cal-toolbar">
          <div class="range-toggle">
            <button class="range-btn" data-view="year" onclick="setCalView('year')">Year</button>
            <button class="range-btn" data-view="quarter" onclick="setCalView('quarter')">Quarter</button>
            <button class="range-btn active" data-view="month" onclick="setCalView('month')">Month</button>
            <button class="range-btn" data-view="week" onclick="setCalView('week')">Week</button>
            <button class="range-btn" data-view="day" onclick="setCalView('day')">Day</button>
          </div>
          <div class="cal-nav">
            <button class="btn" onclick="calStep(-1)">&larr;</button>
            <span class="cal-label" id="calLabel"></span>
            <button class="btn" onclick="calStep(1)">&rarr;</button>
          </div>
        </div>
        <div id="calGrid"></div>
      </div>
    </section>

    <!-- Accounts -->
    <section id="page-accounts" class="page">
      <div class="page-head">
        <h2>Accounts</h2>
        <p>Import, strategize, and work your book of business.</p>
      </div>

      <div id="acctsEmpty" style="display:none">
        <div class="pipe-step" id="card-gma" style="max-width:540px;">
          <div class="pipe-title">Import accounts</div>
          <div class="pipe-sub">IBM Sales Cloud + install base + segmentation</div>
          <div class="pipe-status" id="gmaStatus"><span class="dot pending"></span><span class="amsg">Not started</span></div>
          <div class="pipe-seller" id="gmaSeller"></div>
          <div class="pipe-foot">
            <span class="pipe-records" id="gmaResults"></span>
            <button class="btn primary" id="gmaBtn" onclick="runGetMyAccounts()">Import accounts</button>
          </div>
          <div class="pipe-chips" id="gmaChips"></div>
          <button class="link showlog" id="gmaLogToggle" onclick="toggleLog('gma')" style="display:none">Show details</button>
          <div class="alog" id="gmaLog"></div>
        </div>
      </div>

      <div id="acctsBody" style="display:none">
        <div class="accts-head">
          <span class="accts-count" id="acctsCount"></span>
          <button class="btn primary" id="strategizeBtn" onclick="runStrategize()">Sort accounts into cadences</button>
        </div>

        <!-- Refresh cadences confirmation modal -->
        <div class="modal" id="refreshModal" onclick="if(event.target===this) closeRefreshModal()">
          <div class="modal-card" style="max-width:520px;">
            <div class="modal-head">
              <h2>Refresh cadences?</h2>
              <button class="link" onclick="closeRefreshModal()">Cancel</button>
            </div>
            <p style="font-size:13.5px; line-height:1.6; margin:0 0 14px;">
              This will re-run account intelligence on all accounts that haven't been touched yet —
              pulling in the latest signals, news, and market data. Granite will re-evaluate urgency,
              re-rank accounts, and adjust cadence groupings based on what's changed since the last run.
            </p>
            <p style="font-size:13px; color:var(--blue-text); margin:0 0 22px; line-height:1.55;">
              Accounts already contacted this quarter will <strong>stay in their current cadence and plan</strong> —
              only untouched accounts are re-evaluated.
            </p>
            <div style="display:flex; gap:10px; justify-content:flex-end;">
              <button class="btn" onclick="closeRefreshModal()">Cancel</button>
              <button class="btn primary" onclick="confirmRefresh()">Yes, refresh cadences</button>
            </div>
          </div>
        </div>

        <div class="stages" id="stages" style="display:none">
          <div class="stage" id="stage-contacts">
            <span class="dot pending sicon"></span>
            <div><div class="stitle">Contacts check</div><div class="smsg">Checking each account's contacts in ZoomInfo for an IT decision-maker.</div></div>
          </div>
          <div class="stage" id="stage-scoring">
            <span class="dot pending sicon"></span>
            <div><div class="stitle">Signals &amp; quarter segmentation</div><div class="smsg">Waiting…</div></div>
          </div>
          <div class="stage" id="stage-cadences">
            <span class="dot pending sicon"></span>
            <div><div class="stitle">Cadences, ranking &amp; tags</div><div class="smsg">Waiting…</div></div>
          </div>
          <div class="stage" id="stage-schedule">
            <span class="dot pending sicon"></span>
            <div><div class="stitle">Quarter distribution</div><div class="smsg">Waiting…</div></div>
          </div>
        </div>

        <div class="accts-layout" id="acctsLayout">
          <aside class="accts-sidebar" id="acctsSidebar" style="display:none"></aside>
          <div class="accts-main">
            <div class="accts-tools" id="acctsTools" style="display:none">
              <input type="text" id="acctSearch" placeholder="Search accounts..." oninput="renderAccounts()">
              <div class="tag-legend" id="tagLegend" style="display:none">
                <span class="tag-legend-item"><span class="tagdot white"></span> Whitespace / Bluemix footprint</span>
                <span class="tag-legend-item"><span class="tagdot up"></span> Growing spend</span>
                <span class="tag-legend-item"><span class="tagdot risk"></span> At-risk / Competitive</span>
                <span class="tag-legend-item"><span class="tagdot neutral"></span> Other signal</span>
              </div>
            </div>
            <div id="acctList"></div>
          </div>
        </div>
      </div>
    </section>

    <!-- Cadences -->
    <section id="page-cadences" class="page">
      <div class="page-head">
        <h2>Cadences</h2>
        <p>Your active outreach sequences — steps, timeline, and account progress.</p>
      </div>
      <div id="cadencesEmpty" class="empty-state" style="display:none">
        <h3>Upload accounts to get started</h3>
        <p>Go to Accounts, import your accounts, and run Sort accounts into cadences. Your cadences will appear here once strategizing is complete.</p>
        <button class="btn primary" onclick="showPage('accounts')">Go to Accounts</button>
      </div>
      <div id="cadencesStratEmpty" class="empty-state" style="display:none">
        <h3>Sort accounts into cadences first</h3>
        <p>Your accounts are in — run "Sort accounts into cadences" on the Accounts tab to build your outreach sequences.</p>
        <button class="btn primary" onclick="showPage('accounts')">Go to Accounts</button>
      </div>
      <div id="cadencesBody" style="display:none">
        <div id="cadencesList"></div>
      </div>
    </section>

    <!-- Email -->
    <section id="page-email" class="page">
      <div class="page-head">
        <h2>Email</h2>
        <p id="emailDateLabel">Today's outbound emails across all cadences.</p>
      </div>
      <div id="emailEmpty" class="empty-state" style="display:none">
        <h3>Upload accounts to get started</h3>
        <p>Go to the Accounts tab, import your accounts, and run Sort accounts into cadences. Email drafts will appear here once your quarter is planned.</p>
        <button class="btn primary" onclick="showPage('accounts')">Go to Accounts</button>
      </div>
      <div id="emailStratEmpty" class="empty-state" style="display:none">
        <h3>Sort accounts into cadences first</h3>
        <p>Your accounts are in — run "Sort accounts into cadences" on the Accounts tab to build cadences and unlock email drafts.</p>
        <button class="btn primary" onclick="showPage('accounts')">Go to Accounts</button>
      </div>
      <div id="emailBody" style="display:none">
        <div class="email-toolbar">
          <span id="emailCountLabel" style="font-size:13px;"></span>
          <div style="display:flex;gap:8px;">
            <button class="btn ai" id="generateEmailsBtn" onclick="generateAllEmails()">""" + _SPARKLE + """ Draft all emails</button>
            <button class="btn primary" id="sendAllBtn" onclick="sendAllEmails()" disabled>Send all</button>
          </div>
        </div>
        <div class="email-grid" id="emailGrid"></div>
      </div>
    </section>

    <!-- Call -->
    <section id="page-call" class="page">
      <div class="page-head">
        <h2>Call</h2>
        <p id="callDateLabel">Today's call list across all cadences.</p>
      </div>
      <div id="callEmpty" class="empty-state" style="display:none">
        <h3>Upload accounts to get started</h3>
        <p>Go to the Accounts tab, import your accounts, and run Sort accounts into cadences. Call plans will appear here once your quarter is planned.</p>
        <button class="btn primary" onclick="showPage('accounts')">Go to Accounts</button>
      </div>
      <div id="callStratEmpty" class="empty-state" style="display:none">
        <h3>Sort accounts into cadences first</h3>
        <p>Your accounts are in — run "Sort accounts into cadences" on the Accounts tab to build cadences and unlock call plans.</p>
        <button class="btn primary" onclick="showPage('accounts')">Go to Accounts</button>
      </div>
      <div id="callBody" style="display:none">
        <div class="call-toolbar">
          <span id="callCountLabel" style="font-size:13px;"></span>
          <button class="btn ai" id="generateBriefsBtn" onclick="generateAllBriefs()">""" + _SPARKLE + """ Generate all briefings</button>
        </div>
        <div class="call-list" id="callList"></div>
      </div>
    </section>

    <!-- Profile -->
    <section id="page-profile" class="page">
      <div class="page-head" style="display:flex;align-items:center;justify-content:space-between;">
        <div>
          <h2 class="w3-name">Tim Zhou</h2>
        </div>
      </div>
      <div class="profile-page">
        <div class="profile-tabs">
          <button class="profile-tab active" data-ptab="profile" onclick="switchProfileTab('profile')">Profile</button>
          <button class="profile-tab" data-ptab="personalization" onclick="switchProfileTab('personalization')">Personalization</button>
          <button class="profile-tab" data-ptab="settings" onclick="switchProfileTab('settings')">Settings</button>
        </div>

        <!-- ── Profile tab ── -->
        <div class="profile-section active" id="ptab-profile">

          <!-- w3-style identity header -->
          <div class="w3-head">
            <div class="w3-avatar" id="w3Avatar">TZ</div>
            <div class="w3-ident">
              <div class="w3-role">TSS - Infrastructure - FSS/PUB - CA/HI/GU/MP</div>
              <div class="w3-fn">Sales</div>
              <div class="w3-loc">
                <a class="w3-link" href="#" onclick="return false">Brookhaven, GA, United States</a>
                <span class="w3-sep">|</span><span id="w3Clock">—</span>
              </div>
              <div class="w3-org">International Business Machines Corporation</div>
              <div class="w3-meta">IBM employee, Regular <span class="w3-sep">|</span> Talent ID: 0K3692897</div>
            </div>
          </div>

          <div class="w3-contact">
            <div class="w3-ctile">
              <div class="w3-cicon blue">✉</div>
              <div class="w3-clabel">Email (Preferred)</div>
              <a class="w3-link" href="mailto:tim.zhou@ibm.com">tim.zhou@ibm.com</a>
            </div>
            <div class="w3-ctile">
              <div class="w3-cicon purple">#</div>
              <div class="w3-clabel">Slack</div>
              <a class="w3-link" href="#" onclick="return false">@Tim Zhou</a>
            </div>
          </div>

          <!-- Details left, territory map right (sticky, fills the column) -->
          <div class="prof-split">
            <div class="prof-main">

              <div class="prof-card">
                <div class="prof-card-head"><h3>Contact</h3></div>
                <div class="w3-rows">
                  <div class="w3-row"><span class="k">Preferred contact</span><span class="v">The best way to contact me is via email</span></div>
                  <div class="w3-row"><span class="k">Email</span><span class="v"><a class="w3-link" href="mailto:tim.zhou@ibm.com">tim.zhou@ibm.com</a></span></div>
                  <div class="w3-row"><span class="k">Slack</span><span class="v"><a class="w3-link" href="#" onclick="return false">@Tim Zhou</a></span></div>
                  <div class="w3-row"><span class="k">Primary language</span><span class="v">English</span></div>
                  <div class="w3-row"><span class="k">Business address</span><span class="v">1001 Summit Blvd<br>Brookhaven, GA 30319-6408, US<br><span class="dim">Building: HU5 · Office: MOBILE</span></span></div>
                  <div class="w3-row"><span class="k">Work location code</span><span class="v">HU5</span></div>
                  <div class="w3-row"><span class="k">Campus ID</span><span class="v">US152024</span></div>
                </div>
              </div>

              <div class="prof-card">
                <div class="prof-card-head"><h3>Business information</h3></div>
                <div class="w3-rows">
                  <div class="w3-row"><span class="k">Organization</span><span class="v">Sales &gt; Global Sales &gt; IBM Technology, Americas</span></div>
                  <div class="w3-row"><span class="k">Department name</span><span class="v">SELA Infra Territory Sales</span></div>
                  <div class="w3-row"><span class="k">Business unit</span><span class="v">Sales</span></div>
                  <div class="w3-row"><span class="k">Department code</span><span class="v">FCY</span></div>
                  <div class="w3-row"><span class="k">Org code</span><span class="v">GF</span></div>
                  <div class="w3-row"><span class="k">Division code</span><span class="v">12</span></div>
                  <div class="w3-row"><span class="k">Cost center</span><span class="v">FCY</span></div>
                </div>
              </div>

              <div class="prof-card">
                <div class="prof-card-head"><h3>Expertise</h3></div>
                <div class="w3-exp">
                  <div class="w3-expitem">
                    <div class="w3-expname">Territory Sales Specialist (Select Territory)</div>
                    <div class="w3-expdesc">Territory Sales Specialists focus on Select Territory accounts. They are digital sellers who cover an entire suite of products on both an outbound and inbound basis.</div>
                    <span class="badge neutral">Generalist</span>
                  </div>
                  <div class="w3-expitem">
                    <div class="w3-expname">Brand Sales Specialist - Digital</div>
                    <div class="w3-expdesc">Responsible for their Brand's Digital Focus Product offerings and accountable for creating opportunities in a specific segment.</div>
                    <span class="badge neutral">Storage Portfolio</span>
                  </div>
                  <div class="w3-expitem">
                    <div class="w3-expname">Holding Code Digital Sales</div>
                    <div class="w3-expdesc">Exclusively for employees that have been or will be in a commissionable code.</div>
                    <span class="badge neutral">Generalist</span>
                  </div>
                </div>
              </div>

              <div class="prof-card">
                <div class="prof-card-head"><h3>Credentials</h3></div>
                <div class="w3-creds">
                  <span class="w3-cred">Aerospace and Defense Industry Jumpstart</span>
                  <span class="w3-cred">Storage for FlashSystem - Foundational</span>
                  <span class="w3-cred">Global Sales School</span>
                </div>
              </div>

              <div style="margin-top:4px;font-size:12px;color:var(--text3);">Profile data sourced from IBM w3. Contact your manager to update territory or role.</div>
            </div>

            <aside class="prof-aside">
              <div class="prof-card viz-panel map-card">
                <div class="viz-head">
                  <div>
                    <h3>Territory coverage</h3>
                    <p class="viz-label" id="mapLabel">—</p>
                  </div>
                </div>
                <div class="seg seg-wrap" id="mapViews">
                  <button class="seg-btn active" data-view="accounts" onclick="setMapView('accounts')">Accounts</button>
                  <button class="seg-btn" data-view="cadences" onclick="setMapView('cadences')">In cadence</button>
                  <button class="seg-btn" data-view="spend" onclick="setMapView('spend')">IBM spend</button>
                  <button class="seg-btn" data-view="industries" onclick="setMapView('industries')">Industry mix</button>
                </div>
                <div class="seg seg-wrap" id="mapFocus" style="margin-top:8px;">
                  <button class="seg-btn active" data-focus="all" onclick="setMapFocus('all')">All</button>
                  <button class="seg-btn" data-focus="CA" onclick="setMapFocus('CA')">CA</button>
                  <button class="seg-btn" data-focus="HI" onclick="setMapFocus('HI')">HI</button>
                  <button class="seg-btn" data-focus="GU" onclick="setMapFocus('GU')">GU</button>
                  <button class="seg-btn" data-focus="MP" onclick="setMapFocus('MP')">MP</button>
                </div>
                <div class="viz-stats" style="margin:16px 0;">
                  <div class="vstat"><span class="v" id="mapTotal">0</span><span class="l" id="mapTotalLbl">Total</span></div>
                  <div class="vstat"><span class="v" id="mapStates">0</span><span class="l">Territories</span></div>
                  <div class="vstat"><span class="v" id="mapTop">—</span><span class="l">Top territory</span></div>
                </div>
                <div class="usmap" id="usMap"></div>
                <div class="map-foot">
                  <div class="map-scale">
                    <span>0</span><i class="scale-bar"></i><span id="mapScaleMax">0</span>
                  </div>
                </div>
                <div class="map-note">Territories with no accounts are unlit. Click one for detail.</div>
                <div class="map-tip" id="mapTip" style="display:none"></div>
              </div>
            </aside>
          </div>
        </div>

        <!-- ── Personalization tab ── -->
        <div class="profile-section" id="ptab-personalization">
          <div class="ai-note">
            <span class="ai-note-mark">""" + _SPARKLE + """</span>
            <div>These settings shape what <b>watsonx.ai</b> writes for you. Anything carrying
              this mark &mdash; and the purple accent &mdash; is model-generated, not
              deterministic pipeline data.</div>
          </div>

          <!-- Email style -->
          <div class="prof-card">
            <div class="prof-card-head">
              <h3>""" + _SPARKLE + """ Email writing style</h3>
              <button class="reset-link" onclick="resetPref('email')">Reset to default</button>
            </div>
            <div class="field-grid single" style="gap:14px;">
              <div class="field">
                <label>Tone</label>
                <select id="pref-email-tone">
                  <option value="professional">Professional</option>
                  <option value="conversational">Conversational</option>
                  <option value="direct">Direct &amp; concise</option>
                  <option value="warm">Warm &amp; relationship-first</option>
                </select>
              </div>
              <div class="field">
                <label>Context / framing</label>
                <textarea id="pref-email-context" placeholder="e.g. Always open with a reference to the account's recent news or financial results. Avoid mentioning competitors by name."></textarea>
                <span class="hint">Granite will use this as a standing instruction when drafting every email.</span>
              </div>
              <div class="field">
                <label>Example email (optional)</label>
                <textarea id="pref-email-example" rows="6" placeholder="Paste a real email you've sent that reflects your preferred style. Granite will match its structure, length, and voice."></textarea>
              </div>
              <div class="field">
                <label>Behavior notes</label>
                <textarea id="pref-email-behavior" placeholder="e.g. Keep emails under 150 words. Always end with a specific ask. Never use bullet points."></textarea>
              </div>
            </div>
          </div>

          <!-- Call briefings -->
          <div class="prof-card">
            <div class="prof-card-head">
              <h3>""" + _SPARKLE + """ Pre-call briefings</h3>
              <button class="reset-link" onclick="resetPref('call')">Reset to default</button>
            </div>
            <div class="field-grid single" style="gap:14px;">
              <div class="field">
                <label>What to know before each call</label>
                <textarea id="pref-call-know" placeholder="e.g. Recent news about the company, current IBM spend and trend, any open opportunities or past deals."></textarea>
                <span class="hint">Granite will always surface these data points in the pre-call brief.</span>
              </div>
              <div class="field">
                <label>What AI should provide</label>
                <textarea id="pref-call-provide" placeholder="e.g. A one-sentence opening line I can use. The top objection I might face and a response. A suggested product to mention."></textarea>
              </div>
            </div>
          </div>

          <!-- Cadence preferences -->
          <div class="prof-card">
            <div class="prof-card-head">
              <h3>Cadence defaults</h3>
              <button class="reset-link" onclick="resetPref('cadence')">Reset to default</button>
            </div>
            <div class="pref-row">
              <label>Number of touches per cadence</label>
              <span class="pref-hint">steps</span>
              <input type="number" id="pref-cad-steps" min="3" max="20" value="7">
            </div>
            <div class="pref-row">
              <label>Cadence duration</label>
              <span class="pref-hint">days</span>
              <input type="number" id="pref-cad-days" min="7" max="90" value="14">
            </div>
            <div class="pref-row">
              <label>Preferred first touch type</label>
              <select id="pref-cad-first">
                <option value="email">Email</option>
                <option value="call">Call</option>
                <option value="either">Either</option>
              </select>
            </div>
            <div class="pref-row">
              <label>Accounts started per day</label>
              <span class="pref-hint">accounts</span>
              <input type="number" id="pref-cad-starts" min="1" max="10" value="3">
            </div>
            <div class="pref-row">
              <label>Max accounts per cadence</label>
              <span class="pref-hint">accounts</span>
              <input type="number" id="pref-cad-cap" min="3" max="30" value="8">
            </div>
          </div>

          <div style="display:flex;justify-content:flex-end;gap:10px;margin-top:4px;">
            <button class="btn primary" onclick="savePrefs()">Save preferences</button>
          </div>
        </div>

        <!-- ── Settings tab ── -->
        <div class="profile-section" id="ptab-settings">
          <div class="set-split">
            <nav class="set-nav">
              <button class="set-navlink active" data-sec="about" onclick="showSetting('about')">About</button>
              <button class="set-navlink" data-sec="access" onclick="showSetting('access')">Access &amp; sessions</button>
              <button class="set-navlink" data-sec="intel" onclick="showSetting('intel')">How account intelligence works</button>
              <button class="set-navlink" data-sec="ai" onclick="showSetting('ai')">Where AI is used</button>
              <button class="set-navlink" data-sec="data" onclick="showSetting('data')">Data sources</button>
            </nav>

            <div class="set-body">
              <section class="set-sec active" id="set-about">
                <div class="prof-card">
                  <div class="prof-card-head"><h3>About IBM BobBee</h3></div>
                  <p class="set-p">BobBee turns a raw territory list into a ranked, cadenced, day-by-day
                     outreach plan — who to email and call each day of the quarter, and why.</p>
                  <div class="w3-rows" style="margin-top:8px;">
                    <div class="w3-row"><span class="k">Created by</span><span class="v">Sydney Chin &middot; Patrick McBridge &middot; Tim Zhou</span></div>
                    <div class="w3-row"><span class="k">Built for</span><span class="v">The 2026 IBMer watsonx Challenge</span></div>
                    <div class="w3-row"><span class="k">Audience</span><span class="v">Select Territory sellers working a multi-thousand account book</span></div>
                    <div class="w3-row"><span class="k">Model</span><span class="v">watsonx.ai Granite (ibm/granite-4-h-small)</span></div>
                    <div class="w3-row"><span class="k">Design</span><span class="v">IBM Carbon, Gray 100 dark theme, IBM Plex</span></div>
                  </div>
                </div>
              </section>
              <section class="set-sec" id="set-access">
                <div class="prof-card">
                  <div class="prof-card-head"><h3>Access &amp; sessions</h3></div>
                  <p class="set-p">Connected systems and the sessions BobBee is using on your behalf.
                     Nothing here is sent anywhere — every service is mocked locally.</p>
                  <div class="signed-as" id="signedAs" style="margin-top:14px;"></div>
                </div>
                <div class="prof-card">
                  <div class="prof-card-head"><h3>Sessions</h3></div>
                  <div class="alert" id="loginAlert"></div>
                  <div id="loginRows"></div>
                </div>
                <div class="prof-card">
                  <div class="prof-card-head"><h3>Saved password</h3></div>
                  <p class="set-p">One IBM W3ID sign-in covers ISC, ZoomInfo, and Salesloft (all SSO
                     through IBM). In this clone the login is mocked — only the email is kept locally,
                     the password is discarded.</p>
                  <div id="credRows"></div>
                </div>
              </section>

              <section class="set-sec" id="set-intel">
                <div class="prof-card">
                  <div class="prof-card-head"><h3>How account intelligence works</h3></div>
                  <p class="set-p">Sorting accounts into cadences runs a five-stage pipeline. Each stage
                     writes its own output, so you can always see why an account landed where it did.</p>
                  <ol class="set-steps">
                    <li><b>Contacts.</b> Every account is checked for a real IT decision-maker. Accounts
                        without one are set aside into <i>No contacts</i> rather than being worked blind.</li>
                    <li><b>Scoring.</b> Account Tiering scores what's left on IBM spend and trend, install
                        base, company size, and recent buying signals.</li>
                    <li><b>Quarter segmentation.</b> Accounts are split across the four quarters by their
                        buying signals. Only the current quarter's accounts continue; the rest are saved
                        to <i>Future quarters</i>.</li>
                    <li><b>Cadence and rank.</b> Each account is matched to a play, ranked within its
                        cadence, and tagged. Accounts past the per-cadence cap drop to <i>Leftovers</i>
                        and rejoin the pool for a future quarter.</li>
                    <li><b>Distribution.</b> Cadence starts are spread across the quarter's weekdays, and
                        each account's touches are laid on its cadence's step days — producing the
                        day-by-day schedule.</li>
                  </ol>
                </div>
              </section>

              <section class="set-sec" id="set-ai">
                <div class="prof-card">
                  <div class="prof-card-head"><h3>Where AI is used</h3></div>
                  <p class="set-p">The colour convention runs through the whole app:
                     <b style="color:var(--blue-text)">blue</b> is deterministic pipeline data,
                     <b style="color:var(--purple-text)">purple with a sparkle</b> is generated by
                     watsonx.ai. Only two things are model-generated:</p>
                  <ul class="set-list">
                    <li><b>Play and sales angle</b> on the account detail popup.</li>
                    <li><b>Pre-call briefs</b> on the Call tab.</li>
                  </ul>
                  <p class="set-p">Everything else — scoring, ranking, cadence assignment, the schedule,
                     email drafts — is deterministic Python. If watsonx is unreachable or has no key, both
                     features fall back to deterministic output built from the same account data, so the
                     app keeps working.</p>
                </div>
              </section>

              <section class="set-sec" id="set-data">
                <div class="prof-card">
                  <div class="prof-card-head"><h3>Data sources</h3></div>
                  <div class="w3-rows">
                    <div class="w3-row"><span class="k">IBM Sales Cloud / ISC</span><span class="v">Territory accounts, coverage IDs, IBM spend, relationship status</span></div>
                    <div class="w3-row"><span class="k">IBM install base</span><span class="v">Installed products per account, used for whitespace</span></div>
                    <div class="w3-row"><span class="k">ZoomInfo</span><span class="v">Company revenue and size, contacts and their titles</span></div>
                    <div class="w3-row"><span class="k">Salesloft</span><span class="v">Cadence definitions, steps, and per-account progress</span></div>
                    <div class="w3-row"><span class="k">News and signals</span><span class="v">Funding, M&amp;A, leadership and expansion events per account</span></div>
                    <div class="w3-row"><span class="k">watsonx.ai</span><span class="v">Granite, for plays/angles and pre-call briefs only</span></div>
                  </div>
                  <p class="set-p" style="margin-top:16px;">Every source except watsonx.ai is mocked with
                     deterministic local data, so the app runs with no logins, no VPN, and no internet.</p>
                </div>
              </section>

            </div>
          </div>
        </div>
      </div>
    </section>
  </main>
</div>

<!-- ── Contextual side panel (Email + Call tabs) ── -->
<div class="side-panel" id="sidePanel">
  <div class="day-panel-head">
    <h3 id="sidePanelTitle">Details</h3>
    <button class="day-panel-close" onclick="closeSidePanel()">&#10005;</button>
  </div>
  <div class="side-panel-body" id="sidePanelBody"></div>
</div>

<!-- ── Day-detail side panel (Plan tab) — outside #app so position:fixed is always viewport-relative ── -->
<div class="day-panel" id="dayPanel">
  <div class="day-panel-head">
    <h3 id="dayPanelTitle">—</h3>
    <button class="day-panel-close" onclick="closeDayPanel()">&#10005;</button>
  </div>
  <div class="day-panel-sums" id="dayPanelSums"></div>
  <div class="day-panel-items" id="dayPanelItems"></div>
</div>

<!-- ── account detail modal ─────────────────────────────────────── -->
<div class="modal" id="acctModal" onclick="if(event.target===this) closeAcctModal()">
  <div class="modal-card wide">
    <div class="modal-head">
      <h2 id="acctModalTitle">Account</h2>
      <button class="link" onclick="closeAcctModal()">Close</button>
    </div>
    <div id="acctModalBody"></div>
  </div>
</div>

<!-- ── Details (Access) modal ─────────────────────────────────── -->
<script>
// The one marker for "watsonx generated this" — kept in JS too so buttons that
// rebuild their own label can restore it instead of dropping it.
const AI_SPARK = '""" + _SPARKLE.replace("'", "\\'") + """';

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
  // Access lives inline in Profile → Settings now; keep the entry point so any
  // remaining caller lands in the right place instead of opening a dead modal.
  showPage('profile');
  switchProfileTab('settings');
  showSetting('access');
}
function closeDetails(){}

// ── page nav ──────────────────────────────────────────────────
function showPage(name, opts){
  // Any right-hand panel belongs to the page that opened it — leaving that page
  // should take it with you, not leave it hanging over the next one.
  closeDayPanel();
  closeSidePanel();
  document.querySelectorAll('.page').forEach(p => p.classList.toggle('active', p.id === 'page-' + name));
  document.querySelectorAll('.navlink').forEach(b => b.classList.toggle('active', b.dataset.page === name));
  if (name === 'accounts'){ fetchAccountsList(); fetchStrategizeStatus(); }
  if (name === 'dashboard'){ refreshDashboard(); }
  if (name === 'plan'){ fetchSchedule(); }
  if (name === 'cadences'){ fetchCadences(opts && opts.open); }
  if (name === 'email'){ fetchTodayEmail(); }
  if (name === 'call'){ fetchTodayCall(); }
  if (name === 'profile'){ loadProfilePage(); }
}

// ── accounts tab: strategize stages ───────────────────────────
const STAGE_ORDER = ['contacts', 'scoring', 'quarters', 'cadences', 'schedule', 'done'];
function stageIdx(phase){ return STAGE_ORDER.indexOf(phase); }

function setStageEl(id, cls, msg){
  const el = document.getElementById(id);
  el.className = 'stage ' + cls;
  el.querySelector('.dot').className = 'dot sicon ' + cls;
  if (msg) el.querySelector('.smsg').textContent = msg;
}

function renderStages(a){
  const box = document.getElementById('stages');
  if (!a || a.phase === 'idle' || (a.done && !a.active)){ box.style.display = 'none'; return; }
  box.style.display = '';
  const idx = stageIdx(a.phase);
  const err = a.phase === 'error';
  const c = a.counts || {};

  if (err && idx <= 0) setStageEl('stage-contacts', 'err', a.message);
  else if (idx === 0) setStageEl('stage-contacts', 'running', a.message);
  else if (idx > 0) setStageEl('stage-contacts', 'done',
    c.no_contacts != null ? `${c.no_contacts} of ${c.total} accounts had no IT decision-maker — saved to No Contacts.` : 'Done.');

  if (err && idx > 0 && idx <= 2) setStageEl('stage-scoring', 'err', a.message);
  else if (idx === 1 || idx === 2) setStageEl('stage-scoring', 'running', a.message);
  else if (idx > 2) setStageEl('stage-scoring', 'done',
    c.current_quarter != null ? `${c.current_quarter} accounts selected for this quarter.` : 'Done.');

  if (err && idx === 3) setStageEl('stage-cadences', 'err', a.message);
  else if (idx === 3) setStageEl('stage-cadences', 'running', a.message);
  else if (idx > 3) setStageEl('stage-cadences', 'done',
    c.cadences ? `${Object.keys(c.cadences).length} cadence(s) built${c.leftovers ? ` — ${c.leftovers} account(s) moved to Leftovers` : ''}.` : 'Done.');

  if (err && idx === 4) setStageEl('stage-schedule', 'err', a.message);
  else if (idx === 4) setStageEl('stage-schedule', 'running', a.message);
  else if (idx > 4) setStageEl('stage-schedule', 'done',
    c.scheduled_activities ? `${c.scheduled_activities} touches distributed across the quarter.` : 'Done.');

  document.getElementById('strategizeBtn').disabled = !!a.active;
}

// ── accounts tab: lists, search, tag filter, detail popup ─────
let _acctData = null;
let _acctSel = 'all';
const _tagSel = new Set();

const TAG_TIPS = {
  'Whitespace':             'No IBM product installed — fresh opportunity to land new revenue.',
  'Whitespace: AI':         'No IBM AI product installed — open opportunity for watsonx.',
  'Whitespace: Security':   'No IBM security product installed — open opportunity for QRadar/Verify.',
  'Whitespace: Storage':    'No IBM storage product installed — open opportunity for Storage solutions.',
  'Whitespace: Hybrid':     'No IBM hybrid cloud product — open opportunity for Cloud Paks.',
  'Bluemix footprint':      'Existing IBM Cloud / Bluemix usage — expand within the platform.',
  'At-risk spend':          'IBM spend is declining year-over-year — risk of churn; prioritize retention.',
  'Competitive displacement':'Competitor product detected in install base — opportunity to displace.',
  'Growing spend':          'IBM spend is growing year-over-year — healthy momentum, expand further.',
};
function tagTip(t){
  if (TAG_TIPS[t]) return TAG_TIPS[t];
  if (t.startsWith('Whitespace')) return 'No IBM product in this category installed — open whitespace opportunity.';
  return '';
}

function tagClass(t){
  if (t.startsWith('Whitespace') || t === 'Bluemix footprint') return 'white';
  if (t === 'At-risk spend' || t === 'Competitive displacement') return 'risk';
  if (t === 'Growing spend') return 'up';
  return '';
}

function renderSidebar(){
  const bar = document.getElementById('acctsSidebar');
  if (!_acctData || !_acctData.strategized){ bar.style.display = 'none'; return; }
  bar.style.display = '';
  const L = _acctData.lists;
  const item = (key, label, n) =>
    `<button class="slist ${_acctSel === key ? 'active' : ''}" onclick="selectList('${esc(key)}')">${esc(label)}<span class="n">${n}</span></button>`;
  bar.innerHTML = '<h4>Lists</h4>'
    + item('all', 'All accounts', L.all)
    + '<h4>Cadences</h4>'
    + Object.entries(L.cadences).map(([nm, n]) => item('cadence:' + nm, nm, n)).join('')
    + '<h4>Set aside</h4>'
    + item('leftovers', 'Leftovers', L.leftovers)
    + item('no_contacts', 'No contacts', L.no_contacts)
    + item('future', 'Future quarters', L.future);
}

function selectList(key){ _acctSel = key; renderSidebar(); renderAccounts(); }
function toggleTag(t){ _tagSel.has(t) ? _tagSel.delete(t) : _tagSel.add(t); renderTagFilters(); renderAccounts(); }

function renderTagFilters(){
  const legend = document.getElementById('tagLegend');
  if (!legend) return;
  if (!_acctData || !_acctData.strategized){ legend.style.display = 'none'; return; }
  const tags = [...new Set(_acctData.accounts.flatMap(a => a.tags || []))];
  legend.style.display = tags.length ? '' : 'none';
}

// Global search routes into the Accounts list, which already does the filtering.
// Live once there's enough to be meaningful, so a stray keystroke doesn't yank
// you off the page you're on; Enter always jumps.
function globalSearch(q){
  if ((q || '').trim().length < 2) return;
  globalSearchGo();
}

function globalSearchGo(){
  const q = (document.getElementById('globalSearch')?.value || '').trim();
  if (!q) return;
  showPage('accounts');
  _acctSel = 'all';
  const box = document.getElementById('acctSearch');
  if (box) box.value = q;
  if (_acctData) renderAccounts();
}

function renderAccounts(){
  const host = document.getElementById('acctList');
  if (!_acctData) return;
  const q = (document.getElementById('acctSearch')?.value || '').toLowerCase();
  const inCadenceView = _acctSel.startsWith('cadence:');
  const currentCadence = inCadenceView ? _acctSel.slice(8) : null;

  let rows = _acctData.accounts;
  if (inCadenceView){
    rows = rows.filter(a => a.cadence === currentCadence).sort((x, y) => (x.rank || 99) - (y.rank || 99));
  } else if (_acctSel !== 'all'){
    const bucket = _acctSel === 'no_contacts' ? 'no_contacts' : _acctSel === 'leftovers' ? 'leftovers' : 'future';
    rows = rows.filter(a => a.bucket === bucket);
  }
  if (q) rows = rows.filter(a => (a.account || '').toLowerCase().includes(q) || (a.industry || '').toLowerCase().includes(q));
  if (_tagSel.size) rows = rows.filter(a => [..._tagSel].every(t => (a.tags || []).includes(t)));

  if (!rows.length){ host.innerHTML = '<div class="aitems-empty">No accounts match.</div>'; return; }

  // "View in Cadences →" header when browsing a specific cadence list.
  const cadHdr = inCadenceView
    ? `<div style="display:flex;align-items:center;justify-content:space-between;padding:10px 18px;background:var(--layer2);border-bottom:1px solid var(--border);font-size:12.5px;">
        <span style="font-weight:600;">${esc(currentCadence)}</span>
        <button class="link" onclick="goToCadence('${esc(currentCadence)}')">View in Cadences &#8594;</button>
       </div>`
    : '';

  // Carbon data tables are always headed. Which optional columns exist is a
  // property of the *view*, not the row, so decide once — otherwise a row with
  // no cadence drops its cell and knocks the remaining columns out of line.
  const showRank = inCadenceView;
  // One template drives both the header and every row (see .acct-row CSS).
  const cols = [
    showRank ? '38px' : null,
    // Floor, not 0: with the day panel open the container narrows, and a
    // minmax(0,1fr) account column collapses to "Ke…" while the fixed columns
    // keep their width. The list scrolls sideways before the name gives up.
    'minmax(200px,340px)', // account — capped so industry stays near the left
    '190px',               // industry
    '150px',               // location
    'minmax(0,1fr)',       // spacer: absorbs slack instead of the name column
    '110px',               // signals
  ].filter(Boolean).join(' ');

  const head = `<div class="acct-row acct-head">
      ${showRank ? '<span class="arank">#</span>' : ''}
      <span class="an">Account</span>
      <span class="ai">Industry</span>
      <span class="aloc">Location</span>
      <span></span>
      <span class="atags">Signals</span>
    </div>`;

  host.innerHTML = `<div class="acct-list" style="--acct-cols:${cols}">` + cadHdr + head + rows.map(a => {
    const dots = (a.tags || []).map(t => {
      const cls = tagClass(t) || 'neutral';
      const tip = t + (tagTip(t) ? ': ' + tagTip(t) : '');
      return `<span class="tagdot ${cls}"${tip ? ` data-tip="${esc(tip)}"` : ''}></span>`;
    }).join('');
    return `<div class="acct-row" style="cursor:pointer" onclick="openAcctModal('${esc(a.account)}')">
      ${showRank ? `<span class="arank">${a.rank ? '#' + a.rank : ''}</span>` : ''}
      <span class="an" title="${esc(a.account || '')}">${esc(a.account || '')}</span>
      <span class="ai" title="${esc(a.industry || '')}">${esc(a.industry || '')}</span>
      <span class="aloc">${esc(a.location || '')}</span>
      <span></span>
      <span class="atags" style="display:flex;gap:4px;align-items:center;">${dots}</span>
    </div>`;
  }).join('') + '</div>';
}

function renderAccountList(data){
  _acctData = data;
  const count = document.getElementById('acctsCount');
  const empty = document.getElementById('acctsEmpty');
  const body = document.getElementById('acctsBody');
  if (!data.has_accounts){ empty.style.display = ''; body.style.display = 'none'; return; }
  empty.style.display = 'none'; body.style.display = '';

  document.getElementById('acctsTools').style.display = data.strategized ? '' : 'none';
  document.getElementById('strategizeBtn').textContent = data.strategized ? 'Refresh cadences' : 'Sort accounts into cadences';
  renderSidebar(); renderTagFilters();

  if (!data.strategized){
    count.textContent = `${data.accounts.length} accounts`;
    renderAccounts();
    return;
  }
  const L = data.lists;
  const inCadences = Object.values(L.cadences).reduce((n, x) => n + x, 0);
  count.innerHTML = `${L.all} accounts &middot; ${inCadences} in Q${data.current_quarter} cadences`;
  renderAccounts();
}

async function fetchAccountsList(){
  let data;
  try { data = await (await fetch('/api/accounts/list')).json(); } catch(e){ return; }
  renderAccountList(data);
}

async function fetchStrategizeStatus(){
  let data;
  try { data = await (await fetch('/api/status')).json(); } catch(e){ return; }
  const a = (data._actions || {}).strategize;
  renderStages(a);
  if (a && a.done && !_strategizeWasDone){ _strategizeWasDone = true; fetchAccountsList(); fetchSchedule(); refreshDashboard(); }
  if (!a || !a.done) _strategizeWasDone = false;
}
let _strategizeWasDone = false;

function closeRefreshModal(){ document.getElementById('refreshModal').classList.remove('show'); }

async function confirmRefresh(){
  closeRefreshModal();
  const res = await fetch('/api/strategize/run', {method:'POST'});
  const body = await res.json();
  if (!body.ok){ alert('Error: ' + body.error); return; }
  fetchStrategizeStatus();
}

async function runStrategize(){
  // If already strategized, show the refresh confirmation instead of running immediately.
  if (_acctData && _acctData.strategized){
    document.getElementById('refreshModal').classList.add('show');
    return;
  }
  const res = await fetch('/api/strategize/run', {method:'POST'});
  const body = await res.json();
  if (!body.ok){ alert('Error: ' + body.error); return; }
  fetchStrategizeStatus();
}

// ── account detail popup ──────────────────────────────────────
function fmtMoney(v){
  if (v == null || v === '') return '—';
  const n = Number(v);
  if (isNaN(n)) return String(v);
  if (Math.abs(n) >= 1e9) return '$' + (n / 1e9).toFixed(1) + 'B';
  if (Math.abs(n) >= 1e6) return '$' + (n / 1e6).toFixed(1) + 'M';
  if (Math.abs(n) >= 1e3) return '$' + Math.round(n / 1e3) + 'K';
  return '$' + n.toLocaleString();
}
const kv = (k, v) => `<div class="kv"><span class="k">${esc(k)}</span><span class="v">${v == null || v === '' ? '—' : esc(String(v))}</span></div>`;

async function openAcctModal(name){
  let d;
  try { d = await (await fetch('/api/accounts/detail?name=' + encodeURIComponent(name))).json(); } catch(e){ return; }
  document.getElementById('acctModalTitle').textContent = d.account;
  const sc = d.sales_cloud, zi = d.zoominfo, sl = d.salesloft, ai = d.ai;
  document.getElementById('acctModalBody').innerHTML = `
    <div style="margin-bottom:12px;">${(d.tags || []).map(t => `<span class="tagpill ${tagClass(t)}">${esc(t)}</span>`).join(' ')}</div>
    <div class="detail-grid">
      <div class="panel ai-panel full"><h3>""" + _SPARKLE + """AI analysis</h3>
        ${kv('Urgency', ai.urgency + (ai.score != null ? ` (score ${Number(ai.score).toFixed(1)}, tier ${ai.tier})` : ''))}
        ${kv('Best product fit', ai.product_fit)}
        ${kv('Recommended play', ai.play)}
        ${ai.angle ? `<div style="font-size:12.5px; margin-top:10px; line-height:1.5;">${esc(ai.angle)}</div>` : ''}
      </div>
      <div class="panel"><h3>IBM Sales Cloud</h3>
        ${kv('Industry', sc.industry)}${kv('Coverage ID', sc.coverage_id)}${kv('Relationship', sc.relationship)}
        ${kv('IBM spend (current)', fmtMoney(sc.ibm_spend_current))}${kv('IBM spend (prior)', fmtMoney(sc.ibm_spend_prior))}
        ${kv('Spend trend', sc.spend_trend)}${kv('Installs', sc.install_summary)}
      </div>
      <div class="panel"><h3>ZoomInfo</h3>
        ${kv('Annual revenue', fmtMoney(zi.revenue))}${kv('Employees', zi.employees != null ? Number(zi.employees).toLocaleString() : null)}
        <div style="margin-top:10px;">
          ${(zi.contacts || []).map(c => `<div class="contact-row"><span class="cn">${esc(c.first_name)} ${esc(c.last_name)}</span><span class="ct">${esc(c.title)}</span>${c.decision_maker ? '<span class="dm-badge">Decision maker</span>' : ''}</div>`).join('') || '<div class="note">No contacts found.</div>'}
        </div>
      </div>
      <div class="panel"><h3>Salesloft</h3>
        ${kv('Cadence', sl.cadence)}${kv('Rank in cadence', sl.rank != null ? '#' + sl.rank : null)}
        <div style="margin-top:10px;">
          ${(sl.touches || []).map(t => `<div class="act-row"><span class="act-type ${esc(t.type)}">${esc(t.type)}</span><span>${esc(t.date)}</span><span style="color:var(--text3)">${esc(t.step)}</span></div>`).join('') || '<div class="note">No touches scheduled.</div>'}
        </div>
      </div>
      <div class="panel"><h3>Signals &amp; news</h3>
        ${(d.signals || []).map(s => `<div class="news-item"><span class="nd">${esc(s.date)}</span><div class="nb"><span class="na">${esc(s.type)}</span> — ${esc(s.summary)}</div></div>`).join('') || '<div class="note">No recent signals.</div>'}
      </div>
    </div>`;
  document.getElementById('acctModal').classList.add('show');
}
function closeAcctModal(){ document.getElementById('acctModal').classList.remove('show'); }

// The app's "today" always comes from the server (window.__today), never the
// browser clock — BOBBEE_DEMO_DATE can pin the app to a different day, and a
// half-pinned UI (Monday's schedule under Saturday's header) is worse than none.
function appTodayIso(){ return window.__today || new Date().toISOString().slice(0,10); }
function appTodayDate(){ const [y,m,d] = appTodayIso().split('-').map(Number); return new Date(y, m-1, d); }
function appTodayLabel(){
  return appTodayDate().toLocaleDateString(undefined, {weekday:'long', month:'long', day:'numeric'});
}

// ── plan calendar (quarter / month / week / day) ──────────────
let _cal = {view: 'month', anchor: appTodayDate(), data: null, sel: null};

function isoOf(d){ return d.toISOString().slice(0, 10); }
function dayInfo(iso){ return (_cal.data && _cal.data.days[iso]) || null; }

// Totals for one quarter, for the year view's per-quarter summary line.
// Accounts are de-duplicated across the quarter, so it's "distinct accounts
// touched", not a sum of daily counts.
function quarterTotals(year, q){
  const out = {emails: 0, calls: 0, accounts: 0};
  if (!_cal.data) return out;
  const seen = new Set();
  for (const [iso, info] of Object.entries(_cal.data.days)){
    const d = new Date(iso + 'T00:00:00');
    if (d.getFullYear() !== year || Math.floor(d.getMonth() / 3) !== q) continue;
    out.emails += info.emails || 0;
    out.calls += info.calls || 0;
    (info.accounts || []).forEach(n => seen.add(n));
  }
  out.accounts = seen.size;
  return out;
}

async function fetchSchedule(){
  let d;
  try { d = await (await fetch('/api/schedule')).json(); } catch(e){ return; }
  _cal.data = d.has_schedule ? d : null;
  renderCal();
}

// Drill from the year (or quarter) view into one month.
function openMonth(year, month){
  _cal.anchor = new Date(year, month, 1);
  setCalView('month');
}

function setCalView(v){
  _cal.view = v;
  document.querySelectorAll('#page-plan .range-btn').forEach(b => b.classList.toggle('active', b.dataset.view === v));
  renderCal();
}

function calStep(dir){
  const a = new Date(_cal.anchor);
  if (_cal.view === 'year') a.setFullYear(a.getFullYear() + dir);
  else if (_cal.view === 'month' || _cal.view === 'quarter') a.setMonth(a.getMonth() + dir * (_cal.view === 'quarter' ? 3 : 1));
  else a.setDate(a.getDate() + dir * (_cal.view === 'week' ? 7 : 1));
  _cal.anchor = a;
  renderCal();
}

// Fill + open the right-side day panel. Pure (no renderCal) so it can be called
// from both selectCalDay and renderCal's day-view branch without recursion.
function fillDayPanel(iso){
  const info = dayInfo(iso) || {emails: 0, calls: 0, accounts: [], items: []};
  const d = new Date(iso + 'T00:00:00');
  document.getElementById('dayPanelTitle').textContent = d.toLocaleDateString(undefined, {weekday: 'long', month: 'long', day: 'numeric'});
  document.getElementById('dayPanelSums').innerHTML =
    `<b>${info.emails}</b> email${info.emails === 1 ? '' : 's'} &middot; <b>${info.calls}</b> call${info.calls === 1 ? '' : 's'} &middot; <b>${info.accounts.length}</b> account${info.accounts.length === 1 ? '' : 's'} touched`;
  // Group by activity type — all emails under an "Emails" header, then all calls
  // under a "Calls" header — instead of interleaving them with per-row tags.
  const items = info.items || [];
  const row = a => `<div class="panel-act"><div class="panel-act-body"><div class="pa-acct">${esc(a.account)}</div><div class="pa-step">${esc(a.step)} &middot; ${esc(a.cadence)}</div></div></div>`;
  const section = (label, arr) => arr.length
    ? `<div class="day-panel-section">${label} (${arr.length})</div>` + arr.map(row).join('')
    : '';
  const emails = items.filter(a => a.type === 'email');
  const calls = items.filter(a => a.type === 'call');
  document.getElementById('dayPanelItems').innerHTML =
    items.length ? section('Emails', emails) + section('Calls', calls)
                 : '<div class="note" style="padding-top:14px;">Nothing scheduled.</div>';
  document.getElementById('dayPanel').classList.add('open');
  // Shift the page instead of covering it — the panel is a fixed overlay, so
  // without this it sits on top of the calendar you're reading it against.
  document.body.classList.add('day-panel-open');
}

function selectCalDay(iso){
  _cal.sel = iso;
  renderCal();       // re-highlight the selected cell (renderCal never calls back)
  fillDayPanel(iso); // then open the right-side panel
}

function closeDayPanel(){
  document.getElementById('dayPanel').classList.remove('open');
  document.body.classList.remove('day-panel-open');
  _cal.sel = null;
  renderCal();
}

function monthGridHTML(year, month, compact){
  const first = new Date(year, month, 1);
  const label = first.toLocaleDateString(undefined, {month: 'long', year: 'numeric'});
  // Server's today, not the browser's — they differ under BOBBEE_DEMO_DATE.
  const todayIso = appTodayIso();
  // Weekdays only — cadences never schedule on a weekend, so Sat/Sun columns
  // were two permanently empty stripes down every calendar.
  let cells = '<div class="cal-grid">' + ['Mon','Tue','Wed','Thu','Fri'].map(d => `<div class="dow">${d}</div>`).join('');
  // Monday-based lead-in: getDay() is 0=Sun, so shift to 0=Mon and skip weekends.
  const lead = (first.getDay() + 6) % 7;
  for (let i = 0; i < Math.min(lead, 5); i++) cells += '<div class="cal-cell out compact"></div>';
  const dim = new Date(year, month + 1, 0).getDate();
  for (let day = 1; day <= dim; day++){
    const dow = new Date(year, month, day).getDay();
    if (dow === 0 || dow === 6) continue;
    const iso = isoOf(new Date(Date.UTC(year, month, day)));
    const info = dayInfo(iso);
    const n = info ? info.emails + info.calls : 0;
    cells += `<div class="cal-cell ${compact ? 'compact' : ''} ${info ? 'has' : ''} ${iso === todayIso ? 'today' : ''} ${iso === _cal.sel ? 'sel' : ''}"
      ${info ? `onclick="selectCalDay('${iso}')"` : ''}>
      <span class="d">${day}</span>${info && !compact ? `<div class="acts">${info.emails}e &middot; ${info.calls}c</div>` : info ? `<div class="acts">${n}</div>` : ''}</div>`;
  }
  cells += '</div>';
  return {label, html: cells};
}

function renderCal(){
  const grid = document.getElementById('calGrid');
  const label = document.getElementById('calLabel');
  if (!grid) return;
  if (!_cal.data){ grid.innerHTML = ''; return; }
  const a = _cal.anchor;

  if (_cal.view === 'year'){
    // Whole year, grouped into its four quarters (each a row of three months).
    label.textContent = String(a.getFullYear());
    grid.innerHTML = '<div class="cal-year">' + [0, 1, 2, 3].map(q => {
      const months = [0, 1, 2].map(i => {
        const mi = q * 3 + i;
        const m = monthGridHTML(a.getFullYear(), mi, true);
        // The month heading drills into the full month view; day cells inside
        // still open the day panel (monthGridHTML wires those itself).
        return `<div class="cal-month">
          <h4 class="cal-month-link" onclick="openMonth(${a.getFullYear()}, ${mi})">${m.label}</h4>
          ${m.html}</div>`;
      }).join('');
      const tot = quarterTotals(a.getFullYear(), q);
      return `<section class="cal-qblock">
        <div class="cal-qhead">
          <h4>Q${q + 1}</h4>
          <span class="cal-qsum">${tot.emails} emails &middot; ${tot.calls} calls &middot; ${tot.accounts} accounts</span>
        </div>
        <div class="cal-quarter">${months}</div>
      </section>`;
    }).join('') + '</div>';
  } else if (_cal.view === 'quarter'){
    const q = Math.floor(a.getMonth() / 3);
    label.textContent = `Q${q + 1} ${a.getFullYear()}`;
    grid.innerHTML = '<div class="cal-quarter">' + [0, 1, 2].map(i => {
      const mi = q * 3 + i;
      const m = monthGridHTML(a.getFullYear(), mi, true);
      return `<div class="cal-month">
        <h4 class="cal-month-link" onclick="openMonth(${a.getFullYear()}, ${mi})">${m.label}</h4>
        ${m.html}</div>`;
    }).join('') + '</div>';
  } else if (_cal.view === 'month'){
    const m = monthGridHTML(a.getFullYear(), a.getMonth(), false);
    label.textContent = m.label;
    grid.innerHTML = `<div class="cal-month">${m.html}</div>`;
  } else if (_cal.view === 'week'){
    const mon = new Date(a); mon.setDate(a.getDate() - ((a.getDay() + 6) % 7));
    const fri = new Date(mon); fri.setDate(mon.getDate() + 4);
    label.textContent = `${mon.toLocaleDateString(undefined, {month: 'short', day: 'numeric'})} – ${fri.toLocaleDateString(undefined, {month: 'short', day: 'numeric'})}`;
    grid.innerHTML = '<div class="cal-week">' + [0, 1, 2, 3, 4].map(i => {
      const d = new Date(mon); d.setDate(mon.getDate() + i);
      const iso = isoOf(new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate())));
      const info = dayInfo(iso);
      return `<div class="cal-weekday ${iso === _cal.sel ? 'sel' : ''}" onclick="selectCalDay('${iso}')">
        <h5>${d.toLocaleDateString(undefined, {weekday: 'short', month: 'short', day: 'numeric'})}</h5>
        <div class="cnt">${info ? `${info.emails} emails &middot; ${info.calls} calls` : 'Free'}</div>
        ${info ? info.accounts.slice(0, 4).map(n => `<div style="font-size:11.5px; padding:2px 0;">${esc(n)}</div>`).join('') + (info.accounts.length > 4 ? `<div style="font-size:11px; color:var(--text3);">+${info.accounts.length - 4} more</div>` : '') : ''}
      </div>`;
    }).join('') + '</div>';
  } else {
    // Day view: no grid, just drive the right-side panel to the anchor day.
    const iso = isoOf(new Date(Date.UTC(a.getFullYear(), a.getMonth(), a.getDate())));
    label.textContent = a.toLocaleDateString(undefined, {weekday: 'long', month: 'long', day: 'numeric'});
    grid.innerHTML = '';
    _cal.sel = iso;
    fillDayPanel(iso);
  }
}

// ── gates: every tab needs accounts (and most need a strategy) ─
async function refreshGates(){
  let st, dash;
  try { st = await (await fetch('/api/status')).json(); } catch(e){ return; }
  const hasAccounts = st.segment && st.segment.state === 'done';
  try { dash = await (await fetch('/api/dashboard')).json(); } catch(e){ dash = {has_schedule: false}; }
  const hasPlan = !!dash.has_schedule;

  const show = (id, on) => { const el = document.getElementById(id); if (el) el.style.display = on ? '' : 'none'; };
  show('dashboardEmpty', !hasAccounts);
  show('dashboardStrat', hasAccounts && !hasPlan);
  show('dashboardBody', hasAccounts && hasPlan);
  show('planEmpty', !hasAccounts);
  show('planStrat', hasAccounts && !hasPlan);
  show('planBody', hasAccounts && hasPlan);
  show('cadencesEmpty', !hasAccounts);
  show('cadencesStratEmpty', hasAccounts && !hasPlan);
  show('cadencesBody', hasAccounts && hasPlan);
  show('emailEmpty', !hasAccounts);
  show('emailStratEmpty', hasAccounts && !hasPlan);
  show('emailBody', hasAccounts && hasPlan);
  show('callEmpty', !hasAccounts);
  show('callStratEmpty', hasAccounts && !hasPlan);
  show('callBody', hasAccounts && hasPlan);
  if (hasAccounts && hasPlan) renderDashboard(dash);
  // Accounts landed since the last list fetch (import just finished) — refresh.
  if (hasAccounts && (!_acctData || !_acctData.has_accounts)) fetchAccountsList();
}

// ── dashboard activity chart ───────────────────────────────────
// Bars are stacked emails-over-calls and scaled to the tallest bucket, so the
// shape stays readable whether a period holds 3 activities or 300.
let _vizPeriod = 'week';
let _vizOffset = 0;   // 0 = current window; -1/+1 step back/forward
// refreshGates() re-renders the dashboard every 2s; without this the chart would
// refetch and replay its transitions on every tick. Reset by refreshDashboard()
// so a fresh strategize does rebuild it.
let _vizLoaded = false;

function stepViz(dir){
  _vizOffset += dir;
  loadViz();
}

function stepVizNow(){
  _vizOffset = 0;
  loadViz();
}

function setVizPeriod(p){
  _vizPeriod = p;
  _vizOffset = 0;   // switching grain returns to the current window
  document.querySelectorAll('#vizPeriods .seg-btn')
    .forEach(b => b.classList.toggle('active', b.dataset.period === p));
  loadViz();
}

async function loadViz(){
  let v;
  try { v = await (await fetch(`/api/dashboard/progress?period=${_vizPeriod}&offset=${_vizOffset}`)).json(); }
  catch(e){ return; }
  if (!v || !v.has_schedule) return;
  renderViz(v);
}

function renderViz(v){
  document.getElementById('vizLabel').textContent = v.label;
  const nowBtn = document.getElementById('vizNowBtn');
  if (nowBtn) nowBtn.style.display = _vizOffset ? '' : 'none';
  document.getElementById('vizEmails').textContent = v.totals.emails;
  document.getElementById('vizCalls').textContent = v.totals.calls;
  document.getElementById('vizAccounts').textContent = v.totals.accounts;

  // Ring = share of this window's activities whose day has already passed.
  // There's no per-activity completion flag, so "worked" means scheduled on or
  // before today — not confirmed done.
  const done = v.elapsed, total = v.elapsed + v.upcoming;
  const pct = total ? done / total : 0;
  const C = 2 * Math.PI * 52;
  const ring = document.getElementById('vizRing');
  ring.style.strokeDasharray = C;
  ring.style.strokeDashoffset = C * (1 - pct);
  document.getElementById('vizPct').textContent = Math.round(pct * 100) + '%';

  const host = document.getElementById('vizChart');
  const series = v.series || [];
  if (!series.length){
    host.innerHTML = '<div class="viz-empty">Nothing scheduled in this period.</div>';
    // Clear the axis too, or the previous period's ticks/gridlines linger.
    const ya = document.getElementById('vizYAxis'), gr = document.getElementById('vizGrid');
    if (ya) ya.innerHTML = '';
    if (gr) gr.innerHTML = '';
    return;
  }
  // carbon-charts rounds the y-axis up to a "nice" number (1/2/5 x 10^n) so the
  // ticks land on readable values instead of the raw data maximum.
  const peak = Math.max(1, ...series.map(s => s.emails + s.calls));
  const niceMax = (n) => {
    const mag = Math.pow(10, Math.floor(Math.log10(n)));
    const f = n / mag;
    return (f <= 1 ? 1 : f <= 2 ? 2 : f <= 5 ? 5 : 10) * mag;
  };
  const max = niceMax(peak);
  const TICKS = 4;
  host.innerHTML = series.map(s => {
    const tot = s.emails + s.calls;
    const h = t => Math.round((t / max) * 120);
    // "Now" comes from the server, not the browser clock — they differ whenever
    // BOBBEE_DEMO_DATE pins the app to a different day.
    const isNow = (v.period === 'week' && s.label === v.today_short)
               || (v.period === 'quarter' && s.label === v.today_month);
    const stack = tot === 0
      ? '<div class="vbar-seg zero"></div>'
      : `<div class="vbar-seg call" style="height:${h(s.calls)}px"></div>
         <div class="vbar-seg email" style="height:${h(s.emails)}px"></div>`;
    return `<div class="vbar ${isNow ? 'now' : ''}">
      <span class="vbar-val">${tot || ''}</span>
      <div class="vbar-stack" title="${esc(s.label)}: ${s.emails} emails, ${s.calls} calls">${stack}</div>
      <span class="vbar-lbl">${esc(s.label)}</span>
    </div>`;
  }).join('');

  // Gridlines have to line up with the *plot band* — the 120px stack area — not
  // the container, which also holds the value label above and the tick label
  // below. Measure a real bar rather than assuming those label heights.
  const yAxis = document.getElementById('vizYAxis');
  const grid = document.getElementById('vizGrid');
  const stackEl = host.querySelector('.vbar-stack');
  if (yAxis && grid && stackEl){
    const gRect = grid.parentElement.getBoundingClientRect();
    const sRect = stackEl.getBoundingClientRect();
    const top = sRect.top - gRect.top;
    const band = sRect.height;
    const ticks = [];
    for (let i = TICKS; i >= 0; i--) ticks.push(Math.round((max / TICKS) * i));
    yAxis.style.height = band + 'px';
    yAxis.style.paddingBottom = '0';
    yAxis.style.marginTop = top + 'px';
    yAxis.innerHTML = ticks.map(t => `<span class="viz-ytick">${t}</span>`).join('');
    grid.innerHTML = ticks.map((t, i) => {
      const y = top + band * (i / TICKS);
      return `<div class="viz-gridline ${i === TICKS ? 'zero' : ''}" style="top:${y}px"></div>`;
    }).join('');
  }
}

// ── book-of-business snapshot ──────────────────────────────────
let _bookLoaded = false;

let _mtgScope = 'quarter';
let _mtgOffset = 0;

function setMtgScope(scope){
  _mtgScope = scope;
  _mtgOffset = 0;
  document.querySelectorAll('#mtgScope .seg-btn')
    .forEach(b => b.classList.toggle('active', b.dataset.scope === scope));
  // Stepping only means something for a week window.
  ['mtgPrev','mtgNext'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.style.visibility = scope === 'week' ? 'visible' : 'hidden';
  });
  loadBook();
}

function stepMtg(dir){ _mtgOffset += dir; loadBook(); }

async function loadBook(){
  let b;
  try { b = await (await fetch(`/api/book?mtg_scope=${_mtgScope}&mtg_offset=${_mtgOffset}`)).json(); }
  catch(e){ return; }
  if (!b || !b.has_accounts) return;

  const fmt = n => n.toLocaleString('en-US');
  document.getElementById('bobLabel').textContent =
    `${fmt(b.total)} accounts across ${b.territories.length} territories`;
  document.getElementById('bobTotal').textContent = fmt(b.total);
  document.getElementById('bobCovered').textContent = fmt(b.covered);
  document.getElementById('bobSpend').textContent = fmtMapVal(b.spend, 'currency');
  document.getElementById('bobIndustries').textContent = b.industry_count;

  const pct = b.total ? (b.covered / b.total) * 100 : 0;
  document.getElementById('bobCoverage').innerHTML = `
    <div class="meter-track"><div class="meter-fill" style="width:${pct.toFixed(1)}%"></div></div>
    <div class="meter-legend">
      <span><b>${fmt(b.covered)}</b> in a cadence</span>
      <span><b>${pct.toFixed(1)}%</b> of book</span>
    </div>`;

  // Bars are scaled to the biggest slice, so the mix stays readable whatever
  // the absolute counts are.
  const bars = (rows) => {
    const max = Math.max(1, ...rows.map(r => r.value));
    return rows.map(r => `<div class="bar-item">
      <span class="bl" title="${esc(r.label)}">${esc(r.label)}</span>
      <span class="bv">${fmt(r.value)}</span>
      <span class="bar-track"><span class="bar-fill" style="width:${(r.value / max * 100).toFixed(1)}%"></span></span>
    </div>`).join('');
  };
  document.getElementById('bobIndList').innerHTML = bars(b.industries);
  document.getElementById('bobTerrList').innerHTML = bars(b.territories);

  const m = b.meetings;
  if (m){
    document.getElementById('mtgLabel').textContent =
      `${m.label} · ${fmt(m.worked_accounts)} accounts worked`;
    document.getElementById('mtgTotal').textContent = fmt(m.total);
    document.getElementById('mtgBooked').textContent = fmt(m.booked);
    document.getElementById('mtgCompleted').textContent = fmt(m.completed);
    document.getElementById('mtgUpcoming').textContent = fmt(m.upcoming);
    document.getElementById('mtgCancelled').textContent = fmt(m.cancelled);
    document.getElementById('mtgOI').textContent = fmt(m.oi_count);
    document.getElementById('mtgOIValue').textContent = fmtMapVal(m.oi_value, 'currency');
  }
}

// ── territory choropleth ───────────────────────────────────────
// Simplified outlines of the four territories Tim covers. These are hand-traced
// approximations — recognisable silhouettes, not survey-grade boundaries — drawn
// once here rather than pulled from a geo dataset the app doesn't ship. Each
// shape uses fill:currentColor so the choropleth colour is set on the <svg>.
const TERRITORY_SHAPES = {
  CA: {
    name: 'California', viewBox: '0 0 110 190',
    path: 'M12 5 L72 5 L72 50 L98 110 L94 131 L90 149 L88 166 L60 170 L51 164 L43 156 L35 149 L29 144 L23 136 L21 129 L26 121 L24 111 L18 101 L16 85 L14 69 L11 47 L10 25 Z',
    // Approximate positions inside the viewBox, used to place heat blobs.
    cities: {'Sacramento':[46,78],'Oakland':[29,92],'Berkeley':[29,88],'San Jose':[36,100],
             'Santa Clara':[34,98],'Fresno':[52,112],'Riverside':[70,150],'Pasadena':[60,148],
             'Long Beach':[57,155],'Anaheim':[63,152],'Irvine':[66,155],'San Diego':[72,164]}
  },
  HI: {
    name: 'Hawaii', viewBox: '0 0 200 120',
    shapes: [[10,40,6,4,0],[30,31,12,9,0],[66,45,14,9,-18],[98,52,13,5,-8],
             [100,66,7,6,0],[122,63,14,10,-14],[114,78,7,4,0],[163,93,24,20,0]],
    cities: {'Honolulu':[66,47],'Pearl City':[60,45],'Kapolei':[55,48],'Kailua':[73,42],'Hilo':[172,95]}
  },
  GU: {
    name: 'Guam', viewBox: '0 0 100 160',
    path: 'M46 16 L58 21 L62 40 L58 58 L52 70 L55 87 L63 101 L67 121 L58 141 L43 143 L35 126 L40 104 L44 86 L40 70 L38 50 L40 29 Z',
    cities: {'Dededo':[48,40],'Tamuning':[53,72],'Hagåtña':[47,90]}
  },
  MP: {
    name: 'Northern Mariana Islands', viewBox: '0 0 100 160',
    shapes: [[50,38,12,26,0],[47,85,9,16,0],[53,126,12,9,0]],
    cities: {'Saipan':[50,44],'Garapan':[49,28]}
  }
};
// Purple 70 → Purple 10. Low values stay saturated, high values go near-white.
const MAP_STOPS = ['#6929c4','#8a3ffc','#a56eff','#be95ff','#d4bbff','#e8daff','#f6f2ff'];
let _mapView = 'accounts';
let _mapFocus = 'all';     // 'all' or a territory code
let _mapData = null;

function _mix(a, b, t){
  const p = h => [1,3,5].map(i => parseInt(h.slice(i,i+2),16));
  const [r1,g1,b1] = p(a), [r2,g2,b2] = p(b);
  const c = (x,y) => Math.round(x + (y-x)*t).toString(16).padStart(2,'0');
  return `#${c(r1,r2)}${c(g1,g2)}${c(b1,b2)}`;
}

function mapColor(v, max){
  if (!v || !max) return null;
  const t = Math.min(1, Math.sqrt(v / max));
  const seg = t * (MAP_STOPS.length - 1);
  const i = Math.min(MAP_STOPS.length - 2, Math.floor(seg));
  return _mix(MAP_STOPS[i], MAP_STOPS[i+1], seg - i);
}

function fmtMapVal(v, format){
  if (format === 'currency'){
    if (v >= 1e9) return '$' + (v/1e9).toFixed(1) + 'B';
    if (v >= 1e6) return '$' + (v/1e6).toFixed(1) + 'M';
    if (v >= 1e3) return '$' + Math.round(v/1e3) + 'K';
    return '$' + v;
  }
  return String(v);
}

function setMapView(view){
  _mapView = view;
  document.querySelectorAll('#mapViews .seg-btn')
    .forEach(b => b.classList.toggle('active', b.dataset.view === view));
  loadTerritory();
}

function setMapFocus(code){
  _mapFocus = code;
  document.querySelectorAll('#mapFocus .seg-btn')
    .forEach(b => b.classList.toggle('active', b.dataset.focus === code));
  if (_mapData) renderTerritory(_mapData);
}

// The body of one territory: base silhouette plus a soft blob per city, sized
// and coloured by that city's share. Blobs are clipped to the outline, so the
// heat stays inside the territory instead of bleeding into the card.
function territoryBody(code, t, idx){
  const shape = TERRITORY_SHAPES[code];
  const cities = (t.cities || {})[code] || {};
  const counts = Object.values(cities);
  const cityMax = counts.length ? Math.max(...counts) : 0;
  const cityMin = counts.length ? Math.min(...counts) : 0;
  // City counts inside a territory cluster tightly (e.g. 84-109), so a 0-based
  // scale puts every one at the top and the whole shape washes out to one
  // colour. Spread the ramp across the actual observed range instead.
  const span = Math.max(1, cityMax - cityMin);
  const rel = n => (n - cityMin) / span;
  const clipId = `clip-${code}-${idx}`;

  const outline = shape.path
    ? `<path d="${shape.path}"/>`
    : shape.shapes.map(([cx,cy,rx,ry,rot]) =>
        `<ellipse cx="${cx}" cy="${cy}" rx="${rx}" ry="${ry}" transform="rotate(${rot} ${cx} ${cy})"/>`).join('');

  const blobs = Object.entries(shape.cities || {}).map(([city, [x,y]]) => {
    const n = cities[city] || 0;
    if (!n || !cityMax) return '';
    const share = rel(n);
    const r = 15 + share * 22;
    // Colour by position in the range; opacity carries intensity so the darker
    // plate still reads through the cooler spots.
    const col = MAP_STOPS[Math.round(share * (MAP_STOPS.length - 1))];
    const peak = 0.5 + share * 0.42;
    const gid = `g-${code}-${idx}-${city.replace(/[^a-z]/gi,'')}`;
    return `<defs><radialGradient id="${gid}">
        <stop offset="0%" stop-color="${col}" stop-opacity="${peak.toFixed(2)}"/>
        <stop offset="50%" stop-color="${col}" stop-opacity="${(peak*0.42).toFixed(2)}"/>
        <stop offset="100%" stop-color="${col}" stop-opacity="0"/>
      </radialGradient></defs>
      <circle cx="${x}" cy="${y}" r="${r}" fill="url(#${gid})"/>`;
  }).join('');

  return `<svg class="terr-svg" viewBox="${shape.viewBox}" preserveAspectRatio="xMidYMid meet" aria-hidden="true">
      <defs><clipPath id="${clipId}">${outline}</clipPath></defs>
      <g class="terr-base">${outline}</g>
      <g clip-path="url(#${clipId})">${blobs}</g>
      <g class="terr-edge">${outline}</g>
    </svg>`;
}

async function loadTerritory(){
  let t;
  try { t = await (await fetch('/api/territory?view=' + _mapView)).json(); }
  catch(e){ return; }
  if (!t || !t.has_accounts) return;
  _mapData = t;
  renderTerritory(t);
}

function renderTerritory(t){
  document.getElementById('mapLabel').textContent = t.label + ' by territory';
  document.getElementById('mapTotalLbl').textContent = t.label;
  document.getElementById('mapTotal').textContent = fmtMapVal(t.total, t.format);
  document.getElementById('mapStates').textContent = t.states_covered;
  document.getElementById('mapScaleMax').textContent = fmtMapVal(t.max, t.format);

  const entries = Object.entries(t.values).filter(([,v]) => v);
  entries.sort((a,b) => b[1]-a[1]);
  document.getElementById('mapTop').textContent = entries.length ? entries[0][0] : '—';

  const codes = _mapFocus === 'all' ? Object.keys(TERRITORY_SHAPES) : [_mapFocus];
  const host = document.getElementById('usMap');
  host.className = 'usmap' + (_mapFocus === 'all' ? '' : ' single');
  host.innerHTML = codes.map((code, i) => {
    const shape = TERRITORY_SHAPES[code];
    const v = t.values[code] || 0;
    const cityRows = Object.entries((t.cities || {})[code] || {})
      .sort((a,b) => b[1]-a[1]).slice(0, _mapFocus === 'all' ? 0 : 6);
    return `<button class="terr ${v ? 'has' : 'empty'}" onclick="showMapTip('${code}')"
              title="${esc(shape.name)}: ${v ? fmtMapVal(v, t.format) : 'no accounts'}">
      <div class="terr-iso">${territoryBody(code, t, i)}</div>
      <span class="terr-code">${code}</span>
      <span class="terr-name">${esc(shape.name)}</span>
      <span class="terr-val">${fmtMapVal(v, t.format)}</span>
      ${cityRows.length ? `<div class="terr-cities">${cityRows.map(([c,n]) =>
        `<div class="terr-city"><span>${esc(c)}</span><b>${n}</b></div>`).join('')}</div>` : ''}
    </button>`;
  }).join('');

  const tip = document.getElementById('mapTip');
  if (tip) tip.style.display = 'none';
}

function showMapTip(st){
  const t = _mapData; if (!t) return;
  const d = (t.detail || {})[st] || {};
  const tip = document.getElementById('mapTip');
  tip.style.display = '';
  tip.innerHTML = `<b>${esc((TERRITORY_SHAPES[st] || {}).name || st)}</b>
    <div class="mt-row">${d.accounts||0} accounts · ${d.cadences||0} in a Q3 cadence
    · ${fmtMapVal(Math.round(d.spend||0),'currency')} IBM spend this year</div>`;
}

// ── contextual right-hand panel (email + call tabs) ────────────
// Opening it shifts the card grid rather than covering it, and marks the card
// it belongs to, so you can keep scrolling the other cards for context.
let _focusKey = null;

function toggleKebab(ev, id){
  ev.stopPropagation();
  const open = document.getElementById(id);
  document.querySelectorAll('.kebab-menu.show').forEach(m => { if (m !== open) m.classList.remove('show'); });
  if (open) open.classList.toggle('show');
}
document.addEventListener('click', () => {
  document.querySelectorAll('.kebab-menu.show').forEach(m => m.classList.remove('show'));
});

function closeSidePanel(){
  const p = document.getElementById('sidePanel');
  if (p) p.classList.remove('open');
  document.body.classList.remove('side-panel-open');
  _focusKey = null;
  if (typeof _emailItems !== 'undefined' && _emailItems.length) renderEmailGrid();
  if (typeof _callItems !== 'undefined' && _callItems.length) renderCallList();
}

function _kv(k, v){ return v ? `<div class="sp-row"><span class="k">${esc(k)}</span><span class="v">${esc(v)}</span></div>` : ''; }

function sidePanelHTML(kind, item){
  const d = item.acctDetail || {};
  const sc = d.sales_cloud || {}, zi = d.zoominfo || {}, sl = d.salesloft || {}, ai = d.ai || {};
  if (kind === 'person'){
    const c = item.contact || (zi.contacts || []).find(x => x.decision_maker) || (zi.contacts || [])[0];
    if (!c) return '<div class="note">No contact on record for this account.</div>';
    return `<div class="sp-title">${esc(c.first_name)} ${esc(c.last_name)}</div>
      <div class="sp-sub">${esc(c.title || '')}${c.decision_maker ? ' · <span class="dm-badge">Decision maker</span>' : ''}</div>
      <div class="sp-block">
        ${_kv('Email', c.email)}
        ${_kv('Direct phone', c.direct_phone)}
        ${_kv('Account', item.account)}
        ${_kv('Location', c.city || '')}
      </div>`;
  }
  return `<div class="sp-title">${esc(item.account)}</div>
    <div class="sp-sub">${esc(sc.industry || '')}</div>
    <div class="sp-block">
      ${_kv('Relationship', sc.relationship)}
      ${_kv('IBM spend (current)', sc.ibm_spend_current)}
      ${_kv('IBM spend (prior)', sc.ibm_spend_prior)}
      ${_kv('Spend trend', sc.spend_trend)}
      ${_kv('Install base', sc.install_summary)}
      ${_kv('Revenue', zi.revenue)}
      ${_kv('Employees', zi.employees)}
      ${_kv('Cadence', sl.cadence)}
      ${_kv('Rank', sl.rank ? '#' + sl.rank : '')}
    </div>
    ${ai.play ? `<div class="sp-ai"><div class="sp-ai-head">${AI_SPARK} AI analysis</div>
      ${_kv('Urgency', ai.urgency)}${_kv('Best fit', ai.product)}${_kv('Play', ai.play)}${_kv('Angle', ai.angle)}</div>` : ''}`;
}

function openSidePanel(kind, i, source){
  const list = (source === 'call') ? _callItems : _emailItems;
  const item = list[i];
  if (!item) return;
  document.getElementById('sidePanelBody').innerHTML = sidePanelHTML(kind, item);
  document.getElementById('sidePanelTitle').textContent =
    kind === 'person' ? 'Contact' : 'Account';
  document.getElementById('sidePanel').classList.add('open');
  document.body.classList.add('side-panel-open');
  _focusKey = item.account;
  if (source === 'call') renderCallList(); else renderEmailGrid();
  const card = document.getElementById((source === 'call' ? 'callcard-' : 'emailcard-') + i);
  if (card) card.scrollIntoView({behavior: 'smooth', block: 'center'});
}

function openCallPerson(i, email){
  const a = _callItems[i];
  if (!a) return;
  const contacts = ((a.acctDetail || {}).zoominfo || {}).contacts || [];
  const c = contacts.find(x => x.email === email) || contacts[0];
  openSidePanel('person', i, 'call');
  if (c){
    document.getElementById('sidePanelBody').innerHTML = sidePanelHTML('person', {...a, contact: c});
  }
}

function removeFromCadence(i){
  const a = _emailItems[i];
  if (!a) return;
  if (!confirm(`Remove ${a.account} from ${a.cadence}?\n\nThis only affects today's list in this session.`)) return;
  _emailItems.splice(i, 1);
  renderEmailGrid();
  refreshDashboard();
}

// Calls have no completion flag in the schedule data, so "done" is tracked
// client-side per day and persisted — otherwise the progress meter could never
// move. Emails use the real `sent` flag from the Email tab.
function callDoneKey(){ return 'bobbee_calls_done_' + appTodayIso(); }
function callDoneSet(){
  try { return new Set(JSON.parse(localStorage.getItem(callDoneKey()) || '[]')); }
  catch(e){ return new Set(); }
}
function callDoneId(a){ return a.account + '|' + a.step; }
function toggleCallDone(account, step){
  const set = callDoneSet();
  const id = account + '|' + step;
  set.has(id) ? set.delete(id) : set.add(id);
  localStorage.setItem(callDoneKey(), JSON.stringify([...set]));
  renderCallList();
  refreshDashboard();
}

function renderDashboard(d){
  if (!_vizLoaded){ _vizLoaded = true; loadViz(); }
  if (!_bookLoaded){ _bookLoaded = true; loadBook(); }
  document.getElementById('dashTodayLabel').textContent = d.today.date_label;
  document.getElementById('dashTodaySub').textContent =
    `${d.today.emails} emails · ${d.today.calls} calls · ${d.today.accounts} accounts to touch`;

  const items = d.today.items || [];
  const emails = items.filter(a => a.type === 'email');
  const calls  = items.filter(a => a.type === 'call');
  const sentIds = new Set(_emailItems.filter(e => e.sent).map(e => e.account + '|' + e.step));
  const doneCalls = callDoneSet();

  const fill = (id, done, total) => {
    const el = document.getElementById(id);
    if (el) el.style.width = (total ? (done / total) * 100 : 0).toFixed(1) + '%';
  };
  const list = (rows, isDone) => rows.length
    ? rows.map(a => `<div class="task-row ${isDone(a) ? 'done' : ''}">
        <span class="task-tick">${isDone(a) ? '&#10003;' : ''}</span>
        <span class="task-acct">${esc(a.account)}</span>
        <span class="task-step">${esc(a.step)}</span>
      </div>`).join('')
    : '<div class="note" style="padding:16px 0;">Nothing scheduled today.</div>';

  const eDone = emails.filter(a => sentIds.has(a.account + '|' + a.step)).length;
  const cDone = calls.filter(a => doneCalls.has(a.account + '|' + a.step)).length;
  document.getElementById('taskEmailDone').textContent = eDone;
  document.getElementById('taskEmailTotal').textContent = emails.length;
  document.getElementById('taskCallDone').textContent = cDone;
  document.getElementById('taskCallTotal').textContent = calls.length;
  fill('taskEmailFill', eDone, emails.length);
  fill('taskCallFill', cDone, calls.length);
  document.getElementById('taskEmailList').innerHTML =
    list(emails, a => sentIds.has(a.account + '|' + a.step));
  document.getElementById('taskCallList').innerHTML =
    list(calls, a => doneCalls.has(a.account + '|' + a.step));
}

async function refreshDashboard(){ _vizLoaded = false; _bookLoaded = false; refreshGates(); }

// ── app boot ──────────────────────────────────────────────────
let _pollTimer = null;
function startApp(){
  document.getElementById('app').style.display = 'block';
  fetchStatus(); fetchSeller(); fetchLoginStatus(); refreshGates(); fetchStrategizeStatus(); fetchAccountsList(); fetchSchedule();
  if (!_pollTimer) _pollTimer = setInterval(() => {
    fetchStatus(); fetchLoginStatus(); refreshGates(); fetchStrategizeStatus();
  }, 2000);
}

// ── cadences tab ──────────────────────────────────────────────
let _cadData = null;
let _cadOpenName = null; // cadence to auto-expand on load

async function fetchCadences(openName){
  if (openName) _cadOpenName = openName;
  let d;
  try { d = await (await fetch('/api/cadences')).json(); } catch(e){ return; }
  if (!d.has_cadences) return;
  _cadData = d.cadences;
  renderCadences();
}

function renderCadences(){
  const host = document.getElementById('cadencesList');
  if (!host || !_cadData) return;
  const STATUS_LABEL = {not_started: 'Not started', in_progress: 'In progress', completed: 'Completed'};
  // A cadence is finished when nothing in it is still pending or in flight —
  // every account has worked through its last step.
  const isFinished = c => c.accounts.length > 0 &&
        c.accounts.every(a => a.status === 'completed');
  const active = _cadData.filter(c => !isFinished(c));
  const finished = _cadData.filter(isFinished);

  const card = c => {
    const isOpen = c.name === _cadOpenName;
    const notStarted = c.accounts.filter(a => a.status === 'not_started').length;
    const inProg = c.accounts.filter(a => a.status === 'in_progress').length;
    const done = c.accounts.filter(a => a.status === 'completed').length;
    const steps = c.steps.map(s => {
      const dotCls = s.type === 'Email' ? 'email' : s.type === 'Call' ? 'call' : '';
      return `<div class="step-node">
        <div class="step-dot ${dotCls}">${s.step_number}</div>
        <div class="step-label">${esc(s.name)}</div>
        <div class="step-day">Day ${s.day}</div>
      </div>`;
    }).join('');
    const accts = c.accounts.map(a => {
      const nt = a.next_touch ? `${esc(a.next_touch.type)} · ${esc(a.next_touch.step)} on ${esc(a.next_touch.date)}` : 'No upcoming touch';
      return `<div class="cad-acct-row">
        <span class="cad-acct-rank">${a.rank ? '#' + a.rank : ''}</span>
        <span class="cad-acct-name" onclick="openAcctModal('${esc(a.account)}')">${esc(a.account)}</span>
        <span class="cad-acct-ind">${esc(a.industry || '')}</span>
        <span class="cad-acct-next">${nt}</span>
        <span class="cad-acct-status"><span class="status-pill ${a.status}">${STATUS_LABEL[a.status] || a.status}</span></span>
      </div>`;
    }).join('');
    return `<div class="cad-card ${isOpen ? 'open' : ''}" id="cadcard-${esc(c.name)}">
      <div class="cad-header" onclick="toggleCadCard('${esc(c.name)}')">
        <span class="cad-chevron">&#9658;</span>
        <div class="cad-meta">
          <div class="cad-name">${esc(c.name)}</div>
          <div class="cad-desc">${esc(c.description)}</div>
        </div>
        <span class="cad-count">${c.account_count} account${c.account_count === 1 ? '' : 's'}</span>
        <div class="cad-status">
          ${inProg ? `<span class="status-pill in_progress">${inProg} active</span>` : ''}
          ${notStarted ? `<span class="status-pill not_started">${notStarted} pending</span>` : ''}
          ${done ? `<span class="status-pill completed">${done} done</span>` : ''}
        </div>
      </div>
      <div class="cad-body">
        <div class="cad-steps">
          <h4>Sequence — ${c.steps.length} steps</h4>
          <div class="step-timeline">${steps}</div>
        </div>
        <div class="cad-accounts">${accts}</div>
      </div>
    </div>`;
  };

  host.innerHTML = active.map(card).join('')
    + (finished.length ? `<div class="cad-finished">
         <div class="cad-finished-head">
           <h3>Finished cadences</h3>
           <span class="cad-finished-note">${finished.length} cadence${finished.length === 1 ? '' : 's'}
             with no pending actions left</span>
         </div>
         ${finished.map(card).join('')}
       </div>` : '');
  // Scroll to and expand the requested cadence after render.
  if (_cadOpenName){
    const el = document.getElementById('cadcard-' + _cadOpenName);
    if (el) el.scrollIntoView({behavior:'smooth', block:'start'});
    _cadOpenName = null;
  }
}

function toggleCadCard(name){
  const el = document.getElementById('cadcard-' + name);
  if (el) el.classList.toggle('open');
}

// Called from the Accounts tab "View in Cadences" button.
function goToCadence(name){
  showPage('cadences', {open: name});
}

// ── email tab ─────────────────────────────────────────────────
// _emailItems: per-email-today objects enriched with contact info.
// Shape: {account, step, cadence, contact:{first_name,last_name,title,work_email}, draft, sent}
let _emailItems = [];

// One request for many accounts. The per-account endpoint is fine on its own,
// but today's lists need 20-40 of them and the browser only runs six at a time.
async function fetchAccountDetails(names){
  if (!names.length) return {};
  try {
    const r = await fetch('/api/accounts/details?names=' + encodeURIComponent(names.join('\x1f')));
    return (await r.json()).accounts || {};
  } catch(e){ return {}; }
}

function showListLoading(hostId, what){
  const el = document.getElementById(hostId);
  if (el) el.innerHTML = `<div class="list-loading"><span class="spin"></span>Loading today's ${what}…</div>`;
}

async function fetchTodayEmail(){
  showListLoading('emailGrid', 'emails');
  let sched;
  try { sched = await (await fetch('/api/schedule')).json(); } catch(e){ return; }
  if (!sched.has_schedule) return;
  const today = appTodayIso();
  const raw = ((sched.days[today] || {}).items || []).filter(a => a.type === 'email');

  // Enrich each scheduled email with the DM contact for that account. One batch
  // request, not one per account — see /api/accounts/details.
  const contactCache = await fetchAccountDetails([...new Set(raw.map(r => r.account))]);

  _emailItems = raw.map(a => {
    const d = contactCache[a.account] || {};
    const contacts = (d.zoominfo || {}).contacts || [];
    // Prefer the decision-maker; fall back to first contact.
    const contact = contacts.find(c => c.decision_maker) || contacts[0] || null;
    return {...a, contact, acctDetail: d, draft: null, sent: false};
  });

  const lbl = document.getElementById('emailDateLabel');
  const cnt = document.getElementById('emailCountLabel');
  if (lbl) lbl.textContent = `Today's outbound emails — ${appTodayLabel()}.`;
  if (cnt) cnt.textContent = `${_emailItems.length} email${_emailItems.length === 1 ? '' : 's'} scheduled today`;
  renderEmailGrid();
}

function _saveEditIfOpen(i){
  // Flush any in-progress edit back to the item before re-rendering.
  const ta = document.getElementById('emailedit-' + i);
  if (ta) _emailItems[i].draft = ta.value;
}

function toggleEmailEdit(i){
  _saveEditIfOpen(i);
  _emailItems[i].editing = !_emailItems[i].editing;
  renderEmailGrid();
  if (_emailItems[i].editing){
    const ta = document.getElementById('emailedit-' + i);
    if (ta){ ta.focus(); ta.setSelectionRange(ta.value.length, ta.value.length); }
  }
}

function saveEmailEdit(i){
  const ta = document.getElementById('emailedit-' + i);
  if (ta) _emailItems[i].draft = ta.value;
  _emailItems[i].editing = false;
  renderEmailGrid();
}

// "Send all" is only available once at least one email is actually drafted and
// not yet sent — you can't send emails that haven't been written.
function updateSendAllBtn(){
  const btn = document.getElementById('sendAllBtn');
  if (!btn) return;
  btn.disabled = !_emailItems.some(a => a.draft != null && !a.draft.startsWith('…') && !a.sent);
}

function renderEmailGrid(){
  const host = document.getElementById('emailGrid');
  if (!host) return;
  updateSendAllBtn();
  if (!_emailItems.length){
    host.innerHTML = '<div class="aitems-empty" style="grid-column:1/-1;">No emails scheduled for today.</div>';
    return;
  }
  // Update toolbar button: "Redraft all" once every card has a draft.
  const allDrafted = _emailItems.every(a => a.draft != null && !a.draft.startsWith('…'));
  const draftBtn = document.getElementById('generateEmailsBtn');
  // innerHTML, not textContent: the sparkle is an inline SVG and textContent
  // would strip it, so the button silently stopped being marked as an AI action.
  if (draftBtn) draftBtn.innerHTML = AI_SPARK + (allDrafted ? ' Redraft all' : ' Draft all emails');

  host.innerHTML = _emailItems.map((a, i) => {
    const c = a.contact;
    const toLine = c ? `${esc(c.first_name)} ${esc(c.last_name)}` : 'Decision-maker';
    const toSub  = c ? `${esc(c.title)} &middot; ${esc(a.account)}` : esc(a.account);
    const toAddr = c && c.work_email ? esc(c.work_email) : '';
    const hasDraft = a.draft != null && !a.draft.startsWith('…');
    const isDrafting = a.draft && a.draft.startsWith('…');
    const isEditing = !!a.editing;

    const bodySection = isDrafting
      ? `<div class="email-body-text" style="color:var(--text3);font-style:italic;">Drafting…</div>`
      : hasDraft
        ? `<div class="email-body-text ${isEditing ? '' : ''}" id="emailbody-${i}" ${isEditing ? 'style="display:none"' : ''}>${esc(a.draft)}</div>
           <textarea id="emailedit-${i}" class="email-body-edit ${isEditing ? 'active' : ''}" rows="7">${esc(a.draft)}</textarea>`
        : `<div class="email-body-text empty">Draft not yet generated.</div>`;

    const pencilBtn = hasDraft && !a.sent
      ? `<button class="icon-btn" title="${isEditing ? 'Save edits' : 'Edit'}" onclick="${isEditing ? 'saveEmailEdit(' + i + ')' : 'toggleEmailEdit(' + i + ')'}">${isEditing ? '&#10003;' : '&#9998;'}</button>`
      : '';
    const redraftBtn = hasDraft && !a.sent
      ? `<button class="icon-btn" title="Regenerate" onclick="redraftOne(${i})">&#8635;</button>`
      : '';

    return `<div class="email-card ${_focusKey === a.account ? 'focused' : ''}" id="emailcard-${i}">
      <div class="email-card-head">
        <div style="min-width:0;">
          <div class="email-card-to link" onclick="openSidePanel('person', ${i})">${toLine}</div>
          <div class="email-card-sub">${toSub}</div>
          <div class="email-card-cadence">${esc(a.cadence)} &middot; ${esc(a.step)}</div>
        </div>
        <div class="email-card-head-actions">
          ${pencilBtn}${redraftBtn}
          <div class="kebab-wrap">
            <button class="kebab" onclick="toggleKebab(event, 'ek-${i}')" title="More">&#8942;</button>
            <div class="kebab-menu" id="ek-${i}">
              <button onclick="openSidePanel('account', ${i})">View account details</button>
              <button onclick="openSidePanel('person', ${i})">View profile details</button>
              <button class="danger" onclick="removeFromCadence(${i})">Remove from cadence</button>
            </div>
          </div>
        </div>
      </div>
      ${hasDraft && a.subject ? `<div class="email-card-subject"><span>Subject:</span> ${esc(a.subject)}</div>` : ''}
      <div class="email-body-wrap">${bodySection}</div>
      <div class="email-foot">
        ${hasDraft && !a.sent && !isEditing ? `<button class="btn primary" onclick="sendOneEmail(${i})">Send</button>` : ''}
        ${isEditing ? `<button class="btn primary" onclick="saveEmailEdit(${i})">Save</button>` : ''}
        <span class="email-sent ${a.sent ? 'show' : ''}" id="emailsent-${i}">&#10003; Sent</span>
      </div>
    </div>`;
  }).join('');
}

async function _draftOne(i, force){
  const a = _emailItems[i];
  if (!force && a.draft != null) return;
  a.draft = '…drafting…';
  a.editing = false;
  renderEmailGrid();
  try {
    // watsonx.ai drafts the email from every connected source (Sales Cloud,
    // ZoomInfo, Salesloft, news), tailored to the contact + cadence step.
    // Fail-soft to a deterministic template server-side.
    const first = a.contact ? a.contact.first_name : 'there';
    const url = '/api/email_draft?name=' + encodeURIComponent(a.account)
      + '&step=' + encodeURIComponent(a.step || '')
      + '&first=' + encodeURIComponent(first);
    const r = await (await fetch(url)).json();
    a.draft = r.body || 'Could not generate a draft.';
    a.subject = r.subject || '';
    a.draftSource = r.source;
  } catch(e){
    a.draft = 'Error generating draft.';
  }
  renderEmailGrid();
}

async function generateAllEmails(){
  const btn = document.getElementById('generateEmailsBtn');
  if (btn) btn.disabled = true;
  const allDrafted = _emailItems.every(a => a.draft != null && !a.draft.startsWith('…'));
  for (let i = 0; i < _emailItems.length; i++){
    // "Redraft all" forces regeneration of everything (including already-drafted).
    await _draftOne(i, allDrafted);
  }
  if (btn) btn.disabled = false;
}

async function redraftOne(i){
  _saveEditIfOpen(i);
  await _draftOne(i, true);
}

function sendOneEmail(i){
  const a = _emailItems[i];
  if (!a) return;
  _saveEditIfOpen(i);
  a.sent = true;
  a.editing = false;
  renderEmailGrid();
  const sentCount = _emailItems.filter(x => x.sent).length;
  const cnt = document.getElementById('emailCountLabel');
  if (cnt) cnt.textContent = `${_emailItems.length} scheduled today &middot; ${sentCount} sent`;
}

function sendAllEmails(){
  const ready = _emailItems.filter(a => a.draft != null && !a.draft.startsWith('…') && !a.sent);
  if (!ready.length){ alert('Draft all emails first before sending.'); return; }
  for (let i = 0; i < _emailItems.length; i++){
    const a = _emailItems[i];
    if (a.draft == null || a.draft.startsWith('…') || a.sent) continue;
    _saveEditIfOpen(i);
    a.sent = true;
    a.editing = false;
  }
  renderEmailGrid();
  const sentCount = _emailItems.filter(x => x.sent).length;
  const cnt = document.getElementById('emailCountLabel');
  if (cnt) cnt.textContent = `${_emailItems.length} scheduled today &middot; ${sentCount} sent`;
}

// ── call tab ──────────────────────────────────────────────────
// _callItems enriched with contacts + brief after fetch.
let _callItems = [];
let _callBriefs = {};  // account → brief text

async function fetchTodayCall(){
  showListLoading('callList', 'calls');
  let sched;
  try { sched = await (await fetch('/api/schedule')).json(); } catch(e){ return; }
  if (!sched.has_schedule) return;
  const today = appTodayIso();
  const raw = ((sched.days[today] || {}).items || []).filter(a => a.type === 'call');

  // Enrich with contacts — one batch request, not one per account.
  const contactCache = await fetchAccountDetails([...new Set(raw.map(r => r.account))]);

  _callItems = raw.map(a => ({...a, acctDetail: contactCache[a.account] || {}}));

  const lbl = document.getElementById('callDateLabel');
  const cnt = document.getElementById('callCountLabel');
  if (lbl) lbl.textContent = `Today's call list — ${appTodayLabel()}.`;
  if (cnt) cnt.textContent = `${_callItems.length} call${_callItems.length === 1 ? '' : 's'} scheduled today`;
  renderCallList();
}

function renderCallList(){
  const host = document.getElementById('callList');
  if (!host) return;
  if (!_callItems.length){
    host.innerHTML = '<div class="aitems-empty">No calls scheduled for today.</div>';
    return;
  }
  host.innerHTML = _callItems.map((a, i) => {
    const d = a.acctDetail || {};
    const zi = d.zoominfo || {};
    const ai = d.ai || {};
    const brief = _callBriefs[a.account];   // array of bullet strings, a status string, or undefined
    const contacts = (zi.contacts || []);
    const dm = contacts.find(c => c.decision_maker);
    // Show DM first, then others.
    const ordered = dm ? [dm, ...contacts.filter(c => c !== dm)] : contacts;
    const contactsHtml = ordered.map(c => {
      const phoneHref = c.direct_phone ? c.direct_phone.replace(/[^+\\d]/g,'') : '';
      return `<div class="call-person">
        <div class="call-person-name">
          <span class="link" onclick="openCallPerson(${i}, '${esc(c.email || '')}')">${esc(c.first_name)} ${esc(c.last_name)}</span>
          ${c.decision_maker ? '<span class="dm-badge">DM</span>' : ''}
          ${phoneHref ? `<a class="btn call" href="tel:${phoneHref}">&#9742; Call</a>` : ''}
        </div>
        <div class="call-person-title">${esc(c.title)}</div>
        <div class="call-person-info">
          ${c.direct_phone ? `<span class="call-person-phone">${esc(c.direct_phone)}</span>` : ''}
          ${c.work_email ? `<span class="call-person-email">${esc(c.work_email)}</span>` : ''}
        </div>
      </div>`;
    }).join('') || '<div class="note">No contacts on record.</div>';
    const briefHtml = Array.isArray(brief)
      ? `<ul class="brief-bullets">${brief.map(b => `<li>${esc(b)}</li>`).join('')}</ul>`
      : (typeof brief === 'string'
          ? `<p style="color:var(--text3);font-style:italic;">${esc(brief)}</p>`
          : `<p style="color:var(--text3);font-style:italic;">Not yet generated.</p>`);
    const isDone = callDoneSet().has(callDoneId(a));
    return `<div class="call-card ${isDone ? 'done' : ''} ${_focusKey === a.account ? 'focused' : ''}" id="callcard-${i}">
      <div class="call-card-head">
        <span class="call-card-rank">${i + 1}</span>
        <div style="flex:1;min-width:0;">
          <div style="display:flex;align-items:baseline;gap:10px;">
            <span class="call-card-name" onclick="openSidePanel('account', ${i}, 'call')">${esc(a.account)}</span>
            <span class="call-card-step">${esc(a.step)} &middot; ${esc(a.cadence)}</span>
            <button class="call-done-btn ${isDone ? 'on' : ''}"
                    onclick="toggleCallDone('${esc(a.account)}','${esc(a.step)}')">
              ${isDone ? '&#10003; Called' : 'Mark as called'}
            </button>
          </div>
          ${dm ? `<div class="call-card-acct">Primary contact: ${esc(dm.first_name)} ${esc(dm.last_name)}, ${esc(dm.title)}</div>` : ''}
        </div>
      </div>
      <div class="call-card-body">
        <div class="call-contacts">
          <h4>Contacts (${ordered.length})</h4>
          ${contactsHtml}
        </div>
        <div class="call-brief ${brief ? '' : 'loading'}">
          <h4>""" + _SPARKLE + """ Pre-call brief</h4>
          ${briefHtml}
        </div>
      </div>
    </div>`;
  }).join('');
}

async function generateAllBriefs(){
  const btn = document.getElementById('generateBriefsBtn');
  if (btn) btn.disabled = true;
  for (const a of _callItems){
    if (Array.isArray(_callBriefs[a.account])) continue;   // already generated
    _callBriefs[a.account] = 'Generating brief…';           // status string
    renderCallList();
    try {
      // Backend synthesizes every connected source (IBM Sales Cloud, ZoomInfo,
      // Salesloft, recent news) into bullet points via watsonx.ai, fail-soft.
      const r = await (await fetch('/api/call_brief?name=' + encodeURIComponent(a.account))).json();
      _callBriefs[a.account] = (r.bullets && r.bullets.length) ? r.bullets : ['No brief available.'];
    } catch(e){
      _callBriefs[a.account] = ['Error generating brief.'];
    }
    renderCallList();
  }
  if (btn) btn.disabled = false;
}

// ── seller identity ───────────────────────────────────────────
async function fetchSeller(){
  let d = {};
  try { d = await (await fetch('/api/seller')).json(); } catch(e){ return; }
  const el = document.getElementById('gmaSeller');
  const signed = document.getElementById('signedAs');
  const profileBtn = document.getElementById('profileBtn');
  if (d.signed_in && d.seller_name && d.covids){
    el.innerHTML = `Signed in as <b>${esc(d.seller_name)}</b> &middot; ${d.covids} coverage ID${d.covids===1?'':'s'}`;
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
  if (profileBtn){
    // Fixed demo persona: Tim (avatar always "TZ"), independent of whichever
    // IBM email the demo happens to be signed in under.
    profileBtn.textContent = 'TZ';
  }
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
  // Strategy/Contacts/Bobby AI move into the Email/Call tabs in the next pass —
  // not wired to the Plan page's Import Accounts card, so nothing to update yet.
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

// ── profile page & preferences ────────────────────────────────
const _PREF_DEFAULTS = {
  email:   { tone: 'professional', context: '', example: '', behavior: '' },
  call:    { know: '', provide: '' },
  cadence: { steps: 7, days: 14, first: 'email', starts: 3, cap: 8 },
};
let _prefs = JSON.parse(JSON.stringify(_PREF_DEFAULTS));

function showSetting(sec){
  document.querySelectorAll('.set-navlink').forEach(b => b.classList.toggle('active', b.dataset.sec === sec));
  const el = document.getElementById('set-' + sec);
  if (el) el.scrollIntoView({behavior: 'smooth', block: 'start'});
}

// Keep the sidebar in step with what's actually on screen while scrolling.
function initSettingsSpy(){
  if (window._setSpy) return;
  const secs = [...document.querySelectorAll('.set-sec')];
  if (!secs.length) return;
  window._setSpy = new IntersectionObserver(entries => {
    const vis = entries.filter(e => e.isIntersecting)
                       .sort((a,b) => a.boundingClientRect.top - b.boundingClientRect.top)[0];
    if (!vis) return;
    const id = vis.target.id.replace('set-', '');
    document.querySelectorAll('.set-navlink')
      .forEach(b => b.classList.toggle('active', b.dataset.sec === id));
  }, {rootMargin: '-70px 0px -60% 0px'});
  secs.forEach(sec => window._setSpy.observe(sec));
}

function switchProfileTab(tab){
  document.querySelectorAll('.profile-tab').forEach(b => b.classList.toggle('active', b.dataset.ptab === tab));
  document.querySelectorAll('.profile-section').forEach(s => s.classList.toggle('active', s.id === 'ptab-' + tab));
  if (tab === 'settings'){
    // Access panels are inline now, so they need their data on open.
    fetchLoginStatus(); fetchCredStatus(); fetchSeller();
    initSettingsSpy();
  }
}

function loadProfilePage(){
  // Restore prefs from localStorage.
  try { const s = localStorage.getItem('bobbee_prefs'); if (s) _prefs = {...JSON.parse(JSON.stringify(_PREF_DEFAULTS)), ...JSON.parse(s)}; } catch(e){}
  const v = (id, val) => { const el = document.getElementById(id); if (el) el.value = val; };
  v('pref-email-tone',     _prefs.email.tone);
  v('pref-email-context',  _prefs.email.context);
  v('pref-email-example',  _prefs.email.example);
  v('pref-email-behavior', _prefs.email.behavior);
  v('pref-call-know',      _prefs.call.know);
  v('pref-call-provide',   _prefs.call.provide);
  v('pref-cad-steps',      _prefs.cadence.steps);
  v('pref-cad-days',       _prefs.cadence.days);
  v('pref-cad-first',      _prefs.cadence.first);
  v('pref-cad-starts',     _prefs.cadence.starts);
  v('pref-cad-cap',        _prefs.cadence.cap);
  // Restore saved profile fields.
  try {
    const p = JSON.parse(localStorage.getItem('bobbee_profile') || '{}');
    ['name','slack','role','territory','market','segment','portfolio'].forEach(k => {
      const el = document.getElementById('prof-' + k); if (el && p[k]) el.value = p[k];
    });
  } catch(e){}
  // w3 shows the person's local time next to their location. Brookhaven, GA is
  // US Eastern, so render in that zone rather than the viewer's.
  const clock = document.getElementById('w3Clock');
  if (clock){
    const tick = () => {
      clock.textContent = new Date().toLocaleTimeString('en-US',
        {timeZone:'America/New_York', hour:'numeric', minute:'2-digit'});
    };
    tick();
    if (!window._w3ClockTimer) window._w3ClockTimer = setInterval(tick, 30000);
  }
  loadTerritory();
}

function saveProfile(){
  const keys = ['name','slack','role','territory','market','segment','portfolio'];
  const p = {};
  keys.forEach(k => { const el = document.getElementById('prof-' + k); if (el) p[k] = el.value; });
  localStorage.setItem('bobbee_profile', JSON.stringify(p));
  // Refresh initials on the profile avatar.
  const initials = (p.name || '').trim().split(/\\s+/).map(w => w[0]).slice(0,2).join('').toUpperCase();
  const btn = document.getElementById('profileBtn');
  if (btn && initials) btn.textContent = initials;
  _flashSaved('Profile saved.');
}

function savePrefs(){
  const g = id => (document.getElementById(id) || {}).value || '';
  const gi = id => parseInt(g(id)) || 0;
  _prefs = {
    email:   { tone: g('pref-email-tone'), context: g('pref-email-context'), example: g('pref-email-example'), behavior: g('pref-email-behavior') },
    call:    { know: g('pref-call-know'), provide: g('pref-call-provide') },
    cadence: { steps: gi('pref-cad-steps') || 7, days: gi('pref-cad-days') || 14,
               first: g('pref-cad-first') || 'email', starts: gi('pref-cad-starts') || 3, cap: gi('pref-cad-cap') || 8 },
  };
  localStorage.setItem('bobbee_prefs', JSON.stringify(_prefs));
  _flashSaved('Preferences saved.');
}

function resetPref(section){
  if (!confirm('Reset ' + section + ' preferences to defaults?')) return;
  _prefs[section] = JSON.parse(JSON.stringify(_PREF_DEFAULTS[section]));
  localStorage.setItem('bobbee_prefs', JSON.stringify(_prefs));
  loadProfilePage();
  _flashSaved(section.charAt(0).toUpperCase() + section.slice(1) + ' preferences reset to defaults.');
}

function _flashSaved(msg){
  const el = document.createElement('div');
  el.textContent = msg;
  el.style.cssText = 'position:fixed;bottom:28px;right:28px;background:var(--layer3);border:1px solid var(--border-strong);color:#fff;padding:10px 18px;font-size:13px;z-index:400;pointer-events:none;';
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 2200);
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
<title>Accounts — IBM BobBee</title>
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
  .trow .track{ flex:1; height:8px; background:var(--layer2); border-radius:0; overflow:hidden; }
  .trow .fill{ height:100%; border-radius:0; }
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
<title>Account Tiering — IBM BobBee</title>
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
<title>Call Planning — IBM BobBee</title>
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
<title>Outbound Strategy — IBM BobBee</title>
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
<title>Contacts — IBM BobBee</title>
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
<title>Bobby AI — IBM BobBee</title>
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
  badge.style.display = p.written_by === 'watsonx' ? 'inline-flex' : 'none';
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
          <span class="by ${p.written_by==='watsonx'?'':'tmpl'}">${esc(p.written_by)}</span></div>
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
