"""
CryptoGuard - Whale Alerts + Sentiment Analysis
Whale Alerts: BTC (Mempool.space) + ETH (Etherscan - يحتاج API key)
"""

import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


# ═══════════════════════════════════════════════════════
#  WHALE ALERTS - BTC (Mempool.space - مجاني بلا key)
# ═══════════════════════════════════════════════════════

def get_btc_whales(limit=5):
    """أكبر تحويلات BTC"""
    try:
        url = "https://mempool.space/api/mempool/recent"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        sorted_txs = sorted(data, key=lambda x: x.get("value", 0), reverse=True)[:limit]

        whales = []
        for tx in sorted_txs:
            value_btc = tx.get("value", 0) / 1e8
            txid = tx.get("txid", "")
            whales.append({
                "chain": "BTC",
                "symbol": "BTC",
                "value": round(value_btc, 4),
                "usd_value": round(value_btc * 85000, 2),
                "txid": txid,
                "url": f"https://mempool.space/tx/{txid}"
            })
        return whales
    except Exception as e:
        print(f"BTC whales error: {e}")
        return []


# ═══════════════════════════════════════════════════════
#  WHALE ALERTS - ETH (Etherscan - يحتاج API key)
# ═══════════════════════════════════════════════════════

def get_eth_whales(limit=5):
    """أكبر تحويلات ETH (Etherscan)"""
    api_key = os.environ.get("ETHERSCAN_API_KEY")
    if not api_key:
        print("ETHERSCAN_API_KEY manquant (skip ETH)")
        return []

    try:
        url = "https://api.etherscan.io/api"

        # أحدث block
        params = {
            "module": "proxy",
            "action": "eth_blockNumber",
            "apikey": api_key
        }
        r = requests.get(url, params=params, timeout=10)
        latest_block = int(r.json()["result"], 16)

        whales = []
        # آخر 3 blocks
        for i in range(3):
            block_num = latest_block - i
            params = {
                "module": "proxy",
                "action": "eth_getBlockByNumber",
                "tag": hex(block_num),
                "boolean": "true",
                "apikey": api_key
            }
            r = requests.get(url, params=params, timeout=10)
            block = r.json().get("result") or {}

            for tx in block.get("transactions", []):
                try:
                    value_wei = int(tx.get("value", "0x0"), 16)
                    value_eth = value_wei / 1e18

                    if value_eth >= 100:  # > 100 ETH
                        tx_hash = tx.get("hash", "")
                        whales.append({
                            "chain": "ETH",
                            "symbol": "ETH",
                            "value": round(value_eth, 4),
                            "usd_value": round(value_eth * 2700, 2),
                            "txid": tx_hash,
                            "url": f"https://etherscan.io/tx/{tx_hash}"
                        })
                except (ValueError, KeyError):
                    continue

        whales.sort(key=lambda x: x["usd_value"], reverse=True)
        return whales[:limit]
    except Exception as e:
        print(f"ETH whales error: {e}")
        return []


def analyze_whale_activity():
    """تحليل Whale Alerts (BTC + ETH)"""
    all_whales = []
    all_whales.extend(get_btc_whales(5))
    all_whales.extend(get_eth_whales(5))

    all_whales.sort(key=lambda x: x["usd_value"], reverse=True)
    total_usd = sum(w["usd_value"] for w in all_whales)

    if total_usd > 100_000_000:
        level = "HIGH"
    elif total_usd > 10_000_000:
        level = "MEDIUM"
    else:
        level = "LOW"

    return {
        "whales": all_whales[:10],
        "total_usd": round(total_usd, 2),
        "count": len(all_whales),
        "level": level,
        "timestamp": datetime.now().isoformat()
    }


# ═══════════════════════════════════════════════════════
#  SENTIMENT ANALYSIS (Fear & Greed + Reddit)
# ═══════════════════════════════════════════════════════

BULLISH_WORDS = [
    "moon", "bullish", "buy", "pump", "ath", "rocket",
    "gain", "profit", "long", "up", "surge", "rally",
    "breakout", "bull", "green", "hodl", "gem", "100x"
]

BEARISH_WORDS = [
    "crash", "bearish", "sell", "dump", "scam", "rug",
    "loss", "short", "down", "drop", "fear", "panic",
    "bear", "red", "rekt", "capitulation", "fud"
]


def analyze_text_sentiment(text):
    """تحليل مشاعر نص"""
    text_lower = text.lower()
    bull_count = sum(1 for word in BULLISH_WORDS if word in text_lower)
    bear_count = sum(1 for word in BEARISH_WORDS if word in text_lower)
    total = bull_count + bear_count
    if total == 0:
        return 0
    score = ((bull_count - bear_count) / total) * 100
    return round(score, 1)


def get_reddit_sentiment(limit=25):
    """جلب منشورات Reddit وتحليلها"""
    try:
        url = "https://www.reddit.com/r/CryptoCurrency/hot.json"
        headers = {"User-Agent": "Mozilla/5.0 CryptoGuard/1.0"}
        response = requests.get(url, params={"limit": limit}, headers=headers, timeout=10)

        if response.status_code != 200:
            print(f"Reddit: HTTP {response.status_code} (skip)")
            return {"posts": [], "avg_sentiment": 0, "total_posts": 0}

        data = response.json()
        posts = []
        total_score = 0

        for post in data.get("data", {}).get("children", []):
            p = post.get("data", {})
            title = p.get("title", "")
            ups = p.get("ups", 0)
            comments = p.get("num_comments", 0)
            url_post = "https://reddit.com" + p.get("permalink", "")

            sentiment = analyze_text_sentiment(title)
            total_score += sentiment

            posts.append({
                "title": title[:100],
                "ups": ups,
                "comments": comments,
                "sentiment": sentiment,
                "url": url_post
            })

        avg_sentiment = round(total_score / len(posts), 1) if posts else 0

        return {
            "posts": posts[:5],
            "avg_sentiment": avg_sentiment,
            "total_posts": len(posts)
        }
    except Exception as e:
        print(f"Reddit error: {e}")
        return {"posts": [], "avg_sentiment": 0, "total_posts": 0}


def get_combined_sentiment():
    """تحليل مركّب (Reddit + Fear&Greed)"""
    reddit = get_reddit_sentiment(25)

    fng_value = 50
    try:
        r = requests.get("https://api.alternative.me/fng/?limit=1", timeout=5)
        if r.ok:
            fng_value = int(r.json()["data"][0]["value"])
    except Exception:
        pass

    # Fear&Greed → sentiment (-100 إلى +100)
    fng_sentiment = (fng_value - 50) * 2

    # دمج: 40% Reddit + 60% Fear&Greed
    combined = (reddit["avg_sentiment"] * 0.4) + (fng_sentiment * 0.6)

    # تصنيف
    if combined >= 30:
        label = "VERY_BULLISH"
        emoji = "🚀"
        color = "#a6e3a1"
    elif combined >= 10:
        label = "BULLISH"
        emoji = "📈"
        color = "#94e2d5"
    elif combined >= -10:
        label = "NEUTRAL"
        emoji = "😐"
        color = "#f9e2af"
    elif combined >= -30:
        label = "BEARISH"
        emoji = "📉"
        color = "#fab387"
    else:
        label = "VERY_BEARISH"
        emoji = "😱"
        color = "#f38ba8"

    return {
        "combined_score": round(combined, 1),
        "label": label,
        "emoji": emoji,
        "color": color,
        "reddit_score": reddit["avg_sentiment"],
        "fng_value": fng_value,
        "fng_sentiment": fng_sentiment,
        "top_posts": reddit["posts"]
    }


# ═══════════════════════════════════════════════════════
#  TEST
# ═══════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("TEST WHALE ALERTS (BTC + ETH)")
    print("=" * 60)
    whales = analyze_whale_activity()
    print(f"Total USD: ${whales['total_usd']:,}")
    print(f"Level: {whales['level']}")
    print(f"Count: {whales['count']}")
    print("\nTop Whales:")
    for w in whales["whales"][:10]:
        print(f"  [{w['symbol']}] {w['value']} ≈ ${w['usd_value']:,}")

    print("\n" + "=" * 60)
    print("TEST SENTIMENT")
    print("=" * 60)
    sentiment = get_combined_sentiment()
    print(f"Combined: {sentiment['combined_score']}")
    print(f"Label: {sentiment['label']} {sentiment['emoji']}")
    print(f"Reddit: {sentiment['reddit_score']}")
    print(f"F&G: {sentiment['fng_value']}")