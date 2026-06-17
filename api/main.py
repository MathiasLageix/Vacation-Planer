"""Application FastAPI — point d'entrée de l'API."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.search import router as search_router
from api.routes.sessions import router as sessions_router

app = FastAPI(title="Vacation Planer API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search_router, prefix="/api")
app.include_router(sessions_router, prefix="/api")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}
