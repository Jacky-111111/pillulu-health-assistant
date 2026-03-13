"""Resend email service for reminders."""
import httpx

from app.config import RESEND_API_KEY, FROM_EMAIL, APP_BASE_URL


def send_email(to_email: str, subject: str, html_content: str, plain_content: str) -> bool:
    """Send email via Resend. Returns True on success."""
    if not RESEND_API_KEY or not FROM_EMAIL or not to_email:
        return False
    try:
        response = httpx.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": FROM_EMAIL,
                "to": [to_email],
                "subject": subject,
                "html": html_content,
                "text": plain_content,
            },
            timeout=12.0,
        )
        return 200 <= response.status_code < 300
    except Exception:
        return False


def send_time_to_take_reminder(to_email: str, med_name: str, time_str: str) -> bool:
    """Send 'time to take' reminder email."""
    subject = f"Medication Reminder: {med_name} at {time_str}"
    plain = (
        "Hello,\n\n"
        "This is your medication reminder.\n\n"
        f"What to take: {med_name}\n"
        f"When to take: {time_str}\n\n"
        "Please take your medication as scheduled.\n\n"
        f"View My Pillbox: {APP_BASE_URL}\n\n"
        "Best regards,\n"
        "Pillulu Health Assistant\n\n"
        "For reference only. This is not medical advice."
    )
    html = f"""
    <div style="margin:0;padding:24px;background:#f4f7fb;font-family:Arial,sans-serif;color:#1f2937;">
      <div style="max-width:560px;margin:0 auto;background:#ffffff;border:1px solid #e5e7eb;border-radius:12px;overflow:hidden;">
        <div style="background:#2563eb;padding:16px 20px;">
          <h2 style="margin:0;font-size:20px;line-height:1.3;color:#ffffff;">Medication Reminder</h2>
        </div>
        <div style="padding:20px;">
          <p style="margin:0 0 14px 0;font-size:15px;">Hello,</p>
          <p style="margin:0 0 16px 0;font-size:15px;">This is a reminder for your scheduled medication.</p>

          <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:14px 16px;margin:0 0 18px 0;">
            <p style="margin:0 0 8px 0;font-size:15px;"><strong>What to take:</strong> {med_name}</p>
            <p style="margin:0;font-size:15px;"><strong>When to take:</strong> {time_str}</p>
          </div>

          <p style="margin:0 0 18px 0;font-size:15px;">Please take your medication as scheduled.</p>
          <a href="{APP_BASE_URL}" style="display:inline-block;background:#2563eb;color:#ffffff;text-decoration:none;padding:10px 16px;border-radius:8px;font-weight:600;">View My Pillbox</a>

          <p style="margin:22px 0 6px 0;font-size:14px;color:#4b5563;">Best regards,<br>Pillulu Health Assistant</p>
          <p style="margin:0;font-size:12px;color:#6b7280;">For reference only. This is not medical advice.</p>
        </div>
      </div>
    </div>
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
