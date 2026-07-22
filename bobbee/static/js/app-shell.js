// The one marker for "watsonx generated this" — kept in JS too so buttons that
// rebuild their own label can restore it instead of dropping it.
const AI_SPARK = '<svg class="spark" viewBox="0 0 24 24" fill="currentColor"><path d="M12 1c.7 5.1 2.6 7 7.7 7.7-5.1.7-7 2.6-7.7 7.7-.7-5.1-2.6-7-7.7-7.7C9.4 8 11.3 6.1 12 1z"/></svg>';

function esc(s){ return String(s==null?'':s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }

// ── auth gate ─────────────────────────────────────────────────
async function checkAuth(){
  // A page refresh should NOT sign you out — if an identity is still stored,
  // go straight into the app. (Use the explicit Sign out button to reset.)
  let saved = {};
  try { saved = await (await fetch('/api/credentials/status')).json(); } catch(e){}
  if (saved.w3id) startApp();
  else document.getElementById('loginGate').style.display = 'flex';
}

async function logout(){
  try { await fetch('/api/logout', {method:'POST'}); } catch(e){}
  // Reload straight to the gate — clean slate for the next demo run.
  location.reload();
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
    // Fresh sign-in = fresh book: wipe any prior demo data so every session
    // walks the full import → strategize flow.
    try { await fetch('/api/demo/reset', {method:'POST'}); } catch(e){}
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
  toggleAsk(false);
  document.querySelectorAll('.page').forEach(p => p.classList.toggle('active', p.id === 'page-' + name));
  document.querySelectorAll('.navlink').forEach(b => b.classList.toggle('active', b.dataset.page === name));
  const profileBtn = document.getElementById('profileBtn');
  if (profileBtn){
    const profileActive = name === 'profile';
    profileBtn.classList.toggle('active', profileActive);
    profileBtn.closest('.profile-wrap')?.classList.toggle('active', profileActive);
    profileBtn.setAttribute('aria-current', profileActive ? 'page' : 'false');
  }
  if (name === 'accounts'){ fetchAccountsList(); fetchStrategizeStatus(); }
  if (name === 'dashboard'){ refreshDashboard(); }
  if (name === 'plan'){ fetchSchedule(); }
  if (name === 'cadences'){ fetchCadences(opts && opts.open); }
  if (name === 'email'){ fetchTodayEmail(); }
  if (name === 'call'){ fetchTodayCall(); }
  if (name === 'profile'){ switchProfileTab('profile'); loadProfilePage(); }
}
