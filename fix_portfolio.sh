#!/bin/bash

echo "🔧 Correction des routes Portfolio..."

# Arrêter le frontend
docker stop frontend-prod

# Reconstruire l'image frontend avec les corrections
cd /home/dorian/trading-etf-app
docker build -t trading-etf-app-frontend ./frontend

# Redémarrer avec la nouvelle image
docker run -d \
  --name frontend-prod-new \
  --network trading-etf-app_default \
  --restart unless-stopped \
  --health-cmd="curl -f http://localhost || exit 1" \
  --health-interval=30s \
  --health-timeout=10s \
  --health-retries=3 \
  trading-etf-app-frontend

# Supprimer l'ancien conteneur
docker rm frontend-prod

# Renommer le nouveau
docker rename frontend-prod-new frontend-prod

echo "✅ Frontend reconstruit avec les corrections!"