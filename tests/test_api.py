"""Tests pour les routes FastAPI — /api/search (SSE), /api/sessions, /api/health."""
import json
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from api.main import app
from models import FlightSegment, NormalizedFlight, SearchCriteria
from datetime import datetime


@pytest.fixture(autouse=True)
def mock_env(monkeypatch, tmp_path):
    monkeypatch.setenv("DUFFEL_API_KEY", "duffel_test_fake")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/test_api.db")
    import api.deps
    api.deps._storage = None  # reset singleton so DATABASE_URL prend effet


def _make_flight(price: float = 500.0) -> NormalizedFlight:
    seg = FlightSegment(
        origin="YUL",
        destination="CDG",
        departure_at=datetime.fromisoformat("2026-09-15T10:00:00"),
        arrival_at=datetime.fromisoformat("2026-09-15T22:30:00"),
        carrier_code="AC",
        flight_number="AC870",
        duration_minutes=450,
    )
    return NormalizedFlight(
        provider="duffel",
        offer_id=f"off_{price}",
        total_price=price,
        currency="CAD",
        stops=0,
        segments=[seg],
        deep_link="https://www.google.com/travel/flights#flt=YUL.CDG.2026-09-15;o;c:CAD;a:AC",
    )


_VALID_SEARCH_BODY = {
    "flight": {
        "origin": "YUL",
        "destination": "CDG",
        "departure_date": "2026-09-15",
        "adults": 1,
        "currency": "CAD",
    }
}


def _parse_sse(content: bytes) -> list[tuple[str, dict]]:
    """Retourne [(event_type, data), ...] depuis un stream SSE."""
    events = []
    current_event = "message"
    for line in content.decode().splitlines():
        if line.startswith("event:"):
            current_event = line[6:].strip()
        elif line.startswith("data:"):
            data = json.loads(line[5:].strip())
            events.append((current_event, data))
    return events


# ─── /api/health ─────────────────────────────────────────────────────────────

def test_health_endpoint():
    client = TestClient(app)
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# ─── /api/search SSE ─────────────────────────────────────────────────────────

def test_search_sse_returns_flights_and_done():
    """Le stream SSE émet 'flights' puis 'done' pour une recherche réussie."""
    client = TestClient(app)

    with patch("api.routes.search.search_core", new_callable=AsyncMock) as mock_core:
        mock_core.return_value = {
            "session_id": "sess_test",
            "flights": [
                {
                    "offer_id": "off_500.0",
                    "provider": "duffel",
                    "total_price": 500.0,
                    "currency": "CAD",
                    "stops": 0,
                    "segments": [
                        {
                            "origin": "YUL",
                            "destination": "CDG",
                            "departure_at": "2026-09-15T10:00:00",
                            "arrival_at": "2026-09-15T22:30:00",
                            "carrier_code": "AC",
                            "flight_number": "AC870",
                            "duration_minutes": 450,
                        }
                    ],
                    "deep_link": "https://www.google.com/travel/flights#flt=YUL.CDG.2026-09-15;o;c:CAD;a:AC",
                }
            ],
            "hotels": [],
            "cars": [],
            "flight_insights": None,
            "hotel_insights": None,
            "flight_error": None,
            "car_stub_message": None,
        }

        resp = client.post("/api/search", json=_VALID_SEARCH_BODY)

    assert resp.status_code == 200
    events = _parse_sse(resp.content)
    event_types = [e[0] for e in events]
    assert "flights" in event_types
    assert "done" in event_types
    flights_data = next(d for t, d in events if t == "flights")
    assert len(flights_data["data"]) == 1
    done_data = next(d for t, d in events if t == "done")
    assert done_data["session_id"] == "sess_test"


def test_search_sse_flight_error_stops_stream():
    """Quand flight_error est rempli, l'événement 'error' est émis et le stream s'arrête."""
    client = TestClient(app)

    with patch("api.routes.search.search_core", new_callable=AsyncMock) as mock_core:
        mock_core.return_value = {
            "session_id": "sess_err",
            "flights": [],
            "hotels": [],
            "cars": [],
            "flight_insights": None,
            "hotel_insights": None,
            "flight_error": "API Duffel indisponible",
            "car_stub_message": None,
        }

        resp = client.post("/api/search", json=_VALID_SEARCH_BODY)

    events = _parse_sse(resp.content)
    event_types = [e[0] for e in events]
    assert "error" in event_types
    assert "done" not in event_types  # early return, no 'done' after error


def test_search_sse_internal_exception_returns_error():
    """Une exception non gérée dans search_core retourne un événement 'error'."""
    client = TestClient(app)

    with patch("api.routes.search.search_core", new_callable=AsyncMock) as mock_core:
        mock_core.side_effect = RuntimeError("crash inattendu")

        resp = client.post("/api/search", json=_VALID_SEARCH_BODY)

    events = _parse_sse(resp.content)
    error_events = [(t, d) for t, d in events if t == "error"]
    assert len(error_events) == 1
    assert "erreur interne" in error_events[0][1]["message"].lower()


def test_search_sse_with_hotel_results():
    """Les résultats d'hôtels sont émis dans un événement 'hotels' séparé."""
    client = TestClient(app)

    with patch("api.routes.search.search_core", new_callable=AsyncMock) as mock_core:
        mock_core.return_value = {
            "session_id": "sess_hotel",
            "flights": [
                {
                    "offer_id": "off_1",
                    "provider": "duffel",
                    "total_price": 500.0,
                    "currency": "CAD",
                    "stops": 0,
                    "segments": [],
                    "deep_link": "https://www.google.com/travel/flights",
                }
            ],
            "hotels": [{"property_id": "prop_1", "name": "Hotel Paris"}],
            "cars": [],
            "flight_insights": None,
            "hotel_insights": None,
            "flight_error": None,
            "car_stub_message": None,
        }

        body = {**_VALID_SEARCH_BODY, "hotel": {
            "city_iata": "CDG",
            "check_in": "2026-09-15",
            "check_out": "2026-09-22",
            "adults": 1,
        }}
        resp = client.post("/api/search", json=body)

    events = _parse_sse(resp.content)
    event_types = [e[0] for e in events]
    assert "hotels" in event_types
    hotels_data = next(d for t, d in events if t == "hotels")
    assert hotels_data["data"][0]["name"] == "Hotel Paris"


def test_search_sse_insights_emitted():
    """Les insights de vols sont émis dans un événement 'insights'."""
    client = TestClient(app)

    with patch("api.routes.search.search_core", new_callable=AsyncMock) as mock_core:
        mock_core.return_value = {
            "session_id": "sess_ins",
            "flights": [],
            "hotels": [],
            "cars": [],
            "flight_insights": {
                "session_id": "sess_ins",
                "search_type": "flight",
                "snapshot_old_at": "2026-06-01T10:00:00",
                "snapshot_new_at": "2026-06-02T10:00:00",
                "price_changes": [{"offer_id": "x", "old_price": 500, "new_price": 450, "delta": -50, "currency": "CAD"}],
                "availability": [],
            },
            "hotel_insights": None,
            "flight_error": None,
            "car_stub_message": None,
        }

        resp = client.post("/api/search", json=_VALID_SEARCH_BODY)

    events = _parse_sse(resp.content)
    insight_events = [(t, d) for t, d in events if t == "insights"]
    assert len(insight_events) == 1
    assert insight_events[0][1]["type"] == "flight"


# ─── /api/search validation ──────────────────────────────────────────────────

def test_search_sse_timeout_returns_error():
    """Une TimeoutError dans search_core retourne un événement 'error' avec message timeout."""
    import asyncio
    client = TestClient(app)

    with patch("api.routes.search.search_core", new_callable=AsyncMock) as mock_core:
        mock_core.side_effect = asyncio.TimeoutError()

        resp = client.post("/api/search", json=_VALID_SEARCH_BODY)

    events = _parse_sse(resp.content)
    error_events = [(t, d) for t, d in events if t == "error"]
    assert len(error_events) == 1
    assert "trop de temps" in error_events[0][1]["message"].lower()


def test_search_missing_origin_returns_422():
    client = TestClient(app)
    body = {"flight": {"destination": "CDG", "departure_date": "2026-09-15"}}
    resp = client.post("/api/search", json=body)
    assert resp.status_code == 422


def test_search_flexible_days_too_high_returns_422():
    """flexible_days > 5 est rejeté (ge=0, le=5 dans le schema)."""
    client = TestClient(app)
    body = {
        "flight": {
            "origin": "YUL",
            "destination": "CDG",
            "departure_date": "2026-09-15",
            "flexible_days": 6,  # interdit (max 5)
        }
    }
    resp = client.post("/api/search", json=body)
    assert resp.status_code == 422


def test_search_flexible_days_negative_returns_422():
    client = TestClient(app)
    body = {
        "flight": {
            "origin": "YUL",
            "destination": "CDG",
            "departure_date": "2026-09-15",
            "flexible_days": -1,
        }
    }
    resp = client.post("/api/search", json=body)
    assert resp.status_code == 422


def test_search_hotel_optional():
    """hotel=None est valide (champ optionnel)."""
    client = TestClient(app)

    with patch("api.routes.search.search_core", new_callable=AsyncMock) as mock_core:
        mock_core.return_value = {
            "session_id": "s",
            "flights": [],
            "hotels": [],
            "cars": [],
            "flight_insights": None,
            "hotel_insights": None,
            "flight_error": None,
            "car_stub_message": None,
        }
        resp = client.post("/api/search", json=_VALID_SEARCH_BODY)

    assert resp.status_code == 200


# ─── /api/sessions ───────────────────────────────────────────────────────────

def test_sessions_empty():
    """GET /api/sessions retourne [] quand la DB est vide."""
    client = TestClient(app)
    with patch("api.routes.sessions.get_storage") as mock_get_storage:
        mock_get_storage.return_value.get_all_sessions.return_value = []
        resp = client.get("/api/sessions")
    assert resp.status_code == 200
    assert resp.json() == []
