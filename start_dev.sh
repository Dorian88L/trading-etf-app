#!/bin/bash
# Script de démarrage pour l'environnement de développement Trading ETF

echo "🚀 Démarrage de l'application Trading ETF..."

# Fonction pour arrêter proprement les services
cleanup() {
    echo "🛑 Arrêt des services..."
    docker-compose down
    exit 0
}

# Capturer les signaux d'arrêt
trap cleanup SIGINT SIGTERM

# Vérifier si Docker est installé
if ! command -v docker &> /dev/null; then
    echo "❌ Docker n'est pas installé. Veuillez l'installer d'abord."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose n'est pas installé. Veuillez l'installer d'abord."
    exit 1
fi

# Démarrer les services avec Docker Compose
echo "🐳 Démarrage des services Docker..."
docker-compose up --build

echo "✅ Services démarrés:"
echo "- Backend API: http://localhost:8000"
echo "- Frontend App: http://localhost:3000" 
echo "- API Documentation: http://localhost:8000/docs"
echo "- PostgreSQL: localhost:5432"
echo "- Redis: localhost:6379"

echo ""
echo "📊 Application Trading ETF prête!"
echo "- Dashboard: http://localhost:3000/dashboard"
echo "- ETF Analysis: http://localhost:3000/etfs"
echo "- Trading Signals: http://localhost:3000/signals"
echo "- Portfolio: http://localhost:3000/portfolio"

echo ""
echo "Pour arrêter l'application, appuyez sur Ctrl+C"

wait
