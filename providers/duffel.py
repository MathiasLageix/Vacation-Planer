"""Fournisseur Duffel pour la recherche de vols."""
import os
from datetime import datetime, timedelta

import httpx

from models import FlightSegment, NormalizedFlight, SearchCriteria

_BASE_URL = "https://api.duffel.com"
_DUFFEL_VERSION = "v2"


def _parse_iso_duration(duration: str) -> int:
    """Retourne la durée en minutes depuis une string ISO 8601 (PT2H30M)."""
    duration = duration.replace("PT", "")
    hours, minutes = 0, 0
    if "H" in duration:
        parts = duration.split("H")
        hours = int(parts[0])
        duration = parts[1]
    if "M" in duration:
        minutes = int(duration.replace("M", ""))
    return hours * 60 + minutes


def _build_deep_link(offer: dict, criteria: SearchCriteria) -> str:
    """Construit un deep link Google Flights à partir d'une offre Duffel."""
    slice_ = offer["slices"][0]
    segs = slice_["segments"]
    origin = segs[0]["origin"]["iata_code"]
    destination = segs[-1]["destination"]["iata_code"]
    dep_date = segs[0]["departing_at"][:10]
    carrier = segs[0]["marketing_carrier"]["iata_code"]

    if criteria.return_date:
        flt = f"{origin}.{destination}.{dep_date}*{destination}.{origin}.{criteria.return_date}"
        trip_type = "r"
    else:
        flt = f"{origin}.{destination}.{dep_date}"
        trip_type = "o"

    return (
        f"https://www.google.com/travel/flights"
        f"#flt={flt};{trip_type};c:{criteria.currency};a:{carrier}"
    )


def _parse_offer(offer: dict, criteria: SearchCriteria) -> NormalizedFlight:
    slice_ = offer["slices"][0]
    raw_segments = slice_["segments"]

    segments = [
        FlightSegment(
            origin=seg["origin"]["iata_code"],
            destination=seg["destination"]["iata_code"],
            departure_at=datetime.fromisoformat(seg["departing_at"]),
            arrival_at=datetime.fromisoformat(seg["arriving_at"]),
            carrier_code=seg["marketing_carrier"]["iata_code"],
            flight_number=(
                f"{seg['marketing_carrier']['iata_code']}"
                f"{seg['marketing_carrier_flight_number']}"
            ),
            duration_minutes=_parse_iso_duration(seg["duration"]),
        )
        for seg in raw_segments
    ]

    return NormalizedFlight(
        provider="duffel",
        offer_id=offer["id"],
        total_price=float(offer["total_amount"]),
        currency=offer["total_currency"],
        stops=len(raw_segments) - 1,
        segments=segments,
        deep_link=_build_deep_link(offer, criteria),
        raw=offer,
    )


class DuffelProvider:
    def __init__(self) -> None:
        self.api_key = os.environ["DUFFEL_API_KEY"]
        self._headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Duffel-Version": _DUFFEL_VERSION,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _create_offer_request(
        self,
        client: httpx.AsyncClient,
        criteria: SearchCriteria,
        departure_date: str,
    ) -> list[dict]:
        slices = [
            {
                "origin": criteria.origin,
                "destination": criteria.destination,
                "departure_date": departure_date,
            }
        ]
        if criteria.return_date:
            slices.append(
                {
                    "origin": criteria.destination,
                    "destination": criteria.origin,
                    "departure_date": criteria.return_date,
                }
            )

        passengers = [{"type": "adult"} for _ in range(criteria.adults)]
        passengers += [{"type": "child"} for _ in range(criteria.children)]

        payload = {
            "data": {
                "slices": slices,
                "passengers": passengers,
                "cabin_class": "economy",
                "currency": criteria.currency,
                "return_offers": True,
            }
        }

        resp = await client.post(
            f"{_BASE_URL}/air/offer_requests",
            json=payload,
            headers=self._headers,
        )
        resp.raise_for_status()
        return resp.json()["data"].get("offers", [])

    async def search(
        self, criteria: SearchCriteria, max_results: int = 10
    ) -> list[NormalizedFlight]:
        dates_to_search = [criteria.departure_date]
        if criteria.flexible_days > 0:
            base = datetime.strptime(criteria.departure_date, "%Y-%m-%d")
            for delta in range(1, criteria.flexible_days + 1):
                dates_to_search.append((base + timedelta(days=delta)).strftime("%Y-%m-%d"))
                dates_to_search.append((base - timedelta(days=delta)).strftime("%Y-%m-%d"))

        all_offers: list[NormalizedFlight] = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            for date in dates_to_search:
                raw_offers = await self._create_offer_request(client, criteria, date)
                parsed = [_parse_offer(o, criteria) for o in raw_offers]
                all_offers.extend(parsed)

        if criteria.max_stops is not None:
            all_offers = [o for o in all_offers if o.stops <= criteria.max_stops]

        if criteria.preferred_carriers:
            carriers = set(criteria.preferred_carriers)
            all_offers = [
                o for o in all_offers if carriers.intersection(o.carrier_codes)
            ]

        if criteria.max_price is not None:
            all_offers = [o for o in all_offers if o.total_price <= criteria.max_price]

        all_offers.sort(key=lambda o: o.total_price)
        return all_offers[:max_results]
