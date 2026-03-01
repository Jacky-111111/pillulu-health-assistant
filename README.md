# Pillulu Health Assistant

A web app to help users search medications, ask AI health questions, manage a personal pillbox with schedules, and receive reminder notifications.

**🌐 Live site:** [https://pillulu-health-assistant.onrender.com](https://pillulu-health-assistant.onrender.com)

**⚠️ Disclaimer:** This app is for educational purposes only. It does not provide medical advice. Always consult a doctor or pharmacist.

## Features

- **🔍 Smart Medication Search** - OpenFDA search with typeahead suggestions, fuzzy/synonym matching, and medication detail modal
- **📷 Label Scan** - Camera OCR to scan medication names from package labels
- **🧠 AI-assisted General Use** - Fallback concise "general use" summary when label data is missing
- **💊 My Pillbox** - Save meds with stock, low-stock thresholds, reminders, visual metadata, and detail modal
- **🫀 Body Insight & Case History** - Body-part based case records and history tracking for ongoing symptoms/conditions
- **🤖 Ask AI** - Ask educational medication questions with optional case-history context awareness (OpenAI; not medical advice)
- **🔔 Notifications** - In-app reminders for time-to-take and low stock
- **👤 User Profile** - Age, gender, height, weight, and location (state/city)
- **🌤️ Local Weather** - Weather widget based on profile location (Open-Meteo)
- **🔐 Auth** - Email/password auth plus Google OAuth login
- **⏰ Cron Reminders** – Server-side cron triggers reminders at scheduled times

## Project Structure

```
pillulu-health-assistant/
├── backend/          # FastAPI + SQLite
├── frontend/         # Vanilla HTML/CSS/JS
├── README.md
└── PROMPT_HISTORY.txt
```

## Run Locally

Run **backend** and **frontend** separately in local dev.

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env` in `backend/` with `OPENAI_API_KEY`, `CRON_SECRET`, etc. (see `backend/.env.example`).

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 2. Frontend

In a **new terminal**:

```bash
cd frontend
python -m http.server 8080
```

Open [http://localhost:8080](http://localhost:8080). The frontend uses `API_BASE=http://127.0.0.1:8000` when on localhost.

### Notes

- If you update DB-backed profile/pillbox fields, restart backend once to allow SQLite auto-migrations to run.
- Camera scan requires browser camera permission and works best on HTTPS or localhost.

## Deployment

- **Merged (recommended):** One Render Web Service serves both frontend and API. See `backend/README.md` for config (Root Directory empty, Build/Start from `backend/`).
- **Cron:** Render Cron Job → POST `/api/cron/send_reminders` with `X-CRON-SECRET`

See `backend/README.md` and `frontend/README.md` for details.

## Secrets

Never commit: `OPENAI_API_KEY`, `CRON_SECRET`, `.env`
