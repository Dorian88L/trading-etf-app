import React, { useState, useEffect } from 'react';
import {
  ExclamationTriangleIcon,
  ShieldCheckIcon,
  CalculatorIcon,
  ChartPieIcon,
  BanknotesIcon,
  ScaleIcon
} from '@heroicons/react/24/outline';

interface Position {
  etf_isin: string;
  etf_name: string;
  quantity: number;
  entry_price: number;
  current_price: number;
  sector: string;
  weight: number;
}

interface RiskMetrics {
  portfolioValue: number;
  totalRisk: number;
  maxDrawdown: number;
  sharpeRatio: number;
  beta: number;
  volatility: number;
  var_95: number; // Value at Risk 95%
}

interface RiskManagementProps {
  positions: Position[];
  availableCash: number;
  riskTolerance: 'conservative' | 'moderate' | 'aggressive';
}

const RiskManagement: React.FC<RiskManagementProps> = ({
  positions,
  availableCash,
  riskTolerance
}) => {
  const [targetPosition, setTargetPosition] = useState({
    etf_isin: '',
    investment_amount: 0,
    risk_percentage: 2
  });
  
  // Charger les limites de risque depuis l'API ou les préférences utilisateur
  const [riskLimits, setRiskLimits] = useState({
    maxPositionSize: 20, // % du portefeuille - à charger depuis l'API
    maxSectorExposure: 30, // à charger depuis l'API
    maxSingleRisk: 2, // à charger depuis l'API
    stopLossThreshold: 5 // à charger depuis l'API
  });

  // TODO: Charger les limites de risque depuis l'API
  useEffect(() => {
    // const fetchRiskLimits = async () => {
    //   try {
    //     const response = await fetch('/api/v1/portfolio/risk-limits');
    //     if (response.ok) {
    //       const data = await response.json();
    //       setRiskLimits(data);
    //     }
    //   } catch (error) {
    //     console.error('Erreur lors du chargement des limites de risque:', error);
    //   }
    // };
    // fetchRiskLimits();
  }, []);

  // Calcul des métriques de risque
  const calculateRiskMetrics = (): RiskMetrics => {
    const portfolioValue = positions.reduce((sum, pos) => 
      sum + (pos.quantity * pos.current_price), 0
    ) + availableCash;

    // Calcul simplifié - dans un vrai système, utiliser des données historiques
    const totalRisk = positions.reduce((sum, pos) => {
      const positionValue = pos.quantity * pos.current_price;
      const positionWeight = positionValue / portfolioValue;
      const positionRisk = Math.abs((pos.current_price - pos.entry_price) / pos.entry_price) * positionWeight;
      return sum + positionRisk;
    }, 0);

    // TODO: Calculer ces métriques depuis les vraies données de marché
    return {
      portfolioValue,
      totalRisk: totalRisk * 100,
      maxDrawdown: 0, // À calculer depuis l'historique du portfolio
      sharpeRatio: 0, // À calculer depuis l'API
      beta: 0, // À calculer depuis l'API
      volatility: 0, // À calculer depuis l'API
      var_95: portfolioValue * 0.03 // VaR à calculer plus précisément
    };
  };

  const riskMetrics = calculateRiskMetrics();

  // Analyse de la diversification sectorielle
  const sectorExposure = positions.reduce((acc, pos) => {
    const value = pos.quantity * pos.current_price;
    acc[pos.sector] = (acc[pos.sector] || 0) + value;
    return acc;
  }, {} as Record<string, number>);

  const sectorPercentages = Object.entries(sectorExposure).map(([sector, value]) => ({
    sector,
    value,
    percentage: (value / riskMetrics.portfolioValue) * 100
  })).sort((a, b) => b.percentage - a.percentage);

  // Calcul de la taille de position recommandée
  const calculatePositionSize = (riskPercentage: number, stopLossPercentage: number) => {
    const riskAmount = riskMetrics.portfolioValue * (riskPercentage / 100);
    return riskAmount / (stopLossPercentage / 100);
  };

  // Validation des risques pour une nouvelle position
  const validateNewPosition = (etfIsin: string, amount: number) => {
    const warnings = [];
    const positionPercentage = (amount / riskMetrics.portfolioValue) * 100;
    
    if (positionPercentage > riskLimits.maxPositionSize) {
      warnings.push(`Position trop importante: ${positionPercentage.toFixed(1)}% > ${riskLimits.maxPositionSize}%`);
    }
    
    if (amount > availableCash) {
      warnings.push(`Liquidités insuffisantes: ${amount.toFixed(0)}€ > ${availableCash.toFixed(0)}€`);
    }

    // Vérifier l'exposition sectorielle (simplifié)
    const existingPosition = positions.find(p => p.etf_isin === etfIsin);
    if (existingPosition) {
      const newSectorExposure = sectorExposure[existingPosition.sector] + amount;
      const newSectorPercentage = (newSectorExposure / riskMetrics.portfolioValue) * 100;
      
      if (newSectorPercentage > riskLimits.maxSectorExposure) {
        warnings.push(`Exposition sectorielle excessive: ${newSectorPercentage.toFixed(1)}% > ${riskLimits.maxSectorExposure}%`);
      }
    }

    return warnings;
  };

  const getRiskLevel = (percentage: number) => {
    if (percentage < 15) return { label: 'Faible', color: 'text-green-600', bg: 'bg-green-100' };
    if (percentage < 25) return { label: 'Modéré', color: 'text-yellow-600', bg: 'bg-yellow-100' };
    return { label: 'Élevé', color: 'text-red-600', bg: 'bg-red-100' };
  };

  const portfolioRiskLevel = getRiskLevel(riskMetrics.totalRisk);

  const positionSizeRecommendation = calculatePositionSize(
    targetPosition.risk_percentage, 
    riskLimits.stopLossThreshold
  );

  const newPositionWarnings = validateNewPosition(
    targetPosition.etf_isin, 
    targetPosition.investment_amount
  );

  return (
    <div className="space-y-6">
      {/* En-tête */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center space-x-3 mb-4">
          <ShieldCheckIcon className="h-8 w-8 text-blue-600" />
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Gestion des Risques</h2>
            <p className="text-gray-600">Profil: {riskTolerance === 'conservative' ? 'Conservateur' : riskTolerance === 'moderate' ? 'Modéré' : 'Agressif'}</p>
          </div>
        </div>

        {/* Métriques principales */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">
              {riskMetrics.portfolioValue.toLocaleString('fr-FR')} €
            </div>
            <div className="text-sm text-gray-500">Valeur du portefeuille</div>
          </div>
          
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className={`text-2xl font-bold ${portfolioRiskLevel.color}`}>
              {riskMetrics.totalRisk.toFixed(1)}%
            </div>
            <div className="text-sm text-gray-500">Risque total</div>
          </div>
          
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">
              {riskMetrics.var_95.toLocaleString('fr-FR')} €
            </div>
            <div className="text-sm text-gray-500">VaR 95% (1 jour)</div>
          </div>
          
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">
              {riskMetrics.sharpeRatio.toFixed(2)}
            </div>
            <div className="text-sm text-gray-500">Ratio de Sharpe</div>
          </div>
        </div>
      </div>

      {/* Calculateur de position */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center space-x-2 mb-4">
          <CalculatorIcon className="h-6 w-6 text-green-600" />
          <h3 className="text-lg font-semibold text-gray-900">Calculateur de Position</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              ETF ISIN
            </label>
            <input
              type="text"
              value={targetPosition.etf_isin}
              onChange={(e) => setTargetPosition(prev => ({ ...prev, etf_isin: e.target.value }))}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="FR0010296061"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Montant d'investissement (€)
            </label>
            <input
              type="number"
              value={targetPosition.investment_amount}
              onChange={(e) => setTargetPosition(prev => ({ ...prev, investment_amount: Number(e.target.value) }))}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="10000"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Risque par position (%)
            </label>
            <input
              type="number"
              min="0.5"
              max="5"
              step="0.1"
              value={targetPosition.risk_percentage}
              onChange={(e) => setTargetPosition(prev => ({ ...prev, risk_percentage: Number(e.target.value) }))}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>

        {/* Recommandations */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
          <h4 className="font-medium text-blue-900 mb-2">Recommandations</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
            <div>
              <span className="text-blue-700">Taille de position recommandée:</span>
              <span className="font-semibold ml-1">
                {positionSizeRecommendation.toLocaleString('fr-FR')} €
              </span>
            </div>
            <div>
              <span className="text-blue-700">Stop-loss suggéré:</span>
              <span className="font-semibold ml-1">-{riskLimits.stopLossThreshold}%</span>
            </div>
            <div>
              <span className="text-blue-700">% du portefeuille:</span>
              <span className="font-semibold ml-1">
                {((targetPosition.investment_amount / riskMetrics.portfolioValue) * 100).toFixed(1)}%
              </span>
            </div>
            <div>
              <span className="text-blue-700">Risque estimé:</span>
              <span className="font-semibold ml-1">
                {((targetPosition.investment_amount * targetPosition.risk_percentage / 100) / riskMetrics.portfolioValue * 100).toFixed(2)}%
              </span>
            </div>
          </div>
        </div>

        {/* Alertes de validation */}
        {newPositionWarnings.length > 0 && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <ExclamationTriangleIcon className="h-5 w-5 text-red-600" />
              <h4 className="font-medium text-red-900">Alertes de risque</h4>
            </div>
            <ul className="space-y-1 text-sm text-red-700">
              {newPositionWarnings.map((warning, index) => (
                <li key={index}>• {warning}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Diversification sectorielle */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center space-x-2 mb-4">
          <ChartPieIcon className="h-6 w-6 text-purple-600" />
          <h3 className="text-lg font-semibold text-gray-900">Exposition Sectorielle</h3>
        </div>

        <div className="space-y-3">
          {sectorPercentages.map((sector, index) => (
            <div key={sector.sector} className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className={`w-4 h-4 rounded-full bg-blue-${(index % 6 + 1) * 100}`}></div>
                <span className="font-medium text-gray-900">{sector.sector}</span>
              </div>
              
              <div className="flex items-center space-x-4">
                <div className="text-right">
                  <div className="font-semibold text-gray-900">{sector.percentage.toFixed(1)}%</div>
                  <div className="text-sm text-gray-500">
                    {sector.value.toLocaleString('fr-FR')} €
                  </div>
                </div>
                
                <div className="w-24 bg-gray-200 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full ${
                      sector.percentage > riskLimits.maxSectorExposure ? 'bg-red-500' : 'bg-blue-500'
                    }`}
                    style={{ width: `${Math.min(sector.percentage, 100)}%` }}
                  ></div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {sectorPercentages.some(s => s.percentage > riskLimits.maxSectorExposure) && (
          <div className="mt-4 p-3 bg-orange-50 border border-orange-200 rounded-lg">
            <div className="flex items-center space-x-2">
              <ExclamationTriangleIcon className="h-5 w-5 text-orange-600" />
              <span className="text-sm font-medium text-orange-900">
                Certains secteurs dépassent la limite de {riskLimits.maxSectorExposure}%
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Limites de risque */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center space-x-2 mb-4">
          <ScaleIcon className="h-6 w-6 text-red-600" />
          <h3 className="text-lg font-semibold text-gray-900">Limites de Risque</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Taille max de position (%)
            </label>
            <input
              type="number"
              min="5"
              max="50"
              value={riskLimits.maxPositionSize}
              onChange={(e) => setRiskLimits(prev => ({ ...prev, maxPositionSize: Number(e.target.value) }))}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Exposition sectorielle max (%)
            </label>
            <input
              type="number"
              min="10"
              max="60"
              value={riskLimits.maxSectorExposure}
              onChange={(e) => setRiskLimits(prev => ({ ...prev, maxSectorExposure: Number(e.target.value) }))}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Risque max par position (%)
            </label>
            <input
              type="number"
              min="0.5"
              max="10"
              step="0.1"
              value={riskLimits.maxSingleRisk}
              onChange={(e) => setRiskLimits(prev => ({ ...prev, maxSingleRisk: Number(e.target.value) }))}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Seuil stop-loss (%)
            </label>
            <input
              type="number"
              min="1"
              max="15"
              step="0.5"
              value={riskLimits.stopLossThreshold}
              onChange={(e) => setRiskLimits(prev => ({ ...prev, stopLossThreshold: Number(e.target.value) }))}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Statistiques avancées */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center space-x-2 mb-4">
          <BanknotesIcon className="h-6 w-6 text-green-600" />
          <h3 className="text-lg font-semibold text-gray-900">Métriques Avancées</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <h4 className="font-medium text-gray-900 mb-2">Risque de marché</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Bêta du portefeuille:</span>
                <span className="font-medium">{riskMetrics.beta}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Volatilité:</span>
                <span className="font-medium">{riskMetrics.volatility}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Drawdown max:</span>
                <span className="font-medium text-red-600">-{riskMetrics.maxDrawdown}%</span>
              </div>
            </div>
          </div>
          
          <div>
            <h4 className="font-medium text-gray-900 mb-2">Performance ajustée</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Ratio de Sharpe:</span>
                <span className="font-medium">{riskMetrics.sharpeRatio}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Information Ratio:</span>
                <span className="font-medium">0.85</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Tracking Error:</span>
                <span className="font-medium">2.1%</span>
              </div>
            </div>
          </div>
          
          <div>
            <h4 className="font-medium text-gray-900 mb-2">Liquidité</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Cash disponible:</span>
                <span className="font-medium">{availableCash.toLocaleString('fr-FR')} €</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">% liquidités:</span>
                <span className="font-medium">
                  {((availableCash / riskMetrics.portfolioValue) * 100).toFixed(1)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Temps de liquidation:</span>
                <span className="font-medium">&lt; 1 jour</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RiskManagement;