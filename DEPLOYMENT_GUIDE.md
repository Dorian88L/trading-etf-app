# 🚀 Guide de Déploiement - Application Trading ETF

## 📋 Vue d'ensemble

Application web complète de trading ETF avec authentification, données de marché en temps réel, signaux de trading et interface utilisateur moderne.

**Architecture :**
- **Backend** : FastAPI (Python) avec PostgreSQL et Redis
- **Frontend** : React TypeScript avec Tailwind CSS
- **Base de données** : PostgreSQL + TimescaleDB
- **Cache** : Redis
- **Authentification** : JWT avec OAuth2

---

## 🎯 Prérequis Debian

### 1. Mise à jour du système
```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Installation des dépendances système
```bash
# Python et outils de développement
sudo apt install -y python3 python3-pip python3-venv python3-dev

# Node.js et npm (version 18+)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# PostgreSQL et Redis
sudo apt install -y postgresql postgresql-contrib redis-server

# Outils système
sudo apt install -y git curl wget nginx supervisor
```

### 3. Vérification des versions
```bash
python3 --version   # >= 3.9
node --version      # >= 18.0
npm --version       # >= 8.0
psql --version      # >= 12.0
redis-server --version  # >= 6.0
```

---

## 🗃️ Configuration Base de Données

### 1. PostgreSQL
```bash
# Démarrer et activer PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Créer utilisateur et base de données
sudo -u postgres psql << EOF
CREATE USER trading_user WITH PASSWORD 'trading_password_secure_2024';
CREATE DATABASE trading_etf OWNER trading_user;
GRANT ALL PRIVILEGES ON DATABASE trading_etf TO trading_user;
\q
EOF

# Installer TimescaleDB (optionnel pour les données temporelles)
sudo apt install -y postgresql-15-timescaledb
echo "shared_preload_libraries = 'timescaledb'" | sudo tee -a /etc/postgresql/15/main/postgresql.conf
sudo systemctl restart postgresql
```

### 2. Redis
```bash
# Démarrer et activer Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Configuration Redis (optionnel)
sudo sed -i 's/# maxmemory <bytes>/maxmemory 256mb/' /etc/redis/redis.conf
sudo sed -i 's/# maxmemory-policy noeviction/maxmemory-policy allkeys-lru/' /etc/redis/redis.conf
sudo systemctl restart redis-server
```

---

## 📦 Déploiement de l'Application

### 1. Clonage du repository
```bash
# Créer utilisateur dédié (recommandé)
sudo adduser tradingapp
sudo usermod -aG sudo tradingapp
su - tradingapp

# Cloner le projet
git clone <VOTRE_REPO_URL> /home/tradingapp/trading-etf-app
cd /home/tradingapp/trading-etf-app
```

### 2. Configuration Backend
```bash
cd backend

# Créer environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer dépendances
pip install -r requirements.txt

# Variables d'environnement
cp .env.example .env
nano .env
```

**Contenu du fichier `.env` :**
```env
# Base de données
DATABASE_URL=postgresql://trading_user:trading_password_secure_2024@localhost:5432/trading_etf

# Redis
REDIS_URL=redis://localhost:6379

# Sécurité
JWT_SECRET_KEY=votre_cle_secrete_tres_longue_et_complexe_2024
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application
ENVIRONMENT=production
DEBUG=False

# CORS (ajuster selon vos domaines)
CORS_ALLOWED_ORIGINS=http://localhost:80,http://votre-domaine.com

# API Keys (optionnel pour données réelles)
ALPHA_VANTAGE_API_KEY=votre_cle_alpha_vantage
YAHOO_FINANCE_API_KEY=votre_cle_yahoo
```

### 3. Initialisation Base de Données
```bash
# Initialiser les tables et données
python init_database_complete.py

# Créer utilisateur de test
python create_test_user.py
```

### 4. Configuration Frontend
```bash
cd ../frontend

# Installer dépendances
npm install

# Variables d'environnement
echo "REACT_APP_API_URL=http://localhost:8443" > .env

# Build production
npm run build
```

---

## 🔧 Configuration Production

### 1. Nginx (Proxy + Serveur statique)
```bash
sudo nano /etc/nginx/sites-available/trading-etf
```

**Configuration Nginx :**
```nginx
server {
    listen 80;
    server_name votre-domaine.com www.votre-domaine.com;

    # Frontend (fichiers statiques)
    location / {
        root /home/tradingapp/trading-etf-app/frontend/build;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8443;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Documentation API
    location /docs {
        proxy_pass http://127.0.0.1:8443;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
# Activer le site
sudo ln -s /etc/nginx/sites-available/trading-etf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 2. Supervisor (Gestion des processus)
```bash
sudo nano /etc/supervisor/conf.d/trading-backend.conf
```

**Configuration Supervisor :**
```ini
[program:trading-backend]
command=/home/tradingapp/trading-etf-app/backend/venv/bin/python start_backend_with_auth.py
directory=/home/tradingapp/trading-etf-app/backend
user=tradingapp
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/trading-backend.log
environment=PYTHONPATH="/home/tradingapp/trading-etf-app/backend"
```

```bash
# Recharger et démarrer
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start trading-backend
```

---

## 🔒 Sécurité Production

### 1. Firewall
```bash
# UFW Configuration
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### 2. SSL/TLS avec Let's Encrypt
```bash
# Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtenir certificat
sudo certbot --nginx -d votre-domaine.com -d www.votre-domaine.com

# Renouvellement automatique
sudo crontab -e
# Ajouter : 0 12 * * * /usr/bin/certbot renew --quiet
```

### 3. Sécurité Base de Données
```bash
# PostgreSQL
sudo nano /etc/postgresql/15/main/pg_hba.conf
# Modifier : local all all md5

# Redis
sudo nano /etc/redis/redis.conf
# Ajouter : requirepass votre_mot_de_passe_redis_secure
# bind 127.0.0.1
```

---

## 🚀 Démarrage Application

### 1. Services
```bash
# Démarrer tous les services
sudo systemctl start postgresql redis-server nginx supervisor

# Vérifier les statuts
sudo systemctl status postgresql redis-server nginx supervisor
```

### 2. Application
```bash
# Backend
sudo supervisorctl start trading-backend
sudo supervisorctl status

# Vérifier les logs
sudo tail -f /var/log/trading-backend.log
```

### 3. Tests
```bash
# Health check backend
curl http://localhost:8443/health

# Test frontend
curl http://localhost/

# Test API
curl -X POST http://localhost/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@trading.com&password=test123"
```

---

## 📊 Monitoring et Logs

### 1. Logs Application
```bash
# Backend
sudo tail -f /var/log/trading-backend.log

# Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# PostgreSQL
sudo tail -f /var/log/postgresql/postgresql-15-main.log
```

### 2. Monitoring Système
```bash
# Processus
sudo supervisorctl status
ps aux | grep -E "(python|nginx|postgres|redis)"

# Ports
sudo netstat -tlnp | grep -E ":80|:8443|:5432|:6379"

# Ressources
htop
df -h
free -h
```

---

## 🔄 Maintenance

### 1. Mises à jour
```bash
# Code application
cd /home/tradingapp/trading-etf-app
git pull origin main

# Backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo supervisorctl restart trading-backend

# Frontend
cd ../frontend
npm install
npm run build
sudo systemctl reload nginx
```

### 2. Sauvegardes
```bash
# Base de données
pg_dump -h localhost -U trading_user trading_etf > backup_$(date +%Y%m%d_%H%M%S).sql

# Code et configuration
tar -czf backup_app_$(date +%Y%m%d_%H%M%S).tar.gz /home/tradingapp/trading-etf-app
```

---

## 🆘 Dépannage

### 1. Problèmes courants
```bash
# Backend ne démarre pas
sudo supervisorctl status trading-backend
sudo supervisorctl tail trading-backend

# Base de données inaccessible
sudo systemctl status postgresql
sudo -u postgres psql -c "SELECT version();"

# Redis inaccessible
sudo systemctl status redis-server
redis-cli ping

# Nginx erreur 502
sudo nginx -t
sudo systemctl status nginx
curl http://localhost:8443/health
```

### 2. Reset complet
```bash
# Arrêter services
sudo supervisorctl stop trading-backend
sudo systemctl stop nginx

# Reset base de données (ATTENTION: supprime toutes les données)
sudo -u postgres dropdb trading_etf
sudo -u postgres createdb trading_etf -O trading_user
python init_database_complete.py

# Redémarrer
sudo supervisorctl start trading-backend
sudo systemctl start nginx
```

---

## 📝 URLs Finales

- **Application** : http://votre-domaine.com
- **API Documentation** : http://votre-domaine.com/docs
- **Admin PostgreSQL** : Installer pgAdmin4 si nécessaire

**Comptes par défaut :**
- Email : `test@trading.com`
- Mot de passe : `test123`

---

## 📞 Support

Pour toute question ou problème, vérifiez d'abord les logs et consultez la documentation FastAPI et React officielle.

**Version :** 1.0.0  
**Dernière mise à jour :** Juin 2025