"""Scheduler APScheduler : re-check périodique des sessions de recherche sauvegardées.

Usage :
    python scheduler.py                  # démarre le daemon (toutes les 30 min)
    python scheduler.py --interval 60    # toutes les 60 minutes
    python scheduler.py --once           # un seul check puis quitte (utile en test)
"""
import argparse
import asyncio
import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime, timezone

from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv

load_dotenv()

from display import print_insights
from insights import compare_snapshots
from models import CarSearchCriteria, HotelSearchCriteria, SearchCriteria
from providers.cars import CarsProvider
from providers.duffel import DuffelProvider
from providers.duffel_stays import DuffelStaysProvider
from storage import Storage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger(__name__)


@dataclass
class SchedulerConfig:
    interval_minutes: int = 30
    max_results: int = 10


async def _recheck_session(
    session_id: str,
    search_type: str,
    criteria_json: str,
    storage: Storage,
    config: SchedulerConfig,
) -> None:
    criteria = json.loads(criteria_json)

    # P2 : filtre les clés inconnues pour survivre aux évolutions de schema
    def _safe_build(cls, data: dict):
        known = cls.__dataclass_fields__
        return cls(**{k: v for k, v in data.items() if k in known})

    try:
        if search_type == "flight":
            results = await DuffelProvider().search(
                _safe_build(SearchCriteria, criteria), max_results=config.max_results
            )
        elif search_type == "hotel":
            results = await DuffelStaysProvider().search(
                _safe_build(HotelSearchCriteria, criteria), max_results=config.max_results
            )
        elif search_type == "car":
            results = await CarsProvider().search(
                _safe_build(CarSearchCriteria, criteria), max_results=config.max_results
            )
        else:
            log.warning("Type de session inconnu : %s", search_type)
            return
    except Exception as exc:
        log.error("Session %s (%s) — erreur recherche : %s", session_id[:8], search_type, exc)
        return

    # P1 : storage séparé du try/except API pour ne pas annuler les autres sessions
    try:
        storage.save_snapshot(session_id, results)
        snapshots = storage.get_latest_snapshots(session_id, limit=2)
    except Exception as exc:
        log.error("Session %s (%s) — erreur storage : %s", session_id[:8], search_type, exc)
        return

    if len(snapshots) < 2:
        log.info("Session %s (%s) — premier snapshot, pas encore d'insights.", session_id[:8], search_type)
        return

    (old_at, old_data), (new_at, new_data) = snapshots[0], snapshots[1]
    report = compare_snapshots(session_id, search_type, old_at, old_data, new_at, new_data)

    if report.has_insights:
        print(
            f"\n[{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}]"
            f" Insights — session {session_id[:8]} ({search_type})"
        )
        print_insights(report)
    else:
        log.info("Session %s (%s) — aucun changement détecté.", session_id[:8], search_type)


def run_check(storage: Storage, config: SchedulerConfig) -> None:
    """Lance un re-check de toutes les sessions enregistrées."""
    sessions = storage.get_all_sessions()
    if not sessions:
        log.info("Aucune session enregistrée — lancez d'abord une recherche via main.py.")
        return

    log.info("Re-check de %d session(s)...", len(sessions))

    async def _run_all() -> None:
        tasks = [
            _recheck_session(sid, stype, cjson, storage, config)
            for sid, stype, cjson in sessions
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

    asyncio.run(_run_all())
    log.info("Re-check terminé.")


def start_scheduler(storage: Storage, config: SchedulerConfig) -> None:
    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(
        run_check,
        trigger="interval",
        minutes=config.interval_minutes,
        args=[storage, config],
        next_run_time=datetime.now(timezone.utc),  # exécute immédiatement au démarrage
        id="travel_recheck",
        max_instances=1,  # évite les chevauchements si un check est lent
    )

    print(
        f"Scheduler démarré — re-check toutes les {config.interval_minutes} min. Ctrl+C pour arrêter."
    )
    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("\nScheduler arrêté.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Scheduler de re-check périodique des voyages.")
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        metavar="MIN",
        help="Intervalle entre les re-checks en minutes (défaut : 30).",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Effectue un seul check puis quitte (utile pour les tests).",
    )
    args = parser.parse_args()

    if args.interval < 1:
        parser.error("--interval doit être ≥ 1 minute.")

    config = SchedulerConfig(interval_minutes=args.interval)
    storage = Storage()

    if args.once:
        run_check(storage, config)
        sys.exit(0)

    start_scheduler(storage, config)


if __name__ == "__main__":
    main()
