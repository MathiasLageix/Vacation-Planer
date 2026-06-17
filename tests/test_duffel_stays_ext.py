"""Tests additionnels pour duffel_stays.py — branche list, timeout, filtre prix."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from models import HotelSearchCriteria


@pytest.fixture
def criteria() -> HotelSearchCriteria:
    return HotelSearchCriteria(
        city_iata="CDG",
        check_in="2026-09-15",
        check_out="2026-09-22",
        adults=2,
        rooms=1,
        currency="CAD",
    )


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    monkeypatch.setenv("DUFFEL_API_KEY", "duffel_test_fake")


def _make_mock_client(response_data: dict, status_code: int = 200) -> AsyncMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.raise_for_status = MagicMock()
    resp.json.return_value = response_data

    client = AsyncMock()
    client.post = AsyncMock(return_value=resp)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    return client


def _hotel_result(name: str = "Hotel Test", price: str = "150.00", property_id: str = "prop_1") -> dict:
    return {
        "id": property_id,
        "accommodation": {
            "id": property_id,
            "name": name,
            "rating": {"value": 4},
            "location": {
                "address": {
                    "line_one": "1 Rue de la Paix",
                    "city_name": "Paris",
                    "country_code": "FR",
                }
            },
        },
        "cheapest_rate_total_amount": price,
        "cheapest_rate_currency": "CAD",
    }


@pytest.mark.asyncio
async def test_data_node_is_list(criteria):
    """Quand data est une liste directe, les résultats sont extraits correctement."""
    from providers.duffel_stays import DuffelStaysProvider

    # Duffel peut retourner data comme liste directe
    response = {"data": [_hotel_result("Hotel Liste")]}

    with patch("providers.duffel_stays.httpx.AsyncClient", return_value=_make_mock_client(response)):
        results = await DuffelStaysProvider().search(criteria)

    assert len(results) == 1
    assert results[0].name == "Hotel Liste"


@pytest.mark.asyncio
async def test_data_node_is_dict_with_results(criteria):
    """Quand data est un dict avec clé 'results', les hôtels sont extraits."""
    from providers.duffel_stays import DuffelStaysProvider

    response = {"data": {"results": [_hotel_result("Hotel Dict")]}}

    with patch("providers.duffel_stays.httpx.AsyncClient", return_value=_make_mock_client(response)):
        results = await DuffelStaysProvider().search(criteria)

    assert len(results) == 1
    assert results[0].name == "Hotel Dict"


@pytest.mark.asyncio
async def test_max_price_filter(criteria):
    """Les hôtels dépassant max_price_per_night sont filtrés."""
    from providers.duffel_stays import DuffelStaysProvider

    criteria.max_price_per_night = 100.0  # 7 nuits → max 100/nuit
    response = {
        "data": {
            "results": [
                _hotel_result("Cher", price="1400.00", property_id="p1"),  # 200/nuit → filtré
                _hotel_result("Abordable", price="630.00", property_id="p2"),  # 90/nuit → gardé
            ]
        }
    }

    with patch("providers.duffel_stays.httpx.AsyncClient", return_value=_make_mock_client(response)):
        results = await DuffelStaysProvider().search(criteria)

    assert len(results) == 1
    assert results[0].name == "Abordable"


@pytest.mark.asyncio
async def test_sorted_by_total_price(criteria):
    """Les résultats sont triés par prix total croissant."""
    from providers.duffel_stays import DuffelStaysProvider

    response = {
        "data": {
            "results": [
                _hotel_result("Cher", price="700.00", property_id="p1"),
                _hotel_result("Pas Cher", price="350.00", property_id="p2"),
            ]
        }
    }

    with patch("providers.duffel_stays.httpx.AsyncClient", return_value=_make_mock_client(response)):
        results = await DuffelStaysProvider().search(criteria)

    assert results[0].name == "Pas Cher"
    assert results[1].name == "Cher"


@pytest.mark.asyncio
async def test_max_results_respected(criteria):
    """max_results limite le nombre d'hôtels retournés."""
    from providers.duffel_stays import DuffelStaysProvider

    hotels = [_hotel_result(f"Hotel {i}", price=str(100 + i * 10), property_id=f"p{i}") for i in range(10)]
    response = {"data": {"results": hotels}}

    with patch("providers.duffel_stays.httpx.AsyncClient", return_value=_make_mock_client(response)):
        results = await DuffelStaysProvider().search(criteria, max_results=3)

    assert len(results) == 3


@pytest.mark.asyncio
async def test_empty_results(criteria):
    """Une réponse vide retourne une liste vide."""
    from providers.duffel_stays import DuffelStaysProvider

    response = {"data": {"results": []}}

    with patch("providers.duffel_stays.httpx.AsyncClient", return_value=_make_mock_client(response)):
        results = await DuffelStaysProvider().search(criteria)

    assert results == []
