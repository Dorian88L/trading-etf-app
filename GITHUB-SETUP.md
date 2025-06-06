# 🐙 Configuration GitHub pour Trading ETF

## 📋 Instructions pour créer le repository privé

### **Étape 1 : Créer le repository sur GitHub**

1. **Aller sur GitHub** : https://github.com
2. **Cliquer sur "New repository"** (bouton vert)
3. **Configurer le repository** :
   - **Repository name** : `trading-etf-app`
   - **Description** : `Application de trading court terme d'ETF avec signaux automatisés et analyse technique avancée`
   - **Visibilité** : ✅ **Private** (très important !)
   - **Initialize repository** : ❌ Ne pas cocher (on a déjà le code)

4. **Cliquer sur "Create repository"**

### **Étape 2 : Connecter le repository local**

Après création, GitHub te donnera des commandes. Utilise celles-ci dans ton WSL :

```bash
# Dans ton terminal WSL Ubuntu
cd /home/dorian/trading-etf-app

# Ajouter l'origine GitHub (remplace ton-username par ton nom d'utilisateur GitHub)
git remote add origin https://github.com/ton-username/trading-etf-app.git

# Renommer la branche principale
git branch -M main

# Pousser le code vers GitHub
git push -u origin main
```

### **Étape 3 : Configuration optionnelle**

#### **Ajouter des collaborateurs (si nécessaire)**
1. Aller dans **Settings** > **Collaborators and teams**
2. Cliquer **Add people**
3. Entrer l'username ou email

#### **Configurer les branches protégées**
1. Aller dans **Settings** > **Branches**
2. Cliquer **Add rule**
3. Configurer la protection de `main`

#### **Configurer les secrets (pour CI/CD futur)**
1. Aller dans **Settings** > **Secrets and variables** > **Actions**
2. Ajouter les variables d'environnement sensibles

### **Étape 4 : Clonage sur d'autres machines**

Pour récupérer le code sur une autre machine :

```bash
# Cloner le repository privé
git clone https://github.com/ton-username/trading-etf-app.git

# Ou avec SSH (après configuration des clés)
git clone git@github.com:ton-username/trading-etf-app.git
```

### **🔐 Configuration SSH (Recommandé)**

Pour éviter de taper ton mot de passe à chaque push :

1. **Générer une clé SSH** :
```bash
ssh-keygen -t ed25519 -C "ton-email@example.com"
```

2. **Ajouter la clé à GitHub** :
```bash
# Copier la clé publique
cat ~/.ssh/id_ed25519.pub
```

3. **Sur GitHub** : Settings > SSH and GPG keys > New SSH key

4. **Tester la connexion** :
```bash
ssh -T git@github.com
```

5. **Changer l'origine pour utiliser SSH** :
```bash
git remote set-url origin git@github.com:ton-username/trading-etf-app.git
```

### **📝 Commandes Git utiles**

```bash
# Voir le status
git status

# Ajouter des changements
git add .

# Commiter
git commit -m "Description des changements"

# Pousser vers GitHub
git push

# Récupérer les derniers changements
git pull

# Voir l'historique
git log --oneline

# Créer une nouvelle branche
git checkout -b nouvelle-fonctionnalite

# Fusionner une branche
git checkout main
git merge nouvelle-fonctionnalite
```

### **🚀 Workflow recommandé**

1. **Développement local** :
```bash
# Créer une branche pour chaque fonctionnalité
git checkout -b feature/nouvelle-fonctionnalite

# Développer et tester
# ...

# Commiter les changements
git add .
git commit -m "Ajout nouvelle fonctionnalité"

# Pousser la branche
git push -u origin feature/nouvelle-fonctionnalite
```

2. **Sur GitHub** :
   - Créer une Pull Request
   - Review du code
   - Merge vers main

3. **Récupérer les changements** :
```bash
git checkout main
git pull
```

### **📁 Structure du repository GitHub**

```
trading-etf-app/
├── README.md                 # Documentation principale
├── WINDOWS-SETUP.md         # Instructions Windows/WSL
├── GITHUB-SETUP.md          # Ce fichier
├── docker-compose.yml       # Configuration Docker
├── start_dev.sh            # Script de démarrage
├── .gitignore              # Fichiers à ignorer
├── backend/                # Code backend Python
├── frontend/               # Code frontend React
└── docs/                   # Documentation (à créer)
```

### **🛡️ Sécurité du repository privé**

- ✅ **Repository privé** : Seul toi et tes collaborateurs y ont accès
- ✅ **Pas de secrets dans le code** : Utilise les variables d'environnement
- ✅ **Protection des branches** : Évite les push directs sur main
- ✅ **SSH keys** : Plus sécurisé que HTTPS avec mot de passe

Ton code sera en sécurité et accessible uniquement par toi !