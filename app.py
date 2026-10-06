"""
CryptoGuard Web App - Flask Backend
Version: 7.0.0 - Complete Clean
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for, session, Response
from flask_login import LoginManager, current_user, login_required, login_user
from datetime import datetime
from models import db, User, WatchlistItem, PortfolioItem
from auth import auth
import main as cg
from ai_chat import chat
from scam_detector import enrich_with_risk
from email_alerts import send_alert_email
from authlib.integrations.flask_client import OAuth
import requests
import json
import time
import os
import re
import csv
from io import StringIO


# ═══════════════════════════════════════════════════════
#  APP CONFIG
# ═══════════════════════════════════════════════════════

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///cryptoguard.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


# ═══════════════════════════════════════════════════════
#  OAUTH CONFIG
# ═══════════════════════════════════════════════════════

oauth = OAuth(app)

oauth.register(
    name="google",
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"}
)

oauth.register(
    name="facebook",
    client_id=os.environ.get("FACEBOOK_CLIENT_ID"),
    client_secret=os.environ.get("FACEBOOK_CLIENT_SECRET"),
    access_token_url="https://graph.facebook.com/oauth/access_token",
    authorize_url="https://www.facebook.com/dialog/oauth",
    api_base_url="https://graph.facebook.com/",
    client_kwargs={"scope": "email public_profile"}
)


# ═══════════════════════════════════════════════════════
#  TRANSLATIONS
# ═══════════════════════════════════════════════════════

LANGUAGES = {"fr": "Français", "en": "English", "ar": "العربية"}

TRANSLATIONS = {
    "fr": {
        "home": "Accueil", "alerts": "Alertes", "login": "Connexion",
        "register": "Inscription", "profile": "Profil", "logout": "Déconnexion",
        "watchlist": "Watchlist", "portfolio": "Portfolio", "ai_chat": "AI Chat",
        "title": "Surveillance des cryptomonnaies en temps réel", "top": "Top",
        "refresh": "Rafraîchir", "export_csv": "Exporter CSV", "loading": "Chargement",
        "symbol": "Symbole", "name": "Nom", "price": "Prix",
        "market_cap": "Market Cap", "risk": "Risque", "action": "Action",
        "hours_24": "24 heures", "days_7": "7 jours", "days_30": "30 jours",
        "months_3": "3 mois", "year_1": "1 an",
        "top_gainers": "Top Gainers (24h)", "top_losers": "Top Losers (24h)",
        "create_alert": "Créer une alerte", "crypto": "Cryptomonnaie",
        "condition": "Condition", "target_price": "Prix cible",
        "current_price": "Prix actuel", "send_alert": "Envoyer l'alerte",
        "alert_sent": "Email envoyé!",
        "chat_placeholder": "Posez votre question...", "send": "Envoyer",
        "thinking": "Réflexion",
        "news": "Actualités crypto", "read_more": "Lire la suite",
        "description": "Description", "market_data": "Données du marché",
        "where_to_buy": "Où l'acheter?", "useful_links": "Liens utiles",
        "website": "Site officiel", "whitepaper": "Whitepaper",
        "twitter": "Twitter", "reddit": "Reddit", "explorer": "Explorer",
        "created_on": "Créée le", "volume_24h": "Volume 24h",
        "circulating": "Circulating", "max_supply": "Max Supply",
        "or_continue_with": "Ou continuer avec",
        "continue_google": "Continuer avec Google",
        "continue_facebook": "Continuer avec Facebook",
    },
    "en": {
        "home": "Home", "alerts": "Alerts", "login": "Login",
        "register": "Sign Up", "profile": "Profile", "logout": "Logout",
        "watchlist": "Watchlist", "portfolio": "Portfolio", "ai_chat": "AI Chat",
        "title": "Real-time cryptocurrency monitoring", "top": "Top",
        "refresh": "Refresh", "export_csv": "Export CSV", "loading": "Loading",
        "symbol": "Symbol", "name": "Name", "price": "Price",
        "market_cap": "Market Cap", "risk": "Risk", "action": "Action",
        "hours_24": "24 hours", "days_7": "7 days", "days_30": "30 days",
        "months_3": "3 months", "year_1": "1 year",
        "top_gainers": "Top Gainers (24h)", "top_losers": "Top Losers (24h)",
        "create_alert": "Create an alert", "crypto": "Cryptocurrency",
        "condition": "Condition", "target_price": "Target price",
        "current_price": "Current price", "send_alert": "Send alert",
        "alert_sent": "Email sent!",
        "chat_placeholder": "Ask your question...", "send": "Send",
        "thinking": "Thinking",
        "news": "Crypto news", "read_more": "Read more",
        "description": "Description", "market_data": "Market data",
        "where_to_buy": "Where to buy?", "useful_links": "Useful links",
        "website": "Official site", "whitepaper": "Whitepaper",
        "twitter": "Twitter", "reddit": "Reddit", "explorer": "Explorer",
        "created_on": "Created on", "volume_24h": "24h Volume",
        "circulating": "Circulating", "max_supply": "Max Supply",
        "or_continue_with": "Or continue with",
        "continue_google": "Continue with Google",
        "continue_facebook": "Continue with Facebook",
    },
    "ar": {
        "home": "الرئيسية", "alerts": "التنبيهات", "login": "دخول",
        "register": "تسجيل", "profile": "الملف", "logout": "خروج",
        "watchlist": "المراقبة", "portfolio": "المحفظة", "ai_chat": "المساعد الذكي",
        "title": "مراقبة العملات الرقمية في الوقت الحقيقي", "top": "الأعلى",
        "refresh": "تحديث", "export_csv": "تصدير CSV", "loading": "جاري التحميل",
        "symbol": "الرمز", "name": "الاسم", "price": "السعر",
        "market_cap": "القيمة السوقية", "risk": "المخاطر", "action": "إجراء",
        "hours_24": "24 ساعة", "days_7": "7 أيام", "days_30": "30 يوم",
        "months_3": "3 أشهر", "year_1": "سنة واحدة",
        "top_gainers": "الأكثر صعودًا (24 ساعة)", "top_losers": "الأكثر هبوطًا (24 ساعة)",
        "create_alert": "إنشاء تنبيه", "crypto": "العملة الرقمية",
        "condition": "الشرط", "target_price": "السعر المستهدف",
        "current_price": "السعر الحالي", "send_alert": "إرسال التنبيه",
        "alert_sent": "تم إرسال الإيميل!",
        "chat_placeholder": "اطرح سؤالك...", "send": "إرسال",
        "thinking": "جاري التفكير",
        "news": "أخبار العملات", "read_more": "اقرأ المزيد",
        "description": "الوصف", "market_data": "بيانات السوق",
        "where_to_buy": "أين تشتريها؟", "useful_links": "روابط مفيدة",
        "website": "الموقع الرسمي", "whitepaper": "الورقة البيضاء",
        "twitter": "تويتر", "reddit": "ريديت", "explorer": "المستكشف",
        "created_on": "أنشئت في", "volume_24h": "حجم 24 ساعة",
        "circulating": "المتداول", "max_supply": "الحد الأقصى",
        "or_continue_with": "أو تابع بـ",
        "continue_google": "تابع بحساب Google",
        "continue_facebook": "تابع بحساب Facebook",
    },
}


def get_locale():
    if "language" in session:
        return session["language"]
    return request.accept_languages.best_match(LANGUAGES.keys())


def t(key, default=None):
    lang = get_locale()
    value = TRANSLATIONS.get(lang, {}).get(key)
    if value:
        return value
    value = TRANSLATIONS.get("en", {}).get(key)
    if value:
        return value
    if default:
        return default
    return key.replace("_", " ").title()


@app.context_processor
def inject_globals():
    return dict(get_locale=get_locale, languages=LANGUAGES, t=t)


# ═══════════════════════════════════════════════════════
#  LOGIN MANAGER
# ═══════════════════════════════════════════════════════

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


app.register_blueprint(auth)


# ═══════════════════════════════════════════════════════
#  MAIN ROUTES
# ═══════════════════════════════════════════════════════

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/set_language/<lang>")
def set_language(lang):
    if lang in LANGUAGES:
        session["language"] = lang
    return redirect(request.referrer or url_for("index"))


# ═══════════════════════════════════════════════════════
#  OAUTH
# ═══════════════════════════════════════════════════════

@app.route("/auth/google")
def google_login():
    redirect_uri = url_for("google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@app.route("/auth/google/callback")
def google_callback():
    try:
        token = oauth.google.authorize_access_token()
        user_info = token.get("userinfo") or oauth.google.userinfo()
        email = (user_info.get("email") or "").lower()
        name = user_info.get("name") or email.split("@")[0]
        if not email:
            return redirect(url_for("auth.login"))
        user = User.query.filter_by(email=email).first()
        if not user:
            base_username = email.split("@")[0]
            username = base_username
            counter = 1
            while User.query.filter_by(username=username).first():
                username = f"{base_username}{counter}"
                counter += 1
            user = User(username=username, email=email, password_hash="oauth-google")
            db.session.add(user)
            db.session.commit()
        login_user(user)
        return redirect(url_for("index"))
    except Exception as e:
        print(f"Google OAuth error: {e}")
        return redirect(url_for("auth.login"))


@app.route("/auth/facebook")
def facebook_login():
    redirect_uri = url_for("facebook_callback", _external=True)
    return oauth.facebook.authorize_redirect(redirect_uri)


@app.route("/auth/facebook/callback")
def facebook_callback():
    try:
        token = oauth.facebook.authorize_access_token()
        resp = oauth.facebook.get("me?fields=id,name,email")
        profile = resp.json()
        email = (profile.get("email") or "").lower()
        name = profile.get("name", "Facebook User")
        fb_id = profile.get("id", "")
        if not email:
            email = f"fb_{fb_id}@cryptoguard.local"
        user = User.query.filter_by(email=email).first()
        if not user:
            base_username = name.replace(" ", "").lower()[:15] or f"fb_{fb_id}"
            username = base_username
            counter = 1
            while User.query.filter_by(username=username).first():
                username = f"{base_username}{counter}"
                counter += 1
            user = User(username=username, email=email, password_hash="oauth-facebook")
            db.session.add(user)
            db.session.commit()
        login_user(user)
        return redirect(url_for("index"))
    except Exception as e:
        print(f"Facebook OAuth error: {e}")
        return redirect(url_for("auth.login"))


# ═══════════════════════════════════════════════════════
#  API: PRICES
# ═══════════════════════════════════════════════════════

@app.route("/api/prices")
def api_prices():
    limit = request.args.get("limit", 20, type=int)
    currency = request.args.get("currency", "usd")
    data = cg.get_top_cryptos(limit, currency)
    if not data:
        data = cg.fetch_prices_robust(cg.CRYPTOS[:limit], currency)
    if not data:
        return jsonify({"error": "Impossible de récupérer les données"}), 500
    data = enrich_with_risk(data)
    return jsonify({"timestamp": datetime.now().isoformat(), "currency": currency, "data": data})


# ═══════════════════════════════════════════════════════
#  API: HISTORY
# ═══════════════════════════════════════════════════════

@app.route("/api/history/<crypto_id>")
def api_history(crypto_id):
    days = request.args.get("days", 7, type=int)
    if days not in [1, 7, 30, 90, 365]:
        days = 7
    cache_file = "cache_history.json"
    cache_key = f"{crypto_id}_{days}"
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cache = json.load(f)
            entry = cache.get(cache_key)
            if entry and (time.time() - entry["timestamp"]) < 3600:
                return jsonify({"crypto_id": crypto_id, "days": days, "prices": entry["prices"], "timestamps": entry.get("timestamps", []), "cached": True})
        except (json.JSONDecodeError, IOError):
            pass
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}/market_chart"
        r = requests.get(url, params={"vs_currency": "usd", "days": days}, timeout=10)
        r.raise_for_status()
        data = r.json()
        prices = [p[1] for p in data.get("prices", [])]
        timestamps = [p[0] for p in data.get("prices", [])]
        cache = {}
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache = json.load(f)
            except (json.JSONDecodeError, IOError):
                cache = {}
        cache[cache_key] = {"timestamp": time.time(), "prices": prices, "timestamps": timestamps}
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache, f)
        except IOError:
            pass
        return jsonify({"crypto_id": crypto_id, "days": days, "prices": prices, "timestamps": timestamps, "cached": False})
    except requests.RequestException as e:
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache = json.load(f)
                entry = cache.get(cache_key)
                if entry:
                    return jsonify({"crypto_id": crypto_id, "days": days, "prices": entry["prices"], "timestamps": entry.get("timestamps", []), "cached": True, "stale": True})
            except (json.JSONDecodeError, IOError):
                pass
        return jsonify({"error": f"Erreur API: {str(e)}"}), 500


# ═══════════════════════════════════════════════════════
#  API: INDICATORS
# ═══════════════════════════════════════════════════════

@app.route("/api/indicators/<crypto_id>")
def api_indicators(crypto_id):
    from technical_indicators import calculate_all_indicators
    days = request.args.get("days", 90, type=int)
    cache_file = "cache_history.json"
    cache_key = f"{crypto_id}_{days}"
    prices = None
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cache = json.load(f)
            entry = cache.get(cache_key)
            if entry and (time.time() - entry["timestamp"]) < 3600:
                prices = entry["prices"]
        except (json.JSONDecodeError, IOError):
            pass
    if not prices:
        try:
            url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}/market_chart"
            r = requests.get(url, params={"vs_currency": "usd", "days": days}, timeout=10)
            r.raise_for_status()
            data = r.json()
            prices = [p[1] for p in data.get("prices", [])]
            cache = {}
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        cache = json.load(f)
                except (json.JSONDecodeError, IOError):
                    cache = {}
            cache[cache_key] = {"timestamp": time.time(), "prices": prices, "timestamps": []}
            try:
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(cache, f)
            except IOError:
                pass
        except requests.RequestException:
            pass
    if not prices:
        bmap = {"bitcoin":"BTCUSDT","ethereum":"ETHUSDT","binancecoin":"BNBUSDT","solana":"SOLUSDT","ripple":"XRPUSDT","cardano":"ADAUSDT","dogecoin":"DOGEUSDT"}
        symbol = bmap.get(crypto_id)
        if symbol:
            try:
                r = requests.get("https://api.binance.com/api/v3/klines", params={"symbol": symbol, "interval": "1d", "limit": min(days, 365)}, timeout=10)
                r.raise_for_status()
                prices = [float(k[4]) for k in r.json()]
            except Exception:
                pass
    if not prices:
        return jsonify({"error": "Impossible de récupérer les données"}), 500
    indicators = calculate_all_indicators(prices)
    return jsonify({"crypto_id": crypto_id, "indicators": indicators})


# ═══════════════════════════════════════════════════════
#  API: FEAR & GREED
# ═══════════════════════════════════════════════════════

@app.route("/api/fear-greed")
def api_fear_greed():
    try:
        r = requests.get("https://api.alternative.me/fng/?limit=30", timeout=10)
        r.raise_for_status()
        data = r.json()
        current = data["data"][0]
        value = int(current["value"])
        classification = current["value_classification"]
        timestamp = int(current["timestamp"])
        history = [{"value": int(i["value"]), "timestamp": int(i["timestamp"]), "classification": i["value_classification"]} for i in data["data"]]
        if value <= 25:
            color, emoji = "#f38ba8", "😱"
        elif value <= 45:
            color, emoji = "#fab387", "😟"
        elif value <= 55:
            color, emoji = "#f9e2af", "😐"
        elif value <= 75:
            color, emoji = "#a6e3a1", "😊"
        else:
            color, emoji = "#40a02b", "🤑"
        return jsonify({"value": value, "classification": classification, "color": color, "emoji": emoji, "timestamp": timestamp, "history": history})
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500


# ═══════════════════════════════════════════════════════
#  API: GAS
# ═══════════════════════════════════════════════════════

@app.route("/api/gas")
def api_gas():
    eth_price = 2500
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price", params={"ids": "ethereum", "vs_currencies": "usd"}, timeout=5)
        if r.ok:
            eth_price = r.json().get("ethereum", {}).get("usd", 2500)
    except Exception:
        pass
    gas_data = {"slow": {"gwei": 12, "seconds": 300}, "standard": {"gwei": 22, "seconds": 60}, "fast": {"gwei": 35, "seconds": 30}}
    def calc(gwei, units):
        return round(gwei * units * 1e-9 * eth_price, 3)
    result = []
    for name, info in gas_data.items():
        g = info["gwei"]
        result.append({"name": name, "max_fee": g, "usd_transfer": calc(g, 21000), "usd_swap": calc(g, 150000), "estimated_seconds": info["seconds"]})
    return jsonify({"eth_price": round(eth_price, 2), "speeds": result, "timestamp": int(time.time())})


# ═══════════════════════════════════════════════════════
#  API: WHALES
# ═══════════════════════════════════════════════════════

@app.route("/api/whales")
def api_whales():
    from whale_sentiment import analyze_whale_activity
    try:
        return jsonify(analyze_whale_activity())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ═══════════════════════════════════════════════════════
#  API: SENTIMENT
# ═══════════════════════════════════════════════════════

@app.route("/api/sentiment")
def api_sentiment():
    from whale_sentiment import get_combined_sentiment
    try:
        return jsonify(get_combined_sentiment())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ═══════════════════════════════════════════════════════
#  API: DCA
# ═══════════════════════════════════════════════════════

@app.route("/api/dca", methods=["POST"])
def api_dca():
    data = request.get_json()
    crypto_id = data.get("crypto_id", "bitcoin").lower()
    amount = float(data.get("monthly_amount", 100))
    months = int(data.get("months", 12))
    if months < 1 or months > 60 or amount <= 0:
        return jsonify({"error": "Paramètres invalides"}), 400
    try:
        days = months * 30
        url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}/market_chart"
        r = requests.get(url, params={"vs_currency": "usd", "days": days}, timeout=15)
        r.raise_for_status()
        cd = r.json()
        prices = [p[1] for p in cd.get("prices", [])]
        timestamps = [p[0] for p in cd.get("prices", [])]
        if not prices:
            return jsonify({"error": "Pas de données"}), 500
        total_inv = 0
        total_coins = 0
        purchases = []
        step = max(1, len(prices) // months)
        for i in range(0, len(prices), step):
            if len(purchases) >= months:
                break
            price = prices[i]
            if price > 0:
                cb = amount / price
                total_coins += cb
                total_inv += amount
                purchases.append({"date": timestamps[i], "coins": cb})
        cur_price = prices[-1]
        cur_val = total_coins * cur_price
        roi = ((cur_val - total_inv) / total_inv * 100) if total_inv > 0 else 0
        avg = (total_inv / total_coins) if total_coins > 0 else 0
        first = purchases[0] if purchases else None
        lump = (total_inv / prices[0]) * cur_price if prices[0] > 0 else 0
        return jsonify({
            "crypto_id": crypto_id, "monthly_amount": amount, "months": months,
            "total_invested": round(total_inv, 2), "total_coins": round(total_coins, 8),
            "current_price": round(cur_price, 2), "current_value": round(cur_val, 2),
            "roi": round(roi, 2), "avg_buy_price": round(avg, 2),
            "profit": round(cur_val - total_inv, 2),
            "lump_sum_value": round(lump, 2),
            "dca_vs_lumpsum": round(cur_val - lump, 2)
        })
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500


# ═══════════════════════════════════════════════════════
#  API: SIGNALS
# ═══════════════════════════════════════════════════════

@app.route("/api/signals/<crypto_id>")
def api_signals(crypto_id):
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}"
        params = {"localization": "false", "tickers": "false", "market_data": "true", "developer_data": "false", "community_data": "false"}
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        md = data.get("market_data", {})
        name = data.get("name", crypto_id)
        symbol = (data.get("symbol") or "").upper()
        prompt = f"""Analyse {name} ({symbol}) et donne un signal de trading:
Prix: ${md.get('current_price', {}).get('usd', 0):,.2f}
24h: {md.get('price_change_percentage_24h', 0):.2f}%
7j: {md.get('price_change_percentage_7d', 0):.2f}%
30j: {md.get('price_change_percentage_30d', 0):.2f}%
Market Cap: ${md.get('market_cap', {}).get('usd', 0):,.0f}
ATH: ${md.get('ath', {}).get('usd', 0):,.2f}

Réponds en JSON:
{{
  "signal": "BUY" ou "SELL" ou "HOLD",
  "confidence": 0-100,
  "timeframe": "short" ou "medium" ou "long",
  "reasoning": "3-4 phrases",
  "risk_level": "LOW" ou "MEDIUM" ou "HIGH",
  "key_points": ["p1", "p2", "p3"]
}}
Ne donne QUE le JSON."""
        response_text = chat(prompt)
        m = re.search(r'\{.*\}', response_text, re.DOTALL)
        if not m:
            return jsonify({"error": "Réponse AI invalide"}), 500
        try:
            result = json.loads(m.group())
        except json.JSONDecodeError:
            return jsonify({"error": "JSON invalide"}), 500
        result["crypto_id"] = crypto_id
        result["crypto_name"] = name
        result["crypto_symbol"] = symbol
        result["current_price"] = md.get("current_price", {}).get("usd", 0)
        return jsonify(result)
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500


# ═══════════════════════════════════════════════════════
#  API: EXCHANGES
# ═══════════════════════════════════════════════════════

@app.route("/api/exchanges/<crypto_id>")
def api_exchanges(crypto_id):
    bmap = {"bitcoin":"BTCUSDT","ethereum":"ETHUSDT","binancecoin":"BNBUSDT","solana":"SOLUSDT","ripple":"XRPUSDT","cardano":"ADAUSDT","dogecoin":"DOGEUSDT"}
    kmap = {"bitcoin":"XBTUSDT","ethereum":"ETHUSDT","binancecoin":"BNBUSDT","solana":"SOLUSDT","ripple":"XRPUSDT","cardano":"ADAUSDT","dogecoin":"DOGEUSDT"}
    exchanges = []
    bs = bmap.get(crypto_id)
    if bs:
        try:
            r = requests.get("https://api.binance.com/api/v3/ticker/24hr", params={"symbol": bs}, timeout=8)
            if r.ok:
                d = r.json()
                exchanges.append({"name": "Binance", "price": float(d["lastPrice"]), "volume_24h": float(d["quoteVolume"]), "change_24h": float(d["priceChangePercent"]), "url": f"https://www.binance.com/en/trade/{bs}"})
        except Exception:
            pass
    ks = kmap.get(crypto_id)
    if ks:
        try:
            r = requests.get("https://api.kraken.com/0/public/Ticker", params={"pair": ks}, timeout=8)
            if r.ok:
                d = r.json()
                if d.get("result"):
                    pd = list(d["result"].values())[0]
                    price = float(pd["c"][0])
                    op = float(pd["o"])
                    change = ((price - op) / op * 100) if op > 0 else 0
                    exchanges.append({"name": "Kraken", "price": price, "volume_24h": float(pd["v"][1]) * price, "change_24h": round(change, 2), "url": f"https://pro.kraken.com/app/trade/{ks.lower()}"})
        except Exception:
            pass
    if not exchanges:
        return jsonify({"error": "Aucune donnée"}), 500
    exchanges.sort(key=lambda x: x["price"])
    cheapest = exchanges[0]
    expensive = exchanges[-1]
    spread = ((expensive["price"] - cheapest["price"]) / cheapest["price"] * 100) if cheapest["price"] > 0 else 0
    return jsonify({"crypto_id": crypto_id, "exchanges": exchanges, "cheapest": cheapest["name"], "expensive": expensive["name"], "spread": round(spread, 3)})


# ═══════════════════════════════════════════════════════
#  API: TOP MOVERS
# ═══════════════════════════════════════════════════════

@app.route("/api/top_movers")
def api_top_movers():
    limit = request.args.get("limit", 100, type=int)
    data = cg.get_top_cryptos(limit, "usd")
    if not data:
        data = cg.fetch_prices_robust(cg.CRYPTOS[:limit], "usd")
    if not data:
        return jsonify({"error": "Impossible"}), 500
    valid = [c for c in data if c.get("price_change_percentage_24h") is not None]
    gainers = sorted(valid, key=lambda x: x.get("price_change_percentage_24h", 0), reverse=True)[:5]
    losers = sorted(valid, key=lambda x: x.get("price_change_percentage_24h", 0))[:5]
    def fmt(c):
        return {"id": c.get("id"), "symbol": c.get("symbol", "").upper(), "name": c.get("name"), "current_price": c.get("current_price", 0), "price_change_percentage_24h": c.get("price_change_percentage_24h", 0), "market_cap": c.get("market_cap", 0)}
    return jsonify({"gainers": [fmt(c) for c in gainers], "losers": [fmt(c) for c in losers]})


# ═══════════════════════════════════════════════════════
#  API: EXPORT CSV
# ═══════════════════════════════════════════════════════

@app.route("/api/export/csv")
def export_csv():
    limit = request.args.get("limit", 20, type=int)
    currency = request.args.get("currency", "usd")
    data = cg.get_top_cryptos(limit, currency)
    if not data:
        data = cg.fetch_prices_robust(cg.CRYPTOS[:limit], currency)
    if not data:
        return jsonify({"error": "Impossible"}), 500
    data = enrich_with_risk(data)
    si = StringIO()
    w = csv.writer(si)
    w.writerow(["#", "Symbole", "Nom", "Prix", "24h (%)", "Market Cap", "Risque", "Level"])
    for i, c in enumerate(data, 1):
        w.writerow([i, c.get("symbol", "").upper(), c.get("name", ""), c.get("current_price", 0), c.get("price_change_percentage_24h", 0), c.get("market_cap", 0), c.get("risk_score", 0), c.get("risk_level", "LOW")])
    out = si.getvalue()
    si.close()
    return Response(out, mimetype="text/csv", headers={"Content-Disposition": f"attachment; filename=cryptoguard_{currency}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"})


# ═══════════════════════════════════════════════════════
#  API: CRYPTO DETAILS
# ═══════════════════════════════════════════════════════

@app.route("/api/crypto/<crypto_id>")
def api_crypto_details(crypto_id):
    cache_file = "cache_crypto.json"
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cache = json.load(f)
            entry = cache.get(crypto_id)
            if entry and (time.time() - entry["timestamp"]) < 86400:
                return jsonify(entry["data"])
        except (json.JSONDecodeError, IOError):
            pass
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}"
        params = {"localization": "false", "tickers": "false", "market_data": "true", "community_data": "false", "developer_data": "false"}
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        md = data.get("market_data", {})
        links = data.get("links", {})
        desc = data.get("description", {}).get("en", "") or ""
        desc = re.sub(r'<[^>]+>', '', desc)[:600]
        exchanges = []
        try:
            r2 = requests.get(f"https://api.coingecko.com/api/v3/coins/{crypto_id}/tickers", params={"order": "trust_score_desc"}, timeout=10)
            if r2.ok:
                seen = set()
                for tk in r2.json().get("tickers", []):
                    en = tk.get("market", {}).get("name", "")
                    eu = tk.get("trade_url", "") or tk.get("market", {}).get("url", "")
                    if en and en not in seen:
                        seen.add(en)
                        exchanges.append({"name": en, "url": eu, "pair": tk.get("base", "") + "/" + tk.get("target", "")})
                    if len(exchanges) >= 6:
                        break
        except Exception:
            pass
        result = {
            "id": data.get("id"), "symbol": (data.get("symbol") or "").upper(), "name": data.get("name", ""),
            "image": (data.get("image") or {}).get("large", ""), "description": desc,
            "genesis_date": data.get("genesis_date"),
            "homepage": (links.get("homepage") or [""])[0], "whitepaper": links.get("whitepaper", ""),
            "twitter": links.get("twitter_screen_name", ""), "reddit": links.get("subreddit_url", ""),
            "blockchain_site": (links.get("blockchain_site") or [""])[0],
            "market_data": {
                "current_price": md.get("current_price", {}).get("usd", 0), "market_cap": md.get("market_cap", {}).get("usd", 0),
                "total_volume": md.get("total_volume", {}).get("usd", 0), "ath": md.get("ath", {}).get("usd", 0),
                "circulating_supply": md.get("circulating_supply", 0), "max_supply": md.get("max_supply", 0),
                "price_change_24h": md.get("price_change_percentage_24h", 0),
            },
            "exchanges": exchanges
        }
        cache = {}
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache = json.load(f)
            except (json.JSONDecodeError, IOError):
                cache = {}
        cache[crypto_id] = {"timestamp": time.time(), "data": result}
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache, f)
        except IOError:
            pass
        return jsonify(result)
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500


# ═══════════════════════════════════════════════════════
#  API: NEWS
# ═══════════════════════════════════════════════════════

@app.route("/api/news")
def api_news():
    import xml.etree.ElementTree as ET
    feeds = ["https://cointelegraph.com/rss", "https://www.coindesk.com/arc/outboundfeeds/rss/", "https://cryptonews.com/news/feed/"]
    for feed_url in feeds:
        try:
            r = requests.get(feed_url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()
            root = ET.fromstring(r.content)
            news = []
            for item in root.findall(".//item")[:9]:
                title = item.find("title")
                link = item.find("link")
                pd = item.find("pubDate")
                desc = item.find("description")
                enc = item.find("enclosure")
                image = enc.get("url", "") if enc is not None else ""
                published = 0
                if pd is not None and pd.text:
                    try:
                        from email.utils import parsedate_to_datetime
                        published = int(parsedate_to_datetime(pd.text).timestamp())
                    except Exception:
                        pass
                news.append({"title": (title.text if title is not None else "") or "", "url": (link.text if link is not None else "") or "", "source": feed_url.split("/")[2].replace("www.", ""), "image": image, "published": published, "body": ((desc.text if desc is not None else "") or "")[:120] + "..."})
            if news:
                return jsonify({"news": news})
        except Exception:
            continue
    return jsonify({"error": "Impossible"}), 500


# ═══════════════════════════════════════════════════════
#  API: CHAT
# ═══════════════════════════════════════════════════════

@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json()
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "Message vide"}), 400
    cdata = cg.get_top_cryptos(10, "usd")
    if not cdata:
        cdata = cg.fetch_prices_robust(cg.CRYPTOS[:10], "usd")
    return jsonify({"message": message, "response": chat(message, cdata)})


# ═══════════════════════════════════════════════════════
#  API: ALERTS
# ═══════════════════════════════════════════════════════

@app.route("/api/alerts/test", methods=["POST"])
@login_required
def api_alerts_test():
    data = request.get_json()
    result = send_alert_email(
        to_email=current_user.email, username=current_user.username,
        crypto_symbol=data.get("crypto_symbol", "BTC"),
        current_price=data.get("current_price", 0),
        condition=data.get("condition", "above"),
        target_price=data.get("target_price", 0)
    )
    return jsonify(result)


# ═══════════════════════════════════════════════════════
#  API: ANALYZE CONTRACT
# ═══════════════════════════════════════════════════════

@app.route("/api/analyze-contract", methods=["POST"])
def api_analyze_contract():
    from contract_analyzer import analyze_contract_image
    if "image" not in request.files:
        return jsonify({"error": "Aucune image"}), 400
    image = request.files["image"]
    if not image.filename:
        return jsonify({"error": "Fichier vide"}), 400
    if image.mimetype not in ["image/png", "image/jpeg", "image/jpg", "image/webp"]:
        return jsonify({"error": "Type non supporté"}), 400
    image.seek(0, 2)
    size = image.tell()
    image.seek(0)
    if size > 5 * 1024 * 1024:
        return jsonify({"error": "Image > 5 MB"}), 400
    try:
        result = analyze_contract_image(image.read(), image.mimetype, get_locale())
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ═══════════════════════════════════════════════════════
#  API: PORTFOLIO HISTORY
# ═══════════════════════════════════════════════════════

@app.route("/api/portfolio/history")
@login_required
def api_portfolio_history():
    items = PortfolioItem.query.filter_by(user_id=current_user.id).all()
    if not items:
        return jsonify({"error": "Portfolio vide"}), 400
    cids = list(set([i.crypto_id for i in items]))
    days = 30
    cache_file = "cache_history.json"
    ch = {}
    for cid in cids:
        ck = f"{cid}_{days}"
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache = json.load(f)
                entry = cache.get(ck)
                if entry and entry.get("prices"):
                    ch[cid] = {"prices": entry["prices"]}
                    continue
            except (json.JSONDecodeError, IOError):
                pass
        try:
            r = requests.get(f"https://api.coingecko.com/api/v3/coins/{cid}/market_chart", params={"vs_currency": "usd", "days": days}, timeout=10)
            if r.ok:
                d = r.json()
                prices = [p[1] for p in d.get("prices", [])]
                timestamps = [p[0] for p in d.get("prices", [])]
                ch[cid] = {"prices": prices, "timestamps": timestamps}
                cache = {}
                if os.path.exists(cache_file):
                    try:
                        with open(cache_file, "r", encoding="utf-8") as f:
                            cache = json.load(f)
                    except (json.JSONDecodeError, IOError):
                        cache = {}
                cache[ck] = {"timestamp": time.time(), "prices": prices, "timestamps": timestamps}
                try:
                    with open(cache_file, "w", encoding="utf-8") as f:
                        json.dump(cache, f)
                except IOError:
                    pass
        except requests.RequestException:
            continue
    if not ch:
        return jsonify({"error": "Impossible"}), 500
    min_len = min(len(h["prices"]) for h in ch.values())
    timeline = []
    ts_ref = None
    for cid, h in ch.items():
        if h.get("timestamps") and len(h["timestamps"]) >= min_len and not ts_ref:
            ts_ref = h["timestamps"][-min_len:]
    for i in range(min_len):
        total = 0
        for item in items:
            h = ch.get(item.crypto_id)
            if h and len(h["prices"]) > i:
                total += h["prices"][-(min_len - i)] * item.amount
        timeline.append(round(total, 2))
    total_cost = sum(i.buy_price * i.amount for i in items)
    return jsonify({"timeline": timeline, "timestamps": ts_ref or [], "total_cost": round(total_cost, 2), "crypto_count": len(cids)})


# ═══════════════════════════════════════════════════════
#  PROFILE / WATCHLIST / PORTFOLIO
# ═══════════════════════════════════════════════════════

@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html", user=current_user)


@app.route("/watchlist")
@login_required
def watchlist():
    items = WatchlistItem.query.filter_by(user_id=current_user.id).all()
    cids = [i.crypto_id for i in items]
    prices = {}
    if cids:
        data = cg.fetch_prices_robust(cids, "usd")
        if data:
            prices = {c["id"]: c for c in data}
    return render_template("watchlist.html", items=items, prices=prices)


@app.route("/watchlist/add/<crypto_id>", methods=["POST"])
@login_required
def watchlist_add(crypto_id):
    symbol = request.form.get("symbol", crypto_id[:3]).upper()
    if not WatchlistItem.query.filter_by(user_id=current_user.id, crypto_id=crypto_id).first():
        db.session.add(WatchlistItem(user_id=current_user.id, crypto_id=crypto_id, crypto_symbol=symbol))
        db.session.commit()
        return jsonify({"status": "added"})
    return jsonify({"status": "exists"})


@app.route("/watchlist/remove/<crypto_id>", methods=["POST"])
@login_required
def watchlist_remove(crypto_id):
    item = WatchlistItem.query.filter_by(user_id=current_user.id, crypto_id=crypto_id).first()
    if item:
        db.session.delete(item)
        db.session.commit()
        return jsonify({"status": "removed"})
    return jsonify({"status": "not_found"}), 404


@app.route("/portfolio")
@login_required
def portfolio():
    items = PortfolioItem.query.filter_by(user_id=current_user.id).all()
    cids = list(set([i.crypto_id for i in items]))
    prices = {}
    if cids:
        data = cg.fetch_prices_robust(cids, "usd")
        if data:
            prices = {c["id"]: c["current_price"] for c in data}
    total_value = 0
    total_cost = 0
    enriched = []
    for item in items:
        cp = prices.get(item.crypto_id, 0)
        cv = cp * item.amount
        cost = item.buy_price * item.amount
        pnl = cv - cost
        pnl_p = (pnl / cost * 100) if cost > 0 else 0
        total_value += cv
        total_cost += cost
        enriched.append({"id": item.id, "crypto_id": item.crypto_id, "symbol": item.crypto_symbol, "amount": item.amount, "buy_price": item.buy_price, "current_price": cp, "current_value": cv, "cost": cost, "pnl": pnl, "pnl_percent": pnl_p})
    total_pnl = total_value - total_cost
    total_pnl_p = (total_pnl / total_cost * 100) if total_cost > 0 else 0
    return render_template("portfolio.html", items=enriched, total_value=total_value, total_cost=total_cost, total_pnl=total_pnl, total_pnl_percent=total_pnl_p)


@app.route("/portfolio/add", methods=["POST"])
@login_required
def portfolio_add():
    data = request.get_json()
    cid = data.get("crypto_id", "").lower()
    sym = data.get("crypto_symbol", "").upper()
    amount = float(data.get("amount", 0))
    bp = float(data.get("buy_price", 0))
    if not cid or amount <= 0 or bp <= 0:
        return jsonify({"error": "Données invalides"}), 400
    item = PortfolioItem(user_id=current_user.id, crypto_id=cid, crypto_symbol=sym, amount=amount, buy_price=bp)
    db.session.add(item)
    db.session.commit()
    return jsonify({"status": "added", "id": item.id})


@app.route("/portfolio/remove/<int:item_id>", methods=["POST"])
@login_required
def portfolio_remove(item_id):
    item = PortfolioItem.query.filter_by(id=item_id, user_id=current_user.id).first()
    if item:
        db.session.delete(item)
        db.session.commit()
        return jsonify({"status": "removed"})
    return jsonify({"status": "not_found"}), 404


# ═══════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=5000)