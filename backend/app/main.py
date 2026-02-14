"""Pillulu Health Assistant - FastAPI backend."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import med_search, ai, pillbox, cron, notifications


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

app.include_router(med_search.router)
app.include_router(ai.router)
app.include_router(pillbox.router)
app.include_router(notifications.router)
app.include_router(cron.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "pillulu-health-assistant"}
