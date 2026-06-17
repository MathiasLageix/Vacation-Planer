"""Persistance SQLite des snapshots de résultats de recherche."""
import hashlib
import json
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, mapped_column

from models import (
    NormalizedCar,
    NormalizedFlight,
    NormalizedHotel,
)

NormalizedResult = NormalizedFlight | NormalizedHotel | NormalizedCar


class Base(DeclarativeBase):
    pass


class SearchSessionRow(Base):
    __tablename__ = "search_sessions"

    id = Column(String, primary_key=True)
    search_type = Column(String, nullable=False)   # "flight" | "hotel" | "car"
    criteria_hash = Column(String, nullable=False)  # SHA256 des critères
    criteria_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class SnapshotRow(Base):
    __tablename__ = "snapshots"

    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("search_sessions.id"), nullable=False)
    captured_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    results_json = Column(Text, nullable=False)
    result_count = Column(Integer, nullable=False)


def _criteria_hash(criteria_dict: dict) -> str:
    canonical = json.dumps(criteria_dict, sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


def _serialize(results: list[NormalizedResult]) -> str:
    def default(o: Any) -> Any:
        if isinstance(o, datetime):
            return o.isoformat()
        raise TypeError(f"Not serializable: {type(o)}")

    serialized = []
    for r in results:
        d = asdict(r)
        # Retire raw (verbeux, non utile pour les insights)
        d.pop("raw", None)
        serialized.append(d)
    return json.dumps(serialized, default=default)


def _deserialize_flights(data: list[dict]) -> list[NormalizedFlight]:
    from models import FlightSegment
    flights = []
    for d in data:
        d["segments"] = [
            FlightSegment(
                **{k: datetime.fromisoformat(v) if k.endswith("_at") else v
                   for k, v in seg.items()}
            )
            for seg in d.get("segments", [])
        ]
        d.setdefault("raw", {})
        flights.append(NormalizedFlight(**d))
    return flights


def _deserialize_hotels(data: list[dict]) -> list[NormalizedHotel]:
    for d in data:
        d.setdefault("raw", {})
    return [NormalizedHotel(**d) for d in data]


class Storage:
    def __init__(self, database_url: str = "sqlite:///travel_agent.db") -> None:
        self._engine = create_engine(database_url)
        Base.metadata.create_all(self._engine)

    def _session(self) -> Session:
        return Session(self._engine)

    def get_or_create_session(
        self, search_type: str, criteria_dict: dict
    ) -> str:
        chash = _criteria_hash(criteria_dict)
        with self._session() as db:
            row = (
                db.query(SearchSessionRow)
                .filter_by(search_type=search_type, criteria_hash=chash)
                .first()
            )
            if row:
                return row.id
            session_id = str(uuid.uuid4())
            db.add(
                SearchSessionRow(
                    id=session_id,
                    search_type=search_type,
                    criteria_hash=chash,
                    criteria_json=json.dumps(criteria_dict, default=str),
                )
            )
            db.commit()
            return session_id

    def save_snapshot(
        self, session_id: str, results: list[NormalizedResult]
    ) -> str:
        snapshot_id = str(uuid.uuid4())
        with self._session() as db:
            db.add(
                SnapshotRow(
                    id=snapshot_id,
                    session_id=session_id,
                    captured_at=datetime.now(timezone.utc),
                    results_json=_serialize(results),
                    result_count=len(results),
                )
            )
            db.commit()
        return snapshot_id

    def get_latest_snapshots(
        self, session_id: str, limit: int = 2
    ) -> list[tuple[datetime, list[dict]]]:
        """Retourne les `limit` snapshots les plus récents, du plus ancien au plus récent."""
        with self._session() as db:
            rows = (
                db.query(SnapshotRow)
                .filter_by(session_id=session_id)
                .order_by(SnapshotRow.captured_at.desc())
                .limit(limit)
                .all()
            )
        result = []
        for row in reversed(rows):
            result.append((row.captured_at, json.loads(row.results_json)))
        return result
