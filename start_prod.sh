#!/bin/bash

# Script pour démarrer l'application en mode production
# ATTENTION: Ce script nécessite des privilèges sudo pour les ports 80 et 443

echo "🚀 Démarrage de l'application Trading ETF (PRODUCTION)"
echo "===================================================="

# Vérifier les privilèges sudo
echo "🔐 Vérification des privilèges sudo..."
if ! sudo -n true 2>/dev/null; then
    echo "⚠️ Ce script nécessite des privilèges sudo pour utiliser les ports 80 et 443"
    echo "Veuillez saisir votre mot de passe sudo si demandé"
    sudo -v || exit 1
fi

# Créer dossier logs
mkdir -p logs
mkdir -p backend/logs

# Charger les variables d'environnement depuis .env.prod
if [ -f .env.prod ]; then
    echo "📁 Chargement des variables d'environnement depuis .env.prod"
    export $(grep -v '^#' .env.prod | xargs)
else
    echo "❌ Fichier .env.prod non trouvé! Arrêt du script."
    exit 1
fi

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

# Démarrer le backend sur port 8443
echo "🖥️ Démarrage du backend FastAPI (PRODUCTION)..."
cd backend
source venv/bin/activate 2>/dev/null || echo "⚠️ Environnement virtuel non trouvé"
nohup uvicorn app.main_production:app --host 0.0.0.0 --port 8443 > logs/backend.log 2>&1 &
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

# Construire le frontend pour la production
echo "🔨 Construction du frontend React pour la production..."
cd frontend
npm run build || {
    echo "❌ Échec de la construction du frontend"
    exit 1
}
cd ..

# Démarrer nginx avec SSL
echo "🌐 Démarrage de nginx avec SSL (PRODUCTION)..."
sudo nginx -c /home/dorian/trading-etf-app/nginx_complete_ssl.conf
echo "✅ Nginx démarré avec configuration SSL"

echo ""
# Obtenir l'IP publique
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || echo "IP_PUBLIQUE_NON_DETECTEE")

echo "🎉 Application démarrée en PRODUCTION!"
echo "====================================="
echo "Accès externe (depuis Internet):"
echo "  Frontend: https://investeclaire.fr"
echo "  Backend:  https://api.investeclaire.fr"
echo ""
echo "Accès local (pour debug):"
echo "  Backend:  http://localhost:8443"
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