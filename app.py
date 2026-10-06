"""
CryptoGuard Web App - Flask Backend
Version: 6.0.0 - Complete with all features
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
        "chart_title": "Bitcoin - 7 derniers jours",
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
        "chart_title": "Bitcoin - Last 7 days",
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
        "chart_title": "Bitcoin - آخر 7 أيام",
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
#  OAUTH ROUTES
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
    allowed_days = [1, 7, 30, 90, 365]
    if days not in allowed_days:
        days = 7

    cache_file = "cache_history.json"
    cache_duration = 3600
    cache_key = f"{crypto_id}_{days}"

    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cache = json.load(f)
            entry = cache.get(cache_key)
            if entry and (time.time() - entry["timestamp"]) < cache_duration:
                return jsonify({"crypto_id": crypto_id, "days": days, "prices": entry["prices"], "timestamps": entry.get("timestamps", []), "cached": True})
        except (json.JSONDecodeError, IOError):
            pass

    try:
        url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}/market_chart"
        params = {"vs_currency": "usd", "days": days}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
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
#  API: TECHNICAL INDICATORS
# ═══════════════════════════════════════════════════════

@app.route("/api/indicators/<crypto_id>")
def api_indicators(crypto_id):
    from technical_indicators import calculate_all_indicators

    days = request.args.get("days", 90, type=int)

    cache_file = "cache_history.json"
    cache_duration = 3600
    cache_key = f"{crypto_id}_{days}"

    prices = None
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cache = json.load(f)
            entry = cache.get(cache_key)
            if entry and (time.time() - entry["timestamp"]) < cache_duration:
                prices = entry["prices"]
        except (json.JSONDecodeError, IOError):
            pass

    if not prices:
        try:
            url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}/market_chart"
            params = {"vs_currency": "usd", "days": days}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
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
        binance_map = {
            "bitcoin": "BTCUSDT", "ethereum": "ETHUSDT",
            "binancecoin": "BNBUSDT", "solana": "SOLUSDT",
            "ripple": "XRPUSDT", "cardano": "ADAUSDT",
            "dogecoin": "DOGEUSDT", "tron": "TRXUSDT",
            "polkadot": "DOTUSDT", "chainlink": "LINKUSDT",
            "matic-network": "MATICUSDT", "avalanche-2": "AVAXUSDT",
            "litecoin": "LTCUSDT", "uniswap": "UNIUSDT",
            "stellar": "XLMUSDT"
        }
        symbol = binance_map.get(crypto_id)
        if symbol:
            try:
                url = "https://api.binance.com/api/v3/klines"
                params = {"symbol": symbol, "interval": "1d", "limit": min(days, 365)}
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                prices = [float(k[4]) for k in data]
            except Exception:
                pass

    if not prices:
        return jsonify({"error": "Impossible de récupérer les données. Réessayez dans 1 minute."}), 500

    indicators = calculate_all_indicators(prices)
    return jsonify({"crypto_id": crypto_id, "indicators": indicators})


# ═══════════════════════════════════════════════════════
#  API: FEAR & GREED
# ═══════════════════════════════════════════════════════

@app.route("/api/fear-greed")
def api_fear_greed():
    try:
        url = "https://api.alternative.me/fng/?limit=30"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        current = data["data"][0]
        value = int(current["value"])
        classification = current["value_classification"]
        timestamp = int(current["timestamp"])

        history = []
        for item in data["data"]:
            history.append({
                "value": int(item["value"]),
                "timestamp": int(item["timestamp"]),
                "classification": item["value_classification"]
            })

        if value <= 25:
            color = "#f38ba8"
            emoji = "😱"
        elif value <= 45:
            color = "#fab387"
            emoji = "😟"
        elif value <= 55:
            color = "#f9e2af"
            emoji = "😐"
        elif value <= 75:
            color = "#a6e3a1"
            emoji = "😊"
        else:
            color = "#40a02b"
            emoji = "🤑"

        return jsonify({
            "value": value,
            "classification": classification,
            "color": color,
            "emoji": emoji,
            "timestamp": timestamp,
            "history": history
        })
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500


# ═══════════════════════════════════════════════════════
#  API: GAS TRACKER
# ═══════════════════════════════════════════════════════

@app.route("/api/gas")
def api_gas():
    eth_price = 2500
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "ethereum", "vs_currencies": "usd"},
            timeout=5
        )
        if r.ok:
            eth_price = r.json().get("ethereum", {}).get("usd", 2500)
    except Exception:
        pass

    gas_data = {
        "slow": {"gwei": 12, "seconds": 300},
        "standard": {"gwei": 22, "seconds": 60},
        "fast": {"gwei": 35, "seconds": 30},
    }

    def calc_usd(gwei, gas_units):
        return round(gwei * gas_units * 1e-9 * eth_price, 3)

    result = []
    for name, info in gas_data.items():
        gwei = info["gwei"]
        result.append({
            "name": name,
            "max_fee": gwei,
            "usd_transfer": calc_usd(gwei, 21000),
            "usd_swap": calc_usd(gwei, 150000),
            "usd_nft": calc_usd(gwei, 85000),
            "estimated_seconds": info["seconds"],
        })

    return jsonify({
        "eth_price": round(eth_price, 2),
        "speeds": result,
        "timestamp": int(time.time())
    })


# ═══════════════════════════════════════════════════════
#  API: DCA CALCULATOR
# ═══════════════════════════════════════════════════════

@app.route("/api/dca", methods=["POST"])
def api_dca():
    data = request.get_json()
    crypto_id = data.get("crypto_id", "bitcoin").lower()
    monthly_amount = float(data.get("monthly_amount", 100))
    months = int(data.get("months", 12))

    if months < 1 or months > 60:
        return jsonify({"error": "Mois entre 1 et 60"}), 400
    if monthly_amount <= 0:
        return jsonify({"error": "Montant invalide"}), 400

    try:
        days = months * 30
        url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}/market_chart"
        params = {"vs_currency": "usd", "days": days}
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        chart_data = response.json()

        prices = [p[1] for p in chart_data.get("prices", [])]
        timestamps = [p[0] for p in chart_data.get("prices", [])]

        if not prices:
            return jsonify({"error": "Pas de données"}), 500

        total_invested = 0
        total_coins = 0
        purchases = []

        step = max(1, len(prices) // months)
        for i in range(0, len(prices), step):
            if len(purchases) >= months:
                break
            price = prices[i]
            if price > 0:
                coins_bought = monthly_amount / price
                total_coins += coins_bought
                total_invested += monthly_amount
                purchases.append({
                    "date": timestamps[i] if i < len(timestamps) else None,
                    "price": round(price, 2),
                    "coins": round(coins_bought, 8),
                })

        current_price = prices[-1]
        current_value = total_coins * current_price

        timeline = []
        step_t = max(1, len(prices) // 50)
        for i in range(0, len(prices), step_t):
            coins_so_far = 0
            invested_so_far = 0
            for p in purchases:
                if p["date"] and timestamps[i] and p["date"] <= timestamps[i]:
                    coins_so_far += p["coins"]
                    invested_so_far += monthly_amount
            if coins_so_far > 0:
                timeline.append({
                    "timestamp": timestamps[i],
                    "value": round(coins_so_far * prices[i], 2),
                    "invested": round(invested_so_far, 2)
                })

        roi = ((current_value - total_invested) / total_invested * 100) if total_invested > 0 else 0
        avg_buy_price = (total_invested / total_coins) if total_coins > 0 else 0

        first_price = purchases[0]["price"] if purchases else prices[0]
        lump_sum_coins = total_invested / first_price if first_price > 0 else 0
        lump_sum_value = lump_sum_coins * current_price

        return jsonify({
            "crypto_id": crypto_id,
            "monthly_amount": monthly_amount,
            "months": months,
            "total_invested": round(total_invested, 2),
            "total_coins": round(total_coins, 8),
            "current_price": round(current_price, 2),
            "current_value": round(current_value, 2),
            "roi": round(roi, 2),
            "avg_buy_price": round(avg_buy_price, 2),
            "profit": round(current_value - total_invested, 2),
            "timeline": timeline,
            "lump_sum_value": round(lump_sum_value, 2),
            "dca_vs_lumpsum": round(current_value - lump_sum_value, 2)
        })
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/exchanges/<crypto_id>")
def api_exchanges(crypto_id):
    """API: Multi-Exchange Prices (Binance + Kraken)"""
    # Mapping من CoinGecko ID إلى symbols
    binance_map = {
        "bitcoin": "BTCUSDT", "ethereum": "ETHUSDT",
        "binancecoin": "BNBUSDT", "solana": "SOLUSDT",
        "ripple": "XRPUSDT", "cardano": "ADAUSDT",
        "dogecoin": "DOGEUSDT", "tron": "TRXUSDT",
        "polkadot": "DOTUSDT", "chainlink": "LINKUSDT",
        "matic-network": "MATICUSDT", "avalanche-2": "AVAXUSDT",
        "litecoin": "LTCUSDT", "uniswap": "UNIUSDT",
        "stellar": "XLMUSDT"
    }

    kraken_map = {
        "bitcoin": "XBTUSDT", "ethereum": "ETHUSDT",
        "binancecoin": "BNBUSDT", "solana": "SOLUSDT",
        "ripple": "XRPUSDT", "cardano": "ADAUSDT",
        "dogecoin": "DOGEUSDT", "tron": "TRXUSDT",
        "polkadot": "DOTUSDT", "chainlink": "LINKUSDT",
        "matic-network": "MATICUSDT", "avalanche-2": "AVAXUSDT",
        "litecoin": "LTCUSDT", "uniswap": "UNIUSDT",
        "stellar": "XLMUSDT"
    }

    exchanges = []

    # Binance
    binance_symbol = binance_map.get(crypto_id)
    if binance_symbol:
        try:
            url = "https://api.binance.com/api/v3/ticker/24hr"
            response = requests.get(url, params={"symbol": binance_symbol}, timeout=8)
            if response.ok:
                data = response.json()
                exchanges.append({
                    "name": "Binance",
                    "price": float(data["lastPrice"]),
                    "volume_24h": float(data["quoteVolume"]),
                    "change_24h": float(data["priceChangePercent"]),
                    "url": f"https://www.binance.com/en/trade/{binance_symbol}"
                })
        except Exception as e:
            print(f"Binance error: {e}")

    # Kraken
    kraken_symbol = kraken_map.get(crypto_id)
    if kraken_symbol:
        try:
            url = "https://api.kraken.com/0/public/Ticker"
            response = requests.get(url, params={"pair": kraken_symbol}, timeout=8)
            if response.ok:
                data = response.json()
                if data.get("result"):
                    pair_data = list(data["result"].values())[0]
                    price = float(pair_data["c"][0])
                    volume = float(pair_data["v"][1])
                    open_price = float(pair_data["o"])
                    change = ((price - open_price) / open_price * 100) if open_price > 0 else 0
                    exchanges.append({
                        "name": "Kraken",
                        "price": price,
                        "volume_24h": volume * price,
                        "change_24h": round(change, 2),
                        "url": f"https://pro.kraken.com/app/trade/{kraken_symbol.lower()}"
                    })
        except Exception as e:
            print(f"Kraken error: {e}")

    if not exchanges:
        return jsonify({"error": "Aucune donnée disponible"}), 500

    # ترتيب حسب السعر
    exchanges_sorted = sorted(exchanges, key=lambda x: x["price"])

    cheapest = exchanges_sorted[0]
    expensive = exchanges_sorted[-1]
    spread = ((expensive["price"] - cheapest["price"]) / cheapest["price"] * 100) if cheapest["price"] > 0 else 0

    return jsonify({
        "crypto_id": crypto_id,
        "exchanges": exchanges_sorted,
        "cheapest": cheapest["name"],
        "expensive": expensive["name"],
        "spread": round(spread, 3)
    })
# ═══════════════════════════════════════════════════════
#  API: AI TRADING SIGNALS
# ═══════════════════════════════════════════════════════

@app.route("/api/signals/<crypto_id>")
def api_signals(crypto_id):
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}"
        params = {"localization": "false", "tickers": "false", "market_data": "true", "developer_data": "false", "community_data": "false"}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        md = data.get("market_data", {})
        name = data.get("name", crypto_id)
        symbol = (data.get("symbol") or "").upper()

        signal_data = f"""
Crypto: {name} ({symbol})
Prix actuel: ${md.get('current_price', {}).get('usd', 0):,.2f}
24h: {md.get('price_change_percentage_24h', 0):.2f}%
7j: {md.get('price_change_percentage_7d', 0):.2f}%
30j: {md.get('price_change_percentage_30d', 0):.2f}%
Market Cap: ${md.get('market_cap', {}).get('usd', 0):,.0f}
Volume 24h: ${md.get('total_volume', {}).get('usd', 0):,.0f}
ATH: ${md.get('ath', {}).get('usd', 0):,.2f}
Du ATH: {md.get('ath_change_percentage', {}).get('usd', 0):.2f}%
"""

        prompt = f"""Analyse cette cryptomonnaie et donne un signal de trading:

{signal_data}

Réponds en JSON avec ce format exact:
{{
  "signal": "BUY" ou "SELL" ou "HOLD",
  "confidence": 0-100,
  "timeframe": "short" ou "medium" ou "long",
  "reasoning": "3-4 phrases expliquant pourquoi",
  "risk_level": "LOW" ou "MEDIUM" ou "HIGH",
  "key_points": ["point 1", "point 2", "point 3"]
}}

Ne donne que le JSON, rien d'autre. Sois objectif et mentionne les risques."""

        response_text = chat(prompt)
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if not json_match:
            return jsonify({"error": "Réponse AI invalide", "raw": response_text[:500]}), 500

        try:
            result = json.loads(json_match.group())
        except json.JSONDecodeError:
            return jsonify({"error": "JSON invalide", "raw": response_text[:500]}), 500

        result["crypto_id"] = crypto_id
        result["crypto_name"] = name
        result["crypto_symbol"] = symbol
        result["current_price"] = md.get("current_price", {}).get("usd", 0)

        return jsonify(result)
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500


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
        return jsonify({"error": "Impossible de récupérer les données"}), 500

    valid = [c for c in data if c.get("price_change_percentage_24h") is not None]
    gainers = sorted(valid, key=lambda x: x.get("price_change_percentage_24h", 0), reverse=True)[:5]
    losers = sorted(valid, key=lambda x: x.get("price_change_percentage_24h", 0))[:5]

    def fmt(c):
        return {
            "id": c.get("id", ""), "symbol": c.get("symbol", "").upper(),
            "name": c.get("name", ""), "current_price": c.get("current_price", 0),
            "price_change_percentage_24h": c.get("price_change_percentage_24h", 0),
            "market_cap": c.get("market_cap", 0),
        }

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
        return jsonify({"error": "Impossible de récupérer les données"}), 500

    data = enrich_with_risk(data)

    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(["#", "Symbole", "Nom", "Prix", "24h (%)", "Market Cap", "Risque (score)", "Risque (level)"])

    for i, coin in enumerate(data, 1):
        writer.writerow([
            i,
            coin.get("symbol", "").upper(),
            coin.get("name", ""),
            coin.get("current_price", 0),
            coin.get("price_change_percentage_24h", 0),
            coin.get("market_cap", 0),
            coin.get("risk_score", 0),
            coin.get("risk_level", "LOW"),
        ])

    output = si.getvalue()
    si.close()

    return Response(
        output,
        mimetype="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=cryptoguard_{currency}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )


# ═══════════════════════════════════════════════════════
#  API: CRYPTO DETAILS
# ═══════════════════════════════════════════════════════

@app.route("/api/crypto/<crypto_id>")
def api_crypto_details(crypto_id):
    cache_file = "cache_crypto.json"
    cache_duration = 86400

    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cache = json.load(f)
            entry = cache.get(crypto_id)
            if entry and (time.time() - entry["timestamp"]) < cache_duration:
                return jsonify(entry["data"])
        except (json.JSONDecodeError, IOError):
            pass

    try:
        url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}"
        params = {"localization": "false", "tickers": "false", "market_data": "true", "community_data": "false", "developer_data": "false"}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        md = data.get("market_data", {})
        links = data.get("links", {})

        desc = data.get("description", {}).get("en", "") or ""
        desc = re.sub(r'<[^>]+>', '', desc)
        desc = desc[:600] + ("..." if len(desc) > 600 else "")

        exchanges = []
        try:
            tickers_url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}/tickers"
            tickers_resp = requests.get(tickers_url, params={"order": "trust_score_desc"}, timeout=10)
            if tickers_resp.ok:
                tickers_data = tickers_resp.json()
                seen = set()
                for tk in tickers_data.get("tickers", []):
                    ex_name = tk.get("market", {}).get("name", "")
                    ex_url = tk.get("trade_url", "") or tk.get("market", {}).get("url", "")
                    if ex_name and ex_name not in seen:
                        seen.add(ex_name)
                        exchanges.append({"name": ex_name, "url": ex_url, "pair": tk.get("base", "") + "/" + tk.get("target", "")})
                    if len(exchanges) >= 6:
                        break
        except Exception:
            pass

        result = {
            "id": data.get("id"), "symbol": (data.get("symbol") or "").upper(),
            "name": data.get("name", ""), "image": (data.get("image") or {}).get("large", ""),
            "description": desc, "genesis_date": data.get("genesis_date"),
            "categories": (data.get("categories") or [])[:5],
            "homepage": (links.get("homepage") or [""])[0],
            "whitepaper": links.get("whitepaper", ""),
            "twitter": links.get("twitter_screen_name", ""),
            "reddit": links.get("subreddit_url", ""),
            "blockchain_site": (links.get("blockchain_site") or [""])[0],
            "market_data": {
                "current_price": md.get("current_price", {}).get("usd", 0),
                "market_cap": md.get("market_cap", {}).get("usd", 0),
                "total_volume": md.get("total_volume", {}).get("usd", 0),
                "ath": md.get("ath", {}).get("usd", 0),
                "circulating_supply": md.get("circulating_supply", 0),
                "max_supply": md.get("max_supply", 0),
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
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache = json.load(f)
                entry = cache.get(crypto_id)
                if entry:
                    return jsonify(entry["data"])
            except (json.JSONDecodeError, IOError):
                pass
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
            response = requests.get(feed_url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
            root = ET.fromstring(response.content)
            news = []
            for item in root.findall(".//item")[:9]:
                title = item.find("title")
                link = item.find("link")
                pub_date = item.find("pubDate")
                description = item.find("description")
                enclosure = item.find("enclosure")
                image = enclosure.get("url", "") if enclosure is not None else ""
                published = 0
                if pub_date is not None and pub_date.text:
                    try:
                        from email.utils import parsedate_to_datetime
                        dt = parsedate_to_datetime(pub_date.text)
                        published = int(dt.timestamp())
                    except Exception:
                        pass
                news.append({
                    "title": (title.text if title is not None else "") or "",
                    "url": (link.text if link is not None else "") or "",
                    "source": feed_url.split("/")[2].replace("www.", ""),
                    "image": image, "published": published,
                    "body": ((description.text if description is not None else "") or "")[:120] + "..."
                })
            if news:
                return jsonify({"news": news})
        except Exception as e:
            print(f"Feed error: {e}")
            continue
    return jsonify({"error": "Impossible de charger les news"}), 500


# ═══════════════════════════════════════════════════════
#  API: CHAT
# ═══════════════════════════════════════════════════════

@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json()
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "Message vide"}), 400
    crypto_data = cg.get_top_cryptos(10, "usd")
    if not crypto_data:
        crypto_data = cg.fetch_prices_robust(cg.CRYPTOS[:10], "usd")
    response = chat(message, crypto_data)
    return jsonify({"message": message, "response": response})


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
        return jsonify({"error": "Aucune image fournie"}), 400

    image = request.files["image"]
    if not image.filename:
        return jsonify({"error": "Fichier vide"}), 400

    allowed_types = ["image/png", "image/jpeg", "image/jpg", "image/webp"]
    if image.mimetype not in allowed_types:
        return jsonify({"error": "Type d'image non supporté"}), 400

    image.seek(0, 2)
    size = image.tell()
    image.seek(0)

    if size > 5 * 1024 * 1024:
        return jsonify({"error": "Image trop volumineuse (max 5 MB)"}), 400

    try:
        lang = get_locale()
        image_bytes = image.read()
        result = analyze_contract_image(image_bytes, image.mimetype, lang)
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

    crypto_ids = list(set([item.crypto_id for item in items]))
    days = 30

    cache_file = "cache_history.json"
    crypto_history = {}

    for cid in crypto_ids:
        cache_key = f"{cid}_{days}"

        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache = json.load(f)
                entry = cache.get(cache_key)
                if entry and entry.get("prices"):
                    crypto_history[cid] = {
                        "prices": entry["prices"],
                        "timestamps": entry.get("timestamps", [])
                    }
                    continue
            except (json.JSONDecodeError, IOError):
                pass

        try:
            url = f"https://api.coingecko.com/api/v3/coins/{cid}/market_chart"
            params = {"vs_currency": "usd", "days": days}
            response = requests.get(url, params=params, timeout=10)
            if response.ok:
                data = response.json()
                prices = [p[1] for p in data.get("prices", [])]
                timestamps = [p[0] for p in data.get("prices", [])]
                crypto_history[cid] = {"prices": prices, "timestamps": timestamps}

                cache = {}
                if os.path.exists(cache_file):
                    try:
                        with open(cache_file, "r", encoding="utf-8") as f:
                            cache = json.load(f)
                    except (json.JSONDecodeError, IOError):
                        cache = {}
                cache[cache_key] = {
                    "timestamp": time.time(),
                    "prices": prices,
                    "timestamps": timestamps
                }
                try:
                    with open(cache_file, "w", encoding="utf-8") as f:
                        json.dump(cache, f)
                except IOError:
                    pass
        except requests.RequestException:
            continue

    if not crypto_history:
        return jsonify({"error": "Impossible de récupérer l'historique"}), 500

    min_len = min(len(h["prices"]) for h in crypto_history.values())

    timeline = []
    timestamps_ref = None

    for cid, h in crypto_history.items():
        if len(h["timestamps"]) >= min_len and not timestamps_ref:
            timestamps_ref = h["timestamps"][-min_len:]

    for i in range(min_len):
        total = 0
        for item in items:
            h = crypto_history.get(item.crypto_id)
            if h and len(h["prices"]) > i:
                total += h["prices"][-(min_len - i)] * item.amount
        timeline.append(round(total, 2))

    total_cost = sum(item.buy_price * item.amount for item in items)

    return jsonify({
        "timeline": timeline,
        "timestamps": timestamps_ref or [],
        "total_cost": round(total_cost, 2),
        "crypto_count": len(crypto_ids)
    })


# ═══════════════════════════════════════════════════════
#  PROFILE
# ═══════════════════════════════════════════════════════

@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html", user=current_user)


# ═══════════════════════════════════════════════════════
#  WATCHLIST
# ═══════════════════════════════════════════════════════

@app.route("/watchlist")
@login_required
def watchlist():
    items = WatchlistItem.query.filter_by(user_id=current_user.id).all()
    crypto_ids = [item.crypto_id for item in items]
    prices = {}
    if crypto_ids:
        data = cg.fetch_prices_robust(crypto_ids, "usd")
        if data:
            prices = {coin["id"]: coin for coin in data}
    return render_template("watchlist.html", items=items, prices=prices)


@app.route("/watchlist/add/<crypto_id>", methods=["POST"])
@login_required
def watchlist_add(crypto_id):
    symbol = request.form.get("symbol", crypto_id[:3]).upper()
    existing = WatchlistItem.query.filter_by(user_id=current_user.id, crypto_id=crypto_id).first()
    if not existing:
        item = WatchlistItem(user_id=current_user.id, crypto_id=crypto_id, crypto_symbol=symbol)
        db.session.add(item)
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


# ═══════════════════════════════════════════════════════
#  PORTFOLIO
# ═══════════════════════════════════════════════════════

@app.route("/portfolio")
@login_required
def portfolio():
    items = PortfolioItem.query.filter_by(user_id=current_user.id).all()
    crypto_ids = list(set([item.crypto_id for item in items]))
    prices = {}
    if crypto_ids:
        data = cg.fetch_prices_robust(crypto_ids, "usd")
        if data:
            prices = {coin["id"]: coin["current_price"] for coin in data}

    total_value = 0
    total_cost = 0
    enriched_items = []

    for item in items:
        current_price = prices.get(item.crypto_id, 0)
        current_value = current_price * item.amount
        cost = item.buy_price * item.amount
        pnl = current_value - cost
        pnl_percent = (pnl / cost * 100) if cost > 0 else 0
        total_value += current_value
        total_cost += cost
        enriched_items.append({
            "id": item.id, "crypto_id": item.crypto_id, "symbol": item.crypto_symbol,
            "amount": item.amount, "buy_price": item.buy_price, "current_price": current_price,
            "current_value": current_value, "cost": cost, "pnl": pnl, "pnl_percent": pnl_percent,
        })

    total_pnl = total_value - total_cost
    total_pnl_percent = (total_pnl / total_cost * 100) if total_cost > 0 else 0

    return render_template("portfolio.html", items=enriched_items, total_value=total_value,
                          total_cost=total_cost, total_pnl=total_pnl, total_pnl_percent=total_pnl_percent)


@app.route("/portfolio/add", methods=["POST"])
@login_required
def portfolio_add():
    data = request.get_json()
    crypto_id = data.get("crypto_id", "").lower()
    crypto_symbol = data.get("crypto_symbol", "").upper()
    amount = float(data.get("amount", 0))
    buy_price = float(data.get("buy_price", 0))
    if not crypto_id or amount <= 0 or buy_price <= 0:
        return jsonify({"error": "Données invalides"}), 400
    item = PortfolioItem(user_id=current_user.id, crypto_id=crypto_id, crypto_symbol=crypto_symbol, amount=amount, buy_price=buy_price)
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