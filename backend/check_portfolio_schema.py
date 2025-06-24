import sys
sys.path.append('/app')
from app.core.config import settings
from sqlalchemy import create_engine, text

engine = create_engine(settings.DATABASE_URL)
with engine.connect() as conn:
    result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'portfolios'"))
    columns = [row[0] for row in result]
    print('Colonnes portfolios:', columns)
    
    # Vérifier aussi les tables liées
    tables = ['portfolios', 'positions', 'transactions']
    for table in tables:
        try:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.fetchone()[0]
            print(f'Table {table}: {count} entrées')
        except Exception as e:
            print(f'Table {table}: Erreur - {e}')