"""
🛡️ CryptoGuard - Système de surveillance crypto
Version: 0.2.1
"""

import requests
import pandas as pd
from datetime import datetime


# ═══════════════════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════════════════

CRYPTOS = ["bitcoin", "ethereum", "binancecoin", "solana", "ripple"]


# ═══════════════════════════════════════════════════════
#  FONCTIONS
# ═══════════════════════════════════════════════════════

def fetch_prices(vs_currency="usd"):
    """جلب الأسعار بعملة معينة"""
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": vs_currency,
        "ids": ",".join(CRYPTOS),
        "price_change_percentage": "24h"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"❌ Erreur API: {e}")
        return None


def format_change(change):
    """تنسيق نسبة التغيير مع سهم"""
    if change is None:
        return "  N/A "
    arrow = "▲" if change >= 0 else "▼"
    return f"{arrow} {change:+.2f}%"


def display_table(data, currency="USD"):
    """عرض البيانات في جدول منظم"""
    rows = []
    for coin in data:
        rows.append({
            "Symbole": coin["symbol"].upper(),
            "Nom": coin["name"],
            f"Prix ({currency})": f"{coin['current_price']:,.2f}",
            "24h": format_change(coin.get("price_change_percentage_24h")),
            "Market Cap": f"{coin['market_cap']:,.0f}"
        })
    
    df = pd.DataFrame(rows)
    print(df.to_string(index=False))


# ═══════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════

def main():
    print("🛡️  CryptoGuard v0.2.1")
    print("=" * 70)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # USD
    print("\n💵 === USD ===")
    data_usd = fetch_prices("usd")
    if data_usd:
        display_table(data_usd, "USD")
    
    # EUR
    print("\n💶 === EUR ===")
    data_eur = fetch_prices("eur")
    if data_eur:
        display_table(data_eur, "EUR")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()