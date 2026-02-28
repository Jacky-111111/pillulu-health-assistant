"""Application configuration from environment variables and optional local file."""
import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env into os.environ (for local dev)
load_dotenv()


def _get_secret(key: str, default: str = "") -> str:
    """Get secret: try env var first, then optional secrets.txt fallback."""
    value = os.getenv(key, "").strip()
    if value:
        return value
    # Fallback: try secrets.txt (local dev, one key per line: KEY=value)
    try:
        secrets_path = Path(__file__).parent.parent / "secrets.txt"
        if secrets_path.exists():
            with open(secrets_path) as f:
                for line in f:
                    if line.strip().startswith(f"{key}="):
                        return line.split("=", 1)[1].strip()
    except (FileNotFoundError, PermissionError):
        pass
    return default


# Database
DATABASE_PATH = os.getenv("DATABASE_PATH", "./data/pillulu.db")
DB_DIR = str(Path(DATABASE_PATH).parent)

# API Keys - works with .env, Render env vars, or secrets.txt
OPENAI_API_KEY = _get_secret("OPENAI_API_KEY")
SENDGRID_API_KEY = _get_secret("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL", "")
APP_BASE_URL = os.getenv("APP_BASE_URL", "https://your-username.github.io/pillulu-health-assistant/")
CRON_SECRET = _get_secret("CRON_SECRET")
JWT_SECRET = _get_secret("JWT_SECRET") or "dev-secret-change-in-production"

# OAuth / OIDC
OAUTH_FRONTEND_BASE_URL = os.getenv("OAUTH_FRONTEND_BASE_URL", "").strip()
OAUTH_BACKEND_BASE_URL = os.getenv("OAUTH_BACKEND_BASE_URL", "").strip()

GOOGLE_OIDC_DISCOVERY_URL = os.getenv(
    "GOOGLE_OIDC_DISCOVERY_URL",
    "https://accounts.google.com/.well-known/openid-configuration",
).strip()
GOOGLE_CLIENT_ID = _get_secret("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = _get_secret("GOOGLE_CLIENT_SECRET")
