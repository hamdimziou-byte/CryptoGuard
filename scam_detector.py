"""
CryptoGuard - Scam Detector
كشف العملات الرقمية المشبوهة (Scam)

يقوم بتحليل:
- الكلمات المشبوهة في الإسم/الرمز
- نسبة Volume/Market Cap (تداول مريب)
- عمر العملة (جديدة = خطر)
- Whitelist (عملات موثوقة)
- Blacklist (عملات معروفة Scam)
"""


# ═══════════════════════════════════════════════════════
#  Whitelist: عملات موثوقة (Top 50 Market Cap)
# ═══════════════════════════════════════════════════════

TRUSTED_CRYPTOS = {
    "bitcoin", "ethereum", "binancecoin", "solana", "ripple",
    "cardano", "dogecoin", "tron", "polkadot", "chainlink",
    "litecoin", "monero", "stellar", "uniswap", "aave",
    "cosmos", "filecoin", "aptos", "arbitrum", "optimism",
    "matic-network", "avalanche-2", "shiba-inu", "tether",
    "usd-coin", "dai", "binance-usd", "wrapped-bitcoin",
    "ethereum-classic", "near", "algorand", "fantom",
    "the-sandbox", "decentraland", "axie-infinity",
    "flow", "the-graph", "curve-dao-token",
    "compound-governance-token", "maker", "sushi",
    "zcash", "dash", "neo", "waves", "ontology",
    "vechain", "tezos", "iota", "eos",
}


# ═══════════════════════════════════════════════════════
#  Blacklist: عملات معروفة Scam / Rug Pull
# ═══════════════════════════════════════════════════════

KNOWN_SCAMS = {
    "squid",
    "safemoon",
    "safemoon-inu",
    "safemars",
    "luna-classic",
    "ftx-token",
    "bitconnect",
    "onecoin",
    "plus-token",
    "thodex",
    "titan",
    "squidgame",
    "elongate",
}


# ═══════════════════════════════════════════════════════
#  الكلمات المشبوهة
# ═══════════════════════════════════════════════════════

SUSPICIOUS_WORDS = [
    # Elon / Musk
    "elon", "musk", "doge", "shiba", "floki", "kishu",
    # Squid Game
    "squid",
    # Safe / Moon / Rocket
    "safemoon", "safemars", "moon", "rocket",
    # Baby / Sex
    "baby", "cum", "sex", "porn", "xxx",
    # Trump / Political
    "trump", "biden", "putin", "zelensky",
    # Christmas / Season
    "santa", "christmas", "halloween",
    # Animals
    "inu", "akita", "husky", "corgi", "puppy",
    # Test / Fake
    "test", "fake",
    # 1000x / Rich
    "1000x", "100x", "millionaire",
]

HIGH_RISK_WORDS = [
    "scam", "rug", "honeypot", "fake", "test",
]


# ═══════════════════════════════════════════════════════
#  الدالة الرئيسية
# ═══════════════════════════════════════════════════════

def calculate_risk_score(coin):
    """
    حساب Risk Score (0-100) لعملة رقمية
    """
    score = 0
    flags = []
    
    coin_id = (coin.get("id") or "").lower()
    name = (coin.get("name") or "").lower()
    symbol = (coin.get("symbol") or "").lower()
    market_cap = coin.get("market_cap") or 0
    volume = coin.get("total_volume") or coin.get("volume_24h") or 0
    price = coin.get("current_price") or 0
    
    # ═══ 0. Whitelist ═══
    if coin_id in TRUSTED_CRYPTOS:
        return {
            "score": 0,
            "level": "LOW",
            "flags": ["Crypto de confiance (Top 50)"],
            "color": "OK",
        }
    
    # ═══ 1. Blacklist ═══
    if coin_id in KNOWN_SCAMS:
        score += 60
        flags.append("Crypto connue comme SCAM")
    
    # ═══ 2. الكلمات المشبوهة ═══
    for word in SUSPICIOUS_WORDS:
        if word in name or word in symbol:
            if word in HIGH_RISK_WORDS:
                score += 40
                flags.append(f"Mot a haut risque: '{word}'")
            else:
                score += 15
                flags.append(f"Mot suspect: '{word}'")
            break
    
    # ═══ 3. Volume / Market Cap ═══
    if market_cap > 0:
        ratio = volume / market_cap
        if ratio > 10:
            score += 30
            flags.append(f"Volume/MarketCap tres eleve: {ratio:.1f}x")
        elif ratio > 3:
            score += 15
            flags.append(f"Volume/MarketCap eleve: {ratio:.1f}x")
    elif market_cap == 0:
        score += 20
        flags.append("Market Cap manquant")
    
    # ═══ 4. سعر منخفض + Market Cap عالي ═══
    if price > 0 and price < 0.00001 and market_cap > 1_000_000:
        score += 20
        flags.append("Prix tres bas avec Market Cap eleve")
    
    # ═══ 5. Market Cap صغير ═══
    if 0 < market_cap < 100_000:
        score += 20
        flags.append("Market Cap tres faible (< $100k)")
    
    # ═══ 6. الرمز طويل ═══
    if len(symbol) > 6:
        score += 10
        flags.append(f"Symbole long: '{symbol}'")
    
    # ═══ 7. أرقام في الإسم ═══
    if any(c.isdigit() for c in name) and len(name) < 15:
        score += 10
        flags.append("Chiffres dans le nom")
    
    # ═══ تحديد المستوى ═══
    score = min(score, 100)
    
    if score >= 70:
        level = "HIGH"
        color = "DANGER"
    elif score >= 40:
        level = "MEDIUM"
        color = "WARN"
    else:
        level = "LOW"
        color = "OK"
    
    if not flags:
        flags.append("Aucun signal suspect")
    
    return {
        "score": score,
        "level": level,
        "flags": flags,
        "color": color,
    }


def enrich_with_risk(data):
    """تزييد كل عملة في قائمة بـRisk Score"""
    if not data:
        return data
    
    for coin in data:
        risk = calculate_risk_score(coin)
        coin["risk_score"] = risk["score"]
        coin["risk_level"] = risk["level"]
        coin["risk_color"] = risk["color"]
        coin["risk_flags"] = risk["flags"]
    
    return data


# ═══════════════════════════════════════════════════════
#  اختبار سريع
# ═══════════════════════════════════════════════════════

if __name__ == "__main__":
    btc = {
        "id": "bitcoin",
        "name": "Bitcoin",
        "symbol": "btc",
        "current_price": 83580,
        "market_cap": 1_680_000_000_000,
        "total_volume": 30_000_000_000,
    }
    
    scam = {
        "id": "elonsquidmoon",
        "name": "ElonSquidMoon1000x",
        "symbol": "ELONSQUID",
        "current_price": 0.0000001,
        "market_cap": 50_000,
        "total_volume": 2_000_000,
    }
    
    print("Test Risk Score\n")
    print("=" * 60)
    print("Bitcoin:")
    print(calculate_risk_score(btc))
    print("\n" + "=" * 60)
    print("ElonSquidMoon1000x:")
    print(calculate_risk_score(scam))
    print("=" * 60)