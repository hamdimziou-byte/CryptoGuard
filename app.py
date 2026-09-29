"""
CryptoGuard Web App - Flask Backend
Version: 2.3.0
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_login import LoginManager, current_user, login_required
from datetime import datetime
from models import db, User, WatchlistItem
from auth import auth
import main as cg

from ai_chat import chat
from scam_detector import enrich_with_risk
import requests
import os
import json
import time

CACHE_DIR = "cache"
HISTORY_CACHE_DURATION = 3600  # ساعة وحدة

# ═══════════════════════════════════════════════════════
#  APP CONFIG
# ═══════════════════════════════════════════════════════

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///cryptoguard.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


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


# ═══════════════════════════════════════════════════════
#  BLUEPRINTS
# ═══════════════════════════════════════════════════════

app.register_blueprint(auth)


# ═══════════════════════════════════════════════════════
#  ROUTES
# ═══════════════════════════════════════════════════════

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/prices")
def api_prices():
    """API: جلب الأسعار"""
    limit = request.args.get("limit", 20, type=int)
    currency = request.args.get("currency", "usd")
    
    data = cg.get_top_cryptos(limit, currency)
    if not data:
        data = cg.fetch_prices_robust(cg.CRYPTOS[:limit], currency)
    
    if not data:
        return jsonify({"error": "Impossible de récupérer les données"}), 500
    
    # زيد Risk Score
    data = enrich_with_risk(data)
    
    return jsonify({
        "timestamp": datetime.now().isoformat(),
        "currency": currency,
        "data": data
    })


@app.route("/api/history/<crypto_id>")
def api_history(crypto_id):
    """API: تاريخ السعر (7 أيام) مع Cache"""
    cache_key = f"history_{crypto_id}"
    
    # 1. جرب Cache (24 ساعة)
    if os.path.exists(cg.CACHE_FILE):
        try:
            with open(cg.CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
            entry = cache.get(cache_key)
            if entry and (time.time() - entry["timestamp"]) < 3600:  # ساعة
                return jsonify({
                    "crypto_id": crypto_id,
                    "prices": entry["prices"],
                    "timestamps": entry["timestamps"],
                    "cached": True
                })
        except (json.JSONDecodeError, IOError):
            pass
    
    # 2. Fetch من API
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}/market_chart"
        params = {"vs_currency": "usd", "days": 7}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        prices = [p[1] for p in data.get("prices", [])]
        timestamps = [p[0] for p in data.get("prices", [])]
        
        # 3. حفظ في Cache
        cache = {}
        if os.path.exists(cg.CACHE_FILE):
            try:
                with open(cg.CACHE_FILE, "r", encoding="utf-8") as f:
                    cache = json.load(f)
            except (json.JSONDecodeError, IOError):
                cache = {}
        
        cache[cache_key] = {
            "timestamp": time.time(),
            "prices": prices,
            "timestamps": timestamps
        }
        
        try:
            with open(cg.CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False)
        except IOError:
            pass
        
        return jsonify({
            "crypto_id": crypto_id,
            "prices": prices,
            "timestamps": timestamps,
            "cached": False
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    # 2. Fetch من API
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}/market_chart"
        params = {
            "vs_currency": "usd",
            "days": 7
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        prices = [p[1] for p in data.get("prices", [])]
        timestamps = [p[0] for p in data.get("prices", [])]
        
        # 3. حفظ في Cache
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump({
                    "timestamp": time.time(),
                    "prices": prices,
                    "timestamps": timestamps
                }, f)
        except IOError:
            pass
        
        return jsonify({
            "crypto_id": crypto_id,
            "prices": prices,
            "timestamps": timestamps,
            "cached": False
        })
    except requests.RequestException as e:
        # إذا 429، جرب Cache قديمة حتى لو expired
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cached = json.load(f)
                return jsonify({
                    "crypto_id": crypto_id,
                    "prices": cached["prices"],
                    "timestamps": cached["timestamps"],
                    "cached": True,
                    "stale": True
                })
            except (json.JSONDecodeError, IOError):
                pass
        
        return jsonify({"error": f"Erreur API: {str(e)}"}), 500


@app.route("/api/chat", methods=["POST"])
def api_chat():
    """API: AI Chat"""
    data = request.get_json()
    message = data.get("message", "").strip()
    
    if not message:
        return jsonify({"error": "Message vide"}), 400
    
    crypto_data = cg.get_top_cryptos(10, "usd")
    if not crypto_data:
        crypto_data = cg.fetch_prices_robust(cg.CRYPTOS[:10], "usd")
    
    response = chat(message, crypto_data)
    
    return jsonify({
        "message": message,
        "response": response
    })


@app.route("/api/search")
def api_search():
    """API: بحث عن عملة"""
    query = request.args.get("q", "")
    if not query:
        return jsonify({"error": "Query vide"}), 400
    results = cg.search_crypto(query)
    return jsonify({"query": query, "results": results or []})


@app.route("/api/exchange")
def api_exchange():
    """API: سعر الصرف"""
    target = request.args.get("to", "TND")
    rate = cg.get_exchange_rate(target)
    return jsonify({"from": "USD", "to": target, "rate": rate})


@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html", user=current_user)


@app.route("/watchlist")
@login_required
def watchlist():
    """صفحة قائمة المراقبة"""
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
    """إضافة عملة للـwatchlist"""
    symbol = request.form.get("symbol", crypto_id[:3]).upper()
    
    existing = WatchlistItem.query.filter_by(
        user_id=current_user.id,
        crypto_id=crypto_id
    ).first()
    
    if not existing:
        item = WatchlistItem(
            user_id=current_user.id,
            crypto_id=crypto_id,
            crypto_symbol=symbol
        )
        db.session.add(item)
        db.session.commit()
        return jsonify({"status": "added", "crypto_id": crypto_id})
    
    return jsonify({"status": "exists", "crypto_id": crypto_id})


@app.route("/watchlist/remove/<crypto_id>", methods=["POST"])
@login_required
def watchlist_remove(crypto_id):
    """حيّد عملة من الـwatchlist"""
    item = WatchlistItem.query.filter_by(
        user_id=current_user.id,
        crypto_id=crypto_id
    ).first()
    
    if item:
        db.session.delete(item)
        db.session.commit()
        return jsonify({"status": "removed", "crypto_id": crypto_id})
    
    return jsonify({"status": "not_found", "crypto_id": crypto_id}), 404


# ═══════════════════════════════════════════════════════
#  ERROR HANDLERS
# ═══════════════════════════════════════════════════════

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("500.html"), 500


# ═══════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=5000)