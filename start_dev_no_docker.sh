#!/bin/bash

# Script pour démarrer l'application sans Docker
# ATTENTION: Ce script nécessite des privilèges sudo pour le port 80

echo "🚀 Démarrage de l'application Trading ETF (sans Docker)"
echo "====================================================="

# Vérifier les privilèges sudo
echo "🔐 Vérification des privilèges sudo..."
if ! sudo -n true 2>/dev/null; then
    echo "⚠️ Ce script nécessite des privilèges sudo pour utiliser le port 80"
    echo "Veuillez saisir votre mot de passe sudo si demandé"
    sudo -v || exit 1
fi

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

# Démarrer le backend sur port 8443
echo "🖥️ Démarrage du backend FastAPI..."
cd backend
source venv/bin/activate 2>/dev/null || echo "⚠️ Environnement virtuel non trouvé"
nohup uvicorn app.main:app --host 0.0.0.0 --port 8443 --reload > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > logs/backend.pid
cd ..

# Attendre que le backend soit prêt
echo "⏳ Attente du backend (30s max)..."
for i in {1..30}; do
    if curl -s http://localhost:8443/health >/dev/null 2>&1; then
        echo "✅ Backend prêt sur http://localhost:8443"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Timeout backend"
        exit 1
    fi
    sleep 1
done

# Démarrer le frontend sur port 3000
echo "🌐 Démarrage du frontend React..."
cd frontend
PORT=3000 HOST=0.0.0.0 nohup npm start > ../logs/frontend.log 2>&1 &
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

# Démarrer nginx avec SSL
echo "🌐 Démarrage de nginx avec SSL..."
sudo nginx -c /home/dorian/trading-etf-app/nginx_complete_ssl.conf
echo "✅ Nginx démarré avec configuration SSL"

echo ""
# Obtenir l'IP publique
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || echo "IP_PUBLIQUE_NON_DETECTEE")

echo "🎉 Application démarrée avec succès!"
echo "======================================"
echo "Accès local:"
echo "  Backend:  http://localhost:8443"
echo "  Frontend: http://localhost:3000 (via nginx: https://investeclaire.fr)"
echo ""
echo "Accès externe (depuis Internet):"
echo "  Frontend: https://investeclaire.fr"
echo "  Backend:  https://api.investeclaire.fr"
echo ""
echo "⚠️  IMPORTANT: Assurez-vous que les ports 80, 443 et 8443 sont ouverts dans votre firewall"
echo "    - sudo ufw allow 80"
echo "    - sudo ufw allow 443"
echo "    - sudo ufw allow 8443"
echo ""
echo "PIDs sauvegardés dans logs/"
echo "Logs disponibles dans logs/"
echo ""
echo "Pour arrêter: ./stop_dev_no_docker.sh"