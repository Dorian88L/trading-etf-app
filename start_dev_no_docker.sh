#!/bin/bash

# Script pour démarrer l'application sans Docker

echo "🚀 Démarrage de l'application Trading ETF (sans Docker)"
echo "====================================================="

# Créer dossier logs
mkdir -p logs
mkdir -p backend/logs

# Vérifier PostgreSQL local
echo "🗄️ Vérification de PostgreSQL..."
if systemctl is-active --quiet postgresql; then
    echo "✅ PostgreSQL actif"
else
    echo "⚠️ PostgreSQL non actif, tentative de démarrage..."
    sudo systemctl start postgresql || echo "❌ Échec démarrage PostgreSQL"
fi

# Vérifier Redis local
echo "📦 Vérification de Redis..."
if systemctl is-active --quiet redis-server; then
    echo "✅ Redis actif"
else
    echo "⚠️ Redis non actif, tentative de démarrage..."
    sudo systemctl start redis-server || echo "❌ Échec démarrage Redis"
fi

# Configuration des variables d'environnement
export DATABASE_URL="postgresql://trading_user:trading_password@localhost:5432/trading_etf"
export REDIS_URL="redis://localhost:6379"
export ENVIRONMENT="development"

# Démarrer le backend sur port 8000 (sans SSL pour être derrière nginx)
echo "🖥️ Démarrage du backend FastAPI..."
cd backend
source venv/bin/activate 2>/dev/null || echo "⚠️ Environnement virtuel non trouvé"
nohup uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > logs/backend.pid
cd ..

# Attendre que le backend soit prêt
echo "⏳ Attente du backend (30s max)..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        echo "✅ Backend prêt sur http://localhost:8000"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Timeout backend"
        exit 1
    fi
    sleep 1
done

# Démarrer le frontend
echo "🌐 Démarrage du frontend React..."
cd frontend
nohup npm start > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../logs/frontend.pid
cd ..

# Attendre que le frontend soit prêt
echo "⏳ Attente du frontend (60s max)..."
for i in {1..60}; do
    if curl -s http://localhost:3000 >/dev/null 2>&1; then
        echo "✅ Frontend prêt sur http://localhost:3000"
        break
    fi
    if [ $i -eq 60 ]; then
        echo "❌ Timeout frontend"
        exit 1
    fi
    sleep 1
done

echo ""
echo "🎉 Application démarrée avec succès!"
echo "======================================"
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "API SSL:  https://api.investeclaire.fr (nécessite configuration nginx)"
echo ""
echo "PIDs sauvegardés dans logs/"
echo "Logs disponibles dans logs/"
echo ""
echo "Pour arrêter: ./stop_dev_simple.sh"