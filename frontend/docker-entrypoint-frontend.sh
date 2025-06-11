#!/bin/sh
set -e

echo "🚀 Démarrage du frontend Trading ETF en mode PRODUCTION"

# Vérifications de sécurité
echo "🔍 Vérifications de sécurité..."

# Vérifier les permissions des fichiers
find /usr/share/nginx/html -name "*.js" -perm /o+w -exec echo "⚠️ Fichier JS accessible en écriture: {}" \;
find /usr/share/nginx/html -name "*.html" -perm /o+w -exec echo "⚠️ Fichier HTML accessible en écriture: {}" \;

# Vérifier qu'aucun fichier sensible n'est présent
if find /usr/share/nginx/html -name "*.env*" | grep -q .; then
    echo "❌ ERREUR: Fichiers .env détectés dans les assets !"
    exit 1
fi

if find /usr/share/nginx/html -name "*.map" | grep -q .; then
    echo "⚠️ ATTENTION: Source maps détectées (recommandé de les supprimer en production)"
fi

# Vérifier la configuration nginx
echo "🔧 Validation de la configuration Nginx..."
nginx -t

echo "✅ Vérifications terminées"

# Créer les répertoires de logs si nécessaire
mkdir -p /var/log/nginx

# Démarrer nginx
echo "🌐 Démarrage de Nginx..."
exec "$@"