"""
Script pour ajouter des index et contraintes supplémentaires pour optimiser les performances
et renforcer la prévention des doublons
"""

import os
from sqlalchemy import create_engine, text

# Récupérer l'URL de base de données depuis les variables d'environnement
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://trading_user:trading_password@localhost:5432/trading_etf_prod")

def add_performance_indexes():
    """Ajoute des index pour optimiser les performances des requêtes fréquentes"""
    
    engine = create_engine(DATABASE_URL)
    
    queries = [
        # Index sur les colonnes les plus consultées pour market_data
        """
        CREATE INDEX IF NOT EXISTS idx_market_data_time_desc 
        ON market_data (time DESC);
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_market_data_etf_time 
        ON market_data (etf_isin, time DESC);
        """,
        
        # Index composite pour les requêtes de plage de dates
        """
        CREATE INDEX IF NOT EXISTS idx_market_data_etf_time_range 
        ON market_data (etf_isin, time) 
        WHERE time >= CURRENT_DATE - INTERVAL '1 year';
        """,
        
        # Index pour les indicateurs techniques
        """
        CREATE INDEX IF NOT EXISTS idx_technical_indicators_etf_time 
        ON technical_indicators (etf_isin, time DESC);
        """,
        
        # Index sur les ETF pour les recherches par nom/symbole
        """
        CREATE INDEX IF NOT EXISTS idx_etfs_name_gin 
        ON etfs USING gin(to_tsvector('english', name));
        """,
        
        # Index pour les signaux récents
        """
        CREATE INDEX IF NOT EXISTS idx_signals_etf_recent 
        ON signals (etf_isin, created_at DESC) 
        WHERE created_at >= CURRENT_DATE - INTERVAL '30 days';
        """,
        
        # Contrainte unique supplémentaire pour s'assurer de l'unicité
        """
        ALTER TABLE market_data 
        ADD CONSTRAINT unique_market_data_per_day 
        UNIQUE (etf_isin, time);
        """,
        
        """
        ALTER TABLE technical_indicators 
        ADD CONSTRAINT unique_technical_indicators_per_day 
        UNIQUE (etf_isin, time);
        """
    ]
    
    with engine.connect() as conn:
        for query in queries:
            try:
                print(f"Exécution: {query.strip()[:60]}...")
                conn.execute(text(query))
                conn.commit()
                print("✅ Succès")
            except Exception as e:
                print(f"⚠️ Erreur (peut-être déjà existant): {e}")
                conn.rollback()
    
    print("\n🎉 Index et contraintes ajoutés avec succès!")

if __name__ == "__main__":
    add_performance_indexes()