"""
Service de scoring et ranking avancé des ETF
Combine analyse technique, fondamentale et de risque
"""
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.etf import ETF
from app.services.technical_analysis import TechnicalAnalyzer
from app.services.market_data import MarketDataProvider

logger = logging.getLogger(__name__)

class ETFScoringService:
    def __init__(self):
        self.technical_service = TechnicalAnalysisService()
        self.market_service = MarketDataService()
        
        # Pondérations pour le score final
        self.weights = {
            'technical': 0.4,      # 40% analyse technique
            'fundamental': 0.3,    # 30% analyse fondamentale
            'risk': 0.2,          # 20% analyse de risque
            'momentum': 0.1       # 10% momentum récent
        }
        
    async def calculate_etf_score(self, etf_isin: str, db: Session) -> Dict:
        """
        Calcule le score complet d'un ETF
        """
        try:
            # 1. Score technique (0-100)
            technical_score = await self._calculate_technical_score(etf_isin, db)
            
            # 2. Score fondamental (0-100)
            fundamental_score = await self._calculate_fundamental_score(etf_isin, db)
            
            # 3. Score de risque (0-100, où 100 = risque faible)
            risk_score = await self._calculate_risk_score(etf_isin, db)
            
            # 4. Score de momentum (0-100)
            momentum_score = await self._calculate_momentum_score(etf_isin, db)
            
            # Score final pondéré
            final_score = (
                technical_score * self.weights['technical'] +
                fundamental_score * self.weights['fundamental'] +
                risk_score * self.weights['risk'] +
                momentum_score * self.weights['momentum']
            )
            
            return {
                'etf_isin': etf_isin,
                'final_score': round(final_score, 2),
                'technical_score': round(technical_score, 2),
                'fundamental_score': round(fundamental_score, 2),
                'risk_score': round(risk_score, 2),
                'momentum_score': round(momentum_score, 2),
                'timestamp': datetime.utcnow(),
                'rating': self._get_rating(final_score),
                'confidence': self._calculate_confidence(technical_score, fundamental_score, risk_score)
            }
            
        except Exception as e:
            logger.error(f"Erreur calcul score ETF {etf_isin}: {e}")
            return None
    
    async def _calculate_technical_score(self, etf_isin: str, db: Session) -> float:
        """
        Score technique basé sur les indicateurs
        """
        try:
            # Récupération des données historiques (90 jours)
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=90)
            
            # Simulation des données (à remplacer par vrais données)
            prices = np.random.normal(100, 5, 90) + np.linspace(0, 10, 90)  # Tendance haussière
            volumes = np.random.normal(1000000, 200000, 90)
            
            df = pd.DataFrame({
                'price': prices,
                'volume': volumes,
                'date': pd.date_range(start_date, periods=90, freq='D')
            })
            
            score = 0
            max_score = 100
            
            # 1. Tendance des moyennes mobiles (25 points)
            sma_20 = df['price'].rolling(20).mean().iloc[-1]
            sma_50 = df['price'].rolling(50).mean().iloc[-1] if len(df) >= 50 else sma_20
            current_price = df['price'].iloc[-1]
            
            if current_price > sma_20 > sma_50:
                score += 25  # Tendance haussière forte
            elif current_price > sma_20:
                score += 15  # Tendance haussière modérée
            elif current_price > sma_50:
                score += 10  # Tendance neutre positive
            
            # 2. RSI (20 points)
            rsi = self._calculate_rsi(df['price'])
            if 30 <= rsi <= 70:
                score += 20  # Zone neutre = bon
            elif 20 <= rsi < 30 or 70 < rsi <= 80:
                score += 15  # Zones de retournement potentiel
            elif rsi < 20:
                score += 10  # Survente = opportunité
            
            # 3. Volume (15 points)
            avg_volume = df['volume'].rolling(20).mean().iloc[-1]
            recent_volume = df['volume'].iloc[-5:].mean()
            if recent_volume > avg_volume * 1.2:
                score += 15  # Volume en hausse
            elif recent_volume > avg_volume:
                score += 10
            
            # 4. Volatilité (20 points)
            volatility = df['price'].pct_change().std() * np.sqrt(252)
            if volatility < 0.15:
                score += 20  # Faible volatilité = bon
            elif volatility < 0.25:
                score += 15
            elif volatility < 0.35:
                score += 10
            
            # 5. Performance récente (20 points)
            perf_1w = (df['price'].iloc[-1] / df['price'].iloc[-5] - 1) * 100
            perf_1m = (df['price'].iloc[-1] / df['price'].iloc[-20] - 1) * 100
            
            if perf_1w > 2 and perf_1m > 5:
                score += 20  # Performance excellente
            elif perf_1w > 1 or perf_1m > 3:
                score += 15
            elif perf_1w > 0 or perf_1m > 0:
                score += 10
            
            return min(score, max_score)
            
        except Exception as e:
            logger.error(f"Erreur calcul score technique: {e}")
            return 50  # Score neutre en cas d'erreur
    
    async def _calculate_fundamental_score(self, etf_isin: str, db: Session) -> float:
        """
        Score fondamental basé sur les métriques ETF
        """
        try:
            # Récupération des données ETF
            etf = db.query(ETF).filter(ETF.isin == etf_isin).first()
            if not etf:
                return 50
            
            score = 0
            
            # 1. Frais de gestion (TER) - 30 points
            ter = getattr(etf, 'ter', None) or 0.5  # Défaut 0.5%
            if ter < 0.1:
                score += 30  # Très faibles frais
            elif ter < 0.2:
                score += 25
            elif ter < 0.5:
                score += 20
            elif ter < 1.0:
                score += 15
            else:
                score += 5
            
            # 2. Taille du fonds (AUM) - 25 points
            aum = getattr(etf, 'aum', None) or 100_000_000  # Défaut 100M
            if aum > 1_000_000_000:  # > 1B
                score += 25
            elif aum > 500_000_000:  # > 500M
                score += 20
            elif aum > 100_000_000:  # > 100M
                score += 15
            elif aum > 50_000_000:   # > 50M
                score += 10
            else:
                score += 5
            
            # 3. Liquidité (spread et volume) - 20 points
            # Simulation basée sur la taille du fonds
            if aum > 500_000_000:
                score += 20  # Grande liquidité
            elif aum > 100_000_000:
                score += 15
            else:
                score += 10
            
            # 4. Diversification - 15 points
            # Simulation basée sur le secteur
            sector = getattr(etf, 'sector', 'Other')
            if sector in ['Diversified', 'Broad Market']:
                score += 15  # Très diversifié
            elif sector in ['Technology', 'Healthcare']:
                score += 12  # Secteurs solides
            else:
                score += 8   # Spécialisé
            
            # 5. Tracking error - 10 points
            # Simulation : la plupart des ETF ont un bon tracking
            score += 8
            
            return min(score, 100)
            
        except Exception as e:
            logger.error(f"Erreur calcul score fondamental: {e}")
            return 50
    
    async def _calculate_risk_score(self, etf_isin: str, db: Session) -> float:
        """
        Score de risque (100 = risque faible)
        """
        try:
            # Simulation des métriques de risque
            volatility = np.random.uniform(0.1, 0.4)  # Volatilité annualisée
            max_drawdown = np.random.uniform(0.05, 0.25)  # Drawdown max
            beta = np.random.uniform(0.8, 1.2)  # Beta vs marché
            
            score = 0
            
            # 1. Volatilité (40 points)
            if volatility < 0.15:
                score += 40  # Faible volatilité
            elif volatility < 0.20:
                score += 35
            elif volatility < 0.25:
                score += 25
            elif volatility < 0.30:
                score += 15
            else:
                score += 5
            
            # 2. Drawdown maximum (30 points)
            if max_drawdown < 0.1:
                score += 30  # Faible drawdown
            elif max_drawdown < 0.15:
                score += 25
            elif max_drawdown < 0.20:
                score += 20
            else:
                score += 10
            
            # 3. Beta (20 points)
            beta_score = max(0, 20 - abs(beta - 1) * 40)
            score += beta_score
            
            # 4. Corrélation avec d'autres actifs (10 points)
            correlation_diversification = np.random.uniform(0.3, 0.8)
            if correlation_diversification < 0.5:
                score += 10  # Bonne diversification
            elif correlation_diversification < 0.7:
                score += 7
            else:
                score += 3
            
            return min(score, 100)
            
        except Exception as e:
            logger.error(f"Erreur calcul score de risque: {e}")
            return 50
    
    async def _calculate_momentum_score(self, etf_isin: str, db: Session) -> float:
        """
        Score de momentum récent
        """
        try:
            # Simulation des performances récentes
            perf_1d = np.random.normal(0, 1)    # Performance 1 jour
            perf_1w = np.random.normal(0, 2)    # Performance 1 semaine
            perf_1m = np.random.normal(0, 4)    # Performance 1 mois
            
            score = 0
            
            # Performance 1 jour (20 points)
            if perf_1d > 1:
                score += 20
            elif perf_1d > 0.5:
                score += 15
            elif perf_1d > 0:
                score += 10
            elif perf_1d > -0.5:
                score += 5
            
            # Performance 1 semaine (30 points)
            if perf_1w > 3:
                score += 30
            elif perf_1w > 1:
                score += 25
            elif perf_1w > 0:
                score += 15
            elif perf_1w > -1:
                score += 10
            
            # Performance 1 mois (50 points)
            if perf_1m > 5:
                score += 50
            elif perf_1m > 3:
                score += 40
            elif perf_1m > 1:
                score += 30
            elif perf_1m > 0:
                score += 20
            elif perf_1m > -2:
                score += 10
            
            return min(score, 100)
            
        except Exception as e:
            logger.error(f"Erreur calcul score momentum: {e}")
            return 50
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """
        Calcul du RSI
        """
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
        except:
            return 50
    
    def _get_rating(self, score: float) -> str:
        """
        Conversion du score en rating
        """
        if score >= 85:
            return 'A+'
        elif score >= 75:
            return 'A'
        elif score >= 65:
            return 'B+'
        elif score >= 55:
            return 'B'
        elif score >= 45:
            return 'B-'
        elif score >= 35:
            return 'C'
        else:
            return 'D'
    
    def _calculate_confidence(self, tech: float, fund: float, risk: float) -> float:
        """
        Calcul de la confiance basée sur la cohérence des scores
        """
        scores = [tech, fund, risk]
        std = np.std(scores)
        mean_score = np.mean(scores)
        
        # Confiance élevée si les scores sont cohérents et élevés
        consistency = max(0, 100 - std * 2)  # Pénalité pour incohérence
        quality = mean_score  # Bonus pour scores élevés
        
        confidence = (consistency * 0.6 + quality * 0.4)
        return min(confidence, 100)
    
    async def rank_etfs(self, etf_isins: List[str], db: Session) -> List[Dict]:
        """
        Classe une liste d'ETF par score
        """
        try:
            scored_etfs = []
            
            for isin in etf_isins:
                score_data = await self.calculate_etf_score(isin, db)
                if score_data:
                    scored_etfs.append(score_data)
            
            # Tri par score décroissant
            scored_etfs.sort(key=lambda x: x['final_score'], reverse=True)
            
            # Ajout du rang
            for i, etf in enumerate(scored_etfs):
                etf['rank'] = i + 1
                etf['percentile'] = round((len(scored_etfs) - i) / len(scored_etfs) * 100, 1)
            
            return scored_etfs
            
        except Exception as e:
            logger.error(f"Erreur ranking ETF: {e}")
            return []
    
    async def get_top_etfs(self, limit: int = 10, sector: Optional[str] = None, 
                          db: Session = None) -> List[Dict]:
        """
        Récupère les meilleurs ETF par score
        """
        try:
            # Récupération de tous les ETF (ou filtrés par secteur)
            query = db.query(ETF)
            if sector:
                query = query.filter(ETF.sector == sector)
            
            etfs = query.limit(50).all()  # Limite pour performance
            etf_isins = [etf.isin for etf in etfs]
            
            # Calcul et classement
            ranked_etfs = await self.rank_etfs(etf_isins, db)
            
            return ranked_etfs[:limit]
            
        except Exception as e:
            logger.error(f"Erreur récupération top ETF: {e}")
            return []