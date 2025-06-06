#!/bin/bash

echo "🚀 Démarrage simplifié de l'application Trading ETF..."

# Vérifier si Docker tourne
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker n'est pas en cours d'exécution"
    exit 1
fi

# Stopper et nettoyer les anciens conteneurs
echo "🧹 Nettoyage des anciens conteneurs..."
docker-compose down 2>/dev/null || true

# Démarrer seulement la base de données et Redis
echo "🐘 Démarrage de PostgreSQL et Redis..."
docker-compose up -d postgres redis

# Attendre que PostgreSQL soit prêt
echo "⏳ Attente que PostgreSQL soit prêt..."
for i in {1..30}; do
    if docker-compose exec postgres pg_isready -U trading_user -d trading_etf >/dev/null 2>&1; then
        echo "✅ PostgreSQL est prêt!"
        break
    fi
    sleep 1
    echo -n "."
done

echo ""
echo "🔄 Pour démarrer le backend manuellement:"
echo "cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

echo ""
echo "🔄 Pour démarrer le frontend manuellement:"
echo "cd frontend && npm install && npm start"

echo ""
echo "📊 Services démarrés:"
echo "- PostgreSQL: localhost:5432"
echo "- Redis: localhost:6379"
echo ""
echo "📍 Ton IP WSL: $(hostname -I | awk '{print $1}')"
echo "🌐 Utilise cette IP depuis Windows si localhost ne marche pas"