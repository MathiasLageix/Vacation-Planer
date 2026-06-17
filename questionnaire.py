"""Questionnaire CLI pour recueillir les critères de recherche."""
from models import CarSearchCriteria, HotelSearchCriteria, SearchCriteria


def _ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{prompt}{suffix}: ").strip()
    return value or default


def _ask_int(prompt: str, default: int) -> int:
    raw = _ask(prompt, str(default))
    try:
        return int(raw)
    except ValueError:
        return default


def _ask_optional_int(prompt: str) -> int | None:
    raw = _ask(prompt + " (laisser vide = pas de limite)")
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def _ask_bool(prompt: str, default: bool = True) -> bool:
    default_hint = "O/n" if default else "o/N"
    raw = _ask(f"{prompt} [{default_hint}]").lower()
    if not raw:
        return default
    return raw in ("o", "oui", "y", "yes")


def _ask_flight_criteria() -> SearchCriteria:
    print("\n--- Vols ---")
    origin = _ask("Aéroport de départ (IATA, ex: YUL)").upper()
    destination = _ask("Aéroport d'arrivée (IATA, ex: CDG)").upper()
    departure_date = _ask("Date de départ (YYYY-MM-DD)")
    return_date_raw = _ask("Date de retour (YYYY-MM-DD, vide = aller simple)")
    return_date = return_date_raw if return_date_raw else None

    adults = _ask_int("Nombre de passagers adultes", default=1)
    currency = _ask("Devise", default="CAD")
    max_stops_raw = _ask_optional_int("Nombre max d'escales (0 = direct, 1 = 1 escale)")
    max_price_raw = _ask_optional_int(f"Budget max vol ({currency})")
    carriers_raw = _ask(
        "Compagnies préférées (IATA séparés par virgule, ex: AC,AF — vide = toutes)"
    )
    preferred_carriers = [c.strip().upper() for c in carriers_raw.split(",") if c.strip()]
    flexible_days = _ask_int("Flexibilité ±N jours (0 = date fixe)", default=0)

    return SearchCriteria(
        origin=origin,
        destination=destination,
        departure_date=departure_date,
        return_date=return_date,
        adults=adults,
        max_stops=max_stops_raw,
        preferred_carriers=preferred_carriers,
        max_price=float(max_price_raw) if max_price_raw else None,
        currency=currency,
        flexible_days=flexible_days,
    )


def _ask_hotel_criteria(flight: SearchCriteria) -> HotelSearchCriteria:
    print("\n--- Hébergement ---")
    # Déduit la ville de destination depuis le code aéroport (approximation : même code IATA)
    # Les codes IATA de ville diffèrent parfois (ex: NYC vs JFK/LGA/EWR)
    city_iata = _ask(
        f"Code IATA de la ville d'arrivée (ex: PAR pour Paris)",
        default=flight.destination,
    ).upper()
    check_in = _ask("Date d'arrivée à l'hôtel (YYYY-MM-DD)", default=flight.departure_date)
    check_out_default = flight.return_date or ""
    check_out = _ask("Date de départ de l'hôtel (YYYY-MM-DD)", default=check_out_default)
    adults = _ask_int("Adultes", default=flight.adults)
    rooms = _ask_int("Chambres", default=1)
    max_ppn_raw = _ask_optional_int(f"Budget max par nuit ({flight.currency})")

    return HotelSearchCriteria(
        city_iata=city_iata,
        check_in=check_in,
        check_out=check_out,
        adults=adults,
        rooms=rooms,
        max_price_per_night=float(max_ppn_raw) if max_ppn_raw else None,
        currency=flight.currency,
    )


def _ask_car_criteria(flight: SearchCriteria) -> CarSearchCriteria:
    print("\n--- Location de voiture ---")
    pickup = _ask("Lieu de prise en charge (IATA aéroport)", default=flight.destination).upper()
    dropoff = _ask("Lieu de retour (IATA aéroport)", default=pickup).upper()
    pickup_dt = _ask("Date/heure de prise en charge (YYYY-MM-DDTHH:MM)", default=f"{flight.departure_date}T10:00")
    dropoff_default = f"{flight.return_date}T10:00" if flight.return_date else ""
    dropoff_dt = _ask("Date/heure de retour (YYYY-MM-DDTHH:MM)", default=dropoff_default)

    return CarSearchCriteria(
        pickup_location=pickup,
        dropoff_location=dropoff,
        pickup_datetime=pickup_dt,
        dropoff_datetime=dropoff_dt,
        currency=flight.currency,
    )


def run_questionnaire() -> tuple[
    SearchCriteria,
    HotelSearchCriteria | None,
    CarSearchCriteria | None,
]:
    print("\n=== Agent de recherche de voyage ===\n")

    flight_criteria = _ask_flight_criteria()

    hotel_criteria: HotelSearchCriteria | None = None
    if _ask_bool("Rechercher des hébergements ?"):
        hotel_criteria = _ask_hotel_criteria(flight_criteria)

    car_criteria: CarSearchCriteria | None = None
    if _ask_bool("Rechercher une location de voiture ?"):
        car_criteria = _ask_car_criteria(flight_criteria)

    return flight_criteria, hotel_criteria, car_criteria
