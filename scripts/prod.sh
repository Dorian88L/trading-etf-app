#!/bin/bash

# Script pour démarrer l'environnement de production avec Docker et Traefik
echo "🚀 Démarrage de l'environnement de PRODUCTION"
echo "============================================="

# Vérifier que nous sommes en mode production
if [ "$NODE_ENV" != "production" ] && [ "$ENVIRONMENT" != "production" ]; then
    echo "⚠️ ATTENTION: Vous démarrez l'environnement de production!"
    echo "⚠️ Assurez-vous que:"
    echo "   - Le fichier .env.prod est correctement configuré"
    echo "   - Les domaines pointent vers ce serveur"
    echo "   - Les certificats SSL seront générés automatiquement"
    echo ""
    read -p "Voulez-vous continuer? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Opération annulée"
        exit 1
    fi
fi

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

# Vérifier que le fichier .env.prod existe
if [ ! -f .env.prod ]; then
    echo "❌ Le fichier .env.prod est manquant. Veuillez le créer d'abord."
    exit 1
fi

# Charger les variables d'environnement de production
source .env.prod

# Vérifier les variables critiques
if [ -z "$POSTGRES_PASSWORD" ] || [ -z "$REDIS_PASSWORD" ] || [ -z "$JWT_SECRET_KEY" ]; then
    echo "❌ Variables d'environnement critiques manquantes dans .env.prod"
    echo "   - POSTGRES_PASSWORD"
    echo "   - REDIS_PASSWORD" 
    echo "   - JWT_SECRET_KEY"
    exit 1
fi

# Créer les dossiers nécessaires
echo "📁 Création des dossiers nécessaires..."
mkdir -p data/postgres data/redis data/letsencrypt backend/logs

# Arrêter les services de développement si ils sont en cours
echo "🛑 Arrêt des services de développement..."
docker-compose down 2>/dev/null || true

# Arrêter Nginx système pour libérer les ports 80/443
echo "🛑 Arrêt de Nginx système..."
sudo systemctl stop nginx 2>/dev/null || true
sudo pkill -f nginx 2>/dev/null || true

# Construire et démarrer les services de production
echo "🔨 Construction et démarrage des services de production..."
docker-compose -f docker-compose.prod.yml up -d --build

# Attendre que les services soient prêts
echo "⏳ Attente que les services soient prêts..."

# Attendre PostgreSQL
echo "🗄️ Attente de PostgreSQL..."
until docker-compose -f docker-compose.prod.yml exec -T postgres pg_isready -U trading_user -d trading_etf_prod; do
    echo "PostgreSQL n'est pas encore prêt - attente..."
    sleep 2
done
echo "✅ PostgreSQL prêt"

# Attendre Redis
echo "📦 Attente de Redis..."
until docker-compose -f docker-compose.prod.yml exec -T redis redis-cli --no-auth-warning -a "$REDIS_PASSWORD" ping; do
    echo "Redis n'est pas encore prêt - attente..."
    sleep 2
done
echo "✅ Redis prêt"

# Attendre le backend (peut prendre du temps avec les certificats SSL)
echo "🖥️ Attente du backend..."
timeout=300  # 5 minutes
counter=0
until curl -k -s https://api.investeclaire.fr/health > /dev/null || [ $counter -eq $timeout ]; do
    echo "Backend n'est pas encore prêt - attente... ($counter/$timeout)"
    sleep 5
    counter=$((counter + 5))
done

if [ $counter -eq $timeout ]; then
    echo "❌ Timeout - Le backend n'a pas démarré dans les temps"
    echo "📋 Vérifiez les logs: docker-compose -f docker-compose.prod.yml logs backend"
    exit 1
fi
echo "✅ Backend prêt"

echo ""
echo "🎉 Environnement de PRODUCTION prêt!"
echo "===================================="
echo "🌐 Frontend: https://investeclaire.fr"
echo "🔧 Backend API: https://api.investeclaire.fr"
echo "🔍 Traefik Dashboard: https://traefik.investeclaire.fr (si configuré)"
echo ""
echo "📋 Commandes utiles:"
echo "  - Logs: docker-compose -f docker-compose.prod.yml logs -f [service]"
echo "  - Status: docker-compose -f docker-compose.prod.yml ps"
echo "  - Arrêter: ./scripts/stop-prod.sh"
echo ""
echo "🔒 Les certificats SSL sont générés automatiquement par Let's Encrypt"
echo "📊 Surveillez les logs pour vous assurer que tout fonctionne correctement"