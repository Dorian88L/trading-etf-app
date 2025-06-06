# Trading ETF - Application de Trading Court Terme

Application web progressive (PWA) d'analyse et de trading court terme d'ETF avec signaux d'achat/vente automatisés, optimisée pour compte-titres ordinaire.

## 🚀 Fonctionnalités

### 📊 Analyse Technique Avancée
- **Indicateurs techniques complets** : SMA, EMA, RSI, MACD, Bollinger Bands, ATR, OBV, VWAP
- **Moteur d'analyse** : Évaluation automatique des tendances et patterns
- **Scoring multicritères** : Technical score, fundamental score, risk score

### 🎯 Signaux de Trading Automatisés
- **4 types de signaux** : BUY, SELL, HOLD, WAIT
- **Niveau de confiance** : Score de 0 à 100% pour chaque signal
- **Prix cibles et stop-loss** : Calculs automatiques basés sur l'analyse technique
- **Expiration automatique** : Gestion du cycle de vie des signaux

### 💼 Gestion de Portefeuille
- **Suivi des positions** : Quantités, prix moyens, P&L en temps réel
- **Historique des transactions** : Audit trail complet
- **Performance tracking** : Métriques de performance vs benchmarks
- **Gestion des risques** : Position sizing et diversification

### 🔔 Système d'Alertes Intelligent
- **Notifications push** : Alertes temps réel via PWA
- **Personnalisation** : Seuils configurables par utilisateur
- **Multi-canaux** : In-app, email, notifications push
- **Filtrage avancé** : Par type, priorité, ETF

### 📱 Progressive Web App (PWA)
- **Installation native** : Fonctionne comme une app mobile
- **Mode hors-ligne** : Cache intelligent pour consultation offline
- **Notifications push** : Alertes même quand l'app est fermée
- **Performance optimisée** : Chargement rapide et UX fluide

## 🏗️ Architecture Technique

### Backend (FastAPI + Python)
- **API REST** : FastAPI avec documentation automatique
- **Base de données** : PostgreSQL + TimescaleDB pour les time-series
- **Cache** : Redis pour les performances
- **Tâches asynchrones** : Celery pour la collecte de données
- **Authentification** : JWT + OAuth2
- **Sécurité** : Rate limiting, validation, CORS

### Frontend (React + TypeScript)
- **React 18+** : Interface utilisateur moderne et réactive
- **TypeScript** : Type safety et meilleure DX
- **Tailwind CSS** : Design system cohérent
- **Redux Toolkit** : Gestion d'état globale
- **React Query** : Cache et synchronisation des données API
- **Chart.js** : Visualisations financières interactives

### Infrastructure
- **Docker** : Containerisation complète
- **Docker Compose** : Orchestration des services
- **PostgreSQL + TimescaleDB** : Base de données time-series optimisée
- **Redis** : Cache et broker pour Celery
- **Nginx** : Reverse proxy et serving des assets statiques

## 📋 Prérequis

- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum
- 10GB espace disque

## 🚀 Installation et Démarrage

### 1. Cloner le repository
```bash
git clone <repository-url>
cd trading-etf-app
```

### 2. Configuration des variables d'environnement
```bash
# Backend - Créer un fichier .env dans /backend
cp backend/.env.example backend/.env
# Modifier les valeurs selon votre environnement
```

### 3. Démarrage avec Docker Compose
```bash
# Rendre le script exécutable
chmod +x start_dev.sh

# Démarrer l'application
./start_dev.sh
```

### 4. Accès à l'application
- **Frontend** : http://localhost:3000
- **Backend API** : http://localhost:8000
- **Documentation API** : http://localhost:8000/docs
- **Database** : PostgreSQL sur port 5432
- **Redis** : Port 6379

### 5. Comptes par défaut
L'application démarre avec des données d'exemple. Créez un compte via l'interface d'inscription.

## 📊 Sources de Données

### APIs Financières Supportées
- **Yahoo Finance** : Données de marché en temps réel
- **Alpha Vantage** : Données fondamentales et techniques
- **APIs ETF** : iShares, Vanguard, Amundi (si disponibles)

### ETF Pré-configurés
- Lyxor CAC 40 (FR0010296061)
- iShares Core MSCI World (IE00B4L5Y983)
- Xtrackers MSCI World (LU0274211217)
- iShares Core S&P 500 (IE00B4L5YC18)
- Lyxor MSCI Emerging Markets (FR0010315770)
- Et plus...

## 🔧 Configuration

### Variables d'environnement Backend
```env
# Database
DATABASE_URL=postgresql://trading_user:trading_password@postgres:5432/trading_etf

# Redis
REDIS_URL=redis://redis:6379

# Security
JWT_SECRET_KEY=your-secret-key-change-in-production

# External APIs
ALPHA_VANTAGE_API_KEY=your-api-key
YAHOO_FINANCE_API_KEY=your-api-key

# Trading Parameters
MIN_SIGNAL_CONFIDENCE=60.0
MAX_POSITION_SIZE=0.1
DEFAULT_STOP_LOSS_PCT=0.05
```

### Configuration Frontend
```env
# API URL
REACT_APP_API_URL=http://localhost:8000

# Features flags
REACT_APP_ENABLE_NOTIFICATIONS=true
REACT_APP_ENABLE_OFFLINE_MODE=true
```

## 📈 Utilisation

### 1. Dashboard
- Vue d'ensemble du portefeuille
- Signaux actifs en temps réel
- Performance des marchés
- Alertes récentes

### 2. Analyse ETF
- Recherche et filtrage d'ETF
- Graphiques techniques interactifs
- Indicateurs et signaux détaillés
- Historique des performances

### 3. Gestion de Portefeuille
- Suivi des positions en temps réel
- Historique des transactions
- Calcul automatique du P&L
- Métriques de performance

### 4. Signaux de Trading
- Liste des signaux actifs
- Historique et performance
- Filtrage par confiance et type
- Détails et justifications

### 5. Alertes et Notifications
- Configuration des seuils
- Gestion des notifications push
- Historique des alertes
- Personnalisation par préférences

## 🔒 Sécurité et Conformité

### Mesures de Sécurité
- **Authentification JWT** : Tokens sécurisés avec expiration
- **Rate limiting** : Protection contre les attaques par déni de service
- **Validation des données** : Pydantic models pour la validation
- **HTTPS/TLS** : Chiffrement des communications
- **CORS** : Configuration stricte des origins autorisées

### Conformité Financière
- **Disclaimer** : Pas de conseil en investissement
- **Risk warning** : Avertissements sur les risques
- **Audit trail** : Traçabilité complète des signaux et transactions
- **RGPD** : Gestion des données personnelles

## 🚀 Déploiement Production

### Docker Production
```bash
# Build des images optimisées
docker-compose -f docker-compose.prod.yml build

# Déploiement
docker-compose -f docker-compose.prod.yml up -d
```

### Variables d'environnement Production
- Modifier toutes les clés secrètes
- Configurer les URLs de production
- Activer HTTPS/SSL
- Configurer les backups automatiques

## 📊 Monitoring et Métriques

### Métriques Applicatives
- **Prometheus** : Collecte des métriques système et applicatives
- **Health checks** : Endpoints de santé pour tous les services
- **Logs structurés** : Logging JSON pour analyse

### Critères de Succès
- **Latence API** : < 200ms (95e percentile)
- **Disponibilité** : > 99.5%
- **Précision signaux** : > 60% sur 3 mois
- **Temps de chargement** : < 3s first paint

## 🤝 Contribution

### Développement Local
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm start
```

### Standards de Code
- **Backend** : Black, isort, flake8, mypy
- **Frontend** : ESLint, Prettier, TypeScript strict
- **Tests** : pytest (backend), Jest (frontend)

## 📝 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## ⚠️ Avertissement

Cette application est destinée à des fins éducatives et d'information uniquement. Les signaux de trading générés ne constituent pas des conseils en investissement. Tradez à vos propres risques et consultez un conseiller financier professionnel avant de prendre des décisions d'investissement.

## 📞 Support

Pour toute question ou support :
- 📧 Email : support@tradingetf.com
- 📖 Documentation : [https://docs.tradingetf.com](https://docs.tradingetf.com)
- 🐛 Issues : [GitHub Issues](https://github.com/tradingetf/issues)

---

**Trading ETF** - Votre assistant IA pour le trading d'ETF court terme 🚀📈