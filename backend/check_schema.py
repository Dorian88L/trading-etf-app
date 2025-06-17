import sys
sys.path.append('/app')
from app.core.config import settings
from sqlalchemy import create_engine, text

engine = create_engine(settings.DATABASE_URL)
with engine.connect() as conn:
    result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'users'"))
    columns = [row[0] for row in result]
    print('Colonnes users:', columns)
    
    # Vérifier aussi le modèle User
    from app.models.user import User
    print('Attributs du modèle User:', [attr for attr in dir(User) if not attr.startswith('_')])