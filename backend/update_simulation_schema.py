#!/usr/bin/env python3
"""
Script pour mettre à jour le schéma de base de données des simulations trading.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text, inspect
from app.core.database import engine, SessionLocal
from app.models.trading_simulation import TradingSimulation, SimulationTrade, SimulationPerformanceSnapshot
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_table_exists(table_name):
    """Vérifie si une table existe."""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()

def check_column_exists(table_name, column_name):
    """Vérifie si une colonne existe dans une table."""
    inspector = inspect(engine)
    if not check_table_exists(table_name):
        return False
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def update_database_schema():
    """Met à jour le schéma de base de données pour les simulations."""
    db = SessionLocal()
    
    try:
        logger.info("🔄 Mise à jour du schéma de base de données pour les simulations...")
        
        # 1. Vérifier si les tables existent, sinon les créer
        if not check_table_exists('trading_simulations'):
            logger.info("📝 Création de la table trading_simulations...")
            TradingSimulation.__table__.create(bind=engine, checkfirst=True)
        
        if not check_table_exists('simulation_trades'):
            logger.info("📝 Création de la table simulation_trades...")
            SimulationTrade.__table__.create(bind=engine, checkfirst=True)
        
        if not check_table_exists('simulation_performance_snapshots'):
            logger.info("📝 Création de la table simulation_performance_snapshots...")
            SimulationPerformanceSnapshot.__table__.create(bind=engine, checkfirst=True)
        
        # 2. Mettre à jour les enums
        logger.info("📝 Mise à jour des types ENUM...")
        
        # Mettre à jour SimulationStatus enum
        try:
            db.execute(text("""
                DO $$ BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'simulationstatus') THEN
                        CREATE TYPE simulationstatus AS ENUM ('created', 'running', 'paused', 'completed', 'failed');
                    ELSE
                        ALTER TYPE simulationstatus ADD VALUE IF NOT EXISTS 'created';
                        ALTER TYPE simulationstatus ADD VALUE IF NOT EXISTS 'failed';
                    END IF;
                END $$;
            """))
        except Exception as e:
            logger.warning(f"Erreur mise à jour enum SimulationStatus: {e}")
        
        # Créer SimulationStrategy enum
        try:
            db.execute(text("""
                DO $$ BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'simulationstrategy') THEN
                        CREATE TYPE simulationstrategy AS ENUM ('technical', 'momentum', 'mean_reversion');
                    END IF;
                END $$;
            """))
        except Exception as e:
            logger.warning(f"Erreur création enum SimulationStrategy: {e}")
        
        # 3. Ajouter les nouvelles colonnes si elles n'existent pas
        new_columns = [
            ('trading_simulations', 'description', 'TEXT'),
            ('trading_simulations', 'current_capital', 'FLOAT DEFAULT 0'),
            ('trading_simulations', 'max_position_size', 'FLOAT DEFAULT 0.1'),
            ('trading_simulations', 'strategy', 'simulationstrategy DEFAULT \'technical\''),
            ('trading_simulations', 'stop_loss_percent', 'FLOAT DEFAULT 5.0'),
            ('trading_simulations', 'take_profit_percent', 'FLOAT DEFAULT 10.0'),
            ('trading_simulations', 'max_etfs', 'INTEGER DEFAULT 10'),
            ('trading_simulations', 'etf_list', 'JSONB'),
            ('trading_simulations', 'current_positions', 'JSONB'),
            ('trading_simulations', 'total_return', 'FLOAT DEFAULT 0'),
            ('trading_simulations', 'total_return_percent', 'FLOAT DEFAULT 0'),
            ('trading_simulations', 'total_trades', 'INTEGER DEFAULT 0'),
            ('trading_simulations', 'winning_trades', 'INTEGER DEFAULT 0'),
            ('trading_simulations', 'losing_trades', 'INTEGER DEFAULT 0'),
            ('trading_simulations', 'win_rate', 'FLOAT DEFAULT 0'),
            ('trading_simulations', 'max_drawdown', 'FLOAT DEFAULT 0'),
            ('trading_simulations', 'sharpe_ratio', 'FLOAT'),
            ('trading_simulations', 'ended_at', 'TIMESTAMP'),
            ('trading_simulations', 'paused_at', 'TIMESTAMP'),
            ('trading_simulations', 'last_rebalance_at', 'TIMESTAMP'),
            
            ('simulation_trades', 'etf_symbol', 'VARCHAR(50)'),
            ('simulation_trades', 'etf_isin', 'VARCHAR(12)'),
            ('simulation_trades', 'trade_type', 'VARCHAR(10)'),
            ('simulation_trades', 'total_amount', 'FLOAT'),
            ('simulation_trades', 'fees', 'FLOAT DEFAULT 0'),
            ('simulation_trades', 'executed_at', 'TIMESTAMP'),
            ('simulation_trades', 'portfolio_value_before', 'FLOAT'),
            ('simulation_trades', 'portfolio_value_after', 'FLOAT'),
            ('simulation_trades', 'profit_loss', 'FLOAT'),
        ]
        
        for table_name, column_name, column_type in new_columns:
            if not check_column_exists(table_name, column_name):
                logger.info(f"➕ Ajout de la colonne {table_name}.{column_name}")
                try:
                    db.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"))
                except Exception as e:
                    logger.error(f"Erreur ajout colonne {table_name}.{column_name}: {e}")
        
        # 4. Mettre à jour les valeurs par défaut pour les simulations existantes
        logger.info("🔄 Mise à jour des valeurs par défaut...")
        
        try:
            # Mettre à jour current_capital pour les simulations existantes
            db.execute(text("""
                UPDATE trading_simulations 
                SET current_capital = initial_capital 
                WHERE current_capital IS NULL OR current_capital = 0
            """))
            
            # Mettre à jour les positions vides
            db.execute(text("""
                UPDATE trading_simulations 
                SET current_positions = '{}' 
                WHERE current_positions IS NULL
            """))
            
            # Mettre à jour etf_list pour les simulations existantes
            db.execute(text("""
                UPDATE trading_simulations 
                SET etf_list = etf_symbols 
                WHERE etf_list IS NULL AND etf_symbols IS NOT NULL
            """))
            
        except Exception as e:
            logger.error(f"Erreur mise à jour valeurs par défaut: {e}")
        
        # 5. Créer les index pour optimiser les performances
        logger.info("📊 Création des index...")
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_trading_simulations_user_id ON trading_simulations(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_trading_simulations_status ON trading_simulations(status)",
            "CREATE INDEX IF NOT EXISTS idx_simulation_trades_simulation_id ON simulation_trades(simulation_id)",
            "CREATE INDEX IF NOT EXISTS idx_simulation_trades_executed_at ON simulation_trades(executed_at)",
            "CREATE INDEX IF NOT EXISTS idx_simulation_performance_snapshots_simulation_id ON simulation_performance_snapshots(simulation_id)",
        ]
        
        for index_sql in indexes:
            try:
                db.execute(text(index_sql))
            except Exception as e:
                logger.warning(f"Erreur création index: {e}")
        
        # Valider les changements
        db.commit()
        
        logger.info("✅ Mise à jour du schéma terminée avec succès!")
        
        # 6. Vérification finale
        logger.info("🔍 Vérification du schéma...")
        
        # Compter les simulations existantes
        result = db.execute(text("SELECT COUNT(*) FROM trading_simulations")).fetchone()
        logger.info(f"📊 Nombre de simulations en base: {result[0]}")
        
        # Compter les trades existants
        result = db.execute(text("SELECT COUNT(*) FROM simulation_trades")).fetchone()
        logger.info(f"📊 Nombre de trades en base: {result[0]}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la mise à jour du schéma: {e}")
        db.rollback()
        return False
        
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("🚀 Démarrage de la mise à jour du schéma des simulations...")
    
    success = update_database_schema()
    
    if success:
        logger.info("🎉 Mise à jour terminée avec succès!")
        sys.exit(0)
    else:
        logger.error("💥 Échec de la mise à jour!")
        sys.exit(1)