#!/bin/bash

# Script pour arrêter l'environnement de développement
echo "🛑 Arrêt de l'environnement de développement"
echo "==========================================="

# Arrêter les services Docker Compose
echo "📦 Arrêt des conteneurs..."
docker-compose down

# Afficher les conteneurs restants
echo ""
echo "📋 État des conteneurs:"
docker ps -a --filter "name=trading" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "✅ Environnement de développement arrêté"
echo ""
echo "💡 Pour nettoyer complètement:"
echo "  - Supprimer les volumes: docker-compose down -v"
echo "  - Supprimer les images: docker system prune -a"