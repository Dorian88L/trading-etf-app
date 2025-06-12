#!/bin/bash

echo "🔍 DIAGNOSTIC COMPLET - PROBLÈME SIGNUP"
echo "========================================"
echo

echo "1. VÉRIFICATION DES SERVICES"
echo "----------------------------"
echo "Frontend (port 3000):"
ss -tlnp | grep :3000 && echo "✅ Frontend actif" || echo "❌ Frontend inactif"

echo "Backend (port 8000):"
ss -tlnp | grep :8000 && echo "✅ Backend actif" || echo "❌ Backend inactif"

echo "Nginx (ports 80/443):"
ss -tlnp | grep -E ':80|:443' | head -2

echo

echo "2. TEST DIRECT API"
echo "------------------"
echo "Test health check:"
curl -k -s https://api.investeclaire.fr/health && echo " ✅" || echo " ❌"

echo "Test inscription direct:"
RESPONSE=$(curl -k -s -X POST https://api.investeclaire.fr/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"debug@test.com","password":"test123","full_name":"Debug Test"}' \
  -w "%{http_code}")

if [[ "$RESPONSE" == *"200"* ]]; then
    echo "✅ API inscription fonctionne"
else
    echo "❌ API inscription échoue: $RESPONSE"
fi

echo

echo "3. VÉRIFICATION CONFIGURATION FRONTEND"
echo "--------------------------------------"
echo "Variables d'environnement (.env):"
cat /home/dorian/trading-etf-app/frontend/.env

echo

echo "4. TEST DEPUIS LE FRONTEND"
echo "--------------------------"
echo "Accès page principale:"
curl -k -s -I https://investeclaire.fr | head -1

echo "Test page de debug disponible:"
curl -k -s -I https://investeclaire.fr/test.html | head -1

echo

echo "5. LOGS RÉCENTS"
echo "---------------"
echo "Backend logs (dernières 5 lignes):"
tail -5 /home/dorian/trading-etf-app/backend/logs/backend.log

echo
echo "Frontend logs (dernières 5 lignes):"
tail -5 /home/dorian/trading-etf-app/logs/frontend.log

echo

echo "6. CONFIGURATION NGINX"
echo "----------------------"
nginx -t && echo "✅ Configuration nginx valide" || echo "❌ Configuration nginx invalide"

echo

echo "🎯 INSTRUCTIONS DE TEST:"
echo "========================"
echo "1. Allez sur: https://investeclaire.fr/test.html"
echo "2. Testez l'inscription directement"
echo "3. Ouvrez F12 sur https://investeclaire.fr/register"
echo "4. Regardez la console pour les messages 🔧 DEBUG"
echo "5. Tentez une inscription et notez l'erreur exacte"