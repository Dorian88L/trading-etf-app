#!/bin/bash

# Script pour démarrer l'environnement de développement avec Docker et Traefik
echo "🚀 Démarrage de l'environnement de développement"
echo "=============================================="

# Vérifier que Docker est installé et en cours d'exécution
if ! command -v docker &> /dev/null; then
    echo "❌ Docker n'est pas installé. Veuillez l'installer d'abord."
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Docker n'est pas en cours d'exécution. Veuillez le démarrer."
    exit 1
fi

# Vérifier que Docker Compose est installé
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose n'est pas installé. Veuillez l'installer d'abord."
    exit 1
fi

# Créer les dossiers nécessaires
echo "📁 Création des dossiers nécessaires..."
mkdir -p data/postgres data/redis data/letsencrypt backend/logs

# Arrêter les services en cours si ils existent
echo "🛑 Arrêt des services existants..."
docker-compose down 2>/dev/null || true

# Construire et démarrer les services
echo "🔨 Construction et démarrage des services..."
docker-compose up -d --build

# Attendre que les services soient prêts
echo "⏳ Attente que les services soient prêts..."

# Attendre PostgreSQL
echo "🗄️ Attente de PostgreSQL..."
until docker-compose exec -T postgres pg_isready -U trading_user -d trading_etf_dev; do
    echo "PostgreSQL n'est pas encore prêt - attente..."
    sleep 2
done
echo "✅ PostgreSQL prêt"

# Attendre Redis
echo "📦 Attente de Redis..."
until docker-compose exec -T redis redis-cli ping; do
    echo "Redis n'est pas encore prêt - attente..."
    sleep 2
done
echo "✅ Redis prêt"

# Attendre le backend
echo "🖥️ Attente du backend..."
until curl -s http://localhost:8080/api/health > /dev/null; do
    echo "Backend n'est pas encore prêt - attente..."
    sleep 2
done
echo "✅ Backend prêt"

# Attendre le frontend
echo "🌐 Attente du frontend..."
until curl -s http://localhost > /dev/null; do
    echo "Frontend n'est pas encore prêt - attente..."
    sleep 2
done
echo "✅ Frontend prêt"

echo ""
echo "🎉 Environnement de développement prêt!"
echo "======================================"
echo "📱 Frontend: http://localhost"
echo "🔧 Backend API: http://localhost:8080/api"
echo "🗄️ Base de données: PostgreSQL sur port 5432"
echo "📦 Cache: Redis sur port 6379"
echo "🔍 Traefik Dashboard: http://localhost:8080"
echo ""
echo "📋 Commandes utiles:"
echo "  - Logs: docker-compose logs -f [service]"
echo "  - Shell: docker-compose exec [service] /bin/bash"
echo "  - Arrêter: ./scripts/stop.sh"
echo ""
echo "💡 Les fichiers sont synchronisés avec les conteneurs pour le hot reload"