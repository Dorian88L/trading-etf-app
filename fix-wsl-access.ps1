# Script PowerShell pour configurer l'accès WSL depuis Windows
# À exécuter en tant qu'administrateur dans PowerShell Windows

Write-Host "🔧 Configuration de l'accès WSL vers Windows..." -ForegroundColor Green

# Obtenir l'IP de WSL
Write-Host "📍 Détection de l'IP WSL..." -ForegroundColor Yellow
$wslIP = (wsl hostname -I).Split()[0].Trim()
Write-Host "IP WSL trouvée: $wslIP" -ForegroundColor Cyan

# Supprimer les anciennes règles (si elles existent)
Write-Host "🧹 Nettoyage des anciennes règles..." -ForegroundColor Yellow
try {
    netsh interface portproxy delete v4tov4 listenport=3000 listenaddress=0.0.0.0 2>$null
    netsh interface portproxy delete v4tov4 listenport=8000 listenaddress=0.0.0.0 2>$null
    Remove-NetFirewallRule -DisplayName "WSL Trading ETF Frontend" -ErrorAction SilentlyContinue 2>$null
    Remove-NetFirewallRule -DisplayName "WSL Trading ETF Backend" -ErrorAction SilentlyContinue 2>$null
} catch {
    # Ignorer les erreurs de nettoyage
}

# Configurer le port forwarding
Write-Host "🌐 Configuration du port forwarding..." -ForegroundColor Cyan
netsh interface portproxy add v4tov4 listenport=3000 listenaddress=0.0.0.0 connectport=3000 connectaddress=$wslIP
netsh interface portproxy add v4tov4 listenport=8000 listenaddress=0.0.0.0 connectport=8000 connectaddress=$wslIP

# Configurer le pare-feu Windows
Write-Host "🔥 Configuration du pare-feu..." -ForegroundColor Cyan
New-NetFirewallRule -DisplayName "WSL Trading ETF Frontend" -Direction Inbound -Protocol TCP -LocalPort 3000 -Action Allow -Enabled True
New-NetFirewallRule -DisplayName "WSL Trading ETF Backend" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow -Enabled True

# Vérifier la configuration
Write-Host "`n📋 Vérification de la configuration..." -ForegroundColor Yellow
$portProxy = netsh interface portproxy show v4tov4
Write-Host "Port forwarding actif:" -ForegroundColor White
Write-Host $portProxy -ForegroundColor Gray

# Instructions pour l'utilisateur
Write-Host "`n✅ Configuration terminée!" -ForegroundColor Green
Write-Host "🚀 L'application est déjà en cours d'exécution dans WSL!" -ForegroundColor Yellow
Write-Host "   Frontend: ✅ Actif sur port 3000" -ForegroundColor Green
Write-Host "   Backend:  ✅ Actif sur port 8000" -ForegroundColor Green

Write-Host "`n🌐 Accès depuis Windows:" -ForegroundColor Yellow
Write-Host "   Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "   Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor White

# Obtenir l'IP Windows pour accès réseau
$windowsIP = (Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "Ethernet*" | Where-Object {$_.IPAddress -like "192.168.*" -or $_.IPAddress -like "10.*"})[0].IPAddress
if ($windowsIP) {
    Write-Host "`n📱 Accès depuis d'autres appareils:" -ForegroundColor Yellow
    Write-Host "   Frontend: http://$windowsIP:3000" -ForegroundColor White
    Write-Host "   Backend:  http://$windowsIP:8000" -ForegroundColor White
}

Write-Host "`n💡 Troubleshooting:" -ForegroundColor Blue
Write-Host "   - Si ça ne marche pas, redémarre WSL: wsl --shutdown puis relance" -ForegroundColor Gray
Write-Host "   - Vérifie que Docker tourne dans WSL: sudo service docker status" -ForegroundColor Gray
Write-Host "   - Pour nettoyer: netsh interface portproxy reset" -ForegroundColor Gray

Write-Host "`n🔄 Ce script doit être relancé après chaque redémarrage de Windows/WSL" -ForegroundColor Yellow