"""Point d'entrée : questionnaire → recherche Duffel → affichage."""
import asyncio

from dotenv import load_dotenv

load_dotenv()

from display import print_results
from models import SearchCriteria
from providers.duffel import DuffelProvider
from questionnaire import run_questionnaire


async def search_and_display(criteria: SearchCriteria) -> None:
    provider = DuffelProvider()
    print("\nRecherche en cours...\n")
    flights = await provider.search(criteria, max_results=10)
    summary = (
        f"{criteria.origin} → {criteria.destination} | "
        f"{criteria.departure_date}"
        + (f" → {criteria.return_date}" if criteria.return_date else " (aller simple)")
        + f" | {criteria.adults} adulte(s)"
    )
    print_results(flights, criteria_summary=summary)


def main() -> None:
    criteria = run_questionnaire()
    asyncio.run(search_and_display(criteria))


if __name__ == "__main__":
    main()
