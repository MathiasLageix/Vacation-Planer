"""Modèle de données normalisé commun à tous les fournisseurs."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


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
    provider: str  # "amadeus" | "duffel"
    offer_id: str
    total_price: float
    currency: str
    stops: int  # 0 = direct
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
    departure_date: str          # YYYY-MM-DD
    return_date: Optional[str]   # None = aller simple
    adults: int = 1
    max_stops: Optional[int] = None
    preferred_carriers: list[str] = field(default_factory=list)
    max_price: Optional[float] = None
    currency: str = "CAD"
    flexible_days: int = 0       # ±N jours autour de la date
