#!/usr/bin/env python3
"""
Test de l'application en mode production avec sécurité
"""
import os
import sys
import uvicorn
import logging
from pathlib import Path

# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def validate_production_environment():
    """Valide les variables d'environnement pour la production"""
    required_vars = [
        'JWT_SECRET_KEY',
        'DATABASE_URL',
        'REDIS_URL'
    ]
    
    missing_vars = []
    weak_keys = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        elif var == 'JWT_SECRET_KEY' and (
            len(value) < 32 or 
            value in ['your-secret-key-change-in-production', 'dev-key', 'test']
        ):
            weak_keys.append(var)
    
    if missing_vars:
        logger.error(f"❌ Variables manquantes: {', '.join(missing_vars)}")
        return False
    
    if weak_keys:
        logger.warning(f"⚠️ Clés faibles détectées: {', '.join(weak_keys)}")
    
    logger.info("✅ Variables d'environnement validées")
    return True

def setup_production_security():
    """Configure la sécurité pour la production"""
    # Désactiver le mode debug
    os.environ['DEBUG'] = 'false'
    os.environ['ENVIRONMENT'] = 'production'
    
    # Configuration CORS stricte (à partir des variables d'environnement)
    cors_origins = os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:3000')
    allowed_hosts = os.getenv('ALLOWED_HOSTS', 'localhost')
    
    logger.info(f"🔒 CORS configuré: {cors_origins}")
    logger.info(f"🔒 Hosts autorisés: {allowed_hosts}")

def main():
    """Point d'entrée principal"""
    logger.info("🚀 Démarrage de l'application Trading ETF en mode PRODUCTION TEST")
    
    # Validation de l'environnement
    if not validate_production_environment():
        logger.error("❌ Échec de la validation de l'environnement")
        sys.exit(1)
    
    # Configuration de la sécurité
    setup_production_security()
    
    try:
        # Import de l'application après configuration
        from app.main_production import app
        
        logger.info("✅ Application chargée avec succès")
        
        # Configuration uvicorn pour la production
        uvicorn_config = {
            "app": app,
            "host": "0.0.0.0",
            "port": 8000,
            "log_level": "info",
            "access_log": True,
            "server_header": False,  # Masquer les headers serveur
            "date_header": True,
        }
        
        logger.info("🌐 Démarrage du serveur sur http://0.0.0.0:8000")
        logger.info("📚 Documentation disponible sur: http://localhost:8000/docs")
        logger.info("💚 Health check disponible sur: http://localhost:8000/health")
        
        # Démarrer le serveur
        uvicorn.run(**uvicorn_config)
        
    except KeyboardInterrupt:
        logger.info("⏹️ Arrêt demandé par l'utilisateur")
    except Exception as e:
        logger.error(f"❌ Erreur lors du démarrage: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()