"""Fournisseurs de voyage — chacun expose search() -> list[Normalized*]."""
from providers.cars import CarsProvider
from providers.duffel import DuffelProvider
from providers.duffel_stays import DuffelStaysProvider

__all__ = ["DuffelProvider", "DuffelStaysProvider", "CarsProvider"]
