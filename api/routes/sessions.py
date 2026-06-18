"""Route GET /api/sessions — liste des sessions sauvegardées."""
from fastapi import APIRouter

from api.deps import get_storage
from api.schemas import SessionOut

router = APIRouter()


@router.get("/sessions", response_model=list[SessionOut])
def list_sessions() -> list[SessionOut]:
    storage = get_storage()
    rows = storage.get_all_sessions()
    return [
        SessionOut(session_id=sid, search_type=stype, criteria_json=cjson)
        for sid, stype, cjson in rows
    ]
