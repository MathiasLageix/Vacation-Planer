"""Fournisseur de location d'autos — stub Phase 2.

Aucune API de location de voitures n'est disponible via Duffel.
Les candidats pour la Phase 3 : RentalCars API, CarTrawler, ou Rentalcars.com affiliate.
En attendant, ce provider retourne une liste vide et affiche un avertissement.
"""
from models import CarSearchCriteria, NormalizedCar


class CarsProvider:
    async def search(
        self, criteria: CarSearchCriteria, max_results: int = 10
    ) -> list[NormalizedCar]:
        return []

    @property
    def is_stub(self) -> bool:
        return True

    @property
    def stub_message(self) -> str:
        return (
            "Location d'autos : aucun fournisseur connecté pour l'instant. "
            "Consultez Google Cars ou Kayak directement : "
            f"https://www.kayak.com/cars/{self._pickup_hint}"
        )

    def _pickup_hint(self) -> str:
        return ""
