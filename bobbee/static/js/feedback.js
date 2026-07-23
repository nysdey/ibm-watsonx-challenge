// ── Rate Email modal (Email tab) ────────────────────────────────
// Submits seller star ratings for one sent email. Feeds directly into the
// Training Data tab and, once an email clears the quality bar, into future
// watsonx email drafts as a live few-shot example — see docs on
// bobbee/domain/feedback.py and EmailService.top_examples_for_prompt.
const RATE_DIMENSIONS = [
  ['relevance', 'Relevance to Prospect'],
  ['personalization', 'Personalization Quality'],
  ['clarity', 'Clarity & Conciseness'],
  ['cta_strength', 'Call-to-Action Strength'],
  ['tone', 'Professional Tone'],
];

let _rateIndex = null;
let _rateValues = {};

function openRateModal(i){
  const a = _emailItems[i];
  if (!a || !a.emailId) return;
  _rateIndex = i;
  _rateValues = {};
  const subjEl = document.getElementById('rateModalSubject');
  if (subjEl) subjEl.textContent = a.subject || '(no subject)';
  const notesEl = document.getElementById('rateModalNotes');
  if (notesEl) notesEl.value = '';
  renderRateStars();
  document.getElementById('rateModal').classList.add('show');
}

function closeRateModal(){
  document.getElementById('rateModal').classList.remove('show');
  _rateIndex = null;
}

function setRating(key, value){
  _rateValues[key] = value;
  renderRateStars();
}

function renderRateStars(){
  const host = document.getElementById('rateModalRows');
  if (!host) return;
  host.innerHTML = RATE_DIMENSIONS.map(([key, label]) => {
    const val = _rateValues[key] || 0;
    const stars = [1, 2, 3, 4, 5].map(n =>
      `<button type="button" class="star-btn ${n <= val ? 'on' : ''}" onclick="setRating('${key}', ${n})" title="${n} star${n > 1 ? 's' : ''}">${n <= val ? STAR_ICON_FILLED : STAR_ICON}</button>`
    ).join('');
    return `<div class="rate-row"><span class="rate-label">${esc(label)}</span><span class="rate-stars">${stars}</span></div>`;
  }).join('');
}

async function submitRating(){
  const a = _emailItems[_rateIndex];
  if (!a || !a.emailId) return;
  const ratings = {};
  Object.keys(_rateValues).forEach(k => { if (_rateValues[k] > 0) ratings[k] = _rateValues[k]; });
  if (!Object.keys(ratings).length){ alert('Rate at least one category before submitting.'); return; }
  const btn = document.getElementById('rateSubmitBtn');
  if (btn){ btn.disabled = true; btn.textContent = 'Submitting…'; }
  try {
    const r = await fetch('/api/email_feedback', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        email_id: a.emailId, ratings,
        notes: (document.getElementById('rateModalNotes') || {}).value || '',
      }),
    });
    const d = await r.json();
    if (d.ok){
      a.feedback = d.email;
      closeRateModal();
      renderEmailGrid();
    } else {
      alert(d.error || 'Could not submit feedback.');
    }
  } catch(e){
    alert('Could not submit feedback — check your connection and try again.');
  }
  if (btn){ btn.disabled = false; btn.innerHTML = '<svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16"><path d="M2 12l19-9-4 19-6-6-5 4z"/></svg> Submit for Retraining'; }
}

// ── Training Data tab ────────────────────────────────────────────
let _trainingRows = [];

async function fetchTrainingData(q){
  const host = document.getElementById('trainingGrid');
  if (host) host.innerHTML = '<div class="list-loading"><span class="spin"></span>Loading training data…</div>';
  let d;
  try {
    d = await (await fetch('/api/training_data' + (q ? '?q=' + encodeURIComponent(q) : ''))).json();
  } catch(e){
    if (host) host.innerHTML = '<div class="aitems-empty">Could not load training data.</div>';
    return;
  }
  _trainingRows = d.examples || [];
  const countEl = document.getElementById('trainingCount');
  if (countEl) countEl.textContent = `${d.count} example${d.count === 1 ? '' : 's'} qualified for retrieval`;
  renderTrainingGrid();
}

function searchTrainingData(value){
  fetchTrainingData(value);
}

function _engagementLine(engagement){
  if (!engagement) return '';
  const parts = [];
  parts.push(engagement.opened ? `Opened${engagement.open_count > 1 ? ' &times;' + engagement.open_count : ''}` : 'Not yet opened');
  if (engagement.clicked) parts.push('Clicked');
  if (engagement.replied) parts.push('Replied');
  return parts.join(' &middot; ');
}

function renderTrainingGrid(){
  const host = document.getElementById('trainingGrid');
  if (!host) return;
  if (!_trainingRows.length){
    host.innerHTML = `<div class="aitems-empty" style="grid-column:1/-1;">
      No training examples yet. Rate a sent email highly — once it's rated well and
      picks up real engagement, it will show up here and start shaping future drafts.
    </div>`;
    return;
  }
  host.innerHTML = _trainingRows.map(row => {
    const isTop = row.badges.includes('Top Example');
    const badgeChips = row.badges.map(b => {
      const cls = b === 'Top Example' ? 'top' : b === 'High Priority' ? 'priority' : 'good';
      const icon = b === 'Top Example' ? '&#127942; ' : b === 'High Priority' ? '&#128293; ' : '&#10003; ';
      return `<span class="td-badge ${cls}">${icon}${esc(b)}</span>`;
    }).join('');
    const styleChips = (row.style_tags || []).map(t => `<span class="td-tag">${esc(t)}</span>`).join('');
    return `<div class="td-card ${isTop ? 'top' : ''}">
      <div class="td-badges">${badgeChips}</div>
      <div class="td-prompt"><span>Prompt:</span> ${esc(row.prompt)}</div>
      <div class="td-subject"><span>Subject:</span> ${esc(row.subject)}</div>
      <div class="td-body">${esc(row.body)}</div>
      ${styleChips ? `<div class="td-tags">${styleChips}</div>` : ''}
      <div class="td-foot">
        <span class="td-score">Score ${row.score}/100</span>
        <span class="td-engagement">${_engagementLine(row.engagement)}</span>
      </div>
      ${row.notes ? `<div class="td-notes">&ldquo;${esc(row.notes)}&rdquo;</div>` : ''}
      ${isTop ? `<div class="td-rag-note">&#9733; This example is prioritized for RAG retrieval and future drafts</div>` : ''}
    </div>`;
  }).join('');
}
