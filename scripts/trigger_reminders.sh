#!/bin/bash
# Manually trigger send_reminders for local testing.
# Usage: ./scripts/trigger_reminders.sh [BASE_URL] [CRON_SECRET]
# Example: ./scripts/trigger_reminders.sh http://localhost:8000 your-cron-secret

BASE_URL="${1:-http://localhost:8000}"
SECRET="${2:-$CRON_SECRET}"

if [ -z "$SECRET" ]; then
  echo "Usage: $0 [BASE_URL] [CRON_SECRET]"
  echo "Or set CRON_SECRET env var. Get it from backend/.env"
  exit 1
fi

echo "Calling $BASE_URL/api/cron/send_reminders ..."
curl -s -X POST "$BASE_URL/api/cron/send_reminders" \
  -H "Content-Type: application/json" \
  -H "X-CRON-SECRET: $SECRET" \
  -d '{}' | python3 -m json.tool
