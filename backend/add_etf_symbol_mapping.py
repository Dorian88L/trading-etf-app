"""
Script pour ajouter une table de mapping ISIN vers symboles de trading
et une table pour configurer quels ETFs afficher
"""

import sys
import os
sys.path.append('/app')

from sqlalchemy import create_engine, Column, String, Boolean, DateTime, DECIMAL, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from datetime import datetime

from app.core.database import SessionLocal, engine, Base

# Créer les nouvelles tables
class ETFSymbolMapping(Base):
    __tablename__ = "etf_symbol_mappings"
    
    id = Column(String, primary_key=True)  # Composite: isin_exchange
    etf_isin = Column(String(12), ForeignKey("etfs.isin"), nullable=False)
    exchange_code = Column(String(10), nullable=False)  # AS, DE, L, PA
    trading_symbol = Column(String(20), nullable=False)  # CSPX.AS, IWDA.L
    currency = Column(String(3), nullable=False)  # EUR, USD, GBP
    is_primary = Column(Boolean, default=False)  # Symbole principal pour les données temps réel
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relation
    etf = relationship("ETF", back_populates="symbol_mappings")

class ETFDisplayConfig(Base):
    __tablename__ = "etf_display_config"
    
    etf_isin = Column(String(12), ForeignKey("etfs.isin"), primary_key=True)
    is_visible_on_dashboard = Column(Boolean, default=True)
    is_visible_on_etf_list = Column(Boolean, default=True)
    display_order = Column(DECIMAL(3, 1), default=0)  # Pour l'ordre d'affichage
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relation
    etf = relationship("ETF", back_populates="display_config")

def create_tables_and_populate():
    """Crée les tables et ajoute les données initiales"""
    
    # Créer les tables
    Base.metadata.create_all(bind=engine)
    print("✅ Tables créées")
    
    db = SessionLocal()
    try:
        # Données initiales pour les mappings symboles
        symbol_mappings = [
            # iShares Core S&P 500 UCITS ETF
            {"etf_isin": "IE00B5BMR087", "exchange_code": "AS", "trading_symbol": "CSPX.AS", "currency": "EUR", "is_primary": True},
            {"etf_isin": "IE00B5BMR087", "exchange_code": "L", "trading_symbol": "CSPX.L", "currency": "USD", "is_primary": False},
            
            # iShares Core MSCI World UCITS ETF
            {"etf_isin": "IE00B4L5Y983", "exchange_code": "AS", "trading_symbol": "IWDA.AS", "currency": "EUR", "is_primary": True},
            {"etf_isin": "IE00B4L5Y983", "exchange_code": "L", "trading_symbol": "IWDA.L", "currency": "USD", "is_primary": False},
            
            # Vanguard FTSE All-World UCITS ETF
            {"etf_isin": "IE00BK5BQT80", "exchange_code": "AS", "trading_symbol": "VWRL.AS", "currency": "EUR", "is_primary": True},
            {"etf_isin": "IE00BK5BQT80", "exchange_code": "L", "trading_symbol": "VWRL.L", "currency": "USD", "is_primary": False},
            
            # Vanguard S&P 500 UCITS ETF
            {"etf_isin": "IE00B3XXRP09", "exchange_code": "L", "trading_symbol": "VUSA.L", "currency": "USD", "is_primary": True},
            
            # iShares Core MSCI Europe UCITS ETF
            {"etf_isin": "IE00B1YZSC51", "exchange_code": "AS", "trading_symbol": "IEUR.AS", "currency": "EUR", "is_primary": True},
            {"etf_isin": "IE00B1YZSC51", "exchange_code": "L", "trading_symbol": "IEUR.L", "currency": "EUR", "is_primary": False},
            
            # iShares Core DAX UCITS ETF
            {"etf_isin": "IE00B02KXL92", "exchange_code": "DE", "trading_symbol": "EXS1.DE", "currency": "EUR", "is_primary": True},
            
            # iShares MSCI Europe UCITS ETF
            {"etf_isin": "IE00B14X4M10", "exchange_code": "L", "trading_symbol": "IMEU.L", "currency": "EUR", "is_primary": True},
            
            # Vanguard FTSE Developed Europe UCITS ETF
            {"etf_isin": "IE00B945VV12", "exchange_code": "L", "trading_symbol": "VERX.L", "currency": "EUR", "is_primary": True},
            
            # Xtrackers DAX UCITS ETF
            {"etf_isin": "LU0274211480", "exchange_code": "DE", "trading_symbol": "DBX1.DE", "currency": "EUR", "is_primary": True},
            
            # Xtrackers MSCI World UCITS ETF
            {"etf_isin": "IE00BJ0KDQ92", "exchange_code": "DE", "trading_symbol": "A1XB5U.DE", "currency": "EUR", "is_primary": True},
        ]
        
        # Ajouter les mappings
        for mapping_data in symbol_mappings:
            # Créer un ID composite
            mapping_id = f"{mapping_data['etf_isin']}_{mapping_data['exchange_code']}"
            
            existing = db.query(ETFSymbolMapping).filter(ETFSymbolMapping.id == mapping_id).first()
            if not existing:
                mapping = ETFSymbolMapping(
                    id=mapping_id,
                    **mapping_data
                )
                db.add(mapping)
        
        # Configuration d'affichage - Par défaut tous visibles
        # Utilisons une requête SQL directe pour éviter les problèmes d'import
        result = db.execute("SELECT isin, name FROM etfs")
        etfs_data = result.fetchall()
        
        for etf_data in etfs_data:
            etf_isin, etf_name = etf_data
            existing_config = db.query(ETFDisplayConfig).filter(ETFDisplayConfig.etf_isin == etf_isin).first()
            if not existing_config:
                config = ETFDisplayConfig(
                    etf_isin=etf_isin,
                    is_visible_on_dashboard=True,
                    is_visible_on_etf_list=True,
                    display_order=0,
                    notes=f"Configuration automatique pour {etf_name}"
                )
                db.add(config)
        
        db.commit()
        print("✅ Données initiales ajoutées")
        
        # Afficher un résumé
        total_mappings = db.query(ETFSymbolMapping).count()
        total_configs = db.query(ETFDisplayConfig).count()
        
        print(f"📊 Résumé:")
        print(f"   - {total_mappings} mappings symboles créés")
        print(f"   - {total_configs} configurations d'affichage créées")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_tables_and_populate()