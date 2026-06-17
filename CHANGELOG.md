# Changelog

All notable changes to this project will be documented in this file.

Format: `## [MAJOR.MINOR.PATCH.MICRO] - YYYY-MM-DD`

## [0.4.0.0] - 2026-06-17

### Changed
- **`providers/rapidapi_flights.py`** (nouveau) : remplace Duffel pour la recherche de vols. Utilise l'API Google Flights Live by Matan Rabi (`google-flights-live-api.p.rapidapi.com`). Endpoints POST `/api/google_flights/oneway/v1` et `/roundtrip/v1`. Clé `RAPIDAPI_KEY` dans `.env`.
- **`main.py`** : `DuffelProvider` → `RapidAPIFlightsProvider`. Duffel reste actif pour les hôtels uniquement (`DuffelStaysProvider` inchangé).
- **`.env.example`** : ajout de `RAPIDAPI_KEY`, clarification que Duffel est hôtels uniquement.
- **`tests/test_search_core.py`** : patches mis à jour de `DuffelProvider` → `RapidAPIFlightsProvider`.

### Added
- **`tests/test_rapidapi_flights.py`** : 31 tests couvrant `_to_iata`, `_parse_description` (next-day, explicit +N, fallback), `_parse_one_way`, `_parse_roundtrip`, `_stable_id`, `search()` (tri par prix, max_results, flexible_days, erreur HTTP), et validation du payload (currency lowercase, passengers adults/children, max_stops, preferred_carriers, max_price, endpoints oneway/roundtrip).

## [0.3.7.0] - 2026-06-17

### Fixed
- **`frontend/nixpacks.toml`** : `cacheDirectories = ["/root/.npm"]` — Nixpacks (node.rs) ajoute automatiquement `node_modules/.cache` comme `--mount=type=cache` Docker BuildKit. Quand `npm ci` essaie de supprimer `node_modules`, Linux refuse `rmdir /app/node_modules/.cache` avec EBUSY car c'est un point de montage Docker actif. En overridant `cacheDirectories` pour ne garder que `/root/.npm`, Nixpacks ne crée plus ce mount et `npm ci` peut supprimer librement `node_modules`. `NPM_CONFIG_CACHE` ne corrigeait pas ce bug (contrôle le cache de tarballs npm, pas le cache mount Nixpacks).
- **`frontend/.npmrc`** : suppression de `cache=/tmp/npm` — cohérent avec la suppression de `NPM_CONFIG_CACHE` ; npm utilise son default `/root/.npm` qui est désormais persisté via `cacheDirectories`.

## [0.3.6.0] - 2026-06-17

### Fixed
- **`frontend/nixpacks.toml`** (nouveau) : configuration Nixpacks directe — `railway.toml` `buildCommand` est ignoré par Nixpacks qui génère son propre pipeline. `nixpacks.toml` est lu en premier par le builder et définit `NPM_CONFIG_CACHE=/tmp/npm-cache` avant tout appel npm, éliminant le `EBUSY: resource busy or locked, rmdir node_modules/.cache`.
- **`frontend/railway.toml`** : suppression de `buildCommand` — la commande de build est désormais gérée exclusivement par `nixpacks.toml`.

## [0.3.5.0] - 2026-06-17

### Fixed
- **`frontend/.npmrc`** : `cache=false` → `cache=/tmp/npm` — rediriger le cache npm vers `/tmp` au lieu de le désactiver. `cache=false` causait `npm ci exit code 1` car `--prefer-offline` ne pouvait plus trouver de cache pour résoudre les paquets.
- **`frontend/railway.toml`** : suppression de `--prefer-offline` — inutile et contradictoire avec un cache vide ; npm résout désormais normalement depuis le registry.

## [0.3.4.0] - 2026-06-17

### Fixed
- **`frontend/.npmrc`** : `cache=false` — désactive le cache disque npm qui causait `EBUSY: resource busy or locked, rmdir node_modules/.cache` lors du build Railway (filesystem éphémère Nixpacks)
- **`frontend/railway.toml`** : `npm ci` → `npm ci --prefer-offline` — utilise les modules Nixpacks déjà résolus sans retenter d'écrire dans le cache réseau

## [0.3.3.0] - 2026-06-17

### Added
- **`frontend/.env.production`** : `API_URL=https://vacation-planer-production.up.railway.app` — le route handler Next.js lit cette variable à runtime pour proxifier `/api/*` vers le backend Railway. Non-secret (URL publique), commité volontairement.
- **Instructions post-déploiement** dans `deploy.sh` : commande `railway variables --service backend set FRONTEND_URL=...` pour autoriser le CORS une fois l'URL du frontend Railway connue.

### Changed
- **`.gitignore`** : exception `!frontend/.env.production` — `.env.*` reste ignoré globalement, seul ce fichier non-secret est suivi.
- **`.env.example`** : documentation clarifiée pour les variables Railway prod (`FRONTEND_URL` sur le backend, `API_URL` via `frontend/.env.production`).

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
