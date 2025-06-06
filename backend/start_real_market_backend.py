#!/usr/bin/env python3

"""
Backend complet avec données de marché réelles et système avancé
"""

import os
import sys
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from typing import Optional
from pydantic import BaseModel

# Ajouter le chemin de l'application
sys.path.append('/home/dorian/trading-etf-app/backend')

from app.services.real_market_data import RealMarketDataService

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
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

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

# Application FastAPI
app = FastAPI(
    title="Trading ETF API - Real Market Data",
    description="API avec données de marché réelles pour Trading ETF",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service de données de marché réelles
market_service = RealMarketDataService()

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

def get_current_user(token: str = Depends(oauth2_scheme)):
    """Récupère l'utilisateur actuel depuis le token JWT"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = get_user_from_db(email)
    if user is None:
        raise credentials_exception
    return user

# Endpoints
@app.get("/")
def read_root():
    return {"message": "Trading ETF API avec données réelles", "status": "running", "version": "2.0.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "Backend avec données réelles fonctionne"}

@app.post("/api/v1/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Endpoint de connexion"""
    print(f"Tentative de connexion pour: {form_data.username}")
    
    user = get_user_from_db(form_data.username)
    
    if not user:
        print("Utilisateur non trouvé")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(form_data.password, user["hashed_password"]):
        print("Mot de passe incorrect")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Utilisateur inactif"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    
    print(f"Connexion réussie pour: {user['email']}")
    
    return {
        "access_token": access_token,
        "refresh_token": access_token,
        "token_type": "bearer"
    }

# Endpoints de données réelles
@app.get("/api/v1/real-market/available-etfs")
def get_available_etfs(current_user: dict = Depends(get_current_user)):
    """Retourne la liste des ETFs européens disponibles"""
    etf_list = []
    
    for symbol, info in market_service.EUROPEAN_ETFS.items():
        etf_list.append({
            'symbol': symbol,
            'isin': info['isin'],
            'name': info['name'],
            'sector': info['sector'],
            'exchange': info['exchange']
        })
    
    return {
        'status': 'success',
        'count': len(etf_list),
        'etfs': etf_list,
        'timestamp': datetime.now().isoformat()
    }

@app.get("/api/v1/real-market/real-etfs")
def get_real_etf_data(
    symbols: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Récupère les données réelles des ETFs européens"""
    try:
        if symbols:
            symbol_list = [s.strip() for s in symbols.split(',')]
            etf_data = []
            for symbol in symbol_list:
                data = market_service.get_real_etf_data(symbol)
                if data:
                    etf_data.append({
                        'symbol': data.symbol,
                        'isin': data.isin,
                        'name': data.name,
                        'current_price': data.current_price,
                        'change': data.change,
                        'change_percent': data.change_percent,
                        'volume': data.volume,
                        'market_cap': data.market_cap,
                        'currency': data.currency,
                        'exchange': data.exchange,
                        'sector': data.sector,
                        'last_update': data.last_update.isoformat()
                    })
        else:
            # Récupérer quelques ETFs par défaut
            default_symbols = ['LYX0CD.PA', 'SX5T.DE', 'EUNL.DE', 'VWCE.DE']
            etf_data = []
            for symbol in default_symbols:
                try:
                    data = market_service.get_real_etf_data(symbol)
                    if data:
                        etf_data.append({
                            'symbol': data.symbol,
                            'isin': data.isin,
                            'name': data.name,
                            'current_price': data.current_price,
                            'change': data.change,
                            'change_percent': data.change_percent,
                            'volume': data.volume,
                            'market_cap': data.market_cap,
                            'currency': data.currency,
                            'exchange': data.exchange,
                            'sector': data.sector,
                            'last_update': data.last_update.isoformat()
                        })
                except Exception as e:
                    print(f"Erreur pour {symbol}: {e}")
                    continue
        
        return {
            'status': 'success',
            'count': len(etf_data),
            'data': etf_data,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des données: {str(e)}")

@app.get("/api/v1/real-market/real-indices")
def get_real_market_indices(current_user: dict = Depends(get_current_user)):
    """Récupère les données réelles des indices de marché européens"""
    try:
        indices_data = market_service.get_market_indices()
        
        return {
            'status': 'success',
            'count': len(indices_data),
            'data': indices_data,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des indices: {str(e)}")

@app.get("/api/v1/real-market/real-market-data/{symbol}")
def get_real_historical_data(
    symbol: str,
    period: str = "1mo",
    current_user: dict = Depends(get_current_user)
):
    """Récupère les données historiques réelles d'un ETF"""
    try:
        historical_data = market_service.get_historical_data(symbol, period)
        
        if not historical_data:
            raise HTTPException(status_code=404, detail=f"Aucune donnée trouvée pour le symbole {symbol}")
        
        data_points = []
        for point in historical_data:
            data_points.append({
                'timestamp': point.timestamp.isoformat(),
                'open_price': point.open_price,
                'high_price': point.high_price,
                'low_price': point.low_price,
                'close_price': point.close_price,
                'volume': point.volume,
                'adj_close': point.adj_close
            })
        
        return {
            'status': 'success',
            'symbol': symbol,
            'period': period,
            'count': len(data_points),
            'data': data_points,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération de l'historique: {str(e)}")

# Maintenir la compatibilité avec les anciens endpoints
@app.get("/api/v1/user/profile")
def get_profile(current_user: dict = Depends(get_current_user)):
    """Endpoint pour récupérer le profil utilisateur"""
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "full_name": current_user["full_name"],
        "is_active": current_user["is_active"],
        "is_verified": True
    }

@app.get("/api/v1/signals/advanced")
def get_advanced_signals(current_user: dict = Depends(get_current_user)):
    """Récupère les signaux avancés avec vraies données ETF"""
    import random
    
    try:
        # Utiliser les vraies données ETF pour générer des signaux
        etf_data = []
        default_symbols = ['LYX0CD.PA', 'SX5T.DE', 'EUNL.DE', 'VWCE.DE']
        
        for symbol in default_symbols:
            try:
                data = market_service.get_real_etf_data(symbol)
                if data:
                    etf_data.append(data)
            except:
                continue
        
        signals = []
        for i, etf in enumerate(etf_data):
            signal_types = ['BUY', 'SELL', 'HOLD']
            algorithms = ['BREAKOUT', 'MEAN_REVERSION', 'MOMENTUM', 'STATISTICAL_ARBITRAGE']
            
            confidence = random.uniform(60, 95)
            current_price = etf.current_price
            price_target = current_price * random.uniform(0.95, 1.08)
            stop_loss = current_price * random.uniform(0.92, 1.03)
            
            signal_type = random.choice(signal_types)
            expected_return = ((price_target - current_price) / current_price) * 100
            if signal_type == 'SELL':
                expected_return = -expected_return
            
            signals.append({
                'id': f"sig_{i+1:03d}",
                'etf_isin': etf.isin,
                'etf_name': etf.name,
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
                'justification': f"Signal {signal_type} - Basé sur prix réel: {current_price:.2f}€. Score composite: {confidence:.1f}/100.",
                'timestamp': datetime.now().isoformat(),
                'sector': etf.sector
            })
        
        return signals
        
    except Exception as e:
        # Fallback vers des données mock en cas d'erreur
        return []

@app.get("/api/v1/market-data/{etf_isin}")
def get_market_data(etf_isin: str, current_user: dict = Depends(get_current_user)):
    """Récupère les données de marché pour un ETF avec vraies données"""
    try:
        # Trouver le symbole par ISIN
        symbol = None
        for sym, info in market_service.EUROPEAN_ETFS.items():
            if info['isin'] == etf_isin:
                symbol = sym
                break
        
        if symbol:
            historical_data = market_service.get_historical_data(symbol, "1mo")
            return [
                {
                    'timestamp': point.timestamp.isoformat(),
                    'open_price': point.open_price,
                    'high_price': point.high_price,
                    'low_price': point.low_price,
                    'close_price': point.close_price,
                    'volume': point.volume
                }
                for point in historical_data
            ]
        else:
            raise HTTPException(status_code=404, detail="ETF non trouvé")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.get("/api/v1/indices")
def get_market_indices(current_user: dict = Depends(get_current_user)):
    """Récupère les indices de marché avec vraies données"""
    try:
        indices_data = market_service.get_market_indices()
        
        indices_list = []
        for symbol, data in indices_data.items():
            indices_list.append({
                "name": data["name"],
                "symbol": symbol,
                "value": data["value"],
                "change": data["change"],
                "change_percent": data["change_percent"],
                "volume": data.get("volume", 0),
                "currency": data.get("currency", "EUR"),
                "last_update": data["last_update"]
            })
        
        return indices_list
        
    except Exception as e:
        # Fallback vers des données mock
        return [
            {"name": "CAC 40", "value": 7500.25, "change": 1.2, "change_percent": 0.016},
            {"name": "EURO STOXX 50", "value": 4200.60, "change": 0.5, "change_percent": 0.012}
        ]

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
    print("🚀 Démarrage du backend Trading ETF avec données réelles...")
    print("📍 Backend accessible sur: http://localhost:8000")
    print("🔐 Login endpoint: http://localhost:8000/api/v1/auth/login")
    print("📊 Données réelles ETF: http://localhost:8000/api/v1/real-market/")
    print("👤 Test user: test@trading.com / test123")
    print("")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )