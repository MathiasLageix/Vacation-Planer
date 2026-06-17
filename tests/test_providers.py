"""Tests du provider Duffel avec réponses mockées."""
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models import NormalizedFlight, SearchCriteria

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def criteria() -> SearchCriteria:
    return SearchCriteria(
        origin="YUL",
        destination="CDG",
        departure_date="2026-08-15",
        return_date=None,
        adults=1,
        currency="CAD",
    )


@pytest.fixture
def mock_duffel_response() -> dict:
    return json.loads((FIXTURES_DIR / "duffel_flight_response.json").read_text())


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    monkeypatch.setenv("DUFFEL_API_KEY", "duffel_test_fake")


def _make_mock_client(response_data: dict) -> AsyncMock:
    post_response = MagicMock()
    post_response.json.return_value = response_data
    post_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=post_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    return mock_client


@pytest.mark.asyncio
async def test_search_returns_normalized_flights(criteria, mock_duffel_response):
    from providers.duffel import DuffelProvider

    with patch("providers.duffel.httpx.AsyncClient", return_value=_make_mock_client(mock_duffel_response)):
        results = await DuffelProvider().search(criteria, max_results=10)

    assert len(results) == 2
    assert all(isinstance(r, NormalizedFlight) for r in results)
    # Triés par prix : DL (620) avant AC (750)
    assert results[0].total_price == 620.0
    assert results[1].total_price == 750.0
    assert all(r.provider == "duffel" for r in results)


@pytest.mark.asyncio
async def test_filter_by_max_stops(criteria, mock_duffel_response):
    from providers.duffel import DuffelProvider

    criteria.max_stops = 0  # direct seulement

    with patch("providers.duffel.httpx.AsyncClient", return_value=_make_mock_client(mock_duffel_response)):
        results = await DuffelProvider().search(criteria)

    assert len(results) == 1
    assert results[0].stops == 0
    assert results[0].carrier_codes == ["AC"]


@pytest.mark.asyncio
async def test_direct_flight_parsed_correctly(criteria, mock_duffel_response):
    from providers.duffel import DuffelProvider

    with patch("providers.duffel.httpx.AsyncClient", return_value=_make_mock_client(mock_duffel_response)):
        results = await DuffelProvider().search(criteria)

    ac_flight = next(r for r in results if "AC" in r.carrier_codes)
    assert ac_flight.stops == 0
    assert ac_flight.total_duration_minutes == 450  # 7h30
    assert ac_flight.segments[0].flight_number == "AC870"
    assert "google.com/travel/flights" in ac_flight.deep_link


@pytest.mark.asyncio
async def test_filter_by_preferred_carrier(criteria, mock_duffel_response):
    from providers.duffel import DuffelProvider

    criteria.preferred_carriers = ["AC"]

    with patch("providers.duffel.httpx.AsyncClient", return_value=_make_mock_client(mock_duffel_response)):
        results = await DuffelProvider().search(criteria)

    assert len(results) == 1
    assert results[0].carrier_codes == ["AC"]


@pytest.mark.asyncio
async def test_filter_by_max_price(criteria, mock_duffel_response):
    from providers.duffel import DuffelProvider

    criteria.max_price = 700.0

    with patch("providers.duffel.httpx.AsyncClient", return_value=_make_mock_client(mock_duffel_response)):
        results = await DuffelProvider().search(criteria)

    assert len(results) == 1
    assert results[0].total_price == 620.0
