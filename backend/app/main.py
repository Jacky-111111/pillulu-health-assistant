"""Pillulu Health Assistant - FastAPI backend."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.config import JWT_SECRET
from app.routers import med_search, ai, pillbox, cron, notifications, auth, user_profile, weather


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Pillulu Health Assistant API",
    description="Medication search, AI Q&A, pillbox management, and email reminders.",
    lifespan=lifespan,
)

# CORS for GitHub Pages / static hosting
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key=JWT_SECRET, same_site="lax", https_only=False)

app.include_router(med_search.router)
app.include_router(ai.router)
app.include_router(pillbox.router)
app.include_router(notifications.router)
app.include_router(cron.router)
app.include_router(auth.router)
app.include_router(user_profile.router)
app.include_router(weather.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "pillulu-health-assistant"}


# Serve frontend (merged deployment). Must be last so API routes take precedence.
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="static")
