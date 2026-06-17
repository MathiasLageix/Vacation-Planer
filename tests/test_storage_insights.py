"""Tests du stockage SQLite et de la couche d'insights."""
from dataclasses import asdict
from datetime import datetime, timedelta

import pytest

from insights import compare_snapshots
from models import (
    FlightSegment,
    HotelSearchCriteria,
    InsightReport,
    NormalizedFlight,
    NormalizedHotel,
    SearchCriteria,
)
from storage import Storage


@pytest.fixture
def mem_storage(tmp_path):
    return Storage(f"sqlite:///{tmp_path}/test.db")


@pytest.fixture
def flight_criteria() -> SearchCriteria:
    return SearchCriteria(
        origin="YUL", destination="CDG", departure_date="2026-09-15",
        return_date=None, adults=1, currency="CAD",
    )


def make_flight(offer_id: str, price: float) -> NormalizedFlight:
    seg = FlightSegment(
        origin="YUL", destination="CDG",
        departure_at=datetime(2026, 9, 15, 8, 0),
        arrival_at=datetime(2026, 9, 15, 20, 0),
        carrier_code="AC", flight_number="AC870", duration_minutes=480,
    )
    return NormalizedFlight(
        provider="duffel", offer_id=offer_id,
        total_price=price, currency="CAD",
        stops=0, segments=[seg], deep_link="https://example.com",
    )


def make_hotel(property_id: str, price: float) -> NormalizedHotel:
    return NormalizedHotel(
        provider="duffel_stays", property_id=property_id,
        name=f"Hôtel {property_id}", stars=3,
        price_per_night=price / 5, total_price=price, currency="USD",
        check_in="2026-09-15", check_out="2026-09-20", nights=5,
        address="Paris, FR", deep_link="https://example.com",
    )


# ---- Storage tests ----

def test_create_session_idempotent(mem_storage, flight_criteria):
    sid1 = mem_storage.get_or_create_session("flight", asdict(flight_criteria))
    sid2 = mem_storage.get_or_create_session("flight", asdict(flight_criteria))
    assert sid1 == sid2


def test_different_criteria_different_session(mem_storage, flight_criteria):
    from dataclasses import replace
    c2 = SearchCriteria(
        origin="YUL", destination="LHR", departure_date="2026-09-15",
        return_date=None, adults=1, currency="CAD",
    )
    sid1 = mem_storage.get_or_create_session("flight", asdict(flight_criteria))
    sid2 = mem_storage.get_or_create_session("flight", asdict(c2))
    assert sid1 != sid2


def test_save_and_retrieve_snapshot(mem_storage, flight_criteria):
    flights = [make_flight("off_001", 750.0), make_flight("off_002", 620.0)]
    sid = mem_storage.get_or_create_session("flight", asdict(flight_criteria))
    mem_storage.save_snapshot(sid, flights)
    snapshots = mem_storage.get_latest_snapshots(sid, limit=2)
    assert len(snapshots) == 1
    _, data = snapshots[0]
    assert len(data) == 2
    assert data[0]["offer_id"] == "off_001"


def test_two_snapshots_returned_in_order(mem_storage, flight_criteria):
    sid = mem_storage.get_or_create_session("flight", asdict(flight_criteria))
    mem_storage.save_snapshot(sid, [make_flight("off_001", 750.0)])
    mem_storage.save_snapshot(sid, [make_flight("off_001", 700.0)])
    snapshots = mem_storage.get_latest_snapshots(sid, limit=2)
    assert len(snapshots) == 2
    # Ordre chronologique : le plus ancien en premier
    _, old_data = snapshots[0]
    _, new_data = snapshots[1]
    assert old_data[0]["total_price"] == 750.0
    assert new_data[0]["total_price"] == 700.0


# ---- Insights tests ----

def test_no_insights_identical_results():
    t1 = datetime(2026, 6, 1, 10, 0)
    t2 = datetime(2026, 6, 1, 12, 0)
    data = [{"offer_id": "off_001", "total_price": 750.0, "currency": "CAD"}]
    report = compare_snapshots("sid", "flight", t1, data, t2, data)
    assert not report.has_insights


def test_price_decrease_detected():
    t1 = datetime(2026, 6, 1, 10, 0)
    t2 = datetime(2026, 6, 1, 12, 0)
    old = [{"offer_id": "off_001", "total_price": 750.0, "currency": "CAD"}]
    new = [{"offer_id": "off_001", "total_price": 680.0, "currency": "CAD"}]
    report = compare_snapshots("sid", "flight", t1, old, t2, new)
    assert len(report.price_changes) == 1
    pc = report.price_changes[0]
    assert pc.delta == pytest.approx(-70.0)
    assert pc.pct_change < 0


def test_disappeared_offer_detected():
    t1 = datetime(2026, 6, 1, 10, 0)
    t2 = datetime(2026, 6, 1, 12, 0)
    old = [
        {"offer_id": "off_001", "total_price": 750.0, "currency": "CAD"},
        {"offer_id": "off_002", "total_price": 620.0, "currency": "CAD"},
    ]
    new = [{"offer_id": "off_001", "total_price": 750.0, "currency": "CAD"}]
    report = compare_snapshots("sid", "flight", t1, old, t2, new)
    assert len(report.availability) == 1
    assert report.availability[0].event == "disappeared"
    assert report.availability[0].offer_id == "off_002"


def test_new_offer_detected():
    t1 = datetime(2026, 6, 1, 10, 0)
    t2 = datetime(2026, 6, 1, 12, 0)
    old = [{"offer_id": "off_001", "total_price": 750.0, "currency": "CAD"}]
    new = [
        {"offer_id": "off_001", "total_price": 750.0, "currency": "CAD"},
        {"offer_id": "off_003", "total_price": 590.0, "currency": "CAD"},
    ]
    report = compare_snapshots("sid", "flight", t1, old, t2, new)
    assert len(report.availability) == 1
    assert report.availability[0].event == "appeared"
    assert report.availability[0].price == 590.0


def test_hotel_insights_use_property_id():
    t1 = datetime(2026, 6, 1, 10, 0)
    t2 = datetime(2026, 6, 1, 12, 0)
    old = [{"property_id": "acc_001", "name": "Hôtel A", "total_price": 500.0, "currency": "USD"}]
    new = [{"property_id": "acc_001", "name": "Hôtel A", "total_price": 450.0, "currency": "USD"}]
    report = compare_snapshots("sid", "hotel", t1, old, t2, new)
    assert len(report.price_changes) == 1
    assert report.price_changes[0].delta == pytest.approx(-50.0)
