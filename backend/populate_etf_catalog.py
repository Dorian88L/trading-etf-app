#!/usr/bin/env python3
"""
Script pour peupler la base de données avec le catalogue d'ETFs
"""

import sys
import os

# Ajouter le répertoire parent au path pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.services.etf_catalog import get_etf_catalog_service

# Import direct pour éviter les dépendances circulaires
from sqlalchemy import Column, String, DateTime, DECIMAL, BigInteger, ForeignKey, PrimaryKeyConstraint, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class ETF(Base):
    __tablename__ = "etfs"
    
    isin = Column(String(12), primary_key=True)
    name = Column(String(255), nullable=False)
    sector = Column(String(100))
    currency = Column(String(3), default="EUR")
    ter = Column(DECIMAL(5, 4))
    aum = Column(BigInteger)
    exchange = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


def populate_etf_database():
    """Peuple la base de données avec le catalogue d'ETFs"""
    print("🚀 Démarrage de la population de la base de données ETF...")
    
    db = SessionLocal()
    try:
        catalog_service = get_etf_catalog_service()
        
        # Compter les ETFs existants
        existing_count = db.query(ETF).count()
        print(f"📊 ETFs existants en base: {existing_count}")
        
        # Peupler avec le catalogue
        catalog_service.populate_database(db)
        
        # Vérifier le nouveau nombre
        new_count = db.query(ETF).count()
        print(f"✅ ETFs en base après population: {new_count}")
        print(f"➕ ETFs ajoutés: {new_count - existing_count}")
        
        # Afficher quelques exemples
        sample_etfs = db.query(ETF).limit(5).all()
        print("\n📋 Exemples d'ETFs en base:")
        for etf in sample_etfs:
            print(f"  - {etf.name} ({etf.isin}) - Secteur: {etf.sector}")
        
        print("\n🎉 Population terminée avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur lors de la population: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    populate_etf_database()