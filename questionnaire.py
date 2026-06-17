"""Questionnaire CLI pour recueillir les critères de recherche."""
from models import SearchCriteria


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


def run_questionnaire() -> SearchCriteria:
    print("\n=== Agent de recherche de voyage ===\n")

    origin = _ask("Aéroport de départ (code IATA, ex: YUL)").upper()
    destination = _ask("Aéroport d'arrivée (code IATA, ex: CDG)").upper()
    departure_date = _ask("Date de départ (YYYY-MM-DD)")
    return_date_raw = _ask("Date de retour (YYYY-MM-DD, laisser vide = aller simple)")
    return_date = return_date_raw if return_date_raw else None

    adults = _ask_int("Nombre de passagers adultes", default=1)
    currency = _ask("Devise", default="CAD")

    max_stops_raw = _ask_optional_int("Nombre max d'escales (ex: 0 = direct, 1 = 1 escale)")
    max_price_raw = _ask_optional_int(f"Budget max ({currency})")

    carriers_raw = _ask("Compagnies préférées (codes IATA séparés par virgule, ex: AC,AF, laisser vide = toutes)")
    preferred_carriers = [c.strip().upper() for c in carriers_raw.split(",") if c.strip()] if carriers_raw else []

    flexible_days = _ask_int("Flexibilité en jours (±N jours autour de la date, 0 = date fixe)", default=0)

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
