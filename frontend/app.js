/**
 * Pillulu Health Assistant - Frontend
 * Configure API_BASE for your backend URL (local or Render)
 */
const API_BASE = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
  ? "http://127.0.0.1:8000"
  : "https://YOUR-RENDER-URL.onrender.com";

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

async function fetchApi(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

// --- Search ---
document.getElementById("search-btn").addEventListener("click", doSearch);
document.getElementById("search-input").addEventListener("keypress", (e) => {
  if (e.key === "Enter") doSearch();
});

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
    if (!data || data.length === 0) {
      resultsEl.innerHTML = '<p style="text-align:center;color:#666;">No medications found. Try different keywords.</p>';
      return;
    }
    resultsEl.innerHTML = data.map((m) => {
      const name = m.brand_name || m.generic_name || m.substance_name || "Unknown";
      return `
        <div class="med-card">
          <h4>${escapeHtml(name)}</h4>
          ${m.generic_name ? `<p>Generic: ${escapeHtml(m.generic_name)}</p>` : ""}
          ${m.manufacturer ? `<p>Manufacturer: ${escapeHtml(m.manufacturer)}</p>` : ""}
          ${m.route ? `<p>Route: ${escapeHtml(m.route)}</p>` : ""}
          ${m.warnings_snippet ? `<p>Warnings: ${escapeHtml(m.warnings_snippet.substring(0, 150))}...</p>` : ""}
          <div class="card-actions">
            <button class="btn btn-secondary btn-small" data-action="ask" data-name="${escapeHtml(name)}">Ask AI</button>
            <button class="btn btn-primary btn-small" data-action="add" data-name="${escapeHtml(name)}">Add to Pillbox</button>
          </div>
        </div>
      `;
    }).join("");

    resultsEl.querySelectorAll("[data-action]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const action = btn.dataset.action;
        const name = btn.dataset.name;
        if (action === "ask") {
          document.getElementById("ai-med-context").value = name;
          document.getElementById("ai-section").scrollIntoView({ behavior: "smooth" });
        } else if (action === "add") {
          openAddMedModal(name);
        }
      });
    });
  } catch (e) {
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
function openAddMedModal(presetName = "") {
  document.getElementById("add-med-name").value = presetName;
  document.getElementById("add-med-purpose").value = "";
  document.getElementById("add-med-stock").value = "10";
  document.getElementById("add-med-threshold").value = "5";
  document.getElementById("add-med-notes").value = "";
  document.getElementById("add-med-modal").classList.remove("hidden");
}

document.getElementById("add-med-cancel").addEventListener("click", () => {
  document.getElementById("add-med-modal").classList.add("hidden");
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
        stock_count: parseInt(document.getElementById("add-med-stock").value, 10) || 0,
        low_stock_threshold: parseInt(document.getElementById("add-med-threshold").value, 10) || 5,
      }),
    });
    document.getElementById("add-med-modal").classList.add("hidden");
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
    answerEl.classList.remove("hidden");
  } catch (err) {
    showError("ai-error", err.message || "AI service temporarily unavailable. Try again later.");
  } finally {
    document.getElementById("ai-ask-btn").disabled = false;
    document.getElementById("ai-ask-btn").textContent = "Ask";
  }
}

// --- Pillbox ---
async function loadPillbox() {
  hideError("pillbox-error");
  const listEl = document.getElementById("pillbox-list");
  const emptyEl = document.getElementById("pillbox-empty");
  listEl.innerHTML = '<p style="text-align:center;color:#666;">Loading...</p>';
  emptyEl.classList.add("hidden");

  try {
    const meds = await fetchApi("/api/pillbox/meds");
    if (!meds || meds.length === 0) {
      listEl.innerHTML = "";
      emptyEl.classList.remove("hidden");
      return;
    }
    emptyEl.classList.add("hidden");
    listEl.innerHTML = meds.map((m) => {
      const isLow = m.stock_count <= m.low_stock_threshold;
      const stockClass = isLow ? "stock-info low" : "stock-info";
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
          <h4>${escapeHtml(m.name)}</h4>
          ${m.purpose ? `<p>Purpose: ${escapeHtml(m.purpose)}</p>` : ""}
          <p class="${stockClass}">Stock: ${m.stock_count} | Alert threshold: ${m.low_stock_threshold}</p>
          ${m.dosage_notes ? `<p>Notes: ${escapeHtml(m.dosage_notes)}</p>` : ""}
          <div class="schedule-list">
            <strong>Reminder times:</strong>
            ${schedulesHtml || "<p>None</p>"}
          </div>
          <div class="card-actions">
            <button class="btn btn-secondary btn-small" data-edit-med data-id="${m.id}">Edit</button>
            <button class="btn btn-primary btn-small" data-add-sched data-id="${m.id}" data-name="${escapeHtml(m.name)}">Add time</button>
            <button class="btn btn-secondary btn-small" data-del-med data-id="${m.id}">Delete</button>
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
        document.getElementById("add-schedule-modal").classList.remove("hidden");
      });
    });
    listEl.querySelectorAll("[data-del-med]").forEach((btn) => {
      btn.addEventListener("click", () => deleteMed(parseInt(btn.dataset.id, 10)));
    });
    listEl.querySelectorAll("[data-edit-sched]").forEach((btn) => {
      btn.addEventListener("click", () => alert("Edit schedule: use API or a future version"));
    });
    listEl.querySelectorAll("[data-del-sched]").forEach((btn) => {
      btn.addEventListener("click", () => deleteSchedule(parseInt(btn.dataset.id, 10)));
    });
  } catch (err) {
    showError("pillbox-error", err.message || "Failed to load pillbox. Check your connection.");
    listEl.innerHTML = "";
  }
}

async function deleteMed(id) {
  if (!confirm("Delete this medication?")) return;
  try {
    await fetchApi(`/api/pillbox/meds/${id}`, { method: "DELETE" });
    loadPillbox();
  } catch (err) {
    showError("pillbox-error", err.message);
  }
}

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
document.getElementById("add-schedule-cancel").addEventListener("click", () => {
  document.getElementById("add-schedule-modal").classList.add("hidden");
});

document.getElementById("add-schedule-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const medId = document.getElementById("add-schedule-med-id").value;
  const timeInput = document.getElementById("add-schedule-time").value;
  const days = document.getElementById("add-schedule-days").value.trim() || "daily";
  try {
    const timezone = document.getElementById("add-schedule-timezone")?.value || "Asia/Shanghai";
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

// --- Email ---
async function loadUserEmail() {
  try {
    const data = await fetchApi("/api/user/email");
    document.getElementById("user-email").value = data.email || "";
  } catch {
    // ignore
  }
}

document.getElementById("save-email-btn").addEventListener("click", async () => {
  const email = document.getElementById("user-email").value.trim();
  hideError("email-error");
  document.getElementById("email-success").classList.add("hidden");
  if (!email) {
    showError("email-error", "Please enter your email address");
    return;
  }
  try {
    await fetchApi("/api/user/email", {
      method: "PUT",
      body: JSON.stringify({ email }),
    });
    showSuccess("email-success");
  } catch (err) {
    showError("email-error", err.message);
  }
});

// --- Init ---
loadPillbox();
loadUserEmail();
