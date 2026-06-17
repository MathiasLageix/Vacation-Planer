# TODOS

## Phase 3 — Roadmap restant

### Airbnb / VRBO (scraping)
**Priority:** P2
Ajouter les hébergements Airbnb/VRBO via scraping prudent (pas d'API publique).

### Alertes de prix
**Priority:** P2
Notifier l'utilisateur par email/push quand un prix dépasse un seuil défini.

### Autos (provider réel)
**Priority:** P3
Trouver un provider API pour la location de voitures (actuellement stub `providers/cars.py`).

### Postgres
**Priority:** P3
Migrer de SQLite vers Postgres pour la production.

## Technique / Qualité

### Rate limiting sur POST /api/search
**Priority:** P2
Sans rate limiting, un bot peut déclencher des appels Duffel illimités. Ajouter un throttle (ex. `slowapi` ou middleware custom) avec un quota par IP.

### Validation codes IATA
**Priority:** P3
Les champs `origin` / `destination` acceptent n'importe quelle chaîne. Valider au format IATA 3 lettres ([A-Z]{3}) dans les schémas Pydantic pour éviter des appels Duffel invalides.

### Pagination GET /api/sessions
**Priority:** P3
`get_all_sessions()` retourne toutes les sessions sans limite. Ajouter `limit` + `offset` pour les utilisateurs avec beaucoup d'historique.

### SQLAlchemy async (non-bloquant)
**Priority:** P3
`storage.py` utilise SQLAlchemy synchrone dans un contexte async FastAPI — bloque la boucle d'événements sous charge. Migrer vers `sqlalchemy.ext.asyncio`.

### Race condition dans `get_or_create_session`
**Priority:** P3
Double appel concurrent peut créer deux sessions identiques. Ajouter une contrainte UNIQUE sur le hash de critères ou un verrou applicatif.

### Pruning des snapshots
**Priority:** P3
Les snapshots s'accumulent indéfiniment dans SQLite. Ajouter une purge automatique (ex. garder les 30 derniers jours) dans `storage.py`.

### Tests scheduler.py
**Priority:** P3
`scheduler.py` n'a aucune couverture de test. Ajouter des tests unitaires pour la logique de re-check et le mode `--once`.

### Tests frontend (Next.js)
**Priority:** P3
Pas de framework de test JS en place. Ajouter Vitest ou Jest + React Testing Library pour couvrir les composants critiques (`SearchForm`, `FlightCard`, lecture SSE).

### Variables d'environnement pour CORS et URL backend
**Priority:** P3
CORS origin (`http://localhost:3001`) et URL backend Next.js (`http://localhost:8000`) sont en dur dans le code. Externaliser dans `.env` pour les déploiements non-locaux.

## Completed

### UI Web FastAPI + Next.js
**Priority:** P1
**Completed:** v0.3.0.0 (2026-06-16)
Backend FastAPI avec SSE streaming (`/api/search`, `/api/sessions`, `/api/health`) + frontend Next.js 14 (formulaire multistep, page résultats temps réel, cards vols/hôtels, InsightBadge).

### Vols Duffel
**Priority:** P1
**Completed:** v0.1.0.0 (2026-06-16)
Intégration Duffel pour la recherche de vols — remplacement Amadeus décommissionné 2026-07-17.

### Hébergements Duffel Stays
**Priority:** P1
**Completed:** v0.1.0.0 (2026-06-16)
Intégration Duffel Stays API pour la recherche d'hôtels avec snapshots et insights.

### Stockage SQLite + Insights
**Priority:** P1
**Completed:** v0.1.0.0 (2026-06-16)
Snapshots horodatés via SQLAlchemy + couche d'insights (diff prix/dispo entre snapshots).

### Scheduler APScheduler (Phase 2)
**Priority:** P1
**Completed:** v0.1.0.0 (2026-06-16)
Daemon de re-check périodique via APScheduler — relance les recherches sauvegardées, génère des insights automatiquement.
