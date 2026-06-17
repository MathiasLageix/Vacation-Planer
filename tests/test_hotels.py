"""Tests du provider Duffel Stays avec réponses mockées."""
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models import HotelSearchCriteria, NormalizedHotel

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def criteria() -> HotelSearchCriteria:
    return HotelSearchCriteria(
        city_iata="PAR",
        check_in="2026-09-15",
        check_out="2026-09-20",
        adults=2,
        rooms=1,
        currency="CAD",
    )


@pytest.fixture
def mock_stays_response() -> dict:
    return json.loads((FIXTURES_DIR / "duffel_stays_response.json").read_text())


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    monkeypatch.setenv("DUFFEL_API_KEY", "duffel_test_fake")


def _make_mock_client(response_data: dict) -> AsyncMock:
    post_resp = MagicMock()
    post_resp.json.return_value = response_data
    post_resp.raise_for_status = MagicMock()

    client = AsyncMock()
    client.post = AsyncMock(return_value=post_resp)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    return client


@pytest.mark.asyncio
async def test_search_returns_normalized_hotels(criteria, mock_stays_response):
    from providers.duffel_stays import DuffelStaysProvider

    with patch("providers.duffel_stays.httpx.AsyncClient", return_value=_make_mock_client(mock_stays_response)):
        results = await DuffelStaysProvider().search(criteria, max_results=10)

    assert len(results) == 2
    assert all(isinstance(r, NormalizedHotel) for r in results)
    # Trié par prix : Ibis (450) avant Louvre (900)
    assert results[0].total_price == 450.0
    assert results[1].total_price == 900.0
    assert all(r.provider == "duffel_stays" for r in results)


@pytest.mark.asyncio
async def test_hotel_nights_calculated(criteria, mock_stays_response):
    from providers.duffel_stays import DuffelStaysProvider

    with patch("providers.duffel_stays.httpx.AsyncClient", return_value=_make_mock_client(mock_stays_response)):
        results = await DuffelStaysProvider().search(criteria)

    assert results[0].nights == 5  # 15 sept → 20 sept
    assert results[0].price_per_night == round(450.0 / 5, 2)


@pytest.mark.asyncio
async def test_filter_by_max_price_per_night(criteria, mock_stays_response):
    from providers.duffel_stays import DuffelStaysProvider

    criteria.max_price_per_night = 100.0  # 100 USD/nuit = 500 USD total → garde Ibis (90/nuit)

    with patch("providers.duffel_stays.httpx.AsyncClient", return_value=_make_mock_client(mock_stays_response)):
        results = await DuffelStaysProvider().search(criteria)

    assert len(results) == 1
    assert results[0].name == "Ibis Paris Gare du Nord"


@pytest.mark.asyncio
async def test_hotel_address_parsed(criteria, mock_stays_response):
    from providers.duffel_stays import DuffelStaysProvider

    with patch("providers.duffel_stays.httpx.AsyncClient", return_value=_make_mock_client(mock_stays_response)):
        results = await DuffelStaysProvider().search(criteria)

    louvre = next(r for r in results if "Louvre" in r.name)
    assert "Paris" in louvre.address
    assert louvre.stars == 4
