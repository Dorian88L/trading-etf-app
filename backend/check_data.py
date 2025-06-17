import sys
sys.path.append('/app')
from app.core.config import settings
from sqlalchemy import create_engine, text

engine = create_engine(settings.DATABASE_URL)
with engine.connect() as conn:
    result = conn.execute(text('SELECT COUNT(*) FROM etfs'))
    etf_count = result.fetchone()[0]
    print(f'Nombre ETFs en base: {etf_count}')
    
    result = conn.execute(text('SELECT COUNT(*) FROM users'))
    user_count = result.fetchone()[0]
    print(f'Nombre utilisateurs: {user_count}')
    
    if etf_count > 0:
        result = conn.execute(text('SELECT name, isin FROM etfs LIMIT 3'))
        print('Premiers ETFs:')
        for row in result:
            print(f'  - {row[0]} ({row[1]})')