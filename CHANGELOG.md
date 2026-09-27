# 📜 Changelog

Toutes les modifications notables de CryptoGuard sont documentées ici.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/),
et ce projet adhère au [Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-09-27

### 🎉 Version initiale stable

**Fonctionnalités principales:**
- 🖥️ Interface graphique (Tkinter)
- 💰 Suivi de 5 cryptomonnaies (BTC, ETH, BNB, XRP, SOL)
- 💵 Support multi-devises (USD, EUR, TND)
- 📊 Variation 24h avec indicateurs visuels
- 🔔 Système d'alertes configurables
- 👁️ Watchlist personnalisable (JSON)
- 🎨 Interface colorée

## [0.7.0] - 2026-09-27

### Ajouté
- 🖥️ Interface graphique avec Tkinter (`gui.py`)
- 🔄 Bouton Refresh
- 🔘 Sélection devise (USD/EUR/TND)
- 📊 Tableau coloré (vert/hausse, rouge/baisse)
- 📅 Barre de statut
- 📦 Packaging avec PyInstaller (`CryptoGuard.exe`)

### Modifié
- `main.py` : ajout de `if __name__ == "__main__"` pour éviter les conflits d'import

## [0.6.0] - 2026-09-27

### Ajouté
- 🎨 Dashboard coloré avec `colorama`
- 🟢 Vert pour hausses
- 🔴 Rouge pour baisses
- 🟡 Symboles jaunes
- 🟦 En-têtes cyan

## [0.5.0] - 2026-09-27

### Ajouté
- 🔔 Système d'alertes (`alerts.json`)
- 📈 Alertes "above" (au-dessus)
- 📉 Alertes "below" (en-dessous)

## [0.4.0] - 2026-09-27

### Ajouté
- 👁️ Watchlist personnalisable (`watchlist.json`)
- 💾 Sauvegarde/chargement des cryptos suivies
- 💱 Sélection des devises

## [0.3.0] - 2026-09-26

### Ajouté
- 🇹🇳 Support du Dinar Tunisien (TND)
- 💱 API exchangerate-api.com
- 🔄 Conversion automatique USD → TND

## [0.2.1] - 2026-09-26

### Ajouté
- 💶 Support EUR
- 📊 Market Cap
- 📈 Variation 24h (▲/▼)

### Modifié
- `main.py` : refactoring des fonctions

## [0.1.0] - 2026-09-26

### Ajouté
- 🎉 Version initiale
- 💰 Prix Bitcoin
- 🔌 API CoinGecko

---

## 🔗 Liens

- [Repository GitHub](https://github.com/hamdimziou-byte/CryptoGuard)
- [Issues](https://github.com/hamdimziou-byte/CryptoGuard/issues)