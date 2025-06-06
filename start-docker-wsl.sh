#!/bin/bash
# Script pour démarrer Docker et l'application dans WSL

echo "🐳 Démarrage de Docker dans WSL..."

# Fonction pour démarrer Docker selon la distribution
start_docker() {
    if command -v systemctl >/dev/null 2>&1; then
        echo "🔧 Utilisation de systemctl..."
        sudo systemctl start docker
    elif command -v service >/dev/null 2>&1; then
        echo "🔧 Utilisation de service..."
        sudo service docker start
    else
        echo "❌ Impossible de démarrer Docker automatiquement"
        echo "💡 Essaie manuellement: sudo dockerd &"
        return 1
    fi
}

# Vérifier si Docker est déjà en cours d'exécution
if docker info >/dev/null 2>&1; then
    echo "✅ Docker est déjà en cours d'exécution"
else
    echo "🚀 Démarrage de Docker..."
    start_docker
    
    # Attendre que Docker soit prêt
    echo "⏳ Attente que Docker soit prêt..."
    for i in {1..30}; do
        if docker info >/dev/null 2>&1; then
            echo "✅ Docker est prêt!"
            break
        fi
        sleep 1
        echo -n "."
    done
    
    if ! docker info >/dev/null 2>&1; then
        echo "❌ Docker n'a pas pu démarrer"
        echo "💡 Essaie manuellement:"
        echo "   sudo dockerd &"
        echo "   ou"
        echo "   sudo service docker start"
        exit 1
    fi
fi

echo ""
echo "🚀 Démarrage de l'application Trading ETF..."
echo "📍 Ton IP WSL: $(hostname -I | awk '{print $1}')"
echo ""

# Démarrer l'application
./start_dev.sh