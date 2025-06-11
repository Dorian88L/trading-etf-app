#!/bin/bash

# Script pour rendre l'application accessible sur le réseau avec un nom personnalisé

echo "🌐 Configuration de l'accès réseau pour Trading ETF App"

# Nom personnalisé pour l'application
APP_NAME="trading-etf.local"
WSL_IP="172.17.232.143"
WINDOWS_IP="192.168.1.156"

echo "📝 Configuration pour le nom: $APP_NAME"

# 1. Installer Nginx dans WSL
echo "📦 Installation de Nginx..."
sudo apt update
sudo apt install -y nginx

# 2. Créer la configuration Nginx
echo "⚙️ Configuration de Nginx..."
sudo tee /etc/nginx/sites-available/trading-etf > /dev/null << EOF
server {
    listen 80;
    server_name $APP_NAME *.local;
    
    # Frontend React
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
    
    # Documentation
    location /docs {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# 3. Activer le site
sudo ln -sf /etc/nginx/sites-available/trading-etf /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# 4. Tester la configuration
sudo nginx -t

# 5. Démarrer Nginx
sudo systemctl enable nginx
sudo systemctl restart nginx

echo "✅ Nginx configuré et démarré"

# 6. Instructions pour Windows
echo ""
echo "🖥️ Configuration Windows requise:"
echo "1. Ouvrez PowerShell en tant qu'administrateur"
echo "2. Exécutez ces commandes:"
echo ""
echo "# Port forwarding pour HTTP (port 80)"
echo "netsh interface portproxy add v4tov4 listenport=80 listenaddress=0.0.0.0 connectport=80 connectaddress=$WSL_IP"
echo ""
echo "# Ajouter l'entrée DNS locale (fichier hosts)"
echo "echo '$WINDOWS_IP $APP_NAME' >> C:\\Windows\\System32\\drivers\\etc\\hosts"
echo ""
echo "3. Pour les autres appareils du réseau, ajoutez dans leurs paramètres DNS ou hosts:"
echo "   $WINDOWS_IP -> $APP_NAME"
echo ""
echo "🌐 Une fois configuré, l'application sera accessible via:"
echo "   http://$APP_NAME"
echo "   depuis tous les appareils du réseau !"

# 7. Afficher le statut
echo ""
echo "📊 Statut des services:"
echo "Nginx: $(sudo systemctl is-active nginx)"
echo "Port 80: $(sudo netstat -tlnp | grep :80 || echo 'Non utilisé')"
echo ""
echo "🔗 URLs locales de test:"
echo "http://localhost (via Nginx)"
echo "http://$WSL_IP (direct via Nginx)"