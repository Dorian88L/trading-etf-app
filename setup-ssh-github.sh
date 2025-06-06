#!/bin/bash

echo "🔑 Configuration SSH pour GitHub"
echo ""

# Vérifier si une clé SSH existe déjà
if [ -f ~/.ssh/id_ed25519.pub ]; then
    echo "✅ Clé SSH trouvée :"
    cat ~/.ssh/id_ed25519.pub
    echo ""
    echo "📋 Copie cette clé et ajoute-la sur GitHub :"
    echo "   GitHub.com > Settings > SSH and GPG keys > New SSH key"
else
    echo "🔧 Génération d'une nouvelle clé SSH..."
    read -p "Entre ton email GitHub : " email
    
    ssh-keygen -t ed25519 -C "$email" -f ~/.ssh/id_ed25519 -N ""
    
    echo ""
    echo "✅ Clé SSH générée !"
    echo "📋 Copie cette clé publique :"
    echo ""
    cat ~/.ssh/id_ed25519.pub
    echo ""
    echo "📋 Ajoute-la sur GitHub :"
    echo "   GitHub.com > Settings > SSH and GPG keys > New SSH key"
fi

echo ""
read -p "Appuie sur Entrée quand tu as ajouté la clé sur GitHub..."

# Tester la connexion SSH
echo "🧪 Test de la connexion SSH..."
ssh -T git@github.com

# Changer l'URL pour utiliser SSH
echo "🔧 Configuration du repository pour SSH..."
git remote set-url origin git@github.com:Dorian88L/trading-etf-app.git

# Pousser avec SSH
echo "🚀 Push avec SSH..."
git push -u origin main

echo ""
echo "✅ Configuration SSH terminée !"
echo "🌐 Repository : https://github.com/Dorian88L/trading-etf-app"