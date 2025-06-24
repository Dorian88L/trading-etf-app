#!/usr/bin/env python3
"""
Script de mise à jour du schéma de base de données pour le backtesting et trading automatique
Ajoute les nouvelles tables pour les backtests et simulations de trading
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text, inspect
from app.core.database import SessionLocal, engine
from app.models.backtest import Backtest, BacktestComparison
from app.models.trading_simulation import (
    TradingSimulation, 
    SimulationTrade, 
    SimulationPerformanceSnapshot, 
    SimulationLeaderboard
)
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_table_exists(table_name: str) -> bool:
    """Vérifie si une table existe"""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()

def create_backtesting_tables(session):
    """Crée les tables pour le backtesting"""
    logger.info("🏗️  Création des tables de backtesting...")
    
    # Table Backtest
    if not check_table_exists('backtests'):
        try:
            Backtest.__table__.create(engine)
            logger.info("✓ Table backtests créée")
        except Exception as e:
            logger.warning(f"⚠️  Erreur création backtests: {e}")
    else:
        logger.info("→ Table backtests existe déjà")
    
    # Table BacktestComparison
    if not check_table_exists('backtest_comparisons'):
        try:
            BacktestComparison.__table__.create(engine)
            logger.info("✓ Table backtest_comparisons créée")
        except Exception as e:
            logger.warning(f"⚠️  Erreur création backtest_comparisons: {e}")
    else:
        logger.info("→ Table backtest_comparisons existe déjà")

def create_trading_simulation_tables(session):
    """Crée les tables pour les simulations de trading"""
    logger.info("🏗️  Création des tables de simulation de trading...")
    
    # Table TradingSimulation
    if not check_table_exists('trading_simulations'):
        try:
            TradingSimulation.__table__.create(engine)
            logger.info("✓ Table trading_simulations créée")
        except Exception as e:
            logger.warning(f"⚠️  Erreur création trading_simulations: {e}")
    else:
        logger.info("→ Table trading_simulations existe déjà")
    
    # Table SimulationTrade
    if not check_table_exists('simulation_trades'):
        try:
            SimulationTrade.__table__.create(engine)
            logger.info("✓ Table simulation_trades créée")
        except Exception as e:
            logger.warning(f"⚠️  Erreur création simulation_trades: {e}")
    else:
        logger.info("→ Table simulation_trades existe déjà")
    
    # Table SimulationPerformanceSnapshot
    if not check_table_exists('simulation_performance_snapshots'):
        try:
            SimulationPerformanceSnapshot.__table__.create(engine)
            logger.info("✓ Table simulation_performance_snapshots créée")
        except Exception as e:
            logger.warning(f"⚠️  Erreur création simulation_performance_snapshots: {e}")
    else:
        logger.info("→ Table simulation_performance_snapshots existe déjà")
    
    # Table SimulationLeaderboard
    if not check_table_exists('simulation_leaderboard'):
        try:
            SimulationLeaderboard.__table__.create(engine)
            logger.info("✓ Table simulation_leaderboard créée")
        except Exception as e:
            logger.warning(f"⚠️  Erreur création simulation_leaderboard: {e}")
    else:
        logger.info("→ Table simulation_leaderboard existe déjà")

def create_indexes(session):
    """Crée les index pour optimiser les performances"""
    logger.info("📊 Création des index d'optimisation...")
    
    indexes = [
        # Index pour les backtests
        "CREATE INDEX IF NOT EXISTS idx_backtests_user_id ON backtests(user_id, created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_backtests_strategy ON backtests(strategy_type, created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_backtests_performance ON backtests(total_return_pct DESC, sharpe_ratio DESC)",
        
        # Index pour les simulations de trading
        "CREATE INDEX IF NOT EXISTS idx_trading_simulations_user_id ON trading_simulations(user_id, status, created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_trading_simulations_status ON trading_simulations(status, next_rebalance)",
        "CREATE INDEX IF NOT EXISTS idx_trading_simulations_celery_task ON trading_simulations(celery_task_id)",
        "CREATE INDEX IF NOT EXISTS idx_trading_simulations_performance ON trading_simulations(total_return_pct DESC, created_at DESC)",
        
        # Index pour les trades de simulation
        "CREATE INDEX IF NOT EXISTS idx_simulation_trades_simulation_id ON simulation_trades(simulation_id, timestamp DESC)",
        "CREATE INDEX IF NOT EXISTS idx_simulation_trades_symbol ON simulation_trades(symbol, timestamp DESC)",
        
        # Index pour les snapshots de performance
        "CREATE INDEX IF NOT EXISTS idx_simulation_snapshots_simulation_id ON simulation_performance_snapshots(simulation_id, timestamp DESC)",
        
        # Index pour le leaderboard
        "CREATE INDEX IF NOT EXISTS idx_simulation_leaderboard_period ON simulation_leaderboard(period, rank)",
        "CREATE INDEX IF NOT EXISTS idx_simulation_leaderboard_performance ON simulation_leaderboard(period, return_pct DESC)",
    ]
    
    for index_sql in indexes:
        try:
            session.execute(text(index_sql))
            session.commit()
            index_name = index_sql.split('idx_')[1].split(' ')[0]
            logger.info(f"✓ Index créé: {index_name}")
        except Exception as e:
            logger.warning(f"⚠️  Erreur création index: {e}")
            session.rollback()

def create_constraints(session):
    """Crée les contraintes de base de données"""
    logger.info("🔐 Création des contraintes...")
    
    constraints = [
        # Contraintes pour les backtests
        "ALTER TABLE backtests ADD CONSTRAINT chk_backtest_dates CHECK (end_date > start_date)",
        "ALTER TABLE backtests ADD CONSTRAINT chk_backtest_capital CHECK (initial_capital > 0)",
        "ALTER TABLE backtests ADD CONSTRAINT chk_backtest_status CHECK (status IN ('completed', 'failed', 'running'))",
        
        # Contraintes pour les simulations
        "ALTER TABLE trading_simulations ADD CONSTRAINT chk_simulation_capital CHECK (initial_capital > 0)",
        "ALTER TABLE trading_simulations ADD CONSTRAINT chk_simulation_duration CHECK (duration_days > 0)",
        "ALTER TABLE trading_simulations ADD CONSTRAINT chk_simulation_risk_level CHECK (risk_level IN ('conservative', 'moderate', 'aggressive'))",
        
        # Contraintes pour les trades
        "ALTER TABLE simulation_trades ADD CONSTRAINT chk_trade_quantity CHECK (quantity > 0)",
        "ALTER TABLE simulation_trades ADD CONSTRAINT chk_trade_price CHECK (price > 0)",
        "ALTER TABLE simulation_trades ADD CONSTRAINT chk_trade_action CHECK (action IN ('BUY', 'SELL'))",
    ]
    
    for constraint_sql in constraints:
        try:
            session.execute(text(constraint_sql))
            session.commit()
            constraint_name = constraint_sql.split('ADD CONSTRAINT ')[1].split(' ')[0]
            logger.info(f"✓ Contrainte créée: {constraint_name}")
        except Exception as e:
            logger.warning(f"⚠️  Contrainte déjà existante ou erreur: {e}")
            session.rollback()

def create_views(session):
    """Crée des vues utiles pour les requêtes"""
    logger.info("👁️  Création des vues...")
    
    views = [
        # Vue pour les statistiques de backtesting par utilisateur
        """
        CREATE OR REPLACE VIEW user_backtest_stats AS
        SELECT 
            user_id,
            COUNT(*) as total_backtests,
            AVG(total_return_pct) as avg_return_pct,
            MAX(total_return_pct) as best_return_pct,
            AVG(sharpe_ratio) as avg_sharpe_ratio,
            COUNT(CASE WHEN total_return_pct > 0 THEN 1 END) as profitable_backtests
        FROM backtests 
        WHERE status = 'completed'
        GROUP BY user_id
        """,
        
        # Vue pour les simulations actives
        """
        CREATE OR REPLACE VIEW active_simulations_summary AS
        SELECT 
            ts.id,
            ts.user_id,
            ts.name,
            ts.status,
            ts.current_value,
            ts.total_return_pct,
            ts.days_remaining,
            ts.next_rebalance,
            COUNT(st.id) as total_trades,
            ts.created_at
        FROM trading_simulations ts
        LEFT JOIN simulation_trades st ON ts.id = st.simulation_id
        WHERE ts.status IN ('running', 'paused')
        GROUP BY ts.id, ts.user_id, ts.name, ts.status, ts.current_value, 
                 ts.total_return_pct, ts.days_remaining, ts.next_rebalance, ts.created_at
        """,
        
        # Vue pour le leaderboard en temps réel
        """
        CREATE OR REPLACE VIEW current_leaderboard AS
        SELECT 
            ts.id,
            ts.user_id,
            ts.name,
            ts.total_return_pct,
            ts.risk_level,
            ts.duration_days - ts.days_remaining as elapsed_days,
            ts.current_value,
            ts.initial_capital,
            ROW_NUMBER() OVER (ORDER BY ts.total_return_pct DESC) as rank
        FROM trading_simulations ts
        WHERE ts.status IN ('running', 'completed')
        AND ts.total_return_pct IS NOT NULL
        """
    ]
    
    for view_sql in views:
        try:
            session.execute(text(view_sql))
            session.commit()
            view_name = view_sql.split('VIEW ')[1].split(' ')[0]
            logger.info(f"✓ Vue créée: {view_name}")
        except Exception as e:
            logger.warning(f"⚠️  Erreur création vue: {e}")
            session.rollback()

def main():
    """Fonction principale de migration"""
    logger.info("🚀 Début de la création des tables de backtesting et trading automatique")
    
    session = SessionLocal()
    
    try:
        # 1. Créer les tables de backtesting
        create_backtesting_tables(session)
        
        # 2. Créer les tables de simulation de trading
        create_trading_simulation_tables(session)
        
        # 3. Créer les index d'optimisation
        create_indexes(session)
        
        # 4. Créer les contraintes
        create_constraints(session)
        
        # 5. Créer les vues utiles
        create_views(session)
        
        logger.info("✅ Création des tables de backtesting et trading terminée avec succès!")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la création: {e}")
        session.rollback()
        return 1
        
    finally:
        session.close()
    
    return 0

if __name__ == "__main__":
    exit(main())