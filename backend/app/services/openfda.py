"""OpenFDA API client for medication search."""
import httpx
from typing import List

from app.schemas import MedSearchResult

OPENFDA_URL = "https://api.fda.gov/drug/label.json"


async def search_medications(query: str, limit: int = 10) -> List[MedSearchResult]:
    """
    Search OpenFDA for medications. Returns list of MedSearchResult.
    Raises httpx.HTTPError on network/API errors.
    """
    # OpenFDA: use simple search (complex OR queries cause 500 errors)
    search_term = query.strip().replace('"', "").replace("+", " ")
    params = {"search": search_term, "limit": limit}
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(OPENFDA_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    results = []
    for item in data.get("results", []):
        openfda = item.get("openfda", {})
        brand = openfda.get("brand_name", [None])[0] if openfda.get("brand_name") else None
        generic = openfda.get("generic_name", [None])[0] if openfda.get("generic_name") else None
        manufacturer = openfda.get("manufacturer_name", [None])[0] if openfda.get("manufacturer_name") else None
        route = openfda.get("route", [None])[0] if openfda.get("route") else None
        substance = openfda.get("substance_name", [None])[0] if openfda.get("substance_name") else None

        warnings = item.get("warnings", [])
        warnings_snippet = warnings[0][:300] if warnings else None

        results.append(
            MedSearchResult(
                brand_name=brand,
                generic_name=generic,
                manufacturer=manufacturer,
                route=route,
                substance_name=substance,
                warnings_snippet=warnings_snippet,
            )
        )
    return results
