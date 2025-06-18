"""
Test du service de scraping ETF
"""

import sys
import os
sys.path.append('/app')

import asyncio
import logging
from app.services.etf_scraping_service import ETFScrapingService

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_scraping():
    """Test du scraping pour l'ETF iShares Core S&P 500"""
    
    service = ETFScrapingService()
    
    try:
        # Test avec l'ISIN de l'ETF iShares Core S&P 500
        test_isin = "IE00B5BMR087"
        
        logger.info(f"🧪 Test du scraping pour {test_isin}...")
        
        # Test JustETF
        logger.info("📊 Test JustETF...")
        justetf_data = await service.scrape_justetf_etf(test_isin)
        if justetf_data:
            logger.info(f"✅ JustETF: {justetf_data.name}")
            logger.info(f"   Prix: {justetf_data.current_price} {justetf_data.currency}")
            logger.info(f"   Variation: {justetf_data.change} ({justetf_data.change_percent}%)")
        else:
            logger.warning("❌ JustETF: Pas de données")
        
        # Test Boursorama
        logger.info("📊 Test Boursorama...")
        boursorama_data = await service.scrape_boursorama_etf(test_isin)
        if boursorama_data:
            logger.info(f"✅ Boursorama: {boursorama_data.name}")
            logger.info(f"   Prix: {boursorama_data.current_price} {boursorama_data.currency}")
            logger.info(f"   Variation: {boursorama_data.change} ({boursorama_data.change_percent}%)")
        else:
            logger.warning("❌ Boursorama: Pas de données")
        
        # Test du scraping global
        logger.info("📊 Test scraping global...")
        data = await service.scrape_etf_data(test_isin)
        if data:
            logger.info(f"🎯 RÉSULTAT FINAL:")
            logger.info(f"   Nom: {data.name}")
            logger.info(f"   Prix: {data.current_price} {data.currency}")
            logger.info(f"   Variation: {data.change} ({data.change_percent}%)")
            logger.info(f"   Source: {data.source}")
            logger.info(f"   Mise à jour: {data.last_update}")
            
            # Comparer avec le prix attendu (EUR 555,51)
            expected_price = 555.51
            if abs(data.current_price - expected_price) < 10:
                logger.info(f"✅ Le prix est proche de l'attendu ({expected_price} EUR)")
            else:
                logger.warning(f"⚠️ Le prix diffère de l'attendu ({expected_price} EUR)")
        else:
            logger.error("❌ Aucune donnée récupérée")
        
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        
    finally:
        await service.close()

if __name__ == "__main__":
    asyncio.run(test_scraping())