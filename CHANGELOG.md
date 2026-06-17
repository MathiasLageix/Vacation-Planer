# Changelog

All notable changes to this project will be documented in this file.

Format: `## [MAJOR.MINOR.PATCH.MICRO] - YYYY-MM-DD`

## [0.3.2.0] - 2026-06-17

### Fixed
- **`Procfile`** : Nixpacks détecte `main.py` à la racine et génère automatiquement `uvicorn main:app` — qui échoue car `main.py` (CLI agent) n'a pas de variable `app`. Le `Procfile` est prioritaire sur l'auto-détection et pointe explicitement vers `api.main:app`

## [0.3.1.0] - 2026-06-17

### Added
- **Déploiement Railway** : `railway.toml` pour le backend FastAPI et `frontend/railway.toml` pour le frontend Next.js (Nixpacks builder, healthcheck, restart policy)
- **Script `deploy.sh`** : déploie backend et/ou frontend via `railway up --service` avec `set -euo pipefail`
- **`make install`** / **`make start-api`** / **`make start-web`** : cibles production pour Railway

### Fixed
- **Proxy API runtime** : l'URL du backend (`API_URL`) était évaluée au moment du build Next.js (baked dans `routes-manifest.json`) — remplacée par un route handler App Router (`app/api/[...path]/route.ts`) qui lit l'env var à chaque requête, rendant le proxy fonctionnel sur Railway
- **CORS fallback** : si `FRONTEND_URL` est une chaîne vide, `_allowed_origins` restait `[]` et bloquait toutes les requêtes browser — ajout d'un fallback `or ["http://localhost:3001"]`
- **PORT fallback** dans `railway.toml` : `$PORT` → `${PORT:-8000}` pour cohérence avec le Makefile

### Changed
- **`frontend/next.config.mjs`** : suppression du rewrite `/api/*` (remplacé par le route handler, plus de build-time evaluation de `API_URL`)
- **`frontend/package.json`** : `next start --port 3001` → `next start --port ${PORT:-3001}` (Railway injecte `$PORT`)
- **`requirements.txt` + `pyproject.toml`** : suppression de `amadeus>=12.0.0` (décommissionné 2026-07-17, jamais utilisé)
- **`.env.example`** : mise à jour pour refléter Duffel-only + variables Railway documentées

## [0.3.0.0] - 2026-06-16

### Added
- **Interface web complète** : formulaire de recherche multistep (vols → hôtels → autos) et page de résultats avec streaming temps réel via Next.js 14 + Tailwind CSS
- **Backend FastAPI** avec endpoint SSE `POST /api/search` — les résultats vols, hôtels et insights arrivent en flux au fur et à mesure
- **GET /api/sessions** pour lister les recherches passées, **GET /api/health** pour le healthcheck
- **Schémas Pydantic v2** (`api/schemas.py`) avec validation stricte : `flexible_days` borné 0–5, champs requis/optionnels, conversion automatique des critères en dataclasses internes
- **`search_core()`** extrait de `main.py` — logique de recherche testable indépendamment du CLI et de l'API
- **`make dev`** lance FastAPI (:8000) et Next.js (:3001) en parallèle
- **Proxy Next.js** : `/api/*` → `http://localhost:8000/api/*` (pas de CORS à gérer)
- **`InsightBadge`** : badge coloré affiché si un prix a changé ou une dispo évolué depuis la dernière recherche
- **30 nouveaux tests** couvrant les routes SSE, `search_core()`, schémas Pydantic, deep links Duffel, parsing hôtels et stub autos

### Fixed
- **`flexible_days` faisait systématiquement timeout** : les appels Duffel multi-dates étaient séquentiels (11 × ~5s = 55s > timeout 30s). Maintenant parallélisés avec `asyncio.gather()`.
- **XSS via `deep_link`** : les `href` dans `FlightCard` et `HotelCard` vérifient désormais `startsWith("https://")` avant de rendre le lien cliquable
- **Fuite d'erreur interne** : le message d'erreur 422 ne reflète plus le détail de l'exception Python côté serveur
- **Parsing hôtels Duffel Stays** : gestion des deux formats de réponse API (`data` = liste ou `data.results` = liste)
- **Isolation des tests** : `test_sessions_empty` mocke désormais `Storage` pour éviter la pollution entre tests
- **`scheduler.py`** : ajout du daemon APScheduler avec re-check périodique et mode `--once` pour les tests
- **`storage.py`** : ajout de `get_all_sessions()` avec couverture de test

### Changed
- `run_search()` dans `main.py` délègue maintenant à `search_core()` — le CLI reste fonctionnel sans modification
- Les erreurs non gérées dans le stream SSE retournent un événement `error` générique plutôt que d'interrompre le stream silencieusement

## [0.2.0.0] - 2026-06-16

### Added
- Hôtels via Duffel Stays API (`providers/duffel_stays.py`)
- Stub autos (`providers/cars.py`) — en attente d'un provider API
- Stockage SQLite avec snapshots horodatés (`storage.py`, SQLAlchemy)
- Insights de prix et de disponibilité (`insights.py`) — diff entre deux snapshots
- Questionnaire étendu (hôtels + autos optionnels)
- Recherches parallèles (`asyncio.gather`) dans `main.py`

## [0.1.0.0] - 2026-06-16

### Added
- Recherche de vols via Duffel API (`providers/duffel.py`)
- Questionnaire CLI de critères (origine, destination, dates, budget, compagnie)
- Normalisation des résultats et deep links Google Flights préremplis
- Affichage tabulaire (`display.py`)
