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
      ${_kv('Cadence', cadenceLabel(sl.cadence))}
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
  if (!confirm(`Remove ${a.account} from ${a.cadence}?

This only affects today's list in this session.`)) return;
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

// The AI-first hero: greeting + generated brief. Deterministic /api/today.
function greetWord(){
  const h = new Date().getHours();
  return h < 12 ? 'Good morning' : h < 18 ? 'Good afternoon' : 'Good evening';
}

async function loadToday(){
  let t;
  try { t = await (await fetch('/api/today')).json(); } catch(e){ return; }
  if (!t || !t.has_schedule) return;

  const name = (window.__sellerFirst || 'there');
  document.getElementById('tdGreet').textContent = `${greetWord()}, ${name}.`;
  const pace = t.pace || {};
  const paceStr = `on pace for ${pace.done} of ${pace.total} touches this week`;
  document.getElementById('tdMeta').textContent =
    t.looking_ahead ? `${t.date_label} · showing ${t.focus_label}` : `${t.date_label} · ${paceStr}`;
  document.getElementById('briefBody').textContent = t.brief;
}

function startMyDay(){ showPage('email'); }

function openAsk(){ toggleAsk(true); }

function renderDashboard(d){
  if (!_vizLoaded){ _vizLoaded = true; loadViz(); }
  if (!_bookLoaded){ _bookLoaded = true; loadBook(); }
  if (!_todayLoaded){ _todayLoaded = true; loadToday(); }

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
        <span class="task-step">${esc(displayStepLabel(a.step))}</span>
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

async function refreshDashboard(){ _vizLoaded = false; _bookLoaded = false; _todayLoaded = false; refreshGates(); }
