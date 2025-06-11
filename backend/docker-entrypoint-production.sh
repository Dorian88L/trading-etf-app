#!/bin/bash
set -e

echo "🚀 Démarrage de l'application Trading ETF en mode PRODUCTION"

# Validation des variables d'environnement critiques
check_env_var() {
    if [ -z "${!1}" ]; then
        echo "❌ ERREUR: Variable d'environnement $1 manquante"
        exit 1
    fi
}

echo "🔍 Validation des variables d'environnement..."
check_env_var "JWT_SECRET_KEY"
check_env_var "DATABASE_URL"
check_env_var "REDIS_URL"

# Vérifier que JWT_SECRET_KEY n'est pas une valeur par défaut
if [[ "$JWT_SECRET_KEY" == *"your-secret-key"* ]] || [[ "$JWT_SECRET_KEY" == *"change-in-production"* ]]; then
    echo "❌ ERREUR: JWT_SECRET_KEY utilise une valeur par défaut non sécurisée"
    exit 1
fi

# Vérifier la longueur de la clé secrète
if [ ${#JWT_SECRET_KEY} -lt 32 ]; then
    echo "❌ ERREUR: JWT_SECRET_KEY trop courte (minimum 32 caractères)"
    exit 1
fi

echo "✅ Variables d'environnement validées"

# Attendre que les services de base soient disponibles
echo "⏳ Attente de la base de données..."
python -c "
import psycopg2
import os
import time
import sys
from urllib.parse import urlparse

url = urlparse(os.environ['DATABASE_URL'])
max_attempts = 30
attempt = 0

while attempt < max_attempts:
    try:
        conn = psycopg2.connect(
            host=url.hostname,
            port=url.port or 5432,
            user=url.username,
            password=url.password,
            database=url.path[1:]
        )
        conn.close()
        print('✅ Base de données accessible')
        break
    except Exception as e:
        attempt += 1
        print(f'⏳ Tentative {attempt}/{max_attempts} - En attente de la base de données...')
        time.sleep(2)

if attempt >= max_attempts:
    print('❌ Impossible de se connecter à la base de données')
    sys.exit(1)
"

echo "⏳ Attente de Redis..."
python -c "
import redis
import os
import time
import sys
from urllib.parse import urlparse

url = urlparse(os.environ['REDIS_URL'])
max_attempts = 30
attempt = 0

while attempt < max_attempts:
    try:
        r = redis.Redis(
            host=url.hostname,
            port=url.port or 6379,
            password=url.password,
            db=0
        )
        r.ping()
        print('✅ Redis accessible')
        break
    except Exception as e:
        attempt += 1
        print(f'⏳ Tentative {attempt}/{max_attempts} - En attente de Redis...')
        time.sleep(2)

if attempt >= max_attempts:
    print('❌ Impossible de se connecter à Redis')
    sys.exit(1)
"

# Initialiser la base de données si nécessaire (uniquement au premier démarrage)
if [ "$INIT_DB" = "true" ]; then
    echo "🗄️ Initialisation de la base de données..."
    python -c "
from app.core.database import engine
from app.models.user import Base
import logging

logging.basicConfig(level=logging.INFO)
try:
    Base.metadata.create_all(bind=engine)
    print('✅ Tables créées avec succès')
except Exception as e:
    print(f'❌ Erreur lors de la création des tables: {e}')
    exit(1)
"
fi

# Vérifications de sécurité supplémentaires
echo "🔒 Vérifications de sécurité..."

# Vérifier que l'application n'est pas en mode debug
if [ "$DEBUG" = "true" ]; then
    echo "⚠️ ATTENTION: Mode debug activé en production (non recommandé)"
fi

# Vérifier les permissions des fichiers
echo "🔍 Vérification des permissions..."
find /app -name "*.py" -perm /o+w -exec echo "⚠️ Fichier accessible en écriture par tous: {}" \;

echo "✅ Vérifications de sécurité terminées"

# Démarrer l'application
echo "🚀 Démarrage de l'application..."
exec "$@"