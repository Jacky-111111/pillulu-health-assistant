"""Cron-friendly endpoints for reminders and stock decrement."""
from datetime import datetime, date
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Med, Schedule, User
from app.config import CRON_SECRET
from app.services.email import send_time_to_take_reminder, send_low_stock_reminder

router = APIRouter(prefix="/api/cron", tags=["cron"])


def verify_cron_secret(token: str | None):
    """Verify CRON_SECRET from body or header."""
    if not CRON_SECRET or token != CRON_SECRET:
        raise HTTPException(status_code=403, detail="Invalid or missing cron secret")


def _now_in_tz(tz_name: str) -> tuple[datetime, str, str]:
    """Return (now, current_hm, today_weekday) in given timezone."""
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = ZoneInfo("America/New_York")
    now = datetime.now(tz)
    return now, now.strftime("%H:%M"), now.strftime("%a").lower()


@router.post("/send_reminders")
async def send_reminders(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Check due schedules and low stock, send emails.
    Requires X-CRON-SECRET header or body { "secret": "..." }.
    """
    body = {}
    try:
        body = await request.json()
    except Exception:
        pass
    secret = body.get("secret") or request.headers.get("X-CRON-SECRET")
    verify_cron_secret(secret)

    user = db.query(User).first()
    if not user or not user.email:
        return {"sent": 0, "message": "No user email configured"}

    today_date = date.today()
    today_date = date.today()
    sent_count = 0

    # Time-to-take reminders (evaluate each schedule in its timezone)
    schedules = db.query(Schedule).filter(Schedule.enabled == True).all()
    for s in schedules:
        now_tz, current_hm, today_weekday = _now_in_tz(s.timezone or "America/New_York")
        if s.time_of_day != current_hm:
            continue
        if s.days_of_week != "daily":
            days = [d.strip().lower()[:3] for d in s.days_of_week.split(",")]
            if today_weekday not in days:
                continue
        # Dedupe: don't send if we already sent in last 3 minutes
        if s.last_reminder_sent_at and (now - s.last_reminder_sent_at).total_seconds() < 180:
            continue

        if send_time_to_take_reminder(user.email, s.med.name, s.time_of_day):
            s.last_reminder_sent_at = now
            sent_count += 1
            # Decrement stock on reminder (MVP assumption)
            if s.med.stock_count > 0:
                s.med.stock_count -= 1

    db.commit()

    # Low stock reminders (dedupe daily)
    meds_low = db.query(Med).filter(Med.stock_count <= Med.low_stock_threshold).all()
    for med in meds_low:
        if med.last_low_stock_sent_at == today_date:
            continue
        if send_low_stock_reminder(user.email, med.name, med.stock_count, med.low_stock_threshold):
            med.last_low_stock_sent_at = today_date
            sent_count += 1

    db.commit()

    return {"sent": sent_count, "message": "Reminders processed"}


@router.post("/decrement_stock")
async def decrement_stock(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Optional: manually trigger stock decrement (e.g. when reminder fires).
    For MVP, decrement is done in send_reminders. This endpoint can be used for testing.
    """
    body = {}
    try:
        body = await request.json()
    except Exception:
        pass
    secret = body.get("secret") or request.headers.get("X-CRON-SECRET")
    verify_cron_secret(secret)

    med_id = body.get("med_id")
    if not med_id:
        return {"ok": False, "message": "med_id required"}

    med = db.query(Med).filter(Med.id == int(med_id)).first()
    if not med:
        return {"ok": False, "message": "Medication not found"}

    if med.stock_count > 0:
        med.stock_count -= 1
    db.commit()
    return {"ok": True, "stock_count": med.stock_count}
