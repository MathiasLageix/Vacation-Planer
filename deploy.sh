#!/usr/bin/env bash
# deploy.sh — Déploiement Railway (backend + frontend séparés)
#
# Prérequis :
#   railway login       # une seule fois
#   railway link        # lier ce dossier à un projet Railway existant
#
# Usage :
#   ./deploy.sh          # déploie tout (backend + frontend)
#   ./deploy.sh backend  # backend seulement
#   ./deploy.sh frontend # frontend seulement

set -euo pipefail

TARGET="${1:-all}"

deploy_backend() {
  echo "==> Déploiement du backend FastAPI..."
  railway up --service backend --detach
  echo "    Backend déployé."
}

deploy_frontend() {
  echo "==> Déploiement du frontend Next.js..."
  railway up --service frontend --detach --root frontend
  echo "    Frontend déployé."
}

case "$TARGET" in
  backend)  deploy_backend ;;
  frontend) deploy_frontend ;;
  all)
    deploy_backend
    deploy_frontend
    ;;
  *)
    echo "Usage: $0 [backend|frontend|all]" >&2
    exit 1
    ;;
esac

echo ""
echo "==> Déploiement terminé. Vérifier :"
echo "    railway status"
echo "    railway logs --service backend"
echo "    railway logs --service frontend"
echo ""
echo "==> Post-déploiement (première fois seulement) :"
echo "    1. Copier l'URL Railway du service frontend (ex. my-frontend.up.railway.app)"
echo "    2. Autoriser le CORS sur le backend :"
echo "       railway variables --service backend set FRONTEND_URL=https://my-frontend.up.railway.app"
echo "    3. Redéployer le backend pour appliquer :"
echo "       railway up --service backend --detach"
