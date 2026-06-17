"""Tests pour CarsProvider (stub Phase 2)."""
import pytest

from models import CarSearchCriteria


@pytest.fixture
def criteria() -> CarSearchCriteria:
    return CarSearchCriteria(
        pickup_location="CDG",
        dropoff_location="CDG",
        pickup_datetime="2026-09-15T10:00",
        dropoff_datetime="2026-09-22T10:00",
        currency="CAD",
    )


@pytest.mark.asyncio
async def test_cars_stub_returns_empty_list(criteria):
    """CarsProvider retourne toujours une liste vide (stub)."""
    from providers.cars import CarsProvider

    results = await CarsProvider().search(criteria)
    assert results == []


def test_cars_is_stub():
    """CarsProvider.is_stub est True."""
    from providers.cars import CarsProvider

    assert CarsProvider().is_stub is True


def test_cars_stub_message_non_empty():
    """stub_message est une chaîne non vide."""
    from providers.cars import CarsProvider

    provider = CarsProvider()
    # stub_message est une propriété qui retourne une chaîne
    msg = provider.stub_message
    assert isinstance(msg, str)
    assert len(msg) > 0
