"""Schémas Pydantic pour l'API FastAPI — miroir des dataclasses models.py."""
from pydantic import BaseModel, Field


class FlightCriteriaIn(BaseModel):
    origin: str
    destination: str
    departure_date: str
    return_date: str | None = None
    adults: int = 1
    children: int = 0
    max_stops: int | None = None
    preferred_carriers: list[str] = Field(default_factory=list)
    max_price: float | None = None
    currency: str = "CAD"
    flexible_days: int = 0


class HotelCriteriaIn(BaseModel):
    city_iata: str
    check_in: str
    check_out: str
    adults: int = 1
    rooms: int = 1
    max_price_per_night: float | None = None
    currency: str = "CAD"


class CarCriteriaIn(BaseModel):
    pickup_location: str
    dropoff_location: str
    pickup_datetime: str
    dropoff_datetime: str
    currency: str = "CAD"


class SearchRequest(BaseModel):
    flight: FlightCriteriaIn
    hotel: HotelCriteriaIn | None = None
    car: CarCriteriaIn | None = None


class SessionOut(BaseModel):
    session_id: str
    search_type: str
    criteria_json: str
