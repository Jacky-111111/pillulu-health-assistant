"""Cron-friendly endpoints for reminders and stock decrement."""
from datetime import datetime, date
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Med, Schedule
from app.config import CRON_SECRET
from app.services.notification import create_time_to_take_notification, create_low_stock_notification

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


def _seconds_since(last_dt: datetime | None, now_tz: datetime) -> float:
    """Seconds between last_dt and now_tz. Handles naive datetime from SQLite."""
    if not last_dt:
        return float("inf")
    if last_dt.tzinfo is None:
        last_dt = last_dt.replace(tzinfo=now_tz.tzinfo)
    return (now_tz - last_dt).total_seconds()


@router.get("/debug_reminders")
def debug_reminders(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Debug endpoint: show which schedules would match right now.
    Helps diagnose why reminders aren't firing. Pass ?secret=YOUR_CRON_SECRET
    """
    secret = request.query_params.get("secret") or request.headers.get("X-CRON-SECRET")
    if CRON_SECRET and secret != CRON_SECRET:
        raise HTTPException(status_code=403, detail="Invalid or missing cron secret")

    schedules = db.query(Schedule).filter(Schedule.enabled == True).all()
    results = []
    for s in schedules:
        now_tz, current_hm, today_weekday = _now_in_tz(s.timezone or "America/New_York")
        time_match = s.time_of_day == current_hm
        days_match = True
        if s.days_of_week != "daily":
            days = [d.strip().lower()[:3] for d in s.days_of_week.split(",")]
            days_match = today_weekday in days
        dedupe_ok = _seconds_since(s.last_reminder_sent_at, now_tz) >= 180
        would_fire = time_match and days_match and dedupe_ok
        results.append({
            "med_name": s.med.name,
            "time_of_day": s.time_of_day,
            "timezone": s.timezone,
            "days_of_week": s.days_of_week,
            "current_hm_in_tz": current_hm,
            "today_weekday": today_weekday,
            "time_match": time_match,
            "days_match": days_match,
            "dedupe_ok": dedupe_ok,
            "would_fire": would_fire,
        })
    now_ny, hm_ny, wd_ny = _now_in_tz("America/New_York")
    return {
        "server_time_utc": datetime.utcnow().isoformat() + "Z",
        "ny_time": now_ny.isoformat(),
        "ny_hm": hm_ny,
        "ny_weekday": wd_ny,
        "schedules": results,
        "hint": "Cron must POST /api/cron/send_reminders every minute. Use: curl -X POST .../api/cron/send_reminders -H 'X-CRON-SECRET: YOUR_SECRET'",
    }


@router.post("/send_reminders")
async def send_reminders(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Check due schedules and low stock, create in-app notifications.
    Requires X-CRON-SECRET header or body { "secret": "..." }.
    """
    body = {}
    try:
        body = await request.json()
    except Exception:
        pass
    secret = body.get("secret") or request.headers.get("X-CRON-SECRET")
    verify_cron_secret(secret)

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
        if _seconds_since(s.last_reminder_sent_at, now_tz) < 180:
            continue

        create_time_to_take_notification(db, s.med.name, s.time_of_day)
        s.last_reminder_sent_at = now_tz
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
        create_low_stock_notification(db, med.name, med.stock_count, med.low_stock_threshold)
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
