# CLAUDE.md

> Fichier de contexte vivant pour Claude Code. À mettre à jour à mesure que le produit évolue.
> Claude lit ce fichier automatiquement au démarrage de chaque session.

## Le produit en une phrase

Un **agent de recherche de voyage** qui prend les critères de l'utilisateur via un
questionnaire, interroge plusieurs fournisseurs (vols, hébergements, autos) en temps
réel, et retourne une comparaison enrichie d'**insights** — pas juste une liste de
résultats bruts comme une recherche Google.

## Ce que le produit fait (et ne fait PAS)

**Fait :**
- Pose des questions pour cerner les critères (dates ±4-5 jours, budget, compagnie
  préférée, nombre d'escales toléré, type d'hébergement, etc.).
- Interroge plusieurs fournisseurs en parallèle.
- Filtre/optimise selon les critères (ex. « Air Canada seulement », « max 1 escale »).
- Suit les disponibilités dans le temps pour produire des insights
  (« cette maison était dispo hier à telle date, elle est maintenant bookée »).
- Retourne des **liens directs (deep links) préremplis** vers la page d'achat.

**Ne fait PAS (par design, pour rester simple et non fragile) :**
- N'ouvre pas de plateforme automatiquement, ne remplit pas de panier.
- Ne crée pas de comptes à la place de l'utilisateur.
- Ne complète aucun paiement. L'humain fait le « click & pay » final.

## Stack technique

| Couche            | Choix                          | Raison |
|-------------------|--------------------------------|--------|
| Langage           | Python 3.12                    | Orchestration API + async + SDK Anthropic natif |
| Cerveau de l'agent| Anthropic SDK (tool use)       | Claude appelle lui-même les outils de recherche |
| HTTP              | httpx (async)                  | Appels parallèles aux fournisseurs |
| Vols              | Duffel                         | Amadeus décommissionné 2026-07-17 |
| Hôtels            | Duffel Stays                   | Duffel Stays API (hôtels) |
| Autos             | stub `providers/cars.py`       | Aucun provider API dispo — Phase 3 |
| Stockage          | SQLite → Postgres plus tard    | Snapshots de dispo pour les insights |
| Scheduler         | APScheduler                    | Re-check périodique des dispos |
| Secrets           | python-dotenv (.env)           | Clés API hors du code |
| Interface         | CLI + Next.js 14 (Phase 3 ✅)  | CLI pour dev, web UI sur port 3001 en prod |

**Hors scope au début :** Airbnb et VRBO (pas d'API publique → scraping fragile,
remis à la Phase 2). Création de comptes et automatisation du checkout.

## Architecture

```
Utilisateur
   │  (critères via questionnaire)
   ▼
Agent (Claude + tool use)
   │  appelle en parallèle ↓
   ├── search_flights(...)   → Duffel
   ├── search_hotels(...)    → Duffel Stays
   └── search_cars(...)      → stub (provider à venir)
   │
   ▼
Normalisation des résultats → SQLite (snapshot horodaté)
   │
   ▼
Couche d'insights (compare snapshots, détecte changements de dispo/prix)
   │
   ▼
Réponse : tableau comparatif + insights + deep links préremplis
```

## Conventions de code

- Python : formatage `ruff` + `black`, typage avec annotations (mypy-friendly).
- Chaque fournisseur = un module dans `providers/` exposant une interface commune
  (`search() -> list[NormalizedResult]`) pour pouvoir en ajouter facilement.
- Modèle de données normalisé commun à tous les fournisseurs (un vol Amadeus et un
  vol Duffel sortent dans le même format).
- Aucune clé API en dur. Tout passe par `.env` (jamais commité — voir `.env.example`).
- Les appels réseau sont async et testables avec des fixtures (réponses API mockées).

## Roadmap par phases

- **Phase 1 (MVP)** : recherche de vols Amadeus, questionnaire de base, sortie en
  tableau avec deep links. Une recherche bout-en-bout qui marche.
- **Phase 2** : ajout hôtels + autos, snapshots de dispo + insights, scheduler. ✅
- **Phase 3** : UI web + backend FastAPI + correctifs. ✅ — Airbnb/VRBO, alertes de prix, Postgres restants.

## État actuel

> ⚠️ Mettre cette section à jour à chaque session.

- [x] Repo scaffoldé (`models.py`, `providers/duffel.py`, `questionnaire.py`, `display.py`, `main.py`)
- [x] `.env` configuré avec clé Duffel (`DUFFEL_API_KEY`) — Amadeus décommissionné 2026-07-17
- [x] Premier appel `search_flights` Duffel qui retourne des résultats réels (5 vols YUL→CDG)
- [x] Questionnaire de critères CLI
- [x] Hébergements : `providers/duffel_stays.py` (Duffel Stays API)
- [x] Autos : stub `providers/cars.py` (aucune API dispo — Phase 3)
- [x] Stockage SQLite + snapshots (`storage.py` — SQLAlchemy, sessions par hash de critères)
- [x] Insights de prix/dispo (`insights.py` — diff entre deux snapshots)
- [x] Questionnaire étendu (vols + hôtels + autos optionnels)
- [x] Recherches parallèles + affichage unifié (`main.py`)
- [x] Scheduler APScheduler (`scheduler.py` — daemon + `--once` pour les tests, re-check toutes les N min)
- [x] Backend FastAPI (`api/` — POST /api/search SSE, GET /api/sessions, GET /api/health)
- [x] Frontend Next.js 14 (`frontend/` — port 3001, TypeScript, Tailwind, formulaire multistep + page résultats SSE)
- [x] `Makefile` — `make dev` lance api (:8000) + web (:3001) en parallèle
- [ ] Alertes de prix (email/push — Phase 3 restant)
- [ ] Airbnb/VRBO scraping (Phase 3 restant)
- [ ] Postgres (Phase 3 restant)
