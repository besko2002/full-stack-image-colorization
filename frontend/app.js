const API_BASE = '';
let currentRating = 0;
let session = JSON.parse(localStorage.getItem('session')) || null;
let preferences = JSON.parse(localStorage.getItem('preferences')) || { dark_mode: false, notifications: true };
let historyItems = [];
let activityItems = [];

window.onload = async function () {
  document.addEventListener('click', closeUserMenu);
  applySettings();

  if (session?.token) {
    goTo('app');
    await bootstrapApp();
  } else {
    goTo('login');
  }
};

function authHeaders(json = true) {
  const headers = {};
  if (session?.token) headers['Authorization'] = `Bearer ${session.token}`;
  if (json) headers['Content-Type'] = 'application/json';
  return headers;
}

function showLoading(show) {
  const loader = document.getElementById('pageLoader');
  loader.classList.toggle('show', !!show);
}

function showToast(message, type = '') {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`.trim();
  toast.innerText = message;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 2500);
}

function setError(id, message) {
  const el = document.getElementById(id);
  if (el) el.innerText = message || '';
}

function goTo(id) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.getElementById(id).classList.add('active');
}

function show(id, btn) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  document.querySelectorAll('.nav-link').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
}

function showAdminTab(id, btn) {
  document.querySelectorAll('.admin-page').forEach(p => p.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  document.querySelectorAll('.admin-tab').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
}

function toggleUserMenu(e) {
  e.stopPropagation();
  document.getElementById('userMenu').classList.toggle('show');
}

function closeUserMenu() {
  document.getElementById('userMenu')?.classList.remove('show');
}

function persistSession(payload) {
  session = {
    token: payload.access_token,
    user: payload.user,
  };
  preferences = payload.preferences || preferences;
  localStorage.setItem('session', JSON.stringify(session));
  localStorage.setItem('preferences', JSON.stringify(preferences));
}

async function bootstrapApp() {
  await loadProfile();
  await loadHistory();
  await loadFeedback();
  if (session?.user?.role === 'admin') {
    document.getElementById('adminNavBtn').classList.remove('hidden');
    document.getElementById('admin').classList.remove('hidden');
    await loadAdminData();
  }
}

async function apiRequest(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, options);
  const contentType = res.headers.get('content-type') || '';
  const data = contentType.includes('application/json') ? await res.json() : await res.text();
  if (!res.ok) {
    throw new Error(data.error || data.detail || data.message || 'Request failed');
  }
  return data;
}

async function login() {
  setError('loginError', '');
  try {
    showLoading(true);
    const email = document.getElementById('loginEmail').value.trim();
    const password = document.getElementById('loginPassword').value;
    const data = await apiRequest('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    persistSession(data);
    applyProfile(data.user);
    goTo('app');
    await bootstrapApp();
    showToast('Welcome back!', 'success');
  } catch (err) {
    setError('loginError', err.message);
  } finally {
    showLoading(false);
  }
}

async function signUp() {
  setError('signupError', '');
  try {
    showLoading(true);
    const name = document.getElementById('signupName').value.trim();
    const email = document.getElementById('signupEmail').value.trim();
    const password = document.getElementById('signupPassword').value;
    const data = await apiRequest('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, password })
    });
    persistSession(data);
    applyProfile(data.user);
    goTo('app');
    await bootstrapApp();
    showToast('Account created successfully', 'success');
  } catch (err) {
    setError('signupError', err.message);
  } finally {
    showLoading(false);
  }
}

async function sendReset() {
  setError('forgetError', '');
  try {
    showLoading(true);
    const email = document.getElementById('forgetEmail').value.trim();
    const data = await apiRequest('/api/auth/forgot-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email })
    });
    if (data.reset_token) {
      document.getElementById('resetToken').value = data.reset_token;
    }
    showToast(data.message, 'success');
  } catch (err) {
    setError('forgetError', err.message);
  } finally {
    showLoading(false);
  }
}

async function completeReset() {
  try {
    showLoading(true);
    const token = document.getElementById('resetToken').value.trim();
    const password = document.getElementById('newResetPassword').value;
    const data = await apiRequest('/api/auth/reset-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token, password })
    });
    showToast(data.message, 'success');
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    showLoading(false);
  }
}

async function loadProfile() {
  const data = await apiRequest('/api/users/me', { headers: authHeaders() });
  session.user = data.user;
  preferences = data.preferences;
  localStorage.setItem('session', JSON.stringify(session));
  localStorage.setItem('preferences', JSON.stringify(preferences));
  applyProfile(data.user);
  applySettings();
}

function applyProfile(user) {
  if (!user) return;
  const first = (user.name || 'U').charAt(0).toUpperCase();
  document.getElementById('userName').innerText = user.name;
  document.getElementById('userEmail').innerText = user.email;
  document.getElementById('userAvatar').innerText = first;
  document.getElementById('profileAvatar').innerText = first;
  document.getElementById('profileName').innerText = user.name;
  document.getElementById('profileEmail').innerText = user.email;
  document.getElementById('profileNameInput').value = user.name;
  document.getElementById('profileEmailInput').value = user.email;
}

function applySettings() {
  document.body.classList.toggle('dark', !!preferences.dark_mode);
  const darkToggle = document.getElementById('darkModeToggle');
  const notifToggle = document.getElementById('notificationsToggle');
  if (darkToggle) darkToggle.checked = !!preferences.dark_mode;
  if (notifToggle) notifToggle.checked = !!preferences.notifications;
}

async function saveProfile() {
  try {
    showLoading(true);
    const name = document.getElementById('profileNameInput').value.trim();
    const email = document.getElementById('profileEmailInput').value.trim();
    const data = await apiRequest('/api/users/me', {
      method: 'PUT',
      headers: authHeaders(),
      body: JSON.stringify({ name, email })
    });
    session.user = data.user;
    localStorage.setItem('session', JSON.stringify(session));
    applyProfile(data.user);
    showToast('Profile updated', 'success');
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    showLoading(false);
  }
}

async function toggleSetting(key, value) {
  try {
    const payload = { [key]: value };
    const data = await apiRequest('/api/users/preferences', {
      method: 'PUT',
      headers: authHeaders(),
      body: JSON.stringify(payload)
    });
    preferences = data.preferences;
    localStorage.setItem('preferences', JSON.stringify(preferences));
    applySettings();
    showToast('Preference updated', 'success');
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function changePassword() {
  try {
    showLoading(true);
    const current_password = document.getElementById('currentPassword').value;
    const new_password = document.getElementById('newPassword').value;
    const data = await apiRequest('/api/users/change-password', {
      method: 'PUT',
      headers: authHeaders(),
      body: JSON.stringify({ current_password, new_password })
    });
    document.getElementById('currentPassword').value = '';
    document.getElementById('newPassword').value = '';
    showToast(data.message, 'success');
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    showLoading(false);
  }
}

function showLocalPreview(event) {
  const file = event.target.files?.[0];
  if (!file) return;
  const url = URL.createObjectURL(file);
  const originalPreview = document.getElementById('originalPreview');
  originalPreview.src = url;
  originalPreview.style.display = 'block';
  document.getElementById('originalPlaceholder').style.display = 'none';
}

async function upload() {
  const fileInput = document.getElementById('file');
  if (!fileInput.files.length) {
    showToast('Choose an image first', 'error');
    return;
  }

  try {
    showLoading(true);
    const formData = new FormData();
    formData.append('image', fileInput.files[0]);

    const res = await fetch('/api/images/upload', {
      method: 'POST',
      headers: { Authorization: `Bearer ${session.token}` },
      body: formData
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Upload failed');

    const item = data.image;
    const preview = document.getElementById('preview');
    preview.src = item.output_image_url;
    preview.style.display = 'block';
    document.getElementById('placeholder').style.display = 'none';

    const originalPreview = document.getElementById('originalPreview');
    originalPreview.src = item.original_image_url;
    originalPreview.style.display = 'block';
    document.getElementById('originalPlaceholder').style.display = 'none';

    showToast('Image colorized successfully', 'success');
    fileInput.value = '';
    await loadHistory();
    if (session.user.role === 'admin') await loadAdminData();
    show('home', document.querySelectorAll('.nav-link')[0]);
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    showLoading(false);
  }
}

async function loadHistory() {
  const data = await apiRequest('/api/images/my-history', { headers: authHeaders(false) });
  historyItems = data.images || [];
  renderHistory();
  renderStats();
  renderActivity();
}

function renderHistory() {
  const empty = document.getElementById('empty');
  const cards = document.getElementById('historyCards');
  cards.innerHTML = '';

  if (!historyItems.length) {
    empty.style.display = 'block';
    return;
  }

  empty.style.display = 'none';
  historyItems.forEach(item => {
    const card = document.createElement('div');
    card.className = 'history-card';
    card.innerHTML = `
      <img src="${item.output_image_url || item.original_image_url}" alt="result">
      <div class="content">
        <div class="strong">${item.original_filename}</div>
        <div class="subtle">Status: ${item.status}</div>
        <div class="subtle">Processing: ${item.processing_time || 0}s</div>
        <div class="subtle">Uploaded: ${new Date(item.created_at).toLocaleString()}</div>
      </div>
    `;
    cards.appendChild(card);
  });
}

function renderStats() {
  document.getElementById('total').innerText = historyItems.length;
  const now = new Date();
  const weekCount = historyItems.filter(item => (now - new Date(item.created_at)) / (1000 * 60 * 60 * 24) <= 7).length;
  document.getElementById('week').innerText = weekCount;

  if (historyItems[0]) {
    const latest = historyItems[0];
    const preview = document.getElementById('preview');
    preview.src = latest.output_image_url;
    preview.style.display = 'block';
    document.getElementById('placeholder').style.display = 'none';
    const originalPreview = document.getElementById('originalPreview');
    originalPreview.src = latest.original_image_url;
    originalPreview.style.display = 'block';
    document.getElementById('originalPlaceholder').style.display = 'none';
  }
}

function renderActivity() {
  const list = document.getElementById('activityList');
  const empty = document.getElementById('activityEmpty');
  activityItems = historyItems.slice(0, 6).map(item => ({ text: `Colorized ${item.original_filename}`, time: new Date(item.created_at).toLocaleString() }));
  list.innerHTML = '';
  if (!activityItems.length) {
    empty.style.display = 'block';
    return;
  }
  empty.style.display = 'none';
  activityItems.forEach(a => {
    const li = document.createElement('li');
    li.className = 'activity-item';
    li.innerHTML = `<span>${a.text}</span><span class="activity-time">${a.time}</span>`;
    list.appendChild(li);
  });
}

function rate(num) {
  currentRating = num;
  document.querySelectorAll('#stars span').forEach((s, i) => s.classList.toggle('active', i < num));
}

async function submitFeedback() {
  const message = document.getElementById('feedbackText').value.trim();
  if (!message || !currentRating) {
    showToast('Please write feedback and select a rating', 'error');
    return;
  }

  try {
    showLoading(true);
    await apiRequest('/api/feedback', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ message, rating: currentRating })
    });
    document.getElementById('feedbackText').value = '';
    currentRating = 0;
    document.querySelectorAll('#stars span').forEach(s => s.classList.remove('active'));
    showToast('Thanks for your feedback!', 'success');
    if (session.user.role === 'admin') await loadAdminData();
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    showLoading(false);
  }
}

async function loadFeedback() {
  try {
    await apiRequest('/api/feedback/me', { headers: authHeaders(false) });
  } catch (_) {
    // Optional in UI for now.
  }
}

async function loadAdminData() {
  await Promise.all([loadAdminStats(), loadAdminUsers(), loadAdminImages(), loadAdminFeedback()]);
}

async function loadAdminStats() {
  const data = await apiRequest('/api/admin/stats', { headers: authHeaders(false) });
  document.getElementById('adminTotalUsers').innerText = data.total_users;
  document.getElementById('adminTotalImages').innerText = data.total_images;
  document.getElementById('adminTotalFeedback').innerText = data.total_feedback;
  document.getElementById('adminAvgProcessing').innerText = data.avg_processing_time;
  document.getElementById('apiStatus').innerText = data.api_server;
  document.getElementById('dbStatus').innerText = data.database;
  document.getElementById('modelStatus').innerText = data.model;
}

async function loadAdminUsers() {
  const search = document.getElementById('userSearch')?.value?.trim() || '';
  const data = await apiRequest(`/api/admin/users?search=${encodeURIComponent(search)}`, { headers: authHeaders(false) });
  const body = document.getElementById('usersBody');
  body.innerHTML = '';
  (data.users || []).forEach(user => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${user.name}</td>
      <td>${user.email}</td>
      <td>${user.role}</td>
      <td>${user.image_count}</td>
      <td>${user.feedback_count}</td>
    `;
    body.appendChild(tr);
  });
}

async function loadAdminImages() {
  const data = await apiRequest('/api/admin/images', { headers: authHeaders(false) });
  const body = document.getElementById('imagesBody');
  body.innerHTML = '';
  (data.images || []).forEach(img => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${img.id}</td>
      <td>${img.user_id}</td>
      <td>${img.original_filename}</td>
      <td>${img.status}</td>
      <td>${img.processing_time || 0}</td>
    `;
    body.appendChild(tr);
  });
}

async function loadAdminFeedback() {
  const data = await apiRequest('/api/admin/feedback', { headers: authHeaders(false) });
  const body = document.getElementById('feedbackBody');
  body.innerHTML = '';
  (data.feedback || []).forEach(item => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${item.user_id}</td>
      <td>${item.rating}</td>
      <td>${item.message}</td>
      <td>${new Date(item.created_at).toLocaleString()}</td>
    `;
    body.appendChild(tr);
  });
}

function doLogout() {
  localStorage.removeItem('session');
  localStorage.removeItem('preferences');
  session = null;
  preferences = { dark_mode: false, notifications: true };
  showToast('Logged out', 'success');
  goTo('login');
}
