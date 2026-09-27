import requests
import pandas as pd
from datetime import datetime
import json
import os


CRYPTOS = ["bitcoin", "ethereum", "binancecoin", "solana", "ripple"]
WATCHLIST_FILE = "watchlist.json"


def fetch_prices(vs_currency="usd", cryptos=None):
    if cryptos is None:
        cryptos = CRYPTOS
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": vs_currency,
        "ids": ",".join(cryptos),
        "price_change_percentage": "24h"
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Erreur API: {e}")
        return None


def get_exchange_rate(target_currency="TND"):
    url = "https://api.exchangerate-api.com/v4/latest/USD"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data["rates"].get(target_currency)
    except requests.RequestException as e:
        print(f"Erreur API taux: {e}")
        return None


def format_change(change):
    if change is None:
        return "  N/A "
    arrow = "^" if change >= 0 else "v"
    return f"{arrow} {change:+.2f}%"


def display_table(data, currency="USD"):
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


def load_watchlist():
    default = {
        "cryptos": ["bitcoin", "ethereum", "binancecoin", "solana", "ripple"],
        "currencies": ["usd", "eur", "tnd"]
    }
    if not os.path.exists(WATCHLIST_FILE):
        return default
    try:
        with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Erreur lecture watchlist: {e}")
        return default


def save_watchlist(watchlist):
    try:
        with open(WATCHLIST_FILE, "w", encoding="utf-8") as f:
            json.dump(watchlist, f, indent=2, ensure_ascii=False)
        print(f"Watchlist sauvegardee dans {WATCHLIST_FILE}")
    except IOError as e:
        print(f"Erreur ecriture: {e}")

ALERTS_FILE = "alerts.json"


def load_alerts():
    """تحميل التنبيهات من ملف"""
    default = {
        "alerts": [
            {"crypto": "bitcoin", "above": 100000},
            {"crypto": "ethereum", "above": 3000},
            {"crypto": "solana", "below": 100}
        ]
    }
    
    if not os.path.exists(ALERTS_FILE):
        return default
    
    try:
        with open(ALERTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Erreur lecture alerts: {e}")
        return default


def save_alerts(alerts_data):
    """حفظ التنبيهات في ملف"""
    try:
        with open(ALERTS_FILE, "w", encoding="utf-8") as f:
            json.dump(alerts_data, f, indent=2, ensure_ascii=False)
        print(f"Alertes sauvegardees dans {ALERTS_FILE}")
    except IOError as e:
        print(f"Erreur ecriture alerts: {e}")


def check_alerts(alerts_data, prices_data):
    """فحص التنبيهات ومقارنتها بالأسعار"""
    if not prices_data or not alerts_data:
        return
    
    alerts = alerts_data.get("alerts", [])
    if not alerts:
        return
    
    # نبنيو dict من الأسعار للوصول السريع
    prices = {coin["id"]: coin for coin in prices_data}
    
    triggered = []
    
    for alert in alerts:
        crypto_id = alert.get("crypto")
        coin = prices.get(crypto_id)
        
        if not coin:
            continue
        
        price = coin["current_price"]
        symbol = coin["symbol"].upper()
        
        # شرط above
        if "above" in alert and price >= alert["above"]:
            triggered.append(
                f"🔔 ALERTE: {symbol} = ${price:,.2f} (>= ${alert['above']:,})"
            )
        
        # شرط below
        if "below" in alert and price <= alert["below"]:
            triggered.append(
                f"🔔 ALERTE: {symbol} = ${price:,.2f} (<= ${alert['below']:,})"
            )
    
    if triggered:
        print("\n" + "=" * 70)
        print("🚨 ALERTES DECLENCHEES:")
        print("=" * 70)
        for msg in triggered:
            print(msg)
        print("=" * 70)
    else:
        print("\n✅ Aucune alerte declenchee")

def main():
    print("CryptoGuard v0.5.0")
    print("=" * 70)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    watchlist = load_watchlist()
    cryptos = watchlist["cryptos"]
    currencies = watchlist["currencies"]

    print(f"\nSurveillance de {len(cryptos)} cryptos: {', '.join(cryptos)}")
    print(f"Devises: {', '.join(currencies).upper()}")

    data_usd = fetch_prices("usd", cryptos)

        # تحميل التنبيهات
    alerts_data = load_alerts()

    for curr in currencies:
        print(f"\n=== {curr.upper()} ===")
        if curr == "usd":
            if data_usd:
                display_table(data_usd, "USD")
        elif curr == "tnd":
            taux = get_exchange_rate("TND")
            if taux and data_usd:
                data_tnd = [dict(coin) for coin in data_usd]
                for coin in data_tnd:
                    coin["current_price"] = coin["current_price"] * taux
                    coin["market_cap"] = coin["market_cap"] * taux
                display_table(data_tnd, "TND")
                print(f"Taux: 1 USD = {taux:.4f} TND")
        else:
            data = fetch_prices(curr, cryptos)
            if data:
                display_table(data, curr.upper())
     # فحص التنبيهات
    print("\n" + "=" * 70)
    print("🔔 Verification des alertes...")
    check_alerts(alerts_data, data_usd)
    print("\n" + "=" * 70)


main()