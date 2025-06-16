"""
Endpoints pour les données historiques des ETFs
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

from app.services.real_market_data import get_real_market_data_service, RealMarketDataService
from app.services.smart_market_data import get_smart_market_data_service, SmartMarketDataService
from app.services.technical_analysis import TechnicalAnalyzer
from app.services.signal_generator import get_signal_generator_service, TradingSignalGenerator
from app.core.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/etf/{symbol}/historical")
async def get_etf_historical_data(
    symbol: str,
    period: str = Query("1mo", description="Period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)"),
    include_indicators: bool = Query(False, description="Include technical indicators"),
    smart_service: SmartMarketDataService = Depends(get_smart_market_data_service),
    db: Session = Depends(get_db)
):
    """
    Récupère les données historiques d'un ETF avec cache intelligent et sauvegarde automatique
    """
    try:
        # Utiliser le service intelligent qui vérifie d'abord en base
        historical_data = await smart_service.get_historical_data_smart(symbol, period, db)
        
        if not historical_data:
            raise HTTPException(
                status_code=404,
                detail=f"Aucune donnée historique trouvée pour {symbol}"
            )
        
        response = {
            "symbol": symbol,
            "period": period,
            "data_points": len(historical_data),
            "historical_data": historical_data,
            "last_update": datetime.now().isoformat()
        }
        
        # Ajouter les indicateurs techniques si demandés
        if include_indicators and len(historical_data) >= 20:
            try:
                import pandas as pd
                
                # Convertir en DataFrame pour l'analyse technique
                df = pd.DataFrame(historical_data)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
                
                # Calculer les indicateurs techniques
                analyzer = TechnicalAnalyzer()
                technical_data = analyzer.analyze_etf(df)
                
                response["technical_indicators"] = technical_data
                
            except Exception as e:
                logger.warning(f"Erreur calcul indicateurs pour {symbol}: {e}")
                response["technical_indicators"] = None
        
        return response
        
    except Exception as e:
        logger.error(f"Erreur récupération données historiques {symbol}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des données: {str(e)}"
        )

@router.get("/etf/{symbol}/technical-analysis")
async def get_etf_technical_analysis(
    symbol: str,
    period: str = Query("1mo", description="Period for analysis"),
    market_service: RealMarketDataService = Depends(get_real_market_data_service)
):
    """
    Récupère l'analyse technique complète d'un ETF
    """
    try:
        # Récupérer les données historiques
        historical_data = market_service.get_historical_data(symbol, period)
        
        if not historical_data or len(historical_data) < 20:
            raise HTTPException(
                status_code=404,
                detail=f"Données insuffisantes pour l'analyse technique de {symbol}"
            )
        
        import pandas as pd
        
        # Convertir en DataFrame
        df = pd.DataFrame(historical_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        
        # Analyse technique complète
        analyzer = TechnicalAnalyzer()
        technical_data = analyzer.analyze_etf(df)
        
        # Générer un signal de trading
        signal_generator = get_signal_generator_service()
        trading_signal = signal_generator.generate_signal(df, "", symbol)
        
        response = {
            "symbol": symbol,
            "period": period,
            "technical_indicators": technical_data,
            "trading_signal": trading_signal.__dict__ if trading_signal else None,
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Erreur analyse technique {symbol}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'analyse technique: {str(e)}"
        )

@router.get("/etf/{symbol}/price-history")
async def get_etf_price_history(
    symbol: str,
    days: int = Query(30, description="Number of days"),
    market_service: RealMarketDataService = Depends(get_real_market_data_service)
):
    """
    Récupère l'historique des prix simplifié pour les graphiques
    """
    try:
        # Calculer la période basée sur le nombre de jours
        if days <= 5:
            period = "5d"
        elif days <= 30:
            period = "1mo"
        elif days <= 90:
            period = "3mo"
        elif days <= 365:
            period = "1y"
        else:
            period = "2y"
        
        historical_data = market_service.get_historical_data(symbol, period)
        
        if not historical_data:
            raise HTTPException(
                status_code=404,
                detail=f"Aucune donnée trouvée pour {symbol}"
            )
        
        # Filtrer pour le nombre de jours demandé
        if len(historical_data) > days:
            historical_data = historical_data[-days:]
        
        # Format simplifié pour les graphiques
        chart_data = [
            {
                "date": point["timestamp"],
                "price": point["close_price"],
                "volume": point["volume"]
            }
            for point in historical_data
        ]
        
        return {
            "symbol": symbol,
            "days": len(chart_data),
            "chart_data": chart_data
        }
        
    except Exception as e:
        logger.error(f"Erreur historique prix {symbol}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération: {str(e)}"
        )