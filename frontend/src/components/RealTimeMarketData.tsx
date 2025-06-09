import React, { useState, useEffect, useCallback } from 'react';
import { useAppSelector } from '../hooks/redux';
import { realtimeMarketAPI } from '../services/api';

interface MarketData {
  symbol: string;
  timestamp: string;
  price: number;
  open: number;
  high: number;
  low: number;
  volume: number;
  change: number;
  change_percent: number;
  source: string;
  market_status: string;
}

interface RealTimeMarketDataProps {
  symbols?: string[];
  autoConnect?: boolean;
  onDataUpdate?: (data: Record<string, MarketData>) => void;
}

const RealTimeMarketData: React.FC<RealTimeMarketDataProps> = ({
  symbols = [],
  autoConnect = true,
  onDataUpdate
}) => {
  const [marketData, setMarketData] = useState<Record<string, MarketData>>({});
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected');
  const [websocket, setWebsocket] = useState<WebSocket | null>(null);
  const [lastUpdate, setLastUpdate] = useState<string>('');
  
  const { isAuthenticated } = useAppSelector(state => state.auth);

  const connectWebSocket = useCallback(() => {
    if (!isAuthenticated || websocket?.readyState === WebSocket.OPEN) {
      return;
    }

    setConnectionStatus('connecting');
    
    try {
      // Utilisation de l'helper API pour l'URL WebSocket
      const wsUrl = realtimeMarketAPI.getWebSocketUrl();
      
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('WebSocket connecté au marché temps réel');
        setConnectionStatus('connected');
        setWebsocket(ws);
        
        // Envoi d'un ping initial
        ws.send(JSON.stringify({
          command: 'ping'
        }));
        
        // Souscription aux symboles si spécifiés
        if (symbols.length > 0) {
          ws.send(JSON.stringify({
            command: 'subscribe',
            symbols: symbols
          }));
        }
      };
      
      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          
          switch (message.type) {
            case 'pong':
              console.log('Pong reçu du serveur');
              break;
              
            case 'subscribed':
              console.log('Souscription confirmée pour:', message.symbols);
              break;
              
            case 'initial_data':
            case 'market_update':
              if (message.data) {
                setMarketData(message.data);
                setLastUpdate(message.timestamp);
                onDataUpdate?.(message.data);
              }
              break;
              
            default:
              console.log('Message WebSocket non géré:', message);
          }
        } catch (error) {
          console.error('Erreur parsing message WebSocket:', error);
        }
      };
      
      ws.onclose = () => {
        console.log('WebSocket fermé');
        setConnectionStatus('disconnected');
        setWebsocket(null);
        
        // Reconnexion automatique après 5 secondes
        if (autoConnect) {
          setTimeout(() => {
            connectWebSocket();
          }, 5000);
        }
      };
      
      ws.onerror = (error) => {
        console.error('Erreur WebSocket:', error);
        setConnectionStatus('error');
      };
      
    } catch (error) {
      console.error('Erreur création WebSocket:', error);
      setConnectionStatus('error');
    }
  }, [isAuthenticated, websocket, symbols, autoConnect, onDataUpdate]);

  const disconnectWebSocket = useCallback(() => {
    if (websocket) {
      websocket.close();
      setWebsocket(null);
      setConnectionStatus('disconnected');
    }
  }, [websocket]);

  const sendPing = useCallback(() => {
    if (websocket?.readyState === WebSocket.OPEN) {
      websocket.send(JSON.stringify({
        command: 'ping'
      }));
    }
  }, [websocket]);

  // Auto-connexion à l'initialisation
  useEffect(() => {
    if (autoConnect && isAuthenticated) {
      connectWebSocket();
    }
    
    return () => {
      if (websocket) {
        websocket.close();
      }
    };
  }, [autoConnect, isAuthenticated, connectWebSocket, websocket]);

  // Ping périodique pour maintenir la connexion
  useEffect(() => {
    if (connectionStatus === 'connected') {
      const pingInterval = setInterval(sendPing, 30000); // Ping toutes les 30 secondes
      return () => clearInterval(pingInterval);
    }
  }, [connectionStatus, sendPing]);

  const getConnectionStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'text-green-500';
      case 'connecting': return 'text-yellow-500';
      case 'error': return 'text-red-500';
      default: return 'text-gray-500';
    }
  };

  const getConnectionStatusText = () => {
    switch (connectionStatus) {
      case 'connected': return 'Connecté';
      case 'connecting': return 'Connexion...';
      case 'error': return 'Erreur';
      default: return 'Déconnecté';
    }
  };

  const formatPrice = (price: number) => {
    return price.toFixed(2);
  };

  const formatChange = (change: number, changePercent: number) => {
    const sign = change >= 0 ? '+' : '';
    const color = change >= 0 ? 'text-green-500' : 'text-red-500';
    return (
      <span className={color}>
        {sign}{formatPrice(change)} ({sign}{changePercent.toFixed(2)}%)
      </span>
    );
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold">Données de Marché Temps Réel</h3>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${connectionStatus === 'connected' ? 'bg-green-500' : connectionStatus === 'connecting' ? 'bg-yellow-500' : 'bg-red-500'}`}></div>
            <span className={`text-sm ${getConnectionStatusColor()}`}>
              {getConnectionStatusText()}
            </span>
          </div>
          <div className="flex space-x-2">
            {connectionStatus === 'disconnected' && (
              <button
                onClick={connectWebSocket}
                className="px-3 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600"
              >
                Connecter
              </button>
            )}
            {connectionStatus === 'connected' && (
              <button
                onClick={disconnectWebSocket}
                className="px-3 py-1 bg-red-500 text-white rounded text-sm hover:bg-red-600"
              >
                Déconnecter
              </button>
            )}
          </div>
        </div>
      </div>

      {lastUpdate && (
        <p className="text-sm text-gray-500 mb-4">
          Dernière mise à jour: {new Date(lastUpdate).toLocaleTimeString()}
        </p>
      )}

      {Object.keys(marketData).length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          {connectionStatus === 'connected' 
            ? 'En attente de données de marché...' 
            : 'Connectez-vous pour recevoir les données temps réel'
          }
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead>
              <tr className="bg-gray-50">
                <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">Symbole</th>
                <th className="px-4 py-2 text-right text-sm font-medium text-gray-700">Prix</th>
                <th className="px-4 py-2 text-right text-sm font-medium text-gray-700">Variation</th>
                <th className="px-4 py-2 text-right text-sm font-medium text-gray-700">Volume</th>
                <th className="px-4 py-2 text-center text-sm font-medium text-gray-700">Statut</th>
                <th className="px-4 py-2 text-center text-sm font-medium text-gray-700">Source</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {Object.entries(marketData).map(([symbol, data]) => (
                <tr key={symbol} className="hover:bg-gray-50">
                  <td className="px-4 py-2 font-medium text-gray-900">{symbol}</td>
                  <td className="px-4 py-2 text-right font-mono">${formatPrice(data.price)}</td>
                  <td className="px-4 py-2 text-right font-mono">
                    {formatChange(data.change, data.change_percent)}
                  </td>
                  <td className="px-4 py-2 text-right text-sm text-gray-600">
                    {data.volume.toLocaleString()}
                  </td>
                  <td className="px-4 py-2 text-center">
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      data.market_status === 'open' ? 'bg-green-100 text-green-800' :
                      data.market_status === 'closed' ? 'bg-red-100 text-red-800' :
                      'bg-yellow-100 text-yellow-800'
                    }`}>
                      {data.market_status}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-center text-sm text-gray-500">
                    {data.source}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default RealTimeMarketData;