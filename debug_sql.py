#!/usr/bin/env python3

import psycopg2

# Configuration
DATABASE_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'trading_etf',
    'user': 'trading_user',
    'password': 'trading_password'
}

try:
    conn = psycopg2.connect(**DATABASE_CONFIG)
    cursor = conn.cursor()
    
    # Test de la requête SQL de l'endpoint
    query = """
        SELECT DISTINCT
            e.isin,
            e.name,
            e.sector,
            e.currency,
            e.exchange,
            e.aum,
            COALESCE(latest.close_price, 100 + (RANDOM() * 400)) as current_price,
            COALESCE(latest.volume, 500000 + (RANDOM() * 1500000)::int) as volume,
            COALESCE(latest.time, NOW()) as last_update
        FROM etfs e
        LEFT JOIN LATERAL (
            SELECT close_price, volume, time
            FROM market_data md
            WHERE md.etf_isin = e.isin
            ORDER BY md.time DESC
            LIMIT 1
        ) latest ON true
        ORDER BY e.name
        LIMIT 5
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    print(f"Nombre de résultats: {len(results)}")
    
    if results:
        print("Premiers résultats:")
        for row in results:
            print(f"  ISIN: {row[0]}, Nom: {row[1]}, Prix: {row[6]}")
    else:
        print("Aucun résultat. Test basique:")
        cursor.execute("SELECT COUNT(*) FROM etfs")
        count = cursor.fetchone()[0]
        print(f"  Nombre d'ETFs: {count}")
        
        cursor.execute("SELECT COUNT(*) FROM market_data")
        count = cursor.fetchone()[0]
        print(f"  Nombre de données de marché: {count}")
        
        cursor.execute("SELECT e.isin, e.name FROM etfs e LIMIT 3")
        etfs = cursor.fetchall()
        print("  Quelques ETFs:")
        for isin, name in etfs:
            print(f"    {isin}: {name}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Erreur: {e}")