// Mooder Phone PWA Client

const STORAGE_KEY_QUEUE = 'mooder_offline_queue';
let state = {
  rating: 0,
  reflectionQuestion: "What made you smile today?",
  selectedKeywords: new Set(),
  questions: [],
  predefinedKeywords: [],
  online: navigator.onLine,
  deferredInstallPrompt: null
};

// ── DOM Elements ───────────────────────────────────────────────────
const starsEl = document.getElementById('stars');
const ratingLabelEl = document.getElementById('rating-label');
const notesInput = document.getElementById('notes');
const questionTextEl = document.getElementById('reflection-question');
const reflectionInput = document.getElementById('reflection-answer');
const refreshQuestionBtn = document.getElementById('refresh-question-btn');
const keywordsContainer = document.getElementById('keywords-container');
const customKeywordInput = document.getElementById('custom-keyword');
const addKeywordBtn = document.getElementById('add-keyword-btn');
const saveBtn = document.getElementById('save-btn');
const toastEl = document.getElementById('toast');
const networkBanner = document.getElementById('network-banner');
const installBtn = document.getElementById('install-btn');

// ── Toast notification ─────────────────────────────────────────────
function showToast(msg) {
  toastEl.textContent = msg;
  toastEl.classList.add('show');
  setTimeout(() => toastEl.classList.remove('show'), 3000);
}

// ── Date helper ────────────────────────────────────────────────────
function getTodayKey() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

// ── Star Rating ────────────────────────────────────────────────────
function initStars() {
  starsEl.innerHTML = '';
  for (let i = 1; i <= 5; i++) {
    const btn = document.createElement('button');
    btn.className = 'star-btn';
    btn.innerHTML = '★';
    btn.dataset.value = i;
    btn.addEventListener('click', () => setRating(i));
    starsEl.appendChild(btn);
  }
}

function setRating(val) {
  state.rating = val;
  const starBtns = starsEl.querySelectorAll('.star-btn');
  starBtns.forEach((btn, idx) => {
    btn.classList.toggle('filled', idx < val);
  });
  ratingLabelEl.textContent = val > 0 ? `${val}/5` : 'Tap a star to rate';
  saveBtn.disabled = val === 0;
}

// ── Questions ──────────────────────────────────────────────────────
function cycleQuestion() {
  if (state.questions.length > 0) {
    const nextQ = state.questions[Math.floor(Math.random() * state.questions.length)];
    state.reflectionQuestion = nextQ;
    questionTextEl.textContent = nextQ;
  }
}

// ── Keywords ───────────────────────────────────────────────────────
function renderKeywords() {
  keywordsContainer.innerHTML = '';
  state.predefinedKeywords.forEach((kw) => {
    const chip = document.createElement('div');
    chip.className = `chip ${state.selectedKeywords.has(kw) ? 'active' : ''}`;
    chip.textContent = kw;
    chip.addEventListener('click', () => {
      if (state.selectedKeywords.has(kw)) {
        state.selectedKeywords.delete(kw);
      } else {
        state.selectedKeywords.add(kw);
      }
      renderKeywords();
    });
    keywordsContainer.appendChild(chip);
  });
}

function addCustomKeyword() {
  const kw = customKeywordInput.value.trim().toLowerCase();
  if (kw && !state.predefinedKeywords.includes(kw)) {
    state.predefinedKeywords.unshift(kw);
    state.selectedKeywords.add(kw);
    customKeywordInput.value = '';
    renderKeywords();
  }
}

// ── Network status & Offline Queue ─────────────────────────────────
function updateNetworkStatus() {
  state.online = navigator.onLine;
  if (!state.online) {
    networkBanner.textContent = '⚡ Offline mode (Changes will sync when reconnected)';
    networkBanner.classList.add('visible');
  } else {
    networkBanner.classList.remove('visible');
    flushOfflineQueue();
  }
}

function saveToOfflineQueue(dayKey, entry) {
  const queue = JSON.parse(localStorage.getItem(STORAGE_KEY_QUEUE) || '{}');
  queue[dayKey] = entry;
  localStorage.setItem(STORAGE_KEY_QUEUE, JSON.stringify(queue));
}

async function flushOfflineQueue() {
  const queue = JSON.parse(localStorage.getItem(STORAGE_KEY_QUEUE) || '{}');
  const count = Object.keys(queue).length;
  if (count === 0) return;

  try {
    const res = await fetch('/api/sync', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ entries: queue }),
    });
    if (res.ok) {
      localStorage.removeItem(STORAGE_KEY_QUEUE);
      showToast(`🔄 Synced ${count} offline log(s) to laptop!`);
    }
  } catch (err) {
    console.warn('Sync retry failed:', err);
  }
}

// ── Load Today Data from Server ────────────────────────────────────
async function loadToday() {
  try {
    const res = await fetch('/api/today');
    if (!res.ok) throw new Error('Network error');
    const data = await res.json();

    if (data.questions && data.questions.length > 0) {
      state.questions = data.questions;
    }

    if (data.exists && data.entry) {
      const e = data.entry;
      setRating(e.rating || 0);
      if (e.notes) notesInput.value = e.notes;
      if (e.reflection) {
        state.reflectionQuestion = e.reflection.question || state.reflectionQuestion;
        questionTextEl.textContent = state.reflectionQuestion;
        reflectionInput.value = e.reflection.answer || '';
      }
      if (e.keywords && Array.isArray(e.keywords)) {
        e.keywords.forEach((k) => state.selectedKeywords.add(k.toLowerCase()));
      }
    } else {
      cycleQuestion();
    }
  } catch (err) {
    console.warn('Could not load today data from server (running offline):', err);
    // Check local queue
    const queue = JSON.parse(localStorage.getItem(STORAGE_KEY_QUEUE) || '{}');
    const localToday = queue[getTodayKey()];
    if (localToday) {
      setRating(localToday.rating || 0);
      if (localToday.notes) notesInput.value = localToday.notes;
      if (localToday.reflection) {
        questionTextEl.textContent = localToday.reflection.question;
        reflectionInput.value = localToday.reflection.answer;
      }
    } else {
      cycleQuestion();
    }
  }

  // Load keywords
  try {
    const kwRes = await fetch('/api/keywords');
    if (kwRes.ok) {
      const kwData = await kwRes.json();
      const all = [];
      Object.values(kwData).forEach((list) => all.push(...list));
      state.predefinedKeywords = Array.from(new Set(all));
      renderKeywords();
    }
  } catch (err) {
    // Default fallback
    state.predefinedKeywords = [
      "productive", "grateful", "awesome", "energized",
      "routine", "meh", "exhausted", "anxious", "challenging"
    ];
    renderKeywords();
  }
}

// ── Save Entry ─────────────────────────────────────────────────────
async function saveEntry() {
  if (state.rating === 0) return;

  const todayKey = getTodayKey();
  const entry = {
    rating: state.rating,
    notes: notesInput.value.trim() || null,
    reflection: reflectionInput.value.trim()
      ? { question: state.reflectionQuestion, answer: reflectionInput.value.trim() }
      : null,
    keywords: Array.from(state.selectedKeywords),
    timestamp: new Date().toISOString()
  };

  saveBtn.disabled = true;
  saveBtn.textContent = 'Saving...';

  try {
    const res = await fetch(`/api/day/${todayKey}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(entry),
    });

    if (!res.ok) throw new Error('Save failed');
    showToast('✅ Saved successfully!');
  } catch (err) {
    console.warn('Saved to offline queue:', err);
    saveToOfflineQueue(todayKey, entry);
    showToast('💾 Saved offline! Will sync on WiFi');
    networkBanner.textContent = '⚡ Saved to offline queue';
    networkBanner.classList.add('visible');
  } finally {
    saveBtn.disabled = false;
    saveBtn.textContent = 'Save Entry';
  }
}

// ── Setup Event Listeners ──────────────────────────────────────────
function init() {
  initStars();
  updateNetworkStatus();

  window.addEventListener('online', updateNetworkStatus);
  window.addEventListener('offline', updateNetworkStatus);

  refreshQuestionBtn.addEventListener('click', cycleQuestion);
  saveBtn.addEventListener('click', saveEntry);

  addKeywordBtn.addEventListener('click', addCustomKeyword);
  customKeywordInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') addCustomKeyword();
  });

  // PWA Install Prompt
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    state.deferredInstallPrompt = e;
    if (installBtn) {
      installBtn.style.display = 'block';
      installBtn.addEventListener('click', async () => {
        if (state.deferredInstallPrompt) {
          state.deferredInstallPrompt.prompt();
          await state.deferredInstallPrompt.userChoice;
          state.deferredInstallPrompt = null;
          installBtn.style.display = 'none';
        }
      });
    }
  });

  // Register service worker
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js').catch((err) => {
      console.warn('SW registration failed:', err);
    });
  }

  loadToday();
}

document.addEventListener('DOMContentLoaded', init);
