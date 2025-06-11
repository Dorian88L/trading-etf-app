#!/usr/bin/env python3
"""
Test de production adapté pour WSL/Windows
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
    """Configure l'environnement pour WSL"""
    os.environ['ENVIRONMENT'] = 'development'  # Utiliser dev config mais avec sécurité
    os.environ['DEBUG'] = 'false'
    os.environ['JWT_SECRET_KEY'] = 'b4d75d113f67a3857febe2495b1ec4c9c9d56441c18946cedf833707269f814d'
    os.environ['DATABASE_URL'] = 'postgresql://trading_user:trading_password@localhost:5433/trading_etf'
    os.environ['REDIS_URL'] = 'redis://localhost:6380'

def main():
    """Point d'entrée principal"""
    logger.info("🚀 Test de production WSL-compatible")
    
    # Configuration de l'environnement
    setup_environment()
    
    try:
        # Import de l'application standard avec middleware ajouté
        from app.main import app
        from app.core.security_middleware import SecurityMiddleware
        from app.core.config import settings
        
        # Créer une config compatible WSL
        class WSLSettings:
            ALLOWED_HOSTS = ["localhost", "127.0.0.1", "localhost:8001"]
            RATE_LIMIT_REQUESTS = 100
            RATE_LIMIT_WINDOW = 60
            SECURE_HSTS_SECONDS = 31536000
        
        wsl_settings = WSLSettings()
        
        # Ajouter le middleware de sécurité
        app.add_middleware(SecurityMiddleware, settings=wsl_settings)
        
        logger.info("✅ Application avec middleware de sécurité WSL chargée")
        
        # Configuration uvicorn
        uvicorn_config = {
            "app": app,
            "host": "0.0.0.0",
            "port": 8001,
            "log_level": "info",
            "access_log": True,
            "server_header": False,
            "date_header": True,
        }
        
        logger.info("🌐 Serveur démarré sur http://0.0.0.0:8001")
        logger.info("🔒 Middleware de sécurité activé pour WSL")
        logger.info("💚 Health check: http://localhost:8001/health")
        logger.info("📚 Documentation: http://localhost:8001/docs")
        
        # Démarrer le serveur
        uvicorn.run(**uvicorn_config)
        
    except KeyboardInterrupt:
        logger.info("⏹️ Arrêt demandé")
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()