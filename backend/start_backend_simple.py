#!/usr/bin/env python3

"""
Script de démarrage simplifié pour le backend Trading ETF
"""

import os
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Configuration simple
os.environ["DATABASE_URL"] = "postgresql://trading_user:trading_password@localhost:5433/trading_etf"
os.environ["REDIS_URL"] = "redis://localhost:6380" 
os.environ["JWT_SECRET_KEY"] = "dev-secret-key-not-for-production"
os.environ["ENVIRONMENT"] = "development"

# Application FastAPI simple pour tester
app = FastAPI(
    title="Trading ETF API - Simple",
    description="Version simplifiée pour test",
    version="1.0.0"
)

@app.get("/")
def read_root():
    return {"message": "Trading ETF API Simple", "status": "running"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "Backend is running"}

@app.get("/test-db")
def test_database():
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="localhost",
            port=5433,
            database="trading_etf", 
            user="trading_user",
            password="trading_password"
        )
        conn.close()
        return {"database": "connected", "status": "ok"}
    except Exception as e:
        return {"database": "error", "message": str(e)}

@app.get("/test-redis") 
def test_redis():
    try:
        import redis
        r = redis.from_url("redis://localhost:6380")
        r.ping()
        return {"redis": "connected", "status": "ok"}
    except Exception as e:
        return {"redis": "error", "message": str(e)}

if __name__ == "__main__":
    print("🚀 Démarrage du backend Trading ETF simplifié...")
    print("📍 Backend accessible sur: http://localhost:8000")
    print("🔍 Health check: http://localhost:8000/health")
    print("💾 Test DB: http://localhost:8000/test-db")
    print("🗄️ Test Redis: http://localhost:8000/test-redis")
    print("")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )