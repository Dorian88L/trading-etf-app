import sys
sys.path.append('/app')
from app.core.config import settings
from sqlalchemy import create_engine, text

engine = create_engine(settings.DATABASE_URL)
with engine.connect() as conn:
    result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'etfs'"))
    columns = [row[0] for row in result]
    print('Colonnes etfs:', columns)