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
  const row = a => `<div class="panel-act"><div class="panel-act-body"><div class="pa-acct">${esc(a.account)}</div><div class="pa-step">${esc(displayStepLabel(a.step))} &middot; ${esc(cadenceLabel(a.cadence))}</div></div></div>`;
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
  // Scale each day's load bar against the busiest weekday this month, so a full
  // bar reads as "this is a heavy day" relative to the month.
  const dim = new Date(year, month + 1, 0).getDate();
  let monthMax = 1;
  for (let d = 1; d <= dim; d++){
    const dw = new Date(year, month, d).getDay();
    if (dw === 0 || dw === 6) continue;
    const inf = dayInfo(isoOf(new Date(Date.UTC(year, month, d))));
    if (inf) monthMax = Math.max(monthMax, inf.emails + inf.calls);
  }

  let cells = '<div class="cal-grid">' + ['Mon','Tue','Wed','Thu','Fri'].map(d => `<div class="dow">${d}</div>`).join('');
  const lead = (first.getDay() + 6) % 7;
  for (let i = 0; i < Math.min(lead, 5); i++) cells += '<div class="cal-cell out compact"></div>';
  for (let day = 1; day <= dim; day++){
    const dow = new Date(year, month, day).getDay();
    if (dow === 0 || dow === 6) continue;
    const iso = isoOf(new Date(Date.UTC(year, month, day)));
    const info = dayInfo(iso);
    const n = info ? info.emails + info.calls : 0;
    const isToday = iso === todayIso, isSel = iso === _cal.sel;

    let inner = `<span class="cell-num">${day}</span>`;
    if (info && !compact){
      // Stacked load bar: emails (blue) over calls (purple), width ∝ load.
      const w = Math.max(14, Math.round((n / monthMax) * 100));
      const ep = n ? Math.round(info.emails / n * 100) : 0;
      inner = `<div class="cell-head"><span class="cell-num">${day}</span><span class="cell-count">${n}</span></div>
        <div class="cell-bar" style="width:${w}%">
          <i class="cbar-e" style="width:${ep}%"></i><i class="cbar-c" style="width:${100 - ep}%"></i>
        </div>`;
    } else if (info){
      // Compact (year/quarter thumbnails): a load dot, no bar.
      const lvl = Math.ceil((n / monthMax) * 3) || 1;
      inner = `<span class="cell-num">${day}</span><span class="cell-load l${lvl}"></span>`;
    }
    cells += `<div class="cal-cell ${compact ? 'compact' : ''} ${info ? 'has' : ''} ${isToday ? 'today' : ''} ${isSel ? 'sel' : ''}"
      ${info ? `onclick="selectCalDay('${iso}')"` : ''}>${inner}</div>`;
  }
  cells += '</div>';
  return {label, html: cells};
}

// Jump the calendar back to the working day (respects the weekend look-ahead).
function calToday(){ _cal.anchor = appTodayDate(); renderCal(); }

// Month orientation strip: total load, weekdays with work, and the busiest day.
function renderCalSummary(year, month){
  const summ = document.getElementById('calSummary'), leg = document.getElementById('calLegend');
  if (!summ) return;
  const dim = new Date(year, month + 1, 0).getDate();
  let emails = 0, calls = 0, workdays = 0, busiest = null, busiestN = 0;
  for (let d = 1; d <= dim; d++){
    const dw = new Date(year, month, d).getDay();
    if (dw === 0 || dw === 6) continue;
    const info = dayInfo(isoOf(new Date(Date.UTC(year, month, d))));
    if (!info) continue;
    workdays++; emails += info.emails; calls += info.calls;
    const n = info.emails + info.calls;
    if (n > busiestN){ busiestN = n; busiest = new Date(year, month, d); }
  }
  if (!workdays){
    summ.style.display = 'flex';
    summ.innerHTML = '<span class="cal-sum-empty">No activity scheduled this month.</span>';
    return;
  }
  const busyLabel = busiest ? busiest.toLocaleDateString(undefined, {weekday:'short', month:'short', day:'numeric'}) : '—';
  summ.style.display = 'flex';
  summ.innerHTML = `
    <div class="cal-stat"><span class="v">${emails + calls}</span><span class="l">Touches</span></div>
    <div class="cal-stat"><span class="v">${emails}</span><span class="l">Emails</span></div>
    <div class="cal-stat"><span class="v">${calls}</span><span class="l">Calls</span></div>
    <div class="cal-stat"><span class="v">${workdays}</span><span class="l">Active days</span></div>
    <div class="cal-stat"><span class="v">${esc(busyLabel)}</span><span class="l">Busiest · ${busiestN}</span></div>`;
  if (leg) leg.style.display = 'flex';
}

function renderCal(){
  const grid = document.getElementById('calGrid');
  const label = document.getElementById('calLabel');
  if (!grid) return;
  if (!_cal.data){ grid.innerHTML = ''; return; }
  const a = _cal.anchor;

  // Summary + legend belong to the month view only.
  const summEl = document.getElementById('calSummary'), legEl = document.getElementById('calLegend');
  if (summEl) summEl.style.display = 'none';
  if (legEl) legEl.style.display = 'none';
  // Highlight the active range button.
  document.querySelectorAll('#page-plan .range-btn')
    .forEach(b => b.classList.toggle('active', b.dataset.view === _cal.view));

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
    renderCalSummary(a.getFullYear(), a.getMonth());
  } else if (_cal.view === 'week'){
    const mon = new Date(a); mon.setDate(a.getDate() - ((a.getDay() + 6) % 7));
    const fri = new Date(mon); fri.setDate(mon.getDate() + 4);
    label.textContent = `${mon.toLocaleDateString(undefined, {month: 'short', day: 'numeric'})} – ${fri.toLocaleDateString(undefined, {month: 'short', day: 'numeric'})}`;
    // Scale the load bars against the busiest day this week, same as the month view.
    let wkMax = 1;
    for (let i = 0; i < 5; i++){ const d = new Date(mon); d.setDate(mon.getDate() + i);
      const inf = dayInfo(isoOf(new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()))));
      if (inf) wkMax = Math.max(wkMax, inf.emails + inf.calls); }
    const todayIso = appTodayIso();
    grid.innerHTML = '<div class="cal-week">' + [0, 1, 2, 3, 4].map(i => {
      const d = new Date(mon); d.setDate(mon.getDate() + i);
      const iso = isoOf(new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate())));
      const info = dayInfo(iso);
      const n = info ? info.emails + info.calls : 0;
      const w = n ? Math.max(14, Math.round((n / wkMax) * 100)) : 0;
      const ep = n ? Math.round(info.emails / n * 100) : 0;
      const accts = info ? info.accounts.slice(0, 5).map(nm =>
        `<div class="wd-acct">${esc(nm)}</div>`).join('') +
        (info.accounts.length > 5 ? `<div class="wd-more">+${info.accounts.length - 5} more</div>` : '') : '';
      return `<div class="cal-weekday ${info ? 'has' : 'empty'} ${iso === todayIso ? 'today' : ''} ${iso === _cal.sel ? 'sel' : ''}"
                ${info ? `onclick="selectCalDay('${iso}')"` : ''}>
        <div class="wd-head">
          <span class="wd-date">${d.toLocaleDateString(undefined, {weekday: 'short'})} ${d.getDate()}</span>
          ${n ? `<span class="wd-count">${n}</span>` : ''}
        </div>
        <div class="cell-bar" style="width:${w}%;${n ? '' : 'visibility:hidden'}">
          <i class="cbar-e" style="width:${ep}%"></i><i class="cbar-c" style="width:${100 - ep}%"></i>
        </div>
        <div class="wd-accts">${accts || '<div class="wd-free">No activity</div>'}</div>
      </div>`;
    }).join('') + '</div>';
  } else {
    // Day view: an inline "zoomed-in day" board (the popout's content, in-page),
    // and NO popout — close it if one was open from another view.
    const iso = isoOf(new Date(Date.UTC(a.getFullYear(), a.getMonth(), a.getDate())));
    label.textContent = a.toLocaleDateString(undefined, {weekday: 'long', month: 'long', day: 'numeric'});
    document.getElementById('dayPanel').classList.remove('open');
    document.body.classList.remove('day-panel-open');
    _cal.sel = iso;
    grid.innerHTML = dayBoardHTML(iso);
  }
}

// The day's plan as an inline board: summary + Emails / Calls columns, matching
// the dashboard's email-left / call-right language. Shared shape with the popout.
function dayBoardHTML(iso){
  const info = dayInfo(iso) || {emails: 0, calls: 0, accounts: [], items: []};
  const items = info.items || [];
  const emails = items.filter(a => a.type === 'email');
  const calls  = items.filter(a => a.type === 'call');
  const rows = arr => arr.length
    ? arr.map(a => `<div class="dv-row"><span class="dv-acct">${esc(a.account)}</span>
        <span class="dv-step">${esc(displayStepLabel(a.step))} &middot; ${esc(cadenceLabel(a.cadence))}</span></div>`).join('')
    : '<div class="dv-empty">None scheduled.</div>';
  const col = (label, kind, arr) => `<div class="dv-col ${kind}">
      <div class="dv-colhead">${label}<span class="dv-n">${arr.length}</span></div>
      <div class="dv-list">${rows(arr)}</div>
    </div>`;
  return `<div class="cal-dayboard">
    <div class="dv-sums"><b>${info.emails}</b> emails &middot; <b>${info.calls}</b> calls &middot;
      <b>${info.accounts.length}</b> accounts to touch</div>
    <div class="dv-cols">${col('Emails', 'email', emails)}${col('Calls', 'call', calls)}</div>
  </div>`;
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
