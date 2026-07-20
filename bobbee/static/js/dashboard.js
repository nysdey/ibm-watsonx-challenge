// ── dashboard activity chart ───────────────────────────────────
// Bars are stacked emails-over-calls and scaled to the tallest bucket, so the
// shape stays readable whether a period holds 3 activities or 300.
let _vizPeriod = 'week';
let _vizOffset = 0;   // 0 = current window; -1/+1 step back/forward
// Avoid replaying chart transitions when another view refreshes dashboard gates.
// Reset by refreshDashboard() so a fresh strategy does rebuild it.
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
let _todayLoaded = false;

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
    outline: '<path d="M12 5 L72 5 L72 50 L98 110 L94 131 L90 149 L88 166 L60 170 L51 164 L43 156 L35 149 L29 144 L23 136 L21 129 L26 121 L24 111 L18 101 L16 85 L14 69 L11 47 L10 25 Z"/>',
    // Latitude bands, north to south. Real regions in real order — not invented
    // county lines, which would be fabricated geography dressed up as data.
    regions: [
      {name: 'North Coast & Sacramento Valley', band: [0, 88],    cities: ['Sacramento']},
      {name: 'Bay Area',                        band: [88, 106],  cities: ['Oakland','Berkeley','San Jose','Santa Clara']},
      {name: 'Central Valley',                  band: [106, 126], cities: ['Fresno']},
      {name: 'Central Coast',                   band: [126, 143], cities: []},
      {name: 'Los Angeles',                     band: [143, 153], cities: ['Pasadena','Long Beach','Anaheim']},
      {name: 'Inland Empire & Orange County',   band: [153, 161], cities: ['Riverside','Irvine']},
      {name: 'San Diego',                       band: [161, 190], cities: ['San Diego']}
    ]
  },
  HI: {
    name: 'Hawaii', viewBox: '0 0 200 120',
    regions: [
      {name: 'Kauai & Niihau', cities: [],
       svg: '<path d="M5 42l8-4 5 3-4 5-8 1z"/><path d="M22 31l5-9 10-3 8 5-1 8-9 7-9-2z"/>'},
      {name: 'Oahu', cities: ['Honolulu','Pearl City','Kapolei','Kailua'],
       svg: '<path d="M52 44l8-10 13-3 10 5-3 10-12 7-11-2z"/>'},
      {name: 'Maui County', cities: [],
       svg: '<path d="M88 51l15-5 15 3-3 6-22 3z"/><path d="M94 63l7-5 7 5-3 9-8 1z"/>' +
            '<path d="M112 62l9-9 17 1 6 9-8 10-14 3-9-6z"/><path d="M106 78l9-4 8 5-5 6-10 0z"/>'},
      {name: 'Hawaii Island', cities: ['Hilo'],
       svg: '<path d="M148 76l18-7 17 9 10 16-8 17-18 8-18-8-10-17z"/>'}
    ]
  },
  GU: {
    name: 'Guam', viewBox: '0 0 100 160',
    outline: '<path d="M46 16 L58 21 L62 40 L58 58 L52 70 L55 87 L63 101 L67 121 L58 141 L43 143 L35 126 L40 104 L44 86 L40 70 L38 50 L40 29 Z"/>',
    regions: [
      {name: 'Northern Guam', band: [0, 62],    cities: ['Dededo']},
      {name: 'Central Guam',  band: [62, 100],  cities: ['Tamuning','Hagåtña']},
      {name: 'Southern Guam', band: [100, 160], cities: []}
    ]
  },
  MP: {
    name: 'Northern Mariana Islands', viewBox: '0 0 100 160',
    regions: [
      {name: 'Saipan', cities: ['Saipan','Garapan'], svg: '<path d="M46 9l10 8 6 21-5 24-10 11-9-14 2-26z"/>'},
      {name: 'Tinian', cities: [], svg: '<path d="M42 77l11-5 8 9-2 20-12 9-8-11z"/>'},
      {name: 'Rota',   cities: [], svg: '<path d="M39 126l12-9 17 3 6 9-11 10-18 1z"/>'}
    ]
  }
};
// Purple 70 → Purple 10. Discrete steps, like the reference legend.
const MAP_STOPS = ['#4589ff','#5f7fe8','#7b75dc','#966bd0','#a56eff','#be95ff','#d4bbff'];
let _mapView = 'accounts';
let _mapFocus = 'all';
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

// Preserve the geographic silhouette and add isometric depth with an offset.
function territoryBody(code, t, idx){
  const shape = TERRITORY_SHAPES[code];
  const value = (t.values || {})[code] || 0;
  const color = value ? mapColor(value, t.max) : 'var(--map-base)';
  const geometry = shape.outline || shape.regions.map(r => r.svg || '').join('');
  const [vw, vh] = shape.viewBox.split(' ').slice(2).map(Number);
  const tip = `${shape.name} — ${value ? fmtMapVal(value, t.format) : 'no accounts'}`;
  return `<svg class="terr-svg" viewBox="-8 -8 ${vw+24} ${vh+26}" preserveAspectRatio="xMidYMid meet"
              onmousemove="mapTip(event,'${esc(tip)}')" onmouseleave="mapTipHide()">
      <g class="geo-shadow" transform="translate(8 11)">${geometry}</g>
      <g class="geo-extrusion" transform="translate(5 7)">${geometry}</g>
      <g class="geo-face" style="fill:${color}" transform="translate(0 -2)">${geometry}</g>
    </svg>`;
}

// Follows the cursor like the reference map's hover label.
function mapTip(ev, text){
  let el = document.getElementById('mapHover');
  if (!el){
    el = document.createElement('div');
    el.id = 'mapHover';
    el.className = 'map-hover';
    document.body.appendChild(el);
  }
  el.textContent = text;
  el.style.display = 'block';
  el.style.left = (ev.clientX + 14) + 'px';
  el.style.top  = (ev.clientY - 10) + 'px';
}
function mapTipHide(){
  const el = document.getElementById('mapHover');
  if (el) el.style.display = 'none';
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
