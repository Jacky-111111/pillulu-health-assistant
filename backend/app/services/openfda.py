"""OpenFDA + RxNav medication search and visual enrichment."""
import asyncio
import re
import time
from typing import Any, Dict, List, Optional

import httpx

from app.schemas import MedSearchResult

OPENFDA_URL = "https://api.fda.gov/drug/label.json"
RXNAV_APPROX_URL = "https://rxnav.nlm.nih.gov/REST/Prescribe/approximateTerm.json"
RXNAV_RXCUI_URL = "https://rxnav.nlm.nih.gov/REST/rxcui.json"
RXIMAGE_URL = "https://rximage.nlm.nih.gov/api/rximage/1/rxnav"
RXNAV_NDC_PROPS_URL = "https://rxnav.nlm.nih.gov/REST/ndcproperties.json"

_SYNONYM_GROUPS = {
    "ibuprofen": ["advil", "motrin", "midol ib"],
    "acetaminophen": ["tylenol", "paracetamol"],
    "naproxen": ["aleve"],
    "loratadine": ["claritin"],
    "cetirizine": ["zyrtec"],
    "fexofenadine": ["allegra"],
    "diphenhydramine": ["benadryl"],
    "omeprazole": ["prilosec"],
    "famotidine": ["pepcid"],
    "loperamide": ["imodium"],
    "dextromethorphan": ["delsym", "robitussin dm"],
    "guaifenesin": ["mucinex"],
}

_ALIAS_TO_CANONICAL: Dict[str, str] = {}
for _canonical, _aliases in _SYNONYM_GROUPS.items():
    _ALIAS_TO_CANONICAL[_canonical] = _canonical
    for _alias in _aliases:
        _ALIAS_TO_CANONICAL[_alias] = _canonical

_SUGGEST_CACHE: Dict[str, tuple[float, List[str]]] = {}
_SUGGEST_CACHE_TTL_SECONDS = 180.0
_SUGGEST_CACHE_MAX_ENTRIES = 400


def _normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def _build_term(query: str, prefix_len: Optional[int] = None) -> str:
    q = query.strip().replace('"', "").replace("+", " ").replace("*", "")
    if not q:
        return ""
    if prefix_len is not None and prefix_len >= 3 and prefix_len < len(q):
        return q[:prefix_len] + "*"
    return q


def _get_first_str(values: Any) -> Optional[str]:
    if isinstance(values, list) and values:
        value = values[0]
    else:
        value = values
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _display_name(brand: Optional[str], generic: Optional[str], substance: Optional[str]) -> str:
    if brand:
        return brand.strip()
    if generic:
        return generic.strip()
    if substance:
        return substance.strip()
    return ""


def _candidate_attempts(term: str) -> List[Optional[int]]:
    attempts: List[Optional[int]] = [None]
    if len(term) >= 5:
        attempts.extend([len(term) - 1, len(term) - 2])
    elif len(term) >= 4:
        attempts.append(len(term) - 1)
    return attempts


def _extract_property_map(ndc_data: Dict[str, Any]) -> Dict[str, str]:
    props: Dict[str, str] = {}
    ndc_props = ndc_data.get("ndcPropertyList", {}).get("ndcProperty", [])
    if isinstance(ndc_props, dict):
        ndc_props = [ndc_props]
    if not ndc_props:
        return props
    property_items = ndc_props[0].get("propertyConceptList", {}).get("propertyConcept", [])
    if isinstance(property_items, dict):
        property_items = [property_items]
    for item in property_items:
        name = str(item.get("propName", "")).upper()
        value = str(item.get("propValue", "")).strip()
        if name and value:
            props[name] = value
    return props


async def _fetch_one_field(field: str, term: str, limit: int, client: httpx.AsyncClient) -> List[dict]:
    params = {"search": f"openfda.{field}:{term}", "limit": limit}
    resp = await client.get(OPENFDA_URL, params=params)
    if resp.status_code == 404:
        return []
    resp.raise_for_status()
    return resp.json().get("results", [])


async def _rxnorm_approximate_terms(query: str, client: httpx.AsyncClient) -> List[str]:
    try:
        resp = await client.get(RXNAV_APPROX_URL, params={"term": query, "maxEntries": 5, "option": 0})
        if not resp.is_success:
            return []
        data = resp.json()
        candidates = data.get("approximateGroup", {}).get("candidate", [])
        if isinstance(candidates, dict):
            candidates = [candidates]
        out: List[str] = []
        for c in candidates:
            candidate = (c.get("rxnormString") or c.get("name") or c.get("term") or "").strip()
            if candidate:
                out.append(candidate)
        return out
    except Exception:
        return []


async def _resolve_rxcui_by_name(name: str, client: httpx.AsyncClient, cache: Dict[str, Optional[str]]) -> Optional[str]:
    key = _normalize_name(name)
    if key in cache:
        return cache[key]
    try:
        resp = await client.get(RXNAV_RXCUI_URL, params={"name": name})
        if not resp.is_success:
            cache[key] = None
            return None
        ids = resp.json().get("idGroup", {}).get("rxnormId", [])
        rxcui = ids[0] if isinstance(ids, list) and ids else None
        cache[key] = rxcui
        return rxcui
    except Exception:
        cache[key] = None
        return None


async def _fetch_visual_by_rxcui(
    rxcui: str,
    client: httpx.AsyncClient,
    image_cache: Dict[str, Dict[str, Optional[str]]],
    ndc_cache: Dict[str, Dict[str, Optional[str]]],
) -> Dict[str, Optional[str]]:
    if rxcui in image_cache:
        return image_cache[rxcui]

    visual = {"image_url": None, "imprint": None, "color": None, "shape": None}
    try:
        image_resp = await client.get(RXIMAGE_URL, params={"rxcui": rxcui})
        if image_resp.is_success:
            img_data = image_resp.json()
            images = img_data.get("nlmRxImages", [])
            if isinstance(images, dict):
                images = [images]
            if images:
                first = images[0]
                visual["image_url"] = first.get("imageUrl")
                ndc11 = first.get("ndc11")
                if ndc11:
                    if ndc11 not in ndc_cache:
                        ndc_appearance = {"imprint": None, "color": None, "shape": None}
                        try:
                            ndc_resp = await client.get(RXNAV_NDC_PROPS_URL, params={"ndc": ndc11})
                            if ndc_resp.is_success:
                                prop_map = _extract_property_map(ndc_resp.json())
                                ndc_appearance["imprint"] = prop_map.get("IMPRINT_CODE") or prop_map.get("IMPRINT")
                                ndc_appearance["color"] = prop_map.get("COLORTEXT") or prop_map.get("COLOR")
                                ndc_appearance["shape"] = prop_map.get("SHAPETEXT") or prop_map.get("SHAPE")
                        except Exception:
                            pass
                        ndc_cache[ndc11] = ndc_appearance
                    appearance = ndc_cache.get(ndc11, {})
                    visual["imprint"] = appearance.get("imprint")
                    visual["color"] = appearance.get("color")
                    visual["shape"] = appearance.get("shape")
    except Exception:
        pass

    image_cache[rxcui] = visual
    return visual


async def _resolve_best_rxcui(
    names: List[str], client: httpx.AsyncClient, rxcui_cache: Dict[str, Optional[str]]
) -> Optional[str]:
    for name in names:
        if not name:
            continue
        rxcui = await _resolve_rxcui_by_name(name, client, rxcui_cache)
        if rxcui:
            return rxcui
    return None


async def _build_query_variants(query: str, client: httpx.AsyncClient) -> List[str]:
    variants: List[str] = [query]
    norm = _normalize_name(query)

    canonical = _ALIAS_TO_CANONICAL.get(norm)
    if canonical:
        variants.append(canonical)
        variants.extend(_SYNONYM_GROUPS.get(canonical, []))
    elif norm in _SYNONYM_GROUPS:
        variants.extend(_SYNONYM_GROUPS[norm])

    variants.extend(await _rxnorm_approximate_terms(query, client))

    deduped: List[str] = []
    seen = set()
    for v in variants:
        vv = v.strip()
        key = _normalize_name(vv)
        if not vv or not key or key in seen:
            continue
        seen.add(key)
        deduped.append(vv)
    return deduped


async def enrich_med_visuals(
    *,
    display_name: str,
    generic_name: Optional[str] = None,
    substance_name: Optional[str] = None,
    canonical_name: Optional[str] = None,
    rxcui: Optional[str] = None,
) -> Dict[str, Optional[str]]:
    image_cache: Dict[str, Dict[str, Optional[str]]] = {}
    ndc_cache: Dict[str, Dict[str, Optional[str]]] = {}
    rxcui_cache: Dict[str, Optional[str]] = {}

    candidates = [display_name, canonical_name, generic_name, substance_name]
    candidates = [c for c in candidates if c]

    async with httpx.AsyncClient(timeout=15.0) as client:
        resolved_rxcui = rxcui or await _resolve_best_rxcui(candidates, client, rxcui_cache)
        if not resolved_rxcui:
            return {"image_url": None, "imprint": None, "color": None, "shape": None}
        return await _fetch_visual_by_rxcui(resolved_rxcui, client, image_cache, ndc_cache)


async def search_medications(query: str, limit: int = 10) -> List[MedSearchResult]:
    q = query.strip()
    if not q:
        return []

    seen_canonical: set[str] = set()
    results: List[MedSearchResult] = []
    image_cache: Dict[str, Dict[str, Optional[str]]] = {}
    ndc_cache: Dict[str, Dict[str, Optional[str]]] = {}
    rxcui_cache: Dict[str, Optional[str]] = {}

    async with httpx.AsyncClient(timeout=15.0) as client:
        query_variants = await _build_query_variants(q, client)

        for query_variant in query_variants:
            for prefix_len in _candidate_attempts(query_variant):
                term = _build_term(query_variant, prefix_len=prefix_len)
                if not term:
                    break

                all_items: List[dict] = []
                for field in ["generic_name", "brand_name", "substance_name"]:
                    try:
                        all_items.extend(await _fetch_one_field(field, term, limit * 2, client))
                    except Exception:
                        if prefix_len is not None:
                            break
                        raise

                for item in all_items:
                    openfda = item.get("openfda", {})
                    brand = _get_first_str(openfda.get("brand_name"))
                    generic = _get_first_str(openfda.get("generic_name"))
                    substance = _get_first_str(openfda.get("substance_name"))
                    manufacturer = _get_first_str(openfda.get("manufacturer_name"))
                    route = _get_first_str(openfda.get("route"))
                    rxcui = _get_first_str(openfda.get("rxcui"))

                    display_name = _display_name(brand, generic, substance)
                    if not display_name:
                        continue

                    canonical_name = generic or substance or display_name
                    canonical_key = _normalize_name(canonical_name)
                    if not canonical_key or canonical_key in seen_canonical:
                        continue
                    seen_canonical.add(canonical_key)

                    warnings = item.get("warnings", [])
                    warnings_snippet = warnings[0][:300] if warnings else None

                    visual = {"image_url": None, "imprint": None, "color": None, "shape": None}
                    resolved_rxcui = rxcui or await _resolve_best_rxcui(
                        [display_name, canonical_name, generic, substance], client, rxcui_cache
                    )
                    if resolved_rxcui:
                        visual = await _fetch_visual_by_rxcui(resolved_rxcui, client, image_cache, ndc_cache)

                    if not visual.get("imprint"):
                        visual["imprint"] = _get_first_str(item.get("spl_imprint"))
                    if not visual.get("color"):
                        visual["color"] = _get_first_str(item.get("spl_color"))
                    if not visual.get("shape"):
                        visual["shape"] = _get_first_str(item.get("spl_shape"))

                    results.append(
                        MedSearchResult(
                            brand_name=brand,
                            generic_name=generic,
                            manufacturer=manufacturer,
                            route=route,
                            substance_name=substance,
                            warnings_snippet=warnings_snippet,
                            display_name=display_name,
                            canonical_name=canonical_name,
                            image_url=visual.get("image_url"),
                            imprint=visual.get("imprint"),
                            color=visual.get("color"),
                            shape=visual.get("shape"),
                        )
                    )
                    if len(results) >= limit:
                        break

                if len(results) >= limit:
                    break
            if len(results) >= limit:
                break

    return results[:limit]


async def suggest_medication_names(query: str, limit: int = 3) -> List[str]:
    """Return lightweight medication name suggestions for typeahead."""
    q = query.strip()
    if not q:
        return []
    q_key = _normalize_name(q)
    if not q_key:
        return []

    now = time.time()
    cached = _SUGGEST_CACHE.get(q_key)
    if cached and now - cached[0] <= _SUGGEST_CACHE_TTL_SECONDS:
        return cached[1][:limit]

    suggestions: List[str] = []
    scored: List[tuple[int, str]] = []
    seen_keys: set[str] = set()
    norm_q = _normalize_name(q)

    def _score_candidate(name: str) -> int:
        n = _normalize_name(name)
        if not n:
            return 99
        if n.startswith(norm_q):
            return 0
        if any(part.startswith(norm_q) for part in n.split()):
            return 1
        if norm_q in n:
            return 2
        return 99

    async with httpx.AsyncClient(timeout=6.0) as client:
        # Typeahead should be fast: one narrow wildcard term, parallel field requests.
        term = _build_term(f"{q}*", prefix_len=None) if len(q) >= 2 else _build_term(q, prefix_len=None)
        if not term:
            return []

        fields = ["generic_name", "brand_name"] if len(norm_q) <= 3 else ["generic_name", "brand_name", "substance_name"]
        tasks = [_fetch_one_field(field, term, max(limit * 3, 8), client) for field in fields]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        all_items: List[dict] = []
        for resp in responses:
            if isinstance(resp, Exception):
                continue
            all_items.extend(resp)

        # For longer terms, one extra relaxed exact query as fallback.
        if len(all_items) < limit and len(norm_q) >= 6:
            fallback_tasks = [_fetch_one_field(field, _build_term(q, prefix_len=None), max(limit * 2, 6), client) for field in fields]
            fallback_responses = await asyncio.gather(*fallback_tasks, return_exceptions=True)
            for resp in fallback_responses:
                if isinstance(resp, Exception):
                    continue
                all_items.extend(resp)

        for item in all_items:
            openfda = item.get("openfda", {})
            brand = _get_first_str(openfda.get("brand_name"))
            generic = _get_first_str(openfda.get("generic_name"))
            substance = _get_first_str(openfda.get("substance_name"))
            display_name = _display_name(brand, generic, substance)
            if not display_name:
                continue

            key = _normalize_name(generic or substance or display_name)
            if not key or key in seen_keys:
                continue
            score = _score_candidate(display_name)
            if score >= 99:
                continue
            seen_keys.add(key)
            scored.append((score, display_name))

    scored.sort(key=lambda x: (x[0], len(x[1]), x[1].lower()))
    suggestions = [name for _, name in scored][:limit]
    _SUGGEST_CACHE[q_key] = (time.time(), suggestions[:limit])
    if len(_SUGGEST_CACHE) > _SUGGEST_CACHE_MAX_ENTRIES:
        oldest_key = min(_SUGGEST_CACHE.keys(), key=lambda k: _SUGGEST_CACHE[k][0])
        _SUGGEST_CACHE.pop(oldest_key, None)
    return suggestions[:limit]
