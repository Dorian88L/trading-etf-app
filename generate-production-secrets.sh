#!/bin/bash
set -e

echo "🔐 Génération des secrets pour l'environnement de production"
echo "=================================================="

# Créer le répertoire pour les secrets
mkdir -p ./secrets

# Fonction pour générer une clé sécurisée
generate_secret() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-32
}

# Fonction pour générer un mot de passe complexe
generate_password() {
    openssl rand -base64 32 | tr -d "=+/"
}

# Générer JWT Secret Key
JWT_SECRET=$(openssl rand -hex 32)
echo "✅ JWT_SECRET_KEY généré"

# Générer les mots de passe base de données
POSTGRES_USER="trading_prod_$(openssl rand -hex 8)"
POSTGRES_PASSWORD=$(generate_password)
echo "✅ Credentials PostgreSQL générés"

# Générer le mot de passe Redis
REDIS_PASSWORD=$(generate_password)
echo "✅ Mot de passe Redis généré"

# Générer les clés VAPID pour les notifications push
echo "🔑 Génération des clés VAPID..."
cd backend
source venv/bin/activate
python3 -c "
import base64
from py_vapid import Vapid

# Générer une nouvelle paire de clés VAPID
vapid = Vapid()
vapid.generate_keys()

# Récupérer les clés
private_key_pem = vapid.private_key_pem().decode().replace('\n', '\\n')
public_key_hex = vapid.public_key.public_bytes_uncompressed().hex()

print(f'VAPID_PRIVATE_KEY=\"{private_key_pem}\"')
print(f'VAPID_PUBLIC_KEY={public_key_hex}')
" > ../secrets/vapid_keys.env 2>/dev/null || echo "VAPID_PRIVATE_KEY=demo_private_key_replace_in_production
VAPID_PUBLIC_KEY=demo_public_key_replace_in_production" > ../secrets/vapid_keys.env
cd ..
echo "✅ Clés VAPID générées"

# Créer le fichier .env.production avec les secrets
cat > .env.production << EOF
# CONFIGURATION PRODUCTION - Trading ETF App
# ⚠️ IMPORTANT: Ce fichier contient des secrets - ne jamais le committer !
# Généré le: $(date)

# Environment
ENVIRONMENT=production
DEBUG=false

# Security
JWT_SECRET_KEY=${JWT_SECRET}
ALGORITHM=HS256

# Database
POSTGRES_USER=${POSTGRES_USER}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}

# Redis
REDIS_PASSWORD=${REDIS_PASSWORD}

# External APIs - À REMPLACER par vos vraies clés
ALPHA_VANTAGE_API_KEY=your_real_alpha_vantage_key
YAHOO_FINANCE_API_KEY=your_real_yahoo_key
FINANCIAL_MODELING_PREP_API_KEY=your_real_fmp_key

# Push Notifications (VAPID)
$(cat secrets/vapid_keys.env)
VAPID_EMAIL=admin@yourcompany.com

# CORS et domaines autorisés - À REMPLACER par vos vrais domaines
CORS_ALLOWED_ORIGINS=https://yourapp.com,https://www.yourapp.com
ALLOWED_HOSTS=yourapp.com,www.yourapp.com

# React App Configuration
REACT_APP_API_URL=https://api.yourapp.com

# Monitoring (optionnel)
SENTRY_DSN=your_sentry_dsn_for_error_tracking
LOG_LEVEL=WARNING

# Rate Limiting
RATE_LIMIT_REQUESTS=50
RATE_LIMIT_WINDOW=60
EOF

echo "✅ Fichier .env.production créé"

# Créer un fichier de sauvegarde sécurisé
cp .env.production "secrets/env-production-backup-$(date +%Y%m%d-%H%M%S).txt"

# Sécuriser les permissions
chmod 600 .env.production
chmod 700 secrets/
chmod 600 secrets/*

echo ""
echo "🎉 SECRETS GÉNÉRÉS AVEC SUCCÈS !"
echo "================================"
echo ""
echo "📁 Fichiers créés :"
echo "   - .env.production (secrets pour docker-compose)"
echo "   - secrets/vapid_keys.env (clés VAPID)"
echo "   - secrets/env-production-backup-*.txt (sauvegarde)"
echo ""
echo "⚠️  ACTIONS REQUISES AVANT LE DÉPLOIEMENT :"
echo ""
echo "1. 🔑 REMPLACER les clés d'API factices dans .env.production :"
echo "   - ALPHA_VANTAGE_API_KEY"
echo "   - YAHOO_FINANCE_API_KEY"  
echo "   - FINANCIAL_MODELING_PREP_API_KEY"
echo ""
echo "2. 🌐 CONFIGURER vos vrais domaines :"
echo "   - CORS_ALLOWED_ORIGINS"
echo "   - ALLOWED_HOSTS"
echo "   - REACT_APP_API_URL"
echo ""
echo "3. 📊 CONFIGURER le monitoring (optionnel) :"
echo "   - SENTRY_DSN"
echo ""
echo "4. 🔒 SAUVEGARDER ces secrets dans un gestionnaire de mots de passe !"
echo ""
echo "5. 📜 AJOUTER .env.production au .gitignore :"
echo "   echo '.env.production' >> .gitignore"
echo ""
echo "🚀 Une fois configuré, lancez :"
echo "   docker-compose -f docker-compose.production.yml up -d"
echo ""

# Ajouter au .gitignore si pas déjà présent
if ! grep -q ".env.production" .gitignore 2>/dev/null; then
    echo ".env.production" >> .gitignore
    echo "secrets/" >> .gitignore
    echo "✅ .env.production ajouté au .gitignore"
fi