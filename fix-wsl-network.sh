#!/bin/bash

echo "🔧 Configuration réseau WSL pour accès externe"

# 1. Obtenir les IPs
WSL_IP=$(hostname -I | awk '{print $1}')
WINDOWS_IP=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}')

echo "📍 IP WSL: $WSL_IP"
echo "📍 IP Windows: $WINDOWS_IP"

# 2. Vérifier les services actifs
echo ""
echo "📊 Services actifs:"
netstat -tlnp | grep -E ":(3000|8000|8080)"

# 3. Instructions PowerShell pour Windows
echo ""
echo "🖥️ OBLIGATOIRE - Exécutez dans PowerShell Administrateur Windows:"
echo ""
echo "# Port forwarding"
echo "netsh interface portproxy add v4tov4 listenport=3000 listenaddress=0.0.0.0 connectport=3000 connectaddress=$WSL_IP"
echo "netsh interface portproxy add v4tov4 listenport=8000 listenaddress=0.0.0.0 connectport=8000 connectaddress=$WSL_IP"
echo ""
echo "# Vérification"
echo "netsh interface portproxy show v4tov4"
echo ""

# 4. Obtenir l'IP Windows réelle
echo "🔍 Pour obtenir votre vraie IP Windows, exécutez dans PowerShell:"
echo "Get-NetIPAddress -AddressFamily IPv4 | Where-Object {\$_.InterfaceAlias -like '*Wi-Fi*'} | Select IPAddress"
echo ""

# 5. Test de connectivité
echo "🧪 Test de connectivité locale:"
curl -s http://localhost:3000 > /dev/null && echo "✅ Frontend: OK" || echo "❌ Frontend: KO"
curl -s http://localhost:8000/health > /dev/null && echo "✅ Backend: OK" || echo "❌ Backend: KO"

echo ""
echo "📱 Après configuration PowerShell, testez depuis votre téléphone:"
echo "   http://[IP_WINDOWS]:3000"
echo "   http://[IP_WINDOWS]:8000"