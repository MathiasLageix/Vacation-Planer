# TODOS

## Phase 3 — Roadmap

### UI Web
**Priority:** P1
Construire une interface Next.js pour remplacer le questionnaire CLI.

### Airbnb / VRBO (scraping)
**Priority:** P2
Ajouter les hébergements Airbnb/VRBO via scraping prudent (pas d'API publique).

### Alertes de prix
**Priority:** P2
Notifier l'utilisateur par email/push quand un prix dépasse un seuil défini.

### Autos (provider réel)
**Priority:** P3
Trouver un provider API pour la location de voitures (actuellement stub).

### Postgres
**Priority:** P3
Migrer de SQLite vers Postgres pour la production.

## Completed

### Vols Duffel
**Priority:** P1
**Completed:** v0.1.0 (2026-06-16)
Intégration Duffel pour la recherche de vols — remplacement Amadeus décommissionné 2026-07-17.

### Hébergements Duffel Stays
**Priority:** P1
**Completed:** v0.1.0 (2026-06-16)
Intégration Duffel Stays API pour la recherche d'hôtels avec snapshots et insights.

### Stockage SQLite + Insights
**Priority:** P1
**Completed:** v0.1.0 (2026-06-16)
Snapshots horodatés via SQLAlchemy + couche d'insights (diff prix/dispo entre snapshots).

### Scheduler APScheduler (Phase 2)
**Priority:** P1
**Completed:** v0.1.0 (2026-06-16)
Daemon de re-check périodique via APScheduler — relance les recherches sauvegardées, génère des insights automatiquement.
