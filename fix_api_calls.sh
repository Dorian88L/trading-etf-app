#!/bin/bash

# Script pour corriger tous les appels API directs dans le frontend

echo "🔧 Correction des appels API pour utiliser les noms de domaine..."

cd /home/dorian/trading-etf-app/frontend

# Fonction pour ajouter l'import getApiUrl si absent
add_import_if_missing() {
    local file=$1
    if ! grep -q "import.*getApiUrl" "$file"; then
        # Trouve la dernière ligne d'import et ajoute après
        local last_import_line=$(grep -n "^import" "$file" | tail -1 | cut -d: -f1)
        if [ -n "$last_import_line" ]; then
            sed -i "${last_import_line}a import { getApiUrl } from '../config/api';" "$file"
            echo "✅ Import ajouté dans $file"
        fi
    fi
}

# Fonction pour corriger les appels fetch
fix_fetch_calls() {
    local file=$1
    echo "🔄 Correction de $file..."
    
    # Ajouter l'import si nécessaire
    add_import_if_missing "$file"
    
    # Remplacer les appels fetch('/api/... par fetch(getApiUrl('/api/...
    sed -i "s|fetch('/api/|fetch(getApiUrl('/api/|g" "$file"
    sed -i "s|fetch(\`/api/|fetch(getApiUrl(\`/api/|g" "$file"
    
    echo "✅ $file corrigé"
}

# Liste des fichiers à corriger
files=(
    "src/pages/ETFSelection.tsx"
    "src/pages/Signals.tsx"
    "src/pages/Portfolio.tsx"
    "src/pages/Dashboard.tsx"
    "src/pages/NotificationSettings.tsx"
    "src/components/WatchlistManager.tsx"
    "src/components/RiskManagement.tsx"
    "src/components/backtesting/AdvancedBacktestingEngine.tsx"
    "src/components/NotificationCenter.tsx"
    "src/components/SmartSearch.tsx"
    "src/components/ETFSelector.tsx"
)

# Correction de chaque fichier
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        fix_fetch_calls "$file"
    else
        echo "❌ Fichier non trouvé: $file"
    fi
done

echo "🎉 Correction terminée ! Tous les appels API utilisent maintenant getApiUrl()"
echo "📋 En production, les requêtes iront vers: https://api.investeclaire.fr"