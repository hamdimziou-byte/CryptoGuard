"""
CryptoGuard Web App - Flask Backend
Version: 2.7.0 - News Feed
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from flask_login import LoginManager, current_user, login_required
from datetime import datetime
from models import db, User, WatchlistItem, PortfolioItem
from auth import auth
import main as cg
from ai_chat import chat
from scam_detector import enrich_with_risk
from email_alerts import send_alert_email
import requests
import json
import time
import os


# ═══════════════════════════════════════════════════════
#  APP CONFIG
# ═══════════════════════════════════════════════════════

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///cryptoguard.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


# ═══════════════════════════════════════════════════════
#  TRANSLATIONS
# ═══════════════════════════════════════════════════════

LANGUAGES = {
    "fr": "Français",
    "en": "English",
    "ar": "العربية"
}

TRANSLATIONS = {
    "fr": {
        "accueil": "Accueil", "alertes": "Alertes", "connexion": "Connexion",
        "inscription": "Inscription", "profil": "Profil", "deconnexion": "Déconnexion",
        "titre": "Surveillance des cryptomonnaies en temps réel", "top": "Top",
        "rafraichir": "Rafraîchir", "prix": "Prix", "symbole": "Symbole",
        "nom": "Nom", "marche": "Market Cap", "risque": "Risque",
        "chart_titre": "BTC - 7 derniers jours", "creer_alerte": "Créer une alerte",
        "cryptomonnaie": "Cryptomonnaie", "condition": "Condition",
        "prix_cible": "Prix cible", "prix_actuel": "Prix actuel",
        "envoyer_alerte": "Envoyer l'alerte", "chat_placeholder": "Posez votre question...",
        "envoyer": "Envoyer", "actualites": "Actualités crypto",
        "lire_suite": "Lire la suite",
    },
    "en": {
        "accueil": "Home", "alertes": "Alerts", "connexion": "Login",
        "inscription": "Sign Up", "profil": "Profile", "deconnexion": "Logout",
        "titre": "Real-time cryptocurrency monitoring", "top": "Top",
        "rafraichir": "Refresh", "prix": "Price", "symbole": "Symbol",
        "nom": "Name", "marche": "Market Cap", "risque": "Risk",
        "chart_titre": "BTC - Last 7 days", "creer_alerte": "Create an alert",
        "cryptomonnaie": "Cryptocurrency", "condition": "Condition",
        "prix_cible": "Target price", "prix_actuel": "Current price",
        "envoyer_alerte": "Send alert", "chat_placeholder": "Ask your question...",
        "envoyer": "Send", "actualites": "Crypto news",
        "lire_suite": "Read more",
    },
    "ar": {
        "accueil": "الرئيسية", "alertes": "التنبيهات", "connexion": "دخول",
        "inscription": "تسجيل", "profil": "الملف", "deconnexion": "خروج",
        "titre": "مراقبة العملات الرقمية في الوقت الحقيقي", "top": "الأعلى",
        "rafraichir": "تحديث", "prix": "السعر", "symbole": "الرمز",
        "nom": "الاسم", "marche": "القيمة السوقية", "risque": "المخاطر",
        "chart_titre": "BTC - آخر 7 أيام", "creer_alerte": "إنشاء تنبيه",
        "cryptomonnaie": "العملة الرقمية", "condition": "الشرط",
        "prix_cible": "السعر المستهدف", "prix_actuel": "السعر الحالي",
        "envoyer_alerte": "إرسال التنبيه", "chat_placeholder": "اطرح سؤالك...",
        "envoyer": "إرسال", "actualites": "أخبار العملات",
        "lire_suite": "اقرأ المزيد",
    },
}

app.config["BABEL_DEFAULT_LOCALE"] = "fr"


def get_locale():
    if "language" in session:
        return session["language"]
    return request.accept_languages.best_match(LANGUAGES.keys())


def t(key):
    lang = get_locale()
    return TRANSLATIONS.get(lang, TRANSLATIONS["fr"]).get(key, key)


@app.context_processor
def inject_globals():
    return dict(get_locale=get_locale, languages=LANGUAGES, t=t)


# ═══════════════════════════════════════════════════════
#  LOGIN MANAGER
# ═══════════════════════════════════════════════════════

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"
login_manager.login_message = "Connectez-vous pour accéder à cette page."


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


app.register_blueprint(auth)


# ═══════════════════════════════════════════════════════
#  ROUTES
# ═══════════════════════════════════════════════════════

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/set_language/<lang>")
def set_language(lang):
    if lang in LANGUAGES:
        session["language"] = lang
    return redirect(request.referrer or url_for("index"))


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


@app.route("/api/history/<crypto_id>")
def api_history(crypto_id):
    cache_file = "cache_history.json"
    cache_duration = 3600
    
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cache = json.load(f)
            entry = cache.get(crypto_id)
            if entry and (time.time() - entry["timestamp"]) < cache_duration:
                return jsonify({"crypto_id": crypto_id, "prices": entry["prices"], "timestamps": entry["timestamps"], "cached": True})
        except (json.JSONDecodeError, IOError):
            pass
    
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}/market_chart"
        response = requests.get(url, params={"vs_currency": "usd", "days": 7}, timeout=10)
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
        
        cache[crypto_id] = {"timestamp": time.time(), "prices": prices, "timestamps": timestamps}
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache, f)
        except IOError:
            pass
        
        return jsonify({"crypto_id": crypto_id, "prices": prices, "timestamps": timestamps, "cached": False})
    except requests.RequestException as e:
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache = json.load(f)
                entry = cache.get(crypto_id)
                if entry:
                    return jsonify({"crypto_id": crypto_id, "prices": entry["prices"], "timestamps": entry["timestamps"], "cached": True, "stale": True})
            except (json.JSONDecodeError, IOError):
                pass
        return jsonify({"error": f"Erreur API: {str(e)}"}), 500


@app.route("/api/news")
def api_news():
    """API: أخبار الكريبتو (RSS Feed)"""
    import xml.etree.ElementTree as ET
    
    feeds = [
        "https://cointelegraph.com/rss",
        "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "https://cryptonews.com/news/feed/",
    ]
    
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
                
                # صورة
                image = ""
                if enclosure is not None:
                    image = enclosure.get("url", "")
                
                # تاريخ
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
                    "image": image,
                    "published": published,
                    "body": ((description.text if description is not None else "") or "")[:120] + "..."
                })
            
            if news:
                return jsonify({"news": news})
        except Exception as e:
            print(f"Feed error ({feed_url}): {e}")
            continue
    
    return jsonify({"error": "Impossible de charger les news"}), 500
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


@app.route("/api/alerts/test", methods=["POST"])
@login_required
def api_alerts_test():
    data = request.get_json()
    result = send_alert_email(
        to_email=current_user.email,
        username=current_user.username,
        crypto_symbol=data.get("crypto_symbol", "BTC"),
        current_price=data.get("current_price", 0),
        condition=data.get("condition", "above"),
        target_price=data.get("target_price", 0)
    )
    return jsonify(result)


@app.route("/api/search")
def api_search():
    query = request.args.get("q", "")
    if not query:
        return jsonify({"error": "Query vide"}), 400
    results = cg.search_crypto(query)
    return jsonify({"query": query, "results": results or []})


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
    
    item = PortfolioItem(user_id=current_user.id, crypto_id=crypto_id,
                        crypto_symbol=crypto_symbol, amount=amount, buy_price=buy_price)
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