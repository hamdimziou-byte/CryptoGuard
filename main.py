import requests
import pandas as pd
from datetime import datetime
import json
import os

from colorama import init, Fore, Style

init(autoreset=True)

CRYPTOS = ["bitcoin", "ethereum", "binancecoin", "solana", "ripple"]
WATCHLIST_FILE = "watchlist.json"
ALERTS_FILE = "alerts.json"

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

def get_top_cryptos(limit=100, currency="usd"):
    """جلب أعلى N عملة حسب Market Cap"""
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": currency,
        "order": "market_cap_desc",
        "per_page": min(limit, 250),  # الحد الأقصى 250 لكل صفحة
        "page": 1,
        "price_change_percentage": "24h"
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Erreur API top: {e}")
        return None

# Mapping من CoinGecko ID إلى Binance Symbol
BINANCE_MAP = {
    "bitcoin": "BTCUSDT",
    "ethereum": "ETHUSDT",
    "binancecoin": "BNBUSDT",
    "solana": "SOLUSDT",
    "ripple": "XRPUSDT",
    "cardano": "ADAUSDT",
    "dogecoin": "DOGEUSDT",
    "polkadot": "DOTUSDT",
    "tron": "TRXUSDT",
    "litecoin": "LTCUSDT",
    "chainlink": "LINKUSDT",
    "monero": "XMRUSDT",
    "zcash": "ZECUSDT",
    "tether": "USDTUSDT",
    "usd-coin": "USDCUSDT",
    "stellar": "XLMUSDT",
    "uniswap": "UNIUSDT",
    "aave": "AAVEUSDT",
    "cosmos": "ATOMUSDT",
    "filecoin": "FILUSDT",
    "aptos": "APTUSDT",
    "arbitrum": "ARBUSDT",
    "optimism": "OPUSDT",
    "polygon": "MATICUSDT",
    "avalanche-2": "AVAXUSDT",
    "shiba-inu": "SHIBUSDT",
}


def fetch_from_binance(cryptos, currency="usd"):
    """جلب الأسعار من Binance API"""
    if currency != "usd":
        return None  # Binance يدعم USD فقط في هذا الـendpoint
    
    results = []
    for cg_id in cryptos:
        binance_symbol = BINANCE_MAP.get(cg_id)
        if not binance_symbol:
            continue
        
        url = f"https://api.binance.com/api/v3/ticker/24hr"
        params = {"symbol": binance_symbol}
        
        try:
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            results.append({
                "id": cg_id,
                "symbol": binance_symbol.replace("USDT", "").lower(),
                "name": cg_id.replace("-", " ").title(),
                "current_price": float(data["lastPrice"]),
                "price_change_percentage_24h": float(data["priceChangePercent"]),
                "market_cap": 0,
            })
        except (requests.RequestException, KeyError, ValueError):
            continue
    
    return results if results else None

def fetch_from_coinpaprika(cryptos, currency="usd"):
    """جلب الأسعار من CoinPaprika API (بديل CoinCap)"""
    # Mapping من CoinGecko ID إلى CoinPaprika ID
    PAPRIKA_MAP = {
        "bitcoin": "btc-bitcoin",
        "ethereum": "eth-ethereum",
        "binancecoin": "bnb-binance-coin",
        "solana": "sol-solana",
        "ripple": "xrp-xrp",
        "cardano": "ada-cardano",
        "dogecoin": "doge-dogecoin",
        "polkadot": "dot-polkadot",
        "tron": "trx-tron",
        "litecoin": "ltc-litecoin",
        "chainlink": "link-chainlink",
        "monero": "xmr-monero",
        "zcash": "zec-zcash",
        "stellar": "xlm-stellar",
        "uniswap": "uni-uniswap",
        "aave": "aave-aave",
        "cosmos": "atom-cosmos",
        "filecoin": "fil-filecoin",
        "aptos": "apt-aptos",
        "arbitrum": "arb-arbitrum",
        "optimism": "op-optimism",
        "matic-network": "matic-polygon",
        "avalanche-2": "avax-avalanche",
        "shiba-inu": "shib-shiba-inu",
    }
    
    url = "https://api.coinpaprika.com/v1/tickers"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        all_data = response.json()
    except requests.RequestException as e:
        print(f"CoinPaprika erreur: {e}")
        return None
    
    # نبنيو dict بالـid
    paprika_index = {t["id"]: t for t in all_data}
    
    results = []
    for cg_id in cryptos:
        paprika_id = PAPRIKA_MAP.get(cg_id)
        if not paprika_id:
            continue
        
        ticker = paprika_index.get(paprika_id)
        if not ticker:
            continue
        
        try:
            quotes = ticker.get("quotes", {})
            quote = quotes.get(currency.upper(), {})
            
            results.append({
                "id": cg_id,
                "symbol": ticker["symbol"].lower(),
                "name": ticker["name"],
                "current_price": quote.get("price", 0),
                "price_change_percentage_24h": quote.get("percent_change_24h", 0),
                "market_cap": quote.get("market_cap", 0),
            })
        except (KeyError, ValueError):
            continue
    
    return results if results else None

def fetch_prices_robust(cryptos, currency="usd"):
    """جلب الأسعار مع Fallback (CoinGecko → Binance → CoinPaprika)"""
    providers = [
        ("CoinGecko",   lambda: fetch_prices(currency, cryptos)),
        ("Binance",     lambda: fetch_from_binance(cryptos, currency)),
        ("CoinPaprika", lambda: fetch_from_coinpaprika(cryptos, currency)),
    ]
    
    for name, provider in providers:
        try:
            data = provider()
            if data:
                if name != "CoinGecko":
                    print(f"{Fore.YELLOW}[Fallback: {name}]{Style.RESET_ALL}")
                return data
        except Exception as e:
            print(f"{Fore.RED}[{name} error: {e}]{Style.RESET_ALL}")
            continue
    
    return None
def search_crypto(query):
    """البحث عن عملة بالاسم أو الرمز"""
    url = "https://api.coingecko.com/api/v3/search"
    params = {"query": query}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("coins", [])[:10]  # أول 10 نتائج
    except requests.RequestException as e:
        print(f"Erreur search: {e}")
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
        return f"{Fore.YELLOW}  N/A {Style.RESET_ALL}"
    
    if change >= 0:
        color = Fore.GREEN
        arrow = "^"
    else:
        color = Fore.RED
        arrow = "v"
    
    return f"{color}{arrow} {change:+.2f}%{Style.RESET_ALL}"


def display_table(data, currency="USD"):
    # Header
    header = f"{Fore.CYAN}{'Symbole':<8}{'Nom':<12}{'Prix':<18}{'24h':<15}{'Market Cap':<20}{Style.RESET_ALL}"
    print(header)
    print(f"{Fore.CYAN}{'-' * 70}{Style.RESET_ALL}")
    
    for coin in data:
        symbol = coin["symbol"].upper()
        name = coin["name"][:10]
        price = f"{coin['current_price']:,.2f}"
        change_str = format_change(coin.get("price_change_percentage_24h"))
        market_cap = f"{coin['market_cap']:,.0f}"
        
        # لون الرمز (أصفر)
        symbol_colored = f"{Fore.YELLOW}{symbol:<8}{Style.RESET_ALL}"
        name_colored = f"{name:<12}"
        price_colored = f"{Fore.WHITE}{price:<18}{Style.RESET_ALL}"
        cap_colored = f"{Fore.MAGENTA}{market_cap:<20}{Style.RESET_ALL}"
        
        print(f"{symbol_colored}{name_colored}{price_colored}{change_str:<15}{cap_colored}")


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
        print(f"{Fore.RED}{Style.BRIGHT}ALERTES DECLENCHEES:{Style.RESET_ALL}")
        print("=" * 70)
        for msg in triggered:
            print(msg)
        print("=" * 70)
    else:
        print("\n✅ Aucune alerte declenchee")

def main():
    import sys
    
    args = sys.argv[1:]
    limit = 5
    search_query = None
    
    if "--top" in args:
        idx = args.index("--top")
        if idx + 1 < len(args):
            limit = int(args[idx + 1])
    
    if "--search" in args:
        idx = args.index("--search")
        if idx + 1 < len(args):
            search_query = args[idx + 1]
    
    print(f"{Fore.CYAN}{Style.BRIGHT}CryptoGuard v1.2.0{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}")
    
    # Search mode
    if search_query:
        print(f"\n{Fore.YELLOW}Recherche: '{search_query}'{Style.RESET_ALL}")
        results = search_crypto(search_query)
        if results:
            for i, coin in enumerate(results, 1):
                print(f"  {i}. {coin['name']} ({coin['symbol'].upper()}) - {coin['id']}")
        else:
            print("Aucun résultat")
        return
    
    # Top mode
    print(f"\n{Fore.YELLOW}Top {limit} cryptos (Market Cap){Style.RESET_ALL}")
    data = get_top_cryptos(limit, "usd")
    
    # Fallback إذا CoinGecko فشل
    if not data:
        print(f"{Fore.YELLOW}Tentative avec APIs alternatives...{Style.RESET_ALL}")
        data = fetch_prices_robust(CRYPTOS[:limit], "usd")
    
    if not data:
        print(f"{Fore.RED}Impossible de récupérer les données{Style.RESET_ALL}")
        return
    
    # Display
    print(f"\n{Fore.BLUE}{Style.BRIGHT}=== TOP {limit} (USD) ==={Style.RESET_ALL}")
    display_table(data, "USD")
        # ✅ قحص Alerts
    alerts_data = load_alerts()
    print(f"\n{Fore.YELLOW}🔔 Verification des alertes...{Style.RESET_ALL}")
    check_alerts(alerts_data, data)
    print(f"\n{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}")


main()