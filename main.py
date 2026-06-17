"""Point d'entrée : questionnaire → recherches parallèles → snapshots → insights → affichage."""
import asyncio
from dataclasses import asdict

from dotenv import load_dotenv

load_dotenv()

from display import print_cars, print_flights, print_hotels, print_insights
from insights import compare_snapshots
from models import CarSearchCriteria, HotelSearchCriteria, SearchCriteria
from providers.cars import CarsProvider
from providers.duffel import DuffelProvider
from providers.duffel_stays import DuffelStaysProvider
from questionnaire import run_questionnaire
from storage import Storage


async def search_core(
    flight_criteria: SearchCriteria,
    hotel_criteria: HotelSearchCriteria | None,
    car_criteria: CarSearchCriteria | None,
    storage: Storage,
    max_hotel_results: int = 10,
) -> dict:
    """Logique de recherche pure : retourne un dict structuré sans rien imprimer.

    Utilisé par l'API FastAPI et par run_search() (CLI).
    """
    flight_provider = DuffelProvider()
    hotel_provider = DuffelStaysProvider()
    car_provider = CarsProvider()

    tasks = [flight_provider.search(flight_criteria, max_results=10)]
    if hotel_criteria:
        tasks.append(hotel_provider.search(hotel_criteria, max_results=max_hotel_results))
    if car_criteria:
        tasks.append(car_provider.search(car_criteria, max_results=10))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    flights = results[0] if not isinstance(results[0], Exception) else []
    hotels = results[1] if hotel_criteria and len(results) > 1 and not isinstance(results[1], Exception) else []
    cars = results[-1] if car_criteria and not isinstance(results[-1], Exception) else []

    flight_error = str(results[0]) if isinstance(results[0], Exception) else None

    # Snapshots + insights vols
    flight_session = storage.get_or_create_session("flight", asdict(flight_criteria))
    storage.save_snapshot(flight_session, flights)
    flight_snapshots = storage.get_latest_snapshots(flight_session, limit=2)

    flight_insights = None
    if len(flight_snapshots) >= 2:
        (old_at, old_data), (new_at, new_data) = flight_snapshots[0], flight_snapshots[1]
        flight_insights = compare_snapshots(flight_session, "flight", old_at, old_data, new_at, new_data)

    # Snapshots + insights hôtels
    hotel_insights = None
    if hotel_criteria and hotels:
        hotel_session = storage.get_or_create_session("hotel", asdict(hotel_criteria))
        storage.save_snapshot(hotel_session, hotels)
        hotel_snapshots = storage.get_latest_snapshots(hotel_session, limit=2)
        if len(hotel_snapshots) >= 2:
            (old_at, old_data), (new_at, new_data) = hotel_snapshots[0], hotel_snapshots[1]
            hotel_insights = compare_snapshots(hotel_session, "hotel", old_at, old_data, new_at, new_data)

    def _serialize_insights(ins) -> dict | None:
        if ins is None:
            return None
        return {
            "session_id": ins.session_id,
            "search_type": ins.search_type,
            "snapshot_old_at": ins.snapshot_old_at.isoformat(),
            "snapshot_new_at": ins.snapshot_new_at.isoformat(),
            "price_changes": [asdict(p) for p in ins.price_changes],
            "availability": [asdict(a) for a in ins.availability],
        }

    def _serialize_flight(f) -> dict:
        d = asdict(f)
        # Convertit les datetime des segments en ISO string
        for seg in d.get("segments", []):
            if hasattr(seg.get("departure_at"), "isoformat"):
                seg["departure_at"] = seg["departure_at"].isoformat()
            if hasattr(seg.get("arrival_at"), "isoformat"):
                seg["arrival_at"] = seg["arrival_at"].isoformat()
        d.pop("raw", None)
        return d

    return {
        "session_id": flight_session,
        "flights": [_serialize_flight(f) for f in flights],
        "hotels": [asdict(h) | {"raw": None} for h in hotels],
        "cars": [asdict(c) | {"raw": None} for c in cars],
        "flight_insights": _serialize_insights(flight_insights),
        "hotel_insights": _serialize_insights(hotel_insights),
        "flight_error": flight_error,
        "car_stub_message": car_provider.stub_message if car_provider.is_stub else None,
    }


async def run_search(
    flight_criteria: SearchCriteria,
    hotel_criteria: HotelSearchCriteria | None,
    car_criteria: CarSearchCriteria | None,
    storage: Storage,
) -> None:
    print("\nRecherche en cours (vols" + (", hôtels" if hotel_criteria else "") + (", autos" if car_criteria else "") + ")...\n")

    data = await search_core(flight_criteria, hotel_criteria, car_criteria, storage)

    if data["flight_error"]:
        print(f"[Erreur vols] {data['flight_error']}")

    # Re-hydrate pour display (display.py attend les objets dataclass)
    from models import NormalizedFlight, NormalizedHotel, FlightSegment
    from datetime import datetime

    def _hydrate_flight(d: dict) -> NormalizedFlight:
        segs = [
            FlightSegment(
                **{k: datetime.fromisoformat(v) if k.endswith("_at") else v for k, v in seg.items()}
            )
            for seg in d.get("segments", [])
        ]
        return NormalizedFlight(
            provider=d["provider"], offer_id=d["offer_id"],
            total_price=d["total_price"], currency=d["currency"],
            stops=d["stops"], segments=segs, deep_link=d["deep_link"],
        )

    def _hydrate_hotel(d: dict) -> NormalizedHotel:
        d = {k: v for k, v in d.items() if k != "raw"}
        return NormalizedHotel(**d)

    flights = [_hydrate_flight(f) for f in data["flights"]]
    hotels = [_hydrate_hotel(h) for h in data["hotels"]]

    flight_summary = (
        f"{flight_criteria.origin} → {flight_criteria.destination} | {flight_criteria.departure_date}"
        + (f" → {flight_criteria.return_date}" if flight_criteria.return_date else " (aller simple)")
        + f" | {flight_criteria.adults} adulte(s)"
    )
    print_flights(flights, criteria_summary=flight_summary)
    if data["flight_insights"]:
        from models import InsightReport, PriceInsight, AvailabilityInsight
        from datetime import datetime
        ins = data["flight_insights"]
        report = InsightReport(
            session_id=ins["session_id"],
            search_type=ins["search_type"],
            snapshot_old_at=datetime.fromisoformat(ins["snapshot_old_at"]),
            snapshot_new_at=datetime.fromisoformat(ins["snapshot_new_at"]),
            price_changes=[PriceInsight(**p) for p in ins["price_changes"]],
            availability=[AvailabilityInsight(**a) for a in ins["availability"]],
        )
        print_insights(report)

    if hotel_criteria:
        hotel_summary = f"{hotel_criteria.city_iata} | {hotel_criteria.check_in} → {hotel_criteria.check_out}"
        print_hotels(hotels, criteria_summary=hotel_summary)

    if hotel_criteria and data["hotel_insights"]:
        from models import InsightReport, PriceInsight, AvailabilityInsight
        from datetime import datetime
        ins = data["hotel_insights"]
        report = InsightReport(
            session_id=ins["session_id"],
            search_type=ins["search_type"],
            snapshot_old_at=datetime.fromisoformat(ins["snapshot_old_at"]),
            snapshot_new_at=datetime.fromisoformat(ins["snapshot_new_at"]),
            price_changes=[PriceInsight(**p) for p in ins["price_changes"]],
            availability=[AvailabilityInsight(**a) for a in ins["availability"]],
        )
        print_insights(report)

    if data.get("car_stub_message"):
        print_cars([], stub_message=data["car_stub_message"])


def main() -> None:
    flight_criteria, hotel_criteria, car_criteria = run_questionnaire()
    storage = Storage()
    asyncio.run(run_search(flight_criteria, hotel_criteria, car_criteria, storage))


if __name__ == "__main__":
    main()
