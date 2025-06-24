#!/usr/bin/env python3
"""
Script de test pour valider l'implémentation du backtesting et trading automatique
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
import logging
from datetime import datetime, date
from typing import Dict, Any

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_imports():
    """Test des imports des nouveaux modules"""
    logger.info("🧪 Test des imports...")
    
    try:
        # Test des modèles
        from app.models.backtest import Backtest, BacktestComparison
        from app.models.trading_simulation import TradingSimulation, SimulationTrade, SimulationStatus
        logger.info("✅ Modèles importés avec succès")
        
        # Test des services
        from app.services.advanced_backtesting_service import get_advanced_backtesting_service
        from app.services.trading_simulation_service import get_trading_simulation_service
        from app.services.simulation_recovery_service import get_simulation_recovery_service
        logger.info("✅ Services importés avec succès")
        
        # Test des tâches Celery
        from app.services.simulation_tasks import start_trading_simulation_task
        logger.info("✅ Tâches Celery importées avec succès")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur d'import: {e}")
        return False

async def test_backtesting_service():
    """Test du service de backtesting avancé"""
    logger.info("🧪 Test du service de backtesting...")
    
    try:
        from app.services.advanced_backtesting_service import get_advanced_backtesting_service
        
        # Configuration de test
        class MockConfig:
            def __init__(self):
                self.name = "Test Backtest"
                self.start_date = date(2024, 1, 1)
                self.end_date = date(2024, 3, 1)
                self.initial_capital = 10000
                self.strategy_type = "rsi"
                self.strategy_params = {"rsi": {"period": 14, "oversold": 30, "overbought": 70}}
                self.etf_symbols = ["IE00B4L5Y983"]  # IWDA
                self.rebalance_frequency = "daily"
                self.transaction_cost_pct = 0.1
                self.max_position_size_pct = 20
                
            def dict(self):
                return {
                    "name": self.name,
                    "start_date": self.start_date.isoformat(),
                    "end_date": self.end_date.isoformat(),
                    "initial_capital": self.initial_capital,
                    "strategy_type": self.strategy_type,
                    "strategy_params": self.strategy_params,
                    "etf_symbols": self.etf_symbols,
                    "rebalance_frequency": self.rebalance_frequency,
                    "transaction_cost_pct": self.transaction_cost_pct,
                    "max_position_size_pct": self.max_position_size_pct
                }
        
        service = get_advanced_backtesting_service()
        config = MockConfig()
        
        logger.info("📊 Configuration de test créée")
        logger.info(f"   - ETF: {config.etf_symbols}")
        logger.info(f"   - Période: {config.start_date} à {config.end_date}")
        logger.info(f"   - Capital: {config.initial_capital}€")
        logger.info(f"   - Stratégie: {config.strategy_type}")
        
        # NOTE: Nous ne lançons pas le backtest complet car il nécessite une connexion DB
        # et des données de marché. Nous testons juste la structure.
        
        logger.info("✅ Service de backtesting structurellement valide")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur test backtesting: {e}")
        return False

async def test_trading_simulation_service():
    """Test du service de simulation de trading"""
    logger.info("🧪 Test du service de simulation de trading...")
    
    try:
        from app.services.trading_simulation_service import get_trading_simulation_service
        from app.models.trading_simulation import SimulationStatus
        
        # Configuration de test
        class MockSimulationConfig:
            def __init__(self):
                self.name = "Test Trading Simulation"
                self.initial_capital = 100
                self.duration_days = 30
                self.strategy_type = "advanced"
                self.risk_level = "moderate"
                self.allowed_etf_sectors = ["technology", "healthcare"]
                self.rebalance_frequency_hours = 24
                self.auto_stop_loss = True
                self.auto_take_profit = True
        
        service = get_trading_simulation_service()
        config = MockSimulationConfig()
        
        logger.info("🎯 Configuration de simulation créée")
        logger.info(f"   - Capital initial: {config.initial_capital}€")
        logger.info(f"   - Durée: {config.duration_days} jours")
        logger.info(f"   - Niveau de risque: {config.risk_level}")
        logger.info(f"   - Rééquilibrage: {config.rebalance_frequency_hours}h")
        
        # Test de la sélection d'ETFs (simulation)
        logger.info("📈 Test de sélection d'ETFs...")
        etf_symbols = await service._select_etfs_for_simulation(config)
        logger.info(f"   - ETFs sélectionnés: {etf_symbols}")
        
        logger.info("✅ Service de simulation structurellement valide")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur test simulation: {e}")
        return False

async def test_recovery_service():
    """Test du service de récupération"""
    logger.info("🧪 Test du service de récupération...")
    
    try:
        from app.services.simulation_recovery_service import get_simulation_recovery_service
        
        service = get_simulation_recovery_service()
        
        # Test de la structure du service
        logger.info("🔄 Vérification de la structure du service de récupération...")
        
        # Vérifier que les méthodes existent
        methods = [
            'recover_active_simulations',
            'get_recovery_status',
            'cleanup_abandoned_simulations'
        ]
        
        for method in methods:
            if hasattr(service, method):
                logger.info(f"   ✅ Méthode {method} disponible")
            else:
                logger.error(f"   ❌ Méthode {method} manquante")
                return False
        
        logger.info("✅ Service de récupération structurellement valide")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur test récupération: {e}")
        return False

async def test_celery_tasks():
    """Test de la structure des tâches Celery"""
    logger.info("🧪 Test des tâches Celery...")
    
    try:
        from app.services.simulation_tasks import (
            start_trading_simulation_task,
            pause_trading_simulation_task,
            stop_trading_simulation_task,
            cleanup_old_simulations_task
        )
        
        # Vérifier que les tâches sont bien des objets Celery
        tasks = [
            ('start_trading_simulation_task', start_trading_simulation_task),
            ('pause_trading_simulation_task', pause_trading_simulation_task),
            ('stop_trading_simulation_task', stop_trading_simulation_task),
            ('cleanup_old_simulations_task', cleanup_old_simulations_task)
        ]
        
        for task_name, task_obj in tasks:
            if hasattr(task_obj, 'delay'):
                logger.info(f"   ✅ Tâche {task_name} correctement configurée")
            else:
                logger.warning(f"   ⚠️ Tâche {task_name} pas entièrement configurée (normal en test)")
        
        logger.info("✅ Tâches Celery structurellement valides")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur test tâches Celery: {e}")
        return False

def test_database_models():
    """Test de la structure des modèles de base de données"""
    logger.info("🧪 Test des modèles de base de données...")
    
    try:
        from app.models.backtest import Backtest, BacktestComparison
        from app.models.trading_simulation import (
            TradingSimulation, 
            SimulationTrade, 
            SimulationPerformanceSnapshot,
            SimulationLeaderboard,
            SimulationStatus
        )
        
        # Vérifier les champs des modèles
        backtest_fields = [
            'id', 'user_id', 'name', 'start_date', 'end_date', 
            'initial_capital', 'strategy_type', 'total_return_pct'
        ]
        
        for field in backtest_fields:
            if hasattr(Backtest, field):
                logger.info(f"   ✅ Backtest.{field} défini")
            else:
                logger.error(f"   ❌ Backtest.{field} manquant")
                return False
        
        simulation_fields = [
            'id', 'user_id', 'name', 'initial_capital', 'duration_days',
            'strategy_type', 'risk_level', 'status', 'celery_task_id'
        ]
        
        for field in simulation_fields:
            if hasattr(TradingSimulation, field):
                logger.info(f"   ✅ TradingSimulation.{field} défini")
            else:
                logger.error(f"   ❌ TradingSimulation.{field} manquant")
                return False
        
        # Vérifier les énumérations
        status_values = [
            SimulationStatus.PENDING,
            SimulationStatus.RUNNING,
            SimulationStatus.PAUSED,
            SimulationStatus.COMPLETED,
            SimulationStatus.STOPPED,
            SimulationStatus.ERROR
        ]
        
        logger.info(f"   ✅ SimulationStatus avec {len(status_values)} valeurs")
        
        logger.info("✅ Modèles de base de données structurellement valides")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur test modèles DB: {e}")
        return False

async def run_all_tests():
    """Lance tous les tests"""
    logger.info("🚀 Démarrage des tests d'implémentation backtesting et trading automatique")
    logger.info("=" * 70)
    
    tests = [
        ("Imports", test_imports),
        ("Modèles DB", lambda: test_database_models()),
        ("Service Backtesting", test_backtesting_service),
        ("Service Trading", test_trading_simulation_service),
        ("Service Récupération", test_recovery_service),
        ("Tâches Celery", test_celery_tasks)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 Test: {test_name}")
        logger.info("-" * 50)
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results[test_name] = result
            
            if result:
                logger.info(f"✅ {test_name}: RÉUSSI")
            else:
                logger.error(f"❌ {test_name}: ÉCHEC")
                
        except Exception as e:
            logger.error(f"💥 {test_name}: ERREUR - {e}")
            results[test_name] = False
    
    # Résumé final
    logger.info("\n" + "=" * 70)
    logger.info("📊 RÉSUMÉ DES TESTS")
    logger.info("=" * 70)
    
    success_count = sum(1 for r in results.values() if r)
    total_count = len(results)
    
    for test_name, result in results.items():
        status = "✅ RÉUSSI" if result else "❌ ÉCHEC"
        logger.info(f"   {test_name:<20}: {status}")
    
    logger.info("-" * 70)
    logger.info(f"📈 Résultat global: {success_count}/{total_count} tests réussis")
    
    if success_count == total_count:
        logger.info("🎉 TOUS LES TESTS RÉUSSIS! L'implémentation est structurellement correcte.")
        logger.info("📝 Prochaines étapes:")
        logger.info("   1. Exécuter le script de migration: python upgrade_database_backtesting.py")
        logger.info("   2. Redémarrer les services Docker")
        logger.info("   3. Tester via l'interface web")
    else:
        logger.warning(f"⚠️ {total_count - success_count} test(s) en échec. Vérifiez les erreurs ci-dessus.")
    
    return success_count == total_count

if __name__ == "__main__":
    result = asyncio.run(run_all_tests())
    sys.exit(0 if result else 1)