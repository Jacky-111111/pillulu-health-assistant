"""OpenFDA API client for medication search."""
import re
import httpx
from typing import List, Optional

from app.schemas import MedSearchResult

OPENFDA_URL = "https://api.fda.gov/drug/label.json"


def _extract_display_name(
    brand: Optional[str],
    generic: Optional[str],
    substance: Optional[str],
    item: dict,
) -> str:
    """Derive best available name from openfda or fallback fields."""
    if brand:
        return brand.strip()
    if generic:
        return generic.strip()
    if substance:
        return substance.strip()

    # Fallback: extract from active_ingredient (e.g. "Active ingredient... Ibuprofen 200 mg")
    active = item.get("active_ingredient") or []
    if active:
        text = active[0] if isinstance(active[0], str) else str(active[0])
        # Try to extract drug name before "XXX mg/mcg/g"
        match = re.search(r"([A-Za-z][A-Za-z\s\-]+?)\s+\d+\s*(?:mg|mcg|g|mL)\b", text, re.I)
        if match:
            name = match.group(1).strip().rstrip(",")
            if 2 < len(name) < 80:
                return name
        # Fallback: text after ")" (e.g. after "in each tablet)")
        match = re.search(r"\)\s*([A-Za-z][A-Za-z\s\-,]+?)(?:\s+\d|$)", text)
        if match:
            name = match.group(1).strip().rstrip(",")
            if 2 < len(name) < 80:
                return name
        # Last resort: strip common prefixes, take first 60 chars
        cleaned = re.sub(r"^(?:Active ingredient|in each).*?[):]\s*", "", text, flags=re.I)
        if len(cleaned) > 3:
            return cleaned[:60].strip()

    # Fallback: purpose (e.g. "Purpose Pain reliever/fever reducer")
    purpose = item.get("purpose") or []
    if purpose:
        text = purpose[0] if isinstance(purpose[0], str) else str(purpose[0])
        cleaned = re.sub(r"^Purpose[s]?\s*", "", text, flags=re.I).strip()
        if cleaned and len(cleaned) < 80:
            return cleaned[:60]

    # Fallback: first line of indications_and_usage
    indications = item.get("indications_and_usage") or []
    if indications:
        text = indications[0] if isinstance(indications[0], str) else str(indications[0])
        if len(text) > 5:
            return text[:60].strip()

    return ""


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

        display_name = _extract_display_name(brand, generic, substance, item)

        results.append(
            MedSearchResult(
                brand_name=brand,
                generic_name=generic,
                manufacturer=manufacturer,
                route=route,
                substance_name=substance,
                warnings_snippet=warnings_snippet,
                display_name=display_name or None,
            )
        )
    return results
