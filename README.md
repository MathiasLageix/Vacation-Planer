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
- **Amadeus Self-Service API** (vols, hôtels, autos) + **Duffel** (vols, alternative)
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
| Amadeus   | developers.amadeus.com (Self-Service)          | Oui (quota test)      |
| Duffel    | duffel.com (optionnel, alternative vols)       | Mode test             |

## Utilisation

```bash
python -m agent          # lance l'agent en mode chat/CLI
```

## Roadmap

- **Phase 1 (MVP)** — Recherche de vols + questionnaire + sortie comparative ✅ objectif initial
- **Phase 2** — Hôtels, autos, snapshots de dispo + insights, scheduler
- **Phase 3** — UI web, Airbnb/VRBO, alertes de prix

## Structure du projet

```
travel-search-agent/
├── CLAUDE.md            # contexte pour Claude Code (à garder à jour)
├── README.md
├── .env.example
├── requirements.txt
├── agent/
│   ├── __main__.py      # point d'entrée
│   ├── brain.py         # boucle agent (Claude + tool use)
│   └── questionnaire.py # collecte des critères
├── providers/
│   ├── base.py          # interface commune + modèle normalisé
│   ├── amadeus.py
│   └── duffel.py
├── storage/
│   ├── db.py            # SQLite
│   └── snapshots.py     # suivi de dispo dans le temps
└── insights/
    └── compare.py       # détection de changements prix/dispo
```

## Note légale

Outil personnel de recherche. Respecte les conditions d'utilisation de chaque
fournisseur. N'automatise pas d'achats ni de création de comptes.
