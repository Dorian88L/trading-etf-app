"""
Tests critiques pour le générateur de signaux
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import pandas as pd

from app.services.signal_generator import SignalGenerator
from app.models.signal import SignalType


class TestSignalGenerator:
    """Tests pour le générateur de signaux"""
    
    def setup_method(self):
        """Setup avant chaque test"""
        self.signal_generator = SignalGenerator()
    
    def test_breakout_algorithm_buy_signal(self):
        """Test l'algorithme breakout pour signal d'achat"""
        # Données de test - cassure de résistance
        price_data = pd.DataFrame({
            'close': [100, 101, 102, 103, 104, 106, 108],  # Breakout upward
            'high': [101, 102, 103, 104, 105, 107, 109],
            'low': [99, 100, 101, 102, 103, 105, 107],
            'volume': [1000, 1100, 1200, 1300, 1400, 2000, 2500]  # Volume croissant
        })
        
        result = self.signal_generator._breakout_algorithm('TEST', price_data)
        
        assert result['signal'] == SignalType.BUY
        assert result['confidence'] > 0.6
        assert 'breakout' in result['reason'].lower()
    
    def test_mean_reversion_sell_signal(self):
        """Test l'algorithme mean reversion pour signal de vente"""
        # Données de test - prix très au-dessus de la moyenne
        price_data = pd.DataFrame({
            'close': [100, 101, 102, 120, 125, 130, 135],  # Surévalué
            'high': [101, 102, 103, 122, 127, 132, 137],
            'low': [99, 100, 101, 118, 123, 128, 133],
            'volume': [1000, 1000, 1000, 3000, 2000, 1500, 1000]  # Volume décroissant
        })
        
        result = self.signal_generator._mean_reversion_algorithm('TEST', price_data)
        
        assert result['signal'] == SignalType.SELL
        assert result['confidence'] > 0.5
        assert 'reversion' in result['reason'].lower()
    
    def test_momentum_hold_signal(self):
        """Test l'algorithme momentum pour signal hold"""
        # Données de test - tendance stable
        price_data = pd.DataFrame({
            'close': [100, 100.5, 101, 101.5, 102, 102.2, 102.5],  # Tendance légère
            'high': [101, 101.5, 102, 102.5, 103, 103.2, 103.5],
            'low': [99, 99.5, 100, 100.5, 101, 101.2, 101.5],
            'volume': [1000, 1000, 1000, 1000, 1000, 1000, 1000]  # Volume stable
        })
        
        result = self.signal_generator._momentum_algorithm('TEST', price_data)
        
        assert result['signal'] in [SignalType.HOLD, SignalType.WAIT]
        assert result['confidence'] >= 0
    
    @patch('app.services.signal_generator.SignalGenerator._get_price_data')
    def test_generate_signal_integration(self, mock_get_price_data):
        """Test d'intégration de génération de signal"""
        # Mock des données de prix
        mock_price_data = pd.DataFrame({
            'close': [100, 101, 102, 103, 104, 106, 108],
            'high': [101, 102, 103, 104, 105, 107, 109],
            'low': [99, 100, 101, 102, 103, 105, 107],
            'volume': [1000, 1100, 1200, 1300, 1400, 2000, 2500]
        })
        mock_get_price_data.return_value = mock_price_data
        
        signal = self.signal_generator.generate_signal('TEST.PA')
        
        assert signal is not None
        assert hasattr(signal, 'signal_type')
        assert hasattr(signal, 'confidence')
        assert hasattr(signal, 'price_target')
        assert hasattr(signal, 'stop_loss')
        assert 0 <= signal.confidence <= 1
    
    def test_calculate_price_targets(self):
        """Test du calcul des prix cibles"""
        current_price = 100.0
        signal_type = SignalType.BUY
        
        targets = self.signal_generator._calculate_price_targets(
            current_price, signal_type
        )
        
        assert 'price_target' in targets
        assert 'stop_loss' in targets
        assert targets['price_target'] > current_price  # Pour un signal BUY
        assert targets['stop_loss'] < current_price     # Stop loss en dessous
    
    def test_signal_confidence_bounds(self):
        """Test que la confidence est toujours entre 0 et 1"""
        # Test avec différents scénarios
        test_cases = [
            pd.DataFrame({'close': [100], 'high': [100], 'low': [100], 'volume': [1000]}),
            pd.DataFrame({'close': [100, 150], 'high': [100, 150], 'low': [100, 150], 'volume': [1000, 2000]}),
            pd.DataFrame({'close': [100, 50], 'high': [100, 50], 'low': [100, 50], 'volume': [1000, 500]})
        ]
        
        for price_data in test_cases:
            result = self.signal_generator._breakout_algorithm('TEST', price_data)
            assert 0 <= result['confidence'] <= 1
            
            result = self.signal_generator._mean_reversion_algorithm('TEST', price_data)
            assert 0 <= result['confidence'] <= 1
            
            result = self.signal_generator._momentum_algorithm('TEST', price_data)
            assert 0 <= result['confidence'] <= 1


if __name__ == '__main__':
    pytest.main([__file__])