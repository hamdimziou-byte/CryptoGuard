# 🛡️ CryptoGuard

> Système de surveillance des prix des cryptomonnaies en temps réel

![Python](https://img.shields.io/badge/Python-3.14-blue?logo=python)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Stable-success)
![Version](https://img.shields.io/badge/Version-1.0.0-blue)

---

## 📋 Description

**CryptoGuard** est un outil puissant qui récupère en temps réel les prix des principales cryptomonnaies depuis l'API **CoinGecko**.

Il offre **deux interfaces** :
- 🖥️ **GUI** (Tkinter) — interface graphique moderne
- ⌨️ **CLI** (console) — pour les utilisateurs avancés

---

## ✨ Fonctionnalités

- 🖥️ **Interface graphique** (Tkinter) — moderne et intuitive
- 💰 **5 cryptomonnaies** : BTC, ETH, BNB, XRP, SOL
- 💵 **Multi-devises** : USD, EUR, TND 🇹🇳
- 📊 **Variation 24h** avec indicateurs visuels (▲/▼)
- 🔔 **Alertes configurables** (above/below)
- 👁️ **Watchlist personnalisable** (JSON)
- 🎨 **Interface colorée** (vert/hausse, rouge/baisse)
- 📦 **Packaging .exe** pour Windows

---

## 🚀 Installation

### 1. Cloner le repository


git clone https://github.com/hamdimziou-byte/CryptoGuard.git
cd CryptoGuard

### 2. Créer un environnement virtuel


python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # macOS/Linux


### 3. Installer les dépendances


pip install -r requirements.txt


---

## 🎮 Utilisation

### 🖥️ Interface graphique (recommandé)


python gui.py


### ⌨️ Interface console


python main.py


---

## 📸 Aperçu

### Interface graphique

![GUI Screenshot](https://raw.githubusercontent.com/hamdimziou-byte/CryptoGuard/main/screenshot.png)

### Interface console

```
🛡️  CryptoGuard v0.6.0
======================================================================
📅 2026-09-27 13:05:09
======================================================================

💵 === USD ===
Symbole       Nom  Prix (USD)      24h     Market Cap
     BTC  Bitcoin  84,930.00  ^ +0.97%  1,706,192,812,994
     ETH Ethereum   2,711.62  ^ +0.89%    331,050,080,321
     BNB  BNB         780.14  ^ +0.71%    103,882,644,792
     XRP  XRP           1.54  v -0.36%     96,893,561,755
     SOL  Solana      124.20  ^ +2.57%     73,014,528,993
```

---

## 🛠️ Technologies

| Technologie | Utilisation |
|-------------|-------------|
| **Python 3.14** | Langage principal |
| **Tkinter** | Interface graphique |
| **requests** | Requêtes HTTP |
| **pandas** | Formatage des tableaux |
| **colorama** | Couleurs console |
| **PyInstaller** | Packaging .exe |
| **CoinGecko API** | Source des prix |
| **exchangerate-api** | Taux de change |

---

## 📁 Structure du projet

```
CryptoGuard/
├── main.py              # Interface console
├── gui.py               # Interface graphique
├── requirements.txt     # Dépendances
├── watchlist.json       # Config watchlist
├── alerts.json          # Config alertes
├── CHANGELOG.md         # Historique versions
├── README.md            # Documentation
└── .gitignore
```

---

## 🔔 Configuration des alertes

Créez un fichier `alerts.json` :

```json
{
  "alerts": [
    {"crypto": "bitcoin", "above": 100000},
    {"crypto": "ethereum", "below": 2000},
    {"crypto": "solana", "above": 150}
  ]
}
```

---

## 👁️ Configuration de la watchlist

Créez un fichier `watchlist.json` :

```json
{
  "cryptos": ["bitcoin", "ethereum", "solana"],
  "currencies": ["usd", "eur", "tnd"]
}
```

---

## 🗺️ Roadmap

- [x] Support multi-cryptomonnaies
- [x] Support multi-devises (USD/EUR/TND)
- [x] Alertes configurables
- [x] Watchlist
- [x] Interface graphique
- [x] Packaging .exe
- [ ] Export CSV/Excel
- [ ] Graphiques historiques
- [ ] Version mobile
- [ ] Version web (Flask)

---

## 👤 Auteur

**Hamdi Mziou**
- GitHub : [@hamdimziou-byte](https://github.com/hamdimziou-byte)

---

## 📄 Licence

Ce projet est sous licence MIT.

---

## ⭐ Support

Si ce projet vous plaît, n'hésitez pas à lui donner une ⭐ sur GitHub !
