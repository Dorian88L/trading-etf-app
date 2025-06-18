"""
Script pour créer la table des préférences ETF par utilisateur
"""

import sys
sys.path.append('/app')

from sqlalchemy import text
from app.core.database import SessionLocal

def create_user_etf_preferences_table():
    """Crée la table des préférences ETF par utilisateur"""
    
    db = SessionLocal()
    try:
        # Créer la table des préférences ETF par utilisateur
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS user_etf_preferences (
                id SERIAL PRIMARY KEY,
                user_id UUID NOT NULL,
                etf_isin VARCHAR(12) NOT NULL,
                is_visible_on_dashboard BOOLEAN DEFAULT TRUE,
                is_visible_on_etf_list BOOLEAN DEFAULT TRUE,
                is_favorite BOOLEAN DEFAULT FALSE,
                display_order INTEGER DEFAULT 0,
                custom_name VARCHAR(255),  -- Nom personnalisé par l'utilisateur
                notes TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                
                -- Contraintes
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (etf_isin) REFERENCES etfs(isin) ON DELETE CASCADE,
                UNIQUE(user_id, etf_isin)  -- Un utilisateur ne peut avoir qu'une préférence par ETF
            );
        """))
        
        # Créer des index pour les performances
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_user_etf_prefs_user_id ON user_etf_preferences(user_id);
            CREATE INDEX IF NOT EXISTS idx_user_etf_prefs_etf_isin ON user_etf_preferences(etf_isin);
            CREATE INDEX IF NOT EXISTS idx_user_etf_prefs_dashboard ON user_etf_preferences(user_id, is_visible_on_dashboard);
            CREATE INDEX IF NOT EXISTS idx_user_etf_prefs_favorites ON user_etf_preferences(user_id, is_favorite);
        """))
        
        print("✅ Table user_etf_preferences créée")
        
        # Créer aussi une vue pour simplifier les requêtes
        db.execute(text("""
            CREATE OR REPLACE VIEW user_etf_dashboard_view AS
            SELECT 
                uep.user_id,
                e.isin,
                e.name as etf_name,
                e.sector,
                e.currency,
                e.exchange,
                COALESCE(uep.custom_name, e.name) as display_name,
                uep.is_visible_on_dashboard,
                uep.is_visible_on_etf_list,
                uep.is_favorite,
                uep.display_order,
                uep.notes,
                esm.trading_symbol,
                esm.exchange_code,
                esm.is_primary
            FROM user_etf_preferences uep
            JOIN etfs e ON uep.etf_isin = e.isin
            LEFT JOIN etf_symbol_mappings esm ON e.isin = esm.etf_isin AND esm.is_primary = TRUE
            WHERE uep.is_visible_on_dashboard = TRUE
            ORDER BY uep.display_order, uep.is_favorite DESC, e.name;
        """))
        
        print("✅ Vue user_etf_dashboard_view créée")
        
        db.commit()
        
        # Afficher les ETFs disponibles pour test
        etfs_result = db.execute(text("SELECT isin, name FROM etfs ORDER BY name"))
        etfs_data = etfs_result.fetchall()
        
        print(f"📊 ETFs disponibles pour configuration ({len(etfs_data)}):")
        for isin, name in etfs_data[:5]:  # Afficher les 5 premiers
            print(f"   - {isin}: {name}")
        if len(etfs_data) > 5:
            print(f"   ... et {len(etfs_data) - 5} autres")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_user_etf_preferences_table()