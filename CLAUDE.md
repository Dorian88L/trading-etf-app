# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🏗️ Architecture Overview

**Trading ETF Application** - Modern web application for ETF trading with real-time market data, advanced trading signals, and portfolio management.

### IMPORTANT :
Je ne veux que des données réelles, pas de simulation ou données mockées !! En production je travaille sur docker, en dev regarde si docker est utilisé, sinon fait en local

### Tech Stack
- **Backend**: FastAPI (Python 3.11+) with PostgreSQL, Redis, Celery
- **Frontend**: React 18 + TypeScript, Redux Toolkit, TanStack Query, Tailwind CSS
- **Infrastructure**: Docker + Traefik with SSL automation
- **Charts**: Chart.js with react-chartjs-2
- **Market Data**: Multi-source ETF data (Yahoo Finance, Alpha Vantage, TwelveData, etc.)

### Key Architecture Patterns
- **Service Layer Pattern**: Business logic in `/backend/app/services/`
- **Multi-source Data Aggregation**: Intelligent fallback system for market data
- **Caching Strategy**: Redis for performance optimization
- **Signal Generation**: Advanced trading algorithms with confidence scoring

## 🛠️ Development Commands

### Quick Start (Docker)
```bash
./scripts/dev.sh          # Full development environment with Traefik
./scripts/stop.sh         # Stop all services
./scripts/prod.sh         # Production deployment
```

### Manual Development
```bash
# Backend (standalone)
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python start_backend_with_auth.py

# Frontend
cd frontend
npm install
npm start
npm run build
npm test
```

### Database & Cache
- **PostgreSQL**: Port 5432 (Docker) / 5433 (local)
- **Redis**: Port 6379
- **Migrations**: Alembic in `/backend/alembic/`

## 🔧 Common Development Tasks

### Testing
- **Frontend**: `npm test` (React Testing Library + Jest)
- **Backend**: `pytest` (if configured)

### Build & Deployment
- **Frontend Build**: `npm run build`
- **Docker Build**: Automatic via compose scripts
- **Production**: Uses multi-stage Docker builds with SSL certificates

### API Documentation
- **Swagger UI**: `/docs` endpoint
- **ReDoc**: `/redoc` endpoint
- **Health Check**: `/api/health`

## 📁 Important File Locations

### Backend Structure
```
backend/app/
├── api/v1/endpoints/     # API endpoints (auth, portfolio, signals, etc.)
├── core/                 # Config, database, security, Redis setup
├── models/               # SQLAlchemy ORM models
├── services/             # Business logic (20+ services)
│   ├── multi_source_etf_data.py    # Core data aggregation
│   ├── signal_generator.py         # Trading signals
│   └── technical_analysis.py       # Technical indicators
└── schemas/              # Pydantic validation schemas
```

### Frontend Structure
```
frontend/src/
├── components/           # Reusable UI components
├── pages/               # Route pages (Dashboard, ETFList, Portfolio, etc.)
├── store/slices/        # Redux state management
├── services/            # API services
└── hooks/               # Custom React hooks
```

### Configuration Files
- **Environment**: `.env.dev`, `.env.prod`
- **Docker**: `docker-compose.yml`, `docker-compose.prod.yml`
- **Database**: Connection via environment variables
- **API Keys**: Stored in environment files (not committed)

## 🎯 Key Features

### Market Data Integration
- **Primary Source**: Yahoo Finance (yfinance)
- **Fallback Sources**: TwelveData, EODHD, Finnhub, Alpha Vantage, FMP
- **European ETFs**: IWDA, VWCE, CSPX focus
- **Real-time Data**: Intelligent caching with Redis

### Trading Signals
- **Algorithms**: Multiple signal generation methods
- **Confidence Scoring**: Advanced scoring system
- **Signal Types**: BUY/SELL/HOLD/WAIT recommendations
- **Technical Analysis**: RSI, MACD, Bollinger Bands, etc.

### User Management
- **Authentication**: JWT with refresh tokens
- **Features**: Watchlists, portfolios, preferences
- **Test Account**: test@trading.com / test123

## 🐛 Development Notes

### Current Development Status
The application is actively developed with recent focus on:
- Real-time market data optimization
- Multi-source data integration improvements
- Frontend compilation fixes
- Portfolio management enhancements

### Known Development Patterns
- **Hot Reload**: Enabled in development mode via Docker volumes
- **API Versioning**: `/api/v1/` prefix for all endpoints
- **Error Handling**: Centralized via FastAPI exception handlers
- **Logging**: Structured logging to `/backend/logs/`

### Environment Access
- **Development**: http://localhost (Traefik routing)
- **API**: http://localhost/api/v1/
- **Traefik Dashboard**: http://localhost:8080
- **Database**: PostgreSQL on localhost:5432 (Docker)

### Market Data Sources Priority
1. Yahoo Finance (primary)
2. TwelveData, EODHD, Finnhub (high priority)
3. Alpha Vantage, FMP, Marketstack (fallback)

Rate limiting and intelligent fallback are implemented in `multi_source_etf_data.py`.