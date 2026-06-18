# Vacation Planer

Un **agent de recherche de voyage** qui fait le travail d'un vrai agent de voyages : tu donnes tes critères une fois, il cherche en temps réel sur plusieurs fournisseurs, suit les prix dans le temps et t'amène directement à la page d'achat. Toi, tu fais le « click & pay ».

---

## Ce qui le différencie d'une recherche Google

| Google Flights / Booking | Vacation Planer |
|--------------------------|-----------------|
| Tu compares manuellement des dizaines d'onglets | Vols + hôtels + autos en un seul formulaire |
| Les prix d'hier sont perdus | Snapshots horodatés — le système sait si un prix a baissé |
| Pas de contexte entre deux visites | Historique de toutes tes recherches et leurs évolutions |
| Tu perds ton avance si le prix monte | Insights automatiques : « -8 % depuis ta dernière visite » |

---

## Features actuelles (v0.6.0.0)

- **Recherche vols** via [Duffel](https://duffel.com) et RapidAPI Google Flights (Matan Rabi), en parallèle, triée par prix
- **Recherche hôtels** via Duffel Stays, filtrable par budget nuit
- **Dates flexibles** : cherche automatiquement ±N jours autour de ta date
- **Snapshots + insights** : compare les prix entre deux visites et alerte sur les changements
- **Scheduler** : re-check automatique des recherches sauvegardées en arrière-plan (APScheduler)
- **UI web** : formulaire en étapes (vols → hôtel → autos) + résultats en streaming temps réel (SSE)
- **Deep links** : chaque résultat ouvre directement la page d'achat préremplie
- **Historique** : toutes les recherches sont sauvegardées et consultables

---

## Stack technique

| Couche | Technologie |
|--------|-------------|
| Backend API | FastAPI 0.115 + uvicorn (SSE streaming) |
| Frontend | Next.js 14 App Router — TypeScript + Tailwind CSS |
| Vols | Duffel API + RapidAPI Google Flights Live |
| Hôtels | Duffel Stays API |
| Stockage | SQLite (dev) → Postgres (prod) |
| Scheduler | APScheduler (daemon + `--once`) |
| Déploiement | Railway (cible) |
| Secrets | python-dotenv — jamais de clé dans le code |

---

## Installation

```bash
git clone https://github.com/MathiasLageix/Vacation-Planer.git
cd Vacation-Planer
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # remplis tes clés API

# Frontend
cd frontend && npm install && cd ..
```

### Clés API requises

| Service | Où l'obtenir | Gratuit pour démarrer |
|---------|--------------|----------------------|
| Duffel | [app.duffel.com](https://app.duffel.com) | Mode test (sandbox) |
| RapidAPI Google Flights | [rapidapi.com/matan-rabi](https://rapidapi.com) | Plan gratuit (quota limité) |

---

## Lancer le projet

```bash
make dev        # lance API (:8000) + frontend (:3001) en parallèle
make api        # backend seul
make web        # frontend seul
```

Ouvre [http://localhost:3001](http://localhost:3001) dans ton navigateur.

### CLI (mode dev)

```bash
source .venv/bin/activate
python main.py          # questionnaire interactif en terminal
python scheduler.py --once   # force un re-check immédiat
```

---

## Structure du projet

```
Vacation-Planer/
├── api/                  # Backend FastAPI
│   ├── main.py           # App + CORS + lifespan
│   ├── schemas.py        # Pydantic request/response
│   └── routes/
│       ├── search.py     # POST /api/search (SSE streaming)
│       └── sessions.py   # GET /api/sessions
├── frontend/             # Next.js 14
│   └── src/app/
│       ├── page.tsx      # Formulaire multistep
│       └── results/      # Page résultats temps réel
├── providers/
│   ├── duffel.py         # Vols Duffel
│   ├── duffel_stays.py   # Hôtels Duffel Stays
│   ├── rapidapi_flights.py  # Vols RapidAPI (Google Flights Live)
│   └── cars.py           # Autos — stub (provider à venir)
├── models.py             # Modèle normalisé commun
├── storage.py            # SQLite + sessions + snapshots
├── insights.py           # Diff prix/dispo entre snapshots
├── scheduler.py          # Daemon APScheduler
├── main.py               # CLI + search_core()
├── Makefile
└── TODOS.md              # Backlog priorisé
```

---

## Roadmap — 5 sprints

| Sprint | Scope | Priorité |
|--------|-------|---------|
| **S1 — Sécurité** | Rate limiting `/api/search` · auth `GET /api/sessions` · TOCTOU storage | P2 |
| **S2 — Qualité** | Tests scheduler + SSE error path · couverture provider errors · frontend Vitest | P2 |
| **S3 — UX** | Date picker francophone · options avancées accordion · SSE : vols error ≠ stop hôtels | P3 |
| **S4 — Nouveaux providers** | Airbnb/VRBO scraping · alertes de prix email/push · autos (provider réel) | P2 |
| **S5 — Production** | Postgres · lien de recherche partageable · déploiement Railway stable | P3 |

---

## Ce que l'agent ne fait pas (volontairement)

Il **n'ouvre pas de plateformes**, **ne crée pas de comptes** et **ne paie rien** à ta place. Le scraping de paiement est fragile (CAPTCHA, détection de bots) et souvent contre les conditions d'utilisation. L'agent t'amène jusqu'à la page d'achat préremplie — le dernier clic reste le tien.

---

## Note légale

Outil personnel de recherche. Respecte les conditions d'utilisation de chaque fournisseur. N'automatise aucun achat ni création de compte.
