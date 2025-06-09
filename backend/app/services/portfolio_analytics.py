"""
Service d'analytiques avancés pour les portefeuilles
Calculs de risque, performance, optimisation
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class PortfolioMetrics:
    """Métriques de performance d'un portefeuille"""
    total_value: float
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    beta: float
    alpha: float
    value_at_risk_95: float
    diversification_ratio: float

@dataclass
class RiskMetrics:
    """Métriques de risque détaillées"""
    portfolio_variance: float
    portfolio_volatility: float
    var_95: float
    var_99: float
    expected_shortfall_95: float
    maximum_drawdown: float
    concentration_risk: float
    correlation_risk: float

class PortfolioAnalytics:
    """Service d'analytiques de portefeuille"""
    
    def __init__(self):
        self.risk_free_rate = 0.02  # 2% taux sans risque
        
    async def calculate_portfolio_metrics(
        self,
        positions: Dict[str, float],  # {symbol: value}
        historical_returns: Dict[str, pd.Series],
        benchmark_returns: pd.Series = None
    ) -> PortfolioMetrics:
        """
        Calcule les métriques complètes d'un portefeuille
        
        Args:
            positions: Valeur de chaque position en euros
            historical_returns: Rendements historiques de chaque ETF
            benchmark_returns: Rendements du benchmark (optionnel)
        """
        try:
            # Calculer les poids du portefeuille
            total_value = sum(positions.values())
            weights = {symbol: value / total_value for symbol, value in positions.items()}
            
            # Créer le DataFrame des rendements
            returns_df = pd.DataFrame(historical_returns)
            returns_df = returns_df.dropna()
            
            if returns_df.empty:
                return self._empty_metrics(total_value)
            
            # Calculer les rendements du portefeuille
            portfolio_returns = self._calculate_portfolio_returns(returns_df, weights)
            
            # Métriques de base
            total_return = (1 + portfolio_returns).prod() - 1
            annualized_return = (1 + portfolio_returns.mean()) ** 252 - 1
            volatility = portfolio_returns.std() * np.sqrt(252)
            
            # Sharpe ratio
            excess_returns = portfolio_returns - self.risk_free_rate / 252
            sharpe_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(252) if excess_returns.std() > 0 else 0
            
            # Maximum drawdown
            cumulative_returns = (1 + portfolio_returns).cumprod()
            peak = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - peak) / peak
            max_drawdown = drawdown.min()
            
            # Beta et Alpha (si benchmark fourni)
            beta = 0
            alpha = 0
            if benchmark_returns is not None and len(benchmark_returns) > 0:
                # Aligner les données
                aligned_data = pd.DataFrame({
                    'portfolio': portfolio_returns,
                    'benchmark': benchmark_returns
                }).dropna()
                
                if len(aligned_data) > 10:
                    covariance = aligned_data['portfolio'].cov(aligned_data['benchmark'])
                    benchmark_var = aligned_data['benchmark'].var()
                    beta = covariance / benchmark_var if benchmark_var > 0 else 0
                    
                    portfolio_mean = aligned_data['portfolio'].mean() * 252
                    benchmark_mean = aligned_data['benchmark'].mean() * 252
                    alpha = portfolio_mean - (self.risk_free_rate + beta * (benchmark_mean - self.risk_free_rate))
            
            # Value at Risk (95%)
            var_95 = np.percentile(portfolio_returns, 5) * np.sqrt(252)
            
            # Ratio de diversification
            diversification_ratio = self._calculate_diversification_ratio(returns_df, weights)
            
            return PortfolioMetrics(
                total_value=total_value,
                total_return=total_return,
                annualized_return=annualized_return,
                volatility=volatility,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                beta=beta,
                alpha=alpha,
                value_at_risk_95=var_95,
                diversification_ratio=diversification_ratio
            )
            
        except Exception as e:
            logger.error(f"Erreur calcul métriques portfolio: {e}")
            return self._empty_metrics(total_value if 'total_value' in locals() else 0)
    
    def _calculate_portfolio_returns(self, returns_df: pd.DataFrame, weights: Dict[str, float]) -> pd.Series:
        """Calcule les rendements du portefeuille"""
        portfolio_returns = pd.Series(0, index=returns_df.index)
        
        for symbol, weight in weights.items():
            if symbol in returns_df.columns:
                portfolio_returns += returns_df[symbol] * weight
        
        return portfolio_returns
    
    def _calculate_diversification_ratio(self, returns_df: pd.DataFrame, weights: Dict[str, float]) -> float:
        """
        Calcule le ratio de diversification
        Ratio = Volatilité pondérée des actifs / Volatilité du portefeuille
        """
        try:
            # Volatilités individuelles
            individual_vols = returns_df.std() * np.sqrt(252)
            
            # Volatilité pondérée
            weighted_vol = sum(weights.get(symbol, 0) * vol for symbol, vol in individual_vols.items())
            
            # Volatilité du portefeuille
            portfolio_returns = self._calculate_portfolio_returns(returns_df, weights)
            portfolio_vol = portfolio_returns.std() * np.sqrt(252)
            
            if portfolio_vol > 0:
                return weighted_vol / portfolio_vol
            else:
                return 1.0
                
        except Exception:
            return 1.0
    
    def _empty_metrics(self, total_value: float) -> PortfolioMetrics:
        """Retourne des métriques vides en cas d'erreur"""
        return PortfolioMetrics(
            total_value=total_value,
            total_return=0,
            annualized_return=0,
            volatility=0,
            sharpe_ratio=0,
            max_drawdown=0,
            beta=0,
            alpha=0,
            value_at_risk_95=0,
            diversification_ratio=1
        )
    
    async def calculate_risk_metrics(
        self,
        positions: Dict[str, float],
        historical_returns: Dict[str, pd.Series]
    ) -> RiskMetrics:
        """Calcule les métriques de risque détaillées"""
        try:
            total_value = sum(positions.values())
            weights = {symbol: value / total_value for symbol, value in positions.items()}
            
            returns_df = pd.DataFrame(historical_returns).dropna()
            portfolio_returns = self._calculate_portfolio_returns(returns_df, weights)
            
            # Variance et volatilité du portefeuille
            portfolio_variance = portfolio_returns.var() * 252
            portfolio_volatility = portfolio_returns.std() * np.sqrt(252)
            
            # Value at Risk
            var_95 = np.percentile(portfolio_returns, 5) * total_value
            var_99 = np.percentile(portfolio_returns, 1) * total_value
            
            # Expected Shortfall (Conditional VaR)
            worst_5_percent = portfolio_returns[portfolio_returns <= np.percentile(portfolio_returns, 5)]
            expected_shortfall_95 = worst_5_percent.mean() * total_value if len(worst_5_percent) > 0 else 0
            
            # Maximum Drawdown
            cumulative = (1 + portfolio_returns).cumprod()
            peak = cumulative.expanding().max()
            drawdown = (cumulative - peak) / peak
            maximum_drawdown = abs(drawdown.min())
            
            # Risque de concentration (HHI)
            concentration_risk = sum(w**2 for w in weights.values())
            
            # Risque de corrélation (corrélation moyenne)
            correlation_matrix = returns_df.corr()
            correlation_risk = correlation_matrix.values[np.triu_indices_from(correlation_matrix.values, k=1)].mean()
            
            return RiskMetrics(
                portfolio_variance=portfolio_variance,
                portfolio_volatility=portfolio_volatility,
                var_95=var_95,
                var_99=var_99,
                expected_shortfall_95=expected_shortfall_95,
                maximum_drawdown=maximum_drawdown,
                concentration_risk=concentration_risk,
                correlation_risk=correlation_risk
            )
            
        except Exception as e:
            logger.error(f"Erreur calcul métriques risque: {e}")
            return RiskMetrics(0, 0, 0, 0, 0, 0, 0, 0)
    
    async def suggest_rebalancing(
        self,
        current_positions: Dict[str, float],
        target_allocation: Dict[str, float],
        tolerance: float = 0.05
    ) -> Dict[str, Dict]:
        """
        Suggère un rééquilibrage du portefeuille
        
        Args:
            current_positions: Positions actuelles
            target_allocation: Allocation cible (en pourcentages)
            tolerance: Tolérance de dérive (5% par défaut)
        """
        try:
            total_value = sum(current_positions.values())
            current_allocation = {
                symbol: value / total_value 
                for symbol, value in current_positions.items()
            }
            
            rebalancing_needed = {}
            
            for symbol in set(list(current_allocation.keys()) + list(target_allocation.keys())):
                current_weight = current_allocation.get(symbol, 0)
                target_weight = target_allocation.get(symbol, 0)
                drift = abs(current_weight - target_weight)
                
                if drift > tolerance:
                    current_value = current_positions.get(symbol, 0)
                    target_value = target_weight * total_value
                    difference = target_value - current_value
                    
                    rebalancing_needed[symbol] = {
                        "current_weight": current_weight,
                        "target_weight": target_weight,
                        "drift": drift,
                        "current_value": current_value,
                        "target_value": target_value,
                        "action": "buy" if difference > 0 else "sell",
                        "amount": abs(difference)
                    }
            
            return {
                "rebalancing_needed": len(rebalancing_needed) > 0,
                "total_drift": sum(abs(current_allocation.get(s, 0) - target_allocation.get(s, 0)) 
                                 for s in set(list(current_allocation.keys()) + list(target_allocation.keys()))),
                "suggestions": rebalancing_needed
            }
            
        except Exception as e:
            logger.error(f"Erreur suggestion rééquilibrage: {e}")
            return {"rebalancing_needed": False, "total_drift": 0, "suggestions": {}}
    
    async def calculate_optimal_allocation(
        self,
        expected_returns: Dict[str, float],
        covariance_matrix: pd.DataFrame,
        risk_tolerance: str = "moderate"
    ) -> Dict[str, float]:
        """
        Calcule l'allocation optimale selon Markowitz
        
        Args:
            expected_returns: Rendements attendus pour chaque ETF
            covariance_matrix: Matrice de covariance
            risk_tolerance: Tolérance au risque (conservative, moderate, aggressive)
        """
        try:
            # Paramètres de risque selon le profil
            risk_params = {
                "conservative": 0.5,  # Favorise la réduction du risque
                "moderate": 1.0,      # Équilibre risque/rendement
                "aggressive": 2.0     # Favorise le rendement
            }
            
            risk_aversion = risk_params.get(risk_tolerance, 1.0)
            
            # Simplification: allocation équipondérée ajustée par le rendement et le risque
            symbols = list(expected_returns.keys())
            n_assets = len(symbols)
            
            if n_assets == 0:
                return {}
            
            # Score basé sur le ratio rendement/risque
            scores = {}
            for symbol in symbols:
                expected_return = expected_returns[symbol]
                variance = covariance_matrix.loc[symbol, symbol] if symbol in covariance_matrix.index else 0.1
                
                # Score ajusté par l'aversion au risque
                score = expected_return - (risk_aversion * variance / 2)
                scores[symbol] = max(score, 0.01)  # Score minimum
            
            # Normaliser pour obtenir des poids
            total_score = sum(scores.values())
            optimal_weights = {symbol: score / total_score for symbol, score in scores.items()}
            
            return optimal_weights
            
        except Exception as e:
            logger.error(f"Erreur calcul allocation optimale: {e}")
            # Retourner allocation équipondérée en cas d'erreur
            symbols = list(expected_returns.keys())
            if symbols:
                equal_weight = 1.0 / len(symbols)
                return {symbol: equal_weight for symbol in symbols}
            return {}