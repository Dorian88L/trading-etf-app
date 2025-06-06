#!/bin/bash

echo "🚀 Push vers GitHub avec Personal Access Token"
echo ""
echo "📋 Instructions :"
echo "1. Va sur GitHub.com > Settings > Developer settings > Personal access tokens"
echo "2. Generate new token (classic) avec scope 'repo'"
echo "3. Copie le token et colle-le quand demandé"
echo ""

read -p "Appuie sur Entrée quand tu as ton token prêt..."

echo ""
echo "🔑 Push avec authentification..."

# Configurer l'URL avec le nom d'utilisateur
git remote set-url origin https://Dorian88L@github.com/Dorian88L/trading-etf-app.git

# Pousser (GitHub demandera le token comme mot de passe)
git push -u origin main

echo ""
echo "✅ Si le push a réussi, ton code est maintenant sur GitHub !"
echo "🌐 Repository : https://github.com/Dorian88L/trading-etf-app"