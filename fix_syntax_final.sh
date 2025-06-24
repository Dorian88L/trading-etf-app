#!/bin/bash

echo "🔧 Correction finale de la syntaxe des appels fetch..."

cd /home/dorian/trading-etf-app/frontend

# Corriger les patterns problématiques
# Pattern: getApiUrl('/api/...'), { => getApiUrl('/api/...'), {
find src/ -name "*.tsx" -o -name "*.ts" | xargs sed -i 's/getApiUrl(\([^)]*\)), {/getApiUrl(\1), {/g'

# Pattern: fetch(getApiUrl(API_CONFIG.ENDPOINTS.DASHBOARD_STATS)), { => fetch(getApiUrl(API_CONFIG.ENDPOINTS.DASHBOARD_STATS), {
find src/ -name "*.tsx" -o -name "*.ts" | xargs sed -i 's/fetch(getApiUrl(\([^)]*\))), {/fetch(getApiUrl(\1), {/g'

# Pattern: fetch(`${fetch(getApiUrl( => fetch(getApiUrl(
find src/ -name "*.tsx" -o -name "*.ts" | xargs sed -i 's/fetch(`\${fetch(getApiUrl(/fetch(getApiUrl(/g'

# Pattern: )}`), { => ), {
find src/ -name "*.tsx" -o -name "*.ts" | xargs sed -i 's/)}`), {/), {/g'

echo "✅ Correction finale terminée !"

# Vérifier s'il reste des erreurs
echo "🔍 Vérification des erreurs restantes..."
if grep -r "getApiUrl.*)), {" src/; then
    echo "❌ Il reste des erreurs de syntaxe à corriger manuellement"
else
    echo "✅ Toutes les erreurs de syntaxe ont été corrigées !"
fi