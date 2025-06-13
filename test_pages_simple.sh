#!/bin/bash

# Script simple pour tester les pages du frontend Trading ETF
# Vérifie si les pages répondent et si le HTML de base est présent

FRONTEND_URL="http://localhost:3000"
BACKEND_URL="http://localhost:8443"

echo "🚀 Test des pages frontend Trading ETF"
echo "======================================="
echo ""

# Array des pages à tester
declare -a pages=(
    "/:Dashboard/Home"
    "/etfs:ETF List"
    "/signals:Signals"
    "/portfolio:Portfolio"
    "/alerts:Alerts"
    "/settings:Settings"
    "/login:Login"
)

echo "📡 Test de connectivité..."
echo "Frontend URL: $FRONTEND_URL"
echo "Backend URL: $BACKEND_URL"
echo ""

# Test connectivité backend
if curl -s -f "$BACKEND_URL/health" > /dev/null; then
    echo "✅ Backend accessible"
else
    echo "❌ Backend non accessible"
fi

# Test connectivité frontend
if curl -s -f "$FRONTEND_URL" > /dev/null; then
    echo "✅ Frontend accessible"
else
    echo "❌ Frontend non accessible"
    exit 1
fi

echo ""
echo "📄 Test des pages individuelles..."
echo ""

success_count=0
total_count=${#pages[@]}

for page_info in "${pages[@]}"; do
    IFS=':' read -r path name <<< "$page_info"
    url="${FRONTEND_URL}${path}"
    
    echo "Testing: $name ($path)"
    
    # Faire la requête
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" "$url")
    http_code=$(echo "$response" | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
    body=$(echo "$response" | sed '/HTTPSTATUS:/d')
    
    # Vérifications
    has_html_tag=$(echo "$body" | grep -q "<html" && echo "✅" || echo "❌")
    has_react_root=$(echo "$body" | grep -q 'id="root"' && echo "✅" || echo "❌")
    has_bundle_js=$(echo "$body" | grep -q "bundle.js" && echo "✅" || echo "❌")
    has_title=$(echo "$body" | grep -q "<title>" && echo "✅" || echo "❌")
    
    echo "  HTTP Status: $http_code"
    echo "  HTML structure: $has_html_tag"
    echo "  React root div: $has_react_root"
    echo "  Bundle JS: $has_bundle_js"
    echo "  Title tag: $has_title"
    
    # Vérifier s'il y a des erreurs évidentes dans le HTML
    if echo "$body" | grep -q "Cannot GET"; then
        echo "  ❌ Erreur: Route non trouvée"
    elif echo "$body" | grep -q "Error"; then
        echo "  ⚠️  Possible erreur détectée"
    else
        echo "  ✅ Pas d'erreurs évidentes"
    fi
    
    # Compter comme succès si HTTP 200 et structure HTML présente
    if [[ "$http_code" == "200" ]] && [[ "$has_html_tag" == "✅" ]] && [[ "$has_react_root" == "✅" ]]; then
        ((success_count++))
        echo "  🎉 SUCCÈS"
    else
        echo "  💥 ÉCHEC"
    fi
    
    echo ""
done

echo "📊 RÉSULTATS FINAUX"
echo "==================="
echo "Pages testées: $total_count"
echo "Pages fonctionnelles: $success_count"
echo "Taux de succès: $(( (success_count * 100) / total_count ))%"
echo ""

# Test des endpoints backend critiques
echo "🔧 Test des endpoints backend critiques..."
echo ""

# Créer un utilisateur test et récupérer un token
echo "Création utilisateur test..."
test_email="testpage@example.com"
test_password="testpass123"

# Register user (ignorer si existe déjà)
curl -s -X POST "$BACKEND_URL/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$test_email\",\"password\":\"$test_password\",\"full_name\":\"Test User\"}" > /dev/null 2>&1

# Login to get token
login_response=$(curl -s -X POST "$BACKEND_URL/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$test_email&password=$test_password")

if echo "$login_response" | grep -q "access_token"; then
    token=$(echo "$login_response" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    echo "✅ Authentification réussie"
    
    # Test des endpoints utilisés par le frontend
    declare -a endpoints=(
        "/api/v1/market/etfs:ETFs List"
        "/api/v1/market/dashboard-stats:Dashboard Stats"
        "/api/v1/market/real-etfs:Real ETFs"
        "/api/v1/signals/active:Active Signals"
        "/api/v1/portfolio/positions:Portfolio Positions"
        "/api/v1/alerts/:Alerts"
        "/api/v1/user/profile:User Profile"
    )
    
    for endpoint_info in "${endpoints[@]}"; do
        IFS=':' read -r endpoint description <<< "$endpoint_info"
        
        response=$(curl -s -w "HTTPSTATUS:%{http_code}" \
          -H "Authorization: Bearer $token" \
          "$BACKEND_URL$endpoint")
        
        http_code=$(echo "$response" | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
        
        if [[ "$http_code" == "200" ]]; then
            echo "✅ $description ($endpoint)"
        else
            echo "❌ $description ($endpoint) - Status: $http_code"
        fi
    done
else
    echo "❌ Échec de l'authentification"
fi

echo ""
echo "🏁 Test terminé!"