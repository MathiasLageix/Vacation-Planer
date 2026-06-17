"""Route GET /api/sessions — liste des sessions sauvegardées."""
from fastapi import APIRouter

from api.schemas import SessionOut
from storage import Storage

router = APIRouter()


@router.get("/sessions", response_model=list[SessionOut])
def list_sessions() -> list[SessionOut]:
    storage = Storage()
    rows = storage.get_all_sessions()
    return [
        SessionOut(session_id=sid, search_type=stype, criteria_json=cjson)
        for sid, stype, cjson in rows
    ]
