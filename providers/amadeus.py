"""Fournisseur Amadeus Self-Service pour la recherche de vols."""
import os
from datetime import datetime, timedelta

import httpx

from models import FlightSegment, NormalizedFlight, SearchCriteria

_TOKEN_URL_TEST = "https://test.api.amadeus.com/v1/security/oauth2/token"
_TOKEN_URL_PROD = "https://api.amadeus.com/v1/security/oauth2/token"
_SEARCH_URL_TEST = "https://test.api.amadeus.com/v2/shopping/flight-offers"
_SEARCH_URL_PROD = "https://api.amadeus.com/v2/shopping/flight-offers"

# Amadeus encode les durées en ISO 8601 : PT2H30M
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
    """Construit un deep link Google Flights à partir d'une offre Amadeus."""
    itinerary = offer["itineraries"][0]
    segments = itinerary["segments"]
    first = segments[0]
    last = segments[-1]
    dep_date = first["departure"]["at"][:10].replace("-", "")
    origin = first["departure"]["iataCode"]
    dest = last["arrival"]["iataCode"]
    trip_type = "r" if criteria.return_date else "o"
    return (
        f"https://www.google.com/travel/flights/search?"
        f"tfs=CBwQAhoeEgoyMDI1LTAxLTAxagcIARIDWVVMcgcIARIDWVVMQAFIAXABggELCP___________wE%3D"
        f"#flt={origin}.{dest}.{dep_date};{trip_type};c:{criteria.currency}"
    )


def _parse_offer(offer: dict, criteria: SearchCriteria) -> NormalizedFlight:
    itinerary = offer["itineraries"][0]
    raw_segments = itinerary["segments"]

    segments = [
        FlightSegment(
            origin=seg["departure"]["iataCode"],
            destination=seg["arrival"]["iataCode"],
            departure_at=datetime.fromisoformat(seg["departure"]["at"]),
            arrival_at=datetime.fromisoformat(seg["arrival"]["at"]),
            carrier_code=seg["carrierCode"],
            flight_number=f"{seg['carrierCode']}{seg['number']}",
            duration_minutes=_parse_iso_duration(seg["duration"]),
        )
        for seg in raw_segments
    ]

    price_info = offer["price"]
    return NormalizedFlight(
        provider="amadeus",
        offer_id=offer["id"],
        total_price=float(price_info["grandTotal"]),
        currency=price_info["currency"],
        stops=len(raw_segments) - 1,
        segments=segments,
        deep_link=_build_deep_link(offer, criteria),
        raw=offer,
    )


class AmadeusProvider:
    def __init__(self) -> None:
        self.client_id = os.environ["AMADEUS_CLIENT_ID"]
        self.client_secret = os.environ["AMADEUS_CLIENT_SECRET"]
        env = os.getenv("AMADEUS_ENV", "test")
        self._token_url = _TOKEN_URL_TEST if env == "test" else _TOKEN_URL_PROD
        self._search_url = _SEARCH_URL_TEST if env == "test" else _SEARCH_URL_PROD
        self._access_token: str | None = None
        self._token_expires_at: datetime = datetime.min

    async def _get_token(self, client: httpx.AsyncClient) -> str:
        if self._access_token and datetime.now() < self._token_expires_at:
            return self._access_token

        resp = await client.post(
            self._token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        data = resp.json()
        self._access_token = data["access_token"]
        self._token_expires_at = datetime.now() + timedelta(seconds=data["expires_in"] - 30)
        return self._access_token

    async def search(
        self, criteria: SearchCriteria, max_results: int = 10
    ) -> list[NormalizedFlight]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            token = await self._get_token(client)

            dates_to_search = [criteria.departure_date]
            if criteria.flexible_days > 0:
                base = datetime.strptime(criteria.departure_date, "%Y-%m-%d")
                for delta in range(1, criteria.flexible_days + 1):
                    dates_to_search.append((base + timedelta(days=delta)).strftime("%Y-%m-%d"))
                    dates_to_search.append((base - timedelta(days=delta)).strftime("%Y-%m-%d"))

            all_offers: list[NormalizedFlight] = []
            for date in dates_to_search:
                params: dict = {
                    "originLocationCode": criteria.origin,
                    "destinationLocationCode": criteria.destination,
                    "departureDate": date,
                    "adults": criteria.adults,
                    "currencyCode": criteria.currency,
                    "max": max_results,
                    "nonStop": "false",
                }
                if criteria.return_date:
                    params["returnDate"] = criteria.return_date
                if criteria.preferred_carriers:
                    params["includedAirlineCodes"] = ",".join(criteria.preferred_carriers)
                if criteria.max_price:
                    params["maxPrice"] = int(criteria.max_price)

                resp = await client.get(
                    self._search_url,
                    params=params,
                    headers={"Authorization": f"Bearer {token}"},
                )
                resp.raise_for_status()
                data = resp.json()
                offers = [_parse_offer(o, criteria) for o in data.get("data", [])]
                all_offers.extend(offers)

            # Filtre stops après coup (Amadeus ne filtre pas exactement)
            if criteria.max_stops is not None:
                all_offers = [o for o in all_offers if o.stops <= criteria.max_stops]

            # Trie par prix
            all_offers.sort(key=lambda o: o.total_price)
            return all_offers[:max_results]
