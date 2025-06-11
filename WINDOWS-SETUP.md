# 🪟 Configuration Windows + WSL pour Trading ETF

## 🚀 Étapes pour accéder à l'application depuis Windows

### **Étape 1 : Configuration des ports WSL**

1. **Ouvrir PowerShell en tant qu'administrateur** (clic droit > "Exécuter en tant qu'administrateur")

2. **Naviguer vers le dossier du projet** :
```powershell
# Remplace par ton chemin WSL
cd \\wsl$\Ubuntu\home\dorian\trading-etf-app
```

3. **Exécuter le script de configuration** :
```powershell
.\configure-wsl-ports.ps1
```

### **Étape 2 : Démarrer l'application dans WSL**

```bash
# Dans ton terminal WSL Ubuntu
cd /home/dorian/trading-etf-app
./start_dev.sh
```

### **Étape 3 : Accès depuis Windows**

Une fois l'application démarrée, accède aux URLs suivantes **depuis ton navigateur Windows** :

- 🌐 **Frontend** : http://localhost:80
- 🔌 **Backend API** : http://localhost:8443  
- 📚 **Documentation** : http://localhost:8443/docs

### **🌍 Accès depuis d'autres appareils du réseau**

Pour accéder depuis ton téléphone ou un autre PC :

1. **Trouve ton IP Windows** :
```powershell
ipconfig | findstr "IPv4"
```

2. **Accède via l'IP** (exemple avec 192.168.1.100) :
- Frontend : http://192.168.1.100:80
- Backend : http://192.168.1.100:8443

### **🔧 Vérification de la configuration**

```powershell
# Voir les redirections de ports actives
netsh interface portproxy show v4tov4

# Tester la connectivité
curl http://localhost:8443/health
```

### **🗑️ Nettoyage (si nécessaire)**

```powershell
# Supprimer les redirections
netsh interface portproxy delete v4tov4 listenport=80
netsh interface portproxy delete v4tov4 listenport=8443

# Supprimer les règles de pare-feu
Remove-NetFirewallRule -DisplayName "Trading ETF Frontend"
Remove-NetFirewallRule -DisplayName "Trading ETF Backend"
```

### **🐛 Troubleshooting**

**Problème : "This site can't be reached"**
- Vérifier que l'application tourne dans WSL
- Vérifier les redirections de ports : `netsh interface portproxy show v4tov4`
- Redémarrer le service WSL : `wsl --shutdown` puis relancer

**Problème : Pare-feu bloque la connexion**
- Exécuter le script PowerShell en tant qu'administrateur
- Vérifier les règles de pare-feu dans Windows Defender

**Problème : IP WSL change**
- Relancer le script PowerShell après chaque redémarrage de WSL

### **💡 Automatisation (Optionnel)**

Créer un raccourci Windows pour lancer automatiquement :

1. **Créer un batch file** `start-trading-etf.bat` :
```batch
@echo off
echo Démarrage Trading ETF...
wsl -d Ubuntu -e bash -c "cd /home/dorian/trading-etf-app && ./start_dev.sh"
```

2. **Créer un raccourci** pointant vers ce fichier batch

Ainsi, tu pourras démarrer l'application directement depuis Windows !