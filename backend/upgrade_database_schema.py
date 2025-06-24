#!/usr/bin/env python3
"""
Script de mise à jour du schéma de base de données
Ajoute les nouvelles colonnes et tables pour l'optimisation ETF
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text, inspect
from app.core.database import SessionLocal, engine
from app.models.etf import ETF, MarketData, ETFHistoricalData, ETFMarketAlert, ETFDataQuality
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_column_exists(table_name: str, column_name: str) -> bool:
    """Vérifie si une colonne existe dans une table"""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def check_table_exists(table_name: str) -> bool:
    """Vérifie si une table existe"""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()

def add_column_if_not_exists(session, table_name: str, column_name: str, column_definition: str):
    """Ajoute une colonne si elle n'existe pas"""
    if not check_column_exists(table_name, column_name):
        try:
            sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
            session.execute(text(sql))
            session.commit()
            logger.info(f"✓ Colonne {column_name} ajoutée à {table_name}")
        except Exception as e:
            logger.warning(f"⚠️  Erreur ajout colonne {column_name}: {e}")
            session.rollback()
    else:
        logger.info(f"→ Colonne {column_name} existe déjà dans {table_name}")

def upgrade_etfs_table(session):
    """Met à jour la table ETFs avec les nouvelles colonnes"""
    logger.info("🔧 Mise à jour de la table ETFs...")
    
    # Nouvelles colonnes pour la table ETFs
    new_columns = {
        'description': 'TEXT',
        'dividend_yield': 'DECIMAL(5, 4)',
        'pe_ratio': 'DECIMAL(8, 2)',
        'beta': 'DECIMAL(6, 4)',
        'inception_date': 'TIMESTAMP WITH TIME ZONE',
        'geography': 'VARCHAR(100)',
        'investment_theme': 'VARCHAR(100)',
        'replication_method': 'VARCHAR(50)',
        'data_quality_score': 'DECIMAL(3, 2) DEFAULT 1.0',
        'last_data_update': 'TIMESTAMP WITH TIME ZONE',
        'is_active': 'BOOLEAN DEFAULT TRUE'
    }
    
    for column_name, column_def in new_columns.items():
        add_column_if_not_exists(session, 'etfs', column_name, column_def)

def upgrade_market_data_table(session):
    """Met à jour la table MarketData avec les nouvelles colonnes"""
    logger.info("🔧 Mise à jour de la table MarketData...")
    
    new_columns = {
        'change_absolute': 'DECIMAL(10, 4)',
        'change_percent': 'DECIMAL(6, 4)', 
        'market_cap': 'BIGINT',
        'bid_price': 'DECIMAL(10, 4)',
        'ask_price': 'DECIMAL(10, 4)',
        'spread': 'DECIMAL(8, 4)',
        'data_source': 'VARCHAR(50)',
        'confidence_score': 'DECIMAL(3, 2) DEFAULT 1.0',
        'is_realtime': 'BOOLEAN DEFAULT TRUE'
    }
    
    for column_name, column_def in new_columns.items():
        add_column_if_not_exists(session, 'market_data', column_name, column_def)

def upgrade_etf_display_config_table(session):
    """Met à jour la table ETFDisplayConfig"""
    logger.info("🔧 Mise à jour de la table ETFDisplayConfig...")
    
    new_columns = {
        'preferred_chart_type': "VARCHAR(20) DEFAULT 'line'",
        'show_technical_indicators': 'BOOLEAN DEFAULT TRUE',
        'default_timeframe': "VARCHAR(10) DEFAULT '1D'",
        'enable_price_alerts': 'BOOLEAN DEFAULT FALSE',
        'enable_volume_alerts': 'BOOLEAN DEFAULT FALSE',
        'alert_threshold_percent': 'DECIMAL(5, 2) DEFAULT 2.0'
    }
    
    for column_name, column_def in new_columns.items():
        add_column_if_not_exists(session, 'etf_display_config', column_name, column_def)

def create_new_tables(session):
    """Crée les nouvelles tables"""
    logger.info("🏗️  Création des nouvelles tables...")
    
    # Créer la table ETFHistoricalData
    if not check_table_exists('etf_historical_data'):
        try:
            ETFHistoricalData.__table__.create(engine)
            logger.info("✓ Table etf_historical_data créée")
        except Exception as e:
            logger.warning(f"⚠️  Erreur création etf_historical_data: {e}")
    
    # Créer la table ETFMarketAlert
    if not check_table_exists('etf_market_alerts'):
        try:
            ETFMarketAlert.__table__.create(engine)
            logger.info("✓ Table etf_market_alerts créée")
        except Exception as e:
            logger.warning(f"⚠️  Erreur création etf_market_alerts: {e}")
    
    # Créer la table ETFDataQuality
    if not check_table_exists('etf_data_quality'):
        try:
            ETFDataQuality.__table__.create(engine)
            logger.info("✓ Table etf_data_quality créée")
        except Exception as e:
            logger.warning(f"⚠️  Erreur création etf_data_quality: {e}")

def create_indexes(session):
    """Crée les index pour optimiser les performances"""
    logger.info("📊 Création des index d'optimisation...")
    
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_market_data_realtime ON market_data(etf_isin, time, is_realtime)",
        "CREATE INDEX IF NOT EXISTS idx_market_data_source ON market_data(data_source, time)",
        "CREATE INDEX IF NOT EXISTS idx_etfs_active ON etfs(is_active, sector)",
        "CREATE INDEX IF NOT EXISTS idx_etfs_geography ON etfs(geography, investment_theme)",
    ]
    
    for index_sql in indexes:
        try:
            session.execute(text(index_sql))
            session.commit()
            logger.info(f"✓ Index créé: {index_sql.split('idx_')[1].split(' ')[0]}")
        except Exception as e:
            logger.warning(f"⚠️  Erreur création index: {e}")
            session.rollback()

def populate_default_data(session):
    """Remplit les nouvelles colonnes avec des valeurs par défaut"""
    logger.info("📝 Remplissage des données par défaut...")
    
    try:
        # Mettre à jour les ETFs existants avec des valeurs par défaut
        session.execute(text("""
            UPDATE etfs 
            SET 
                data_quality_score = 1.0,
                is_active = TRUE,
                last_data_update = NOW()
            WHERE data_quality_score IS NULL
        """))
        
        # Mettre à jour MarketData existant
        session.execute(text("""
            UPDATE market_data 
            SET 
                confidence_score = 0.8,
                is_realtime = FALSE,
                data_source = 'legacy'
            WHERE confidence_score IS NULL
        """))
        
        session.commit()
        logger.info("✓ Données par défaut remplies")
        
    except Exception as e:
        logger.error(f"❌ Erreur remplissage données par défaut: {e}")
        session.rollback()

def main():
    """Fonction principale de migration"""
    logger.info("🚀 Début de la mise à jour du schéma de base de données")
    
    session = SessionLocal()
    
    try:
        # 1. Mettre à jour les tables existantes
        upgrade_etfs_table(session)
        upgrade_market_data_table(session)
        upgrade_etf_display_config_table(session)
        
        # 2. Créer les nouvelles tables
        create_new_tables(session)
        
        # 3. Créer les index d'optimisation
        create_indexes(session)
        
        # 4. Remplir avec des données par défaut
        populate_default_data(session)
        
        logger.info("✅ Mise à jour du schéma terminée avec succès!")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la mise à jour: {e}")
        session.rollback()
        return 1
        
    finally:
        session.close()
    
    return 0

if __name__ == "__main__":
    exit(main())