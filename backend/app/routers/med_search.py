"""Medication search via OpenFDA."""
import httpx
from fastapi import APIRouter, HTTPException

from app.services.openfda import search_medications
from app.schemas import MedSearchResult

router = APIRouter(prefix="/api/med", tags=["med-search"])


@router.get("/search", response_model=list[MedSearchResult])
async def search_meds(q: str = ""):
    """Search medications via OpenFDA. Query param 'q' required."""
    query = (q or "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required and cannot be empty")
    try:
        results = await search_medications(query, limit=10)
        return results
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"OpenFDA API error: {str(e)}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"OpenFDA request failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Medication search failed: {str(e)}")
