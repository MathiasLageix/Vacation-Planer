"""Tests pour providers/rapidapi_flights.py."""
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from models import NormalizedFlight, SearchCriteria


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _criteria(
    *,
    origin="YUL",
    destination="CDG",
    departure_date="2026-09-15",
    return_date=None,
    adults=1,
    children=0,
    max_stops=None,
    preferred_carriers=None,
    max_price=None,
    currency="CAD",
    flexible_days=0,
) -> SearchCriteria:
    return SearchCriteria(
        origin=origin,
        destination=destination,
        departure_date=departure_date,
        return_date=return_date,
        adults=adults,
        children=children,
        max_stops=max_stops,
        preferred_carriers=preferred_carriers or [],
        max_price=max_price,
        currency=currency,
        flexible_days=flexible_days,
    )


def _raw_oneway(
    price=650.0,
    airline="Air Canada",
    dep_desc="8:00 AM – 10:30 PM",
    duration_sec=52200,
    stops=0,
    buy_link="https://www.google.com/travel/flights?tfs=foo",
) -> dict:
    return {
        "from_airport": "YUL",
        "to_airport": "CDG",
        "price": "$650",
        "price_as_number": price,
        "airline": airline,
        "departure_description": dep_desc,
        "duration_seconds": duration_sec,
        "stops": stops,
        "buy_link": buy_link,
    }


def _raw_roundtrip(
    total_price=1200.0,
    dep_airline="Air Canada",
    ret_airline="Air France",
    dep_desc="8:00 AM – 10:30 PM",
    ret_desc="2:00 PM – 4:30 PM",
    dep_dur_sec=52200,
    ret_dur_sec=43200,
    dep_stops=0,
    buy_link="https://www.google.com/travel/flights?tfs=bar",
) -> dict:
    return {
        "from_airport": "YUL",
        "to_airport": "CDG",
        "total_price": "$1200",
        "total_price_as_number": total_price,
        "total_stops": dep_stops,
        "departure_flight_airline": dep_airline,
        "departure_flight_departure_description": dep_desc,
        "departure_flight_duration_seconds": dep_dur_sec,
        "departure_flight_stops": dep_stops,
        "return_flight_airline": ret_airline,
        "return_flight_departure_description": ret_desc,
        "return_flight_duration_seconds": ret_dur_sec,
        "buy_link": buy_link,
    }


def _mock_client(response_data: list) -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json = MagicMock(return_value=response_data)

    client = AsyncMock()
    client.post = AsyncMock(return_value=resp)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    return client


# ---------------------------------------------------------------------------
# _to_iata
# ---------------------------------------------------------------------------

def test_to_iata_known_airline():
    from providers.rapidapi_flights import _to_iata
    assert _to_iata("Air Canada") == "AC"
    assert _to_iata("air france") == "AF"
    assert _to_iata("WestJet") == "WS"
    assert _to_iata("Lufthansa") == "LH"


def test_to_iata_partial_match():
    from providers.rapidapi_flights import _to_iata
    assert _to_iata("Air Canada Express") == "AC"
    assert _to_iata("TAP Air Portugal") == "TP"


def test_to_iata_unknown_falls_back_to_initials():
    from providers.rapidapi_flights import _to_iata
    code = _to_iata("Oceanic Airlines")
    assert len(code) == 2
    assert code == "OC"


# ---------------------------------------------------------------------------
# _parse_description
# ---------------------------------------------------------------------------

def test_parse_description_simple():
    from providers.rapidapi_flights import _parse_description
    dep, arr = _parse_description("8:00 AM – 10:30 PM", "2026-09-15")
    assert dep == datetime(2026, 9, 15, 8, 0)
    assert arr == datetime(2026, 9, 15, 22, 30)


def test_parse_description_next_day_explicit():
    from providers.rapidapi_flights import _parse_description
    dep, arr = _parse_description("11:00 PM – 7:00 AM +1", "2026-09-15")
    assert dep == datetime(2026, 9, 15, 23, 0)
    assert arr == datetime(2026, 9, 16, 7, 0)


def test_parse_description_next_day_inferred():
    """Arrivée avant départ sans +N → inféré lendemain."""
    from providers.rapidapi_flights import _parse_description
    dep, arr = _parse_description("10:00 PM – 6:00 AM", "2026-09-15")
    assert dep == datetime(2026, 9, 15, 22, 0)
    assert arr == datetime(2026, 9, 16, 6, 0)


def test_parse_description_invalid_falls_back():
    from providers.rapidapi_flights import _parse_description
    dep, arr = _parse_description("non-date garbage", "2026-09-15")
    # Les deux tombent à midi
    assert dep.hour == 12
    assert arr.hour == 12


# ---------------------------------------------------------------------------
# _parse_one_way
# ---------------------------------------------------------------------------

def test_parse_one_way_price_currency():
    from providers.rapidapi_flights import _parse_one_way
    nf = _parse_one_way(_raw_oneway(price=742.0), _criteria(currency="CAD"), "2026-09-15")
    assert isinstance(nf, NormalizedFlight)
    assert nf.total_price == 742.0
    assert nf.currency == "CAD"
    assert nf.provider == "rapidapi_google_flights"


def test_parse_one_way_stops():
    from providers.rapidapi_flights import _parse_one_way
    nf = _parse_one_way(_raw_oneway(stops=1), _criteria(), "2026-09-15")
    assert nf.stops == 1


def test_parse_one_way_carrier_code():
    from providers.rapidapi_flights import _parse_one_way
    nf = _parse_one_way(_raw_oneway(airline="Air France"), _criteria(), "2026-09-15")
    assert nf.segments[0].carrier_code == "AF"
    assert "AF" in nf.carrier_codes


def test_parse_one_way_duration():
    from providers.rapidapi_flights import _parse_one_way
    nf = _parse_one_way(_raw_oneway(duration_sec=52200), _criteria(), "2026-09-15")
    assert nf.segments[0].duration_minutes == 870  # 52200 / 60


def test_parse_one_way_deep_link_https():
    from providers.rapidapi_flights import _parse_one_way
    nf = _parse_one_way(_raw_oneway(buy_link="https://google.com/flights?tfs=x"), _criteria(), "2026-09-15")
    assert nf.deep_link.startswith("https://")


def test_parse_one_way_xss_blocked():
    """Un buy_link non-https est rejeté."""
    from providers.rapidapi_flights import _parse_one_way
    nf = _parse_one_way(
        _raw_oneway(buy_link="javascript:alert(1)"),
        _criteria(), "2026-09-15",
    )
    assert nf.deep_link == ""


# ---------------------------------------------------------------------------
# _parse_roundtrip
# ---------------------------------------------------------------------------

def test_parse_roundtrip_two_segments():
    from providers.rapidapi_flights import _parse_roundtrip
    crit = _criteria(return_date="2026-09-22")
    nf = _parse_roundtrip(_raw_roundtrip(), crit)
    assert len(nf.segments) == 2


def test_parse_roundtrip_price():
    from providers.rapidapi_flights import _parse_roundtrip
    crit = _criteria(return_date="2026-09-22")
    nf = _parse_roundtrip(_raw_roundtrip(total_price=1350.0), crit)
    assert nf.total_price == 1350.0


def test_parse_roundtrip_segments_direction():
    from providers.rapidapi_flights import _parse_roundtrip
    crit = _criteria(origin="YUL", destination="CDG", return_date="2026-09-22")
    nf = _parse_roundtrip(_raw_roundtrip(), crit)
    assert nf.segments[0].origin == "YUL"
    assert nf.segments[0].destination == "CDG"
    assert nf.segments[1].origin == "CDG"
    assert nf.segments[1].destination == "YUL"


def test_parse_roundtrip_carriers():
    from providers.rapidapi_flights import _parse_roundtrip
    crit = _criteria(return_date="2026-09-22")
    nf = _parse_roundtrip(_raw_roundtrip(dep_airline="Air Canada", ret_airline="Air France"), crit)
    codes = nf.carrier_codes
    assert "AC" in codes
    assert "AF" in codes


# ---------------------------------------------------------------------------
# _stable_id
# ---------------------------------------------------------------------------

def test_stable_id_deterministic():
    from providers.rapidapi_flights import _stable_id
    raw = _raw_oneway()
    id1 = _stable_id(raw, "2026-09-15")
    id2 = _stable_id(raw, "2026-09-15")
    assert id1 == id2


def test_stable_id_different_for_different_prices():
    from providers.rapidapi_flights import _stable_id
    r1 = _raw_oneway(price=500.0)
    r2 = _raw_oneway(price=700.0)
    assert _stable_id(r1, "2026-09-15") != _stable_id(r2, "2026-09-15")


# ---------------------------------------------------------------------------
# RapidAPIFlightsProvider.search — aller simple
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_search_oneway_returns_flights(monkeypatch):
    monkeypatch.setenv("RAPIDAPI_KEY", "test_key")
    from providers.rapidapi_flights import RapidAPIFlightsProvider

    mock_client = _mock_client([_raw_oneway(price=650.0), _raw_oneway(price=750.0)])
    with patch("providers.rapidapi_flights.httpx.AsyncClient", return_value=mock_client):
        flights = await RapidAPIFlightsProvider().search(_criteria(), max_results=10)

    assert len(flights) == 2
    assert flights[0].total_price <= flights[1].total_price  # trié par prix


@pytest.mark.asyncio
async def test_search_sorted_by_price(monkeypatch):
    monkeypatch.setenv("RAPIDAPI_KEY", "test_key")
    from providers.rapidapi_flights import RapidAPIFlightsProvider

    raw = [_raw_oneway(price=900.0), _raw_oneway(price=500.0), _raw_oneway(price=700.0)]
    mock_client = _mock_client(raw)
    with patch("providers.rapidapi_flights.httpx.AsyncClient", return_value=mock_client):
        flights = await RapidAPIFlightsProvider().search(_criteria())

    prices = [f.total_price for f in flights]
    assert prices == sorted(prices)


@pytest.mark.asyncio
async def test_search_max_results_respected(monkeypatch):
    monkeypatch.setenv("RAPIDAPI_KEY", "test_key")
    from providers.rapidapi_flights import RapidAPIFlightsProvider

    raw = [_raw_oneway(price=float(i * 100)) for i in range(1, 8)]
    mock_client = _mock_client(raw)
    with patch("providers.rapidapi_flights.httpx.AsyncClient", return_value=mock_client):
        flights = await RapidAPIFlightsProvider().search(_criteria(), max_results=3)

    assert len(flights) == 3


# ---------------------------------------------------------------------------
# Payload envoyé à l'API
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_payload_currency_lowercase(monkeypatch):
    monkeypatch.setenv("RAPIDAPI_KEY", "test_key")
    from providers.rapidapi_flights import RapidAPIFlightsProvider

    captured: list[dict] = []
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json = MagicMock(return_value=[])

    async def fake_post(url, json=None, headers=None):
        captured.append(json or {})
        return resp

    client = AsyncMock()
    client.post = AsyncMock(side_effect=fake_post)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)

    with patch("providers.rapidapi_flights.httpx.AsyncClient", return_value=client):
        await RapidAPIFlightsProvider().search(_criteria(currency="CAD"))

    assert captured[0]["currency"] == "cad"


@pytest.mark.asyncio
async def test_payload_passengers_adults_children(monkeypatch):
    monkeypatch.setenv("RAPIDAPI_KEY", "test_key")
    from providers.rapidapi_flights import RapidAPIFlightsProvider

    captured: list[dict] = []
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json = MagicMock(return_value=[])

    async def fake_post(url, json=None, headers=None):
        captured.append(json or {})
        return resp

    client = AsyncMock()
    client.post = AsyncMock(side_effect=fake_post)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)

    crit = _criteria(adults=2, children=1)
    with patch("providers.rapidapi_flights.httpx.AsyncClient", return_value=client):
        await RapidAPIFlightsProvider().search(crit)

    passengers = captured[0]["passengers"]
    assert passengers.count("adult") == 2
    assert passengers.count("child") == 1


@pytest.mark.asyncio
async def test_payload_max_stops_included(monkeypatch):
    monkeypatch.setenv("RAPIDAPI_KEY", "test_key")
    from providers.rapidapi_flights import RapidAPIFlightsProvider

    captured: list[dict] = []
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json = MagicMock(return_value=[])

    async def fake_post(url, json=None, headers=None):
        captured.append(json or {})
        return resp

    client = AsyncMock()
    client.post = AsyncMock(side_effect=fake_post)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)

    with patch("providers.rapidapi_flights.httpx.AsyncClient", return_value=client):
        await RapidAPIFlightsProvider().search(_criteria(max_stops=1))

    assert captured[0]["max_stops"] == 1


@pytest.mark.asyncio
async def test_payload_preferred_carriers(monkeypatch):
    monkeypatch.setenv("RAPIDAPI_KEY", "test_key")
    from providers.rapidapi_flights import RapidAPIFlightsProvider

    captured: list[dict] = []
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json = MagicMock(return_value=[])

    async def fake_post(url, json=None, headers=None):
        captured.append(json or {})
        return resp

    client = AsyncMock()
    client.post = AsyncMock(side_effect=fake_post)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)

    with patch("providers.rapidapi_flights.httpx.AsyncClient", return_value=client):
        await RapidAPIFlightsProvider().search(_criteria(preferred_carriers=["AC", "WS"]))

    assert captured[0]["airline_codes"] == ["AC", "WS"]


@pytest.mark.asyncio
async def test_payload_max_price(monkeypatch):
    monkeypatch.setenv("RAPIDAPI_KEY", "test_key")
    from providers.rapidapi_flights import RapidAPIFlightsProvider

    captured: list[dict] = []
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json = MagicMock(return_value=[])

    async def fake_post(url, json=None, headers=None):
        captured.append(json or {})
        return resp

    client = AsyncMock()
    client.post = AsyncMock(side_effect=fake_post)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)

    with patch("providers.rapidapi_flights.httpx.AsyncClient", return_value=client):
        await RapidAPIFlightsProvider().search(_criteria(max_price=800.0))

    assert captured[0]["max_price"] == 800


# ---------------------------------------------------------------------------
# Flexible days : nombre d'appels API
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_flexible_days_calls_multiple_dates(monkeypatch):
    monkeypatch.setenv("RAPIDAPI_KEY", "test_key")
    from providers.rapidapi_flights import RapidAPIFlightsProvider

    call_count = 0
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json = MagicMock(return_value=[])

    async def fake_post(url, json=None, headers=None):
        nonlocal call_count
        call_count += 1
        return resp

    client = AsyncMock()
    client.post = AsyncMock(side_effect=fake_post)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)

    with patch("providers.rapidapi_flights.httpx.AsyncClient", return_value=client):
        await RapidAPIFlightsProvider().search(_criteria(flexible_days=2))

    # flexible_days=2 → dates [-2, -1, 0, +1, +2] = 5 appels
    assert call_count == 5


# ---------------------------------------------------------------------------
# Round-trip : endpoint correct
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_roundtrip_uses_roundtrip_endpoint(monkeypatch):
    monkeypatch.setenv("RAPIDAPI_KEY", "test_key")
    from providers.rapidapi_flights import RapidAPIFlightsProvider

    urls_called: list[str] = []
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json = MagicMock(return_value=[])

    async def fake_post(url, json=None, headers=None):
        urls_called.append(url)
        return resp

    client = AsyncMock()
    client.post = AsyncMock(side_effect=fake_post)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)

    crit = _criteria(return_date="2026-09-22")
    with patch("providers.rapidapi_flights.httpx.AsyncClient", return_value=client):
        await RapidAPIFlightsProvider().search(crit)

    assert all("roundtrip" in u for u in urls_called)


@pytest.mark.asyncio
async def test_oneway_uses_oneway_endpoint(monkeypatch):
    monkeypatch.setenv("RAPIDAPI_KEY", "test_key")
    from providers.rapidapi_flights import RapidAPIFlightsProvider

    urls_called: list[str] = []
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json = MagicMock(return_value=[])

    async def fake_post(url, json=None, headers=None):
        urls_called.append(url)
        return resp

    client = AsyncMock()
    client.post = AsyncMock(side_effect=fake_post)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)

    with patch("providers.rapidapi_flights.httpx.AsyncClient", return_value=client):
        await RapidAPIFlightsProvider().search(_criteria())

    assert all("oneway" in u for u in urls_called)


# ---------------------------------------------------------------------------
# Erreur HTTP : silencieuse (exception absorbée)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_http_error_raises(monkeypatch):
    """HTTP error se propage comme exception (visible dans flight_error) au lieu de [] silencieux."""
    monkeypatch.setenv("RAPIDAPI_KEY", "test_key")
    from providers.rapidapi_flights import RapidAPIFlightsProvider

    resp = MagicMock()
    resp.raise_for_status = MagicMock(side_effect=httpx.HTTPStatusError(
        "429", request=MagicMock(), response=MagicMock()
    ))

    client = AsyncMock()
    client.post = AsyncMock(return_value=resp)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)

    with patch("providers.rapidapi_flights.httpx.AsyncClient", return_value=client):
        with pytest.raises(httpx.HTTPStatusError):
            await RapidAPIFlightsProvider().search(_criteria())
