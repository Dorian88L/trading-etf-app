"""
Endpoints pour le scoring et l'évaluation des ETFs
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging
import pandas as pd

from app.services.real_market_data import get_real_market_data_service, RealMarketDataService
from app.services.etf_catalog import get_etf_catalog_service, ETFCatalogService
from app.services.technical_analysis import TechnicalAnalyzer
from app.services.signal_generator import get_signal_generator_service

logger = logging.getLogger(__name__)

router = APIRouter()

class ETFScoringService:
    """Service de scoring des ETFs basé sur des critères réels"""
    
    def __init__(self, market_service: RealMarketDataService, catalog_service: ETFCatalogService):
        self.market_service = market_service
        self.catalog_service = catalog_service
        self.analyzer = TechnicalAnalyzer()
    
    def calculate_etf_score(self, symbol: str) -> Optional[Dict]:
        """Calcule le score complet d'un ETF"""
        try:
            # Récupérer les données de marché
            etf_data = self.market_service.get_real_etf_data(symbol)
            if not etf_data:
                return None
            
            # Récupérer les données historiques pour l'analyse
            historical_data = self.market_service.get_historical_data(symbol, "3mo")
            if not historical_data or len(historical_data) < 20:
                return None
            
            # Convertir en DataFrame
            df = pd.DataFrame(historical_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
            # Calculer les scores
            technical_score = self._calculate_technical_score(df)
            fundamental_score = self._calculate_fundamental_score(symbol, etf_data)
            risk_score = self._calculate_risk_score(df, etf_data)
            momentum_score = self._calculate_momentum_score(df)
            liquidity_score = self._calculate_liquidity_score(df, etf_data)
            
            # Score final pondéré
            final_score = (
                technical_score * 0.25 +
                fundamental_score * 0.20 +
                risk_score * 0.20 +
                momentum_score * 0.20 +
                liquidity_score * 0.15
            )
            
            return {
                "symbol": symbol,
                "name": etf_data.name,
                "isin": etf_data.isin,
                "final_score": round(final_score, 2),
                "technical_score": round(technical_score, 2),
                "fundamental_score": round(fundamental_score, 2),
                "risk_score": round(risk_score, 2),
                "momentum_score": round(momentum_score, 2),
                "liquidity_score": round(liquidity_score, 2),
                "current_price": etf_data.current_price,
                "currency": etf_data.currency,
                "sector": etf_data.sector,
                "change_percent": etf_data.change_percent,
                "volume": etf_data.volume,
                "last_update": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur calcul score pour {symbol}: {e}")
            return None
    
    def _calculate_technical_score(self, df: pd.DataFrame) -> float:
        """Score basé sur l'analyse technique (0-100)"""
        try:
            technical_data = self.analyzer.analyze_etf(df)
            score = 50  # Score de base
            
            # RSI
            if technical_data.get('rsi'):
                rsi = technical_data['rsi']
                if 30 <= rsi <= 70:  # Zone neutre favorable
                    score += 15
                elif rsi < 30:  # Oversold (opportunité)
                    score += 10
                elif rsi > 70:  # Overbought (risque)
                    score -= 10
            
            # MACD
            if technical_data.get('macd') and technical_data.get('macd_signal'):
                if technical_data['macd'] > technical_data['macd_signal']:
                    score += 10  # Signal haussier
                else:
                    score -= 5
            
            # Tendance des moyennes mobiles
            if all(k in technical_data for k in ['sma_20', 'sma_50']):
                if technical_data['sma_20'] > technical_data['sma_50']:
                    score += 15  # Tendance haussière
                else:
                    score -= 10
            
            # Volatilité (ATR)
            if technical_data.get('atr'):
                current_price = df['close_price'].iloc[-1]
                volatility_ratio = technical_data['atr'] / current_price
                if volatility_ratio < 0.02:  # Faible volatilité
                    score += 10
                elif volatility_ratio > 0.05:  # Forte volatilité
                    score -= 15
            
            return max(0, min(100, score))
            
        except Exception:
            return 50
    
    def _calculate_fundamental_score(self, symbol: str, etf_data) -> float:
        """Score basé sur les fondamentaux de l'ETF (0-100)"""
        try:
            etf_info = self.catalog_service.get_etf_by_symbol(symbol)
            score = 50
            
            if etf_info:
                # TER (frais de gestion)
                if etf_info.ter <= 0.1:  # Très faibles frais
                    score += 20
                elif etf_info.ter <= 0.3:  # Frais modérés
                    score += 10
                elif etf_info.ter > 0.5:  # Frais élevés
                    score -= 15
                
                # AUM (taille du fonds)
                if etf_info.aum >= 10000000000:  # > 10B
                    score += 15
                elif etf_info.aum >= 1000000000:  # > 1B
                    score += 10
                elif etf_info.aum < 100000000:  # < 100M
                    score -= 10
                
                # Diversification par secteur
                if "Global" in etf_info.sector or "World" in etf_info.sector:
                    score += 10
                elif "Technology" in etf_info.sector:
                    score += 5  # Secteur porteur mais concentré
            
            # Performance récente
            if etf_data.change_percent > 0:
                score += min(10, etf_data.change_percent)  # Max 10 points
            else:
                score += max(-10, etf_data.change_percent)  # Max -10 points
            
            return max(0, min(100, score))
            
        except Exception:
            return 50
    
    def _calculate_risk_score(self, df: pd.DataFrame, etf_data) -> float:
        """Score de risque (0-100, plus haut = moins risqué)"""
        try:
            score = 50
            
            # Volatilité des prix
            returns = df['close_price'].pct_change().dropna()
            volatility = returns.std() * (252 ** 0.5)  # Volatilité annualisée
            
            if volatility < 0.15:  # Faible volatilité
                score += 20
            elif volatility < 0.25:  # Volatilité modérée
                score += 10
            elif volatility > 0.4:  # Forte volatilité
                score -= 20
            
            # Drawdown maximum
            cumulative_returns = (1 + returns).cumprod()
            rolling_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - rolling_max) / rolling_max
            max_drawdown = drawdown.min()
            
            if max_drawdown > -0.1:  # Faible drawdown
                score += 15
            elif max_drawdown < -0.3:  # Fort drawdown
                score -= 15
            
            # Consistance du volume
            volume_cv = df['volume'].std() / df['volume'].mean()
            if volume_cv < 0.5:  # Volume consistant
                score += 10
            elif volume_cv > 1.0:  # Volume erratique
                score -= 10
            
            return max(0, min(100, score))
            
        except Exception:
            return 50
    
    def _calculate_momentum_score(self, df: pd.DataFrame) -> float:
        """Score de momentum (0-100)"""
        try:
            score = 50
            
            # Performance sur différentes périodes
            current_price = df['close_price'].iloc[-1]
            
            # 1 mois
            if len(df) >= 20:
                month_ago_price = df['close_price'].iloc[-20]
                month_return = (current_price - month_ago_price) / month_ago_price
                score += min(20, max(-20, month_return * 100))
            
            # 3 mois
            if len(df) >= 60:
                quarter_ago_price = df['close_price'].iloc[-60]
                quarter_return = (current_price - quarter_ago_price) / quarter_ago_price
                score += min(15, max(-15, quarter_return * 50))
            
            # Tendance récente (5 jours)
            if len(df) >= 5:
                recent_trend = df['close_price'].tail(5).pct_change().mean()
                score += min(15, max(-15, recent_trend * 1000))
            
            return max(0, min(100, score))
            
        except Exception:
            return 50
    
    def _calculate_liquidity_score(self, df: pd.DataFrame, etf_data) -> float:
        """Score de liquidité (0-100)"""
        try:
            score = 50
            
            # Volume moyen
            avg_volume = df['volume'].mean()
            if avg_volume > 1000000:  # Volume élevé
                score += 25
            elif avg_volume > 100000:  # Volume modéré
                score += 15
            elif avg_volume < 10000:  # Faible volume
                score -= 20
            
            # Régularité du trading
            zero_volume_days = (df['volume'] == 0).sum()
            total_days = len(df)
            
            if zero_volume_days == 0:
                score += 15
            elif zero_volume_days / total_days > 0.1:  # Plus de 10% de jours sans volume
                score -= 20
            
            # Spread estimé (via volatilité intraday)
            if len(df) > 1:
                intraday_volatility = ((df['high_price'] - df['low_price']) / df['close_price']).mean()
                if intraday_volatility < 0.01:  # Spread serré
                    score += 10
                elif intraday_volatility > 0.03:  # Spread large
                    score -= 10
            
            return max(0, min(100, score))
            
        except Exception:
            return 50

@router.get("/etf/{symbol}/score")
async def get_etf_score(
    symbol: str,
    market_service: RealMarketDataService = Depends(get_real_market_data_service),
    catalog_service: ETFCatalogService = Depends(get_etf_catalog_service)
):
    """
    Récupère le score complet d'un ETF
    """
    try:
        scoring_service = ETFScoringService(market_service, catalog_service)
        score_data = scoring_service.calculate_etf_score(symbol)
        
        if not score_data:
            raise HTTPException(
                status_code=404,
                detail=f"Impossible de calculer le score pour {symbol}"
            )
        
        return score_data
        
    except Exception as e:
        logger.error(f"Erreur scoring ETF {symbol}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du calcul du score: {str(e)}"
        )

@router.get("/etfs/scores")
async def get_etfs_scores(
    limit: int = Query(20, description="Number of top ETFs to return"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    market_service: RealMarketDataService = Depends(get_real_market_data_service),
    catalog_service: ETFCatalogService = Depends(get_etf_catalog_service)
):
    """
    Récupère les scores de tous les ETFs disponibles
    """
    try:
        scoring_service = ETFScoringService(market_service, catalog_service)
        
        # Récupérer la liste des ETFs du service de marché (symboles fonctionnels)
        available_etfs = list(market_service.EUROPEAN_ETFS.keys())
        
        # Calculer les scores
        scored_etfs = []
        for symbol in available_etfs:
            score_data = scoring_service.calculate_etf_score(symbol)
            if score_data:
                # Filtrer par secteur si demandé
                if not sector or sector.lower() in score_data.get('sector', '').lower():
                    scored_etfs.append(score_data)
        
        # Trier par score décroissant
        scored_etfs.sort(key=lambda x: x['final_score'], reverse=True)
        
        # Limiter le nombre de résultats
        scored_etfs = scored_etfs[:limit]
        
        return {
            "total_etfs_analyzed": len(scored_etfs),
            "sector_filter": sector,
            "top_etfs": scored_etfs,
            "last_update": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erreur scoring ETFs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du calcul des scores: {str(e)}"
        )

@router.get("/sectors/analysis")
async def get_sectors_analysis(
    market_service: RealMarketDataService = Depends(get_real_market_data_service),
    catalog_service: ETFCatalogService = Depends(get_etf_catalog_service)
):
    """
    Analyse des performances par secteur
    """
    try:
        scoring_service = ETFScoringService(market_service, catalog_service)
        
        # Grouper les ETFs par secteur
        sector_etfs = {}
        for symbol, etf_info in market_service.EUROPEAN_ETFS.items():
            sector = etf_info['sector']
            if sector not in sector_etfs:
                sector_etfs[sector] = []
            sector_etfs[sector].append(symbol)
        
        sector_analysis = []
        
        for sector, symbols in sector_etfs.items():
            # Calculer les statistiques du secteur
            sector_scores = []
            sector_changes = []
            
            for symbol in symbols[:5]:  # Limiter à 5 ETFs par secteur
                score_data = scoring_service.calculate_etf_score(symbol)
                if score_data:
                    sector_scores.append(score_data['final_score'])
                    sector_changes.append(score_data['change_percent'])
            
            if sector_scores:
                avg_score = sum(sector_scores) / len(sector_scores)
                avg_change = sum(sector_changes) / len(sector_changes)
                
                sector_analysis.append({
                    "sector": sector,
                    "average_score": round(avg_score, 2),
                    "average_change_percent": round(avg_change, 2),
                    "etfs_count": len(sector_scores),
                    "performance_trend": "up" if avg_change > 0 else "down" if avg_change < 0 else "neutral"
                })
        
        # Trier par score moyen décroissant
        sector_analysis.sort(key=lambda x: x['average_score'], reverse=True)
        
        return {
            "sectors_analyzed": len(sector_analysis),
            "sector_performance": sector_analysis,
            "last_update": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erreur analyse secteurs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'analyse des secteurs: {str(e)}"
        )