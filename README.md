# Travel Search Agent 🧳

Un agent de recherche de voyage qui agit comme un **agent de voyage personnel** :
tu donnes tes critères, il cherche en temps réel sur plusieurs fournisseurs (vols,
hébergements, autos), et il te ressort une comparaison enrichie d'insights avec des
liens directs vers l'achat. Toi, tu fais juste le « click & pay ».

## Pourquoi ce projet existe

Planifier un voyage demande de comparer manuellement des dizaines d'onglets : vols,
hôtels, autos, sur des dates flexibles. Cet agent fait ce travail à ta place et, surtout,
ne se contente pas de lister des résultats — il **raisonne dessus** :

- « Le même vol coûte le même prix du 12 au 16 et du 14 au 18 — choisis selon tes activités. »
- « Cette maison était dispo hier sur tes dates, elle vient d'être bookée. »
- « Avec 1 escale au lieu d'un direct, tu économises 240 $ pour 1h40 de plus. »

## Ce qu'il fait

- Questionnaire de critères (dates ±4-5 jours, budget, compagnie, escales, type d'hébergement…)
- Recherche parallèle multi-fournisseurs
- Filtrage et optimisation selon tes préférences
- Suivi des disponibilités dans le temps (insights)
- Liens directs préremplis vers la page d'achat

## Ce qu'il ne fait pas (volontairement)

Il **ne crée pas de comptes**, **n'ouvre pas de plateformes** et **ne paie rien** à ta
place. Ces parties dépendent du scraping et de l'automatisation de navigateur, qui sont
fragiles (CAPTCHA, détection de bots) et souvent contre les conditions d'utilisation.
L'agent t'amène jusqu'à la page d'achat préremplie ; le paiement reste entre tes mains.

## Stack

- **Python 3.12** + **httpx** (async)
- **Anthropic SDK** (tool use) comme cerveau de l'agent
- **Duffel** (vols + hôtels via Duffel Stays) — Amadeus décommissionné 2026-07-17
- **FastAPI** + **SSE** pour le backend (`/api/search`, `/api/sessions`, `/api/health`)
- **Next.js 14** + **Tailwind CSS** pour l'interface web (port 3001)
- **SQLite** (snapshots de dispo) → Postgres plus tard
- **APScheduler** pour le re-check périodique

## Installation

```bash
git clone <ton-repo>
cd travel-search-agent
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # puis remplis tes clés API
```

### Clés API requises

| Service   | Où l'obtenir                                   | Gratuit pour démarrer |
|-----------|------------------------------------------------|-----------------------|
| Anthropic | console.anthropic.com                          | Crédit de départ      |
| Duffel    | duffel.com                                     | Mode test             |

## Utilisation

```bash
# Interface web (recommandé) — lance FastAPI (:8000) + Next.js (:3001) en parallèle
make dev

# Ou séparément :
uvicorn api.main:app --reload          # backend FastAPI sur http://localhost:8000
cd frontend && npm run dev             # frontend Next.js sur http://localhost:3001

# Mode CLI uniquement
python main.py

# Scheduler de re-check périodique (mode démon)
python scheduler.py                    # démarre le daemon
python scheduler.py --once             # une seule passe (pour les tests)
```

## Roadmap

- **Phase 1 (MVP)** — Recherche de vols + questionnaire + sortie comparative ✅
- **Phase 2** — Hôtels, autos, snapshots de dispo + insights, scheduler ✅
- **Phase 3** — UI web + backend FastAPI + correctifs (v0.3.0.0) ✅ — alertes de prix, Airbnb/VRBO, Postgres restants

## Structure du projet

```
Vacation-Planer/
├── CLAUDE.md            # contexte pour Claude Code (à garder à jour)
├── README.md
├── CHANGELOG.md
├── TODOS.md
├── VERSION              # version courante (0.3.0.0)
├── Makefile             # make dev = FastAPI + Next.js en parallèle
├── .env.example
├── requirements.txt
├── pyproject.toml
├── main.py              # CLI + search_core() partagé avec l'API
├── models.py            # dataclasses normalisées (SearchCriteria, FlightResult…)
├── questionnaire.py     # collecte des critères en mode CLI
├── display.py           # affichage tabulaire CLI
├── storage.py           # SQLite via SQLAlchemy — sessions + snapshots
├── insights.py          # diff prix/dispo entre deux snapshots
├── scheduler.py         # daemon APScheduler — re-check périodique
├── providers/
│   ├── duffel.py        # vols via Duffel API
│   ├── duffel_stays.py  # hôtels via Duffel Stays API
│   └── cars.py          # stub autos (provider à déterminer)
├── api/
│   ├── main.py          # app FastAPI
│   ├── schemas.py       # schémas Pydantic v2
│   └── routes/
│       ├── search.py    # POST /api/search (SSE streaming)
│       └── sessions.py  # GET /api/sessions, GET /api/health
├── frontend/            # Next.js 14 (port 3001)
│   ├── app/
│   │   ├── page.tsx
│   │   ├── results/page.tsx
│   │   ├── components/  # SearchForm, FlightCard, HotelCard, InsightBadge
│   │   └── types.ts
│   └── package.json
└── tests/
    └── test_storage_insights.py
```

## Note légale

Outil personnel de recherche. Respecte les conditions d'utilisation de chaque
fournisseur. N'automatise pas d'achats ni de création de comptes.
