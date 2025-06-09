#!/bin/bash

# Script de démarrage complet de l'application Trading ETF
# Démarre tous les services selon le cahier des charges

echo "🚀 Démarrage de l'application Trading ETF complète"
echo "=================================================="

# Fonction pour vérifier si un port est utilisé
check_port() {
    port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        echo "⚠️  Le port $port est déjà utilisé"
        return 1
    else
        return 0
    fi
}

# Vérifier les prérequis
echo "🔍 Vérification des prérequis..."

# Vérifier Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker n'est pas installé"
    exit 1
fi

# Vérifier Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose n'est pas installé"
    exit 1
fi

# Vérifier Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js n'est pas installé"
    exit 1
fi

# Vérifier Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 n'est pas installé"
    exit 1
fi

echo "✅ Tous les prérequis sont installés"

# Arrêter les services existants
echo "🛑 Arrêt des services existants..."
docker-compose down --remove-orphans 2>/dev/null || true
pkill -f "uvicorn" 2>/dev/null || true
pkill -f "celery" 2>/dev/null || true
pkill -f "npm start" 2>/dev/null || true

# Attendre que les ports se libèrent
sleep 3

# Créer les variables d'environnement si nécessaire
echo "⚙️  Configuration de l'environnement..."

if [ ! -f .env ]; then
    echo "📝 Création du fichier .env..."
    cat > .env << EOF
# Database
DATABASE_URL=postgresql://trading_user:trading_password@localhost:5432/trading_etf

# Redis
REDIS_URL=redis://localhost:6379

# APIs externes (optionnel)
ALPHA_VANTAGE_API_KEY=demo
YAHOO_FINANCE_API_KEY=
FINANCIAL_MODELING_PREP_API_KEY=demo

# Security
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production

# Environment
ENVIRONMENT=development
EOF
    echo "✅ Fichier .env créé"
else
    echo "✅ Fichier .env existe déjà"
fi

# Démarrer les services d'infrastructure (PostgreSQL, Redis)
echo "🗄️  Démarrage des services d'infrastructure..."
docker-compose up -d postgres redis

# Attendre que PostgreSQL soit prêt
echo "⏳ Attente de PostgreSQL..."
timeout=30
while ! docker-compose exec -T postgres pg_isready -U trading_user -d trading_etf >/dev/null 2>&1; do
    sleep 1
    timeout=$((timeout - 1))
    if [ $timeout -eq 0 ]; then
        echo "❌ Timeout: PostgreSQL n'est pas démarré"
        exit 1
    fi
done
echo "✅ PostgreSQL est prêt"

# Attendre que Redis soit prêt
echo "⏳ Attente de Redis..."
timeout=30
while ! docker-compose exec -T redis redis-cli ping >/dev/null 2>&1; do
    sleep 1
    timeout=$((timeout - 1))
    if [ $timeout -eq 0 ]; then
        echo "❌ Timeout: Redis n'est pas démarré"
        exit 1
    fi
done
echo "✅ Redis est prêt"

# Installer/Mettre à jour les dépendances backend
echo "📦 Installation des dépendances backend..."
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Générer les clés VAPID si elles n'existent pas
if ! grep -q "VAPID_PRIVATE_KEY" ../.env 2>/dev/null; then
    echo "🔑 Génération des clés VAPID pour les notifications push..."
    python generate_vapid_keys.py
fi

echo "✅ Dépendances backend installées"

# Initialiser la base de données
echo "🗄️  Initialisation de la base de données..."
cd ../
python backend/add_sample_data.py
echo "✅ Base de données initialisée"

# Démarrer le backend FastAPI
echo "🖥️  Démarrage du backend FastAPI..."
cd backend
source venv/bin/activate
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ../

# Attendre que le backend soit prêt
echo "⏳ Attente du backend..."
timeout=30
while ! curl -s http://localhost:8000/health >/dev/null 2>&1; do
    sleep 1
    timeout=$((timeout - 1))
    if [ $timeout -eq 0 ]; then
        echo "❌ Timeout: Backend n'est pas démarré"
        kill $BACKEND_PID 2>/dev/null || true
        exit 1
    fi
done
echo "✅ Backend est prêt"

# Démarrer Celery Worker pour les tâches temps réel
echo "⚡ Démarrage de Celery Worker..."
cd backend
source venv/bin/activate
nohup celery -A app.celery_app worker --loglevel=info > ../logs/celery_worker.log 2>&1 &
CELERY_WORKER_PID=$!

# Démarrer Celery Beat pour les tâches périodiques
echo "⏰ Démarrage de Celery Beat..."
nohup celery -A app.celery_app beat --loglevel=info > ../logs/celery_beat.log 2>&1 &
CELERY_BEAT_PID=$!
cd ../

echo "✅ Celery Worker et Beat démarrés"

# Installer/Mettre à jour les dépendances frontend
echo "📦 Installation des dépendances frontend..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install --silent
else
    npm install --silent
fi
echo "✅ Dépendances frontend installées"

# Démarrer le frontend React
echo "🌐 Démarrage du frontend React..."
nohup npm start > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ../

# Attendre que le frontend soit prêt
echo "⏳ Attente du frontend..."
timeout=60
while ! curl -s http://localhost:3000 >/dev/null 2>&1; do
    sleep 2
    timeout=$((timeout - 2))
    if [ $timeout -eq 0 ]; then
        echo "❌ Timeout: Frontend n'est pas démarré"
        break
    fi
done

# Créer le dossier de logs s'il n'existe pas
mkdir -p logs

# Sauvegarder les PIDs pour pouvoir arrêter les services
echo $BACKEND_PID > logs/backend.pid
echo $CELERY_WORKER_PID > logs/celery_worker.pid
echo $CELERY_BEAT_PID > logs/celery_beat.pid
echo $FRONTEND_PID > logs/frontend.pid

echo ""
echo "🎉 Application Trading ETF démarrée avec succès!"
echo "================================================"
echo ""
echo "📋 Services disponibles:"
echo "   • Frontend React:      http://localhost:3000"
echo "   • Backend API:         http://localhost:8000"
echo "   • Documentation API:   http://localhost:8000/docs"
echo "   • PostgreSQL:          localhost:5432"
echo "   • Redis:               localhost:6379"
echo ""
echo "📊 Fonctionnalités implémentées:"
echo "   ✅ Collecte de données ETF temps réel (Yahoo Finance, Alpha Vantage)"
echo "   ✅ Moteur d'analyse technique complet (SMA, EMA, RSI, MACD, Bollinger Bands)"
echo "   ✅ Génération de signaux automatisés (BUY/SELL/HOLD/WAIT)"
echo "   ✅ Catalogue d'ETFs européens populaires"
echo "   ✅ Interface de sélection ETF personnalisée"
echo "   ✅ Collecte de données temps réel avec Celery"
echo "   ✅ Gestion de portefeuille avec calculs de performance"
echo "   ✅ Graphiques avancés avec indicateurs techniques"
echo ""
echo "📝 Logs disponibles dans le dossier logs/"
echo "   • Backend:       logs/backend.log"
echo "   • Celery Worker: logs/celery_worker.log"
echo "   • Celery Beat:   logs/celery_beat.log"
echo "   • Frontend:      logs/frontend.log"
echo ""
echo "🛑 Pour arrêter l'application: ./stop_app.sh"
echo ""
echo "🔍 Test rapide:"
echo "   curl http://localhost:8000/api/v1/market/etfs/popular"
echo "   curl http://localhost:8000/api/v1/etfs/catalog"
echo ""

# Créer le script d'arrêt
cat > stop_app.sh << 'EOF'
#!/bin/bash
echo "🛑 Arrêt de l'application Trading ETF..."

# Arrêter les services Node.js et Python
if [ -f logs/frontend.pid ]; then
    kill $(cat logs/frontend.pid) 2>/dev/null || true
    rm logs/frontend.pid
fi

if [ -f logs/backend.pid ]; then
    kill $(cat logs/backend.pid) 2>/dev/null || true
    rm logs/backend.pid
fi

if [ -f logs/celery_worker.pid ]; then
    kill $(cat logs/celery_worker.pid) 2>/dev/null || true
    rm logs/celery_worker.pid
fi

if [ -f logs/celery_beat.pid ]; then
    kill $(cat logs/celery_beat.pid) 2>/dev/null || true
    rm logs/celery_beat.pid
fi

# Arrêter les conteneurs Docker
docker-compose down

echo "✅ Application arrêtée"
EOF

chmod +x stop_app.sh

echo "📈 L'application Trading ETF est maintenant opérationnelle!"
echo "Rendez-vous sur http://localhost:3000 pour commencer à trader!"