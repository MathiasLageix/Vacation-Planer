"""Route POST /api/search — SSE stream des résultats."""
import asyncio
import json
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from api.deps import get_storage
from api.schemas import SearchRequest
from main import search_core
from models import CarSearchCriteria, HotelSearchCriteria, SearchCriteria

router = APIRouter()
_log = logging.getLogger(__name__)


def _to_sse(event_type: str, data: dict | str) -> str:
    payload = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False)
    return f"event: {event_type}\ndata: {payload}\n\n"


@router.post("/search")
async def search(req: SearchRequest) -> StreamingResponse:
    try:
        flight_criteria = SearchCriteria(**req.flight.model_dump())
        hotel_criteria = HotelSearchCriteria(**req.hotel.model_dump()) if req.hotel else None
        car_criteria = CarSearchCriteria(**req.car.model_dump()) if req.car else None
    except Exception:
        raise HTTPException(status_code=422, detail={"code": "INVALID_INPUT", "message": "Les données soumises sont invalides."})

    async def event_stream():
        yield _to_sse("status", {"message": "Recherche en cours…"})
        await asyncio.sleep(0)  # flush immédiat

        try:
            result = await asyncio.wait_for(
                search_core(flight_criteria, hotel_criteria, car_criteria, get_storage(), max_hotel_results=5),
                timeout=30.0,
            )
        except asyncio.TimeoutError:
            yield _to_sse("error", {"message": "La recherche a pris trop de temps. Réessayez."})
            return
        except Exception:
            _log.exception("Erreur lors de la recherche")
            yield _to_sse("error", {"message": "Une erreur interne est survenue. Réessayez."})
            return

        if result.get("flight_error"):
            yield _to_sse("error", {"message": result["flight_error"]})
            return

        try:
            yield _to_sse("flights", {"data": result["flights"]})
            await asyncio.sleep(0)

            if result["hotels"]:
                yield _to_sse("hotels", {"data": result["hotels"]})
                await asyncio.sleep(0)

            if result["flight_insights"]:
                yield _to_sse("insights", {"type": "flight", "data": result["flight_insights"]})

            if result["hotel_insights"]:
                yield _to_sse("insights", {"type": "hotel", "data": result["hotel_insights"]})

            yield _to_sse("done", {"session_id": result["session_id"]})
        except Exception:
            _log.exception("Erreur lors de la sérialisation SSE")
            yield _to_sse("error", {"message": "Une erreur interne est survenue. Réessayez."})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
