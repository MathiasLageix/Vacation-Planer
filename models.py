"""Modèle de données normalisé commun à tous les fournisseurs."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Optional


# ---------------------------------------------------------------------------
# Vols
# ---------------------------------------------------------------------------

@dataclass
class FlightSegment:
    origin: str
    destination: str
    departure_at: datetime
    arrival_at: datetime
    carrier_code: str
    flight_number: str
    duration_minutes: int


@dataclass
class NormalizedFlight:
    provider: str
    offer_id: str
    total_price: float
    currency: str
    stops: int
    segments: list[FlightSegment]
    deep_link: str
    raw: dict = field(default_factory=dict, repr=False)

    @property
    def carrier_codes(self) -> list[str]:
        return list({s.carrier_code for s in self.segments})

    @property
    def total_duration_minutes(self) -> int:
        return sum(s.duration_minutes for s in self.segments)


@dataclass
class SearchCriteria:
    origin: str
    destination: str
    departure_date: str
    return_date: Optional[str]
    adults: int = 1
    children: int = 0
    max_stops: Optional[int] = None
    preferred_carriers: list[str] = field(default_factory=list)
    max_price: Optional[float] = None
    currency: str = "CAD"
    flexible_days: int = 0


# ---------------------------------------------------------------------------
# Hôtels
# ---------------------------------------------------------------------------

@dataclass
class NormalizedHotel:
    provider: str
    property_id: str
    name: str
    stars: Optional[int]
    price_per_night: float
    total_price: float
    currency: str
    check_in: str
    check_out: str
    nights: int
    address: str
    deep_link: str
    raw: dict = field(default_factory=dict, repr=False)


@dataclass
class HotelSearchCriteria:
    city_iata: str           # Code IATA de ville, ex: "PAR"
    check_in: str            # YYYY-MM-DD
    check_out: str           # YYYY-MM-DD
    adults: int = 1
    rooms: int = 1
    max_price_per_night: Optional[float] = None
    currency: str = "CAD"


# ---------------------------------------------------------------------------
# Autos
# ---------------------------------------------------------------------------

@dataclass
class NormalizedCar:
    provider: str
    offer_id: str
    category: str            # "economy", "compact", "SUV", etc.
    company: str
    price_per_day: float
    total_price: float
    currency: str
    pickup_location: str
    dropoff_location: str
    pickup_datetime: str
    dropoff_datetime: str
    deep_link: str
    raw: dict = field(default_factory=dict, repr=False)


@dataclass
class CarSearchCriteria:
    pickup_location: str     # Code IATA aéroport, ex: "CDG"
    dropoff_location: str
    pickup_datetime: str     # YYYY-MM-DDTHH:MM
    dropoff_datetime: str
    currency: str = "CAD"


# ---------------------------------------------------------------------------
# Insights
# ---------------------------------------------------------------------------

@dataclass
class PriceInsight:
    offer_id: str
    label: str
    old_price: float
    new_price: float
    delta: float
    pct_change: float
    currency: str


@dataclass
class AvailabilityInsight:
    offer_id: str
    label: str
    event: Literal["disappeared", "appeared"]
    price: float
    currency: str


@dataclass
class InsightReport:
    session_id: str
    search_type: str
    snapshot_old_at: datetime
    snapshot_new_at: datetime
    price_changes: list[PriceInsight] = field(default_factory=list)
    availability: list[AvailabilityInsight] = field(default_factory=list)

    @property
    def has_insights(self) -> bool:
        return bool(self.price_changes or self.availability)
