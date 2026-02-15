"""Weather proxy - fetches from Open-Meteo (no API key required)."""
import httpx
from fastapi import APIRouter, Depends, HTTPException

from app.routers.auth import get_current_user
from app.models import User
from app.data.us_locations import get_coords, US_STATES_CITIES

router = APIRouter(prefix="/api", tags=["weather"])


@router.get("/weather/states")
def list_states():
    """List US states for location selection. No auth required."""
    return {"states": sorted(US_STATES_CITIES.keys())}


@router.get("/weather/cities/{state}")
def list_cities(state: str):
    """List cities for a state. No auth required."""
    cities = US_STATES_CITIES.get(state)
    if not cities:
        raise HTTPException(status_code=400, detail="Unknown state")
    return {"cities": [c[0] for c in cities]}


@router.get("/weather")
async def get_weather(state: str, city: str, user: User = Depends(get_current_user)):
    """Get current weather + 3-day forecast. Requires auth."""
    coords = get_coords(state, city)
    if not coords:
        raise HTTPException(status_code=400, detail="Unknown state/city")
    lat, lon = coords
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&current_weather=true"
        f"&daily=temperature_2m_max,temperature_2m_min,weathercode"
        f"&forecast_days=4"
        f"&timezone=auto"
    )
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()
    if "current_weather" not in data or "daily" not in data:
        raise HTTPException(status_code=502, detail="Weather service unavailable")
    daily = data["daily"]
    # First 4 days: today + 3 forecast days
    forecast = []
    for i in range(min(4, len(daily["time"]))):
        forecast.append({
            "date": daily["time"][i],
            "temp_max": daily["temperature_2m_max"][i],
            "temp_min": daily["temperature_2m_min"][i],
            "weathercode": daily["weathercode"][i],
        })
    return {
        "current_weather": data["current_weather"],
        "forecast": forecast,
    }
