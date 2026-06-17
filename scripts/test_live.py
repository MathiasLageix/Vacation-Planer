"""Test bout-en-bout rapide avec l'API Duffel réelle."""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from display import print_results
from models import SearchCriteria
from providers.duffel import DuffelProvider


async def main() -> None:
    criteria = SearchCriteria(
        origin="YUL",
        destination="CDG",
        departure_date="2026-09-15",
        return_date=None,
        adults=1,
        currency="CAD",
    )
    print(f"\nTest live Duffel : {criteria.origin} → {criteria.destination} le {criteria.departure_date}\n")
    provider = DuffelProvider()
    flights = await provider.search(criteria, max_results=5)
    print_results(flights, criteria_summary=f"{criteria.origin} → {criteria.destination} | {criteria.departure_date}")


if __name__ == "__main__":
    asyncio.run(main())
