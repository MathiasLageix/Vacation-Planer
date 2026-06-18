"""Dépendances FastAPI — singleton Storage partagé entre les routes."""
from storage import Storage

_storage: Storage | None = None


def get_storage() -> Storage:
    global _storage
    if _storage is None:
        _storage = Storage()
    return _storage
