#!/usr/bin/env python3

"""
Backend simplifié avec authentification pour tester la connexion
"""

import os
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from typing import Optional
from pydantic import BaseModel

# Configuration
DATABASE_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "trading_etf",
    "user": "trading_user",
    "password": "trading_password"
}

JWT_SECRET_KEY = "dev-secret-key-not-for-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Models
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class User(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    is_active: bool = True

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None

# Application FastAPI
app = FastAPI(
    title="Trading ETF API",
    description="API avec authentification pour Trading ETF",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Autorise toutes les origines pour le dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Fonctions utilitaires
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user_from_db(email: str):
    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, email, hashed_password, full_name, is_active FROM users WHERE email = %s",
            (email,)
        )
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user_data:
            return {
                "id": str(user_data[0]),
                "email": user_data[1],
                "hashed_password": user_data[2],
                "full_name": user_data[3],
                "is_active": user_data[4]
            }
        return None
    except Exception as e:
        print(f"Database error: {e}")
        return None

def create_user_in_db(email: str, hashed_password: str, full_name: str = None):
    try:
        import uuid
        user_id = str(uuid.uuid4())
        
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO users (id, email, hashed_password, full_name, is_active, is_verified, created_at, updated_at) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
            (user_id, email, hashed_password, full_name, True, True, datetime.utcnow(), datetime.utcnow())
        )
        created_user_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "id": str(created_user_id),
            "email": email,
            "full_name": full_name,
            "is_active": True
        }
    except Exception as e:
        print(f"Database error creating user: {e}")
        return None

# Endpoints
@app.get("/")
def read_root():
    return {"message": "Trading ETF API avec authentification", "status": "running"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "Backend avec auth fonctionne"}

@app.post("/api/v1/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Endpoint de connexion"""
    print(f"Tentative de connexion pour: {form_data.username}")
    
    # Récupérer l'utilisateur
    user = get_user_from_db(form_data.username)
    
    if not user:
        print("Utilisateur non trouvé")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Vérifier le mot de passe
    if not verify_password(form_data.password, user["hashed_password"]):
        print("Mot de passe incorrect")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Vérifier si l'utilisateur est actif
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Utilisateur inactif"
        )
    
    # Créer le token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    
    print(f"Connexion réussie pour: {user['email']}")
    
    return {
        "access_token": access_token,
        "refresh_token": access_token,  # Simplified
        "token_type": "bearer"
    }

@app.post("/api/v1/auth/register")
def register(user_data: UserCreate):
    """Endpoint d'inscription"""
    print(f"Tentative d'inscription pour: {user_data.email}")
    
    # Vérifier si l'utilisateur existe déjà
    existing_user = get_user_from_db(user_data.email)
    if existing_user:
        print("Utilisateur existe déjà")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email déjà enregistré"
        )
    
    # Hasher le mot de passe
    hashed_password = pwd_context.hash(user_data.password)
    
    # Créer l'utilisateur
    new_user = create_user_in_db(user_data.email, hashed_password, user_data.full_name)
    
    if not new_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la création de l'utilisateur"
        )
    
    print(f"Inscription réussie pour: {new_user['email']}")
    
    return {
        "id": new_user["id"],
        "email": new_user["email"],
        "full_name": new_user["full_name"],
        "is_active": new_user["is_active"],
        "is_verified": True
    }

@app.get("/api/v1/user/profile")
def get_profile():
    """Endpoint pour récupérer le profil utilisateur"""
    return {
        "id": "test-user-id",
        "email": "test@trading.com",
        "full_name": "Utilisateur Test",
        "is_active": True,
        "is_verified": True
    }

# Endpoints pour les signaux avancés
@app.get("/api/v1/signals/advanced")
def get_advanced_signals():
    """Récupère les signaux avancés"""
    import random
    from datetime import datetime, timedelta
    
    # Données d'exemple conformes au cahier des charges
    etfs = [
        {'isin': 'FR0010296061', 'name': 'Lyxor CAC 40 UCITS ETF', 'sector': 'Large Cap France'},
        {'isin': 'IE00B4L5Y983', 'name': 'iShares Core MSCI World UCITS ETF', 'sector': 'Global Developed'},
        {'isin': 'LU0290358497', 'name': 'Xtrackers EURO STOXX 50 UCITS ETF', 'sector': 'Europe Large Cap'},
        {'isin': 'IE00B4L5YC18', 'name': 'iShares Core S&P 500 UCITS ETF', 'sector': 'US Large Cap'},
    ]
    
    signals = []
    for i, etf in enumerate(etfs):
        signal_types = ['BUY', 'SELL', 'HOLD']
        algorithms = ['BREAKOUT', 'MEAN_REVERSION', 'MOMENTUM', 'STATISTICAL_ARBITRAGE']
        
        confidence = random.uniform(60, 95)
        current_price = random.uniform(40, 500)
        price_target = current_price * random.uniform(0.95, 1.08)
        stop_loss = current_price * random.uniform(0.92, 1.03)
        
        signal_type = random.choice(signal_types)
        expected_return = ((price_target - current_price) / current_price) * 100
        if signal_type == 'SELL':
            expected_return = -expected_return
        
        signals.append({
            'id': f"sig_{i+1:03d}",
            'etf_isin': etf['isin'],
            'etf_name': etf['name'],
            'signal_type': signal_type,
            'algorithm_type': random.choice(algorithms),
            'confidence': round(confidence, 1),
            'technical_score': round(confidence + random.uniform(-10, 10), 1),
            'fundamental_score': round(random.uniform(50, 90), 1),
            'risk_score': round(random.uniform(40, 80), 1),
            'current_price': round(current_price, 2),
            'price_target': round(price_target, 2),
            'stop_loss': round(stop_loss, 2),
            'expected_return': round(expected_return, 1),
            'risk_reward_ratio': round(random.uniform(0.5, 2.5), 2),
            'holding_period': random.randint(3, 15),
            'justification': f"Signal {signal_type} - Algorithme {random.choice(['Cassure', 'Retour moyenne', 'Momentum'])}. Score composite: {confidence:.1f}/100.",
            'timestamp': (datetime.now() - timedelta(hours=random.randint(1, 48))).isoformat(),
            'sector': etf['sector']
        })
    
    return signals

@app.get("/api/v1/market-data/{etf_isin}")
def get_market_data(etf_isin: str):
    """Récupère les données de marché pour un ETF"""
    import random
    from datetime import datetime, timedelta
    
    # Générer 30 jours de données
    data = []
    base_price = 50.0
    current_price = base_price
    
    for i in range(30):
        # Variation journalière
        change = random.uniform(-0.03, 0.03)
        current_price *= (1 + change)
        
        # OHLC
        open_price = current_price * random.uniform(0.995, 1.005)
        high_price = max(open_price, current_price) * random.uniform(1.0, 1.02)
        low_price = min(open_price, current_price) * random.uniform(0.98, 1.0)
        close_price = current_price
        volume = random.randint(1000000, 5000000)
        
        data.append({
            'timestamp': (datetime.now() - timedelta(days=30-i)).isoformat(),
            'open_price': round(open_price, 2),
            'high_price': round(high_price, 2),
            'low_price': round(low_price, 2),
            'close_price': round(close_price, 2),
            'volume': volume
        })
    
    return data

@app.get("/api/v1/indices")
def get_market_indices():
    """Récupère les indices de marché"""
    import random
    
    indices = [
        {'name': 'CAC 40', 'symbol': 'CAC', 'value': 7425.30, 'change': 89.2, 'changePercent': 1.22, 'region': 'France'},
        {'name': 'EURO STOXX 50', 'symbol': 'SX5E', 'value': 4286.15, 'change': 21.4, 'changePercent': 0.50, 'region': 'Europe'},
        {'name': 'S&P 500', 'symbol': 'SPX', 'value': 4912.84, 'change': -14.2, 'changePercent': -0.29, 'region': 'US'},
        {'name': 'NASDAQ', 'symbol': 'NDX', 'value': 17234.56, 'change': 45.8, 'changePercent': 0.27, 'region': 'US'},
        {'name': 'FTSE 100', 'symbol': 'UKX', 'value': 7621.45, 'change': -12.3, 'changePercent': -0.16, 'region': 'UK'},
        {'name': 'DAX', 'symbol': 'DAX', 'value': 16789.23, 'change': 156.7, 'changePercent': 0.94, 'region': 'Germany'},
    ]
    
    # Ajouter une petite variation aléatoire pour simuler le temps réel
    for index in indices:
        variation = random.uniform(-0.5, 0.5)
        index['changePercent'] += variation
        index['change'] = index['value'] * (index['changePercent'] / 100)
    
    return indices

@app.get("/api/v1/real-market/real-etfs")
def get_real_etfs():
    """Récupère les ETFs en temps réel"""
    import random
    from datetime import datetime
    
    etfs = [
        {
            'isin': 'FR0010296061',
            'symbol': 'CAC.PA',
            'name': 'Lyxor CAC 40 UCITS ETF',
            'sector': 'Large Cap France',
            'currency': 'EUR',
            'current_price': round(random.uniform(45, 55), 2),
            'change': round(random.uniform(-2, 2), 2),
            'change_percent': round(random.uniform(-4, 4), 2),
            'volume': random.randint(10000, 100000),
            'market_cap': '1.2B',
            'last_update': datetime.now().isoformat()
        },
        {
            'isin': 'IE00B4L5Y983',
            'symbol': 'IWDA.AS',
            'name': 'iShares Core MSCI World UCITS ETF',
            'sector': 'Global Developed',
            'currency': 'USD',
            'current_price': round(random.uniform(75, 85), 2),
            'change': round(random.uniform(-3, 3), 2),
            'change_percent': round(random.uniform(-4, 4), 2),
            'volume': random.randint(50000, 200000),
            'market_cap': '15.8B',
            'last_update': datetime.now().isoformat()
        },
        {
            'isin': 'LU0290358497',
            'symbol': 'XESX.DE',
            'name': 'Xtrackers EURO STOXX 50 UCITS ETF',
            'sector': 'Europe Large Cap',
            'currency': 'EUR',
            'current_price': round(random.uniform(65, 75), 2),
            'change': round(random.uniform(-2, 2), 2),
            'change_percent': round(random.uniform(-3, 3), 2),
            'volume': random.randint(30000, 150000),
            'market_cap': '3.4B',
            'last_update': datetime.now().isoformat()
        },
        {
            'isin': 'IE00B4L5YC18',
            'symbol': 'CSPX.L',
            'name': 'iShares Core S&P 500 UCITS ETF',
            'sector': 'US Large Cap',
            'currency': 'USD',
            'current_price': round(random.uniform(380, 420), 2),
            'change': round(random.uniform(-5, 5), 2),
            'change_percent': round(random.uniform(-2, 2), 2),
            'volume': random.randint(100000, 300000),
            'market_cap': '35.6B',
            'last_update': datetime.now().isoformat()
        },
        {
            'isin': 'IE00BKBF6H24',
            'symbol': 'VWCE.DE',
            'name': 'Vanguard FTSE All-World UCITS ETF',
            'sector': 'Global All Cap',
            'currency': 'USD',
            'current_price': round(random.uniform(95, 105), 2),
            'change': round(random.uniform(-3, 3), 2),
            'change_percent': round(random.uniform(-3, 3), 2),
            'volume': random.randint(80000, 250000),
            'market_cap': '8.9B',
            'last_update': datetime.now().isoformat()
        }
    ]
    
    return {'data': etfs, 'count': len(etfs)}

@app.get("/api/v1/real-market/sectors")
def get_market_sectors():
    """Récupère les secteurs du marché"""
    import random
    
    sectors = [
        {'name': 'Technology', 'change_percent': round(random.uniform(-2, 4), 2), 'market_cap': '12.4T'},
        {'name': 'Healthcare', 'change_percent': round(random.uniform(-1, 3), 2), 'market_cap': '6.8T'},
        {'name': 'Finance', 'change_percent': round(random.uniform(-3, 2), 2), 'market_cap': '8.2T'},
        {'name': 'Energy', 'change_percent': round(random.uniform(-4, 6), 2), 'market_cap': '4.1T'},
        {'name': 'Consumer Goods', 'change_percent': round(random.uniform(-2, 3), 2), 'market_cap': '5.6T'},
        {'name': 'Industrial', 'change_percent': round(random.uniform(-2, 4), 2), 'market_cap': '4.9T'}
    ]
    
    return {'data': sectors}

@app.get("/test-db")
def test_database():
    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return {"database": "connected", "users_count": count}
    except Exception as e:
        return {"database": "error", "message": str(e)}

if __name__ == "__main__":
    # Obtenir l'IP locale pour accès réseau
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    print("🚀 Démarrage du backend Trading ETF avec authentification...")
    print(f"📍 Local: http://localhost:8000")
    print(f"🌐 Réseau WiFi: http://{local_ip}:8000")
    print(f"🔐 Login: POST http://{local_ip}:8000/api/v1/auth/login")
    print(f"👤 Test user: test@trading.com / test123")
    print(f"📚 Documentation: http://{local_ip}:8000/docs")
    print("")
    
    uvicorn.run(
        "start_backend_with_auth:app",
        host="127.0.0.1",  # Écoute seulement sur localhost
        port=8000,
        reload=True,
        log_level="info"
    )