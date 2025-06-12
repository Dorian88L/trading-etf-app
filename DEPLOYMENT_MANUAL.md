# 📋 Guide de Déploiement Manuel - Trading ETF Application

## 🎯 Vue d'ensemble

Cette documentation explique comment déployer manuellement l'application Trading ETF avec :
- **Frontend React** sur le port 3000
- **Backend FastAPI** sur le port 8000  
- **Nginx avec SSL** pour les domaines `investeclaire.fr` et `api.investeclaire.fr`
- **PostgreSQL** et **Redis** pour les données

---

## 🔧 Prérequis Système

### Packages requis
```bash
sudo apt update
sudo apt install -y nginx postgresql postgresql-contrib redis-server python3 python3-pip python3-venv nodejs npm git curl
```

### Vérification des versions
```bash
node --version    # >= 18.x
npm --version     # >= 8.x
python3 --version # >= 3.8
psql --version    # >= 12.x
redis-server --version # >= 6.x
nginx -v          # >= 1.18
```

---

## 🗃️ Configuration Base de Données

### PostgreSQL
```bash
# Démarrer PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Créer l'utilisateur et la base
sudo -u postgres psql
```

```sql
-- Dans psql
CREATE USER trading_user WITH PASSWORD 'Gnouconfi876*';
CREATE DATABASE trading_etf OWNER trading_user;
GRANT ALL PRIVILEGES ON DATABASE trading_etf TO trading_user;
\q
```

### Redis
```bash
# Démarrer Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Vérifier Redis
redis-cli ping  # Doit retourner PONG
```

---

## 🚀 Lancement du Backend (FastAPI)

### 1. Préparation de l'environnement Python
```bash
cd /home/dorian/trading-etf-app/backend

# Créer et activer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

### 2. Configuration des variables d'environnement
```bash
# Créer le fichier .env
cat > .env << 'EOF'
# Base de données
DATABASE_URL=postgresql://trading_user:Gnouconfi876*@localhost:5432/trading_etf

# Redis
REDIS_URL=redis://localhost:6379/0

# Sécurité
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API Keys (optionnel)
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
FINANCIAL_MODELING_PREP_API_KEY=your_fmp_key

# Environment
ENVIRONMENT=production
DEBUG=False

# CORS
ALLOWED_ORIGINS=https://investeclaire.fr,https://api.investeclaire.fr
EOF
```

### 3. Initialisation de la base de données
```bash
# Activer l'environnement virtuel si pas déjà fait
source venv/bin/activate

# Initialiser les tables et données
python init_database_complete.py

# Optionnel: Ajouter des données de test
python add_sample_data.py
```

### 4. Lancement du serveur backend
```bash
# Méthode 1: Script de démarrage simple
python start_backend_simple.py

# Méthode 2: Directement avec uvicorn
uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4

# Méthode 3: Avec le script de production
python start_real_market_backend.py
```

### 5. Vérification du backend
```bash
# Test de santé
curl http://127.0.0.1:8000/health

# Documentation API
curl http://127.0.0.1:8000/docs
```

---

## 🎨 Lancement du Frontend (React)

### 1. Préparation de l'environnement Node.js
```bash
cd /home/dorian/trading-etf-app/frontend

# Installer les dépendances
npm install
```

### 2. Configuration des variables d'environnement
```bash
# Créer le fichier .env
cat > .env << 'EOF'
REACT_APP_API_URL=https://api.investeclaire.fr
GENERATE_SOURCEMAP=false
EOF
```

### 3. Construction et lancement
```bash
# Méthode 1: Mode développement (avec hot reload)
npm start

# Méthode 2: Construction pour production
npm run build
# Puis servir avec un serveur statique
npx serve -s build -l 3000

# Méthode 3: Construction optimisée
npm run build:production
```

### 4. Vérification du frontend
```bash
# Vérifier que le serveur écoute
curl http://127.0.0.1:3000

# Vérifier les logs
tail -f /home/dorian/trading-etf-app/logs/frontend.log
```

---

## 🔒 Configuration SSL et Nginx

### 1. Obtention des certificats SSL

#### Option A: Let's Encrypt (Recommandé)
```bash
# Installer certbot
sudo apt install certbot python3-certbot-nginx

# Obtenir les certificats
sudo certbot certonly --standalone -d investeclaire.fr -d api.investeclaire.fr

# Les certificats seront dans:
# /etc/letsencrypt/live/investeclaire.fr/fullchain.pem
# /etc/letsencrypt/live/investeclaire.fr/privkey.pem
```

#### Option B: Certificats existants
```bash
# Si vous avez déjà des certificats
sudo mkdir -p /etc/ssl/private /etc/ssl/certs
sudo cp /path/to/your/investeclaire.fr.crt /etc/ssl/certs/
sudo cp /path/to/your/investeclaire.fr.key /etc/ssl/private/
sudo chmod 600 /etc/ssl/private/investeclaire.fr.key
```

### 2. Configuration Nginx complète

```bash
# Sauvegarder la configuration par défaut
sudo cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup

# Créer la nouvelle configuration
sudo tee /etc/nginx/sites-available/trading-etf << 'EOF'
# Configuration Nginx pour Trading ETF Application

# Redirect HTTP to HTTPS pour le domaine principal
server {
    listen 80;
    server_name investeclaire.fr www.investeclaire.fr;
    return 301 https://investeclaire.fr$request_uri;
}

# Redirect HTTP to HTTPS pour l'API
server {
    listen 80;
    server_name api.investeclaire.fr;
    return 301 https://api.investeclaire.fr$request_uri;
}

# Frontend HTTPS (investeclaire.fr)
server {
    listen 443 ssl http2;
    server_name investeclaire.fr www.investeclaire.fr;

    # Certificats SSL
    ssl_certificate /etc/ssl/certs/investeclaire.fr.crt;
    ssl_certificate_key /etc/ssl/private/investeclaire.fr.key;
    
    # Configuration SSL moderne
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_session_tickets off;
    
    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    
    # Headers de sécurité
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' https://api.investeclaire.fr wss://api.investeclaire.fr; font-src 'self';" always;

    # Redirection www -> non-www
    if ($host = www.investeclaire.fr) {
        return 301 https://investeclaire.fr$request_uri;
    }

    # Logs
    access_log /var/log/nginx/investeclaire.fr.access.log;
    error_log /var/log/nginx/investeclaire.fr.error.log;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied expired no-cache no-store private must-revalidate auth;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # Frontend React App
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Hot reload pour le développement
    location /sockjs-node {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # Static assets avec cache long
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        proxy_pass http://127.0.0.1:3000;
        expires 1y;
        add_header Cache-Control "public, immutable";
        proxy_set_header Host $host;
    }

    # Health check
    location /health {
        access_log off;
        return 200 "Frontend OK\n";
        add_header Content-Type text/plain;
    }
}

# API Backend HTTPS (api.investeclaire.fr)
server {
    listen 443 ssl http2;
    server_name api.investeclaire.fr;

    # Certificats SSL
    ssl_certificate /etc/ssl/certs/investeclaire.fr.crt;
    ssl_certificate_key /etc/ssl/private/investeclaire.fr.key;
    
    # Configuration SSL moderne
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_session_tickets off;
    
    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;

    # Headers de sécurité
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # CORS pour l'API
    add_header Access-Control-Allow-Origin "https://investeclaire.fr" always;
    add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
    add_header Access-Control-Allow-Headers "Authorization, Content-Type, Accept, Origin, X-Requested-With" always;
    add_header Access-Control-Allow-Credentials "true" always;
    add_header Access-Control-Max-Age "86400" always;

    # Logs
    access_log /var/log/nginx/api.investeclaire.fr.access.log;
    error_log /var/log/nginx/api.investeclaire.fr.error.log;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types application/json text/plain text/css application/javascript text/xml application/xml;

    # Handle preflight requests
    if ($request_method = 'OPTIONS') {
        add_header Access-Control-Allow-Origin "https://investeclaire.fr" always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Authorization, Content-Type, Accept, Origin, X-Requested-With" always;
        add_header Access-Control-Allow-Credentials "true" always;
        add_header Access-Control-Max-Age "86400" always;
        add_header Content-Length 0;
        add_header Content-Type text/plain;
        return 204;
    }

    # API Backend FastAPI
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_redirect off;
        
        # Timeouts pour l'API
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 300s;
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }

    # WebSocket support pour les données temps réel
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }

    # Health check API
    location /health {
        access_log off;
        proxy_pass http://127.0.0.1:8000/health;
        proxy_set_header Host $host;
    }

    # Documentation API (optionnel, à désactiver en production)
    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
        proxy_set_header Host $host;
        # Optionnel: protection par IP
        # allow 192.168.1.0/24;
        # deny all;
    }
}
EOF
```

### 3. Activation de la configuration

```bash
# Désactiver la configuration par défaut
sudo unlink /etc/nginx/sites-enabled/default

# Activer la nouvelle configuration
sudo ln -s /etc/nginx/sites-available/trading-etf /etc/nginx/sites-enabled/

# Tester la configuration
sudo nginx -t

# Si OK, recharger nginx
sudo systemctl reload nginx
```

### 4. Configuration du firewall

```bash
# Ouvrir les ports nécessaires
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP (redirect)
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

---

## 🎯 Scripts de Démarrage Automatique

### 1. Service Systemd pour le Backend

```bash
sudo tee /etc/systemd/system/trading-backend.service << 'EOF'
[Unit]
Description=Trading ETF Backend API
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=dorian
Group=dorian
WorkingDirectory=/home/dorian/trading-etf-app/backend
Environment=PATH=/home/dorian/trading-etf-app/backend/venv/bin
ExecStart=/home/dorian/trading-etf-app/backend/venv/bin/python start_backend_simple.py
Restart=always
RestartSec=10

# Logs
StandardOutput=append:/home/dorian/trading-etf-app/logs/backend.log
StandardError=append:/home/dorian/trading-etf-app/logs/backend.error.log

[Install]
WantedBy=multi-user.target
EOF

# Activer le service
sudo systemctl daemon-reload
sudo systemctl enable trading-backend
sudo systemctl start trading-backend
```

### 2. Service Systemd pour le Frontend

```bash
sudo tee /etc/systemd/system/trading-frontend.service << 'EOF'
[Unit]
Description=Trading ETF Frontend React
After=network.target

[Service]
Type=simple
User=dorian
Group=dorian
WorkingDirectory=/home/dorian/trading-etf-app/frontend
Environment=PATH=/usr/bin:/bin:/usr/local/bin
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10

# Logs
StandardOutput=append:/home/dorian/trading-etf-app/logs/frontend.log
StandardError=append:/home/dorian/trading-etf-app/logs/frontend.error.log

[Install]
WantedBy=multi-user.target
EOF

# Activer le service
sudo systemctl daemon-reload
sudo systemctl enable trading-frontend
sudo systemctl start trading-frontend
```

---

## 📝 Commandes de Gestion Quotidienne

### Démarrage complet
```bash
# Services système
sudo systemctl start postgresql redis-server nginx

# Applications
sudo systemctl start trading-backend trading-frontend

# Vérification
sudo systemctl status trading-backend trading-frontend nginx
```

### Arrêt complet
```bash
sudo systemctl stop trading-frontend trading-backend
sudo systemctl stop nginx redis-server postgresql
```

### Redémarrage
```bash
sudo systemctl restart trading-backend trading-frontend nginx
```

### Logs et monitoring
```bash
# Logs en temps réel
sudo journalctl -u trading-backend -f
sudo journalctl -u trading-frontend -f
tail -f /var/log/nginx/api.investeclaire.fr.access.log

# Status des services
sudo systemctl status trading-backend trading-frontend nginx postgresql redis-server

# Utilisation des ports
sudo ss -tlnp | grep -E ':3000|:8000|:80|:443'
```

---

## 🔧 Dépannage

### Backend ne démarre pas
```bash
# Vérifier les logs
sudo journalctl -u trading-backend -n 50

# Test manuel
cd /home/dorian/trading-etf-app/backend
source venv/bin/activate
python start_backend_simple.py

# Vérifier la base de données
psql -h localhost -U trading_user -d trading_etf -c "\dt"
```

### Frontend ne démarre pas
```bash
# Vérifier les logs
sudo journalctl -u trading-frontend -n 50

# Test manuel
cd /home/dorian/trading-etf-app/frontend
npm start

# Vérifier les dépendances
npm install
```

### Problèmes SSL
```bash
# Vérifier les certificats
sudo openssl x509 -in /etc/ssl/certs/investeclaire.fr.crt -text -noout

# Test SSL
openssl s_client -connect api.investeclaire.fr:443 -servername api.investeclaire.fr

# Renouveler Let's Encrypt
sudo certbot renew --dry-run
```

### Problèmes Nginx
```bash
# Tester la configuration
sudo nginx -t

# Vérifier les logs
tail -f /var/log/nginx/error.log
tail -f /var/log/nginx/api.investeclaire.fr.error.log

# Reload configuration
sudo systemctl reload nginx
```

---

## 🚀 URLs d'accès

- **Frontend** : https://investeclaire.fr
- **API Backend** : https://api.investeclaire.fr
- **Documentation API** : https://api.investeclaire.fr/docs
- **Health Check Frontend** : https://investeclaire.fr/health
- **Health Check Backend** : https://api.investeclaire.fr/health

---

## 📊 Monitoring et Maintenance

### Monitoring quotidien
```bash
# Script de vérification automatique
cat > /home/dorian/trading-etf-app/check_health.sh << 'EOF'
#!/bin/bash
echo "=== Health Check Trading ETF ==="
echo "Frontend: $(curl -s -o /dev/null -w '%{http_code}' https://investeclaire.fr/health)"
echo "Backend: $(curl -s -o /dev/null -w '%{http_code}' https://api.investeclaire.fr/health)"
echo "Services:"
systemctl is-active trading-frontend trading-backend nginx postgresql redis-server
EOF

chmod +x /home/dorian/trading-etf-app/check_health.sh
```

### Sauvegarde automatique
```bash
# Script de sauvegarde quotidienne
cat > /home/dorian/trading-etf-app/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/dorian/backups/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Sauvegarde base de données
pg_dump -h localhost -U trading_user trading_etf > $BACKUP_DIR/trading_etf.sql

# Sauvegarde logs
cp -r /home/dorian/trading-etf-app/logs $BACKUP_DIR/

echo "Sauvegarde créée dans $BACKUP_DIR"
EOF

chmod +x /home/dorian/trading-etf-app/backup.sh

# Ajouter à crontab pour exécution quotidienne
echo "0 2 * * * /home/dorian/trading-etf-app/backup.sh" | crontab -
```

---

## ✅ Checklist de Déploiement

- [ ] PostgreSQL installé et configuré
- [ ] Redis installé et démarré
- [ ] Python 3.8+ avec venv créé
- [ ] Node.js 18+ installé
- [ ] Backend démarré sur port 8000
- [ ] Frontend démarré sur port 3000
- [ ] Certificats SSL en place
- [ ] Configuration Nginx active
- [ ] Services systemd configurés
- [ ] Firewall configuré
- [ ] Health checks fonctionnels
- [ ] DNS pointant vers le serveur
- [ ] Monitoring en place

---

**🎉 Votre application Trading ETF est maintenant déployée !**

Pour toute question ou problème, vérifiez les logs et utilisez les commandes de dépannage fournies.