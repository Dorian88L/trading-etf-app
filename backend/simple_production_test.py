#!/usr/bin/env python3
"""
Test simple de production avec security middleware
"""
import os
import sys
import uvicorn
import logging

# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_environment():
    """Configure les variables d'environnement de base"""
    os.environ['ENVIRONMENT'] = 'production'
    os.environ['DEBUG'] = 'false'
    os.environ['JWT_SECRET_KEY'] = 'b4d75d113f67a3857febe2495b1ec4c9c9d56441c18946cedf833707269f814d'
    os.environ['DATABASE_URL'] = 'postgresql://trading_user:trading_password@localhost:5433/trading_etf'
    os.environ['REDIS_URL'] = 'redis://localhost:6380'
    os.environ['RATE_LIMIT_REQUESTS'] = '100'
    os.environ['RATE_LIMIT_WINDOW'] = '60'
    os.environ['LOG_LEVEL'] = 'INFO'
    # Permettre l'accès depuis Windows WSL
    os.environ['ALLOWED_HOSTS'] = 'localhost,127.0.0.1,localhost:8001'
    os.environ['CORS_ALLOWED_ORIGINS'] = 'http://localhost,http://localhost:3000,http://localhost:8001'

def main():
    """Point d'entrée principal"""
    logger.info("🚀 Test de production simple avec middleware de sécurité")
    
    # Configuration de l'environnement
    setup_environment()
    
    try:
        # Import de l'application de production
        from app.main_production import app
        
        logger.info("✅ Application sécurisée chargée avec succès")
        
        # Configuration uvicorn pour la production
        uvicorn_config = {
            "app": app,
            "host": "0.0.0.0",
            "port": 8001,
            "log_level": "info",
            "access_log": True,
            "server_header": False,
            "date_header": True,
        }
        
        logger.info("🌐 Démarrage du serveur sécurisé sur http://0.0.0.0:8001")
        logger.info("🔒 Middleware de sécurité activé")
        logger.info("📚 Documentation DÉSACTIVÉE en production")
        logger.info("💚 Health check disponible sur: http://localhost:8001/health")
        
        # Démarrer le serveur
        uvicorn.run(**uvicorn_config)
        
    except KeyboardInterrupt:
        logger.info("⏹️ Arrêt demandé par l'utilisateur")
    except Exception as e:
        logger.error(f"❌ Erreur lors du démarrage: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()