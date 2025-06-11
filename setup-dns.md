# 🌐 Configuration DNS pour Trading ETF App

## Configuration terminée ✅

Votre application est maintenant accessible via un proxy sur le réseau !

## 📱 Accès depuis tous les appareils du réseau :

### Option 1 : Accès direct par IP
- **URL** : `http://172.17.232.143:8080`
- Fonctionne immédiatement sur tous les appareils

### Option 2 : Nom personnalisé (facultatif)
Pour utiliser `http://trading-etf.local` :

#### Sur Windows (votre PC) :
1. Ouvrez **Bloc-notes en tant qu'administrateur**
2. Ouvrez `C:\Windows\System32\drivers\etc\hosts`
3. Ajoutez : `192.168.1.156 trading-etf.local`
4. Sauvegardez

#### Sur Android/iPhone :
- **Android** : Utilisez une app comme "Hosts Editor" (root requis)
- **iPhone** : Modifiez via un profil de configuration
- **Plus simple** : Utilisez directement l'IP `172.17.232.143:8080`

#### Sur Mac/Linux :
```bash
echo "192.168.1.156 trading-etf.local" | sudo tee -a /etc/hosts
```

## 🔧 Configuration Windows PowerShell (optionnel) :

Pour rediriger le port 80 :
```powershell
# En tant qu'administrateur
netsh interface portproxy add v4tov4 listenport=80 listenaddress=0.0.0.0 connectport=8080 connectaddress=172.17.232.143
```

## 🎯 URLs finales :

- **Simple (recommandé)** : `http://172.17.232.143:8080`
- **Avec nom personnalisé** : `http://trading-etf.local` (après config DNS)
- **Frontend** : Interface complète React
- **Backend API** : Accessible via `/api/`
- **Documentation** : Accessible via `/docs`

## ✅ Test :
Depuis votre téléphone/tablette, ouvrez :
`http://172.17.232.143:8080`

L'application Trading ETF devrait s'afficher !