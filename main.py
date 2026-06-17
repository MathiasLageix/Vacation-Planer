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


async def run_search(
    flight_criteria: SearchCriteria,
    hotel_criteria: HotelSearchCriteria | None,
    car_criteria: CarSearchCriteria | None,
    storage: Storage,
) -> None:
    flight_provider = DuffelProvider()
    hotel_provider = DuffelStaysProvider()
    car_provider = CarsProvider()

    # Recherches en parallèle
    tasks = [flight_provider.search(flight_criteria, max_results=10)]
    if hotel_criteria:
        tasks.append(hotel_provider.search(hotel_criteria, max_results=10))
    if car_criteria:
        tasks.append(car_provider.search(car_criteria, max_results=10))

    print("\nRecherche en cours (vols" + (", hôtels" if hotel_criteria else "") + (", autos" if car_criteria else "") + ")...\n")

    results = await asyncio.gather(*tasks, return_exceptions=True)

    flights = results[0] if not isinstance(results[0], Exception) else []
    hotels = results[1] if hotel_criteria and len(results) > 1 and not isinstance(results[1], Exception) else []
    cars = results[-1] if car_criteria and not isinstance(results[-1], Exception) else []

    if isinstance(results[0], Exception):
        print(f"[Erreur vols] {results[0]}")

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

    # Affichage
    flight_summary = (
        f"{flight_criteria.origin} → {flight_criteria.destination} | {flight_criteria.departure_date}"
        + (f" → {flight_criteria.return_date}" if flight_criteria.return_date else " (aller simple)")
        + f" | {flight_criteria.adults} adulte(s)"
    )
    print_flights(flights, criteria_summary=flight_summary)
    if flight_insights:
        print_insights(flight_insights)

    if hotel_criteria:
        hotel_summary = f"{hotel_criteria.city_iata} | {hotel_criteria.check_in} → {hotel_criteria.check_out}"
        if isinstance(hotels, list):
            print_hotels(hotels, criteria_summary=hotel_summary)
        if hotel_insights:
            print_insights(hotel_insights)

    if car_criteria:
        stub_msg = car_provider.stub_message if car_provider.is_stub else ""
        print_cars(cars, stub_message=stub_msg)


def main() -> None:
    flight_criteria, hotel_criteria, car_criteria = run_questionnaire()
    storage = Storage()
    asyncio.run(run_search(flight_criteria, hotel_criteria, car_criteria, storage))


if __name__ == "__main__":
    main()
