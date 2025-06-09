#!/bin/bash

# Script simple pour démarrer l'application en mode développement

echo "🚀 Démarrage simple de l'application Trading ETF"
echo "==============================================="

# Créer dossier logs
mkdir -p logs

# Démarrer PostgreSQL si nécessaire (en local ou Docker)
echo "🗄️ Démarrage de PostgreSQL (Docker)..."
docker run -d --name postgres-trading \
  -e POSTGRES_USER=trading_user \
  -e POSTGRES_PASSWORD=trading_password \
  -e POSTGRES_DB=trading_etf \
  -p 5432:5432 \
  postgres:13 2>/dev/null || echo "PostgreSQL déjà en cours ou échec de démarrage"

# Démarrer Redis
echo "📦 Démarrage de Redis (Docker)..."
docker run -d --name redis-trading \
  -p 6379:6379 \
  redis:alpine 2>/dev/null || echo "Redis déjà en cours ou échec de démarrage"

# Attendre que les services soient prêts
sleep 5

# Démarrer le backend
echo "🖥️ Démarrage du backend FastAPI..."
cd backend
source venv/bin/activate
export DATABASE_URL="postgresql://trading_user:trading_password@localhost:5432/trading_etf"
export REDIS_URL="redis://localhost:6379"
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > ../logs/backend.pid
cd ..

# Attendre que le backend soit prêt
echo "⏳ Attente du backend (30s max)..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        echo "✅ Backend prêt"
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
BROWSER=none nohup npm start > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../logs/frontend.pid
cd ..

# Attendre que le frontend soit prêt
echo "⏳ Attente du frontend (60s max)..."
for i in {1..60}; do
    if curl -s http://localhost:3000 >/dev/null 2>&1; then
        echo "✅ Frontend prêt"
        break
    fi
    if [ $i -eq 60 ]; then
        echo "⚠️ Frontend peut prendre plus de temps"
        break
    fi
    sleep 1
done

echo ""
echo "🎉 Application démarrée!"
echo "======================="
echo ""
echo "📋 URLs:"
echo "   • Frontend:  http://localhost:3000"
echo "   • Backend:   http://localhost:8000"
echo "   • Swagger:   http://localhost:8000/docs"
echo ""
echo "📝 Logs:"
echo "   • Backend:   logs/backend.log"
echo "   • Frontend:  logs/frontend.log"
echo ""
echo "🛑 Pour arrêter: ./stop_dev_simple.sh"

# Créer script d'arrêt
cat > stop_dev_simple.sh << 'EOF'
#!/bin/bash
echo "🛑 Arrêt de l'application..."

if [ -f logs/backend.pid ]; then
    kill $(cat logs/backend.pid) 2>/dev/null || true
    rm logs/backend.pid
fi

if [ -f logs/frontend.pid ]; then
    kill $(cat logs/frontend.pid) 2>/dev/null || true
    rm logs/frontend.pid
fi

docker stop postgres-trading redis-trading 2>/dev/null || true
docker rm postgres-trading redis-trading 2>/dev/null || true

echo "✅ Application arrêtée"
EOF

chmod +x stop_dev_simple.sh

echo "✨ Prêt à utiliser!"