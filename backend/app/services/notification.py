"""In-app notification service. Same content as email templates for future sync."""
from datetime import datetime

from app.models import Notification


def create_time_to_take_notification(db, med_name: str, time_str: str) -> Notification:
    """Create 'time to take' reminder notification. Caller must commit."""
    title = f"⏰ Time to take {med_name}"
    message = f"It's {time_str} — time to take {med_name}. Please take your medication as scheduled."
    n = Notification(type="time_to_take", title=title, message=message)
    db.add(n)
    db.flush()  # Get ID without committing
    return n


def create_low_stock_notification(db, med_name: str, stock_count: int, threshold: int) -> Notification:
    """Create low stock reminder notification. Caller must commit."""
    title = f"⚠️ Low stock - {med_name}"
    message = f"{med_name} is running low. Current stock: {stock_count}, alert threshold: {threshold}. Please restock soon."
    n = Notification(type="low_stock", title=title, message=message)
    db.add(n)
    db.flush()
    return n
