"""Fournisseur RapidAPI Google Flights Live (by Matan Rabi) pour la recherche de vols.

Endpoint : https://google-flights-live-api.p.rapidapi.com
  POST /api/google_flights/oneway/v1   — vols aller simple
  POST /api/google_flights/roundtrip/v1 — vols aller-retour

Auth : x-rapidapi-key (RAPIDAPI_KEY dans .env), x-rapidapi-host.
"""

import asyncio
import hashlib
import os
import re
from datetime import datetime, timedelta

import httpx

from models import FlightSegment, NormalizedFlight, SearchCriteria

_BASE_URL = "https://google-flights-live-api.p.rapidapi.com"
_RAPIDAPI_HOST = "google-flights-live-api.p.rapidapi.com"

# Compagnies les plus fréquentes sur les routes CA/Europe — complétable librement.
_AIRLINE_IATA: dict[str, str] = {
    "air canada": "AC",
    "westjet": "WS",
    "air transat": "TS",
    "porter": "PD",
    "sunwing": "WG",
    "air france": "AF",
    "british airways": "BA",
    "lufthansa": "LH",
    "klm": "KL",
    "swiss": "LX",
    "tap air portugal": "TP",
    "iberia": "IB",
    "vueling": "VY",
    "united": "UA",
    "american": "AA",
    "delta": "DL",
    "emirates": "EK",
    "turkish airlines": "TK",
    "qatar airways": "QR",
    "aer lingus": "EI",
}


def _to_iata(airline_name: str) -> str:
    """Retourne le code IATA depuis un nom de compagnie, ou 2 initiales en fallback."""
    lower = airline_name.lower().strip()
    for key, code in _AIRLINE_IATA.items():
        if key in lower:
            return code
    parts = airline_name.upper().split()
    return parts[0][:2] if parts else "??"


def _parse_description(description: str, base_date: str) -> tuple[datetime, datetime]:
    """Parse 'H:MM AM – H:MM PM' ou 'H:MM AM – H:MM PM +1' → (dep_dt, arr_dt).

    Gère l'arrivée le lendemain (indicateur +N ou inférence heure < départ).
    """
    base = datetime.strptime(base_date, "%Y-%m-%d")
    m = re.match(
        r"(\d{1,2}:\d{2}\s*[AP]M)\s*[–\-]\s*(\d{1,2}:\d{2}\s*[AP]M)(?:\s*\+(\d+))?",
        description.strip(),
        re.IGNORECASE,
    )
    if not m:
        # Fallback : midi → midi (on ne peut pas déduire les heures)
        return base.replace(hour=12), base.replace(hour=12)

    dep_str, arr_str = m.group(1).strip(), m.group(2).strip()
    extra_days = int(m.group(3) or 0)

    dep_dt = datetime.strptime(f"{base_date} {dep_str}", "%Y-%m-%d %I:%M %p")
    arr_dt = datetime.strptime(f"{base_date} {arr_str}", "%Y-%m-%d %I:%M %p")
    arr_dt += timedelta(days=extra_days)

    # Si arrivée avant départ sans indicateur +N → arrivée le lendemain
    if arr_dt <= dep_dt and extra_days == 0:
        arr_dt += timedelta(days=1)

    return dep_dt, arr_dt


def _stable_id(flight: dict, date: str) -> str:
    """Génère un ID stable et court depuis les champs discriminants du vol."""
    key = "|".join([
        str(flight.get("from_airport", "")),
        str(flight.get("to_airport", "")),
        date,
        str(flight.get("airline", flight.get("departure_flight_airline", ""))),
        str(flight.get("price_as_number", flight.get("total_price_as_number", ""))),
    ])
    return hashlib.md5(key.encode()).hexdigest()[:16]


def _safe_link(url: str) -> str:
    """Refuse les URLs non-HTTPS pour éviter l'injection XSS."""
    return url if url.startswith("https://") else ""


def _parse_one_way(raw: dict, criteria: SearchCriteria, date: str) -> NormalizedFlight:
    carrier_code = _to_iata(raw.get("airline", ""))
    dep_dt, arr_dt = _parse_description(raw.get("departure_description", ""), date)
    duration_min = (raw.get("duration_seconds") or 0) // 60

    segment = FlightSegment(
        origin=criteria.origin,
        destination=criteria.destination,
        departure_at=dep_dt,
        arrival_at=arr_dt,
        carrier_code=carrier_code,
        flight_number=f"{carrier_code}???",
        duration_minutes=duration_min,
    )

    return NormalizedFlight(
        provider="rapidapi_google_flights",
        offer_id=_stable_id(raw, date),
        total_price=float(raw.get("price_as_number", 0)),
        currency=criteria.currency.upper(),
        stops=int(raw.get("stops", 0)),
        segments=[segment],
        deep_link=_safe_link(raw.get("buy_link", "")),
        raw=raw,
    )


def _parse_roundtrip(raw: dict, criteria: SearchCriteria) -> NormalizedFlight:
    dep_carrier = _to_iata(raw.get("departure_flight_airline", ""))
    ret_carrier = _to_iata(raw.get("return_flight_airline", ""))

    dep_dt, dep_arr_dt = _parse_description(
        raw.get("departure_flight_departure_description", ""),
        criteria.departure_date,
    )
    ret_dt, ret_arr_dt = _parse_description(
        raw.get("return_flight_departure_description", ""),
        criteria.return_date or criteria.departure_date,
    )

    dep_min = (raw.get("departure_flight_duration_seconds") or 0) // 60
    ret_min = (raw.get("return_flight_duration_seconds") or 0) // 60

    segments = [
        FlightSegment(
            origin=criteria.origin,
            destination=criteria.destination,
            departure_at=dep_dt,
            arrival_at=dep_arr_dt,
            carrier_code=dep_carrier,
            flight_number=f"{dep_carrier}???",
            duration_minutes=dep_min,
        ),
        FlightSegment(
            origin=criteria.destination,
            destination=criteria.origin,
            departure_at=ret_dt,
            arrival_at=ret_arr_dt,
            carrier_code=ret_carrier,
            flight_number=f"{ret_carrier}???",
            duration_minutes=ret_min,
        ),
    ]

    return NormalizedFlight(
        provider="rapidapi_google_flights",
        offer_id=_stable_id(raw, criteria.departure_date),
        total_price=float(raw.get("total_price_as_number", 0)),
        currency=criteria.currency.upper(),
        stops=int(raw.get("departure_flight_stops") or 0),
        segments=segments,
        deep_link=_safe_link(raw.get("buy_link", "")),
        raw=raw,
    )


class RapidAPIFlightsProvider:
    def __init__(self) -> None:
        self.api_key = os.environ["RAPIDAPI_KEY"]
        self._headers = {
            "Content-Type": "application/json",
            "x-rapidapi-host": _RAPIDAPI_HOST,
            "x-rapidapi-key": self.api_key,
        }

    def _build_payload(self, criteria: SearchCriteria, departure_date: str) -> dict:
        payload: dict = {
            "from_airport": criteria.origin,
            "to_airport": criteria.destination,
            "departure_date": departure_date,
            "currency": criteria.currency.lower(),
            "passengers": ["adult"] * criteria.adults + ["child"] * criteria.children,
            "seat_type": 1,  # 1 = Economy
        }
        if criteria.return_date:
            payload["return_date"] = criteria.return_date
        if criteria.max_stops is not None:
            payload["max_stops"] = criteria.max_stops
        if criteria.preferred_carriers:
            payload["airline_codes"] = criteria.preferred_carriers
        if criteria.max_price is not None:
            payload["max_price"] = int(criteria.max_price)
        return payload

    async def _search_date(
        self,
        client: httpx.AsyncClient,
        criteria: SearchCriteria,
        departure_date: str,
    ) -> list[dict]:
        path = "roundtrip" if criteria.return_date else "oneway"
        url = f"{_BASE_URL}/api/google_flights/{path}/v1"
        payload = self._build_payload(criteria, departure_date)

        resp = await client.post(url, json=payload, headers=self._headers)
        resp.raise_for_status()

        data = resp.json()
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in ("results", "flights", "data", "offers"):
                if key in data and isinstance(data[key], list):
                    return data[key]
        return []

    async def search(
        self, criteria: SearchCriteria, max_results: int = 10
    ) -> list[NormalizedFlight]:
        dates = [criteria.departure_date]
        if criteria.flexible_days > 0:
            base = datetime.strptime(criteria.departure_date, "%Y-%m-%d")
            for delta in range(1, criteria.flexible_days + 1):
                dates.append((base + timedelta(days=delta)).strftime("%Y-%m-%d"))
                dates.append((base - timedelta(days=delta)).strftime("%Y-%m-%d"))

        is_roundtrip = bool(criteria.return_date)
        all_flights: list[NormalizedFlight] = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            raw_results = await asyncio.gather(
                *[self._search_date(client, criteria, d) for d in dates],
                return_exceptions=True,
            )
            for raw_list, date in zip(raw_results, dates):
                if isinstance(raw_list, Exception):
                    continue
                for flight in raw_list:
                    nf = (
                        _parse_roundtrip(flight, criteria)
                        if is_roundtrip
                        else _parse_one_way(flight, criteria, date)
                    )
                    all_flights.append(nf)

        all_flights.sort(key=lambda f: f.total_price)
        return all_flights[:max_results]
