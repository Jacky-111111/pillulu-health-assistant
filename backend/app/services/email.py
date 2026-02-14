"""SendGrid email service for reminders."""
import os
from typing import Optional

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from app.config import SENDGRID_API_KEY, FROM_EMAIL, APP_BASE_URL


def send_email(to_email: str, subject: str, html_content: str, plain_content: str) -> bool:
    """Send email via SendGrid. Returns True on success."""
    if not SENDGRID_API_KEY or not FROM_EMAIL:
        return False
    try:
        message = Mail(
            from_email=FROM_EMAIL,
            to_emails=to_email,
            subject=subject,
            html_content=html_content,
            plain_text_content=plain_content,
        )
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)
        return True
    except Exception:
        return False


def send_time_to_take_reminder(to_email: str, med_name: str, time_str: str) -> bool:
    """Send 'time to take' reminder email."""
    subject = f"⏰ Reminder: Time to take {med_name}"
    plain = f"Hello!\n\nIt's {time_str} — time to take {med_name}.\n\nPlease take your medication as scheduled.\n\nView My Pillbox: {APP_BASE_URL}\n\n---\nPillulu Health Assistant (This reminder is for reference only, not medical advice)"
    html = f"""
    <p>Hello!</p>
    <p><strong>It's {time_str} — time to take {med_name}.</strong></p>
    <p>Please take your medication as scheduled.</p>
    <p><a href="{APP_BASE_URL}">View My Pillbox</a></p>
    <hr>
    <p style="font-size:12px;color:#666;">Pillulu Health Assistant — This reminder is for reference only, not medical advice</p>
    """
    return send_email(to_email, subject, html, plain)


def send_low_stock_reminder(to_email: str, med_name: str, stock_count: int, threshold: int) -> bool:
    """Send low stock reminder email."""
    subject = f"⚠️ Low stock alert - {med_name}"
    plain = f"Hello!\n\n{med_name} is running low.\nCurrent stock: {stock_count}\nAlert threshold: {threshold}\n\nPlease restock soon.\n\nView My Pillbox: {APP_BASE_URL}\n\n---\nPillulu Health Assistant"
    html = f"""
    <p>Hello!</p>
    <p><strong>{med_name} is running low</strong></p>
    <p>Current stock: <strong>{stock_count}</strong></p>
    <p>Alert threshold: {threshold}</p>
    <p>Please restock soon.</p>
    <p><a href="{APP_BASE_URL}">View My Pillbox</a></p>
    <hr>
    <p style="font-size:12px;color:#666;">Pillulu Health Assistant</p>
    """
    return send_email(to_email, subject, html, plain)
