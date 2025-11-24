const API_BASE = 'http://localhost:8000';

const els = {
  loginCard: document.getElementById('loginCard'),
  chatCard: document.getElementById('chatCard'),
  username: document.getElementById('username'),
  password: document.getElementById('password'),
  loginBtn: document.getElementById('loginBtn'),
  loginErr: document.getElementById('loginErr'),
  roleLabel: document.getElementById('roleLabel'),
  category: document.getElementById('category'),
  messages: document.getElementById('messages'),
  prompt: document.getElementById('prompt'),
  sendBtn: document.getElementById('sendBtn'),
  chatErr: document.getElementById('chatErr'),
  ctxBox: document.getElementById('ctxBox'),
  ctxList: document.getElementById('ctxList'),
  toggleCtx: document.getElementById('toggleCtx'),
  logoutBtn: document.getElementById('logoutBtn'),
  flagBtn: document.getElementById('flagBtn'),
  addDialog: document.getElementById('addDialog'),
  addCancel: document.getElementById('addCancel'),
  addSubmit: document.getElementById('addSubmit'),
  addTitle: document.getElementById('addTitle'),
  addDesc: document.getElementById('addDesc'),
  addFolder: document.getElementById('addFolder'),
  addFile: document.getElementById('addFile'),
  addErr: document.getElementById('addErr'),
};

let auth = { token: null, categories: [] };

// ---------------- Auth helpers ----------------
function saveAuth(a) {
  auth = a || { token: null, categories: [] };
  try { localStorage.setItem('rbacAuth', JSON.stringify(auth)); } catch {}
}
function loadAuth() {
  try { return JSON.parse(localStorage.getItem('rbacAuth') || 'null'); } catch { return null; }
}

// ---------------- View toggles ----------------
function showLogin() {
  els.loginCard.classList.remove('hidden');
  els.chatCard.classList.add('hidden');

  els.username.value = '';
  els.password.value = '';
  els.loginErr.textContent = '';
  els.loginBtn.disabled = false;

  setTimeout(() => els.username.focus(), 100);
}

function showChat() {
  els.loginCard.classList.add('hidden');
  els.chatCard.classList.remove('hidden');
}

// ---------------- Generic API helper ----------------
async function api(path, opts = {}) {
  const headers = opts.headers ? { ...opts.headers } : {};
  if (auth.token) headers['Authorization'] = `Bearer ${auth.token}`;

  const res = await fetch(`${API_BASE}${path}`, {
    method: opts.method || 'POST',
    headers,
    body: opts.body || null,
  });

  if (!res.ok) {
    const txt = await res.text().catch(() => '');
    let msg = txt;
    try { msg = (JSON.parse(txt)).detail || txt; } catch {}
    throw new Error(msg || `HTTP ${res.status}`);
  }
  return res.json();
}

// ---------------- Chat UI helpers ----------------
function addMsg(role, content) {
  const el = document.createElement('div');
  el.className = `msg ${role}`;
  el.innerHTML = `<b>${role}</b>: ${escapeHtml(content)}`;
  els.messages.appendChild(el);
  els.messages.scrollTop = els.messages.scrollHeight;
}

function setCtx(items) {
  els.ctxList.innerHTML = items && items.length
    ? items.map(c => {
        const t = (c.text || '').slice(0, 240).replace(/\n/g, ' ');
        return `<div><code>${escapeHtml(c.source || '')}</code>: ${escapeHtml(t)}...</div>`;
      }).join('')
    : '';
  els.ctxBox.classList.toggle('hidden', !els.toggleCtx.checked || !els.ctxList.innerHTML.trim());
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, ch =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch])
  );
}

// ---------------- Category and Flag visibility ----------------
function setCategoryOptions(cats) {
  const all = ["public", "internal", "private"];
  for (const opt of all) {
    const optionEl = [...els.category.options].find(o => o.value === opt);
    if (optionEl) optionEl.disabled = !cats.includes(opt);
  }

  els.category.value = cats[0] || "public";

  // Show flag button only for private
  els.flagBtn.classList.toggle('hidden', !cats.includes('private'));
}

// ---------------- Login flow ----------------
document.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && (e.target === els.username || e.target === els.password)) {
    e.preventDefault();
    els.loginBtn.click();
  }
});

els.loginBtn.addEventListener('click', async () => {
  els.loginErr.textContent = '⏳ Signing in...';
  els.loginBtn.disabled = true;
  try {
    const r = await api('/auth/login', {
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: els.username.value.trim(),
        password: els.password.value
      })
    });

    saveAuth({ token: r.token, categories: r.categories || [] });
    els.roleLabel.textContent = (r.categories || []).join(', ');
    setCategoryOptions(r.categories || []);
    addMsg('assistant', `Welcome! Categories: ${(r.categories || []).join(', ')}`);
    showChat();
  } catch (e) {
    els.loginErr.textContent = e.message || 'Login failed';
    els.loginErr.style.color = 'crimson';
  } finally {
    els.loginBtn.disabled = false;
  }
});

els.logoutBtn.addEventListener('click', () => {
  saveAuth(null);
  els.messages.innerHTML = '';
  els.ctxList.innerHTML = '';
  els.ctxBox.classList.add('hidden');
  showLogin();
});

// ---------------- Chat flow ----------------
async function send() {
  const q = els.prompt.value.trim();
  if (!q) return;
  els.prompt.value = '';
  els.chatErr.textContent = '';
  addMsg('user', q);
  els.sendBtn.disabled = true;

  try {
    const res = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${auth.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        category: els.category.value,
        message: q,
        top_k: 5
      })
    });
    const r = await res.json();
    addMsg('assistant', r.answer || '(no answer)');
    setCtx(r.context || []);
  } catch (e) {
    addMsg('assistant', 'Error: ' + (e.message || 'Request failed'));
  } finally {
    els.sendBtn.disabled = false;
  }
}
els.sendBtn.addEventListener('click', send);
els.prompt.addEventListener('keydown', (ev) => { if (ev.key === 'Enter') send(); });
els.toggleCtx.addEventListener('change', () => setCtx([]));

// ---------------- Flag dialog ----------------
els.flagBtn.addEventListener('click', () => {
  els.addErr.textContent = '';
  els.addDialog.showModal();
});

els.addCancel.addEventListener('click', () => els.addDialog.close());

// ---------------- Document Upload ----------------
els.addSubmit.addEventListener('click', async (e) => {
  e.preventDefault();
  els.addErr.textContent = '⏳ Uploading & processing document...';
  els.addSubmit.disabled = true;

  const title = els.addTitle.value.trim();
  const desc = els.addDesc.value.trim();
  const folder = els.addFolder.value.trim();
  const file = els.addFile.files[0];

  if (!file) {
    els.addErr.textContent = 'Please select a file.';
    els.addSubmit.disabled = false;
    return;
  }

  const formData = new FormData();
  formData.append('title', title);
  formData.append('description', desc);
  formData.append('folder', folder);
  formData.append('file', file);

  try {
    const res = await fetch(`${API_BASE}/documents/flag`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${auth.token}` },
      body: formData,
    });

    if (!res.ok) {
      const msg = await res.text();
      els.addErr.style.color = 'crimson';
      els.addErr.textContent = 'Upload failed: ' + msg;
      els.addSubmit.disabled = false;
      return;
    }

    els.addErr.style.color = 'green';
    els.addErr.textContent = '✅ Document uploaded & indexed successfully.';
    setTimeout(() => els.addDialog.close(), 2000);

  } catch (err) {
    els.addErr.style.color = 'crimson';
    els.addErr.textContent = 'Error: ' + err.message;
  } finally {
    els.addSubmit.disabled = false;
  }
});

// ---------------- Boot ----------------
(function init() {
  const a = loadAuth();
  if (a && a.token) {
    auth = a;
    els.roleLabel.textContent = (a.categories || []).join(', ');
    setCategoryOptions(a.categories || []);
    addMsg('assistant', `Welcome back! Categories: ${(a.categories || []).join(', ')}`);
    showChat();
  } else {
    showLogin();
  }
})();
