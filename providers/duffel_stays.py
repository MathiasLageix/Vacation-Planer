"""Fournisseur Duffel Stays pour la recherche d'hébergements."""
import os
from datetime import datetime, timedelta

import httpx

from models import HotelSearchCriteria, NormalizedHotel

_BASE_URL = "https://api.duffel.com"
_DUFFEL_VERSION = "v2"


def _nights_between(check_in: str, check_out: str) -> int:
    d1 = datetime.strptime(check_in, "%Y-%m-%d")
    d2 = datetime.strptime(check_out, "%Y-%m-%d")
    return max(1, (d2 - d1).days)


def _build_deep_link(result: dict, criteria: HotelSearchCriteria) -> str:
    """Construit un deep link Google Hotels."""
    name = result.get("accommodation", {}).get("name", "")
    import urllib.parse
    query = urllib.parse.quote_plus(f"{name} {criteria.city_iata}")
    return (
        f"https://www.google.com/travel/hotels/search?"
        f"q={query}&dates={criteria.check_in.replace('-', '')},{criteria.check_out.replace('-', '')}"
    )


def _parse_result(result: dict, criteria: HotelSearchCriteria) -> NormalizedHotel:
    acc = result.get("accommodation", {})
    nights = _nights_between(criteria.check_in, criteria.check_out)
    total = float(result.get("cheapest_rate_total_amount", 0))
    ppn = round(total / nights, 2) if nights else total

    rating = acc.get("rating", {})
    stars: int | None = None
    if isinstance(rating, dict):
        stars = rating.get("value")

    location = acc.get("location", {})
    address_parts = []
    if isinstance(location, dict):
        addr = location.get("address", {})
        if isinstance(addr, dict):
            address_parts = [
                v for k, v in addr.items()
                if k in ("line_one", "city_name", "country_code") and v
            ]

    return NormalizedHotel(
        provider="duffel_stays",
        property_id=acc.get("id", result.get("id", "")),
        name=acc.get("name", "Hébergement inconnu"),
        stars=stars,
        price_per_night=ppn,
        total_price=total,
        currency=result.get("cheapest_rate_currency", criteria.currency),
        check_in=criteria.check_in,
        check_out=criteria.check_out,
        nights=nights,
        address=", ".join(address_parts) if address_parts else "",
        deep_link=_build_deep_link(result, criteria),
        raw=result,
    )


class DuffelStaysProvider:
    def __init__(self) -> None:
        self.api_key = os.environ["DUFFEL_API_KEY"]
        self._headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Duffel-Version": _DUFFEL_VERSION,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def search(
        self, criteria: HotelSearchCriteria, max_results: int = 10
    ) -> list[NormalizedHotel]:
        guests = [{"type": "adult"} for _ in range(criteria.adults)]

        payload = {
            "data": {
                "rooms": criteria.rooms,
                "guests": guests,
                "check_in_date": criteria.check_in,
                "check_out_date": criteria.check_out,
                "location": {"iata_city_code": criteria.city_iata},
            }
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{_BASE_URL}/stays/search_results",
                json=payload,
                headers=self._headers,
            )
            resp.raise_for_status()
            data = resp.json()

        print(f"[duffel_stays] status={resp.status_code} keys={list(data.keys())}")
        data_node = data.get("data") or {}
        if isinstance(data_node, list):
            raw_results = data_node
        else:
            raw_results = data_node.get("results", [])
        print(f"[duffel_stays] {len(raw_results)} résultats bruts")
        hotels = [_parse_result(r, criteria) for r in raw_results]

        if criteria.max_price_per_night is not None:
            hotels = [h for h in hotels if h.price_per_night <= criteria.max_price_per_night]

        hotels.sort(key=lambda h: h.total_price)
        return hotels[:max_results]
