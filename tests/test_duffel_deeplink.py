"""Tests pour _build_deep_link dans duffel.py — enfants, aller-retour, devise."""
import pytest
from models import SearchCriteria


def _make_offer(origin: str = "YUL", destination: str = "CDG", dep_date: str = "2026-09-15", carrier: str = "AC") -> dict:
    return {
        "slices": [
            {
                "segments": [
                    {
                        "origin": {"iata_code": origin},
                        "destination": {"iata_code": destination},
                        "departing_at": f"{dep_date}T10:00:00",
                        "arriving_at": f"{dep_date}T22:30:00",
                        "marketing_carrier": {"iata_code": carrier},
                        "marketing_carrier_flight_number": "870",
                        "duration": "PT12H30M",
                    }
                ]
            }
        ]
    }


def test_deep_link_one_way():
    """Vol aller simple : trip_type=o, pas d'astérisque."""
    from providers.duffel import _build_deep_link

    criteria = SearchCriteria(
        origin="YUL", destination="CDG", departure_date="2026-09-15", return_date=None, currency="CAD"
    )
    url = _build_deep_link(_make_offer(), criteria)

    assert "#flt=" in url
    assert ";o;" in url
    assert "*" not in url
    assert "c:CAD" in url
    assert "a:AC" in url


def test_deep_link_round_trip():
    """Vol aller-retour : trip_type=r, format flt inclut return_date avec astérisque."""
    from providers.duffel import _build_deep_link

    criteria = SearchCriteria(
        origin="YUL", destination="CDG",
        departure_date="2026-09-15",
        return_date="2026-09-22",
        currency="CAD",
    )
    url = _build_deep_link(_make_offer(), criteria)

    assert ";r;" in url
    assert "YUL.CDG.2026-09-15*CDG.YUL.2026-09-22" in url
    assert "c:CAD" in url
    assert "a:AC" in url


def test_deep_link_currency_propagated():
    """La devise est correctement incluse dans le deep link."""
    from providers.duffel import _build_deep_link

    criteria = SearchCriteria(
        origin="YUL", destination="LHR", departure_date="2026-10-01",
        return_date=None, currency="USD"
    )
    url = _build_deep_link(_make_offer(origin="YUL", destination="LHR"), criteria)
    assert "c:USD" in url


def test_deep_link_carrier_code():
    """Le code IATA de la compagnie est inclus dans le deep link."""
    from providers.duffel import _build_deep_link

    criteria = SearchCriteria(
        origin="YUL", destination="CDG", departure_date="2026-09-15",
        return_date=None, currency="CAD"
    )
    url = _build_deep_link(_make_offer(carrier="AF"), criteria)
    assert "a:AF" in url


@pytest.mark.asyncio
async def test_children_passengers_included(monkeypatch):
    """Les enfants sont inclus dans le payload Duffel comme type 'child'."""
    from unittest.mock import AsyncMock, MagicMock, patch
    import providers.duffel as duffel_mod

    monkeypatch.setenv("DUFFEL_API_KEY", "duffel_test_fake")

    captured_payload = {}

    async def fake_create_offer(self, client, criteria, departure_date):
        # Capturer le payload envoyé à Duffel
        return []

    async def fake_post(url, json=None, headers=None):
        captured_payload.update(json or {})
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.json.return_value = {"data": {"offers": []}}
        return resp

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=fake_post)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    criteria = SearchCriteria(
        origin="YUL", destination="CDG",
        departure_date="2026-09-15",
        return_date=None,
        adults=2,
        children=1,
        currency="CAD",
    )

    with patch("providers.duffel.httpx.AsyncClient", return_value=mock_client):
        from providers.duffel import DuffelProvider
        await DuffelProvider().search(criteria)

    passengers = captured_payload.get("data", {}).get("passengers", [])
    adult_count = sum(1 for p in passengers if p["type"] == "adult")
    child_count = sum(1 for p in passengers if p["type"] == "child")
    assert adult_count == 2
    assert child_count == 1
