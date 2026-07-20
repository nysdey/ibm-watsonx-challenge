// ── app boot ──────────────────────────────────────────────────
function startApp(){
  initTheme();
  document.getElementById('app').style.display = 'block';
  fetchStatus(); fetchSeller(); fetchLoginStatus(); refreshGates(); fetchStrategizeStatus(); fetchAccountsList(); fetchSchedule();
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
      const type = displayStepLabel(s.type);
      const dotCls = type === 'Email' ? 'email' : type === 'Call' ? 'call' : '';
      return `<div class="step-node">
        <div class="step-dot ${dotCls}">${s.step_number}</div>
        <div class="step-label">${esc(displayStepLabel(s.name))}</div>
        <div class="step-day">Day ${s.day}</div>
      </div>`;
    }).join('');
    const accts = c.accounts.map(a => {
      const nt = a.next_touch ? `${esc(displayStepLabel(a.next_touch.type))} · ${esc(displayStepLabel(a.next_touch.step))} on ${esc(a.next_touch.date)}` : 'No upcoming touch';
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
          <div class="cad-name">${esc(cadenceLabel(c.name))}</div>
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
    const r = await fetch('/api/accounts/details?names=' + encodeURIComponent(names.join('')));
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
          <div class="email-card-cadence">${esc(cadenceLabel(a.cadence))} &middot; ${esc(displayStepLabel(a.step))}</div>
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
      const phoneHref = c.direct_phone ? c.direct_phone.replace(/[^+\d]/g,'') : '';
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
        <div class="call-card-summary">
          <div class="call-card-titleline">
            <span class="call-card-name" onclick="openSidePanel('account', ${i}, 'call')">${esc(a.account)}</span>
          </div>
          <span class="call-card-step">${esc(displayStepLabel(a.step))} &middot; ${esc(cadenceLabel(a.cadence))}</span>
          ${dm ? `<div class="call-card-acct">Primary contact: ${esc(dm.first_name)} ${esc(dm.last_name)}, ${esc(dm.title)}</div>` : ''}
        </div>
        <button class="call-done-btn ${isDone ? 'on' : ''}"
                onclick="toggleCallDone('${esc(a.account)}','${esc(a.step)}')">
          ${isDone ? '&#10003; Called' : 'Mark as called'}
        </button>
      </div>
      <div class="call-card-body">
        <div class="call-contacts">
          <h4>Contacts (${ordered.length})</h4>
          ${contactsHtml}
        </div>
        <div class="call-brief ${brief ? '' : 'loading'}">
          <h4><svg class="spark" viewBox="0 0 24 24" fill="currentColor"><path d="M12 1c.7 5.1 2.6 7 7.7 7.7-5.1.7-7 2.6-7.7 7.7-.7-5.1-2.6-7-7.7-7.7C9.4 8 11.3 6.1 12 1z"/></svg> Pre-call brief</h4>
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
  // Wire the greeting + full-name header control to whoever is signed in.
  const person = (d.seller_name && d.seller_name.trim())
    || (d.email ? d.email.split('@')[0].replace(/[._]/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) : '');
  if (person){
    window.__sellerFirst = person.split(' ')[0];
    if (profileBtn) profileBtn.textContent = person;
  }
}

// ── account import job ─────────────────────────────────────────
// Account import is exposed as one application job.
function actDotClass(a){
  if (!a) return 'pending';
  if (a.error) return 'err';
  if (a.active) return 'running';
  if (a.done) return 'done';
  return 'pending';
}

function updateImport(a, accountCount){
  const key = 'gma';
  const card = document.getElementById('card-' + key);
  if (!card) return;
  card.classList.toggle('working', !!(a && a.active));
  card.classList.toggle('done', !!(a && a.done && !a.active));

  const status = document.getElementById(key + 'Status');
  const dotCls = actDotClass(a);
  const msg = (a && a.message) ? a.message : status.querySelector('.amsg').textContent;
  status.classList.toggle('err', dotCls === 'err');

  status.innerHTML = `<span class="${a && a.active ? 'spinner' : 'dot ' + dotCls}"></span><span class="amsg">${esc(msg)}</span>`;

  const btn = document.getElementById(key + 'Btn');
  btn.disabled = !!(a && a.active);

  const resultsEl = document.getElementById(key + 'Results');
  if (resultsEl) resultsEl.textContent = accountCount ? `${accountCount.toLocaleString()} accounts` : '';
  const chips = document.getElementById('gmaChips');
  if (chips) chips.innerHTML = accountCount
    ? '<span class="pipe-chip"><span class="dot done"></span>Account book ready</span>' : '';
}

function toggleLog(){}

async function fetchStatus(){
  let data;
  try { data = await (await fetch('/api/status')).json(); } catch(e){ return; }
  const acts = data._actions || {};
  const importing = acts.get_my_accounts;
  updateImport(importing, (data.segment || {}).rows || 0);
  if (importing && importing.active && !window._importPoll){
    window._importPoll = setInterval(fetchStatus, 600);
  } else if ((!importing || !importing.active) && window._importPoll){
    clearInterval(window._importPoll);
    window._importPoll = null;
  }
  if (importing && importing.done && !window._importWasDone){
    window._importWasDone = true;
    fetchAccountsList();
    refreshGates();
  }
  if (!importing || !importing.done) window._importWasDone = false;
}

async function runGetMyAccounts(){
  const res = await fetch('/api/get_my_accounts/run', {method:'POST'});
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
      + ' — those steps can\'t run until re-authenticated.';
    alertEl.classList.add('show');
  } else {
    alertEl.classList.remove('show');
  }
  const detailsWarning = document.getElementById('detailsWarn');
  if (detailsWarning) detailsWarning.style.display = needLogin.length ? '' : 'none';
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
    div.className = 'cred-block';
    div.innerHTML =
      `<div class="cred-head"><span class="cred-name">${CRED_LABELS[key]}</span>`
      + `<span class="pill ${isSaved ? 'ready' : ''}"><span class="dot"></span>${isSaved ? 'saved' : 'not saved'}</span></div>`
      + `<div class="cred-form">`
      + `<input type="text" id="cred-email-${key}" placeholder="email / username">`
      + `<input type="password" id="cred-pw-${key}" placeholder="password">`
      + `<button class="btn primary" onclick="saveCredential('${key}')">${isSaved ? 'Update' : 'Save'}</button>`
      + `</div>`;
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
  // Refresh the full name in the header.
  const fullName = (p.name || '').trim();
  const btn = document.getElementById('profileBtn');
  if (btn && fullName) btn.textContent = fullName;
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
  el.style.cssText = 'position:fixed;bottom:28px;right:28px;background:var(--layer3);border:1px solid var(--border-strong);color:#fff;padding:10px 18px;font-size:var(--fs-label);z-index:400;pointer-events:none;';
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 2200);
}

window.__today = window.BOBBEE_CONFIG.today;        // the working day (weekend → next weekday)
window.__realtoday = window.BOBBEE_CONFIG.realToday;
checkAuth();
