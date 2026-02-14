"""Application configuration from environment variables."""
import os
from pathlib import Path

# Database
DATABASE_PATH = os.getenv("DATABASE_PATH", "./data/pillulu.db")
DB_DIR = str(Path(DATABASE_PATH).parent)

# API Keys (required for full functionality)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "")
APP_BASE_URL = os.getenv("APP_BASE_URL", "https://your-username.github.io/pillulu-health-assistant/")
CRON_SECRET = os.getenv("CRON_SECRET", "")
