# Pillulu Health Assistant - Backend

FastAPI backend for medication search, AI Q&A, pillbox management, and in-app notifications.

## Quick Start (Local)

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env` in `backend/` (or set env vars). Keys are loaded in order: env vars → `.env` (via dotenv) → `secrets.txt` fallback.

```
OPENAI_API_KEY=sk-...
SENDGRID_API_KEY=SG....
FROM_EMAIL=your-verified-sender@domain.com
APP_BASE_URL=https://your-username.github.io/pillulu-health-assistant/
DATABASE_PATH=./data/pillulu.db
CRON_SECRET=your-random-secret-for-cron
```

Optional: `backend/secrets.txt` (one per line: `KEY=value`) as fallback when env vars are empty.

Run:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Health check: http://127.0.0.1:8000/health

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/med/search?q=...` | Search medications (OpenFDA) |
| POST | `/api/ai/ask` | AI Q&A about medication |
| GET | `/api/pillbox/meds` | List meds with schedules |
| POST | `/api/pillbox/meds` | Create med |
| PUT | `/api/pillbox/meds/{id}` | Update med |
| DELETE | `/api/pillbox/meds/{id}` | Delete med |
| POST | `/api/pillbox/meds/{id}/schedules` | Add schedule |
| GET | `/api/pillbox/meds/{id}/schedules` | List schedules |
| PUT | `/api/schedules/{id}` | Update schedule |
| DELETE | `/api/schedules/{id}` | Delete schedule |
| GET | `/api/user/email` | Get user email (for future email sync) |
| PUT | `/api/user/email` | Set user email (for future email sync) |
| GET | `/api/notifications` | List notifications |
| PUT | `/api/notifications/{id}/read` | Mark notification read |
| PUT | `/api/notifications/read-all` | Mark all read |
| POST | `/api/cron/send_reminders` | Cron: create notifications (requires CRON_SECRET) |
| POST | `/api/cron/decrement_stock` | Cron: decrement stock (optional) |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| OPENAI_API_KEY | For AI | OpenAI API key |
| SENDGRID_API_KEY | Optional | For future email sync |
| FROM_EMAIL | Optional | For future email sync |
| APP_BASE_URL | Optional | Frontend URL |
| DATABASE_PATH | Optional | Default: ./data/pillulu.db |
| CRON_SECRET | For cron | Secret for cron endpoints |

## Render Deployment

1. Create a Web Service, connect repo.
2. Build: `pip install -r requirements.txt`
3. Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add env vars in Render dashboard.
5. Ensure `backend/data` exists (Render ephemeral disk) or use Persistent Disk and set `DATABASE_PATH=/var/data/pillulu.db`.

## Cron Job (Render Cron)

Create a Cron Job that runs **every minute** (required for precise time matching):

- **URL**: `https://YOUR-SERVICE.onrender.com/api/cron/send_reminders`
- **Method**: POST
- **Header**: `X-CRON-SECRET: your-cron-secret` (must match CRON_SECRET env var)

Or send JSON body: `{"secret": "your-cron-secret"}`

## Troubleshooting: No reminders received

1. **Cron not running**: Reminders only fire when `/api/cron/send_reminders` is called. Locally, nothing calls it automatically. Use:
   ```bash
   # From project root, with CRON_SECRET from backend/.env
   ./scripts/trigger_reminders.sh http://localhost:8000 your-cron-secret
   ```
   Or: `curl -X POST http://localhost:8000/api/cron/send_reminders -H "X-CRON-SECRET: YOUR_SECRET"`

2. **Debug which schedules would match**: `GET /api/cron/debug_reminders?secret=YOUR_SECRET` shows current time per timezone and whether each schedule would fire.

3. **Time must match exactly**: Schedule time (e.g. 08:30) must equal the current minute in the schedule's timezone when cron runs. Cron must run every minute.

4. **Deployed on Render**: Ensure a Cron Job is configured and runs every minute (`* * * * *`).

## Secrets

- Never commit `.env` or API keys.
- Use Render Environment Variables for production.
- CRON_SECRET should be a long random string.
