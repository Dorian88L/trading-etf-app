# Configuration SSL pour investeclaire.fr

## Fichiers requis

1. ✅ **Certificat SSL** : `investeclaire.fr.crt` (fourni)
2. ❌ **Clé privée** : `investeclaire.fr.key` (MANQUANT)

## Pour obtenir la clé privée

Vous devez fournir le fichier de clé privée `investeclaire.fr.key` qui correspond au certificat SSL.

Si vous ne l'avez pas, vous pouvez :
1. La récupérer depuis votre fournisseur SSL (Sectigo)
2. La récupérer depuis votre serveur web existant
3. Utiliser la clé privée que vous avez générée lors de la création de la demande de certificat (CSR)

## Placement du fichier

Placez le fichier `investeclaire.fr.key` dans ce dossier `/ssl/`

## Test temporaire

Pour tester sans SSL, vous pouvez temporairement revenir aux paramètres HTTP en supprimant les options SSL du script `start_dev_simple.sh`.