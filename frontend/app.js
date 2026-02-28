/**
 * Pillulu Health Assistant - Frontend
 * Configure API_BASE for your backend URL (local or Render)
 */
const API_BASE = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
  ? "http://127.0.0.1:8000"
  : "";
const MED_PLACEHOLDER_IMAGE = "icons8-pill-80.png";

// --- Helpers ---
function showError(containerId, message) {
  const el = document.getElementById(containerId);
  if (!el) return;
  el.textContent = message;
  el.classList.remove("hidden");
}

function hideError(containerId) {
  const el = document.getElementById(containerId);
  if (el) el.classList.add("hidden");
}

function showSuccess(containerId) {
  const el = document.getElementById(containerId);
  if (!el) return;
  el.classList.remove("hidden");
  setTimeout(() => el.classList.add("hidden"), 3000);
}

function cleanOptionalStr(value, maxLen = 255) {
  if (value == null) return null;
  const text = String(value).trim();
  if (!text) return null;
  return text.slice(0, maxLen);
}

function initClearableInput(inputId, clearBtnId) {
  const inputEl = document.getElementById(inputId);
  const clearBtnEl = document.getElementById(clearBtnId);
  if (!inputEl || !clearBtnEl) return;

  const syncVisibility = () => {
    clearBtnEl.classList.toggle("hidden", !inputEl.value);
  };

  inputEl.addEventListener("input", syncVisibility);
  clearBtnEl.addEventListener("click", () => {
    inputEl.value = "";
    inputEl.dispatchEvent(new Event("input", { bubbles: true }));
    inputEl.focus();
    if (inputId === "search-input") hideError("search-error");
  });
  syncVisibility();
}

const AUTH_TOKEN_KEY = "pillulu_token";

function getAuthToken() {
  return localStorage.getItem(AUTH_TOKEN_KEY);
}

function setAuthToken(token) {
  localStorage.setItem(AUTH_TOKEN_KEY, token);
}

function clearAuthToken() {
  localStorage.removeItem(AUTH_TOKEN_KEY);
}

async function fetchApi(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const headers = {
    "Content-Type": "application/json",
    ...options.headers,
  };
  const token = getAuthToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(url, { ...options, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

// --- Auth ---
async function checkAuth() {
  try {
    const me = await fetchApi("/api/auth/me");
    return me.logged_in ? me : null;
  } catch {
    return null;
  }
}

function updateAuthUI(user) {
  const loginBtn = document.getElementById("login-btn");
  const logoutBtn = document.getElementById("logout-btn");
  const userEmail = document.getElementById("user-email");
  if (user) {
    loginBtn.classList.add("hidden");
    logoutBtn.classList.remove("hidden");
    userEmail.textContent = user.email;
    userEmail.classList.remove("hidden");
  } else {
    loginBtn.classList.remove("hidden");
    logoutBtn.classList.add("hidden");
    userEmail.classList.add("hidden");
  }
}

document.getElementById("login-btn").addEventListener("click", () => {
  document.getElementById("login-modal").classList.remove("hidden");
});

document.getElementById("login-modal").addEventListener("click", (e) => {
  if (e.target.id === "login-modal") document.getElementById("login-modal").classList.add("hidden");
});
document.getElementById("login-modal-close").addEventListener("click", () => {
  document.getElementById("login-modal").classList.add("hidden");
});

document.getElementById("oauth-google-btn").addEventListener("click", () => {
  window.location.href = `${API_BASE}/api/auth/oauth/google/start`;
});

function handleOAuthRedirectResult() {
  const url = new URL(window.location.href);
  const token = url.searchParams.get("token");
  const email = url.searchParams.get("email");
  const oauthError = url.searchParams.get("oauth_error");

  const clearOAuthParams = () => {
    ["token", "email", "oauth_error"].forEach((key) => url.searchParams.delete(key));
    window.history.replaceState({}, "", `${url.pathname}${url.search}${url.hash}`);
  };

  if (oauthError) {
    alert(oauthError);
    clearOAuthParams();
    return null;
  }

  if (token && email) {
    setAuthToken(token);
    updateAuthUI({ email });
    document.getElementById("login-modal").classList.add("hidden");
    clearOAuthParams();
    return { email };
  }
  return null;
}

document.getElementById("login-submit").addEventListener("click", async () => {
  const email = document.getElementById("login-email").value.trim();
  const password = document.getElementById("login-password").value;
  if (!email || !password) {
    alert("Please enter email and password.");
    return;
  }
  try {
    const data = await fetchApi("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    setAuthToken(data.token);
    updateAuthUI({ email: data.email });
    document.getElementById("login-modal").classList.add("hidden");
    document.getElementById("login-email").value = "";
    document.getElementById("login-password").value = "";
    loadPillbox();
    loadProfile();
  } catch (err) {
    alert(err.message || "Login failed.");
  }
});

document.getElementById("register-submit").addEventListener("click", async () => {
  const email = document.getElementById("register-email").value.trim();
  const password = document.getElementById("register-password").value;
  const acceptedTerms = document.getElementById("register-terms").checked;
  if (!email || !password) {
    alert("Please enter email and password.");
    return;
  }
  if (password.length < 6) {
    alert("Password must be at least 6 characters.");
    return;
  }
  if (!acceptedTerms) {
    alert("Please accept the educational-use terms before creating an account.");
    return;
  }
  try {
    const data = await fetchApi("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    setAuthToken(data.token);
    updateAuthUI({ email: data.email });
    document.getElementById("login-modal").classList.add("hidden");
    document.getElementById("register-email").value = "";
    document.getElementById("register-password").value = "";
    document.getElementById("register-terms").checked = false;
    loadPillbox();
    loadProfile();
  } catch (err) {
    alert(err.message || "Registration failed.");
  }
});

document.getElementById("logout-btn").addEventListener("click", () => {
  clearAuthToken();
  updateAuthUI(null);
  loadPillbox();
  updateProfileUI(null);
  loadWeather(null, null);
});

// --- US States & Cities (for location selection) ---
async function populateStateSelect() {
  try {
    const { states } = await fetchApi("/api/weather/states");
    const sel = document.getElementById("profile-state-input");
    if (!sel) return;
    sel.innerHTML = '<option value="">Select state</option>';
    (states || []).forEach((s) => {
      const opt = document.createElement("option");
      opt.value = s;
      opt.textContent = s;
      sel.appendChild(opt);
    });
  } catch {}
}

async function populateCitySelect(state) {
  const sel = document.getElementById("profile-city-input");
  if (!sel) return;
  sel.innerHTML = '<option value="">Select city</option>';
  if (!state) return;
  try {
    const { cities } = await fetchApi(`/api/weather/cities/${encodeURIComponent(state)}`);
    (cities || []).forEach((c) => {
      const opt = document.createElement("option");
      opt.value = c;
      opt.textContent = c;
      sel.appendChild(opt);
    });
  } catch {}
}

document.getElementById("profile-state-input")?.addEventListener("change", (e) => {
  populateCitySelect(e.target.value);
  document.getElementById("profile-city-input").value = "";
});

// --- User Profile ---
function renderProfileValue(val) {
  return val != null && val !== "" ? String(val) : "—";
}

function updateProfileUI(profile) {
  const displayEl = document.getElementById("profile-display");
  const promptEl = document.getElementById("profile-login-prompt");
  const editBtn = document.getElementById("profile-edit-btn");
  if (profile) {
    displayEl.classList.remove("hidden");
    promptEl.classList.add("hidden");
    document.getElementById("profile-age").textContent = renderProfileValue(profile.age);
    document.getElementById("profile-height").textContent = renderProfileValue(profile.height_cm);
    document.getElementById("profile-weight").textContent = renderProfileValue(profile.weight_kg);
    const loc = [profile.city, profile.state].filter(Boolean).join(", ") || profile.region;
    document.getElementById("profile-location").textContent = renderProfileValue(loc || null);
    editBtn.disabled = false;
  } else {
    displayEl.classList.add("hidden");
    promptEl.classList.remove("hidden");
    editBtn.disabled = true;
  }
}

async function loadProfile() {
  if (!getAuthToken()) {
    updateProfileUI(null);
    loadWeather(null, null);
    return;
  }
  try {
    const p = await fetchApi("/api/user/profile");
    updateProfileUI(p);
    loadWeather(p?.state, p?.city);
  } catch {
    updateProfileUI(null);
    loadWeather(null, null);
  }
}

// --- Weather (Open-Meteo, no API key) ---
const WEATHER_CODE_MAP = {
  0: { desc: "Clear", icon: "☀️" },
  1: { desc: "Mainly clear", icon: "🌤️" },
  2: { desc: "Partly cloudy", icon: "⛅" },
  3: { desc: "Overcast", icon: "☁️" },
  45: { desc: "Foggy", icon: "🌫️" },
  48: { desc: "Depositing rime fog", icon: "🌫️" },
  51: { desc: "Light drizzle", icon: "🌧️" },
  53: { desc: "Drizzle", icon: "🌧️" },
  55: { desc: "Dense drizzle", icon: "🌧️" },
  61: { desc: "Slight rain", icon: "🌧️" },
  63: { desc: "Rain", icon: "🌧️" },
  65: { desc: "Heavy rain", icon: "⛈️" },
  71: { desc: "Slight snow", icon: "🌨️" },
  73: { desc: "Snow", icon: "🌨️" },
  75: { desc: "Heavy snow", icon: "❄️" },
  77: { desc: "Snow grains", icon: "🌨️" },
  80: { desc: "Slight showers", icon: "🌦️" },
  81: { desc: "Showers", icon: "🌦️" },
  82: { desc: "Heavy showers", icon: "⛈️" },
  85: { desc: "Slight snow showers", icon: "🌨️" },
  86: { desc: "Heavy snow showers", icon: "❄️" },
  95: { desc: "Thunderstorm", icon: "⛈️" },
  96: { desc: "Thunderstorm with hail", icon: "⛈️" },
};

function getWeatherInfo(code) {
  return WEATHER_CODE_MAP[code] || { desc: "Unknown", icon: "🌡️" };
}

async function loadWeather(state, city) {
  const widgetEl = document.getElementById("weather-widget");
  const emptyEl = document.getElementById("weather-empty");
  if (!state || !city) {
    widgetEl.classList.add("hidden");
    emptyEl.classList.remove("hidden");
    emptyEl.querySelector("p").textContent = "Set your state and city in profile to see local weather.";
    return;
  }
  try {
    const data = await fetchApi(`/api/weather?state=${encodeURIComponent(state)}&city=${encodeURIComponent(city)}`);
    const cw = data.current_weather;
    const info = getWeatherInfo(cw.weathercode);
    const tempF = Math.round(cw.temperature * 9 / 5 + 32);
    document.getElementById("weather-location").textContent = `${city}, ${state}`;
    document.getElementById("weather-temp").innerHTML = `<span class="weather-temp-value">${tempF}</span>°F <span class="weather-temp-alt">(${Math.round(cw.temperature)}°C)</span>`;
    document.getElementById("weather-desc").textContent = `${info.icon} ${info.desc}`;
    document.getElementById("weather-details").innerHTML = `Wind: ${cw.windspeed} km/h`;

    const forecastEl = document.getElementById("weather-forecast");
    const forecast = data.forecast || [];
    const dayNames = ["Today", "Tomorrow", "Day 3", "Day 4"];
    forecastEl.innerHTML = forecast.slice(0, 4).map((day, i) => {
      const info2 = getWeatherInfo(day.weathercode);
      const maxF = Math.round(day.temp_max * 9 / 5 + 32);
      const minF = Math.round(day.temp_min * 9 / 5 + 32);
      const dateStr = day.date ? new Date(day.date).toLocaleDateString("en-US", { weekday: "short" }) : dayNames[i];
      return `<div class="forecast-day"><span class="forecast-date">${dateStr}</span><span class="forecast-icon">${info2.icon}</span><span class="forecast-temp">${minF}°–${maxF}°</span></div>`;
    }).join("");

    widgetEl.classList.remove("hidden");
    emptyEl.classList.add("hidden");
  } catch {
    widgetEl.classList.add("hidden");
    emptyEl.classList.remove("hidden");
    emptyEl.querySelector("p").textContent = "Unable to load weather. Try again later.";
  }
}

document.getElementById("profile-edit-btn").addEventListener("click", async () => {
  if (!getAuthToken()) return;
  try {
    const p = await fetchApi("/api/user/profile");
    document.getElementById("profile-age-input").value = p.age ?? "";
    document.getElementById("profile-height-input").value = p.height_cm ?? "";
    document.getElementById("profile-weight-input").value = p.weight_kg ?? "";
    document.getElementById("profile-state-input").value = p.state ?? "";
    await populateCitySelect(p.state);
    document.getElementById("profile-city-input").value = p.city ?? "";
    document.getElementById("profile-modal").classList.remove("hidden");
  } catch {
    alert("Please log in to edit your profile.");
  }
});

document.getElementById("profile-cancel").addEventListener("click", () => {
  document.getElementById("profile-modal").classList.add("hidden");
});

document.getElementById("profile-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const age = document.getElementById("profile-age-input").value;
  const height_cm = document.getElementById("profile-height-input").value;
  const weight_kg = document.getElementById("profile-weight-input").value;
  const state = document.getElementById("profile-state-input").value || null;
  const city = document.getElementById("profile-city-input").value || null;
  try {
    await fetchApi("/api/user/profile", {
      method: "PUT",
      body: JSON.stringify({
        age: age ? parseInt(age, 10) : null,
        height_cm: height_cm ? parseInt(height_cm, 10) : null,
        weight_kg: weight_kg ? parseInt(weight_kg, 10) : null,
        state,
        city,
      }),
    });
    document.getElementById("profile-modal").classList.add("hidden");
    loadProfile();
    loadWeather(state, city);
  } catch (err) {
    alert(err.message || "Failed to save profile.");
  }
});

// --- Search ---
let lastSearchResults = [];
let pendingAddMedMeta = null;

document.getElementById("search-btn").addEventListener("click", doSearch);
document.getElementById("search-input").addEventListener("keypress", (e) => {
  if (e.key === "Enter") doSearch();
});
document.getElementById("scan-btn").addEventListener("click", openScanModal);
document.getElementById("scan-cancel").addEventListener("click", closeScanModal);
document.getElementById("scan-capture").addEventListener("click", captureAndDetectFromCamera);
document.getElementById("scan-modal").addEventListener("click", (e) => {
  if (e.target.id === "scan-modal") closeScanModal();
});

let scanStream = null;
let scanInProgress = false;

const OCR_IGNORE_WORDS = new Set([
  "TABLET", "TABLETS", "CAPSULE", "CAPSULES", "SOFTGEL", "SOFTGELS", "SOLUTION",
  "INJECTION", "TOPICAL", "ORAL", "USP", "NDC", "LOT", "EXP", "RX", "ONLY",
  "MG", "MCG", "ML", "GRAM", "G", "FOR", "THE", "AND", "WITH", "PAIN", "RELIEF",
]);

function updateScanStatus(message, isError = false) {
  const statusEl = document.getElementById("scan-status");
  statusEl.textContent = message;
  statusEl.classList.toggle("error", !!isError);
}

function stopScanCamera() {
  if (!scanStream) return;
  scanStream.getTracks().forEach((track) => track.stop());
  scanStream = null;
  const videoEl = document.getElementById("scan-video");
  videoEl.srcObject = null;
}

async function openScanModal() {
  hideError("search-error");
  stopScanCamera();
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    showError("search-error", "Camera is not supported in this browser.");
    return;
  }

  document.getElementById("scan-modal").classList.remove("hidden");
  updateScanStatus("Starting camera...");

  try {
    scanStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: { ideal: "environment" } },
      audio: false,
    });
    const videoEl = document.getElementById("scan-video");
    videoEl.srcObject = scanStream;
    await videoEl.play();
    updateScanStatus("Camera ready. Hold label steady and tap Capture & Detect.");
  } catch {
    updateScanStatus("Unable to access camera. Check browser permissions.", true);
    showError("search-error", "Unable to access camera. Please allow camera permission.");
  }
}

function closeScanModal(force = false) {
  if (scanInProgress && !force) return;
  stopScanCamera();
  document.getElementById("scan-modal").classList.add("hidden");
  updateScanStatus("Camera not started");
}

function extractMedicationCandidate(rawText) {
  if (!rawText) return "";
  const cleanedLines = rawText
    .split(/\r?\n/)
    .map((line) => line.replace(/[^A-Za-z0-9\s-]/g, " ").replace(/\s+/g, " ").trim())
    .filter((line) => line.length >= 4);

  const candidates = [];
  for (const line of cleanedLines) {
    const upper = line.toUpperCase();
    if (/\b(NDC|LOT|EXP)\b/.test(upper)) continue;
    if (/\b\d+(\.\d+)?\s?(MG|MCG|ML|G)\b/.test(upper) && upper.split(" ").length <= 2) continue;

    const words = upper
      .split(" ")
      .filter((w) => /^[A-Z-]{3,}$/.test(w) && !OCR_IGNORE_WORDS.has(w));
    if (words.length === 0) continue;

    const oneWord = words[0];
    const twoWord = words.length >= 2 ? `${words[0]} ${words[1]}` : words[0];
    const score = Math.max(oneWord.length, twoWord.length) + words.length;
    candidates.push({ oneWord, twoWord, score });
  }

  if (candidates.length === 0) return "";
  candidates.sort((a, b) => b.score - a.score);
  const best = candidates[0];
  return best.twoWord.length <= 28 ? best.twoWord : best.oneWord;
}

function toDisplayMedicationName(name) {
  return name
    .toLowerCase()
    .split(" ")
    .map((part) => (part ? part[0].toUpperCase() + part.slice(1) : part))
    .join(" ");
}

async function captureAndDetectFromCamera() {
  if (scanInProgress) return;

  const videoEl = document.getElementById("scan-video");
  const canvasEl = document.getElementById("scan-canvas");
  const captureBtn = document.getElementById("scan-capture");
  if (!videoEl.videoWidth || !videoEl.videoHeight) {
    updateScanStatus("Camera not ready. Please wait a moment and retry.", true);
    return;
  }

  if (!window.Tesseract || typeof window.Tesseract.recognize !== "function") {
    updateScanStatus("OCR library failed to load. Refresh and try again.", true);
    return;
  }

  scanInProgress = true;
  captureBtn.disabled = true;
  captureBtn.textContent = "Detecting...";
  updateScanStatus("Running OCR... this can take a few seconds.");

  try {
    canvasEl.width = videoEl.videoWidth;
    canvasEl.height = videoEl.videoHeight;
    const ctx = canvasEl.getContext("2d");
    ctx.drawImage(videoEl, 0, 0, canvasEl.width, canvasEl.height);

    const result = await window.Tesseract.recognize(canvasEl, "eng");
    const text = result?.data?.text || "";
    const candidate = extractMedicationCandidate(text);

    if (!candidate) {
      updateScanStatus("No medication name detected. Try better lighting or move closer.", true);
      return;
    }

    const displayName = toDisplayMedicationName(candidate);
    document.getElementById("search-input").value = displayName;
    closeScanModal(true);
    doSearch();
  } catch {
    updateScanStatus("OCR failed. Please try again.", true);
  } finally {
    scanInProgress = false;
    captureBtn.disabled = false;
    captureBtn.textContent = "Capture & Detect";
  }
}

window.addEventListener("beforeunload", stopScanCamera);

async function doSearch() {
  const input = document.getElementById("search-input");
  const q = (input.value || "").trim();
  const resultsEl = document.getElementById("search-results");
  hideError("search-error");

  if (!q) {
    showError("search-error", "Please enter a medication name");
    return;
  }

  resultsEl.innerHTML = '<p style="text-align:center;color:#666;">Searching...</p>';
  try {
    const data = await fetchApi(`/api/med/search?q=${encodeURIComponent(q)}`);
    lastSearchResults = data || [];
    if (!data || data.length === 0) {
      resultsEl.innerHTML = '<p style="text-align:center;color:#666;">No medications found. Try different keywords.</p>';
      return;
    }
    resultsEl.innerHTML = data.map((m, idx) => {
      const name = m.display_name || m.brand_name || m.generic_name || m.substance_name || "Medication (name not available)";
      const imageUrl = m.image_url || MED_PLACEHOLDER_IMAGE;
      const canonicalName = m.canonical_name && m.canonical_name !== name ? m.canonical_name : null;
      const appearanceItems = [
        m.imprint ? `Imprint: ${escapeHtml(m.imprint)}` : null,
        m.color ? `Color: ${escapeHtml(m.color)}` : null,
        m.shape ? `Shape: ${escapeHtml(m.shape)}` : null,
      ].filter(Boolean);
      return `
        <div class="med-card">
          <div class="med-card-top">
            <img src="${escapeHtml(imageUrl)}" alt="${escapeHtml(name)}" class="med-thumb" loading="lazy" onerror="this.onerror=null;this.src='${MED_PLACEHOLDER_IMAGE}'">
            <div class="med-main">
              <h4>${escapeHtml(name)}</h4>
              ${canonicalName ? `<p class="med-canonical">Standard: ${escapeHtml(canonicalName)}</p>` : ""}
            </div>
          </div>
          ${m.generic_name ? `<p>Generic: ${escapeHtml(m.generic_name)}</p>` : ""}
          ${m.manufacturer ? `<p>Manufacturer: ${escapeHtml(m.manufacturer)}</p>` : ""}
          ${m.route ? `<p>Route: ${escapeHtml(m.route)}</p>` : ""}
          ${appearanceItems.length ? `<p>${appearanceItems.join(" | ")}</p>` : ""}
          ${m.warnings_snippet ? `<p>Warnings: ${escapeHtml(m.warnings_snippet.substring(0, 150))}...</p>` : ""}
          <div class="card-actions">
            <button class="btn btn-secondary btn-small" data-action="ask" data-name="${escapeHtml(name)}">Ask AI</button>
            <button class="btn btn-primary btn-small" data-action="add" data-name="${escapeHtml(name)}" data-idx="${idx}">Add to Pillbox</button>
          </div>
        </div>
      `;
    }).join("");

    resultsEl.querySelectorAll("[data-action]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const action = btn.dataset.action;
        const name = btn.dataset.name;
        const idx = Number(btn.dataset.idx);
        if (action === "ask") {
          document.getElementById("ai-med-context").value = name;
          document.getElementById("ai-section").scrollIntoView({ behavior: "smooth" });
        } else if (action === "add") {
          const fromSearch = Number.isInteger(idx) && idx >= 0 && idx < lastSearchResults.length
            ? lastSearchResults[idx]
            : null;
          openAddMedModal(name, fromSearch);
        }
      });
    });
  } catch (e) {
    lastSearchResults = [];
    showError("search-error", e.message || "Search failed. Check your connection or try again later.");
    resultsEl.innerHTML = "";
  }
}

function escapeHtml(s) {
  if (!s) return "";
  const div = document.createElement("div");
  div.textContent = s;
  return div.innerHTML;
}

// --- Add Med Modal ---
function openAddMedModal(presetName = "", sourceMeta = null) {
  document.getElementById("add-med-name").value = presetName;
  document.getElementById("add-med-purpose").value = "";
  document.getElementById("add-med-stock").value = "10";
  document.getElementById("add-med-threshold").value = "5";
  document.getElementById("add-med-notes").value = "";
  pendingAddMedMeta = sourceMeta
    ? {
        canonical_name: cleanOptionalStr(sourceMeta.canonical_name, 255),
        image_url: cleanOptionalStr(sourceMeta.image_url, 1024),
        imprint: cleanOptionalStr(sourceMeta.imprint, 255),
        color: cleanOptionalStr(sourceMeta.color, 128),
        shape: cleanOptionalStr(sourceMeta.shape, 128),
      }
    : null;
  document.getElementById("add-med-modal").classList.remove("hidden");
}

document.getElementById("add-med-cancel").addEventListener("click", () => {
  document.getElementById("add-med-modal").classList.add("hidden");
  pendingAddMedMeta = null;
});

document.getElementById("add-med-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const name = document.getElementById("add-med-name").value.trim();
  if (!name) return;
  try {
    await fetchApi("/api/pillbox/meds", {
      method: "POST",
      body: JSON.stringify({
        name,
        purpose: document.getElementById("add-med-purpose").value.trim() || null,
        dosage_notes: document.getElementById("add-med-notes").value.trim() || null,
        canonical_name: pendingAddMedMeta?.canonical_name || null,
        image_url: pendingAddMedMeta?.image_url || null,
        imprint: pendingAddMedMeta?.imprint || null,
        color: pendingAddMedMeta?.color || null,
        shape: pendingAddMedMeta?.shape || null,
        stock_count: parseInt(document.getElementById("add-med-stock").value, 10) || 0,
        low_stock_threshold: parseInt(document.getElementById("add-med-threshold").value, 10) || 5,
      }),
    });
    document.getElementById("add-med-modal").classList.add("hidden");
    pendingAddMedMeta = null;
    loadPillbox();
  } catch (err) {
    showError("pillbox-error", err.message);
  }
});

// --- AI Ask ---
document.getElementById("ai-ask-btn").addEventListener("click", doAiAsk);

async function doAiAsk() {
  const question = document.getElementById("ai-question").value.trim();
  const contextMed = document.getElementById("ai-med-context").value.trim();
  hideError("ai-error");
  const answerEl = document.getElementById("ai-answer");
  answerEl.classList.add("hidden");

  if (!question) {
    showError("ai-error", "Please enter your question");
    return;
  }

  document.getElementById("ai-ask-btn").disabled = true;
  document.getElementById("ai-ask-btn").textContent = "Thinking...";
  try {
    const data = await fetchApi("/api/ai/ask", {
      method: "POST",
      body: JSON.stringify({
        question,
        context_med_name: contextMed || undefined,
      }),
    });
    answerEl.querySelector(".answer-content").innerHTML = data.answer.replace(/\n/g, "<br>");
    answerEl.querySelector(".answer-disclaimer").textContent = data.disclaimer;

    const suggestedEl = document.getElementById("ai-suggested-meds");
    if (data.suggested_medications && data.suggested_medications.length > 0) {
      suggestedEl.innerHTML = `<p class="suggested-label">Add to Pillbox:</p>` + data.suggested_medications.map((name) =>
        `<button type="button" class="btn btn-secondary btn-small add-from-ai" data-med-name="${escapeHtml(name)}">${escapeHtml(name)}</button>`
      ).join(" ");
      suggestedEl.classList.remove("hidden");
      suggestedEl.querySelectorAll(".add-from-ai").forEach((btn) => {
        btn.addEventListener("click", () => openAddMedModal(btn.dataset.medName));
      });
    } else {
      suggestedEl.innerHTML = "";
      suggestedEl.classList.add("hidden");
    }

    answerEl.classList.remove("hidden");
  } catch (err) {
    showError("ai-error", err.message || "AI service temporarily unavailable. Try again later.");
  } finally {
    document.getElementById("ai-ask-btn").disabled = false;
    document.getElementById("ai-ask-btn").textContent = "Ask";
  }
}

// --- Pillbox ---
let cachedMeds = [];

async function loadPillbox() {
  hideError("pillbox-error");
  const listEl = document.getElementById("pillbox-list");
  const emptyEl = document.getElementById("pillbox-empty");
  listEl.innerHTML = '<p style="text-align:center;color:#666;">Loading...</p>';
  emptyEl.classList.add("hidden");

  try {
    const meds = await fetchApi("/api/pillbox/meds");
    cachedMeds = meds || [];
    if (!meds || meds.length === 0) {
      listEl.innerHTML = "";
      emptyEl.classList.remove("hidden");
      return;
    }
    emptyEl.classList.add("hidden");
    listEl.innerHTML = meds.map((m) => {
      const isLow = m.stock_count <= m.low_stock_threshold;
      const stockClass = isLow ? "stock-info low" : "stock-info";
      const imageUrl = m.image_url || MED_PLACEHOLDER_IMAGE;
      const appearanceItems = [
        m.imprint ? `Imprint: ${escapeHtml(m.imprint)}` : null,
        m.color ? `Color: ${escapeHtml(m.color)}` : null,
        m.shape ? `Shape: ${escapeHtml(m.shape)}` : null,
      ].filter(Boolean);
      const schedulesHtml = (m.schedules || []).map((s) => `
        <div class="schedule-item">
          <span class="schedule-time">${escapeHtml(s.time_of_day)} ${s.days_of_week}</span>
          <span>
            <button class="btn btn-small btn-secondary" data-edit-sched data-id="${s.id}">Edit</button>
            <button class="btn btn-small btn-secondary" data-del-sched data-id="${s.id}">Delete</button>
          </span>
        </div>
      `).join("");
      return `
        <div class="pillbox-card" data-med-id="${m.id}">
          <div class="med-card-top">
            <img src="${escapeHtml(imageUrl)}" alt="${escapeHtml(m.name)}" class="med-thumb" loading="lazy" onerror="this.onerror=null;this.src='${MED_PLACEHOLDER_IMAGE}'">
            <div class="med-main">
              <h4>${escapeHtml(m.name)}</h4>
              ${m.canonical_name ? `<p class="med-canonical">Standard: ${escapeHtml(m.canonical_name)}</p>` : ""}
            </div>
          </div>
          ${m.purpose ? `<p>Purpose: ${escapeHtml(m.purpose)}</p>` : ""}
          ${appearanceItems.length ? `<p>${appearanceItems.join(" | ")}</p>` : ""}
          <p class="${stockClass}">Stock: ${m.stock_count} | Alert threshold: ${m.low_stock_threshold}</p>
          ${m.dosage_notes ? `<p>Notes: ${escapeHtml(m.dosage_notes)}</p>` : ""}
          <div class="schedule-list">
            <strong>Reminder times:</strong>
            ${schedulesHtml || "<p>None</p>"}
          </div>
          <div class="card-actions">
            <button class="btn btn-secondary btn-small" data-edit-med data-id="${m.id}">Edit</button>
            <button class="btn btn-primary btn-small" data-add-sched data-id="${m.id}" data-name="${escapeHtml(m.name)}">Add time</button>
            <button class="btn btn-secondary btn-small" data-del-med data-id="${m.id}" data-name="${escapeHtml(m.name)}">Delete</button>
          </div>
        </div>
      `;
    }).join("");

    listEl.querySelectorAll("[data-edit-med]").forEach((btn) => {
      btn.addEventListener("click", () => openEditMedModal(parseInt(btn.dataset.id, 10)));
    });
    listEl.querySelectorAll("[data-add-sched]").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.getElementById("add-schedule-med-id").value = btn.dataset.id;
        openAddScheduleModal();
      });
    });
    listEl.querySelectorAll("[data-del-med]").forEach((btn) => {
      btn.addEventListener("click", () => openDeleteMedModal(parseInt(btn.dataset.id, 10), btn.dataset.name || ""));
    });
    listEl.querySelectorAll("[data-edit-sched]").forEach((btn) => {
      btn.addEventListener("click", () => alert("Edit schedule: use API or a future version"));
    });
    listEl.querySelectorAll("[data-del-sched]").forEach((btn) => {
      btn.addEventListener("click", () => deleteSchedule(parseInt(btn.dataset.id, 10)));
    });
    startCountdownUpdates();
  } catch (err) {
    if (err.message && (err.message.includes("Login required") || err.message.includes("401"))) {
      clearAuthToken();
      updateAuthUI(null);
      listEl.innerHTML = '<p class="empty-state">Please log in to view your pillbox.</p>';
    } else {
      showError("pillbox-error", err.message || "Failed to load pillbox. Check your connection.");
      listEl.innerHTML = "";
    }
  }
}

let pendingDeleteMedId = null;

function openDeleteMedModal(id, name) {
  pendingDeleteMedId = id;
  document.getElementById("delete-med-message").textContent = name
    ? `Are you sure you want to delete "${name}"?`
    : "Are you sure you want to delete this medication?";
  document.getElementById("delete-med-modal").classList.remove("hidden");
}

document.getElementById("delete-med-cancel").addEventListener("click", () => {
  document.getElementById("delete-med-modal").classList.add("hidden");
  pendingDeleteMedId = null;
});

document.getElementById("delete-med-confirm").addEventListener("click", async () => {
  if (pendingDeleteMedId == null) return;
  const id = pendingDeleteMedId;
  document.getElementById("delete-med-modal").classList.add("hidden");
  pendingDeleteMedId = null;
  try {
    await fetchApi(`/api/pillbox/meds/${id}`, { method: "DELETE" });
    loadPillbox();
  } catch (err) {
    showError("pillbox-error", err.message);
  }
});

async function deleteSchedule(id) {
  if (!confirm("Delete this reminder time?")) return;
  try {
    await fetchApi(`/api/schedules/${id}`, { method: "DELETE" });
    loadPillbox();
  } catch (err) {
    showError("pillbox-error", err.message);
  }
}

// --- Edit Med Modal ---
async function openEditMedModal(id) {
  try {
    const m = await fetchApi(`/api/pillbox/meds/${id}`);
    document.getElementById("edit-med-id").value = m.id;
    document.getElementById("edit-med-name").value = m.name;
    document.getElementById("edit-med-purpose").value = m.purpose || "";
    document.getElementById("edit-med-stock").value = m.stock_count;
    document.getElementById("edit-med-threshold").value = m.low_stock_threshold;
    document.getElementById("edit-med-notes").value = m.dosage_notes || "";
    document.getElementById("edit-med-modal").classList.remove("hidden");
  } catch (err) {
    showError("pillbox-error", err.message);
  }
}

document.getElementById("edit-med-cancel").addEventListener("click", () => {
  document.getElementById("edit-med-modal").classList.add("hidden");
});

document.getElementById("edit-med-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = document.getElementById("edit-med-id").value;
  try {
    await fetchApi(`/api/pillbox/meds/${id}`, {
      method: "PUT",
      body: JSON.stringify({
        name: document.getElementById("edit-med-name").value.trim(),
        purpose: document.getElementById("edit-med-purpose").value.trim() || null,
        dosage_notes: document.getElementById("edit-med-notes").value.trim() || null,
        stock_count: parseInt(document.getElementById("edit-med-stock").value, 10),
        low_stock_threshold: parseInt(document.getElementById("edit-med-threshold").value, 10),
      }),
    });
    document.getElementById("edit-med-modal").classList.add("hidden");
    loadPillbox();
  } catch (err) {
    showError("pillbox-error", err.message);
  }
});

// --- Add Schedule Modal ---
function getSelectedDays() {
  const checks = document.querySelectorAll("#add-schedule-days input[data-day]:checked");
  const days = Array.from(checks).map((c) => c.dataset.day);
  return days.length === 7 ? "daily" : days.join(",") || "daily";
}

function getTimezoneOffsetHours(timezone, year, month, day) {
  try {
    const utcNoon = Date.UTC(year, month - 1, day, 12, 0, 0);
    const d = new Date(utcNoon);
    const formatter = new Intl.DateTimeFormat("en-CA", {
      timeZone: timezone,
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
    const parts = formatter.formatToParts(d);
    const h = parseInt(parts.find((p) => p.type === "hour")?.value || "12", 10);
    return h - 12;
  } catch {
    return 0;
  }
}

/** Returns { date: Date, displayStr: string } or null. Used for countdown. */
function getNextReminderDate(timeStr, timezone, daysStr) {
  if (!timeStr) return null;
  const [hour, min] = timeStr.split(":").map(Number);
  const selectedDays = daysStr === "daily" ? ["sun", "mon", "tue", "wed", "thu", "fri", "sat"] : daysStr.split(",").map((d) => d.trim().toLowerCase().slice(0, 3));
  if (selectedDays.length === 0) return null;

  const now = new Date();
  const formatter = new Intl.DateTimeFormat("en-CA", {
    timeZone: timezone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    weekday: "short",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
  const parts = formatter.formatToParts(now);
  const get = (type) => parts.find((p) => p.type === type)?.value;
  const tzYear = parseInt(get("year"), 10);
  const tzMonth = parseInt(get("month"), 10) - 1;
  const tzDay = parseInt(get("day"), 10);
  const tzHour = parseInt(get("hour"), 10);
  const tzMin = parseInt(get("minute"), 10);
  const dayNames = ["sun", "mon", "tue", "wed", "thu", "fri", "sat"];

  for (let offset = 0; offset < 8; offset++) {
    const d = new Date(tzYear, tzMonth, tzDay + offset);
    const dayName = dayNames[d.getDay()];
    if (!selectedDays.includes(dayName)) continue;

    const isToday = offset === 0;
    const timePassed = isToday && (tzHour > hour || (tzHour === hour && tzMin >= min));
    const y = d.getFullYear();
    const m = d.getMonth() + 1;
    const day = d.getDate();
    const offsetH = getTimezoneOffsetHours(timezone, y, m, day);
    const utcDate = new Date(Date.UTC(y, m - 1, day, hour - offsetH, min || 0, 0, 0));
    let tzAbbr = "";
    try {
      tzAbbr = new Date().toLocaleTimeString("en-US", { timeZone: timezone, timeZoneName: "short" }).split(" ").pop() || timezone;
    } catch {
      tzAbbr = timezone;
    }
    const displayStr = `${y}-${String(m).padStart(2, "0")}-${String(day).padStart(2, "0")} ${timeStr} (${tzAbbr})`;
    if (isToday && !timePassed) return { date: utcDate, displayStr };
    if (offset > 0) return { date: utcDate, displayStr };
  }
  return null;
}

function computeNextReminder(timeStr, timezone, daysStr) {
  const r = getNextReminderDate(timeStr, timezone, daysStr);
  return r ? r.displayStr : null;
}

function updateNextReminderPreview() {
  const timeInput = document.getElementById("add-schedule-time").value;
  const timezone = document.getElementById("add-schedule-timezone")?.value || "America/New_York";
  const days = getSelectedDays();
  const el = document.getElementById("next-reminder-preview");
  const next = computeNextReminder(timeInput, timezone, days);
  el.textContent = next ? `Next reminder: ${next}` : "Select time and days";
  if (next) el.innerHTML = `<strong>Next reminder:</strong> ${next}`;
}

function openAddScheduleModal() {
  const now = new Date();
  document.getElementById("add-schedule-time").value = `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`;
  document.querySelectorAll("#add-schedule-days input[data-day]").forEach((cb) => (cb.checked = true));
  updateNextReminderPreview();
  document.getElementById("add-schedule-modal").classList.remove("hidden");
}

document.getElementById("add-schedule-time").addEventListener("input", updateNextReminderPreview);
document.getElementById("add-schedule-time").addEventListener("change", updateNextReminderPreview);
document.getElementById("add-schedule-timezone").addEventListener("change", updateNextReminderPreview);
document.getElementById("add-schedule-days").addEventListener("change", updateNextReminderPreview);

document.getElementById("add-schedule-cancel").addEventListener("click", () => {
  document.getElementById("add-schedule-modal").classList.add("hidden");
});

document.getElementById("add-schedule-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const medId = document.getElementById("add-schedule-med-id").value;
  const timeInput = document.getElementById("add-schedule-time").value;
  const days = getSelectedDays();
  const checked = document.querySelectorAll("#add-schedule-days input[data-day]:checked").length;
  if (checked === 0) {
    showError("pillbox-error", "Please select at least one day.");
    return;
  }
  try {
    const timezone = document.getElementById("add-schedule-timezone")?.value || "America/New_York";
    await fetchApi(`/api/pillbox/meds/${medId}/schedules`, {
      method: "POST",
      body: JSON.stringify({
        time_of_day: timeInput,
        timezone,
        days_of_week: days,
        enabled: true,
      }),
    });
    document.getElementById("add-schedule-modal").classList.add("hidden");
    loadPillbox();
  } catch (err) {
    showError("pillbox-error", err.message);
  }
});

// --- Notifications ---
const NOTIFICATION_POLL_INTERVAL = 30000; // 30 seconds
let notificationPollTimer = null;
let countdownInterval = null;

function formatCountdown(ms) {
  if (ms <= 0) return "Now";
  const s = Math.floor(ms / 1000) % 60;
  const m = Math.floor(ms / 60000) % 60;
  const h = Math.floor(ms / 3600000) % 24;
  const d = Math.floor(ms / 86400000);
  const parts = [];
  if (d > 0) parts.push(`${d}d`);
  if (h > 0) parts.push(`${h}h`);
  parts.push(`${m}m`);
  parts.push(`${s}s`);
  return parts.join(" ");
}

function renderCountdown() {
  const listEl = document.getElementById("countdown-list");
  const emptyEl = document.getElementById("countdown-empty");
  if (!listEl || !emptyEl) return;

  const meds = cachedMeds || [];
  const items = [];
  for (const m of meds) {
    const schedules = (m.schedules || []).filter((s) => s.enabled !== false);
    for (const s of schedules) {
      const next = getNextReminderDate(s.time_of_day, s.timezone || "America/New_York", s.days_of_week || "daily");
      if (next) {
        const ms = next.date.getTime() - Date.now();
        items.push({
          medName: m.name,
          timeStr: s.time_of_day,
          displayStr: next.displayStr,
          ms,
        });
      }
    }
  }
  items.sort((a, b) => a.ms - b.ms);

  if (items.length === 0) {
    listEl.innerHTML = "";
    emptyEl.classList.remove("hidden");
    return;
  }
  emptyEl.classList.add("hidden");
  listEl.innerHTML = items
    .map(
      (it) => `
    <div class="countdown-item">
      <div class="countdown-med">${escapeHtml(it.medName)}</div>
      <div class="countdown-time">${escapeHtml(it.timeStr)} · ${escapeHtml(it.displayStr)}</div>
      <div class="countdown-timer">${formatCountdown(it.ms)}</div>
    </div>
  `
    )
    .join("");
}

function startCountdownUpdates() {
  if (countdownInterval) clearInterval(countdownInterval);
  renderCountdown();
  countdownInterval = setInterval(renderCountdown, 1000);
}

function formatNotificationTime(isoStr) {
  if (!isoStr) return "";
  const d = new Date(isoStr);
  const now = new Date();
  const diffMs = now - d;
  if (diffMs < 60000) return "Just now";
  if (diffMs < 3600000) return `${Math.floor(diffMs / 60000)}m ago`;
  if (diffMs < 86400000) return `${Math.floor(diffMs / 3600000)}h ago`;
  return d.toLocaleDateString();
}

async function loadNotifications() {
  try {
    const items = await fetchApi("/api/notifications");
    const listEl = document.getElementById("notifications-list");
    const emptyEl = document.getElementById("notifications-empty");
    if (!items || items.length === 0) {
      listEl.innerHTML = "";
      emptyEl.classList.remove("hidden");
      return;
    }
    emptyEl.classList.add("hidden");
    listEl.innerHTML = items.map((n) => {
      const isRead = !!n.read_at;
      const rowClass = isRead ? "notification-item read" : "notification-item unread";
      return `
        <div class="${rowClass}" data-id="${n.id}">
          <div class="notification-content">
            <strong>${escapeHtml(n.title)}</strong>
            <p>${escapeHtml(n.message)}</p>
            <span class="notification-time">${formatNotificationTime(n.created_at)}</span>
          </div>
          ${!isRead ? `<button class="btn btn-small btn-secondary" data-mark-read data-id="${n.id}">Mark read</button>` : ""}
        </div>
      `;
    }).join("");

    listEl.querySelectorAll("[data-mark-read]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        try {
          await fetchApi(`/api/notifications/${btn.dataset.id}/read`, { method: "PUT" });
          loadNotifications();
        } catch (err) {
          console.error(err);
        }
      });
    });
  } catch (err) {
    console.error("Failed to load notifications:", err);
  }
}

document.getElementById("mark-all-read-btn").addEventListener("click", async () => {
  try {
    await fetchApi("/api/notifications/read-all", { method: "PUT" });
    loadNotifications();
  } catch (err) {
    console.error(err);
  }
});

function startNotificationPolling() {
  if (notificationPollTimer) clearInterval(notificationPollTimer);
  notificationPollTimer = setInterval(loadNotifications, NOTIFICATION_POLL_INTERVAL);
}

// --- Init ---
initClearableInput("search-input", "search-input-clear");
initClearableInput("ai-question", "ai-question-clear");
initClearableInput("ai-med-context", "ai-med-context-clear");

populateStateSelect();

(async () => {
  const oauthUser = handleOAuthRedirectResult();
  if (oauthUser) {
    loadPillbox();
    loadProfile();
    return;
  }
  const user = await checkAuth();
  updateAuthUI(user);
  if (user) {
    loadPillbox();
    loadProfile();
  } else {
    document.getElementById("pillbox-list").innerHTML = '<p class="empty-state">Please log in to view your pillbox.</p>';
    updateProfileUI(null);
    loadWeather(null, null);
  }
})();
loadNotifications();
startNotificationPolling();
renderCountdown();
