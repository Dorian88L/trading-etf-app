# Tests des fonctionnalités frontend - Trading ETF App

## ✅ État de l'initialisation
- **Base de données** : Initialisée avec 10 ETFs européens réels
- **Utilisateur admin** : `admin@investeclaire.fr` / `AdminTradingETF2024!`
- **Docker** : En production avec .env.prod
- **Données mockées** : Supprimées du frontend

## 🧪 Plan de tests des fonctionnalités

### 1. **Page de connexion (Login.tsx)**
- [ ] Champ email requis
- [ ] Champ mot de passe requis
- [ ] Bouton "Sign in (Redux)" fonctionnel
- [ ] Bouton "Test Direct API" pour debug
- [ ] Redirection vers dashboard après connexion
- [ ] Gestion d'erreurs d'authentification
- [ ] Lien vers inscription

### 2. **Dashboard (Page d'accueil)**
- [ ] Chargement des données ETF en temps réel
- [ ] Bouton "Actualiser" fonctionnel
- [ ] Toggle temps réel (30s) actif/inactif
- [ ] Affichage vue d'ensemble des marchés
- [ ] Panneau des signaux de trading
- [ ] Graphiques avancés visibles
- [ ] Système de notifications opérationnel

### 3. **Liste des ETFs (ETFList.tsx)**
- [ ] Affichage des 10 ETFs de la base
- [ ] Bouton "Actualiser" recharge la liste
- [ ] Toggle vue tableau/cartes
- [ ] Recherche par nom/symbole/ISIN
- [ ] Filtres par secteur fonctionnels
- [ ] Filtres par devise fonctionnels
- [ ] Tri par nom/prix/variation/volume
- [ ] Boutons favoris actifs
- [ ] Boutons watchlist actifs
- [ ] Navigation vers détail ETF

### 4. **Détail ETF (ETFDetail.tsx)**
- [ ] Onglet "Vue d'ensemble" avec infos
- [ ] Onglet "Analyse technique" avec indicateurs
- [ ] Onglet "Signaux de trading" avec signaux réels
- [ ] Graphiques temps réel
- [ ] Bouton "Créer alerte prix"
- [ ] Actualisation automatique (30s)
- [ ] Données en temps réel depuis Yahoo Finance

### 5. **Signaux de trading (Signals.tsx)**
- [ ] Onglet "Signaux actifs"
- [ ] Onglet "Historique"
- [ ] Onglet "Analyse" avec statistiques
- [ ] Onglet "Alertes" configuration
- [ ] Filtres par type de signal
- [ ] Slider confidence minimale
- [ ] Bouton "Actualiser" signaux
- [ ] Notifications système

### 6. **Portfolio (Portfolio.tsx)**
- [ ] Onglet "Vue d'ensemble" résumé
- [ ] Onglet "Positions" détail
- [ ] Onglet "Transactions" historique
- [ ] Onglet "Analyse" performance
- [ ] Bouton "Nouvelle transaction"
- [ ] Calculs temps réel
- [ ] Allocation par secteur
- [ ] Métriques de performance

### 7. **Scoring ETF (ETFScoring.tsx)**
- [ ] Classement des ETFs par score
- [ ] Analyse sectorielle
- [ ] Filtres avancés
- [ ] Données sans mock (supprimées)

## 🔍 Points d'attention spécifiques

### APIs critiques à vérifier :
1. `/api/v1/market/etfs` - Liste ETFs
2. `/api/v1/real-market/real-etfs` - Données temps réel
3. `/api/v1/signals/active` - Signaux actifs
4. `/api/v1/portfolio/positions` - Positions portfolio

### Fonctionnalités temps réel :
- WebSocket pour données de marché
- Actualisation automatique (30s)
- Cache intelligent (30s)
- Fallback en cas d'erreur API

### Corrections apportées :
- ✅ Supprimé `generateMockETFScores()` 
- ✅ Supprimé signaux aléatoires ETFDetail
- ✅ Remplacé secteurs hardcodés par dynamiques
- ✅ Corrigé cash balance Portfolio
- ✅ Ajouté `fetchSignals()` et `latestSignals`

## 🎯 Objectif final
Vérifier que **100% des fonctionnalités utilisent des vraies données** :
- Données ETF depuis base PostgreSQL
- Prix temps réel depuis Yahoo Finance
- Calculs algorithmes réels
- Aucune donnée simulée ou aléatoire