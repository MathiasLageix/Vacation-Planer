"""Tests pour search_core() dans main.py."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from models import (
    CarSearchCriteria,
    FlightSegment,
    HotelSearchCriteria,
    NormalizedFlight,
    NormalizedHotel,
    SearchCriteria,
)
from storage import Storage
from datetime import datetime


@pytest.fixture(autouse=True)
def mock_env(monkeypatch, tmp_path):
    monkeypatch.setenv("RAPIDAPI_KEY", "test_key")
    monkeypatch.setenv("DATABASE_URL", str(tmp_path / "test.db"))


def _make_flight(price: float = 500.0, stops: int = 0) -> NormalizedFlight:
    seg = FlightSegment(
        origin="YUL",
        destination="CDG",
        departure_at=datetime.fromisoformat("2026-08-15T10:00:00"),
        arrival_at=datetime.fromisoformat("2026-08-15T22:30:00"),
        carrier_code="AC",
        flight_number="AC870",
        duration_minutes=450,
    )
    return NormalizedFlight(
        provider="duffel",
        offer_id=f"off_{price}",
        total_price=price,
        currency="CAD",
        stops=stops,
        segments=[seg],
        deep_link=f"https://www.google.com/travel/flights#flt=YUL.CDG.2026-08-15;o;c:CAD;a:AC",
    )


def _make_hotel(price: float = 150.0) -> NormalizedHotel:
    return NormalizedHotel(
        provider="duffel_stays",
        property_id="prop_1",
        name="Hotel Test",
        stars=4,
        price_per_night=price,
        total_price=price * 7,
        currency="CAD",
        check_in="2026-08-15",
        check_out="2026-08-22",
        nights=7,
        address="Paris, France",
        deep_link="https://www.google.com/travel/hotels/search?q=Hotel+Test+CDG",
    )


@pytest.mark.asyncio
async def test_search_core_flights_only():
    """search_core avec vols seulement retourne la structure attendue."""
    from main import search_core

    flight = _make_flight()
    criteria = SearchCriteria(
        origin="YUL", destination="CDG", departure_date="2026-08-15",
        return_date=None, adults=1, currency="CAD"
    )
    storage = Storage("sqlite:///:memory:")

    with (
        patch("main.RapidAPIFlightsProvider") as mock_fp,
        patch("main.DuffelStaysProvider"),
        patch("main.CarsProvider"),
    ):
        mock_fp.return_value.search = AsyncMock(return_value=[flight])
        result = await search_core(criteria, None, None, storage)

    assert result["flight_error"] is None
    assert len(result["flights"]) == 1
    assert result["flights"][0]["offer_id"] == "off_500.0"
    assert result["hotels"] == []
    assert result["cars"] == []
    assert result["flight_insights"] is None  # first snapshot, no diff yet
    assert "session_id" in result


@pytest.mark.asyncio
async def test_search_core_flight_error_propagated():
    """Quand le provider lève une exception, flight_error est rempli."""
    from main import search_core

    criteria = SearchCriteria(
        origin="YUL", destination="CDG", departure_date="2026-08-15",
        return_date=None, adults=1, currency="CAD"
    )
    storage = Storage("sqlite:///:memory:")

    with (
        patch("main.RapidAPIFlightsProvider") as mock_fp,
        patch("main.DuffelStaysProvider"),
        patch("main.CarsProvider"),
    ):
        mock_fp.return_value.search = AsyncMock(side_effect=RuntimeError("API down"))
        result = await search_core(criteria, None, None, storage)

    assert result["flight_error"] is not None
    assert "API down" in result["flight_error"]
    assert result["flights"] == []


@pytest.mark.asyncio
async def test_search_core_with_hotels():
    """search_core avec hôtels remplit hotels dans le résultat."""
    from main import search_core

    criteria = SearchCriteria(
        origin="YUL", destination="CDG", departure_date="2026-08-15",
        return_date=None, adults=2, currency="CAD"
    )
    hotel_criteria = HotelSearchCriteria(
        city_iata="CDG", check_in="2026-08-15", check_out="2026-08-22", adults=2, rooms=1
    )
    hotel = _make_hotel()

    with (
        patch("main.RapidAPIFlightsProvider") as mock_fp,
        patch("main.DuffelStaysProvider") as mock_hs,
        patch("main.CarsProvider"),
    ):
        mock_fp.return_value.search = AsyncMock(return_value=[_make_flight()])
        mock_hs.return_value.search = AsyncMock(return_value=[hotel])
        result = await search_core(criteria, hotel_criteria, None, Storage("sqlite:///:memory:"), max_hotel_results=5)

    assert len(result["hotels"]) == 1
    assert result["hotels"][0]["name"] == "Hotel Test"


@pytest.mark.asyncio
async def test_search_core_serialize_flight_segments():
    """Les datetimes des segments sont sérialisées en ISO string."""
    from main import search_core

    criteria = SearchCriteria(
        origin="YUL", destination="CDG", departure_date="2026-08-15",
        return_date=None, adults=1, currency="CAD"
    )
    storage = Storage("sqlite:///:memory:")

    with (
        patch("main.RapidAPIFlightsProvider") as mock_fp,
        patch("main.DuffelStaysProvider"),
        patch("main.CarsProvider"),
    ):
        mock_fp.return_value.search = AsyncMock(return_value=[_make_flight()])
        result = await search_core(criteria, None, None, storage)

    seg = result["flights"][0]["segments"][0]
    assert isinstance(seg["departure_at"], str)
    assert "T" in seg["departure_at"]  # format ISO


@pytest.mark.asyncio
async def test_search_core_flight_insights_on_second_run():
    """Le deuxième appel avec des prix différents génère des insights."""
    from main import search_core

    criteria = SearchCriteria(
        origin="YUL", destination="CDG", departure_date="2026-08-15",
        return_date=None, adults=1, currency="CAD"
    )
    storage = Storage("sqlite:///:memory:")

    with (
        patch("main.RapidAPIFlightsProvider") as mock_fp,
        patch("main.DuffelStaysProvider"),
        patch("main.CarsProvider"),
    ):
        # Premier snapshot
        mock_fp.return_value.search = AsyncMock(return_value=[_make_flight(price=500.0)])
        await search_core(criteria, None, None, storage)

        # Deuxième snapshot avec un prix différent
        mock_fp.return_value.search = AsyncMock(return_value=[_make_flight(price=450.0)])
        result = await search_core(criteria, None, None, storage)

    # Doit avoir des insights (price change)
    assert result["flight_insights"] is not None
    assert "price_changes" in result["flight_insights"]
