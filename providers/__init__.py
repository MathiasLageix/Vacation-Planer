"""Fournisseurs de voyage — chacun expose search() -> list[NormalizedFlight]."""
from providers.duffel import DuffelProvider

__all__ = ["DuffelProvider"]
