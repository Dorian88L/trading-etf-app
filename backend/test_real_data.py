#!/usr/bin/env python3
"""
Tests de validation pour les données temps réel et les performances
"""

import time
import logging
from typing import List, Dict, Any

from app.services.real_market_data import real_market_service
from app.core.cache import cache, CacheManager

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealDataTester:
    """Classe pour tester les données temps réel et les performances"""
    
    def __init__(self):
        self.market_service = real_market_service
        self.test_symbols = ['IWDA.AS', 'VWCE.DE', 'CSPX.L', 'VUAA.DE']
        self.results = []
    
    def test_single_etf_data(self, symbol: str) -> Dict[str, Any]:
        """Test de récupération de données pour un ETF"""
        start_time = time.time()
        
        try:
            data = self.market_service.get_single_etf_data(symbol)
            end_time = time.time()
            
            if data:
                result = {
                    'symbol': symbol,
                    'status': 'SUCCESS',
                    'response_time_ms': round((end_time - start_time) * 1000, 2),
                    'current_price': data.current_price,
                    'change_percent': data.change_percent,
                    'volume': data.volume,
                    'currency': data.currency,
                    'last_update': str(data.last_update),
                    'data_quality': self._evaluate_data_quality(data)
                }
            else:
                result = {
                    'symbol': symbol,
                    'status': 'NO_DATA',
                    'response_time_ms': round((end_time - start_time) * 1000, 2),
                    'error': 'Aucune donnée retournée'
                }
                
        except Exception as e:
            end_time = time.time()
            result = {
                'symbol': symbol,
                'status': 'ERROR',
                'response_time_ms': round((end_time - start_time) * 1000, 2),
                'error': str(e)
            }
        
        return result
    
    def _evaluate_data_quality(self, data) -> str:
        """Évalue la qualité des données"""
        issues = []
        
        if data.current_price <= 0:
            issues.append("Prix invalide")
        
        if data.volume < 0:
            issues.append("Volume invalide")
        
        if abs(data.change_percent) > 50:
            issues.append("Variation suspecte")
        
        if not data.currency or data.currency == 'N/A':
            issues.append("Devise manquante")
        
        if issues:
            return f"PROBLEMES: {', '.join(issues)}"
        
        return "BONNE"
    
    def run_full_test_suite(self) -> Dict[str, Any]:
        """Exécute la suite complète de tests"""
        logger.info("🚀 Démarrage de la suite de tests complète...")
        
        # Test des ETFs individuels
        etf_results = []
        for symbol in self.test_symbols:
            logger.info(f"Test de {symbol}...")
            result = self.test_single_etf_data(symbol)
            etf_results.append(result)
            time.sleep(0.5)  # Délai pour éviter les limites de taux
        
        # Statistiques globales
        successful_etfs = [r for r in etf_results if r['status'] == 'SUCCESS']
        avg_response_time = sum(r['response_time_ms'] for r in successful_etfs) / len(successful_etfs) if successful_etfs else 0
        
        summary = {
            'test_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_etfs_tested': len(etf_results),
            'successful_etfs': len(successful_etfs),
            'success_rate': round((len(successful_etfs) / len(etf_results)) * 100, 1) if etf_results else 0,
            'avg_response_time_ms': round(avg_response_time, 2),
            'detailed_results': etf_results
        }
        
        return summary

def main():
    """Fonction principale pour exécuter les tests"""
    tester = RealDataTester()
    
    try:
        results = tester.run_full_test_suite()
        
        print("\n" + "="*60)
        print("📊 RÉSULTATS DES TESTS")
        print("="*60)
        
        print(f"✅ ETFs testés: {results['total_etfs_tested']}")
        print(f"✅ Succès: {results['successful_etfs']}/{results['total_etfs_tested']} ({results['success_rate']}%)")
        print(f"⏱️  Temps de réponse moyen: {results['avg_response_time_ms']}ms")
        
        print(f"\n📝 Détails par ETF:")
        for result in results['detailed_results']:
            status_icon = "✅" if result['status'] == 'SUCCESS' else "❌"
            print(f"   {status_icon} {result['symbol']}: {result['response_time_ms']}ms - {result['status']}")
            
            if result['status'] == 'SUCCESS':
                print(f"      Prix: {result.get('current_price', 'N/A')} {result.get('currency', '')}")
                print(f"      Variation: {result.get('change_percent', 0):.2f}%")
                print(f"      Qualité: {result.get('data_quality', 'N/A')}")
        
        # Vérification finale
        print(f"\n🎯 STATUT GLOBAL:")
        if results['success_rate'] >= 80 and results['avg_response_time_ms'] < 2000:
            print("   🟢 EXCELLENT - Application prête pour la production")
        elif results['success_rate'] >= 60:
            print("   🟡 CORRECT - Quelques améliorations recommandées")
        else:
            print("   🔴 PROBLÉMATIQUE - Corrections nécessaires")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Erreur lors des tests: {e}")
        return None

if __name__ == "__main__":
    main()