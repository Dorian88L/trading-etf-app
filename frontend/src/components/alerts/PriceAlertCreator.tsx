import React, { useState, useEffect } from 'react';
import { alertsAPI } from '../../services/api';

interface PriceAlertCreatorProps {
  isOpen: boolean;
  onClose: () => void;
  onAlertCreated: () => void;
  etfSymbol?: string;
  currentPrice?: number;
}

interface CreatePriceAlertData {
  etf_symbol: string;
  target_price: number;
  alert_type: 'above' | 'below';
  message?: string;
  is_active: boolean;
}

const PriceAlertCreator: React.FC<PriceAlertCreatorProps> = ({
  isOpen,
  onClose,
  onAlertCreated,
  etfSymbol = '',
  currentPrice = 0
}) => {
  const [formData, setFormData] = useState<CreatePriceAlertData>({
    etf_symbol: etfSymbol,
    target_price: currentPrice,
    alert_type: 'above',
    message: '',
    is_active: true
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (etfSymbol) {
      setFormData(prev => ({ ...prev, etf_symbol: etfSymbol }));
    }
    if (currentPrice) {
      setFormData(prev => ({ ...prev, target_price: currentPrice }));
    }
  }, [etfSymbol, currentPrice]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await alertsAPI.createPriceAlert(formData);
      onAlertCreated();
      onClose();
      setFormData({
        etf_symbol: '',
        target_price: 0,
        alert_type: 'above',
        message: '',
        is_active: true
      });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur lors de la création de l\'alerte');
    } finally {
      setLoading(false);
    }
  };

  const handlePriceChange = (value: string) => {
    const price = parseFloat(value);
    if (!isNaN(price)) {
      setFormData(prev => ({ ...prev, target_price: price }));
    }
  };

  const suggestPrice = (percentage: number) => {
    if (currentPrice > 0) {
      const suggestedPrice = currentPrice * (1 + percentage / 100);
      setFormData(prev => ({ ...prev, target_price: Math.round(suggestedPrice * 100) / 100 }));
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full max-h-screen overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold text-gray-900">💰 Créer une alerte de prix</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-2xl"
            >
              ✕
            </button>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-red-600 text-sm">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* ETF Symbol */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Symbole ETF
              </label>
              <input
                type="text"
                value={formData.etf_symbol}
                onChange={(e) => setFormData(prev => ({ ...prev, etf_symbol: e.target.value.toUpperCase() }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                placeholder="Ex: SPY, QQQ, VTI..."
                required
              />
            </div>

            {/* Prix actuel info */}
            {currentPrice > 0 && (
              <div className="p-3 bg-blue-50 rounded-md">
                <p className="text-sm text-blue-800">
                  📊 Prix actuel: <span className="font-semibold">{currentPrice.toFixed(2)} €</span>
                </p>
              </div>
            )}

            {/* Type d'alerte */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Type d'alerte
              </label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setFormData(prev => ({ ...prev, alert_type: 'above' }))}
                  className={`p-3 rounded-md border text-sm font-medium ${
                    formData.alert_type === 'above'
                      ? 'bg-green-100 border-green-300 text-green-700'
                      : 'bg-gray-50 border-gray-300 text-gray-700'
                  }`}
                >
                  📈 Au-dessus de
                </button>
                <button
                  type="button"
                  onClick={() => setFormData(prev => ({ ...prev, alert_type: 'below' }))}
                  className={`p-3 rounded-md border text-sm font-medium ${
                    formData.alert_type === 'below'
                      ? 'bg-red-100 border-red-300 text-red-700'
                      : 'bg-gray-50 border-gray-300 text-gray-700'
                  }`}
                >
                  📉 En-dessous de
                </button>
              </div>
            </div>

            {/* Prix cible */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Prix cible (€)
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={formData.target_price}
                onChange={(e) => handlePriceChange(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                required
              />
              
              {/* Suggestions de prix */}
              {currentPrice > 0 && (
                <div className="mt-2">
                  <p className="text-xs text-gray-500 mb-1">Suggestions rapides:</p>
                  <div className="flex gap-1 flex-wrap">
                    <button
                      type="button"
                      onClick={() => suggestPrice(-10)}
                      className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200"
                    >
                      -10%
                    </button>
                    <button
                      type="button"
                      onClick={() => suggestPrice(-5)}
                      className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200"
                    >
                      -5%
                    </button>
                    <button
                      type="button"
                      onClick={() => suggestPrice(5)}
                      className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded hover:bg-green-200"
                    >
                      +5%
                    </button>
                    <button
                      type="button"
                      onClick={() => suggestPrice(10)}
                      className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded hover:bg-green-200"
                    >
                      +10%
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Message personnalisé */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Message personnalisé (optionnel)
              </label>
              <textarea
                value={formData.message}
                onChange={(e) => setFormData(prev => ({ ...prev, message: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                rows={3}
                placeholder="Message qui sera affiché lors du déclenchement de l'alerte..."
              />
            </div>

            {/* Statut actif */}
            <div className="flex items-center">
              <input
                type="checkbox"
                id="is_active"
                checked={formData.is_active}
                onChange={(e) => setFormData(prev => ({ ...prev, is_active: e.target.checked }))}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="is_active" className="ml-2 block text-sm text-gray-700">
                Alerte active
              </label>
            </div>

            {/* Boutons */}
            <div className="flex gap-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
              >
                Annuler
              </button>
              <button
                type="submit"
                disabled={loading}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? '⏳ Création...' : '💰 Créer l\'alerte'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default PriceAlertCreator;