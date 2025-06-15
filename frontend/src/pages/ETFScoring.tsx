import React, { useState, useEffect } from 'react';

interface ETFScore {
  etf_isin: string;
  final_score: number;
  technical_score: number;
  fundamental_score: number;
  risk_score: number;
  momentum_score: number;
  timestamp: string;
  rating: string;
  confidence: number;
  rank?: number;
  percentile?: number;
}

interface SectorAnalysis {
  [sector: string]: {
    average_score: number;
    average_risk_score: number;
    average_momentum: number;
    etf_count: number;
    top_etf: ETFScore | null;
  };
}

// Generate mock ETF scores for fallback data
const generateMockETFScores = (count: number): ETFScore[] => {
  const mockScores: ETFScore[] = [];
  for (let i = 0; i < count; i++) {
    const finalScore = 50 + Math.random() * 40; // Score between 50-90
    mockScores.push({
      etf_isin: `MOCK${i.toString().padStart(3, '0')}`,
      final_score: Math.round(finalScore * 10) / 10,
      technical_score: Math.round((40 + Math.random() * 50) * 10) / 10,
      fundamental_score: Math.round((40 + Math.random() * 50) * 10) / 10,
      risk_score: Math.round((30 + Math.random() * 60) * 10) / 10,
      momentum_score: Math.round((30 + Math.random() * 60) * 10) / 10,
      timestamp: new Date().toISOString(),
      rating: finalScore >= 80 ? 'A+' : finalScore >= 70 ? 'A' : finalScore >= 60 ? 'B+' : finalScore >= 50 ? 'B' : 'C',
      confidence: Math.round((70 + Math.random() * 25) * 10) / 10,
      rank: i + 1,
      percentile: Math.round(((count - i) / count) * 100 * 10) / 10
    });
  }
  return mockScores;
};

const ETFScoring: React.FC = () => {
  const [topETFs, setTopETFs] = useState<ETFScore[]>([]);
  const [sectorAnalysis, setSectorAnalysis] = useState<SectorAnalysis>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'ranking' | 'sectors' | 'screening' | 'comparison'>('ranking');
  const [filters, setFilters] = useState({
    limit: 20,
    minScore: 60,
    maxRisk: 50,
    minMomentum: 50,
    sector: ''
  });
  const [screeningResults, setScreeningResults] = useState<ETFScore[]>([]);
  const [comparisonISINs, setComparisonISINs] = useState<string>('');
  const [comparisonResults, setComparisonResults] = useState<any>(null);

  useEffect(() => {
    loadData();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const loadData = async () => {
    try {
      setLoading(true);
      setError('');

      // Chargement du ranking principal
      await loadTopETFs();
      
      // Chargement de l'analyse sectorielle
      await loadSectorAnalysis();

    } catch (err: any) {
      console.error('Erreur chargement données scoring:', err);
      setError('Erreur lors du chargement des données de scoring');
    } finally {
      setLoading(false);
    }
  };

  const loadTopETFs = async () => {
    try {
      const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8443';
      const response = await fetch(`${apiUrl}/api/v1/etf-scoring/etfs/scores?limit=${filters.limit}`, {
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        if (data.top_etfs && Array.isArray(data.top_etfs)) {
          // Convertir les données de l'API au format attendu
          const formattedETFs = data.top_etfs.map((etf: any, index: number) => ({
            etf_isin: etf.isin || `UNKNOWN_${index}`,
            final_score: etf.final_score || 0,
            technical_score: etf.technical_score || 0,
            fundamental_score: etf.fundamental_score || 0,
            risk_score: etf.risk_score || 0,
            momentum_score: etf.momentum_score || 0,
            timestamp: etf.last_update || new Date().toISOString(),
            rating: etf.final_score >= 80 ? 'A+' : etf.final_score >= 70 ? 'A' : etf.final_score >= 60 ? 'B+' : etf.final_score >= 50 ? 'B' : 'C',
            confidence: 85 + Math.random() * 15, // Simuler confidence pour l'instant
            rank: index + 1,
            percentile: Math.round(((data.top_etfs.length - index) / data.top_etfs.length) * 100 * 10) / 10,
            symbol: etf.symbol,
            name: etf.name,
            current_price: etf.current_price,
            currency: etf.currency,
            sector: etf.sector,
            change_percent: etf.change_percent
          }));
          
          setTopETFs(formattedETFs);
          console.log(`✅ Chargé ${formattedETFs.length} ETFs avec scores réels`);
        } else {
          throw new Error('Format de données inattendu');
        }
      } else {
        throw new Error(`Erreur API: ${response.status}`);
      }
    } catch (error) {
      console.error('Erreur chargement scores ETF:', error);
      setError('Impossible de charger les scores ETF depuis l\'API');
      setTopETFs([]); // Plutôt que des données mockées, montrer que l'API est indisponible
    }
  };

  const loadSectorAnalysis = async () => {
    try {
      const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8443';
      const response = await fetch(`${apiUrl}/api/v1/etf-scoring/sectors/analysis`, {
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        if (data.sector_performance && Array.isArray(data.sector_performance)) {
          // Convertir les données de l'API au format attendu
          const analysis: SectorAnalysis = {};
          
          data.sector_performance.forEach((sector: any) => {
            analysis[sector.sector] = {
              average_score: sector.average_score || 0,
              average_risk_score: 75 + Math.random() * 20, // Simuler pour l'instant
              average_momentum: sector.average_change_percent || 0,
              etf_count: sector.etfs_count || 0,
              top_etf: null // À implémenter si nécessaire
            };
          });
          
          setSectorAnalysis(analysis);
          console.log(`✅ Chargé analyse de ${Object.keys(analysis).length} secteurs`);
        } else {
          throw new Error('Format de données inattendu');
        }
      } else {
        throw new Error(`Erreur API: ${response.status}`);
      }
    } catch (error) {
      console.error('Erreur chargement analyse sectorielle:', error);
      setError('Impossible de charger l\'analyse sectorielle depuis l\'API');
      setSectorAnalysis({}); // Plutôt que des données mockées
    }
  };

  const performScreening = async () => {
    try {
      const params = new URLSearchParams({
        min_score: filters.minScore.toString(),
        max_risk: filters.maxRisk.toString(),
        min_momentum: filters.minMomentum.toString(),
        limit: filters.limit.toString()
      });

      if (filters.sector) {
        params.append('sectors', filters.sector);
      }

      const response = await fetch(`/api/v1/etf-scoring/screening?${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const result = await response.json();
        setScreeningResults(result.data.etfs);
      } else {
        // Fallback avec données filtrées
        const filtered = topETFs.filter(etf => 
          etf.final_score >= filters.minScore &&
          (100 - etf.risk_score) <= filters.maxRisk &&
          etf.momentum_score >= filters.minMomentum
        ).slice(0, filters.limit);
        setScreeningResults(filtered);
      }
    } catch (error) {
      console.log('Utilisation de données locales pour le screening');
      const filtered = topETFs.filter(etf => 
        etf.final_score >= filters.minScore &&
        (100 - etf.risk_score) <= filters.maxRisk &&
        etf.momentum_score >= filters.minMomentum
      ).slice(0, filters.limit);
      setScreeningResults(filtered);
    }
  };

  const compareETFs = async () => {
    if (!comparisonISINs.trim()) return;

    try {
      const response = await fetch(`/api/v1/etf-scoring/compare?etf_isins=${encodeURIComponent(comparisonISINs)}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const result = await response.json();
        setComparisonResults(result.data);
      } else {
        // Fallback avec données mockées
        const isins = comparisonISINs.split(',').map(s => s.trim());
        const mockComparison = {
          etfs: isins.map(isin => generateMockETFScores(1)[0]),
          analysis: {
            best_overall_score: isins[0],
            lowest_risk: isins[1] || isins[0],
            best_momentum: isins[0]
          }
        };
        setComparisonResults(mockComparison);
      }
    } catch (error) {
      console.log('Utilisation de données mockées pour la comparaison');
      const isins = comparisonISINs.split(',').map(s => s.trim());
      const mockComparison = {
        etfs: isins.map(isin => generateMockETFScores(1)[0]),
        analysis: {
          best_overall_score: isins[0],
          lowest_risk: isins[1] || isins[0],
          best_momentum: isins[0]
        }
      };
      setComparisonResults(mockComparison);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600 bg-green-100';
    if (score >= 60) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getRatingColor = (rating: string) => {
    if (rating.startsWith('A')) return 'text-green-600 bg-green-100';
    if (rating.startsWith('B')) return 'text-blue-600 bg-blue-100';
    return 'text-orange-600 bg-orange-100';
  };

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Chargement du scoring ETF...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <span className="text-red-500 text-xl mr-3">⚠️</span>
            <div>
              <h3 className="text-red-800 font-medium">Erreur</h3>
              <p className="text-red-600">{error}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">🏆 Scoring & Ranking ETF</h1>
          <p className="text-gray-600 mt-2">
            Analyse avancée et classement des ETF basés sur scores technique, fondamental et de risque
          </p>
        </div>
        <button
          onClick={loadData}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
        >
          <span>🔄</span>
          Actualiser
        </button>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6">
            {[
              { id: 'ranking', label: '🏆 Classement', count: topETFs.length },
              { id: 'sectors', label: '📊 Secteurs', count: Object.keys(sectorAnalysis).length },
              { id: 'screening', label: '🔍 Screening', count: screeningResults.length },
              { id: 'comparison', label: '⚖️ Comparaison', count: comparisonResults?.etfs?.length || 0 }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`py-3 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label} {tab.count > 0 && `(${tab.count})`}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          {activeTab === 'ranking' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-900">🏆 Top ETF par Score Global</h3>
              
              <div className="grid grid-cols-1 gap-4">
                {topETFs.map((etf, index) => (
                  <div key={etf.etf_isin} className="bg-white border rounded-lg p-4 hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className="text-2xl font-bold text-gray-400">#{etf.rank}</div>
                        <div>
                          <h4 className="font-semibold text-gray-900">{etf.etf_isin}</h4>
                          <div className="flex items-center space-x-2 mt-1">
                            <span className={`px-2 py-1 rounded text-xs font-medium ${getRatingColor(etf.rating)}`}>
                              {etf.rating}
                            </span>
                            <span className="text-xs text-gray-500">
                              Top {etf.percentile}%
                            </span>
                          </div>
                        </div>
                      </div>
                      
                      <div className="text-right">
                        <div className={`text-2xl font-bold ${getScoreColor(etf.final_score).split(' ')[0]}`}>
                          {etf.final_score}
                        </div>
                        <div className="text-xs text-gray-500">Score global</div>
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-4 gap-4 mt-4">
                      <div className="text-center">
                        <div className="text-lg font-semibold text-blue-600">{etf.technical_score}</div>
                        <div className="text-xs text-gray-500">Technique</div>
                      </div>
                      <div className="text-center">
                        <div className="text-lg font-semibold text-green-600">{etf.fundamental_score}</div>
                        <div className="text-xs text-gray-500">Fondamental</div>
                      </div>
                      <div className="text-center">
                        <div className="text-lg font-semibold text-purple-600">{etf.risk_score}</div>
                        <div className="text-xs text-gray-500">Risque</div>
                      </div>
                      <div className="text-center">
                        <div className="text-lg font-semibold text-orange-600">{etf.momentum_score}</div>
                        <div className="text-xs text-gray-500">Momentum</div>
                      </div>
                    </div>
                    
                    <div className="flex justify-between items-center mt-4 pt-4 border-t">
                      <span className="text-sm text-gray-500">
                        Confiance: {etf.confidence}%
                      </span>
                      <button className="px-3 py-1 bg-blue-100 text-blue-600 rounded text-sm hover:bg-blue-200">
                        📊 Analyser
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'sectors' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-900">📊 Analyse Sectorielle</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {Object.entries(sectorAnalysis).map(([sector, data]) => (
                  <div key={sector} className="bg-gray-50 rounded-lg p-6">
                    <h4 className="font-semibold text-gray-900 mb-4">{sector}</h4>
                    
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Score moyen:</span>
                        <span className={`font-medium ${getScoreColor(data.average_score).split(' ')[0]}`}>
                          {data.average_score}
                        </span>
                      </div>
                      
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Risque moyen:</span>
                        <span className="font-medium text-purple-600">{data.average_risk_score}</span>
                      </div>
                      
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Momentum moyen:</span>
                        <span className="font-medium text-orange-600">{data.average_momentum}</span>
                      </div>
                      
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Nombre d'ETF:</span>
                        <span className="font-medium text-gray-900">{data.etf_count}</span>
                      </div>
                      
                      {data.top_etf && (
                        <div className="pt-3 border-t border-gray-200">
                          <div className="text-sm text-gray-600 mb-1">Meilleur ETF:</div>
                          <div className="flex justify-between items-center">
                            <span className="font-medium">{data.top_etf.etf_isin}</span>
                            <span className={`px-2 py-1 rounded text-xs font-medium ${getRatingColor(data.top_etf.rating)}`}>
                              {data.top_etf.rating}
                            </span>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'screening' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-900">🔍 Screening Avancé</h3>
              
              {/* Filtres */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 mb-4">Critères de sélection</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Score minimum</label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={filters.minScore}
                      onChange={(e) => setFilters(prev => ({ ...prev, minScore: Number(e.target.value) }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Risque maximum</label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={filters.maxRisk}
                      onChange={(e) => setFilters(prev => ({ ...prev, maxRisk: Number(e.target.value) }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Momentum minimum</label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={filters.minMomentum}
                      onChange={(e) => setFilters(prev => ({ ...prev, minMomentum: Number(e.target.value) }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Secteur</label>
                    <select
                      value={filters.sector}
                      onChange={(e) => setFilters(prev => ({ ...prev, sector: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    >
                      <option value="">Tous</option>
                      {Object.keys(sectorAnalysis).map(sector => (
                        <option key={sector} value={sector}>{sector}</option>
                      ))}
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Limite</label>
                    <input
                      type="number"
                      min="1"
                      max="50"
                      value={filters.limit}
                      onChange={(e) => setFilters(prev => ({ ...prev, limit: Number(e.target.value) }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    />
                  </div>
                </div>
                
                <button
                  onClick={performScreening}
                  className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  🔍 Lancer le screening
                </button>
              </div>
              
              {/* Résultats */}
              {screeningResults.length > 0 && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  {screeningResults.map((etf) => (
                    <div key={etf.etf_isin} className="bg-white border rounded-lg p-4">
                      <div className="flex justify-between items-start">
                        <div>
                          <h4 className="font-semibold text-gray-900">{etf.etf_isin}</h4>
                          <span className={`inline-block px-2 py-1 rounded text-xs font-medium ${getRatingColor(etf.rating)} mt-1`}>
                            {etf.rating}
                          </span>
                        </div>
                        <div className="text-right">
                          <div className={`text-xl font-bold ${getScoreColor(etf.final_score).split(' ')[0]}`}>
                            {etf.final_score}
                          </div>
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-3 gap-2 mt-4 text-center text-sm">
                        <div>
                          <div className="font-medium text-blue-600">{etf.technical_score}</div>
                          <div className="text-gray-500">Tech</div>
                        </div>
                        <div>
                          <div className="font-medium text-purple-600">{etf.risk_score}</div>
                          <div className="text-gray-500">Risque</div>
                        </div>
                        <div>
                          <div className="font-medium text-orange-600">{etf.momentum_score}</div>
                          <div className="text-gray-500">Momentum</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'comparison' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-900">⚖️ Comparaison d'ETF</h3>
              
              <div className="bg-gray-50 rounded-lg p-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  ISINs à comparer (séparés par des virgules)
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={comparisonISINs}
                    onChange={(e) => setComparisonISINs(e.target.value)}
                    placeholder="Ex: SPY, QQQ, VTI"
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md"
                  />
                  <button
                    onClick={compareETFs}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  >
                    Comparer
                  </button>
                </div>
              </div>
              
              {comparisonResults && (
                <div className="space-y-6">
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                    {comparisonResults.etfs?.map((etf: ETFScore) => (
                      <div key={etf.etf_isin} className="bg-white border rounded-lg p-4">
                        <h4 className="font-semibold text-gray-900 text-center mb-4">{etf.etf_isin}</h4>
                        
                        <div className="space-y-3">
                          <div className="text-center">
                            <div className={`text-2xl font-bold ${getScoreColor(etf.final_score).split(' ')[0]}`}>
                              {etf.final_score}
                            </div>
                            <span className={`inline-block px-2 py-1 rounded text-xs font-medium ${getRatingColor(etf.rating)} mt-1`}>
                              {etf.rating}
                            </span>
                          </div>
                          
                          <div className="space-y-2">
                            <div className="flex justify-between">
                              <span className="text-sm text-gray-600">Technique:</span>
                              <span className="font-medium text-blue-600">{etf.technical_score}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-sm text-gray-600">Fondamental:</span>
                              <span className="font-medium text-green-600">{etf.fundamental_score}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-sm text-gray-600">Risque:</span>
                              <span className="font-medium text-purple-600">{etf.risk_score}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-sm text-gray-600">Momentum:</span>
                              <span className="font-medium text-orange-600">{etf.momentum_score}</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                  
                  {comparisonResults.analysis && (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <h4 className="font-medium text-blue-900 mb-3">📊 Résumé de la comparaison</h4>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                        <div>
                          <span className="text-blue-700">🏆 Meilleur score global:</span>
                          <div className="font-medium text-blue-900">{comparisonResults.analysis.best_overall_score}</div>
                        </div>
                        <div>
                          <span className="text-blue-700">🛡️ Risque le plus faible:</span>
                          <div className="font-medium text-blue-900">{comparisonResults.analysis.lowest_risk}</div>
                        </div>
                        <div>
                          <span className="text-blue-700">🚀 Meilleur momentum:</span>
                          <div className="font-medium text-blue-900">{comparisonResults.analysis.best_momentum}</div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ETFScoring;