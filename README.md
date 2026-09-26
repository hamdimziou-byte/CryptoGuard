# 🛡️ CryptoGuard

> Système de surveillance des prix des cryptomonnaies en Python

![Python](https://img.shields.io/badge/Python-3.14-blue?logo=python)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-success)
---

## 📋 Description

**CryptoGuard** est un outil en ligne de commande qui récupère en temps réel les prix des principales cryptomonnaies depuis l'API **CoinGecko**.

Il affiche un tableau formaté avec :
- 💰 Le prix actuel
- 📈 La variation sur 24h
- 💎 La capitalisation boursière
- ---

## ✨ Fonctionnalités

- ✅ Suivi de **5 cryptomonnaies** : BTC, ETH, BNB, XRP, SOL
- ✅ Support **multi-devises** : USD, EUR
- ✅ Variation **24h** avec indicateurs visuels (▲/▼)
- ✅ Tableaux formatés avec **pandas**
- ✅ Gestion d'erreurs robuste
- ---

## 🚀 Installation

### 1. Cloner le repository

git clone https://github.com/hamdimziou-byte/CryptoGuard.git
cd CryptoGuard
### 2. Créer un environnement virtuel

    python -m venv .venv
    .venv\Scripts\activate

### 3. Installer les dépendances

    pip install -r requirements.txt
    
---

## 🎮 Utilisation

    python main.py
    
---

## 🛠️ Technologies

| Technologie | Utilisation |
|-------------|-------------|
| **Python 3.14** | Langage principal |
| **requests** | Requêtes HTTP |
| **pandas** | Formatage des tableaux |
| **CoinGecko API** | Source des données |

---

## 🗺️ Roadmap

- [x] Support multi-cryptomonnaies
- [x] Support USD/EUR
- [ ] Support TND (Dinar tunisien)
- [ ] Watchlist personnalisée
- [ ] Système d'alertes
- [ ] Interface web (Flask)
- [ ] 
---

## 👤 Auteur

**Hamdi Mziou**
- GitHub : [@hamdimziou-byte](https://github.com/hamdimziou-byte)

---

## 📄 Licence

Ce projet est sous licence MIT.
