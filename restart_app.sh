#!/bin/bash

echo "🚀 Redémarrage de l'application Trading ETF..."

# Arrêter tous les processus
echo "📛 Arrêt des services..."
pkill -f "uvicorn" 2>/dev/null || true
pkill -f "react-scripts" 2>/dev/null || true
pkill -f "node.*start" 2>/dev/null || true

# Attendre que les ports se libèrent
sleep 3

# Libérer les ports au cas où
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true

sleep 2

echo "🔧 Démarrage du backend..."
cd /home/dorian/trading-etf-app/backend
nohup python start_backend_with_auth.py > backend.log 2>&1 &

sleep 3

echo "🎨 Démarrage du frontend..."
cd /home/dorian/trading-etf-app/frontend
nohup npm start > frontend.log 2>&1 &

echo "⏱️  Attente du démarrage complet..."
sleep 10

echo "✅ Vérification du statut..."
python /home/dorian/trading-etf-app/check_status.py

echo ""
echo "🌐 Application accessible sur:"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"
echo ""
echo "🔐 Compte de test:"
echo "   Email: test@trading.com"
echo "   Password: test123"