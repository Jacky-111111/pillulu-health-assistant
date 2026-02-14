# Pillulu Health Assistant

A web app to help users search medications, ask AI about dosage/info, manage a pillbox with schedules, and receive email reminders.

**⚠️ Disclaimer:** This app is for educational purposes only. It does not provide medical advice. Always consult a doctor or pharmacist.

## Project Structure

```
pillulu-health-assistant/
├── backend/          # FastAPI + SQLite
├── frontend/         # Vanilla HTML/CSS/JS
├── README.md
└── PROMPT_HISTORY.txt
```

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Set env vars: OPENAI_API_KEY, SENDGRID_API_KEY, FROM_EMAIL, CRON_SECRET
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
python -m http.server 8080
# Open http://localhost:8080
```

Update `API_BASE` in `frontend/app.js` if backend URL differs.

## Features

1. **Search Medications** – OpenFDA API
2. **Ask AI** – OpenAI Chat (dosage, info) with safety disclaimers
3. **My Pillbox** – Add meds, set stock, thresholds, schedules
4. **Email Settings** – Store email for reminders
5. **Cron Reminders** – Time-to-take and low-stock emails via `/api/cron/send_reminders`

## Deployment

- **Backend:** Render Web Service
- **Frontend:** GitHub Pages or any static host
- **Cron:** Render Cron Job → POST `/api/cron/send_reminders` with `X-CRON-SECRET`

See `backend/README.md` and `frontend/README.md` for details.

## Secrets

Never commit: `OPENAI_API_KEY`, `SENDGRID_API_KEY`, `CRON_SECRET`, `.env`
