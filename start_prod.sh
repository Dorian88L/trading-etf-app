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

# Build du frontend React pour la production
echo "🔨 Build du frontend React pour la production..."
cd frontend
npm run build
if [ $? -ne 0 ]; then
    echo "❌ Échec du build frontend"
    exit 1
fi
echo "✅ Build frontend terminé"
cd ..

# Démarrer nginx avec SSL
echo "🌐 Démarrage de nginx avec SSL (PRODUCTION)..."

# Arrêter nginx système s'il tourne
sudo systemctl stop nginx 2>/dev/null || true
sudo pkill -f nginx 2>/dev/null || true
sleep 2

# Supprimer les configs de dev et activer la config SSL
sudo rm -f /etc/nginx/sites-enabled/frontend-http
sudo rm -f /etc/nginx/sites-enabled/api-8443
sudo ln -sf /etc/nginx/sites-available/ssl-config /etc/nginx/sites-enabled/ssl-config

# Tester et démarrer nginx système avec config SSL
sudo nginx -t
if [ $? -eq 0 ]; then
    sudo systemctl start nginx
    echo "✅ Nginx démarré avec configuration SSL système"
else
    echo "❌ Échec test configuration nginx"
    exit 1
fi

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
echo "  Frontend: https://localhost (si certificat valide)"
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