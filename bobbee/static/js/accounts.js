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
let _acctPage = 0;
const ACCOUNT_PAGE_SIZE = 75;
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

// Display name for a cadence — the underlying key keeps its full name for
// lookups, but "Cadence" is implied and the trailing number is noise.
function cadenceLabel(nm){
  const label = (nm || '').replace(/\s*cadence\s*/i, ' ').replace(/\s+\d+\s*$/, '').replace(/\s+/g, ' ').trim();
  return label.replace(/\b[a-z][a-z']*/g, w => w[0].toUpperCase() + w.slice(1));
}

// Data keys are deliberately lowercase; UI labels should still read like prose.
function displayStepLabel(value){
  return (value || '').replace(/\bemail\b/gi, 'Email').replace(/\bcall\b/gi, 'Call');
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
    + Object.entries(L.cadences).map(([nm, n]) => item('cadence:' + nm, cadenceLabel(nm), n)).join('')
    + '<h4>Set aside</h4>'
    + item('leftovers', 'Leftovers', L.leftovers)
    + item('no_contacts', 'No contacts', L.no_contacts)
    + item('future', 'Future quarters', L.future);
}

function selectList(key){ _acctSel = key; _acctPage = 0; renderSidebar(); renderAccounts(); }
function toggleTag(t){ _tagSel.has(t) ? _tagSel.delete(t) : _tagSel.add(t); _acctPage = 0; renderTagFilters(); renderAccounts(); }
function searchAccounts(){ _acctPage = 0; renderAccounts(); }
function setAccountPage(page){
  _acctPage = Math.max(0, page);
  renderAccounts();
  document.getElementById('acctList')?.scrollIntoView({block:'nearest'});
}

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
  _acctPage = 0;
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

  const pageCount = Math.max(1, Math.ceil(rows.length / ACCOUNT_PAGE_SIZE));
  _acctPage = Math.min(_acctPage, pageCount - 1);
  const pageRows = rows.slice(_acctPage * ACCOUNT_PAGE_SIZE, (_acctPage + 1) * ACCOUNT_PAGE_SIZE);

  // "View in Cadences →" header when browsing a specific cadence list.
  const cadHdr = inCadenceView
    ? `<div style="display:flex;align-items:center;justify-content:space-between;padding:10px 18px;background:var(--layer2);border-bottom:1px solid var(--border);font-size:var(--fs-label);">
        <span style="font-weight:600;">${esc(currentCadence)}</span>
        <button class="link" onclick="goToCadence('${esc(currentCadence)}')">View in Cadences &#8594;</button>
       </div>`
    : '';

  // Carbon data tables are always headed. Which optional columns exist is a
  // property of the *view*, not the row, so decide once — otherwise a row with
  // no cadence drops its cell and knocks the remaining columns out of line.
  const showRank = inCadenceView;
  // Signals only exist after strategize (they come from tiering/analysis). Before
  // that the column would be empty and misleading, so it isn't shown at all.
  const showSignals = !!(_acctData && _acctData.strategized);
  // One template drives both the header and every row (see .acct-row CSS).
  // All fractional so the table always fits its container — no sideways scroll.
  const cols = [
    showRank ? '38px' : null,
    'minmax(0,2.1fr)',           // account
    'minmax(0,1.5fr)',           // industry
    'minmax(0,1.2fr)',           // location
    showSignals ? '104px' : null, // signals
  ].filter(Boolean).join(' ');

  const head = `<div class="acct-row acct-head">
      ${showRank ? '<span class="arank">#</span>' : ''}
      <span class="an">Account</span>
      <span class="ai">Industry</span>
      <span class="aloc">Location</span>
      ${showSignals ? '<span class="atags">Signals</span>' : ''}
    </div>`;

  const pagination = pageCount > 1 ? `<div class="acct-pagination">
      <span>Showing ${_acctPage * ACCOUNT_PAGE_SIZE + 1}&ndash;${Math.min((_acctPage + 1) * ACCOUNT_PAGE_SIZE, rows.length)} of ${rows.length}</span>
      <div>
        <button class="btn" onclick="setAccountPage(${_acctPage - 1})" ${_acctPage === 0 ? 'disabled' : ''}>Previous</button>
        <span>Page ${_acctPage + 1} of ${pageCount}</span>
        <button class="btn" onclick="setAccountPage(${_acctPage + 1})" ${_acctPage === pageCount - 1 ? 'disabled' : ''}>Next</button>
      </div>
    </div>` : '';

  host.innerHTML = `<div class="acct-list" style="--acct-cols:${cols}">` + cadHdr + head + pageRows.map(a => {
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
      ${showSignals ? `<span class="atags" style="display:flex;gap:4px;align-items:center;">${dots}</span>` : ''}
    </div>`;
  }).join('') + '</div>' + pagination;
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
  // While strategize is running, poll fast (600ms) so every stage transition is
  // seen — the 2s app poll would skip the quick final stages.
  if (a && a.active && !a.done){
    if (!window._stratFast) window._stratFast = setInterval(fetchStrategizeStatus, 600);
  } else if (window._stratFast){
    clearInterval(window._stratFast); window._stratFast = null;
  }
  if (a && a.done && !_strategizeWasDone){
    _strategizeWasDone = true;
    fetchAccountsList(); fetchSchedule(); refreshDashboard(); refreshGates();
  }
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
      <div class="panel ai-panel full"><h3><svg class="spark" viewBox="0 0 24 24" fill="currentColor"><path d="M12 1c.7 5.1 2.6 7 7.7 7.7-5.1.7-7 2.6-7.7 7.7-.7-5.1-2.6-7-7.7-7.7C9.4 8 11.3 6.1 12 1z"/></svg>AI analysis</h3>
        ${kv('Urgency', ai.urgency + (ai.score != null ? ` (score ${Number(ai.score).toFixed(1)}, tier ${ai.tier})` : ''))}
        ${kv('Best product fit', ai.product_fit)}
        ${kv('Recommended play', ai.play)}
        ${ai.angle ? `<div style="font-size:var(--fs-label); margin-top:10px; line-height:1.5;">${esc(ai.angle)}</div>` : ''}
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
        ${kv('Cadence', cadenceLabel(sl.cadence))}${kv('Rank in cadence', sl.rank != null ? '#' + sl.rank : null)}
        <div style="margin-top:10px;">
          ${(sl.touches || []).map(t => `<div class="act-row"><span class="act-type ${esc(t.type)}">${esc(displayStepLabel(t.type))}</span><span>${esc(t.date)}</span><span style="color:var(--text3)">${esc(displayStepLabel(t.step))}</span></div>`).join('') || '<div class="note">No touches scheduled.</div>'}
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
