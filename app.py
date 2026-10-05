"""
CryptoGuard Web App - Flask Backend
Version: 4.0.0 - With OAuth (Google + Facebook)
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for, session, Response
from flask_login import LoginManager, current_user, login_required, login_user
from flask_babel import Babel, gettext as _
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

# Google OAuth
oauth.register(
    name="google",
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"}
)

# Facebook OAuth
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
    """بداية Google OAuth"""
    redirect_uri = url_for("google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@app.route("/auth/google/callback")
def google_callback():
    """Callback من Google"""
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

            user = User(
                username=username,
                email=email,
                password_hash="oauth-google"
            )
            db.session.add(user)
            db.session.commit()

        login_user(user)
        return redirect(url_for("index"))
    except Exception as e:
        print(f"Google OAuth error: {e}")
        return redirect(url_for("auth.login"))


@app.route("/auth/facebook")
def facebook_login():
    """بداية Facebook OAuth"""
    redirect_uri = url_for("facebook_callback", _external=True)
    return oauth.facebook.authorize_redirect(redirect_uri)


@app.route("/auth/facebook/callback")
def facebook_callback():
    """Callback من Facebook"""
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

            user = User(
                username=username,
                email=email,
                password_hash="oauth-facebook"
            )
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
                return jsonify({"crypto_id": crypto_id, "days": days, "prices": entry["prices"], "timestamps": entry["timestamps"], "cached": True})
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
                    return jsonify({"crypto_id": crypto_id, "days": days, "prices": entry["prices"], "timestamps": entry["timestamps"], "cached": True, "stale": True})
            except (json.JSONDecodeError, IOError):
                pass
        return jsonify({"error": f"Erreur API: {str(e)}"}), 500


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

@app.route("/api/analyze-contract", methods=["POST"])
def api_analyze_contract():
    """API: تحليل صورة عقد ذكي"""
    from contract_analyzer import analyze_contract_image
    
    if "image" not in request.files:
        return jsonify({"error": "Aucune image fournie"}), 400
    
    image = request.files["image"]
    
    if not image.filename:
        return jsonify({"error": "Fichier vide"}), 400
    
    # التحقق من النوع
    allowed_types = ["image/png", "image/jpeg", "image/jpg", "image/webp"]
    if image.mimetype not in allowed_types:
        return jsonify({"error": "Type d'image non supporté"}), 400
    
    # التحقق من الحجم (max 5 MB)
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