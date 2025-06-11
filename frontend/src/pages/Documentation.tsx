import React, { useState, useEffect } from 'react';
import { 
  BookOpenIcon, 
  ChartBarIcon, 
  CurrencyDollarIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  ChartPieIcon,
  ArrowTrendingUpIcon,
  BellIcon,
  MagnifyingGlassIcon,
  DocumentTextIcon,
  PaperClipIcon
} from '@heroicons/react/24/outline';
import { marketAPI } from '../services/api';

interface DocSection {
  id: string;
  title: string;
  icon: React.ComponentType<any>;
  content: React.ReactNode;
}

const Documentation: React.FC = () => {
  const [activeSection, setActiveSection] = useState<string>('overview');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [etfData, setEtfData] = useState<any[]>([]);
  const [showInteractiveDemo, setShowInteractiveDemo] = useState(false);

  useEffect(() => {
    const fetchETFData = async () => {
      try {
        const data = await marketAPI.getRealETFs();
        setEtfData(data.slice(0, 5)); // Limite à 5 ETFs pour la démo
      } catch (error) {
        console.error('Erreur lors du chargement des ETFs:', error);
        // Données fallback pour la démo
        setEtfData([
          { symbol: 'IWDA.AS', regularMarketPrice: 85.42, regularMarketChangePercent: 1.23 },
          { symbol: 'VWCE.DE', regularMarketPrice: 110.75, regularMarketChangePercent: -0.54 },
          { symbol: 'CSPX.L', regularMarketPrice: 520.30, regularMarketChangePercent: 0.89 }
        ]);
      }
    };

    if (activeSection === 'etfs') {
      fetchETFData();
    }
  }, [activeSection]);

  const sections: DocSection[] = [
    {
      id: 'overview',
      title: 'Vue d\'ensemble',
      icon: BookOpenIcon,
      content: (
        <div className="space-y-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Application Trading ETF</h2>
            <p className="text-gray-600 mb-4">
              Cette application est conçue pour vous aider à trader des ETFs européens en temps réel avec des signaux intelligents 
              et une gestion de portfolio avancée.
            </p>
            
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Fonctionnalités principales :</h3>
            <ul className="space-y-2 text-gray-600">
              <li className="flex items-start">
                <span className="w-2 h-2 bg-blue-500 rounded-full mt-2 mr-3 flex-shrink-0"></span>
                <span><strong>Données temps réel</strong> : Prix et variations des ETFs européens mis à jour toutes les 30 secondes</span>
              </li>
              <li className="flex items-start">
                <span className="w-2 h-2 bg-blue-500 rounded-full mt-2 mr-3 flex-shrink-0"></span>
                <span><strong>Signaux de trading</strong> : Algorithmes avancés pour identifier les opportunités d'achat/vente</span>
              </li>
              <li className="flex items-start">
                <span className="w-2 h-2 bg-blue-500 rounded-full mt-2 mr-3 flex-shrink-0"></span>
                <span><strong>Gestion de portfolio</strong> : Suivi des positions, P&L et performance en temps réel</span>
              </li>
              <li className="flex items-start">
                <span className="w-2 h-2 bg-blue-500 rounded-full mt-2 mr-3 flex-shrink-0"></span>
                <span><strong>Alertes intelligentes</strong> : Notifications sur les mouvements significatifs et opportunités</span>
              </li>
            </ul>
          </div>
          
          <div className="bg-blue-50 p-4 rounded-lg">
            <h4 className="font-semibold text-blue-900 mb-2">🎯 Public cible</h4>
            <p className="text-blue-800">
              Traders particuliers et investisseurs souhaitant optimiser leurs investissements en ETFs européens 
              avec des outils professionnels et des données fiables.
            </p>
          </div>
        </div>
      )
    },
    {
      id: 'dashboard',
      title: 'Dashboard',
      icon: ChartBarIcon,
      content: (
        <div className="space-y-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Dashboard - Vue d'ensemble du marché</h2>
          
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Statistiques principales</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-semibold text-gray-900 mb-2">📊 Marché Global</h4>
                <p className="text-gray-600">
                  Affiche le nombre total d'ETFs suivis et la performance moyenne du marché en temps réel.
                </p>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-semibold text-gray-900 mb-2">📈 ETFs Positifs</h4>
                <p className="text-gray-600">
                  Ratio des ETFs en hausse par rapport au total, indicateur de la tendance générale du marché.
                </p>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-semibold text-gray-900 mb-2">⚡ Performance Moyenne</h4>
                <p className="text-gray-600">
                  Variation moyenne de tous les ETFs suivis, mise à jour toutes les 30 secondes.
                </p>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-semibold text-gray-900 mb-2">🚨 Alertes</h4>
                <p className="text-gray-600">
                  Nombre d'ETFs avec des mouvements significatifs (&gt;2%) nécessitant votre attention.
                </p>
              </div>
            </div>
          </div>
          
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Graphiques et analyses</h3>
            <ul className="space-y-2 text-gray-600">
              <li>• <strong>Graphique principal</strong> : Évolution des indices européens (CAC 40, DAX, FTSE 100, etc.)</li>
              <li>• <strong>Signaux avancés</strong> : Top 5 des signaux les plus récents avec scores de confiance</li>
              <li>• <strong>Top gainers/losers</strong> : ETFs avec les meilleures et pires performances du jour</li>
            </ul>
          </div>
        </div>
      )
    },
    {
      id: 'etfs',
      title: 'ETFs',
      icon: ChartPieIcon,
      content: (
        <div className="space-y-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Liste des ETFs - Suivi en temps réel</h2>
          
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">ETFs européens disponibles</h3>
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="flex justify-between items-center mb-3">
                <h4 className="font-semibold text-blue-900">🌍 ETFs suivis en temps réel</h4>
                <button
                  onClick={() => setShowInteractiveDemo(!showInteractiveDemo)}
                  className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
                >
                  {showInteractiveDemo ? 'Masquer' : 'Voir démo'}
                </button>
              </div>
              
              {showInteractiveDemo ? (
                <div className="space-y-2">
                  {etfData.map((etf) => (
                    <div key={etf.symbol} className="flex justify-between items-center bg-white p-3 rounded border">
                      <div>
                        <span className="font-semibold text-gray-900">{etf.symbol}</span>
                        <span className="text-sm text-gray-600 ml-2">Prix actuel</span>
                      </div>
                      <div className="text-right">
                        <div className="font-bold text-gray-900">
                          {etf.regularMarketPrice?.toFixed(2) || 'N/A'} €
                        </div>
                        <div className={`text-sm font-medium ${
                          (etf.regularMarketChangePercent || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {(etf.regularMarketChangePercent || 0) >= 0 ? '+' : ''}
                          {(etf.regularMarketChangePercent || 0).toFixed(2)}%
                        </div>
                      </div>
                    </div>
                  ))}
                  <div className="text-xs text-blue-600 text-center mt-2">
                    Données mises à jour automatiquement
                  </div>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-blue-800 text-sm">
                  <div>• <strong>IWDA.AS</strong> - iShares Core MSCI World</div>
                  <div>• <strong>VWCE.DE</strong> - Vanguard FTSE All-World</div>
                  <div>• <strong>CSPX.L</strong> - iShares Core S&P 500</div>
                  <div>• <strong>VUAA.DE</strong> - Vanguard S&P 500</div>
                  <div>• <strong>IUSQ.DE</strong> - iShares Core S&P 500</div>
                  <div>• <strong>EIMI.DE</strong> - iShares Core MSCI EM</div>
                </div>
              )}
            </div>
          </div>
          
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Informations affichées</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-semibold text-gray-900 mb-2">💰 Prix actuel</h4>
                <p className="text-gray-600">Prix en temps réel avec devise (EUR/GBP) mis à jour toutes les 30 secondes.</p>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-semibold text-gray-900 mb-2">📊 Variation</h4>
                <p className="text-gray-600">Changement en valeur absolue et pourcentage depuis la clôture précédente.</p>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-semibold text-gray-900 mb-2">🏢 Secteur</h4>
                <p className="text-gray-600">Classification par secteur : Global Developed, US Large Cap, Emerging Markets, etc.</p>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-semibold text-gray-900 mb-2">🏛️ Bourse</h4>
                <p className="text-gray-600">Place de cotation : Euronext Amsterdam, XETRA, London Stock Exchange.</p>
              </div>
            </div>
          </div>
          
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Fonctionnalités</h3>
            <ul className="space-y-2 text-gray-600">
              <li>• <strong>Recherche</strong> : Filtrage par nom, symbole ou ISIN</li>
              <li>• <strong>Tri par secteur</strong> : Affichage par catégorie d'investissement</li>
              <li>• <strong>Indicateurs visuels</strong> : Couleurs pour variations positives (vert) et négatives (rouge)</li>
              <li>• <strong>Actualisation automatique</strong> : Données mises à jour en continu</li>
            </ul>
          </div>
        </div>
      )
    },
    {
      id: 'signals',
      title: 'Signaux',
      icon: ArrowTrendingUpIcon,
      content: (
        <div className="space-y-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Signaux de Trading - Intelligence artificielle</h2>
          
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Types de signaux</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                <h4 className="font-semibold text-green-900 mb-2">🟢 BUY - Achat</h4>
                <p className="text-green-800">
                  Signal d'achat détecté par l'analyse technique. Inclut un prix cible et un stop-loss recommandés.
                </p>
              </div>
              <div className="bg-red-50 p-4 rounded-lg border border-red-200">
                <h4 className="font-semibold text-red-900 mb-2">🔴 SELL - Vente</h4>
                <p className="text-red-800">
                  Signal de vente recommandé basé sur les indicateurs techniques et l'analyse des tendances.
                </p>
              </div>
              <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
                <h4 className="font-semibold text-yellow-900 mb-2">🟡 HOLD - Conserver</h4>
                <p className="text-yellow-800">
                  Maintenir la position actuelle. Aucune action recommandée pour le moment.
                </p>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                <h4 className="font-semibold text-gray-900 mb-2">⚪ WAIT - Attendre</h4>
                <p className="text-gray-800">
                  Attendre une confirmation ou de meilleures conditions de marché avant d'agir.
                </p>
              </div>
            </div>
          </div>
          
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Métriques des signaux</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-semibold text-gray-900 mb-2">🎯 Score de confiance</h4>
                <p className="text-gray-600">
                  Pourcentage de 0 à 100% indiquant la fiabilité du signal basé sur l'analyse des données historiques.
                </p>
                <ul className="mt-2 text-sm text-gray-500">
                  <li>• 80-100% : Très haute confiance (vert)</li>
                  <li>• 60-79% : Confiance moyenne (jaune)</li>
                  <li>• 0-59% : Faible confiance (rouge)</li>
                </ul>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-semibold text-gray-900 mb-2">⚙️ Score technique</h4>
                <p className="text-gray-600">
                  Évaluation basée sur les indicateurs techniques : RSI, MACD, moyennes mobiles, bandes de Bollinger.
                </p>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-semibold text-gray-900 mb-2">⚠️ Score de risque</h4>
                <p className="text-gray-600">
                  Évaluation du risque associé au signal, tenant compte de la volatilité et des conditions de marché.
                </p>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-semibold text-gray-900 mb-2">💰 Prix cible / Stop-loss</h4>
                <p className="text-gray-600">
                  Niveaux recommandés pour la prise de profit et la limitation des pertes.
                </p>
              </div>
            </div>
          </div>
          
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Filtres et options</h3>
            <ul className="space-y-2 text-gray-600">
              <li>• <strong>Filtrage par type</strong> : Afficher uniquement BUY, SELL, HOLD ou WAIT</li>
              <li>• <strong>Confiance minimum</strong> : Curseur pour définir le seuil de confiance (0-100%)</li>
              <li>• <strong>Signaux actifs</strong> : Seuls les signaux non expirés sont affichés</li>
              <li>• <strong>Tri par confiance</strong> : Les signaux les plus fiables apparaissent en premier</li>
            </ul>
          </div>
        </div>
      )
    },
    {
      id: 'portfolio',
      title: 'Portfolio',
      icon: CurrencyDollarIcon,
      content: (
        <div className="space-y-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Gestion de Portfolio - Suivi des performances</h2>
          
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Métriques principales</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-blue-50 p-4 rounded-lg">
                <h4 className="font-semibold text-blue-900 mb-2">💰 Valeur totale</h4>
                <p className="text-blue-800">
                  Valeur actuelle de toutes vos positions calculée en temps réel avec les prix de marché actuels.
                </p>
              </div>
              <div className="bg-green-50 p-4 rounded-lg">
                <h4 className="font-semibold text-green-900 mb-2">📈 Gain/Perte total</h4>
                <p className="text-green-800">
                  Différence entre la valeur actuelle et le coût d'acquisition de vos positions, en euros et pourcentage.
                </p>
              </div>
              <div className="bg-yellow-50 p-4 rounded-lg">
                <h4 className="font-semibold text-yellow-900 mb-2">⚡ Variation du jour</h4>
                <p className="text-yellow-800">
                  Performance de votre portfolio depuis l'ouverture du marché, basée sur les variations intraday.
                </p>
              </div>
              <div className="bg-purple-50 p-4 rounded-lg">
                <h4 className="font-semibold text-purple-900 mb-2">💳 Liquidités</h4>
                <p className="text-purple-800">
                  Montant disponible en espèces pour de nouveaux investissements (fonctionnalité à venir).
                </p>
              </div>
            </div>
          </div>
          
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Positions détaillées</h3>
            <p className="text-gray-600 mb-4">
              Tableau complet de toutes vos positions avec calculs en temps réel :
            </p>
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <h5 className="font-semibold text-gray-900 mb-2">Informations par position :</h5>
                  <ul className="space-y-1 text-gray-600">
                    <li>• ISIN de l'ETF</li>
                    <li>• Nombre de parts détenues</li>
                    <li>• Prix d'achat moyen</li>
                    <li>• Valeur actuelle calculée</li>
                    <li>• Date d'acquisition</li>
                  </ul>
                </div>
                <div>
                  <h5 className="font-semibold text-gray-900 mb-2">Calculs automatiques :</h5>
                  <ul className="space-y-1 text-gray-600">
                    <li>• P&L par position</li>
                    <li>• Pourcentage de gain/perte</li>
                    <li>• Poids dans le portfolio</li>
                    <li>• Performance relative</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
          
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Historique des transactions</h3>
            <p className="text-gray-600 mb-4">
              Suivi complet de toutes vos opérations d'achat et de vente :
            </p>
            <ul className="space-y-2 text-gray-600">
              <li>• <strong>Type de transaction</strong> : BUY (vert) ou SELL (rouge)</li>
              <li>• <strong>Détails complets</strong> : ETF, quantité, prix, frais</li>
              <li>• <strong>Calcul du total</strong> : (Quantité × Prix) + Frais</li>
              <li>• <strong>Horodatage</strong> : Date et heure précises de chaque opération</li>
            </ul>
          </div>
        </div>
      )
    },
    {
      id: 'alerts',
      title: 'Alertes',
      icon: BellIcon,
      content: (
        <div className="space-y-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Système d'Alertes - Notifications intelligentes</h2>
          
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Types d'alertes</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-red-50 p-4 rounded-lg border border-red-200">
                <h4 className="font-semibold text-red-900 mb-2">🚨 Alertes de prix</h4>
                <p className="text-red-800">
                  Notifications lorsqu'un ETF atteint un seuil de prix défini (au-dessus ou en-dessous).
                </p>
              </div>
              <div className="bg-orange-50 p-4 rounded-lg border border-orange-200">
                <h4 className="font-semibold text-orange-900 mb-2">📊 Alertes de variation</h4>
                <p className="text-orange-800">
                  Notifications sur les mouvements importants (&gt;2%, &gt;5%, etc.) en temps réel.
                </p>
              </div>
              <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                <h4 className="font-semibold text-blue-900 mb-2">🎯 Alertes de signaux</h4>
                <p className="text-blue-800">
                  Notifications automatiques lors de la génération de nouveaux signaux BUY/SELL.
                </p>
              </div>
              <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                <h4 className="font-semibold text-green-900 mb-2">💼 Alertes de portfolio</h4>
                <p className="text-green-800">
                  Notifications sur les performances du portfolio (objectifs atteints, stop-loss, etc.).
                </p>
              </div>
            </div>
          </div>
          
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Configuration des alertes</h3>
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-semibold text-gray-900 mb-2">Paramètres personnalisables :</h4>
              <ul className="space-y-2 text-gray-600">
                <li>• <strong>Seuils de prix</strong> : Définir des niveaux de support et résistance</li>
                <li>• <strong>Pourcentages de variation</strong> : Alertes sur mouvements de 1%, 2%, 5%, 10%</li>
                <li>• <strong>Volume anormal</strong> : Détection des pics de volume inhabituels</li>
                <li>• <strong>Horaires d'activation</strong> : Limiter les notifications aux heures de trading</li>
                <li>• <strong>Canaux de notification</strong> : Email, push browser, SMS (à venir)</li>
              </ul>
            </div>
          </div>
          
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Gestion des alertes</h3>
            <ul className="space-y-2 text-gray-600">
              <li>• <strong>Création facile</strong> : Interface intuitive pour configurer rapidement</li>
              <li>• <strong>Activation/Désactivation</strong> : Contrôle granulaire de chaque alerte</li>
              <li>• <strong>Historique</strong> : Consultation des alertes passées et leur pertinence</li>
              <li>• <strong>Groupes d'alertes</strong> : Organisation par thème (portfolio, secteur, etc.)</li>
            </ul>
          </div>
        </div>
      )
    },
    {
      id: 'glossary',
      title: 'Glossaire',
      icon: InformationCircleIcon,
      content: (
        <div className="space-y-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Glossaire des termes financiers</h2>
          
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">ETFs et Instruments</h3>
            <div className="space-y-3">
              <div className="border-l-4 border-blue-500 pl-4">
                <h4 className="font-semibold text-gray-900">ETF (Exchange-Traded Fund)</h4>
                <p className="text-gray-600">
                  Fonds négocié en bourse qui réplique la performance d'un indice, d'un secteur ou d'une région géographique. 
                  Permet une diversification instantanée avec un seul instrument.
                </p>
              </div>
              <div className="border-l-4 border-blue-500 pl-4">
                <h4 className="font-semibold text-gray-900">ISIN (International Securities Identification Number)</h4>
                <p className="text-gray-600">
                  Code international unique à 12 caractères identifiant de manière univoque un instrument financier.
                </p>
              </div>
              <div className="border-l-4 border-blue-500 pl-4">
                <h4 className="font-semibold text-gray-900">TER (Total Expense Ratio)</h4>
                <p className="text-gray-600">
                  Ratio des frais totaux d'un ETF, exprimé en pourcentage annuel. Plus le TER est bas, moins l'ETF coûte à détenir.
                </p>
              </div>
            </div>
          </div>
          
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Indicateurs techniques</h3>
            <div className="space-y-3">
              <div className="border-l-4 border-green-500 pl-4">
                <h4 className="font-semibold text-gray-900">RSI (Relative Strength Index)</h4>
                <p className="text-gray-600">
                  Oscillateur de momentum de 0 à 100. RSI &gt; 70 = surachat, RSI &lt; 30 = survente.
                </p>
              </div>
              <div className="border-l-4 border-green-500 pl-4">
                <h4 className="font-semibold text-gray-900">MACD (Moving Average Convergence Divergence)</h4>
                <p className="text-gray-600">
                  Indicateur de tendance basé sur la différence entre deux moyennes mobiles exponentielles.
                </p>
              </div>
              <div className="border-l-4 border-green-500 pl-4">
                <h4 className="font-semibold text-gray-900">Bandes de Bollinger</h4>
                <p className="text-gray-600">
                  Enveloppe statistique autour d'une moyenne mobile, utilisée pour identifier les niveaux de surachat/survente.
                </p>
              </div>
              <div className="border-l-4 border-green-500 pl-4">
                <h4 className="font-semibold text-gray-900">Volume</h4>
                <p className="text-gray-600">
                  Nombre de parts échangées sur une période. Un volume élevé confirme généralement une tendance.
                </p>
              </div>
            </div>
          </div>
          
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Gestion des risques</h3>
            <div className="space-y-3">
              <div className="border-l-4 border-red-500 pl-4">
                <h4 className="font-semibold text-gray-900">Stop-Loss</h4>
                <p className="text-gray-600">
                  Ordre automatique de vente déclenché lorsque le prix atteint un niveau prédéfini pour limiter les pertes.
                </p>
              </div>
              <div className="border-l-4 border-red-500 pl-4">
                <h4 className="font-semibold text-gray-900">Prix cible (Take Profit)</h4>
                <p className="text-gray-600">
                  Niveau de prix auquel il est recommandé de prendre ses bénéfices et clôturer la position.
                </p>
              </div>
              <div className="border-l-4 border-red-500 pl-4">
                <h4 className="font-semibold text-gray-900">Volatilité</h4>
                <p className="text-gray-600">
                  Mesure de l'amplitude des variations de prix. Une forte volatilité indique des mouvements importants.
                </p>
              </div>
              <div className="border-l-4 border-red-500 pl-4">
                <h4 className="font-semibold text-gray-900">Drawdown</h4>
                <p className="text-gray-600">
                  Baisse maximale d'un investissement depuis son plus haut historique, exprimée en pourcentage.
                </p>
              </div>
            </div>
          </div>
          
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Performance et métriques</h3>
            <div className="space-y-3">
              <div className="border-l-4 border-purple-500 pl-4">
                <h4 className="font-semibold text-gray-900">P&L (Profit & Loss)</h4>
                <p className="text-gray-600">
                  Gain ou perte réalisé(e) ou latent(e) sur une position ou un portfolio.
                </p>
              </div>
              <div className="border-l-4 border-purple-500 pl-4">
                <h4 className="font-semibold text-gray-900">Ratio de Sharpe</h4>
                <p className="text-gray-600">
                  Mesure du rendement ajusté au risque. Plus le ratio est élevé, meilleure est la performance par unité de risque.
                </p>
              </div>
              <div className="border-l-4 border-purple-500 pl-4">
                <h4 className="font-semibold text-gray-900">Alpha</h4>
                <p className="text-gray-600">
                  Performance excédentaire d'un investissement par rapport à son indice de référence.
                </p>
              </div>
              <div className="border-l-4 border-purple-500 pl-4">
                <h4 className="font-semibold text-gray-900">Bêta</h4>
                <p className="text-gray-600">
                  Mesure de la sensibilité d'un actif aux mouvements du marché. Bêta = 1 signifie mouvement identique au marché.
                </p>
              </div>
            </div>
          </div>
        </div>
      )
    },
    {
      id: 'risks',
      title: 'Avertissements',
      icon: ExclamationTriangleIcon,
      content: (
        <div className="space-y-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Avertissements et gestion des risques</h2>
          
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 mb-6">
            <div className="flex items-start">
              <ExclamationTriangleIcon className="h-6 w-6 text-red-600 mt-1 mr-3 flex-shrink-0" />
              <div>
                <h3 className="text-lg font-semibold text-red-900 mb-2">⚠️ Avertissement important</h3>
                <p className="text-red-800">
                  Le trading d'ETFs comporte des risques de perte en capital. Les performances passées ne préjugent pas 
                  des performances futures. Cette application fournit des outils d'aide à la décision mais ne constitue 
                  pas un conseil en investissement.
                </p>
              </div>
            </div>
          </div>
          
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Risques principaux</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-orange-50 p-4 rounded-lg border border-orange-200">
                <h4 className="font-semibold text-orange-900 mb-2">🎲 Risque de marché</h4>
                <p className="text-orange-800">
                  Les prix des ETFs fluctuent selon les conditions de marché. Une baisse générale peut affecter 
                  tous vos investissements simultanément.
                </p>
              </div>
              <div className="bg-orange-50 p-4 rounded-lg border border-orange-200">
                <h4 className="font-semibold text-orange-900 mb-2">💱 Risque de change</h4>
                <p className="text-orange-800">
                  Les ETFs cotés en devises étrangères (GBP, USD) exposent à un risque de change 
                  qui peut amplifier les gains ou les pertes.
                </p>
              </div>
              <div className="bg-orange-50 p-4 rounded-lg border border-orange-200">
                <h4 className="font-semibold text-orange-900 mb-2">📊 Risque de liquidité</h4>
                <p className="text-orange-800">
                  En cas de forte volatilité, il peut être difficile d'acheter ou vendre à des prix favorables.
                </p>
              </div>
              <div className="bg-orange-50 p-4 rounded-lg border border-orange-200">
                <h4 className="font-semibold text-orange-900 mb-2">🤖 Risque algorithmique</h4>
                <p className="text-orange-800">
                  Les signaux automatiques peuvent donner de fausses indications. Toujours analyser avant d'agir.
                </p>
              </div>
            </div>
          </div>
          
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Bonnes pratiques</h3>
            <div className="bg-green-50 p-4 rounded-lg border border-green-200">
              <ul className="space-y-2 text-green-800">
                <li>• <strong>Diversification</strong> : Ne pas concentrer tous vos investissements sur un seul ETF</li>
                <li>• <strong>Gestion de position</strong> : Ne jamais investir plus que vous ne pouvez vous permettre de perdre</li>
                <li>• <strong>Stop-loss</strong> : Toujours définir un niveau maximum de perte acceptable</li>
                <li>• <strong>Formation continue</strong> : Se tenir informé des évolutions des marchés financiers</li>
                <li>• <strong>Patience</strong> : Éviter les décisions impulsives basées sur des émotions</li>
                <li>• <strong>Analyse personnelle</strong> : Compléter les signaux automatiques par votre propre analyse</li>
              </ul>
            </div>
          </div>
          
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Responsabilité</h3>
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-gray-600 mb-4">
                <strong>Cette application est un outil d'aide à la décision.</strong> L'utilisateur reste seul responsable 
                de ses décisions d'investissement et de leurs conséquences.
              </p>
              <ul className="space-y-1 text-gray-600 text-sm">
                <li>• Les données peuvent contenir des erreurs ou des retards</li>
                <li>• Les signaux ne garantissent pas la performance future</li>
                <li>• Il est recommandé de consulter un conseiller financier pour des investissements importants</li>
                <li>• Toujours effectuer ses propres recherches avant d'investir</li>
              </ul>
            </div>
          </div>
        </div>
      )
    },
    {
      id: 'tutorial',
      title: 'Tutoriel interactif',
      icon: DocumentTextIcon,
      content: (
        <div className="space-y-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">🎓 Tutoriel interactif - Premiers pas</h2>
          
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-6 rounded-lg border">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">🚀 Guide de démarrage rapide</h3>
            
            <div className="space-y-4">
              <div className="flex items-start space-x-4">
                <div className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold">1</div>
                <div>
                  <h4 className="font-semibold text-gray-900">Connexion à l'application</h4>
                  <p className="text-gray-600 mb-2">Connectez-vous avec vos identifiants ou créez un compte</p>
                  <div className="bg-gray-100 p-3 rounded text-sm font-mono">
                    Email: test@trading.com<br />
                    Mot de passe: test123
                  </div>
                </div>
              </div>
              
              <div className="flex items-start space-x-4">
                <div className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold">2</div>
                <div>
                  <h4 className="font-semibold text-gray-900">Explorer le Dashboard</h4>
                  <p className="text-gray-600 mb-2">Découvrez la vue d'ensemble du marché et les statistiques principales</p>
                  <button 
                    onClick={() => window.location.href = '/dashboard'}
                    className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
                  >
                    🏠 Aller au Dashboard
                  </button>
                </div>
              </div>
              
              <div className="flex items-start space-x-4">
                <div className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold">3</div>
                <div>
                  <h4 className="font-semibold text-gray-900">Consulter les ETFs</h4>
                  <p className="text-gray-600 mb-2">Explorez la liste des ETFs européens avec les prix en temps réel</p>
                  <button 
                    onClick={() => window.location.href = '/etf-list'}
                    className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 text-sm"
                  >
                    📊 Voir les ETFs
                  </button>
                </div>
              </div>
              
              <div className="flex items-start space-x-4">
                <div className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold">4</div>
                <div>
                  <h4 className="font-semibold text-gray-900">Analyser les signaux</h4>
                  <p className="text-gray-600 mb-2">Découvrez les signaux de trading automatisés générés par nos algorithmes</p>
                  <button 
                    onClick={() => window.location.href = '/signals'}
                    className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 text-sm"
                  >
                    🎯 Consulter les signaux
                  </button>
                </div>
              </div>
              
              <div className="flex items-start space-x-4">
                <div className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold">5</div>
                <div>
                  <h4 className="font-semibold text-gray-900">Gérer votre portfolio</h4>
                  <p className="text-gray-600 mb-2">Suivez vos positions et analysez les performances</p>
                  <button 
                    onClick={() => window.location.href = '/portfolio'}
                    className="px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700 text-sm"
                  >
                    💼 Gérer le portfolio
                  </button>
                </div>
              </div>
            </div>
          </div>
          
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-yellow-900 mb-3">💡 Conseils pour débuter</h3>
            <ul className="space-y-2 text-yellow-800">
              <li>• Commencez par explorer le Dashboard pour comprendre l'état général du marché</li>
              <li>• Familiarisez-vous avec les ETFs en consultant leurs fiches détaillées</li>
              <li>• Observez les signaux sans agir immédiatement pour comprendre leur logique</li>
              <li>• Configurez des alertes sur quelques ETFs qui vous intéressent</li>
              <li>• Testez les fonctionnalités de backtesting avant de prendre des positions réelles</li>
            </ul>
          </div>
          
          <div className="bg-green-50 border border-green-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-green-900 mb-3">📚 Ressources utiles</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h4 className="font-semibold text-green-800 mb-2">📖 Guides détaillés</h4>
                <ul className="space-y-1 text-green-700 text-sm">
                  <li>• Comprendre les signaux de trading</li>
                  <li>• Interpréter l'analyse technique</li>
                  <li>• Optimiser la diversification</li>
                  <li>• Gérer les risques efficacement</li>
                </ul>
              </div>
              <div>
                <h4 className="font-semibold text-green-800 mb-2">🔧 Outils pratiques</h4>
                <ul className="space-y-1 text-green-700 text-sm">
                  <li>• Calculateur de position sizing</li>
                  <li>• Simulateur de backtesting</li>
                  <li>• Générateur d'alertes personnalisées</li>
                  <li>• Analyseur de performance portfolio</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )
    }
  ];

  // Fonction de filtrage pour la recherche
  const filteredSections = sections.filter(section =>
    searchTerm === '' || 
    section.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    section.id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="flex">
        {/* Sidebar */}
        <div className="w-64 bg-white shadow-lg h-screen sticky top-0 overflow-y-auto">
          <div className="p-6 border-b border-gray-200">
            <h1 className="text-xl font-bold text-gray-900">Documentation</h1>
            <p className="text-sm text-gray-600 mt-1">Guide complet de l'application</p>
            
            {/* Barre de recherche */}
            <div className="mt-4 relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="text"
                className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="Rechercher dans la documentation..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>
          
          <nav className="p-4">
            {searchTerm && (
              <div className="mb-4 text-xs text-gray-500">
                {filteredSections.length} résultat(s) pour "{searchTerm}"
              </div>
            )}
            <ul className="space-y-2">
              {filteredSections.map((section) => {
                const Icon = section.icon;
                return (
                  <li key={section.id}>
                    <button
                      onClick={() => setActiveSection(section.id)}
                      className={`w-full flex items-center px-3 py-2 text-left rounded-lg transition-colors ${
                        activeSection === section.id
                          ? 'bg-blue-100 text-blue-700 font-medium'
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      <Icon className="h-5 w-5 mr-3" />
                      {section.title}
                    </button>
                  </li>
                );
              })}
            </ul>
          </nav>
        </div>
        
        {/* Main content */}
        <div className="flex-1 overflow-y-auto">
          <div className="max-w-4xl mx-auto p-8">
            {filteredSections.find(section => section.id === activeSection)?.content || (
              <div className="text-center py-12">
                <MagnifyingGlassIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">Aucun résultat trouvé</h3>
                <p className="text-gray-500">Essayez avec d'autres termes de recherche</p>
                <button
                  onClick={() => setSearchTerm('')}
                  className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  Effacer la recherche
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Documentation;