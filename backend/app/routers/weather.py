"""Weather proxy - fetches from Open-Meteo (no API key required)."""
import httpx
from fastapi import APIRouter, Depends, HTTPException

from app.routers.auth import get_current_user
from app.models import User

router = APIRouter(prefix="/api", tags=["weather"])

# US state coordinates (capital/major city)
US_COORDS = {
    "Alabama": (32.3668, -86.3000),
    "Alaska": (58.3019, -134.4197),
    "Arizona": (33.4484, -112.0740),
    "Arkansas": (34.7465, -92.2896),
    "California": (37.7749, -122.4194),
    "Colorado": (39.7392, -104.9903),
    "Connecticut": (41.7658, -72.6734),
    "Delaware": (38.9108, -75.5277),
    "Florida": (25.7617, -80.1918),
    "Georgia": (33.7490, -84.3880),
    "Hawaii": (21.3099, -157.8581),
    "Idaho": (43.6150, -116.2023),
    "Illinois": (41.8781, -87.6298),
    "Indiana": (39.7684, -86.1581),
    "Iowa": (41.5868, -93.6250),
    "Kansas": (39.0473, -95.6752),
    "Kentucky": (38.2527, -85.7585),
    "Louisiana": (29.9511, -90.0715),
    "Maine": (43.6591, -70.2568),
    "Maryland": (39.2904, -76.6122),
    "Massachusetts": (42.3601, -71.0589),
    "Michigan": (42.3314, -83.0458),
    "Minnesota": (44.9778, -93.2650),
    "Mississippi": (32.2988, -90.1848),
    "Missouri": (38.6270, -90.1994),
    "Montana": (46.5891, -112.0391),
    "Nebraska": (40.8086, -96.6783),
    "Nevada": (36.1699, -115.1398),
    "New Hampshire": (43.1939, -71.5724),
    "New Jersey": (40.7128, -74.0060),
    "New Mexico": (35.0844, -106.6504),
    "New York": (40.7128, -74.0060),
    "North Carolina": (35.2271, -80.8431),
    "North Dakota": (46.8772, -96.7898),
    "Ohio": (39.9612, -82.9988),
    "Oklahoma": (35.4676, -97.5164),
    "Oregon": (45.5152, -122.6784),
    "Pennsylvania": (39.9526, -75.1652),
    "Rhode Island": (41.8240, -71.4128),
    "South Carolina": (34.0522, -81.0320),
    "South Dakota": (43.5446, -96.7311),
    "Tennessee": (36.1627, -86.7816),
    "Texas": (29.7604, -95.3698),
    "Utah": (40.7608, -111.8910),
    "Vermont": (44.2601, -72.5754),
    "Virginia": (37.5407, -77.4360),
    "Washington": (47.6062, -122.3321),
    "West Virginia": (38.3498, -81.6326),
    "Wisconsin": (43.0731, -89.4012),
    "Wyoming": (41.1399, -104.8202),
    "District of Columbia": (38.9072, -77.0369),
}


@router.get("/weather/{region}")
async def get_weather(region: str, user: User = Depends(get_current_user)):
    """Get weather for a US region. Requires auth."""
    coords = US_COORDS.get(region)
    if not coords:
        raise HTTPException(status_code=400, detail="Unknown region")
    lat, lon = coords
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()
    if "current_weather" not in data:
        raise HTTPException(status_code=502, detail="Weather service unavailable")
    return data["current_weather"]
