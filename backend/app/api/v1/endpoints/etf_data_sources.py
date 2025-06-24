"""
Endpoints pour le statut et la gestion des sources de données ETF
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import asyncio
import logging

from app.core.database import get_db
from app.models.etf import MarketData
from app.services.etf_scraping_service import get_etf_scraping_service, ETFScrapingService
from app.services.historical_data_service import get_historical_data_service, HistoricalDataService
from app.services.multi_source_etf_data import MultiSourceETFDataService

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/status")
async def get_data_sources_status():
    """
    Retourne le statut de toutes les sources de données ETF
    """
    try:
        # Tester chaque source individuellement
        status = {
            "last_updated": datetime.now().isoformat(),
            "sources": {
                "scraping": {
                    "name": "Web Scraping",
                    "status": "unknown",
                    "description": "Scraping temps réel depuis Investing.com, Yahoo Finance, etc.",
                    "last_success": None,
                    "error_count": 0,
                    "confidence": 0.0
                },
                "yahoo_finance": {
                    "name": "Yahoo Finance API",
                    "status": "unknown", 
                    "description": "API officielle Yahoo Finance",
                    "last_success": None,
                    "error_count": 0,
                    "confidence": 0.0
                },
                "alpha_vantage": {
                    "name": "Alpha Vantage",
                    "status": "unknown",
                    "description": "API Alpha Vantage pour données financières",
                    "last_success": None,
                    "error_count": 0,
                    "confidence": 0.0
                },
                "database": {
                    "name": "Base de données",
                    "status": "unknown",
                    "description": "Données en cache PostgreSQL",
                    "last_success": None,
                    "error_count": 0,
                    "confidence": 0.0
                }
            },
            "overall_status": "checking",
            "data_freshness": "unknown",
            "total_etfs_tracked": 0
        }
        
        # Test de la base de données
        try:
            from app.core.database import SessionLocal
            db = SessionLocal()
            
            # Compter les ETFs avec des données récentes (dernières 24h)
            recent_cutoff = datetime.now() - timedelta(hours=24)
            recent_count = db.query(MarketData).filter(
                MarketData.time >= recent_cutoff
            ).count()
            
            total_etfs = db.query(MarketData.etf_isin).distinct().count()
            
            status["sources"]["database"]["status"] = "operational"
            status["sources"]["database"]["last_success"] = datetime.now().isoformat()
            status["sources"]["database"]["confidence"] = 1.0 if recent_count > 0 else 0.3
            status["total_etfs_tracked"] = total_etfs
            
            if recent_count > 0:
                status["data_freshness"] = f"{recent_count} ETFs avec données récentes"
            else:
                status["data_freshness"] = "Données non récentes"
                
            db.close()
            
        except Exception as e:
            logger.error(f"Erreur test database: {e}")
            status["sources"]["database"]["status"] = "error"
            status["sources"]["database"]["error_count"] = 1
        
        # Test du scraping (rapide)
        try:
            scraping_service = get_etf_scraping_service()
            
            # Test simple avec un ETF populaire
            test_data = await scraping_service.scrape_etf_data("IE00B5BMR087")  # CSPX
            
            if test_data and test_data.current_price > 0:
                status["sources"]["scraping"]["status"] = "operational"
                status["sources"]["scraping"]["last_success"] = datetime.now().isoformat()
                status["sources"]["scraping"]["confidence"] = test_data.confidence_score
            else:
                status["sources"]["scraping"]["status"] = "degraded"
                status["sources"]["scraping"]["error_count"] = 1
                status["sources"]["scraping"]["confidence"] = 0.2
                
        except Exception as e:
            logger.error(f"Erreur test scraping: {e}")
            status["sources"]["scraping"]["status"] = "error"
            status["sources"]["scraping"]["error_count"] = 1
        
        # Test Yahoo Finance
        try:
            import yfinance as yf
            ticker = yf.Ticker("AAPL")  # Test simple
            info = ticker.fast_info
            
            if hasattr(info, 'last_price') and info.last_price > 0:
                status["sources"]["yahoo_finance"]["status"] = "operational"
                status["sources"]["yahoo_finance"]["last_success"] = datetime.now().isoformat()
                status["sources"]["yahoo_finance"]["confidence"] = 0.8
            else:
                status["sources"]["yahoo_finance"]["status"] = "degraded"
                status["sources"]["yahoo_finance"]["confidence"] = 0.3
                
        except Exception as e:
            logger.error(f"Erreur test Yahoo Finance: {e}")
            status["sources"]["yahoo_finance"]["status"] = "error"
            status["sources"]["yahoo_finance"]["error_count"] = 1
        
        # Test Alpha Vantage (si configuré)
        try:
            from app.core.config import settings
            if hasattr(settings, 'ALPHA_VANTAGE_API_KEY') and settings.ALPHA_VANTAGE_API_KEY != "demo":
                # Test simple de l'API
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=AAPL&apikey={settings.ALPHA_VANTAGE_API_KEY}"
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            if "Global Quote" in data:
                                status["sources"]["alpha_vantage"]["status"] = "operational"
                                status["sources"]["alpha_vantage"]["last_success"] = datetime.now().isoformat()
                                status["sources"]["alpha_vantage"]["confidence"] = 0.9
                            else:
                                status["sources"]["alpha_vantage"]["status"] = "degraded"
                                status["sources"]["alpha_vantage"]["confidence"] = 0.4
                        else:
                            status["sources"]["alpha_vantage"]["status"] = "error"
                            status["sources"]["alpha_vantage"]["error_count"] = 1
            else:
                status["sources"]["alpha_vantage"]["status"] = "not_configured"
                status["sources"]["alpha_vantage"]["confidence"] = 0.0
                
        except Exception as e:
            logger.error(f"Erreur test Alpha Vantage: {e}")
            status["sources"]["alpha_vantage"]["status"] = "error"
            status["sources"]["alpha_vantage"]["error_count"] = 1
        
        # Calculer le statut global
        operational_sources = sum(1 for source in status["sources"].values() 
                                 if source["status"] == "operational")
        total_sources = len([s for s in status["sources"].values() 
                           if s["status"] != "not_configured"])
        
        if operational_sources >= total_sources * 0.7:  # 70% des sources fonctionnent
            status["overall_status"] = "operational"
        elif operational_sources >= total_sources * 0.3:  # 30% des sources fonctionnent
            status["overall_status"] = "degraded"
        else:
            status["overall_status"] = "critical"
        
        return status
        
    except Exception as e:
        logger.error(f"Erreur récupération statut sources: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur statut sources: {str(e)}")

@router.post("/refresh")
async def refresh_all_data():
    """
    Lance un rafraîchissement complet de toutes les données ETF
    """
    try:
        logger.info("Début rafraîchissement complet des données ETF")
        
        results = {
            "started_at": datetime.now().isoformat(),
            "scraping_results": None,
            "historical_results": None,
            "status": "in_progress"
        }
        
        # Rafraîchissement des données temps réel via scraping
        try:
            scraping_service = get_etf_scraping_service()
            
            # ETFs prioritaires européens
            priority_isins = [
                "IE00B5BMR087",  # CSPX
                "IE00B4L5Y983",  # IWDA
                "IE00BK5BQT80",  # VWRL
                "IE00B3XXRP09",  # VUSA
                "IE00B4L5YC18",  # IEMA
                "IE00B1YZSC51",  # IEUR
            ]
            
            scraped_data = await scraping_service.scrape_multiple_etfs(priority_isins)
            
            results["scraping_results"] = {
                "attempted": len(priority_isins),
                "successful": len(scraped_data),
                "etfs": [
                    {
                        "isin": data.isin,
                        "name": data.name,
                        "price": data.current_price,
                        "currency": data.currency,
                        "source": data.source
                    } for data in scraped_data
                ]
            }
            
        except Exception as e:
            logger.error(f"Erreur rafraîchissement scraping: {e}")
            results["scraping_results"] = {"error": str(e)}
        
        # Rafraîchissement des données historiques (période courte)
        try:
            historical_service = get_historical_data_service()
            
            # Mettre à jour seulement les données récentes (1 mois)
            historical_count = await historical_service.update_all_historical_data("1mo")
            
            results["historical_results"] = {
                "updated_etfs": historical_count,
                "period": "1mo"
            }
            
        except Exception as e:
            logger.error(f"Erreur rafraîchissement historique: {e}")
            results["historical_results"] = {"error": str(e)}
        
        results["completed_at"] = datetime.now().isoformat()
        results["status"] = "completed"
        
        logger.info(f"Rafraîchissement terminé: {results}")
        
        return results
        
    except Exception as e:
        logger.error(f"Erreur rafraîchissement général: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur rafraîchissement: {str(e)}")

@router.get("/health")
async def get_data_health():
    """
    Retourne un résumé simple de la santé des données
    """
    try:
        from app.core.database import SessionLocal
        db = SessionLocal()
        
        # Compter les données récentes par source
        recent_cutoff = datetime.now() - timedelta(hours=1)
        very_recent_cutoff = datetime.now() - timedelta(minutes=15)
        
        recent_count = db.query(MarketData).filter(
            MarketData.time >= recent_cutoff
        ).count()
        
        very_recent_count = db.query(MarketData).filter(
            MarketData.time >= very_recent_cutoff
        ).count()
        
        total_etfs = db.query(MarketData.etf_isin).distinct().count()
        
        health_status = "healthy" if very_recent_count > 0 else "stale" if recent_count > 0 else "critical"
        
        db.close()
        
        return {
            "status": health_status,
            "total_etfs": total_etfs,
            "recent_data_points": recent_count,
            "very_recent_data_points": very_recent_count,
            "last_check": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erreur health check: {e}")
        return {
            "status": "error",
            "error": str(e),
            "last_check": datetime.now().isoformat()
        }