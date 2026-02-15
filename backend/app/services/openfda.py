"""OpenFDA API client for medication search.

Searches ONLY in drug name fields (brand, generic, substance) - no full-text.
Supports typo tolerance via wildcard fallback.
"""
import re
import httpx
from typing import List, Optional

from app.schemas import MedSearchResult

OPENFDA_URL = "https://api.fda.gov/drug/label.json"


def _build_term(query: str, prefix_len: Optional[int] = None) -> str:
    """Build search term. prefix_len: use first N chars + * for typo tolerance."""
    q = query.strip().replace('"', "").replace("+", " ").replace("*", "")
    if not q:
        return ""
    if prefix_len is not None and prefix_len >= 3 and prefix_len < len(q):
        return q[:prefix_len] + "*"
    return q


def _display_name(brand: Optional[str], generic: Optional[str], substance: Optional[str]) -> str:
    """Best display name from openfda only - no fallback to label text."""
    if brand:
        return brand.strip()
    if generic:
        return generic.strip()
    if substance:
        return substance.strip()
    return ""


async def _fetch_one_field(
    field: str, term: str, limit: int, client: httpx.AsyncClient
) -> List[dict]:
    """Fetch from OpenFDA for a single name field. OR queries cause 500, so we search one field at a time."""
    params = {"search": f"openfda.{field}:{term}", "limit": limit}
    resp = await client.get(OPENFDA_URL, params=params)
    if resp.status_code == 404:
        return []  # OpenFDA returns 404 when no results
    resp.raise_for_status()
    data = resp.json()
    return data.get("results", [])


async def search_medications(query: str, limit: int = 10) -> List[MedSearchResult]:
    """
    Search OpenFDA for medications by name only (brand, generic, substance).
    No full-text search. Typo-tolerant via wildcard fallback.
    """
    q = query.strip()
    if not q:
        return []

    seen_names: set[str] = set()
    results: List[MedSearchResult] = []

    attempts: List[Optional[int]] = [None]
    if len(q) >= 5:
        attempts.extend([len(q) - 1, len(q) - 2])
    elif len(q) >= 4:
        attempts.append(len(q) - 1)

    async with httpx.AsyncClient(timeout=15.0) as client:
        for prefix_len in attempts:
            term = _build_term(q, prefix_len=prefix_len)
            if not term:
                break
            all_items: List[dict] = []
            for field in ["generic_name", "brand_name", "substance_name"]:
                try:
                    items = await _fetch_one_field(field, term, limit * 2, client)
                    all_items.extend(items)
                except Exception:
                    if prefix_len is not None:
                        break
                    raise

            for item in all_items:
                openfda = item.get("openfda", {})
                brand = openfda.get("brand_name", [None])[0] if openfda.get("brand_name") else None
                generic = openfda.get("generic_name", [None])[0] if openfda.get("generic_name") else None
                substance = openfda.get("substance_name", [None])[0] if openfda.get("substance_name") else None
                manufacturer = openfda.get("manufacturer_name", [None])[0] if openfda.get("manufacturer_name") else None
                route = openfda.get("route", [None])[0] if openfda.get("route") else None

                display_name = _display_name(brand, generic, substance)
                if not display_name:
                    continue
                if display_name in seen_names:
                    continue
                seen_names.add(display_name)

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
                        display_name=display_name,
                    )
                )
                if len(results) >= limit:
                    break

            if len(results) >= limit:
                break

    return results[:limit]
