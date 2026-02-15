# Pillulu Health Assistant

A web app to help users search medications, ask AI about dosage/info, manage a pillbox with schedules, and receive in-app notifications for reminders.

**🌐 Live site:** [https://pillulu-health-assistant.onrender.com](https://pillulu-health-assistant.onrender.com)

**⚠️ Disclaimer:** This app is for educational purposes only. It does not provide medical advice. Always consult a doctor or pharmacist.

## Features

- **🔍 Search Medications** – Search by drug name via OpenFDA API
- **🤖 Ask AI** – Ask about dosage, usage, interactions (OpenAI; for reference only)
- **💊 My Pillbox** – Add meds, set stock, low-stock thresholds, and schedules
- **🔔 Notifications** – In-app reminders for time-to-take and low stock (browser notifications optional)
- **👤 User Profile** – Age, height, weight, location (region/state/city)
- **🌤️ Local Weather** – Weather widget based on your profile region (Open-Meteo)
- **🔐 Auth** – Register, login, logout
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

You need to run **backend** and **frontend** separately. Activate the backend venv before starting the server.

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

## Deployment

- **Merged (recommended):** One Render Web Service serves both frontend and API. See `backend/README.md` for config (Root Directory empty, Build/Start from `backend/`).
- **Cron:** Render Cron Job → POST `/api/cron/send_reminders` with `X-CRON-SECRET`

See `backend/README.md` and `frontend/README.md` for details.

## Secrets

Never commit: `OPENAI_API_KEY`, `CRON_SECRET`, `.env`
