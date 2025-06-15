#!/bin/bash

# Script pour arrêter l'application sans Docker

echo "🛑 Arrêt de l'application Trading ETF (sans Docker)"
echo "===================================================="

# Fonction pour arrêter un processus via PID
stop_process() {
    local service_name=$1
    local pid_file=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        echo "🔄 Arrêt de $service_name (PID: $pid)..."
        
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null
            sleep 2
            
            # Vérifier si le processus est toujours actif
            if kill -0 "$pid" 2>/dev/null; then
                echo "⚠️ Arrêt forcé de $service_name..."
                kill -9 "$pid" 2>/dev/null
            fi
            echo "✅ $service_name arrêté"
        else
            echo "⚠️ $service_name n'était pas actif"
        fi
        
        rm -f "$pid_file"
    else
        echo "⚠️ Fichier PID non trouvé pour $service_name"
    fi
}

# Arrêter le frontend
stop_process "Frontend" "logs/frontend.pid"

# Arrêter le backend
stop_process "Backend" "logs/backend.pid"

# Arrêter tous les processus restants sur les ports utilisés
echo "🔍 Nettoyage des processus sur les ports 3000 et 8443..."

# Port 80 (frontend)
if lsof -ti:3000 >/dev/null 2>&1; then
    echo "🔄 Arrêt des processus sur le port 3000..."
    sudo kill -9 $(lsof -ti:80) 2>/dev/null || true
fi

# Port 8443 (backend)
if lsof -ti:8443 >/dev/null 2>&1; then
    echo "🔄 Arrêt des processus sur le port 8443..."
    kill -9 $(lsof -ti:8443) 2>/dev/null || true
fi

# Nettoyer les processus node et uvicorn orphelins
echo "🧹 Nettoyage des processus orphelins..."
pkill -f "npm start" 2>/dev/null || true
pkill -f "uvicorn app.main:app" 2>/dev/null || true

echo ""
echo "✅ Arrêt terminé!"
echo "=================="
echo "Tous les services ont été arrêtés"
echo "Les fichiers de logs sont conservés dans logs/"