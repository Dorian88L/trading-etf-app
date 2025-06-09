#!/bin/bash
echo "🛑 Arrêt de l'application Trading ETF..."

# Arrêter les services Node.js et Python
if [ -f logs/frontend.pid ]; then
    kill $(cat logs/frontend.pid) 2>/dev/null || true
    rm logs/frontend.pid
fi

if [ -f logs/backend.pid ]; then
    kill $(cat logs/backend.pid) 2>/dev/null || true
    rm logs/backend.pid
fi

if [ -f logs/celery_worker.pid ]; then
    kill $(cat logs/celery_worker.pid) 2>/dev/null || true
    rm logs/celery_worker.pid
fi

if [ -f logs/celery_beat.pid ]; then
    kill $(cat logs/celery_beat.pid) 2>/dev/null || true
    rm logs/celery_beat.pid
fi

# Arrêter les conteneurs Docker
docker-compose down

echo "✅ Application arrêtée"
