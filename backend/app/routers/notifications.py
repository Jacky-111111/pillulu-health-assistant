"""Notifications API for in-app reminders."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Notification
from app.schemas import NotificationResponse

router = APIRouter(prefix="/api", tags=["notifications"])


@router.get("/notifications", response_model=list[NotificationResponse])
def list_notifications(limit: int = 50, db: Session = Depends(get_db)):
    """List notifications, newest first."""
    items = db.query(Notification).order_by(Notification.created_at.desc()).limit(limit).all()
    return items


@router.put("/notifications/{id}/read")
def mark_read(id: int, db: Session = Depends(get_db)):
    """Mark a notification as read."""
    from datetime import datetime
    n = db.query(Notification).filter(Notification.id == id).first()
    if n:
        n.read_at = datetime.utcnow()
        db.commit()
    return {"ok": True}


@router.put("/notifications/read-all")
def mark_all_read(db: Session = Depends(get_db)):
    """Mark all notifications as read."""
    from datetime import datetime
    for n in db.query(Notification).filter(Notification.read_at.is_(None)).all():
        n.read_at = datetime.utcnow()
    db.commit()
    return {"ok": True}
