"""
Script simple pour ajouter les tables de mapping ETF sans relations complexes
"""

import sys
sys.path.append('/app')

from sqlalchemy import create_engine, text
from app.core.database import SessionLocal

def create_tables_and_data():
    """Crée les tables et ajoute les données directement avec SQL"""
    
    db = SessionLocal()
    try:
        # Créer la table des mappings symboles
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS etf_symbol_mappings (
                id VARCHAR PRIMARY KEY,
                etf_isin VARCHAR(12) NOT NULL,
                exchange_code VARCHAR(10) NOT NULL,
                trading_symbol VARCHAR(20) NOT NULL,
                currency VARCHAR(3) NOT NULL,
                is_primary BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                FOREIGN KEY (etf_isin) REFERENCES etfs(isin)
            );
        """))
        
        # Créer la table de configuration d'affichage
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS etf_display_config (
                etf_isin VARCHAR(12) PRIMARY KEY,
                is_visible_on_dashboard BOOLEAN DEFAULT TRUE,
                is_visible_on_etf_list BOOLEAN DEFAULT TRUE,
                display_order DECIMAL(3,1) DEFAULT 0,
                notes TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                FOREIGN KEY (etf_isin) REFERENCES etfs(isin)
            );
        """))
        
        print("✅ Tables créées")
        
        # Ajouter les mappings symboles
        symbol_mappings = [
            # iShares Core S&P 500 UCITS ETF - LE PLUS IMPORTANT !
            ("IE00B5BMR087_AS", "IE00B5BMR087", "AS", "CSPX.AS", "EUR", True),
            ("IE00B5BMR087_L", "IE00B5BMR087", "L", "CSPX.L", "USD", False),
            
            # iShares Core MSCI World UCITS ETF
            ("IE00B4L5Y983_AS", "IE00B4L5Y983", "AS", "IWDA.AS", "EUR", True),
            ("IE00B4L5Y983_L", "IE00B4L5Y983", "L", "IWDA.L", "USD", False),
            
            # Vanguard FTSE All-World UCITS ETF
            ("IE00BK5BQT80_AS", "IE00BK5BQT80", "AS", "VWRL.AS", "EUR", True),
            ("IE00BK5BQT80_L", "IE00BK5BQT80", "L", "VWRL.L", "USD", False),
            
            # Vanguard S&P 500 UCITS ETF
            ("IE00B3XXRP09_L", "IE00B3XXRP09", "L", "VUSA.L", "USD", True),
            
            # iShares Core MSCI Europe UCITS ETF
            ("IE00B1YZSC51_AS", "IE00B1YZSC51", "AS", "IEUR.AS", "EUR", True),
            ("IE00B1YZSC51_L", "IE00B1YZSC51", "L", "IEUR.L", "EUR", False),
            
            # iShares Core DAX UCITS ETF
            ("IE00B02KXL92_DE", "IE00B02KXL92", "DE", "EXS1.DE", "EUR", True),
            
            # iShares MSCI Europe UCITS ETF
            ("IE00B14X4M10_L", "IE00B14X4M10", "L", "IMEU.L", "EUR", True),
            
            # Vanguard FTSE Developed Europe UCITS ETF
            ("IE00B945VV12_L", "IE00B945VV12", "L", "VERX.L", "EUR", True),
            
            # Xtrackers DAX UCITS ETF
            ("LU0274211480_DE", "LU0274211480", "DE", "DBX1.DE", "EUR", True),
            
            # Xtrackers MSCI World UCITS ETF
            ("IE00BJ0KDQ92_DE", "IE00BJ0KDQ92", "DE", "A1XB5U.DE", "EUR", True),
        ]
        
        for mapping_id, etf_isin, exchange_code, trading_symbol, currency, is_primary in symbol_mappings:
            # Vérifier si le mapping existe déjà
            result = db.execute(text(
                "SELECT id FROM etf_symbol_mappings WHERE id = :mapping_id"
            ), {"mapping_id": mapping_id})
            
            if not result.fetchone():
                db.execute(text("""
                    INSERT INTO etf_symbol_mappings 
                    (id, etf_isin, exchange_code, trading_symbol, currency, is_primary, is_active) 
                    VALUES (:id, :etf_isin, :exchange_code, :trading_symbol, :currency, :is_primary, TRUE)
                """), {
                    "id": mapping_id,
                    "etf_isin": etf_isin,
                    "exchange_code": exchange_code,
                    "trading_symbol": trading_symbol,
                    "currency": currency,
                    "is_primary": is_primary
                })
        
        # Ajouter la configuration d'affichage pour tous les ETFs
        etfs_result = db.execute(text("SELECT isin, name FROM etfs"))
        etfs_data = etfs_result.fetchall()
        
        for etf_isin, etf_name in etfs_data:
            # Vérifier si la config existe déjà
            result = db.execute(text(
                "SELECT etf_isin FROM etf_display_config WHERE etf_isin = :etf_isin"
            ), {"etf_isin": etf_isin})
            
            if not result.fetchone():
                db.execute(text("""
                    INSERT INTO etf_display_config 
                    (etf_isin, is_visible_on_dashboard, is_visible_on_etf_list, display_order, notes) 
                    VALUES (:etf_isin, TRUE, TRUE, 0, :notes)
                """), {
                    "etf_isin": etf_isin,
                    "notes": f"Configuration automatique pour {etf_name}"
                })
        
        db.commit()
        print("✅ Données ajoutées")
        
        # Vérifier les résultats
        mappings_count = db.execute(text("SELECT COUNT(*) FROM etf_symbol_mappings")).scalar()
        configs_count = db.execute(text("SELECT COUNT(*) FROM etf_display_config")).scalar()
        
        print(f"📊 Résumé:")
        print(f"   - {mappings_count} mappings symboles créés")
        print(f"   - {configs_count} configurations d'affichage créées")
        
        # Afficher le mapping pour iShares Core S&P 500
        result = db.execute(text("""
            SELECT trading_symbol, currency, is_primary 
            FROM etf_symbol_mappings 
            WHERE etf_isin = 'IE00B5BMR087'
        """))
        
        print(f"🎯 Mappings pour iShares Core S&P 500 (IE00B5BMR087):")
        for symbol, currency, is_primary in result.fetchall():
            primary_text = " (PRINCIPAL)" if is_primary else ""
            print(f"   - {symbol} ({currency}){primary_text}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_tables_and_data()