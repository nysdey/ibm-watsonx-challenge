// ── Ask BobBee (watsonx Assistant) ─────────────────────────────
// Product Q&A only — the server never sends account data to the service.
// Replies are tagged when they came from the local fallback set instead of the
// live assistant, so a canned answer is never passed off as the real thing.
const ASK_CLIENT_ID = 'c' + Math.random().toString(36).slice(2, 10);
let _askReady = false;

function toggleAsk(force){
  const p = document.getElementById('askPanel');
  const open = force === undefined ? !p.classList.contains('open') : force;
  p.classList.toggle('open', open);
  document.body.classList.toggle('ask-panel-open', open);
  if (open){
    if (!_askReady){ _askReady = true; askInit(); }
    document.getElementById('askInput').focus();
  }
}

async function askInit(){
  let st = {configured: false};
  try { st = await (await fetch('/api/assistant/status')).json(); } catch(e){}
  document.getElementById('askNote').textContent = st.configured
    ? 'Answers questions about BobBee. Your account data is never sent.'
    : 'watsonx Assistant is not configured — answering from a small built-in set.';
  askPush('bot', 'Ask me how cadences are built, what a tag means, or where a number comes from.', true);
}

function askPush(who, text, quiet){
  const log = document.getElementById('askLog');
  const el = document.createElement('div');
  el.className = 'ask-msg ' + (who === 'me' ? 'me' : 'bot');
  el.textContent = text;
  if (who === 'bot' && quiet === false){
    const tag = document.createElement('span');
    tag.className = 'ask-tag';
    tag.textContent = 'Offline answer — watsonx Assistant unreachable';
    el.classList.add('offline');
    el.appendChild(tag);
  }
  log.appendChild(el);
  log.scrollTop = log.scrollHeight;
  return el;
}

async function askSend(ev){
  ev.preventDefault();
  const input = document.getElementById('askInput');
  const text = input.value.trim();
  if (!text) return;
  input.value = '';
  askPush('me', text, true);
  const pending = askPush('bot', 'Thinking…', true);
  let r = {reply: '', live: false};
  try {
    r = await (await fetch('/api/assistant/message', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({text, client_id: ASK_CLIENT_ID})
    })).json();
  } catch(e){ r = {reply: 'Something went wrong sending that.', live: false}; }
  pending.remove();
  askPush('bot', r.reply || 'No answer came back.', r.live);
}

// ── theme ──────────────────────────────────────────────────────
function setTheme(name){
  const t = name === 'light' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', t);
  try { localStorage.setItem('bobbee_theme', t); } catch(e){}
  document.querySelectorAll('#themeToggle .seg-btn')
    .forEach(b => b.classList.toggle('active', b.dataset.themeOpt === t));
}

function initTheme(){
  let t = 'dark';
  try { t = localStorage.getItem('bobbee_theme') || 'dark'; } catch(e){}
  setTheme(t);
}
