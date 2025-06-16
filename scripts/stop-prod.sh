#!/bin/bash

# Script pour arrêter l'environnement de production
echo "🛑 Arrêt de l'environnement de PRODUCTION"
echo "========================================"

# Confirmation avant arrêt
echo "⚠️ ATTENTION: Vous allez arrêter l'environnement de PRODUCTION!"
echo "⚠️ Cela rendra votre site inaccessible."
echo ""
read -p "Voulez-vous vraiment continuer? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Opération annulée"
    exit 1
fi

# Arrêter les services Docker Compose de production
echo "📦 Arrêt des conteneurs de production..."
docker-compose -f docker-compose.prod.yml down

# Afficher les conteneurs restants
echo ""
echo "📋 État des conteneurs:"
docker ps -a --filter "name=prod" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "✅ Environnement de production arrêté"
echo ""
echo "💡 Pour redémarrer: ./scripts/prod.sh"
echo "💡 Pour nettoyer complètement:"
echo "  - Supprimer les volumes: docker-compose -f docker-compose.prod.yml down -v"
echo "  - Supprimer les images: docker system prune -a"