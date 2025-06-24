#!/bin/bash

echo "🔧 Correction de la syntaxe des appels getApiUrl..."

cd /home/dorian/trading-etf-app/frontend

# Corriger la syntaxe incorrecte getApiUrl('/api/...', { dans tous les fichiers
find src/ -name "*.tsx" -o -name "*.ts" | xargs sed -i 's/getApiUrl(\([^,]*\), {/fetch(getApiUrl(\1), {/g'

# Corriger les cas où il y a deux fetch( consécutifs
find src/ -name "*.tsx" -o -name "*.ts" | xargs sed -i 's/fetch(fetch(getApiUrl(/fetch(getApiUrl(/g'

echo "✅ Syntaxe des appels getApiUrl corrigée !"