/**
 * Pillulu Health Assistant - Frontend
 * Configure API_BASE for your backend URL (local or Render)
 */
const API_BASE = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
  ? "http://127.0.0.1:8000"
  : "";

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
      const name = m.display_name || m.brand_name || m.generic_name || m.substance_name || "Medication (name not available)";
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
        openAddScheduleModal();
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
function getSelectedDays() {
  const checks = document.querySelectorAll("#add-schedule-days input[data-day]:checked");
  const days = Array.from(checks).map((c) => c.dataset.day);
  return days.length === 7 ? "daily" : days.join(",") || "daily";
}

function computeNextReminder(timeStr, timezone, daysStr) {
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
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    let tzAbbr = "";
    try {
      tzAbbr = new Date().toLocaleTimeString("en-US", { timeZone: timezone, timeZoneName: "short" }).split(" ").pop() || timezone;
    } catch {
      tzAbbr = timezone;
    }
    if (isToday && !timePassed) {
      return `${y}-${m}-${day} ${timeStr} (${tzAbbr})`;
    }
    if (offset > 0) {
      return `${y}-${m}-${day} ${timeStr} (${tzAbbr})`;
    }
  }
  return null;
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
let lastUnreadCount = 0;

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

    // Browser notification when new unread arrives (user has granted permission)
    const unreadCount = items.filter((n) => !n.read_at).length;
    if (unreadCount > lastUnreadCount && unreadCount > 0 && "Notification" in window && Notification.permission === "granted") {
      const newest = items.find((n) => !n.read_at);
      if (newest) new Notification(newest.title, { body: newest.message });
    }
    lastUnreadCount = unreadCount;
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

document.getElementById("enable-browser-notifications-btn").addEventListener("click", async () => {
  if (!("Notification" in window)) {
    alert("Your browser does not support notifications.");
    return;
  }
  if (Notification.permission === "granted") {
    alert("Browser notifications are already enabled.");
    return;
  }
  const permission = await Notification.requestPermission();
  if (permission === "granted") {
    new Notification("Pillulu", { body: "Notifications enabled! You'll get reminders here." });
    document.getElementById("enable-browser-notifications-btn").textContent = "Notifications enabled";
  }
});

function startNotificationPolling() {
  if (notificationPollTimer) clearInterval(notificationPollTimer);
  notificationPollTimer = setInterval(loadNotifications, NOTIFICATION_POLL_INTERVAL);
}

// --- Init ---
loadPillbox();
loadNotifications();
startNotificationPolling();
