"""Application FastAPI — point d'entrée de l'API."""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.search import router as search_router
from api.routes.sessions import router as sessions_router

app = FastAPI(title="Vacation Planer API", version="0.1.0")

# FRONTEND_URL : "http://localhost:3001" en dev, URL Railway en prod
# Plusieurs origines séparées par des virgules sont supportées.
_raw = os.environ.get("FRONTEND_URL", "http://localhost:3001")
_allowed_origins = [o.strip() for o in _raw.split(",") if o.strip()] or ["http://localhost:3001"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search_router, prefix="/api")
app.include_router(sessions_router, prefix="/api")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}
