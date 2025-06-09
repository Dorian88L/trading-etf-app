#!/bin/bash

echo "🔍 Vérification de la page ETF..."

# Vérifier si le serveur de développement fonctionne
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Serveur frontend accessible"
else
    echo "❌ Serveur frontend non accessible sur http://localhost:3000"
    exit 1
fi

# Vérifier la route /etfs
echo "📄 Test de la route /etfs..."
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/etfs)
if [ "$response" -eq 200 ]; then
    echo "✅ Route /etfs accessible (HTTP $response)"
else
    echo "⚠️  Route /etfs retourne HTTP $response"
fi

# Vérifier si le backend API fonctionne
echo "🔧 Test de l'API backend..."
api_response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/real-market/real-etfs)
if [ "$api_response" -eq 200 ] || [ "$api_response" -eq 401 ]; then
    echo "✅ API backend accessible (HTTP $api_response)"
else
    echo "❌ API backend non accessible (HTTP $api_response)"
fi

# Vérifier les dépendances critiques
echo "📦 Vérification des dépendances..."
cd /home/dorian/trading-etf-app/frontend

# Vérifier que les modules critiques sont installés
if npm list react-router-dom > /dev/null 2>&1; then
    echo "✅ react-router-dom installé"
else
    echo "❌ react-router-dom manquant"
fi

if npm list @heroicons/react > /dev/null 2>&1; then
    echo "✅ @heroicons/react installé"
else
    echo "❌ @heroicons/react manquant"
fi

if npm list axios > /dev/null 2>&1; then
    echo "✅ axios installé"
else
    echo "❌ axios manquant"
fi

echo ""
echo "📋 Résumé des problèmes potentiels identifiés:"
echo ""
echo "1. 🔧 Optimisations appliquées:"
echo "   - Ajout de useMemo pour le filtrage et tri"
echo "   - Gestion d'erreur améliorée dans l'API call"
echo "   - Validation des données avant formatage"
echo "   - Sécurisation des fonctions de formatage"
echo ""
echo "2. 🛡️  Sécurité:"
echo "   - Protection contre les valeurs null/undefined"
echo "   - Gestion des erreurs de formatage de devise"
echo "   - Validation des types avant affichage"
echo ""
echo "3. 📊 Diagnostic:"
echo "   - Composant de diagnostic en mode développement"
echo "   - Logs détaillés pour le débogage"
echo ""
echo "4. ⚡ Performance:"
echo "   - Évitement des re-calculs inutiles"
echo "   - Optimisation des listes de filtres"
echo ""

echo "✅ Vérification terminée!"